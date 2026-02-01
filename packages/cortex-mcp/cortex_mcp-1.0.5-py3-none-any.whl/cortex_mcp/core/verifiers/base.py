"""
Verifier 기본 인터페이스

모든 Verifier는 이 인터페이스를 구현해야 합니다.
AI가 주장하는 코드 작업을 독립적으로 검증하는 시스템의 기반.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceType(Enum):
    """증거 유형"""
    GIT_DIFF = "git_diff"
    AST_ELEMENT = "ast_element"
    TEST_RESULT = "test_result"
    CODE_PATTERN = "code_pattern"
    FILE_EXISTS = "file_exists"
    CONTENT_MATCH = "content_match"


@dataclass
class Evidence:
    """
    검증 증거

    AI의 주장을 검증하기 위한 독립적인 증거를 표현합니다.
    """
    type: EvidenceType
    source: str  # 증거 출처 (파일 경로, 명령어 등)
    content: str  # 증거 내용
    confidence: float  # 신뢰도 (0.0 - 1.0)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """유효성 검증"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (직렬화용)"""
        return {
            "type": self.type.value,
            "source": self.source,
            "content": self.content[:500] if len(self.content) > 500 else self.content,  # 긴 내용 truncate
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        """딕셔너리에서 생성"""
        return cls(
            type=EvidenceType(data["type"]),
            source=data["source"],
            content=data["content"],
            confidence=data["confidence"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data.get("timestamp"), str) else datetime.now(),
            metadata=data.get("metadata", {}),
        )


@dataclass
class VerificationResult:
    """
    검증 결과

    Claim에 대한 검증 결과를 담습니다.
    """
    verified: bool
    confidence: float
    evidence: List[Evidence]
    reason: str
    verifier_type: str

    def __post_init__(self):
        """유효성 검증"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "verified": self.verified,
            "confidence": self.confidence,
            "evidence": [e.to_dict() for e in self.evidence],
            "reason": self.reason,
            "verifier_type": self.verifier_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationResult":
        """딕셔너리에서 생성"""
        return cls(
            verified=data["verified"],
            confidence=data["confidence"],
            evidence=[Evidence.from_dict(e) for e in data.get("evidence", [])],
            reason=data["reason"],
            verifier_type=data["verifier_type"],
        )

    def merge_with(self, other: "VerificationResult") -> "VerificationResult":
        """
        다른 검증 결과와 병합

        여러 Verifier의 결과를 하나로 합칠 때 사용
        """
        # 증거 합치기
        merged_evidence = self.evidence + other.evidence

        # 신뢰도 계산 (가중 평균)
        if merged_evidence:
            total_weight = sum(e.confidence for e in merged_evidence)
            if total_weight > 0:
                merged_confidence = sum(e.confidence ** 2 for e in merged_evidence) / total_weight
            else:
                merged_confidence = 0.0
        else:
            merged_confidence = min(self.confidence, other.confidence)

        # 검증 여부 (둘 다 verified여야 함)
        merged_verified = self.verified and other.verified

        return VerificationResult(
            verified=merged_verified,
            confidence=merged_confidence,
            evidence=merged_evidence,
            reason=f"{self.reason}; {other.reason}",
            verifier_type=f"{self.verifier_type}+{other.verifier_type}",
        )


class BaseVerifier(ABC):
    """
    Verifier 기본 클래스

    모든 Verifier는 이 클래스를 상속받아 구현합니다.
    """

    @property
    @abstractmethod
    def verifier_type(self) -> str:
        """
        Verifier 유형 반환

        Returns:
            Verifier를 식별하는 문자열 (예: "file_change", "code_element")
        """
        pass

    @abstractmethod
    def verify(self, claim: Any, context: Dict[str, Any]) -> VerificationResult:
        """
        Claim 검증 수행

        Args:
            claim: 검증할 Claim 객체 (claim.text, claim.claim_type 등)
            context: 검증에 필요한 컨텍스트
                - project_path: 프로젝트 경로
                - file_contents: 파일 내용 딕셔너리
                - test_output: 테스트 출력
                - mentioned_files: 언급된 파일 목록

        Returns:
            VerificationResult: 검증 결과
        """
        pass

    def _create_result(
        self,
        verified: bool,
        confidence: float,
        evidence: List[Evidence],
        reason: str
    ) -> VerificationResult:
        """
        결과 객체 생성 헬퍼

        Args:
            verified: 검증 성공 여부
            confidence: 신뢰도 (0.0 - 1.0)
            evidence: 수집된 증거 목록
            reason: 검증 결과 설명

        Returns:
            VerificationResult 객체
        """
        return VerificationResult(
            verified=verified,
            confidence=confidence,
            evidence=evidence,
            reason=reason,
            verifier_type=self.verifier_type,
        )

    def _create_evidence(
        self,
        type: EvidenceType,
        source: str,
        content: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Evidence:
        """
        Evidence 객체 생성 헬퍼

        Args:
            type: 증거 유형
            source: 증거 출처
            content: 증거 내용
            confidence: 신뢰도
            metadata: 추가 메타데이터

        Returns:
            Evidence 객체
        """
        return Evidence(
            type=type,
            source=source,
            content=content,
            confidence=confidence,
            metadata=metadata or {},
        )
