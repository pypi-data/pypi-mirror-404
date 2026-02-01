#!/usr/bin/env python3
"""
Semantic Relationship Engine - Tier 2 Implementation

핵심 기능:
- Context 간 의미적 관계 분석 (RAG 기반)
- Reference History 패턴 학습
- 작업 시퀀스 추론 (PRECEDES 관계)
- 임베딩 유사도 기반 관련성 계산

Tier 2 (Pro+): 의미적 관계 분석
- RELATED_TO: 임베딩 유사도 > 0.7
- FREQUENTLY_USED_WITH: Reference History co-occurrence
- PRECEDES: 작업 시퀀스 패턴 (A 후 B 작업 빈도 > 70%)

알고리즘:
1. 임베딩 유사도: Cosine Similarity (sentence-transformers)
2. Co-occurrence: Jaccard Similarity (공동 등장 빈도)
3. Sequence Pattern: Conditional Probability P(B|A)

Author: Cortex Development Team
Date: 2026-01-02
Version: 1.0.0
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
from datetime import datetime

logger = logging.getLogger(__name__)


class SemanticRelationshipEngine:
    """
    의미적 관계 분석 엔진 (RAG + Reference History)

    입력:
    - RAG Engine (임베딩 유사도)
    - Reference History (함께 사용된 이력)

    출력:
    - RELATED_TO 관계 (유사도 기반)
    - FREQUENTLY_USED_WITH 관계 (co-occurrence)
    - PRECEDES 관계 (sequence pattern)
    """

    def __init__(self, rag_engine, reference_history):
        """
        초기화

        Args:
            rag_engine: RAGEngine 인스턴스 (임베딩 검색)
            reference_history: ReferenceHistory 인스턴스 (참조 이력)
        """
        self.rag = rag_engine
        self.ref_history = reference_history

        # 설정
        self.similarity_threshold = 0.7  # RELATED_TO 임계값
        self.cooccurrence_min_count = 3  # FREQUENTLY_USED_WITH 최소 빈도
        self.sequence_threshold = 0.7    # PRECEDES 확률 임계값

        logger.info("[SemanticRelationship] Engine initialized")

    def infer_semantic_relations(
        self,
        context_id: str,
        project_id: str,
        top_k: int = 10
    ) -> Dict[str, List[Tuple[str, float, str]]]:
        """
        의미적으로 관련된 Context 추론

        방법:
        1. 임베딩 유사도 (cosine > 0.7) → RELATED_TO
        2. Reference History (함께 사용된 빈도) → FREQUENTLY_USED_WITH
        3. 작업 시퀀스 패턴 (A 후 B 작업 빈도) → PRECEDES

        Args:
            context_id: 기준 Context ID
            project_id: 프로젝트 ID
            top_k: 상위 K개 반환

        Returns:
            {
                "RELATED_TO": [("file://auth.py", 0.85, "임베딩 유사도")],
                "FREQUENTLY_USED_WITH": [("file://session.py", 0.92, "12회 함께 사용")],
                "PRECEDES": [("file://payment.py", 0.78, "78% 순차 패턴")]
            }
        """
        relations = {
            "RELATED_TO": [],
            "FREQUENTLY_USED_WITH": [],
            "PRECEDES": []
        }

        try:
            # 1. 임베딩 유사도 기반 관련성
            similar_contexts = self._find_similar_by_embedding(
                context_id,
                project_id,
                top_k
            )
            relations["RELATED_TO"] = similar_contexts

            # 2. Reference History co-occurrence
            cooccurred_contexts = self._find_cooccurrence(
                context_id,
                project_id,
                top_k
            )
            relations["FREQUENTLY_USED_WITH"] = cooccurred_contexts

            # 3. 작업 시퀀스 패턴
            sequence_contexts = self._find_sequence_pattern(
                context_id,
                project_id,
                top_k
            )
            relations["PRECEDES"] = sequence_contexts

        except Exception as e:
            logger.error(f"[SemanticRelationship] Error inferring relations: {e}")

        logger.info(f"[SemanticRelationship] Inferred relations for {context_id}:")
        logger.info(f"  - RELATED_TO: {len(relations['RELATED_TO'])}")
        logger.info(f"  - FREQUENTLY_USED_WITH: {len(relations['FREQUENTLY_USED_WITH'])}")
        logger.info(f"  - PRECEDES: {len(relations['PRECEDES'])}")

        return relations

    def _find_similar_by_embedding(
        self,
        context_id: str,
        project_id: str,
        top_k: int
    ) -> List[Tuple[str, float, str]]:
        """
        임베딩 유사도 기반 관련 Context 찾기

        Args:
            context_id: 기준 Context ID
            project_id: 프로젝트 ID
            top_k: 상위 K개

        Returns:
            [("file://auth.py", 0.85, "임베딩 유사도 0.85")]
        """
        similar = []

        try:
            # RAG 검색 (top_k * 2로 여유있게)
            search_results = self.rag.search(
                query=context_id,
                project_id=project_id,
                top_k=top_k * 2,
                min_similarity=self.similarity_threshold
            )

            # 결과 변환
            for result in search_results[:top_k]:
                ctx_id = result.get("context_id")
                similarity = result.get("similarity", 0.0)

                if ctx_id != context_id and similarity >= self.similarity_threshold:
                    reason = f"임베딩 유사도 {similarity:.2f}"
                    similar.append((ctx_id, similarity, reason))

        except Exception as e:
            logger.warning(f"[SemanticRelationship] Embedding search error: {e}")

        return similar

    def _find_cooccurrence(
        self,
        context_id: str,
        project_id: str,
        top_k: int
    ) -> List[Tuple[str, float, str]]:
        """
        Reference History 기반 co-occurrence 찾기

        Args:
            context_id: 기준 Context ID
            project_id: 프로젝트 ID
            top_k: 상위 K개

        Returns:
            [("file://session.py", 0.92, "12회 함께 사용")]
        """
        cooccurred = []

        try:
            # Reference History에서 함께 사용된 Context 조회
            history = self.ref_history.get_cooccurrence(
                context_id=context_id,
                project_id=project_id,
                min_count=self.cooccurrence_min_count
            )

            # 상위 K개 추출
            for ctx_id, count, score in history[:top_k]:
                reason = f"{count}회 함께 사용 (스코어 {score:.2f})"
                cooccurred.append((ctx_id, score, reason))

        except Exception as e:
            logger.warning(f"[SemanticRelationship] Co-occurrence error: {e}")

        return cooccurred

    def _find_sequence_pattern(
        self,
        context_id: str,
        project_id: str,
        top_k: int
    ) -> List[Tuple[str, float, str]]:
        """
        작업 시퀀스 패턴 분석 (PRECEDES 관계)

        조건확률: P(B|A) = Count(A→B) / Count(A)
        - P(B|A) > 0.7이면 "A PRECEDES B" 관계 성립

        Args:
            context_id: 기준 Context ID (A)
            project_id: 프로젝트 ID
            top_k: 상위 K개

        Returns:
            [("file://payment.py", 0.78, "A 후 B 작업 78%")]
        """
        sequences = []

        try:
            # Reference History에서 시퀀스 패턴 조회
            patterns = self.ref_history.get_sequence_patterns(
                context_id=context_id,
                project_id=project_id,
                min_probability=self.sequence_threshold
            )

            # 상위 K개 추출
            for next_ctx, probability, count in patterns[:top_k]:
                reason = f"A 후 B 작업 {int(probability * 100)}% ({count}회)"
                sequences.append((next_ctx, probability, reason))

        except Exception as e:
            logger.warning(f"[SemanticRelationship] Sequence pattern error: {e}")

        return sequences

    def merge_and_rank(
        self,
        relations: Dict[str, List[Tuple[str, float, str]]],
        max_results: int = 20
    ) -> List[Dict]:
        """
        여러 관계를 병합하고 스코어링

        알고리즘:
        - RELATED_TO: weight 0.3
        - FREQUENTLY_USED_WITH: weight 0.5
        - PRECEDES: weight 0.2

        Args:
            relations: infer_semantic_relations 결과
            max_results: 최대 반환 개수

        Returns:
            [
                {
                    "context_id": "file://auth.py",
                    "final_score": 0.85,
                    "relations": {
                        "RELATED_TO": 0.85,
                        "FREQUENTLY_USED_WITH": 0.92
                    },
                    "reasons": ["임베딩 유사도 0.85", "12회 함께 사용"]
                }
            ]
        """
        # 가중치
        weights = {
            "RELATED_TO": 0.3,
            "FREQUENTLY_USED_WITH": 0.5,
            "PRECEDES": 0.2
        }

        # Context별 스코어 집계
        context_scores = defaultdict(lambda: {
            "scores": {},
            "reasons": []
        })

        for rel_type, contexts in relations.items():
            for ctx_id, score, reason in contexts:
                context_scores[ctx_id]["scores"][rel_type] = score
                context_scores[ctx_id]["reasons"].append(reason)

        # 최종 스코어 계산
        ranked = []
        for ctx_id, data in context_scores.items():
            final_score = sum(
                data["scores"].get(rel_type, 0) * weight
                for rel_type, weight in weights.items()
            )

            ranked.append({
                "context_id": ctx_id,
                "final_score": final_score,
                "relations": data["scores"],
                "reasons": data["reasons"]
            })

        # 스코어 내림차순 정렬
        ranked.sort(key=lambda x: x["final_score"], reverse=True)

        return ranked[:max_results]

    def update_settings(
        self,
        similarity_threshold: Optional[float] = None,
        cooccurrence_min_count: Optional[int] = None,
        sequence_threshold: Optional[float] = None
    ):
        """
        엔진 설정 업데이트

        Args:
            similarity_threshold: RELATED_TO 임계값 (기본 0.7)
            cooccurrence_min_count: FREQUENTLY_USED_WITH 최소 빈도 (기본 3)
            sequence_threshold: PRECEDES 확률 임계값 (기본 0.7)
        """
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
            logger.info(f"[SemanticRelationship] similarity_threshold updated: {similarity_threshold}")

        if cooccurrence_min_count is not None:
            self.cooccurrence_min_count = cooccurrence_min_count
            logger.info(f"[SemanticRelationship] cooccurrence_min_count updated: {cooccurrence_min_count}")

        if sequence_threshold is not None:
            self.sequence_threshold = sequence_threshold
            logger.info(f"[SemanticRelationship] sequence_threshold updated: {sequence_threshold}")


# Helper 함수들

def calculate_jaccard_similarity(set1: Set, set2: Set) -> float:
    """
    Jaccard Similarity 계산

    J(A, B) = |A ∩ B| / |A ∪ B|

    Args:
        set1: 집합 A
        set2: 집합 B

    Returns:
        float: 0.0 ~ 1.0
    """
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def calculate_conditional_probability(
    sequences: List[Tuple[str, str]],
    context_a: str,
    context_b: str
) -> float:
    """
    조건부 확률 계산: P(B|A)

    Args:
        sequences: [(ctx1, ctx2), ...] 시퀀스 리스트
        context_a: 조건 Context A
        context_b: 결과 Context B

    Returns:
        float: 0.0 ~ 1.0
    """
    count_a = sum(1 for a, b in sequences if a == context_a)
    count_ab = sum(1 for a, b in sequences if a == context_a and b == context_b)

    return count_ab / count_a if count_a > 0 else 0.0
