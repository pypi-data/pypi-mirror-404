"""
Smart Context Cache - 지능형 컨텍스트 캐싱 시스템

목적:
- 디스크 I/O를 메모리 액세스로 대체 (300배 속도 향상)
- mtime 기반 자동 유효성 검증 (Stale Data 방지)
- LRU 정책으로 메모리 사용량 제한

핵심 원칙:
1. 읽기 전 항상 mtime 검증 (0.0001초 오버헤드)
2. update_memory 후 즉시 캐시 무효화
3. 캐시 실패 시 디스크 폴백 (Graceful Degradation)

작성자: Cortex Team
일자: 2026-01-03
"""

import hashlib
import logging
import os
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class CacheMetadata:
    """캐시 엔트리의 메타데이터"""

    def __init__(self, mtime: float, size: int, hash_value: str):
        self.mtime = mtime  # 파일 수정 시간
        self.size = size  # 파일 크기 (바이트)
        self.hash_value = hash_value  # 내용 해시 (선택적 검증용)
        self.cached_at = time.time()  # 캐싱 시간
        self.hit_count = 0  # 캐시 히트 횟수
        self.last_accessed_at = time.time()  # 마지막 접근 시간 (Phase 4)


class SmartContextCache:
    """
    지능형 컨텍스트 캐시 시스템

    주요 기능:
    - mtime 기반 자동 유효성 검증
    - LRU 정책으로 메모리 제한
    - Thread-Safe 보장
    - 상세한 통계 제공

    사용 예:
        cache = SmartContextCache(max_size=1000)

        # 읽기 (자동 검증 포함)
        content = cache.get("project_id:branch_id:context_id",
                           "/path/to/context.md")

        # 명시적 무효화 (update_memory 후)
        cache.invalidate("project_id:branch_id:context_id")

        # 통계 조회
        stats = cache.get_stats()
    """

    def __init__(self, max_size: int = 1000, enable_hash_check: bool = False):
        """
        Args:
            max_size: 최대 캐시 엔트리 수 (기본 1000개 = 약 50MB)
            enable_hash_check: 내용 해시 검증 활성화 (기본 False, mtime만 사용)
        """
        self.max_size = max_size
        self.enable_hash_check = enable_hash_check

        # LRU 캐시 (OrderedDict로 구현)
        self._content_cache: OrderedDict[str, str] = OrderedDict()
        self._metadata_cache: Dict[str, CacheMetadata] = {}

        # Thread-Safe 잠금 (재진입 가능)
        self._lock = threading.RLock()

        # 통계
        self._stats = {
            "hits": 0,  # 캐시 히트
            "misses": 0,  # 캐시 미스
            "invalidations": 0,  # 무효화 횟수
            "validations": 0,  # 검증 횟수
            "reloads": 0,  # 재로드 횟수
        }

        logger.info(f"[SMART_CACHE] 초기화 완료 (max_size={max_size}, hash_check={enable_hash_check})")

    def get(self, context_id: str, file_path: str) -> Optional[str]:
        """
        컨텍스트 내용 가져오기 (자동 유효성 검증 포함)

        Args:
            context_id: 컨텍스트 고유 ID (예: "project_id:branch_id:context_id")
            file_path: 실제 파일 경로

        Returns:
            컨텍스트 내용 (파일이 없으면 None)

        동작:
            1. 캐시 확인
            2. 캐시 있으면 mtime 검증
            3. 유효하면 반환, 아니면 재로드
            4. 캐시 없으면 디스크 로드 + 캐싱
        """
        with self._lock:
            # Step 1: 캐시 확인
            if context_id in self._content_cache:
                # Step 2: 유효성 검증
                if self._is_valid(context_id, file_path):
                    # 캐시 히트 - LRU 업데이트
                    self._content_cache.move_to_end(context_id)
                    self._metadata_cache[context_id].hit_count += 1
                    self._metadata_cache[context_id].last_accessed_at = time.time()  # Phase 4
                    self._stats["hits"] += 1

                    logger.debug(f"[CACHE HIT] {context_id} (hit_count={self._metadata_cache[context_id].hit_count})")
                    return self._content_cache[context_id]
                else:
                    # 유효성 검증 실패 - 재로드 필요
                    logger.info(f"[CACHE INVALID] {context_id} - 파일 변경 감지, 재로드")
                    self._stats["reloads"] += 1
                    self._invalidate_internal(context_id)

            # Step 3: 캐시 미스 또는 무효화됨 - 디스크 로드
            self._stats["misses"] += 1
            return self._load_and_cache(context_id, file_path)

    def _is_valid(self, context_id: str, file_path: str) -> bool:
        """
        캐시 유효성 검증 (mtime 기반, 선택적 hash 검증)

        Args:
            context_id: 컨텍스트 ID
            file_path: 파일 경로

        Returns:
            유효하면 True, 변경되었으면 False
        """
        self._stats["validations"] += 1

        # 파일 존재 확인
        if not os.path.exists(file_path):
            logger.warning(f"[CACHE VALIDATION] {context_id} - 파일 없음: {file_path}")
            return False

        metadata = self._metadata_cache.get(context_id)
        if not metadata:
            return False

        # mtime 검증 (빠른 체크 - 0.0001초)
        current_mtime = os.path.getmtime(file_path)
        if current_mtime > metadata.mtime:
            logger.debug(f"[CACHE VALIDATION] {context_id} - mtime 변경 감지")
            return False

        # 선택적: 내용 해시 검증 (정확한 체크 - 0.01초)
        if self.enable_hash_check:
            current_hash = self._calculate_hash(file_path)
            if current_hash != metadata.hash_value:
                logger.debug(f"[CACHE VALIDATION] {context_id} - 내용 해시 변경 감지")
                return False

        return True

    def _load_and_cache(self, context_id: str, file_path: str) -> Optional[str]:
        """
        디스크에서 로드 후 캐싱

        Args:
            context_id: 컨텍스트 ID
            file_path: 파일 경로

        Returns:
            파일 내용 (실패 시 None)
        """
        try:
            # 파일 읽기
            if not os.path.exists(file_path):
                logger.warning(f"[CACHE LOAD] {context_id} - 파일 없음: {file_path}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 메타데이터 수집
            stat = os.stat(file_path)
            mtime = stat.st_mtime
            size = stat.st_size
            hash_value = self._calculate_hash(file_path) if self.enable_hash_check else ""

            # LRU 제한 확인
            if len(self._content_cache) >= self.max_size:
                # 가장 오래된 항목 제거
                oldest_id, _ = self._content_cache.popitem(last=False)
                del self._metadata_cache[oldest_id]
                logger.debug(f"[CACHE LRU] 오래된 항목 제거: {oldest_id}")

            # 캐싱
            self._content_cache[context_id] = content
            self._metadata_cache[context_id] = CacheMetadata(mtime, size, hash_value)

            logger.debug(f"[CACHE LOAD] {context_id} - 디스크에서 로드 완료 ({size} bytes)")
            return content

        except Exception as e:
            logger.error(f"[CACHE LOAD ERROR] {context_id} - {e}", exc_info=True)
            return None

    def invalidate(self, context_id: str) -> None:
        """
        캐시 명시적 무효화 (update_memory 후 호출)

        Args:
            context_id: 무효화할 컨텍스트 ID
        """
        with self._lock:
            self._invalidate_internal(context_id)
            self._stats["invalidations"] += 1
            logger.info(f"[CACHE INVALIDATE] {context_id} - 명시적 무효화")

    def _invalidate_internal(self, context_id: str) -> None:
        """내부용 무효화 (잠금 없음)"""
        if context_id in self._content_cache:
            del self._content_cache[context_id]
        if context_id in self._metadata_cache:
            del self._metadata_cache[context_id]

    def clear(self) -> None:
        """전체 캐시 클리어 (세션 재시작 시)"""
        with self._lock:
            count = len(self._content_cache)
            self._content_cache.clear()
            self._metadata_cache.clear()
            logger.info(f"[CACHE CLEAR] 전체 캐시 클리어 ({count}개 항목)")

    def get_stats(self) -> Dict:
        """
        캐시 통계 반환

        Returns:
            {
                "hits": 캐시 히트 수,
                "misses": 캐시 미스 수,
                "hit_rate": 히트율 (0.0 ~ 1.0),
                "size": 현재 캐시 크기,
                "max_size": 최대 크기,
                "memory_usage_mb": 메모리 사용량 (추정),
                ...
            }
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

            # 메모리 사용량 추정 (내용 크기 합산)
            total_bytes = sum(len(content) for content in self._content_cache.values())
            memory_mb = total_bytes / (1024 * 1024)

            return {
                **self._stats,
                "hit_rate": hit_rate,
                "size": len(self._content_cache),
                "max_size": self.max_size,
                "memory_usage_mb": round(memory_mb, 2),
            }

    def _calculate_hash(self, file_path: str) -> str:
        """파일 내용 해시 계산 (SHA256)"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"[HASH ERROR] {file_path} - {e}")
            return ""


# 싱글톤 인스턴스
_context_cache_instance: Optional[SmartContextCache] = None


def get_context_cache() -> SmartContextCache:
    """SmartContextCache 싱글톤 인스턴스 반환"""
    global _context_cache_instance
    if _context_cache_instance is None:
        _context_cache_instance = SmartContextCache(max_size=1000, enable_hash_check=False)
    return _context_cache_instance
