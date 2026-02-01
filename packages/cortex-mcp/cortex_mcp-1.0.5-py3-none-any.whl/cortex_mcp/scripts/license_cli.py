#!/usr/bin/env python3
"""
Cortex MCP - License Management CLI
라이센스 생성, 관리, 차단 도구

사용법:
    # 서버 라이센스 활성화 (권장)
    python license_cli.py activate --key ctx_xxxxx --server

    # 로컬 라이센스 생성 (관리자용)
    python license_cli.py generate --type beta_free --email user@example.com

    # 현재 상태 확인 (통합 검증)
    python license_cli.py status

    # 서버 검증 (온라인 필수)
    python license_cli.py verify --key ctx_xxxxx

    # 기타 명령어
    python license_cli.py check        # 로컬 캐시 확인
    python license_cli.py list         # 로컬 라이센스 목록 (관리자)
    python license_cli.py block --key CORTEX-XXXX-XXXX-XXXX-XXXX --reason "abuse"
    python license_cli.py info --key CORTEX-XXXX-XXXX-XXXX-XXXX
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.license_manager import LicenseStatus, LicenseType, get_license_manager


def cmd_generate(args):
    """라이센스 생성"""
    manager = get_license_manager()

    # 타입 변환
    type_map = {
        "beta_free": LicenseType.BETA_FREE,
        "trial": LicenseType.TRIAL,
        "monthly": LicenseType.MONTHLY,
        "yearly": LicenseType.YEARLY,
        "lifetime": LicenseType.LIFETIME,
    }

    license_type = type_map.get(args.type)
    if not license_type:
        print(f"[ERROR] Invalid license type: {args.type}")
        print(f"Valid types: {', '.join(type_map.keys())}")
        return 1

    # 유효 기간 설정
    days_map = {
        "beta_free": None,  # 평생
        "trial": 7,
        "monthly": 30,
        "yearly": 365,
        "lifetime": None,
    }
    days = args.days if args.days else days_map.get(args.type)

    result = manager.generate_license_key(
        license_type=license_type, user_email=args.email, days_valid=days
    )

    if result["success"]:
        print("\n" + "=" * 50)
        print("    LICENSE GENERATED SUCCESSFULLY")
        print("=" * 50)
        print(f"  License Key : {result['license_key']}")
        print(f"  Type        : {result['license_type']}")
        print(f"  Email       : {result['user_email']}")
        print(f"  Expires     : {result['expires_at']}")
        print("=" * 50)
        print("\n  Share this key with the user.")
        print("  They can activate it with:")
        print(f"    python license_cli.py activate --key {result['license_key']}")
        print()
        return 0
    else:
        print(f"[ERROR] {result['error']}")
        return 1


def cmd_activate(args):
    """라이센스 활성화 (서버 또는 로컬)"""
    manager = get_license_manager()

    # 서버 활성화 (권장)
    if args.server:
        print("\n[INFO] Verifying license with server...")
        result = manager.verify_with_server_sync(args.key)
    else:
        # 로컬 활성화 (레거시)
        result = manager.activate_license(args.key)

    if result["success"]:
        print("\n" + "=" * 50)
        print("    LICENSE ACTIVATED")
        print("=" * 50)
        print(f"  Status  : {result['status']}")
        print(f"  Type    : {result.get('license_type', 'unknown')}")
        print(f"  Tier    : {result.get('tier', '-')}")
        print(f"  Expires : {result.get('expires_at') or 'Never'}")
        print(f"  Source  : {result.get('source', 'local')}")
        if result.get("trial"):
            print(f"  Trial   : {result.get('trial_days_remaining', 0)} days remaining")
        if result.get("message"):
            print(f"  Message : {result['message']}")
        print("=" * 50)

        # 파라미터 표시
        params = result.get("params", {})
        if params:
            print("\n  Features Enabled:")
            print(f"    - Ontology     : {'Yes' if params.get('ONTOLOGY_ON') else 'No'}")
            print(f"    - Multi-PC Sync: {'Yes' if params.get('MULTI_PC_SYNC') else 'No'}")
            max_branches = params.get('MAX_BRANCHES', 5)
            print(f"    - Max Branches : {'Unlimited' if max_branches == -1 else max_branches}")

        print("\n  Cortex MCP is ready to use!")
        print()
        return 0
    else:
        print(f"\n[ERROR] License activation failed")
        print(f"  Status  : {result.get('status', 'unknown')}")
        print(f"  Reason  : {result.get('error', 'Unknown error')}")
        print(f"  Source  : {result.get('source', 'unknown')}")
        if result.get("warning"):
            print(f"  Warning : {result['warning']}")
        print()
        return 1


def cmd_verify(args):
    """서버에서 라이센스 검증"""
    manager = get_license_manager()

    print("\n[INFO] Connecting to license server...")
    result = manager.verify_with_server_sync(args.key)

    if result["success"]:
        print("\n" + "=" * 50)
        print("    SERVER VERIFICATION SUCCESS")
        print("=" * 50)
        print(f"  Status  : {result['status']}")
        print(f"  Tier    : {result.get('tier', '-')}")
        print(f"  Type    : {result.get('license_type', '-')}")
        print(f"  Expires : {result.get('expires_at') or 'Never'}")
        print(f"  Source  : {result.get('source', '-')}")
        if result.get("trial"):
            print(f"  Trial   : {result.get('trial_days_remaining', 0)} days remaining")

        # 파라미터 표시
        params = result.get("params", {})
        if params:
            print("\n  Tier Parameters:")
            for key, value in params.items():
                display_value = "Unlimited" if value == -1 else ("Yes" if value is True else ("No" if value is False else value))
                print(f"    - {key}: {display_value}")

        print("=" * 50)
        print("\n  License cached for 72 hours offline use.")
        print()
        return 0
    else:
        print(f"\n[ERROR] Server verification failed")
        print(f"  Reason  : {result.get('error', 'Unknown error')}")
        print(f"  Source  : {result.get('source', 'unknown')}")
        if result.get("source") == "cache":
            print("\n  Using cached license (offline mode)")
        print()
        return 1


def cmd_status(args):
    """통합 라이센스 상태 확인 (권장)"""
    manager = get_license_manager()

    print("\n[INFO] Checking license status...")
    result = manager.validate_license_unified()

    print("\n" + "=" * 50)
    if result["success"]:
        tier = result.get("tier", result.get("license_type", "free"))
        is_premium = tier in ["pro", "premium", "tier_1_pro", "tier_2_premium", "closed_beta", "open_beta"]

        print(f"    LICENSE STATUS: {'PREMIUM' if is_premium else 'FREE'}")
        print("=" * 50)
        print(f"  Status  : {result.get('status', 'active')}")
        print(f"  Tier    : {tier}")
        print(f"  Type    : {result.get('license_type', '-')}")
        print(f"  Expires : {result.get('expires_at') or 'Never'}")
        print(f"  Source  : {result.get('source', '-')}")

        if result.get("cache_valid_until"):
            print(f"  Cache   : Valid until {result['cache_valid_until']}")

        # 파라미터 표시
        params = result.get("params", {})
        if params:
            print("\n  Features:")
            print(f"    - Ontology     : {'Enabled' if params.get('ONTOLOGY_ON') else 'Disabled'}")
            print(f"    - Multi-PC Sync: {'Enabled' if params.get('MULTI_PC_SYNC') else 'Disabled'}")
            max_branches = params.get('MAX_BRANCHES', 5)
            print(f"    - Max Branches : {'Unlimited' if max_branches == -1 else max_branches}")
            confirm = params.get('BRANCHING_CONFIRM_REQUIRED', True)
            print(f"    - Zero-Effort  : {'Yes' if not confirm else 'No (Click Tax)'}")

        if result.get("message"):
            print(f"\n  Note: {result['message']}")

        print("=" * 50)
        return 0
    else:
        print("    LICENSE STATUS: ERROR")
        print("=" * 50)
        print(f"  Error: {result.get('error', 'Unknown')}")
        print("=" * 50)
        return 1


def cmd_check(args):
    """현재 라이센스 상태 확인"""
    manager = get_license_manager()

    result = manager.validate_local_license()

    if result["success"]:
        print("\n" + "=" * 50)
        print("    LICENSE STATUS: VALID")
        print("=" * 50)
        print(f"  Type    : {result['license_type']}")
        print(f"  Expires : {result['expires_at'] or 'Never'}")
        print("=" * 50)
        return 0
    else:
        print(f"\n[WARNING] License issue detected")
        print(f"  Status : {result['status']}")
        print(f"  Reason : {result['error']}")
        print("\n  Please activate a valid license.")
        return 1


def cmd_list(args):
    """모든 라이센스 목록"""
    manager = get_license_manager()

    result = manager.list_all_licenses()

    print("\n" + "=" * 70)
    print("                      ALL LICENSES")
    print("=" * 70)
    print(f"  Total: {result['total_count']}")
    print(
        f"  Beta Free: {result['beta_free_count']}/{10} (Remaining: {result['beta_free_remaining']})"
    )
    print("-" * 70)

    for lic in result["licenses"]:
        status_icon = "" if lic["status"] == "active" else ""
        print(f"  {status_icon} {lic['license_key']}")
        print(f"      Type: {lic['license_type']} | Email: {lic['user_email']}")
        print(f"      Status: {lic['status']} | Devices: {lic['devices']}")
        print(f"      Expires: {lic['expires_at'] or 'Never'}")
        print()

    print("=" * 70)
    return 0


def cmd_block(args):
    """라이센스 차단"""
    manager = get_license_manager()

    result = manager.block_license(args.key, args.reason or "Manual block by admin")

    if result["success"]:
        print(f"\n[SUCCESS] {result['message']}")
        return 0
    else:
        print(f"[ERROR] {result['error']}")
        return 1


def cmd_info(args):
    """라이센스 정보 조회"""
    manager = get_license_manager()

    result = manager.get_license_info(args.key)

    if result["success"]:
        print("\n" + "=" * 50)
        print("    LICENSE INFORMATION")
        print("=" * 50)
        print(f"  Key     : {result['license_key']}")
        print(f"  Type    : {result['license_type']}")
        print(f"  Email   : {result['user_email']}")
        print(f"  Status  : {result['status']}")
        print(f"  Created : {result['created_at']}")
        print(f"  Expires : {result['expires_at'] or 'Never'}")
        print(f"  Devices : {result['bound_devices_count']}")
        print(f"  Abuse Attempts : {result['abuse_attempts_count']}")
        print("=" * 50)
        return 0
    else:
        print(f"[ERROR] {result['error']}")
        return 1


def cmd_device_id(args):
    """현재 기기 ID 표시"""
    manager = get_license_manager()
    device_id = manager.get_device_id()

    print(f"\nCurrent Device ID: {device_id}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Cortex MCP License Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Activate server license (recommended):
    python license_cli.py activate --key ctx_xxxxx --server

  Check license status (unified):
    python license_cli.py status

  Verify with server (online required):
    python license_cli.py verify --key ctx_xxxxx

  Generate local license (admin):
    python license_cli.py generate --type beta_free --email user@example.com

  Check local cache:
    python license_cli.py check

  List local licenses (admin):
    python license_cli.py list

  Block a license (admin):
    python license_cli.py block --key CORTEX-XXXX-XXXX-XXXX-XXXX --reason "abuse"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status (recommended - unified check)
    subparsers.add_parser("status", help="Check license status (unified, recommended)")

    # activate
    act_parser = subparsers.add_parser("activate", help="Activate license on this device")
    act_parser.add_argument("--key", "-k", required=True, help="License key (ctx_xxx or CORTEX-xxx)")
    act_parser.add_argument(
        "--server", "-s",
        action="store_true",
        help="Verify with server (recommended for ctx_xxx keys)"
    )

    # verify (server only)
    verify_parser = subparsers.add_parser("verify", help="Verify license with server (online required)")
    verify_parser.add_argument("--key", "-k", required=True, help="License key (ctx_xxx format)")

    # generate (admin/local)
    gen_parser = subparsers.add_parser("generate", help="Generate new local license (admin)")
    gen_parser.add_argument(
        "--type",
        "-t",
        required=True,
        choices=["beta_free", "trial", "monthly", "yearly", "lifetime"],
        help="License type",
    )
    gen_parser.add_argument("--email", "-e", required=True, help="User email")
    gen_parser.add_argument("--days", "-d", type=int, help="Custom validity days")

    # check (local cache only)
    subparsers.add_parser("check", help="Check local cache (legacy)")

    # list
    subparsers.add_parser("list", help="List all local licenses (admin)")

    # block
    block_parser = subparsers.add_parser("block", help="Block a license (admin)")
    block_parser.add_argument("--key", "-k", required=True, help="License key to block")
    block_parser.add_argument("--reason", "-r", help="Block reason")

    # info
    info_parser = subparsers.add_parser("info", help="Get license info")
    info_parser.add_argument("--key", "-k", required=True, help="License key")

    # device-id
    subparsers.add_parser("device-id", help="Show current device ID")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "status": cmd_status,
        "activate": cmd_activate,
        "verify": cmd_verify,
        "generate": cmd_generate,
        "check": cmd_check,
        "list": cmd_list,
        "block": cmd_block,
        "info": cmd_info,
        "device-id": cmd_device_id,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
