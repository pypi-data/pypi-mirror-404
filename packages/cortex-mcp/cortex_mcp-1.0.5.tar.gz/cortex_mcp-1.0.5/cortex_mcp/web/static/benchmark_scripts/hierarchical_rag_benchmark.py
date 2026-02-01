"""
Hierarchical RAG 레이턴시 벤치마크

목표:
- P50 Latency: 20ms 이하
- P95 Latency: 50ms 이하
- P99 Latency: 100ms 이하
- Recall@10: 95% 이상

비교:
- 기존 RAG vs Hierarchical RAG
- 현재 베이스라인: 평균 400ms, P95 319ms
"""

import json
import statistics
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.hierarchical_rag import HierarchicalRAGEngine, HierarchicalSearchResult


@dataclass
class BenchmarkMetrics:
    """벤치마크 측정 지표"""

    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    samples: int
    passed_p50: bool
    passed_p95: bool
    passed_p99: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "avg_ms": round(self.avg_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "samples": self.samples,
            "passed_p50": self.passed_p50,
            "passed_p95": self.passed_p95,
            "passed_p99": self.passed_p99,
        }


@dataclass
class RecallMetrics:
    """Recall 측정 지표"""

    recall_at_10: float
    precision_at_10: float
    true_positives: int
    false_positives: int
    false_negatives: int
    test_cases: int
    passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recall_at_10": round(self.recall_at_10, 4),
            "precision_at_10": round(self.precision_at_10, 4),
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "test_cases": self.test_cases,
            "passed": self.passed,
        }


