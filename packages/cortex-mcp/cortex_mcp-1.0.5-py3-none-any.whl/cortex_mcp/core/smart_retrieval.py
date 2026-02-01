"""
Cortex MCP - Smart Retrieval Strategy v1.0

Context 수에 따라 최적의 검색 전략을 자동 선택

전략:
- < 50 contexts: Full Context (전체 제공, RAG 불필요)
- 50-200 contexts: RAG Only (검색 필요, 온톨로지 불필요)
- 200+ contexts: Ontology + RAG (카테고리 필터링 필수)

Claude Code 특성:
- 200K 토큰 컨텍스트 윈도우
- 세션 종료/요약 시 기억 손실
- Cortex가 장기 기억 담당
"""

import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))

from config import config

from .alpha_logger import LogModule, get_alpha_logger


class RetrievalStrategy(Enum):
    """검색 전략 타입"""

    FULL_CONTEXT = "full_context"  # 전체 컨텍스트 제공
    RAG_ONLY = "rag_only"  # RAG 검색만
    ONTOLOGY_RAG = "ontology_rag"  # 온톨로지 + RAG


@dataclass
class StrategyDecision:
    """전략 결정 결과"""

    strategy: RetrievalStrategy
    context_count: int
    reason: str
    use_ontology: bool
    use_rag: bool
    use_fuzzy: bool
    top_k: int  # RAG 검색 시 반환할 결과 수


