#!/usr/bin/env python3
"""
Phase 9 수정사항 할루시네이션 검증 스크립트
Cortex Auto Verifier를 사용하여 작업 보고서 검증
"""

import sys
import os

# Cortex 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auto_verifier import get_auto_verifier
import json

# 검증할 작업 보고서 (방금 수행한 작업)
WORK_REPORT = """
## Phase 9 CRITICAL/HIGH/MEDIUM 이슈 수정 완료 보고

### 수정 완료 항목 (12개)

**CRITICAL 이슈 (4개):**
1. grounding_score 계산 통일화 구현 완료
2. Evidence Graph 동기화 구현 완료
3. Phase 9 초기화 에러 처리 추가 완료
4. Semantic Depth 계산 구현 완료

**HIGH 이슈 (4개):**
1. claim_extractor 명시적 우선순위 구현 완료
2. fuzzy_claim_analyzer 부정 표현 개선 완료
3. claim_verifier 파일 수정 여부 확인 (Git diff) 구현 완료
4. contradiction_detector_v2 성능 최적화 완료 (0.79초 달성)

**MEDIUM 이슈 (4개):**
1. Evidence Graph 캐시 동기화 완료 (grounding_scorer에 evidence_graph 주입)
   - 파일: core/grounding_scorer.py line 46
   - 파일: core/memory_manager.py
   - 방법: 생성자에 evidence_graph 파라미터 추가, memory_manager에서 전달

2. claim_verifier context_history 처리 통일 완료
   - 파일: core/claim_verifier.py lines 285-311
   - 방법: 우선순위 명확화 (context_history > Evidence Graph)
   - 디버깅 로그 추가

3. evidence_graph bare except 수정 완료
   - 파일: core/evidence_graph.py
   - 위치: compute_degree_centrality, compute_betweenness_centrality
   - 방법: bare except → (nx.NetworkXError, ValueError, KeyError)

4. fuzzy_claim_analyzer 기본 confidence 값 개선 완료
   - 파일: core/fuzzy_claim_analyzer.py
   - line 36: CONFIDENCE_SCORES["none"] = 0.0 → 0.5
   - line 442: return 0.0 → return 0.5
   - 근거: 확신도 표현 없음 = 중립값 0.5가 더 합리적

### 추가 수정 (회귀 방지)
- auto_verifier.py에서 Claim 없을 때 grounding_score 1.0 → 0.5 수정 (2곳)
  - line 139: 확신도 낮을 때
  - line 194: Claim 없을 때

### 검증 결과
- auto_verifier 테스트: 11/11 통과 (100%)
- 모든 수정사항 테스트 통과 확인

### LOW 이슈 현황
- Low #1 (claim_extractor 중복 Claim 감지): Semantic deduplication 필요 - 추후 개선 예정
- Low #2 (contradiction_detector_v2 함수 정의): 확인 완료 - 모든 함수 정의되어 있음
- Low #3 (하드코딩된 파라미터): 16개 이상 파라미터가 여러 파일에 하드코딩 - 추후 개선 예정
"""

