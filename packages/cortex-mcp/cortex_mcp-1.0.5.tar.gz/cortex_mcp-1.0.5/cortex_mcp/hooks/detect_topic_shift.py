#!/usr/bin/env python3
"""
Stop Hook - 주제 전환 감지 및 자동 브랜치 생성

AI 응답 완료 시 호출되어:
1. 주제 전환 여부 감지 (4가지 신호 종합)
2. 확신도 >= 0.7 시 자동으로 create_branch 호출
3. 보고 스타일로 사용자에게 알림 출력

Zero-Effort 원칙 구현:
- 사용자 개입 없이 자동으로 브랜치 생성
- CORTEX_MEMORY_PROTOCOL v2.0 준수
"""

import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cortex_mcp.hooks.runner import HookContext

logger = logging.getLogger(__name__)

# Lazy import for heavy dependencies
_embedder = None
_cosine_similarity = None


def get_embedder():
    """Lazy load sentence-transformers embedder"""
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer

            _embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            logger.info("[TOPIC_SHIFT] Embedder loaded: paraphrase-multilingual-MiniLM-L12-v2")
        except Exception as e:
            logger.error(f"[TOPIC_SHIFT] Failed to load embedder: {e}")
            _embedder = None
    return _embedder


def get_cosine_similarity():
    """Lazy load sklearn cosine_similarity"""
    global _cosine_similarity
    if _cosine_similarity is None:
        try:
            from sklearn.metrics.pairwise import cosine_similarity

            _cosine_similarity = cosine_similarity
        except Exception as e:
            logger.error(f"[TOPIC_SHIFT] Failed to load cosine_similarity: {e}")
            _cosine_similarity = None
    return _cosine_similarity


# 주제 전환 키워드 (한국어 + 영어)
TOPIC_SHIFT_KEYWORDS = [
    # 한국어
    "다음으로", "새로운", "이제", "그럼", "다른", "별도로", "전환",
    "넘어가자", "넘어가요", "시작하자", "시작하죠", "바꾸자", "바꿔",
    "새 프로젝트", "다른 프로젝트", "별도 프로젝트",
    "브랜치 생성", "새 맥락", "맥락 분리",
    # 영어
    "next", "new", "different", "another", "switch", "change",
    "let's move", "move on", "start", "create branch", "new context",
    "change topic", "new topic", "switch to", "work on",
]


def calculate_semantic_similarity(text1: str, text2: str) -> Optional[float]:
    """
    두 텍스트의 시맨틱 유사도 계산 (코사인 유사도)

    Args:
        text1: 이전 대화
        text2: 현재 대화

    Returns:
        유사도 (0.0-1.0), 실패 시 None
    """
    try:
        embedder = get_embedder()
        cosine_similarity_fn = get_cosine_similarity()

        if embedder is None or cosine_similarity_fn is None:
            logger.warning("[TOPIC_SHIFT] Embedder not available, skipping semantic similarity")
            return None

        # 임베딩 생성
        emb1 = embedder.encode([text1])[0]
        emb2 = embedder.encode([text2])[0]

        # 코사인 유사도 계산
        similarity = cosine_similarity_fn([emb1], [emb2])[0][0]

        logger.info(f"[TOPIC_SHIFT] Semantic similarity: {similarity:.3f}")
        return float(similarity)

    except Exception as e:
        logger.error(f"[TOPIC_SHIFT] Semantic similarity calculation failed: {e}")
        return None


def check_keyword_signal(user_message: str, assistant_response: str) -> float:
    """
    주제 전환 키워드 감지

    Args:
        user_message: 사용자 메시지
        assistant_response: AI 응답

    Returns:
        신뢰도 (0.0-0.3)
    """
    combined_text = (user_message + " " + assistant_response).lower()

    # 키워드 매칭 개수
    matches = sum(1 for keyword in TOPIC_SHIFT_KEYWORDS if keyword in combined_text)

    if matches == 0:
        return 0.0
    elif matches == 1:
        return 0.1
    elif matches == 2:
        return 0.2
    else:  # 3개 이상
        return 0.3


