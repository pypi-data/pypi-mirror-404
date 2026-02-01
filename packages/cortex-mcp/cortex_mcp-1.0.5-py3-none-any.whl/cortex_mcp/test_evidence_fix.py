"""
Evidence 인식 수정 검증 스크립트

이전에 0.00 Grounding Score를 받았던 verify_response 호출을 재현하여
수정 후 정상적으로 작동하는지 확인합니다.
"""

import sys
import tempfile
from core.auto_verifier import get_auto_verifier

def test_evidence_recognition():
    """최상위 test_results 키 인식 테스트"""

    verifier = get_auto_verifier()

    # 이전에 사용했던 응답
    response = """
Feature 1 E2E 테스트 작업을 완료했습니다.

완료된 작업:
1. E2E 테스트 5개 전부 통과 (100% 성공률)
2. Unit 테스트 20개 전부 통과 (100% 성공률)
3. 총 25개 테스트 통과
4. Git commit 생성: 29a2298aa88056036fad1e73879b515fc0c69244
5. MemoryManager API 시그니처 수정 완료
"""

    # 이전과 동일한 context 구조
    with tempfile.TemporaryDirectory() as tmpdir:
        context = {
            "project_id": "test_proj",
            "project_path": tmpdir,
            "test_results": "25 passed, 3 warnings in 2.5s",  # 최상위 키
            "file_contents": {
                "test_feature1_e2e.py": "# E2E test code",
                "test_auto_verifier.py": "# Unit test code"
            },
            "git_commit": "29a2298aa88056036fad1e73879b515fc0c69244"
        }

        # 검증 수행
        print("[검증 시작]")

        # DEBUG: 추출된 Claim 확인
        from core.claim_extractor import ClaimExtractor
        from core.fuzzy_claim_analyzer import FuzzyClaimAnalyzer

        extractor = ClaimExtractor()
        fuzzy_analyzer = FuzzyClaimAnalyzer()

        claims = extractor.extract_claims(response)
        analysis = fuzzy_analyzer.analyze_response(response)

        print(f"\n=== 확신도 분석 ===")
        print(f"Overall Confidence: {analysis['overall_confidence_level']}")
        print(f"Claim Analyses 개수: {len(analysis.get('claims', []))}")

        print(f"\n=== 추출된 Claim ===")
        for i, claim in enumerate(claims, 1):
            claim_analysis = analysis['claims'][i-1] if i-1 < len(analysis['claims']) else {}
            fuzzy_score = claim_analysis.get('fuzzy_score', 0.0)
            conf_level = claim_analysis.get('confidence_level', 'none')

            print(f"\n[Claim {i}]")
            print(f"  Type: {claim.claim_type}")
            print(f"  Fuzzy Score: {fuzzy_score}")
            print(f"  Confidence: {conf_level}")
            print(f"  Text: {claim.text[:100]}...")

            if fuzzy_score >= 0.8:
                print("  → HIGH 그룹")
            elif fuzzy_score >= 0.5:
                print("  → MEDIUM 그룹")
            else:
                print("  → LOW 그룹")

        result = verifier.verify_response(response, context)

        # 결과 출력
        print(f"\n=== 검증 결과 ===")
        print(f"Confidence Level: {result.confidence_level}")
        print(f"Grounding Score: {result.grounding_score:.2f}")
        print(f"Requires Retry: {result.requires_retry}")
        print(f"\nClaims 개수: {len(result.claims)}")
        print(f"Verified Claims 개수: {len(result.verified_claims)}")
        print(f"Pending Claims 개수: {len(result.pending_claims)}")

        # Evidence 확인
        print(f"\n=== Evidence 인식 여부 ===")
        for claim in result.verified_claims:
            print(f"\n[Verified Claim] {claim['text'][:50]}...")
            if 'evidence' in claim:
                for ev in claim['evidence']:
                    print(f"  - Evidence: {ev.get('type', 'unknown')} from {ev.get('source', 'unknown')}")

        # 판정
        if result.grounding_score >= 0.7:
            print("\n[PASS] Grounding Score >= 0.7 - Evidence 인식 성공!")
            return True
        elif result.grounding_score > 0.0:
            print(f"\n[PARTIAL] Grounding Score {result.grounding_score:.2f} - 일부 개선됨")
            return False
        else:
            print("\n[FAIL] Grounding Score 0.00 - 여전히 Evidence 인식 실패")
            return False

if __name__ == "__main__":
    success = test_evidence_recognition()
    sys.exit(0 if success else 1)
