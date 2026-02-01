#!/usr/bin/env python3
"""
Cortex MCP - 실시간 로그 뷰어

사용법:
    python scripts/log_viewer.py           # 실시간 모니터링
    python scripts/log_viewer.py --json    # JSON 로그 분석
    python scripts/log_viewer.py --status  # 현재 상태 요약
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

# 로그 디렉토리
LOG_DIR = Path.home() / ".cortex" / "logs"
MEMORY_DIR = Path.home() / ".cortex" / "memory"


# 컬러 출력
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}  {text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")


def tail_log_file():
    """실시간 로그 파일 모니터링 (tail -f 스타일)"""
    log_file = LOG_DIR / "tool_calls.log"

    if not log_file.exists():
        print(f"{Colors.YELLOW}로그 파일이 아직 없습니다: {log_file}{Colors.ENDC}")
        print("MCP 서버가 시작되면 로그가 생성됩니다...")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file.touch()

    print_header("Cortex MCP 실시간 로그 모니터")
    print(f"로그 파일: {log_file}")
    print(f"종료: Ctrl+C\n")
    print("-" * 60)

    # 파일 끝으로 이동 후 새 내용 모니터링
    with open(log_file, "r", encoding="utf-8") as f:
        # 기존 내용 건너뛰기 (마지막 10줄만 표시)
        lines = f.readlines()
        if lines:
            print(f"\n{Colors.CYAN}[최근 로그]{Colors.ENDC}")
            for line in lines[-10:]:
                colorize_log_line(line.strip())

        print(f"\n{Colors.GREEN}[실시간 모니터링 시작...]{Colors.ENDC}\n")

        # 실시간 모니터링
        while True:
            line = f.readline()
            if line:
                colorize_log_line(line.strip())
            else:
                time.sleep(0.5)


def colorize_log_line(line):
    """로그 라인 컬러 출력"""
    if not line:
        return

    if "TOOL_CALL" in line or "도구 호출 시작" in line:
        print(f"{Colors.BLUE}{line}{Colors.ENDC}")
    elif "도구 호출 완료" in line:
        print(f"{Colors.GREEN}{line}{Colors.ENDC}")
    elif "도구 호출 실패" in line or "ERROR" in line:
        print(f"{Colors.RED}{line}{Colors.ENDC}")
    elif "서버 시작" in line:
        print(f"{Colors.BOLD}{Colors.CYAN}{line}{Colors.ENDC}")
    else:
        print(line)


def analyze_json_logs():
    """JSON 로그 분석"""
    json_log_file = LOG_DIR / "tool_calls.jsonl"

    if not json_log_file.exists():
        print(f"{Colors.YELLOW}JSON 로그 파일이 없습니다: {json_log_file}{Colors.ENDC}")
        return

    print_header("도구 호출 통계")

    tool_stats = {}
    total_calls = 0
    total_errors = 0
    total_duration = 0

    with open(json_log_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                tool_name = entry.get("tool", "unknown")
                success = entry.get("result_success", False)
                duration = entry.get("duration_ms", 0)

                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {"calls": 0, "success": 0, "total_duration": 0}

                tool_stats[tool_name]["calls"] += 1
                tool_stats[tool_name]["total_duration"] += duration
                if success:
                    tool_stats[tool_name]["success"] += 1
                else:
                    total_errors += 1

                total_calls += 1
                total_duration += duration

            except json.JSONDecodeError:
                continue

    # 통계 출력
    print(f"총 도구 호출: {Colors.BOLD}{total_calls}{Colors.ENDC}")
    print(f"총 에러: {Colors.RED}{total_errors}{Colors.ENDC}")
    print(f"총 실행 시간: {Colors.CYAN}{total_duration:.1f}ms{Colors.ENDC}")
    print()

    print(f"{'도구명':<25} {'호출':<8} {'성공률':<10} {'평균 시간'}")
    print("-" * 60)

    for tool, stats in sorted(tool_stats.items()):
        calls = stats["calls"]
        success_rate = (stats["success"] / calls * 100) if calls > 0 else 0
        avg_duration = stats["total_duration"] / calls if calls > 0 else 0

        color = (
            Colors.GREEN
            if success_rate == 100
            else (Colors.YELLOW if success_rate >= 50 else Colors.RED)
        )
        print(
            f"{tool:<25} {calls:<8} {color}{success_rate:>6.1f}%{Colors.ENDC}    {avg_duration:>8.1f}ms"
        )


def show_status():
    """현재 Cortex 상태 요약"""
    print_header("Cortex MCP 상태")

    # 1. 메모리 디렉토리 확인
    print(f"{Colors.BOLD}[메모리 디렉토리]{Colors.ENDC}")
    print(f"경로: {MEMORY_DIR}")

    if MEMORY_DIR.exists():
        projects = list(MEMORY_DIR.iterdir())
        print(f"프로젝트 수: {Colors.CYAN}{len(projects)}{Colors.ENDC}")

        for project_dir in projects[:5]:  # 최대 5개만 표시
            if project_dir.is_dir():
                md_files = list(project_dir.glob("*.md"))
                print(f"  - {project_dir.name}: {len(md_files)}개 브랜치")

        if len(projects) > 5:
            print(f"  ... 외 {len(projects) - 5}개")
    else:
        print(f"  {Colors.YELLOW}(아직 생성되지 않음){Colors.ENDC}")

    print()

    # 2. 로그 파일 확인
    print(f"{Colors.BOLD}[로그 파일]{Colors.ENDC}")
    log_file = LOG_DIR / "tool_calls.log"
    json_log = LOG_DIR / "tool_calls.jsonl"

    if log_file.exists():
        size = log_file.stat().st_size
        print(f"tool_calls.log: {size / 1024:.1f} KB")
    else:
        print(f"tool_calls.log: {Colors.YELLOW}없음{Colors.ENDC}")

    if json_log.exists():
        line_count = sum(1 for _ in open(json_log))
        print(f"tool_calls.jsonl: {line_count}개 기록")
    else:
        print(f"tool_calls.jsonl: {Colors.YELLOW}없음{Colors.ENDC}")

    print()

    # 3. ChromaDB 확인
    print(f"{Colors.BOLD}[RAG 인덱스 (ChromaDB)]{Colors.ENDC}")
    chroma_dir = Path.home() / ".cortex" / "chroma_db"
    if chroma_dir.exists():
        print(f"경로: {chroma_dir}")
        print(f"  {Colors.GREEN}초기화됨{Colors.ENDC}")
    else:
        print(f"  {Colors.YELLOW}(아직 생성되지 않음){Colors.ENDC}")

    print()

    # 4. 최근 도구 호출
    print(f"{Colors.BOLD}[최근 도구 호출 (최대 5개)]{Colors.ENDC}")
    if json_log.exists():
        lines = list(open(json_log, "r", encoding="utf-8"))[-5:]
        for line in lines:
            try:
                entry = json.loads(line.strip())
                tool = entry.get("tool", "?")
                timestamp = entry.get("timestamp", "?")[:19]
                success = "✓" if entry.get("result_success") else "✗"
                color = Colors.GREEN if entry.get("result_success") else Colors.RED
                print(f"  {timestamp} | {color}{success}{Colors.ENDC} | {tool}")
            except:
                pass
    else:
        print(f"  {Colors.YELLOW}(기록 없음){Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description="Cortex MCP 로그 뷰어")
    parser.add_argument("--json", action="store_true", help="JSON 로그 분석")
    parser.add_argument("--status", action="store_true", help="현재 상태 요약")

    args = parser.parse_args()

    try:
        if args.json:
            analyze_json_logs()
        elif args.status:
            show_status()
        else:
            tail_log_file()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}모니터링 종료{Colors.ENDC}")


if __name__ == "__main__":
    main()
