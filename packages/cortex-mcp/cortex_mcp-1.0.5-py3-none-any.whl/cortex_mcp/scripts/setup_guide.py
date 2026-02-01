#!/usr/bin/env python3
"""
Cortex MCP - 대화형 설정 가이드

MCP 클라이언트를 자동으로 감지하고 Cortex 설정을 도와줍니다.

사용법:
    python scripts/setup_guide.py

지원 클라이언트:
    - Claude Desktop (Anthropic 공식 데스크톱 앱)
    - Claude Code (터미널 기반 CLI)
    - Cursor (AI 통합 코드 에디터)
    - Continue.dev (VS Code/JetBrains 확장)
    - Zed (고성능 코드 에디터)
    - Windsurf (AI 코드 에디터)
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    ENDC = "\033[0m"


class MCPClient:
    """MCP 클라이언트 정보"""

    def __init__(
        self,
        name: str,
        config_path: str,
        detected: bool = False,
        auto_setup: bool = False,
    ):
        self.name = name
        self.config_path = config_path
        self.detected = detected
        self.auto_setup = auto_setup


def print_header(text: str):
    """헤더 출력"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.ENDC}\n")


def print_info(text: str):
    """정보 출력"""
    print(f"{Colors.CYAN}ℹ{Colors.ENDC}  {text}")


def print_success(text: str):
    """성공 메시지"""
    print(f"{Colors.GREEN}✓{Colors.ENDC}  {text}")


def print_warning(text: str):
    """경고 메시지"""
    print(f"{Colors.YELLOW}⚠{Colors.ENDC}  {text}")


def print_error(text: str):
    """에러 메시지"""
    print(f"{Colors.RED}✗{Colors.ENDC}  {text}")


def get_home_dir() -> Path:
    """홈 디렉토리 반환"""
    return Path.home()


def expand_path(path: str) -> Path:
    """경로 확장 (환경변수 및 ~)"""
    expanded = os.path.expandvars(os.path.expanduser(path))
    return Path(expanded)


def detect_claude_desktop() -> Optional[MCPClient]:
    """Claude Desktop 감지"""
    system = platform.system()

    if system == "Darwin":  # macOS
        config_path = get_home_dir() / "Library/Application Support/Claude/claude_desktop_config.json"
    elif system == "Windows":
        appdata = os.getenv("APPDATA")
        if not appdata:
            return None
        config_path = Path(appdata) / "Claude/claude_desktop_config.json"
    else:  # Linux
        config_path = get_home_dir() / ".config/Claude/claude_desktop_config.json"

    detected = config_path.parent.exists()
    return MCPClient("Claude Desktop", str(config_path), detected)


def detect_claude_code() -> Optional[MCPClient]:
    """Claude Code 감지"""
    # claude 명령어 존재 여부 확인
    claude_bin = shutil.which("claude")
    detected = claude_bin is not None

    # 설정 파일 경로는 claude mcp add로 자동 처리
    return MCPClient("Claude Code", "auto", detected, auto_setup=True)


def detect_cursor() -> Optional[MCPClient]:
    """Cursor 감지"""
    config_path = get_home_dir() / ".cursor/mcp_config.json"
    detected = config_path.parent.exists()
    return MCPClient("Cursor", str(config_path), detected)


def detect_continue_dev() -> Optional[MCPClient]:
    """Continue.dev 감지"""
    config_path = get_home_dir() / ".continue/config.json"
    detected = config_path.parent.exists()
    return MCPClient("Continue.dev", str(config_path), detected)


def detect_zed() -> Optional[MCPClient]:
    """Zed 감지"""
    system = platform.system()

    if system == "Darwin":  # macOS
        config_path = get_home_dir() / "Library/Application Support/Zed/mcp_config.json"
    elif system == "Windows":
        appdata = os.getenv("APPDATA")
        if not appdata:
            return None
        config_path = Path(appdata) / "Zed/mcp_config.json"
    else:  # Linux
        config_path = get_home_dir() / ".config/zed/mcp_config.json"

    detected = config_path.parent.exists()
    return MCPClient("Zed", str(config_path), detected)


def detect_windsurf() -> Optional[MCPClient]:
    """Windsurf 감지"""
    system = platform.system()

    if system == "Darwin":  # macOS
        config_path = get_home_dir() / "Library/Application Support/Windsurf/mcp_config.json"
    elif system == "Windows":
        appdata = os.getenv("APPDATA")
        if not appdata:
            return None
        config_path = Path(appdata) / "Windsurf/mcp_config.json"
    else:  # Linux
        config_path = get_home_dir() / ".config/windsurf/mcp_config.json"

    detected = config_path.parent.exists()
    return MCPClient("Windsurf", str(config_path), detected)


