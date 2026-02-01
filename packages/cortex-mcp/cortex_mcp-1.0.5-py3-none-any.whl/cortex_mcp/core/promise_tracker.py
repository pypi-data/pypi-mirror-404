"""
Cortex MCP - Promise Tracker

AI가 "~하겠습니다"라고 한 약속을 추적하고 이행 여부를 검증

기능:
- AI 약속 기록 (pending_promises)
- 약속 이행 확인 (fulfilled_promises)
- 약속 파기 처리 (broken_promises)
- AI 판단 결과 기반 상태 전환
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import portalocker

logger = logging.getLogger(__name__)


class PromiseTracker:
    """
    AI 약속 추적 관리

    AI가 "~하겠습니다", "~할 예정입니다" 등의 약속을 추적하고,
    실제 이행 여부를 검증할 수 있도록 지원
    """

    def __init__(self, project_id: str, memory_dir: Optional[Path] = None):
        """
        Args:
            project_id: 프로젝트 ID
            memory_dir: 메모리 저장 디렉토리 (기본: ~/.cortex/memory)
        """
        self.project_id = project_id

        if memory_dir is None:
            memory_dir = Path.home() / ".cortex" / "memory"

        self.memory_dir = memory_dir / project_id
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.tracker_file = self.memory_dir / "_promises.json"
        self._data = self._load_data()

    def _load_data(self) -> Dict:
        """트래커 파일 로드"""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, "r", encoding="utf-8") as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    data = json.load(f)
                    portalocker.unlock(f)
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"[PromiseTracker] 데이터 로드 실패: {e}")

        return {
            "pending_promises": [],
            "fulfilled_promises": [],
            "broken_promises": [],
            "max_pending": 20,  # 최대 pending 개수
            "max_history": 100,  # fulfilled/broken 히스토리 개수
        }

    def _save_data(self) -> None:
        """트래커 파일 저장"""
        try:
            with open(self.tracker_file, "w", encoding="utf-8") as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                json.dump(self._data, f, ensure_ascii=False, indent=2)
                portalocker.unlock(f)
        except IOError as e:
            logger.error(f"[PromiseTracker] 데이터 저장 실패: {e}")

    def add_promise(
        self,
        text: str,
        source_response_id: Optional[str] = None,
        promise_type: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        새로운 약속 기록

        Args:
            text: 약속 텍스트 (예: "JWT 인증으로 구현하겠습니다")
            source_response_id: 원본 응답 ID
            promise_type: 약속 유형 (implementation, fix, refactor, etc.)
            metadata: 추가 메타데이터

        Returns:
            생성된 약속 객체
        """
        promise = {
            "id": f"promise_{uuid.uuid4().hex[:8]}",
            "text": text,
            "made_at": datetime.now(timezone.utc).isoformat(),
            "source_response_id": source_response_id,
            "promise_type": promise_type,
            "status": "pending",
            "metadata": metadata or {},
        }

        self._data["pending_promises"].append(promise)

        # max_pending 초과 시 가장 오래된 것 broken으로 이동
        max_pending = self._data.get("max_pending", 20)
        while len(self._data["pending_promises"]) > max_pending:
            oldest = self._data["pending_promises"].pop(0)
            oldest["status"] = "broken"
            oldest["broken_at"] = datetime.now(timezone.utc).isoformat()
            oldest["break_reason"] = "max_pending_exceeded"
            self._data["broken_promises"].append(oldest)

        self._trim_history()
        self._save_data()

        logger.info(f"[PromiseTracker] 약속 추가: {promise['id']} - {text[:50]}")
        return promise

    def get_pending_promises(self) -> List[Dict]:
        """
        현재 미이행 약속 목록 반환

        Returns:
            pending 상태의 약속 리스트
        """
        return self._data.get("pending_promises", [])

    def fulfill_promise(
        self,
        promise_id: str,
        evidence: Optional[str] = None,
        verified_by: str = "ai",
    ) -> bool:
        """
        약속 이행 완료 처리

        Args:
            promise_id: 이행된 약속 ID
            evidence: 이행 증거 (선택)
            verified_by: 검증 주체 ("ai" 또는 "user")

        Returns:
            성공 여부
        """
        for i, promise in enumerate(self._data["pending_promises"]):
            if promise["id"] == promise_id:
                promise["status"] = "fulfilled"
                promise["fulfilled_at"] = datetime.now(timezone.utc).isoformat()
                promise["evidence"] = evidence
                promise["verified_by"] = verified_by

                self._data["fulfilled_promises"].append(promise)
                self._data["pending_promises"].pop(i)

                self._trim_history()
                self._save_data()

                logger.info(f"[PromiseTracker] 약속 이행 확인: {promise_id}")
                return True

        logger.warning(f"[PromiseTracker] 약속을 찾을 수 없음: {promise_id}")
        return False

    def break_promise(
        self,
        promise_id: str,
        reason: str = "not_fulfilled",
    ) -> bool:
        """
        약속 파기 처리

        Args:
            promise_id: 파기할 약속 ID
            reason: 파기 사유

        Returns:
            성공 여부
        """
        for i, promise in enumerate(self._data["pending_promises"]):
            if promise["id"] == promise_id:
                promise["status"] = "broken"
                promise["broken_at"] = datetime.now(timezone.utc).isoformat()
                promise["break_reason"] = reason

                self._data["broken_promises"].append(promise)
                self._data["pending_promises"].pop(i)

                self._trim_history()
                self._save_data()

                logger.info(f"[PromiseTracker] 약속 파기: {promise_id} - {reason}")
                return True

        return False

    def check_fulfillment(
        self,
        current_action: str,
        ai_judgment: Optional[Dict] = None,
    ) -> Dict:
        """
        현재 행동이 pending 약속을 이행하는지 확인

        AI의 판단 결과를 받아서 처리하거나,
        단순히 pending 약속 목록만 반환

        Args:
            current_action: 현재 수행 중인 작업 설명
            ai_judgment: AI의 판단 결과 (선택)
                {
                    "fulfilled_promise_id": "promise_001" | null,
                    "is_fulfilled": true | false,
                    "reason": "..."
                }

        Returns:
            {
                "pending_promises": [...],
                "fulfillment_result": {...} | null,
                "warnings": [...]
            }
        """
        pending = self.get_pending_promises()
        result = {
            "pending_promises": pending,
            "fulfillment_result": None,
            "warnings": [],
        }

        if not pending:
            return result

        if ai_judgment:
            result["fulfillment_result"] = ai_judgment

            fulfilled_id = ai_judgment.get("fulfilled_promise_id")
            is_fulfilled = ai_judgment.get("is_fulfilled", False)

            if fulfilled_id and is_fulfilled:
                # 약속 이행 완료 처리
                self.fulfill_promise(
                    fulfilled_id,
                    evidence=current_action,
                    verified_by="ai",
                )

        # 오래된 약속 경고
        for promise in pending:
            elapsed = self._get_elapsed_hours(promise["made_at"])
            if elapsed > 24:  # 24시간 이상 경과
                result["warnings"].append({
                    "type": "stale_promise",
                    "promise_id": promise["id"],
                    "message": f"약속이 {int(elapsed)}시간 이상 미이행: {promise['text'][:50]}",
                    "made_at": promise["made_at"],
                })

        return result

    def get_context_for_ai(self) -> str:
        """
        AI에게 제공할 컨텍스트 문자열 생성

        Returns:
            pending 약속 목록을 포맷팅한 문자열
        """
        pending = self.get_pending_promises()

        if not pending:
            return "현재 미이행 약속 없음"

        lines = ["현재 미이행 약속 목록:"]
        for promise in pending:
            elapsed = self._get_elapsed_time_str(promise["made_at"])
            promise_type = promise.get("promise_type", "unknown")
            lines.append(f"- [{promise['id']}] ({promise_type}) {promise['text']} ({elapsed})")

        return "\n".join(lines)

    def _get_elapsed_hours(self, iso_time: str) -> float:
        """경과 시간(시간) 계산"""
        try:
            dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = now - dt
            return delta.total_seconds() / 3600
        except Exception:
            return 0

    def _get_elapsed_time_str(self, iso_time: str) -> str:
        """경과 시간 문자열 계산"""
        try:
            dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = now - dt

            if delta.total_seconds() < 60:
                return "방금 전"
            elif delta.total_seconds() < 3600:
                return f"{int(delta.total_seconds() / 60)}분 전"
            elif delta.total_seconds() < 86400:
                return f"{int(delta.total_seconds() / 3600)}시간 전"
            else:
                return f"{int(delta.total_seconds() / 86400)}일 전"
        except Exception:
            return "알 수 없음"

    def _trim_history(self) -> None:
        """히스토리 개수 제한"""
        max_history = self._data.get("max_history", 100)

        if len(self._data["fulfilled_promises"]) > max_history:
            self._data["fulfilled_promises"] = self._data["fulfilled_promises"][-max_history:]

        if len(self._data["broken_promises"]) > max_history:
            self._data["broken_promises"] = self._data["broken_promises"][-max_history:]

    def get_stats(self) -> Dict:
        """통계 반환"""
        return {
            "pending_count": len(self._data.get("pending_promises", [])),
            "fulfilled_count": len(self._data.get("fulfilled_promises", [])),
            "broken_count": len(self._data.get("broken_promises", [])),
        }

    def get_fulfillment_rate(self) -> float:
        """약속 이행률 계산"""
        fulfilled = len(self._data.get("fulfilled_promises", []))
        broken = len(self._data.get("broken_promises", []))
        total = fulfilled + broken

        if total == 0:
            return 1.0  # 기록 없으면 100%

        return fulfilled / total

    def clear_all(self) -> None:
        """모든 데이터 초기화 (테스트용)"""
        self._data = {
            "pending_promises": [],
            "fulfilled_promises": [],
            "broken_promises": [],
            "max_pending": 20,
            "max_history": 100,
        }
        self._save_data()
        logger.info("[PromiseTracker] 데이터 초기화 완료")


# 싱글톤 인스턴스 관리
_promise_tracker_instances: Dict[str, PromiseTracker] = {}


def get_promise_tracker(project_id: str, memory_dir: Optional[Path] = None) -> PromiseTracker:
    """
    PromiseTracker 싱글톤 인스턴스 반환

    Args:
        project_id: 프로젝트 ID
        memory_dir: 메모리 디렉토리 (선택)

    Returns:
        PromiseTracker 인스턴스
    """
    if project_id not in _promise_tracker_instances:
        _promise_tracker_instances[project_id] = PromiseTracker(project_id, memory_dir)

    return _promise_tracker_instances[project_id]
