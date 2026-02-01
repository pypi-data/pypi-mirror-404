"""
Embedding Cache - 임베딩 벡터 캐싱 시스템

목적:
- 텍스트 임베딩 생성 비용 절감 (200배 속도 향상)
- 동일 텍스트에 대한 중복 모델 추론 방지
- RAG 검색 성능 최적화

핵심 원칙:
1. 텍스트 내용 해시를 캐시 키로 사용 (파일 무관)
2. LRU 정책으로 메모리 제한
3. 모델 지연 로딩 (필요 시점에만 초기화)

작성자: Cortex Team
일자: 2026-01-03
"""

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingMetadata:
    """임베딩 캐시 엔트리의 메타데이터"""

    def __init__(self, text_length: int, created_at: float):
        self.text_length = text_length  # 원본 텍스트 길이
        self.created_at = created_at  # 생성 시간
        self.hit_count = 0  # 캐시 히트 횟수
        self.last_accessed_at = created_at  # 마지막 접근 시간 (Phase 4)


class EmbeddingCache:
    """
    임베딩 벡터 캐싱 시스템

    주요 기능:
    - 텍스트 → 임베딩 벡터 캐싱 (SHA256 해시 기반)
    - LRU 정책으로 메모리 제한
    - Thread-Safe 보장
    - 모델 지연 로딩 (성능 최적화)

    사용 예:
        cache = EmbeddingCache(max_size=1000)

        # 임베딩 생성 (캐시 확인 → 없으면 모델 추론)
        embedding = cache.get_embedding("검색할 텍스트")

        # 명시적 무효화 (update_memory 후 변경된 텍스트)
        cache.invalidate("이전 텍스트")

        # 통계 조회
        stats = cache.get_stats()
    """

    # 캐싱 대상 텍스트 최대 길이 (100KB)
    MAX_TEXT_LENGTH = 100 * 1024

    def __init__(
        self,
        max_size: int = 1000,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        Args:
            max_size: 최대 캐시 엔트리 수 (기본 1000개 = 약 3MB)
            model_name: SentenceTransformer 모델명
        """
        self.max_size = max_size
        self.model_name = model_name

        # 모델 인스턴스 (지연 로딩)
        self._model = None
        self._model_lock = threading.Lock()

        # LRU 캐시
        self._embedding_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._metadata_cache: Dict[str, EmbeddingMetadata] = {}

        # Thread-Safe 잠금
        self._cache_lock = threading.RLock()

        # 통계
        self._stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "model_inferences": 0,  # 실제 모델 추론 횟수
            "skipped_long_texts": 0,  # 너무 긴 텍스트 스킵
        }

        logger.info(f"[EMBEDDING_CACHE] 초기화 완료 (max_size={max_size}, model={model_name})")

    def _get_model(self):
        """SentenceTransformer 모델 가져오기 (지연 로딩)"""
        if self._model is None:
            with self._model_lock:
                # Double-check locking
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer

                        logger.info(f"[EMBEDDING_CACHE] 모델 로딩 시작: {self.model_name}")
                        self._model = SentenceTransformer(self.model_name)
                        logger.info(f"[EMBEDDING_CACHE] 모델 로딩 완료")
                    except Exception as e:
                        logger.error(f"[EMBEDDING_CACHE] 모델 로딩 실패: {e}", exc_info=True)
                        raise RuntimeError(f"SentenceTransformer 모델 로딩 실패: {e}")
        return self._model

    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        텍스트의 임베딩 벡터 가져오기 (캐시 우선)

        Args:
            text: 임베딩 생성할 텍스트

        Returns:
            임베딩 벡터 (numpy.ndarray, shape: [768]) 또는 None (실패 시)

        동작:
            1. 텍스트 길이 확인 (100KB 초과 시 스킵)
            2. 텍스트 해시 계산
            3. 캐시 확인 → 있으면 반환
            4. 없으면 모델 추론 → 캐싱 → 반환
        """
        # Step 1: 텍스트 길이 확인
        if len(text) > self.MAX_TEXT_LENGTH:
            logger.warning(
                f"[EMBEDDING_CACHE] 텍스트 너무 김 ({len(text)} bytes) - 캐싱 스킵"
            )
            self._stats["skipped_long_texts"] += 1
            # 캐싱 없이 직접 추론
            return self._compute_embedding(text)

        with self._cache_lock:
            # Step 2: 텍스트 해시 계산
            text_hash = self._calculate_hash(text)

            # Step 3: 캐시 확인
            if text_hash in self._embedding_cache:
                # 캐시 히트 - LRU 업데이트
                self._embedding_cache.move_to_end(text_hash)
                self._metadata_cache[text_hash].hit_count += 1
                self._metadata_cache[text_hash].last_accessed_at = time.time()  # Phase 4
                self._stats["hits"] += 1

                logger.debug(
                    f"[EMBEDDING CACHE HIT] hash={text_hash[:8]}... "
                    f"(hit_count={self._metadata_cache[text_hash].hit_count})"
                )
                return self._embedding_cache[text_hash]

            # Step 4: 캐시 미스 - 모델 추론
            self._stats["misses"] += 1
            embedding = self._compute_and_cache(text, text_hash)
            return embedding

    def _compute_embedding(self, text: str) -> Optional[np.ndarray]:
        """모델로 임베딩 계산 (캐싱 없음)"""
        try:
            model = self._get_model()
            embedding = model.encode(text, convert_to_numpy=True)
            self._stats["model_inferences"] += 1
            return embedding
        except Exception as e:
            logger.error(f"[EMBEDDING ERROR] {e}", exc_info=True)
            return None

    def _compute_and_cache(self, text: str, text_hash: str) -> Optional[np.ndarray]:
        """임베딩 계산 후 캐싱"""
        try:
            # 모델 추론
            embedding = self._compute_embedding(text)
            if embedding is None:
                return None

            # LRU 제한 확인
            if len(self._embedding_cache) >= self.max_size:
                # 가장 오래된 항목 제거
                oldest_hash, _ = self._embedding_cache.popitem(last=False)
                del self._metadata_cache[oldest_hash]
                logger.debug(f"[EMBEDDING LRU] 오래된 항목 제거: {oldest_hash[:8]}...")

            # 캐싱
            self._embedding_cache[text_hash] = embedding
            self._metadata_cache[text_hash] = EmbeddingMetadata(
                text_length=len(text), created_at=time.time()
            )

            logger.debug(
                f"[EMBEDDING CACHED] hash={text_hash[:8]}... "
                f"(text_len={len(text)}, vector_dim={embedding.shape[0]})"
            )
            return embedding

        except Exception as e:
            logger.error(f"[EMBEDDING CACHE ERROR] {e}", exc_info=True)
            return None

    def invalidate(self, text: str) -> None:
        """
        특정 텍스트의 캐시 무효화

        Args:
            text: 무효화할 텍스트 (update_memory로 변경된 경우)

        Note:
            텍스트가 변경되면 해시도 바뀌므로, 실제로는 자동 무효화됨.
            이 메서드는 명시적 무효화가 필요한 경우에만 사용.
        """
        with self._cache_lock:
            text_hash = self._calculate_hash(text)
            if text_hash in self._embedding_cache:
                del self._embedding_cache[text_hash]
                del self._metadata_cache[text_hash]
                self._stats["invalidations"] += 1
                logger.info(f"[EMBEDDING INVALIDATE] hash={text_hash[:8]}...")

    def clear(self) -> None:
        """전체 캐시 클리어 (세션 재시작 시)"""
        with self._cache_lock:
            count = len(self._embedding_cache)
            self._embedding_cache.clear()
            self._metadata_cache.clear()
            logger.info(f"[EMBEDDING CACHE CLEAR] 전체 클리어 ({count}개 항목)")

    def get_stats(self) -> Dict:
        """
        캐시 통계 반환

        Returns:
            {
                "hits": 캐시 히트 수,
                "misses": 캐시 미스 수,
                "hit_rate": 히트율,
                "model_inferences": 실제 모델 추론 횟수,
                "size": 현재 캐시 크기,
                "memory_usage_mb": 메모리 사용량 (추정),
                ...
            }
        """
        with self._cache_lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

            # 메모리 사용량 추정 (벡터 크기 합산)
            total_bytes = sum(emb.nbytes for emb in self._embedding_cache.values())
            memory_mb = total_bytes / (1024 * 1024)

            return {
                **self._stats,
                "hit_rate": hit_rate,
                "size": len(self._embedding_cache),
                "max_size": self.max_size,
                "memory_usage_mb": round(memory_mb, 2),
            }

    @staticmethod
    def _calculate_hash(text: str) -> str:
        """텍스트 내용 해시 계산 (SHA256)"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


# 싱글톤 인스턴스
_embedding_cache_instance: Optional[EmbeddingCache] = None


def get_embedding_cache() -> EmbeddingCache:
    """EmbeddingCache 싱글톤 인스턴스 반환"""
    global _embedding_cache_instance
    if _embedding_cache_instance is None:
        _embedding_cache_instance = EmbeddingCache(max_size=1000)
    return _embedding_cache_instance
