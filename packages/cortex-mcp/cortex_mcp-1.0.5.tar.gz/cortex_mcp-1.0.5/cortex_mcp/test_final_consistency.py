"""
최종 grounding_score 일관성 검증

모든 경로에서 Claim 없을 때 grounding_score = 1.0 검증
"""

from pathlib import Path
from core.auto_verifier import AutoVerifier


def test_no_claims_high_confidence():
    """Claim 없음 + 확신도 높음"""
    print("\n[TEST 1] Claim 없음 + 확신도 높음")

    verifier = AutoVerifier()
    content = "이 프로젝트는 확실히 Python Flask 기반입니다."

    result = verifier.verify_response(
        response_text=content,
        context={"project_id": "test", "project_path": str(Path.cwd())}
    )

    print(f"  Grounding Score: {result.grounding_score}")
    print(f"  Expected: 1.0 (Claim 없음)")
    assert result.grounding_score == 1.0
    print("  ✅ PASS")


def test_no_claims_low_confidence():
    """Claim 없음 + 확신도 낮음"""
    print("\n[TEST 2] Claim 없음 + 확신도 낮음")

    verifier = AutoVerifier()
    content = "이 프로젝트는 아마도 Python일 것 같아요."

    result = verifier.verify_response(
        response_text=content,
        context={"project_id": "test", "project_path": str(Path.cwd())}
    )

    print(f"  Grounding Score: {result.grounding_score}")
    print(f"  Expected: 1.0 (Claim 없음, 확신도 무관)")
    assert result.grounding_score == 1.0
    print("  ✅ PASS")


def test_with_claims_low_confidence():
    """Claim 있음 + 확신도 낮음"""
    print("\n[TEST 3] Claim 있음 + 확신도 낮음")

    verifier = AutoVerifier()
    content = "함수 add()를 아마도 구현한 것 같아요."

    result = verifier.verify_response(
        response_text=content,
        context={"project_id": "test", "project_path": str(Path.cwd())}
    )

    print(f"  Grounding Score: {result.grounding_score}")
    print(f"  Confidence Level: {result.confidence_level}")
    print(f"  Claims Count: {len(result.claims)}")
    print(f"  Expected: 0.5 (Claim 있음 + 확신도 낮음)")

    # DEBUG: 실제 반환값 확인
    print(f"  DEBUG - result.verified: {result.verified}")
    print(f"  DEBUG - result.claims: {result.claims}")

    assert result.grounding_score == 0.5, f"Expected 0.5, got {result.grounding_score}"
    print("  ✅ PASS")


if __name__ == "__main__":
    print("="*60)
    print("최종 Grounding Score 일관성 검증")
    print("="*60)

    test_no_claims_high_confidence()
    test_no_claims_low_confidence()
    test_with_claims_low_confidence()

    print("\n" + "="*60)
    print("전체 테스트 통과! 일관성 확보 완료!")
    print("="*60)
