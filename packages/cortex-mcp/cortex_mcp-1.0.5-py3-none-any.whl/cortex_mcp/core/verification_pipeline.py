"""
Verification Pipeline - 전체 Hallucination 검증 파이프라인

모든 검증 컴포넌트를 통합하여 하나의 파이프라인으로 제공합니다.

흐름:
1. Response에서 Claim 추출
2. 현재 Git/File 상태에서 Evidence 수집
3. 각 Claim을 Evidence와 매칭
4. Grounding Score 계산
5. 검증 결과 반환
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

from .evidence_collector import EvidenceCollector
from .evidence_store import EvidenceStore
from .evidence_matcher import EvidenceMatcher, MatchResult
from .claim_extractor import ClaimExtractor

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """검증 파이프라인 결과"""
    is_grounded: bool  # 전체적으로 grounded인지
    grounding_score: float  # 전체 Grounding Score (0.0 ~ 1.0)
    claims: List[Dict]  # 추출된 Claim 목록
    match_results: List[MatchResult]  # 각 Claim의 매칭 결과
    ungrounded_claims: List[Dict]  # 근거 없는 Claim 목록
    reasoning: str  # 전체 검증 근거
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "is_grounded": self.is_grounded,
            "grounding_score": self.grounding_score,
            "total_claims": len(self.claims),
            "grounded_claims": len(self.claims) - len(self.ungrounded_claims),
            "ungrounded_claims": len(self.ungrounded_claims),
            "ungrounded_claim_details": [
                {"content": c.get("content", "")[:100], "type": c.get("type", "")}
                for c in self.ungrounded_claims
            ],
            "reasoning": self.reasoning,
            "details": self.details,
        }


class VerificationPipeline:
    """
    전체 Hallucination 검증 파이프라인

    사용 예시:
        pipeline = VerificationPipeline(
            project_id="my_project",
            project_path="/path/to/project"
        )

        result = pipeline.verify(response_text)

        if result.is_grounded:
            print(f"Response is grounded! Score: {result.grounding_score:.2f}")
        else:
            print(f"Ungrounded claims found: {len(result.ungrounded_claims)}")
            for claim in result.ungrounded_claims:
                print(f"  - {claim['content']}")
    """

    # 기본 설정
    DEFAULT_CONFIG = {
        "grounding_threshold": 0.7,  # 이 이상이면 grounded로 판정
        "claim_weight_by_type": {
            "implementation_claim": 1.0,
            "modification_claim": 0.9,
            "bug_fix_claim": 0.9,
            "existence_claim": 0.8,
            "performance_claim": 0.7,
            "generic": 0.5,
        },
        "min_score_for_grounded": 0.5,  # 개별 Claim이 grounded로 판정되는 최소 점수
        "auto_refresh_evidence": True,  # verify 호출 시 Evidence 자동 새로고침
    }

    def __init__(
        self,
        project_id: str,
        project_path: str,
        config: Optional[Dict] = None
    ):
        """
        VerificationPipeline 초기화

        Args:
            project_id: 프로젝트 식별자
            project_path: 프로젝트 루트 경로
            config: 설정 딕셔너리
        """
        self.project_id = project_id
        self.project_path = Path(project_path)
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}

        # 컴포넌트 초기화
        self.evidence_collector = EvidenceCollector(str(project_path))
        self.evidence_store = EvidenceStore(str(project_path))
        self.evidence_matcher = EvidenceMatcher(project_path=str(project_path))  # 파일 시스템 직접 확인용
        self.claim_extractor = ClaimExtractor()

        logger.info(f"[PIPELINE] Initialized for project: {project_id}")

    def verify(self, response_text: str) -> VerificationResult:
        """
        Response 텍스트 검증

        Args:
            response_text: 검증할 LLM 응답 텍스트

        Returns:
            VerificationResult: 검증 결과
        """
        logger.info("[PIPELINE] Starting verification...")

        # 1. Evidence 수집 (현재 Git/File 상태)
        if self.config["auto_refresh_evidence"]:
            evidence_stats = self.evidence_store.refresh()
            logger.info(f"[PIPELINE] Evidence refreshed: {evidence_stats}")

        # 2. Claim 추출
        extracted_claims = self.claim_extractor.extract_claims(response_text)
        # Claim 객체를 Dict로 변환
        claims = [
            {
                "type": c.claim_type,
                "content": c.text,
                "start": c.start,
                "end": c.end,
                "confidence": c.confidence,
                "metadata": c.metadata or {},
            }
            for c in extracted_claims
        ]

        if not claims:
            logger.info("[PIPELINE] No claims extracted, returning grounded")
            return VerificationResult(
                is_grounded=True,
                grounding_score=1.0,
                claims=[],
                match_results=[],
                ungrounded_claims=[],
                reasoning="No verifiable claims found in response"
            )

        logger.info(f"[PIPELINE] Extracted {len(claims)} claims")

        # 3. 각 Claim에 대해 Evidence 매칭
        match_results = []
        for claim in claims:
            # 관련 Evidence 검색
            relevant_evidences = self.evidence_store.get_relevant(claim)

            # 매칭 수행
            result = self.evidence_matcher.match(claim, relevant_evidences)
            match_results.append(result)

            logger.debug(
                f"[PIPELINE] Claim '{claim.get('type', '')}': "
                f"score={result.score:.2f}, matched={result.matched}"
            )

        # 4. Grounding Score 계산
        grounding_score = self._calculate_final_score(claims, match_results)

        # 5. Ungrounded Claims 식별
        min_score = self.config["min_score_for_grounded"]
        ungrounded = []
        for claim, result in zip(claims, match_results):
            if not result.matched or result.score < min_score:
                ungrounded.append(claim)

        # 6. 전체 판정
        threshold = self.config["grounding_threshold"]
        is_grounded = grounding_score >= threshold and len(ungrounded) == 0

        # 7. 결과 생성
        reasoning = self._generate_reasoning(claims, match_results, grounding_score)

        result = VerificationResult(
            is_grounded=is_grounded,
            grounding_score=grounding_score,
            claims=claims,
            match_results=match_results,
            ungrounded_claims=ungrounded,
            reasoning=reasoning,
            details={
                "evidence_stats": self.evidence_store.to_dict(),
                "threshold": threshold,
                "config": self.config,
            }
        )

        logger.info(
            f"[PIPELINE] Verification complete: "
            f"grounded={is_grounded}, score={grounding_score:.2f}, "
            f"ungrounded={len(ungrounded)}/{len(claims)}"
        )

        return result

    def verify_claim(self, claim: Dict) -> MatchResult:
        """
        단일 Claim 검증

        Args:
            claim: 검증할 Claim

        Returns:
            MatchResult: 매칭 결과
        """
        # Evidence 새로고침
        self.evidence_store.refresh()

        # 관련 Evidence 검색
        relevant_evidences = self.evidence_store.get_relevant(claim)

        # 매칭 수행
        return self.evidence_matcher.match(claim, relevant_evidences)

    def add_execution_evidence(
        self,
        command: str,
        output: str,
        exit_code: int,
        stderr: str = ""
    ) -> None:
        """
        명령 실행 결과를 Evidence로 추가

        Args:
            command: 실행된 명령어
            output: stdout 결과
            exit_code: 종료 코드
            stderr: stderr 결과
        """
        from .evidence_collector import ExecutionEvidence

        evidence = ExecutionEvidence(
            command=command,
            output=output,
            exit_code=exit_code,
            stderr=stderr
        )
        self.evidence_store.add(evidence)
        logger.info(f"[PIPELINE] Added execution evidence for '{command[:50]}...'")

    def _calculate_final_score(
        self,
        claims: List[Dict],
        match_results: List[MatchResult]
    ) -> float:
        """
        최종 Grounding Score 계산

        가중 평균 사용:
        - Claim 타입별 가중치 적용
        - 매칭되지 않은 Claim은 0점 처리
        """
        if not claims or not match_results:
            return 1.0  # Claim이 없으면 1.0 반환

        weights = self.config["claim_weight_by_type"]
        total_weight = 0.0
        weighted_sum = 0.0

        for claim, result in zip(claims, match_results):
            claim_type = claim.get("type", "generic")
            weight = weights.get(claim_type, 0.5)

            total_weight += weight
            weighted_sum += result.score * weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _generate_reasoning(
        self,
        claims: List[Dict],
        match_results: List[MatchResult],
        score: float
    ) -> str:
        """검증 결과에 대한 설명 생성"""
        parts = []

        # 전체 요약
        total = len(claims)
        grounded = sum(1 for r in match_results if r.matched and r.score >= 0.5)
        parts.append(f"Verified {grounded}/{total} claims (score: {score:.2f})")

        # 타입별 통계
        type_stats = {}
        for claim, result in zip(claims, match_results):
            ctype = claim.get("type", "unknown")
            if ctype not in type_stats:
                type_stats[ctype] = {"total": 0, "grounded": 0}
            type_stats[ctype]["total"] += 1
            if result.matched and result.score >= 0.5:
                type_stats[ctype]["grounded"] += 1

        for ctype, stats in type_stats.items():
            parts.append(f"  - {ctype}: {stats['grounded']}/{stats['total']}")

        # 문제 있는 Claim 하이라이트
        for claim, result in zip(claims, match_results):
            if not result.matched or result.score < 0.5:
                content = claim.get("content", "")[:50]
                parts.append(f"  [UNGROUNDED] {content}... (score: {result.score:.2f})")

        return "\n".join(parts)

    def get_evidence_summary(self) -> Dict:
        """현재 Evidence 상태 요약 반환"""
        return self.evidence_store.to_dict()

    def force_refresh(self) -> Dict[str, int]:
        """Evidence 강제 새로고침"""
        return self.evidence_store.refresh()


# Singleton 인스턴스 관리
_pipeline_instances: Dict[str, VerificationPipeline] = {}


def get_verification_pipeline(
    project_id: str,
    project_path: str,
    config: Optional[Dict] = None
) -> VerificationPipeline:
    """
    VerificationPipeline 싱글톤 반환

    Args:
        project_id: 프로젝트 식별자
        project_path: 프로젝트 루트 경로
        config: 설정

    Returns:
        VerificationPipeline 인스턴스
    """
    global _pipeline_instances

    if project_id not in _pipeline_instances:
        _pipeline_instances[project_id] = VerificationPipeline(
            project_id, project_path, config
        )

    return _pipeline_instances[project_id]


def clear_pipeline_cache():
    """파이프라인 캐시 초기화"""
    global _pipeline_instances
    _pipeline_instances.clear()
