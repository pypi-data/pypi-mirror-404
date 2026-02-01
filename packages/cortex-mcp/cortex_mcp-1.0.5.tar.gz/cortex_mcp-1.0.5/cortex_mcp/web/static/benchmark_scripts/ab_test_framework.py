"""
A/B 테스트 프레임워크 (v3.0)

Cortex vs 경쟁사 RAG 비교 테스트

목표:
- Agent Decision Error Rate: 50% 감소 (경쟁사 대비)
- 통계적 유의미성: p-value < 0.05

오류 유형:
1. 맥락 누락: 필요한 맥락을 로드하지 않음
2. 맥락 오염: 관련 없는 맥락을 로드함
3. 추론 오류: 잘못된 결론 도출
4. 일관성 오류: 이전 대화와 모순
"""

import math
import statistics
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ErrorType(Enum):
    """오류 유형"""

    CONTEXT_MISSING = "context_missing"  # 맥락 누락
    CONTEXT_POLLUTION = "context_pollution"  # 맥락 오염
    REASONING_ERROR = "reasoning_error"  # 추론 오류
    CONSISTENCY_ERROR = "consistency_error"  # 일관성 오류


class TestDomain(Enum):
    """테스트 도메인"""

    CODING = "coding"  # 코딩: 함수 구현 → 오류율 측정
    DOCUMENT = "document"  # 문서: 정보 검색 → 정확도 측정
    CONVERSATION = "conversation"  # 대화: 맥락 유지 → 일관성 측정


@dataclass
class TestCase:
    """테스트 케이스"""

    id: str
    domain: TestDomain
    query: str
    expected_output: Any
    ground_truth_contexts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """단일 테스트 결과"""

    test_case_id: str
    output: Any
    latency_ms: float
    contexts_used: List[str] = field(default_factory=list)
    errors: List[ErrorType] = field(default_factory=list)
    score: float = 0.0  # 0.0 ~ 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTestResult:
    """A/B 테스트 결과"""

    # 기본 지표
    cortex_error_rate: float
    baseline_error_rate: float
    improvement_percentage: float
    p_value: float
    statistically_significant: bool

    # 상세 지표
    cortex_results: List[TestResult] = field(default_factory=list)
    baseline_results: List[TestResult] = field(default_factory=list)

    # 오류 유형별 분석
    cortex_errors_by_type: Dict[str, int] = field(default_factory=dict)
    baseline_errors_by_type: Dict[str, int] = field(default_factory=dict)

    # 도메인별 분석
    domain_analysis: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # 메타데이터
    total_tests: int = 0
    test_duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cortex_error_rate": self.cortex_error_rate,
            "baseline_error_rate": self.baseline_error_rate,
            "improvement_percentage": self.improvement_percentage,
            "p_value": self.p_value,
            "statistically_significant": self.statistically_significant,
            "total_tests": self.total_tests,
            "test_duration_seconds": self.test_duration_seconds,
            "cortex_errors_by_type": self.cortex_errors_by_type,
            "baseline_errors_by_type": self.baseline_errors_by_type,
            "domain_analysis": self.domain_analysis,
        }


