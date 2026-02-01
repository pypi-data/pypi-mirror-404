"""
Cortex MCP - Auto Logging Wrapper

파일 수정 도구 호출 후 자동으로 update_memory를 실행하는 데코레이터 패턴
"""

import logging
from functools import wraps
from typing import Any, Dict, Callable, Optional

logger = logging.getLogger(__name__)


def auto_update_memory(tool_name: str):
    """
    Tool Wrapper Decorator

    파일 수정 도구(Edit, Write, Delete 등) 호출 후 자동으로 update_memory를 실행합니다.

    Args:
        tool_name: 도구 이름 (예: "Edit", "Write", "Delete")

    사용 예시:
        @auto_update_memory("Edit")
        def edit_file(file_path: str, content: str) -> Dict[str, Any]:
            # ... 파일 수정 로직
            return {"success": True, "file_path": file_path}

    동작 방식:
        1. 원본 도구 실행
        2. 성공 시 자동으로 memory_manager.update_memory() 호출
        3. 실패해도 원본 작업에 영향 없음 (에러 무시)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            # 1. 원본 도구 실행
            result = func(*args, **kwargs)

            # 2. 성공 시 자동 메모리 업데이트
            if result.get("success"):
                try:
                    _auto_log_to_memory(tool_name, result, args, kwargs)
                except Exception as e:
                    # 메모리 업데이트 실패해도 원본 작업은 성공으로 유지
                    logger.warning(f"Auto-logging failed for {tool_name}: {e}")

            return result
        return wrapper
    return decorator


def _auto_log_to_memory(
    tool_name: str,
    result: Dict[str, Any],
    args: tuple,
    kwargs: Dict[str, Any]
) -> None:
    """
    메모리에 자동으로 로깅하는 내부 함수

    Args:
        tool_name: 도구 이름
        result: 도구 실행 결과
        args: 위치 인자
        kwargs: 키워드 인자
    """
    # HookContext와 MemoryManager 임포트 (순환 임포트 방지)
    from cortex_mcp.hooks.hook_context import HookContext
    from cortex_mcp.core.memory_manager import MemoryManager

    ctx = HookContext()

    # 프로젝트 ID와 브랜치 ID가 없으면 건너뜀
    if not ctx.project_id or not ctx.active_branch:
        logger.debug(f"Skipping auto-logging: no active project or branch")
        return

    # 파일 경로 추출
    file_path = _extract_file_path(result, args, kwargs)

    # 변경 내용 요약 생성
    content = _generate_auto_log_content(tool_name, file_path, result)

    # MemoryManager를 통해 저장
    mem_mgr = MemoryManager(project_id=ctx.project_id)
    mem_mgr.update_memory(
        project_id=ctx.project_id,
        branch_id=ctx.active_branch,
        content=content,
        role="assistant",
        verified=True  # 자동 로깅은 할루시네이션 검증 건너뜀
    )

    logger.info(f"Auto-logged: {tool_name} on {file_path}")


def _extract_file_path(
    result: Dict[str, Any],
    args: tuple,
    kwargs: Dict[str, Any]
) -> Optional[str]:
    """
    도구 실행 결과에서 파일 경로를 추출

    우선순위:
    1. result["file_path"]
    2. kwargs["file_path"]
    3. kwargs["path"]
    4. args[0] (첫 번째 위치 인자)

    Args:
        result: 도구 실행 결과
        args: 위치 인자
        kwargs: 키워드 인자

    Returns:
        파일 경로 또는 None
    """
    # 1. result에서 추출
    if "file_path" in result:
        return result["file_path"]
    if "path" in result:
        return result["path"]

    # 2. kwargs에서 추출
    if "file_path" in kwargs:
        return kwargs["file_path"]
    if "path" in kwargs:
        return kwargs["path"]

    # 3. args에서 추출 (첫 번째 인자가 파일 경로인 경우)
    if args and isinstance(args[0], str):
        return args[0]

    return None


def _generate_auto_log_content(
    tool_name: str,
    file_path: Optional[str],
    result: Dict[str, Any]
) -> str:
    """
    자동 로그 메시지 생성

    Args:
        tool_name: 도구 이름
        file_path: 파일 경로
        result: 도구 실행 결과

    Returns:
        로그 메시지
    """
    file_display = file_path if file_path else "unknown file"

    # 도구별 메시지 템플릿
    templates = {
        "Edit": f"[Auto] 파일 수정: {file_display}",
        "Write": f"[Auto] 파일 생성/덮어쓰기: {file_display}",
        "Delete": f"[Auto] 파일 삭제: {file_display}",
        "NotebookEdit": f"[Auto] Jupyter 노트북 수정: {file_display}",
    }

    message = templates.get(tool_name, f"[Auto] {tool_name}: {file_display}")

    # 추가 정보가 있으면 포함
    if "lines_changed" in result:
        message += f" ({result['lines_changed']} lines changed)"
    elif "size_kb" in result:
        message += f" ({result['size_kb']:.1f} KB)"

    return message


# ============================================================================
# 적용 대상 도구 목록
# ============================================================================
"""
자동 로깅이 필요한 MCP 도구:

Category 1 (P0 - 필수):
1. update_memory - SessionEnd Hook + Wrapper
2. validate_boundary_action - Wrapper (파일 접근 전 자동 검증)

Category 3 (선택적 - 수동 도구에 적용 가능):
- Edit - 파일 수정 시
- Write - 파일 생성 시
- Delete - 파일 삭제 시
- NotebookEdit - 주피터 노트북 수정 시

적용 방법:
1. cortex_tools.py의 각 도구 함수에 @auto_update_memory 데코레이터 추가
2. 또는 call_tool() 함수 내부에서 도구 실행 후 자동 호출

권장 방식: call_tool() 내부 적용 (모든 도구에 일괄 적용 가능)
"""
