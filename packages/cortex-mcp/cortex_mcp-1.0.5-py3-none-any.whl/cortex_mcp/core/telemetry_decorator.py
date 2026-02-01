"""
Cortex MCP - Telemetry Decorators
자동 텔레메트리 수집을 위한 데코레이터
"""

import functools
import time
import traceback
from typing import Callable, Optional


def track_call(module_name: str):
    """
    함수 호출을 자동으로 추적하는 데코레이터

    Args:
        module_name: 모듈 이름 (예: "memory_manager", "rag_engine")

    Example:
        @track_call("memory_manager")
        def update_memory(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_info = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_info = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "tool_name": func.__name__,
                    "stack_trace": traceback.format_exc(),
                }
                raise
            finally:
                # 처리 시간 계산
                latency_ms = (time.time() - start_time) * 1000

                # 텔레메트리 기록
                try:
                    from .telemetry_client import record_call, record_error

                    record_call(module_name, success=success, latency_ms=latency_ms)

                    # 에러 발생 시 에러 로그도 전송
                    if not success and error_info:
                        record_error(**error_info)
                except Exception:
                    # 텔레메트리 실패해도 원래 함수 동작에는 영향 없음
                    pass

        return wrapper
    return decorator


def track_async_call(module_name: str):
    """
    비동기 함수 호출을 자동으로 추적하는 데코레이터

    Args:
        module_name: 모듈 이름

    Example:
        @track_async_call("memory_manager")
        async def async_update_memory(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_info = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_info = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "tool_name": func.__name__,
                    "stack_trace": traceback.format_exc(),
                }
                raise
            finally:
                # 처리 시간 계산
                latency_ms = (time.time() - start_time) * 1000

                # 텔레메트리 기록
                try:
                    from .telemetry_client import record_call, record_error

                    record_call(module_name, success=success, latency_ms=latency_ms)

                    # 에러 발생 시 에러 로그도 전송
                    if not success and error_info:
                        record_error(**error_info)
                except Exception:
                    pass

        return wrapper
    return decorator
