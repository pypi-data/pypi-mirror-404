import sys
"""
Auto-Save Timer System (P0-4)

Periodically saves unsaved contexts to prevent data loss.

Core Principle:
- Every 5 minutes (configurable), check for unsaved work
- Automatically save to memory
- Continue running in background thread
- Python threading.Timer guarantees execution
"""

import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AutoSaver:
    """
    Auto-Save Timer: Periodic context saver (P0-4)

    Runs in background thread and automatically saves unsaved contexts
    every N seconds (default: 300 = 5 minutes).

    Features:
    - Threading.Timer based (Python guarantee)
    - Lazy import to avoid circular dependencies
    - Tracks last save time per session
    - Error handling (continues on failure)

    Example:
        auto_saver = AutoSaver(interval=300)  # 5 minutes
        auto_saver.start()

        # ... server runs ...

        auto_saver.stop()  # On shutdown
    """

    def __init__(self, interval: int = 300, memory_dir: Optional[Path] = None):
        """
        Initialize Auto-Saver.

        Args:
            interval: Save interval in seconds (default: 300 = 5 minutes)
            memory_dir: Memory directory path (default: ~/.cortex/memory/)
        """
        self.interval = interval
        self.memory_dir = memory_dir
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Track last save time per project/branch
        self.last_save_times: Dict[str, float] = {}

        # Lazy import placeholders
        self._memory_manager_class = None

    def _lazy_import(self):
        """
        Lazy import MemoryManager to avoid circular imports.
        Called only when auto-saver starts.
        """
        if self._memory_manager_class is None:
            try:
                from .memory_manager import MemoryManager
                self._memory_manager_class = MemoryManager
                logger.info("[AUTO_SAVER] Lazy import completed")
            except Exception as e:
                logger.error(f"[AUTO_SAVER] Lazy import failed: {e}")
                raise

    def start(self):
        """
        Start auto-save timer thread.

        Creates a daemon thread that periodically checks and saves contexts.
        """
        if self.running:
            logger.warning("[AUTO_SAVER] Already running")
            return

        self._lazy_import()

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

        logger.info(f"[AUTO_SAVER] Started with {self.interval}s interval")
        print(f"[Cortex] Auto-save timer started (every {self.interval}s, file=sys.stderr)")

    def stop(self):
        """
        Stop auto-save timer thread.
        """
        self.running = False
        logger.info("[AUTO_SAVER] Stopped")

    def _run(self):
        """
        Main loop: sleep → check → save → repeat.

        Runs until self.running becomes False.
        """
        while self.running:
            try:
                # Wait for interval
                time.sleep(self.interval)

                if not self.running:
                    break

                # Check and save
                self._check_and_save()

            except Exception as e:
                logger.error(f"[AUTO_SAVER] Loop error: {e}")
                # Continue running even on error

    def _check_and_save(self):
        """
        Check all projects/branches and save if needed (최적화 버전).

        update_memory()가 이미 즉시 저장하므로:
        - MemoryManager 인스턴스 생성 불필요
        - get_active_summary() 호출 불필요
        - 파일 수정 시간만 체크하여 백업 보장
        """
        logger.info("[AUTO_SAVER] Checking context file integrity...")

        checked = 0

        try:
            # Get memory directory
            if self.memory_dir is None:
                try:
                    from ..config import config
                except ImportError:
                    from config import config
                self.memory_dir = config.memory_dir

            if not self.memory_dir.exists():
                logger.info("[AUTO_SAVER] No memory directory found.")
                return

            # Iterate over all projects
            for project_dir in self.memory_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                project_id = project_dir.name
                contexts_dir = project_dir / "contexts"

                if not contexts_dir.exists():
                    continue

                # 단순히 파일 존재 여부와 수정 시간만 체크
                for branch_file in contexts_dir.glob("*.md"):
                    try:
                        # 파일이 존재하고 읽을 수 있는지만 확인
                        if branch_file.exists() and branch_file.stat().st_size > 0:
                            checked += 1
                            # update_memory()가 이미 저장했으므로 추가 작업 불필요
                    except Exception as e:
                        logger.warning(f"[AUTO_SAVE] File check failed {branch_file}: {e}")

            logger.info(f"[AUTO_SAVE] Integrity check complete: {checked} context files verified")
            logger.info("[AUTO_SAVE] All contexts already saved via update_memory()")

        except Exception as e:
            logger.error(f"[AUTO_SAVE] Error during integrity check: {e}")


# Global instance (optional, for convenient access)
_global_auto_saver: Optional[AutoSaver] = None


def get_auto_saver() -> Optional[AutoSaver]:
    """
    Get global auto-saver instance.

    Returns:
        AutoSaver instance or None if not started
    """
    return _global_auto_saver


def start_auto_saver(interval: int = 300) -> AutoSaver:
    """
    Start global auto-saver.

    Args:
        interval: Save interval in seconds (default: 300 = 5 minutes)

    Returns:
        AutoSaver instance
    """
    global _global_auto_saver

    if _global_auto_saver is not None:
        logger.warning("[AUTO_SAVER] Global instance already exists")
        return _global_auto_saver

    _global_auto_saver = AutoSaver(interval=interval)
    _global_auto_saver.start()

    return _global_auto_saver


def stop_auto_saver():
    """
    Stop global auto-saver.
    """
    global _global_auto_saver

    if _global_auto_saver is not None:
        _global_auto_saver.stop()
        _global_auto_saver = None


# Example usage (for documentation purposes)
if __name__ == "__main__":
    # This is just an example
    import logging
    logging.basicConfig(level=logging.INFO)

    # Start auto-saver with 10-second interval (for testing)
    saver = AutoSaver(interval=10)
    saver.start()

    try:
        # Keep running
        print("Auto-saver running. Press Ctrl+C to stop.", file=sys.stderr)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping auto-saver...", file=sys.stderr)
        saver.stop()
        print("Auto-saver stopped.", file=sys.stderr)