def check_time_gap_signal(ctx: HookContext) -> float:
    """
    시간 간격 신호 감지

    Args:
        ctx: Hook Context

    Returns:
        신뢰도 (0.0-0.2)
    """
    try:
        last_message_time_str = ctx.state.get("last_message_time")
        if not last_message_time_str:
            # 첫 메시지
            return 0.0

        last_message_time = datetime.fromisoformat(last_message_time_str)
        current_time = datetime.utcnow()
        time_gap = (current_time - last_message_time).total_seconds()

        # 30분(1800초) 이상 경과
        if time_gap >= 1800:
            return 0.2
        # 15분(900초) 이상 경과
        elif time_gap >= 900:
            return 0.1
        else:
            return 0.0

    except Exception as e:
        logger.warning(f"[TOPIC_SHIFT] Time gap check failed: {e}")
        return 0.0


def check_file_context_change_signal(ctx: HookContext, tool_calls_made: List[Dict]) -> float:
    """
    파일 컨텍스트 변경 신호 감지

    Args:
        ctx: Hook Context
        tool_calls_made: 이번 턴에서 호출된 도구 목록

    Returns:
        신뢰도 (0.0-0.4)
    """
    try:
        # 현재 턴에서 접근한 파일 추출
        current_files: Set[str] = set()

        for tc in tool_calls_made:
            tool_name = tc.get("tool_name", "")
            tool_input = tc.get("tool_input", {})

            # Read, Edit, Write 도구에서 파일 경로 추출
            if "file_path" in tool_input:
                current_files.add(tool_input["file_path"])
            elif "path" in tool_input:
                current_files.add(tool_input["path"])

        # 이전 파일 집합
        previous_files_list = ctx.state.get("recent_files", [])
        previous_files: Set[str] = set(previous_files_list)

        # 파일이 없으면 판단 불가
        if not current_files or not previous_files:
            return 0.0

        # 교집합 계산
        intersection = current_files.intersection(previous_files)

        # 교집합이 없으면 완전히 다른 파일들
        if len(intersection) == 0:
            logger.info("[TOPIC_SHIFT] File context completely changed")
            return 0.4
        # 교집합이 20% 미만
        elif len(intersection) / len(previous_files) < 0.2:
            logger.info("[TOPIC_SHIFT] File context partially changed")
            return 0.2
        else:
            return 0.0

    except Exception as e:
        logger.warning(f"[TOPIC_SHIFT] File context check failed: {e}")
        return 0.0


def should_create_branch(
    ctx: HookContext,
    user_message: str,
    assistant_response: str,
    tool_calls_made: List[Dict]
) -> Tuple[bool, float, Dict[str, float]]:
    """
    브랜치 생성 필요 여부 판단

    Args:
        ctx: Hook Context
        user_message: 사용자 메시지
        assistant_response: AI 응답
        tool_calls_made: 이번 턴에서 호출된 도구 목록

    Returns:
        (브랜치 생성 필요 여부, 확신도, 신호별 점수)
    """
    signals: Dict[str, float] = {}

    # A. 시맨틱 유사도 (코사인)
    previous_conversation = ctx.state.get("last_conversation", "")
    current_conversation = user_message + " " + assistant_response

    if previous_conversation:
        similarity = calculate_semantic_similarity(previous_conversation, current_conversation)

        if similarity is not None:
            # 유사도가 낮을수록 전환 가능성 높음
            if similarity < 0.5:
                signals["semantic"] = 0.5 * (0.5 - similarity)  # 0.0 ~ 0.25
            else:
                signals["semantic"] = 0.0
        else:
            signals["semantic"] = 0.0
    else:
        # 첫 대화
        signals["semantic"] = 0.0

    # B. 키워드 기반
    signals["keyword"] = check_keyword_signal(user_message, assistant_response)

    # C. 시간 간격
    signals["time_gap"] = check_time_gap_signal(ctx)

    # D. 파일 컨텍스트 변경
    signals["file_context"] = check_file_context_change_signal(ctx, tool_calls_made)

    # 최종 확신도 계산
    total_confidence = sum(signals.values())

    logger.info(f"[TOPIC_SHIFT] Signals: {signals}")
    logger.info(f"[TOPIC_SHIFT] Total confidence: {total_confidence:.3f}")

    # 확신도 >= 0.7 시 브랜치 생성
    should_create = total_confidence >= 0.7

    return should_create, total_confidence, signals


