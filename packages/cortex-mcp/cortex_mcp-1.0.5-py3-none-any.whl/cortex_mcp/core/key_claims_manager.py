"""
Cortex MCP - Key Claims Manager

세션 간 주요 주장을 관리하고 모순 감지를 지원

기능:
- 세션별 주요 주장 기록
- 이전 주장과 현재 응답 모순 감지 지원
- 세션 히스토리 관리
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import portalocker

logger = logging.getLogger(__name__)


class KeyClaimsManager:
    """
    세션 간 주요 주장 관리

    이전 세션의 주장과 현재 응답이 모순되는지 감지할 수 있도록
    주요 주장을 세션별로 기록하고 관리
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

        self.claims_file = self.memory_dir / "_key_claims.json"
        self._data = self._load_data()

    def _load_data(self) -> Dict:
        """데이터 파일 로드"""
        if self.claims_file.exists():
            try:
                with open(self.claims_file, "r", encoding="utf-8") as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    data = json.load(f)
                    portalocker.unlock(f)
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"[KeyClaimsManager] 데이터 로드 실패: {e}")

        return {
            "sessions": [],
            "max_sessions": 10,  # 최대 세션 개수
            "current_session_id": None,
        }

    def _save_data(self) -> None:
        """데이터 파일 저장"""
        try:
            with open(self.claims_file, "w", encoding="utf-8") as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                json.dump(self._data, f, ensure_ascii=False, indent=2)
                portalocker.unlock(f)
        except IOError as e:
            logger.error(f"[KeyClaimsManager] 데이터 저장 실패: {e}")

    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        새 세션 시작

        Args:
            session_id: 세션 ID (미지정 시 자동 생성)

        Returns:
            세션 ID
        """
        if session_id is None:
            session_id = f"sess_{uuid.uuid4().hex[:8]}"

        session = {
            "session_id": session_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "claims": [],
        }

        self._data["sessions"].append(session)
        self._data["current_session_id"] = session_id

        # max_sessions 초과 시 가장 오래된 세션 제거
        max_sessions = self._data.get("max_sessions", 10)
        while len(self._data["sessions"]) > max_sessions:
            self._data["sessions"].pop(0)

        self._save_data()
        logger.info(f"[KeyClaimsManager] 세션 시작: {session_id}")

        return session_id

    def add_claim(
        self,
        text: str,
        claim_type: str,
        confidence: float = 1.0,
        source_context: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """
        현재 세션에 주요 주장 추가

        Args:
            text: 주장 텍스트
            claim_type: 주장 유형 (implementation_complete, bug_fix, verification, etc.)
            confidence: 확신도 (0.0 ~ 1.0)
            source_context: 원본 응답 맥락
            metadata: 추가 메타데이터

        Returns:
            생성된 주장 객체 (세션 없으면 None)
        """
        current_session = self._get_current_session()
        if current_session is None:
            logger.warning("[KeyClaimsManager] 활성 세션 없음. start_session() 먼저 호출 필요")
            return None

        claim = {
            "id": f"claim_{uuid.uuid4().hex[:8]}",
            "text": text,
            "type": claim_type,
            "confidence": confidence,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "source_context": source_context,
            "metadata": metadata or {},
        }

        current_session["claims"].append(claim)
        self._save_data()

        logger.info(f"[KeyClaimsManager] 주장 추가: {claim['id']} - {text[:50]}")
        return claim

    def _get_current_session(self) -> Optional[Dict]:
        """현재 활성 세션 반환"""
        current_id = self._data.get("current_session_id")
        if current_id is None:
            return None

        for session in self._data["sessions"]:
            if session["session_id"] == current_id:
                return session

        return None

    def get_previous_claims(self, max_claims: int = 50) -> List[Dict]:
        """
        이전 세션들의 주장 목록 반환

        Args:
            max_claims: 반환할 최대 주장 개수

        Returns:
            이전 세션들의 주장 리스트 (최신순)
        """
        all_claims = []
        current_id = self._data.get("current_session_id")

        for session in reversed(self._data["sessions"]):
            # 현재 세션은 제외
            if session["session_id"] == current_id:
                continue

            for claim in reversed(session["claims"]):
                claim_with_session = claim.copy()
                claim_with_session["session_id"] = session["session_id"]
                claim_with_session["session_started_at"] = session["started_at"]
                all_claims.append(claim_with_session)

                if len(all_claims) >= max_claims:
                    return all_claims

        return all_claims

    def get_context_for_ai(self, max_claims: int = 20) -> str:
        """
        AI에게 제공할 이전 주장 컨텍스트 생성

        Args:
            max_claims: 포함할 최대 주장 개수

        Returns:
            이전 주장 목록을 포맷팅한 문자열
        """
        previous_claims = self.get_previous_claims(max_claims)

        if not previous_claims:
            return "이전 세션의 주요 주장 없음"

        lines = ["이전 세션 주요 주장 (최신순):"]
        for claim in previous_claims:
            elapsed = self._get_elapsed_time_str(claim["recorded_at"])
            lines.append(
                f"- [{claim['type']}] {claim['text'][:80]} ({elapsed}, 세션: {claim['session_id'][:12]})"
            )

        return "\n".join(lines)

    def check_contradiction(
        self,
        current_response: str,
        ai_judgment: Optional[Dict] = None,
    ) -> Dict:
        """
        현재 응답과 이전 주장 간 모순 확인

        AI의 판단 결과를 받아서 처리하거나,
        단순히 이전 주장 목록만 반환

        Args:
            current_response: 현재 AI 응답
            ai_judgment: AI의 판단 결과 (선택)
                {
                    "has_contradiction": true | false,
                    "conflicting_claims": [
                        {
                            "previous_claim_id": "claim_001",
                            "previous_text": "...",
                            "current_text": "...",
                            "reason": "..."
                        }
                    ]
                }

        Returns:
            {
                "previous_claims": [...],
                "contradiction_result": {...} | null,
                "warnings": [...]
            }
        """
        previous_claims = self.get_previous_claims(max_claims=30)
        result = {
            "previous_claims": previous_claims,
            "contradiction_result": None,
            "warnings": [],
        }

        if not previous_claims:
            return result

        if ai_judgment:
            result["contradiction_result"] = ai_judgment

            if ai_judgment.get("has_contradiction", False):
                conflicts = ai_judgment.get("conflicting_claims", [])
                for conflict in conflicts:
                    result["warnings"].append({
                        "type": "cross_session_contradiction",
                        "message": f"이전 주장과 모순 감지: {conflict.get('reason', '')}",
                        "previous_text": conflict.get("previous_text", ""),
                        "current_text": conflict.get("current_text", ""),
                        "previous_claim_id": conflict.get("previous_claim_id"),
                    })

        return result

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

    def get_stats(self) -> Dict:
        """통계 반환"""
        total_claims = 0
        for session in self._data["sessions"]:
            total_claims += len(session["claims"])

        return {
            "session_count": len(self._data["sessions"]),
            "total_claims": total_claims,
            "current_session_id": self._data.get("current_session_id"),
        }

    def end_session(self) -> bool:
        """
        현재 세션 종료

        Returns:
            성공 여부
        """
        current_id = self._data.get("current_session_id")
        if current_id is None:
            return False

        for session in self._data["sessions"]:
            if session["session_id"] == current_id:
                session["ended_at"] = datetime.now(timezone.utc).isoformat()
                break

        self._data["current_session_id"] = None
        self._save_data()

        logger.info(f"[KeyClaimsManager] 세션 종료: {current_id}")
        return True

    def clear_all(self) -> None:
        """모든 데이터 초기화 (테스트용)"""
        self._data = {
            "sessions": [],
            "max_sessions": 10,
            "current_session_id": None,
        }
        self._save_data()
        logger.info("[KeyClaimsManager] 데이터 초기화 완료")


# 싱글톤 인스턴스 관리
_key_claims_instances: Dict[str, KeyClaimsManager] = {}


def get_key_claims_manager(project_id: str, memory_dir: Optional[Path] = None) -> KeyClaimsManager:
    """
    KeyClaimsManager 싱글톤 인스턴스 반환

    Args:
        project_id: 프로젝트 ID
        memory_dir: 메모리 디렉토리 (선택)

    Returns:
        KeyClaimsManager 인스턴스
    """
    if project_id not in _key_claims_instances:
        _key_claims_instances[project_id] = KeyClaimsManager(project_id, memory_dir)

    return _key_claims_instances[project_id]
