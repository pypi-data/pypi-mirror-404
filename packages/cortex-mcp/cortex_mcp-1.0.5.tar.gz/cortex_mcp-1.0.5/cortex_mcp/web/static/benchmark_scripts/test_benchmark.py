"""
벤치마크 시스템 테스트 (v3.0)

테스트 항목:
1. Latency 측정 기능
2. Recall@K 벤치마크
3. 분류 정확도 벤치마크
4. A/B 테스트 프레임워크
5. KPI 추적기
"""

import sys
import time
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.benchmark.ab_test_framework import (
    ABTestFramework,
    ErrorType,
    TestCase,
    TestDomain,
    TestResult,
    create_mock_baseline_test,
    create_mock_cortex_test,
)
from tests.benchmark.benchmark_runner import BenchmarkRunner, LatencyStats
from tests.benchmark.kpi_tracker import KPITracker, get_kpi_tracker, reset_kpi_tracker


class TestBenchmarkRunner:
    """벤치마크 러너 테스트"""

    def test_latency_measurement(self):
        """Latency 측정 테스트"""
        runner = BenchmarkRunner(warmup_runs=1)

        # 테스트 함수 (약 10ms 대기)
        def slow_func():
            time.sleep(0.01)
            return True

        stats = runner.measure_latency(slow_func, iterations=5)

        # 검증
        assert stats.samples == 5
        assert stats.min_latency >= 9.0  # 최소 9ms
        assert stats.max_latency <= 20.0  # 최대 20ms
        assert stats.avg_latency >= 9.0

        print(f"\n[TEST] Latency 측정:")
        print(f"  - P50: {stats.p50:.2f}ms")
        print(f"  - P95: {stats.p95:.2f}ms")
        print(f"  - Avg: {stats.avg_latency:.2f}ms")
        print(f"  - Samples: {stats.samples}")

    def test_recall_benchmark(self):
        """Recall@K 벤치마크 테스트"""
        runner = BenchmarkRunner()

        # 모의 검색 함수
        def mock_search(query, top_k=10):
            # 간단한 키워드 매칭 시뮬레이션
            results = []
            if "인증" in query:
                results = [{"doc_id": "auth_1"}, {"doc_id": "auth_2"}]
            elif "데이터베이스" in query:
                results = [{"doc_id": "db_1"}, {"doc_id": "db_2"}]
            return results

        # 테스트 케이스
        test_cases = [
            {"query": "인증 시스템", "expected_ids": ["auth_1", "auth_2"]},
            {"query": "데이터베이스 최적화", "expected_ids": ["db_1"]},
        ]

        result = runner.benchmark_recall_at_k(search_func=mock_search, test_cases=test_cases, k=10)

        # 검증
        assert result.recall_at_k is not None
        assert 0.0 <= result.recall_at_k <= 1.0

        print(f"\n[TEST] Recall@K 벤치마크:")
        print(f"  - Recall@10: {result.recall_at_k * 100:.1f}%")
        print(f"  - Precision@10: {result.precision_at_k * 100:.1f}%")
        print(f"  - Passed: {result.passed}")

    def test_accuracy_benchmark(self):
        """분류 정확도 벤치마크 테스트"""
        runner = BenchmarkRunner()

        # 모의 분류 함수
        def mock_classify(text):
            if "React" in text or "프론트엔드" in text:
                return "frontend"
            elif "데이터베이스" in text or "SQL" in text:
                return "database"
            elif "인증" in text or "보안" in text:
                return "security"
            return "general"

        # 테스트 케이스
        test_cases = [
            {"text": "React 컴포넌트 개발", "expected_category": "frontend"},
            {"text": "SQL 쿼리 최적화", "expected_category": "database"},
            {"text": "JWT 인증 구현", "expected_category": "security"},
            {"text": "일반적인 텍스트", "expected_category": "general"},
        ]

        result = runner.benchmark_accuracy(classify_func=mock_classify, test_cases=test_cases)

        # 검증
        assert result.accuracy is not None
        assert result.accuracy == 1.0  # 모의 함수는 100% 정확

        print(f"\n[TEST] 분류 정확도 벤치마크:")
        print(f"  - Accuracy: {result.accuracy * 100:.1f}%")
        print(f"  - Target: {runner.TARGET_ACCURACY * 100:.0f}%")
        print(f"  - Passed: {result.passed}")

    def test_token_savings_benchmark(self):
        """토큰 절감율 벤치마크 테스트"""
        runner = BenchmarkRunner()

        # 예시: 1000 토큰 -> 300 토큰 (70% 절감)
        result = runner.benchmark_token_savings(original_tokens=1000, compressed_tokens=300)

        # 검증
        assert result.token_savings is not None
        assert result.token_savings == 0.7  # 70% 절감
        assert result.passed is True  # 목표 달성

        print(f"\n[TEST] 토큰 절감율 벤치마크:")
        print(f"  - Savings: {result.token_savings * 100:.1f}%")
        print(f"  - Target: {runner.TARGET_TOKEN_SAVINGS * 100:.0f}%")
        print(f"  - Passed: {result.passed}")

    def test_benchmark_report(self):
        """벤치마크 리포트 테스트"""
        runner = BenchmarkRunner()

        # 여러 벤치마크 실행
        runner.benchmark_token_savings(1000, 300)
        runner.benchmark_token_savings(500, 200)

        summary = runner.get_summary()

        # 검증
        assert summary["total_benchmarks"] == 2
        assert "results" in summary

        print(f"\n[TEST] 벤치마크 리포트:")
        print(f"  - Total: {summary['total_benchmarks']}")
        print(f"  - Passed: {summary['passed']}")
        print(f"  - Pass Rate: {summary['pass_rate'] * 100:.1f}%")


