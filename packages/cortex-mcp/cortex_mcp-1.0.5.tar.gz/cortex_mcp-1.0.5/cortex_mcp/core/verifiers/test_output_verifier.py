"""
테스트 출력 검증기

pytest, jest, go test 등 테스트 프레임워크 출력을 파싱하여 결과를 확인합니다.
AI가 "테스트가 통과했습니다"라고 주장할 때 실제 테스트 결과를 독립적으로 검증.
"""
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import BaseVerifier, Evidence, EvidenceType, VerificationResult

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """개별 테스트 케이스 결과"""
    name: str
    status: str  # "passed", "failed", "error", "skipped"
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    file_path: Optional[str] = None


@dataclass
class TestResult:
    """테스트 실행 결과"""
    framework: str
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration_seconds: Optional[float] = None
    test_cases: List[TestCase] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """성공률 계산"""
        if self.total == 0:
            return 0.0
        return self.passed / self.total

    @property
    def all_passed(self) -> bool:
        """모든 테스트 통과 여부"""
        return self.failed == 0 and self.errors == 0


class TestOutputParser(ABC):
    """테스트 출력 파서 기본 클래스"""

    @property
    @abstractmethod
    def framework(self) -> str:
        """프레임워크 이름"""
        pass

    @abstractmethod
    def can_parse(self, output: str) -> bool:
        """이 파서로 파싱 가능한지 확인"""
        pass

    @abstractmethod
    def parse(self, output: str) -> TestResult:
        """출력 파싱"""
        pass


class PytestOutputParser(TestOutputParser):
    """pytest 출력 파서"""

    @property
    def framework(self) -> str:
        return "pytest"

    def can_parse(self, output: str) -> bool:
        """pytest 출력인지 확인"""
        indicators = [
            "pytest",
            "test session starts",
            "PASSED",
            "FAILED",
            "passed",
            "failed",
            "collected",
            "===",
        ]
        return any(indicator in output for indicator in indicators)

    def parse(self, output: str) -> TestResult:
        """
        pytest 출력 파싱

        예시:
        =================== test session starts ===================
        collected 7 items

        test_mcp_tools.py::test_init PASSED                  [ 14%]
        test_mcp_tools.py::test_update PASSED                [ 28%]
        ...
        =================== 7 passed in 1.23s ====================
        """
        test_cases: List[TestCase] = []
        total = 0
        passed = 0
        failed = 0
        errors = 0
        skipped = 0
        duration = None

        # 요약 라인 파싱: "7 passed, 2 failed, 1 error in 1.23s"
        summary_pattern = r'(\d+)\s+(passed|failed|error|errors|skipped|warnings?|deselected)'
        for match in re.finditer(summary_pattern, output, re.IGNORECASE):
            count = int(match.group(1))
            status = match.group(2).lower()

            if status == "passed":
                passed = count
            elif status == "failed":
                failed = count
            elif status in ("error", "errors"):
                errors = count
            elif status == "skipped":
                skipped = count

        # 총 테스트 수 계산
        total = passed + failed + errors + skipped

        # collected N items 에서 총 수 추출
        collected_match = re.search(r'collected\s+(\d+)\s+item', output)
        if collected_match:
            collected = int(collected_match.group(1))
            total = max(total, collected)

        # 실행 시간 추출: "in 1.23s"
        duration_match = re.search(r'in\s+([\d.]+)\s*s(?:econds?)?', output)
        if duration_match:
            duration = float(duration_match.group(1))

        # 개별 테스트 케이스 파싱
        # 패턴: test_file.py::test_name PASSED/FAILED [percentage]
        test_pattern = r'(\S+\.py)::(\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)'
        for match in re.finditer(test_pattern, output):
            file_path = match.group(1)
            test_name = match.group(2)
            status = match.group(3).lower()

            test_cases.append(TestCase(
                name=f"{file_path}::{test_name}",
                status=status,
                file_path=file_path
            ))

        # 테스트 케이스가 없으면 간단한 패턴 시도
        if not test_cases:
            simple_pattern = r'(\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)'
            for match in re.finditer(simple_pattern, output):
                test_name = match.group(1)
                status = match.group(2).lower()
                if not test_name.startswith('='):
                    test_cases.append(TestCase(
                        name=test_name,
                        status=status
                    ))

        # 총 수가 0이면 테스트 케이스 수로 대체
        if total == 0 and test_cases:
            total = len(test_cases)
            passed = sum(1 for tc in test_cases if tc.status == "passed")
            failed = sum(1 for tc in test_cases if tc.status == "failed")
            errors = sum(1 for tc in test_cases if tc.status == "error")
            skipped = sum(1 for tc in test_cases if tc.status == "skipped")

        return TestResult(
            framework="pytest",
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            duration_seconds=duration,
            test_cases=test_cases
        )


