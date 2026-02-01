"""
다중 테스트 프레임워크 출력 파서 (Test Output Parser)

Cortex Phase 9.x: 테스트 결과 검증 시스템
다양한 테스트 프레임워크의 출력을 파싱하여 테스트 Claim을 검증합니다.

지원 프레임워크:
- Python: pytest, unittest
- JavaScript: jest, mocha
- Go: go test
- Rust: cargo test
- Ruby: rspec
- Java: JUnit (Maven/Gradle)

보안 원칙:
- Cortex는 테스트를 직접 실행하지 않음 (임의 코드 실행 위험)
- 테스트 결과 파싱만 수행
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """파싱된 테스트 결과"""
    framework: str
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total: int = 0
    coverage: Optional[float] = None
    duration: Optional[str] = None
    parsed: bool = False

    def __post_init__(self):
        """total 자동 계산"""
        if self.total == 0:
            self.total = self.passed + self.failed + self.skipped + self.errors


class TestOutputParser:
    """
    다양한 테스트 프레임워크 출력 파서

    사용법:
        parser = TestOutputParser()
        result = parser.parse(test_output_string)

        if result.parsed:
            print(f"Framework: {result.framework}")
            print(f"Passed: {result.passed}/{result.total}")
    """

    # 프레임워크별 파싱 패턴
    PATTERNS = {
        "pytest": {
            "passed": r'(\d+)\s+passed',
            "failed": r'(\d+)\s+failed',
            "skipped": r'(\d+)\s+skipped',
            "error": r'(\d+)\s+error',
            "duration": r'in\s+([\d.]+)s',
            # 한국어 지원
            "passed_kr": r'(\d+)\s*개\s*(통과|성공)',
            "failed_kr": r'(\d+)\s*개\s*(실패)',
        },
        "unittest": {
            "total": r'Ran\s+(\d+)\s+tests?',
            "ok": r'^OK$',
            "failed": r'FAILED\s+\(failures=(\d+)',
            "errors": r'errors=(\d+)',
            "duration": r'in\s+([\d.]+)s',
        },
        "jest": {
            "passed": r'Tests:\s+(\d+)\s+passed',
            "failed": r'Tests:\s+(\d+)\s+failed',
            "skipped": r'Tests:\s+(\d+)\s+skipped',
            "total": r'Tests:\s+\d+\s+\w+,\s+(\d+)\s+total',
            "duration": r'Time:\s+([\d.]+)\s*s',
            # 대체 패턴
            "passed_alt": r'(\d+)\s+passing',
            "failed_alt": r'(\d+)\s+failing',
        },
        "mocha": {
            "passed": r'(\d+)\s+passing',
            "failed": r'(\d+)\s+failing',
            "pending": r'(\d+)\s+pending',
            "duration": r'\((\d+[ms]+)\)',
        },
        "go_test": {
            "ok": r'^ok\s+\S+\s+([\d.]+s)',
            "fail": r'^FAIL\s+\S+',
            "coverage": r'coverage:\s+([\d.]+)%',
            "passed": r'^---\s+PASS:\s+',
            "failed": r'^---\s+FAIL:\s+',
        },
        "cargo_test": {
            "result_ok": r'test result: ok\.\s+(\d+)\s+passed',
            "result_fail": r'test result: FAILED\.\s+\d+\s+passed;\s+(\d+)\s+failed',
            "ignored": r'(\d+)\s+ignored',
            "filtered": r'(\d+)\s+filtered out',
            "passed": r'^test\s+\S+\s+\.\.\.\s+ok$',
            "failed": r'^test\s+\S+\s+\.\.\.\s+FAILED$',
        },
        "rspec": {
            "total": r'(\d+)\s+examples?',
            "failed": r'(\d+)\s+failures?',
            "pending": r'(\d+)\s+pending',
            "duration": r'Finished in\s+([\d.]+)\s*seconds?',
        },
        "junit_maven": {
            "total": r'Tests run:\s*(\d+)',
            "failed": r'Failures:\s*(\d+)',
            "errors": r'Errors:\s*(\d+)',
            "skipped": r'Skipped:\s*(\d+)',
            "duration": r'Time elapsed:\s*([\d.]+)\s*s',
        },
        "junit_gradle": {
            "total": r'(\d+)\s+tests?',
            "passed": r'(\d+)\s+passed',
            "failed": r'(\d+)\s+failed',
            "skipped": r'(\d+)\s+skipped',
            "success": r'BUILD SUCCESSFUL',
            "failure": r'BUILD FAILED',
        },
    }

    def parse(self, output: str) -> TestResult:
        """
        테스트 출력 파싱

        Args:
            output: 테스트 프레임워크 출력 문자열

        Returns:
            TestResult 객체
        """
        if not output:
            return TestResult(framework="unknown", parsed=False)

        # 각 프레임워크 패턴으로 시도
        for framework, patterns in self.PATTERNS.items():
            result = self._try_parse(output, framework, patterns)
            if result.parsed:
                logger.info(f"[TEST_PARSER] Detected framework: {framework}, "
                           f"passed={result.passed}, failed={result.failed}")
                return result

        logger.warning("[TEST_PARSER] Could not detect test framework")
        return TestResult(framework="unknown", parsed=False)

    def _try_parse(self, output: str, framework: str, patterns: Dict[str, str]) -> TestResult:
        """특정 프레임워크 패턴으로 파싱 시도"""
        result = TestResult(framework=framework)

        for field, pattern in patterns.items():
            matches = re.findall(pattern, output, re.IGNORECASE | re.MULTILINE)

            if matches:
                result.parsed = True
                value = matches[-1] if matches else None  # 마지막 매칭 사용

                # 튜플인 경우 첫 번째 값 사용
                if isinstance(value, tuple):
                    value = value[0]

                if not value:
                    continue

                # 필드별 처리
                if field in ("passed", "passed_alt", "passed_kr"):
                    if value.isdigit():
                        result.passed = max(result.passed, int(value))
                elif field in ("failed", "failed_alt", "failed_kr", "fail"):
                    if value.isdigit():
                        result.failed = max(result.failed, int(value))
                elif field in ("skipped", "pending", "ignored", "filtered"):
                    if value.isdigit():
                        result.skipped = max(result.skipped, int(value))
                elif field in ("error", "errors"):
                    if value.isdigit():
                        result.errors = max(result.errors, int(value))
                elif field == "total":
                    if value.isdigit():
                        result.total = int(value)
                elif field == "coverage":
                    try:
                        result.coverage = float(value)
                    except ValueError:
                        pass
                elif field == "duration":
                    result.duration = value
                elif field == "ok":
                    # pytest/unittest OK = 모든 테스트 통과
                    if result.total > 0:
                        result.passed = result.total
                elif field == "result_ok":
                    # cargo test result line
                    if value.isdigit():
                        result.passed = int(value)
                elif field == "result_fail":
                    # cargo test FAILED result
                    if value.isdigit():
                        result.failed = int(value)
                elif field in ("success", "failure"):
                    # gradle build result (추가 처리 없음)
                    pass

        # 라인 카운팅 방식 (go_test, cargo_test)
        if framework in ("go_test", "cargo_test") and not result.passed:
            passed_count = len(re.findall(patterns.get("passed", r'$^'), output, re.MULTILINE))
            failed_count = len(re.findall(patterns.get("failed", r'$^'), output, re.MULTILINE))
            if passed_count or failed_count:
                result.passed = passed_count
                result.failed = failed_count
                result.parsed = True

        # total 재계산
        if result.parsed and result.total == 0:
            result.total = result.passed + result.failed + result.skipped + result.errors

        return result

    def parse_junit_xml(self, xml_content: str) -> TestResult:
        """
        JUnit XML 형식 파싱 (CI 아티팩트용)

        Args:
            xml_content: JUnit XML 문자열

        Returns:
            TestResult 객체
        """
        result = TestResult(framework="junit_xml")

        try:
            # testsuite 태그에서 통계 추출
            testsuite_match = re.search(
                r'<testsuite[^>]*'
                r'tests="(\d+)"[^>]*'
                r'failures="(\d+)"[^>]*'
                r'errors="(\d+)"',
                xml_content
            )

            if testsuite_match:
                result.total = int(testsuite_match.group(1))
                result.failed = int(testsuite_match.group(2))
                result.errors = int(testsuite_match.group(3))
                result.passed = result.total - result.failed - result.errors
                result.parsed = True

            # 대체 패턴 (속성 순서 다를 수 있음)
            if not result.parsed:
                tests_match = re.search(r'tests="(\d+)"', xml_content)
                failures_match = re.search(r'failures="(\d+)"', xml_content)
                errors_match = re.search(r'errors="(\d+)"', xml_content)
                skipped_match = re.search(r'skipped="(\d+)"', xml_content)

                if tests_match:
                    result.total = int(tests_match.group(1))
                    result.failed = int(failures_match.group(1)) if failures_match else 0
                    result.errors = int(errors_match.group(1)) if errors_match else 0
                    result.skipped = int(skipped_match.group(1)) if skipped_match else 0
                    result.passed = result.total - result.failed - result.errors - result.skipped
                    result.parsed = True

        except Exception as e:
            logger.error(f"[TEST_PARSER] JUnit XML parse error: {e}")

        return result


def extract_test_count_from_claim(text: str) -> Optional[int]:
    """
    Claim 텍스트에서 테스트 개수 추출

    Args:
        text: Claim 텍스트 (예: "10개 테스트가 통과했습니다")

    Returns:
        추출된 숫자 또는 None
    """
    patterns = [
        r'(\d+)\s*개?\s*(테스트|tests?)',  # 한국어
        r'(\d+)\s*tests?\s*(passed|통과)',
        r'all\s*(\d+)\s*tests?',
        r'(\d+)\s*(passed|통과)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue

    # "모든 테스트" = 특정 숫자 없음
    if re.search(r'(모든|all)\s*(테스트|tests?)', text, re.IGNORECASE):
        return 0  # 0은 "전체 통과" 의미로 사용

    return None


# 싱글톤 인스턴스
_parser_instance: Optional[TestOutputParser] = None


def get_test_output_parser() -> TestOutputParser:
    """전역 TestOutputParser 인스턴스 반환"""
    global _parser_instance

    if _parser_instance is None:
        _parser_instance = TestOutputParser()

    return _parser_instance
