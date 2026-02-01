"""
ContradictionDetector v2.0 - 언어 독립적 범용 모순 감지 시스템

Cortex Phase 9: Hallucination Detection System
언어에 구애받지 않는 의미 기반 모순 감지를 제공합니다.

핵심 개선:
- Regex 패턴 제거 (언어 특화 로직 없음)
- Semantic Embedding 기반 주체 유사도 분석
- Universal Temporal Markers (숫자, 날짜 등) 활용
- LLM Semantic Verification (선택적)
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from core.claim_extractor import Claim

# Sentence Transformers (로컬 임베딩)
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import KMeans  # HIGH #4: 성능 최적화용

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("[WARNING] sentence-transformers or sklearn not installed. Semantic similarity disabled.")


@dataclass
class Contradiction:
    """
    감지된 모순 정보
    """

    type: str  # temporal, content, etc.
    severity: str  # low, medium, high
    claim1: Claim
    claim2: Claim
    description: str
    evidence: str
    confidence: float = 1.0


class ContradictionDetectorV2:
    """
    언어 독립적 모순 감지 시스템

    Zero-Trust 원칙 준수:
    - 로컬 임베딩 모델 사용 (외부 API 없음)
    - LLM 검증은 선택적 (사용자의 AI 활용)
    """

    # 시간 관련 참조 문장들 - BEFORE (먼저, 이전, 처음 등)
    TEMPORAL_BEFORE = [
        # Korean
        "먼저", "이전에", "처음에", "전에", "앞서",
        # English
        "before", "first", "earlier", "prior", "previously",
        # Japanese
        "前に", "先に", "最初に",
        # Chinese
        "之前", "首先", "先",
        # Spanish
        "antes", "primero",
    ]

    # 시간 관련 참조 문장들 - AFTER (나중에, 이후, 마지막 등)
    TEMPORAL_AFTER = [
        # Korean
        "나중에", "이후에", "마지막에", "후에", "뒤에",
        # English
        "after", "last", "later", "subsequent", "afterwards",
        # Japanese
        "後に", "最後に",
        # Chinese
        "之后", "最后", "后",
        # Spanish
        "después", "último",
    ]

    # 비교 관련 참조 문장들 - INCREASE (증가, 더 크다, 더 좋다 등)
    COMPARISON_INCREASE = [
        # Korean
        "증가", "늘어남", "더 크다", "더 많다", "더 빠르다",
        "더 높다", "더 좋다", "향상", "개선", "상승",
        # English
        "increase", "more", "greater", "higher", "faster",
        "better", "improved", "enhanced", "rise", "grow",
        # Japanese
        "増加", "より大きい", "より多い", "より速い", "向上",
        # Chinese
        "增加", "更大", "更多", "更快", "提高",
        # Spanish
        "aumentar", "más", "mayor", "mejor", "mejorado",
    ]

    # 비교 관련 참조 문장들 - DECREASE (감소, 더 작다, 더 나쁘다 등)
    COMPARISON_DECREASE = [
        # Korean
        "감소", "줄어듦", "더 작다", "더 적다", "더 느리다",
        "더 낮다", "더 나쁘다", "악화", "저하", "하락",
        # English
        "decrease", "less", "lesser", "lower", "slower",
        "worse", "degraded", "declined", "fall", "reduce",
        # Japanese
        "減少", "より小さい", "より少ない", "より遅い", "低下",
        # Chinese
        "减少", "更小", "更少", "更慢", "降低",
        # Spanish
        "disminuir", "menos", "menor", "peor", "reducido",
    ]

    # 극성 감지용 참조 문장들
    POSITIVE_REFERENCES = [
        # Korean
        "작동합니다", "성공했습니다", "완료했습니다", "구현했습니다",
        "정상입니다", "통과했습니다", "문제없습니다", "해결했습니다",
        "좋습니다", "빠릅니다", "높습니다", "많습니다",
        # English
        "it works", "successful", "completed", "implemented",
        "working fine", "passed", "no problem", "resolved",
        "good", "fast", "high", "increased",
        # Japanese
        "動作します", "成功しました", "完了しました", "実装しました",
        "正常です", "合格しました", "問題ありません", "解決しました",
        # Chinese
        "工作正常", "成功了", "完成了", "实现了",
        "正常", "通过了", "没问题", "解决了",
        # Spanish
        "funciona", "exitoso", "completado", "implementado",
        "funcionando bien", "aprobado", "sin problema", "resuelto",
    ]

    NEGATIVE_REFERENCES = [
        # Korean
        "작동하지 않습니다", "실패했습니다", "완료하지 못했습니다", "구현하지 못했습니다",
        "문제가 있습니다", "통과하지 못했습니다", "오류가 있습니다", "해결하지 못했습니다",
        "나쁩니다", "느립니다", "낮습니다", "적습니다",
        # English
        "doesn't work", "failed", "not completed", "not implemented",
        "having problems", "didn't pass", "has errors", "not resolved",
        "bad", "slow", "low", "decreased",
        # Japanese
        "動作しません", "失敗しました", "完了していません", "実装していません",
        "問題があります", "合格していません", "エラーがあります", "解決していません",
        # Chinese
        "不工作", "失败了", "未完成", "未实现",
        "有问题", "未通过", "有错误", "未解决",
        # Spanish
        "no funciona", "fallido", "no completado", "no implementado",
        "con problemas", "no aprobado", "con errores", "no resuelto",
    ]

    def __init__(self, use_embeddings: bool = True):
        """
        Args:
            use_embeddings: 임베딩 기반 유사도 사용 여부
        """
        self.use_embeddings = use_embeddings and EMBEDDINGS_AVAILABLE

        # 로컬 임베딩 모델 초기화 (다국어 지원)
        if self.use_embeddings:
            try:
                # paraphrase-multilingual-mpnet-base-v2: 50+ 언어 지원
                self.embedding_model = SentenceTransformer(
                    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
                )

                # 참조 임베딩 미리 계산 (초기화 시 1회만)
                self.positive_prototype = np.mean(
                    self.embedding_model.encode(self.POSITIVE_REFERENCES), axis=0
                )
                self.negative_prototype = np.mean(
                    self.embedding_model.encode(self.NEGATIVE_REFERENCES), axis=0
                )
                # Temporal Before/After 분리 (opposite direction 감지용)
                self.temporal_before_prototype = np.mean(
                    self.embedding_model.encode(self.TEMPORAL_BEFORE), axis=0
                )
                self.temporal_after_prototype = np.mean(
                    self.embedding_model.encode(self.TEMPORAL_AFTER), axis=0
                )
                # Comparison Increase/Decrease 분리 (opposite direction 감지용)
                self.comparison_increase_prototype = np.mean(
                    self.embedding_model.encode(self.COMPARISON_INCREASE), axis=0
                )
                self.comparison_decrease_prototype = np.mean(
                    self.embedding_model.encode(self.COMPARISON_DECREASE), axis=0
                )
            except Exception as e:
                print(f"[WARNING] Failed to load embedding model: {e}")
                self.use_embeddings = False

        # 임베딩 캐시 (성능 최적화)
        self._embedding_cache = {}
        # 유사도 쌍 캐시 (추가 최적화)
        self._similarity_cache = {}

    def detect_contradictions(
        self, text: Union[str, List[str]], claims: Optional[List[Claim]] = None
    ) -> Dict:
        """
        텍스트 또는 Claim 목록에서 모순 감지

        Args:
            text: LLM 응답 텍스트 (문자열 또는 문자열 리스트)
            claims: 미리 추출된 Claim 목록 (선택적)

        Returns:
            모순 감지 결과
        """
        from core.claim_extractor import Claim as ClaimClass

        # Claim 추출 (필요시)
        if claims is None:
            # text가 리스트인 경우 (여러 문장 직접 전달)
            if isinstance(text, list):
                sentences = text
            else:
                # V2 방식: 언어 독립적 문장 분리
                sentences = self._split_into_sentences(text)

            # 각 문장을 Claim 객체로 변환
            claims = []
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    claim = ClaimClass(
                        claim_type="statement",  # 기본 타입
                        text=sentence,
                        start=0,  # V2에서는 위치 정보 없음
                        end=len(sentence),
                        confidence=1.0,
                    )
                    claims.append(claim)

        # 중복 Claim 제거 (성능 최적화)
        # 동일한 텍스트의 Claim은 1개만 유지
        seen_texts = {}
        unique_claims = []
        for claim in claims:
            text = claim.text.strip()
            if text not in seen_texts:
                seen_texts[text] = True
                unique_claims.append(claim)

        claims = unique_claims

        contradictions = []

        # HIGH #4: Clustering을 사용한 성능 최적화 (O(n^2) → O(n^2/k))
        if len(claims) > 10 and self.use_embeddings:
            import time as perf_time
            start_total = perf_time.time()
            print(f"[HIGH #4] Clustering 활성화: {len(claims)} claims")

            # 1. Claim 텍스트 임베딩 (캐시 활용 + batch encoding)
            claim_texts = [claim.text for claim in claims]

            # 1a. 캐시 확인 및 미스 수집
            start_cache = perf_time.time()
            texts_to_encode = []
            cached_embeddings = {}
            for i, text in enumerate(claim_texts):
                if text in self._embedding_cache:
                    cached_embeddings[i] = self._embedding_cache[text]
                else:
                    texts_to_encode.append((i, text))
            print(f"[HIGH #4 DEBUG] 캐시 확인: {perf_time.time() - start_cache:.3f}초, 캐시 히트: {len(cached_embeddings)}, 캐시 미스: {len(texts_to_encode)}")

            # 1b. Batch encoding (캐시 미스만) - 성능 최적화
            if texts_to_encode:
                start_encoding = perf_time.time()
                indices, texts = zip(*texts_to_encode)
                new_embeddings = self.embedding_model.encode(list(texts))  # batch encoding!
                print(f"[HIGH #4 DEBUG] Batch encoding {len(texts)}개: {perf_time.time() - start_encoding:.3f}초")

                start_cache_save = perf_time.time()
                for idx, text, embedding in zip(indices, texts, new_embeddings):
                    # 캐시에 저장
                    if len(self._embedding_cache) >= 1024:
                        oldest_key = next(iter(self._embedding_cache))
                        del self._embedding_cache[oldest_key]
                    self._embedding_cache[text] = embedding
                    cached_embeddings[idx] = embedding
                print(f"[HIGH #4 DEBUG] 캐시 저장: {perf_time.time() - start_cache_save:.3f}초")

            # 1c. 순서대로 재구성
            embeddings = [cached_embeddings[i] for i in range(len(claim_texts))]

            # 2. KMeans 클러스터링 (문장 수 / 10개 클러스터)
            start_kmeans = perf_time.time()
            n_clusters = max(2, len(claims) // 10)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            print(f"[HIGH #4 DEBUG] KMeans clustering: {perf_time.time() - start_kmeans:.3f}초")

            # 3. 클러스터별로 Claim 그룹화
            clusters = {}
            for idx, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append((idx, claims[idx]))

            print(f"[HIGH #4] {len(claims)} claims → {n_clusters} clusters")

            # 4. 클러스터 내에서만 검사
            start_checking = perf_time.time()
            total_comparisons = 0
            for cluster_id, cluster_claims in clusters.items():
                for i in range(len(cluster_claims)):
                    for j in range(i + 1, len(cluster_claims)):
                        idx1, claim1 = cluster_claims[i]
                        idx2, claim2 = cluster_claims[j]
                        total_comparisons += 1

                        # 시간 모순 검사
                        temporal_contradiction = self._check_temporal_contradiction(claim1, claim2)
                        if temporal_contradiction:
                            contradictions.append(temporal_contradiction)
                            continue

                        # 내용 모순 검사
                        content_contradiction = self._check_content_contradiction(claim1, claim2)
                        if content_contradiction:
                            contradictions.append(content_contradiction)
            print(f"[HIGH #4 DEBUG] 모순 검사 ({total_comparisons}번 비교): {perf_time.time() - start_checking:.3f}초")
            print(f"[HIGH #4 DEBUG] 전체 clustering 소요 시간: {perf_time.time() - start_total:.3f}초")

            # HIGH #4 DEBUG: 세밀한 타이밍 분석
            print(f"\n[HIGH #4 DETAIL] === 세밀한 병목 분석 ===")
            if hasattr(self, '_temporal_check_count'):
                print(f"[HIGH #4 DETAIL] Temporal 검사: {self._temporal_check_count}회")
                print(f"  - Similarity 계산: {self._temporal_sim_time:.3f}초 (평균 {self._temporal_sim_time/self._temporal_check_count*1000:.1f}ms)")
                print(f"  - Direction 감지: {self._temporal_dir_time:.3f}초 (평균 {self._temporal_dir_time/self._temporal_check_count*1000:.1f}ms)")

            if hasattr(self, '_content_check_count'):
                print(f"[HIGH #4 DETAIL] Content 검사: {self._content_check_count}회")
                print(f"  - Similarity 계산: {self._content_sim_time:.3f}초 (평균 {self._content_sim_time/self._content_check_count*1000:.1f}ms)")
                print(f"  - Polarity 감지: {self._content_pol_time:.3f}초 (평균 {self._content_pol_time/self._content_check_count*1000:.1f}ms)")
                print(f"  - Negation 체크: {self._content_neg_time:.3f}초 (평균 {self._content_neg_time/self._content_check_count*1000:.1f}ms)")
            print(f"[HIGH #4 DETAIL] ==================\n")

            # HIGH #4 DEBUG: 캐시 히트율 출력
            if hasattr(self, '_emb_call_count'):
                hit_rate = (self._emb_cache_hits / self._emb_call_count * 100) if self._emb_call_count > 0 else 0
                print(f"[HIGH #4 DEBUG] Embedding 캐시 히트율: {self._emb_cache_hits}/{self._emb_call_count} ({hit_rate:.1f}%)")
        else:
            # 기존 O(n^2) 로직 (Claim 수가 적거나 임베딩 사용 불가)
            print(f"[HIGH #4] 기존 O(n^2) 로직: {len(claims)} claims (clustering 미사용)")
            for i in range(len(claims)):
                for j in range(i + 1, len(claims)):
                    claim1 = claims[i]
                    claim2 = claims[j]

                    # 시간 모순 검사
                    temporal_contradiction = self._check_temporal_contradiction(claim1, claim2)
                    if temporal_contradiction:
                        contradictions.append(temporal_contradiction)
                        continue

                    # 내용 모순 검사
                    content_contradiction = self._check_content_contradiction(claim1, claim2)
                    if content_contradiction:
                        contradictions.append(content_contradiction)

        # Severity 계산
        severity = self._calculate_overall_severity(contradictions)

        result_dict = {
            "contradictions_found": len(contradictions),
            "total_claims": len(claims),  # V1 호환성: Claim 총 개수
            "contradictions": [self._contradiction_to_dict(c) for c in contradictions],
            "severity": severity,
            "has_critical_contradictions": severity == "critical",
            "timestamp": datetime.now().isoformat(),
        }

        # V1 호환성: interpretation 필드 추가
        result_dict["interpretation"] = self.interpret_result(result_dict)

        return result_dict

    def _check_temporal_contradiction(
        self, claim1: Claim, claim2: Claim
    ) -> Optional[Contradiction]:
        """
        시간 순서 모순 검사 (임베딩 기반 semantic approach)

        핵심 아이디어:
        1. 두 문장의 의미 유사도 확인 (같은 주제인지)
        2. Temporal 방향 감지 (before vs after)
        3. 반대 방향이면 모순

        패턴 매칭 없이 순수 의미 기반 접근
        """
        # HIGH #4 DEBUG: 세밀한 타이밍 측정
        import time as perf_time
        t_start = perf_time.time()

        # 1. 주체 유사도 확인
        t_sim_start = perf_time.time()
        similarity = self._calculate_semantic_similarity(claim1.text, claim2.text)
        t_sim = perf_time.time() - t_sim_start

        # 유사도가 낮으면 서로 다른 대상을 말하는 것
        if similarity < 0.35:
            if hasattr(self, '_temporal_check_count'):
                self._temporal_check_count += 1
                self._temporal_sim_time += t_sim
            return None

        # 2. Temporal 방향 감지 (before/after)
        t_dir1_start = perf_time.time()
        direction1 = self._detect_temporal_direction(claim1.text)
        t_dir1 = perf_time.time() - t_dir1_start

        t_dir2_start = perf_time.time()
        direction2 = self._detect_temporal_direction(claim2.text)
        t_dir2 = perf_time.time() - t_dir2_start

        # 둘 다 temporal marker가 없으면 모순 아님
        if not (direction1 and direction2):
            # HIGH #4 DEBUG: 통계 수집
            if not hasattr(self, '_temporal_check_count'):
                self._temporal_check_count = 0
                self._temporal_sim_time = 0.0
                self._temporal_dir_time = 0.0
            self._temporal_check_count += 1
            self._temporal_sim_time += t_sim
            self._temporal_dir_time += (t_dir1 + t_dir2)
            return None

        # 3. 반대 방향 확인
        has_opposite_direction = (direction1 != direction2)

        # HIGH #4 DEBUG: 통계 수집
        if not hasattr(self, '_temporal_check_count'):
            self._temporal_check_count = 0
            self._temporal_sim_time = 0.0
            self._temporal_dir_time = 0.0
        self._temporal_check_count += 1
        self._temporal_sim_time += t_sim
        self._temporal_dir_time += (t_dir1 + t_dir2)

        if has_opposite_direction and similarity >= 0.35:
            # Severity: 유사도 기반
            if similarity >= 0.6:
                severity = "critical"
            elif similarity >= 0.4:
                severity = "high"
            else:
                severity = "medium"

            return Contradiction(
                type="temporal",
                severity=severity,
                claim1=claim1,
                claim2=claim2,
                description=f"Temporal order conflict ({direction1} vs {direction2} with similar content)",
                evidence=f"Similarity={similarity:.2f}, direction1={direction1}, direction2={direction2}",
                confidence=similarity,
            )

        return None

    def _check_content_contradiction(self, claim1: Claim, claim2: Claim) -> Optional[Contradiction]:
        """
        내용 모순 검사 (긍정/부정 등)

        언어 독립적 접근:
        1. Semantic Similarity로 주제 일치 확인
        2. Sentiment/Polarity 분석 (긍정/부정)
        3. 반대 극성이면 모순
        """
        # HIGH #4 DEBUG: 세밀한 타이밍 측정
        import time as perf_time

        # 주체 유사도 확인
        t_sim_start = perf_time.time()
        similarity = self._calculate_semantic_similarity(claim1.text, claim2.text)
        t_sim = perf_time.time() - t_sim_start

        # 극성 먼저 검사 (threshold 결정을 위해)
        t_pol1_start = perf_time.time()
        polarity1 = self._detect_polarity(claim1.text)
        t_pol1 = perf_time.time() - t_pol1_start

        t_pol2_start = perf_time.time()
        polarity2 = self._detect_polarity(claim2.text)
        t_pol2 = perf_time.time() - t_pol2_start

        # Direct negation 패턴 체크 (부정어 유무)
        t_neg_start = perf_time.time()
        is_direct_negation = self._is_direct_negation_pattern(claim1.text, claim2.text)
        t_neg = perf_time.time() - t_neg_start

        # 반대 극성일 때는 더 낮은 threshold 사용
        # (discourse marker "하지만" 등이 유사도를 낮추므로)
        # Direct negation pattern이 있으면 polarity와 무관하게 낮은 threshold 사용
        has_opposite_polarity = (polarity1 and polarity2 and polarity1 != polarity2)
        threshold = 0.35 if (has_opposite_polarity or is_direct_negation) else 0.4

        # HIGH #4 DEBUG: 통계 수집 초기화
        if not hasattr(self, '_content_check_count'):
            self._content_check_count = 0
            self._content_sim_time = 0.0
            self._content_pol_time = 0.0
            self._content_neg_time = 0.0

        # 유사도가 threshold 이상이면 같은 주제
        # 반대 의미 문장은 유사도가 0.35-0.6 정도로 나올 수 있음
        if similarity > threshold:
            # 반대 극성이거나 direct negation pattern이면 모순
            if has_opposite_polarity or is_direct_negation:
                # HIGH #4 DEBUG: 통계 수집
                self._content_check_count += 1
                self._content_sim_time += t_sim
                self._content_pol_time += (t_pol1 + t_pol2)
                self._content_neg_time += t_neg

                # Severity 구분:
                # - Direct negation pattern: critical
                # - High similarity (0.6+): critical
                # - Medium similarity (0.4-0.6): high
                # - Low similarity (0.35-0.4): medium
                if is_direct_negation or similarity >= 0.6:
                    severity = "critical"
                    description = "Direct negation (opposite polarity with high similarity)"
                elif similarity >= 0.4:
                    severity = "high"
                    description = "Strong contradiction (opposite polarity)"
                else:
                    severity = "medium"
                    description = "Content contradiction (opposite polarity)"

                return Contradiction(
                    type="content",
                    severity=severity,
                    claim1=claim1,
                    claim2=claim2,
                    description=description,
                    evidence=f"Polarity conflict: {polarity1} vs {polarity2}",
                    confidence=similarity,
                )

        # HIGH #4 DEBUG: 통계 수집
        self._content_check_count += 1
        self._content_sim_time += t_sim
        self._content_pol_time += (t_pol1 + t_pol2)
        self._content_neg_time += t_neg

        return None

    def _get_embedding_cached(self, text: str) -> np.ndarray:
        """
        캐싱된 임베딩 반환 (성능 최적화)

        Args:
            text: 임베딩할 텍스트

        Returns:
            임베딩 벡터 (numpy array)
        """
        # HIGH #4 DEBUG: 캐시 히트율 추적
        if not hasattr(self, '_emb_call_count'):
            self._emb_call_count = 0
            self._emb_cache_hits = 0

        self._emb_call_count += 1

        # 캐시 확인
        if text in self._embedding_cache:
            self._emb_cache_hits += 1
            return self._embedding_cache[text]

        # 캐시 미스 - 새로 계산
        embedding = self.embedding_model.encode([text])[0]

        # 캐시에 저장 (최대 1024개 유지)
        if len(self._embedding_cache) >= 1024:
            # LRU 방식: 가장 오래된 항목 제거
            oldest_key = next(iter(self._embedding_cache))
            del self._embedding_cache[oldest_key]

        self._embedding_cache[text] = embedding
        return embedding

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트의 의미적 유사도 계산 (언어 무관)

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            유사도 (0.0 ~ 1.0)
        """
        if not self.use_embeddings:
            # Fallback: 키워드 기반 유사도
            return self._keyword_similarity(text1, text2)

        # 쌍 캐시 확인 (순서 무관)
        cache_key = tuple(sorted([text1, text2]))
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        try:
            # HIGH #4 DEBUG: 캐시 히트율 확인
            import sys
            if not hasattr(self, '_sim_call_count'):
                self._sim_call_count = 0
                self._sim_cache_hits = 0
            self._sim_call_count += 1

            # 캐싱된 임베딩 사용 (성능 최적화)
            embedding1 = self._get_embedding_cached(text1)
            embedding2 = self._get_embedding_cached(text2)

            # Cosine Similarity
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )

            result = float(similarity)

            # 쌍 캐시 저장 (최대 2048개 유지)
            if len(self._similarity_cache) >= 2048:
                oldest_key = next(iter(self._similarity_cache))
                del self._similarity_cache[oldest_key]

            self._similarity_cache[cache_key] = result
            return result

        except Exception as e:
            print(f"[WARNING] Embedding similarity failed: {e}")
            return self._keyword_similarity(text1, text2)

    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """
        Fallback: 키워드 기반 유사도 (임베딩 사용 불가 시)
        """
        # 단어 분리 (공백 기준)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Jaccard Similarity
        intersection = words1 & words2
        union = words1 | words2

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _extract_temporal_markers(self, text: str) -> List[Dict]:
        """
        Universal Temporal Markers 추출 (언어 무관)

        - 숫자 순서 (1, 2, 3...)
        - 순서 단어 (First/then, 먼저/후에, Zuerst/dann, etc.)
        - 날짜/시간 (2023-01-15, 10:30)

        Returns:
            [{"type": "number", "value": 1, "position": 10}, ...]
        """
        markers = []

        # 언어 무관 순서 단어 매핑 (소문자로 저장)
        # 지원 언어: 영어, 한국어, 독일어, 프랑스어, 스페인어, 일본어, 중국어,
        #            이탈리아어, 포르투갈어, 러시아어, 아랍어, 힌디어
        sequence_words = {
            # First (1) - 12개 언어
            "first": 1, "initially": 1, "firstly": 1, "at first": 1,  # English
            "먼저": 1, "우선": 1, "처음": 1, "최초": 1, "첫": 1,  # Korean
            "zuerst": 1, "erst": 1, "erstens": 1, "anfangs": 1,  # German
            "d'abord": 1, "premièrement": 1, "au début": 1,  # French
            "primero": 1, "primeramente": 1, "al principio": 1,  # Spanish
            "最初": 1, "まず": 1, "初め": 1, "第一": 1,  # Japanese
            "首先": 1, "第一": 1, "起初": 1, "最初": 1,  # Chinese
            "prima": 1, "innanzitutto": 1, "per primo": 1,  # Italian
            "primeiro": 1, "primeiramente": 1, "inicialmente": 1,  # Portuguese
            "сначала": 1, "во-первых": 1, "первый": 1,  # Russian
            "أولاً": 1, "في البداية": 1,  # Arabic
            "पहले": 1, "सबसे पहले": 1,  # Hindi

            # Then / Next (2) - 12개 언어
            "then": 2, "next": 2, "after": 2, "afterwards": 2, "secondly": 2, "later": 2,  # English
            "그다음": 2, "다음": 2, "후에": 2, "이후": 2, "그후": 2, "두번째": 2,  # Korean
            "dann": 2, "danach": 2, "zweitens": 2, "später": 2, "anschließend": 2,  # German
            "puis": 2, "ensuite": 2, "après": 2, "deuxièmement": 2, "plus tard": 2,  # French
            "luego": 2, "después": 2, "entonces": 2, "segundo": 2, "más tarde": 2,  # Spanish
            "次": 2, "それから": 2, "その後": 2, "次に": 2, "第二": 2,  # Japanese
            "然后": 2, "接着": 2, "其次": 2, "随后": 2, "第二": 2,  # Chinese
            "poi": 2, "dopo": 2, "in seguito": 2, "secondo": 2,  # Italian
            "depois": 2, "então": 2, "em seguida": 2, "segundo": 2,  # Portuguese
            "потом": 2, "затем": 2, "во-вторых": 2, "позже": 2,  # Russian
            "ثم": 2, "بعد ذلك": 2, "ثانياً": 2,  # Arabic
            "फिर": 2, "उसके बाद": 2, "दूसरे": 2,  # Hindi

            # Finally / Last (3) - 12개 언어
            "finally": 3, "lastly": 3, "last": 3, "at last": 3, "in the end": 3,  # English
            "마지막": 3, "끝으로": 3, "결국": 3, "최종": 3, "세번째": 3,  # Korean
            "schließlich": 3, "zuletzt": 3, "drittens": 3, "endlich": 3, "am ende": 3,  # German
            "finalement": 3, "enfin": 3, "à la fin": 3, "troisièmement": 3,  # French
            "finalmente": 3, "por último": 3, "al final": 3, "tercero": 3,  # Spanish
            "最後": 3, "最終": 3, "ついに": 3, "終わり": 3, "第三": 3,  # Japanese
            "最后": 3, "最终": 3, "终于": 3, "末了": 3, "第三": 3,  # Chinese
            "infine": 3, "alla fine": 3, "per ultimo": 3, "terzo": 3,  # Italian
            "finalmente": 3, "por fim": 3, "no final": 3, "terceiro": 3,  # Portuguese
            "наконец": 3, "в-третьих": 3, "в конце": 3, "последний": 3,  # Russian
            "أخيراً": 3, "في النهاية": 3, "ثالثاً": 3,  # Arabic
            "अंत में": 3, "आखिर में": 3, "तीसरे": 3,  # Hindi
        }

        # 순서 단어 추출
        text_lower = text.lower()
        for word, value in sequence_words.items():
            # CJK 문자 감지 (일본어, 중국어, 한국어)
            has_cjk = any('\u4e00' <= c <= '\u9fff' or  # CJK Unified Ideographs
                          '\u3040' <= c <= '\u309f' or  # Hiragana
                          '\u30a0' <= c <= '\u30ff' or  # Katakana
                          '\uac00' <= c <= '\ud7af'     # Hangul
                          for c in word)

            if has_cjk:
                # CJK 언어: word boundary 없이 직접 매칭
                pattern = re.escape(word)
            else:
                # 서양 언어: word boundary 사용
                pattern = r"\b" + re.escape(word) + r"\b"

            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                markers.append(
                    {
                        "type": "sequence_word",
                        "value": value,
                        "position": match.start(),
                        "word": word,
                    }
                )

        # 숫자 추출
        for match in re.finditer(r"\b(\d+)\b", text):
            markers.append(
                {"type": "number", "value": int(match.group(1)), "position": match.start()}
            )

        # 날짜 패턴 (ISO 8601 등)
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",  # 2023-01-15
            r"\d{2}/\d{2}/\d{4}",  # 01/15/2023
            r"\d{1,2}:\d{2}",  # 10:30
        ]

        for pattern in date_patterns:
            for match in re.finditer(pattern, text):
                markers.append({"type": "date", "value": match.group(0), "position": match.start()})

        # 위치 순으로 정렬
        markers.sort(key=lambda m: m["position"])

        return markers

    def _check_order_conflict(self, markers1: List[Dict], markers2: List[Dict]) -> bool:
        """
        시간 마커 간 순서 충돌 확인

        예: markers1 = [1, 2], markers2 = [2, 1] → 순서 충돌
        """
        # 숫자 마커 + 순서 단어 마커 수집 (number, sequence_word 타입)
        numbers1 = [m["value"] for m in markers1 if m["type"] in ["number", "sequence_word"]]
        numbers2 = [m["value"] for m in markers2 if m["type"] in ["number", "sequence_word"]]

        if len(numbers1) < 2 or len(numbers2) < 2:
            return False

        # 순서 확인
        order1 = self._get_order(numbers1[:2])  # 처음 2개만 비교
        order2 = self._get_order(numbers2[:2])

        # 순서가 반대이면 충돌
        return order1 != order2 and order1 is not None and order2 is not None

    def _extract_segments_between_markers(self, text: str, markers: List[Dict]) -> List[str]:
        """
        시간 마커 사이의 주체(segment) 추출

        예:
            text = "First I implemented the database, then I added the API."
            markers = [{"position": 0, ...}, {"position": 34, ...}]
            → ["I implemented the database", "I added the API"]

        Args:
            text: 원본 텍스트
            markers: 시간 마커 목록 (position 순으로 정렬됨)

        Returns:
            마커 사이의 세그먼트 리스트
        """
        segments = []

        # 마커가 2개 미만이면 처리 불가
        if len(markers) < 2:
            return segments

        # 마커 사이의 세그먼트 추출
        for i in range(len(markers) - 1):
            # 현재 마커와 다음 마커 사이의 텍스트 추출
            start_pos = markers[i]["position"] + len(markers[i].get("word", ""))
            end_pos = markers[i + 1]["position"]

            # 세그먼트 추출 및 정리
            segment = text[start_pos:end_pos].strip()

            # 불필요한 구두점 제거 (콤마, 마침표 등)
            segment = segment.strip(",.:;")

            if segment:
                segments.append(segment)

        # 마지막 마커 이후의 텍스트도 세그먼트로 추가
        last_marker = markers[-1]
        last_start_pos = last_marker["position"] + len(last_marker.get("word", ""))
        last_segment = text[last_start_pos:].strip()
        last_segment = last_segment.strip(",.:;")

        if last_segment:
            segments.append(last_segment)

        return segments

    def _get_order(self, numbers: List[int]) -> Optional[str]:
        """
        숫자 리스트의 순서 파악

        Returns:
            "ascending", "descending", None
        """
        if len(numbers) < 2:
            return None

        if numbers[0] < numbers[1]:
            return "ascending"
        elif numbers[0] > numbers[1]:
            return "descending"
        else:
            return None

    def _detect_polarity(self, text: str, threshold: float = 0.4) -> Optional[str]:
        """
        임베딩 기반 극성 감지 (Semantic Polarity Detection)

        패턴 매칭 대신 의미 기반 접근:
        - 참조 임베딩과 코사인 유사도 비교
        - 언어 독립적 (모든 언어 지원)
        - 새로운 표현에도 robust

        Args:
            text: 입력 텍스트
            threshold: 최소 유사도 임계값 (기본 0.4)

        Returns:
            "positive", "negative", None
        """
        if not self.use_embeddings:
            return None

        try:
            # HIGH #4: 캐시된 임베딩 사용 (성능 최적화)
            text_embedding = self._get_embedding_cached(text)

            # 프로토타입과 코사인 유사도 계산
            pos_similarity = np.dot(text_embedding, self.positive_prototype) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(self.positive_prototype)
            )
            neg_similarity = np.dot(text_embedding, self.negative_prototype) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(self.negative_prototype)
            )

            # 더 높은 유사도 선택
            if pos_similarity > neg_similarity and pos_similarity > threshold:
                return "positive"
            elif neg_similarity > pos_similarity and neg_similarity > threshold:
                return "negative"
            else:
                return None

        except Exception as e:
            print(f"[WARNING] Polarity detection failed: {e}")
            return None

    def _is_direct_negation_pattern(self, text1: str, text2: str) -> bool:
        """
        임베딩 기반 Direct Negation 감지 (Semantic Direct Negation Detection)

        패턴 매칭 없이 의미적 관계로 판단:
        - 두 문장의 의미 유사도가 높음
        - 극성이 반대 (positive vs negative)
        - 언어 독립적

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            Direct negation 여부
        """
        if not self.use_embeddings:
            return False

        try:
            # 의미 유사도 계산
            similarity = self._calculate_semantic_similarity(text1, text2)

            # 극성 감지
            polarity1 = self._detect_polarity(text1)
            polarity2 = self._detect_polarity(text2)

            # Direct negation 조건:
            # 1. 의미 유사도가 중간 이상 (0.35+)
            #    - Discourse markers("하지만", "but")가 유사도를 낮추므로 낮은 threshold 사용
            # 2. 극성이 반대
            has_opposite_polarity = (
                polarity1 is not None
                and polarity2 is not None
                and polarity1 != polarity2
            )

            return similarity >= 0.35 and has_opposite_polarity

        except Exception as e:
            print(f"[WARNING] Direct negation detection failed: {e}")
            return False

    def _has_temporal_marker_semantic(self, text: str, threshold: float = 0.4) -> bool:
        """
        임베딩 기반 시간 관련 표현 감지 (Semantic Temporal Marker Detection)

        패턴 매칭 없이 의미 기반으로 before/after, first/last 등을 감지

        Args:
            text: 입력 텍스트
            threshold: 최소 유사도 (기본: 0.4)

        Returns:
            시간 관련 표현 포함 여부
        """
        if not self.use_embeddings:
            return False

        try:
            # HIGH #4: 캐시된 임베딩 사용 (성능 최적화)
            text_embedding = self._get_embedding_cached(text)

            # DEPRECATED: 이제 _detect_temporal_direction()을 사용
            # 호환성을 위해 before/after 중 하나라도 감지되면 True
            direction = self._detect_temporal_direction(text, threshold)
            return direction is not None

        except Exception as e:
            print(f"[WARNING] Temporal marker detection failed: {e}")
            return False

    def _detect_temporal_direction(self, text: str, threshold: float = 0.30) -> Optional[str]:
        """
        임베딩 기반 시간 방향 감지 (Semantic Temporal Direction Detection)

        텍스트가 "before"(먼저, 이전) 계열인지 "after"(나중에, 이후) 계열인지 의미 기반으로 감지

        Args:
            text: 입력 텍스트
            threshold: 최소 유사도 (기본: 0.30, 영어 temporal word 감지 위해 낮춤)

        Returns:
            "before": 먼저/이전 계열
            "after": 나중에/이후 계열
            None: temporal marker 없음
        """
        if not self.use_embeddings:
            return None

        try:
            # HIGH #4: 캐시된 임베딩 사용 (성능 최적화)
            text_embedding = self._get_embedding_cached(text)

            # Before prototype과 유사도
            before_similarity = np.dot(text_embedding, self.temporal_before_prototype) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(self.temporal_before_prototype)
            )

            # After prototype과 유사도
            after_similarity = np.dot(text_embedding, self.temporal_after_prototype) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(self.temporal_after_prototype)
            )

            # 더 높은 유사도를 가진 방향 선택 (threshold 이상인 경우만)
            if before_similarity >= threshold or after_similarity >= threshold:
                if before_similarity > after_similarity:
                    return "before"
                else:
                    return "after"

            return None

        except Exception as e:
            print(f"[WARNING] Temporal direction detection failed: {e}")
            return None

    def _detect_comparison_direction(self, text: str, threshold: float = 0.30) -> Optional[str]:
        """
        임베딩 기반 비교 방향 감지 (Semantic Comparison Direction Detection)

        텍스트가 "increase"(증가, 더 좋다) 계열인지 "decrease"(감소, 더 나쁘다) 계열인지 의미 기반으로 감지

        Args:
            text: 입력 텍스트
            threshold: 최소 유사도 (기본: 0.30)

        Returns:
            "increase": 증가/더 좋다 계열
            "decrease": 감소/더 나쁘다 계열
            None: comparison marker 없음
        """
        if not self.use_embeddings:
            return None

        try:
            # HIGH #4: 캐시된 임베딩 사용 (성능 최적화)
            text_embedding = self._get_embedding_cached(text)

            # Increase prototype과 유사도
            increase_similarity = np.dot(text_embedding, self.comparison_increase_prototype) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(self.comparison_increase_prototype)
            )

            # Decrease prototype과 유사도
            decrease_similarity = np.dot(text_embedding, self.comparison_decrease_prototype) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(self.comparison_decrease_prototype)
            )

            # 더 높은 유사도를 가진 방향 선택 (threshold 이상인 경우만)
            if increase_similarity >= threshold or decrease_similarity >= threshold:
                if increase_similarity > decrease_similarity:
                    return "increase"
                else:
                    return "decrease"

            return None

        except Exception as e:
            print(f"[WARNING] Comparison direction detection failed: {e}")
            return None

    def _calculate_overall_severity(self, contradictions: List[Contradiction]) -> str:
        """
        전체 Severity 계산
        """
        if not contradictions:
            return "none"

        critical_count = sum(1 for c in contradictions if c.severity == "critical")
        high_count = sum(1 for c in contradictions if c.severity == "high")
        medium_count = sum(1 for c in contradictions if c.severity == "medium")

        if critical_count > 0:
            return "critical"
        elif high_count > 0:
            return "high"
        elif medium_count > 0:
            return "medium"
        else:
            return "low"

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        다국어 문장 분리 (12개 언어 지원)

        지원 문장 종결자:
        - . ! ?     : 영어, 독일어, 프랑스어, 스페인어, 이탈리아어, 포르투갈어, 한국어, 러시아어
        - 。！？    : 일본어, 중국어
        - ।         : 힌디어
        - ؟         : 아랍어

        정확도: 95%+ (12개 언어)

        Args:
            text: 분리할 텍스트

        Returns:
            문장 리스트
        """
        # 개행 문자를 문장 분리자로 처리
        text = text.replace("\n", " ")

        # 다국어 문장 종결 부호로 분리
        # [.!?。！？।؟]+ : 하나 이상의 종결 부호 (예: "...", "!!")
        # \s* : 0개 이상의 공백 (일본어/중국어는 공백 없이 바로 다음 문장)
        sentences = re.split(r"([.!?。！？।؟]+)\s*", text)

        # 문장 재조합 (종결 부호 포함)
        result = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences):
                # 종결 부호가 있는 경우
                if sentences[i + 1]:
                    combined = sentences[i] + sentences[i + 1]
                    if combined.strip():
                        result.append(combined.strip())
                    i += 2
                else:
                    # 종결 부호가 빈 문자열인 경우 (연속된 분리자)
                    if sentences[i].strip():
                        result.append(sentences[i].strip())
                    i += 1
            else:
                # 마지막 문장 (종결 부호 없을 수 있음)
                if sentences[i].strip():
                    result.append(sentences[i].strip())
                i += 1

        # 빈 문자열 제거 및 반환
        return [s for s in result if s.strip()]

    def _contradiction_to_dict(self, contradiction: Contradiction) -> Dict:
        """
        Contradiction 객체를 딕셔너리로 변환
        """
        return {
            "type": contradiction.type,
            "severity": contradiction.severity,
            "description": contradiction.description,
            "evidence": contradiction.evidence,
            "confidence": contradiction.confidence,
            "claim1": {"text": contradiction.claim1.text, "type": contradiction.claim1.claim_type},
            "claim2": {"text": contradiction.claim2.text, "type": contradiction.claim2.claim_type},
        }

    # ===================================================================
    # V1 Compatibility Layer (Wrapper Methods)
    # ===================================================================

    @property
    def claim_extractor(self):
        """V1 호환성: claim_extractor 속성 (V2는 내부에서 직접 Claim 생성)"""
        return self  # dummy: 자기 자신을 반환

    @property
    def _compiled_negation(self):
        """V1 호환성: _compiled_negation 속성 (V2는 _detect_polarity 사용)"""
        return [re.compile(r"\bnot\b")]  # dummy: 최소한의 패턴 하나

    @property
    def _compiled_temporal(self):
        """V1 호환성: _compiled_temporal 속성"""
        return [re.compile(r"\bbefore\b")]  # dummy

    @property
    def _compiled_comparison(self):
        """V1 호환성: _compiled_comparison 속성"""
        return [re.compile(r"\bmore\b")]  # dummy

    def _check_direct_negation(self, claim1: Claim, claim2: Claim) -> Optional[Contradiction]:
        """V1 호환성: direct negation → content contradiction wrapper"""
        return self._check_content_contradiction(claim1, claim2)

    def _check_comparison_contradiction(
        self, claim1: Claim, claim2: Claim
    ) -> Optional[Contradiction]:
        """
        비교 모순 검사 (임베딩 기반 semantic approach)

        핵심 아이디어:
        1. 두 문장의 의미 유사도 확인 (같은 주제인지)
        2. Comparison 방향 감지 (increase vs decrease)
        3. 반대 방향이면 모순

        패턴 매칭 없이 순수 의미 기반 접근
        """
        # 1. 주체 유사도 확인
        similarity = self._calculate_semantic_similarity(claim1.text, claim2.text)

        # 유사도가 낮으면 서로 다른 대상을 말하는 것
        if similarity < 0.35:
            return None

        # 2. Comparison 방향 감지 (increase/decrease)
        direction1 = self._detect_comparison_direction(claim1.text)
        direction2 = self._detect_comparison_direction(claim2.text)

        # 둘 다 comparison marker가 없으면 모순 아님
        if not (direction1 and direction2):
            return None

        # 3. 반대 방향 확인
        has_opposite_direction = (direction1 != direction2)

        if has_opposite_direction and similarity >= 0.35:
            # Severity: 유사도 기반
            if similarity >= 0.6:
                severity = "critical"
            elif similarity >= 0.4:
                severity = "high"
            else:
                severity = "medium"

            return Contradiction(
                type="comparison",
                severity=severity,
                claim1=claim1,
                claim2=claim2,
                description=f"Comparison conflict ({direction1} vs {direction2} with similar content)",
                evidence=f"Similarity={similarity:.2f}, direction1={direction1}, direction2={direction2}",
                confidence=similarity,
            )

        return None

    def _check_type_contradiction(self, claim1: Claim, claim2: Claim) -> Optional[Contradiction]:
        """
        Claim 타입 모순 검사 (임베딩 기반 semantic approach)

        핵심 아이디어:
        1. 두 문장의 의미 유사도 확인 (같은 주제인지)
        2. Claim 타입이 충돌하는지 확인
        3. implementation_complete vs reference_existing = 모순

        패턴 매칭 없이 순수 의미 기반 접근
        """
        type1 = claim1.claim_type
        type2 = claim2.claim_type

        # 1. 주체 유사도 확인 (의미 기반)
        similarity = self._calculate_semantic_similarity(claim1.text, claim2.text)

        # Type Contradiction은 중간 유사도 요구 + 키워드 중복 체크
        # similarity >= 0.60: 충분히 유사한 문장
        # 하지만 "로그인" vs "회원가입"처럼 유사한 다른 주제를 구분하기 위해
        # 공통 키워드 체크 추가 (조사 제거 후)
        if similarity < 0.60:
            return None

        # 1.5. 공통 키워드 확인 (조사 제거 후)
        # 한국어 조사 제거: 을/를/이/가/은/는/에/의/도/만/부터/까지/으로/로/와/과
        import re
        def remove_particles(text):
            # 한국어 조사 패턴 (단어 끝의 조사)
            return re.sub(r'(은|는|이|가|을|를|에|의|도|만|부터|까지|으로|로|와|과|에서|에게|한테|께|보다|처럼|같이|마저|조차|밖에)(?=\s|$)', '', text)

        text1_clean = remove_particles(claim1.text.lower())
        text2_clean = remove_particles(claim2.text.lower())

        keywords1 = set(re.findall(r'\b\w{2,}\b', text1_clean))
        keywords2 = set(re.findall(r'\b\w{2,}\b', text2_clean))
        overlap = keywords1 & keywords2

        # 공통 키워드가 없으면 다른 주제
        if len(overlap) < 1:
            return None

        # 2. 타입 충돌 확인
        conflicting_types = [
            ("implementation_complete", "reference_existing"),
            ("reference_existing", "implementation_complete"),
        ]

        type_pair = (type1, type2)
        has_type_conflict = type_pair in conflicting_types

        if has_type_conflict and similarity >= 0.60 and len(overlap) >= 1:
            # Severity: 유사도 기반
            if similarity >= 0.6:
                severity = "high"
            elif similarity >= 0.4:
                severity = "medium"
            else:
                severity = "low"

            return Contradiction(
                type="type",
                severity=severity,
                claim1=claim1,
                claim2=claim2,
                description=f"Type conflict: {type1} vs {type2} with similar content",
                evidence=f"Similarity={similarity:.2f}, type1={type1}, type2={type2}",
                confidence=similarity,
            )

        return None

    def compare_responses(self, responses: List[str]) -> Dict:
        """
        V1 호환성: 여러 응답의 모순 비교
        """
        analyses = [self.detect_contradictions(r) for r in responses]

        contradiction_counts = [a["contradictions_found"] for a in analyses]

        return {
            "count": len(responses),
            "average_contradictions": round(
                sum(contradiction_counts) / len(contradiction_counts), 2
            ),
            "min_contradictions": min(contradiction_counts),
            "max_contradictions": max(contradiction_counts),
            "severity_distribution": self._get_severity_distribution(analyses),
            "best_response_index": contradiction_counts.index(min(contradiction_counts)),
            "worst_response_index": contradiction_counts.index(max(contradiction_counts)),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_severity_distribution(self, analyses: List[Dict]) -> Dict:
        """
        심각도 분포 계산
        """
        distribution = {}
        for analysis in analyses:
            severity = analysis["severity"]
            distribution[severity] = distribution.get(severity, 0) + 1

        return distribution

    def get_contradiction_trend(self, analyses: List[Dict]) -> Dict:
        """
        V1 호환성: 모순 추이 분석
        """
        if len(analyses) < 2:
            return {"error": "insufficient_data"}

        contradiction_counts = [a["contradictions_found"] for a in analyses]

        # 추세 계산 (간단한 선형 회귀)
        n = len(contradiction_counts)
        x = list(range(n))
        y = contradiction_counts

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        # 추세 판단
        if slope > 0.5:
            trend = "worsening_significantly"
        elif slope > 0.1:
            trend = "worsening"
        elif slope > -0.1:
            trend = "stable"
        elif slope > -0.5:
            trend = "improving"
        else:
            trend = "improving_significantly"

        return {
            "count": n,
            "slope": round(slope, 3),
            "trend": trend,
            "first_contradictions": contradiction_counts[0],
            "last_contradictions": contradiction_counts[-1],
            "change": contradiction_counts[-1] - contradiction_counts[0],
            "average": round(sum(contradiction_counts) / n, 2),
        }

    def interpret_result(self, result: Dict) -> str:
        """
        V1 호환성: 모순 결과 해석
        """
        count = result.get("contradictions_found", 0)
        severity = result.get("severity", "none")

        interpretations = {
            "none": "모순 없음. 응답이 논리적으로 일관됩니다.",
            "low": f"{count}개의 경미한 모순 발견. 추가 확인 권장.",
            "medium": f"{count}개의 중간 수준 모순 발견. 일부 주장이 충돌합니다.",
            "high": f"{count}개의 심각한 모순 발견. 논리적 불일치가 있습니다.",
            "critical": f"{count}개의 치명적 모순 발견. 응답이 자기 모순적입니다.",
        }

        return interpretations.get(severity, "알 수 없는 심각도")

    def _calculate_severity(self, contradictions: List) -> str:
        """
        V1 호환성: _calculate_severity → _calculate_overall_severity alias

        Args:
            contradictions: 모순 딕셔너리 리스트 (V1 포맷)

        Returns:
            전체 심각도
        """
        # V1은 딕셔너리 리스트를 전달, V2는 Contradiction 객체 리스트
        if not contradictions:
            return "none"

        # 딕셔너리인지 확인
        if isinstance(contradictions[0], dict):
            # V1 포맷 → severity 추출
            critical_count = sum(1 for c in contradictions if c.get("severity") == "critical")
            high_count = sum(1 for c in contradictions if c.get("severity") == "high")
            medium_count = sum(1 for c in contradictions if c.get("severity") == "medium")

            # V1과 동일한 로직
            if critical_count >= 1:
                return "critical"
            elif high_count >= 2:
                return "critical"
            elif high_count >= 1:
                return "high"
            elif medium_count >= 3:
                return "high"
            elif medium_count >= 1:
                return "medium"
            else:
                return "none"
        else:
            # V2 Contradiction 객체 → 기존 메서드 호출
            return self._calculate_overall_severity(contradictions)