def main():
    print("=" * 80)
    print("Phase 9 수정사항 할루시네이션 검증 시작 (ULTRATHINK MODE)")
    print("=" * 80)
    print()

    # Auto Verifier 초기화
    print("[1/4] Auto Verifier 초기화 중...")
    verifier = get_auto_verifier()
    print("✅ Auto Verifier 초기화 완료\n")

    # Context 생성 (프로젝트 경로 제공)
    project_path = "/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp/cortex_mcp"
    project_id = "cortex_mcp_test"

    context = {
        "project_id": project_id,
        "project_path": project_path,
        # files_modified는 제거 - Evidence Graph와 코드베이스 분석으로 검증
    }

    print("[2/4] 작업 보고서 검증 중...")
    print(f"보고서 길이: {len(WORK_REPORT)} 문자\n")

    # 디버그: 확신도 분석 결과 먼저 확인
    print("=" * 80)
    print("[DEBUG] 확신도 분석 (Fuzzy Claim Analyzer)")
    print("=" * 80)
    analyzer = verifier.fuzzy_analyzer
    analysis_result = analyzer.analyze_response(WORK_REPORT)
    print(f"확신도 레벨: {analysis_result['overall_confidence_level']}")
    print(f"확신도 점수: {analysis_result.get('average_confidence', 0.0):.3f}")
    print(f"HIGH_CONFIDENCE_THRESHOLD: {verifier.HIGH_CONFIDENCE_THRESHOLD}")
    print(f"추출된 Claim 수: {analysis_result.get('total_claims', 0)}")

    if analysis_result.get('claim_analyses'):
        print(f"\nClaim별 확신도:")
        for i, ca in enumerate(analysis_result['claim_analyses'], 1):
            print(f"  [{i}] {ca.get('confidence_level', 'unknown')} (fuzzy: {ca.get('fuzzy_score', 0):.2f})")

    if analysis_result.get('vague_expressions'):
        print(f"\n모호한 표현 {len(analysis_result['vague_expressions'])}개 발견")
    print()

    # 할루시네이션 검증 실행
    result = verifier.verify_response(WORK_REPORT, context=context)

    print("=" * 80)
    print("[3/4] 검증 결과")
    print("=" * 80)
    print()

    # 검증 결과 출력
    print(f"✅ 검증 완료: {result.verified}")
    print(f"📊 Grounding Score: {result.grounding_score:.2f}")
    print(f"🎯 Confidence Level: {result.confidence_level}")
    print(f"📝 추출된 Claim 수: {len(result.claims)}")
    print(f"⚠️  미검증 Claim 수: {len(result.unverified_claims)}")
    print(f"🔄 재작업 필요: {result.requires_retry}")
    if result.retry_reason:
        print(f"📋 재작업 사유: {result.retry_reason}")
    print()

    # ULTRATHINK MODE: 확신도별 분류 보고서
    print("=" * 80)
    print("ULTRATHINK MODE: 확신도별 분류 보고서")
    print("=" * 80)
    print()

    # 1. 검증 통과 (HIGH confidence)
    if result.verified_claims:
        print("=" * 80)
        print("검증 통과 (HIGH confidence)")
        print("=" * 80)
        for i, vclaim in enumerate(result.verified_claims, 1):
            print(f"\n[{i}] {vclaim['claim_type']}: {vclaim['text'][:80]}...")
            print(f"    - Fuzzy Score: {vclaim['fuzzy_score']:.2f} ({vclaim['confidence_level']})")
            print(f"    - Evidence 개수: {vclaim['evidence_count']}")
            print(f"    - Grounding Score: {vclaim['grounding_score']:.2f}")
        print()
    else:
        print("검증 통과한 HIGH confidence Claim이 없습니다.\n")

    # 2. 검증 보류 (MEDIUM/LOW confidence)
    if result.pending_claims:
        print("=" * 80)
        print("검증 보류 (MEDIUM/LOW confidence)")
        print("=" * 80)
        for i, pclaim in enumerate(result.pending_claims, 1):
            print(f"\n[{i}] {pclaim['claim_type']}: {pclaim['text'][:80]}...")
            print(f"    - Fuzzy Score: {pclaim['fuzzy_score']:.2f} ({pclaim['confidence_level']})")
            print(f"    - 이유: {pclaim['reason']}")
        print()
    else:
        print("검증 보류된 Claim이 없습니다.\n")

    # 3. 검증 실패 (HIGH confidence인데 실패)
    if result.unverified_claims:
        print("=" * 80)
        print("검증 실패 (HIGH confidence인데 증거 부족)")
        print("=" * 80)
        for i, uclaim in enumerate(result.unverified_claims, 1):
            print(f"\n[{i}] {uclaim['claim_type']}: {uclaim['text'][:80]}...")
            print(f"    - 이유: {uclaim['reason']}")
        print()
    else:
        print("검증 실패한 HIGH confidence Claim이 없습니다.\n")

    # 4. Referenced Contexts
    if result.referenced_contexts:
        print("=" * 80)
        print("참조된 Contexts")
        print("=" * 80)
        for ctx in result.referenced_contexts:
            print(f"  - {ctx}")
        print()

    # 최종 판정
    print("=" * 80)
    print("[4/4] 최종 판정 (ULTRATHINK MODE)")
    print("=" * 80)
    print()

    if result.grounding_score >= 0.7:
        print("✅ 판정: ACCEPT")
        print("   근거가 충분합니다. 작업 보고서가 신뢰할 수 있습니다.")
        exit_code = 0
    elif result.grounding_score >= 0.3:
        print("⚠️  판정: WARN")
        print("   애매한 상태입니다. 수동 확인이 필요합니다.")
        exit_code = 1
    else:
        print("🚨 판정: REJECT")
        print("   근거가 매우 부족합니다. 재작업이 필요합니다.")
        exit_code = 2

    print()
    print(f"Grounding Score: {result.grounding_score:.2f}")
    print(f"미검증 Claim 수: {len(result.unverified_claims)}")
    print()

    # JSON 저장 (ULTRATHINK MODE 필드 포함)
    output_file = "verification_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "verified": result.verified,
            "grounding_score": result.grounding_score,
            "confidence_level": result.confidence_level,
            "claims_count": len(result.claims),
            "unverified_claims_count": len(result.unverified_claims),
            "requires_retry": result.requires_retry,
            "retry_reason": result.retry_reason,
            "referenced_contexts": result.referenced_contexts,
            # ULTRATHINK MODE 필드
            "verified_claims": result.verified_claims,
            "verified_claims_count": len(result.verified_claims),
            "pending_claims": result.pending_claims,
            "pending_claims_count": len(result.pending_claims),
            "claim_grounding_scores": result.claim_grounding_scores,
        }, f, indent=2, ensure_ascii=False)

    print(f"📁 상세 결과 저장: {output_file}")
    print()

    return exit_code

if __name__ == "__main__":
    exit(main())
