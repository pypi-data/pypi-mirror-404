"""
Cortex MCP - Intent Cache

사용자 의도를 추적하고 AI 행동과의 일치 여부를 관리

기능:
- 사용자 의도 저장 (pending_intents)
- 의도 이행 확인 (verified_intents)
- 의도 폐기 처리 (abandoned_intents)
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


class IntentCache:
    """
    사용자 의도 캐시 관리

    AI가 사용자 의도를 잊지 않도록 추적하고,
    현재 행동이 의도와 일치하는지 검증할 수 있도록 지원
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

        self.cache_file = self.memory_dir / "_intent_cache.json"
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """캐시 파일 로드"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    data = json.load(f)
                    portalocker.unlock(f)
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"[IntentCache] 캐시 로드 실패: {e}")

        return {
            "pending_intents": [],
            "verified_intents": [],
            "abandoned_intents": [],
            "max_pending": 10,  # 최대 pending 개수
            "max_history": 50,  # verified/abandoned 히스토리 개수
        }

    def _save_cache(self) -> None:
        """캐시 파일 저장"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
                portalocker.unlock(f)
        except IOError as e:
            logger.error(f"[IntentCache] 캐시 저장 실패: {e}")

    def add_intent(
        self,
        text: str,
        source_message_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        새로운 의도 추가

        Args:
            text: 의도 텍스트 (예: "성능 최적화해줘")
            source_message_id: 원본 메시지 ID
            metadata: 추가 메타데이터

        Returns:
            생성된 의도 객체
        """
        intent = {
            "id": f"intent_{uuid.uuid4().hex[:8]}",
            "text": text,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "source_message_id": source_message_id,
            "status": "pending",
            "metadata": metadata or {},
        }

        self._cache["pending_intents"].append(intent)

        # max_pending 초과 시 가장 오래된 것 abandoned로 이동
        max_pending = self._cache.get("max_pending", 10)
        while len(self._cache["pending_intents"]) > max_pending:
            oldest = self._cache["pending_intents"].pop(0)
            oldest["status"] = "abandoned"
            oldest["abandoned_at"] = datetime.now(timezone.utc).isoformat()
            oldest["abandon_reason"] = "max_pending_exceeded"
            self._cache["abandoned_intents"].append(oldest)

        self._trim_history()
        self._save_cache()

        logger.info(f"[IntentCache] 의도 추가: {intent['id']} - {text[:50]}")
        return intent

    def get_pending_intents(self) -> List[Dict]:
        """
        현재 미검증 의도 목록 반환

        Returns:
            pending 상태의 의도 리스트
        """
        return self._cache.get("pending_intents", [])

    def verify_intent(
        self,
        intent_id: str,
        evidence: Optional[str] = None,
        verified_by: str = "ai",
    ) -> bool:
        """
        의도 이행 완료 처리

        Args:
            intent_id: 이행된 의도 ID
            evidence: 이행 증거 (선택)
            verified_by: 검증 주체 ("ai" 또는 "user")

        Returns:
            성공 여부
        """
        for i, intent in enumerate(self._cache["pending_intents"]):
            if intent["id"] == intent_id:
                intent["status"] = "verified"
                intent["verified_at"] = datetime.now(timezone.utc).isoformat()
                intent["evidence"] = evidence
                intent["verified_by"] = verified_by

                self._cache["verified_intents"].append(intent)
                self._cache["pending_intents"].pop(i)

                self._trim_history()
                self._save_cache()

                logger.info(f"[IntentCache] 의도 이행 확인: {intent_id}")
                return True

        logger.warning(f"[IntentCache] 의도를 찾을 수 없음: {intent_id}")
        return False

    def abandon_intent(
        self,
        intent_id: str,
        reason: str = "user_cancelled",
    ) -> bool:
        """
        의도 폐기 처리

        Args:
            intent_id: 폐기할 의도 ID
            reason: 폐기 사유

        Returns:
            성공 여부
        """
        for i, intent in enumerate(self._cache["pending_intents"]):
            if intent["id"] == intent_id:
                intent["status"] = "abandoned"
                intent["abandoned_at"] = datetime.now(timezone.utc).isoformat()
                intent["abandon_reason"] = reason

                self._cache["abandoned_intents"].append(intent)
                self._cache["pending_intents"].pop(i)

                self._trim_history()
                self._save_cache()

                logger.info(f"[IntentCache] 의도 폐기: {intent_id} - {reason}")
                return True

        return False

    def check_alignment(
        self,
        current_action: str,
        ai_judgment: Optional[Dict] = None,
    ) -> Dict:
        """
        현재 행동과 pending 의도의 일치 여부 확인

        AI의 판단 결과를 받아서 처리하거나,
        단순히 pending 의도 목록만 반환

        Args:
            current_action: 현재 수행 중인 작업 설명
            ai_judgment: AI의 판단 결과 (선택)
                {
                    "matched_intent_id": "intent_001" | null,
                    "is_aligned": true | false,
                    "reason": "..."
                }

        Returns:
            {
                "pending_intents": [...],
                "alignment_result": {...} | null,
                "warnings": [...]
            }
        """
        pending = self.get_pending_intents()
        result = {
            "pending_intents": pending,
            "alignment_result": None,
            "warnings": [],
        }

        if not pending:
            return result

        if ai_judgment:
            result["alignment_result"] = ai_judgment

            matched_id = ai_judgment.get("matched_intent_id")
            is_aligned = ai_judgment.get("is_aligned", False)

            if matched_id and is_aligned:
                # 의도 이행 완료 처리
                self.verify_intent(
                    matched_id,
                    evidence=current_action,
                    verified_by="ai",
                )
            elif not is_aligned and pending:
                # 불일치 경고
                result["warnings"].append({
                    "type": "intent_mismatch",
                    "message": f"현재 행동이 pending 의도와 불일치: {ai_judgment.get('reason', '')}",
                    "pending_intents": [i["text"] for i in pending],
                    "current_action": current_action,
                })

        return result

    def get_context_for_ai(self) -> str:
        """
        AI에게 제공할 컨텍스트 문자열 생성

        Returns:
            pending 의도 목록을 포맷팅한 문자열
        """
        pending = self.get_pending_intents()

        if not pending:
            return "현재 미검증 의도 없음"

        lines = ["현재 미검증 의도 목록:"]
        for intent in pending:
            elapsed = self._get_elapsed_time(intent["extracted_at"])
            lines.append(f"- [{intent['id']}] {intent['text']} ({elapsed})")

        return "\n".join(lines)

    def _get_elapsed_time(self, iso_time: str) -> str:
        """경과 시간 계산"""
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
        max_history = self._cache.get("max_history", 50)

        if len(self._cache["verified_intents"]) > max_history:
            self._cache["verified_intents"] = self._cache["verified_intents"][-max_history:]

        if len(self._cache["abandoned_intents"]) > max_history:
            self._cache["abandoned_intents"] = self._cache["abandoned_intents"][-max_history:]

    def get_stats(self) -> Dict:
        """통계 반환"""
        return {
            "pending_count": len(self._cache.get("pending_intents", [])),
            "verified_count": len(self._cache.get("verified_intents", [])),
            "abandoned_count": len(self._cache.get("abandoned_intents", [])),
        }

    def clear_all(self) -> None:
        """모든 캐시 초기화 (테스트용)"""
        self._cache = {
            "pending_intents": [],
            "verified_intents": [],
            "abandoned_intents": [],
            "max_pending": 10,
            "max_history": 50,
        }
        self._save_cache()
        logger.info("[IntentCache] 캐시 초기화 완료")


# 싱글톤 인스턴스 관리
_intent_cache_instances: Dict[str, IntentCache] = {}


def get_intent_cache(project_id: str, memory_dir: Optional[Path] = None) -> IntentCache:
    """
    IntentCache 싱글톤 인스턴스 반환

    Args:
        project_id: 프로젝트 ID
        memory_dir: 메모리 디렉토리 (선택)

    Returns:
        IntentCache 인스턴스
    """
    if project_id not in _intent_cache_instances:
        _intent_cache_instances[project_id] = IntentCache(project_id, memory_dir)

    return _intent_cache_instances[project_id]