class HierarchicalRAGBenchmark:
    """Hierarchical RAG 벤치마크 시스템"""

    # KPI 목표
    TARGET_P50_MS = 20.0
    TARGET_P95_MS = 50.0
    TARGET_P99_MS = 100.0
    TARGET_RECALL = 0.95

    def __init__(self, warmup_rounds: int = 3):
        """
        벤치마크 시스템 초기화

        Args:
            warmup_rounds: 워밍업 라운드 수 (캐시/JIT 안정화)
        """
        self.warmup_rounds = warmup_rounds
        self.temp_dir = tempfile.mkdtemp(prefix="hierarchical_rag_bench_")
        self.storage_path = Path(self.temp_dir)

        print(f"[INFO] 벤치마크 임시 디렉토리: {self.temp_dir}")

    def _percentile(self, data: List[float], percentile: int) -> float:
        """백분위수 계산"""
        if not data:
            return 0.0
        k = (len(data) - 1) * percentile / 100
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return data[f] + (data[c] - data[f]) * (k - f)

    def _generate_test_documents(
        self, count: int, content_size: int, project_id: str
    ) -> List[Tuple[str, Dict[str, str]]]:
        """
        테스트 문서 생성

        Args:
            count: 문서 개수
            content_size: 문서 크기 (대략적인 문자 수)
            project_id: 프로젝트 ID

        Returns:
            List[(content, metadata)]
        """
        documents = []

        base_content = (
            "이 문서는 Cortex MCP 시스템의 테스트 문서입니다. "
            "Hierarchical RAG 엔진의 성능을 측정하기 위한 벤치마크 데이터입니다. "
            "다양한 주제와 키워드를 포함하여 실제 사용 환경을 시뮬레이션합니다. "
        )

        topics = [
            "인증 시스템",
            "데이터베이스 설계",
            "API 엔드포인트",
            "프론트엔드 컴포넌트",
            "배포 파이프라인",
            "테스트 자동화",
            "성능 최적화",
            "보안 강화",
            "사용자 경험",
            "코드 리뷰",
        ]

        for i in range(count):
            topic = topics[i % len(topics)]
            content = f"[문서 {i+1}] {topic}: " + base_content * (content_size // len(base_content))

            # 일부 문서에 검색 대상 키워드 삽입
            if i % 10 == 0:
                content += f" [KEYWORD_{i}] 중요한 정보가 여기 있습니다."

            metadata = {
                "project_id": project_id,
                "branch_id": "main",
                "doc_type": "benchmark",
                "topic": topic,
                "index": str(i),
            }

            documents.append((content, metadata))

        return documents

    def benchmark_latency(
        self, doc_count: int = 100, doc_size: int = 1000, queries: int = 50
    ) -> BenchmarkMetrics:
        """
        Hierarchical RAG 레이턴시 벤치마크

        Args:
            doc_count: 인덱싱할 문서 수
            doc_size: 문서당 크기 (대략 문자 수)
            queries: 실행할 쿼리 수

        Returns:
            BenchmarkMetrics
        """
        print("\n" + "=" * 70)
        print(f"Hierarchical RAG Latency Benchmark")
        print("=" * 70)
        print(f"문서 수: {doc_count}, 문서 크기: ~{doc_size} chars, 쿼리 수: {queries}")

        # 엔진 초기화
        engine = HierarchicalRAGEngine(storage_path=self.storage_path)
        project_id = "bench_project_001"

        # 1. 테스트 문서 생성 및 인덱싱
        print("\n[1/4] 테스트 문서 생성 및 인덱싱...")
        documents = self._generate_test_documents(doc_count, doc_size, project_id)

        indexing_start = time.perf_counter()
        for i, (content, metadata) in enumerate(documents):
            engine.index_document(content=content, metadata=metadata, doc_id=f"doc_{i}")
            if (i + 1) % 20 == 0:
                print(f"  진행: {i+1}/{doc_count} 문서 인덱싱 완료")

        indexing_time = time.perf_counter() - indexing_start
        print(f"  인덱싱 완료: {indexing_time:.2f}초 (문서당 평균 {indexing_time/doc_count*1000:.1f}ms)")

        # 2. 워밍업
        print(f"\n[2/4] 워밍업 ({self.warmup_rounds}회)...")
        for i in range(self.warmup_rounds):
            engine.search(query="테스트 쿼리", project_id=project_id, final_top_k=10)
            print(f"  워밍업 라운드 {i+1}/{self.warmup_rounds} 완료")

        # 3. 레이턴시 측정
        print(f"\n[3/4] 레이턴시 측정 ({queries}회 검색)...")
        latencies = []

        test_queries = [
            "인증 시스템 구현 방법",
            "데이터베이스 스키마 설계",
            "API 엔드포인트 추가",
            "프론트엔드 컴포넌트 개발",
            "배포 파이프라인 설정",
            "테스트 자동화 전략",
            "성능 최적화 기법",
            "보안 강화 방안",
            "사용자 경험 개선",
            "코드 리뷰 가이드",
        ]

        for i in range(queries):
            query = test_queries[i % len(test_queries)] + f" {i}"

            start = time.perf_counter()
            result = engine.search(query=query, project_id=project_id, final_top_k=10)
            end = time.perf_counter()

            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

            if (i + 1) % 10 == 0:
                print(f"  진행: {i+1}/{queries} 쿼리 실행 (최근 레이턴시: {latency_ms:.2f}ms)")

        # 4. 통계 계산
        print("\n[4/4] 통계 계산...")
        latencies.sort()

        p50 = self._percentile(latencies, 50)
        p95 = self._percentile(latencies, 95)
        p99 = self._percentile(latencies, 99)
        avg = statistics.mean(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)

        metrics = BenchmarkMetrics(
            p50_ms=p50,
            p95_ms=p95,
            p99_ms=p99,
            avg_ms=avg,
            min_ms=min_lat,
            max_ms=max_lat,
            samples=len(latencies),
            passed_p50=p50 <= self.TARGET_P50_MS,
            passed_p95=p95 <= self.TARGET_P95_MS,
            passed_p99=p99 <= self.TARGET_P99_MS,
        )

        # 결과 출력
        print("\n" + "-" * 70)
        print("레이턴시 측정 결과:")
        print("-" * 70)
        print(f"  P50: {p50:.2f}ms {'[PASS]' if metrics.passed_p50 else '[FAIL]'} (목표: {self.TARGET_P50_MS}ms)")
        print(f"  P95: {p95:.2f}ms {'[PASS]' if metrics.passed_p95 else '[FAIL]'} (목표: {self.TARGET_P95_MS}ms)")
        print(f"  P99: {p99:.2f}ms {'[PASS]' if metrics.passed_p99 else '[FAIL]'} (목표: {self.TARGET_P99_MS}ms)")
        print(f"  평균: {avg:.2f}ms")
        print(f"  최소: {min_lat:.2f}ms")
        print(f"  최대: {max_lat:.2f}ms")
        print(f"  샘플: {len(latencies)}개")

        all_passed = metrics.passed_p50 and metrics.passed_p95 and metrics.passed_p99
        print(f"\n전체 결과: {'[PASS] 목표 달성' if all_passed else '[FAIL] 목표 미달성'}")
        print("=" * 70)

        return metrics

    def benchmark_recall(self, doc_count: int = 100, test_cases: int = 20) -> RecallMetrics:
        """
        Hierarchical RAG Recall@10 벤치마크

        Args:
            doc_count: 인덱싱할 문서 수
            test_cases: 테스트 케이스 수

        Returns:
            RecallMetrics
        """
        print("\n" + "=" * 70)
        print(f"Hierarchical RAG Recall@10 Benchmark")
        print("=" * 70)
        print(f"문서 수: {doc_count}, 테스트 케이스: {test_cases}")

        # 엔진 초기화
        engine = HierarchicalRAGEngine(storage_path=self.storage_path)
        project_id = "bench_recall_001"

        # 1. 테스트 문서 생성 (키워드가 포함된 문서)
        print("\n[1/3] 테스트 문서 생성 및 인덱싱...")
        documents = []

        for i in range(doc_count):
            topic = f"주제_{i % 10}"
            content = f"이것은 {topic}에 대한 문서입니다. "

            # 특정 문서에 고유 키워드 삽입
            if i % 5 == 0:
                keyword = f"KEYWORD_{i}"
                content += f"중요: {keyword} 정보가 여기 있습니다. 이것은 검색 대상입니다."

            metadata = {"project_id": project_id, "branch_id": "main", "index": str(i)}

            result = engine.index_document(content=content, metadata=metadata, doc_id=f"recall_doc_{i}")

            if (i + 1) % 20 == 0:
                print(f"  진행: {i+1}/{doc_count} 문서 인덱싱 완료")

        # 2. Recall 테스트 케이스 생성
        print("\n[2/3] Recall 테스트 실행...")
        test_queries = []

        for i in range(test_cases):
            idx = i * 5  # KEYWORD_{0}, KEYWORD_{5}, KEYWORD_{10}, ...
            if idx < doc_count:
                test_queries.append(
                    {
                        "query": f"KEYWORD_{idx} 정보 찾기",
                        "expected_doc_id": f"recall_doc_{idx}",
                        "keyword": f"KEYWORD_{idx}",
                    }
                )

        total_tp = 0
        total_fp = 0
        total_fn = 0

        for i, test_case in enumerate(test_queries):
            result = engine.search(query=test_case["query"], project_id=project_id, final_top_k=10)

            # 결과에서 doc_id 추출
            found_doc_ids = [r.doc_id for r in result.results[:10]]

            # True Positive 확인
            if test_case["expected_doc_id"] in found_doc_ids:
                total_tp += 1
            else:
                total_fn += 1

            if (i + 1) % 5 == 0:
                print(f"  진행: {i+1}/{len(test_queries)} 케이스 테스트 완료")

        # 3. 메트릭 계산
        print("\n[3/3] 메트릭 계산...")

        # Recall = TP / (TP + FN)
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0

        # Precision = TP / (TP + FP) - 이 경우 top-10에서 정답이 1개이므로 simplified
        # 실제로는 top-10 중 관련 문서 개수를 세어야 하지만, 단순화
        precision = total_tp / len(test_queries) if len(test_queries) > 0 else 0.0

        metrics = RecallMetrics(
            recall_at_10=recall,
            precision_at_10=precision,
            true_positives=total_tp,
            false_positives=total_fp,
            false_negatives=total_fn,
            test_cases=len(test_queries),
            passed=recall >= self.TARGET_RECALL,
        )

        # 결과 출력
        print("\n" + "-" * 70)
        print("Recall 측정 결과:")
        print("-" * 70)
        print(f"  Recall@10: {recall:.2%} {'[PASS]' if metrics.passed else '[FAIL]'} (목표: {self.TARGET_RECALL:.0%})")
        print(f"  Precision@10: {precision:.2%}")
        print(f"  True Positives: {total_tp}")
        print(f"  False Negatives: {total_fn}")
        print(f"  테스트 케이스: {len(test_queries)}")

        print(f"\n전체 결과: {'[PASS] 목표 달성' if metrics.passed else '[FAIL] 목표 미달성'}")
        print("=" * 70)

        return metrics

    def run_full_benchmark(self) -> Dict[str, Any]:
        """
        전체 벤치마크 실행

        Returns:
            Dict: 벤치마크 결과 리포트
        """
        print("\n" + "=" * 70)
        print("Hierarchical RAG 전체 벤치마크 시작")
        print("=" * 70)

        start_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # 1. 레이턴시 벤치마크 (다양한 규모)
        latency_results = {}

        print("\n\n[벤치마크 1/3] 소규모 (100 documents)")
        latency_results["small"] = self.benchmark_latency(doc_count=100, doc_size=1000, queries=50)

        print("\n\n[벤치마크 2/3] 중규모 (500 documents)")
        latency_results["medium"] = self.benchmark_latency(doc_count=500, doc_size=1000, queries=50)

        # 대규모는 시간이 오래 걸리므로 생략 (필요시 주석 해제)
        # print("\n\n[벤치마크 3/4] 대규모 (1000 documents)")
        # latency_results["large"] = self.benchmark_latency(doc_count=1000, doc_size=1000, queries=50)

        # 2. Recall 벤치마크
        print("\n\n[벤치마크 3/3] Recall@10 테스트")
        recall_result = self.benchmark_recall(doc_count=100, test_cases=20)

        end_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # 최종 리포트 생성
        report = {
            "benchmark_info": {
                "start_time": start_time,
                "end_time": end_time,
                "storage_path": str(self.storage_path),
            },
            "targets": {
                "p50_ms": self.TARGET_P50_MS,
                "p95_ms": self.TARGET_P95_MS,
                "p99_ms": self.TARGET_P99_MS,
                "recall_at_10": self.TARGET_RECALL,
            },
            "latency_benchmarks": {
                scale: metrics.to_dict() for scale, metrics in latency_results.items()
            },
            "recall_benchmark": recall_result.to_dict(),
            "overall_status": self._calculate_overall_status(latency_results, recall_result),
        }

        # 최종 요약 출력
        self._print_final_summary(report)

        return report

    def _calculate_overall_status(
        self, latency_results: Dict[str, BenchmarkMetrics], recall_result: RecallMetrics
    ) -> Dict[str, Any]:
        """전체 벤치마크 통과 여부 계산"""
        latency_passed = all(
            m.passed_p50 and m.passed_p95 and m.passed_p99 for m in latency_results.values()
        )
        recall_passed = recall_result.passed

        return {
            "latency_passed": latency_passed,
            "recall_passed": recall_passed,
            "all_passed": latency_passed and recall_passed,
        }

    def _print_final_summary(self, report: Dict[str, Any]):
        """최종 요약 출력"""
        print("\n\n" + "=" * 70)
        print("최종 벤치마크 요약")
        print("=" * 70)

        print("\n[레이턴시 벤치마크 결과]")
        for scale, metrics in report["latency_benchmarks"].items():
            passed = metrics["passed_p50"] and metrics["passed_p95"] and metrics["passed_p99"]
            status = "[PASS]" if passed else "[FAIL]"
            print(
                f"  {scale.upper():10} - P50: {metrics['p50_ms']:6.2f}ms, "
                f"P95: {metrics['p95_ms']:6.2f}ms, P99: {metrics['p99_ms']:6.2f}ms {status}"
            )

        print("\n[Recall 벤치마크 결과]")
        recall = report["recall_benchmark"]
        status = "[PASS]" if recall["passed"] else "[FAIL]"
        print(f"  Recall@10: {recall['recall_at_10']:.2%} {status}")

        overall = report["overall_status"]
        print(
            f"\n최종 결과: {'[PASS] 모든 벤치마크 통과' if overall['all_passed'] else '[FAIL] 일부 벤치마크 실패'}"
        )
        print("=" * 70)

    def save_report(self, report: Dict[str, Any], output_path: Optional[Path] = None):
        """벤치마크 리포트 저장"""
        if output_path is None:
            output_path = Path(__file__).parent / "reports" / f"hierarchical_rag_bench_{int(time.time())}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n리포트 저장 완료: {output_path}")


def main():
    """벤치마크 메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="Hierarchical RAG Benchmark")
    parser.add_argument("--latency", action="store_true", help="레이턴시 벤치마크만 실행")
    parser.add_argument("--recall", action="store_true", help="Recall 벤치마크만 실행")
    parser.add_argument("--full", action="store_true", help="전체 벤치마크 실행 (기본값)")
    parser.add_argument("--output", type=str, help="리포트 출력 경로")

    args = parser.parse_args()

    benchmark = HierarchicalRAGBenchmark(warmup_rounds=3)

    if args.latency:
        metrics = benchmark.benchmark_latency(doc_count=100, doc_size=1000, queries=50)
        report = {"latency": metrics.to_dict()}
    elif args.recall:
        metrics = benchmark.benchmark_recall(doc_count=100, test_cases=20)
        report = {"recall": metrics.to_dict()}
    else:
        # 기본: 전체 벤치마크
        report = benchmark.run_full_benchmark()

    # 리포트 저장
    output_path = Path(args.output) if args.output else None
    benchmark.save_report(report, output_path)


if __name__ == "__main__":
    main()
