#!/usr/bin/env python3
"""
Final Test Suite Runner with Hallucination Verification
571개 테스트를 하나씩 실행하고 결과를 final_report.md에 기록
각 테스트 결과에 대해 Phase 9 할루시네이션 검증 수행
"""

import subprocess
import sys
import time
import re
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
REPO_ROOT = PROJECT_ROOT.parent
VENV_PYTEST = REPO_ROOT / ".venv310" / "bin" / "pytest"
TESTS_DIR = PROJECT_ROOT / "tests"
FINAL_TEST_MD = PROJECT_ROOT / "final_test.md"
FINAL_REPORT_MD = PROJECT_ROOT / "final_report.md"


def collect_all_tests():
    """pytest --collect-only 출력을 파싱하여 모든 테스트 ID 수집

    올바른 로직:
    1. Package 레벨은 무시 (<Package cortex_mcp>, <Package tests>)
    2. Dir 레벨만 경로에 포함 (<Dir e2e>, <Dir functional> 등)
    3. indent로 Dir 계층 판단
    4. 최종 경로: tests/[dir1]/[dir2]/test_file.py::TestClass::test_function
    """
    print("테스트 수집 중...")

    result = subprocess.run(
        [str(VENV_PYTEST), str(TESTS_DIR), "--collect-only"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )

    # 출력 파싱
    lines = result.stdout.split('\n')

    dir_stack = []  # 디렉토리 스택 (indent 레벨 기준)
    current_file = None
    current_class = None
    tests = []

    for line in lines:
        # 빈 줄이나 설명 줄 건너뛰기
        if not line.strip() or '<' not in line:
            continue

        # 들여쓰기 레벨 계산 (공백 문자 수)
        indent = len(line) - len(line.lstrip())

        # Package 무시 (<Package cortex_mcp>, <Package tests>)
        if '<Package' in line:
            continue

        # Dir 파싱: <Dir xxx>
        dir_match = re.search(r'<Dir (.+)>', line)
        if dir_match:
            dir_name = dir_match.group(1)
            # indent 레벨로 Dir 계층 판단
            # indent=4: <Dir e2e> (level 0)
            # indent=6: <Dir sub_dir> (level 1)
            # indent=8: <Dir sub_sub_dir> (level 2)
            dir_level = (indent - 4) // 2

            # 스택 조정: 현재 레벨까지만 유지
            dir_stack = dir_stack[:dir_level]
            dir_stack.append(dir_name)

            # Module, Class 리셋
            current_file = None
            current_class = None
            continue

        # Module 파싱: <Module test_xxx.py>
        module_match = re.search(r'<Module (.+\.py)>', line)
        if module_match:
            file_name = module_match.group(1)

            # indent로 root-level 판단
            # indent=4: tests/test_file.py (root-level, Package tests 바로 아래)
            # indent=6+: tests/dir/test_file.py (nested, Dir 하위)
            if indent == 4:
                # Root-level module
                current_file = f'tests/{file_name}'
            elif dir_stack:
                # Nested module (Dir 하위)
                current_file = 'tests/' + '/'.join(dir_stack) + '/' + file_name
            else:
                # 안전 장치: dir_stack이 없는데 indent > 4인 경우
                current_file = f'tests/{file_name}'

            # Class 리셋
            current_class = None
            continue

        # Class 파싱: <Class TestXxx>
        class_match = re.search(r'<Class (.+)>', line)
        if class_match:
            current_class = class_match.group(1)
            continue

        # Function 파싱: <Function test_xxx>
        func_match = re.search(r'<Function (.+)>', line)
        if func_match and current_file:
            func_name = func_match.group(1)

            # 테스트 ID 생성
            if current_class:
                # tests/dir/test_file.py::TestClass::test_function
                test_id = f'{current_file}::{current_class}::{func_name}'
            else:
                # tests/dir/test_file.py::test_function
                test_id = f'{current_file}::{func_name}'

            tests.append(test_id)

    print(f"총 {len(tests)}개 테스트 수집 완료")
    return tests


def write_test_list(tests):
    """final_test.md에 테스트 리스트 작성"""
    with open(FINAL_TEST_MD, 'w', encoding='utf-8') as f:
        f.write(f"# Final Test Suite ({len(tests)} Tests)\n\n")
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


def verify_test_result(test_id, test_passed, stdout, stderr):
    """Phase 9: 테스트 결과에 대한 할루시네이션 검증"""
    if not VERIFICATION_AVAILABLE:
        return {
            'verified': None,
            'grounding_score': None,
            'message': 'Verification not available'
        }

    try:
        verifier = get_auto_verifier()

        # 검증할 응답 텍스트 생성
        response_text = f"""테스트 실행 결과:
테스트: {test_id}
상태: {'PASSED' if test_passed else 'FAILED'}

출력:
{stdout[-500:] if len(stdout) > 500 else stdout}

{f'에러: {stderr[-500:]}' if stderr and not test_passed else ''}
"""

        # 검증 실행
        verification_result = verifier.verify_response(
            response_text=response_text,
            context={}
        )

        return {
            'verified': verification_result.verified,
            'grounding_score': verification_result.grounding_score,
            'confidence_level': verification_result.confidence_level,
            'requires_retry': verification_result.requires_retry,
            'claims_count': len(verification_result.claims),
            'unverified_claims_count': len(verification_result.unverified_claims),
            'message': f"Verified: {verification_result.verified}, Score: {verification_result.grounding_score:.2f}"
        }
    except Exception as e:
        return {
            'verified': None,
            'grounding_score': None,
            'message': f'Verification error: {str(e)}'
        }


def run_single_test(test_id):
    """단일 테스트 실행 + 할루시네이션 검증"""
    try:
        result = subprocess.run(
            [str(VENV_PYTEST), test_id, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=300  # 5분으로 증가
        )

        # Phase 9: 할루시네이션 검증
        verification = verify_test_result(
            test_id=test_id,
            test_passed=(result.returncode == 0),
            stdout=result.stdout,
            stderr=result.stderr
        )

        return {
            'test_id': test_id,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'passed': result.returncode == 0,
            'error': None,
            'verification': verification  # Phase 9 결과 추가
        }
    except subprocess.TimeoutExpired:
        return {
            'test_id': test_id,
            'returncode': -1,
            'stdout': '',
            'stderr': 'Test timeout (300s)',
            'passed': False,
            'error': 'TIMEOUT',
            'verification': {'verified': None, 'grounding_score': None, 'message': 'Skipped (timeout)'}
        }
    except Exception as e:
        return {
            'test_id': test_id,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e),
            'passed': False,
            'error': str(e),
            'verification': {'verified': None, 'grounding_score': None, 'message': 'Skipped (error)'}
        }


def append_test_result(test_num, total, result):
    """테스트 결과 + 할루시네이션 검증 결과를 final_report.md에 추가"""
    with open(FINAL_REPORT_MD, 'a', encoding='utf-8') as f:
        f.write(f"### Test {test_num}/{total}: {result['test_id']}\n\n")
        f.write(f"- Status: {'✅ PASSED' if result['passed'] else '❌ FAILED'}\n")
        f.write(f"- Exit Code: {result['returncode']}\n")
        f.write(f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if result['error']:
            f.write(f"- Error: {result['error']}\n")

        # Phase 9: 할루시네이션 검증 결과 추가
        if 'verification' in result and result['verification']:
            v = result['verification']
            f.write(f"\n**Phase 9 Hallucination Verification:**\n")
            if v['verified'] is not None:
                f.write(f"- Verified: {'✅ YES' if v['verified'] else '❌ NO'}\n")
                f.write(f"- Grounding Score: {v['grounding_score']:.2f}\n")
                f.write(f"- Confidence Level: {v['confidence_level']}\n")
                f.write(f"- Claims: {v['claims_count']} total, {v['unverified_claims_count']} unverified\n")
                if v['requires_retry']:
                    f.write(f"- ⚠️ Requires Retry: YES\n")
            else:
                f.write(f"- {v['message']}\n")

        f.write("\n")

        if not result['passed'] and result['stderr']:
            f.write("**Error Output:**\n")
            f.write("```\n")
            error_msg = result['stderr'][-1000:] if len(result['stderr']) > 1000 else result['stderr']
            f.write(error_msg)
            f.write("\n```\n\n")

        f.write("---\n\n")


def run_all_tests(tests):
    """모든 테스트 실행"""
    total = len(tests)
    passed = 0
    failed = 0
    start_time = time.time()

    print(f"\n{'='*80}")
    print(f"테스트 실행 시작: 총 {total}개")
    print(f"{'='*80}\n")

    for i, test_id in enumerate(tests, 1):
        # 진행 상황 표시
        elapsed = time.time() - start_time
        avg_time = elapsed / i if i > 0 else 0
        eta = avg_time * (total - i)

        print(f"[{i}/{total}] ({elapsed/60:.1f}분 경과, ETA: {eta/60:.1f}분) {test_id}...", end=' ', flush=True)

        result = run_single_test(test_id)

        if result['passed']:
            print("✅ PASS")
            passed += 1
        else:
            print(f"❌ FAIL ({result['error'] or 'test failure'})")
            failed += 1

        append_test_result(i, total, result)

        # 50개마다 요약 출력
        if i % 50 == 0:
            print(f"\n--- 진행률: {i}/{total} ({i*100//total}%) | PASS: {passed} | FAIL: {failed} ---\n")

    return passed, failed, time.time() - start_time


def write_summary(passed, failed, total, elapsed):
    """최종 요약 작성"""
    with open(FINAL_REPORT_MD, 'a', encoding='utf-8') as f:
        f.write("\n## Final Summary\n\n")
        f.write(f"- Total Tests: {total}\n")
        f.write(f"- Passed: {passed} ({passed*100//total}%)\n")
        f.write(f"- Failed: {failed} ({failed*100//total}%)\n")
        f.write(f"- Duration: {elapsed/60:.1f} minutes\n")
        f.write(f"- Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        if failed == 0:
            f.write("✅ **ALL TESTS PASSED!**\n")
        else:
            f.write(f"⚠ **{failed} tests failed. Review required.**\n")


def main():
    """메인 실행 함수"""
    print("\n🚀 Final Test Suite Runner v2 시작\n")

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
    passed, failed, elapsed = run_all_tests(tests)

    # 5. 최종 요약
    write_summary(passed, failed, len(tests), elapsed)

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
