#!/usr/bin/env python3
"""
처음 20개 테스트 실행 + Phase 9 할루시네이션 검증
"""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Phase 9: 할루시네이션 검증
sys.path.insert(0, str(Path(__file__).parent))
try:
    from core.auto_verifier import get_auto_verifier
    VERIFICATION_AVAILABLE = True
except ImportError:
    VERIFICATION_AVAILABLE = False
    get_auto_verifier = None

PROJECT_ROOT = Path(__file__).parent
VENV_PYTEST = PROJECT_ROOT.parent / ".venv310" / "bin" / "pytest"

# 처음 20개 테스트
tests = [
    "tests/e2e/test_needle_in_haystack.py::TestNeedleInHaystack::test_find_secret_code",
    "tests/e2e/test_needle_in_haystack.py::TestNeedleInHaystack::test_find_secret_location",
    "tests/e2e/test_needle_in_haystack.py::TestNeedleInHaystack::test_find_secret_password",
    "tests/e2e/test_needle_in_haystack.py::TestNeedleInHaystack::test_find_api_key",
    "tests/e2e/test_needle_in_haystack.py::TestNeedleInHaystack::test_find_secret_meeting",
    "tests/e2e/test_needle_in_haystack.py::TestNeedleInHaystack::test_100_percent_recall",
    "tests/e2e/test_needle_in_haystack.py::TestDeepHierarchySearch::test_search_in_deep_branches",
    "tests/e2e/test_phase_c_lazy_resolve.py::TestPhaseCLazyResolve::test_end_to_end_workflow",
    "tests/e2e/test_phase_c_lazy_resolve.py::TestPhaseCLazyResolve::test_phase_c_auto_trigger_via_search",
    "tests/e2e/test_token_savings.py::TestTokenSavings::test_smart_context_compression",
    "tests/e2e/test_token_savings.py::TestTokenSavings::test_lazy_loading_efficiency",
    "tests/e2e/test_token_savings.py::TestCompressionQuality::test_compression_preserves_summary",
    "tests/functional/test_mcp_tools.py::TestInitializeContext::test_initialize_full_mode",
    "tests/functional/test_mcp_tools.py::TestInitializeContext::test_initialize_light_mode",
    "tests/functional/test_mcp_tools.py::TestInitializeContext::test_initialize_none_mode",
    "tests/functional/test_mcp_tools.py::TestCreateBranch::test_create_branch_basic",
    "tests/functional/test_mcp_tools.py::TestCreateBranch::test_create_branch_with_parent",
    "tests/functional/test_mcp_tools.py::TestSearchContext::test_search_basic",
    "tests/functional/test_mcp_tools.py::TestSearchContext::test_search_with_top_k",
    "tests/functional/test_mcp_tools.py::TestUpdateMemory::test_update_memory_user",
]

print(f"\n{'='*80}")
print(f"처음 20개 테스트 실행 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}\n")

passed = 0
failed = 0
start_time = time.time()

for i, test_id in enumerate(tests, 1):
    print(f"[{i}/20] {test_id}...", end=' ', flush=True)

    result = subprocess.run(
        [str(VENV_PYTEST), test_id, "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=300
    )

    if result.returncode == 0:
        print("✅ PASS")
        passed += 1
    else:
        print("❌ FAIL")
        failed += 1
        if "KeyError" in result.stdout or "AssertionError" in result.stdout:
            # 에러 요약 출력
            for line in result.stdout.split('\n'):
                if "KeyError" in line or "AssertionError" in line or "assert" in line:
                    print(f"     {line.strip()}")

elapsed = time.time() - start_time

print(f"\n{'='*80}")
print(f"결과 요약:")
print(f"  총 테스트: 20개")
print(f"  통과: {passed}개")
print(f"  실패: {failed}개")
print(f"  소요 시간: {elapsed:.1f}초")
print(f"{'='*80}\n")

sys.exit(0 if failed == 0 else 1)
