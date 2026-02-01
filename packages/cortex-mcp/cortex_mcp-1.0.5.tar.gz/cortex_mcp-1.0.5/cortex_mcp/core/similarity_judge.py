"""
벤더 독립적 유사도 판단 엔진

특징:
- 외부 API 호출 없음 (완전 로컬)
- SharedEmbedder 기반 임베딩 (sentence-transformers)
- 모든 MCP 클라이언트, 모든 AI에서 동일하게 동작

작성일: 2026-01-17
"""

import hashlib
import json
import logging
import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np

from cortex_mcp.core.shared_embedder import get_shared_embedder

logger = logging.getLogger(__name__)


class SimilarityJudge:
    """
    벤더 독립적 유사도 판단 엔진

    모든 AI, 모든 MCP 클라이언트에서 동일하게 동작합니다.
    외부 API 호출 없이 로컬 임베딩만 사용합니다.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        초기화

        Args:
            cache_dir: 캐시 디렉토리 경로 (기본: ~/.cortex/cache/similarity)
        """
        # 캐시 디렉토리 설정
        if cache_dir is None:
            try:
                from cortex_mcp.config import get_cortex_path
                cache_dir = str(get_cortex_path("cache", "similarity"))
            except ImportError:
                cache_dir = str(Path.home() / ".cortex" / "cache" / "similarity")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 캐시 TTL (24시간)
        self.cache_ttl = timedelta(hours=24)

        # 통계
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "calculations": 0,
            "fallback_used": 0,
        }

        # 메모리 캐시 (세션 레벨, 파일 I/O 없이 즉시 반환)
        self._memory_cache: Dict[str, float] = {}
        self._batch_memory_cache: Dict[str, Dict] = {}
        self._cache_lock = threading.Lock()

        # SharedEmbedder (lazy loading)
        self._embedder = None

        logger.info("[SimilarityJudge] 초기화 완료 (벤더 독립적 모드)")

    @property
    def embedder(self):
        """SharedEmbedder 인스턴스 (lazy loading)"""
        if self._embedder is None:
            self._embedder = get_shared_embedder()
        return self._embedder

    def calculate_similarity(
        self,
        text1: str,
        text2: str,
        use_cache: bool = True,
    ) -> float:
        """
        두 텍스트의 의미적 유사도 계산

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            use_cache: 캐시 사용 여부 (기본: True)

        Returns:
            유사도 점수 (0.0 ~ 1.0)
        """
        # 입력 검증
        if not text1 or not text2:
            return 0.0

        # 캐시 키 생성
        cache_key = self._get_cache_key(text1, text2)

        # 캐시 확인
        if use_cache:
            # 1. 메모리 캐시 확인 (가장 빠름)
            with self._cache_lock:
                if cache_key in self._memory_cache:
                    self.stats["cache_hits"] += 1
                    return self._memory_cache[cache_key]

            # 2. 파일 캐시 확인
            cached_score = self._get_cached_score(cache_key)
            if cached_score is not None:
                self.stats["cache_hits"] += 1
                with self._cache_lock:
                    self._memory_cache[cache_key] = cached_score
                return cached_score

            self.stats["cache_misses"] += 1

        # 유사도 계산 (로컬 임베딩)
        try:
            # 두 텍스트의 임베딩 생성 (정규화됨)
            embeddings = self.embedder.encode(
                [text1, text2],
                normalize_embeddings=True,
            )

            # 코사인 유사도 계산 (정규화된 벡터의 내적)
            similarity = float(np.dot(embeddings[0], embeddings[1]))

            # 범위 보정 (0.0 ~ 1.0)
            similarity = max(0.0, min(1.0, similarity))

            self.stats["calculations"] += 1

            # 캐시 저장
            if use_cache:
                with self._cache_lock:
                    self._memory_cache[cache_key] = similarity
                self._save_to_cache(cache_key, similarity)

            return similarity

        except Exception as e:
            logger.warning(f"[SimilarityJudge] 임베딩 계산 실패: {e}")
            self.stats["fallback_used"] += 1
            # 최후의 폴백: Jaccard 유사도
            return self._jaccard_similarity(text1, text2)

    def calculate_similarity_batch(
        self,
        text: str,
        candidates: List[str],
        use_cache: bool = True,
    ) -> List[Dict]:
        """
        하나의 텍스트와 여러 후보 텍스트들의 유사도 일괄 계산

        Args:
            text: 기준 텍스트
            candidates: 비교할 텍스트 목록
            use_cache: 캐시 사용 여부

        Returns:
            [{"text": "...", "similarity": 0.x}, ...]
        """
        if not text or not candidates:
            return []

        results = []

        try:
            # 모든 텍스트를 한 번에 임베딩 (효율적)
            all_texts = [text] + candidates
            embeddings = self.embedder.encode(
                all_texts,
                normalize_embeddings=True,
            )

            text_embedding = embeddings[0]

            for i, candidate in enumerate(candidates):
                candidate_embedding = embeddings[i + 1]
                similarity = float(np.dot(text_embedding, candidate_embedding))
                similarity = max(0.0, min(1.0, similarity))

                results.append({
                    "text": candidate,
                    "similarity": similarity,
                })

                # 개별 캐시 저장
                if use_cache:
                    cache_key = self._get_cache_key(text, candidate)
                    with self._cache_lock:
                        self._memory_cache[cache_key] = similarity

        except Exception as e:
            logger.warning(f"[SimilarityJudge] 배치 계산 실패: {e}")
            # 폴백: 개별 계산
            for candidate in candidates:
                similarity = self._jaccard_similarity(text, candidate)
                results.append({
                    "text": candidate,
                    "similarity": similarity,
                })

        return results

    def classify_to_category(
        self,
        text: str,
        categories: List[Dict],
        use_cache: bool = True,
    ) -> Dict:
        """
        텍스트를 가장 적합한 카테고리로 분류

        Args:
            text: 분류할 텍스트
            categories: [{"name": "카테고리명", "description": "설명"}, ...]
            use_cache: 캐시 사용 여부

        Returns:
            {"category": "선택된_카테고리", "confidence": 0.0~1.0}
        """
        if not categories:
            return {"category": "general", "confidence": 0.5}

        if not text:
            return {"category": categories[0]["name"], "confidence": 0.5}

        # 캐시 키 생성
        cache_key = self._get_batch_cache_key(text, categories)

        # 캐시 확인
        if use_cache:
            with self._cache_lock:
                if cache_key in self._batch_memory_cache:
                    self.stats["cache_hits"] += 1
                    return self._batch_memory_cache[cache_key]

            cached_result = self._get_batch_cached_result(cache_key)
            if cached_result is not None:
                self.stats["cache_hits"] += 1
                with self._cache_lock:
                    self._batch_memory_cache[cache_key] = cached_result
                return cached_result

            self.stats["cache_misses"] += 1

        # 각 카테고리와의 유사도 계산
        try:
            # 텍스트 임베딩
            text_embedding = self.embedder.encode(text, normalize_embeddings=True)

            best_category = None
            best_score = -1.0

            for cat in categories:
                # 카테고리 설명 텍스트 구성
                cat_text = f"{cat['name']} {cat.get('description', '')}"

                # 카테고리 임베딩
                cat_embedding = self.embedder.encode(cat_text, normalize_embeddings=True)

                # 코사인 유사도
                score = float(np.dot(text_embedding, cat_embedding))
                score = max(0.0, min(1.0, score))

                if score > best_score:
                    best_score = score
                    best_category = cat["name"]

            result = {
                "category": best_category or categories[0]["name"],
                "confidence": best_score if best_score >= 0 else 0.5,
            }

            # 캐시 저장
            if use_cache:
                with self._cache_lock:
                    self._batch_memory_cache[cache_key] = result
                self._save_batch_to_cache(cache_key, result)

            return result

        except Exception as e:
            logger.warning(f"[SimilarityJudge] 분류 실패: {e}")
            self.stats["fallback_used"] += 1
            return self._fallback_classify(text, categories)

    def _get_cache_key(self, text1: str, text2: str) -> str:
        """캐시 키 생성 (순서 무관)"""
        # 순서 무관하게 정렬하여 동일한 키 생성
        texts = sorted([text1[:500], text2[:500]])  # 최대 500자
        combined = "|".join(texts)
        return hashlib.sha256(combined.encode()).hexdigest()

    def _get_batch_cache_key(self, text: str, categories: List[Dict]) -> str:
        """배치 분류용 캐시 키"""
        cat_names = "|".join(sorted([cat["name"] for cat in categories]))
        combined = f"{text[:200]}|{cat_names}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _get_cached_score(self, cache_key: str) -> Optional[float]:
        """파일 캐시에서 점수 조회"""
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # TTL 확인
            cached_time = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            if cached_time.tzinfo is None:
                cached_time = cached_time.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - cached_time > self.cache_ttl:
                # 만료된 캐시 삭제
                try:
                    cache_file.unlink()
                except Exception:
                    pass
                return None

            return data["score"]

        except Exception as e:
            logger.debug(f"[SimilarityJudge] 캐시 읽기 실패: {e}")
            return None

    def _save_to_cache(self, cache_key: str, score: float):
        """파일 캐시에 점수 저장"""
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            data = {
                "score": score,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.debug(f"[SimilarityJudge] 캐시 저장 실패: {e}")

    def _get_batch_cached_result(self, cache_key: str) -> Optional[Dict]:
        """배치 캐시에서 결과 조회"""
        cache_file = self.cache_dir / f"batch_{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # TTL 확인
            cached_time = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            if cached_time.tzinfo is None:
                cached_time = cached_time.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - cached_time > self.cache_ttl:
                try:
                    cache_file.unlink()
                except Exception:
                    pass
                return None

            return data["result"]

        except Exception:
            return None

    def _save_batch_to_cache(self, cache_key: str, result: Dict):
        """배치 결과 캐시 저장"""
        cache_file = self.cache_dir / f"batch_{cache_key}.json"

        try:
            data = {
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        폴백: Jaccard 유사도

        임베딩 실패 시에만 사용되는 최후의 수단
        """
        try:
            def extract_words(text: str) -> set:
                text = text.lower()
                # 영숫자 + 한글 추출
                words = re.findall(r"[a-z0-9가-힣]+", text)
                # 2글자 이상만 포함
                return {w for w in words if len(w) >= 2}

            words1 = extract_words(text1)
            words2 = extract_words(text2)

            if not words1 or not words2:
                return 0.5  # 키워드 없으면 중립

            intersection = words1 & words2
            union = words1 | words2

            return len(intersection) / len(union) if union else 0.5

        except Exception:
            return 0.5

    def _fallback_classify(self, text: str, categories: List[Dict]) -> Dict:
        """폴백: 키워드 기반 분류"""
        try:
            text_lower = text.lower()
            text_words = set(re.findall(r"[a-z0-9가-힣]+", text_lower))

            best_category = None
            best_score = 0.0

            for cat in categories:
                cat_text = f"{cat['name']} {cat.get('description', '')}".lower()
                cat_words = set(re.findall(r"[a-z0-9가-힣]+", cat_text))

                if not cat_words:
                    continue

                intersection = text_words & cat_words
                union = text_words | cat_words
                score = len(intersection) / len(union) if union else 0.0

                if score > best_score:
                    best_score = score
                    best_category = cat["name"]

            return {
                "category": best_category or categories[0]["name"],
                "confidence": best_score if best_score > 0 else 0.5,
            }

        except Exception:
            return {
                "category": categories[0]["name"] if categories else "general",
                "confidence": 0.5,
            }

    def get_stats(self) -> Dict:
        """통계 반환"""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = self.stats["cache_hits"] / total if total > 0 else 0

        return {
            **self.stats,
            "cache_hit_rate": f"{hit_rate * 100:.1f}%",
            "total_queries": total,
        }

    def clear_cache(self):
        """캐시 전체 삭제 (메모리 + 파일)"""
        # 메모리 캐시 초기화
        with self._cache_lock:
            self._memory_cache.clear()
            self._batch_memory_cache.clear()

        # 파일 캐시 삭제
        import shutil
        if self.cache_dir.exists():
            try:
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("[SimilarityJudge] 캐시 삭제 완료")
            except Exception as e:
                logger.warning(f"[SimilarityJudge] 캐시 삭제 실패: {e}")


# 싱글톤 인스턴스
_judge_instance: Optional[SimilarityJudge] = None
_judge_lock = threading.Lock()


def get_similarity_judge() -> SimilarityJudge:
    """
    싱글톤 인스턴스 반환

    최초 호출 시에만 인스턴스를 생성하고,
    이후 호출에서는 캐시된 인스턴스를 반환합니다.
    """
    global _judge_instance

    if _judge_instance is not None:
        return _judge_instance

    with _judge_lock:
        if _judge_instance is not None:
            return _judge_instance

        _judge_instance = SimilarityJudge()
        return _judge_instance


def reset_similarity_judge():
    """
    테스트용: 전역 인스턴스 리셋
    """
    global _judge_instance
    with _judge_lock:
        if _judge_instance is not None:
            _judge_instance.clear_cache()
        _judge_instance = None