class TestABTestFramework:
    """A/B 테스트 프레임워크 테스트"""

    def test_ab_test_execution(self):
        """A/B 테스트 실행 테스트"""
        framework = ABTestFramework(
            cortex_func=create_mock_cortex_test, baseline_func=create_mock_baseline_test
        )

        # 테스트 케이스 생성
        test_cases = [
            TestCase(
                id="test_1",
                domain=TestDomain.CODING,
                query="함수 구현",
                expected_output="code",
                ground_truth_contexts=["ctx_1", "ctx_2"],
            ),
            TestCase(
                id="test_2",
                domain=TestDomain.CODING,
                query="complex error 처리",  # error + complex로 baseline에 더 많은 오류 유발
                expected_output="code",
                ground_truth_contexts=["ctx_3"],
            ),
            TestCase(
                id="test_3",
                domain=TestDomain.DOCUMENT,
                query="문서 검색",
                expected_output="document",
                ground_truth_contexts=["ctx_4"],
            ),
        ]

        result = framework.run_test(test_cases)

        # 검증
        assert result.total_tests == 3
        assert 0.0 <= result.cortex_error_rate <= 1.0
        assert 0.0 <= result.baseline_error_rate <= 1.0

        print(f"\n[TEST] A/B 테스트 결과:")
        print(f"  - Cortex Error Rate: {result.cortex_error_rate * 100:.1f}%")
        print(f"  - Baseline Error Rate: {result.baseline_error_rate * 100:.1f}%")
        print(f"  - Improvement: {result.improvement_percentage * 100:+.1f}%")
        print(f"  - P-value: {result.p_value:.4f}")
        print(f"  - Significant: {result.statistically_significant}")

    def test_context_quality_evaluation(self):
        """맥락 품질 평가 테스트"""
        framework = ABTestFramework(
            cortex_func=create_mock_cortex_test, baseline_func=create_mock_baseline_test
        )

        # 완벽한 맥락 사용
        errors1 = framework.evaluate_context_quality(
            used_contexts=["ctx_1", "ctx_2"], ground_truth=["ctx_1", "ctx_2"]
        )
        assert len(errors1) == 0

        # 맥락 누락
        errors2 = framework.evaluate_context_quality(
            used_contexts=["ctx_1"], ground_truth=["ctx_1", "ctx_2", "ctx_3"]
        )
        assert ErrorType.CONTEXT_MISSING in errors2

        # 맥락 오염 (50% 이상 불필요)
        errors3 = framework.evaluate_context_quality(
            used_contexts=["ctx_1", "unrelated_1", "unrelated_2"], ground_truth=["ctx_1"]
        )
        assert ErrorType.CONTEXT_POLLUTION in errors3

        print(f"\n[TEST] 맥락 품질 평가:")
        print(f"  - Perfect context: {len(errors1)} errors")
        print(f"  - Missing context: {[e.value for e in errors2]}")
        print(f"  - Polluted context: {[e.value for e in errors3]}")

    def test_ab_test_report(self):
        """A/B 테스트 리포트 생성 테스트"""
        framework = ABTestFramework(
            cortex_func=create_mock_cortex_test, baseline_func=create_mock_baseline_test
        )

        test_cases = [
            TestCase(
                id=f"test_{i}",
                domain=TestDomain.CODING,
                query=f"query {i} complex error" if i % 3 == 0 else f"query {i}",
                expected_output="result",
                ground_truth_contexts=[f"ctx_{i}"],
            )
            for i in range(10)
        ]

        result = framework.run_test(test_cases)
        report = ABTestFramework.generate_test_report(result)

        # 검증
        assert "A/B Test Report" in report
        assert "Error Rates" in report
        assert "Improvement" in report

        print(f"\n[TEST] A/B 테스트 리포트 생성 완료")
        print(f"  - Report length: {len(report)} chars")


