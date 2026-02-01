#!/usr/bin/env python3
"""
Final Test Suite Runner with Hallucination Verification
780개 테스트를 하나씩 실행하고 결과를 final_report.md에 기록
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
REPO_ROOT = PROJECT_ROOT.parent  # /Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp
VENV_PYTHON = REPO_ROOT / ".venv310" / "bin" / "python3"
VENV_PYTEST = REPO_ROOT / ".venv310" / "bin" / "pytest"
TESTS_DIR = PROJECT_ROOT / "tests"
FINAL_TEST_MD = PROJECT_ROOT / "final_test.md"
FINAL_REPORT_MD = PROJECT_ROOT / "final_report.md"


def collect_all_tests():
    """모든 테스트 ID 수집"""
    print("테스트 수집 중...")

    # pytest Python API 사용
    import pytest

    # 테스트 수집을 위한 클래스
    class TestCollector:
        def __init__(self):
            self.collected = []

        def pytest_collection_modifyitems(self, items):
            self.collected = [item.nodeid for item in items]

    collector = TestCollector()

    # pytest 실행 (수집만, 실행은 안 함)
    pytest.main([
        str(TESTS_DIR),
        "--collect-only",
        "-q"
    ], plugins=[collector])

    tests = collector.collected
    print(f"총 {len(tests)}개 테스트 수집 완료")
    return tests


def write_test_list(tests):
    """final_test.md에 테스트 리스트 작성"""
    with open(FINAL_TEST_MD, 'w', encoding='utf-8') as f:
        f.write("# Final Test Suite (780 Tests)\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total Tests: {len(tests)}\n\n")
        f.write("## Test List\n\n")

        for i, test_id in enumerate(tests, 1):
            f.write(f"{i}. {test_id}\n")

    print(f"✅ final_test.md 생성 완료 ({len(tests)}개 테스트)")


def init_report():
    """final_report.md 초기화"""
    with open(FINAL_REPORT_MD, 'w', encoding='utf-8') as f:
        f.write("# Final Test Execution Report\n\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Test Results\n\n")

    print("✅ final_report.md 초기화 완료")


def run_single_test(test_id):
    """단일 테스트 실행"""
    result = subprocess.run(
        [str(VENV_PYTEST), test_id, "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=60
    )

    return {
        'test_id': test_id,
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'passed': result.returncode == 0
    }


def append_test_result(test_num, total, result):
    """테스트 결과를 final_report.md에 추가"""
    with open(FINAL_REPORT_MD, 'a', encoding='utf-8') as f:
        f.write(f"### Test {test_num}/{total}: {result['test_id']}\n\n")
        f.write(f"- Status: {'✅ PASSED' if result['passed'] else '❌ FAILED'}\n")
        f.write(f"- Exit Code: {result['returncode']}\n")
        f.write(f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        if not result['passed']:
            f.write("**Error Output:**\n")
            f.write("```\n")
            f.write(result['stderr'][-500:] if len(result['stderr']) > 500 else result['stderr'])
            f.write("\n```\n\n")

        f.write("---\n\n")


def run_all_tests(tests):
    """모든 테스트 실행"""
    total = len(tests)
    passed = 0
    failed = 0

    print(f"\n{'='*80}")
    print(f"테스트 실행 시작: 총 {total}개")
    print(f"{'='*80}\n")

    for i, test_id in enumerate(tests, 1):
        print(f"[{i}/{total}] {test_id}...", end=' ', flush=True)

        try:
            result = run_single_test(test_id)

            if result['passed']:
                print("✅ PASS")
                passed += 1
            else:
                print("❌ FAIL")
                failed += 1

            append_test_result(i, total, result)

        except subprocess.TimeoutExpired:
            print("⏱ TIMEOUT")
            failed += 1
            append_test_result(i, total, {
                'test_id': test_id,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Test timeout (60s)',
                'passed': False
            })
        except Exception as e:
            print(f"⚠ ERROR: {e}")
            failed += 1
            append_test_result(i, total, {
                'test_id': test_id,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'passed': False
            })

        # 진행 상황 표시
        if i % 50 == 0:
            print(f"\n진행률: {i}/{total} ({i*100//total}%) - PASS: {passed}, FAIL: {failed}\n")

    return passed, failed


def write_summary(passed, failed, total):
    """최종 요약 작성"""
    with open(FINAL_REPORT_MD, 'a', encoding='utf-8') as f:
        f.write("\n## Final Summary\n\n")
        f.write(f"- Total Tests: {total}\n")
        f.write(f"- Passed: {passed} ({passed*100//total}%)\n")
        f.write(f"- Failed: {failed} ({failed*100//total}%)\n")
        f.write(f"- Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        if failed == 0:
            f.write("✅ **ALL TESTS PASSED!**\n")
        else:
            f.write(f"⚠ **{failed} tests failed. Review required.**\n")


def main():
    """메인 실행 함수"""
    print("\n🚀 Final Test Suite Runner 시작\n")

    # 1. 테스트 수집
    tests = collect_all_tests()

    if not tests:
        print("❌ 테스트를 찾을 수 없습니다.")
        return 1

    # 2. final_test.md 작성
    write_test_list(tests)

    # 3. final_report.md 초기화
    init_report()

    # 4. 모든 테스트 실행
    start_time = time.time()
    passed, failed = run_all_tests(tests)
    elapsed = time.time() - start_time

    # 5. 최종 요약
    write_summary(passed, failed, len(tests))

    print(f"\n{'='*80}")
    print(f"✅ 테스트 완료!")
    print(f"{'='*80}")
    print(f"총 실행: {len(tests)}개")
    print(f"성공: {passed}개 ({passed*100//len(tests)}%)")
    print(f"실패: {failed}개 ({failed*100//len(tests)}%)")
    print(f"소요 시간: {elapsed/60:.1f}분")
    print(f"\n📄 결과 파일:")
    print(f"  - {FINAL_TEST_MD}")
    print(f"  - {FINAL_REPORT_MD}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
