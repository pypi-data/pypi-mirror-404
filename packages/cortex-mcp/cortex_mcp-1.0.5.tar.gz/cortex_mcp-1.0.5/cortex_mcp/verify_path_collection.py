#!/usr/bin/env python3
"""
Path Collection 버그 수정 검증 스크립트
"""
import subprocess
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
VENV_PYTEST = PROJECT_ROOT.parent / ".venv310" / "bin" / "pytest"
TESTS_DIR = PROJECT_ROOT / "tests"


def collect_all_tests():
    """pytest --collect-only 출력을 파싱하여 모든 테스트 ID 수집 (수정된 로직)"""
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
            # indent=4: tests/test_file.py (root-level)
            # indent=6+: tests/dir/test_file.py (nested)
            if indent == 4:
                # Root-level module
                current_file = f'tests/{file_name}'
            elif dir_stack:
                # Nested module (Dir 하위)
                current_file = 'tests/' + '/'.join(dir_stack) + '/' + file_name
            else:
                # 안전 장치
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
                test_id = f'{current_file}::{current_class}::{func_name}'
            else:
                test_id = f'{current_file}::{func_name}'

            tests.append(test_id)

    print(f"총 {len(tests)}개 테스트 수집 완료\n")
    return tests


def verify_specific_paths(tests):
    """특정 경로가 올바르게 수집되었는지 검증"""
    print("=" * 80)
    print("핵심 경로 검증")
    print("=" * 80)

    test_cases = [
        ("tests/test_bayesian_updater.py", "Root-level 파일"),
        ("tests/e2e/test_needle_in_haystack.py", "e2e 디렉토리 파일"),
        ("tests/functional/test_mcp_tools.py", "functional 디렉토리 파일"),
        ("tests/security/test_license_security.py", "security 디렉토리 파일"),
    ]

    all_passed = True

    for expected_path, description in test_cases:
        # 해당 경로로 시작하는 테스트가 있는지 확인
        matching_tests = [t for t in tests if t.startswith(expected_path)]

        if matching_tests:
            print(f"✅ {description}: {expected_path}")
            print(f"   예시: {matching_tests[0]}")
        else:
            print(f"❌ {description}: {expected_path} - 테스트 없음")
            all_passed = False

    print()
    return all_passed


def check_wrong_paths(tests):
    """잘못된 경로가 있는지 확인"""
    print("=" * 80)
    print("잘못된 경로 검사")
    print("=" * 80)

    # 잘못된 패턴: tests/security/test_bayesian_updater.py (실제로는 root-level)
    wrong_patterns = [
        "tests/security/test_bayesian_updater.py",
        "tests/security/test_claim_extractor.py",
        "tests/security/test_claim_verifier.py",
        "tests/e2e/test_bayesian_updater.py",
        "tests/functional/test_bayesian_updater.py",
    ]

    found_wrong = False

    for pattern in wrong_patterns:
        matching = [t for t in tests if t.startswith(pattern)]
        if matching:
            print(f"❌ 잘못된 경로 발견: {pattern}")
            print(f"   예시: {matching[0]}")
            found_wrong = True

    if not found_wrong:
        print("✅ 잘못된 경로 없음")

    print()
    return not found_wrong


def main():
    """검증 메인 함수"""
    tests = collect_all_tests()

    passed_verification = verify_specific_paths(tests)
    passed_wrong_check = check_wrong_paths(tests)

    print("=" * 80)
    if passed_verification and passed_wrong_check:
        print("✅ 모든 검증 통과!")
        print("Path collection 버그가 수정되었습니다.")
    else:
        print("❌ 검증 실패")
        print("Path collection 버그가 여전히 존재합니다.")
    print("=" * 80)


if __name__ == "__main__":
    main()
