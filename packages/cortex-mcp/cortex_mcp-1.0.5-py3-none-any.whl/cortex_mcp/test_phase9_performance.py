"""
Phase 9 성능 벤치마크

대량 텍스트 처리 시 성능 병목 파악:
- 10KB, 50KB 텍스트 처리 시간 측정
- Claim 추출, 검증, Grounding Score 계산 각 단계별 시간 측정
"""

import time
from pathlib import Path

from core.auto_verifier import AutoVerifier


def generate_test_content(size_kb: int) -> str:
    """테스트용 콘텐츠 생성 (반복되는 구현 완료 주장)"""
    base_claim = """
    함수 add_numbers를 구현했습니다.
    이 함수는 두 숫자를 더하여 반환합니다.
    테스트 코드도 작성했습니다.
    """

    target_size = size_kb * 1024
    content = ""

    counter = 0
    while len(content.encode('utf-8')) < target_size:
        content += f"[구현 {counter}] " + base_claim + "\n"
        counter += 1

    return content


def benchmark_phase9(content_size_kb: int):
    """Phase 9 성능 벤치마크"""
    print(f"\n{'='*60}")
    print(f"Phase 9 Performance Benchmark: {content_size_kb}KB")
    print(f"{'='*60}")

    # 테스트 프로젝트 경로
    test_project_path = Path.cwd()

    # AutoVerifier 초기화
    print("\n[1/4] AutoVerifier 초기화...")
    start = time.time()
    verifier = AutoVerifier()
    init_time = time.time() - start
    print(f"      초기화 시간: {init_time:.2f}초")

    # 테스트 콘텐츠 생성
    print(f"\n[2/4] {content_size_kb}KB 테스트 콘텐츠 생성...")
    content = generate_test_content(content_size_kb)
    actual_size = len(content.encode('utf-8')) / 1024
    print(f"      실제 크기: {actual_size:.2f}KB")

    # Phase 9 검증 실행
    print(f"\n[3/4] Phase 9 검증 실행...")
    start = time.time()

    result = verifier.verify_response(
        response_text=content,
        context={
            "project_id": "test_perf",
            "project_path": str(test_project_path)
        }
    )

    verify_time = time.time() - start

    # 결과 출력 (VerificationResult는 dataclass이므로 속성 접근)
    print(f"\n[4/4] 결과 분석")
    print(f"      총 처리 시간: {verify_time:.2f}초")
    print(f"      추출된 Claim 수: {len(result.claims)}")
    print(f"      검증되지 않은 Claim 수: {len(result.unverified_claims)}")
    print(f"      Grounding Score: {result.grounding_score:.2f}")
    print(f"      초당 처리 속도: {actual_size / verify_time:.2f}KB/s")

    return {
        "size_kb": actual_size,
        "init_time": init_time,
        "verify_time": verify_time,
        "total_claims": len(result.claims),
        "unverified_claims": len(result.unverified_claims),
        "grounding_score": result.grounding_score,
        "throughput_kb_s": actual_size / verify_time
    }


def main():
    """벤치마크 실행"""
    sizes = [10, 50]  # KB 단위
    results = []

    for size in sizes:
        result = benchmark_phase9(size)
        results.append(result)

    # 요약 출력
    print(f"\n{'='*60}")
    print("성능 벤치마크 요약")
    print(f"{'='*60}")
    print(f"{'크기 (KB)':<15} {'처리 시간 (초)':<20} {'처리 속도 (KB/s)':<20}")
    print(f"{'-'*60}")

    for r in results:
        print(f"{r['size_kb']:<15.2f} {r['verify_time']:<20.2f} {r['throughput_kb_s']:<20.2f}")

    # 성능 분석
    print(f"\n{'='*60}")
    print("성능 분석")
    print(f"{'='*60}")

    if len(results) >= 2:
        small = results[0]
        large = results[1]

        size_ratio = large['size_kb'] / small['size_kb']
        time_ratio = large['verify_time'] / small['verify_time']

        print(f"크기 증가율: {size_ratio:.1f}x")
        print(f"시간 증가율: {time_ratio:.1f}x")

        if time_ratio > size_ratio * 1.5:
            print("\n⚠️  비선형 성능 저하 감지!")
            print("   → O(n^2) 이상의 복잡도 의심")
            print("   → 배치 처리 최적화 필요")
        else:
            print("\n✅ 선형에 가까운 성능")


if __name__ == "__main__":
    main()
