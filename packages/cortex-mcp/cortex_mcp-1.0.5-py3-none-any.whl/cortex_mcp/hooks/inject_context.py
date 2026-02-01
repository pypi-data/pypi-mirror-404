#!/usr/bin/env python3
"""
UserPromptSubmit Hook - 프롬프트 제출 시 맥락 자동 주입

사용자가 프롬프트를 제출할 때 호출되어:
1. Reference History 기반 맥락 추천
2. 관련 맥락 자동 로드
3. System Prompt에 맥락 주입
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cortex_mcp.hooks.runner import (
    HookContext,
    generate_mcp_tool_call,
    log_hook_activity,
    output_system_message,
    output_tool_suggestion,
)


def extract_keywords(prompt: str) -> list:
    """프롬프트에서 키워드 추출"""
    # 간단한 키워드 추출 (불용어 제거)
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "and",
        "or",
        "but",
        "if",
        "then",
        "else",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "also",
        "now",
        "here",
        "there",
        # 한국어 불용어
        "이",
        "그",
        "저",
        "것",
        "수",
        "등",
        "및",
        "를",
        "을",
        "에",
        "의",
        "가",
        "은",
        "는",
        "로",
        "으로",
        "와",
        "과",
        "도",
        "만",
        "에서",
        "까지",
        "부터",
        "처럼",
        "같이",
        "하다",
        "되다",
        "있다",
        "없다",
        "해주",
        "해줘",
        "좀",
        "좀",
        "그리고",
        "하지만",
        "그러나",
    }

    # 단어 추출 (영문, 한글)
    words = re.findall(r"[a-zA-Z]+|[가-힣]+", prompt.lower())

    # 불용어 제거 및 2글자 이상만
    keywords = [w for w in words if w not in stopwords and len(w) >= 2]

    # 상위 5개만 반환
    return keywords[:5]


def detect_topic_change(prompt: str, previous_topic: str) -> bool:
    """주제 전환 감지"""
    # 주제 전환 키워드
    change_keywords = [
        "새로운",
        "다른",
        "새 프로젝트",
        "새 작업",
        "다른 주제",
        "전환",
        "변경",
        "시작하자",
        "새로 시작",
        "new project",
        "different",
        "switch to",
        "change topic",
        "let's start",
        "begin new",
    ]

    prompt_lower = prompt.lower()
    for keyword in change_keywords:
        if keyword in prompt_lower:
            return True

    return False


def write_cortex_prompt(ctx: HookContext, user_prompt: str, keywords: list):
    """
    프로젝트별 cortex_prompt.md 작성 (강제 실행 - AI 독립)

    SessionEnd Hook 패턴과 동일하게 Python이 직접 실행
    """
    try:
        # 프로젝트 루트 경로 (프로젝트별로 분리)
        project_root = Path(ctx.project_path)
        cortex_prompt = project_root / "cortex_prompt.md"

        # 1. 현재 브랜치 요약 로드
        from cortex_mcp.core.memory_manager import MemoryManager

        memory_mgr = MemoryManager()
        summary_result = memory_mgr.get_active_summary(
            project_id=ctx.project_id,
            branch_id=ctx.active_branch
        )

        current_summary = summary_result.get("summary", "")

        # 2. Reference History 기반 맥락 추천
        from cortex_mcp.core.reference_history import get_reference_history

        ref_history = get_reference_history(project_id=ctx.project_id)
        suggestions = ref_history.suggest_contexts(
            query=user_prompt[:200],
            branch_id=ctx.active_branch,
            top_k=5
        )

        # 3. 신뢰도 기반 자동 로드
        auto_loaded = []

        if suggestions.get("success") and suggestions.get("suggestions"):
            suggestion_list = suggestions["suggestions"]

            # 3-Tier 로딩 전략
            high_conf = [s for s in suggestion_list if s.get("confidence", 0) >= 0.8]
            medium_conf = [s for s in suggestion_list if 0.5 <= s.get("confidence", 0) < 0.8]

            # Tier 1: >= 0.8 신뢰도 → 3개 자동 로드
            if len(high_conf) >= 3:
                for suggestion in high_conf[:3]:
                    context_id = suggestion.get("context_id")
                    if context_id:
                        auto_loaded.append({
                            "context_id": context_id,
                            "confidence": suggestion.get("confidence", 0),
                            "title": suggestion.get("title", "")
                        })

            # Tier 2: 0.5-0.8 → 1개만 로드
            elif len(medium_conf) >= 1:
                suggestion = medium_conf[0]
                context_id = suggestion.get("context_id")
                if context_id:
                    auto_loaded.append({
                        "context_id": context_id,
                        "confidence": suggestion.get("confidence", 0),
                        "title": suggestion.get("title", "")
                    })

            # Tier 3: < 0.5 → 현재 브랜치만

        # 4. 프로젝트/브랜치 목표 로드
        branch_goal = ctx.state.get("branch_goal", "")
        project_goal = ctx.state.get("project_goal", "")

        # 5. 작업 진행 상황 (최근 변경 이력)
        recent_changes = ctx.state.get("recent_changes", [])

        # 6. cortex_prompt.md 작성
        from datetime import datetime

        content_parts = [
            "# CORTEX CONTEXT (Auto-managed)\n",
            f"\nLast updated: {datetime.utcnow().isoformat()}Z\n",
            "\n---\n",
            "\n## 1. Project Goal (프로젝트 목표)\n",
            f"\n{project_goal if project_goal else '(목표 설정 필요 - 작업 완료 후 update_memory에 기록)'}\n",
            "\n---\n",
            "\n## 2. Branch Goal (브랜치 목표)\n",
            f"\n{branch_goal if branch_goal else '(목표 설정 필요 - 작업 완료 후 update_memory에 기록)'}\n",
            "\n---\n",
            "\n## 3. Active Branch Summary (현재 브랜치 요약)\n",
            f"\n**Topic**: {ctx.state.get('current_topic', 'N/A')}\n",
            f"\n**Branch ID**: {ctx.active_branch[:8] if ctx.active_branch else 'N/A'}\n",
            f"\n**Summary**:\n{current_summary[:1000] if current_summary else '(No summary yet)'}\n",
            "\n---\n",
            "\n## 4. Context Refresh (맥락 리프레시)\n",
            "\n### 최근 변경 이력:\n",
        ]

        if recent_changes:
            for change in recent_changes[-5:]:  # 최근 5개만
                content_parts.append(f"\n- {change}\n")
        else:
            content_parts.append("\n(변경 이력 없음)\n")

        content_parts.append("\n---\n")
        content_parts.append("\n## 5. Reference History (참조 이력)\n")

        if auto_loaded:
            content_parts.append("\n### 자동으로 로드된 관련 맥락:\n\n")
            for loaded in auto_loaded:
                content_parts.append(
                    f"- **{loaded['title']}** (confidence: {loaded['confidence']:.2f})\n"
                )
        else:
            content_parts.append("\n(현재 브랜치만 활성)\n")

        content_parts.extend([
            "\n---\n",
            "\n## Instructions\n",
            "\nCortex가 자동으로 관련 맥락을 로드했습니다.\n",
            "프로젝트 전환 시에도 맥락이 유지됩니다.\n",
            "\nNo manual editing needed.\n"
        ])

        content = "".join(content_parts)

        # 5. 파일 쓰기
        cortex_prompt.write_text(content, encoding='utf-8')

        ctx.log(
            "UserPromptSubmit",
            "cortex_prompt_written",
            {
                "auto_loaded_count": len(auto_loaded),
                "file_path": str(cortex_prompt)
            }
        )

        return True

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[UserPromptSubmit] cortex_prompt 작성 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """UserPromptSubmit Hook 메인 로직"""
    ctx = HookContext()

    # stdin에서 프롬프트 정보 읽기
    stdin_data = ctx.stdin_context
    user_prompt = stdin_data.get("prompt", "")

    if not user_prompt:
        # 프롬프트 없으면 패스
        return

    ctx.log(
        "UserPromptSubmit",
        "prompt_received",
        {"prompt_length": len(user_prompt), "project_id": ctx.project_id},
    )

    if not ctx.is_initialized:
        # 초기화 안됨 - SessionStart에서 처리하므로 패스
        return

    # 키워드 추출
    keywords = extract_keywords(user_prompt)

    # 주제 전환 감지
    previous_topic = ctx.state.get("current_topic", "")
    if detect_topic_change(user_prompt, previous_topic):
        # 새 브랜치 생성 제안
        ctx.log(
            "UserPromptSubmit",
            "topic_change_detected",
            {"previous_topic": previous_topic, "new_prompt": user_prompt[:100]},
        )

        branch_message = """[CORTEX_TOPIC_CHANGE_DETECTED]