def detect_all_clients() -> List[MCPClient]:
    """모든 MCP 클라이언트 감지"""
    clients = []

    detectors = [
        detect_claude_desktop,
        detect_claude_code,
        detect_cursor,
        detect_continue_dev,
        detect_zed,
        detect_windsurf,
    ]

    for detector in detectors:
        try:
            client = detector()
            if client:
                clients.append(client)
        except Exception as e:
            print_warning(f"{detector.__name__} 감지 실패: {e}")

    return clients


def get_cortex_config() -> Dict:
    """Cortex MCP 서버 설정 반환"""
    return {
        "command": "python",
        "args": ["-m", "cortex_mcp.main"],
        "env": {
            "CORTEX_LICENSE_KEY": "your-license-key-here"
        }
    }


def setup_claude_code() -> bool:
    """Claude Code 자동 설정"""
    print_info("Claude Code 자동 설정 중...")

    try:
        result = subprocess.run(
            ["claude", "mcp", "add", "cortex"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print_success("Claude Code 설정 완료")
            print_info("재시작 불필요 - 즉시 사용 가능")
            print_info("확인: claude mcp list-tools cortex")
            return True
        else:
            print_error(f"설정 실패: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print_error("설정 시간 초과")
        return False
    except FileNotFoundError:
        print_error("claude 명령어를 찾을 수 없습니다")
        return False
    except Exception as e:
        print_error(f"설정 중 오류: {e}")
        return False


def setup_json_config(client: MCPClient) -> bool:
    """JSON 기반 설정 파일 업데이트"""
    config_path = Path(client.config_path)

    # 백업 생성
    if config_path.exists():
        backup_path = config_path.with_suffix(".json.backup")
        shutil.copy2(config_path, backup_path)
        print_info(f"백업 생성: {backup_path}")

    # 설정 읽기
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    # mcpServers 섹션 확인
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # cortex 이미 있는지 확인
    if "cortex" in config["mcpServers"]:
        print_warning("cortex 설정이 이미 존재합니다")
        overwrite = input(f"{Colors.YELLOW}덮어쓰시겠습니까? (y/N): {Colors.ENDC}").strip().lower()
        if overwrite != "y":
            print_info("설정을 건너뜁니다")
            return False

    # cortex 추가
    config["mcpServers"]["cortex"] = get_cortex_config()

    # 디렉토리 생성
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 설정 저장
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print_success(f"설정 파일 업데이트: {config_path}")
    return True


def show_generic_mcp_guide():
    """기타 MCP 클라이언트를 위한 일반 가이드"""
    print_header("기타 MCP 클라이언트 설정 가이드")

    print(f"{Colors.BOLD}Cortex는 MCP 표준을 준수하므로 모든 MCP 지원 클라이언트에서 작동합니다.{Colors.ENDC}\n")

    print(f"{Colors.BOLD}1. 설정 파일 찾기{Colors.ENDC}")
    print("   사용하는 MCP 클라이언트의 설정 파일을 찾으세요.")
    print("   일반적인 위치:")
    print("   - macOS: ~/Library/Application Support/[클라이언트명]/")
    print("   - Windows: %APPDATA%\\[클라이언트명]\\")
    print("   - Linux: ~/.config/[클라이언트명]/\n")

    print(f"{Colors.BOLD}2. 설정 형식{Colors.ENDC}")
    print("   대부분의 MCP 클라이언트는 JSON 형식의 설정을 사용합니다:\n")

    print(f"{Colors.CYAN}   {{\n     \"mcpServers\": {{\n       \"cortex\": {{\n         \"command\": \"python\",\n         \"args\": [\"-m\", \"cortex_mcp.main\"],\n         \"env\": {{\n           \"CORTEX_LICENSE_KEY\": \"your-license-key-here\"\n         }}\n       }}\n     }}\n   }}{Colors.ENDC}\n")

    print(f"{Colors.BOLD}3. Python 경로 확인{Colors.ENDC}")
    print("   전체 Python 경로를 사용하는 것이 안전합니다:")
    print(f"   {Colors.CYAN}which python3{Colors.ENDC}  또는  {Colors.CYAN}where python{Colors.ENDC}\n")

    print(f"{Colors.BOLD}4. 재시작 및 확인{Colors.ENDC}")
    print("   - MCP 클라이언트를 완전히 종료 후 재시작")
    print("   - Cortex 도구가 표시되는지 확인:")
    print("     • initialize_context")
    print("     • update_memory")
    print("     • search_context")
    print("     • create_branch")
    print("     등...\n")

    print(f"{Colors.BOLD}5. 문제 해결{Colors.ENDC}")
    print("   도구가 표시되지 않으면:")
    print(f"   {Colors.CYAN}python scripts/test_mcp_protocol.py{Colors.ENDC}")
    print("   이 테스트가 통과하면 Cortex 서버는 정상이며 클라이언트 설정을 확인하세요.\n")


def print_restart_instructions(client: MCPClient):
    """재시작 안내"""
    print(f"\n{Colors.BOLD}다음 단계:{Colors.ENDC}")

    if client.name == "Claude Desktop":
        print("  1. Claude Desktop 완전히 종료 (Cmd+Q 또는 Alt+F4)")
        print("  2. Claude Desktop 재시작")
        print("  3. /mcp 명령어로 Cortex 도구 확인")

    elif client.name == "Claude Code":
        print("  1. 재시작 불필요 (자동 적용)")
        print("  2. claude mcp list-tools cortex 명령어로 확인")

    elif client.name == "Cursor":
        print("  1. Cursor 에디터 재시작")
        print("  2. MCP 서버 목록에서 Cortex 확인")

    elif client.name == "Continue.dev":
        print("  1. VS Code 또는 JetBrains IDE 재시작")
        print("  2. Continue.dev 패널에서 Cortex 확인")

    elif client.name == "Zed":
        print("  1. Zed 에디터 재시작")
        print("  2. MCP 서버 목록에서 Cortex 확인")

    elif client.name == "Windsurf":
        print("  1. Windsurf 에디터 재시작")
        print("  2. MCP 서버 목록에서 Cortex 확인")

    print(f"\n{Colors.BOLD}확인 사항:{Colors.ENDC}")
    print("  - Cortex 도구가 표시되어야 합니다:")
    print("    • initialize_context")
    print("    • update_memory")
    print("    • search_context")
    print("    • create_branch")
    print("    등...")


def main():
    """메인 함수"""
    print_header("Cortex MCP 설정 가이드")

    # 클라이언트 감지
    print_info("MCP 클라이언트를 감지하는 중...")
    clients = detect_all_clients()

    # 감지 결과 출력
    detected_clients = [c for c in clients if c.detected] if clients else []
    not_detected_clients = [c for c in clients if not c.detected] if clients else []

    if detected_clients:
        print(f"\n{Colors.BOLD}감지된 클라이언트:{Colors.ENDC}")
        for client in detected_clients:
            print_success(f"{client.name} - {client.config_path}")

    if not_detected_clients:
        print(f"\n{Colors.BOLD}알려진 클라이언트 (미설치):{Colors.ENDC}")
        for client in not_detected_clients:
            print(f"  {Colors.YELLOW}•{Colors.ENDC} {client.name}")

    # 클라이언트 선택
    print(f"\n{Colors.BOLD}설정할 클라이언트를 선택하세요:{Colors.ENDC}")

    if detected_clients:
        for i, client in enumerate(detected_clients, 1):
            print(f"  {i}. {client.name}")
        print(f"  0. 모두 설정")
        print(f"  99. 기타 MCP 클라이언트 (일반 가이드)")
        max_choice = len(detected_clients)
    else:
        print(f"  {Colors.YELLOW}감지된 클라이언트가 없습니다{Colors.ENDC}")
        print(f"  99. 기타 MCP 클라이언트 (일반 가이드)")
        max_choice = 0

    try:
        choice = input(f"\n{Colors.CYAN}선택 (0-{max_choice}, 99): {Colors.ENDC}").strip()
        choice_num = int(choice)

        if choice_num == 99:
            # 기타 MCP 클라이언트 가이드
            show_generic_mcp_guide()
            return 0

        if not detected_clients:
            print_error("감지된 클라이언트가 없습니다. 99를 선택하여 일반 가이드를 확인하세요.")
            return 1

        if choice_num < 0 or choice_num > max_choice:
            print_error("잘못된 선택입니다")
            return 1

        selected_clients = detected_clients if choice_num == 0 else [detected_clients[choice_num - 1]]

    except (ValueError, IndexError):
        print_error("잘못된 입력입니다")
        return 1

    # 설정 진행
    success_count = 0
    for client in selected_clients:
        print(f"\n{Colors.BOLD}━━━ {client.name} 설정 ━━━{Colors.ENDC}")

        if client.auto_setup:
            # Claude Code 자동 설정
            if setup_claude_code():
                success_count += 1
        else:
            # JSON 기반 수동 설정
            if setup_json_config(client):
                print_restart_instructions(client)
                success_count += 1

    # 최종 결과
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    if success_count == len(selected_clients):
        print_success(f"모든 클라이언트 설정 완료 ({success_count}/{len(selected_clients)})")
    elif success_count > 0:
        print_warning(f"일부 클라이언트 설정 완료 ({success_count}/{len(selected_clients)})")
    else:
        print_error("설정에 실패했습니다")
        return 1

    print(f"\n{Colors.BOLD}문제 해결:{Colors.ENDC}")
    print("  - Cortex 도구가 보이지 않으면: python scripts/test_mcp_protocol.py 실행")
    print("  - 설치 확인: python scripts/verify_installation.py")
    print(f"  - 문서: {Colors.CYAN}https://cortex-mcp.com/installation{Colors.ENDC}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}설정이 중단되었습니다{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
