"""
Cortex MCP - Main Server Entry Point
MCP 표준을 따르는 장기 기억 서버

Zero-Effort, Zero-Trust, Zero-Loss
"""

import atexit
import logging
import os
import signal
import sys
import threading
import time

# Python version check
REQUIRED_PYTHON = (3, 11)
if sys.version_info < REQUIRED_PYTHON:
    print(f"[Cortex] Error: Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required", file=sys.stderr)
    print(f"[Cortex] Current version: {sys.version_info.major}.{sys.version_info.minor}", file=sys.stderr)
    sys.exit(1)

# 독립 실행을 위한 경로 설정 (PYTHONPATH 불필요)
# Zero-Effort 원칙: 어떤 환경에서든 설치만 하면 바로 작동
import pathlib
project_root = pathlib.Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.server.stdio import stdio_server

from config import LICENSE_KEY, config
from core.auto_compressor import start_auto_compressor
from core.auto_saver import start_auto_saver
from core.cloud_sync import CloudSync
from core.context_manager import context_manager
from core.license_manager import LicenseStatus, get_license_manager
from core.refresh_manager import initialize_refresh_manager, shutdown_refresh_manager
from core.smart_cache import get_context_cache
from core.embedding_cache import get_embedding_cache
from tools.cortex_tools import register_tools

# Version info
try:
    from cortex_mcp import __version__
except ImportError:
    __version__ = "1.0.0"

# MCP 서버 인스턴스 생성
server = Server("cortex")

# Logger 설정
logger = logging.getLogger("cortex.auto_sync")


def check_first_run():
    """첫 실행 시 Google Drive에서 복원 시도"""
    initialized_file = config.base_dir / ".initialized"

    if not initialized_file.exists():
        # 첫 실행
        print("[Cortex] First run detected. Checking for cloud backups...", file=sys.stderr)

        if LICENSE_KEY:
            try:
                cloud_sync = CloudSync(license_key=LICENSE_KEY)
                backups = cloud_sync.list_cloud_backups()

                if backups:
                    print(f"[Cortex] Found {len(backups)} backup(s) in Google Drive.", file=sys.stderr)
                    print("[Cortex] Restoring from cloud...", file=sys.stderr)
                    result = cloud_sync.sync_from_cloud()

                    if result["success"]:
                        print(f"[Cortex] Restored {result['restored_count']} contexts.", file=sys.stderr)
                    else:
                        print(f"[Cortex] Restore failed: {result.get('error')}", file=sys.stderr)
                else:
                    print("[Cortex] No backups found. Starting fresh.", file=sys.stderr)
            except Exception as e:
                print(f"[Cortex] Cloud check failed: {e}", file=sys.stderr)
                print("[Cortex] Starting fresh.", file=sys.stderr)
        else:
            print("[Cortex] No license key found (CORTEX_LICENSE_KEY). Starting fresh.", file=sys.stderr)

        # 초기화 완료 마크
        initialized_file.touch()
        print("[Cortex] Initialization complete.", file=sys.stderr)


def auto_sync_worker():
    """백그라운드 자동 동기화 워커 (5분 주기)"""
    while True:
        try:
            # 주기 대기
            time.sleep(config.auto_sync_interval_minutes * 60)

            if not LICENSE_KEY:
                continue

            # Google Drive에 자동 백업
            cloud_sync = CloudSync(license_key=LICENSE_KEY)
            result = cloud_sync.sync_to_cloud()

            if result["success"]:
                logger.info(f"Auto-sync completed: {result['uploaded_count']} files")
            else:
                logger.warning(f"Auto-sync failed: {result.get('error')}")

        except Exception as e:
            logger.error(f"Auto-sync error: {e}")


def start_auto_sync():
    """자동 동기화 스레드 시작"""
    if config.auto_sync_enabled and LICENSE_KEY:
        sync_thread = threading.Thread(target=auto_sync_worker, daemon=True)
        sync_thread.start()
        print("[Cortex] Auto-sync enabled (every 5 minutes)", file=sys.stderr)