주제 전환이 감지되었습니다.
새로운 브랜치를 생성하여 맥락을 분리하는 것이 좋습니다.

"[새 주제명] 브랜치를 생성합니다. 조정이 필요하면 알려주세요."
형식으로 사용자에게 보고하세요."""

        output_system_message(branch_message)

        tool_call = generate_mcp_tool_call(
            "create_branch",
            {
                "project_id": ctx.project_id,
                "branch_topic": " ".join(keywords) if keywords else "new_topic",
            },
        )
        output_tool_suggestion([tool_call])
        return

    # 강제 실행: 프로젝트별 cortex_prompt.md 작성
    # (AI-dependent 제안 방식 제거, Python 직접 실행)
    active_branch = ctx.active_branch
    if active_branch and keywords:
        # write_cortex_prompt 직접 실행 (SessionEnd Hook 패턴)
        success = write_cortex_prompt(ctx, user_prompt, keywords)

        if success:
            ctx.log(
                "UserPromptSubmit",
                "cortex_prompt_auto_updated",
                {"keywords": keywords, "branch_id": active_branch},
            )
        else:
            ctx.log(
                "UserPromptSubmit",
                "cortex_prompt_update_failed",
                {"keywords": keywords, "branch_id": active_branch},
            )

    # 현재 토픽 업데이트
    if keywords:
        ctx.state["current_topic"] = " ".join(keywords)

    # 메모리 업데이트 플래그 설정
    ctx.state["pending_memory_update"] = True
    ctx.save()


if __name__ == "__main__":
    main()
