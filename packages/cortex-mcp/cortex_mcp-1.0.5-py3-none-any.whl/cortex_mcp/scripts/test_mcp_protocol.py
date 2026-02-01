#!/usr/bin/env python3
"""
Cortex MCP - MCP 프로토콜 테스트 스크립트

Cortex MCP 서버가 MCP(Model Context Protocol) 표준대로 작동하는지 검증합니다.

사용법:
    python scripts/test_mcp_protocol.py

검증 항목:
    1. MCP stdio 통신 (JSON-RPC)
    2. initialize 메시지 처리
    3. tools/list 응답
    4. 도구 목록 검증 (initialize_context, update_memory 등)

출력:
    - 성공: Cortex 서버 정상 작동 → 클라이언트 설정 문제 가능성
    - 실패: Cortex 서버 오류 → 재설치 필요
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    ENDC = "\033[0m"


def print_header(text: str):
    """헤더 출력"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.ENDC}\n")


def print_test(name: str, passed: bool, detail: str = ""):
    """테스트 결과 출력"""
    status = f"{Colors.GREEN}PASS{Colors.ENDC}" if passed else f"{Colors.RED}FAIL{Colors.ENDC}"
    print(f"  [{status}] {name}")
    if detail:
        color = Colors.GREEN if passed else Colors.YELLOW
        print(f"        {color}→ {detail}{Colors.ENDC}")
    return passed


def print_info(text: str):
    """정보 출력"""
    print(f"{Colors.CYAN}ℹ{Colors.ENDC}  {text}")


def print_success(text: str):
    """성공 메시지"""
    print(f"{Colors.GREEN}✓{Colors.ENDC}  {text}")


def print_error(text: str):
    """에러 메시지"""
    print(f"{Colors.RED}✗{Colors.ENDC}  {text}")


def create_initialize_request() -> Dict:
    """initialize 요청 생성 (MCP 표준)"""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "cortex-test-client",
                "version": "1.0.0"
            }
        }
    }


def create_tools_list_request() -> Dict:
    """tools/list 요청 생성 (MCP 표준)"""
    return {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }


def send_request(proc: subprocess.Popen, request: Dict) -> Optional[Dict]:
    """MCP 서버에 요청 전송 및 응답 수신"""
    try:
        # 요청 전송
        request_json = json.dumps(request) + "\n"
        proc.stdin.write(request_json)
        proc.stdin.flush()

        # 응답 수신 (타임아웃 5초)
        start_time = time.time()
        while time.time() - start_time < 5.0:
            if proc.poll() is not None:
                # 프로세스 종료됨
                return None

            # stdout에서 한 줄 읽기
            line = proc.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue

            # JSON 파싱
            try:
                response = json.loads(line.strip())
                return response
            except json.JSONDecodeError:
                # JSON이 아닌 라인 (로그 등) 무시
                continue

        # 타임아웃
        return None

    except Exception as e:
        print_error(f"요청 전송 중 오류: {e}")
        return None


def validate_initialize_response(response: Dict) -> Tuple[bool, str]:
    """initialize 응답 검증"""
    if not response:
        return False, "응답 없음"

    if "error" in response:
        return False, f"에러 응답: {response['error']}"

    if "result" not in response:
        return False, "result 필드 없음"

    result = response["result"]

    # 필수 필드 확인
    if "protocolVersion" not in result:
        return False, "protocolVersion 없음"

    if "capabilities" not in result:
        return False, "capabilities 없음"

    if "serverInfo" not in result:
        return False, "serverInfo 없음"

    return True, f"프로토콜 버전: {result['protocolVersion']}"


def validate_tools_list_response(response: Dict) -> Tuple[bool, str]:
    """tools/list 응답 검증"""
    if not response:
        return False, "응답 없음"

    if "error" in response:
        return False, f"에러 응답: {response['error']}"

    if "result" not in response:
        return False, "result 필드 없음"

    result = response["result"]

    if "tools" not in result:
        return False, "tools 필드 없음"

    tools = result["tools"]

    if not isinstance(tools, list):
        return False, "tools가 배열이 아님"

    if len(tools) == 0:
        return False, "도구가 0개입니다"

    # 핵심 도구 확인
    tool_names = [tool["name"] for tool in tools if "name" in tool]

    essential_tools = [
        "initialize_context",
        "update_memory",
        "search_context",
        "create_branch",
    ]

    missing_tools = [tool for tool in essential_tools if tool not in tool_names]

    if missing_tools:
        return False, f"필수 도구 누락: {', '.join(missing_tools)}"

    return True, f"{len(tools)}개 도구 발견"


