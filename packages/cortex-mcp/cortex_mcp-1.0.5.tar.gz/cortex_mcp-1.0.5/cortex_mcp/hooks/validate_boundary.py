#!/usr/bin/env python3
"""
PreToolUse Hook - 도구 사용 전 경계 검증

Write, Edit, Bash 등 파일/시스템 조작 도구 사용 전에 호출되어:
1. 프로젝트 경계 검증
2. 민감 파일 보호
3. 위험 명령 차단
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cortex_mcp.hooks.runner import HookContext, log_hook_activity, output_block

# 보호할 파일 패턴
PROTECTED_PATTERNS = [
    r"\.env$",
    r"\.env\..*",
    r"credentials\.json",
    r"secrets\.json",
    r"\.ssh/",
    r"\.aws/",
    r"\.gitconfig",
    r"id_rsa",
    r"id_ed25519",
    r"\.npmrc",
    r"\.pypirc",
]

# 위험 명령어 패턴
DANGEROUS_COMMANDS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r"rm\s+-rf\s+\*",
    r"mkfs\.",
    r"dd\s+if=",
    r">\s+/dev/sd",
    r"chmod\s+-R\s+777\s+/",
    r":()\{\s*:\|:&\s*\};:",  # fork bomb
]


def is_protected_file(file_path: str) -> bool:
    """보호 대상 파일인지 확인"""
    for pattern in PROTECTED_PATTERNS:
        if re.search(pattern, file_path, re.IGNORECASE):
            return True
    return False


def is_dangerous_command(command: str) -> bool:
    """위험 명령어인지 확인"""
    for pattern in DANGEROUS_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def is_outside_project(file_path: str, project_path: str) -> bool:
    """프로젝트 경계 밖 파일인지 확인"""
    try:
        file_abs = Path(file_path).resolve()
        project_abs = Path(project_path).resolve()

        # Cortex 데이터 디렉토리는 허용
        cortex_dir = Path.home() / ".cortex"
        if str(file_abs).startswith(str(cortex_dir)):
            return False

        # 프로젝트 내부인지 확인
        return not str(file_abs).startswith(str(project_abs))
    except Exception:
        return True  # 오류 시 안전하게 차단


def main():
    """PreToolUse Hook 메인 로직"""
    ctx = HookContext()

    # stdin에서 도구 정보 읽기
    stdin_data = ctx.stdin_context
    tool_name = stdin_data.get("tool_name", "")
    tool_input = stdin_data.get("tool_input", {})

    if not tool_name:
        return

    ctx.log("PreToolUse", "tool_check", {"tool_name": tool_name, "project_id": ctx.project_id})

    # Write/Edit 도구 검증
    if tool_name in ["Write", "Edit", "Read"]:
        file_path = tool_input.get("file_path", "")

        # 보호 파일 확인
        if is_protected_file(file_path):
            output_block(f"[CORTEX_SECURITY] 보호된 파일입니다: {file_path}")
            ctx.log(
                "PreToolUse",
                "blocked_protected_file",
                {"tool_name": tool_name, "file_path": file_path},
            )
            return

        # 프로젝트 경계 확인 (Write/Edit만)
        if tool_name in ["Write", "Edit"]:
            if is_outside_project(file_path, ctx.project_path):
                output_block(
                    f"[CORTEX_BOUNDARY] 프로젝트 경계 밖 파일 수정 시도: {file_path}\n"
                    f"프로젝트 경로: {ctx.project_path}"
                )
                ctx.log(
                    "PreToolUse",
                    "blocked_outside_boundary",
                    {
                        "tool_name": tool_name,
                        "file_path": file_path,
                        "project_path": ctx.project_path,
                    },
                )
                return

    # Bash 도구 검증
    elif tool_name == "Bash":
        command = tool_input.get("command", "")

        # 위험 명령어 확인
        if is_dangerous_command(command):
            output_block(
                f"[CORTEX_SECURITY] 위험한 명령어가 감지되었습니다.\n" f"명령어: {command[:100]}..."
            )
            ctx.log("PreToolUse", "blocked_dangerous_command", {"command": command[:100]})
            return

    # 검증 통과
    ctx.log("PreToolUse", "validation_passed", {"tool_name": tool_name})


if __name__ == "__main__":
    main()
