"""
Cortex MCP - Telemetry Wrapper
모든 MCP 도구 호출을 자동으로 추적하는 wrapper
"""

import functools
import time
import traceback
from typing import Callable


def track_mcp_tool(tool_name: str):
    """
    MCP 도구 호출을 자동으로 추적하는 데코레이터

    Args:
        tool_name: MCP 도구 이름

    Example:
        @track_mcp_tool("update_memory")
        async def update_memory_handler(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_info = None
            result = None

            try:
                result = await func(*args, **kwargs)

                # 결과가 dict이고 success 필드가 있으면 그것을 사용
                if isinstance(result, dict) and "success" in result:
                    success = result["success"]

                return result
            except Exception as e:
                success = False
                error_info = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "tool_name": tool_name,
                    "stack_trace": traceback.format_exc(),
                    "severity": "error",
                }
                raise
            finally:
                # 처리 시간 계산
                latency_ms = (time.time() - start_time) * 1000

                # 텔레메트리 기록
                try:
                    from .telemetry_client import record_call, record_error

                    # 도구 이름을 모듈로 매핑
                    module_map = {
                        "update_memory": "memory_manager",
                        "create_branch": "memory_manager",
                        "search_context": "rag_engine",
                        "get_active_summary": "memory_manager",
                        "load_context": "context_manager",
                        "suggest_contexts": "reference_history",
                        "create_snapshot": "backup_manager",
                        "restore_snapshot": "backup_manager",
                        "link_git_branch": "git_sync",
                        "initialize_context": "memory_manager",
                    }

                    module_name = module_map.get(tool_name, "general")
                    record_call(module_name, success=success, latency_ms=latency_ms)

                    # 에러 발생 시 에러 로그도 전송
                    if not success and error_info:
                        record_error(**error_info)
                except Exception:
                    # 텔레메트리 실패해도 원래 도구 동작에는 영향 없음
                    pass

        return wrapper
    return decorator