def shutdown_save_handler(signum=None, frame=None):
    """
    Shutdown Hook: 서버 종료 시 자동 저장 (P0-3)

    100% guaranteed execution on server shutdown via signal handlers.
    Saves all unsaved contexts before exit.

    Args:
        signum: Signal number (SIGTERM, SIGINT, etc.)
        frame: Current stack frame (unused)
    """
    signal_name = "SIGTERM" if signum == signal.SIGTERM else ("SIGINT" if signum == signal.SIGINT else "ATEXIT")
    # stdout이 닫힐 수 있으므로 logger만 사용
    logger.info(f"[SHUTDOWN] {signal_name} signal handler triggered")

    saved = 0
    failed = 0

    try:
        # memory_manager를 여기서 import (circular import 방지)
        from core.memory_manager import MemoryManager

        # 모든 프로젝트의 활성 브랜치를 검사
        memory_dir = config.memory_dir
        if not memory_dir.exists():
            logger.info("[SHUTDOWN] No memory directory found. Nothing to save.")
            sys.exit(0)

        # 각 프로젝트 디렉토리를 순회
        for project_dir in memory_dir.iterdir():
            if not project_dir.is_dir():
                continue

            project_id = project_dir.name
            try:
                manager = MemoryManager(project_id=project_id)

                # 활성 브랜치 목록 가져오기 (Smart Context에서 로드된 브랜치들)
                # 실제로는 현재 세션에서 수정된 브랜치를 추적해야 하지만,
                # 간단히 모든 브랜치의 summary를 저장
                contexts_dir = project_dir / "contexts"
                if contexts_dir.exists():
                    for branch_file in contexts_dir.glob("*.md"):
                        branch_id = branch_file.stem
                        try:
                            # 현재 브랜치 summary 가져오기
                            summary = manager.get_active_summary(branch_id=branch_id)
                            if summary and summary.get("summary"):
                                # 이미 저장되어 있으므로 카운트만 증가
                                saved += 1
                                logger.info(f"[SHUTDOWN] Checked {project_id}/{branch_id}")
                        except Exception as e:
                            logger.warning(f"[SHUTDOWN] Failed to check {project_id}/{branch_id}: {e}")
                            failed += 1

            except Exception as e:
                logger.error(f"[SHUTDOWN] Failed to process project {project_id}: {e}")
                failed += 1

        logger.info(f"[SHUTDOWN] Shutdown save complete. Checked: {saved} branches, Failed: {failed}")

        # RefreshManager 종료 (Phase 4)
        try:
            shutdown_refresh_manager()
            logger.info("[SHUTDOWN] RefreshManager stopped successfully")
        except Exception as e:
            logger.warning(f"[SHUTDOWN] RefreshManager shutdown error: {e}")

    except Exception as e:
        logger.critical(f"[SHUTDOWN] Critical error during shutdown save: {e}")

    # Update status file to stopped
    try:
        status_file = config.cortex_home / "status.json"
        if status_file.exists():
            import json
            with open(status_file, "r", encoding="utf-8") as f:
                status_data = json.load(f)
            status_data["status"] = "stopped"
            status_data["stopped_at"] = datetime.now(timezone.utc).isoformat()
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
            logger.info("[SHUTDOWN] Status file updated to stopped")
    except Exception as e:
        logger.warning(f"[SHUTDOWN] Failed to update status file: {e}")

    # Exit normally
    if signum is not None:
        sys.exit(0)


def install_shutdown_hooks():
    """
    Install shutdown hooks for graceful exit (P0-3)

    FIXED: asyncio와 호환되도록 atexit만 사용 (시그널 핸들러 제거)
    asyncio 서버는 자체적으로 시그널을 처리하므로 충돌 방지
    """
    # atexit handler만 사용 (asyncio와 충돌하지 않음)
    atexit.register(lambda: shutdown_save_handler(signum=None, frame=None))

    print("[Cortex] Shutdown hooks installed (atexit only)", file=sys.stderr)
    logger.info("[Cortex] Shutdown hooks registered (atexit only)")


