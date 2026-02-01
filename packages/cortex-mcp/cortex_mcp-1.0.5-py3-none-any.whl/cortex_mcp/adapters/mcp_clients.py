"""
MCP 클라이언트 어댑터

벤더 독립적인 MCP 클라이언트 지원.
각 클라이언트의 설정 파일 위치 및 설치 방법을 제공합니다.

지원 클라이언트:
1. Claude Desktop (Anthropic)
2. Claude Code (Anthropic)
3. Cursor (Anysphere)
4. Continue (Continue.dev)
5. Cline (VS Code Extension)
6. Zed Editor
"""

import os
import platform
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any


class MCPClientType(Enum):
    """지원하는 MCP 클라이언트 타입"""
    CLAUDE_DESKTOP = "claude_desktop"
    CLAUDE_CODE = "claude_code"
    CURSOR = "cursor"
    CONTINUE = "continue"
    CLINE = "cline"
    ZED = "zed"
    UNKNOWN = "unknown"


@dataclass
class ClientConfig:
    """MCP 클라이언트 설정 정보"""
    client_type: MCPClientType
    display_name: str
    config_path: Optional[Path]
    config_format: str  # "json" or "toml" or "yaml"
    platform: str
    installation_docs_url: str


def _get_platform() -> str:
    """현재 플랫폼 반환"""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    return "unknown"


def _get_home() -> Path:
    """홈 디렉토리 반환"""
    return Path.home()


def get_config_path(client_type: MCPClientType) -> Optional[Path]:
    """
    MCP 클라이언트별 설정 파일 경로 반환

    Args:
        client_type: MCP 클라이언트 타입

    Returns:
        설정 파일 경로 (없으면 None)
    """
    home = _get_home()
    plat = _get_platform()

    paths = {
        MCPClientType.CLAUDE_DESKTOP: {
            "macos": home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            "windows": Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
            "linux": home / ".config" / "Claude" / "claude_desktop_config.json",
        },
        MCPClientType.CLAUDE_CODE: {
            # Claude Code uses .mcp.json in project root or ~/.claude/settings.json
            "macos": home / ".claude" / "settings.json",
            "windows": home / ".claude" / "settings.json",
            "linux": home / ".claude" / "settings.json",
        },
        MCPClientType.CURSOR: {
            "macos": home / ".cursor" / "mcp.json",
            "windows": home / ".cursor" / "mcp.json",
            "linux": home / ".cursor" / "mcp.json",
        },
        MCPClientType.CONTINUE: {
            "macos": home / ".continue" / "config.json",
            "windows": home / ".continue" / "config.json",
            "linux": home / ".continue" / "config.json",
        },
        MCPClientType.CLINE: {
            # Cline stores settings in VS Code settings
            "macos": home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            "windows": Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            "linux": home / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
        },
        MCPClientType.ZED: {
            "macos": home / ".config" / "zed" / "settings.json",
            "windows": home / ".config" / "zed" / "settings.json",
            "linux": home / ".config" / "zed" / "settings.json",
        },
    }

    client_paths = paths.get(client_type, {})
    return client_paths.get(plat)


def get_client_type() -> MCPClientType:
    """
    현재 MCP 클라이언트 타입 감지

    환경 변수, 설정 파일 존재 여부 등으로 추론합니다.

    Returns:
        감지된 MCP 클라이언트 타입
    """
    # 환경 변수로 감지
    env_hints = {
        "CLAUDE_DESKTOP": MCPClientType.CLAUDE_DESKTOP,
        "CLAUDE_CODE": MCPClientType.CLAUDE_CODE,
        "CURSOR_SESSION": MCPClientType.CURSOR,
        "CONTINUE_GLOBAL_DIR": MCPClientType.CONTINUE,
        "CLINE_SESSION": MCPClientType.CLINE,
        "ZED_TERM": MCPClientType.ZED,
    }

    for env_var, client_type in env_hints.items():
        if os.environ.get(env_var):
            return client_type

    # 설정 파일 존재 여부로 감지
    for client_type in MCPClientType:
        if client_type == MCPClientType.UNKNOWN:
            continue
        config_path = get_config_path(client_type)
        if config_path and config_path.exists():
            return client_type

    return MCPClientType.UNKNOWN


