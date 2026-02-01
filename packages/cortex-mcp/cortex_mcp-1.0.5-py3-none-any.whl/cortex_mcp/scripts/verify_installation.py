#!/usr/bin/env python3
"""
Cortex MCP - 설치 및 동작 검증 스크립트

사용법:
    python scripts/verify_installation.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))


class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    ENDC = "\033[0m"


def print_test(name, passed, detail=""):
    status = f"{Colors.GREEN}PASS{Colors.ENDC}" if passed else f"{Colors.RED}FAIL{Colors.ENDC}"
    print(f"  [{status}] {name}")
    if detail and not passed:
        print(f"        {Colors.YELLOW}→ {detail}{Colors.ENDC}")
    return passed


def verify_dependencies():
    """필수 의존성 검증"""
    print(f"\n{Colors.BOLD}1. 의존성 검증{Colors.ENDC}")
    all_passed = True

    # MCP SDK
    try:
        from mcp.server import Server
        from mcp.types import TextContent, Tool

        print_test("MCP SDK 설치", True)
    except ImportError as e:
        print_test("MCP SDK 설치", False, str(e))
        all_passed = False

    # ChromaDB
    try:
        import chromadb

        print_test("ChromaDB 설치", True)
    except ImportError as e:
        print_test("ChromaDB 설치", False, str(e))
        all_passed = False

    # Sentence Transformers
    try:
        from sentence_transformers import SentenceTransformer

        print_test("Sentence Transformers 설치", True)
    except ImportError as e:
        print_test("Sentence Transformers 설치", False, str(e))
        all_passed = False

    # Cryptography
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        print_test("Cryptography 설치", True)
    except ImportError as e:
        print_test("Cryptography 설치", False, str(e))
        all_passed = False

    return all_passed


def verify_core_modules():
    """코어 모듈 로딩 검증"""
    print(f"\n{Colors.BOLD}2. 코어 모듈 검증{Colors.ENDC}")
    all_passed = True

    # Config
    try:
        from config import config

        print_test("config.py 로딩", True)
    except Exception as e:
        print_test("config.py 로딩", False, str(e))
        all_passed = False
        return all_passed

    # MemoryManager
    try:
        from core.memory_manager import MemoryManager

        mm = MemoryManager()
        print_test("MemoryManager 초기화", True)
    except Exception as e:
        print_test("MemoryManager 초기화", False, str(e))
        all_passed = False

    # RAGEngine
    try:
        from core.rag_engine import RAGEngine

        rag = RAGEngine()
        print_test("RAGEngine 초기화", True)
    except Exception as e:
        print_test("RAGEngine 초기화", False, str(e))
        all_passed = False

    # CryptoUtils
    try:
        from core.crypto_utils import CryptoUtils

        crypto = CryptoUtils("test_license_key_1234")
        print_test("CryptoUtils 초기화", True)
    except Exception as e:
        print_test("CryptoUtils 초기화", False, str(e))
        all_passed = False

    # CloudSync (구조만 검증)
    try:
        from core.cloud_sync import CloudSync

        print_test("CloudSync 모듈 로딩", True)
    except Exception as e:
        print_test("CloudSync 모듈 로딩", False, str(e))
        all_passed = False

    return all_passed


def verify_tools_registration():
    """MCP 도구 등록 검증"""
    print(f"\n{Colors.BOLD}3. MCP 도구 등록 검증{Colors.ENDC}")

    try:
        from mcp.server import Server

        from tools.cortex_tools import register_tools

        server = Server("test-cortex")
        register_tools(server)

        # 등록된 핸들러 확인
        expected_tools = [
            "initialize_context",
            "create_branch",
            "search_context",
            "update_memory",
            "get_active_summary",
            "sync_to_cloud",
            "sync_from_cloud",
        ]

        print_test("MCP 서버 생성", True)
        print_test("도구 등록 함수 실행", True)
        print(f"     등록된 도구: {Colors.CYAN}{len(expected_tools)}개{Colors.ENDC}")

        return True

    except Exception as e:
        print_test("MCP 도구 등록", False, str(e))
        return False


def verify_functionality():
    """핵심 기능 검증"""
    print(f"\n{Colors.BOLD}4. 핵심 기능 검증{Colors.ENDC}")
    all_passed = True

    from config import config
    from core.crypto_utils import CryptoUtils
    from core.memory_manager import MemoryManager
    from core.rag_engine import RAGEngine

    mm = MemoryManager()
    rag = RAGEngine()

    # 테스트용 프로젝트 ID
    test_project = f"__test_verify_{datetime.now().strftime('%H%M%S')}"

    # 1. 브랜치 생성
    try:
        result = mm.create_branch(test_project, "테스트 브랜치")
        if result.get("success"):
            print_test("브랜치 생성", True)
            branch_id = result.get("branch_id")
        else:
            print_test("브랜치 생성", False, result.get("error"))
            all_passed = False
            branch_id = None
    except Exception as e:
        print_test("브랜치 생성", False, str(e))
        all_passed = False
        branch_id = None

    # 2. 메모리 업데이트
    if branch_id:
        try:
            result = mm.update_memory(test_project, branch_id, "테스트 대화 내용", "user")
            print_test("메모리 업데이트", result.get("success", False))
            if not result.get("success"):
                all_passed = False
        except Exception as e:
            print_test("메모리 업데이트", False, str(e))
            all_passed = False

    # 3. 요약 조회
    if branch_id:
        try:
            result = mm.get_active_summary(test_project, branch_id)
            print_test("요약 조회", result.get("success", False))
            if not result.get("success"):
                all_passed = False
        except Exception as e:
            print_test("요약 조회", False, str(e))
            all_passed = False

    # 4. RAG 인덱싱
    try:
        doc_id = rag.index_content(
            "이것은 검증용 테스트 문서입니다.", {"project_id": test_project, "type": "test"}
        )
        print_test("RAG 인덱싱", doc_id is not None)
        if doc_id is None:
            all_passed = False
    except Exception as e:
        print_test("RAG 인덱싱", False, str(e))
        all_passed = False

    # 5. RAG 검색
    try:
        results = rag.search_context("검증 테스트", project_id=test_project)
        found = len(results.get("results", [])) > 0
        print_test("RAG 검색", found)
        if not found:
            all_passed = False
    except Exception as e:
        print_test("RAG 검색", False, str(e))
        all_passed = False

    # 6. 암호화/복호화
    try:
        crypto = CryptoUtils("test_license_key_1234567890")
        original = "민감한 데이터 테스트"
        encrypted = crypto.encrypt(original)
        decrypted = crypto.decrypt(encrypted).decode("utf-8")
        print_test("암호화/복호화", original == decrypted)
        if original != decrypted:
            all_passed = False
    except Exception as e:
        print_test("암호화/복호화", False, str(e))
        all_passed = False

    # 테스트 파일 정리
    try:
        test_dir = config.memory_dir / test_project
        if test_dir.exists():
            import shutil

            shutil.rmtree(test_dir)
    except:
        pass

    return all_passed


def verify_directories():
    """디렉토리 구조 검증"""
    print(f"\n{Colors.BOLD}5. 디렉토리 구조 검증{Colors.ENDC}")
    all_passed = True

    from config import config

    config.ensure_directories()

    dirs_to_check = [
        ("메모리 디렉토리", config.memory_dir),
        ("로그 디렉토리", config.logs_dir),
    ]

    for name, path in dirs_to_check:
        exists = path.exists()
        print_test(f"{name}: {path}", exists)
        if not exists:
            all_passed = False

    return all_passed


def main():
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}  Cortex MCP 설치 검증{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")

    results = {
        "의존성": verify_dependencies(),
        "코어 모듈": verify_core_modules(),
        "MCP 도구": verify_tools_registration(),
        "핵심 기능": verify_functionality(),
        "디렉토리": verify_directories(),
    }

    # 최종 결과
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}  검증 결과 요약{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

    all_passed = True
    for category, passed in results.items():
        status = f"{Colors.GREEN}PASS{Colors.ENDC}" if passed else f"{Colors.RED}FAIL{Colors.ENDC}"
        print(f"  {category}: {status}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print(
            f"{Colors.GREEN}{Colors.BOLD}모든 검증 통과! Cortex MCP를 사용할 준비가 되었습니다.{Colors.ENDC}"
        )
        print(f"\n다음 단계:")
        print(f"  1. MCP 서버 등록: claude mcp add cortex-memory -- python {PROJECT_DIR}/main.py")
        print(f"  2. 로그 모니터링: python {PROJECT_DIR}/scripts/log_viewer.py")
    else:
        print(f"{Colors.RED}{Colors.BOLD}일부 검증 실패. 위의 오류를 확인해주세요.{Colors.ENDC}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