class JestOutputParser(TestOutputParser):
    """jest 출력 파서"""

    @property
    def framework(self) -> str:
        return "jest"

    def can_parse(self, output: str) -> bool:
        """jest 출력인지 확인"""
        indicators = [
            "PASS ",
            "FAIL ",
            "Tests:",
            "jest",
            "Test Suites:",
        ]
        return any(indicator in output for indicator in indicators)

    def parse(self, output: str) -> TestResult:
        """
        jest 출력 파싱

        예시:
        PASS  tests/app.test.js
          App Component
            should initialize correctly (5ms)
            should handle errors (3ms)

        Tests:       2 passed, 2 total
        Time:        1.234s
        """
        test_cases: List[TestCase] = []
        passed = 0
        failed = 0
        total = 0
        duration = None

        # Tests: N passed, N failed, N total
        summary_match = re.search(
            r'Tests:\s+(?:(\d+)\s+failed,\s+)?(?:(\d+)\s+skipped,\s+)?(\d+)\s+passed,\s+(\d+)\s+total',
            output
        )
        if summary_match:
            failed = int(summary_match.group(1) or 0)
            # skipped = int(summary_match.group(2) or 0)
            passed = int(summary_match.group(3))
            total = int(summary_match.group(4))
        else:
            # 간단한 패턴: "N passed, N total"
            simple_match = re.search(r'(\d+)\s+passed.*?(\d+)\s+total', output)
            if simple_match:
                passed = int(simple_match.group(1))
                total = int(simple_match.group(2))

        # 실행 시간: Time: 1.234s
        time_match = re.search(r'Time:\s*([\d.]+)\s*s', output)
        if time_match:
            duration = float(time_match.group(1))

        # 개별 테스트 파싱 (체크마크/X 패턴)
        test_pattern = r'([✓✔√]|[✕✗×]|○)\s+(.+?)(?:\s*\((\d+)\s*ms\))?\s*$'
        for match in re.finditer(test_pattern, output, re.MULTILINE):
            symbol = match.group(1)
            name = match.group(2).strip()
            duration_ms = float(match.group(3)) if match.group(3) else None

            if symbol in '✓✔√':
                status = "passed"
            elif symbol in '✕✗×':
                status = "failed"
            else:
                status = "skipped"

            test_cases.append(TestCase(
                name=name,
                status=status,
                duration_ms=duration_ms
            ))

        return TestResult(
            framework="jest",
            total=total,
            passed=passed,
            failed=failed,
            errors=0,
            skipped=total - passed - failed,
            duration_seconds=duration,
            test_cases=test_cases
        )


