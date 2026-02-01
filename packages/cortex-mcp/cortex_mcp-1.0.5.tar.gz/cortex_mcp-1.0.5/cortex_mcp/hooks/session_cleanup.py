#!/usr/bin/env python3
"""
SessionEnd Hook - 세션 종료 시 정리 (P0 자동화 개선)

Claude Code 세션이 종료될 때 호출되어:
1. 미완료 메모리 업데이트 처리 (강제 실행 - 4-tier fallback)
2. Reference History 기록 (자동)
3. 세션 통계 저장
4. 임시 데이터 정리

변경 사항 (P0 Phase 1):
- output_tool_suggestion() 제거 (제안 방식 제거)
- MemoryManager().update_memory() 직접 호출 (강제 실행)
- ReferenceHistory().record_reference() 자동 호출
- 4-tier Graceful Degradation 적용
"""

import json
import logging
import sys
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cortex_mcp.hooks.runner import (
    CORTEX_DIR,
    LOG_DIR,
    HookContext,
    log_hook_activity,
)

logger = logging.getLogger(__name__)


def calculate_session_duration(start_time: str) -> int:
    """세션 지속 시간 계산 (초)"""
    try:
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = datetime.utcnow()
        return int((end - start.replace(tzinfo=None)).total_seconds())
    except Exception:
        return 0


def save_session_summary(ctx: HookContext):
    """세션 요약 저장"""
    session_file = LOG_DIR / "sessions.jsonl"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    session_id = ctx.state.get("session_id", "unknown")
    session_start = ctx.state.get("last_activity")

    duration = 0
    if session_start:
        duration = calculate_session_duration(session_start)

    entry = {
        "session_id": session_id,
        "project_id": ctx.project_id,
        "project_path": ctx.project_path,
        "start_time": session_start,
        "end_time": datetime.utcnow().isoformat(),
        "duration_seconds": duration,
        "active_branch": ctx.state.get("active_branch"),
        "contexts_loaded": ctx.state.get("context_loaded", []),
        "current_topic": ctx.state.get("current_topic"),
    }

    try:
        with open(session_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def cleanup_temp_files():
    """임시 파일 정리"""
    temp_dir = CORTEX_DIR / "temp"
    if temp_dir.exists():
        try:
            import shutil

            # 24시간 이상 된 임시 파일만 삭제
            for item in temp_dir.iterdir():
                if item.is_file():
                    age = datetime.now().timestamp() - item.stat().st_mtime
                    if age > 86400:  # 24시간
                        item.unlink()
        except Exception:
            pass


def queue_for_auto_save(ctx: HookContext, content: str):
    """
    Auto-Saver Queue에 추가 (Tier 3 Fallback)

    Args:
        ctx: Hook Context
        content: 저장할 내용
    """
    try:
        queue_dir = Path.home() / ".cortex" / "queue"
        queue_dir.mkdir(parents=True, exist_ok=True)

        queue_file = queue_dir / f"pending_{ctx.project_id}_{datetime.utcnow().timestamp()}.json"

        queue_data = {
            "project_id": ctx.project_id,
            "branch_id": ctx.active_branch,
            "content": content,
            "role": "assistant",
            "timestamp": datetime.utcnow().isoformat(),
            "retry_count": 0,
            "source": "session_end",
        }

        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, ensure_ascii=False, indent=2)

        logger.info(f"[SESSION_END] Auto-Save Queue에 추가됨: {queue_file.name}")
    except Exception as e:
        logger.error(f"[SESSION_END] Queue 추가 실패: {e}")


