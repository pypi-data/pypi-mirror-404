"""
Cortex Hallucination Detection System - 중앙 상수 정의

모든 할루시네이션 관련 임계값과 설정을 한 곳에서 관리합니다.
다른 모듈에서는 이 파일에서 import하여 사용하세요.

Phase 9.7: 일관성 통일
"""

# =============================================================================
# 1. 확신도 점수 매핑 (Confidence Scores)
# =============================================================================
# fuzzy_claim_analyzer.py와 auto_verifier.py에서 공통 사용
CONFIDENCE_SCORES = {
    "very_high": 1.0,  # 확실, 반드시, 명백히
    "high": 0.8,       # 아마도, 거의, 대부분
    "medium": 0.5,     # 가능성, 추측, 예상
    "low": 0.3,        # 불확실, 모호, 회의적
    "none": 0.5,       # 확신도 표현 없음 → neutral (0.0은 너무 보수적)
}

# =============================================================================
# 2. 검증 임계값 (Verification Thresholds)
# =============================================================================
# auto_verifier.py, claim_verifier.py, memory_manager.py에서 공통 사용

# 자동 검증 트리거 임계값
HIGH_CONFIDENCE_THRESHOLD = 0.8  # 이 이상이면 자동 검증 트리거

# 검증 통과 임계값 (Grounding Score 기준)
# 통일된 값: 0.6 (Balanced Mode)
VERIFICATION_PASS_THRESHOLD = 0.6

# Bayesian Posterior 검증 임계값
# 통일된 값: 0.6 (VERIFICATION_PASS_THRESHOLD와 동일)
BAYESIAN_VERIFICATION_THRESHOLD = 0.6

# =============================================================================
# 3. 3-Tier Decision System (Hallucination Detection)
# =============================================================================
# memory_manager.py에서 사용
# Balanced Mode: 10-15% human review, 85-90% 정확도

HALLUCINATION_THRESHOLDS = {
    "reject_below": 0.4,       # < 0.4 → REJECT (자동 거부)
    "warn_range": (0.4, 0.6),  # 0.4-0.6 → WARN (수동 확인 요청)
    "accept_above": 0.6,       # >= 0.6 → ACCEPT (자동 수락)
}

# =============================================================================
# 4. Content Matching 임계값 (Claim 타입별)
# =============================================================================
# content_matcher.py에서 사용
SIMILARITY_THRESHOLDS = {
    "implementation_complete": 0.35,  # 구현 완료는 높은 기준
    "bug_fix": 0.10,                  # 버그 수정은 낮은 기준 (한-영 매칭 개선)
    "modification": 0.40,             # 수정은 가장 높은 기준
    "reference_existing": 0.25,       # 기존 참조는 낮은 기준
    "verification": 0.30,             # 검증은 중간 기준
    "extension": 0.30,                # 확장은 중간 기준
    "default": 0.30,                  # 기본값
}

# =============================================================================
# 5. Claim 타입 우선순위
# =============================================================================
# claim_extractor.py에서 사용
# bug_fix를 implementation_complete보다 먼저 검사하여 더 구체적인 패턴 우선
CLAIM_TYPE_PRIORITY = [
    "bug_fix",                 # 최우선 (더 구체적인 패턴)
    "modification",            # 수정/변경 완료
    "implementation_complete", # 구현 완료 주장
    "verification",            # 검증/테스트 완료
    "extension",               # 기능 확장
    "reference_existing",      # 기존 코드 참조
]

# =============================================================================
# 6. 타임아웃 설정
# =============================================================================
# auto_verifier.py에서 사용
VERIFICATION_TIMEOUT_SECONDS = 30  # 전체 검증 타임아웃 (초)
PER_CLAIM_TIMEOUT_SECONDS = 5      # 개별 claim 검증 타임아웃 (초)

# =============================================================================
# 7. Grounding Scorer 설정
# =============================================================================
# grounding_scorer.py에서 사용
DEPTH_DECAY_FACTOR = 0.85  # 깊이별 감소 계수
DEPTH_WEIGHT_MIN = 0.15    # 최소 가중치
