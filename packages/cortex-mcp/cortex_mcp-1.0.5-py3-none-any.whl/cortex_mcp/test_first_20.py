#!/usr/bin/env python3
"""
처음 20개 테스트 실행 스크립트
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
VENV_PYTEST = PROJECT_ROOT.parent / ".venv310" / "bin" / "pytest"

# 처음 20개 테스트 목록
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

print(f"처음 20개 테스트 실행 시작...")
print(f"=" * 80)

result = subprocess.run(
    [str(VENV_PYTEST)] + tests + ["-v", "--tb=line"],
    cwd=PROJECT_ROOT,
)

sys.exit(result.returncode)