class GoTestOutputParser(TestOutputParser):
    """go test 출력 파서"""

    @property
    def framework(self) -> str:
        return "go_test"

    def can_parse(self, output: str) -> bool:
        """go test 출력인지 확인"""
        indicators = [
            "--- PASS:",
            "--- FAIL:",
            "PASS",
            "FAIL",
            "ok  \t",
            "go test",
        ]
        return any(indicator in output for indicator in indicators)

    def parse(self, output: str) -> TestResult:
        """
        go test 출력 파싱

        예시:
        === RUN   TestAdd
        --- PASS: TestAdd (0.00s)
        === RUN   TestSubtract
        --- PASS: TestSubtract (0.00s)
        PASS
        ok      mypackage       0.123s
        """
        test_cases: List[TestCase] = []
        passed = 0
        failed = 0
        duration = None

        # 개별 테스트 결과 파싱
        test_pattern = r'---\s+(PASS|FAIL):\s+(\w+)\s*\(([\d.]+)s\)'
        for match in re.finditer(test_pattern, output):
            status = match.group(1).lower()
            name = match.group(2)
            test_duration = float(match.group(3))

            test_cases.append(TestCase(
                name=name,
                status="passed" if status == "pass" else "failed",
                duration_ms=test_duration * 1000
            ))

            if status == "pass":
                passed += 1
            else:
                failed += 1

        # 전체 결과: ok mypackage 0.123s
        summary_match = re.search(r'ok\s+\S+\s+([\d.]+)s', output)
        if summary_match:
            duration = float(summary_match.group(1))

        # FAIL 패키지 확인
        if 'FAIL' in output and not test_cases:
            failed = 1

        total = len(test_cases) if test_cases else (passed + failed)

        return TestResult(
            framework="go_test",
            total=total,
            passed=passed,
            failed=failed,
            errors=0,
            skipped=0,
            duration_seconds=duration,
            test_cases=test_cases
        )


class UnittestOutputParser(TestOutputParser):
    """Python unittest 출력 파서"""

    @property
    def framework(self) -> str:
        return "unittest"

    def can_parse(self, output: str) -> bool:
        """unittest 출력인지 확인"""
        indicators = [
            "Ran ",
            "OK",
            "FAILED (failures=",
            "test (",
            "....",
        ]
        return any(indicator in output for indicator in indicators)

    def parse(self, output: str) -> TestResult:
        """
        unittest 출력 파싱

        예시:
        test_add (__main__.TestMath) ... ok
        test_subtract (__main__.TestMath) ... ok

        ----------------------------------------------------------------------
        Ran 2 tests in 0.001s

        OK
        """
        test_cases: List[TestCase] = []
        passed = 0
        failed = 0
        errors = 0
        total = 0
        duration = None

        # Ran N tests in X.XXXs
        ran_match = re.search(r'Ran\s+(\d+)\s+tests?\s+in\s+([\d.]+)s', output)
        if ran_match:
            total = int(ran_match.group(1))
            duration = float(ran_match.group(2))

        # FAILED (failures=N, errors=N)
        failed_match = re.search(r'FAILED\s*\((?:failures=(\d+))?(?:,?\s*errors=(\d+))?\)', output)
        if failed_match:
            failed = int(failed_match.group(1) or 0)
            errors = int(failed_match.group(2) or 0)
            passed = total - failed - errors
        elif 'OK' in output:
            passed = total

        # 개별 테스트 파싱: test_name (module.class) ... ok/FAIL/ERROR
        test_pattern = r'(\w+)\s+\(([^)]+)\)\s*\.\.\.\s*(ok|FAIL|ERROR)'
        for match in re.finditer(test_pattern, output):
            name = match.group(1)
            module = match.group(2)
            status = match.group(3).lower()

            test_cases.append(TestCase(
                name=f"{module}.{name}",
                status="passed" if status == "ok" else status
            ))

        return TestResult(
            framework="unittest",
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=0,
            duration_seconds=duration,
            test_cases=test_cases
        )