def update_memory_with_fallback(ctx: HookContext, content: str):
    """
    4-tier Fallback으로 메모리 업데이트 (강제 실행)

    Fallback 순서:
    1. Full 기능 (Phase 9 검증 포함)
    2. 검증 없이 저장 (verified=True)
    3. Queue에 추가 (Auto-Save)
    4. 로그만 기록 (완전 실패)

    Args:
        ctx: Hook Context
        content: 저장할 내용
    """
    try:
        # Lazy import to avoid circular dependency
        from cortex_mcp.core.memory_manager import MemoryManager

        memory_manager = MemoryManager()

        # ================================================================
        # Tier 1: Full 기능 (Phase 9 검증 포함)
        # ================================================================
        try:
            logger.info("[SESSION_END] Tier 1 시도: Full 기능 (Phase 9 검증 포함)")

            result = memory_manager.update_memory(
                project_id=ctx.project_id,
                branch_id=ctx.active_branch,
                content=content,
                role="assistant",
                verified=False,  # Phase 9 검증 활성화
            )

            if result.get("success"):
                logger.info("[SESSION_END] Tier 1 성공 (검증 포함)")

                # Grounding Score 확인
                grounding_score = result.get("grounding_score")
                if grounding_score is not None:
                    logger.info(f"[SESSION_END] Grounding Score: {grounding_score:.2f}")

                return result
            else:
                logger.warning(f"[SESSION_END] Tier 1 실패: {result.get('error', 'Unknown error')}")
                raise Exception(result.get("error", "Unknown error"))

        except Exception as e:
            error_name = type(e).__name__
            logger.warning(f"[SESSION_END] Tier 1 실패: {error_name}: {str(e)}")

            # ================================================================
            # Tier 2: 검증 없이 저장 (verified=True)
            # ================================================================
            try:
                logger.info("[SESSION_END] Tier 2 시도: 검증 건너뛰기 (verified=True)")

                result = memory_manager.update_memory(
                    project_id=ctx.project_id,
                    branch_id=ctx.active_branch,
                    content=content,
                    role="assistant",
                    verified=True,  # Phase 9 검증 건너뛰기
                )

                if result.get("success"):
                    logger.info("[SESSION_END] Tier 2 성공 (검증 없이 저장)")
                    return result
                else:
                    logger.warning(f"[SESSION_END] Tier 2 실패: {result.get('error', 'Unknown error')}")
                    raise Exception(result.get("error", "Unknown error"))

            except Exception as e2:
                logger.error(f"[SESSION_END] Tier 2 실패: {type(e2).__name__}: {str(e2)}")

                # ================================================================
                # Tier 3: Queue에 추가 (Auto-Save)
                # ================================================================
                try:
                    logger.info("[SESSION_END] Tier 3 시도: Auto-Save Queue에 추가")
                    queue_for_auto_save(ctx, content)

                    logger.info("[SESSION_END] Tier 3 성공 (Queue 추가)")
                    return {"success": True, "queued": True}

                except Exception as e3:
                    logger.error(f"[SESSION_END] Tier 3 실패: {type(e3).__name__}: {str(e3)}")

                    # ================================================================
                    # Tier 4: 로그만 기록 (완전 실패)
                    # ================================================================
                    logger.error("[SESSION_END] 모든 Tier 실패 - 로그만 기록")
                    logger.error(f"[SESSION_END] 내용 (처음 200자): {content[:200]}")
                    return {"success": False, "error": "All tiers failed"}

    except Exception as outer_e:
        logger.error(f"[SESSION_END] 외부 예외 발생: {type(outer_e).__name__}: {str(outer_e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(outer_e)}


def record_automation_feedback(ctx: HookContext):
    """
    Automation Manager 피드백 자동 기록 (Phase 2 - P0 Medium)

    세션 동안 발생한 자동화 작업에 대한 사용자 피드백을 감지하고 기록

    Args:
        ctx: Hook Context
    """
    try:
        # 세션 중 발생한 피드백 이벤트 수집
        feedback_events = ctx.state.get("automation_feedback", [])

        if not feedback_events:
            logger.info("[SESSION_END] Automation 피드백 없음 (스킵)")
            return

        # Lazy import
        from cortex_mcp.core.automation_manager import record_automation_feedback

        for event in feedback_events:
            try:
                action_type = event.get("action_type")
                feedback = event.get("feedback")
                action_id = event.get("action_id")

                if not action_type or not feedback:
                    continue

                # 피드백 기록
                result = record_automation_feedback(
                    project_id=ctx.project_id,
                    action_type=action_type,
                    feedback=feedback,
                    action_id=action_id
                )

                if result.get("success"):
                    logger.info(f"[SESSION_END] Automation 피드백 기록: {action_type} -> {feedback}")

                    # 모드 전환 발생 시 로그
                    if result.get("mode_switched"):
                        logger.warning(
                            f"[SESSION_END] Plan 모드 전환 발생: {result.get('new_mode')}"
                        )
                else:
                    logger.warning(f"[SESSION_END] 피드백 기록 실패: {result.get('error')}")

            except Exception as e:
                logger.warning(f"[SESSION_END] 피드백 기록 중 예외 (무시): {e}")

        logger.info(f"[SESSION_END] Automation 피드백 처리 완료: {len(feedback_events)}개")

    except Exception as e:
        logger.warning(f"[SESSION_END] Automation 피드백 처리 중 예외 (무시): {e}")


def record_reference_history(ctx: HookContext):
    """
    Reference History 자동 기록

    Args:
        ctx: Hook Context
    """
    try:
        # 사용된 맥락 ID 수집
        contexts_used = ctx.state.get("context_loaded", [])
        current_topic = ctx.state.get("current_topic", "")

        if not contexts_used or not ctx.active_branch:
            logger.info("[SESSION_END] Reference History 기록 스킵 (맥락 없음)")
            return

        # Lazy import
        from cortex_mcp.core.reference_history import get_reference_history

        ref_history = get_reference_history(project_id=ctx.project_id)

        # 키워드 추출
        keywords = current_topic.split()[:5] if current_topic else ["session_end"]

        # Reference History 기록
        result = ref_history.record_reference(
            task_keywords=keywords,
            contexts_used=contexts_used,
            branch_id=ctx.active_branch,
            query=f"Session ended: {current_topic}",
            project_id=ctx.project_id,
        )

        if result.get("success"):
            logger.info(f"[SESSION_END] Reference History 기록 완료: {len(contexts_used)}개 맥락")
        else:
            logger.warning(f"[SESSION_END] Reference History 기록 실패: {result.get('error')}")

    except Exception as e:
        logger.warning(f"[SESSION_END] Reference History 기록 중 예외 (무시): {e}")


def main():
    """SessionEnd Hook 메인 로직 (P0 자동화 개선)"""
    ctx = HookContext()

    ctx.log(
        "SessionEnd",
        "session_ending",
        {"session_id": ctx.state.get("session_id"), "project_id": ctx.project_id},
    )

    # ====================================================================
    # P0-1: 미완료 메모리 업데이트 처리 (강제 실행 - 4-tier fallback)
    # ====================================================================
    if ctx.state.get("pending_memory_update") and ctx.active_branch:
        logger.info("[SESSION_END] 미완료 메모리 업데이트 강제 실행")

        content = f"[Session ended at {datetime.utcnow().isoformat()}]"

        # 백그라운드 스레드로 실행 (세션 종료를 차단하지 않음)
        update_thread = threading.Thread(
            target=update_memory_with_fallback,
            args=(ctx, content),
            daemon=True,
            name="SessionEndMemoryUpdate"
        )
        update_thread.start()

        ctx.log("SessionEnd", "pending_memory_update_forced", {"branch_id": ctx.active_branch})

    # ====================================================================
    # Phase 2 - P0 Medium: Automation 피드백 자동 기록
    # ====================================================================
    logger.info("[SESSION_END] Automation 피드백 자동 기록")

    feedback_thread = threading.Thread(
        target=record_automation_feedback,
        args=(ctx,),
        daemon=True,
        name="SessionEndAutomationFeedback"
    )
    feedback_thread.start()

    # ====================================================================
    # P0-2: Reference History 자동 기록
    # ====================================================================
    if ctx.active_branch:
        logger.info("[SESSION_END] Reference History 자동 기록")

        # 백그라운드 스레드로 실행
        ref_thread = threading.Thread(
            target=record_reference_history,
            args=(ctx,),
            daemon=True,
            name="SessionEndReferenceHistory"
        )
        ref_thread.start()

    # 세션 요약 저장
    save_session_summary(ctx)

    # 임시 파일 정리
    cleanup_temp_files()

    # 상태 초기화 (다음 세션을 위해)
    ctx.state = {
        "session_id": None,
        "project_id": None,
        "active_branch": None,
        "initialized": False,
        "last_activity": None,
        "context_loaded": [],
        "pending_memory_update": False,
    }
    ctx.save()

    ctx.log("SessionEnd", "session_ended", {"cleanup_completed": True})


if __name__ == "__main__":
    main()
