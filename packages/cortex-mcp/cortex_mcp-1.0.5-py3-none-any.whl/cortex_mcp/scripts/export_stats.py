#!/usr/bin/env python3
"""
Cortex MCP - Stats Exporter
AlphaLogger 통계 데이터를 웹사이트 배포용으로 export합니다.

Usage:
    python export_stats.py

Output:
    cortex_mcp/dashboard/export/
    ├── admin_stats.html    # 경량 대시보드 HTML
    └── stats.json          # 통계 데이터 JSON
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

# 경로 설정
PROJECT_DIR = Path(__file__).parent.parent
LOGS_DIR = Path.home() / ".cortex" / "logs" / "alpha_test"
STATS_FILE = LOGS_DIR / "stats.json"
EXPORT_DIR = PROJECT_DIR / "dashboard" / "export"
HTML_TEMPLATE = PROJECT_DIR / "dashboard" / "admin_stats.html"


def export_stats():
    """통계 데이터를 export 디렉토리에 복사"""

    # Export 디렉토리 생성
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. stats.json 존재 확인
    if not STATS_FILE.exists():
        print(f"Error: stats.json not found at {STATS_FILE}")
        print("Please ensure AlphaLogger has collected data.")
        return False

    # 2. stats.json 읽기 및 검증
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            stats_data = json.load(f)

        modules = stats_data.get("modules", {})
        if not modules:
            print("Warning: stats.json contains no module data.")
        else:
            print(f"Found {len(modules)} modules in stats.json")
    except Exception as e:
        print(f"Error reading stats.json: {e}")
        return False

    # 3. stats.json 복사
    dest_stats = EXPORT_DIR / "stats.json"
    shutil.copy2(STATS_FILE, dest_stats)
    print(f"✓ Copied stats.json to {dest_stats}")

    # 4. admin_stats.html 복사
    if not HTML_TEMPLATE.exists():
        print(f"Error: admin_stats.html not found at {HTML_TEMPLATE}")
        return False

    dest_html = EXPORT_DIR / "admin_stats.html"
    shutil.copy2(HTML_TEMPLATE, dest_html)
    print(f"✓ Copied admin_stats.html to {dest_html}")

    # 5. 메타 정보 생성
    meta_data = {
        "export_time": datetime.now().isoformat(),
        "stats_file_size": STATS_FILE.stat().st_size,
        "html_file_size": HTML_TEMPLATE.stat().st_size,
        "modules_count": len(modules),
        "total_calls": sum(m.get("total_calls", 0) for m in modules.values()),
    }

    meta_file = EXPORT_DIR / "export_meta.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Created export metadata: {meta_file}")

    # 6. 배포 안내
    print("\n" + "=" * 60)
    print("Export complete!")
    print("=" * 60)
    print(f"\nExport directory: {EXPORT_DIR}")
    print(f"\nTotal size: {(dest_stats.stat().st_size + dest_html.stat().st_size) / 1024:.1f} KB")
    print(f"  - stats.json: {dest_stats.stat().st_size / 1024:.1f} KB")
    print(f"  - admin_stats.html: {dest_html.stat().st_size / 1024:.1f} KB")

    print("\n" + "-" * 60)
    print("Deployment instructions:")
    print("-" * 60)
    print("1. Upload both files to your website:")
    print("   - admin_stats.html")
    print("   - stats.json")
    print("")
    print("2. Ensure they are in the SAME directory")
    print("")
    print("3. Access via: https://your-website.com/admin_stats.html")
    print("")
    print("4. Update stats.json periodically by re-running this script")
    print("=" * 60)

    return True


def main():
    """메인 실행 함수"""
    print("Cortex MCP - Stats Exporter")
    print("=" * 60)

    success = export_stats()

    if success:
        print("\n✓ Export successful!")
    else:
        print("\n✗ Export failed.")
        exit(1)


if __name__ == "__main__":
    main()
