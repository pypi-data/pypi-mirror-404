#!/usr/bin/env python3
"""
Cortex MCP - Command Line Interface

Entry point for the cortex-mcp command.

Usage:
    cortex-mcp                          # Start MCP server (requires activated license)
    cortex-mcp --license KEY            # Activate license and start
    cortex-mcp --activate KEY           # Activate license only
    cortex-mcp --check                  # Check license status
    cortex-mcp --github-login           # Login with GitHub
    cortex-mcp --update                 # Check for updates from PyPI
    cortex-mcp --version                # Show version
    cortex-mcp --help                   # Show help
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).parent))


def get_version():
    """Get package version"""
    try:
        from . import __version__

        return __version__
    except ImportError:
        return "1.0.0"


def check_for_updates(silent: bool = False) -> dict:
    """
    PyPI 최신 버전 확인 및 업데이트 알림

    Args:
        silent: True면 업데이트 있을 때만 출력

    Returns:
        dict: {
            "current": 현재 버전,
            "latest": 최신 버전,
            "update_available": 업데이트 가능 여부,
            "error": 에러 메시지 (있으면)
        }
    """
    import requests

    current = get_version()
    result = {
        "current": current,
        "latest": None,
        "update_available": False,
        "error": None
    }

    try:
        response = requests.get(
            "https://pypi.org/pypi/cortex-mcp/json",
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            latest = data["info"]["version"]
            result["latest"] = latest

            # 버전 비교 (simple string comparison for semver)
            if _compare_versions(latest, current) > 0:
                result["update_available"] = True
                if not silent:
                    print("\n" + "=" * 50)
                    print("  [UPDATE AVAILABLE]")
                    print("=" * 50)
                    print(f"  Current version : {current}")
                    print(f"  Latest version  : {latest}")
                    print("")
                    print("  To update, run:")
                    print("    pip install --upgrade cortex-mcp")
                    print("=" * 50 + "\n")
            elif not silent:
                print(f"[INFO] Cortex MCP {current} is up to date.")
        else:
            result["error"] = f"PyPI returned status {response.status_code}"

    except requests.exceptions.Timeout:
        result["error"] = "Connection timeout"
    except requests.exceptions.ConnectionError:
        result["error"] = "No internet connection"
    except Exception as e:
        result["error"] = str(e)

    return result


def _compare_versions(v1: str, v2: str) -> int:
    """
    버전 비교 (semver 형식)

    Returns:
        1 if v1 > v2, -1 if v1 < v2, 0 if equal
    """
    def parse_version(v):
        # "1.0.3" -> [1, 0, 3]
        parts = v.replace("-", ".").replace("_", ".").split(".")
        result = []
        for p in parts:
            try:
                result.append(int(p))
            except ValueError:
                result.append(0)
        return result

    v1_parts = parse_version(v1)
    v2_parts = parse_version(v2)

    # 길이 맞추기
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))

    for a, b in zip(v1_parts, v2_parts):
        if a > b:
            return 1
        elif a < b:
            return -1
    return 0


def check_installation():
    """Check installation and license status"""
    print("\n" + "=" * 50)
    print("  Cortex MCP Installation Check")
    print("=" * 50)

    all_passed = True

    # 1. Check dependencies
    print("\n[1] Dependencies")
    deps = [
        ("mcp", "MCP SDK"),
        ("chromadb", "ChromaDB"),
        ("sentence_transformers", "Sentence Transformers"),
        ("cryptography", "Cryptography"),
    ]

    for module, name in deps:
        try:
            __import__(module)
            print(f"  [PASS] {name}")
        except ImportError:
            print(f"  [FAIL] {name} - not installed")
            all_passed = False

    # 2. Check core modules
    print("\n[2] Core Modules")
    try:
        from core.memory_manager import MemoryManager
        print("  [PASS] MemoryManager")
    except Exception as e:
        print(f"  [FAIL] MemoryManager - {e}")
        all_passed = False

    try:
        from core.rag_engine import RAGEngine
        print("  [PASS] RAGEngine")
    except Exception as e:
        print(f"  [FAIL] RAGEngine - {e}")
        all_passed = False

    # 3. Check license
    print("\n[3] License Status")
    try:
        from core.license_manager import get_license_manager
        manager = get_license_manager()
        result = manager.validate_local_license()

        if result["success"]:
            print(f"  [PASS] License: {result['license_type']}")
            exp = result.get('expires_at') or 'Never'
            print(f"         Expires: {exp}")
        else:
            print(f"  [WARN] {result.get('error', 'No active license')}")
            print("         (Free tier features still available)")
    except Exception as e:
        print(f"  [WARN] License check error: {e}")
        print("         (Free tier features still available)")

    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("  STATUS: READY")
        print("  Cortex MCP is properly installed!")
    else:
        print("  STATUS: ISSUES FOUND")
        print("  Please run: pip install cortex-mcp --upgrade")
    print("=" * 50 + "\n")

    return all_passed


def check_license():
    """Check current license status (legacy alias)"""
    return check_installation()


def activate_license(license_key: str):
    """Activate a license key"""
    from core.license_manager import get_license_manager

    manager = get_license_manager()
    result = manager.activate_license(license_key)

    if result["success"]:
        print("\n" + "=" * 50)
        print("    LICENSE ACTIVATED")
        print("=" * 50)
        print(f"  Status  : {result['status']}")
        print(f"  Type    : {result['license_type']}")
        print(f"  Expires : {result['expires_at'] or 'Never'}")
        print("=" * 50)
        print("\n  Cortex MCP is ready to use!")
        return True
    else:
        print(f"\n[ERROR] Activation failed: {result['error']}")
        if result.get("warning"):
            print(f"  Warning: {result['warning']}")
        return False


def github_login():
    """Login with GitHub"""
    from core.github_auth import get_github_auth

    auth = get_github_auth()

    if auth.is_authenticated():
        user = auth.get_current_user()
        if user:
            print(f"\n[INFO] Already logged in as @{user['login']}")
            return True

    result = auth.authenticate_interactive()
    return result.get("success", False)


def run_server(license_key: str = None):
    """Run the MCP server"""
    from core.license_manager import get_license_manager

    # Check for updates silently at startup (only notify if update available)
    update_result = check_for_updates(silent=True)
    if update_result["update_available"]:
        print(f"\n[UPDATE] New version {update_result['latest']} available (current: {update_result['current']})")
        print("         Run: pip install --upgrade cortex-mcp\n")

    # Check or activate license
    manager = get_license_manager()

    if license_key:
        result = manager.activate_license(license_key)
        if not result["success"]:
            print(f"[ERROR] License activation failed: {result['error']}")
            sys.exit(1)
        print(f"[Cortex] License activated: {result['license_type']}")

    # Validate license
    validation = manager.validate_local_license()
    if not validation["success"]:
        print(f"[ERROR] {validation['error']}")
        print("\nPlease activate a license:")
        print("  cortex-mcp --activate YOUR-LICENSE-KEY")
        print("\nOr login with GitHub:")
        print("  cortex-mcp --github-login")
        sys.exit(1)

    print(f"[Cortex] License: {validation['license_type']} (Valid)")

    # Import and run server
    from main import main as server_main

    asyncio.run(server_main())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        prog="cortex-mcp",
        description="Cortex MCP - Intelligent Long-Term Memory Server for LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cortex-mcp                          Start MCP server
  cortex-mcp --license KEY            Activate license and start
  cortex-mcp --activate KEY           Activate license only
  cortex-mcp --check                  Check license status
  cortex-mcp --github-login           Login with GitHub

For more information, visit: https://github.com/syab726/cortex
        """,
    )

    parser.add_argument("--version", "-v", action="version", version=f"cortex-mcp {get_version()}")

    parser.add_argument(
        "--license", "-l", metavar="KEY", help="Activate license key and start server"
    )

    parser.add_argument(
        "--activate", "-a", metavar="KEY", help="Activate license key (without starting server)"
    )

    parser.add_argument("--check", "-c", action="store_true", help="Check current license status")

    parser.add_argument(
        "--github-login", "-g", action="store_true", help="Login with GitHub account"
    )

    parser.add_argument(
        "--telemetry", choices=["on", "off"], help="Enable or disable anonymous telemetry"
    )

    parser.add_argument(
        "--update", "-u", action="store_true", help="Check for updates from PyPI"
    )

    args = parser.parse_args()

    try:
        # Handle update check
        if args.update:
            result = check_for_updates(silent=False)
            if result["error"]:
                print(f"[WARN] Update check failed: {result['error']}")
            return 0

        # Handle telemetry setting
        if args.telemetry:
            from core.telemetry import get_telemetry

            telemetry = get_telemetry()
            if args.telemetry == "on":
                telemetry.enable()
                print("[Cortex] Telemetry enabled")
            else:
                telemetry.disable()
                print("[Cortex] Telemetry disabled")
            return 0

        # Handle GitHub login
        if args.github_login:
            success = github_login()
            return 0 if success else 1

        # Handle license check
        if args.check:
            success = check_license()
            return 0 if success else 1

        # Handle license activation only
        if args.activate:
            success = activate_license(args.activate)
            return 0 if success else 1

        # Run server (with optional license activation)
        run_server(args.license)
        return 0

    except KeyboardInterrupt:
        print("\n[Cortex] Server stopped")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
