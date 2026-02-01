#!/usr/bin/env python3
"""
Cortex MCP CLI Entry Point

사용법:
    python -m cortex_mcp install    # 간편 설치
    python -m cortex_mcp verify     # 설치 확인
    python -m cortex_mcp            # MCP 서버 시작
"""

import sys


def main():
    """CLI 메인 진입점"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "install":
            # 간편 설치 스크립트 실행
            from cortex_mcp.scripts.install import main as install_main
            install_main()

        elif command == "verify":
            # 설치 확인 스크립트 실행
            from cortex_mcp.scripts.verify_installation import main as verify_main
            verify_main()

        elif command in ("--help", "-h", "help"):
            print("Cortex MCP - Making AI Accountable Over Time")
            print("\n사용법: python -m cortex_mcp [명령]")
            print("\n사용 가능한 명령:")
            print("  install  - Cortex MCP 간편 설치")
            print("  verify   - 설치 확인")
            print("  (없음)   - MCP 서버 시작")

        else:
            print(f"알 수 없는 명령: {command}")
            print("python -m cortex_mcp --help 로 도움말을 확인하세요.")
            sys.exit(1)
    else:
        # 기본: MCP 서버 시작
        from cortex_mcp.main import main as server_main
        import asyncio
        asyncio.run(server_main())


if __name__ == "__main__":
    main()