class ABTestFramework:
    """
    A/B 테스트 프레임워크

    Cortex vs 경쟁사 RAG 비교

    목표:
    - 50% 이상 오류율 감소
    - p-value < 0.05 (통계적 유의미성)
    """

    TARGET_ERROR_REDUCTION = 0.50  # 50% 감소 목표
    SIGNIFICANCE_LEVEL = 0.05  # 유의수준

    def __init__(
        self,
        cortex_func: Callable[[TestCase], TestResult],
        baseline_func: Callable[[TestCase], TestResult],
    ):
        """
        A/B 테스트 프레임워크 초기화

        Args:
            cortex_func: Cortex를 사용한 테스트 실행 함수
            baseline_func: Baseline (경쟁사) RAG 테스트 실행 함수
        """
        self.cortex_func = cortex_func
        self.baseline_func = baseline_func

    def run_test(self, test_cases: List[TestCase]) -> ABTestResult:
        """
        A/B 테스트 실행

        Args:
            test_cases: 테스트 케이스 목록

        Returns:
            ABTestResult: 비교 결과
        """
        start_time = time.time()

        cortex_results = []
        baseline_results = []

        for case in test_cases:
            # Cortex 테스트
            try:
                cortex_result = self.cortex_func(case)
                cortex_results.append(cortex_result)
            except Exception as e:
                cortex_results.append(
                    TestResult(
                        test_case_id=case.id,
                        output=None,
                        latency_ms=0,
                        errors=[ErrorType.REASONING_ERROR],
                        metadata={"exception": str(e)},
                    )
                )

            # Baseline 테스트
            try:
                baseline_result = self.baseline_func(case)
                baseline_results.append(baseline_result)
            except Exception as e:
                baseline_results.append(
                    TestResult(
                        test_case_id=case.id,
                        output=None,
                        latency_ms=0,
                        errors=[ErrorType.REASONING_ERROR],
                        metadata={"exception": str(e)},
                    )
                )

        # 오류율 계산
        cortex_error_rate = self._calculate_error_rate(cortex_results)
        baseline_error_rate = self._calculate_error_rate(baseline_results)

        # 개선율 계산
        if baseline_error_rate > 0:
            improvement = (baseline_error_rate - cortex_error_rate) / baseline_error_rate
        else:
            improvement = 0.0 if cortex_error_rate == 0 else -1.0

        # 통계적 유의성 검정 (Z-test for proportions)
        p_value = self._calculate_p_value(
            cortex_results, baseline_results, cortex_error_rate, baseline_error_rate
        )

        # 오류 유형별 분석
        cortex_errors_by_type = self._analyze_errors_by_type(cortex_results)
        baseline_errors_by_type = self._analyze_errors_by_type(baseline_results)

        # 도메인별 분석
        domain_analysis = self._analyze_by_domain(test_cases, cortex_results, baseline_results)

        end_time = time.time()

        return ABTestResult(
            cortex_error_rate=cortex_error_rate,
            baseline_error_rate=baseline_error_rate,
            improvement_percentage=improvement,
            p_value=p_value,
            statistically_significant=p_value < self.SIGNIFICANCE_LEVEL,
            cortex_results=cortex_results,
            baseline_results=baseline_results,
            cortex_errors_by_type=cortex_errors_by_type,
            baseline_errors_by_type=baseline_errors_by_type,
            domain_analysis=domain_analysis,
            total_tests=len(test_cases),
            test_duration_seconds=end_time - start_time,
        )

    def _calculate_error_rate(self, results: List[TestResult]) -> float:
        """오류율 계산"""
        if not results:
            return 0.0

        error_count = sum(1 for r in results if r.errors)
        return error_count / len(results)

    def _calculate_p_value(
        self,
        cortex_results: List[TestResult],
        baseline_results: List[TestResult],
        cortex_error_rate: float,
        baseline_error_rate: float,
    ) -> float:
        """
        Two-proportion Z-test p-value 계산

        H0: p1 = p2 (오류율이 같다)
        H1: p1 < p2 (Cortex 오류율이 더 낮다)
        """
        n1 = len(cortex_results)
        n2 = len(baseline_results)

        if n1 == 0 or n2 == 0:
            return 1.0

        # Pooled proportion
        x1 = int(cortex_error_rate * n1)
        x2 = int(baseline_error_rate * n2)
        p_pooled = (x1 + x2) / (n1 + n2)

        if p_pooled == 0 or p_pooled == 1:
            return 1.0 if cortex_error_rate >= baseline_error_rate else 0.0

        # Standard error
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1 / n1 + 1 / n2))

        if se == 0:
            return 1.0 if cortex_error_rate >= baseline_error_rate else 0.0

        # Z-statistic
        z = (cortex_error_rate - baseline_error_rate) / se

        # p-value (one-tailed, lower)
        # Using normal approximation
        p_value = 0.5 * (1 + math.erf(z / math.sqrt(2)))

        return p_value

    def _analyze_errors_by_type(self, results: List[TestResult]) -> Dict[str, int]:
        """오류 유형별 분석"""
        error_counts = {e.value: 0 for e in ErrorType}

        for result in results:
            for error in result.errors:
                error_counts[error.value] += 1

        return error_counts

    def _analyze_by_domain(
        self,
        test_cases: List[TestCase],
        cortex_results: List[TestResult],
        baseline_results: List[TestResult],
    ) -> Dict[str, Dict[str, float]]:
        """도메인별 분석"""
        domain_analysis = {}

        # 도메인별 그룹화
        for domain in TestDomain:
            domain_cases = [c for c in test_cases if c.domain == domain]
            if not domain_cases:
                continue

            domain_ids = {c.id for c in domain_cases}

            cortex_domain = [r for r in cortex_results if r.test_case_id in domain_ids]
            baseline_domain = [r for r in baseline_results if r.test_case_id in domain_ids]

            cortex_er = self._calculate_error_rate(cortex_domain)
            baseline_er = self._calculate_error_rate(baseline_domain)

            improvement = 0.0
            if baseline_er > 0:
                improvement = (baseline_er - cortex_er) / baseline_er

            domain_analysis[domain.value] = {
                "cortex_error_rate": cortex_er,
                "baseline_error_rate": baseline_er,
                "improvement": improvement,
                "test_count": len(domain_cases),
            }

        return domain_analysis

    def evaluate_context_quality(
        self, used_contexts: List[str], ground_truth: List[str]
    ) -> List[ErrorType]:
        """
        맥락 품질 평가

        Args:
            used_contexts: 실제 사용된 맥락 ID들
            ground_truth: 정답 맥락 ID들

        Returns:
            발생한 오류 유형 목록
        """
        errors = []
        used_set = set(used_contexts)
        truth_set = set(ground_truth)

        # 맥락 누락 검사
        missing = truth_set - used_set
        if missing:
            errors.append(ErrorType.CONTEXT_MISSING)

        # 맥락 오염 검사 (불필요한 맥락 사용)
        pollution = used_set - truth_set
        if len(pollution) > len(used_set) * 0.3:  # 30% 이상이 불필요하면 오염
            errors.append(ErrorType.CONTEXT_POLLUTION)

        return errors

    @staticmethod
    def generate_test_report(result: ABTestResult) -> str:
        """테스트 리포트 생성"""
        lines = [
            "=" * 60,
            "A/B Test Report: Cortex vs Baseline RAG",
            "=" * 60,
            "",
            "Summary:",
            f"  Total Tests: {result.total_tests}",
            f"  Duration: {result.test_duration_seconds:.2f}s",
            "",
            "Error Rates:",
            f"  Cortex:   {result.cortex_error_rate * 100:.1f}%",
            f"  Baseline: {result.baseline_error_rate * 100:.1f}%",
            "",
            f"Improvement: {result.improvement_percentage * 100:+.1f}%",
            f"P-value: {result.p_value:.4f}",
            f"Statistically Significant: {'Yes' if result.statistically_significant else 'No'}",
            "",
            "-" * 60,
            "Error Type Analysis:",
            "",
            "Cortex:",
        ]

        for error_type, count in result.cortex_errors_by_type.items():
            lines.append(f"  {error_type}: {count}")

        lines.append("")
        lines.append("Baseline:")
        for error_type, count in result.baseline_errors_by_type.items():
            lines.append(f"  {error_type}: {count}")

        lines.append("")
        lines.append("-" * 60)
        lines.append("Domain Analysis:")

        for domain, analysis in result.domain_analysis.items():
            lines.append(f"\n{domain}:")
            lines.append(f"  Tests: {analysis['test_count']}")
            lines.append(f"  Cortex Error Rate: {analysis['cortex_error_rate'] * 100:.1f}%")
            lines.append(f"  Baseline Error Rate: {analysis['baseline_error_rate'] * 100:.1f}%")
            lines.append(f"  Improvement: {analysis['improvement'] * 100:+.1f}%")

        lines.append("")
        lines.append("=" * 60)

        # 목표 달성 여부
        target_met = result.improvement_percentage >= ABTestFramework.TARGET_ERROR_REDUCTION
        lines.append(f"\nTarget (50% reduction): {'ACHIEVED' if target_met else 'NOT ACHIEVED'}")
        lines.append("=" * 60)

        return "\n".join(lines)