def get_installation_instructions(client_type: MCPClientType) -> Dict[str, Any]:
    """
    MCP 클라이언트별 Cortex 설치 안내

    Args:
        client_type: MCP 클라이언트 타입

    Returns:
        설치 안내 정보
    """
    base_config = {
        "server_name": "cortex",
        "command": "python",
        "args": ["-m", "cortex_mcp.main"],
    }

    instructions = {
        MCPClientType.CLAUDE_DESKTOP: {
            "display_name": "Claude Desktop",
            "docs_url": "https://modelcontextprotocol.io/quickstart/user",
            "config_format": "json",
            "config_example": {
                "mcpServers": {
                    "cortex": {
                        "command": "python",
                        "args": ["-m", "cortex_mcp.main"]
                    }
                }
            },
            "steps": [
                "1. Claude Desktop 설치",
                "2. 설정 파일 열기 (Claude > Settings > Developer > Edit Config)",
                "3. mcpServers에 cortex 설정 추가",
                "4. Claude Desktop 재시작"
            ]
        },
        MCPClientType.CLAUDE_CODE: {
            "display_name": "Claude Code",
            "docs_url": "https://docs.anthropic.com/claude/docs/claude-code",
            "config_format": "json",
            "config_example": {
                "mcpServers": {
                    "cortex": {
                        "command": "python",
                        "args": ["-m", "cortex_mcp.main"]
                    }
                }
            },
            "steps": [
                "1. Claude Code 설치: npm install -g @anthropic-ai/claude-code",
                "2. 설정: claude mcp add cortex --command 'python -m cortex_mcp.main'",
                "3. 또는 ~/.claude/settings.json에 수동 추가"
            ]
        },
        MCPClientType.CURSOR: {
            "display_name": "Cursor",
            "docs_url": "https://docs.cursor.com/context/model-context-protocol",
            "config_format": "json",
            "config_example": {
                "mcpServers": {
                    "cortex": {
                        "command": "python",
                        "args": ["-m", "cortex_mcp.main"]
                    }
                }
            },
            "steps": [
                "1. Cursor 설치 (https://cursor.sh)",
                "2. ~/.cursor/mcp.json 파일 생성/편집",
                "3. mcpServers에 cortex 설정 추가",
                "4. Cursor 재시작"
            ]
        },
        MCPClientType.CONTINUE: {
            "display_name": "Continue",
            "docs_url": "https://continue.dev/docs/reference/Model%20Context%20Protocol",
            "config_format": "json",
            "config_example": {
                "experimental": {
                    "modelContextProtocolServers": [
                        {
                            "transport": {
                                "type": "stdio",
                                "command": "python",
                                "args": ["-m", "cortex_mcp.main"]
                            }
                        }
                    ]
                }
            },
            "steps": [
                "1. Continue 확장 설치 (VS Code)",
                "2. ~/.continue/config.json 편집",
                "3. experimental.modelContextProtocolServers에 추가",
                "4. VS Code 재시작"
            ]
        },
        MCPClientType.CLINE: {
            "display_name": "Cline",
            "docs_url": "https://github.com/cline/cline#mcp-server-support",
            "config_format": "json",
            "config_example": {
                "mcpServers": {
                    "cortex": {
                        "command": "python",
                        "args": ["-m", "cortex_mcp.main"]
                    }
                }
            },
            "steps": [
                "1. Cline 확장 설치 (VS Code - 'Claude Dev' 검색)",
                "2. Cline 설정에서 MCP Servers 섹션 열기",
                "3. cortex 서버 추가",
                "4. VS Code 재시작"
            ]
        },
        MCPClientType.ZED: {
            "display_name": "Zed Editor",
            "docs_url": "https://zed.dev/docs/assistant/model-context-protocol",
            "config_format": "json",
            "config_example": {
                "context_servers": {
                    "cortex": {
                        "command": {
                            "path": "python",
                            "args": ["-m", "cortex_mcp.main"]
                        }
                    }
                }
            },
            "steps": [
                "1. Zed Editor 설치 (https://zed.dev)",
                "2. Settings 열기 (Cmd+,)",
                "3. context_servers에 cortex 설정 추가",
                "4. Zed 재시작"
            ]
        },
        MCPClientType.UNKNOWN: {
            "display_name": "Generic MCP Client",
            "docs_url": "https://modelcontextprotocol.io/introduction",
            "config_format": "json",
            "config_example": base_config,
            "steps": [
                "1. MCP 지원 클라이언트 설치",
                "2. 클라이언트 문서에 따라 MCP 서버 추가",
                "3. command: python, args: ['-m', 'cortex_mcp.main']"
            ]
        },
    }

    return instructions.get(client_type, instructions[MCPClientType.UNKNOWN])


def get_all_supported_clients() -> Dict[MCPClientType, Dict[str, Any]]:
    """
    모든 지원 클라이언트 목록 반환

    Returns:
        클라이언트별 설치 정보
    """
    return {
        client_type: get_installation_instructions(client_type)
        for client_type in MCPClientType
        if client_type != MCPClientType.UNKNOWN
    }
