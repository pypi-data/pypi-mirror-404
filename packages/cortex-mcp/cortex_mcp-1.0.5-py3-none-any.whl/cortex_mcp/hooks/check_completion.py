#!/usr/bin/env python3
"""
Stop Hook - AI 응답 완료 시 메모리 업데이트 (비동기 강제 실행)

AI가 응답을 완료했을 때 호출되어:
1. 대화 내용 메모리 업데이트 (백그라운드 스레드)
2. Reference History 기록
3. 작업 완료 확인

변경 사항 (v2.0):
- output_tool_suggestion() 제거 (제안 방식 제거)
- threading.Thread로 memory_manager.update_memory() 직접 호출 (비동기 강제 실행)
- 3단계 Graceful Degradation: 검증 → 스킵 → Queue → 로그만
- 사용자 응답은 절대 차단하지 않음 (백그라운드 실행)
"""

import json
import logging
import sys
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cortex_mcp.hooks.runner import (
    HookContext,
    log_hook_activity,
)

logger = logging.getLogger(__name__)


def extract_conversation_summary(assistant_response: str) -> str:
    """AI 응답에서 핵심 내용 추출"""
    if not assistant_response:
        return ""

    # 첫 500자 + 마지막 200자로 요약 생성
    if len(assistant_response) > 700:
        summary = assistant_response[:500] + "\n...\n" + assistant_response[-200:]
    else:
        summary = assistant_response

    return summary


def should_update_memory_forced(ctx: HookContext, response_text: str) -> bool:
    """
    메모리 업데이트 필요 여부 판단 (강화된 스킵 조건)

    Args:
        ctx: Hook Context
        response_text: AI 응답 텍스트

    Returns:
        True: 업데이트 필요, False: 스킵
    """
    # 응답이 너무 짧으면 스킵 (100자 미만)
    if len(response_text) < 100:
        logger.info(f"[MEMORY_SKIP] 응답 길이 부족: {len(response_text)}자 < 100자")
        return False

    # 초기화 안됨
    if not ctx.is_initialized:
        logger.info("[MEMORY_SKIP] Cortex 초기화되지 않음")
        return False

    # 활성 브랜치 없음
    if not ctx.active_branch:
        logger.info("[MEMORY_SKIP] 활성 브랜치 없음")
        return False

    # 단순 응답 스킵
    simple_responses = [
        "ok", "네", "yes", "알겠습니다", "확인",
        "good", "understood", "got it", "알겠어요",
        "오케이", "ㅇㅋ", "ㄱㅅ", "감사합니다", "thank you",
        "thanks", "done", "완료"
    ]
    response_lower = response_text.lower().strip()

    # 응답 전체가 단순 응답인 경우
    if any(resp == response_lower for resp in simple_responses):
        logger.info(f"[MEMORY_SKIP] 단순 응답 감지: {response_lower}")
        return False

    # 응답이 단순 응답만으로 구성된 경우 (10단어 미만 + 단순 응답 포함)
    word_count = len(response_text.split())
    if word_count < 10 and any(resp in response_lower for resp in simple_responses):
        logger.info(f"[MEMORY_SKIP] 단순 짧은 응답: {word_count}단어, 내용: {response_text[:50]}")
        return False

    return True


def queue_for_auto_save(ctx: HookContext, content: str):
    """
    Auto-Saver Queue에 추가 (파일 I/O 실패 시 Fallback)

    Args:
        ctx: Hook Context
        content: 저장할 내용
    """
    try:
        # Auto-Saver Queue 파일 경로
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
        }

        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, ensure_ascii=False, indent=2)

        logger.info(f"[AUTO_SAVE_QUEUE] ✅ Queue에 추가됨: {queue_file.name}")
    except Exception as e:
        logger.error(f"[AUTO_SAVE_QUEUE] Queue 추가 실패: {e}")


