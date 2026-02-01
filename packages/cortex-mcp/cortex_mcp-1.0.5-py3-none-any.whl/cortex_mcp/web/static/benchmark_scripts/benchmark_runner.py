"""
벤치마크 러너 (v3.0)

Cortex MCP 성능 벤치마크 시스템

KPI 목표:
- P50 Latency: 20ms 이하 (10,000건 Vector DB)
- P95 Latency: 50ms 이하 (50,000건 Vector DB)
- P99 Latency: 100ms 이하 (100,000건 Vector DB)
- Recall@10: 95% 이상 (Needle in Haystack)
"""

import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class LatencyStats:
    """Latency 통계 결과"""

    p50: float
    p95: float
    p99: float
    min_latency: float
    max_latency: float
    avg_latency: float
    samples: int
    raw_data: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "p50_ms": self.p50,
            "p95_ms": self.p95,
            "p99_ms": self.p99,
            "min_ms": self.min_latency,
            "max_ms": self.max_latency,
            "avg_ms": self.avg_latency,
            "samples": self.samples,
        }


@dataclass
class BenchmarkResult:
    """벤치마크 결과"""

    name: str
    passed: bool
    latency_stats: Optional[LatencyStats] = None
    recall_at_k: Optional[float] = None
    precision_at_k: Optional[float] = None
    accuracy: Optional[float] = None
    error_rate: Optional[float] = None
    token_savings: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name, "passed": self.passed}
        if self.latency_stats:
            result["latency"] = self.latency_stats.to_dict()
        if self.recall_at_k is not None:
            result["recall_at_k"] = self.recall_at_k
        if self.precision_at_k is not None:
            result["precision_at_k"] = self.precision_at_k
        if self.accuracy is not None:
            result["accuracy"] = self.accuracy
        if self.error_rate is not None:
            result["error_rate"] = self.error_rate
        if self.token_savings is not None:
            result["token_savings_percent"] = self.token_savings
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class BenchmarkRunner:
    """
    Cortex MCP 벤치마크 러너

    KPI 목표:
    - P50 Latency: 20ms 이하
    - P95 Latency: 50ms 이하
    - P99 Latency: 100ms 이하
    - Recall@10: 95% 이상
    """

    # KPI 목표 상수
    TARGET_P50_LATENCY_MS = 20.0
    TARGET_P95_LATENCY_MS = 50.0
    TARGET_P99_LATENCY_MS = 100.0
    TARGET_RECALL_AT_10 = 0.95
    TARGET_ACCURACY = 0.95
    TARGET_TOKEN_SAVINGS = 0.70

    def __init__(self, warmup_runs: int = 3):
        """
        벤치마크 러너 초기화

        Args:
            warmup_runs: 워밍업 실행 횟수 (캐시/JIT 안정화용)
        """
        self.warmup_runs = warmup_runs
        self.results: List[BenchmarkResult] = []

    def measure_latency(
        self, func: Callable, iterations: int = 100, *args, **kwargs
    ) -> LatencyStats:
        """
        함수 실행 Latency 측정

        Args:
            func: 측정할 함수
            iterations: 반복 횟수
            *args, **kwargs: 함수에 전달할 인자

        Returns:
            LatencyStats: 통계 결과
        """
        # 워밍업
        for _ in range(self.warmup_runs):
            try:
                func(*args, **kwargs)
            except Exception:
                pass

        # 측정
        latencies = []
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                func(*args, **kwargs)
            except Exception:
                pass
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # ms 변환

        if not latencies:
            return LatencyStats(
                p50=0, p95=0, p99=0, min_latency=0, max_latency=0, avg_latency=0, samples=0
            )

        latencies.sort()
        return LatencyStats(
            p50=self._percentile(latencies, 50),
            p95=self._percentile(latencies, 95),
            p99=self._percentile(latencies, 99),
            min_latency=min(latencies),
            max_latency=max(latencies),
            avg_latency=statistics.mean(latencies),
            samples=len(latencies),
            raw_data=latencies,
        )

    def _percentile(self, data: List[float], percentile: int) -> float:
        """백분위수 계산"""
        if not data:
            return 0.0
        k = (len(data) - 1) * percentile / 100
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return data[f] + (data[c] - data[f]) * (k - f)

    def benchmark_rag_latency(
        self, search_func: Callable, queries: List[str], iterations_per_query: int = 10
    ) -> BenchmarkResult:
        """
        RAG 검색 Latency 벤치마크

        Args:
            search_func: 검색 함수 (query -> results)
            queries: 테스트 쿼리 목록
            iterations_per_query: 쿼리당 반복 횟수
        """
        all_latencies = []

        for query in queries:
            stats = self.measure_latency(search_func, iterations=iterations_per_query, query=query)
            all_latencies.extend(stats.raw_data)

        if not all_latencies:
            return BenchmarkResult(
                name="RAG Latency Benchmark",
                passed=False,
                metadata={"error": "No latency data collected"},
            )

        all_latencies.sort()
        final_stats = LatencyStats(
            p50=self._percentile(all_latencies, 50),
            p95=self._percentile(all_latencies, 95),
            p99=self._percentile(all_latencies, 99),
            min_latency=min(all_latencies),
            max_latency=max(all_latencies),
            avg_latency=statistics.mean(all_latencies),
            samples=len(all_latencies),
            raw_data=all_latencies,
        )

        # KPI 검증
        passed = (
            final_stats.p50 <= self.TARGET_P50_LATENCY_MS
            and final_stats.p95 <= self.TARGET_P95_LATENCY_MS
            and final_stats.p99 <= self.TARGET_P99_LATENCY_MS
        )

        result = BenchmarkResult(
            name="RAG Latency Benchmark",
            passed=passed,
            latency_stats=final_stats,
            metadata={
                "target_p50_ms": self.TARGET_P50_LATENCY_MS,
                "target_p95_ms": self.TARGET_P95_LATENCY_MS,
                "target_p99_ms": self.TARGET_P99_LATENCY_MS,
                "query_count": len(queries),
                "iterations_per_query": iterations_per_query,
            },
        )

        self.results.append(result)
        return result

    def benchmark_recall_at_k(
        self, search_func: Callable, test_cases: List[Dict[str, Any]], k: int = 10
    ) -> BenchmarkResult:
        """
        Recall@K 벤치마크 (Needle in Haystack)

        Args:
            search_func: 검색 함수 (query -> List[result_ids])
            test_cases: [{"query": str, "expected_ids": List[str]}]
            k: 상위 K개 결과만 평가

        Returns:
            BenchmarkResult
        """
        total_recall = 0.0
        total_precision = 0.0
        valid_cases = 0

        for case in test_cases:
            query = case.get("query", "")
            expected_ids = set(case.get("expected_ids", []))

            if not expected_ids:
                continue

            try:
                results = search_func(query=query, top_k=k)
                result_ids = set()

                # 결과에서 ID 추출 (다양한 형식 지원)
                if isinstance(results, list):
                    for r in results[:k]:
                        if isinstance(r, dict):
                            result_ids.add(r.get("id") or r.get("doc_id") or str(r))
                        elif hasattr(r, "doc_id"):
                            result_ids.add(r.doc_id)
                        else:
                            result_ids.add(str(r))
                elif hasattr(results, "results"):
                    for r in results.results[:k]:
                        if hasattr(r, "doc_id"):
                            result_ids.add(r.doc_id)
                        else:
                            result_ids.add(str(r))

                # Recall = TP / (TP + FN)
                true_positives = len(expected_ids & result_ids)
                recall = true_positives / len(expected_ids) if expected_ids else 0.0

                # Precision = TP / (TP + FP)
                precision = true_positives / len(result_ids) if result_ids else 0.0

                total_recall += recall
                total_precision += precision
                valid_cases += 1

            except Exception as e:
                print(f"[WARN] Recall test failed for query '{query}': {e}")

        if valid_cases == 0:
            return BenchmarkResult(
                name="Recall@K Benchmark", passed=False, metadata={"error": "No valid test cases"}
            )

        avg_recall = total_recall / valid_cases
        avg_precision = total_precision / valid_cases

        result = BenchmarkResult(
            name=f"Recall@{k} Benchmark",
            passed=avg_recall >= self.TARGET_RECALL_AT_10,
            recall_at_k=avg_recall,
            precision_at_k=avg_precision,
            metadata={"k": k, "target_recall": self.TARGET_RECALL_AT_10, "test_cases": valid_cases},
        )

        self.results.append(result)
        return result

    def benchmark_accuracy(
        self, classify_func: Callable, test_cases: List[Dict[str, Any]]
    ) -> BenchmarkResult:
        """
        분류 정확도 벤치마크

        Args:
            classify_func: 분류 함수 (text -> category)
            test_cases: [{"text": str, "expected_category": str}]
        """
        correct = 0
        total = 0

        for case in test_cases:
            text = case.get("text", "")
            expected = case.get("expected_category", "")

            try:
                result = classify_func(text)

                # 결과에서 카테고리 추출
                if isinstance(result, str):
                    predicted = result
                elif hasattr(result, "primary_category"):
                    predicted = result.primary_category
                elif isinstance(result, dict):
                    predicted = result.get("category") or result.get("primary_category")
                else:
                    predicted = str(result)

                if predicted == expected:
                    correct += 1
                total += 1

            except Exception as e:
                print(f"[WARN] Classification failed for '{text[:50]}': {e}")
                total += 1

        accuracy = correct / total if total > 0 else 0.0

        result = BenchmarkResult(
            name="Classification Accuracy Benchmark",
            passed=accuracy >= self.TARGET_ACCURACY,
            accuracy=accuracy,
            metadata={"target_accuracy": self.TARGET_ACCURACY, "correct": correct, "total": total},
        )

        self.results.append(result)
        return result

    def benchmark_token_savings(
        self, original_tokens: int, compressed_tokens: int
    ) -> BenchmarkResult:
        """
        토큰 절감율 벤치마크

        Args:
            original_tokens: 압축 전 토큰 수
            compressed_tokens: 압축 후 토큰 수
        """
        if original_tokens == 0:
            return BenchmarkResult(
                name="Token Savings Benchmark",
                passed=False,
                metadata={"error": "Original tokens is 0"},
            )

        savings = 1 - (compressed_tokens / original_tokens)

        result = BenchmarkResult(
            name="Token Savings Benchmark",
            passed=savings >= self.TARGET_TOKEN_SAVINGS,
            token_savings=savings,
            metadata={
                "target_savings": self.TARGET_TOKEN_SAVINGS,
                "original_tokens": original_tokens,
                "compressed_tokens": compressed_tokens,
            },
        )

        self.results.append(result)
        return result

    def get_summary(self) -> Dict[str, Any]:
        """전체 벤치마크 요약"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)

        return {
            "total_benchmarks": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "results": [r.to_dict() for r in self.results],
        }

    def save_report(self, filepath: Path) -> None:
        """벤치마크 리포트 저장"""
        report = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "summary": self.get_summary()}

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def print_report(self) -> None:
        """벤치마크 리포트 출력"""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("Cortex MCP Benchmark Report")
        print("=" * 60)
        print(f"\nTotal: {summary['total_benchmarks']} benchmarks")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Pass Rate: {summary['pass_rate'] * 100:.1f}%")

        print("\n" + "-" * 60)
        print("Detailed Results:")
        print("-" * 60)

        for result in self.results:
            status = "[PASS]" if result.passed else "[FAIL]"
            print(f"\n{status} {result.name}")

            if result.latency_stats:
                stats = result.latency_stats
                print(f"  P50: {stats.p50:.2f}ms | P95: {stats.p95:.2f}ms | P99: {stats.p99:.2f}ms")

            if result.recall_at_k is not None:
                print(f"  Recall@K: {result.recall_at_k * 100:.1f}%")

            if result.accuracy is not None:
                print(f"  Accuracy: {result.accuracy * 100:.1f}%")

            if result.token_savings is not None:
                print(f"  Token Savings: {result.token_savings * 100:.1f}%")

        print("\n" + "=" * 60)