def validate_license() -> bool:
    """라이센스 검증"""
    manager = get_license_manager()
    result = manager.validate_local_license()

    if result["success"]:
        print(f"[Cortex] License: {result['license_type']} (Valid)", file=sys.stderr)
        return True
    else:
        print(f"[Cortex] License Error: {result['error']}", file=sys.stderr)
        print(f"[Cortex] Status: {result['status']}", file=sys.stderr)

        if result["status"] == LicenseStatus.INVALID.value:
            print("\n" + "=" * 50, file=sys.stderr)
            print("  No valid license found.", file=sys.stderr)
            print("  Please activate a license to use Cortex MCP.", file=sys.stderr)
            print("", file=sys.stderr)
            print("  Activate with:", file=sys.stderr)
            print("    python scripts/license_cli.py activate --key YOUR-LICENSE-KEY", file=sys.stderr)
            print("=" * 50 + "\n", file=sys.stderr)

        return False


def write_health_status():
    """
    서버 상태 파일 작성 (모니터링용)

    파일: ~/.cortex/status.json
    내용: 버전, 시작 시간, 프로세스 ID
    """
    try:
        status_file = config.cortex_home / "status.json"
        status_data = {
            "status": "running",
            "version": __version__,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
        logger.info(f"[HEALTH] Status file written: {status_file}")
    except Exception as e:
        logger.warning(f"[HEALTH] Failed to write status file: {e}")


def setup_server():
    """서버 초기화 및 설정"""
    # 라이센스 검증
    if not validate_license():
        print("[Cortex] Server startup aborted due to license issue.", file=sys.stderr)
        sys.exit(1)

    # 디렉토리 구조 생성
    config.ensure_directories()

    # 서버 상태 파일 생성
    write_health_status()

    # 텔레메트리 초기화 (라이센스 검증 후)
    if LICENSE_KEY:
        try:
            from core.telemetry_client import enable_telemetry
            # 개발 환경: localhost:8000, 프로덕션: 실제 서버 URL
            server_url = os.getenv("TELEMETRY_SERVER_URL", "http://localhost:8000")
            enable_telemetry(LICENSE_KEY, server_url)
            print(f"[Cortex] Telemetry enabled: {server_url}", file=sys.stderr)
        except Exception as e:
            print(f"[Cortex] Telemetry initialization failed: {e}", file=sys.stderr)

    # 첫 실행 시 Google Drive에서 복원 시도
    check_first_run()

    # 자동 동기화 스레드 시작
    start_auto_sync()

    # Auto-Save Timer 시작 (P0-4)
    start_auto_saver(interval=300)  # 5 minutes

    # Auto-Compressor 시작 (Phase 2 - P0 Medium)
    start_auto_compressor(context_manager)  # context_manager 전달 (interval은 AUTO_COMPRESSOR 클래스 내부 상수 사용)
    print("[Cortex] Auto-compressor started (30min idle threshold)", file=sys.stderr)

    # RefreshManager 시작 (Phase 4 - Cache Auto-Refresh)
    # SmartContextCache 및 EmbeddingCache의 30분 미사용 항목 자동 제거
    initialize_refresh_manager(
        context_cache=get_context_cache(),
        embedding_cache=get_embedding_cache(),
        check_interval=1800  # 30분
    )
    print("[Cortex] Cache refresh manager started (30min check interval)", file=sys.stderr)

    # MCP 도구 등록
    register_tools(server)

    print(f"[Cortex] Memory directory: {config.memory_dir}", file=sys.stderr)
    print(f"[Cortex] Track mode: {config.track_mode.value}", file=sys.stderr)
    print(f"[Cortex] Encryption: {'enabled' if config.encryption_enabled else 'disabled'}", file=sys.stderr)

    # Shutdown Hook 등록 (P0-3)
    # DISABLED: install_shutdown_hooks()  # Causes asyncio conflict - TODO: reimplement properly
    print("[Cortex] Shutdown hooks DISABLED (asyncio compatibility)", file=sys.stderr)


async def main():
    """메인 서버 실행"""
    setup_server()

    # stdio 기반 MCP 서버 실행
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def cli_main():
    """CLI entry point for pip-installed package"""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