def create_mock_cortex_test(case: TestCase) -> TestResult:
    """Cortex 모의 테스트 함수 (예시)"""
    # 실제 구현 시 Cortex RAG 호출
    start = time.perf_counter()

    # 시뮬레이션
    errors = []
    if "error" in case.query.lower():
        errors.append(ErrorType.REASONING_ERROR)

    latency = (time.perf_counter() - start) * 1000

    return TestResult(
        test_case_id=case.id,
        output="Cortex result",
        latency_ms=latency,
        contexts_used=case.ground_truth_contexts,
        errors=errors,
        score=1.0 if not errors else 0.0,
    )


def create_mock_baseline_test(case: TestCase) -> TestResult:
    """Baseline 모의 테스트 함수 (예시)"""
    # 실제 구현 시 경쟁사 RAG 호출
    start = time.perf_counter()

    # 시뮬레이션 - baseline은 더 많은 오류 발생
    errors = []
    if "error" in case.query.lower():
        errors.append(ErrorType.REASONING_ERROR)
    if "complex" in case.query.lower():
        errors.append(ErrorType.CONTEXT_MISSING)

    latency = (time.perf_counter() - start) * 1000

    return TestResult(
        test_case_id=case.id,
        output="Baseline result",
        latency_ms=latency,
        contexts_used=case.ground_truth_contexts[:1] if case.ground_truth_contexts else [],
        errors=errors,
        score=1.0 if not errors else 0.0,
    )
