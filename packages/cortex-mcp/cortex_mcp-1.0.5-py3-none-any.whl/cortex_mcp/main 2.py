"""
Cortex MCP - Main Server Entry Point
MCP 표준을 따르는 장기 기억 서버

Zero-Effort, Zero-Trust, Zero-Loss
"""

import sys

# Python version check
REQUIRED_PYTHON = (3, 10)
if sys.version_info < REQUIRED_PYTHON:
    print(f"[Cortex] Error: Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required")
    print(f"[Cortex] Current version: {sys.version_info.major}.{sys.version_info.minor}")
    sys.exit(1)

from mcp.server import Server
from mcp.server.stdio import stdio_server

from config import config
from core.license_manager import LicenseStatus, get_license_manager
from tools.cortex_tools import register_tools

# MCP 서버 인스턴스 생성
server = Server("cortex-memory")


def validate_license() -> bool:
    """라이센스 검증"""
    manager = get_license_manager()
    result = manager.validate_local_license()

    if result["success"]:
        print(f"[Cortex] License: {result['license_type']} (Valid)")
        return True
    else:
        print(f"[Cortex] License Error: {result['error']}")
        print(f"[Cortex] Status: {result['status']}")

        if result["status"] == LicenseStatus.INVALID.value:
            print("\n" + "=" * 50)
            print("  No valid license found.")
            print("  Please activate a license to use Cortex MCP.")
            print("")
            print("  Activate with:")
            print("    python scripts/license_cli.py activate --key YOUR-LICENSE-KEY")
            print("=" * 50 + "\n")

        return False


def setup_server():
    """서버 초기화 및 설정"""
    # 라이센스 검증
    if not validate_license():
        print("[Cortex] Server startup aborted due to license issue.")
        sys.exit(1)

    # 디렉토리 구조 생성
    config.ensure_directories()

    # MCP 도구 등록
    register_tools(server)

    print(f"[Cortex] Memory directory: {config.memory_dir}")
    print(f"[Cortex] Track mode: {config.track_mode.value}")
    print(f"[Cortex] Encryption: {'enabled' if config.encryption_enabled else 'disabled'}")


async def main():
    """메인 서버 실행"""
    setup_server()

    # stdio 기반 MCP 서버 실행
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
