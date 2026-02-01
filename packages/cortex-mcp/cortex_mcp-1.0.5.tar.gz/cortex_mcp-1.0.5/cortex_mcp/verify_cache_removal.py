#!/usr/bin/env python3
"""
캐시 제거 작업 할루시네이션 검증 스크립트
Cortex Auto Verifier를 사용하여 캐시 제거 작업 검증
"""

import sys
import os

# Cortex 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auto_verifier import get_auto_verifier
import json

# 검증할 작업 보고서 (캐시 제거 작업)
WORK_REPORT = """
## ULTRATHINK MODE: 캐시 기능 제거 작업 완료 보고

### 작업 개요
Cortex의 3가지 캐시 시스템을 모두 제거하여 정확성을 우선시하도록 개선했습니다.
파일 수정 후 이전 버전을 참조하는 문제를 완전히 해결했습니다.

### 제거 완료 항목 (3개)

#### 1. Context Cache 제거 (context_manager.py)
**제거된 코드:**
- 라인 98: `self._context_cache: Dict[str, ContextState] = {}` 초기화 제거
- 라인 449-486: `_load_single_context()` 함수에서 캐시 확인 로직 제거
- 라인 234-259: `compress_context()` 함수 단순화 (항상 success 반환)
- 라인 420-428: `_maybe_cleanup()` 함수 비활성화 (pass로 변경)
- 라인 816-863: `_background_compression_worker()` 함수 비활성화 (pass로 변경)
- 라인 827-906: `compress_on_task_completion()` 함수 단순화 (success 반환)

**변경 내용:**
- 모든 Context 로드 시 디스크에서 직접 읽기 (~20ms 추가)
- 캐시 압축 기능 제거 (더 이상 필요 없음)
- 백그라운드 압축 워커 비활성화

**검증 방법:**
- `grep -n "self._context_cache" context_manager.py`로 확인
- 주석 외에 참조 없음 (라인 99 주석만 존재)

#### 2. ClaimVerifier Cache 제거 (auto_verifier.py)
**제거된 코드:**
- 라인 71: `self._claim_verifier_cache = {}` 초기화 제거
- 라인 72: `self._grounding_scorer_cache = {}` 초기화 제거
- 라인 496-506: `_get_claim_verifier()` 함수에서 캐시 확인 로직 제거
- 라인 535-562: `_get_grounding_scorer()` 함수에서 캐시 확인 로직 제거

**변경 내용:**
- 모든 ClaimVerifier 생성 시 새로운 인스턴스 생성 (~100ms 추가)
- 모든 GroundingScorer 생성 시 새로운 인스턴스 생성 (~50ms 추가)
- Evidence Graph 동기화는 유지 (ClaimVerifier와 GroundingScorer 공유)

**검증 방법:**
- `grep -n "_claim_verifier_cache\|_grounding_scorer_cache" auto_verifier.py`로 확인
- 모든 참조 제거 완료

#### 3. Embedding Cache 제거 (rag_engine.py)
**제거된 코드:**
- 라인 89: `self._embedding_cache: Dict[str, List[float]] = {}` 초기화 제거
- 라인 90: `self._cache_max_size = 10000` 제거
- 라인 409-420: 임베딩 캐시 확인 및 저장 로직 제거
- 라인 453-461: `_evict_oldest_embedding()` 함수 비활성화 (pass로 변경)

**변경 내용:**
- 모든 임베딩 생성 시 새로운 벡터 생성 (~400ms 추가)
- SHA256 해시 기반 캐시 제거 (메모리 누수 방지)
- LRU 정리 로직 제거

**검증 방법:**
- `grep -n "_embedding_cache\|_cache_max_size" rag_engine.py`로 확인
- 모든 참조 제거 완료

### 성능 vs 정확성 트레이드오프

#### 성능 저하 (허용 가능)
- Context 로드: +20ms
- ClaimVerifier 생성: +100ms
- GroundingScorer 생성: +50ms
- Embedding 생성: +400ms
- **총 예상 추가 시간: ~570ms (1초 미만)**

#### 정확성 향상 (핵심 가치)
- 파일 수정 후 항상 최신 버전 참조
- Evidence Graph 항상 최신 상태 유지
- 임베딩 벡터 항상 최신 내용 반영
- 할루시네이션 검증 정확도 100% 유지

### 검증 완료
- Context Cache 참조: 0개 (주석 제외)
- ClaimVerifier Cache 참조: 0개
- Embedding Cache 참조: 0개
- **모든 캐시 제거 완료 확인됨**
"""

def main():
    print("=" * 80)
    print("캐시 제거 작업 할루시네이션 검증 시작 (ULTRATHINK MODE)")
    print("=" * 80)
    print()

    # Auto Verifier 초기화
    print("[1/4] Auto Verifier 초기화 중...")
    verifier = get_auto_verifier()
    print("✅ Auto Verifier 초기화 완료\n")

    # Context 생성 (프로젝트 경로 제공)
    project_path = "/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp/cortex_mcp"
    project_id = "cortex_mcp_cache_removal"

    context = {
        "project_id": project_id,
        "project_path": project_path,
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
        print("   근거가 충분합니다. 캐시 제거 작업이 신뢰할 수 있습니다.")
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
    output_file = "cache_removal_verification_result.json"
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
