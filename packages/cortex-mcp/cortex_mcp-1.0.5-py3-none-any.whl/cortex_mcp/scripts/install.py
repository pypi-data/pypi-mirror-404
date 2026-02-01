#!/usr/bin/env python3
"""
Cortex MCP 간편 설치 스크립트

사용법:
    python -m cortex_mcp.install
    python cortex_mcp/scripts/install.py
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


class Colors:
    """터미널 색상 코드"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """헤더 출력"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str):
    """성공 메시지"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """에러 메시지"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """경고 메시지"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """정보 메시지"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def check_python_version() -> bool:
    """Python 버전 확인 (3.11+)"""
    print_info("Python 버전 확인 중...")
    version = sys.version_info

    if version.major == 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} 확인됨")
        return True
    else:
        print_error(f"Python 3.11+ 필요 (현재: {version.major}.{version.minor}.{version.micro})")
        return False


def check_pip() -> bool:
    """pip 설치 여부 확인"""
    print_info("pip 확인 중...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                      check=True, capture_output=True)
        print_success("pip 확인됨")
        return True
    except subprocess.CalledProcessError:
        print_error("pip가 설치되어 있지 않습니다")
        return False


def install_cortex_mcp() -> bool:
    """cortex-mcp 패키지 설치"""
    print_info("cortex-mcp 설치 중...")

    try:
        # 이미 설치되어 있는지 확인
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "cortex-mcp"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print_success("cortex-mcp 이미 설치됨")

            # 업데이트 확인
            response = input(f"\n{Colors.OKCYAN}최신 버전으로 업데이트하시겠습니까? (y/N): {Colors.ENDC}").strip().lower()
            if response == 'y':
                print_info("cortex-mcp 업데이트 중...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "cortex-mcp"],
                    check=True
                )
                print_success("cortex-mcp 업데이트 완료")
            return True
        else:
            # 설치 진행
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "cortex-mcp"],
                check=True
            )
            print_success("cortex-mcp 설치 완료")
            return True

    except subprocess.CalledProcessError as e:
        print_error(f"설치 실패: {e}")
        return False


def get_mcp_config_path() -> Optional[Path]:
    """OS별 MCP config 파일 경로 반환"""
    system = platform.system()

    if system == "Darwin":  # macOS
        path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        path = Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        path = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

    return path


def read_mcp_config(config_path: Path) -> Dict:
    """MCP config 파일 읽기"""
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print_warning(f"기존 config 파일이 손상되었습니다: {config_path}")
            return {}
    return {}


def write_mcp_config(config_path: Path, config: Dict) -> bool:
    """MCP config 파일 쓰기"""
    try:
        # 디렉토리 생성
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # JSON 쓰기 (pretty print)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print_error(f"Config 파일 쓰기 실패: {e}")
        return False


def setup_mcp_config(license_key: Optional[str] = None) -> bool:
    """MCP config 자동 설정"""
    print_info("MCP 설정 파일 구성 중...")

    config_path = get_mcp_config_path()
    print_info(f"Config 경로: {config_path}")

    # 기존 config 읽기
    config = read_mcp_config(config_path)

    # mcpServers 섹션이 없으면 생성
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Python 경로 찾기
    python_path = sys.executable

    # Cortex MCP 설정
    cortex_config = {
        "command": python_path,
        "args": ["-m", "cortex_mcp.main"]
    }

    # 라이센스 키가 있으면 환경변수에 추가
    if license_key:
        cortex_config["env"] = {
            "CORTEX_LICENSE_KEY": license_key
        }

    # Cortex MCP 추가/업데이트
    if "cortex" in config["mcpServers"]:
        print_warning("기존 Cortex 설정을 업데이트합니다")

    config["mcpServers"]["cortex"] = cortex_config

    # Config 파일 쓰기
    if write_mcp_config(config_path, config):
        print_success(f"MCP 설정 완료: {config_path}")
        return True
    else:
        return False


def get_license_key() -> Optional[str]:
    """라이센스 키 입력 받기"""
    print_header("라이센스 키 설정")

    print("라이센스 키를 가지고 계신가요?")
    print("  - 있음: 키를 입력하세요")
    print("  - 없음: Enter를 눌러 건너뛰세요 (나중에 설정 가능)")

    license_key = input(f"\n{Colors.OKCYAN}라이센스 키: {Colors.ENDC}").strip()

    if license_key:
        print_success("라이센스 키가 설정됩니다")
        return license_key
    else:
        print_warning("라이센스 키 없이 진행합니다")
        print_info("라이센스 발급: https://cortex-mcp.com/login")
        return None


def show_next_steps(has_license: bool):
    """다음 단계 안내"""
    print_header("설치 완료!")

    print(f"{Colors.OKGREEN}Cortex MCP가 성공적으로 설치되었습니다!{Colors.ENDC}\n")

    print(f"{Colors.BOLD}다음 단계:{Colors.ENDC}")

    if not has_license:
        print(f"\n{Colors.WARNING}1. 라이센스 키 발급{Colors.ENDC}")
        print(f"   {Colors.OKCYAN}https://cortex-mcp.com/login{Colors.ENDC}")
        print("   - GitHub로 로그인")
        print("   - 승인 대기 (베타: 수동 승인, 최대 24시간)")
        print("   - 대시보드에서 라이센스 키 복사")

        print(f"\n{Colors.WARNING}2. 라이센스 키 설정{Colors.ENDC}")
        config_path = get_mcp_config_path()
        print(f"   {config_path} 파일을 열어서")
        print(f'   "env" 섹션에 추가:')
        print(f'   {Colors.OKCYAN}"CORTEX_LICENSE_KEY": "your-key-here"{Colors.ENDC}')

    print(f"\n{Colors.WARNING}{'3' if not has_license else '1'}. Claude Desktop 재시작{Colors.ENDC}")
    print("   - Claude Desktop을 완전히 종료")
    print("   - 다시 시작")

    print(f"\n{Colors.WARNING}{'4' if not has_license else '2'}. 설치 확인{Colors.ENDC}")
    print("   - Claude Code에서 Cortex 도구 확인")
    print("   - initialize_context, update_memory 등")

    print(f"\n{Colors.OKGREEN}문제가 있으신가요?{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}https://cortex-mcp.com/installation{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}https://github.com/syab726/cortex/issues{Colors.ENDC}")


def main():
    """메인 설치 프로세스"""
    print_header("Cortex MCP 간편 설치")

    # 1. Python 버전 체크
    if not check_python_version():
        print_error("Python 3.11 이상을 설치해주세요")
        sys.exit(1)

    # 2. pip 확인
    if not check_pip():
        print_error("pip를 설치해주세요")
        sys.exit(1)

    # 3. cortex-mcp 설치
    if not install_cortex_mcp():
        print_error("cortex-mcp 설치 실패")
        sys.exit(1)

    # 4. 라이센스 키 입력
    license_key = get_license_key()

    # 5. MCP config 설정
    if not setup_mcp_config(license_key):
        print_error("MCP 설정 실패")
        sys.exit(1)

    # 6. 완료 안내
    show_next_steps(has_license=bool(license_key))

    print(f"\n{Colors.OKGREEN}{Colors.BOLD}Happy Coding with Cortex! 🚀{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}설치가 취소되었습니다.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
