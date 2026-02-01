"""
Response Formatter - Trust UX

Cortex Phase 7: Trust UX
LLM 응답에 신뢰도 지표를 추가하여 사용자가 응답의 신뢰성을 평가할 수 있도록 합니다.

핵심 기능:
- Trust Prefix 추가 (grounding score 기반)
- Verification Summary 포맷팅
- Claim Assessment 포맷팅
- Evidence List 포맷팅
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .alpha_logger import AlphaLogger, LogModule


class TrustLevel(Enum):
    """신뢰도 레벨"""

    HIGH = "high"  # grounding >= 0.7
    MEDIUM = "medium"  # grounding >= 0.4
    LOW = "low"  # grounding < 0.4


class ResponseFormatter:
    """
    Trust UX를 위한 응답 포맷터

    LLM 응답에 신뢰도 지표를 추가하여 사용자에게
    응답의 신뢰성을 명확히 전달합니다.
    """

    # 신뢰도 레벨별 이모지
    TRUST_EMOJIS = {
        TrustLevel.HIGH: "✅",
        TrustLevel.MEDIUM: "⚠️",
        TrustLevel.LOW: "🚨",
    }

    # 신뢰도 레벨별 라벨
    TRUST_LABELS = {
        TrustLevel.HIGH: "High confidence",
        TrustLevel.MEDIUM: "Medium confidence",
        TrustLevel.LOW: "Low confidence",
    }

    def __init__(self, project_id: Optional[str] = None):
        """
        Response Formatter 초기화

        Args:
            project_id: 프로젝트 식별자 (Optional)
        """
        self.project_id = project_id
        self.logger = AlphaLogger()

    def add_trust_prefix(self, response: str, verification_result: Dict[str, Any]) -> str:
        """
        LLM 응답에 신뢰도 지표 Prefix 추가

        Args:
            response: 원본 LLM 응답
            verification_result: 검증 결과 딕셔너리
                - grounding_score: Grounding 점수 (0.0 ~ 1.0)
                - evidence_count: Evidence 파일 개수
                - claim_count: Claim 개수 (Optional)
                - referenced_contexts: 참조된 Context 목록 (Optional)

        Returns:
            Trust prefix가 추가된 응답
        """
        grounding_score = verification_result.get("grounding_score", 0.0)
        evidence_count = verification_result.get("evidence_count", 0)
        claim_count = verification_result.get("claim_count", 0)

        # 신뢰도 레벨 결정
        trust_level = self._get_trust_level(grounding_score)

        # Prefix 구성
        emoji = self.TRUST_EMOJIS[trust_level]
        label = self.TRUST_LABELS[trust_level]

        prefix = (
            f"{emoji} {label} (grounding: {grounding_score:.2f}, {evidence_count} evidence files"
        )

        if claim_count > 0:
            prefix += f", {claim_count} claims"

        prefix += ")\n\n"

        # Low confidence일 때 경고 추가
        if trust_level == TrustLevel.LOW:
            prefix += "⚠️ This response relies on weak evidence. Please verify before using.\n\n"

        # Referenced contexts 추가 (있는 경우)
        referenced_contexts = verification_result.get("referenced_contexts", [])
        if referenced_contexts:
            prefix += f"📁 Cortex loaded context from: {', '.join(referenced_contexts[:3])}"
            if len(referenced_contexts) > 3:
                prefix += f" (+{len(referenced_contexts) - 3} more)"
            prefix += "\n\n"

        # 로깅
        self.logger.log(
            module=LogModule.GENERAL,
            action="add_trust_prefix",
            metadata={
                "trust_level": trust_level.value,
                "grounding_score": grounding_score,
                "evidence_count": evidence_count,
                "claim_count": claim_count,
                "context_count": len(referenced_contexts),
            },
        )

        return prefix + response

    def format_verification_summary(self, verification_result: Dict[str, Any]) -> str:
        """
        검증 결과 요약 포맷팅

        Args:
            verification_result: 검증 결과 딕셔너리

        Returns:
            포맷팅된 검증 요약
        """
        grounding_score = verification_result.get("grounding_score", 0.0)
        evidence_count = verification_result.get("evidence_count", 0)
        claim_count = verification_result.get("claim_count", 0)
        verified_claims = verification_result.get("verified_claims", 0)

        trust_level = self._get_trust_level(grounding_score)
        emoji = self.TRUST_EMOJIS[trust_level]

        summary = f"{emoji} Verification Summary\n"
        summary += f"{'=' * 40}\n"
        summary += f"Grounding Score: {grounding_score:.2f}\n"
        summary += f"Evidence Files: {evidence_count}\n"

        if claim_count > 0:
            verification_rate = (verified_claims / claim_count * 100) if claim_count > 0 else 0
            summary += (
                f"Claims: {verified_claims}/{claim_count} verified ({verification_rate:.1f}%)\n"
            )

        summary += f"Trust Level: {self.TRUST_LABELS[trust_level]}\n"

        return summary

    def format_claim_assessment(self, claim_text: str, assessment_result: Dict[str, Any]) -> str:
        """
        Claim 평가 결과 포맷팅

        Args:
            claim_text: Claim 텍스트
            assessment_result: 평가 결과 (fuzzy_claim_analyzer.assess_claim 결과)

        Returns:
            포맷팅된 평가 결과
        """
        decision = assessment_result.get("decision", "UNKNOWN")
        final_confidence = assessment_result.get("final_confidence", 0.0)
        linguistic_confidence = assessment_result.get("linguistic_confidence", 0.0)
        evidence_confidence = assessment_result.get("evidence_confidence", 0.0)

        # Decision에 따른 이모지
        decision_emoji = {
            "ACCEPT": "✅",
            "CAUTION": "⚠️",
            "WARN": "🚨",
        }.get(decision, "❓")

        formatted = f"{decision_emoji} Claim Assessment: {decision}\n"
        formatted += f'Claim: "{claim_text}"\n'
        formatted += f"Final Confidence: {final_confidence:.2f}\n"
        formatted += f"  └─ Linguistic: {linguistic_confidence:.2f}\n"
        formatted += f"  └─ Evidence: {evidence_confidence:.2f}\n"

        return formatted

    def format_evidence_list(self, evidence_list: List[Dict[str, Any]], max_items: int = 5) -> str:
        """
        Evidence 목록 포맷팅

        Args:
            evidence_list: Evidence 목록
            max_items: 표시할 최대 항목 수

        Returns:
            포맷팅된 Evidence 목록
        """
        if not evidence_list:
            return "📭 No evidence found.\n"

        formatted = f"📚 Evidence ({len(evidence_list)} items):\n"

        for i, evidence in enumerate(evidence_list[:max_items]):
            evidence_type = evidence.get("type", "unknown")
            evidence_id = evidence.get("id", "unknown")
            relevance_score = evidence.get("relevance_score", 0.0)

            formatted += (
                f"  {i + 1}. [{evidence_type}] {evidence_id} (relevance: {relevance_score:.2f})\n"
            )

        if len(evidence_list) > max_items:
            formatted += f"  ... and {len(evidence_list) - max_items} more\n"

        return formatted

    def format_context_summary(self, contexts: List[str], max_items: int = 5) -> str:
        """
        Context 목록 포맷팅

        Args:
            contexts: Context ID 목록
            max_items: 표시할 최대 항목 수

        Returns:
            포맷팅된 Context 목록
        """
        if not contexts:
            return "📂 No contexts loaded.\n"

        formatted = f"📂 Loaded Contexts ({len(contexts)}):\n"

        for i, context_id in enumerate(contexts[:max_items]):
            formatted += f"  {i + 1}. {context_id}\n"

        if len(contexts) > max_items:
            formatted += f"  ... and {len(contexts) - max_items} more\n"

        return formatted

    def format_complete_report(
        self,
        response: str,
        verification_result: Dict[str, Any],
        claim_assessments: Optional[List[Dict[str, Any]]] = None,
        evidence_list: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        완전한 신뢰도 보고서 생성

        Args:
            response: 원본 LLM 응답
            verification_result: 검증 결과
            claim_assessments: Claim 평가 목록 (Optional)
            evidence_list: Evidence 목록 (Optional)

        Returns:
            완전한 보고서
        """
        report = "=" * 60 + "\n"
        report += "CORTEX TRUST REPORT\n"
        report += "=" * 60 + "\n\n"

        # Verification Summary
        report += self.format_verification_summary(verification_result) + "\n"

        # Referenced Contexts
        referenced_contexts = verification_result.get("referenced_contexts", [])
        if referenced_contexts:
            report += self.format_context_summary(referenced_contexts) + "\n"

        # Claim Assessments
        if claim_assessments:
            report += "🔍 Claim Assessments:\n"
            report += "-" * 60 + "\n"
            for assessment in claim_assessments[:3]:  # Top 3만 표시
                claim_text = assessment.get("claim_text", "")
                report += self.format_claim_assessment(claim_text, assessment) + "\n"

            if len(claim_assessments) > 3:
                report += f"... and {len(claim_assessments) - 3} more claims\n\n"

        # Evidence List
        if evidence_list:
            report += self.format_evidence_list(evidence_list) + "\n"

        # Original Response
        report += "=" * 60 + "\n"
        report += "ORIGINAL RESPONSE\n"
        report += "=" * 60 + "\n"
        report += response + "\n"

        return report

    def _get_trust_level(self, grounding_score: float) -> TrustLevel:
        """
        Grounding Score에서 신뢰도 레벨 결정

        Args:
            grounding_score: Grounding 점수 (0.0 ~ 1.0)

        Returns:
            신뢰도 레벨
        """
        if grounding_score >= 0.7:
            return TrustLevel.HIGH
        elif grounding_score >= 0.4:
            return TrustLevel.MEDIUM
        else:
            return TrustLevel.LOW

    def export_trust_metrics(self, verification_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trust Metrics 내보내기 (연구/분석용)

        Args:
            verification_result: 검증 결과

        Returns:
            Trust metrics 딕셔너리
        """
        grounding_score = verification_result.get("grounding_score", 0.0)
        trust_level = self._get_trust_level(grounding_score)

        return {
            "timestamp": datetime.now().isoformat(),
            "trust_level": trust_level.value,
            "grounding_score": grounding_score,
            "evidence_count": verification_result.get("evidence_count", 0),
            "claim_count": verification_result.get("claim_count", 0),
            "verified_claims": verification_result.get("verified_claims", 0),
            "context_count": len(verification_result.get("referenced_contexts", [])),
        }