def update_memory_with_fallback(
    ctx: HookContext,
    response_text: str,
    tool_calls_made: list
):
    """
    3단계 Fallback으로 메모리 업데이트 (백그라운드 스레드)

    Fallback 순서:
    1. Full 기능 (Phase 9 검증 포함)
    2. 검증 없이 저장 (verified=True)
    3. Queue에 추가 (Auto-Save)
    4. 로그만 기록 (완전 실패)

    Args:
        ctx: Hook Context
        response_text: AI 응답 텍스트
        tool_calls_made: 이번 턴에서 호출된 도구 목록
    """
    try:
        # Lazy import to avoid circular dependency
        from cortex_mcp.core.memory_manager import MemoryManager

        memory_manager = MemoryManager()

        # 대화 요약 생성
        conversation_summary = extract_conversation_summary(response_text)

        # ================================================================
        # Tier 1: Full 기능 (Phase 9 검증 포함)
        # ================================================================
        try:
            logger.info("[MEMORY_UPDATE] Tier 1 시도: Full 기능 (Phase 9 검증 포함)")

            result = memory_manager.update_memory(
                project_id=ctx.project_id,
                branch_id=ctx.active_branch,
                content=conversation_summary,
                role="assistant",
                verified=False,  # Phase 9 검증 활성화
            )

            if result.get("success"):
                logger.info("[MEMORY_UPDATE] ✅ Tier 1 성공 (검증 포함)")

                # Grounding Score 확인
                grounding_score = result.get("grounding_score")
                if grounding_score is not None:
                    logger.info(f"[MEMORY_UPDATE] Grounding Score: {grounding_score:.2f}")

                # Reference History 기록 (선택적)
                _record_reference_history(ctx, tool_calls_made, memory_manager)

                return result
            else:
                logger.warning(f"[MEMORY_UPDATE] Tier 1 실패: {result.get('error', 'Unknown error')}")
                raise Exception(result.get("error", "Unknown error"))

        except Exception as e:
            error_name = type(e).__name__
            logger.warning(f"[MEMORY_UPDATE] Tier 1 실패: {error_name}: {str(e)}")

            # HallucinationDetectionError인 경우 Tier 2로 이동
            if "Hallucination" in error_name or "Verification" in error_name:
                logger.info("[MEMORY_UPDATE] 할루시네이션 검증 실패 감지 → Tier 2로 이동")

            # ================================================================
            # Tier 2: 검증 없이 저장 (verified=True)
            # ================================================================
            try:
                logger.info("[MEMORY_UPDATE] Tier 2 시도: 검증 건너뛰기 (verified=True)")

                result = memory_manager.update_memory(
                    project_id=ctx.project_id,
                    branch_id=ctx.active_branch,
                    content=conversation_summary,
                    role="assistant",
                    verified=True,  # Phase 9 검증 건너뛰기
                )

                if result.get("success"):
                    logger.info("[MEMORY_UPDATE] ✅ Tier 2 성공 (검증 없이 저장)")

                    # Reference History 기록 (선택적)
                    _record_reference_history(ctx, tool_calls_made, memory_manager)

                    return result
                else:
                    logger.warning(f"[MEMORY_UPDATE] Tier 2 실패: {result.get('error', 'Unknown error')}")
                    raise Exception(result.get("error", "Unknown error"))

            except Exception as e2:
                logger.error(f"[MEMORY_UPDATE] Tier 2 실패: {type(e2).__name__}: {str(e2)}")

                # ================================================================
                # Tier 3: Queue에 추가 (Auto-Save)
                # ================================================================
                try:
                    logger.info("[MEMORY_UPDATE] Tier 3 시도: Auto-Save Queue에 추가")
                    queue_for_auto_save(ctx, conversation_summary)

                    logger.info("[MEMORY_UPDATE] ✅ Tier 3 성공 (Queue 추가)")
                    return {"success": True, "queued": True}

                except Exception as e3:
                    logger.error(f"[MEMORY_UPDATE] Tier 3 실패: {type(e3).__name__}: {str(e3)}")

                    # ================================================================
                    # Tier 4: 로그만 기록 (완전 실패)
                    # ================================================================
                    logger.error("[MEMORY_UPDATE] ❌ 모든 Tier 실패 - 로그만 기록")
                    logger.error(f"[MEMORY_UPDATE] 원본 응답 (처음 200자): {response_text[:200]}")
                    return {"success": False, "error": "All tiers failed"}

    except Exception as outer_e:
        logger.error(f"[MEMORY_UPDATE] ❌ 외부 예외 발생: {type(outer_e).__name__}: {str(outer_e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(outer_e)}


def _record_reference_history(
    ctx: HookContext,
    tool_calls_made: list,
    memory_manager
):
    """
    Reference History 기록 (선택적)

    Args:
        ctx: Hook Context
        tool_calls_made: 이번 턴에서 호출된 도구 목록
        memory_manager: MemoryManager 인스턴스
    """
    try:
        # Cortex 도구 사용 이력 확인
        cortex_tools_used = [
            tc
            for tc in tool_calls_made
            if tc.get("tool_name", "").startswith("mcp__cortex-memory__")
        ]

        if cortex_tools_used:
            # 사용된 맥락 ID 수집
            contexts_used = []
            for tc in cortex_tools_used:
                tool_input = tc.get("tool_input", {})
                if "context_id" in tool_input:
                    contexts_used.append(tool_input["context_id"])

            if contexts_used:
                # Reference History 기록
                logger.info(f"[REFERENCE_HISTORY] {len(contexts_used)}개 맥락 사용 기록")

                memory_manager.record_reference(
                    project_id=ctx.project_id,
                    branch_id=ctx.active_branch,
                    task_keywords=ctx.state.get("current_topic", "").split()[:5],
                    contexts_used=contexts_used,
                )

                logger.info("[REFERENCE_HISTORY] ✅ 기록 완료")

    except Exception as e:
        logger.warning(f"[REFERENCE_HISTORY] 기록 실패 (무시): {e}")


def main():
    """
    Stop Hook 메인 로직 (비동기 강제 실행)
    """
    ctx = HookContext()

    # stdin에서 응답 정보 읽기
    stdin_data = ctx.stdin_context
    assistant_response = stdin_data.get("response", "")
    tool_calls_made = stdin_data.get("tool_calls", [])
    stop_reason = stdin_data.get("stop_reason", "")

    ctx.log(
        "Stop",
        "response_completed",
        {
            "response_length": len(assistant_response),
            "tool_calls_count": len(tool_calls_made),
            "stop_reason": stop_reason,
        },
    )

    # 메모리 업데이트 필요 여부 확인 (강화된 스킵 조건)
    if not should_update_memory_forced(ctx, assistant_response):
        logger.info("[MEMORY_SKIP] 메모리 업데이트 건너뜀")
        return

    active_branch = ctx.active_branch
    if not active_branch:
        logger.warning("[MEMORY_SKIP] 활성 브랜치 없음")
        return

    # ====================================================================
    # 비동기 강제 실행: threading.Thread로 백그라운드 실행
    # 사용자 응답은 절대 차단하지 않음
    # ====================================================================
    logger.info("[MEMORY_UPDATE] 백그라운드 스레드 시작 (daemon=True)")

    update_thread = threading.Thread(
        target=update_memory_with_fallback,
        args=(ctx, assistant_response, tool_calls_made),
        daemon=True,  # 메인 프로세스 종료 시 자동 종료
        name="MemoryUpdateThread"
    )

    update_thread.start()

    logger.info("[MEMORY_UPDATE] 백그라운드 스레드 시작됨 (사용자 응답 차단 없음)")

    # 상태 업데이트 (메인 스레드에서 즉시 실행)
    ctx.state["pending_memory_update"] = False
    ctx.state["last_response_time"] = datetime.utcnow().isoformat()
    ctx.save()


if __name__ == "__main__":
    main()
