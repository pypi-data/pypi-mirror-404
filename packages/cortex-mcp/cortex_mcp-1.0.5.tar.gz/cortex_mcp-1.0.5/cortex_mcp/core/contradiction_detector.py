"""
자기 모순 감지 시스템

Cortex Phase 9: Hallucination Detection System
LLM 응답 내부의 논리적 모순을 감지합니다.

핵심 기능:
- Claim 간 모순 검사 (직접 모순, 논리적 불일치)
- 시간 순서 모순 감지 (before/after)
- 수치 모순 감지 (더 크다/작다)
- 부정 표현 모순 감지 (긍정 vs 부정)
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .claim_extractor import Claim, ClaimExtractor


class ContradictionDetector:
    """
    자기 모순 감지 클래스

    LLM 응답 내부에서 논리적으로 충돌하는 주장을 감지합니다.
    """

    # 부정 표현 패턴
    NEGATION_PATTERNS = [
        r"(않|안|못|없|말|금지)",
        r"(not|no|never|none|neither)",
        r"(아니|절대|전혀)",
    ]

    # 시간 순서 패턴
    TEMPORAL_PATTERNS = {
        "before": [r"(이전|먼저|앞서|전에)", r"(before|prior|earlier)"],
        "after": [r"(이후|나중|뒤|후에)", r"(after|later|following)"],
        "during": [r"(동안|중|사이)", r"(during|while|meanwhile)"],
    }

    # 비교 표현 패턴 (어형 변화 포함, 부분 매칭 방지)
    COMPARISON_PATTERNS = {
        "greater": [r"(많[은이]?|큰|높[은이]?|증가|좋[은아았]|빠[른르릅]|빨[라랐]|향상|개선)", r"(more|greater|higher|larger|increase|better|faster|improve)"],
        "lesser": [r"(적[은이]?|작[은이]?|낮[은아았]|감소|나쁜|나빠|나빴|느린|느려|느렸|느립|악화|저하)", r"(less|smaller|lower|fewer|decrease|worse|slower|degrade)"],
        "equal": [r"(같|동일|유사|비슷)", r"(same|equal|similar|identical)"],
    }

    def __init__(self):
        """Contradiction Detector 초기화"""
        # ClaimExtractor 인스턴스 생성
        self.claim_extractor = ClaimExtractor()

        # 패턴 컴파일
        self._compiled_negation = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.NEGATION_PATTERNS
        ]

        self._compiled_temporal = {}
        for temp_type, patterns in self.TEMPORAL_PATTERNS.items():
            self._compiled_temporal[temp_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

        self._compiled_comparison = {}
        for comp_type, patterns in self.COMPARISON_PATTERNS.items():
            self._compiled_comparison[comp_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def detect_contradictions(self, response_text: str) -> Dict:
        """
        LLM 응답에서 모순 감지

        Args:
            response_text: LLM 응답 텍스트

        Returns:
            모순 감지 결과
        """
        # Claim 추출 (ClaimExtractor 사용)
        claims = self.claim_extractor.extract_claims(response_text)

        # Fallback: ClaimExtractor가 추출하지 못한 문장도 Claim으로 처리
        # (부정 문장, 모순 문장 등을 포함하기 위함)
        sentences = self._split_sentences(response_text)
        for sentence in sentences:
            # 이미 추출된 Claim에 포함되지 않은 문장만 추가
            if sentence.strip() and not any(claim.text in sentence for claim in claims):
                claims.append(
                    Claim(
                        claim_type="general_statement",
                        text=sentence.strip(),
                        start=response_text.find(sentence),
                        end=response_text.find(sentence) + len(sentence),
                        confidence=0.8,
                    )
                )

        # Claim 쌍 모든 조합 검사
        contradictions = []
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                claim1 = claims[i]
                claim2 = claims[j]

                # 모순 검사
                contradiction = self._check_contradiction(claim1, claim2, response_text)
                if contradiction:
                    contradictions.append(contradiction)

        # 모순 심각도 계산
        severity = self._calculate_severity(contradictions)

        return {
            "total_claims": len(claims),
            "contradictions_found": len(contradictions),
            "contradictions": contradictions,
            "severity": severity,
            "has_critical_contradictions": severity == "critical",
            "interpretation": self._interpret_contradictions(len(contradictions), severity),
            "timestamp": datetime.now().isoformat(),
        }

    def _check_contradiction(self, claim1: Claim, claim2: Claim, full_text: str) -> Optional[Dict]:
        """
        두 Claim 간 모순 검사

        Args:
            claim1: 첫 번째 Claim
            claim2: 두 번째 Claim
            full_text: 전체 텍스트

        Returns:
            모순 정보 (없으면 None)
        """
        # 1. 직접 부정 모순 (A이다 vs A가 아니다)
        direct_negation = self._check_direct_negation(claim1, claim2)
        if direct_negation:
            return {
                "type": "direct_negation",
                "claim1": claim1,
                "claim2": claim2,
                "severity": "critical",
                "description": "직접적인 긍정-부정 모순 발견",
                "evidence": direct_negation,
            }

        # 2. 시간 순서 모순 (A가 B 이전 vs A가 B 이후)
        temporal_contradiction = self._check_temporal_contradiction(claim1, claim2)
        if temporal_contradiction:
            return {
                "type": "temporal",
                "claim1": claim1,
                "claim2": claim2,
                "severity": "high",
                "description": "시간 순서 모순 발견",
                "evidence": temporal_contradiction,
            }

        # 3. 수치/비교 모순 (A > B vs A < B)
        comparison_contradiction = self._check_comparison_contradiction(claim1, claim2)
        if comparison_contradiction:
            return {
                "type": "comparison",
                "claim1": claim1,
                "claim2": claim2,
                "severity": "high",
                "description": "비교/수치 모순 발견",
                "evidence": comparison_contradiction,
            }

        # 4. 타입 모순 (구현 완료 vs 기존 참조)
        type_contradiction = self._check_type_contradiction(claim1, claim2)
        if type_contradiction:
            return {
                "type": "claim_type_mismatch",
                "claim1": claim1,
                "claim2": claim2,
                "severity": "medium",
                "description": "Claim 타입 불일치 (구현 완료 vs 기존 참조)",
                "evidence": type_contradiction,
            }

        return None

    def _check_direct_negation(self, claim1: Claim, claim2: Claim) -> Optional[str]:
        """
        직접 부정 모순 검사

        Args:
            claim1: 첫 번째 Claim
            claim2: 두 번째 Claim

        Returns:
            모순 증거 (없으면 None)
        """
        # Claim1에 부정이 없고, Claim2에 부정이 있는지
        text1 = claim1.text
        text2 = claim2.text

        has_negation1 = any(pattern.search(text1) for pattern in self._compiled_negation)
        has_negation2 = any(pattern.search(text2) for pattern in self._compiled_negation)

        # 하나는 긍정, 하나는 부정
        if has_negation1 != has_negation2:
            # 키워드 겹침 확인 (같은 내용을 다루는지)
            # 한국어 토큰 추출 개선: 조사 제거
            keywords1 = set(self._extract_korean_tokens(text1.lower()))
            keywords2 = set(self._extract_korean_tokens(text2.lower()))
            overlap = keywords1 & keywords2

            if len(overlap) >= 1:  # 1개 이상 키워드 겹침으로 완화 (한국어 대응)
                return f"공통 키워드 {len(overlap)}개, 한쪽은 긍정, 한쪽은 부정"

        return None

    def _extract_korean_tokens(self, text: str) -> List[str]:
        """
        한국어 토큰 추출 (조사 제거)

        Args:
            text: 분석할 텍스트

        Returns:
            핵심 토큰 목록
        """
        # 기본 단어 추출
        words = re.findall(r"\b\w{2,}\b", text)

        # 한국어 조사 패턴 (종성으로 끝나는 일반적인 조사)
        josa_patterns = [
            r"(이|가|을|를|의|에|에서|으로|로|와|과|도|만|부터|까지|한테|께|보다)$",
            r"(합니다|했습니다|됩니다|되었습니다|입니다|있습니다)$",
            r"(하지|하는|되지|되는|않습니다)$",
        ]

        tokens = []
        for word in words:
            # 조사 제거
            clean_word = word
            for pattern in josa_patterns:
                clean_word = re.sub(pattern, "", clean_word)

            # 3글자 이상만 유지
            if len(clean_word) >= 2:
                tokens.append(clean_word)

        return tokens

    def _split_sentences(self, text: str) -> List[str]:
        """
        텍스트를 문장 단위로 분리 (한국어/영어 지원)

        Args:
            text: 분리할 텍스트

        Returns:
            문장 목록
        """
        # 다국어 문장 종결 부호로 분리
        # . ! ? 。 ！ ？ (한국어, 영어, 일본어, 중국어)
        sentences = re.split(r"[.!?。！？]\s*", text)

        # 빈 문자열 제거 및 정리
        return [s.strip() for s in sentences if s.strip()]

    def _extract_file_references(self, text: str) -> List[str]:
        """
        텍스트에서 파일명 추출

        Args:
            text: 분석할 텍스트

        Returns:
            추출된 파일명 목록
        """
        # 파일명 패턴 (확장자가 있는 경우)
        file_pattern = r"(\w+\.\w+)"
        files = re.findall(file_pattern, text)
        return [f.lower() for f in files]

    def _extract_subjects(self, text: str) -> List[str]:
        """
        문장에서 주요 주체(subject) 추출 (개선: 단일 글자 주체 지원)

        Args:
            text: 분석할 텍스트

        Returns:
            추출된 주체 목록
        """
        subjects = []

        # 파일명 추출
        subjects.extend(self._extract_file_references(text))

        # 단일 영문자 주체 추출 (A, B, C 등 - 한국어에서도 자주 사용)
        single_chars = re.findall(r"\b([A-Za-z])\b", text)
        subjects.extend([c.lower() for c in single_chars])

        # 한글 토큰 추출 (조사 제거)
        korean_tokens = self._extract_korean_tokens(text)

        # 일반적인 접속사/동사/시간 표현만 제외 (주체는 제외하지 않음)
        exclude = {
            "했습니다",
            "되었습니다",
            "입니다",
            "있습니다",
            "합니다",
            "작성",
            "구현",
            "추가",
            "수정",
            "완료",
            "먼저",
            "나중",
            "이전",
            "이후",
            "전에",
            "후에",
            "그리고",
            "그러나",
            "발생",
            "작동",
        }

        # 2글자 이상 토큰만 추가 (exclude 제외)
        subjects.extend([k for k in korean_tokens if k not in exclude and len(k) >= 2])

        return list(set(subjects))  # 중복 제거

    def _parse_temporal_order(self, text: str) -> Optional[Tuple[str, str, str]]:
        """
        문장에서 시간 순서 관계 파싱

        예: "먼저 A를 한 후에 B를 했다" → ("A", "before", "B")
            "B 전에 A를 완료했다" → ("A", "before", "B")

        Returns:
            (subject1, relation, subject2) 또는 None
        """
        # "먼저 A ... 후에 B" 패턴
        pattern1 = r"먼저\s+(\S+).*?(?:후에|이후)\s+(\S+)"
        match = re.search(pattern1, text)
        if match:
            return (match.group(1), "before", match.group(2))

        # "A 전에 B" 패턴
        pattern2 = r"(\S+)\s+(?:전에|이전)\s+(\S+)"
        match = re.search(pattern2, text)
        if match:
            return (match.group(2), "before", match.group(1))

        # "A 후에 B" 패턴
        pattern3 = r"(\S+)\s+(?:후에|이후)\s+(\S+)"
        match = re.search(pattern3, text)
        if match:
            return (match.group(1), "before", match.group(2))

        return None

    def _check_temporal_contradiction(self, claim1: Claim, claim2: Claim) -> Optional[str]:
        """
        시간 순서 모순 검사 (개선된 로직)

        Args:
            claim1: 첫 번째 Claim
            claim2: 두 번째 Claim

        Returns:
            모순 증거 (없으면 None)
        """
        text1 = claim1.text
        text2 = claim2.text

        # 1. 파일명 추출 및 비교
        files1 = self._extract_file_references(text1)
        files2 = self._extract_file_references(text2)

        # 서로 다른 파일에 대한 시간 표현은 모순이 아님
        if files1 and files2 and not set(files1) & set(files2):
            return None

        # 2. 주체(subject) 추출
        subjects1 = self._extract_subjects(text1)
        subjects2 = self._extract_subjects(text2)
        common_subjects = set(subjects1) & set(subjects2)

        # 공통 주체가 없으면 서로 다른 대상 (한국어 단일 주체 지원: >= 1)
        if len(common_subjects) < 1:
            return None

        # 3. 복잡한 문장 구조 파싱 시도
        order1 = self._parse_temporal_order(text1)
        order2 = self._parse_temporal_order(text2)

        # 두 문장 모두 명확한 순서 관계가 있는 경우
        if order1 and order2:
            subj1_1, rel1, subj1_2 = order1
            subj2_1, rel2, subj2_2 = order2

            # 같은 주체 쌍이면서 순서가 반대인 경우
            if (
                subj1_1 in common_subjects
                and subj1_2 in common_subjects
                and subj2_1 in common_subjects
                and subj2_2 in common_subjects
            ):
                if rel1 == rel2:
                    # 같은 순서 관계 → 모순 없음
                    return None
                else:
                    # 반대 순서 관계 → 모순
                    return f"시간 순서 충돌: '{subj1_1} {rel1} {subj1_2}' vs '{subj2_1} {rel2} {subj2_2}'"

        # 4. 기본 before/after 패턴 검사
        temporal1 = None
        for temp_type, patterns in self._compiled_temporal.items():
            if any(pattern.search(text1) for pattern in patterns):
                temporal1 = temp_type
                break

        temporal2 = None
        for temp_type, patterns in self._compiled_temporal.items():
            if any(pattern.search(text2) for pattern in patterns):
                temporal2 = temp_type
                break

        # 모순 판단
        if temporal1 and temporal2:
            # before vs after이고, 같은 주체를 다루는 경우만 모순
            if (temporal1 == "before" and temporal2 == "after") or (
                temporal1 == "after" and temporal2 == "before"
            ):
                return f"시간 순서 충돌: {temporal1} vs {temporal2} (공통 주체: {len(common_subjects)}개)"

        return None

    def _check_comparison_contradiction(self, claim1: Claim, claim2: Claim) -> Optional[str]:
        """
        비교/수치 모순 검사

        Args:
            claim1: 첫 번째 Claim
            claim2: 두 번째 Claim

        Returns:
            모순 증거 (없으면 None)
        """
        text1 = claim1.text
        text2 = claim2.text

        # Claim1의 비교 표현 감지
        comparison1 = None
        for comp_type, patterns in self._compiled_comparison.items():
            if any(pattern.search(text1) for pattern in patterns):
                comparison1 = comp_type
                break

        # Claim2의 비교 표현 감지
        comparison2 = None
        for comp_type, patterns in self._compiled_comparison.items():
            if any(pattern.search(text2) for pattern in patterns):
                comparison2 = comp_type
                break

        # 모순 판단
        if comparison1 and comparison2:
            # greater vs lesser는 모순
            if (comparison1 == "greater" and comparison2 == "lesser") or (
                comparison1 == "lesser" and comparison2 == "greater"
            ):
                return f"비교 방향 충돌: {comparison1} vs {comparison2}"

        return None

    def _check_type_contradiction(self, claim1: Claim, claim2: Claim) -> Optional[str]:
        """
        Claim 타입 모순 검사

        Args:
            claim1: 첫 번째 Claim
            claim2: 두 번째 Claim

        Returns:
            모순 증거 (없으면 None)
        """
        # implementation_complete vs reference_existing는 모순일 수 있음
        type1 = claim1.claim_type
        type2 = claim2.claim_type

        # 같은 파일/함수를 다루는지 확인
        keywords1 = set(re.findall(r"\b\w{3,}\b", claim1.text.lower()))
        keywords2 = set(re.findall(r"\b\w{3,}\b", claim2.text.lower()))
        overlap = keywords1 & keywords2

        if len(overlap) >= 2:
            # 구현 완료 vs 기존 참조
            if (type1 == "implementation_complete" and type2 == "reference_existing") or (
                type1 == "reference_existing" and type2 == "implementation_complete"
            ):
                return f"타입 충돌: {type1} vs {type2} (공통 키워드 {len(overlap)}개)"

        return None

    def _calculate_severity(self, contradictions: List[Dict]) -> str:
        """
        모순 심각도 계산

        Args:
            contradictions: 모순 목록

        Returns:
            심각도 (none, low, medium, high, critical)
        """
        if not contradictions:
            return "none"

        # critical 모순이 하나라도 있으면 critical
        if any(c["severity"] == "critical" for c in contradictions):
            return "critical"

        # high 모순이 2개 이상이면 critical
        high_count = sum(1 for c in contradictions if c["severity"] == "high")
        if high_count >= 2:
            return "critical"
        elif high_count >= 1:
            return "high"

        # medium 모순이 3개 이상이면 high
        medium_count = sum(1 for c in contradictions if c["severity"] == "medium")
        if medium_count >= 3:
            return "high"
        elif medium_count >= 1:
            return "medium"

        return "low"

    def _interpret_contradictions(self, count: int, severity: str) -> str:
        """
        모순 해석

        Args:
            count: 모순 개수
            severity: 심각도

        Returns:
            해석 문구
        """
        interpretations = {
            "none": "모순 없음. 응답이 논리적으로 일관됩니다.",
            "low": f"{count}개의 경미한 모순 발견. 추가 확인 권장.",
            "medium": f"{count}개의 중간 수준 모순 발견. 일부 주장이 충돌합니다.",
            "high": f"{count}개의 심각한 모순 발견. 논리적 불일치가 있습니다.",
            "critical": f"{count}개의 치명적 모순 발견. 응답이 자기 모순적입니다.",
        }

        return interpretations.get(severity, "평가 불가")

    def compare_responses(self, responses: List[str]) -> Dict:
        """
        여러 응답의 모순 비교

        Args:
            responses: 응답 텍스트 목록

        Returns:
            비교 분석 결과
        """
        analyses = [self.detect_contradictions(r) for r in responses]

        contradiction_counts = [a["contradictions_found"] for a in analyses]

        return {
            "count": len(responses),
            "average_contradictions": round(
                sum(contradiction_counts) / len(contradiction_counts), 2
            ),
            "min_contradictions": min(contradiction_counts),
            "max_contradictions": max(contradiction_counts),
            "severity_distribution": self._get_severity_distribution(analyses),
            "best_response_index": contradiction_counts.index(min(contradiction_counts)),
            "worst_response_index": contradiction_counts.index(max(contradiction_counts)),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_severity_distribution(self, analyses: List[Dict]) -> Dict:
        """
        심각도 분포 계산

        Args:
            analyses: 분석 결과 목록

        Returns:
            심각도별 개수
        """
        distribution = {}
        for analysis in analyses:
            severity = analysis["severity"]
            distribution[severity] = distribution.get(severity, 0) + 1

        return distribution

    def get_contradiction_trend(self, analyses: List[Dict]) -> Dict:
        """
        모순 추이 분석

        Args:
            analyses: 시간순 분석 결과 목록

        Returns:
            추이 분석 결과
        """
        if len(analyses) < 2:
            return {"error": "insufficient_data"}

        contradiction_counts = [a["contradictions_found"] for a in analyses]

        # 추세 계산 (간단한 선형 회귀)
        n = len(contradiction_counts)
        x = list(range(n))
        y = contradiction_counts

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        # 추세 판단
        if slope > 0.5:
            trend = "worsening_significantly"
        elif slope > 0.1:
            trend = "worsening"
        elif slope > -0.1:
            trend = "stable"
        elif slope > -0.5:
            trend = "improving"
        else:
            trend = "improving_significantly"

        return {
            "count": n,
            "slope": round(slope, 3),
            "trend": trend,
            "first_contradictions": contradiction_counts[0],
            "last_contradictions": contradiction_counts[-1],
            "change": contradiction_counts[-1] - contradiction_counts[0],
            "average": round(sum(contradiction_counts) / n, 2),
        }
