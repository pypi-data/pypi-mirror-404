"""
Comprehensive Performance Test - update_memory 성능 개선 검증

테스트 목표:
1. 17초 → 2초 성능 개선 검증
2. 백그라운드 처리 정상 작동 확인
3. 다양한 텍스트 크기별 성능 측정
4. P1 비활성화 효과 확인
5. RAG 백그라운드 인덱싱 확인

Ultrathink Mode:
- 세계 최고 성능 테스트 전문가 관점
- 4가지 텍스트 크기 시나리오
- 각 3회 반복 측정
- 통계 분석 (평균, 최소, 최대, 표준편차)
- 로그 분석 포함
"""

import sys
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory_manager import MemoryManager
from config import config, get_cortex_path

# 실제 프로젝트 정보
PROJECT_ID = "4d8e58aea4b0"
BRANCH_ID = "update_memory_성능_근본_개선_17초to2초_20260104_06493552000"


class PerformanceTest:
    """성능 테스트 클래스"""

    def __init__(self):
        self.mm = MemoryManager(project_id=PROJECT_ID)
        self.results: List[Dict[str, Any]] = []

    def generate_text(self, size: int) -> str:
        """테스트용 텍스트 생성"""
        base_text = """
성능 테스트 진행 중입니다.
이 텍스트는 update_memory 성능을 측정하기 위한 것입니다.
다양한 크기의 텍스트로 테스트하여 일관된 성능을 확인합니다.
백그라운드 처리가 제대로 작동하는지 확인합니다.
"""
        # 목표 크기까지 반복
        repetitions = (size // len(base_text)) + 1
        return (base_text * repetitions)[:size]

    def run_single_test(
        self, test_name: str, text_size: int, iteration: int
    ) -> Dict[str, Any]:
        """단일 테스트 실행"""
        content = self.generate_text(text_size)

        print(f"\n[{test_name}] Iteration {iteration + 1}/3 - {text_size}자")

        start = time.perf_counter()
        result = self.mm.update_memory(
            project_id=PROJECT_ID,
            branch_id=BRANCH_ID,
            content=content,
            role="assistant",
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "test_name": test_name,
            "text_size": text_size,
            "iteration": iteration + 1,
            "elapsed_ms": elapsed_ms,
            "success": result.get("success", False),
            "background_indexing": result.get("background_indexing_started", False),
            "summary_updated": result.get("summary_updated", False),
            "grounding_score": result.get("grounding_score", 0),
        }

    def run_test_scenario(self, test_name: str, text_size: int, iterations: int = 3):
        """테스트 시나리오 실행 (여러 번 반복)"""
        print(f"\n{'=' * 80}")
        print(f"테스트 시나리오: {test_name}")
        print(f"텍스트 크기: {text_size:,}자")
        print(f"반복 횟수: {iterations}회")
        print(f"{'=' * 80}")

        scenario_results = []

        for i in range(iterations):
            result = self.run_single_test(test_name, text_size, i)
            scenario_results.append(result)
            self.results.append(result)

            print(
                f"  결과: {result['elapsed_ms']:.1f}ms "
                f"(성공: {result['success']}, "
                f"백그라운드: {result['background_indexing']})"
            )

            # 각 테스트 사이 0.5초 대기 (시스템 안정화)
            time.sleep(0.5)

        # 시나리오 통계
        times = [r["elapsed_ms"] for r in scenario_results]
        avg = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        stdev = statistics.stdev(times) if len(times) > 1 else 0

        print(f"\n[{test_name}] 통계:")
        print(f"  평균: {avg:.1f}ms")
        print(f"  최소: {min_time:.1f}ms")
        print(f"  최대: {max_time:.1f}ms")
        print(f"  표준편차: {stdev:.1f}ms")

        return scenario_results

    def analyze_results(self):
        """전체 결과 분석"""
        print(f"\n\n{'=' * 80}")
        print("전체 결과 분석")
        print(f"{'=' * 80}")

        # 테스트별 그룹화
        by_test = {}
        for r in self.results:
            name = r["test_name"]
            if name not in by_test:
                by_test[name] = []
            by_test[name].append(r["elapsed_ms"])

        print(f"\n{'테스트 시나리오':<30} {'평균 (ms)':<15} {'최소 (ms)':<15} {'최대 (ms)':<15}")
        print("-" * 80)

        for name, times in by_test.items():
            avg = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            print(f"{name:<30} {avg:>10.1f}     {min_time:>10.1f}     {max_time:>10.1f}")

        # 전체 통계
        all_times = [r["elapsed_ms"] for r in self.results]
        overall_avg = statistics.mean(all_times)
        overall_min = min(all_times)
        overall_max = max(all_times)
        overall_stdev = statistics.stdev(all_times)

        print(f"\n{'=' * 80}")
        print("전체 통계:")
        print(f"  총 테스트 횟수: {len(self.results)}회")
        print(f"  평균 실행 시간: {overall_avg:.1f}ms")
        print(f"  최소 실행 시간: {overall_min:.1f}ms")
        print(f"  최대 실행 시간: {overall_max:.1f}ms")
        print(f"  표준편차: {overall_stdev:.1f}ms")

        # 성공률 확인
        success_count = sum(1 for r in self.results if r["success"])
        success_rate = (success_count / len(self.results)) * 100
        print(f"  성공률: {success_rate:.1f}% ({success_count}/{len(self.results)})")

        # 백그라운드 처리 확인
        bg_count = sum(1 for r in self.results if r["background_indexing"])
        bg_rate = (bg_count / len(self.results)) * 100
        print(
            f"  백그라운드 인덱싱 성공률: {bg_rate:.1f}% ({bg_count}/{len(self.results)})"
        )

        # 성능 목표 달성 여부
        print(f"\n{'=' * 80}")
        print("성능 목표 달성 여부:")
        print(f"{'=' * 80}")

        target_ms = 2000  # 2초
        if overall_avg <= target_ms:
            print(
                f"✅ 목표 달성! 평균 {overall_avg:.1f}ms (목표: {target_ms}ms 이하)"
            )
            improvement = ((17000 - overall_avg) / 17000) * 100
            print(f"✅ 성능 개선율: {improvement:.1f}% (17초 → {overall_avg/1000:.2f}초)")
        else:
            print(
                f"❌ 목표 미달성. 평균 {overall_avg:.1f}ms (목표: {target_ms}ms 이하)"
            )

        return {
            "overall_avg": overall_avg,
            "overall_min": overall_min,
            "overall_max": overall_max,
            "overall_stdev": overall_stdev,
            "success_rate": success_rate,
            "bg_rate": bg_rate,
            "target_achieved": overall_avg <= target_ms,
        }

    def check_logs(self):
        """로그 파일 확인"""
        print(f"\n\n{'=' * 80}")
        print("로그 분석 (최근 5개 update_memory 호출)")
        print(f"{'=' * 80}")

        log_file = get_cortex_path("logs", "tool_calls.log")
        if not log_file.exists():
            print("❌ 로그 파일을 찾을 수 없습니다.")
            return

        # 최근 5개 update_memory 로그 추출
        with open(log_file, "r") as f:
            lines = f.readlines()

        update_memory_logs = [
            line for line in lines if "update_memory" in line and "도구 호출 완료" in line
        ][-5:]

        if not update_memory_logs:
            print("update_memory 로그를 찾을 수 없습니다.")
            return

        print("\n최근 실행 기록:")
        for log in update_memory_logs:
            # 시간 추출 (예: "<<< 도구 호출 완료: update_memory (1234.5ms)")
            if "(" in log and "ms)" in log:
                time_str = log.split("(")[1].split("ms)")[0]
                print(f"  - {time_str}ms")


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 80)
    print("Cortex update_memory 성능 개선 검증 테스트")
    print("=" * 80)
    print("\n테스트 설계:")
    print("  - 4가지 텍스트 크기 (100, 1000, 5000, 10000자)")
    print("  - 각 시나리오당 3회 반복")
    print("  - 총 12회 테스트")
    print("  - 통계 분석 포함")
    print("  - 로그 분석 포함")
    print("\n목표: 평균 실행 시간 2초 이하 달성")
    print("기존: 평균 17.6초")
    print("=" * 80)

    tester = PerformanceTest()

    try:
        # 시나리오 1: 짧은 텍스트 (100자)
        tester.run_test_scenario("짧은 텍스트 (100자)", 100)

        # 시나리오 2: 중간 텍스트 (1000자)
        tester.run_test_scenario("중간 텍스트 (1,000자)", 1000)

        # 시나리오 3: 긴 텍스트 (5000자)
        tester.run_test_scenario("긴 텍스트 (5,000자)", 5000)

        # 시나리오 4: 매우 긴 텍스트 (10000자)
        tester.run_test_scenario("매우 긴 텍스트 (10,000자)", 10000)

        # 전체 결과 분석
        stats = tester.analyze_results()

        # 로그 분석
        tester.check_logs()

        # 최종 결과 출력
        print(f"\n\n{'=' * 80}")
        print("최종 결과")
        print(f"{'=' * 80}")

        if stats["target_achieved"]:
            print(
                f"\n✅✅✅ 성능 개선 목표 달성! ✅✅✅"
            )
            print(
                f"평균 실행 시간: {stats['overall_avg']:.1f}ms ({stats['overall_avg']/1000:.2f}초)"
            )
            print(f"성능 개선율: {((17000 - stats['overall_avg']) / 17000) * 100:.1f}%")
        else:
            print(f"\n❌ 성능 개선 목표 미달성")
            print(f"평균 실행 시간: {stats['overall_avg']:.1f}ms")

        print(f"\n백그라운드 인덱싱 성공률: {stats['bg_rate']:.1f}%")
        print(f"테스트 성공률: {stats['success_rate']:.1f}%")

    except KeyboardInterrupt:
        print("\n\n테스트 중단됨 (Ctrl+C)")
    except Exception as e:
        print(f"\n\n❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
