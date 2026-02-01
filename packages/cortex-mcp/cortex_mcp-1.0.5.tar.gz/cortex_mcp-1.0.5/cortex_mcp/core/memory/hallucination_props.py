"""
Cortex MCP - Hallucination Properties Mixin
Phase 9: Hallucination Detection Lazy Loading Properties

기능:
- ClaimExtractor lazy loading
- ClaimVerifier lazy loading
- FuzzyClaimAnalyzer lazy loading
- ContradictionDetectorV2 lazy loading
- GroundingScorer lazy loading
- CodeStructureAnalyzer lazy loading
"""

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Config import
try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from config import config
except ImportError:
    config = None


class HallucinationPropsMixin:
    """
    Hallucination Detection Lazy Loading Properties Mixin

    MemoryManager에 믹스인으로 사용
    - 각 프로퍼티는 첫 접근 시에만 초기화됨
    - Feature Flag 체크 후 비활성화 시 None 반환
    """

    # 인스턴스 변수 (MemoryManager.__init__에서 초기화 필요)
    _claim_extractor: Any = None
    _claim_verifier: Any = None
    _fuzzy_analyzer: Any = None
    _contradiction_detector: Any = None
    _grounding_scorer: Any = None
    _code_structure_analyzer: Any = None
    project_id: Optional[str] = None

    @property
    def claim_extractor(self):
        """
        Lazy loading: ClaimExtractor (Phase 9)

        Feature Flag 체크 후 첫 접근 시에만 초기화
        """
        if self._claim_extractor is None:
            if config and not config.feature_flags.hallucination_detection_enabled:
                return None
            if not self.project_id:
                return None

            try:
                # 상위 core 디렉토리에서 import
                import sys
                from pathlib import Path
                core_path = Path(__file__).parent.parent
                if str(core_path) not in sys.path:
                    sys.path.insert(0, str(core_path))
                from claim_extractor import ClaimExtractor
                self._claim_extractor = ClaimExtractor()
                logger.info("[LAZY_LOAD] ClaimExtractor 초기화 완료 (Phase 9)")
            except Exception as e:
                logger.error(f"[LAZY_LOAD] ClaimExtractor 초기화 실패: {e}")
                self._claim_extractor = None

        return self._claim_extractor

    @property
    def claim_verifier(self):
        """
        Lazy loading: ClaimVerifier (Phase 9)

        Feature Flag 체크 후 첫 접근 시에만 초기화
        EvidenceGraph를 내부적으로 생성
        """
        if self._claim_verifier is None:
            if config and not config.feature_flags.hallucination_detection_enabled:
                return None
            if not self.project_id:
                return None

            try:
                from ..claim_verifier import ClaimVerifier
                actual_project_path = str(Path.cwd())
                self._claim_verifier = ClaimVerifier(
                    project_id=self.project_id,
                    project_path=actual_project_path
                )
                logger.info("[LAZY_LOAD] ClaimVerifier 초기화 완료 (Phase 9)")
            except Exception as e:
                logger.error(f"[LAZY_LOAD] ClaimVerifier 초기화 실패: {e}")
                self._claim_verifier = None

        return self._claim_verifier

    @property
    def fuzzy_analyzer(self):
        """
        Lazy loading: FuzzyClaimAnalyzer (Phase 9)

        Feature Flag 체크 후 첫 접근 시에만 초기화
        """
        if self._fuzzy_analyzer is None:
            if config and not config.feature_flags.hallucination_detection_enabled:
                return None
            if not self.project_id:
                return None

            try:
                from ..fuzzy_claim_analyzer import FuzzyClaimAnalyzer
                self._fuzzy_analyzer = FuzzyClaimAnalyzer()
                logger.info("[LAZY_LOAD] FuzzyClaimAnalyzer 초기화 완료 (Phase 9.6 - AI Only)")
            except Exception as e:
                logger.error(f"[LAZY_LOAD] FuzzyClaimAnalyzer 초기화 실패: {e}")
                self._fuzzy_analyzer = None

        return self._fuzzy_analyzer

    @property
    def contradiction_detector(self):
        """
        Lazy loading: ContradictionDetectorV2 (Phase 9)

        Feature Flag 체크 후 첫 접근 시에만 초기화
        """
        if self._contradiction_detector is None:
            if config and not config.feature_flags.hallucination_detection_enabled:
                return None
            if not self.project_id:
                return None

            try:
                from ..contradiction_detector_v2 import ContradictionDetectorV2
                self._contradiction_detector = ContradictionDetectorV2()
                logger.info("[LAZY_LOAD] ContradictionDetectorV2 초기화 완료 (Phase 9)")
            except Exception as e:
                logger.error(f"[LAZY_LOAD] ContradictionDetectorV2 초기화 실패: {e}")
                self._contradiction_detector = None

        return self._contradiction_detector

    @property
    def grounding_scorer(self):
        """
        Lazy loading: GroundingScorer (Phase 9)

        Feature Flag 체크 후 첫 접근 시에만 초기화
        CRITICAL: ClaimVerifier의 EvidenceGraph를 공유 (의존성 유지)
        """
        if self._grounding_scorer is None:
            if config and not config.feature_flags.hallucination_detection_enabled:
                return None
            if not self.project_id:
                return None

            try:
                from ..grounding_scorer import GroundingScorer
                actual_project_path = str(Path.cwd())

                # CRITICAL: ClaimVerifier property 먼저 호출하여 EvidenceGraph 생성
                claim_verifier = self.claim_verifier
                if claim_verifier is None:
                    logger.warning("[LAZY_LOAD] GroundingScorer 초기화 실패: ClaimVerifier 없음")
                    return None

                # ClaimVerifier의 EvidenceGraph를 GroundingScorer에 주입
                self._grounding_scorer = GroundingScorer(
                    project_id=self.project_id,
                    project_path=actual_project_path,
                    evidence_graph=claim_verifier.evidence_graph
                )
                logger.info("[LAZY_LOAD] GroundingScorer 초기화 완료 (Phase 9) - EvidenceGraph 공유")
            except Exception as e:
                logger.error(f"[LAZY_LOAD] GroundingScorer 초기화 실패: {e}")
                self._grounding_scorer = None

        return self._grounding_scorer

    @property
    def code_structure_analyzer(self):
        """
        Lazy loading: CodeStructureAnalyzer (Phase 9)

        Feature Flag 체크 후 첫 접근 시에만 초기화
        """
        if self._code_structure_analyzer is None:
            if config and not config.feature_flags.hallucination_detection_enabled:
                return None
            if not self.project_id:
                return None

            try:
                from ..code_structure_analyzer import CodeStructureAnalyzer
                actual_project_path = str(Path.cwd())
                self._code_structure_analyzer = CodeStructureAnalyzer(project_path=actual_project_path)
                logger.info("[LAZY_LOAD] CodeStructureAnalyzer 초기화 완료 (Phase 9)")
            except Exception as e:
                logger.error(f"[LAZY_LOAD] CodeStructureAnalyzer 초기화 실패: {e}")
                self._code_structure_analyzer = None

        return self._code_structure_analyzer

    def reset_hallucination_components(self) -> None:
        """Hallucination Detection 컴포넌트 리셋 (테스트용)"""
        self._claim_extractor = None
        self._claim_verifier = None
        self._fuzzy_analyzer = None
        self._contradiction_detector = None
        self._grounding_scorer = None
        self._code_structure_analyzer = None
        logger.info("[RESET] Hallucination Detection 컴포넌트 리셋 완료")
