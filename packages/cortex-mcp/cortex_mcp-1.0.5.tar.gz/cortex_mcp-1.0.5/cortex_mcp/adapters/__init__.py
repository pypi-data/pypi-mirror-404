"""
Cortex MCP Adapters

벤더 독립적인 MCP 클라이언트 지원 어댑터 모듈.
Cortex는 MCP 표준을 따르므로 어떤 MCP 클라이언트에서든 동일하게 동작합니다.

지원 클라이언트:
- Claude Desktop (Anthropic)
- Claude Code (Anthropic)
- Cursor (Anysphere)
- Continue (Continue.dev)
- Cline (VS Code Extension)
- Zed Editor

사용법:
    from cortex_mcp.adapters import get_client_type, get_config_path

    # 현재 MCP 클라이언트 타입 감지
    client = get_client_type()

    # 클라이언트별 설정 파일 경로
    config_path = get_config_path(client)
"""

from .mcp_clients import (
    MCPClientType,
    get_client_type,
    get_config_path,
    get_installation_instructions,
    ClientConfig,
)

__all__ = [
    "MCPClientType",
    "get_client_type",
    "get_config_path",
    "get_installation_instructions",
    "ClientConfig",
]
