"""
Cortex Phase 9.1 - 자동 할루시네이션 검증 및 재수행 시스템

핵심 기능:
1. 의미 기반 확신도 감지 (fuzzy_claim_analyzer)
2. 자동 검증 (claim_verifier + grounding_scorer)
3. 할루시네이션 감지 시 자동 재수행
4. 대화 완료 시 전체 검증

사용 흐름:
- AI 답변 생성 → 확신도 분석 → 검증 → 재수행 → 검증된 결과
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.claim_extractor import Claim, ClaimExtractor
from core.claim_verifier import ClaimVerifier
from core.fuzzy_claim_analyzer import FuzzyClaimAnalyzer
from core.grounding_scorer import GroundingScorer

# Phase 9.5: Advanced Hallucination Detection
from core.hardcode_detector import HardcodeDetector
from core.method_existence_checker import MethodExistenceChecker

# Phase 9.7: 중앙 상수 통일
from core.hallucination_constants import (
    CONFIDENCE_SCORES,
    HIGH_CONFIDENCE_THRESHOLD,
    VERIFICATION_PASS_THRESHOLD,
    VERIFICATION_TIMEOUT_SECONDS,
    PER_CLAIM_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """검증 결과"""

    verified: bool  # 검증 통과 여부
    grounding_score: float  # 근거 점수 (0.0-1.0)
    confidence_level: str  # 확신도 레벨 (very_high, high, medium, low, none)
    claims: List[Claim]  # 추출된 주장 목록
    unverified_claims: List[Dict[str, Any]]  # 검증 실패한 주장
    requires_retry: bool  # 재수행 필요 여부
    retry_reason: Optional[str] = None  # 재수행 사유
    referenced_contexts: List[str] = None  # 참조한 맥락 목록 (파일 경로 등) - 전체 파일 리스트 (하위 호환)
    claim_evidence_map: Dict[str, List[str]] = field(default_factory=dict)  # 신규: Claim별 Evidence 매핑 (claim_id -> file_paths)

    # ULTRATHINK MODE: 확신도별 분류 검증 (Phase 9.6)
    verified_claims: List[Dict[str, Any]] = field(default_factory=list)  # 검증 통과한 Claim (확신도 높음 + grounding 통과)
    pending_claims: List[Dict[str, Any]] = field(default_factory=list)  # 검증 보류 Claim (확신도 낮음 - 작업 미완료 가능)
    claim_grounding_scores: Dict[str, float] = field(default_factory=dict)  # Claim ID별 grounding score

    # Phase 9 개선: 성능 주장 별도 처리 (정보 제공용 - 검증 대상 아님)
    performance_claims: Dict[str, Any] = field(default_factory=dict)  # 성능 관련 주장 (예: 300x 향상, 0.0001s 오버헤드)


class AutoVerifier:
    """
    자동 할루시네이션 검증 시스템

    AI 답변의 확신도를 분석하고, 높은 확신도 감지 시 자동으로 검증합니다.
    할루시네이션 발견 시 재수행을 트리거합니다.

    Note:
        Phase 9.7: 모든 상수는 hallucination_constants.py에서 import
        - HIGH_CONFIDENCE_THRESHOLD
        - VERIFICATION_PASS_THRESHOLD
        - VERIFICATION_TIMEOUT_SECONDS
        - PER_CLAIM_TIMEOUT_SECONDS
        - CONFIDENCE_SCORES
    """

    def __init__(self):
        self.claim_extractor = ClaimExtractor()
        self.fuzzy_analyzer = FuzzyClaimAnalyzer()

        # Phase 9.5: Advanced Detection
        self.hardcode_detector = HardcodeDetector()
        self.method_checker = None  # Lazy initialization (project_path 필요)

        # CACHE REMOVED: ClaimVerifier와 GroundingScorer 캐시 제거됨 (정확성 > 성능)
        # - 파일 수정 후 Evidence Graph가 변경되므로 캐시 사용 불가
        # - 항상 새로운 인스턴스 생성하여 최신 Evidence Graph 사용

    def verify_response(
        self, response_text: str, context: Optional[Dict[str, Any]] = None
    ) -> VerificationResult:
        """
        AI 응답 자동 검증

        Args:
            response_text: AI 응답 텍스트
            context: 검증에 필요한 컨텍스트 (파일 경로, 테스트 결과 등)

        Returns:
            VerificationResult: 검증 결과

        검증 절차:
        1. 확신도 분석 (fuzzy_claim_analyzer)
        2. 확신도 >= 0.8이면 Claim 추출
        3. Claim별 검증 및 referenced_contexts 수집 (claim_verifier)
        4. 전체 응답에 대한 Grounding Score 계산 (grounding_scorer)
        5. Score < 0.7이면 재수행 트리거
        """
        # BUG FIX: 타임아웃 방지를 위한 시작 시간 기록
        verification_start_time = time.time()

        def _check_timeout(operation_name: str = "verification") -> bool:
            """타임아웃 체크 - True면 타임아웃 초과"""
            elapsed = time.time() - verification_start_time
            if elapsed > VERIFICATION_TIMEOUT_SECONDS:
                logger.warning(
                    f"[TIMEOUT] {operation_name} 타임아웃 초과: {elapsed:.2f}s > {VERIFICATION_TIMEOUT_SECONDS}s"
                )
                return True
            return False

        # Phase 9.5.1: Hardcode Detection (answer.md Line 113 문제 해결)
        # BUG FIX: 확신도와 무관하게 항상 먼저 실행
        hardcode_detections = self.hardcode_detector.detect_in_response(response_text)

        if hardcode_detections:
            # 하드코딩 패턴 발견 → 검증 실패
            high_severity_detections = [
                d for d in hardcode_detections
                if d.severity in ["CRITICAL", "HIGH"]
            ]

            if high_severity_detections:
                logger.warning(
                    f"[PHASE 9.5.1] 하드코딩 패턴 감지: {len(high_severity_detections)}개 (CRITICAL/HIGH)"
                )

                return VerificationResult(
                    verified=False,
                    grounding_score=0.0,
                    confidence_level="very_high",  # Hardcode는 항상 확신도 높은 위반
                    claims=[],
                    unverified_claims=[
                        {
                            "claim_type": "hardcoded_value",
                            "text": d.line_content,
                            "reason": f"Hardcoded pattern detected: {d.pattern_name} ({d.description})",
                        }
                        for d in high_severity_detections
                    ],
                    requires_retry=True,
                    retry_reason=f"Hardcoded test values detected ({len(high_severity_detections)} patterns)",
                    referenced_contexts=[],
                )

        # 1. 확신도 분석
        analysis_result = self.fuzzy_analyzer.analyze_response(response_text)
        confidence_level = analysis_result["overall_confidence_level"]
        confidence_score = self._confidence_to_score(confidence_level)

        logger.info(f"확신도 분석: {confidence_level} (score: {confidence_score})")

        # 2. Claim 추출
        claims = self.claim_extractor.extract_claims(response_text)
        logger.info(f"추출된 Claim 수: {len(claims)}")

        # ULTRATHINK MODE (Phase 9.6): 확신도별 분류 검증
        # 전체 평균 확신도가 낮아도, 개별 Claim 중 확신도 높은 것은 검증
        logger.info("[ULTRATHINK] 확신도별 Claim 분류 시작")

        # 각 Claim의 확신도 분석 결과 가져오기
        claim_analyses = analysis_result.get("claim_analyses", [])

        # Claim을 확신도별로 분류
        high_confidence_claims = []  # fuzzy_score >= 0.8
        medium_confidence_claims = []  # 0.5 <= fuzzy_score < 0.8
        low_confidence_claims = []  # fuzzy_score < 0.5

        for i, claim in enumerate(claims):
            if i < len(claim_analyses):
                claim_analysis = claim_analyses[i]
                fuzzy_score = claim_analysis.get("fuzzy_score", 0.5)
                conf_level = claim_analysis.get("confidence_level", "none")
            else:
                # 분석 결과 없으면 기본값
                fuzzy_score = 0.5
                conf_level = "none"

            claim_info = {
                "claim": claim,
                "fuzzy_score": fuzzy_score,
                "confidence_level": conf_level,
            }

            if fuzzy_score >= 0.8:
                high_confidence_claims.append(claim_info)
            elif fuzzy_score >= 0.5:
                medium_confidence_claims.append(claim_info)
            else:
                low_confidence_claims.append(claim_info)

        logger.info(f"[ULTRATHINK] HIGH: {len(high_confidence_claims)}, "
                   f"MEDIUM: {len(medium_confidence_claims)}, "
                   f"LOW: {len(low_confidence_claims)}")

        # Phase 9.5.2: Method Existence Deep Check (answer.md Line 148 문제 해결)
        # BUG FIX: claim 의존성 제거 - 항상 method checker 실행
        if context and "project_path" in context:
            # MethodExistenceChecker 초기화 (Lazy)
            if self.method_checker is None:
                self.method_checker = MethodExistenceChecker(context["project_path"])

            # 전체 response_text에서 메서드 호출 검증 (claim 의존성 제거!)
            method_check_result = self.method_checker.verify_claim_method_calls(response_text)

            # 메서드 호출이 감지되었고, 검증 실패한 경우만 처리
            if method_check_result["method_calls"] and not method_check_result["verified"]:
                # 메서드 존재하지 않음 → 검증 실패
                missing_methods = [
                    call_result
                    for call_result in method_check_result["method_calls"]
                    if not call_result["exists"]
                ]

                logger.warning(
                    f"[PHASE 9.5.2] 메서드 존재 확인 실패: {len(missing_methods)}개 메서드"
                )

                return VerificationResult(
                    verified=False,
                    grounding_score=0.0,
                    confidence_level=confidence_level,
                    claims=claims,
                    unverified_claims=[
                        {
                            "claim_type": "missing_method",
                            "text": f"{call_result['method_call'].object_name}.{call_result['method_call'].method_name}()",
                            "reason": call_result["reason"],
                        }
                        for call_result in missing_methods
                    ],
                    requires_retry=True,
                    retry_reason=f"Missing methods detected ({len(missing_methods)} methods)",
                    referenced_contexts=[],
                )

        if not claims:
            # Claim 없으면 검증 불필요
            logger.info("[ULTRATHINK] Claim 없음 - 빈 결과 반환")
            return VerificationResult(
                verified=True,
                grounding_score=0.5,  # Bug Fix: Claim 없음 = 검증 불가 = 중간 점수 (0.5)
                confidence_level=confidence_level,
                claims=[],
                unverified_claims=[],
                requires_retry=False,
                referenced_contexts=[],
                verified_claims=[],
                pending_claims=[],
                claim_grounding_scores={},
            )

        # 3. ULTRATHINK: MEDIUM/LOW 그룹은 pending_claims로 추가
        pending_claims = []
        for claim_info in medium_confidence_claims + low_confidence_claims:
            pending_claims.append({
                "claim_type": claim_info["claim"].claim_type,
                "text": claim_info["claim"].text,
                "fuzzy_score": claim_info["fuzzy_score"],
                "confidence_level": claim_info["confidence_level"],
                "reason": "확신도 낮음 - 작업 미완료 또는 불확실",
            })

        logger.info(f"[ULTRATHINK] {len(pending_claims)}개 Claim 검증 보류 (확신도 낮음)")

        # 4. ULTRATHINK: HIGH 그룹만 검증 수행
        unverified_claims = []
        verified_claims = []
        claim_grounding_scores = {}

        # ULTRATHINK: HIGH 그룹만 검증 (high_confidence_claims 직접 반복)
        logger.info(f"[ULTRATHINK] {len(high_confidence_claims)}개 HIGH confidence Claim 검증 시작")

        # CRITICAL FIX: context에서 referenced_contexts 먼저 확인 (Phase 9.4 통합)
        referenced_contexts = (context or {}).get("referenced_contexts", [])
        if referenced_contexts:
            logger.info(f"✅ Evidence Graph에서 referenced_contexts 사용: {len(referenced_contexts)}개")
        else:
            logger.info("⚠️ Evidence Graph 없음 - _collect_evidence로 대체")
            referenced_contexts = []

        # ClaimVerifier와 GroundingScorer 초기화 (필요 시)
        claim_verifier = self._get_claim_verifier(context or {})
        grounding_scorer = self._get_grounding_scorer(context or {})

        # BUG FIX: context에서 file_contents를 Evidence Graph에 추가
        self._populate_evidence_graph_from_context(context or {}, claim_verifier)

        # referenced_contexts가 없을 때만 _collect_evidence 호출 (Fallback)
        if not referenced_contexts:
            for claim_info in high_confidence_claims:
                claim = claim_info["claim"]
                # 증거 수집 (context에서)
                evidence = self._collect_evidence(claim, context or {})

                # 증거를 referenced_contexts로 변환 (파일 경로 추출)
                for ev in evidence:
                    if ev not in referenced_contexts:
                        referenced_contexts.append(ev)

        # Claim 검증 (referenced_contexts가 있든 없든 수행)
        # 신규: Claim별 Evidence 매핑 초기화
        claim_evidence_map = {}

        # ULTRATHINK: HIGH 그룹 claim_info 반복 (fuzzy_score, confidence_level 접근 가능)
        timeout_occurred = False  # BUG FIX: 타임아웃 플래그
        for claim_info in high_confidence_claims:
            # BUG FIX: 루프 시작 시 타임아웃 체크
            if _check_timeout("claim_verification_loop"):
                timeout_occurred = True
                logger.warning(f"[TIMEOUT] Claim 검증 루프 중단 - 남은 claims: {len(high_confidence_claims) - high_confidence_claims.index(claim_info)}개")
                break

            claim = claim_info["claim"]
            # Claim ID 생성
            claim_id = f"{claim.claim_type}:{claim.start}:{claim.end}"
            claim_files = []  # 이 Claim만의 파일 목록

            # Evidence Graph 기반 검증
            if claim_verifier:
                # DEBUG: context 파라미터 확인 (타임아웃 시 스킵)
                if not _check_timeout("debug_logging"):
                    print(f"[DEBUG-AUTO_VERIFIER] claim_verifier.verify_claim 호출 직전")
                    print(f"[DEBUG-AUTO_VERIFIER]   - context type: {type(context)}")
                    print(f"[DEBUG-AUTO_VERIFIER]   - context is None: {context is None}")
                    if context:
                        print(f"[DEBUG-AUTO_VERIFIER]   - context keys: {context.keys()}")
                        print(f"[DEBUG-AUTO_VERIFIER]   - 'files_modified' in context: {'files_modified' in context}")
                    print(f"[DEBUG-AUTO_VERIFIER]   - context or {{}} 결과: {type(context or {})}")

                # BUG FIX: verify_claim의 두 번째 파라미터는 context_history (Dict)
                verify_result = claim_verifier.verify_claim(claim, context or {})

                # BUG FIX: 검증 결과에서 evidence를 추출하여 referenced_contexts에 추가
                if verify_result.get("evidence"):
                    for evidence_item in verify_result["evidence"]:
                        # Evidence dict에서 파일 경로 추출
                        if isinstance(evidence_item, dict):
                            # file_specific_diff 타입: verified_files 필드에 파일 경로 리스트
                            if evidence_item.get("type") == "file_specific_diff":
                                verified_files = evidence_item.get("verified_files", [])
                                claim_files.extend(verified_files)  # 신규: Claim별 파일 추적
                                for file_path in verified_files:
                                    if file_path not in referenced_contexts:
                                        referenced_contexts.append(file_path)
                                        logger.info(f"[Evidence Matching] referenced_contexts에 추가: {file_path}")
                            # evidence_graph_files, codebase_verified, content_matched_files 타입: files 필드에 파일 목록
                            elif evidence_item.get("type") in ["evidence_graph_files", "codebase_verified", "evidence_graph_diff", "git_diff", "content_matched_files"]:
                                files_list = evidence_item.get("files", [])
                                if files_list:
                                    claim_files.extend(files_list)  # 신규: Claim별 파일 추적
                                    for file_path in files_list:
                                        if file_path not in referenced_contexts:
                                            referenced_contexts.append(file_path)
                                            logger.info(f"[Evidence Matching] referenced_contexts에 추가: {file_path} (from {evidence_item.get('type')})")
                            # Phase 9.6 FIX: indirect_reference 타입 처리 추가
                            elif evidence_item.get("type") == "indirect_reference":
                                # indirect_reference는 original_evidence 필드에 실제 evidence 포함
                                original_evidence = evidence_item.get("original_evidence", {})
                                files_list = original_evidence.get("files", [])
                                if files_list:
                                    claim_files.extend(files_list)  # 신규: Claim별 파일 추적
                                    for file_path in files_list:
                                        if file_path not in referenced_contexts:
                                            referenced_contexts.append(file_path)
                                            logger.info(f"[Evidence Matching] referenced_contexts에 추가: {file_path} (from indirect_reference)")
                            # 기타 타입: file_path 필드 직접 확인
                            elif "file_path" in evidence_item:
                                file_path = evidence_item["file_path"]
                                claim_files.append(file_path)  # 신규: Claim별 파일 추적
                                if file_path not in referenced_contexts:
                                    referenced_contexts.append(file_path)
                                    logger.info(f"[Evidence Matching] referenced_contexts에 추가: {file_path}")

                # ULTRATHINK: 검증 결과 처리
                if verify_result.get("verified", False):
                    # 검증 성공 시 verified_claims에 추가
                    evidence_count = len(verify_result.get("evidence", []))

                    # 개별 Claim의 grounding score 계산
                    # (Evidence 개수 기반 간이 점수: 증거 많을수록 높은 점수)
                    individual_score = min(1.0, evidence_count * 0.3)  # 최대 1.0

                    verified_claims.append({
                        "claim_type": claim.claim_type,
                        "text": claim.text,
                        "fuzzy_score": claim_info["fuzzy_score"],
                        "confidence_level": claim_info["confidence_level"],
                        "evidence_count": evidence_count,
                        "grounding_score": individual_score,
                    })

                    claim_grounding_scores[claim_id] = individual_score
                    logger.info(f"[ULTRATHINK] Claim 검증 성공: {claim.text[:50]}... (score: {individual_score:.2f})")
                else:
                    # 검증 실패 시 unverified_claims에 추가
                    unverified_claims.append(
                        {
                            "claim_type": claim.claim_type,
                            "text": claim.text,
                            "reason": verify_result.get("reason", "증거 부족"),
                        }
                    )
            else:
                # ClaimVerifier 없으면 검증 불가
                unverified_claims.append(
                    {
                        "claim_type": claim.claim_type,
                        "text": claim.text,
                        "reason": "ClaimVerifier 없음",
                    }
                )

            # 신규: Claim별 매핑 저장
            claim_evidence_map[claim_id] = claim_files

        # BUG FIX: 타임아웃 발생 시 조기 반환
        if timeout_occurred or _check_timeout("before_grounding_scorer"):
            logger.warning("[TIMEOUT] 타임아웃으로 인해 검증 조기 종료")
            return VerificationResult(
                verified=False,
                grounding_score=0.0,
                confidence_level=confidence_level,
                claims=claims,
                unverified_claims=[{
                    "claim_type": "timeout",
                    "text": "검증 타임아웃",
                    "reason": f"검증 시간 초과 ({VERIFICATION_TIMEOUT_SECONDS}초)",
                }],
                requires_retry=False,  # 타임아웃은 재시도하지 않음
                retry_reason="검증 타임아웃 - 결과 없이 종료",
                referenced_contexts=referenced_contexts,
                claim_evidence_map=claim_evidence_map,
                verified_claims=verified_claims,
                pending_claims=pending_claims,
                claim_grounding_scores=claim_grounding_scores,
            )

        # 4. Grounding Score 계산 (전체 응답에 대해 한 번만)
        if grounding_scorer:
            # [DEBUG] claim_evidence_map 상태 로깅
            print(f"\n[DEBUG-AUTO_VERIFIER] claim_evidence_map before grounding_scorer:")
            print(f"  - Map keys: {list(claim_evidence_map.keys())}")
            print(f"  - Map values: {claim_evidence_map}")
            print(f"  - Total claims: {len(claims)}")

            # GroundingScorer가 있으면 항상 사용 (referenced_contexts가 비어있어도)
            grounding_result = grounding_scorer.calculate_score(
                response_text=response_text,
                claims=claims,
                referenced_contexts=referenced_contexts,
                context_history=context,
                claim_evidence_map=claim_evidence_map  # 신규: Claim별 매핑 전달
            )
            avg_score = grounding_result["grounding_score"]

            # Phase 9 개선: 성능 주장 정보 추출 (정보 제공용)
            performance_info = grounding_result.get("performance_claims", {})

            # [DEBUG] grounding_result 로깅
            print(f"[DEBUG-AUTO_VERIFIER] grounding_result:")
            print(f"  - grounding_score: {avg_score}")
            print(f"  - verified_claims: {grounding_result.get('verified_claims', 'N/A')}")
            print(f"  - total_claims: {grounding_result.get('total_claims', 'N/A')}")
            print(f"  - performance_claims: {performance_info}")
            print(f"  - mode: {grounding_result.get('mode', 'N/A')}")
        else:
            # GroundingScorer 없으면 간단한 계산: contexts / claims
            if claims:
                avg_score = len(referenced_contexts) / len(claims)
            else:
                avg_score = 1.0 if referenced_contexts else 0.0
            performance_info = {}  # GroundingScorer 없으면 빈 dict

        # 5. 재수행 필요 여부 판단
        requires_retry = avg_score < VERIFICATION_PASS_THRESHOLD
        retry_reason = None

        if requires_retry:
            retry_reason = (
                f"근거 부족 (Grounding Score: {avg_score:.2f} < {VERIFICATION_PASS_THRESHOLD}). "
                f"검증 실패한 주장: {len(unverified_claims)}개"
            )

        # ULTRATHINK: 검증 통계 계산
        total_high_claims = len(high_confidence_claims)
        verified_count = len(verified_claims)
        unverified_count = len(unverified_claims)
        pending_count = len(pending_claims)

        logger.info(f"[ULTRATHINK] 검증 완료 통계:")
        logger.info(f"  - HIGH confidence claims: {total_high_claims}개")
        logger.info(f"  - 검증 통과: {verified_count}개")
        logger.info(f"  - 검증 실패: {unverified_count}개")
        logger.info(f"  - 검증 보류 (MEDIUM/LOW): {pending_count}개")

        return VerificationResult(
            verified=not requires_retry,
            grounding_score=avg_score,
            confidence_level=confidence_level,
            claims=claims,
            unverified_claims=unverified_claims,
            requires_retry=requires_retry,
            retry_reason=retry_reason,
            referenced_contexts=referenced_contexts,
            claim_evidence_map=claim_evidence_map,
            # ULTRATHINK MODE: 확신도별 분류 결과
            verified_claims=verified_claims,
            pending_claims=pending_claims,
            claim_grounding_scores=claim_grounding_scores,
            # Phase 9 개선: 성능 주장 정보
            performance_claims=performance_info,
        )

    def _get_claim_verifier(self, context: Dict[str, Any]):
        """
        ClaimVerifier 인스턴스 반환 (Lazy initialization)

        Args:
            context: 검증 컨텍스트 (project_id, project_path, claim_verifier 포함 가능)

        Returns:
            ClaimVerifier 인스턴스

        Raises:
            ValueError: project_id 또는 project_path가 없을 때
        """
        # CRITICAL FIX: context에서 memory_manager의 ClaimVerifier 우선 사용
        if "claim_verifier" in context and context["claim_verifier"] is not None:
            verifier = context["claim_verifier"]
            print(f"[DEBUG] auto_verifier: memory_manager의 ClaimVerifier 사용 (Evidence Graph 공유)")
            print(f"[DEBUG]   - ClaimVerifier Evidence Graph 객체 ID: {id(verifier.evidence_graph)}")
            print(f"[DEBUG]   - Evidence Graph 파일 경로: {verifier.evidence_graph._get_graph_path()}")
            return verifier

        project_id = context.get("project_id")
        project_path = context.get("project_path")

        if not project_id:
            raise ValueError(
                "project_id is required for claim verification.\n"
                "Please provide project_id in the context parameter."
            )

        if not project_path:
            raise ValueError(
                "project_path is required for claim verification.\n"
                "Please provide project_path in the context parameter."
            )

        # CACHE REMOVED: 항상 새로운 ClaimVerifier 생성 (정확성 > 성능)
        # - 파일 수정 후 Evidence Graph가 변경되므로 캐시 사용 불가
        # - 매번 최신 Evidence Graph를 사용하여 정확한 검증 수행 (~100ms 추가)
        from core.claim_verifier import ClaimVerifier

        verifier = ClaimVerifier(project_id=project_id, project_path=project_path)
        return verifier

    def _get_grounding_scorer(self, context: Dict[str, Any]):
        """
        GroundingScorer 인스턴스 반환 (Lazy initialization)

        Args:
            context: 검증 컨텍스트 (project_id, project_path 포함)

        Returns:
            GroundingScorer 인스턴스

        Raises:
            ValueError: project_id 또는 project_path가 없을 때
        """
        project_id = context.get("project_id")
        project_path = context.get("project_path")

        if not project_id:
            raise ValueError(
                "project_id is required for hallucination verification.\n"
                "Please provide project_id in the context parameter.\n"
                "Example: verify_response(response_text, context={'project_id': 'test', 'project_path': '/path/to/project'})"
            )

        if not project_path:
            raise ValueError(
                "project_path is required for hallucination verification.\n"
                "Evidence Graph needs to know where to store/load verification data.\n"
                "Please provide project_path in the context parameter.\n"
                "Example: verify_response(response_text, context={'project_id': 'test', 'project_path': '/path/to/project'})"
            )

        # CACHE REMOVED: 항상 새로운 GroundingScorer 생성 (정확성 > 성능)
        # - 파일 수정 후 Evidence Graph가 변경되므로 캐시 사용 불가
        # - ClaimVerifier의 Evidence Graph를 공유하여 최신 상태 반영 (~50ms 추가)
        from core.grounding_scorer import GroundingScorer

        scorer = GroundingScorer(project_id=project_id, project_path=project_path)

        # CRITICAL: ClaimVerifier의 Evidence Graph를 공유
        # GroundingScorer가 자체 Evidence Graph를 생성하지만,
        # ClaimVerifier가 파일 노드를 추가하므로 동일한 그래프를 참조해야 함
        verifier = self._get_claim_verifier(context)
        scorer.evidence_graph = verifier.evidence_graph

        return scorer

    def _confidence_to_score(self, confidence_level: str) -> float:
        """
        확신도 레벨을 점수로 변환

        Args:
            confidence_level: very_high, high, medium, low, none

        Returns:
            float: 0.0-1.0 점수

        Note:
            Phase 9.7: hallucination_constants.py의 CONFIDENCE_SCORES 사용
            "none"은 0.5 (neutral) - 확신도 표현이 없는 것은 "틀림"이 아닌 "중립"
        """
        # Phase 9.7: 중앙 상수 사용 (hallucination_constants.py)
        return CONFIDENCE_SCORES.get(confidence_level, 0.5)

    def _collect_evidence(self, claim: Claim, context: Dict[str, Any]) -> List[str]:
        """
        Claim에 대한 증거 수집

        Args:
            claim: 검증할 주장
            context: 검증 컨텍스트

        Returns:
            List[str]: 수집된 증거 목록
        """
        evidence = []

        # context에서 증거 추출
        if "file_contents" in context:
            # 파일 내용 검증
            for file_path, content in context["file_contents"].items():
                if claim.text in content:
                    evidence.append(f"파일 {file_path}에서 발견")

        if "test_results" in context:
            # 테스트 결과 검증
            test_output = context["test_results"]
            if any(keyword in test_output for keyword in ["PASSED", "passed", "성공", "완료"]):
                evidence.append("테스트 결과에서 확인됨")

        if "command_output" in context:
            # 명령 출력 검증
            output = context["command_output"]
            if claim.text in output:
                evidence.append("명령 출력에서 확인됨")

        return evidence

    def _populate_evidence_graph_from_context(
        self, context: Dict[str, Any], claim_verifier
    ) -> None:
        """
        BUG FIX: context에서 Evidence Graph에 파일 노드 추가

        Args:
            context: 검증 컨텍스트 (file_contents, test_results 등 포함)
            claim_verifier: ClaimVerifier 인스턴스 (Evidence Graph 포함)

        Note:
            이 메서드는 verify_response 호출 시마다 실행되어
            context의 file_contents를 Evidence Graph에 노드로 추가합니다.
            이를 통해 Evidence Matching이 정상적으로 작동합니다.
        """
        if not claim_verifier or not hasattr(claim_verifier, "evidence_graph"):
            logger.warning("[Evidence Graph] ClaimVerifier에 Evidence Graph 없음")
            return

        evidence_graph = claim_verifier.evidence_graph
        import hashlib
        from datetime import datetime

        # file_contents를 Evidence Graph에 추가
        if "file_contents" in context:
            for file_path, content in context["file_contents"].items():
                # content hash 생성
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

                # 파일 노드 추가
                success = evidence_graph.add_file_node(
                    file_path=file_path,
                    last_modified=datetime.now().isoformat(),
                    content_hash=content_hash,
                    metadata={"source": "context", "content_length": len(content)}
                )

                if success:
                    logger.info(f"[Evidence Graph] 파일 노드 추가: {file_path} (hash: {content_hash})")
                else:
                    logger.debug(f"[Evidence Graph] 파일 노드 이미 존재: {file_path}")

        # test_results를 Evidence Graph에 추가 (task node로)
        if "test_results" in context:
            task_id = f"test_result_{datetime.now().timestamp()}"
            evidence_graph.add_task_node(
                task_id=task_id,
                task_type="test_execution",
                description="테스트 실행 결과",
                metadata={"test_output": context["test_results"]}
            )
            logger.info(f"[Evidence Graph] 테스트 결과 노드 추가: {task_id}")

    def format_retry_message(self, result: VerificationResult) -> str:
        """
        재수행 메시지 포맷

        Args:
            result: 검증 결과

        Returns:
            str: 사용자에게 표시할 메시지
        """
        if not result.requires_retry:
            return ""

        msg = "⚠️ 검증 중 근거 부족 발견. 재확인하겠습니다.\n\n"
        msg += f"사유: {result.retry_reason}\n"
        msg += f"확신도: {result.confidence_level}\n"
        msg += f"Grounding Score: {result.grounding_score:.2f}\n\n"

        # Issue #3: referenced_contexts 표시
        if result.referenced_contexts:
            msg += f"참조한 맥락 ({len(result.referenced_contexts)}개):\n"
            for ctx in result.referenced_contexts:
                msg += f"  - {ctx}\n"
            msg += "\n"

        if result.unverified_claims:
            msg += "검증 실패한 주장:\n"
            for i, claim in enumerate(result.unverified_claims, 1):
                msg += f"{i}. [{claim['claim_type']}] {claim['text']}\n"
                msg += f"   사유: {claim['reason']}\n"
            msg += "\n"

        # Phase 9 개선: 성능 정보 별도 표시 (정보 제공용)
        if result.performance_claims and result.performance_claims.get("total", 0) > 0:
            msg += "📊 성능 정보 (예상값 - 검증 대상 아님):\n"
            for claim in result.performance_claims.get("claims", []):
                msg += f"  - {claim['text']}\n"
            msg += "  * 성능 주장은 정보 제공용이며 구현 검증과 무관합니다.\n"

        return msg

    def format_verified_message(self, result: VerificationResult) -> str:
        """
        검증 완료 메시지 포맷

        Args:
            result: 검증 결과

        Returns:
            str: 사용자에게 표시할 메시지
        """
        if result.requires_retry:
            return ""

        msg = f"✅ 구현 검증: PASS (Grounding Score: {result.grounding_score:.2f})\n"

        # Issue #3: referenced_contexts 표시
        if result.referenced_contexts:
            msg += f"참조한 맥락 ({len(result.referenced_contexts)}개):\n"
            for ctx in result.referenced_contexts:
                msg += f"  - {ctx}\n"
            msg += "\n"

        # Phase 9 개선: 성능 정보 별도 표시 (정보 제공용)
        if result.performance_claims and result.performance_claims.get("total", 0) > 0:
            msg += "📊 성능 정보 (예상값 - 실측 미정):\n"
            for claim in result.performance_claims.get("claims", []):
                msg += f"  - {claim['text']}\n"
            msg += "  * 성능 주장은 정보 제공용이며 검증 대상이 아닙니다.\n"
            msg += "  * 실제 성능은 Phase 5 벤치마크에서 측정 예정입니다.\n"

        return msg


# 싱글톤 인스턴스
_auto_verifier = None


def get_auto_verifier() -> AutoVerifier:
    """AutoVerifier 싱글톤 인스턴스 반환"""
    global _auto_verifier
    if _auto_verifier is None:
        _auto_verifier = AutoVerifier()
    return _auto_verifier
