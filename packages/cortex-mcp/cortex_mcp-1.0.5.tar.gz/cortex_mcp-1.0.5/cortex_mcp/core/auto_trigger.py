"""
Cortex Auto Trigger 시스템

목적: AI의 선택과 무관하게 핵심 Cortex 기능을 강제 실행
- Pre-Hook: 도구 실행 전 맥락 로딩
- Post-Hook: 도구 실행 후 검증 및 메모리 업데이트

이 시스템은 AI의 확률적 특성으로 인한 맥락 손실을 방지합니다.
"""

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


def _get_memory_manager():
    """
    memory_manager 싱글톤 가져오기
    순환 import 방지를 위해 함수 내에서 import
    """
    from cortex_mcp.core.memory_manager import get_memory_manager
    return get_memory_manager()


def _get_reference_history(project_id: str):
    """
    reference_history 인스턴스 가져오기
    순환 import 방지를 위해 함수 내에서 import
    """
    memory_manager = _get_memory_manager()
    return memory_manager._get_reference_history(project_id)


class SessionCache:
    """
    세션별 캐시 시스템

    추가 기능:
    - pending_suggestions 추적 (출처 책임 보장)
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._first_call_tracker: Dict[str, bool] = {}

        # Phase 10.2: suggest_contexts 후 accept/reject 강제
        self._pending_suggestions: Dict[str, Dict[str, Any]] = {}

    def is_first_call(self, session_id: str) -> bool:
        """세션의 첫 호출 여부 확인"""
        if session_id not in self._first_call_tracker:
            self._first_call_tracker[session_id] = True
            return True
        return False

    def get(self, session_id: str, key: str) -> Optional[Any]:
        """캐시에서 데이터 가져오기"""
        session_cache = self._cache.get(session_id, {})
        return session_cache.get(key)

    def set(self, session_id: str, key: str, value: Any):
        """캐시에 데이터 저장"""
        if session_id not in self._cache:
            self._cache[session_id] = {}
        self._cache[session_id][key] = value

    # ===== Phase 10.2: Pending Suggestions 추적 =====

    def add_pending_suggestion(self, session_id: str, project_id: str, suggestion_data: Dict[str, Any]):
        """
        미처리 suggest_contexts 세션 추가

        Args:
            session_id: suggest_contexts에서 반환한 session_id
            project_id: 프로젝트 ID
            suggestion_data: suggest_contexts 결과 데이터
        """
        self._pending_suggestions[session_id] = {
            "project_id": project_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": suggestion_data,
        }
        logger.info(f"[SESSION_CACHE] Pending suggestion added: {session_id}")

    def remove_pending_suggestion(self, session_id: str) -> bool:
        """
        미처리 세션 제거 (accept/reject 완료 시)

        Returns:
            성공 여부
        """
        if session_id in self._pending_suggestions:
            del self._pending_suggestions[session_id]
            logger.info(f"[SESSION_CACHE] Pending suggestion removed: {session_id}")
            return True
        return False

    def get_pending_suggestions(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        미처리 세션 목록 조회

        Args:
            project_id: 특정 프로젝트만 필터링 (선택)

        Returns:
            미처리 세션 목록
        """
        pending = []
        for session_id, data in self._pending_suggestions.items():
            if project_id is None or data["project_id"] == project_id:
                pending.append({
                    "session_id": session_id,
                    **data
                })
        return pending

    def has_pending_suggestions(self, project_id: Optional[str] = None) -> bool:
        """미처리 세션 존재 여부"""
        return len(self.get_pending_suggestions(project_id)) > 0


