"""
Wave Interference Pattern Detector

Enhancement #3: Claim과 Evidence를 파동으로 모델링
- Constructive Interference: 같은 위상 → 강화 (Grounded)
- Destructive Interference: 반대 위상 → 상쇄 (Contradiction/Hallucination)

이론적 배경:
- 파동 중첩 원리 (Superposition Principle)
- 간섭 패턴: A_result = sqrt(A1^2 + A2^2 + 2*A1*A2*cos(Δφ))
"""

import math
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class WaveComponent:
    """파동 컴포넌트"""
    amplitude: float  # 진폭 (확신도/강도)
    phase: float  # 위상 (라디안, -π ~ π)
    frequency: float = 1.0  # 주파수 (기본값 1)
    source_id: str = ""  # 소스 식별자


@dataclass
class InterferenceResult:
    """간섭 분석 결과"""
    interference_score: float  # -1.0 ~ 1.0 (음수: 상쇄, 양수: 강화)
    interference_type: str  # "constructive", "destructive", "neutral"
    resultant_amplitude: float  # 결과 진폭
    phase_difference: float  # 위상 차이 (라디안)
    is_contradiction: bool  # 모순 감지 여부
    details: Dict


class WaveInterferenceDetector:
    """
    파동 간섭 기반 모순/일치 감지기

    주요 기능:
    1. Claim/Evidence를 파동으로 변환
    2. 간섭 패턴 분석
    3. Constructive/Destructive 판정
    4. 모순 감지 강화
    """

    # 기본 설정
    DEFAULT_CONFIG = {
        "constructive_threshold": 0.3,  # 이 이상이면 constructive
        "destructive_threshold": -0.3,  # 이 이하면 destructive
        "phase_weight": 0.5,  # 위상 차이 가중치
        "amplitude_weight": 0.5,  # 진폭 가중치
        # 시간 키워드 (다국어)
        "before_keywords": [
            "먼저", "이전", "전에", "과거", "before", "prior", "previously",
            "earlier", "先", "之前", "以前", "d'abord", "avant", "先に", "前に"
        ],
        "after_keywords": [
            "나중", "이후", "후에", "다음", "after", "later", "subsequently",
            "then", "後", "之后", "以後", "ensuite", "après", "後で", "次に"
        ],
        # 극성 키워드
        "positive_keywords": [
            "성공", "완료", "동작", "작동", "가능", "있다", "했다",
            "success", "complete", "works", "working", "possible", "done",
            "成功", "完了", "動作", "可能"
        ],
        "negative_keywords": [
            "실패", "오류", "에러", "불가", "없다", "안된다", "못했다",
            "fail", "error", "impossible", "cannot", "doesn't", "won't",
            "失敗", "エラー", "不可能"
        ],
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Wave Interference Detector 초기화

        Args:
            config: 설정 딕셔너리 (None이면 기본값 사용)
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}

    def claim_to_wave(
        self,
        claim_text: str,
        confidence: float,
        context: Optional[Dict] = None
    ) -> WaveComponent:
        """
        Claim을 파동 컴포넌트로 변환

        Args:
            claim_text: Claim 텍스트
            confidence: 확신도 (0.0 ~ 1.0)
            context: 추가 컨텍스트

        Returns:
            WaveComponent
        """
        # 진폭 = 확신도
        amplitude = confidence

        # 위상 = 시간/순서 정보에서 추출
        phase = self._calculate_phase(claim_text)

        # 주파수 = 극성 기반 (긍정: 양수, 부정: 음수 방향)
        polarity = self._detect_polarity(claim_text)
        frequency = 1.0 if polarity >= 0 else -1.0

        return WaveComponent(
            amplitude=amplitude,
            phase=phase,
            frequency=frequency,
            source_id=f"claim:{claim_text[:50]}"
        )

    def evidence_to_wave(
        self,
        evidence_type: str,
        evidence_strength: float,
        evidence_text: str = ""
    ) -> WaveComponent:
        """
        Evidence를 파동 컴포넌트로 변환

        Args:
            evidence_type: 증거 타입 (git_diff, file_exists 등)
            evidence_strength: 증거 강도 (0.0 ~ 1.0)
            evidence_text: 증거 텍스트 (선택적)

        Returns:
            WaveComponent
        """
        # 진폭 = 증거 강도
        amplitude = evidence_strength

        # 위상 = 증거 타입에 따라 결정
        # 직접 증거는 위상 0, 간접 증거는 약간의 위상 차이
        phase_map = {
            "git_diff": 0.0,
            "file_specific_diff": 0.1,
            "codebase_verified": 0.2,
            "file_exists": 0.3,
            "context_match": 0.5,
            "indirect_reference": 0.7,
        }
        base_phase = phase_map.get(evidence_type, 0.5)

        # 텍스트가 있으면 시간 정보 추가
        if evidence_text:
            text_phase = self._calculate_phase(evidence_text)
            phase = (base_phase + text_phase) / 2
        else:
            phase = base_phase

        return WaveComponent(
            amplitude=amplitude,
            phase=phase,
            frequency=1.0,
            source_id=f"evidence:{evidence_type}"
        )

    def calculate_interference(
        self,
        wave1: WaveComponent,
        wave2: WaveComponent
    ) -> InterferenceResult:
        """
        두 파동의 간섭 계산

        파동 중첩 공식:
        A_result = sqrt(A1^2 + A2^2 + 2*A1*A2*cos(Δφ))

        Args:
            wave1: 첫 번째 파동 (보통 Claim)
            wave2: 두 번째 파동 (보통 Evidence)

        Returns:
            InterferenceResult
        """
        A1 = wave1.amplitude
        A2 = wave2.amplitude
        phase_diff = wave1.phase - wave2.phase

        # 주파수 차이 고려 (반대 극성이면 위상 π 추가)
        if wave1.frequency * wave2.frequency < 0:
            phase_diff += math.pi

        # 위상 차이 정규화 (-π ~ π)
        while phase_diff > math.pi:
            phase_diff -= 2 * math.pi
        while phase_diff < -math.pi:
            phase_diff += 2 * math.pi

        # 간섭 계산
        cos_phase = math.cos(phase_diff)

        # 결과 진폭
        amplitude_squared = A1**2 + A2**2 + 2 * A1 * A2 * cos_phase
        resultant_amplitude = math.sqrt(max(0, amplitude_squared))

        # 간섭 점수 (-1 ~ 1)
        # cos(0) = 1 (완전 보강), cos(π) = -1 (완전 상쇄)
        max_amplitude = A1 + A2
        min_amplitude = abs(A1 - A2)

        if max_amplitude > 0:
            # 정규화된 간섭 점수
            interference_score = cos_phase * (A1 * A2) / (max_amplitude * max_amplitude / 4 + 0.01)
            interference_score = max(-1.0, min(1.0, interference_score))
        else:
            interference_score = 0.0

        # 간섭 타입 판정
        if interference_score > self.config["constructive_threshold"]:
            interference_type = "constructive"
        elif interference_score < self.config["destructive_threshold"]:
            interference_type = "destructive"
        else:
            interference_type = "neutral"

        # 모순 감지 (destructive + 높은 진폭)
        is_contradiction = (
            interference_type == "destructive" and
            A1 > 0.5 and A2 > 0.5
        )

        logger.debug(
            f"[WAVE] A1={A1:.2f}, A2={A2:.2f}, "
            f"Δφ={phase_diff:.2f}, score={interference_score:.3f}, "
            f"type={interference_type}"
        )

        return InterferenceResult(
            interference_score=interference_score,
            interference_type=interference_type,
            resultant_amplitude=resultant_amplitude,
            phase_difference=phase_diff,
            is_contradiction=is_contradiction,
            details={
                "wave1_amplitude": A1,
                "wave2_amplitude": A2,
                "cos_phase_diff": cos_phase,
                "wave1_source": wave1.source_id,
                "wave2_source": wave2.source_id,
            }
        )

    def _calculate_phase(self, text: str) -> float:
        """
        텍스트에서 시간/순서 정보 추출하여 위상으로 변환

        Returns:
            위상 (라디안, -π/2 ~ π/2)
        """
        text_lower = text.lower()

        # Before 키워드 감지 → 음수 위상
        for kw in self.config["before_keywords"]:
            if kw.lower() in text_lower:
                return -math.pi / 2

        # After 키워드 감지 → 양수 위상
        for kw in self.config["after_keywords"]:
            if kw.lower() in text_lower:
                return math.pi / 2

        # 기본값 (현재/동시)
        return 0.0

    def _detect_polarity(self, text: str) -> int:
        """
        텍스트의 극성 감지

        Returns:
            1: 긍정, -1: 부정, 0: 중립
        """
        text_lower = text.lower()

        positive_count = sum(
            1 for kw in self.config["positive_keywords"]
            if kw.lower() in text_lower
        )
        negative_count = sum(
            1 for kw in self.config["negative_keywords"]
            if kw.lower() in text_lower
        )

        if positive_count > negative_count:
            return 1
        elif negative_count > positive_count:
            return -1
        return 0

    def analyze_claim_evidence_pair(
        self,
        claim_text: str,
        claim_confidence: float,
        evidence_type: str,
        evidence_strength: float,
        evidence_text: str = ""
    ) -> InterferenceResult:
        """
        Claim-Evidence 쌍의 간섭 분석

        Args:
            claim_text: Claim 텍스트
            claim_confidence: Claim 확신도
            evidence_type: 증거 타입
            evidence_strength: 증거 강도
            evidence_text: 증거 텍스트

        Returns:
            InterferenceResult
        """
        claim_wave = self.claim_to_wave(claim_text, claim_confidence)
        evidence_wave = self.evidence_to_wave(
            evidence_type, evidence_strength, evidence_text
        )
        return self.calculate_interference(claim_wave, evidence_wave)

    def analyze_claims_batch(
        self,
        claims: List[Tuple[str, float]],  # [(text, confidence), ...]
        evidences: List[Tuple[str, float, str]]  # [(type, strength, text), ...]
    ) -> Dict:
        """
        여러 Claim-Evidence 쌍을 일괄 분석

        Args:
            claims: Claim 목록
            evidences: Evidence 목록

        Returns:
            분석 결과 딕셔너리
        """
        results = []

        for claim_text, claim_conf in claims:
            claim_wave = self.claim_to_wave(claim_text, claim_conf)

            for ev_type, ev_strength, ev_text in evidences:
                evidence_wave = self.evidence_to_wave(ev_type, ev_strength, ev_text)
                result = self.calculate_interference(claim_wave, evidence_wave)
                results.append({
                    "claim": claim_text[:50],
                    "evidence_type": ev_type,
                    "result": result,
                })

        # 집계 통계
        if results:
            scores = [r["result"].interference_score for r in results]
            contradictions = sum(1 for r in results if r["result"].is_contradiction)

            return {
                "n_pairs": len(results),
                "avg_interference": np.mean(scores),
                "min_interference": min(scores),
                "max_interference": max(scores),
                "n_contradictions": contradictions,
                "constructive_ratio": sum(1 for r in results if r["result"].interference_type == "constructive") / len(results),
                "destructive_ratio": sum(1 for r in results if r["result"].interference_type == "destructive") / len(results),
                "details": results,
            }
        else:
            return {
                "n_pairs": 0,
                "avg_interference": 0.0,
                "n_contradictions": 0,
                "details": [],
            }

    def detect_contradictions(
        self,
        claims: List[Tuple[str, float]]
    ) -> List[Dict]:
        """
        Claim들 간의 모순 감지 (STEP 8 강화)

        Args:
            claims: [(text, confidence), ...]

        Returns:
            감지된 모순 목록
        """
        contradictions = []

        for i, (text1, conf1) in enumerate(claims):
            wave1 = self.claim_to_wave(text1, conf1)

            for j, (text2, conf2) in enumerate(claims):
                if i >= j:
                    continue

                wave2 = self.claim_to_wave(text2, conf2)
                result = self.calculate_interference(wave1, wave2)

                if result.is_contradiction:
                    contradictions.append({
                        "claim1_index": i,
                        "claim1_text": text1[:100],
                        "claim2_index": j,
                        "claim2_text": text2[:100],
                        "interference_score": result.interference_score,
                        "phase_difference": result.phase_difference,
                        "severity": self._calculate_contradiction_severity(result),
                    })

        logger.info(f"[WAVE] {len(contradictions)}개 모순 감지")
        return contradictions

    def _calculate_contradiction_severity(
        self,
        result: InterferenceResult
    ) -> str:
        """모순 심각도 계산"""
        score = abs(result.interference_score)
        amplitude = result.resultant_amplitude

        if score > 0.7 and amplitude > 0.8:
            return "critical"
        elif score > 0.5 and amplitude > 0.6:
            return "high"
        elif score > 0.3:
            return "medium"
        else:
            return "low"

    def get_interference_factor(
        self,
        claim_text: str,
        claim_confidence: float,
        evidences: List[Dict]
    ) -> float:
        """
        Claim 검증에 사용할 간섭 계수 반환

        STEP 5 Likelihood에 곱할 계수

        Args:
            claim_text: Claim 텍스트
            claim_confidence: Claim 확신도
            evidences: Evidence 목록 [{"type": str, "strength": float, "text": str}, ...]

        Returns:
            간섭 계수 (0.0 ~ 2.0)
            - < 1.0: 상쇄 (패널티)
            - = 1.0: 중립
            - > 1.0: 강화 (보너스)
        """
        if not evidences:
            return 1.0

        claim_wave = self.claim_to_wave(claim_text, claim_confidence)

        interference_scores = []
        for ev in evidences:
            ev_wave = self.evidence_to_wave(
                ev.get("type", "indirect_reference"),
                ev.get("strength", 0.5),
                ev.get("text", "")
            )
            result = self.calculate_interference(claim_wave, ev_wave)
            interference_scores.append(result.interference_score)

        # 평균 간섭 점수
        avg_score = np.mean(interference_scores)

        # 간섭 계수로 변환 (0.0 ~ 2.0)
        # score -1 → factor 0.5
        # score 0 → factor 1.0
        # score 1 → factor 1.5
        factor = 1.0 + avg_score * 0.5

        return max(0.0, min(2.0, factor))


# 싱글톤 인스턴스
_wave_detector: Optional[WaveInterferenceDetector] = None


def get_wave_interference_detector(
    config: Optional[Dict] = None
) -> WaveInterferenceDetector:
    """Wave Interference Detector 싱글톤 반환"""
    global _wave_detector
    if _wave_detector is None:
        _wave_detector = WaveInterferenceDetector(config)
    return _wave_detector
