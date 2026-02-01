"""
Cortex MCP Hooks - Claude Code 완전 자동화 모듈

이 패키지는 Claude Code의 Hook 시스템과 통합되어
Cortex MCP 도구들을 자동으로 호출합니다.

Hook 종류:
- SessionStart: 세션 시작 시 프로젝트 초기화
- UserPromptSubmit: 프롬프트 제출 시 맥락 주입
- PreToolUse: 도구 사용 전 검증
- PostToolUse: 도구 사용 후 로깅
- Stop: AI 응답 완료 시 메모리 업데이트
- SessionEnd: 세션 종료 시 정리
"""

__version__ = "1.0.0"
__all__ = [
    "session_init",
    "inject_context",
    "validate_boundary",
    "log_operation",
    "check_completion",
    "session_cleanup",
    "runner",
]