def extract_topic(conversation_text: str) -> str:
    """
    대화 텍스트에서 주제 추출 (간단한 키워드 기반)

    Args:
        conversation_text: 대화 텍스트

    Returns:
        추출된 주제 (최대 50자)
    """
    try:
        # 간단한 방법: 첫 문장에서 명사구 추출
        # 더 정교한 방법은 spaCy/NER 사용 가능하지만 Zero-Trust 원칙상 로컬 처리

        # 첫 100자 추출
        first_part = conversation_text[:100].strip()

        # 특수문자 제거
        cleaned = "".join(c if c.isalnum() or c.isspace() else " " for c in first_part)

        # 공백 축소
        cleaned = " ".join(cleaned.split())

        # 최대 50자
        if len(cleaned) > 50:
            cleaned = cleaned[:50]

        # 한국어/영어 혼합 가능
        topic = cleaned if cleaned else "새_작업"

        return topic

    except Exception as e:
        logger.warning(f"[TOPIC_SHIFT] Topic extraction failed: {e}")
        return "새_작업"


def create_branch_auto(ctx: HookContext, topic: str, confidence: float, signals: Dict[str, float]) -> Dict:
    """
    자동으로 브랜치 생성 (memory_manager 호출)

    Args:
        ctx: Hook Context
        topic: 추출된 주제
        confidence: 확신도
        signals: 신호별 점수

    Returns:
        브랜치 생성 결과
    """
    try:
        # Lazy import to avoid circular dependency
        from cortex_mcp.core.memory_manager import MemoryManager

        memory_manager = MemoryManager()

        # 브랜치명 생성: "주제_YYYYMMDD_HHMMSS"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        branch_topic = f"{topic}_{timestamp}"

        # 브랜치 생성
        result = memory_manager.create_branch(
            project_id=ctx.project_id,
            branch_topic=branch_topic,
            parent_branch=ctx.active_branch,  # 현재 브랜치를 부모로
        )

        if result.get("success"):
            branch_id = result["branch_id"]

            logger.info(f"[TOPIC_SHIFT] ✅ 브랜치 자동 생성 완료: {branch_id}")

            # 상태 업데이트
            ctx.state["active_branch"] = branch_id
            ctx.state["branch_creation_reason"] = {
                "confidence": confidence,
                "signals": signals,
                "timestamp": datetime.utcnow().isoformat(),
            }
            ctx.save()

            # 사용자에게 알림 (보고 스타일 - CORTEX_MEMORY_PROTOCOL v2.0)
            notification = f"""
[CORTEX_BRANCH_AUTO_CREATED]

주제 전환이 감지되어 새 브랜치를 생성했습니다.

브랜치명: "{branch_topic}"
이전 브랜치: "{ctx.active_branch or 'None'}"
확신도: {confidence:.2f}

신호 분석:
- 시맨틱 유사도: {signals.get('semantic', 0.0):.2f}
- 키워드 매칭: {signals.get('keyword', 0.0):.2f}
- 시간 간격: {signals.get('time_gap', 0.0):.2f}
- 파일 컨텍스트 변경: {signals.get('file_context', 0.0):.2f}

조정이 필요하면 알려주세요.
"""

            # stderr로 알림 출력 (사용자에게 보임)
            print(notification, file=sys.stderr)

            return result
        else:
            logger.error(f"[TOPIC_SHIFT] ❌ 브랜치 생성 실패: {result.get('error')}")
            return result

    except Exception as e:
        logger.error(f"[TOPIC_SHIFT] ❌ 브랜치 생성 중 예외 발생: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


def update_context_state(ctx: HookContext, user_message: str, assistant_response: str, tool_calls_made: List[Dict]):
    """
    컨텍스트 상태 업데이트 (다음 턴 비교용)

    Args:
        ctx: Hook Context
        user_message: 사용자 메시지
        assistant_response: AI 응답
        tool_calls_made: 이번 턴에서 호출된 도구 목록
    """
    try:
        # 현재 대화 저장
        ctx.state["last_conversation"] = user_message + " " + assistant_response

        # 현재 시간 저장
        ctx.state["last_message_time"] = datetime.utcnow().isoformat()

        # 접근한 파일 저장
        current_files: List[str] = []

        for tc in tool_calls_made:
            tool_input = tc.get("tool_input", {})

            if "file_path" in tool_input:
                current_files.append(tool_input["file_path"])
            elif "path" in tool_input:
                current_files.append(tool_input["path"])

        # 최근 10개 파일만 유지
        ctx.state["recent_files"] = current_files[-10:]

        ctx.save()

    except Exception as e:
        logger.warning(f"[TOPIC_SHIFT] Context state update failed: {e}")


def main():
    """
    Stop Hook 메인 로직 - 주제 전환 감지 및 자동 브랜치 생성
    """
    ctx = HookContext()

    # stdin에서 응답 정보 읽기
    stdin_data = ctx.stdin_context
    user_message = stdin_data.get("user_message", "")
    assistant_response = stdin_data.get("response", "")
    tool_calls_made = stdin_data.get("tool_calls", [])

    logger.info("[TOPIC_SHIFT] 주제 전환 감지 시작")

    # 초기화 확인
    if not ctx.is_initialized:
        logger.info("[TOPIC_SHIFT] Cortex 초기화되지 않음 - 스킵")
        return

    # 활성 브랜치 확인 (없으면 자동 생성하지 않음)
    if not ctx.active_branch:
        logger.info("[TOPIC_SHIFT] 활성 브랜치 없음 - 스킵")
        return

    # 응답 길이 확인 (너무 짧으면 스킵)
    if len(assistant_response) < 100:
        logger.info("[TOPIC_SHIFT] 응답 길이 부족 - 스킵")
        update_context_state(ctx, user_message, assistant_response, tool_calls_made)
        return

    # 브랜치 생성 필요 여부 판단
    should_create, confidence, signals = should_create_branch(
        ctx, user_message, assistant_response, tool_calls_made
    )

    if should_create:
        logger.info(f"[TOPIC_SHIFT] 브랜치 생성 트리거 (확신도: {confidence:.2f})")

        # 주제 추출
        topic = extract_topic(user_message + " " + assistant_response)

        # 브랜치 자동 생성
        result = create_branch_auto(ctx, topic, confidence, signals)

        if result.get("success"):
            logger.info("[TOPIC_SHIFT] ✅ 브랜치 자동 생성 완료")
        else:
            logger.error(f"[TOPIC_SHIFT] ❌ 브랜치 생성 실패: {result.get('error')}")
    else:
        logger.info(f"[TOPIC_SHIFT] 브랜치 생성 안 함 (확신도: {confidence:.2f} < 0.7)")

    # 컨텍스트 상태 업데이트 (다음 턴 비교용)
    update_context_state(ctx, user_message, assistant_response, tool_calls_made)

    logger.info("[TOPIC_SHIFT] 주제 전환 감지 완료")


if __name__ == "__main__":
    main()
