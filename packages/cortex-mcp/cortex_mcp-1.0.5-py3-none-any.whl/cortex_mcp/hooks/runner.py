"""
Cortex Hook Runner - 공통 유틸리티

Hook 실행에 필요한 공통 기능들을 제공합니다.
"""

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Cortex 데이터 디렉토리
CORTEX_DIR = Path.home() / ".cortex"
MEMORY_DIR = CORTEX_DIR / "memory"
STATE_FILE = CORTEX_DIR / "hook_state.json"
LOG_DIR = CORTEX_DIR / "logs" / "alpha_test"


def get_project_id(project_path: str) -> str:
    """프로젝트 경로에서 고유 ID 생성"""
    return hashlib.md5(project_path.encode()).hexdigest()[:12]


def get_project_path() -> str:
    """현재 프로젝트 경로 반환"""
    # 환경 변수에서 먼저 확인
    if "CORTEX_PROJECT_PATH" in os.environ:
        return os.environ["CORTEX_PROJECT_PATH"]

    # Claude Code 환경 변수 확인
    if "CLAUDE_WORKING_DIR" in os.environ:
        return os.environ["CLAUDE_WORKING_DIR"]

    # 현재 작업 디렉토리
    return os.getcwd()


def load_state() -> Dict[str, Any]:
    """Hook 상태 로드"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "session_id": None,
        "project_id": None,
        "active_branch": None,
        "initialized": False,
        "last_activity": None,
        "context_loaded": [],
        "pending_memory_update": False,
    }


def save_state(state: Dict[str, Any]) -> None:
    """Hook 상태 저장"""
    CORTEX_DIR.mkdir(parents=True, exist_ok=True)
    state["last_activity"] = datetime.utcnow().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def log_hook_activity(hook_name: str, action: str, details: Dict[str, Any] = None) -> None:
    """Hook 활동 로깅"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "hooks.jsonl"

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "hook": hook_name,
        "action": action,
        "details": details or {},
        "success": True,
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def check_project_initialized(project_id: str) -> bool:
    """프로젝트가 Cortex에 초기화되었는지 확인"""
    # Context Graph 존재 여부로 확인 (실제 초기화 상태)
    import os
    from pathlib import Path

    cortex_home = Path(os.path.expanduser("~/.cortex"))
    context_graph_index = cortex_home / "context_graphs" / project_id / "index.json"

    # Context Graph가 있으면 초기화된 것
    if context_graph_index.exists():
        return True

    # Fallback: 기존 방식도 체크
    index_file = MEMORY_DIR / project_id / "_index.json"
    return index_file.exists()


def get_active_branch(project_id: str) -> Optional[str]:
    """현재 활성 브랜치 ID 반환"""
    index_file = MEMORY_DIR / project_id / "_index.json"
    if not index_file.exists():
        return None

    try:
        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)
            return index.get("active_branch")
    except Exception:
        return None


def get_branch_summary(project_id: str, branch_id: str) -> Optional[str]:
    """브랜치 요약 정보 반환"""
    branch_dir = MEMORY_DIR / project_id / "contexts" / branch_id
    summary_file = branch_dir / "_summary.json"

    if not summary_file.exists():
        return None

    try:
        with open(summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("summary", "")
    except Exception:
        return None


def generate_mcp_tool_call(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP 도구 호출 형식 생성"""
    return {"type": "tool_call", "tool": f"mcp__cortex-memory__{tool_name}", "parameters": params}


def output_system_message(message: str) -> None:
    """시스템 메시지 출력 (Claude Code Hook 응답 형식)"""
    response = {"type": "system-prompt-inject", "content": message}
    print(json.dumps(response))


def output_tool_suggestion(tool_calls: List[Dict[str, Any]]) -> None:
    """도구 호출 제안 출력"""
    response = {"type": "suggested-tool-calls", "tools": tool_calls}
    print(json.dumps(response))


def output_block(reason: str) -> None:
    """작업 차단 출력"""
    response = {"type": "block", "reason": reason}
    print(json.dumps(response))


def read_stdin_context() -> Dict[str, Any]:
    """stdin에서 Claude Code 컨텍스트 읽기"""
    try:
        if not sys.stdin.isatty():
            input_data = sys.stdin.read()
            if input_data:
                return json.loads(input_data)
    except Exception:
        pass
    return {}


class HookContext:
    """Hook 실행 컨텍스트"""

    def __init__(self):
        self.state = load_state()
        self.stdin_context = read_stdin_context()
        self.project_path = get_project_path()
        self.project_id = get_project_id(self.project_path)

    def save(self):
        """상태 저장"""
        save_state(self.state)

    def log(self, hook_name: str, action: str, details: Dict[str, Any] = None):
        """활동 로깅"""
        log_hook_activity(hook_name, action, details)

    @property
    def is_initialized(self) -> bool:
        """프로젝트 초기화 여부"""
        return check_project_initialized(self.project_id)

    @property
    def active_branch(self) -> Optional[str]:
        """활성 브랜치"""
        return get_active_branch(self.project_id)

    def get_summary(self) -> Optional[str]:
        """현재 브랜치 요약"""
        branch_id = self.active_branch
        if branch_id:
            return get_branch_summary(self.project_id, branch_id)
        return None


if __name__ == "__main__":
    # 테스트 실행
    ctx = HookContext()
    print(f"Project Path: {ctx.project_path}")
    print(f"Project ID: {ctx.project_id}")
    print(f"Initialized: {ctx.is_initialized}")
    print(f"Active Branch: {ctx.active_branch}")