class TestOutputVerifier(BaseVerifier):
    """
    테스트 출력 검증기

    pytest, jest, go test 등의 테스트 출력을 파싱하여 결과를 검증합니다.
    """

    def __init__(self):
        self.parsers: List[TestOutputParser] = [
            PytestOutputParser(),
            JestOutputParser(),
            GoTestOutputParser(),
            UnittestOutputParser(),
        ]

    @property
    def verifier_type(self) -> str:
        return "test_output"

    def verify(self, claim: Any, context: Dict[str, Any]) -> VerificationResult:
        """
        테스트 관련 Claim 검증

        Args:
            claim: Claim 객체
            context: {
                "test_output": str (필수),
                "expected_pass_count": int (선택),
                "expected_total_count": int (선택)
            }

        Returns:
            VerificationResult
        """
        test_output = context.get("test_output", "")

        if not test_output:
            return self._create_result(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason="테스트 출력이 제공되지 않음"
            )

        # 프레임워크 감지 및 파싱
        result = self._parse_output(test_output)

        if not result:
            return self._create_result(
                verified=False,
                confidence=0.3,
                evidence=[],
                reason="테스트 출력을 파싱할 수 없음"
            )

        # Claim 분석
        claim_text = getattr(claim, 'text', str(claim)).lower()

        # 예상 값이 context에 제공된 경우
        expected_pass = context.get("expected_pass_count")
        expected_total = context.get("expected_total_count")

        if expected_pass is not None and expected_total is not None:
            if result.passed == expected_pass and result.total == expected_total:
                evidence = self._create_test_evidence(result, test_output)
                return self._create_result(
                    verified=True,
                    confidence=0.99,
                    evidence=[evidence],
                    reason=f"테스트 결과 일치: {expected_pass}/{expected_total}"
                )
            else:
                return self._create_result(
                    verified=False,
                    confidence=0.9,
                    evidence=[self._create_test_evidence(result, test_output)],
                    reason=f"테스트 결과 불일치: 예상 {expected_pass}/{expected_total}, 실제 {result.passed}/{result.total}"
                )

        # "테스트 통과", "all tests passed" 등의 주장 검증
        claims_all_passed = any(phrase in claim_text for phrase in [
            "테스트 통과", "테스트가 통과", "all pass", "tests pass",
            "성공", "모두 통과", "100%", "모든 테스트", "전체 통과"
        ])

        # 숫자 기반 주장 검증 ("7/7", "7개 중 7개", "7 of 7")
        number_patterns = [
            r'(\d+)\s*/\s*(\d+)',  # 7/7
            r'(\d+)\s*(?:개|건|)\s*(?:중|of)\s*(\d+)',  # 7개 중 7
            r'(\d+)\s*(?:passed|통과)\s*(?:out of|of|,)\s*(\d+)',  # 7 passed of 7
        ]

        for pattern in number_patterns:
            match = re.search(pattern, claim_text)
            if match:
                claimed_passed = int(match.group(1))
                claimed_total = int(match.group(2))

                if result.passed == claimed_passed and result.total == claimed_total:
                    evidence = self._create_test_evidence(result, test_output)
                    return self._create_result(
                        verified=True,
                        confidence=0.99,
                        evidence=[evidence],
                        reason=f"테스트 결과 일치: {claimed_passed}/{claimed_total}"
                    )
                else:
                    return self._create_result(
                        verified=False,
                        confidence=0.9,
                        evidence=[self._create_test_evidence(result, test_output)],
                        reason=f"테스트 결과 불일치: 주장 {claimed_passed}/{claimed_total}, 실제 {result.passed}/{result.total}"
                    )

        # 일반 "통과" 주장 검증
        if claims_all_passed:
            if result.all_passed:
                evidence = self._create_test_evidence(result, test_output)
                return self._create_result(
                    verified=True,
                    confidence=0.95,
                    evidence=[evidence],
                    reason=f"모든 테스트 통과: {result.passed}/{result.total}"
                )
            else:
                evidence = self._create_test_evidence(result, test_output)
                return self._create_result(
                    verified=False,
                    confidence=0.95,
                    evidence=[evidence],
                    reason=f"테스트 실패 있음: {result.failed} failed, {result.errors} errors"
                )

        # "실패" 주장 검증
        claims_failed = any(phrase in claim_text for phrase in [
            "테스트 실패", "failed", "error", "에러", "오류"
        ])

        if claims_failed:
            if not result.all_passed:
                evidence = self._create_test_evidence(result, test_output)
                return self._create_result(
                    verified=True,
                    confidence=0.95,
                    evidence=[evidence],
                    reason=f"테스트 실패 확인: {result.failed} failed, {result.errors} errors"
                )
            else:
                return self._create_result(
                    verified=False,
                    confidence=0.95,
                    evidence=[self._create_test_evidence(result, test_output)],
                    reason=f"테스트가 모두 통과했음 ({result.passed}/{result.total})"
                )

        # 기본: 테스트 결과만 반환
        evidence = self._create_test_evidence(result, test_output)
        return self._create_result(
            verified=result.all_passed,
            confidence=0.8,
            evidence=[evidence],
            reason=f"테스트 결과: {result.passed} passed, {result.failed} failed, {result.errors} errors"
        )

    def parse_test_output(self, output: str) -> Optional[TestResult]:
        """
        테스트 출력 파싱 (외부 호출용)

        Args:
            output: 테스트 출력 문자열

        Returns:
            TestResult 또는 None
        """
        return self._parse_output(output)

    def verify_test_count(
        self,
        test_output: str,
        expected_passed: int,
        expected_total: int
    ) -> VerificationResult:
        """
        특정 테스트 수 검증 (편의 메서드)

        Args:
            test_output: 테스트 출력
            expected_passed: 예상 통과 수
            expected_total: 예상 전체 수

        Returns:
            VerificationResult
        """
        result = self._parse_output(test_output)

        if not result:
            return self._create_result(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason="테스트 출력을 파싱할 수 없음"
            )

        if result.passed == expected_passed and result.total == expected_total:
            evidence = self._create_test_evidence(result, test_output)
            return self._create_result(
                verified=True,
                confidence=0.99,
                evidence=[evidence],
                reason=f"테스트 결과 일치: {expected_passed}/{expected_total}"
            )
        else:
            return self._create_result(
                verified=False,
                confidence=0.9,
                evidence=[self._create_test_evidence(result, test_output)],
                reason=f"테스트 결과 불일치: 예상 {expected_passed}/{expected_total}, 실제 {result.passed}/{result.total}"
            )

    def verify_all_passed(self, test_output: str) -> VerificationResult:
        """
        모든 테스트 통과 검증 (편의 메서드)

        Args:
            test_output: 테스트 출력

        Returns:
            VerificationResult
        """
        result = self._parse_output(test_output)

        if not result:
            return self._create_result(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason="테스트 출력을 파싱할 수 없음"
            )

        if result.all_passed:
            evidence = self._create_test_evidence(result, test_output)
            return self._create_result(
                verified=True,
                confidence=0.99,
                evidence=[evidence],
                reason=f"모든 테스트 통과: {result.passed}/{result.total}"
            )
        else:
            return self._create_result(
                verified=False,
                confidence=0.95,
                evidence=[self._create_test_evidence(result, test_output)],
                reason=f"테스트 실패 있음: {result.failed} failed, {result.errors} errors"
            )

    def _parse_output(self, output: str) -> Optional[TestResult]:
        """적절한 파서로 출력 파싱"""
        for parser in self.parsers:
            if parser.can_parse(output):
                try:
                    result = parser.parse(output)
                    logger.info(f"[TestOutputVerifier] {parser.framework} 파서 사용: {result.passed}/{result.total}")
                    return result
                except Exception as e:
                    logger.warning(f"[TestOutputVerifier] {parser.framework} 파싱 실패: {e}")
                    continue

        logger.warning("[TestOutputVerifier] 적절한 파서를 찾을 수 없음")
        return None

    def _create_test_evidence(self, result: TestResult, raw_output: str) -> Evidence:
        """테스트 결과로부터 Evidence 생성"""
        # 실패한 테스트 케이스 목록
        failed_tests = [tc.name for tc in result.test_cases if tc.status in ("failed", "error")]

        return self._create_evidence(
            type=EvidenceType.TEST_RESULT,
            source=result.framework,
            content=f"{result.passed}/{result.total} tests passed ({result.success_rate:.1%})",
            confidence=0.99 if result.all_passed else 0.5,
            metadata={
                "framework": result.framework,
                "total": result.total,
                "passed": result.passed,
                "failed": result.failed,
                "errors": result.errors,
                "skipped": result.skipped,
                "success_rate": result.success_rate,
                "duration_seconds": result.duration_seconds,
                "failed_tests": failed_tests[:10],  # 최대 10개
                "raw_output_preview": raw_output[:500] if raw_output else "",
            }
        )
