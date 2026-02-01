"""
퍼지 확신도 분석 시스템

Cortex Phase 9: Hallucination Detection System
LLM 응답의 확신도 표현을 퍼지 로직으로 분석합니다.

핵심 기능:
- 확신도 키워드 감지 (very_high, high, medium, low)
- 퍼지 멤버십 함수 적용
- Claim Extractor와 통합하여 확신도 점수 산출
- 모호한 표현 감지 및 경고
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .claim_extractor import Claim, ClaimExtractor
from .grounding_scorer import GroundingScorer

# Phase 9.7: 중앙 상수 통일
from .hallucination_constants import CONFIDENCE_SCORES as CENTRAL_CONFIDENCE_SCORES


class FuzzyClaimAnalyzer:
    """
    퍼지 확신도 분석 클래스

    LLM 응답의 확신도 표현을 퍼지 로직으로 분석하여
    할루시네이션 위험을 정량화합니다.
    """

    # Phase 9.7: 중앙 상수 참조 (hallucination_constants.py)
    CONFIDENCE_SCORES = CENTRAL_CONFIDENCE_SCORES

    # Claim 타입별 특화 확신도 패턴 (High-3: Claim-specific analysis)
    CLAIM_TYPE_CONFIDENCE_PATTERNS = {
        "implementation_complete": {
            "very_high": [
                # 파일 경로 포함한 완료 표현
                r"([a-zA-Z0-9_/\\.]+\.(py|js|ts|java|cpp|c|go|rs|rb|php|html|css)).*?(구현|작성|생성|추가).*?(했습니다|완료|되었습니다)",
                r"([a-zA-Z0-9_/\\.]+\.(py|js|ts|java|cpp|c|go|rs|rb|php|html|css)).*?(implement|creat|writ|add).*?(ed|completed|done)",
                # 명시적 완료 표현
                r"(완전히|성공적으로|정상적으로)\s*(구현|작성|완료).*?(했습니다|되었습니다)",
                r"(completely|successfully|properly)\s*(implement|creat|complet).*?(ed|done)",
            ],
            "high": [
                # 부분 완료
                r"(거의|대부분)\s*(구현|작성|완료)",
                r"(almost|mostly)\s*(implement|creat|complet)",
                # 진행률 표현
                r"(90%|95%|99%)\s*(구현|완료)",
                r"(90%|95%|99%)\s*(implement|complet)",
            ],
            "medium": [
                # 진행 중
                r"(구현\s*중|작성\s*중|개발\s*중)",
                r"(implementing|creating|developing|in\s*progress)",
            ],
        },
        "reference_existing": {
            "very_high": [
                # 파일 경로 포함한 기존 참조
                r"([a-zA-Z0-9_/\\.]+\.(py|js|ts|java|cpp|c|go|rs|rb|php|html|css)).*?(이미|기존).*?(존재|있습니다|사용)",
                r"([a-zA-Z0-9_/\\.]+\.(py|js|ts|java|cpp|c|go|rs|rb|php|html|css)).*?(already|existing).*?(exists|is|using)",
                # 명시적 존재 확인
                r"(확실히|명백히)\s*(존재|있습니다|기존)",
                r"(definitely|clearly)\s*(exists|is|already)",
            ],
            "high": [
                # 일반 기존 참조
                r"(이미|기존|이전에).*?(구현|작성|존재)",
                r"(already|existing|previously).*?(implement|creat|exists)",
            ],
            "medium": [
                # 추정 표현
                r"(기존으로\s*보임|있는\s*것\s*같)",
                r"(seems\s*to\s*exist|appears\s*to\s*be)",
            ],
        },
        "modification": {
            "very_high": [
                # 라인 번호 포함한 수정
                r"(line|라인|줄)\s*\d+.*?(수정|변경|업데이트).*?(했습니다|완료)",
                r"(line)\s*\d+.*?(modif|chang|updat).*?(ied|ed|done)",
                # 파일 경로 포함한 수정
                r"([a-zA-Z0-9_/\\.]+\.(py|js|ts|java|cpp|c|go|rs|rb|php|html|css)).*?(수정|변경).*?(했습니다|완료)",
                r"([a-zA-Z0-9_/\\.]+\.(py|js|ts|java|cpp|c|go|rs|rb|php|html|css)).*?(modif|chang).*?(ied|ed|done)",
            ],
            "high": [
                # 일반 수정 완료
                r"(수정|변경|업데이트).*?(했습니다|완료|되었습니다)",
                r"(modif|chang|updat).*?(ied|ed|done|completed)",
            ],
        },
        "verification": {
            "very_high": [
                # 테스트 통과/성공
                r"(테스트|검증).*?(통과|성공|완료)",
                r"(test|verification).*?(passed|success|completed)",
                # 구체적 검증 결과
                r"(\d+/\d+|100%).*?(테스트|검증).*?(통과|성공)",
                r"(\d+/\d+|100%).*?(test).*?(passed|success)",
            ],
            "high": [
                # 일반 검증
                r"(정상|올바르게).*?(작동|동작|실행)",
                r"(properly|correctly).*?(work|run|execut)",
            ],
        },
        "bug_fix": {
            "very_high": [
                # 버그 수정 완료
                r"(버그|오류|에러).*?(수정|해결|고침).*?(했습니다|완료)",
                r"(bug|error|issue).*?(fix|resolv|correct).*?(ed|done)",
                # 동작 확인
                r"(정상|올바르게)\s*작동.*?(수정|변경)",
                r"(properly|correctly)\s*work.*?(fix|modif)",
            ],
            "high": [
                # 수정 시도
                r"(버그|오류).*?(수정|해결)",
                r"(bug|error).*?(fix|resolv)",
            ],
        },
        "extension": {
            "high": [
                # 확장 완료 (기본 high)
                r"(확장|통합|연동).*?(했습니다|완료|되었습니다)",
                r"(extend|integrat|connect).*?(ed|done|completed)",
            ],
            "medium": [
                # 확장 예정
                r"(확장\s*예정|통합\s*예정)",
                r"(will\s*extend|planning\s*to\s*integrat)",
            ],
        },
    }

    # 확신도 키워드 패턴 (Korean + English) - 일반 fallback 패턴
    CONFIDENCE_PATTERNS = {
        "very_high": [
            # Korean
            r"(반드시|확실히|분명히|명백히|틀림없이)",
            r"(100%|확실|완전)",
            r"(보장|약속|단언)",
            r"(완료\s*했|구현\s*했|작성\s*했|추가\s*했|수정\s*했)",
            r"(존재\s*합니|있\s*습니다|되\s*었\s*습니다)",
            # English
            r"(definitely|certainly|clearly|obviously|undoubtedly)",
            r"(100%|sure|complete|absolute)",
            r"(guarantee|promise|assert)",
            r"(completed|implemented|created|added|modified)",
            r"(exists|is|has\s*been|was)",
        ],
        "high": [
            # Korean
            r"(거의|대부분|높은\s*확률)",
            r"(일반적으로|보통|주로)",
            # English
            r"(likely|probable|almost|mostly|highly\s*likely)",
            r"(generally|usually|typically)",
            r"(high\s*probability|confident)",
        ],
        "medium": [
            # Korean
            r"(가능성|추측|예상|생각)",
            r"(\~일\s*수\s*있|것으로\s*보임)",
            r"(을\s*수도\s*있|할\s*수도\s*있|될\s*수도\s*있|수도\s*있)",  # "수도 있습니다" 패턴 개선
            r"(것\s*같|인\s*것\s*같|는\s*것\s*같|을\s*것\s*같|할\s*것\s*같)",  # "것 같습니다" 패턴 추가
            r"(지도\s*모름|알\s*수\s*없)",
            r"(아마도|어쩌면|혹시)",
            # English
            r"(maybe|perhaps|possibly|might|could)",
            r"(may\s*be|seems|appears|looks\s*like)",
            r"(potential|assume|expect)",
        ],
        "low": [
            # Korean
            r"(아닐\s*수도|불확실|모호|확신\s*없)",
            r"(확실하지\s*않|확실치\s*않|잘\s*모르)",
            r"(의심|회의적)",
            # English
            r"(unlikely|uncertain|unsure|doubtful)",
            r"(not\s*sure|unclear|ambiguous)",
            r"(skeptical|questionable)",
        ],
    }

    # 모호한 표현 패턴 (Korean + English)
    VAGUE_PATTERNS = [
        # Korean
        r"(아마|어쩌면|혹시|만약)",
        r"(일\s*듯|것\s*같|로\s*보임)",  # "것 같" 패턴 추가
        r"(수도\s*있|지도\s*모름)",  # "수도 있" 패턴 추가
        r"(대충|대략|약간|조금)",
        # English
        r"(might|could|possibly|probably)",
        r"(maybe|perhaps|sort\s*of|kind\s*of)",
        r"(roughly|approximately|somewhat|slightly)",
    ]

    def __init__(self):
        """Fuzzy Claim Analyzer 초기화"""
        # ClaimExtractor 인스턴스 생성 (Claim 추출용)
        self.claim_extractor = ClaimExtractor()

        # 일반 패턴 컴파일 (성능 최적화)
        self._compiled_confidence = {}
        for level, patterns in self.CONFIDENCE_PATTERNS.items():
            self._compiled_confidence[level] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

        # Claim 타입별 패턴 컴파일 (High-3: Claim-specific analysis)
        self._compiled_claim_type_confidence = {}
        for claim_type, level_patterns in self.CLAIM_TYPE_CONFIDENCE_PATTERNS.items():
            self._compiled_claim_type_confidence[claim_type] = {}
            for level, patterns in level_patterns.items():
                self._compiled_claim_type_confidence[claim_type][level] = [
                    re.compile(pattern, re.IGNORECASE) for pattern in patterns
                ]

        self._compiled_vague = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.VAGUE_PATTERNS
        ]

    def analyze_response(self, response_text: str) -> Dict:
        """
        LLM 응답 전체에 대한 퍼지 확신도 분석

        Args:
            response_text: LLM 응답 텍스트

        Returns:
            분석 결과 딕셔너리
        """
        # Claim 추출
        claims = self.claim_extractor.extract_claims(response_text)

        # 각 Claim의 확신도 분석
        claim_analyses = []
        for claim in claims:
            analysis = self.analyze_claim(claim, response_text)
            claim_analyses.append(analysis)

        # 전체 응답의 평균 확신도 계산
        if claim_analyses:
            avg_confidence = sum(a["fuzzy_score"] for a in claim_analyses) / len(claim_analyses)
        else:
            # Claim이 없는 경우 전체 텍스트 확신도 분석
            text_confidence = self._analyze_text_confidence(response_text)
            # BUG FIX (Phase 9.5): _analyze_text_confidence가 0.0 반환 시 그대로 사용
            # (0.0 → "none" 레벨로 매핑됨)
            avg_confidence = text_confidence

        # 모호한 표현 검사
        vague_expressions = self._detect_vague_expressions(response_text)

        # 위험도 계산
        risk_level = self._calculate_risk_level(avg_confidence, len(vague_expressions))

        # 평균 확신도를 레벨로 변환
        overall_confidence_level = self._score_to_level(avg_confidence)

        return {
            "total_claims": len(claims),
            "claim_analyses": claim_analyses,
            "average_confidence": round(avg_confidence, 3),
            "overall_confidence_level": overall_confidence_level,
            "vague_expression_count": len(vague_expressions),
            "vague_expressions": vague_expressions,
            "risk_level": risk_level,
            "interpretation": self._interpret_confidence(avg_confidence, risk_level),
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_claim(self, claim: Claim, full_text: str) -> Dict:
        """
        단일 Claim의 확신도 분석

        Args:
            claim: 분석할 Claim
            full_text: 전체 텍스트 (컨텍스트 확인용)

        Returns:
            Claim 확신도 분석 결과
        """
        # Claim 전후 컨텍스트 추출 (±50자)
        context_start = max(0, claim.start - 50)
        context_end = min(len(full_text), claim.end + 50)
        context = full_text[context_start:context_end]

        # 확신도 레벨 감지 (High-3: Claim 타입 전달)
        confidence_level = self._detect_confidence_level(context, claim_type=claim.claim_type)

        # 퍼지 점수 적용
        fuzzy_score = self.CONFIDENCE_SCORES.get(confidence_level, 0.0)

        # 모호한 표현 검사 (Claim 텍스트 내)
        has_vague = self._has_vague_expression(claim.text)

        # 모호한 표현이 있으면 점수 하락
        if has_vague:
            fuzzy_score *= 0.7  # 30% 감점

        return {
            "claim": claim,
            "confidence_level": confidence_level,
            "fuzzy_score": round(fuzzy_score, 3),
            "has_vague_expression": has_vague,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }

    def _detect_confidence_level(self, text: str, claim_type: Optional[str] = None) -> str:
        """
        텍스트에서 확신도 레벨 감지 (High-3: Claim-specific analysis)

        모든 매칭된 패턴을 찾아 **가장 낮은 확신도**를 반환합니다.
        이는 확신도 수정 표현(예: "거의", "아마도")이 완료 표현(예: "구현했습니다")보다
        우선하도록 하는 보수적 접근입니다.

        High-3 개선: Claim 타입별 특화 패턴을 우선 매칭합니다.
        - 타입별 패턴 매칭 우선
        - 매칭 실패 시 일반 패턴으로 fallback

        Phase 0 추가: 부정/불확실 표현을 먼저 체크하여 타입별 패턴보다 우선합니다.

        Args:
            text: 분석할 텍스트
            claim_type: Claim 타입 (선택적, 있으면 타입별 패턴 사용)

        Returns:
            확신도 레벨 (very_high, high, medium, low, none)
        """
        # 모든 매칭된 레벨 수집
        matched_levels = []
        has_negative_expression = False

        # Phase 0: 부정/불확실 표현 체크 (HIGH #2: 부정 문맥 윈도우 확장)
        # low: 확실하지 않음, 모호함
        # medium: 것 같다, 수도 있다, 아마도

        # HIGH #2: 부정 표현 강화 검사
        negation_patterns = [
            r"(않|안|못|없)[가-힣]{0,3}(했|함|됨|됐|어요|습니다)",  # "하지 않았습니다", "못했어요"
            r"실패",
            r"미구현",
            r"안\s*됨",
            r"안\s*되",
            r"못\s*해",
        ]

        # 전체 텍스트에서 부정 표현 검색
        for neg_pattern in negation_patterns:
            if re.search(neg_pattern, text):
                has_negative_expression = True
                matched_levels.append("low")  # 부정 표현 발견 시 confidence를 low로 강제
                break

        # 기존 low/medium 패턴 체크
        for check_level in ["low", "medium"]:
            patterns = self._compiled_confidence.get(check_level, [])
            for pattern in patterns:
                if pattern.search(text):
                    if check_level == "low":
                        has_negative_expression = True
                    matched_levels.append(check_level)
                    break

        # Phase 1: Claim 타입별 특화 패턴 우선 매칭 (High-3)
        # 타입별 패턴은 구체적이므로 첫 번째 매칭만 사용 (우선순위: very_high → low)
        type_matched = False
        if claim_type and claim_type in self._compiled_claim_type_confidence:
            type_patterns = self._compiled_claim_type_confidence[claim_type]
            for level in ["very_high", "high", "medium", "low"]:
                patterns = type_patterns.get(level, [])
                for pattern in patterns:
                    if pattern.search(text):
                        matched_levels.append(level)
                        type_matched = True
                        break
                if type_matched:
                    break  # 첫 번째 타입별 매칭에서 중단

        # Phase 2: 일반 패턴 fallback (타입별 패턴이 없거나 매칭 안 된 경우)
        if not type_matched:
            for level in ["very_high", "high", "medium", "low"]:
                patterns = self._compiled_confidence.get(level, [])
                for pattern in patterns:
                    if pattern.search(text):
                        matched_levels.append(level)
                        break  # 같은 레벨에서 중복 매칭 방지

        if not matched_levels:
            return "none"  # 확신도 표현 없음

        # 가장 낮은 확신도 반환 (low < medium < high < very_high)
        level_priority = ["low", "medium", "high", "very_high"]
        for level in level_priority:
            if level in matched_levels:
                return level

        return "none"

    def _analyze_text_confidence(self, text: str) -> float:
        """
        전체 텍스트의 평균 확신도 계산
        (Claim이 없는 응답의 경우)

        Args:
            text: 분석할 텍스트

        Returns:
            평균 확신도 점수 (0.0-1.0)
        """
        # 텍스트를 문장 단위로 분할
        sentences = re.split(r"[.!?]\s+", text)

        confidence_scores = []
        for sentence in sentences:
            if not sentence.strip():
                continue

            level = self._detect_confidence_level(sentence)
            score = self.CONFIDENCE_SCORES.get(level, 0.0)

            # "none"이 아닌 경우만 추가 (확신도 표현이 있는 경우)
            if level != "none":
                confidence_scores.append(score)

        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            # MEDIUM #4: 확신도 표현이 전혀 없으면 neutral 값 (0.5)
            # 0.0은 너무 보수적이며, "완전히 틀렸다"는 의미로 오해될 수 있음
            # "확신도 표현 없음" = "중립" = 0.5가 더 합리적
            return 0.5

    def _detect_vague_expressions(self, text: str) -> List[Dict]:
        """
        모호한 표현 감지

        Args:
            text: 분석할 텍스트

        Returns:
            모호한 표현 목록
        """
        vague_expressions = []

        for pattern in self._compiled_vague:
            matches = pattern.finditer(text)
            for match in matches:
                vague_expressions.append(
                    {
                        "text": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                        "pattern": pattern.pattern,
                    }
                )

        return vague_expressions

    def _has_vague_expression(self, text: str) -> bool:
        """
        텍스트에 모호한 표현이 있는지 확인

        Args:
            text: 확인할 텍스트

        Returns:
            모호한 표현 존재 여부
        """
        for pattern in self._compiled_vague:
            if pattern.search(text):
                return True
        return False

    def _calculate_risk_level(self, avg_confidence: float, vague_count: int) -> str:
        """
        할루시네이션 위험도 계산

        Args:
            avg_confidence: 평균 확신도
            vague_count: 모호한 표현 개수

        Returns:
            위험도 (low, medium, high, critical)
        """
        # 기본 위험도 (확신도 기반)
        if avg_confidence >= 0.8:
            base_risk = "low"
        elif avg_confidence >= 0.5:
            base_risk = "medium"
        elif avg_confidence >= 0.3:
            base_risk = "high"
        else:
            base_risk = "critical"

        # 모호한 표현 개수로 위험도 상향 조정
        if vague_count >= 5:
            if base_risk == "low":
                return "medium"
            elif base_risk == "medium":
                return "high"
            elif base_risk == "high":
                return "critical"
        elif vague_count >= 3:
            if base_risk == "low":
                return "medium"

        return base_risk

    def _interpret_confidence(self, avg_confidence: float, risk_level: str) -> str:
        """
        확신도 및 위험도 해석

        Args:
            avg_confidence: 평균 확신도
            risk_level: 위험도

        Returns:
            해석 문구
        """
        interpretations = {
            "low": "낮은 할루시네이션 위험. 응답이 명확한 확신도 표현을 포함합니다.",
            "medium": "중간 수준의 할루시네이션 위험. 일부 모호한 표현이 포함되어 있습니다.",
            "high": "높은 할루시네이션 위험. 확신도가 낮고 모호한 표현이 많습니다.",
            "critical": "매우 높은 할루시네이션 위험. 대부분의 주장이 불확실하거나 근거가 부족합니다.",
        }

        return interpretations.get(risk_level, "평가 불가")

    def compare_responses(self, responses: List[str]) -> Dict:
        """
        여러 응답의 확신도 비교

        Args:
            responses: 응답 텍스트 목록

        Returns:
            비교 분석 결과
        """
        analyses = [self.analyze_response(r) for r in responses]

        confidences = [a["average_confidence"] for a in analyses]

        return {
            "count": len(responses),
            "average_confidence": round(sum(confidences) / len(confidences), 3),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "risk_distribution": self._get_risk_distribution(analyses),
            "best_response_index": confidences.index(max(confidences)),
            "worst_response_index": confidences.index(min(confidences)),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_risk_distribution(self, analyses: List[Dict]) -> Dict:
        """
        위험도 분포 계산

        Args:
            analyses: 분석 결과 목록

        Returns:
            위험도별 개수
        """
        distribution = {}
        for analysis in analyses:
            risk_level = analysis["risk_level"]
            distribution[risk_level] = distribution.get(risk_level, 0) + 1

        return distribution

    def get_confidence_trend(self, analyses: List[Dict]) -> Dict:
        """
        확신도 추이 분석

        Args:
            analyses: 시간순 분석 결과 목록

        Returns:
            추이 분석 결과
        """
        if len(analyses) < 2:
            return {"error": "insufficient_data"}

        confidences = [a["average_confidence"] for a in analyses]

        # 추세 계산 (간단한 선형 회귀)
        n = len(confidences)
        x = list(range(n))
        y = confidences

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        # 추세 판단
        if slope > 0.1:
            trend = "improving_significantly"
        elif slope > 0.02:
            trend = "improving"
        elif slope > -0.02:
            trend = "stable"
        elif slope > -0.1:
            trend = "declining"
        else:
            trend = "declining_significantly"

        return {
            "count": n,
            "slope": round(slope, 4),
            "trend": trend,
            "first_confidence": confidences[0],
            "last_confidence": confidences[-1],
            "change": round(confidences[-1] - confidences[0], 3),
            "average": round(sum(confidences) / n, 3),
        }

    # =========================================================================
    # Phase 5: Fuzzy Logic Conservatism (Conservative Min-Confidence Rule)
    # =========================================================================

    def assess_claim(
        self,
        claim: Claim,
        full_text: str,
        evidence_list: List[Dict],
        project_id: str,
        referenced_contexts: Optional[List[str]] = None,
        project_path: str = ".",  # Phase 9.5: GroundingScorer 인자 추가
    ) -> Dict:
        """
        Conservative Claim Assessment (Phase 5)

        Linguistic confidence와 Evidence confidence를 모두 고려하여
        보수적으로 최종 신뢰도를 결정합니다.

        핵심 원칙: min-confidence rule
        - linguistic confidence가 높아도 evidence가 부족하면 downgrade
        - evidence가 충분해도 linguistic confidence가 낮으면 downgrade

        Args:
            claim: 평가할 Claim
            full_text: 전체 텍스트
            evidence_list: Evidence 목록 (grounding scorer용)
            project_id: 프로젝트 ID
            referenced_contexts: 참조된 Context 목록 (선택)

        Returns:
            {
                "linguistic_confidence": float,  # Fuzzy 분석 점수
                "evidence_confidence": float,    # Grounding 점수
                "final_confidence": float,       # min(linguistic, evidence)
                "decision": str,                 # WARN / CAUTION / ACCEPT
                "details": Dict                  # 상세 분석 정보
            }
        """
        # 1. Linguistic Confidence (Fuzzy Analysis)
        fuzzy_result = self.analyze_claim(claim, full_text)
        linguistic_confidence = fuzzy_result["fuzzy_score"]

        # 2. Evidence Confidence (Grounding Score)
        grounding_scorer = GroundingScorer(
            project_id=project_id,
            project_path=project_path,  # Phase 9.5: 누락된 인자 추가
            reference_history=None
        )

        # GroundingScorer는 normalized_score (0-100) 반환하므로 0-1로 정규화
        grounding_result = grounding_scorer.calculate_score(
            response_text=full_text, claims=[claim], referenced_contexts=referenced_contexts or []
        )
        evidence_confidence = grounding_result["normalized_score"] / 100.0

        # 3. Conservative Rule: Take MINIMUM
        final_confidence = min(linguistic_confidence, evidence_confidence)

        # 4. Decision Making (Phase 9.5: threshold 조정)
        if final_confidence < 0.3:  # Phase 9.5: 0.5 → 0.3
            decision = "WARN"
            decision_explanation = "Low confidence: Hallucination risk detected"
        elif final_confidence < 0.5:  # Phase 9.5: 0.7 → 0.5
            decision = "CAUTION"
            decision_explanation = "Medium confidence: Review recommended"
        else:  # >= 0.5 (Phase 9.5: 0.7 → 0.5)
            decision = "ACCEPT"
            decision_explanation = "High confidence: Claim appears reliable"

        return {
            "claim_text": claim.text,
            "claim_type": claim.claim_type,
            "linguistic_confidence": round(linguistic_confidence, 3),
            "evidence_confidence": round(evidence_confidence, 3),
            "final_confidence": round(final_confidence, 3),
            "decision": decision,
            "decision_explanation": decision_explanation,
            "details": {
                "fuzzy_analysis": fuzzy_result,
                "grounding_analysis": grounding_result,
                "conservative_rule_applied": True,
                "timestamp": datetime.now().isoformat(),
            },
        }

    def batch_assess_claims(
        self,
        claims: List[Claim],
        full_text: str,
        evidence_map: Dict[str, List[Dict]],
        project_id: str,
        referenced_contexts: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        여러 Claim에 대한 일괄 평가

        Args:
            claims: Claim 목록
            full_text: 전체 텍스트
            evidence_map: {claim.text: evidence_list} 매핑
            project_id: 프로젝트 ID
            referenced_contexts: 참조된 Context 목록

        Returns:
            평가 결과 목록
        """
        results = []
        for claim in claims:
            evidence_list = evidence_map.get(claim.text, [])
            result = self.assess_claim(
                claim, full_text, evidence_list, project_id, referenced_contexts
            )
            results.append(result)

        return results

    def get_assessment_summary(self, assessments: List[Dict]) -> Dict:
        """
        평가 결과 요약

        Args:
            assessments: assess_claim() 결과 목록

        Returns:
            요약 통계
        """
        if not assessments:
            return {"error": "no_assessments_provided"}

        decision_counts = {"WARN": 0, "CAUTION": 0, "ACCEPT": 0}
        for assessment in assessments:
            decision = assessment["decision"]
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

        avg_linguistic = sum(a["linguistic_confidence"] for a in assessments) / len(assessments)
        avg_evidence = sum(a["evidence_confidence"] for a in assessments) / len(assessments)
        avg_final = sum(a["final_confidence"] for a in assessments) / len(assessments)

        return {
            "total_claims": len(assessments),
            "decision_distribution": decision_counts,
            "avg_linguistic_confidence": round(avg_linguistic, 3),
            "avg_evidence_confidence": round(avg_evidence, 3),
            "avg_final_confidence": round(avg_final, 3),
            "conservative_downgrade_rate": round(
                (avg_linguistic - avg_final) / max(avg_linguistic, 0.001), 3
            ),
        }

    def _score_to_level(self, score: float) -> str:
        """
        숫자 점수를 확신도 레벨로 변환

        Args:
            score: 0.0-1.0 범위의 확신도 점수

        Returns:
            확신도 레벨 (very_high, high, medium, low, none)
        """
        if score >= 0.9:
            return "very_high"
        elif score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score > 0.1:
            return "low"
        else:
            return "none"