class SmartRetrievalStrategy:
    """
    Context 수 기반 자동 검색 전략 선택기

    Threshold 기준:
    - FULL_THRESHOLD: 이하면 전체 컨텍스트 제공 (LLM이 처리 가능)
    - RAG_THRESHOLD: 이하면 RAG만 사용
    - 초과하면 온톨로지 + RAG 사용
    """

    # Threshold 설정 (조정 가능)
    FULL_THRESHOLD = 50  # 50개 이하: 전체 제공
    RAG_THRESHOLD = 200  # 200개 이하: RAG만
    # 200개 초과: 온톨로지 + RAG

    # Top-K 설정 (전략별)
    TOP_K_FULL = 0  # 전체 (제한 없음)
    TOP_K_RAG = 10  # RAG: 상위 10개
    TOP_K_ONTOLOGY = 15  # 온톨로지+RAG: 상위 15개 (카테고리별)

    def __init__(self):
        self.logger = get_alpha_logger()
        self.memory_dir = config.memory_dir

        # 캐시: 프로젝트별 context 수
        self._context_count_cache: Dict[str, int] = {}
        self._cache_timestamp: Dict[str, float] = {}
        self._cache_ttl = 300  # 5분 캐시

    def decide_strategy(
        self,
        project_id: str,
        branch_id: Optional[str] = None,
        force_strategy: Optional[RetrievalStrategy] = None,
    ) -> StrategyDecision:
        """
        프로젝트의 context 수에 따라 최적 전략 결정

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID (특정 브랜치만 카운트할 경우)
            force_strategy: 강제 전략 지정 (테스트용)

        Returns:
            StrategyDecision: 전략 결정 결과
        """
        start_time = time.time()

        # 강제 전략 지정된 경우
        if force_strategy:
            decision = self._create_decision(force_strategy, 0, "forced")
            self._log_decision(decision, start_time)
            return decision

        # Context 수 조회
        context_count = self._get_context_count(project_id, branch_id)

        # 전략 결정
        if context_count <= self.FULL_THRESHOLD:
            strategy = RetrievalStrategy.FULL_CONTEXT
            reason = (
                f"context_count({context_count}) <= {self.FULL_THRESHOLD}: LLM이 직접 처리 가능"
            )
        elif context_count <= self.RAG_THRESHOLD:
            strategy = RetrievalStrategy.RAG_ONLY
            reason = f"{self.FULL_THRESHOLD} < context_count({context_count}) <= {self.RAG_THRESHOLD}: RAG 검색 필요"
        else:
            strategy = RetrievalStrategy.ONTOLOGY_RAG
            reason = (
                f"context_count({context_count}) > {self.RAG_THRESHOLD}: 온톨로지 분류 + RAG 필요"
            )

        decision = self._create_decision(strategy, context_count, reason)
        self._log_decision(decision, start_time)

        return decision

    def _create_decision(
        self, strategy: RetrievalStrategy, context_count: int, reason: str
    ) -> StrategyDecision:
        """전략 결정 객체 생성"""
        if strategy == RetrievalStrategy.FULL_CONTEXT:
            return StrategyDecision(
                strategy=strategy,
                context_count=context_count,
                reason=reason,
                use_ontology=False,
                use_rag=False,
                use_fuzzy=False,
                top_k=self.TOP_K_FULL,
            )
        elif strategy == RetrievalStrategy.RAG_ONLY:
            return StrategyDecision(
                strategy=strategy,
                context_count=context_count,
                reason=reason,
                use_ontology=False,
                use_rag=True,
                use_fuzzy=True,  # Fuzzy는 RAG와 함께 사용
                top_k=self.TOP_K_RAG,
            )
        else:  # ONTOLOGY_RAG
            return StrategyDecision(
                strategy=strategy,
                context_count=context_count,
                reason=reason,
                use_ontology=True,
                use_rag=True,
                use_fuzzy=True,
                top_k=self.TOP_K_ONTOLOGY,
            )

    def _get_context_count(self, project_id: str, branch_id: Optional[str] = None) -> int:
        """
        프로젝트의 context 수 조회 (캐시 사용)
        """
        cache_key = f"{project_id}/{branch_id}" if branch_id else project_id
        current_time = time.time()

        # 캐시 확인
        if cache_key in self._context_count_cache:
            if current_time - self._cache_timestamp.get(cache_key, 0) < self._cache_ttl:
                return self._context_count_cache[cache_key]

        # 실제 카운트
        count = self._count_contexts(project_id, branch_id)

        # 캐시 업데이트
        self._context_count_cache[cache_key] = count
        self._cache_timestamp[cache_key] = current_time

        return count

    def _count_contexts(self, project_id: str, branch_id: Optional[str] = None) -> int:
        """
        실제 context 파일 수 카운트
        """
        project_dir = self.memory_dir / project_id

        if not project_dir.exists():
            return 0

        count = 0

        if branch_id:
            # 특정 브랜치만 카운트
            branch_dir = project_dir / "contexts" / branch_id
            if branch_dir.exists():
                count = len(list(branch_dir.glob("*.md")))
        else:
            # 프로젝트 전체 카운트
            # 1. 루트 레벨 .md 파일
            count += len(list(project_dir.glob("*.md")))

            # 2. contexts 디렉토리 내 모든 파일
            contexts_dir = project_dir / "contexts"
            if contexts_dir.exists():
                for branch_path in contexts_dir.iterdir():
                    if branch_path.is_dir():
                        count += len(list(branch_path.glob("*.md")))

        return count

    def _log_decision(self, decision: StrategyDecision, start_time: float):
        """전략 결정 로깅"""
        latency_ms = (time.time() - start_time) * 1000

        self.logger.log(
            module=LogModule.GENERAL,
            action="smart_retrieval_decision",
            success=True,
            latency_ms=latency_ms,
            metadata={
                "strategy": decision.strategy.value,
                "context_count": decision.context_count,
                "reason": decision.reason,
                "use_ontology": decision.use_ontology,
                "use_rag": decision.use_rag,
                "top_k": decision.top_k,
            },
        )

    def invalidate_cache(self, project_id: str, branch_id: Optional[str] = None):
        """캐시 무효화 (context 추가/삭제 시 호출)"""
        cache_key = f"{project_id}/{branch_id}" if branch_id else project_id

        if cache_key in self._context_count_cache:
            del self._context_count_cache[cache_key]
        if cache_key in self._cache_timestamp:
            del self._cache_timestamp[cache_key]

        # 프로젝트 전체 캐시도 무효화
        if branch_id and project_id in self._context_count_cache:
            del self._context_count_cache[project_id]
            if project_id in self._cache_timestamp:
                del self._cache_timestamp[project_id]

    def get_thresholds(self) -> Dict[str, int]:
        """현재 threshold 설정 반환"""
        return {
            "full_threshold": self.FULL_THRESHOLD,
            "rag_threshold": self.RAG_THRESHOLD,
            "top_k_full": self.TOP_K_FULL,
            "top_k_rag": self.TOP_K_RAG,
            "top_k_ontology": self.TOP_K_ONTOLOGY,
        }

    def update_thresholds(
        self, full_threshold: Optional[int] = None, rag_threshold: Optional[int] = None
    ):
        """
        Threshold 동적 업데이트 (튜닝용)

        Args:
            full_threshold: 전체 컨텍스트 제공 임계값
            rag_threshold: RAG 전용 임계값
        """
        if full_threshold is not None:
            self.FULL_THRESHOLD = full_threshold
        if rag_threshold is not None:
            self.RAG_THRESHOLD = rag_threshold

        # 캐시 초기화 (threshold 변경 시 재계산 필요)
        self._context_count_cache.clear()
        self._cache_timestamp.clear()


# 싱글톤 인스턴스
_smart_retrieval: Optional[SmartRetrievalStrategy] = None


def get_smart_retrieval() -> SmartRetrievalStrategy:
    """SmartRetrievalStrategy 싱글톤 인스턴스 반환"""
    global _smart_retrieval
    if _smart_retrieval is None:
        _smart_retrieval = SmartRetrievalStrategy()
    return _smart_retrieval


def reset_smart_retrieval():
    """테스트용 리셋"""
    global _smart_retrieval
    _smart_retrieval = None
