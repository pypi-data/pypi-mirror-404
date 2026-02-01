"""
Shared Embedder - 전역 SentenceTransformer 싱글톤

모든 모듈이 동일한 임베딩 모델 인스턴스를 공유합니다.
최초 1회만 로드하고 이후는 캐시된 인스턴스를 반환합니다.

사용법:
    from cortex_mcp.core.shared_embedder import get_shared_embedder

    embedder = get_shared_embedder()
    vectors = embedder.encode(["텍스트1", "텍스트2"])
"""

import os
import threading
import logging
from typing import List, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)

# 전역 싱글톤 인스턴스
_shared_embedder: Optional["SharedEmbedder"] = None
_embedder_lock = threading.Lock()

# 기본 모델 설정 (다국어 지원 - 한국어 포함)
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class SharedEmbedder:
    """
    전역 공유 임베딩 모델

    모든 Cortex 모듈이 이 인스턴스를 공유합니다.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model = None
        self._init_lock = threading.Lock()
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization - 첫 사용 시에만 모델 로드"""
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            try:
                # HuggingFace 오프라인 모드 설정 (네트워크 타임아웃 방지)
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

                from sentence_transformers import SentenceTransformer

                logger.info(f"[SharedEmbedder] 모델 로드 시작: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                self._initialized = True
                logger.info(f"[SharedEmbedder] 모델 로드 완료")

            except Exception as e:
                logger.error(f"[SharedEmbedder] 모델 로드 실패: {e}")
                raise

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        normalize_embeddings: bool = True,
        convert_to_numpy: bool = True,  # 호환성용 - 항상 numpy 반환
    ) -> np.ndarray:
        """
        텍스트를 벡터로 변환

        Args:
            texts: 단일 문자열 또는 문자열 리스트
            batch_size: 배치 크기
            show_progress_bar: 진행 표시줄 표시 여부
            normalize_embeddings: L2 정규화 여부

        Returns:
            numpy 배열 (단일 입력 시 1D, 리스트 입력 시 2D)
        """
        self._ensure_initialized()

        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=normalize_embeddings,
        )

        if single_input:
            return embeddings[0]
        return embeddings

    def get_embedding_dimension(self) -> int:
        """임베딩 차원 반환"""
        self._ensure_initialized()
        return self._model.get_sentence_embedding_dimension()

    @property
    def is_initialized(self) -> bool:
        """초기화 여부"""
        return self._initialized


def get_shared_embedder(model_name: str = DEFAULT_MODEL) -> SharedEmbedder:
    """
    전역 공유 임베딩 인스턴스 반환

    최초 호출 시에만 인스턴스를 생성하고,
    이후 호출에서는 캐시된 인스턴스를 반환합니다.

    Args:
        model_name: 사용할 모델 이름 (첫 호출 시에만 적용)

    Returns:
        SharedEmbedder 인스턴스
    """
    global _shared_embedder

    if _shared_embedder is not None:
        return _shared_embedder

    with _embedder_lock:
        if _shared_embedder is not None:
            return _shared_embedder

        _shared_embedder = SharedEmbedder(model_name)
        return _shared_embedder


def preload_embedder():
    """
    백그라운드에서 임베딩 모델 미리 로드

    세션 시작 시 호출하여 첫 사용 지연을 방지합니다.
    """
    def _load():
        try:
            embedder = get_shared_embedder()
            embedder._ensure_initialized()
            logger.info("[SharedEmbedder] 프리로드 완료")
        except Exception as e:
            logger.error(f"[SharedEmbedder] 프리로드 실패: {e}")

    thread = threading.Thread(target=_load, daemon=True, name="EmbedderPreload")
    thread.start()
    return thread


def reset_shared_embedder():
    """
    테스트용: 전역 인스턴스 리셋
    """
    global _shared_embedder
    with _embedder_lock:
        _shared_embedder = None
