#!/usr/bin/env python3
"""
PostToolUse Hook - Cortex MCP 도구 사용 후 로깅

mcp__cortex-memory__* 도구 사용 후에 호출되어:
1. 작업 결과 로깅
2. 통계 업데이트
3. Reference History 기록
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cortex_mcp.hooks.runner import CORTEX_DIR, LOG_DIR, HookContext, log_hook_activity

# 통계 파일
STATS_FILE = LOG_DIR / "stats.json"


def update_stats(module: str, success: bool, latency_ms: float = 0):
    """모듈별 통계 업데이트"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    stats = {}
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                stats = json.load(f)
        except Exception:
            pass

    if "session_start" not in stats:
        stats["session_start"] = datetime.utcnow().isoformat()

    if "modules" not in stats:
        stats["modules"] = {}

    if module not in stats["modules"]:
        stats["modules"][module] = {
            "total_calls": 0,
            "success_count": 0,
            "error_count": 0,
            "total_latency_ms": 0,
        }

    mod_stats = stats["modules"][module]
    mod_stats["total_calls"] += 1

    if success:
        mod_stats["success_count"] += 1
    else:
        mod_stats["error_count"] += 1

    if latency_ms > 0:
        mod_stats["total_latency_ms"] += latency_ms

    stats["last_updated"] = datetime.utcnow().isoformat()

    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def extract_module_name(tool_name: str) -> str:
    """도구 이름에서 모듈명 추출"""
    # mcp__cortex-memory__initialize_context -> initialize_context
    parts = tool_name.split("__")
    if len(parts) >= 3:
        return parts[2]
    return tool_name


def log_to_module_file(module: str, action: str, data: dict):
    """모듈별 로그 파일에 기록"""
    # 모듈명과 로그 파일 매핑
    module_log_map = {
        "initialize_context": "general.jsonl",
        "create_branch": "branch_decision.jsonl",
        "search_context": "rag_search.jsonl",
        "update_memory": "smart_context.jsonl",
        "get_active_summary": "smart_context.jsonl",
        "load_context": "smart_context.jsonl",
        "compress_context": "smart_context.jsonl",
        "suggest_contexts": "reference_history.jsonl",
        "record_reference": "reference_history.jsonl",
        "link_git_branch": "git_sync.jsonl",
        "check_git_branch_change": "git_sync.jsonl",
        "sync_to_cloud": "license.jsonl",
        "sync_from_cloud": "license.jsonl",
    }

    log_file_name = module_log_map.get(module, "general.jsonl")
    log_file = LOG_DIR / log_file_name

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    entry = {"timestamp": datetime.utcnow().isoformat(), "module": module, "action": action, **data}

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    """PostToolUse Hook 메인 로직"""
    ctx = HookContext()

    # stdin에서 도구 결과 읽기
    stdin_data = ctx.stdin_context
    tool_name = stdin_data.get("tool_name", "")
    tool_result = stdin_data.get("tool_result", {})
    tool_input = stdin_data.get("tool_input", {})
    latency_ms = stdin_data.get("latency_ms", 0)

    if not tool_name:
        return

    # Cortex MCP 도구만 처리
    if not tool_name.startswith("mcp__cortex-memory__"):
        return

    module = extract_module_name(tool_name)
    success = tool_result.get("success", True)
    error = tool_result.get("error")

    # 통계 업데이트
    update_stats(module, success, latency_ms)

    # 모듈별 로그 기록
    log_data = {
        "success": success,
        "latency_ms": latency_ms,
        "input": tool_input,
        "output": tool_result.get("result", {}),
    }

    if error:
        log_data["error"] = error

    log_to_module_file(module, "tool_call", log_data)

    # Hook 활동 로깅
    ctx.log(
        "PostToolUse",
        "cortex_tool_logged",
        {"module": module, "success": success, "latency_ms": latency_ms},
    )

    # 특정 도구 후처리
    if module == "create_branch" and success:
        # 새 브랜치 생성 시 상태 업데이트
        branch_id = tool_result.get("result", {}).get("branch_id")
        if branch_id:
            ctx.state["active_branch"] = branch_id
            ctx.save()

    elif module == "update_memory" and success:
        # 메모리 업데이트 완료 플래그 해제
        ctx.state["pending_memory_update"] = False
        ctx.save()


if __name__ == "__main__":
    main()
