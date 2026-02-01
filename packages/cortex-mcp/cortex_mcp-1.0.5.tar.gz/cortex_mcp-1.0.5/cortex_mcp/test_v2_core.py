"""
Phase 9.6 v2 핵심 기능 검증

테스트 결과 할루시네이션 문제가 해결되었는지 확인
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.fuzzy_claim_analyzer import FuzzyClaimAnalyzer
from core.claim_extractor import Claim

def test_factual_statement_detection():
    """테스트 결과가 사실 진술로 인식되는지 확인"""
    print("\n[TEST 1] Factual Statement Detection")
    print("=" * 60)

    analyzer = FuzzyClaimAnalyzer()

    # Case 1: 테스트 결과 (이전에 fail 했던 케이스)
    test_cases = [
        {
            "text": "테스트 결과: FAILURE",
            "context": "Phase 9 호환성 테스트를 실행했습니다. 테스트 결과: FAILURE. 3.66초가 걸렸습니다.",
            "expected": "factual_statement"
        },
        {
            "text": "Performance: 3.66s",
            "context": "벤치마크 실행 완료. Performance: 3.66s. 예상: 3.5s, 실제: 3.66s",
            "expected": "factual_statement"
        },
        {
            "text": "5개 테스트 중 3개 통과",
            "context": "테스트 실행 결과 5개 테스트 중 3개 통과, 2개 실패",
            "expected": "factual_statement"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        claim = Claim(
            text=case["text"],
            claim_type="verification",
            start=0,
            end=len(case["text"])
        )

        result = analyzer.analyze_claim(claim, case["context"])

        is_factual = result["is_factual_statement"]
        statement_type = result["statement_type"]

        print(f"\n  Case {i}: {case['text']}")
        print(f"    Is Factual: {is_factual}")
        print(f"    Type: {statement_type}")
        print(f"    Expected: {case['expected']}")

        if is_factual and statement_type in ["test_result", "measurement", "prediction_vs_actual"]:
            print(f"    ✅ PASS - Correctly identified as {statement_type}")
        else:
            print(f"    ❌ FAIL - Should be factual statement")
            return False

    return True


def test_claim_detection():
    """구현 주장이 claim으로 인식되는지 확인"""
    print("\n[TEST 2] Claim Detection (Not Factual)")
    print("=" * 60)

    analyzer = FuzzyClaimAnalyzer()

    # Case 2: 구현 완료 주장 (검증 필요)
    test_cases = [
        {
            "text": "버그를 수정했습니다",
            "context": "memory_manager.py의 버그를 수정했습니다. 이제 정상 작동합니다.",
            "expected": "implementation_claim"
        },
        {
            "text": "core/fuzzy_claim_analyzer.py:351에 파일 경로 패턴을 추가했습니다",
            "context": "core/fuzzy_claim_analyzer.py:351에 파일 경로 패턴을 추가했습니다.",
            "expected": "very_high"  # 파일 경로 있으면 very_high
        }
    ]

    for i, case in enumerate(test_cases, 1):
        claim = Claim(
            text=case["text"],
            claim_type="modification",
            start=0,
            end=len(case["text"])
        )

        result = analyzer.analyze_claim(claim, case["context"])

        is_factual = result["is_factual_statement"]
        confidence_level = result["confidence_level"]

        print(f"\n  Case {i}: {case['text']}")
        print(f"    Is Factual: {is_factual}")
        print(f"    Confidence: {confidence_level}")
        print(f"    Expected: {case['expected']}")

        if i == 1:
            # 첫번째는 claim (not factual)
            if not is_factual:
                print(f"    ✅ PASS - Correctly identified as claim")
            else:
                print(f"    ❌ FAIL - Should be claim, not factual")
                return False
        elif i == 2:
            # 두번째는 파일 경로 포함 → very_high
            if not is_factual and confidence_level == "very_high":
                print(f"    ✅ PASS - File path detected, very_high confidence")
            else:
                print(f"    ❌ FAIL - Should be very_high with file path")
                return False

    return True


def main():
    print("\n" + "=" * 60)
    print("Phase 9.6 v2 Core Functionality Test")
    print("=" * 60)

    # Test 1: Factual statement detection
    test1_pass = test_factual_statement_detection()

    # Test 2: Claim detection
    test2_pass = test_claim_detection()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  Factual Statement Detection: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"  Claim Detection:             {'✅ PASS' if test2_pass else '❌ FAIL'}")

    if test1_pass and test2_pass:
        print("\n✅ All core functionality tests passed!")
        print("v2 successfully distinguishes factual statements from claims.")
        return 0
    else:
        print("\n❌ Some tests failed. v2 needs more work.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