class TestKPITracker:
    """KPI 추적기 테스트"""

    def setup(self):
        """테스트 셋업"""
        reset_kpi_tracker()

    def test_kpi_recording(self):
        """KPI 기록 테스트"""
        tracker = KPITracker(storage_path=Path("/tmp/cortex_kpi_test"))

        # KPI 기록
        measurement = tracker.record(
            kpi_name="context_recommendation_accuracy", value=0.96, metadata={"test": True}
        )

        # 검증
        assert measurement.kpi_name == "context_recommendation_accuracy"
        assert measurement.value == 0.96
        assert measurement.passed is True  # 0.96 >= 0.95 (목표)

        print(f"\n[TEST] KPI 기록:")
        print(f"  - KPI: {measurement.kpi_name}")
        print(f"  - Value: {measurement.value}")
        print(f"  - Passed: {measurement.passed}")

    def test_kpi_target_checking(self):
        """KPI 목표 확인 테스트"""
        tracker = KPITracker(storage_path=Path("/tmp/cortex_kpi_test"))

        # 목표 달성
        m1 = tracker.record("token_savings", 0.75)  # 75% >= 70%
        assert m1.passed is True

        # 목표 미달성
        m2 = tracker.record("token_savings", 0.50)  # 50% < 70%
        assert m2.passed is False

        # Latency 목표 (lte)
        m3 = tracker.record("p95_latency_ms", 45.0)  # 45ms <= 50ms
        assert m3.passed is True

        m4 = tracker.record("p95_latency_ms", 60.0)  # 60ms > 50ms
        assert m4.passed is False

        print(f"\n[TEST] KPI 목표 확인:")
        print(f"  - Token Savings 75%: {m1.passed}")
        print(f"  - Token Savings 50%: {m2.passed}")
        print(f"  - P95 Latency 45ms: {m3.passed}")
        print(f"  - P95 Latency 60ms: {m4.passed}")

    def test_kpi_history(self):
        """KPI 이력 테스트"""
        import shutil

        test_path = Path("/tmp/cortex_kpi_test_history")
        # 테스트 격리: 이전 데이터 정리
        if test_path.exists():
            shutil.rmtree(test_path)

        tracker = KPITracker(storage_path=test_path)

        # 여러 측정값 기록
        for i in range(5):
            tracker.record("rag_accuracy", 0.90 + i * 0.02)

        # 이력 조회
        history = tracker.get_history("rag_accuracy")
        assert len(history) == 5

        # 최신값 조회
        latest = tracker.get_latest("rag_accuracy")
        assert latest is not None
        assert latest.value == 0.98

        print(f"\n[TEST] KPI 이력:")
        print(f"  - History count: {len(history)}")
        print(f"  - Latest value: {latest.value}")

    def test_kpi_dashboard(self):
        """KPI 대시보드 테스트"""
        tracker = KPITracker(storage_path=Path("/tmp/cortex_kpi_test_dashboard"))

        # 여러 KPI 기록
        tracker.record("context_recommendation_accuracy", 0.96)
        tracker.record("token_savings", 0.72)
        tracker.record("p95_latency_ms", 48.0)

        # 대시보드 생성
        dashboard = tracker.get_dashboard()

        # 검증
        assert "kpis" in dashboard
        assert "summary" in dashboard
        assert dashboard["summary"]["met"] == 3

        print(f"\n[TEST] KPI 대시보드:")
        print(f"  - Total KPIs: {dashboard['summary']['total_kpis']}")
        print(f"  - Met: {dashboard['summary']['met']}")
        print(f"  - Not Met: {dashboard['summary']['not_met']}")
        print(f"  - No Data: {dashboard['summary']['no_data']}")


