"""
Cortex MCP - Auto Compressor
30분 미사용 Context 자동 압축

기능:
- 백그라운드 타이머로 주기적 압축 체크
- 30분 이상 미사용 Context 자동 압축
- Smart Context 토큰 절감 최적화
"""

import logging
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))
from config import config

logger = logging.getLogger(__name__)


class AutoCompressor:
    """
    Context 자동 압축 관리자

    기능:
    - 30분 미사용 Context 자동 압축
    - 백그라운드 쓰레드로 주기적 체크
    - ContextManager 통합
    """

    # 설정 상수
    IDLE_THRESHOLD_SECONDS = 30 * 60  # 30분
    CHECK_INTERVAL_SECONDS = 5 * 60  # 5분마다 체크

    def __init__(self, context_manager):
        """
        AutoCompressor 초기화

        Args:
            context_manager: ContextManager 인스턴스
        """
        self.context_manager = context_manager
        self._running = False
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

        logger.info("AutoCompressor initialized (idle threshold: %ds)", self.IDLE_THRESHOLD_SECONDS)

    def start(self):
        """자동 압축 시작 (백그라운드 타이머)"""
        with self._lock:
            if self._running:
                logger.warning("AutoCompressor already running")
                return

            self._running = True
            self._schedule_next_check()
            logger.info("AutoCompressor started (check interval: %ds)", self.CHECK_INTERVAL_SECONDS)

    def stop(self):
        """자동 압축 중지"""
        with self._lock:
            if not self._running:
                return

            self._running = False

            if self._timer:
                self._timer.cancel()
                self._timer = None

            logger.info("AutoCompressor stopped")

    def _schedule_next_check(self):
        """다음 압축 체크 스케줄링"""
        if not self._running:
            return

        self._timer = threading.Timer(self.CHECK_INTERVAL_SECONDS, self._compress_idle_contexts)
        self._timer.daemon = True
        self._timer.start()

    def _compress_idle_contexts(self):
        """30분 이상 미사용 Context 압축"""
        try:
            current_time = time.time()
            compressed_count = 0

            # 모든 활성 브랜치의 Context 체크
            idle_contexts = self._get_idle_contexts(current_time)

            for context_info in idle_contexts:
                project_id = context_info["project_id"]
                branch_id = context_info["branch_id"]
                context_id = context_info["context_id"]
                idle_seconds = context_info["idle_seconds"]

                try:
                    # Context 압축
                    result = self.context_manager.compress_context(
                        project_id=project_id,
                        branch_id=branch_id,
                        context_id=context_id
                    )

                    if result.get("compressed"):
                        compressed_count += 1
                        logger.info(
                            f"Auto-compressed context {context_id} (idle: {idle_seconds:.0f}s)"
                        )

                except Exception as e:
                    logger.error(f"Failed to compress context {context_id}: {e}")

            if compressed_count > 0:
                logger.info(f"Auto-compression completed: {compressed_count} contexts compressed")

        except Exception as e:
            logger.error(f"Auto-compression failed: {e}", exc_info=True)

        finally:
            # 다음 체크 스케줄링
            self._schedule_next_check()

    def _get_idle_contexts(self, current_time: float) -> List[Dict[str, Any]]:
        """
        30분 이상 미사용 Context 목록 조회

        Args:
            current_time: 현재 시간 (timestamp)

        Returns:
            Idle context 목록
        """
        idle_contexts = []

        # ContextManager의 활성 브랜치 순회
        with self.context_manager._lock:
            for branch_id, branch_state in self.context_manager._active_branches.items():
                for context_id, context_state in branch_state.contexts.items():
                    # 로드된 Context만 체크 (압축 대상)
                    if not context_state.is_loaded:
                        continue

                    # 마지막 접근 시간 체크
                    idle_seconds = current_time - context_state.last_accessed

                    if idle_seconds >= self.IDLE_THRESHOLD_SECONDS:
                        idle_contexts.append({
                            "project_id": context_state.project_id,
                            "branch_id": context_state.branch_id,
                            "context_id": context_state.context_id,
                            "idle_seconds": idle_seconds,
                            "last_accessed": context_state.last_accessed
                        })

        return idle_contexts

    def get_status(self) -> Dict[str, Any]:
        """현재 AutoCompressor 상태 조회"""
        current_time = time.time()
        idle_contexts = self._get_idle_contexts(current_time)

        return {
            "running": self._running,
            "idle_threshold_seconds": self.IDLE_THRESHOLD_SECONDS,
            "check_interval_seconds": self.CHECK_INTERVAL_SECONDS,
            "idle_contexts_count": len(idle_contexts),
            "idle_contexts": [
                {
                    "context_id": ctx["context_id"],
                    "idle_minutes": round(ctx["idle_seconds"] / 60, 1)
                }
                for ctx in idle_contexts
            ]
        }

    def force_compress_all_idle(self) -> Dict[str, Any]:
        """
        모든 idle context를 즉시 압축 (수동 트리거)

        Returns:
            압축 결과
        """
        current_time = time.time()
        idle_contexts = self._get_idle_contexts(current_time)
        compressed_count = 0
        errors = []

        for context_info in idle_contexts:
            try:
                result = self.context_manager.compress_context(
                    project_id=context_info["project_id"],
                    branch_id=context_info["branch_id"],
                    context_id=context_info["context_id"]
                )

                if result.get("compressed"):
                    compressed_count += 1

            except Exception as e:
                errors.append({
                    "context_id": context_info["context_id"],
                    "error": str(e)
                })

        return {
            "success": True,
            "total_idle": len(idle_contexts),
            "compressed": compressed_count,
            "errors": errors
        }


# 전역 AutoCompressor 인스턴스 (싱글톤)
_auto_compressor: Optional[AutoCompressor] = None


def get_auto_compressor(context_manager=None) -> Optional[AutoCompressor]:
    """
    AutoCompressor 인스턴스 획득 (싱글톤)

    Args:
        context_manager: ContextManager 인스턴스 (최초 초기화 시 필요)

    Returns:
        AutoCompressor 인스턴스 또는 None
    """
    global _auto_compressor

    if _auto_compressor is None and context_manager is not None:
        _auto_compressor = AutoCompressor(context_manager)

    return _auto_compressor


def start_auto_compressor(context_manager) -> AutoCompressor:
    """
    AutoCompressor 시작

    Args:
        context_manager: ContextManager 인스턴스

    Returns:
        AutoCompressor 인스턴스
    """
    compressor = get_auto_compressor(context_manager)
    if compressor:
        compressor.start()
    return compressor


def stop_auto_compressor():
    """AutoCompressor 중지"""
    compressor = get_auto_compressor()
    if compressor:
        compressor.stop()
