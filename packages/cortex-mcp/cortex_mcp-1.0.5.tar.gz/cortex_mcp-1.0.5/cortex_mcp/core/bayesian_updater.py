"""
Bayesian Claim Confidence Updater
Cortex Phase 1: Track 1 - Product Engineering

설계 원칙 (베이지안 추론 이론 적용):
1. Claim type별 사전 확률(Prior) 정의
2. Evidence 품질 기반 우도(Likelihood) 계산
3. Reference History 성공률 반영
4. 사후 확률(Posterior) 계산: P(Claim | Evidence, History)

목적: False Positive 감소, 경고 precision 증가
이론적 근거: Bayes' Theorem
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .claim_extractor import Claim
from .reference_history import ReferenceHistory

# Claim Type별 사전 확률 (Prior)
# 실제 개발 데이터 기반 추정치
CLAIM_TYPE_PRIORS = {
    "implementation_complete": 0.70,  # 구현 완료 주장: 70% 신뢰도 (Evidence Graph 연동 후 상향)
    "reference_existing": 0.70,  # 기존 코드 참조: 70% 신뢰도
    "extension": 0.60,  # 기능 확장: 60% 신뢰도
    "modification": 0.70,  # 수정 완료: 70% 신뢰도 (Evidence Graph 연동 후 상향)
    "verification": 0.65,  # 검증 완료: 65% 신뢰도
    "bug_fix": 0.70,  # 버그 수정: 70% 신뢰도 (Evidence Graph 연동 후 상향)
}

# Evidence 품질 가중치
EVIDENCE_QUALITY_WEIGHTS = {
    # 기존 타입
    "git_diff": 1.0,  # Git diff 존재: 최고 신뢰도
    "file_exists": 0.8,  # 파일 존재: 높은 신뢰도
    "context_match": 0.6,  # Context 매칭: 중간 신뢰도
    "indirect_reference": 0.4,  # 간접 참조: 낮은 신뢰도

    # claim_verifier.py 신규 타입 (Phase 9.3 개선)
    "file_specific_diff": 0.9,  # 파일별 diff 확인: 매우 강력한 증거
    "evidence_graph_diff": 0.7,  # Evidence Graph의 Diff 노드: 강력한 증거
    "codebase_verified": 0.85,  # 코드베이스 완전 스캔: 매우 강력한 증거
    "evidence_graph_files": 0.6,  # Evidence Graph의 File 노드: 중간 신뢰도
    "modified_files": 0.5,  # 수정된 파일 목록: 보통 신뢰도
}

# Prior Clipping 상수 (Phase 9.3 개선: 극단적 prior 방지)
# Option B: Clipping (0.3-0.85) - 단순하고 scipy 의존성 없음
# 맹점 1-3 개선: PRIOR_CLIP_MIN 0.2 → 0.3 (과도한 부정 편향 방지)
PRIOR_CLIP_MIN = 0.3  # 최소 prior (0.2는 너무 낮아 과도한 경고 발생)
PRIOR_CLIP_MAX = 0.85  # 최대 prior (과신 방지)


def _clip_prior(prior: float) -> float:
    """
    Prior 값을 안전한 범위로 제한

    Args:
        prior: 원본 prior 값

    Returns:
        Clipped prior (0.2 ~ 0.85 범위)
    """
    return max(PRIOR_CLIP_MIN, min(PRIOR_CLIP_MAX, prior))


@dataclass
class BayesianResult:
    """
    베이지안 업데이트 결과

    논문 연구를 위한 모든 중간 계산 과정 포함
    """

    claim_text: str
    claim_type: str

    # Prior (사전 확률)
    prior: float
    prior_source: str  # "default", "history_adjusted", "context_adjusted"

    # Likelihood (우도)
    likelihood: float
    evidence_count: int
    evidence_quality_scores: List[float]

    # Posterior (사후 확률)
    posterior: float

    # 계산 과정 (재현성)
    calculation_steps: Dict[str, Any]

    # 메타데이터
    timestamp: str
    confidence_level: str  # "very_high", "high", "medium", "low", "very_low"


class BayesianUpdater:
    """
    베이지안 Claim Confidence 업데이트 엔진

    Bayes' Theorem 적용:
    P(Claim | Evidence, History) =
        P(Evidence | Claim) × P(Claim | History) / P(Evidence)

    간소화된 구현:
    posterior = prior × likelihood
    (P(Evidence)는 정규화 상수로 생략 가능)
    """

    def __init__(self, project_id: str, reference_history: Optional[ReferenceHistory] = None):
        """
        베이지안 업데이터 초기화

        Args:
            project_id: 프로젝트 식별자
            reference_history: Reference History 시스템 (선택적)
        """
        self.project_id = project_id
        self.reference_history = reference_history

    def update_posterior(
        self, claim: Claim, evidence_list: List[Dict], context_history: Optional[Dict] = None
    ) -> BayesianResult:
        """
        사후 확률 계산

        Args:
            claim: 검증할 Claim
            evidence_list: Evidence 목록 (각 evidence는 quality_score 포함)
            context_history: Context 이력 정보 (선택적)

        Returns:
            BayesianResult 객체
        """
        # Step 1: Prior 계산
        prior, prior_source = self._calculate_prior(claim, context_history)

        # Step 2: Likelihood Ratio 계산 (Noisy-OR Model)
        likelihood_ratio, evidence_quality_scores = self._calculate_likelihood(claim, evidence_list)

        # Step 3: Posterior 계산 (Full Bayesian Update)
        posterior = self._calculate_posterior(prior, likelihood_ratio)

        # Step 4: Confidence Level 결정
        confidence_level = self._determine_confidence_level(posterior)

        # 계산 과정 기록 (재현성)
        calculation_steps = {
            "prior_calculation": {
                "base_prior": CLAIM_TYPE_PRIORS.get(claim.claim_type, 0.5),
                "history_adjustment": prior_source == "history_adjusted",
                "final_prior": prior,
            },
            "likelihood_calculation": {
                "model": "Noisy-OR",
                "evidence_count": len(evidence_list),
                "quality_scores": evidence_quality_scores,
                "avg_quality": sum(evidence_quality_scores) / max(1, len(evidence_quality_scores)),
                "likelihood_ratio": likelihood_ratio,
            },
            "posterior_calculation": {
                "formula": "posterior = (prior_odds × likelihood_ratio) / (1 + prior_odds × likelihood_ratio)",
                "prior": prior,
                "likelihood_ratio": likelihood_ratio,
                "posterior": posterior,
            },
        }

        return BayesianResult(
            claim_text=claim.text,
            claim_type=claim.claim_type,
            prior=prior,
            prior_source=prior_source,
            likelihood=likelihood_ratio,  # Store likelihood_ratio in likelihood field for backward compatibility
            evidence_count=len(evidence_list),
            evidence_quality_scores=evidence_quality_scores,
            posterior=posterior,
            calculation_steps=calculation_steps,
            timestamp=datetime.now().isoformat(),
            confidence_level=confidence_level,
        )

    def _calculate_prior(self, claim: Claim, context_history: Optional[Dict]) -> tuple[float, str]:
        """
        사전 확률 계산

        순서:
        1. Claim type 기본 prior
        2. Reference History 성공률 반영
        3. Context 이력 반영

        Args:
            claim: Claim 객체
            context_history: Context 이력

        Returns:
            (prior, prior_source) 튜플
        """
        # 기본 prior
        base_prior = CLAIM_TYPE_PRIORS.get(claim.claim_type, 0.5)

        # Reference History 반영
        if self.reference_history:
            success_rate = self.reference_history.get_success_rate(
                claim_type=claim.claim_type, lookback_count=10  # 최근 10회 기준
            )

            if success_rate is not None:
                # Prior와 성공률의 가중 평균
                adjusted_prior = (base_prior * 0.5) + (success_rate * 0.5)
                # Clipping 적용: 극단적 prior 방지
                adjusted_prior = _clip_prior(adjusted_prior)
                return (adjusted_prior, "history_adjusted")

        # Context 이력 반영
        if context_history and "similar_claims" in context_history:
            similar_success_rate = context_history.get("success_rate", None)
            if similar_success_rate is not None:
                adjusted_prior = (base_prior * 0.7) + (similar_success_rate * 0.3)
                # Clipping 적용: 극단적 prior 방지
                adjusted_prior = _clip_prior(adjusted_prior)
                return (adjusted_prior, "context_adjusted")

        return (base_prior, "default")

    def _calculate_likelihood(
        self, claim: Claim, evidence_list: List[Dict]
    ) -> tuple[float, List[float]]:
        """
        우도(Likelihood) 계산 - Noisy-OR Model

        Noisy-OR Model:
        - 여러 독립적 증거는 결합하여 강화됨 (평균이 아님)
        - P(E|H_true) = 1 - ∏(1 - quality_score_i)
        - P(E|H_false) = ∏(1 - quality_score_i)
        - Likelihood Ratio = P(E|H_true) / P(E|H_false)

        Args:
            claim: Claim 객체
            evidence_list: Evidence 목록

        Returns:
            (likelihood_ratio, quality_scores) 튜플
        """
        if not evidence_list:
            return (0.0, [])

        quality_scores = []

        for evidence in evidence_list:
            # Evidence 타입별 가중치 적용
            evidence_type = evidence.get("type", "indirect_reference")
            weight = EVIDENCE_QUALITY_WEIGHTS.get(evidence_type, 0.4)

            # Evidence 자체 품질 점수
            base_score = evidence.get("quality_score", 0.5)

            # 가중치 적용
            weighted_score = base_score * weight
            quality_scores.append(weighted_score)

        # Noisy-OR 계산 (division by zero 방지)
        if len(quality_scores) == 0:
            # Evidence는 있지만 quality_scores가 비어있는 edge case
            return (0.0, [])

        # Noisy-OR: P(E|H_true) = 1 - ∏(1 - score_i)
        p_evidence_given_true = 1.0
        for score in quality_scores:
            p_evidence_given_true *= (1.0 - score)
        p_evidence_given_true = 1.0 - p_evidence_given_true

        # P(E|H_false) = ∏(1 - score_i)
        p_evidence_given_false = 1.0
        for score in quality_scores:
            p_evidence_given_false *= (1.0 - score)

        # Avoid division by zero
        if p_evidence_given_false < 0.001:
            p_evidence_given_false = 0.001

        # Likelihood Ratio (증거의 진단력)
        likelihood_ratio = p_evidence_given_true / p_evidence_given_false

        return (likelihood_ratio, quality_scores)

    def _calculate_posterior(self, prior: float, likelihood_ratio: float) -> float:
        """
        사후 확률 계산 (Full Bayesian Update with Likelihood Ratio)

        Posterior Odds = Prior Odds × Likelihood Ratio
        Prior Odds = P(H) / (1 - P(H))
        Posterior = Posterior Odds / (1 + Posterior Odds)

        Args:
            prior: 사전 확률 P(H)
            likelihood_ratio: 우도비 P(E|H_true) / P(E|H_false)

        Returns:
            사후 확률 (0.0 ~ 1.0)
        """
        # Avoid division by zero
        if prior >= 1.0:
            prior = 0.999
        if prior <= 0.0:
            prior = 0.001

        # Convert prior to odds
        prior_odds = prior / (1.0 - prior)

        # Bayesian update
        posterior_odds = prior_odds * likelihood_ratio

        # Convert odds back to probability
        posterior = posterior_odds / (1.0 + posterior_odds)

        # 0.0 ~ 1.0 범위로 클리핑 (수치 안정성)
        return max(0.0, min(1.0, posterior))

    def _determine_confidence_level(self, posterior: float) -> str:
        """
        Posterior 기반 Confidence Level 결정

        Args:
            posterior: 사후 확률

        Returns:
            Confidence level 문자열
        """
        if posterior >= 0.8:
            return "very_high"
        elif posterior >= 0.6:
            return "high"
        elif posterior >= 0.4:
            return "medium"
        elif posterior >= 0.2:
            return "low"
        else:
            return "very_low"

    def batch_update(
        self,
        claims: List[Claim],
        evidence_map: Dict[str, List[Dict]],
        context_history: Optional[Dict] = None,
    ) -> List[BayesianResult]:
        """
        여러 Claim 일괄 업데이트

        Args:
            claims: Claim 목록
            evidence_map: {claim_text: evidence_list} 매핑
            context_history: Context 이력

        Returns:
            BayesianResult 목록
        """
        results = []

        for claim in claims:
            evidence_list = evidence_map.get(claim.text, [])
            result = self.update_posterior(claim, evidence_list, context_history)
            results.append(result)

        return results

    def get_statistics(self, results: List[BayesianResult]) -> Dict:
        """
        베이지안 업데이트 통계 생성 (연구용)

        Args:
            results: BayesianResult 목록

        Returns:
            통계 딕셔너리
        """
        if not results:
            return {}

        posteriors = [r.posterior for r in results]

        # division by zero 방지 (posteriors가 비어있을 수 있음)
        if len(posteriors) == 0:
            avg_posterior = 0.0
            max_posterior = 0.0
            min_posterior = 0.0
        else:
            avg_posterior = sum(posteriors) / len(posteriors)
            max_posterior = max(posteriors)
            min_posterior = min(posteriors)

        return {
            "total_claims": len(results),
            "avg_posterior": avg_posterior,
            "max_posterior": max_posterior,
            "min_posterior": min_posterior,
            "confidence_distribution": {
                "very_high": sum(1 for r in results if r.confidence_level == "very_high"),
                "high": sum(1 for r in results if r.confidence_level == "high"),
                "medium": sum(1 for r in results if r.confidence_level == "medium"),
                "low": sum(1 for r in results if r.confidence_level == "low"),
                "very_low": sum(1 for r in results if r.confidence_level == "very_low"),
            },
            "prior_sources": {
                "default": sum(1 for r in results if r.prior_source == "default"),
                "history_adjusted": sum(1 for r in results if r.prior_source == "history_adjusted"),
                "context_adjusted": sum(1 for r in results if r.prior_source == "context_adjusted"),
            },
        }