def test_mcp_protocol() -> bool:
    """MCP 프로토콜 테스트 실행"""
    print_header("Cortex MCP 프로토콜 테스트")

    all_passed = True

    # 1. Cortex MCP 서버 시작
    print(f"{Colors.BOLD}1. Cortex MCP 서버 시작{Colors.ENDC}\n")

    try:
        # Python 실행 파일 찾기 (python3 우선, 없으면 python)
        python_cmd = sys.executable or "python3"

        proc = subprocess.Popen(
            [python_cmd, "-m", "cortex_mcp.main"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # 라인 버퍼링
        )

        print_success("서버 프로세스 시작됨")
        time.sleep(1)  # 서버 초기화 대기

        # 프로세스가 즉시 종료되었는지 확인
        if proc.poll() is not None:
            stderr = proc.stderr.read()
            print_test("서버 실행", False, f"프로세스 종료됨: {stderr}")
            return False

        print_test("서버 실행", True, f"PID: {proc.pid}")

    except FileNotFoundError:
        print_test("서버 실행", False, "python 또는 cortex_mcp.main을 찾을 수 없음")
        return False
    except Exception as e:
        print_test("서버 실행", False, str(e))
        return False

    # 2. initialize 요청
    print(f"\n{Colors.BOLD}2. initialize 요청{Colors.ENDC}\n")

    init_request = create_initialize_request()
    print_info(f"요청: {init_request['method']}")

    init_response = send_request(proc, init_request)

    if init_response:
        passed, detail = validate_initialize_response(init_response)
        all_passed &= print_test("initialize 응답", passed, detail)
    else:
        all_passed &= print_test("initialize 응답", False, "응답 타임아웃 (5초)")

    # 3. tools/list 요청
    print(f"\n{Colors.BOLD}3. tools/list 요청{Colors.ENDC}\n")

    tools_request = create_tools_list_request()
    print_info(f"요청: {tools_request['method']}")

    tools_response = send_request(proc, tools_request)

    if tools_response:
        passed, detail = validate_tools_list_response(tools_response)
        all_passed &= print_test("tools/list 응답", passed, detail)

        # 도구 목록 출력
        if passed and "result" in tools_response:
            tools = tools_response["result"]["tools"]
            print(f"\n{Colors.BOLD}    감지된 Cortex 도구:{Colors.ENDC}")
            for tool in tools[:10]:  # 처음 10개만 표시
                tool_name = tool.get("name", "unknown")
                print(f"      • {tool_name}")
            if len(tools) > 10:
                print(f"      ... 및 {len(tools) - 10}개 추가 도구")

    else:
        all_passed &= print_test("tools/list 응답", False, "응답 타임아웃 (5초)")

    # 4. 서버 종료
    print(f"\n{Colors.BOLD}4. 서버 종료{Colors.ENDC}\n")

    try:
        proc.terminate()
        proc.wait(timeout=5)
        print_test("서버 종료", True, "정상 종료")
    except subprocess.TimeoutExpired:
        proc.kill()
        print_test("서버 종료", False, "강제 종료됨")
        all_passed = False

    return all_passed


def main():
    """메인 함수"""
    passed = test_mcp_protocol()

    # 최종 결과
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}")

    if passed:
        print_success("Cortex MCP 서버가 정상적으로 작동합니다")
        print()
        print(f"{Colors.BOLD}진단:{Colors.ENDC}")
        print("  ✓ Cortex 서버: 정상")
        print("  ? MCP 클라이언트 설정: 확인 필요")
        print()
        print(f"{Colors.BOLD}다음 단계:{Colors.ENDC}")
        print("  1. MCP 클라이언트 설정 파일 확인")
        print("  2. 클라이언트 재시작")
        print("  3. 여전히 문제가 있으면 python scripts/setup_guide.py 실행")
        return 0

    else:
        print_error("Cortex MCP 서버에 문제가 있습니다")
        print()
        print(f"{Colors.BOLD}진단:{Colors.ENDC}")
        print("  ✗ Cortex 서버: 오류")
        print()
        print(f"{Colors.BOLD}권장 조치:{Colors.ENDC}")
        print("  1. Cortex 재설치: pip install --upgrade cortex-mcp")
        print("  2. 의존성 확인: python scripts/verify_installation.py")
        print("  3. 로그 확인: ~/.cortex/logs/")
        print(f"  4. 문서: {Colors.CYAN}https://cortex-mcp.com/troubleshooting{Colors.ENDC}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}테스트가 중단되었습니다{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