class AutoTrigger:
    """
    자동 트리거 시스템

    핵심 원칙:
    1. AI가 잊어버려도 시스템이 기억한다
    2. AI가 건너뛰어도 시스템이 실행한다
    3. AI가 틀려도 시스템이 검증한다
    """

    # MANDATORY 도구 (항상 실행, Auto Trigger 불필요)
    MANDATORY_TOOLS = {
        "initialize_context",
        "create_branch",
        "update_memory",
        "get_active_summary",
    }

    # 맥락 인지 도구 (Context-Aware Tools)
    # suggest_contexts 자동 호출이 필요한 모든 도구
    CONTEXT_AWARE_TOOLS = {
        # ===== 프로젝트 스캔 =====
        "scan_project_deep",      # 초기 스캔
        "rescan_project",          # 증분 스캔
        "resolve_context",         # 파일 심층 분석

        # ===== 파일 작업 (코드 수정 시 관련 맥락 필요) =====
        "Edit",                    # 파일 편집
        "Write",                   # 파일 작성

        # ===== 검색 (코드 찾을 때 이전 맥락 참조) =====
        "Grep",                    # 코드 검색
        "Glob",                    # 파일 패턴 검색
        "Read",                    # 파일 읽기

        # ===== 맥락 관리 =====
        "load_context",            # 맥락 활성화
        "create_node",             # Node 그룹 생성
        "search_context",          # RAG 검색

        # ===== Git 작업 (코드 변경 시 맥락 필요) =====
        "link_git_branch",         # Git 브랜치 연동
        "create_snapshot",         # 스냅샷 생성

        # ===== 참조 이력 =====
        "record_reference",        # 참조 기록
    }

    # 하위 호환성을 위한 alias
    CODING_TOOLS = CONTEXT_AWARE_TOOLS

    def __init__(self):
        self.cache = SessionCache()

    def _generate_session_id(self, project_id: str, branch_id: str) -> str:
        """세션 ID 생성"""
        # 간단한 해시 기반 세션 ID
        data = f"{project_id}:{branch_id}:{datetime.now(timezone.utc).date()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _read_claude_core(self) -> str:
        """CLAUDE_CORE.md 읽기"""
        try:
            core_path = Path(__file__).parent.parent.parent / "CLAUDE_CORE.md"
            if core_path.exists():
                return core_path.read_text(encoding="utf-8")
            else:
                logger.warning(f"CLAUDE_CORE.md not found at {core_path}")
                return ""
        except Exception as e:
            logger.error(f"Failed to read CLAUDE_CORE.md: {e}")
            return ""

    def _is_coding_work(self, tool_name: str) -> bool:
        """코딩 작업 도구 여부 판단"""
        return tool_name in self.CODING_TOOLS

    def _generate_search_query(self, tool_name: str, arguments: dict) -> str:
        """
        도구와 인자를 기반으로 검색 쿼리 생성

        Args:
            tool_name: 실행된 도구 이름
            arguments: 도구 실행 인자

        Returns:
            검색에 사용할 쿼리 문자열
        """
        # 도구별 쿼리 템플릿
        if tool_name == "scan_project_deep":
            project_path = arguments.get("project_path", "")
            return f"프로젝트 구조 분석 {project_path}"

        elif tool_name == "rescan_project":
            project_path = arguments.get("project_path", "")
            return f"프로젝트 변경사항 {project_path}"

        elif tool_name == "resolve_context":
            file_path = arguments.get("file_path", "")
            context_id = arguments.get("context_id", "")
            if file_path:
                return f"파일 분석 {file_path}"
            elif context_id:
                return f"컨텍스트 해석 {context_id}"
            else:
                return "컨텍스트 분석"

        # 기본 쿼리
        return f"{tool_name} 작업 관련 맥락"

    def _call_suggest_contexts(
        self, project_id: str, query: str, branch_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        suggest_contexts 실제 호출

        Args:
            project_id: 프로젝트 ID
            query: 검색 쿼리
            branch_id: 브랜치 ID (선택)

        Returns:
            suggest_contexts 결과 또는 None (실패 시)
        """
        try:
            reference_history = _get_reference_history(project_id)
            if not reference_history:
                logger.warning("[AUTO_TRIGGER] reference_history를 가져올 수 없음")
                return None

            result = reference_history.suggest_contexts(
                query=query,
                branch_id=branch_id,
                top_k=5
            )

            if result.get("success"):
                logger.info(
                    f"[AUTO_TRIGGER] suggest_contexts 성공 - "
                    f"Tier {result.get('tier')}, "
                    f"Confidence {result.get('confidence')}"
                )
                return result
            else:
                logger.warning("[AUTO_TRIGGER] suggest_contexts 실패")
                return None

        except Exception as e:
            logger.error(f"[AUTO_TRIGGER] suggest_contexts 호출 실패: {e}")
            return None

    def _accept_suggestion(
        self, project_id: str, session_id: str, context_id: str
    ) -> bool:
        """
        accept_suggestions 호출 (단일 맥락)

        Args:
            project_id: 프로젝트 ID
            session_id: suggest_contexts 세션 ID
            context_id: 수락할 맥락 ID

        Returns:
            성공 여부
        """
        try:
            reference_history = _get_reference_history(project_id)
            if not reference_history:
                return False

            result = reference_history.accept_suggestions(
                session_id=session_id,
                contexts_used=[context_id],
                project_id=project_id
            )

            return result.get("success", False)

        except Exception as e:
            logger.error(f"[AUTO_TRIGGER] accept_suggestions 실패: {e}")
            return False

    def _auto_process_suggestions(
        self, project_id: str, suggestions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Threshold 기반 자동 처리

        Threshold 규칙:
        - confidence >= 0.80: 자동 수락
        - 0.50 <= confidence < 0.80: AI 확인 필요
        - confidence < 0.50: 자동 거부

        Args:
            project_id: 프로젝트 ID
            suggestions: suggest_contexts 결과

        Returns:
            {
                "auto_accepted": [...],  # 자동 수락된 맥락
                "need_ai_review": [...],  # AI 확인 필요
                "auto_rejected": [...],  # 자동 거부
                "session_id": "..."
            }
        """
        auto_accepted = []
        need_ai_review = []
        auto_rejected = []
        session_id = suggestions.get("session_id")

        contexts = suggestions.get("contexts", [])

        for context in contexts:
            confidence = context.get("confidence", 0.0)
            context_id = context.get("context_id")

            if confidence >= 0.80:
                # Threshold 1: 자동 수락
                auto_accepted.append(context)
                logger.info(
                    f"[AUTO_TRIGGER] 자동 수락: {context_id} "
                    f"(confidence {confidence:.0%})"
                )

                # accept_suggestions 즉시 호출
                if session_id and context_id:
                    self._accept_suggestion(project_id, session_id, context_id)

            elif confidence >= 0.50:
                # Threshold 2: AI 확인 필요
                need_ai_review.append(context)
                logger.info(
                    f"[AUTO_TRIGGER] AI 확인 필요: {context_id} "
                    f"(confidence {confidence:.0%})"
                )

            else:
                # Threshold 3: 자동 거부
                auto_rejected.append(context)
                logger.info(
                    f"[AUTO_TRIGGER] 자동 거부: {context_id} "
                    f"(confidence {confidence:.0%})"
                )

        return {
            "auto_accepted": auto_accepted,
            "need_ai_review": need_ai_review,
            "auto_rejected": auto_rejected,
            "session_id": session_id,
        }

    def _format_injection_message(self, processed: Dict[str, Any]) -> str:
        """
        강력한 주입 메시지 생성

        Args:
            processed: _auto_process_suggestions 결과

        Returns:
            AI에게 주입할 메시지
        """
        lines = [
            "=" * 60,
            "[CORTEX 자동 실행 보고 - 필수 확인]",
            "=" * 60,
            "",
        ]

        # 자동 수락
        if processed["auto_accepted"]:
            lines.append("✅ 자동 완료:")
            lines.append("  - suggest_contexts 실행됨")
            for ctx in processed["auto_accepted"]:
                confidence = ctx.get("confidence", 0.0)
                context_id = ctx.get("context_id", "unknown")
                lines.append(
                    f"  - {context_id} (신뢰도 {confidence:.0%}) 자동 로드"
                )
            lines.append("")

        # AI 확인 필요
        if processed["need_ai_review"]:
            lines.append("⚠️  AI 확인 필요:")
            for ctx in processed["need_ai_review"]:
                confidence = ctx.get("confidence", 0.0)
                context_id = ctx.get("context_id", "unknown")
                lines.append(f"  - {context_id} (신뢰도 {confidence:.0%})")

            session_id = processed["session_id"]
            lines.append(
                f"    → 필요: accept_suggestions('{session_id}', [...])"
            )
            lines.append(
                f"    → 불필요: reject_suggestions('{session_id}', 'reason')"
            )
            lines.append("")

        # 자동 거부
        if processed["auto_rejected"]:
            lines.append("❌ 자동 제외:")
            for ctx in processed["auto_rejected"]:
                confidence = ctx.get("confidence", 0.0)
                context_id = ctx.get("context_id", "unknown")
                lines.append(f"  - {context_id} (신뢰도 {confidence:.0%})")
            lines.append("")

        lines.extend([
            "=" * 60,
            "⚠️  출처 책임: 자동 로드된 맥락을 참조한 경우 출처를 명시하세요.",
            "=" * 60,
        ])

        return "\n".join(lines)

    def pre_hook(
        self, tool_name: str, arguments: dict, project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pre-Hook: 도구 실행 전 강제 실행

        Returns:
            강제 로드된 데이터 (claude_core, summary 등)
        """
        result = {}

        try:
            # 1. 세션 첫 호출 → CLAUDE_CORE + summary 강제 로드
            if project_id:
                session_id = self._generate_session_id(
                    project_id, arguments.get("branch_id", "main")
                )

                if self.cache.is_first_call(session_id):
                    logger.info("[AUTO_TRIGGER] 세션 첫 호출 감지 - CLAUDE_CORE 로드")

                    # CLAUDE_CORE.md 로드
                    core_content = self._read_claude_core()
                    if core_content:
                        result["claude_core_loaded"] = True
                        result["claude_core_size"] = len(core_content)
                        self.cache.set(session_id, "claude_core", core_content)

                        # CoT 프롬프트 생성
                        result["cot_prompt"] = self._generate_cot_prompt()

            # 2. 코딩 작업 → suggest_contexts 자동 호출 및 Threshold 처리
            if self._is_coding_work(tool_name) and project_id:
                logger.info(f"[AUTO_TRIGGER] 코딩 작업 감지: {tool_name}")
                result["coding_work_detected"] = True

                # 2.1. suggest_contexts 자동 호출
                query = self._generate_search_query(tool_name, arguments)
                suggestions = self._call_suggest_contexts(
                    project_id=project_id,
                    query=query,
                    branch_id=arguments.get("branch_id")
                )

                if suggestions and suggestions.get("success"):
                    # 2.2. Threshold 기반 자동 처리
                    processed = self._auto_process_suggestions(project_id, suggestions)

                    # 2.3. 강력한 메시지 생성
                    injection_message = self._format_injection_message(processed)

                    # 2.4. Phase 10.2: Pending 추가 (AI 확인 필요한 경우)
                    if processed.get("need_ai_review"):
                        session_id = processed.get("session_id")
                        if session_id:
                            self.cache.add_pending_suggestion(
                                session_id=session_id,
                                project_id=project_id,
                                suggestion_data=processed
                            )
                            logger.warning(
                                f"[AUTO_TRIGGER] ⚠️  Pending suggestion added: {session_id}\n"
                                f"AI MUST call accept_suggestions or reject_suggestions"
                            )

                    # 2.5. 결과 반환
                    result["auto_suggestions_processed"] = True
                    result["suggestions_data"] = processed
                    result["cortex_injection"] = injection_message
                else:
                    logger.warning("[AUTO_TRIGGER] suggest_contexts 결과 없음")
                    result["auto_suggestions_processed"] = False

        except Exception as e:
            logger.error(f"[AUTO_TRIGGER] Pre-hook failed: {e}")
            # Graceful degradation: Hook 실패해도 도구는 실행

        return result

    def post_hook(
        self, tool_name: str, tool_result: dict, project_id: Optional[str] = None
    ) -> dict:
        """
        Post-Hook: 도구 실행 후 강제 실행

        Returns:
            수정된 tool_result (hallucination_check 추가 등)
        """
        if not tool_result.get("success"):
            # 실패한 도구는 Hook 건너뛰기
            return tool_result

        try:
            # 1. 코딩 작업 → Phase 9 검증 강제 (verified 무시)
            if self._is_coding_work(tool_name):
                logger.info(f"[AUTO_TRIGGER] 코딩 작업 검증 필요: {tool_name}")

                # Phase 9 할루시네이션 검증 필요 플래그 설정
                # cortex_tools.py에서 verify_response 호출 권장
                tool_result["auto_verification_triggered"] = True
                tool_result["verification_required"] = True
                tool_result["verification_reason"] = f"코딩 작업 완료: {tool_name}"

            # 2. 비-MANDATORY 도구 → update_memory 강제 (Reminder만 우선 제공)
            if tool_name not in self.MANDATORY_TOOLS:
                reminder = self._get_update_memory_reminder(tool_name, tool_result)
                if reminder:
                    tool_result["auto_trigger_reminder"] = reminder

        except Exception as e:
            logger.error(f"[AUTO_TRIGGER] Post-hook failed: {e}")
            # Graceful degradation

        return tool_result

    def _generate_cot_prompt(self) -> str:
        """
        Chain-of-Thought 프롬프트 생성 (현재는 cortex_protocols.md에서 관리)

        Note: 이 메서드는 하위 호환성을 위해 유지되지만,
        실제 CoT 프롬프트는 cortex_protocols.md에서 제공됨
        """
        return "[CoT Prompt managed by cortex_protocols.md]"

    def _get_update_memory_reminder(self, tool_name: str, result: dict) -> Optional[str]:
        """update_memory 호출 리마인더 생성"""
        if tool_name in self.MANDATORY_TOOLS or not result.get("success"):
            return None

        reminder = (
            f"[CORTEX AUTO-TRIGGER REMINDER]\n"
            f"'{tool_name}' 도구 실행이 완료되었습니다.\n"
            f"CORTEX_MEMORY_PROTOCOL에 따라 다음 작업을 권장합니다:\n"
            f"  - update_memory: 방금 작업 내용을 맥락에 기록\n"
            f"  - record_reference: 사용한 맥락 조합을 참조 이력에 기록\n"
        )

        return reminder


# 싱글톤 인스턴스
_auto_trigger_instance: Optional[AutoTrigger] = None


def get_auto_trigger() -> AutoTrigger:
    """AutoTrigger 싱글톤 인스턴스 반환"""
    global _auto_trigger_instance
    if _auto_trigger_instance is None:
        _auto_trigger_instance = AutoTrigger()
    return _auto_trigger_instance
