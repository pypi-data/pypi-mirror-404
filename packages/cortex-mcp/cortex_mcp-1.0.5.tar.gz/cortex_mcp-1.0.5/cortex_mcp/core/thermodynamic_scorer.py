"""
Thermodynamic Free Energy Minimization Scorer

Enhancement #2: Grounding Score를 열역학 자유 에너지로 재해석
- Energy = Evidence Strength (H) - Temperature * Uncertainty (S)
- 낮은 Free Energy = 안정 상태 = Grounded
- 높은 Free Energy = 불안정 상태 = Hallucination

이론적 배경:
- Gibbs Free Energy: ΔG = ΔH - TΔS
- Boltzmann Distribution: P ∝ exp(-E/kT)
"""

import math
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ThermodynamicResult:
    """열역학 분석 결과"""
    free_energy: float  # 자유 에너지 (낮을수록 안정)
    grounding_score: float  # 변환된 Grounding Score (0.0 ~ 1.0)
    temperature: float  # 사용된 온도 파라미터
    enthalpy: float  # 엔탈피 (Evidence 강도)
    entropy: float  # 엔트로피 (불확실성)
    stability_status: str  # "stable", "metastable", "unstable"
    details: Dict


class ThermodynamicScorer:
    """
    열역학 기반 Grounding Score 계산기

    주요 기능:
    1. Evidence Strength를 엔탈피(H)로 변환
    2. Uncertainty를 엔트로피(S)로 변환
    3. Claim 깊이에 따른 동적 온도 조정
    4. Free Energy 기반 안정성 판정
    """

    # 기본 설정
    DEFAULT_CONFIG = {
        "base_temperature": 1.0,
        "depth_decay_rate": 0.15,
        "min_temperature": 0.3,
        "max_temperature": 2.0,
        # 안정성 임계값
        "stable_threshold": -0.3,  # 이 이하면 안정 (grounded)
        "unstable_threshold": 0.5,  # 이 이상이면 불안정 (hallucination)
        # Evidence 타입별 엔탈피 가중치
        "enthalpy_weights": {
            "git_diff": 1.0,
            "file_specific_diff": 0.9,
            "codebase_verified": 0.85,
            "file_exists": 0.8,
            "evidence_graph_diff": 0.7,
            "context_match": 0.6,
            "modified_files": 0.5,
            "indirect_reference": 0.4,
        },
        # Boltzmann 상수 (정규화용)
        "boltzmann_constant": 1.0,
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Thermodynamic Scorer 초기화

        Args:
            config: 설정 딕셔너리 (None이면 기본값 사용)
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}

    def calculate_score(
        self,
        evidence_list: List[Dict],
        uncertainty: float,
        claim_depth: int = 0,
        bayesian_posterior: Optional[float] = None
    ) -> ThermodynamicResult:
        """
        열역학 기반 Grounding Score 계산

        Args:
            evidence_list: 증거 목록 [{"type": str, "weight": float}, ...]
            uncertainty: 불확실성 (0.0 ~ 1.0, Fuzzy 확신도의 역수)
            claim_depth: Claim 깊이 (깊을수록 더 보수적)
            bayesian_posterior: Bayesian Posterior (선택적)

        Returns:
            ThermodynamicResult: 열역학 분석 결과
        """
        # 1. 온도 계산 (깊이에 따라 조정)
        temperature = self._calculate_temperature(claim_depth)

        # 2. 엔탈피 계산 (Evidence 강도)
        enthalpy = self._calculate_enthalpy(evidence_list)

        # 3. 엔트로피 계산 (불확실성)
        entropy = self._calculate_entropy(uncertainty)

        # 4. 자유 에너지 계산
        # ΔG = ΔH - TΔS
        # 여기서는 부호를 반대로: Energy = -H + T*S
        # (높은 Evidence = 낮은 에너지, 높은 불확실성 = 높은 에너지)
        free_energy = -enthalpy + temperature * entropy

        # 5. Boltzmann 분포 기반 Grounding Score 변환
        # P(grounded) ∝ exp(-E/kT)
        k = self.config["boltzmann_constant"]
        grounding_score = self._boltzmann_normalize(free_energy, temperature, k)

        # 6. Bayesian Posterior 적용 (있는 경우)
        if bayesian_posterior is not None:
            grounding_score = grounding_score * bayesian_posterior

        # 7. 안정성 상태 판정
        stability_status = self._determine_stability(free_energy)

        logger.info(
            f"[THERMO] energy={free_energy:.3f}, T={temperature:.3f}, "
            f"H={enthalpy:.3f}, S={entropy:.3f}, score={grounding_score:.3f}"
        )

        return ThermodynamicResult(
            free_energy=free_energy,
            grounding_score=grounding_score,
            temperature=temperature,
            enthalpy=enthalpy,
            entropy=entropy,
            stability_status=stability_status,
            details={
                "n_evidences": len(evidence_list),
                "claim_depth": claim_depth,
                "bayesian_applied": bayesian_posterior is not None,
                "thresholds": {
                    "stable": self.config["stable_threshold"],
                    "unstable": self.config["unstable_threshold"],
                }
            }
        )

    def _calculate_temperature(self, claim_depth: int) -> float:
        """
        Claim 깊이에 따른 동적 온도 계산

        깊이가 깊을수록 더 보수적 (낮은 온도)
        - 낮은 온도: 에너지 차이에 민감 (보수적)
        - 높은 온도: 에너지 차이에 둔감 (관대)
        """
        base_T = self.config["base_temperature"]
        decay = self.config["depth_decay_rate"]
        min_T = self.config["min_temperature"]
        max_T = self.config["max_temperature"]

        # 지수 감쇠
        temperature = base_T * math.exp(-decay * claim_depth)

        # 범위 제한
        return max(min_T, min(max_T, temperature))

    def _calculate_enthalpy(self, evidence_list: List[Dict]) -> float:
        """
        Evidence 목록에서 엔탈피(H) 계산

        엔탈피 = 증거 강도의 가중 합
        높은 엔탈피 = 강한 증거 = 낮은 에너지
        """
        if not evidence_list:
            return 0.0

        weights = self.config["enthalpy_weights"]
        total_enthalpy = 0.0
        max_possible = 0.0

        for evidence in evidence_list:
            ev_type = evidence.get("type", "indirect_reference")
            ev_weight = evidence.get("weight", 1.0)

            # 타입별 기본 가중치
            type_weight = weights.get(ev_type, 0.4)

            # 개별 증거 가중치 적용
            contribution = type_weight * ev_weight
            total_enthalpy += contribution
            max_possible += type_weight

        # 정규화 (0.0 ~ 1.0)
        if max_possible > 0:
            return total_enthalpy / max_possible
        return 0.0

    def _calculate_entropy(self, uncertainty: float) -> float:
        """
        불확실성에서 엔트로피(S) 계산

        Shannon Entropy 스타일 변환
        S = -p*log(p) - (1-p)*log(1-p)
        """
        # uncertainty를 확률로 해석
        p = max(0.001, min(0.999, uncertainty))

        # Shannon entropy (0 ~ 0.693)
        entropy = -p * math.log(p) - (1 - p) * math.log(1 - p)

        # 정규화 (0 ~ 1)
        max_entropy = math.log(2)  # 0.693
        return entropy / max_entropy

    def _boltzmann_normalize(
        self,
        energy: float,
        temperature: float,
        k: float
    ) -> float:
        """
        Boltzmann 분포 기반 정규화

        P(grounded) = exp(-E/kT) / (1 + exp(-E/kT))
        = 1 / (1 + exp(E/kT))  # Sigmoid 형태
        """
        if temperature <= 0:
            temperature = 0.1

        exponent = energy / (k * temperature)

        # Overflow 방지
        if exponent > 700:
            return 0.0
        elif exponent < -700:
            return 1.0

        return 1.0 / (1.0 + math.exp(exponent))

    def _determine_stability(self, free_energy: float) -> str:
        """
        자유 에너지 기반 안정성 판정

        Returns:
            "stable": 안정 (grounded) - 낮은 에너지
            "metastable": 준안정 (경계) - 중간 에너지
            "unstable": 불안정 (hallucination) - 높은 에너지
        """
        stable_th = self.config["stable_threshold"]
        unstable_th = self.config["unstable_threshold"]

        if free_energy <= stable_th:
            return "stable"
        elif free_energy >= unstable_th:
            return "unstable"
        else:
            return "metastable"

    def calculate_batch(
        self,
        claims_data: List[Dict]
    ) -> List[ThermodynamicResult]:
        """
        여러 Claim에 대해 일괄 계산

        Args:
            claims_data: [
                {
                    "evidences": [...],
                    "uncertainty": float,
                    "depth": int,
                    "bayesian_posterior": Optional[float]
                },
                ...
            ]

        Returns:
            List[ThermodynamicResult]
        """
        results = []
        for data in claims_data:
            result = self.calculate_score(
                evidence_list=data.get("evidences", []),
                uncertainty=data.get("uncertainty", 0.5),
                claim_depth=data.get("depth", 0),
                bayesian_posterior=data.get("bayesian_posterior")
            )
            results.append(result)
        return results

    def aggregate_scores(
        self,
        results: List[ThermodynamicResult]
    ) -> ThermodynamicResult:
        """
        여러 결과를 집계하여 전체 점수 계산

        Args:
            results: 개별 ThermodynamicResult 목록

        Returns:
            집계된 ThermodynamicResult
        """
        if not results:
            return ThermodynamicResult(
                free_energy=0.0,
                grounding_score=0.5,
                temperature=self.config["base_temperature"],
                enthalpy=0.0,
                entropy=0.5,
                stability_status="metastable",
                details={"reason": "no_results"}
            )

        # 가중 평균 (불안정한 결과에 더 높은 가중치)
        total_weight = 0.0
        weighted_energy = 0.0
        weighted_score = 0.0

        for result in results:
            # 불안정할수록 가중치 높음 (보수적)
            weight = 1.0 + max(0, result.free_energy)
            total_weight += weight
            weighted_energy += result.free_energy * weight
            weighted_score += result.grounding_score * weight

        avg_energy = weighted_energy / total_weight
        avg_score = weighted_score / total_weight

        # 최악의 안정성 상태 사용 (보수적)
        stability_order = {"stable": 0, "metastable": 1, "unstable": 2}
        worst_stability = max(
            results,
            key=lambda r: stability_order.get(r.stability_status, 1)
        ).stability_status

        return ThermodynamicResult(
            free_energy=avg_energy,
            grounding_score=avg_score,
            temperature=sum(r.temperature for r in results) / len(results),
            enthalpy=sum(r.enthalpy for r in results) / len(results),
            entropy=sum(r.entropy for r in results) / len(results),
            stability_status=worst_stability,
            details={
                "n_claims": len(results),
                "aggregation_method": "weighted_average",
                "stability_method": "worst_case",
            }
        )

    def get_hallucination_risk(
        self,
        result: ThermodynamicResult
    ) -> Tuple[float, str]:
        """
        열역학 결과를 할루시네이션 위험으로 변환

        Returns:
            (risk_score, risk_level)
            - risk_score: 0.0 ~ 1.0
            - risk_level: "low", "medium", "high", "critical"
        """
        # 자유 에너지 기반 위험도
        energy = result.free_energy
        stable_th = self.config["stable_threshold"]
        unstable_th = self.config["unstable_threshold"]

        # 위험 점수 계산
        if energy <= stable_th:
            risk_score = 0.0
        elif energy >= unstable_th:
            # 선형 스케일링 (unstable 이상)
            risk_score = min(1.0, 0.5 + (energy - unstable_th) * 0.5)
        else:
            # 중간 구간
            range_size = unstable_th - stable_th
            risk_score = 0.5 * (energy - stable_th) / range_size

        # 위험 레벨 판정
        if risk_score < 0.25:
            risk_level = "low"
        elif risk_score < 0.5:
            risk_level = "medium"
        elif risk_score < 0.75:
            risk_level = "high"
        else:
            risk_level = "critical"

        return risk_score, risk_level


# 싱글톤 인스턴스
_thermodynamic_scorer: Optional[ThermodynamicScorer] = None


def get_thermodynamic_scorer(config: Optional[Dict] = None) -> ThermodynamicScorer:
    """Thermodynamic Scorer 싱글톤 반환"""
    global _thermodynamic_scorer
    if _thermodynamic_scorer is None:
        _thermodynamic_scorer = ThermodynamicScorer(config)
    return _thermodynamic_scorer
