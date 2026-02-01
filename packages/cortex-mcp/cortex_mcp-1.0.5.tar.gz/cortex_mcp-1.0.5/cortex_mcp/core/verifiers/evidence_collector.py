"""
증거 수집기

Claim 유형에 따라 적절한 Verifier를 선택하고 실행합니다.
모든 Verifier를 통합하여 AI 응답의 독립적인 검증을 수행.
"""
import logging
from typing import Any, Dict, List, Optional, Type

from .base import BaseVerifier, Evidence, EvidenceType, VerificationResult
from .file_change_verifier import FileChangeVerifier
from .code_element_verifier import CodeElementVerifier
from .test_output_verifier import TestOutputVerifier
from .code_pattern_verifier import CodePatternVerifier

logger = logging.getLogger(__name__)


class EvidenceCollector:
    """
    증거 수집 통합 클래스

    Claim 유형에 따라 적절한 Verifier를 선택하고 실행하여
    독립적인 증거를 수집합니다.
    """

    # Claim 타입 → Verifier 매핑
    # 각 Claim 타입별로 사용할 Verifier 목록을 정의
    CLAIM_TYPE_VERIFIERS: Dict[str, List[str]] = {
        # 구현 완료 주장: 파일 변경 + 코드 요소 존재
        "implementation_complete": ["file_change", "code_element"],
        # 수정 완료 주장: 파일 변경 + 코드 패턴
        "modification": ["file_change", "code_element", "code_pattern"],
        # 검증 완료 주장: 테스트 출력
        "verification": ["test_output"],
        # 버그 수정 주장: 파일 변경 + 테스트 출력
        "bug_fix": ["file_change", "test_output"],
        # 기존 코드 참조 주장: 코드 요소 존재
        "reference_existing": ["code_element"],
        # 기능 확장 주장: 파일 변경 + 코드 요소
        "extension": ["file_change", "code_element"],
        # 리팩토링 주장: 파일 변경 + 코드 패턴
        "refactoring": ["file_change", "code_pattern"],
        # 테스트 추가 주장: 파일 변경 + 테스트 출력
        "test_addition": ["file_change", "test_output", "code_element"],
        # 로깅 추가 주장: 파일 변경 + 코드 패턴
        "logging_addition": ["file_change", "code_pattern"],
        # 에러 핸들링 추가 주장: 파일 변경 + 코드 패턴
        "error_handling": ["file_change", "code_pattern"],
        # 기본값 (알 수 없는 타입)
        "unknown": ["file_change"],
    }

    # Verifier 가중치 (종합 점수 계산용)
    VERIFIER_WEIGHTS: Dict[str, float] = {
        "file_change": 0.3,      # 파일 변경: 30%
        "code_element": 0.35,    # 코드 요소 존재: 35%
        "test_output": 0.25,     # 테스트 결과: 25%
        "code_pattern": 0.1,     # 코드 패턴: 10%
    }

    def __init__(self, project_path: str):
        """
        EvidenceCollector 초기화

        Args:
            project_path: 프로젝트 루트 경로
        """
        self.project_path = project_path

        # Verifier 인스턴스 생성
        self.verifiers: Dict[str, BaseVerifier] = {
            "file_change": FileChangeVerifier(),
            "code_element": CodeElementVerifier(),
            "test_output": TestOutputVerifier(),
            "code_pattern": CodePatternVerifier(),
        }

    def collect_evidence(
        self,
        claim: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Evidence]:
        """
        Claim에 대한 증거 수집

        Args:
            claim: 검증할 Claim 객체 (claim.text, claim.claim_type 속성 기대)
            context: 추가 컨텍스트 {
                "test_output": str,       # 테스트 출력
                "file_contents": dict,    # 파일 내용
                "mentioned_files": list,  # 언급된 파일 목록
                "target_file": str,       # 대상 파일
                ...
            }

        Returns:
            수집된 Evidence 목록
        """
        context = context or {}
        context["project_path"] = self.project_path

        all_evidence: List[Evidence] = []

        # Claim 타입에 맞는 Verifier 선택
        claim_type = getattr(claim, 'claim_type', 'unknown')
        claim_text = getattr(claim, 'text', str(claim))

        verifier_types = self.CLAIM_TYPE_VERIFIERS.get(
            claim_type,
            self.CLAIM_TYPE_VERIFIERS["unknown"]
        )

        logger.info(f"[EvidenceCollector] Claim 타입: {claim_type}, Verifiers: {verifier_types}")

        for verifier_type in verifier_types:
            verifier = self.verifiers.get(verifier_type)
            if not verifier:
                logger.warning(f"[EvidenceCollector] Verifier 없음: {verifier_type}")
                continue

            try:
                result = verifier.verify(claim, context)
                all_evidence.extend(result.evidence)

                logger.info(
                    f"[EvidenceCollector] [{verifier_type}] "
                    f"verified={result.verified}, "
                    f"confidence={result.confidence:.2f}, "
                    f"evidence_count={len(result.evidence)}"
                )

            except Exception as e:
                logger.error(f"[EvidenceCollector] [{verifier_type}] 검증 오류: {e}")

        return all_evidence

    def verify_claim(
        self,
        claim: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> VerificationResult:
        """
        Claim 검증 및 종합 결과 반환

        Args:
            claim: 검증할 Claim 객체
            context: 추가 컨텍스트

        Returns:
            종합 VerificationResult
        """
        context = context or {}
        context["project_path"] = self.project_path

        # Claim 정보 추출
        claim_type = getattr(claim, 'claim_type', 'unknown')
        claim_text = getattr(claim, 'text', str(claim))

        # Verifier 선택
        verifier_types = self.CLAIM_TYPE_VERIFIERS.get(
            claim_type,
            self.CLAIM_TYPE_VERIFIERS["unknown"]
        )

        all_evidence: List[Evidence] = []
        verification_results: Dict[str, VerificationResult] = {}

        # 각 Verifier 실행
        for verifier_type in verifier_types:
            verifier = self.verifiers.get(verifier_type)
            if not verifier:
                continue

            try:
                result = verifier.verify(claim, context)
                verification_results[verifier_type] = result
                all_evidence.extend(result.evidence)

            except Exception as e:
                logger.error(f"[EvidenceCollector] [{verifier_type}] 검증 오류: {e}")

        # 증거가 없는 경우
        if not all_evidence:
            return VerificationResult(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason="증거를 수집할 수 없음",
                verifier_type="evidence_collector"
            )

        # 종합 confidence 계산
        weighted_confidence = self._calculate_weighted_confidence(
            verification_results,
            verifier_types
        )

        # 검증 판정
        verified = weighted_confidence >= 0.7

        # 이유 생성
        reason_parts = []
        for vtype, vresult in verification_results.items():
            if vresult.verified:
                reason_parts.append(f"{vtype}: PASS ({vresult.confidence:.2f})")
            else:
                reason_parts.append(f"{vtype}: FAIL ({vresult.confidence:.2f})")

        reason = "; ".join(reason_parts) if reason_parts else f"{len(all_evidence)}개 증거 수집됨"

        return VerificationResult(
            verified=verified,
            confidence=weighted_confidence,
            evidence=all_evidence,
            reason=reason,
            verifier_type="evidence_collector"
        )

    def verify_multiple_claims(
        self,
        claims: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, VerificationResult]:
        """
        여러 Claim 검증

        Args:
            claims: 검증할 Claim 목록
            context: 공통 컨텍스트

        Returns:
            {claim_text: VerificationResult} 딕셔너리
        """
        results = {}

        for claim in claims:
            claim_text = getattr(claim, 'text', str(claim))
            result = self.verify_claim(claim, context)
            results[claim_text[:100]] = result  # 키 길이 제한

        return results

    def get_verification_summary(
        self,
        claims: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        여러 Claim에 대한 검증 요약 생성

        Args:
            claims: 검증할 Claim 목록
            context: 공통 컨텍스트

        Returns:
            요약 딕셔너리 {
                "total_claims": int,
                "verified_claims": int,
                "unverified_claims": int,
                "overall_confidence": float,
                "details": List[Dict]
            }
        """
        details = []
        total_confidence = 0.0
        verified_count = 0

        for claim in claims:
            result = self.verify_claim(claim, context)
            claim_text = getattr(claim, 'text', str(claim))
            claim_type = getattr(claim, 'claim_type', 'unknown')

            details.append({
                "claim_text": claim_text[:100],
                "claim_type": claim_type,
                "verified": result.verified,
                "confidence": result.confidence,
                "reason": result.reason,
                "evidence_count": len(result.evidence),
            })

            total_confidence += result.confidence
            if result.verified:
                verified_count += 1

        total = len(claims)
        overall_confidence = total_confidence / total if total > 0 else 0.0

        return {
            "total_claims": total,
            "verified_claims": verified_count,
            "unverified_claims": total - verified_count,
            "overall_confidence": overall_confidence,
            "verification_rate": verified_count / total if total > 0 else 0.0,
            "details": details,
        }

    def _calculate_weighted_confidence(
        self,
        results: Dict[str, VerificationResult],
        verifier_types: List[str]
    ) -> float:
        """
        가중 평균 confidence 계산

        Args:
            results: Verifier별 결과
            verifier_types: 사용된 Verifier 타입 목록

        Returns:
            가중 평균 confidence
        """
        if not results:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for vtype in verifier_types:
            if vtype in results:
                weight = self.VERIFIER_WEIGHTS.get(vtype, 0.25)
                confidence = results[vtype].confidence
                weighted_sum += weight * confidence
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def add_verifier(self, name: str, verifier: BaseVerifier):
        """
        커스텀 Verifier 추가

        Args:
            name: Verifier 이름
            verifier: BaseVerifier 인스턴스
        """
        self.verifiers[name] = verifier
        logger.info(f"[EvidenceCollector] Verifier 추가됨: {name}")

    def get_available_verifiers(self) -> List[str]:
        """사용 가능한 Verifier 목록 반환"""
        return list(self.verifiers.keys())

    def clear_caches(self):
        """모든 Verifier 캐시 초기화"""
        for verifier in self.verifiers.values():
            if hasattr(verifier, 'clear_cache'):
                verifier.clear_cache()
        logger.info("[EvidenceCollector] 모든 캐시 초기화됨")


class QuickVerifier:
    """
    빠른 검증을 위한 유틸리티 클래스

    개별 검증 작업을 위한 편의 메서드 제공
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.file_verifier = FileChangeVerifier()
        self.code_verifier = CodeElementVerifier()
        self.test_verifier = TestOutputVerifier()
        self.pattern_verifier = CodePatternVerifier()

    def verify_file_changed(
        self,
        file_path: str,
        expected_content: Optional[str] = None
    ) -> VerificationResult:
        """파일 변경 빠른 검증"""
        if expected_content:
            return self.file_verifier.verify_specific_change(
                self.project_path,
                file_path,
                expected_content
            )
        else:
            # 간단한 변경 확인
            class SimpleClaim:
                text = f"{file_path} 파일이 변경됨"

            return self.file_verifier.verify(
                SimpleClaim(),
                {"project_path": self.project_path, "mentioned_files": [file_path]}
            )

    def verify_method_exists(
        self,
        file_path: str,
        method_name: str,
        class_name: Optional[str] = None
    ) -> VerificationResult:
        """메서드 존재 빠른 검증"""
        full_path = file_path
        if not file_path.startswith('/'):
            full_path = f"{self.project_path}/{file_path}"

        return self.code_verifier.verify_method_exists(
            full_path,
            method_name,
            class_name
        )

    def verify_class_exists(
        self,
        file_path: str,
        class_name: str
    ) -> VerificationResult:
        """클래스 존재 빠른 검증"""
        full_path = file_path
        if not file_path.startswith('/'):
            full_path = f"{self.project_path}/{file_path}"

        return self.code_verifier.verify_class_exists(full_path, class_name)

    def verify_test_passed(
        self,
        test_output: str,
        expected_passed: Optional[int] = None,
        expected_total: Optional[int] = None
    ) -> VerificationResult:
        """테스트 통과 빠른 검증"""
        if expected_passed is not None and expected_total is not None:
            return self.test_verifier.verify_test_count(
                test_output,
                expected_passed,
                expected_total
            )
        else:
            return self.test_verifier.verify_all_passed(test_output)

    def verify_import_exists(
        self,
        file_path: str,
        import_name: str
    ) -> VerificationResult:
        """import 존재 빠른 검증"""
        full_path = file_path
        if not file_path.startswith('/'):
            full_path = f"{self.project_path}/{file_path}"

        return self.pattern_verifier.verify_import_exists(full_path, import_name)

    def verify_pattern_exists(
        self,
        file_path: str,
        pattern: str
    ) -> VerificationResult:
        """코드 패턴 존재 빠른 검증"""
        full_path = file_path
        if not file_path.startswith('/'):
            full_path = f"{self.project_path}/{file_path}"

        return self.pattern_verifier.verify_regex_pattern(full_path, pattern)