def run_tests():
    """테스트 실행"""
    print("=" * 60)
    print("벤치마크 시스템 테스트 시작")
    print("=" * 60)

    # 테스트 인스턴스
    benchmark_tests = TestBenchmarkRunner()
    ab_tests = TestABTestFramework()
    kpi_tests = TestKPITracker()

    tests_passed = 0
    tests_failed = 0

    # 벤치마크 러너 테스트
    runner_tests = [
        ("latency_measurement", benchmark_tests.test_latency_measurement),
        ("recall_benchmark", benchmark_tests.test_recall_benchmark),
        ("accuracy_benchmark", benchmark_tests.test_accuracy_benchmark),
        ("token_savings_benchmark", benchmark_tests.test_token_savings_benchmark),
        ("benchmark_report", benchmark_tests.test_benchmark_report),
    ]

    for name, test_func in runner_tests:
        try:
            test_func()
            print(f"[PASS] {name}")
            tests_passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            import traceback

            traceback.print_exc()
            tests_failed += 1

    # A/B 테스트 프레임워크 테스트
    ab_framework_tests = [
        ("ab_test_execution", ab_tests.test_ab_test_execution),
        ("context_quality_evaluation", ab_tests.test_context_quality_evaluation),
        ("ab_test_report", ab_tests.test_ab_test_report),
    ]

    for name, test_func in ab_framework_tests:
        try:
            test_func()
            print(f"[PASS] {name}")
            tests_passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            import traceback

            traceback.print_exc()
            tests_failed += 1

    # KPI 추적기 테스트
    kpi_tracker_tests = [
        ("kpi_recording", kpi_tests.test_kpi_recording),
        ("kpi_target_checking", kpi_tests.test_kpi_target_checking),
        ("kpi_history", kpi_tests.test_kpi_history),
        ("kpi_dashboard", kpi_tests.test_kpi_dashboard),
    ]

    for name, test_func in kpi_tracker_tests:
        try:
            kpi_tests.setup()
            test_func()
            print(f"[PASS] {name}")
            tests_passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            import traceback

            traceback.print_exc()
            tests_failed += 1

    print("\n" + "=" * 60)
    print(f"테스트 결과: {tests_passed}/{tests_passed + tests_failed} 통과")
    print("=" * 60)

    return tests_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
