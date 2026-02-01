"""
Cortex MCP - Memory Manager
F/S I/O 및 트리 생성 관리

기능:
- Context Tree (브랜치) 생성 및 관리
- 대화 기록 저장 (.md 파일)
- YAML Frontmatter 메타데이터 관리
- 자동 요약 트리거 및 갱신
- 추출적 요약 생성 (Zero-Trust: 외부 API 없이 로컬에서 처리)
- 온톨로지 기반 자동 분류 (v2.1)
"""

import json
import logging
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import portalocker
import yaml

# Logger 초기화
logger = logging.getLogger(__name__)

sys.path.append(str(Path(__file__).parent.parent))
from config import Tier, config

# Memory 서브 모듈 import (분리된 기능들)
from .memory import (
    BranchManager,
    ContextLoader,
    FileIO,
    NodeManager,
    SummaryGenerator,
)

# Multiprocessing 백그라운드 프로세서 (threading 대체)
from .background_processor import get_background_processor, worker_indexing_task

# 온톨로지 엔진 (선택적 로드 - 티어별 활성화)
try:
    from .ontology_engine import OntologyEngine

    ONTOLOGY_AVAILABLE = True
except ImportError:
    ONTOLOGY_AVAILABLE = False
    OntologyEngine = None

# 시맨틱 웹 엔진 (Enterprise 전용)
try:
    from .semantic_web import RelationType, SemanticWebEngine

    SEMANTIC_WEB_AVAILABLE = True
except ImportError:
    SEMANTIC_WEB_AVAILABLE = False
    SemanticWebEngine = None
    RelationType = None

# 브랜치 결정 엔진 (자동 맥락 생성 - 핵심 기능)
try:
    from .branch_decision_engine import BranchDecisionEngine, NodeGroupingEngine

    BRANCH_DECISION_AVAILABLE = True
except ImportError:
    BRANCH_DECISION_AVAILABLE = False
    BranchDecisionEngine = None
    NodeGroupingEngine = None

# Reference History (맥락 참조 이력 - Pro 이상)
try:
    from .reference_history import ReferenceHistory

    REFERENCE_HISTORY_AVAILABLE = True
except ImportError:
    REFERENCE_HISTORY_AVAILABLE = False
    ReferenceHistory = None

# Smart Context Manager (압축/해제, Lazy Loading - Pro 이상)
try:
    from .context_manager import ContextManager

    CONTEXT_MANAGER_AVAILABLE = True
except ImportError:
    CONTEXT_MANAGER_AVAILABLE = False
    ContextManager = None

# Context Relationship Graph (Pro+ - 맥락 간 관계 추적)
try:
    from .relationship_graph import RelationshipGraph
    from .semantic_relationship import SemanticRelationshipEngine

    RELATIONSHIP_GRAPH_AVAILABLE = True
except ImportError:
    RELATIONSHIP_GRAPH_AVAILABLE = False
    RelationshipGraph = None
    SemanticRelationshipEngine = None

# Telemetry (사용 지표 자동 수집)
try:
    from .telemetry_decorator import track_call
    from .telemetry_client import get_telemetry_client

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    get_telemetry_client = None

    # Noop decorator when telemetry not available
    def track_call(module_name: str):
        def decorator(func):
            return func

        return decorator

# Auto Verifier (할루시네이션 자동 검증 - Phase 9)
try:
    from .auto_verifier import get_auto_verifier

    AUTO_VERIFIER_AVAILABLE = True
except ImportError:
    AUTO_VERIFIER_AVAILABLE = False
    get_auto_verifier = None

# PayAttention (세션 내 Attention 보존 - Pro 이상)
try:
    from .pay_attention import (
        PayAttentionEngine,
        TriggerType,
        get_pay_attention_engine,
        reset_pay_attention_engine,
    )

    PAY_ATTENTION_AVAILABLE = True
except ImportError:
    PAY_ATTENTION_AVAILABLE = False
    PayAttentionEngine = None
    TriggerType = None
    get_pay_attention_engine = None
    reset_pay_attention_engine = None

# Fuzzy Prompt (퍼지 검색 및 힌트 생성 - Pro 이상)
try:
    from .fuzzy_prompt import FuzzyPromptIntegrator, get_fuzzy_prompt_integrator

    FUZZY_PROMPT_AVAILABLE = True
except ImportError:
    FUZZY_PROMPT_AVAILABLE = False
    FuzzyPromptIntegrator = None
    get_fuzzy_prompt_integrator = None

# Hallucination Detection Thresholds (Phase 9.3 → 9.7: 중앙 상수 통일)
# 유저 설정 가능 - 3-Tier Decision System
# Balanced Mode: 10-15% human review, 85-90% 정확도
from .hallucination_constants import HALLUCINATION_THRESHOLDS


def generate_task_id() -> str:
    """
    Hybrid task_id 생성: timestamp + UUID (짧은 버전)

    형식: task_{timestamp}_{uuid_short}
    예시: task_20250627_143052_abc1

    장점:
    - 가독성: 타임스탬프로 언제 작업했는지 파악 가능
    - 정렬: 문자열 정렬 = 시간순 정렬
    - 고유성: UUID 4자리로 동일 초 내 충돌 방지
    - 간결성: 전체 길이 25자

    Returns:
        생성된 task_id
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    uuid_short = uuid.uuid4().hex[:4]  # UUID 앞 4자리만 사용
    return f"task_{timestamp}_{uuid_short}"


# Phase 9: Hallucination Detection System (모든 티어에서 사용 가능)
try:
    from .claim_extractor import ClaimExtractor
    from .claim_verifier import ClaimVerifier
    from .code_structure_analyzer import CodeStructureAnalyzer
    from .contradiction_detector_v2 import ContradictionDetectorV2
    from .fuzzy_claim_analyzer import FuzzyClaimAnalyzer
    from .grounding_scorer import GroundingScorer

    HALLUCINATION_DETECTION_AVAILABLE = True
except ImportError:
    HALLUCINATION_DETECTION_AVAILABLE = False
    ClaimExtractor = None
    ClaimVerifier = None
    FuzzyClaimAnalyzer = None
    ContradictionDetectorV2 = None
    GroundingScorer = None
    CodeStructureAnalyzer = None

# Research Logger (Phase 9 Integration - 논문 데이터 수집)
try:
    from .research_logger import (
        create_cortex_intervention_event,
        create_llm_response_event,
        log_event_sync,
        InterventionType,
    )
    RESEARCH_LOGGER_AVAILABLE = True
except ImportError:
    RESEARCH_LOGGER_AVAILABLE = False
    create_cortex_intervention_event = None
    create_llm_response_event = None
    log_event_sync = None
    InterventionType = None

# Phase 9.2: Git Evidence Collection
try:
    from .phase92_git_evidence import populate_from_git

    PHASE92_AVAILABLE = True
except ImportError:
    PHASE92_AVAILABLE = False
    populate_from_git = None

# Phase 9.4: Initial Codebase Scan
try:
    from .phase94_initial_scan import populate_from_scan

    PHASE94_AVAILABLE = True
except ImportError:
    PHASE94_AVAILABLE = False
    populate_from_scan = None

# Evidence Graph v2
try:
    from .evidence_graph_v2 import get_evidence_graph_v2

    EVIDENCE_GRAPH_V2_AVAILABLE = True
except ImportError:
    EVIDENCE_GRAPH_V2_AVAILABLE = False
    get_evidence_graph_v2 = None


def sanitize_input(value: str, max_length: int = 255) -> str:
    """
    입력값 살균 - 보안 취약점 방지

    방어 대상:
    - Path Traversal (../, ..\\)
    - Null Byte Injection (\x00)
    - 특수 문자 (파일명 불가)
    - 과도하게 긴 입력
    """
    if not value:
        return ""

    # Null byte 제거
    value = value.replace("\x00", "")

    # Path traversal 패턴 제거
    value = re.sub(r"\.\.[\\/]", "", value)
    value = re.sub(r"[\\/]\.\.", "", value)

    # 절대 경로 시작 방지
    value = re.sub(r"^[\\/]", "", value)
    value = re.sub(r"^[a-zA-Z]:[\\/]", "", value)

    # 파일명에 사용 불가한 문자 제거/치환
    # Windows: < > : " / \ | ? *
    # Unix: / null
    value = re.sub(r'[<>:"/\\|?*]', "_", value)

    # 제어 문자 제거 (0x00-0x1F)
    value = re.sub(r"[\x00-\x1f]", "", value)

    # 길이 제한
    if len(value) > max_length:
        value = value[:max_length]

    # 앞뒤 공백 및 점 제거 (Windows 파일명 제한)
    value = value.strip(" .")

    return value


class MemoryManager:
    """메모리 관리자 - Context Tree 및 파일 I/O (v2.2: Feature Flags + 시맨틱 웹)"""

    # Node 자동 제안 임계치
    NODE_SUGGESTION_THRESHOLD = 30

    def __init__(self, project_id: Optional[str] = None, memory_dir: Optional[Path] = None):
        """
        Args:
            project_id: 프로젝트 ID (시맨틱 웹 엔진용)
            memory_dir: 메모리 저장 디렉토리 (테스트용, 기본값=config.memory_dir)
        """
        self.memory_dir = Path(memory_dir) if memory_dir else config.memory_dir
        self.logs_dir = config.logs_dir
        self.max_size_kb = config.max_context_size_kb
        self.project_id = project_id

        # Memory 서브 모듈 초기화 (composition 패턴)
        self.file_io = FileIO(memory_dir=self.memory_dir, logs_dir=self.logs_dir)
        self.branch_manager = BranchManager(memory_dir=self.memory_dir, file_io=self.file_io)
        self.node_manager = NodeManager(memory_dir=self.memory_dir, file_io=self.file_io)
        self.summary_generator = SummaryGenerator(memory_dir=self.memory_dir, file_io=self.file_io)
        # context_loader는 나중에 RAG engine과 함께 초기화

        # Feature Flags 기반 기능 활성화
        self.ontology_enabled = config.is_feature_enabled("ontology_enabled") and ONTOLOGY_AVAILABLE
        self.semantic_web_enabled = (
            config.is_feature_enabled("semantic_web_enabled") and SEMANTIC_WEB_AVAILABLE
        )

        # 온톨로지 엔진 초기화 (Pro 이상)
        self.ontology_engine = None
        if self.ontology_enabled:
            try:
                self.ontology_engine = OntologyEngine(ontology_enabled=True)
            except Exception:
                self.ontology_enabled = False

        # 시맨틱 웹 엔진 초기화 (Enterprise 전용)
        self.semantic_web_engine = None
        if self.semantic_web_enabled and project_id:
            try:
                self.semantic_web_engine = SemanticWebEngine(project_id, enabled=True)
            except Exception:
                self.semantic_web_enabled = False

        # 브랜치 결정 엔진 초기화 (자동 맥락 생성 - 핵심 기능, 모든 티어 활성화)
        self.branch_decision_engine = None
        self.node_grouping_engine = None
        if BRANCH_DECISION_AVAILABLE:
            try:
                self.branch_decision_engine = BranchDecisionEngine()
                self.node_grouping_engine = NodeGroupingEngine()
            except Exception:
                pass  # 실패해도 계속 진행

        # Reference History 초기화 (Pro 이상)
        self.reference_history = None
        self.reference_history_enabled = (
            config.is_feature_enabled("reference_history_enabled") and REFERENCE_HISTORY_AVAILABLE
        )
        if self.reference_history_enabled and project_id:
            try:
                self.reference_history = ReferenceHistory(project_id=project_id)
            except Exception:
                self.reference_history_enabled = False

        # Fuzzy Prompt 초기화 (퍼지 검색 및 힌트 생성 - Pro 이상)
        self.fuzzy_prompt = None
        self.fuzzy_prompt_enabled = (
            config.is_feature_enabled("fuzzy_prompt_enabled") and FUZZY_PROMPT_AVAILABLE
        )
        if self.fuzzy_prompt_enabled:
            try:
                self.fuzzy_prompt = get_fuzzy_prompt_integrator()
            except Exception:
                self.fuzzy_prompt_enabled = False

        # Context Manager 초기화 (Smart Context - Pro 이상)
        self.context_manager = None
        self.smart_context_enabled = (
            config.is_feature_enabled("smart_context_enabled") and CONTEXT_MANAGER_AVAILABLE
        )
        if self.smart_context_enabled:
            try:
                self.context_manager = ContextManager()
            except Exception:
                self.smart_context_enabled = False

        # RAG Engine 초기화 (Lazy Loading - 검색 시에만 로드)
        self._rag_engine = None

        # Context Loader 초기화 (RAG Engine은 lazy loading)
        self.context_loader = ContextLoader(
            memory_dir=self.memory_dir,
            file_io=self.file_io,
            smart_context_enabled=self.smart_context_enabled,
            rag_engine=None,  # Lazy loading으로 나중에 설정
        )

        # Multi-Session Manager 초기화 (Pro 이상 - 병렬 개발)
        self.multi_session_manager = None
        self.multi_session_enabled = (
            config.is_feature_enabled("multi_session_enabled") and project_id
        )
        if self.multi_session_enabled:
            try:
                from .multi_session_sync import get_multi_session_manager

                self.multi_session_manager = get_multi_session_manager(
                    project_id=project_id, enable_auto_sync=True
                )
            except Exception:
                self.multi_session_enabled = False

        # Context Relationship Graph 초기화 (Pro+ - 맥락 간 관계 추적)
        self.relationship_graph = None
        self.semantic_relationship_engine = None
        self.relationship_graph_enabled = bool(
            config.is_feature_enabled("relationship_graph_enabled")
            and RELATIONSHIP_GRAPH_AVAILABLE
            and project_id
        )
        if self.relationship_graph_enabled:
            try:
                self.relationship_graph = RelationshipGraph(
                    project_id=project_id,
                    storage_path=self.memory_dir / project_id
                )
                logger.info("RelationshipGraph 초기화 성공")
                # SemanticRelationshipEngine은 lazy loading으로 필요 시 초기화
                self.semantic_relationship_engine = None
            except Exception as e:
                logger.error(f"RelationshipGraph/SemanticRelationship 초기화 실패: {e}")
                self.relationship_graph_enabled = False

        # Phase 9: Hallucination Detection 초기화 (모든 티어에서 사용 가능)
        self.claim_extractor = None
        self.claim_verifier = None
        self.fuzzy_analyzer = None
        self.contradiction_detector = None
        self.grounding_scorer = None
        self.code_structure_analyzer = None
        self.hallucination_detection_available = False

        # Phase 9는 project_id가 있을 때만 초기화
        # CRITICAL FIX #3: Phase 9 초기화 에러 핸들링
        # 각 컴포넌트별로 개별 try-except 추가하여 graceful degradation
        if HALLUCINATION_DETECTION_AVAILABLE and project_id:
            # 실제 프로젝트 경로 설정 (Git 저장소용)
            actual_project_path = str(Path.cwd())
            logger.debug(f"Phase 9 초기화 시작 - project_path: {actual_project_path}")

            # 1. ClaimExtractor 초기화
            try:
                self.claim_extractor = ClaimExtractor()
                logger.info("ClaimExtractor 초기화 성공")
            except Exception as e:
                logger.error(f"ClaimExtractor 초기화 실패: {type(e).__name__}: {str(e)}")
                self.claim_extractor = None

            # 2. ClaimVerifier 초기화
            try:
                self.claim_verifier = ClaimVerifier(
                    project_id=self.project_id, project_path=actual_project_path
                )
                logger.info("ClaimVerifier 초기화 성공")
            except Exception as e:
                logger.error(f"ClaimVerifier 초기화 실패: {type(e).__name__}: {str(e)}")
                self.claim_verifier = None

            # 3. FuzzyClaimAnalyzer 초기화
            try:
                self.fuzzy_analyzer = FuzzyClaimAnalyzer()
                logger.info("FuzzyClaimAnalyzer 초기화 성공")
            except Exception as e:
                logger.error(f"FuzzyClaimAnalyzer 초기화 실패: {type(e).__name__}: {str(e)}")
                self.fuzzy_analyzer = None

            # 4. ContradictionDetectorV2 초기화
            try:
                self.contradiction_detector = ContradictionDetectorV2(use_embeddings=True)
                logger.info("ContradictionDetectorV2 초기화 성공")
            except Exception as e:
                logger.error(f"ContradictionDetectorV2 초기화 실패: {type(e).__name__}: {str(e)}")
                self.contradiction_detector = None

            # 5. GroundingScorer 초기화 (MEDIUM #1: Evidence Graph 주입)
            try:
                # ClaimVerifier의 Evidence Graph를 GroundingScorer에 전달
                # → 동일 인스턴스 공유, 불필요한 인스턴스 생성 방지
                evidence_graph_for_scorer = self.claim_verifier.evidence_graph if self.claim_verifier else None

                self.grounding_scorer = GroundingScorer(
                    project_id=self.project_id,
                    project_path=actual_project_path,
                    evidence_graph=evidence_graph_for_scorer  # MEDIUM #1: 생성 시점에 전달
                )
                logger.info("GroundingScorer 초기화 성공 (Evidence Graph 공유)")
            except Exception as e:
                logger.error(f"GroundingScorer 초기화 실패: {type(e).__name__}: {str(e)}")
                self.grounding_scorer = None

            # 7. CodeStructureAnalyzer 초기화
            try:
                self.code_structure_analyzer = CodeStructureAnalyzer(
                    project_path=str(self.memory_dir.parent)
                )
                logger.info("CodeStructureAnalyzer 초기화 성공")
            except Exception as e:
                logger.error(f"CodeStructureAnalyzer 초기화 실패: {type(e).__name__}: {str(e)}")
                self.code_structure_analyzer = None

            # 전체 Phase 9 상태 판정
            # 핵심 컴포넌트(claim_extractor, claim_verifier, grounding_scorer) 모두 성공해야 활성화
            if (self.claim_extractor is not None and
                self.claim_verifier is not None and
                self.grounding_scorer is not None):
                self.hallucination_detection_available = True
                logger.info("Phase 9 할루시네이션 검증 시스템 활성화 완료")
            else:
                self.hallucination_detection_available = False
                logger.warning(
                    "Phase 9 핵심 컴포넌트 초기화 실패, 할루시네이션 검증 비활성화. "
                    f"claim_extractor={self.claim_extractor is not None}, "
                    f"claim_verifier={self.claim_verifier is not None}, "
                    f"grounding_scorer={self.grounding_scorer is not None}"
                )

        # Phase 9 Beta Test: Experiment Group 캐싱 (Control/Treatment 분리)
        self._experiment_group = None
        self._beta_phase = None
        self._experiment_query_attempted = False

    def _get_rag_engine(self):
        """
        RAGEngine lazy loading (검색 시에만 초기화)

        성능 최적화:
        - update_memory는 RAG 검색이 필요없으므로 초기화 불필요
        - search_context 첫 호출 시에만 초기화됨
        - 예상 개선: 13s → 3-5s (update_memory 기준)
        """
        if self._rag_engine is None:
            try:
                from .rag_engine import RAGEngine
                self._rag_engine = RAGEngine(project_id=self.project_id)
                logger.info(f"[LAZY_LOAD] RAGEngine 초기화 완료: {self.project_id}")

                # ContextLoader에도 RAG Engine 설정
                if self.context_loader:
                    self.context_loader.rag_engine = self._rag_engine
            except Exception as e:
                logger.warning(f"[LAZY_LOAD] RAGEngine 초기화 실패: {e}")
                self._rag_engine = None

        return self._rag_engine

    @track_call("memory_manager")
    def create_branch(
        self, project_id: str, branch_topic: str, parent_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        새로운 Context Branch 생성

        Args:
            project_id: 프로젝트 식별자
            branch_topic: 브랜치 주제/이름
            parent_branch: 부모 브랜치 (선택)

        Returns:
            생성된 브랜치 정보
        """
        # 입력 살균 (보안)
        project_id = sanitize_input(project_id, max_length=100)
        branch_topic = sanitize_input(branch_topic, max_length=200)

        if not project_id:
            return {"success": False, "error": "Invalid project_id"}
        if not branch_topic:
            return {"success": False, "error": "Invalid branch_topic"}

        # 브랜치 경로 생성
        project_dir = self.memory_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # 브랜치 ID 생성 (타임스탬프 + 밀리초로 고유성 보장)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S%f")[:20]
        branch_id = f"{branch_topic.replace(' ', '_')}_{timestamp}"
        branch_path = project_dir / f"{branch_id}.md"

        # YAML Frontmatter 생성
        frontmatter = {
            "status": "active",
            "project_id": project_id,
            "branch_topic": branch_topic,
            "branch_id": branch_id,
            "parent_branch": parent_branch,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_summarized": None,
            "is_encrypted": config.encryption_enabled,
            "summary": "새로운 브랜치가 생성되었습니다.",
        }

        # 파일 생성
        content = self._create_md_content(frontmatter, "")
        branch_path.write_text(content, encoding="utf-8")

        # ========================================================================
        # 즉시 검증 (방향에 대한 책임)
        # ========================================================================
        try:
            # 1. 파일 존재 확인
            if not branch_path.exists():
                return {
                    "success": False,
                    "error": f"브랜치 파일 생성 실패: {branch_path}",
                    "verification_failed": "file_not_found",
                }

            # 2. 파일 읽기 및 frontmatter 파싱
            verified_frontmatter, verified_body = self._parse_md_file(branch_path)

            # 3. 핵심 메타데이터 검증
            verification_errors = []

            if verified_frontmatter.get("branch_id") != branch_id:
                verification_errors.append(
                    f"branch_id 불일치: expected={branch_id}, actual={verified_frontmatter.get('branch_id')}"
                )

            if verified_frontmatter.get("project_id") != project_id:
                verification_errors.append(
                    f"project_id 불일치: expected={project_id}, actual={verified_frontmatter.get('project_id')}"
                )

            if verified_frontmatter.get("branch_topic") != branch_topic:
                verification_errors.append(
                    f"branch_topic 불일치: expected={branch_topic}, actual={verified_frontmatter.get('branch_topic')}"
                )

            if verified_frontmatter.get("status") != "active":
                verification_errors.append(
                    f"status 불일치: expected=active, actual={verified_frontmatter.get('status')}"
                )

            # 4. 검증 실패 시 롤백
            if verification_errors:
                # 생성된 파일 삭제 (롤백)
                if branch_path.exists():
                    branch_path.unlink()

                return {
                    "success": False,
                    "error": "브랜치 생성 검증 실패",
                    "verification_failed": "metadata_mismatch",
                    "verification_errors": verification_errors,
                }

        except Exception as verify_error:
            # 검증 중 오류 발생 시 롤백
            if branch_path.exists():
                branch_path.unlink()

            return {
                "success": False,
                "error": f"브랜치 생성 검증 중 오류: {str(verify_error)}",
                "verification_failed": "verification_error",
            }

        # ========================================================================
        # 인덱스 등록 (일관성 보장 - Issue #1 Fix)
        # ========================================================================
        try:
            index = self._load_project_index(project_id)
            index.setdefault("branches", {})[branch_id] = {
                "branch_id": branch_id,
                "branch_topic": branch_topic,
                "parent_branch": parent_branch,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
                "file_path": str(branch_path),
            }
            self._save_project_index(project_id, index)
            logger.info(f"브랜치 인덱스 등록 완료: {branch_id}")
        except Exception as index_error:
            # 인덱스 등록 실패 시 파일 롤백
            logger.error(f"브랜치 인덱스 등록 실패: {index_error}")
            if branch_path.exists():
                branch_path.unlink()
            return {
                "success": False,
                "error": f"브랜치 인덱스 등록 실패: {str(index_error)}",
                "verification_failed": "index_registration_error",
            }

        # 감사 로그 기록
        self._log_audit(
            "create_branch",
            {
                "project_id": project_id,
                "branch_id": branch_id,
                "branch_topic": branch_topic,
                "parent_branch": parent_branch,
                "verified": True,  # 검증 완료 표시
            },
        )

        # Multi-Session: 새 브랜치는 auto_sync=False로 세션 생성
        if self.multi_session_enabled and self.multi_session_manager:
            try:
                self.multi_session_manager.create_session(
                    branch_id=branch_id,
                    enable_auto_sync=False  # 새 브랜치는 sync 비활성화
                )
            except Exception:
                pass  # 세션 생성 실패해도 브랜치 생성은 성공

        return {
            "success": True,
            "branch_id": branch_id,
            "branch_path": str(branch_path),
            "message": f"브랜치 '{branch_topic}' 생성 및 검증 완료",
            "verified": True,
        }

    def has_confidence_expression(self, text: str) -> bool:
        """
        확신 표현 감지 (간단한 키워드 포함 여부)

        Phase 9.2 AI 자기검증을 위한 확신 표현 감지.
        정규식 패턴 없이 단순 키워드 포함 여부만 확인.

        Args:
            text: 검사할 텍스트

        Returns:
            확신 표현이 있으면 True
        """
        CONFIDENCE_KEYWORDS = [
            # Korean
            "확실", "완료", "성공", "구현했", "수정했", "추가했",
            "생성했", "완성했", "해결했", "통과", "정상", "마쳤",
            "반드시", "절대", "명확히", "확인했", "검증했",
            # English
            "completed", "successfully", "implemented", "fixed",
            "added", "created", "finished", "resolved", "passed",
            "working", "done", "achieved", "verified"
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in CONFIDENCE_KEYWORDS)

    def _query_experiment_group(self) -> tuple:
        """
        사용자의 실험 그룹 조회 (Control/Treatment 분리)

        Returns:
            (experiment_group, beta_phase) 튜플
            - experiment_group: "control", "treatment1", "treatment2"
            - beta_phase: "control", "closed_beta", "theory_enhanced"
        """
        # 이미 조회했으면 캐시 반환
        if self._experiment_query_attempted:
            return (self._experiment_group, self._beta_phase)

        self._experiment_query_attempted = True

        try:
            # telemetry_client에서 license_key 가져오기
            from .telemetry_client import get_telemetry_client
            telemetry = get_telemetry_client()

            if not telemetry.enabled or not telemetry.license_key:
                logger.info("텔레메트리가 비활성화되어 있거나 license_key가 없습니다.")
                logger.info("기본값 사용: experiment_group=treatment1, beta_phase=closed_beta")
                self._experiment_group = "treatment1"
                self._beta_phase = "closed_beta"
                return (self._experiment_group, self._beta_phase)

            # 웹 서버 API 호출
            import urllib.request
            import urllib.error
            import json

            url = f"{telemetry.server_url}/api/user/experiment_group?license_key={telemetry.license_key}"

            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))

                    self._experiment_group = data.get("experiment_group", "treatment1")
                    self._beta_phase = data.get("beta_phase", "closed_beta")

                    logger.info(f"조회 성공: {self._experiment_group} → {self._beta_phase}")
                    return (self._experiment_group, self._beta_phase)

            except Exception as e:
                logger.info(f"API 호출 실패: {type(e).__name__}: {e}")
                logger.info(f"기본값 사용: experiment_group=treatment1, beta_phase=closed_beta")
                self._experiment_group = "treatment1"
                self._beta_phase = "closed_beta"
                return (self._experiment_group, self._beta_phase)

        except Exception as e:
            logger.info(f"조회 중 에러: {type(e).__name__}: {e}")
            self._experiment_group = "treatment1"
            self._beta_phase = "closed_beta"
            return (self._experiment_group, self._beta_phase)

    def _auto_collect_context(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Git diff 기반으로 자동으로 context 수집 (Zero-Effort 자동화)

        Args:
            project_path: 프로젝트 경로 (None이면 현재 디렉토리)

        Returns:
            자동 수집된 context dict
        """
        context = {
            "files_modified": {},
            "auto_collected": True,
            "collection_method": "git_diff"
        }

        try:
            import subprocess
            import os

            # 작업 디렉토리 설정
            cwd = project_path or os.getcwd()

            # Git이 설치되어 있는지 확인
            try:
                subprocess.run(
                    ["git", "--version"],
                    check=True,
                    capture_output=True,
                    cwd=cwd
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.debug("Git이 설치되어 있지 않습니다. 자동 수집을 건너뜁니다.")
                return context

            # Git 저장소인지 확인
            try:
                subprocess.run(
                    ["git", "rev-parse", "--git-dir"],
                    check=True,
                    capture_output=True,
                    cwd=cwd
                )
            except subprocess.CalledProcessError:
                logger.debug("Git 저장소가 아닙니다. 자동 수집을 건너뜁니다.")
                return context

            # 1. Git diff로 변경된 파일 수집 (unstaged)
            diff_result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                cwd=cwd
            )

            # 2. Git diff --cached로 staged 파일 수집
            diff_cached_result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                cwd=cwd
            )

            # 변경된 파일 목록 합치기
            changed_files = set()
            if diff_result.stdout:
                changed_files.update(diff_result.stdout.strip().split('\n'))
            if diff_cached_result.stdout:
                changed_files.update(diff_cached_result.stdout.strip().split('\n'))

            # 빈 문자열 제거
            changed_files = {f for f in changed_files if f}

            if not changed_files:
                logger.debug("변경된 파일이 없습니다.")
                return context

            logger.debug(f"{len(changed_files)}개 파일 변경 감지: {list(changed_files)[:5]}")

            # 3. 각 파일의 diff 내용 수집 (최대 10개 파일, 각 파일당 최대 100줄)
            for file_path in list(changed_files)[:10]:
                try:
                    # Git diff로 변경 내용 확인
                    file_diff = subprocess.run(
                        ["git", "diff", "HEAD", file_path],
                        capture_output=True,
                        text=True,
                        cwd=cwd,
                        timeout=5
                    )

                    if file_diff.stdout:
                        # diff 내용에서 추가된 줄만 추출 (+ 로 시작하는 줄)
                        added_lines = [
                            line[1:] for line in file_diff.stdout.split('\n')
                            if line.startswith('+') and not line.startswith('+++')
                        ]

                        # 변경된 내용을 context에 추가
                        context["files_modified"][file_path] = {
                            "path": os.path.join(cwd, file_path),
                            "diff": file_diff.stdout[:2000],  # 최대 2000자
                            "added_lines": added_lines[:50],  # 최대 50줄
                            "change_type": "modified"
                        }

                except subprocess.TimeoutExpired:
                    logger.debug(f"{file_path} diff 수집 시간 초과")
                    continue
                except Exception as e:
                    logger.debug(f"{file_path} diff 수집 실패: {e}")
                    continue

            # 4. 최근 커밋 메시지 수집 (참고용)
            try:
                last_commit = subprocess.run(
                    ["git", "log", "-1", "--pretty=format:%s"],
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    timeout=5
                )
                if last_commit.stdout:
                    context["last_commit"] = last_commit.stdout.strip()
            except:
                pass

            logger.debug(f"Context 자동 수집 완료: {len(context['files_modified'])}개 파일")

        except Exception as e:
            logger.debug(f"Context 자동 수집 중 에러 발생: {e}")
            import traceback
            traceback.print_exc()

        return context

    def _parse_context_to_evidence(
        self,
        context: Dict[str, Any],
        project_path: str,
        branch_id: str
    ) -> List[str]:
        """
        Context JSON을 파싱하여 Evidence Graph에 노드 추가 (근본 해결)

        Args:
            context: Context JSON 객체
            project_path: 프로젝트 경로
            branch_id: 브랜치 ID

        Returns:
            referenced_contexts: 생성된 노드 ID 목록
        """
        import hashlib
        from datetime import datetime

        referenced_contexts = []

        try:
            # CRITICAL FIX: memory_manager의 Evidence Graph 대신 ClaimVerifier의 Evidence Graph 사용
            # memory_manager가 자체 Evidence Graph를 생성하면 ClaimVerifier/GroundingScorer와 분리됨
            if hasattr(self, 'claim_verifier') and self.claim_verifier and hasattr(self.claim_verifier, 'evidence_graph'):
                evidence_graph = self.claim_verifier.evidence_graph
                logger.debug(f"memory_manager: ClaimVerifier의 Evidence Graph 사용")
                logger.debug(f"- 객체 ID: {id(evidence_graph)}")
                logger.debug(f"- 파일 경로: {evidence_graph._get_graph_path()}")
            else:
                # ClaimVerifier가 없으면 Evidence Graph 추가 불가능
                logger.debug(f"memory_manager: ClaimVerifier 없음 - Evidence Graph 노드 추가 불가")
                return referenced_contexts

            # 1. files_modified → File 노드 (Git diff 결과)
            if "files_modified" in context and isinstance(context["files_modified"], dict):
                for file_path, file_info in context["files_modified"].items():
                    try:
                        # File 노드 추가
                        full_path = file_info.get("path", file_path)
                        diff_content = file_info.get("diff", "")

                        # Content hash 계산
                        content_hash = hashlib.sha256(diff_content.encode()).hexdigest()

                        # File 노드 추가
                        evidence_graph.add_file_node(
                            file_path=full_path,
                            last_modified=datetime.now(timezone.utc).isoformat(),
                            content_hash=content_hash,
                            metadata={
                                "change_type": file_info.get("change_type", "modified"),
                                "branch_id": branch_id
                            }
                        )

                        referenced_contexts.append(full_path)
                        logger.debug(f"File 노드 추가: {full_path}")

                    except Exception as e:
                        logger.debug(f"File 노드 추가 실패: {file_path} - {e}")
                        continue

            # 2. test_execution_log → File 노드
            if "test_execution_log" in context:
                try:
                    log_content = str(context["test_execution_log"])
                    log_path = "test_results.log"
                    content_hash = hashlib.sha256(log_content.encode()).hexdigest()

                    evidence_graph.add_file_node(
                        file_path=log_path,
                        last_modified=datetime.now(timezone.utc).isoformat(),
                        content_hash=content_hash,
                        metadata={
                            "type": "test_log",
                            "branch_id": branch_id
                        }
                    )

                    referenced_contexts.append(log_path)
                    logger.debug(f"Test Log 노드 추가: {log_path}")

                except Exception as e:
                    logger.debug(f"Test Log 노드 추가 실패: {e}")

            # 3. file_paths → File 노드 (명시적 파일 경로 목록)
            if "file_paths" in context and isinstance(context["file_paths"], list):
                for file_path in context["file_paths"]:
                    try:
                        content_hash = hashlib.sha256(file_path.encode()).hexdigest()

                        evidence_graph.add_file_node(
                            file_path=file_path,
                            last_modified=datetime.now(timezone.utc).isoformat(),
                            content_hash=content_hash,
                            metadata={
                                "type": "explicit_reference",
                                "branch_id": branch_id
                            }
                        )

                        referenced_contexts.append(file_path)
                        logger.debug(f"File 노드 추가: {file_path}")

                    except Exception as e:
                        logger.debug(f"File 노드 추가 실패: {file_path} - {e}")
                        continue

            # 4. calculations → Context 노드 (계산 결과)
            if "calculations" in context:
                try:
                    calc_content = str(context["calculations"])
                    context_id = f"calc:{datetime.now(timezone.utc).isoformat()}:{hashlib.sha256(calc_content.encode()).hexdigest()[:8]}"
                    content_hash = hashlib.sha256(calc_content.encode()).hexdigest()

                    self.evidence_graph.add_context_node(
                        context_id=context_id,
                        branch_id=branch_id,
                        content_hash=content_hash,
                        metadata={
                            "type": "calculation",
                            "content": calc_content[:500]  # 최대 500자
                        }
                    )

                    referenced_contexts.append(context_id)
                    logger.debug(f"Calculation Context 노드 추가: {context_id}")

                except Exception as e:
                    logger.debug(f"Calculation 노드 추가 실패: {e}")

            # 5. 기타 JSON 내용 → Context 노드 (포괄적 처리)
            if not referenced_contexts:
                # 아무 노드도 추가되지 않았으면 전체 context를 하나의 노드로 추가
                try:
                    context_str = str(context)
                    context_id = f"context:{datetime.now(timezone.utc).isoformat()}:{hashlib.sha256(context_str.encode()).hexdigest()[:8]}"
                    content_hash = hashlib.sha256(context_str.encode()).hexdigest()

                    self.evidence_graph.add_context_node(
                        context_id=context_id,
                        branch_id=branch_id,
                        content_hash=content_hash,
                        metadata={
                            "type": "generic_context",
                            "content": context_str[:500]
                        }
                    )

                    referenced_contexts.append(context_id)
                    logger.debug(f"Generic Context 노드 추가: {context_id}")

                except Exception as e:
                    logger.debug(f"Generic Context 노드 추가 실패: {e}")

            logger.debug(f"총 {len(referenced_contexts)}개 노드 추가 완료")

        except Exception as e:
            logger.debug(f"Context 파싱 중 에러: {e}")
            import traceback
            traceback.print_exc()

        return referenced_contexts

    def _background_indexing(
        self,
        content: str,
        frontmatter: Dict[str, Any],
        project_id: str,
        branch_id: str,
        timestamp: str,
        role: str,
    ) -> None:
        """
        백그라운드에서 온톨로지 분류 및 RAG 인덱싱 수행

        Args:
            content: 저장된 내용
            frontmatter: 메타데이터 (참조로 전달, 수정 가능)
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            timestamp: 타임스탬프
            role: 역할 (user/assistant)
        """
        logger.debug(f"온톨로지 분류 및 RAG 인덱싱 시작 (백그라운드)")

        try:
            # 1. 온톨로지 자동 분류 (티어별 활성화)
            ontology_updated = False
            ontology_category = frontmatter.get("ontology_category")
            if self.ontology_enabled and self.ontology_engine:
                # 아직 분류되지 않았거나, 내용이 크게 변경된 경우 재분류
                if not ontology_category or ontology_category == "general":
                    try:
                        classification = self.ontology_engine.classify(content)
                        # 0.50 이상이면 분류 적용 (랜덤보다 높은 수준)
                        if classification.confidence >= 0.50 and classification.node_name != "general":
                            # frontmatter 업데이트 (파일은 이미 저장되어 있으므로 메모리상에만 기록)
                            frontmatter["ontology_category"] = classification.node_name
                            frontmatter["ontology_path"] = classification.path
                            frontmatter["ontology_confidence"] = round(classification.confidence, 2)
                            ontology_updated = True
                            logger.debug(f"온톨로지 분류 완료: {classification.node_name} (confidence: {classification.confidence:.2f})")
                    except Exception as e:
                        logger.debug(f"온톨로지 분류 실패: {e}")

            # 2. RAG 엔진에 내용 인덱싱 (검색 가능하도록)
            rag_indexed = False
            rag_engine = self._get_rag_engine()
            if rag_engine:
                try:
                    # 메타데이터 준비
                    metadata = {
                        "project_id": project_id,
                        "branch_id": branch_id,
                        "branch_topic": frontmatter.get("branch_topic", ""),
                        "timestamp": timestamp,
                        "role": role,
                    }

                    # 인덱싱 (doc_id는 branch_id 기반으로 생성)
                    doc_id = f"{project_id}_{branch_id}_{timestamp.replace(' ', '_').replace(':', '-')}"
                    rag_engine.index_content(content=content, metadata=metadata, doc_id=doc_id)
                    rag_indexed = True
                    logger.debug(f"RAG 인덱싱 완료: {doc_id}")
                except Exception as e:
                    logger.debug(f"RAG 인덱싱 실패: {type(e).__name__}: {str(e)}")
                    import traceback
                    traceback.print_exc()

            logger.debug(f"백그라운드 작업 완료 (온톨로지: {ontology_updated}, RAG: {rag_indexed})")

        except Exception as e:
            logger.debug(f"백그라운드 작업 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()

    @track_call("memory_manager")
    def update_memory(
        self,
        project_id: str,
        branch_id: Union[str, Dict[str, Any]],
        content: str,
        role: str = "assistant",
        verified: bool = False,
        task_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        task_complete: bool = False,
    ) -> Dict[str, Any]:
        """
        브랜치에 대화 내용 추가 (자동 브랜치 생성 포함 - 핵심 기능)

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            content: 추가할 내용
            role: 역할 (user/assistant)
            verified: AI 자기검증 완료 여부 (True면 검증 건너뛰기)
            task_id: 작업 추적 ID (None이면 자동 생성)
            context: 할루시네이션 검증용 컨텍스트 (파일 내용, 테스트 결과 등)
                    예: {"file_contents": {path: content}, "test_results": "output"}

        Returns:
            업데이트 결과
        """
        import time
        method_start = time.perf_counter()

        # Dict 자동 처리 (branch_id가 Dict인 경우 자동 추출)
        if isinstance(branch_id, dict):
            original_dict = branch_id
            # branch_id 또는 id 키에서 실제 branch_id 추출
            branch_id = branch_id.get("branch_id") or branch_id.get("id")
            if not branch_id:
                return {
                    "success": False,
                    "error": f"Dict에서 branch_id 추출 실패: {original_dict}"
                }
            logger.info(f"Dict에서 branch_id 자동 추출: {branch_id}")

        # task_id 자동 생성 (None이면)
        if task_id is None:
            task_id = generate_task_id()
            logger.info(f"새로운 작업 ID 생성: {task_id}")

        branch_path = self._find_branch_path(project_id, branch_id)
        if not branch_path:
            return {"success": False, "error": "브랜치를 찾을 수 없습니다."}

        # 기존 내용 읽기
        frontmatter, body = self._parse_md_file(branch_path)

        # =====================================================================
        # Phase 9.2: 이미 검증된 응답인지 확인 (verified 파라미터 로직)
        # =====================================================================
        # CRITICAL FIX (gray_area.md Issue #3):
        # verified 파라미터 또는 frontmatter의 verified가 True면 무조건 검증 건너뛰기
        # 코드 변경 감지보다 우선순위가 높음

        skip_verification = verified or frontmatter.get("verified", False)

        if skip_verification:
            verified = True  # 확실히 True로 설정

            if frontmatter.get("verified", False):
                # frontmatter에서 로드한 경우
                verified_timestamp = frontmatter.get("verified_timestamp", "N/A")
                logger.info(f"이전에 검증 완료된 응답입니다. 재검증을 건너뜁니다.")
                logger.info(f"verified_timestamp: {verified_timestamp}")
                logger.info(f"grounding_score: {frontmatter.get('grounding_score', 'N/A')}")
            else:
                # verified 파라미터로 전달된 경우
                logger.info(f"verified=True 파라미터로 검증을 건너뜁니다.")
                logger.info(f"코드 변경 감지 여부와 무관하게 검증을 건너뜁니다.")

        # =====================================================================
        # 자동 브랜치 생성 감지 (핵심 기능 - Zero-Effort 구현)
        # =====================================================================
        auto_branch_created = False
        auto_branch_suggestion = None

        if self.branch_decision_engine and role == "user":  # 유저 입력 시에만 체크
            try:
                # 컨텍스트 메타데이터 준비
                context_metadata = {
                    "last_updated": frontmatter.get(
                        "last_updated", datetime.now(timezone.utc).isoformat()
                    )
                }

                # 브랜치 생성 필요성 판단
                should_create, confidence, reason = (
                    self.branch_decision_engine.should_create_branch(
                        current_branch_id=branch_id,
                        current_branch_topic=frontmatter.get("branch_topic", ""),
                        current_branch_content=body,
                        new_content=content,
                        context_metadata=context_metadata,
                    )
                )

                # DEBUG: 출력 추가
                logger.debug(
                    f"should_create={should_create}, confidence={confidence:.2f}, reason={reason}"
                )

                # 확신도 0.45 이상 시 자동 생성 제안
                if should_create and confidence >= 0.45:
                    suggested_name = self.branch_decision_engine.suggest_branch_name(
                        content, context_metadata
                    )
                    auto_branch_suggestion = {
                        "should_create": True,
                        "confidence": confidence,
                        "reason": reason,
                        "suggested_name": suggested_name,
                    }
                    logger.debug(f"auto_branch_suggestion 생성됨: {auto_branch_suggestion}")

                    # Paid 티어에서는 자동으로 브랜치 생성 (Zero-Effort)
                    if not config.feature_flags.branching_confirm_required:
                        try:
                            logger.debug(f"Paid 티어 - 자동 브랜치 생성 시작")
                            new_branch_result = self.create_branch(
                                project_id=project_id, branch_topic=suggested_name
                            )

                            if new_branch_result.get("success"):
                                auto_branch_created = True
                                new_branch_id = new_branch_result["branch_id"]
                                auto_branch_suggestion["created"] = True
                                auto_branch_suggestion["new_branch_id"] = new_branch_id
                                logger.debug(f"자동 브랜치 생성 성공: {new_branch_id}")
                            else:
                                logger.debug(f"자동 브랜치 생성 실패: {new_branch_result}")
                        except Exception as auto_create_err:
                            logger.debug(f"자동 브랜치 생성 에러: {auto_create_err}")
                            import traceback

                            traceback.print_exc()
            except Exception as e:
                logger.debug(f"Exception 발생: {type(e).__name__}: {str(e)}")
                import traceback

                traceback.print_exc()
                pass  # 실패해도 계속 진행

        # =====================================================================
        # 파일 저장 및 백그라운드 인덱싱
        # MANDATORY: 코드 변경 감지 시 무조건 검증
        # =====================================================================

        # 코드 변경 감지 키워드 (파일 수정, 생성, 삭제 등)
        CODE_CHANGE_KEYWORDS = [
            # 파일 경로 패턴
            r'\.py\b', r'\.js\b', r'\.ts\b', r'\.tsx\b', r'\.java\b', r'\.cpp\b', r'\.c\b',
            r'\.go\b', r'\.rs\b', r'\.rb\b', r'\.php\b', r'\.swift\b', r'\.kt\b',
            # 변경 동사
            '수정', '추가', '변경', '삭제', '제거', '생성', '작성', '업데이트',
            'modified', 'added', 'changed', 'deleted', 'removed', 'created', 'updated',
            '완료', 'completed', 'done',
            # 함수/클래스 언급
            'def ', 'class ', 'function ', 'method',
            # 파일 시스템
            'file_path', 'cortex_mcp/', '/Users/', '/home/',
        ]

        # 코드 변경 감지
        code_change_detected = False
        if role == "assistant":
            content_lower = content.lower()
            for keyword in CODE_CHANGE_KEYWORDS:
                if re.search(keyword, content, re.IGNORECASE):
                    code_change_detected = True
                    logger.warning(f"코드 변경 감지: '{keyword}' 패턴 발견")
                    break

        # =====================================================================
        # Phase 9 Beta Test: Control 그룹은 검증 건너뛰기
        # =====================================================================
        experiment_group, beta_phase = self._query_experiment_group()
        is_control_group = (experiment_group == "control")

        if is_control_group and role == "assistant":
            logger.info(f"Control 그룹 감지 - Phase 9 검증을 건너뜁니다.")
            logger.info(f"experiment_group: {experiment_group}, beta_phase: {beta_phase}")

        # 검증 강제 실행 조건 (모든 assistant 응답에 대해 검증)
        # CRITICAL FIX (gray_area.md Issue #3):
        # skip_verification이 True면 무조건 검증 건너뛰기 (verified 파라미터 또는 frontmatter)
        # Control 그룹도 검증 건너뛰기
        # Feature Flag로 할루시네이션 검증 비활성화 가능 (기본값: 비활성화)
        must_verify = (
            config.feature_flags.hallucination_detection_enabled  # Feature Flag 확인 (기본값: False)
            and self.hallucination_detection_available
            and role == "assistant"
            and not skip_verification  # skip_verification=True면 무조건 검증 건너뛰기
            and not is_control_group  # Control 그룹도 검증 건너뛰기
        )

        # Feature Flag로 검증이 비활성화된 경우 로그 출력
        if not config.feature_flags.hallucination_detection_enabled and role == "assistant":
            logger.info("할루시네이션 검증 비활성화됨 (Feature Flag: hallucination_detection_enabled=False)")
            logger.info("맥락 업데이트 시간: ~0.1초 (검증 없음)")

        if must_verify:
            if code_change_detected:
                logger.warning(f"코드 변경이 감지되었습니다. 할루시네이션 검증을 강제 실행합니다.")
            else:
                logger.warning(f"모든 assistant 응답에 대해 할루시네이션 검증을 실행합니다.")

        # =====================================================================
        # Phase 9.3: 자동 Context 수집 + Evidence Graph 통합 (근본 해결)
        # =====================================================================
        # 프로젝트 경로 찾기 (context가 있든 없든 필요)
        project_path = None
        try:
            project_dir = self.memory_dir / project_id
            if project_dir.exists():
                project_path = str(project_dir)
        except Exception as e:
            logger.debug(f"프로젝트 경로 탐색 실패: {e}")
            project_path = str(self.memory_dir / project_id)  # Fallback

        # context가 제공되지 않았고 검증이 필요한 경우, Git diff로 자동 수집
        if must_verify and context is None and role == "assistant":
            logger.debug(f"context가 제공되지 않았습니다. Git diff 기반 자동 수집을 시작합니다.")
            logger.debug(f"프로젝트 경로: {project_path}")

            # 자동 수집 실행
            auto_context = self._auto_collect_context(project_path)

            # 자동 수집된 context가 있으면 사용
            if auto_context.get("files_modified"):
                context = auto_context
                logger.debug(f"자동 수집 성공 - {len(context['files_modified'])}개 파일 변경 감지됨")
            else:
                logger.debug(f"변경된 파일이 없거나 Git 저장소가 아닙니다.")
                logger.debug(f"Evidence Graph 기반 검증을 사용합니다 (Legacy 모드 제거).")
                # CRITICAL FIX: Legacy 모드 제거
                # 이전 방식은 모든 Context를 referenced_contexts에 누적시켜 점수가 비정상적으로 높아짐
                # 이제는 Evidence Graph에서 자동으로 연결된 엣지를 추적하여 검증

        # =====================================================================
        # Phase 9.4: Context → Evidence Graph 노드 변환 (근본 해결)
        # =====================================================================
        referenced_contexts = []

        # DEBUG: 조건 확인
        logger.debug(f"must_verify={must_verify}, context is None={context is None}, role={role}")
        if must_verify and context and role == "assistant":
            # Legacy 모드 체크
            if context.get("legacy_mode"):
                # Legacy 모드: referenced_contexts 직접 사용
                referenced_contexts = context.get("referenced_contexts", [])
                logger.debug(f"Legacy 모드: {len(referenced_contexts)}개 노드 직접 사용")
            else:
                # 일반 모드: Context 파싱
                logger.debug(f"Context 파라미터를 Evidence Graph 노드로 변환 시작")
                try:
                    referenced_contexts = self._parse_context_to_evidence(
                        context=context,
                        project_path=project_path,
                        branch_id=branch_id
                    )
                    logger.debug(f"변환 완료 - {len(referenced_contexts)}개 노드 생성됨")

                    # CRITICAL FIX: referenced_contexts를 context에 포함시켜 verify_response에 전달
                    if referenced_contexts:
                        context["referenced_contexts"] = referenced_contexts
                        logger.debug(f"referenced_contexts를 context에 추가: {len(referenced_contexts)}개")

                    # CRITICAL FIX: project_id, project_path, claim_verifier도 context에 추가
                    if "project_id" not in context:
                        context["project_id"] = project_id
                    if "project_path" not in context:
                        context["project_path"] = project_path
                    if "claim_verifier" not in context:
                        context["claim_verifier"] = self.claim_verifier
                        logger.debug(f"memory_manager의 ClaimVerifier를 context에 추가")
                except Exception as e:
                    logger.debug(f"변환 실패: {e}")
                    import traceback
                    traceback.print_exc()

        # BUG FIX: verified=True일 때도 기본 verification_result 생성 필요
        # cortex_tools.py에서 check.get()을 호출하므로 None이면 AttributeError 발생
        verification_result = {
            "total_claims": 0,
            "verified_claims": 0,
            "contradictions": 0,
            "average_confidence": 1.0,
            "grounding_score": 1.0,  # 검증 skip이므로 통과로 간주
            "risk_level": "low",
            "decision": "ACCEPT",
            "retry_required": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Evidence Graph 업데이트 통계 초기화
        evidence_graph_stats = {"nodes_added": 0, "edges_added": 0}

        if must_verify:  # 기존: role == "assistant" → 변경: must_verify
            # context가 제공되면 auto_verifier 사용 (더 정확한 검증)
            if context and AUTO_VERIFIER_AVAILABLE and get_auto_verifier:
                logger.info(f"context 제공됨 - auto_verifier로 검증합니다.")

                # CRITICAL FIX: auto_verifier 경로에서도 Evidence Graph 업데이트 필수
                # ============================================================
                # Phase 9 검증 전 Evidence Graph 업데이트
                try:
                    eg_stats = self._update_evidence_graph(project_id, branch_id, content)
                    if eg_stats:
                        evidence_graph_stats = eg_stats
                    logger.debug(f"auto_verifier 경로 - Evidence Graph 업데이트 완료 (노드: {evidence_graph_stats['nodes_added']}, 엣지: {evidence_graph_stats['edges_added']})")
                except Exception as eg_err:
                    logger.error(f"auto_verifier 경로 - Evidence Graph 업데이트 실패: {eg_err}")
                    import traceback
                    traceback.print_exc()

                verifier = get_auto_verifier()
                vr = verifier.verify_response(content, context=context)

                # VerificationResult를 기존 dict 형식으로 변환
                verification_result = {
                    "total_claims": len(vr.claims),
                    "verified_claims": len(vr.claims) - len(vr.unverified_claims),
                    "contradictions": 0,  # auto_verifier는 별도로 계산하지 않음
                    "average_confidence": 0.5,  # 임시값
                    "grounding_score": round(vr.grounding_score, 2),
                    "risk_level": "low" if vr.grounding_score >= 0.7 else "critical",
                    "decision": "REJECT" if vr.requires_retry else "ACCEPT",
                    "retry_required": vr.requires_retry,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # frontmatter 업데이트 (검증 통과 시)
                if not vr.requires_retry:  # ACCEPT
                    frontmatter["verified"] = True
                    frontmatter["verified_timestamp"] = datetime.now(timezone.utc).isoformat()
                    frontmatter["grounding_score"] = vr.grounding_score
                    logger.info(f"검증 통과 - Grounding Score: {vr.grounding_score:.2f}")
                else:  # REJECT
                    logger.info(f" 검증 실패 - Grounding Score: {vr.grounding_score:.2f}")
                    if vr.retry_reason:
                        logger.info(f"사유: {vr.retry_reason}")

            # context 없으면 기존 검증 로직 사용 (None 체크 포함)
            elif (
                self.claim_extractor is not None
                and self.claim_verifier is not None
                and self.fuzzy_analyzer is not None
                and self.contradiction_detector is not None
                and self.grounding_scorer is not None
            ):
                logger.info("Phase 9 검증 시작 - 모든 컴포넌트 정상")
                try:
                    # Phase 9 검증 전 Evidence Graph 업데이트 (CRITICAL)
                    eg_stats = self._update_evidence_graph(project_id, branch_id, content)
                    if eg_stats:
                        evidence_graph_stats = eg_stats

                    # Evidence Graph 상태 로깅
                    logger.info(f"Evidence Graph 상태:")
                    total_nodes = len(self.claim_verifier.evidence_graph.graph.nodes)
                    total_edges = len(self.claim_verifier.evidence_graph.graph.edges)
                    logger.info(f"  - 총 노드 수: {total_nodes}")
                    logger.info(f"  - 총 엣지 수: {total_edges}")

                    # 노드 타입별 분포 계산
                    node_types = {}
                    for node_id, node_data in self.claim_verifier.evidence_graph.graph.nodes(data=True):
                        node_type = node_data.get("type", "unknown")
                        node_types[node_type] = node_types.get(node_type, 0) + 1
                    logger.info(f"  - 노드 타입 분포: {node_types}")

                    if total_nodes == 0:
                        logger.info(f"WARNING: Evidence Graph가 비어있습니다!")
                        logger.info(f"Fallback: 파일 시스템 기반 검증으로 진행")

                    logger.debug(f"Phase 9: 할루시네이션 검증 시작")

                    # 1. Claim 추출
                    claims = self.claim_extractor.extract_claims(content)
                    logger.debug(f"추출된 Claim 수: {len(claims)}")

                    # 추출된 Claim 상세 출력
                    for idx, claim in enumerate(claims):
                        logger.debug(f"Claim {idx + 1}: type={claim.claim_type}, text='{claim.text[:50]}...'")

                    # 2. Claim 검증 (Evidence Graph 사용)
                    verified_claims = []
                    if claims:
                        for idx, claim in enumerate(claims):
                            verification = self.claim_verifier.verify_claim(claim, context_history=context)
                            verified_claims.append({"claim": claim, "verification": verification})

                            # 검증 결과 상세 출력
                            is_verified = verification.get("verified", False)
                            confidence = verification.get("confidence", 0.0)
                            evidence_count = len(verification.get("evidence", []))
                            logger.debug(
                                f"Claim {idx + 1} 검증 결과: "
                                f"verified={is_verified}, confidence={confidence:.2f}, "
                                f"evidence={evidence_count}개"
                            )

                    # 3. 모순 검사
                    contradictions = self.contradiction_detector.detect_contradictions(content)
                    logger.debug(f"모순 검출: {contradictions['contradictions_found']}개")

                    # 4. 퍼지 확신도 분석
                    confidence_analysis = self.fuzzy_analyzer.analyze_response(content)
                    logger.debug(f"평균 확신도: {confidence_analysis['average_confidence']:.3f}")

                    # 5. Grounding Score 계산 (CRITICAL FIX #1: grounding_scorer 사용)
                    # BEFORE: 직접 계산 (verified_claims_count / total_claims_count)
                    # AFTER: grounding_scorer.calculate_score() 호출하여 일관성 보장

                    # Claim별 Evidence 매핑 구성
                    claim_evidence_map = {}
                    for vc in verified_claims:
                        claim = vc["claim"]
                        verification = vc["verification"]

                        # Claim ID 생성 (grounding_scorer와 동일한 형식)
                        claim_id = f"{claim.claim_type}:{claim.start}:{claim.end}"

                        # Evidence 추출 (file path 목록)
                        evidence = verification.get("evidence", [])
                        evidence_files = []
                        for ev in evidence:
                            if isinstance(ev, dict) and "file" in ev:
                                evidence_files.append(ev["file"])
                            elif isinstance(ev, str):
                                evidence_files.append(ev)

                        claim_evidence_map[claim_id] = evidence_files

                    # grounding_scorer 호출 (auto_verifier와 동일한 로직)
                    grounding_result = self.grounding_scorer.calculate_score(
                        response_text=content,
                        claims=claims,
                        referenced_contexts=[],  # claim_evidence_map 사용 시 불필요
                        context_history=context,
                        claim_evidence_map=claim_evidence_map,
                    )

                    grounding_score_value = grounding_result["grounding_score"]
                    verified_claims_count = grounding_result["verified_claims"]
                    total_claims_count = grounding_result["total_claims"]

                    logger.debug(f"Grounding Score: {grounding_score_value:.2f} ({verified_claims_count}/{total_claims_count} Claims 검증)")

                    # Collect all evidence files from verified claims for telemetry
                    evidence_files = []
                    for vc in verified_claims:
                        evidence = vc["verification"].get("evidence", [])
                        # evidence is a list of dicts, extract file paths
                        for ev in evidence:
                            if isinstance(ev, dict) and "file" in ev:
                                evidence_files.append(ev["file"])
                            elif isinstance(ev, str):
                                evidence_files.append(ev)
                    # Remove duplicates
                    evidence_files = list(set(evidence_files))
                    logger.debug(f"총 Evidence 파일 수: {len(evidence_files)}")

                    # Risk Level 계산 (grounding_score 고려)
                    base_risk_level = confidence_analysis["risk_level"]
                    final_risk_level = base_risk_level

                    # Bug Fix: Grounding Score 우선순위를 높여서 과도한 보수성 방지
                    # Grounding Score가 실제 검증 결과를 반영하므로 fuzzy confidence보다 우선
                    score_value = grounding_score_value
                    if score_value < 0.3:
                        # Grounding Score가 매우 낮으면 무조건 critical
                        final_risk_level = "critical"
                    elif score_value < 0.5:
                        # Grounding Score가 낮으면 high
                        final_risk_level = "high"
                    elif score_value >= 0.7:
                        # Grounding Score가 높으면 실제 검증이 완료된 것
                        # base_risk_level이 critical/high여도 risk를 낮춤
                        final_risk_level = "low"
                    elif base_risk_level in ["critical", "high"]:
                        # 중간 점수 (0.5-0.7)에서 base_risk_level이 높으면 유지
                        final_risk_level = base_risk_level
                    else:
                        # 중간 점수, base_risk_level도 중간이면 medium
                        final_risk_level = "medium"

                    # Problem 2 해결: 3-Tier Threshold System (Phase 9.3)
                    # Grounding Score 기반 3단계 판정
                    reject_threshold = HALLUCINATION_THRESHOLDS["reject_below"]
                    warn_min, warn_max = HALLUCINATION_THRESHOLDS["warn_range"]
                    accept_threshold = HALLUCINATION_THRESHOLDS["accept_above"]

                    if grounding_score_value < reject_threshold:
                        decision = "REJECT"
                        retry_required = True
                    elif warn_min <= grounding_score_value < warn_max:
                        decision = "WARN"
                        retry_required = True  # 수동 확인 필요
                    else:  # >= accept_threshold
                        decision = "ACCEPT"
                        retry_required = False

                    # risk_level이 critical/high면 강제 WARN 이상
                    if final_risk_level in ["critical", "high"] and decision == "ACCEPT":
                        decision = "WARN"
                        retry_required = True

                    # 검증 결과 저장
                    verification_result = {
                        "total_claims": total_claims_count,
                        "verified_claims": verified_claims_count,
                        "contradictions": contradictions["contradictions_found"],
                        "average_confidence": round(confidence_analysis["average_confidence"], 3),
                        "grounding_score": round(grounding_score_value, 2),
                        "risk_level": final_risk_level,
                        "decision": decision,  # REJECT / WARN / ACCEPT
                        "retry_required": retry_required,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    # Decision별 메시지 출력
                    if decision == "REJECT":
                        logger.info(f" REJECTED - Grounding Score: {grounding_score_value:.2f}")
                        logger.info(f"근거가 매우 부족합니다. 재작업이 필요합니다.")
                    elif decision == "WARN":
                        logger.info(f"MANUAL REVIEW REQUIRED - Grounding Score: {grounding_score_value:.2f}")
                        logger.info(f"애매한 상태입니다. 수동으로 확인해주세요.")
                    else:  # ACCEPT
                        logger.info(f"ACCEPTED - Grounding Score: {grounding_score_value:.2f}, Risk: {final_risk_level}")
                        # 검증 통과 시 frontmatter에 verified=True 저장
                        frontmatter["verified"] = True
                        frontmatter["verified_timestamp"] = datetime.now(timezone.utc).isoformat()

                    logger.debug(f"Phase 9 검증 완료: {verification_result}")

                    # ============================================================
                    # Research Logger Integration (Phase 9 - 논문 데이터 수집)
                    # ============================================================
                    if RESEARCH_LOGGER_AVAILABLE and log_event_sync:
                        try:
                            # LLM Response Event 생성 및 로깅
                            llm_event = create_llm_response_event(
                                response_text=content,
                                response_length=len(content),
                                claims_extracted=[
                                    {"text": c.text, "type": c.claim_type, "confidence": c.confidence}
                                    for c in claims
                                ],
                                grounding_score=grounding_score_value,
                                evidence_count=len(evidence_files) if evidence_files else 0,
                                contradiction_detected=contradictions.get("contradictions_found", False),
                                context_state={
                                    "project_id": self.project_id or "unknown",
                                    "branch_id": branch_id,
                                    "role": role,
                                },
                                task_id=task_id,  # Hybrid task_id (timestamp + UUID)
                            )
                            log_event_sync(llm_event)
                            logger.debug(f"Research Logger: LLM response event logged")

                            # Cortex Intervention Event 로깅 (REJECT 또는 WARN인 경우)
                            if retry_required:
                                intervention_type_enum = None
                                if decision == "REJECT":
                                    intervention_type_enum = InterventionType.BLOCK
                                elif decision == "WARN":
                                    intervention_type_enum = InterventionType.CONFIRMATION

                                if intervention_type_enum:
                                    intervention_event = create_cortex_intervention_event(
                                        intervention_type=intervention_type_enum,
                                        reason=f"{decision}: Grounding Score {grounding_score_value:.2f} (Threshold: {reject_threshold}-{accept_threshold})",
                                        grounding_score=grounding_score_value,
                                        evidence_count=len(evidence_files) if evidence_files else 0,
                                        context_state={
                                            "project_id": self.project_id or "unknown",
                                            "branch_id": branch_id,
                                            "role": role,
                                            "risk_level": final_risk_level,
                                        },
                                        task_id=task_id,
                                    )
                                    log_event_sync(intervention_event)
                                    logger.debug(f"Research Logger: Intervention event logged ({decision})")

                        except Exception as log_err:
                            # Silent failure: 로깅 실패해도 메모리 업데이트는 계속 진행
                            logger.debug(f"Research Logger error (non-critical): {log_err}")

                    # ============================================================
                    # Phase 9 Telemetry Integration (논문 데이터 수집)
                    # Research Logger와 독립적으로 동작
                    # ============================================================
                    if TELEMETRY_AVAILABLE and get_telemetry_client:
                        try:
                            telemetry = get_telemetry_client()

                            # Confidence level 추출 (fuzzy analyzer 결과)
                            confidence_level = "none"
                            if confidence_analysis and "level" in confidence_analysis:
                                confidence_level = confidence_analysis["level"]

                            # Unverified claims 계산
                            unverified_claims_count = 0
                            for claim in claims:
                                if hasattr(claim, 'verified') and not claim.verified:
                                    unverified_claims_count += 1

                            # Claim types 분포 계산
                            claim_types_dist = {}
                            for claim in claims:
                                if hasattr(claim, 'claim_type'):
                                    claim_type = claim.claim_type
                                    claim_types_dist[claim_type] = claim_types_dist.get(claim_type, 0) + 1
                            claim_types_json = json.dumps(claim_types_dist) if claim_types_dist else None

                            # Context depth (참조된 evidence 수)
                            context_depth = len(evidence_files) if evidence_files else 0

                            # Hallucination detection timestamps
                            current_timestamp = datetime.now(timezone.utc).isoformat()
                            hallucination_detected = retry_required or decision == "REJECT"

                            # Retry reason 생성
                            retry_reason = None
                            if retry_required:
                                retry_reason = f"{decision}: Grounding Score {grounding_score_value:.2f}, Risk Level {final_risk_level}"

                            # Phase 9 데이터 전송
                            telemetry.record_research_metric(
                                beta_phase=beta_phase,  # Control/Treatment 그룹에 따라 동적으로 설정
                                grounding_score=grounding_score_value,
                                confidence_level=confidence_level,
                                total_claims=len(claims),
                                unverified_claims=unverified_claims_count,
                                hallucination_detected=hallucination_detected,
                                hallucination_occurred_at=current_timestamp if hallucination_detected else None,
                                hallucination_detected_at=current_timestamp if hallucination_detected else None,
                                requires_retry=retry_required,
                                retry_reason=retry_reason,
                                claim_types_json=claim_types_json,
                                context_depth_avg=float(context_depth) if context_depth > 0 else None,
                                session_id=task_id,  # Use task_id as session identifier
                            )
                            logger.debug(f"Phase 9 Telemetry: Research metrics recorded (GS={grounding_score_value:.2f}, Claims={len(claims)})")

                        except Exception as telemetry_err:
                            # Silent failure: 텔레메트리 실패해도 메모리 업데이트는 계속 진행
                            logger.debug(f"Phase 9 Telemetry error (non-critical): {telemetry_err}")

                except Exception as verify_err:
                    logger.error(f"Phase 9 검증 중 오류 발생: {type(verify_err).__name__}: {str(verify_err)}")
                    import traceback
                    traceback.print_exc()
                    # 검증 실패해도 메모리 업데이트는 계속 진행

            # Phase 9 컴포넌트가 None인 경우 (CRITICAL FIX #3)
            else:
                if must_verify:
                    # 검증이 필요하지만 컴포넌트가 초기화되지 않은 경우
                    missing_components = []
                    if self.claim_extractor is None:
                        missing_components.append("claim_extractor")
                    if self.claim_verifier is None:
                        missing_components.append("claim_verifier")
                    if self.fuzzy_analyzer is None:
                        missing_components.append("fuzzy_analyzer")
                    if self.contradiction_detector is None:
                        missing_components.append("contradiction_detector")
                    if self.grounding_scorer is None:
                        missing_components.append("grounding_scorer")

                    logger.warning(
                        f"Phase 9 컴포넌트 초기화 실패로 할루시네이션 검증을 건너뜁니다. "
                        f"누락된 컴포넌트: {', '.join(missing_components)}"
                    )
                    logger.info(f"Phase 9 비활성화 상태 - 검증 건너뜀")
                    logger.info(f"누락된 컴포넌트: {', '.join(missing_components)}")

        # =====================================================================

        # 새 내용 추가 전 verified 상태 리셋 (내용 변경 시 재검증 필요)
        if frontmatter.get("verified"):
            logger.info(f"새로운 내용 추가 - verified를 False로 리셋합니다.")
            frontmatter["verified"] = False
            frontmatter.pop("verified_timestamp", None)

        # 새 내용 추가
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        new_entry = f"\n\n### [{role.upper()}] {timestamp}\n{content}"
        updated_body = body + new_entry

        # 파일 크기 확인 및 자동 요약 트리거
        current_size_bytes = len(updated_body.encode("utf-8"))
        needs_summary = current_size_bytes > self.max_size_kb * 1024

        # 자동 요약 생성 (크기 초과 시 또는 일정 간격마다)
        summary_updated = False
        if needs_summary or self._should_update_summary(frontmatter, updated_body):
            import time
            summary_start = time.perf_counter()
            new_summary = self._generate_extractive_summary(
                body=updated_body,
                branch_topic=frontmatter.get("branch_topic", ""),
                max_length=config.summary_target_size_kb * 1024,
            )
            summary_time = time.perf_counter() - summary_start
            logger.debug(f"요약 생성 시간: {summary_time*1000:.1f}ms")
            if new_summary:
                frontmatter["summary"] = new_summary
                frontmatter["last_summarized"] = datetime.now(timezone.utc).isoformat()
                summary_updated = True

                # [FIX] Full content를 summary reference로 압축하여 bloat 방지
                if needs_summary:
                    compressed_body = f"""

이 브랜치는 크기 초과로 압축되었습니다.
전체 내용은 frontmatter의 summary를 참조하세요.
자세한 내용이 필요하면 load_context 도구를 사용하세요.

---
압축 정보:
- 압축 시간: {datetime.now(timezone.utc).isoformat()}
- 원본 크기: {current_size_bytes / 1024:.2f} KB
- 압축 임계치: {self.max_size_kb} KB

Smart Context 시스템에 의해 자동 압축되었습니다.
"""
                    updated_body = compressed_body
                    logger.info(f"Body 압축 완료: {current_size_bytes / 1024:.2f} KB → {len(compressed_body) / 1024:.2f} KB")

        # 온톨로지 자동 분류 (티어별 활성화)
        ontology_updated = False
        ontology_category = frontmatter.get("ontology_category")
        if self.ontology_enabled and self.ontology_engine:
            # 아직 분류되지 않았거나, 내용이 크게 변경된 경우 재분류
            if not ontology_category or ontology_category == "general":
                try:
                    import time
                    ontology_start = time.perf_counter()
                    classification = self.ontology_engine.classify(content)
                    ontology_time = time.perf_counter() - ontology_start
                    logger.debug(f"온톨로지 분류 시간: {ontology_time*1000:.1f}ms")
                    # 0.50 이상이면 분류 적용 (랜덤보다 높은 수준)
                    if classification.confidence >= 0.50 and classification.node_name != "general":
                        frontmatter["ontology_category"] = classification.node_name
                        frontmatter["ontology_path"] = classification.path
                        frontmatter["ontology_confidence"] = round(classification.confidence, 2)
                        ontology_updated = True
                except Exception:
                    pass  # 온톨로지 분류 실패해도 저장은 진행

        # Issue #3: 온톨로지 분류 결과 인덱스에도 반영
        if ontology_updated:
            try:
                index = self._load_project_index(project_id)
                branch_index = index.setdefault("branches", {}).setdefault(branch_id, {})
                branch_index["ontology_category"] = frontmatter["ontology_category"]
                branch_index["ontology_confidence"] = frontmatter["ontology_confidence"]
                branch_index["ontology_path"] = frontmatter.get("ontology_path", [])
                self._save_project_index(project_id, index)
                logger.info(f"온톨로지 인덱스 업데이트: {branch_id} -> {frontmatter['ontology_category']}")
            except Exception as e:
                logger.warning(f"온톨로지 인덱스 업데이트 실패: {e}")

        # 시맨틱 웹 관계 추출 (Enterprise 전용)
        semantic_relations_added = 0
        if self.semantic_web_enabled and self.semantic_web_engine and RelationType:
            try:
                # 1. 기존: 내용에서 관계 키워드 추출하여 자동 관계 생성
                relations = self._extract_semantic_relations(content, branch_id)

                # 2. Issue #4: 브랜치 간 참조 감지
                cross_branch_relations = self._detect_cross_branch_references(
                    project_id, branch_id, content
                )
                relations.extend(cross_branch_relations)

                # 3. 관계 저장
                for rel in relations:
                    self.semantic_web_engine.add_relation(
                        source=rel["source"],
                        target=rel["target"],
                        relation_type=rel["relation_type"],
                        confidence=rel.get("confidence", 0.8),
                        metadata=rel.get("metadata", {"auto_extracted": True, "branch_id": branch_id}),
                    )
                    semantic_relations_added += 1
            except Exception:
                pass  # 시맨틱 웹 실패해도 저장은 진행

        # Hybrid task_id를 frontmatter에 저장
        frontmatter["task_id"] = task_id

        # 파일 저장
        import time
        file_start = time.perf_counter()
        full_content = self._create_md_content(frontmatter, updated_body)
        branch_path.write_text(full_content, encoding="utf-8")
        file_time = time.perf_counter() - file_start
        logger.debug(f"파일 저장 시간: {file_time*1000:.1f}ms")

        # RAG 엔진에 내용 인덱싱 (검색 가능하도록) - BACKGROUND 처리
        background_indexing_started = False
        indexing_failed = False
        indexing_error = None

        rag_engine = self._get_rag_engine()
        if rag_engine:
            try:
                # 메타데이터 준비
                metadata = {
                    "project_id": project_id,
                    "branch_id": branch_id,
                    "branch_topic": frontmatter.get("branch_topic", ""),
                    "timestamp": timestamp,
                    "role": role,
                }

                # Background processor에 RAG 인덱싱 작업 제출 (non-blocking)
                background_processor = get_background_processor()
                background_processor.submit_task(
                    worker_indexing_task,
                    content=content,
                    metadata=metadata,
                    project_id=project_id,
                    branch_id=branch_id,
                    timestamp=timestamp,
                    role=role
                )
                background_indexing_started = True
                logger.info(f"[PERF] RAG 인덱싱 작업을 background로 제출 완료 (project_id={project_id})")
            except Exception as e:
                logger.error(f"[ERROR] Background RAG 인덱싱 제출 실패: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()

                # CRITICAL FIX: 즉시 동기 Fallback으로 재시도
                logger.warning(f"[FALLBACK] 동기 방식으로 RAG 인덱싱 재시도 중...")
                try:
                    doc_id = f"{project_id}_{branch_id}_{timestamp.replace(' ', '_').replace(':', '-')}"
                    rag_engine.index_content(content=content, metadata=metadata, doc_id=doc_id)
                    logger.info(f"[FALLBACK] ✅ 동기 RAG 인덱싱 성공: {doc_id}")
                    background_indexing_started = True  # Fallback 성공 시에도 True
                except Exception as fallback_error:
                    logger.error(f"[FALLBACK] ❌ 동기 RAG 인덱싱도 실패: {fallback_error}")
                    indexing_failed = True
                    indexing_error = str(fallback_error)
                    # 사용자에게 즉시 알림 (반환값에 포함)

        # =====================================================================
        # PayAttention 트래킹 (세션 내 토픽/버전 자동 관리 - Pro 이상)
        # =====================================================================
        pay_attention_tracked = False
        pay_attention_topics = []

        if PAY_ATTENTION_AVAILABLE:
            try:
                pa_engine = get_pay_attention_engine(project_id, branch_id)

                # 온톨로지 카테고리 추출 (있으면)
                topic_category = frontmatter.get("ontology_category", "general")

                # 토픽 감지 (키워드 기반 간단 추출)
                detected_topics = self._detect_topics_from_content(content)

                # 메시지 트래킹
                track_result = pa_engine.track_message(
                    message=content,
                    role=role,
                    detected_topics=detected_topics,
                    topic_category=topic_category
                )

                if track_result.get("success"):
                    pay_attention_tracked = True
                    pay_attention_topics = detected_topics
                    logger.info(
                        f"[PAY_ATTENTION] 메시지 트래킹 완료: turn={track_result.get('turn')}, "
                        f"topics={detected_topics}"
                    )

            except Exception as e:
                logger.warning(f"[PAY_ATTENTION] 트래킹 실패 (무시됨): {e}")

        # 반환값 구성
        result = {
            "success": not indexing_failed,  # CRITICAL FIX: 인덱싱 실패 시 success=False
            "task_id": task_id,  # Hybrid task_id 반환 (Reference History + Dashboard 추적용)
            "needs_summary": needs_summary,
            "summary_updated": summary_updated,
            "ontology_updated": ontology_updated,
            "ontology_category": frontmatter.get("ontology_category"),
            "semantic_relations_added": semantic_relations_added,
            "evidence_graph_nodes_added": evidence_graph_stats["nodes_added"],
            "evidence_graph_edges_added": evidence_graph_stats["edges_added"],
            "background_indexing_started": background_indexing_started,  # 성능 최적화: background 인덱싱
            "indexing_failed": indexing_failed,  # 사용자 알림용
            "indexing_error": indexing_error,  # 사용자 알림용
            "message": "메모리 업데이트 완료"
            + (" (요약 갱신됨)" if summary_updated else "")
            + (" (분류됨)" if ontology_updated else "")
            + (
                f" (관계 {semantic_relations_added}개 추출됨)"
                if semantic_relations_added > 0
                else ""
            )
            + (
                f" (Evidence Graph: 노드 {evidence_graph_stats['nodes_added']}개, 엣지 {evidence_graph_stats['edges_added']}개)"
                if evidence_graph_stats["nodes_added"] > 0 or evidence_graph_stats["edges_added"] > 0
                else ""
            )
            + (" (백그라운드 인덱싱 시작됨)" if background_indexing_started and not indexing_failed else "")
            + (" RAG 인덱싱 실패 - 검색 불가" if indexing_failed else ""),
            "size_kb": current_size_bytes / 1024,
        }

        # PayAttention 트래킹 결과 추가 (Pro 이상)
        if pay_attention_tracked:
            result["pay_attention_tracked"] = True
            result["pay_attention_topics"] = pay_attention_topics
            result["message"] += f" (Attention 트래킹: {len(pay_attention_topics)}개 토픽)"

        # Feature Flag가 활성화된 경우에만 hallucination_check 추가
        if config.feature_flags.hallucination_detection_enabled:
            result["hallucination_check"] = verification_result  # Phase 9: 할루시네이션 검증 결과

        # Phase 9: Hallucination 검증 실패 시 재작업 필요 플래그 설정
        # Feature Flag가 활성화된 경우에만 grounding_score 추가
        if config.feature_flags.hallucination_detection_enabled and verification_result:
            # verification_result의 retry_required 플래그 사용 (Problem 2 해결)
            retry_required = verification_result.get("retry_required", False)
            grounding_score = verification_result.get("grounding_score", 1.0)
            risk_level = verification_result.get("risk_level", "unknown")
            decision = verification_result.get("decision", "UNKNOWN")
            unverified_claims_count = (
                verification_result.get("total_claims", 0)
                - verification_result.get("verified_claims", 0)
            )

            # Phase 9 검증이 실행되었을 때만 grounding_score를 반환값에 포함
            result["grounding_score"] = grounding_score

            # retry_required가 True이면 재작업 필요
            if retry_required:
                result["retry_required"] = True

                # 코드 변경이 감지된 경우 더 강력한 경고
                if code_change_detected:
                    result["code_change_verification_failed"] = True
                    result["retry_reason"] = (
                        f"[MANDATORY VERIFICATION FAILED] 코드 변경이 감지되어 할루시네이션 검증을 수행했으나 실패했습니다.\n"
                        f"  - 판정: {decision}\n"
                        f"  - Grounding Score: {grounding_score:.2f}\n"
                        f"  - Risk Level: {risk_level}\n"
                        f"  - 검증되지 않은 주장: {unverified_claims_count}개\n"
                        f"  \n"
                        f"  코드 변경 작업은 반드시 검증을 통과해야 합니다.\n"
                        f"  근거가 부족한 주장을 수정하거나 관련 파일을 참조한 증거를 제시해주세요."
                    )
                    result["message"] += " (🚨 코드 변경 검증 실패 - 재작업 필수)"
                    logger.info(f"\n{'='*80}")
                    logger.warning(f" CRITICAL WARNING ")
                    logger.warning(f"코드 변경이 감지되었으나 할루시네이션 검증에 실패했습니다.")
                    logger.warning(f"Decision: {decision}, Score: {grounding_score:.2f}, Risk: {risk_level}")
                    logger.warning(f"이 작업은 재작업이 필요합니다.")
                    logger.info(f"{'='*80}\n")
                else:
                    # 일반적인 검증 실패 메시지
                    result["retry_reason"] = (
                        f"할루시네이션 검증 실패. Grounding Score: {grounding_score:.2f}, "
                        f"Risk Level: {risk_level}, "
                        f"검증되지 않은 주장: {unverified_claims_count}개. "
                        f"근거가 부족한 주장을 수정하거나 관련 파일을 참조해주세요."
                    )
                    result["message"] += " (⚠️  재작업 필요)"
            else:
                # 검증 통과한 경우 (코드 변경 시 성공 메시지)
                if code_change_detected:
                    logger.warning(f"코드 변경 검증 통과: {decision}, Score: {grounding_score:.2f}")
                    result["code_change_verification_passed"] = True

            # Bug Fix: decision과 risk_level을 최상위 result에 추가 (접근성 개선)
            # grounding_score는 이미 Line 1435에서 최상위에 추가됨
            result["decision"] = decision
            result["risk_level"] = risk_level

        # 자동 브랜치 생성 제안이 있으면 추가 (핵심 기능)
        if auto_branch_suggestion:
            result["auto_branch_suggestion"] = auto_branch_suggestion
            # 실제로 생성되었는지 확인
            if auto_branch_suggestion.get("created"):
                result["auto_branch_created"] = True
                result["new_branch_id"] = auto_branch_suggestion.get("new_branch_id")
                result["new_branch_topic"] = auto_branch_suggestion.get("suggested_name")

        # Reference History 기록 (Pro 이상)
        # 현재 사용된 맥락(브랜치)를 기록하여 향후 유사 작업 시 추천에 활용
        if self.reference_history_enabled and self.reference_history:
            try:
                # content에서 키워드 추출 (간단한 버전 - 공백 기준 단어 분리)
                task_keywords = [w.strip() for w in content[:200].split() if len(w.strip()) > 3][
                    :10
                ]

                # 현재 사용된 맥락 (현재는 branch_id만, 향후 확장 가능)
                contexts_used = [branch_id]

                # 참조 이력 기록
                self.reference_history.record(
                    task_keywords=task_keywords,
                    contexts_used=contexts_used,
                    branch_id=branch_id,
                    query=content[:100],  # 첫 100자만 저장
                    project_id=project_id,
                )
            except Exception:
                pass  # Reference History 실패해도 메모리 업데이트는 성공

        # Multi-Session Sync (Pro 이상 - 병렬 개발)
        # 세션 자동 생성 및 맥락 동기화
        if self.multi_session_enabled and self.multi_session_manager:
            try:
                # 세션이 없으면 생성
                if not self.multi_session_manager.current_session:
                    self.multi_session_manager.create_session(branch_id=branch_id)

                # 세션 활동 업데이트 및 자동 동기화
                context_id = f"{branch_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                self.multi_session_manager.auto_sync_on_activity(context_id=context_id)

                result["multi_session_sync"] = {
                    "enabled": True,
                    "session_id": (
                        self.multi_session_manager.current_session.session_id
                        if self.multi_session_manager.current_session
                        else None
                    ),
                }
            except Exception:
                pass  # Multi-session sync 실패해도 메모리 업데이트는 성공

        # Task completion compression (Issue #5)
        if task_complete and self.context_manager:
            try:
                compression_result = self.context_manager.compress_on_task_completion(
                    project_id=project_id,
                    branch_id=branch_id
                )
                result["task_compression"] = compression_result
                logger.info(f"작업 완료 압축 수행: {compression_result['compressed_count']}개 Context 압축됨")
            except Exception as e:
                logger.error(f"Task completion compression 실패: {e}")
                # 압축 실패해도 메모리 업데이트는 성공

        # 전체 실행 시간 측정
        method_time = time.perf_counter() - method_start
        logger.debug(f"update_memory 전체 실행 시간: {method_time*1000:.1f}ms")

        return result

    def _should_update_summary(self, frontmatter: Dict, body: str) -> bool:
        """
        요약 업데이트가 필요한지 판단

        조건:
        1. 아직 요약이 초기값인 경우
        2. 마지막 요약 후 새 엔트리가 5개 이상 추가된 경우
        3. 요약이 비어있는 경우
        """
        current_summary = frontmatter.get("summary", "")

        # 초기값이거나 비어있으면 업데이트 필요
        if not current_summary or current_summary == "새로운 브랜치가 생성되었습니다.":
            return True

        # 최소한의 내용이 있어야 요약 생성
        entries = self._parse_conversation_entries(body)
        if len(entries) < 1:
            return False

        # 마지막 요약 이후 새 엔트리 개수 확인
        last_summarized = frontmatter.get("last_summarized")
        if not last_summarized:
            return len(entries) >= 1  # 요약 기록이 없으면 1개 이상일 때 생성

        # 새 엔트리가 5개 이상이면 요약 갱신
        new_entries_count = self._count_entries_after(entries, last_summarized)
        return new_entries_count >= 5

    def _count_entries_after(self, entries: List[Dict], timestamp_str: str) -> int:
        """특정 시간 이후 추가된 엔트리 개수"""
        try:
            threshold = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return len(entries)

        count = 0
        for entry in entries:
            entry_time_str = entry.get("timestamp", "")
            try:
                # "2025-12-10 13:33:36 UTC" 형식 파싱
                entry_time = datetime.strptime(
                    entry_time_str.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
                if entry_time > threshold:
                    count += 1
            except (ValueError, AttributeError):
                count += 1  # 파싱 실패시 새 엔트리로 간주

        return count

    def _parse_conversation_entries(self, body: str) -> List[Dict]:
        """
        대화 본문에서 개별 엔트리 파싱

        형식: ### [ROLE] TIMESTAMP
        """
        entries = []
        # ### [ASSISTANT] 2025-12-10 13:33:36 UTC 또는 ### [USER] ... 패턴 매칭
        pattern = r"###\s*\[(\w+)\]\s*([\d\-]+\s+[\d:]+\s+\w+)\n([\s\S]*?)(?=###\s*\[|\Z)"
        matches = re.findall(pattern, body)

        for role, timestamp, content in matches:
            entries.append(
                {"role": role.lower(), "timestamp": timestamp, "content": content.strip()}
            )

        return entries

    def _generate_extractive_summary(
        self, body: str, branch_topic: str, max_length: int = 20480
    ) -> str:
        """
        추출적 요약 생성 (Zero-Trust: 외부 API 없이 로컬에서 처리)

        전략:
        1. 대화 엔트리 파싱
        2. 핵심 정보 추출 (결정사항, 작업내용, 문제/해결)
        3. 최근 대화 요약
        4. 목표 크기에 맞게 압축
        """
        entries = self._parse_conversation_entries(body)
        if not entries:
            return f"브랜치 주제: {branch_topic}"

        summary_parts = []

        # 1. 브랜치 주제
        summary_parts.append(f"## 브랜치: {branch_topic}")

        # 2. 핵심 정보 추출
        key_info = self._extract_key_information(entries)
        if key_info:
            summary_parts.append("\n## 핵심 정보")
            summary_parts.append(key_info)

        # 3. 최근 대화 요약 (마지막 5개 엔트리)
        recent_entries = entries[-5:] if len(entries) > 5 else entries
        recent_summary = self._summarize_recent_entries(recent_entries)
        if recent_summary:
            summary_parts.append("\n## 최근 대화")
            summary_parts.append(recent_summary)

        # 4. 통계 정보
        summary_parts.append(f"\n## 통계")
        summary_parts.append(f"- 총 대화 수: {len(entries)}개")
        summary_parts.append(f"- 마지막 업데이트: {entries[-1]['timestamp'] if entries else 'N/A'}")

        full_summary = "\n".join(summary_parts)

        # 크기 제한 적용
        if len(full_summary.encode("utf-8")) > max_length:
            full_summary = self._truncate_to_size(full_summary, max_length)

        return full_summary

    def _extract_key_information(self, entries: List[Dict]) -> str:
        """
        대화에서 핵심 정보 추출

        키워드 기반:
        - 결정/결론: "결정", "완료", "해결", "수정"
        - 문제/이슈: "문제", "오류", "에러", "이슈", "버그"
        - 작업: "구현", "개발", "추가", "변경", "삭제"
        """
        key_patterns = {
            "결정/완료": ["결정", "완료", "해결", "수정", "fix", "done", "resolved"],
            "문제/이슈": ["문제", "오류", "에러", "이슈", "버그", "error", "bug", "issue"],
            "작업": [
                "구현",
                "개발",
                "추가",
                "변경",
                "삭제",
                "implement",
                "add",
                "update",
                "remove",
            ],
        }

        extracted = {category: [] for category in key_patterns}

        for entry in entries:
            content = entry.get("content", "").lower()
            first_line = content.split("\n")[0][:200] if content else ""

            for category, keywords in key_patterns.items():
                for keyword in keywords:
                    if keyword in content:
                        # 키워드가 포함된 문장 추출
                        sentences = self._extract_sentences_with_keyword(
                            entry.get("content", ""), keyword
                        )
                        for sentence in sentences[:2]:  # 카테고리당 최대 2개
                            if sentence and sentence not in extracted[category]:
                                extracted[category].append(sentence[:300])
                        break

        # 포맷팅
        result_parts = []
        for category, items in extracted.items():
            if items:
                result_parts.append(f"### {category}")
                for item in items[:3]:  # 카테고리당 최대 3개
                    result_parts.append(f"- {item}")

        return "\n".join(result_parts)

    def _extract_sentences_with_keyword(self, text: str, keyword: str) -> List[str]:
        """키워드가 포함된 문장 추출"""
        sentences = []
        # 문장 분리 (마침표, 줄바꿈 기준)
        for line in text.split("\n"):
            line = line.strip()
            if keyword.lower() in line.lower() and len(line) > 10:
                # 마크다운 헤더 제거
                clean_line = re.sub(r"^#+\s*", "", line)
                clean_line = re.sub(r"^\*+\s*", "", clean_line)
                clean_line = re.sub(r"^-\s*", "", clean_line)
                if clean_line:
                    sentences.append(clean_line)

        return sentences

    def _summarize_recent_entries(self, entries: List[Dict]) -> str:
        """최근 대화 엔트리 요약"""
        if not entries:
            return ""

        summary_parts = []
        for entry in entries:
            role = entry.get("role", "unknown").upper()
            timestamp = entry.get("timestamp", "")
            content = entry.get("content", "")

            # 내용 압축 (첫 200자 또는 첫 3줄)
            lines = content.split("\n")
            compressed = []
            char_count = 0
            for line in lines[:5]:
                line = line.strip()
                if line and not line.startswith("#"):
                    compressed.append(line)
                    char_count += len(line)
                    if char_count > 200:
                        break

            if compressed:
                summary_parts.append(f"- [{role}] {' | '.join(compressed[:2])}")

        return "\n".join(summary_parts)

    def _truncate_to_size(self, text: str, max_bytes: int) -> str:
        """텍스트를 바이트 크기에 맞게 자르기"""
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text

        # 바이트 단위로 자르고 디코딩
        truncated = encoded[:max_bytes]
        # UTF-8 바운더리에서 자르기
        while truncated:
            try:
                return truncated.decode("utf-8") + "\n\n[... 요약 크기 제한으로 일부 생략 ...]"
            except UnicodeDecodeError:
                truncated = truncated[:-1]

        return ""

    @track_call("memory_manager")
    def get_active_summary(
        self,
        project_id: str,
        branch_id: Optional[str] = None,
        user_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        현재 활성 브랜치의 요약 정보 반환 (PayAttention 통합)

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID (없으면 최신 활성 브랜치)
            user_message: 사용자 메시지 (PayAttention 트리거 감지용)

        Returns:
            요약 정보 (+ PayAttention 컨텍스트 주입 결과)
        """
        if branch_id:
            branch_path = self._find_branch_path(project_id, branch_id)
        else:
            branch_path = self._find_latest_active_branch(project_id)

        if not branch_path:
            return {"success": False, "error": "활성 브랜치를 찾을 수 없습니다.", "summary": None}

        frontmatter, body = self._parse_md_file(branch_path)

        # 기본 결과 구성
        result = {
            "success": True,
            "branch_id": frontmatter.get("branch_id"),
            "branch_topic": frontmatter.get("branch_topic"),
            "summary": frontmatter.get("summary", ""),
            "last_summarized": frontmatter.get("last_summarized"),
            "status": frontmatter.get("status"),
        }

        # =====================================================================
        # PayAttention 트리거 감지 및 컨텍스트 주입 (Pro 이상)
        # =====================================================================
        actual_branch_id = frontmatter.get("branch_id") or branch_id

        if (
            PAY_ATTENTION_AVAILABLE
            and user_message
            and actual_branch_id
        ):
            try:
                pa_engine = get_pay_attention_engine(project_id, actual_branch_id)

                # 트리거 감지
                trigger = pa_engine.detect_trigger(user_message)

                if trigger:
                    # 컨텍스트 주입
                    injection = pa_engine.inject_attention_context(trigger, user_message)

                    if injection.injection_text:
                        result["attention_context"] = injection.injection_text
                        result["attention_trigger"] = trigger.value
                        result["attention_confidence"] = injection.confidence
                        result["attention_reason"] = injection.reason
                        result["attention_topics_count"] = len(injection.topics)

                        logger.info(
                            f"[PAY_ATTENTION] 컨텍스트 주입 완료: trigger={trigger.value}, "
                            f"topics={len(injection.topics)}, confidence={injection.confidence:.2f}"
                        )

            except Exception as e:
                logger.warning(f"[PAY_ATTENTION] 컨텍스트 주입 실패 (무시됨): {e}")

        # =====================================================================
        # Fuzzy Prompt 컨텍스트 생성 (Pro 이상)
        # =====================================================================
        if self.fuzzy_prompt_enabled and self.fuzzy_prompt and user_message:
            try:
                fuzzy_context = self.fuzzy_prompt.generate_context(user_message)
                if fuzzy_context and hasattr(fuzzy_context, 'to_system_prompt'):
                    fuzzy_prompt_text = fuzzy_context.to_system_prompt()
                    if fuzzy_prompt_text:
                        result["fuzzy_context"] = fuzzy_prompt_text
                        result["fuzzy_hints_count"] = getattr(fuzzy_context, 'hints_count', 0)
                        logger.info(
                            f"[FUZZY_PROMPT] 컨텍스트 생성 완료: hints={result.get('fuzzy_hints_count', 0)}"
                        )
            except Exception as e:
                logger.warning(f"[FUZZY_PROMPT] 컨텍스트 생성 실패 (무시됨): {e}")

        return result

    def update_summary(self, project_id: str, branch_id: str, new_summary: str) -> Dict[str, Any]:
        """
        브랜치 요약 갱신

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            new_summary: 새 요약 내용

        Returns:
            갱신 결과
        """
        branch_path = self._find_branch_path(project_id, branch_id)
        if not branch_path:
            return {"success": False, "error": "브랜치를 찾을 수 없습니다."}

        frontmatter, body = self._parse_md_file(branch_path)

        # 요약 갱신
        frontmatter["summary"] = new_summary
        frontmatter["last_summarized"] = datetime.now(timezone.utc).isoformat()

        # 파일 저장
        full_content = self._create_md_content(frontmatter, body)
        branch_path.write_text(full_content, encoding="utf-8")

        return {
            "success": True,
            "message": "요약 갱신 완료",
            "last_summarized": frontmatter["last_summarized"],
        }

    def list_branches(self, project_id: str) -> List[Dict[str, Any]]:
        """프로젝트의 모든 브랜치 목록 반환 (위임)"""
        return self.branch_manager.list_branches(project_id)

    # ==================== Node 계층 관리 (v2.0) ====================

    def create_node(
        self, project_id: str, branch_id: str, node_name: str, context_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        브랜치 내에 Node 그룹 생성

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            node_name: Node 이름
            context_ids: 이 Node에 포함할 Context ID 목록 (선택)

        Returns:
            생성된 Node 정보
        """
        # 브랜치 확인
        branch_path = self._find_branch_path(project_id, branch_id)
        if not branch_path:
            return {"success": False, "error": "브랜치를 찾을 수 없습니다."}

        # Node ID 생성
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        node_id = f"node_{node_name.replace(' ', '_')}_{timestamp}"

        # 인덱스 파일 로드/생성
        index = self._load_project_index(project_id)

        # 브랜치 인덱스 확인
        if branch_id not in index.get("branches", {}):
            index.setdefault("branches", {})[branch_id] = {"nodes": {}, "contexts": []}

        # Node 추가
        index["branches"][branch_id]["nodes"][node_id] = {
            "name": node_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "context_ids": context_ids or [],
        }

        # 인덱스 저장
        self._save_project_index(project_id, index)

        # 감사 로그
        self._log_audit(
            "create_node",
            {
                "project_id": project_id,
                "branch_id": branch_id,
                "node_id": node_id,
                "node_name": node_name,
                "context_count": len(context_ids) if context_ids else 0,
            },
        )

        return {
            "success": True,
            "node_id": node_id,
            "node_name": node_name,
            "message": f"Node '{node_name}' 생성 완료",
        }

    def create_node_with_smart_grouping(
        self,
        project_id: str,
        branch_id: str,
        node_name: str,
        node_summary: str,
        context_ids: List[str] = None,
        similarity_threshold: float = 0.70,
    ) -> Dict[str, Any]:
        """
        Smart Grouping을 사용하여 Node 생성
        유사한 노드가 있으면 기존 노드에 추가, 없으면 새 노드 생성

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            node_name: Node 이름
            node_summary: Node 요약 (유사도 계산에 사용)
            context_ids: 이 Node에 포함할 Context ID 목록 (선택)
            similarity_threshold: 유사도 임계값 (기본 0.70)

        Returns:
            생성 결과
        """
        # 기존 노드들과 직접 유사도 비교
        index = self._load_project_index(project_id)

        # 브랜치 인덱스 확인 및 생성 (create_node와 동일한 로직)
        if branch_id not in index.get("branches", {}):
            index.setdefault("branches", {})[branch_id] = {"nodes": {}, "contexts": []}

        existing_nodes = index["branches"][branch_id]["nodes"]

        similar_node_id = None
        max_similarity = 0.0

        # 기존 노드들과 유사도 계산
        for node_id, node_data in existing_nodes.items():
            # 노드의 name과 summary를 결합하여 비교
            node_text = f"{node_data.get('name', '')} {node_data.get('summary', '')}"
            new_node_text = f"{node_name} {node_summary}"

            # context_manager의 유사도 계산 메서드 사용
            similarity = self.context_manager._calculate_semantic_similarity(
                node_text, new_node_text
            )

            if similarity >= similarity_threshold and similarity > max_similarity:
                similar_node_id = node_id
                max_similarity = similarity

        if similar_node_id:
            # 유사한 노드 발견 - 기존 노드에 추가
            existing_node = existing_nodes[similar_node_id]

            # context_ids 추가
            if context_ids:
                existing_node["context_ids"].extend(context_ids)
                self._save_project_index(project_id, index)

            return {
                "success": True,
                "action": "added_to_existing_node",
                "node_id": similar_node_id,
                "message": f"유사한 노드 '{existing_node.get('name')}' 발견 (유사도: {max_similarity:.2f} >= {similarity_threshold}). 기존 노드에 추가했습니다.",
            }

        # 유사한 노드 없음 - 새 노드 직접 생성
        # Node ID 생성
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        node_id = f"node_{node_name.replace(' ', '_')}_{timestamp}"

        # Node 데이터 생성 (summary 포함)
        index["branches"][branch_id]["nodes"][node_id] = {
            "name": node_name,
            "summary": node_summary,  # 유사도 비교를 위해 summary 저장
            "created_at": datetime.now(timezone.utc).isoformat(),
            "context_ids": context_ids or [],
        }

        # 인덱스 저장
        self._save_project_index(project_id, index)

        # 감사 로그
        self._log_audit(
            "create_node_with_smart_grouping",
            {
                "project_id": project_id,
                "branch_id": branch_id,
                "node_id": node_id,
                "node_name": node_name,
                "action": "created_new_node",
            },
        )

        return {
            "success": True,
            "action": "created_new_node",
            "node_id": node_id,
            "message": f"새 노드 '{node_name}' 생성 완료",
        }

    def list_nodes(self, project_id: str, branch_id: str) -> Dict[str, Any]:
        """브랜치의 모든 Node 목록 반환"""
        try:
            # 브랜치 인덱스 로드
            branch_index = self._load_branch_index(project_id, branch_id)

            # nodes는 list 형식
            nodes_list = branch_index.get("nodes", [])

            # 반환용 데이터 구성
            nodes_data = []
            for node_data in nodes_list:
                nodes_data.append(
                    {
                        "node_id": node_data.get("node_id"),
                        "node_name": node_data.get("node_name"),
                        "created_at": node_data.get("created_at"),
                        "context_count": len(node_data.get("context_ids", [])),
                    }
                )

            return {
                "success": True,
                "nodes": sorted(nodes_data, key=lambda x: x.get("created_at", ""), reverse=True),
                "total_count": len(nodes_data),
            }
        except Exception as e:
            return {"success": False, "error": f"Node 목록 조회 실패: {str(e)}"}

    def add_context_to_node(
        self, project_id: str, branch_id: str, node_id: str, context_id: str
    ) -> Dict[str, Any]:
        """Context를 Node에 추가"""
        index = self._load_project_index(project_id)

        if branch_id not in index.get("branches", {}):
            return {"success": False, "error": "브랜치를 찾을 수 없습니다."}

        nodes = index["branches"][branch_id].get("nodes", {})
        if node_id not in nodes:
            return {"success": False, "error": "Node를 찾을 수 없습니다."}

        # Context 추가
        if context_id not in nodes[node_id]["context_ids"]:
            nodes[node_id]["context_ids"].append(context_id)

        self._save_project_index(project_id, index)

        return {"success": True, "message": f"Context '{context_id}'를 Node에 추가 완료"}

    def get_context_count(self, project_id: str, branch_id: str) -> Dict[str, Any]:
        """브랜치의 Context 개수 확인"""
        project_dir = self.memory_dir / project_id
        if not project_dir.exists():
            return {"success": False, "count": 0, "error": "프로젝트를 찾을 수 없습니다."}

        # 현재 구조에서는 branch 파일 = context
        # 향후 확장 시 contexts 서브디렉토리 사용
        count = len(list(project_dir.glob("*.md")))

        return {"success": True, "project_id": project_id, "branch_id": branch_id, "count": count}

    def suggest_node_grouping(
        self, project_id: str, branch_id: str, auto_create: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Context가 많을 경우 Node 그룹핑 제안 및 자동 생성 (Issue #2)

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            auto_create: None이면 Feature Flag에 따름, True/False면 강제 설정

        Returns:
            제안 여부, 추천 그룹핑, 자동 생성 결과
        """
        count_result = self.get_context_count(project_id, branch_id)
        if not count_result["success"]:
            return count_result

        count = count_result["count"]

        if count < self.NODE_SUGGESTION_THRESHOLD:
            return {
                "success": True,
                "needs_grouping": False,
                "count": count,
                "threshold": self.NODE_SUGGESTION_THRESHOLD,
                "message": f"Context 수({count})가 임계치({self.NODE_SUGGESTION_THRESHOLD}) 미만입니다.",
            }

        # 그룹핑 제안 생성
        branches = self.list_branches(project_id)
        suggested_groups = self._analyze_for_grouping(branches)

        # auto_create 결정 (Feature Flag 또는 파라미터)
        should_auto_create = auto_create
        if should_auto_create is None:
            # Feature Flag: node_grouping_confirm_required가 False면 자동 생성
            should_auto_create = not config.feature_flags.node_grouping_confirm_required

        created_nodes = []
        if should_auto_create and suggested_groups:
            # 자동 노드 생성 (최대 3개)
            for group in suggested_groups[:3]:
                node_name = group.get("suggested_name", f"auto_group_{len(created_nodes)+1}")
                node_result = self.create_node(
                    project_id=project_id,
                    branch_id=branch_id,
                    node_name=node_name,
                    context_ids=group.get("context_ids", [])
                )
                if node_result.get("success"):
                    created_nodes.append(node_result.get("node_id"))
                    logger.info(f"자동 노드 생성 완료: {node_result.get('node_id')}")

        return {
            "success": True,
            "needs_grouping": True,
            "count": count,
            "threshold": self.NODE_SUGGESTION_THRESHOLD,
            "suggested_groups": suggested_groups,
            "auto_created": len(created_nodes) > 0,
            "created_nodes": created_nodes,
            "message": f"Context가 {count}개입니다. {'자동 그룹핑 완료' if created_nodes else 'Node 그룹핑을 권장합니다.'}",
        }

    def get_hierarchy(self, project_id: str) -> Dict[str, Any]:
        """
        프로젝트의 전체 계층 구조 반환
        Project → Branch → Node → Context
        """
        project_dir = self.memory_dir / project_id
        if not project_dir.exists():
            return {"success": False, "error": "프로젝트를 찾을 수 없습니다."}

        index = self._load_project_index(project_id)
        branches = self.list_branches(project_id)

        result = {
            "success": True,
            "project_id": project_id,
            "project_name": project_id,  # 하위 호환성
            "branches": []
        }

        for branch in branches:
            branch_id = branch.get("branch_id")
            branch_data = {
                "branch_id": branch_id,
                "branch_topic": branch.get("branch_topic"),
                "status": branch.get("status"),
                "nodes": [],
                "direct_contexts": [],
            }

            # Node 정보 추가
            if branch_id in index.get("branches", {}):
                idx_branch = index["branches"][branch_id]
                for node_id, node_data in idx_branch.get("nodes", {}).items():
                    branch_data["nodes"].append(
                        {
                            "node_id": node_id,
                            "name": node_data.get("name"),
                            "context_ids": node_data.get("context_ids", []),
                        }
                    )

            result["branches"].append(branch_data)

        return result

    def _load_project_index(self, project_id: str) -> Dict:
        """프로젝트 인덱스 파일 로드"""
        project_dir = self.memory_dir / project_id
        index_file = project_dir / "_index.json"

        if index_file.exists():
            try:
                return json.loads(index_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        return {"version": "2.0", "revision": 0, "branches": {}}

    def _save_json_with_lock(self, file_path: Path, data: Dict, max_retries: int = 3):
        """
        파일 잠금을 사용하여 JSON 파일을 안전하게 저장

        Args:
            file_path: 저장할 파일 경로
            data: 저장할 데이터
            max_retries: 최대 재시도 횟수
        """
        for attempt in range(max_retries):
            try:
                # 부모 디렉토리 생성
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # 파일 잠금 및 저장
                with portalocker.Lock(file_path, mode='w', encoding='utf-8', timeout=5) as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return  # 성공
            except portalocker.exceptions.LockException:
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # 점진적 대기
                    continue
                else:
                    raise Exception(f"Failed to acquire lock on {file_path} after {max_retries} attempts")
            except Exception as e:
                raise Exception(f"Failed to save {file_path}: {e}")

    def _save_project_index(self, project_id: str, index: Dict):
        """프로젝트 인덱스 파일 저장 (파일 잠금 사용 + 낙관적 잠금)"""
        project_dir = self.memory_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        index_file = project_dir / "_index.json"

        # 낙관적 잠금: revision 자동 증가
        current_revision = index.get("revision", 0)
        index["revision"] = current_revision + 1
        index["updated_at"] = datetime.now(timezone.utc).isoformat()

        self._save_json_with_lock(index_file, index)

    def _load_branch_index(self, project_id: str, branch_id: str) -> Dict:
        """브랜치 인덱스 파일 로드"""
        branch_dir = self.memory_dir / project_id / "contexts" / branch_id
        index_file = branch_dir / "_branch_index.json"

        if index_file.exists():
            try:
                return json.loads(index_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        return {
            "branch_id": branch_id,
            "branch_topic": "",
            "contexts": [],
            "nodes": [],
            "revision": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _save_branch_index(self, project_id: str, branch_id: str, index: Dict):
        """브랜치 인덱스 파일 저장 (파일 잠금 사용 + 낙관적 잠금)"""
        branch_dir = self.memory_dir / project_id / "contexts" / branch_id
        branch_dir.mkdir(parents=True, exist_ok=True)

        index_file = branch_dir / "_branch_index.json"

        # 낙관적 잠금: revision 자동 증가
        current_revision = index.get("revision", 0)
        index["revision"] = current_revision + 1
        index["updated_at"] = datetime.now(timezone.utc).isoformat()

        self._save_json_with_lock(index_file, index)

    def _analyze_for_grouping(self, branches: List[Dict]) -> List[Dict]:
        """브랜치 목록 분석하여 그룹핑 제안 생성"""
        # 간단한 토픽 기반 그룹핑 제안
        topic_groups = {}

        for branch in branches:
            topic = branch.get("branch_topic", "")
            # 첫 단어를 그룹 키로 사용
            group_key = (
                topic.split("_")[0] if "_" in topic else topic.split()[0] if topic else "기타"
            )

            if group_key not in topic_groups:
                topic_groups[group_key] = []
            topic_groups[group_key].append(branch.get("branch_id"))

        # 2개 이상인 그룹만 제안
        suggestions = []
        for group_name, branch_ids in topic_groups.items():
            if len(branch_ids) >= 2:
                suggestions.append(
                    {
                        "suggested_node_name": group_name,
                        "context_ids": branch_ids,
                        "count": len(branch_ids),
                    }
                )

        return sorted(suggestions, key=lambda x: x["count"], reverse=True)

    # ==================== Private Methods ====================

    def _find_branch_path(self, project_id: str, branch_id: str) -> Optional[Path]:
        """브랜치 파일 경로 찾기"""
        project_dir = self.memory_dir / project_id
        if not project_dir.exists():
            return None

        for md_file in project_dir.glob("*.md"):
            if branch_id in md_file.stem:
                return md_file
        return None

    def _find_latest_active_branch(self, project_id: str) -> Optional[Path]:
        """최신 활성 브랜치 찾기"""
        project_dir = self.memory_dir / project_id
        if not project_dir.exists():
            return None

        active_branches = []
        for md_file in project_dir.glob("*.md"):
            frontmatter, _ = self._parse_md_file(md_file)
            if frontmatter.get("status") == "active":
                active_branches.append((md_file, frontmatter.get("created_at", "")))

        if not active_branches:
            return None

        # 가장 최근 브랜치 반환 (datetime/str 혼합 타입 처리)
        return sorted(active_branches, key=lambda x: str(x[1]) if x[1] else "", reverse=True)[0][0]

    def _create_md_content(self, frontmatter: Dict, body: str) -> str:
        """YAML Frontmatter + Body 형식의 MD 파일 생성"""
        yaml_content = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
        return f"---\n{yaml_content}---\n{body}"

    def _parse_md_file(self, file_path: Path) -> tuple:
        """MD 파일에서 Frontmatter와 Body 분리"""
        content = file_path.read_text(encoding="utf-8")

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
                return frontmatter, body

        return {}, content

    def _detect_topics_from_content(self, content: str) -> List[str]:
        """
        내용에서 토픽(주제) 감지 (PayAttention 연동용)

        온톨로지 엔진이 있으면 온톨로지 기반 분류,
        없으면 간단한 키워드 추출

        Args:
            content: 분석할 내용

        Returns:
            감지된 토픽 목록 (최대 5개)
        """
        topics = []

        # 온톨로지 엔진 활용
        if self.ontology_engine:
            try:
                result = self.ontology_engine.classify(content)
                if result.get("category"):
                    topics.append(result["category"])
                # 하위 카테고리도 추가
                if result.get("path"):
                    for path_item in result["path"]:
                        if path_item not in topics:
                            topics.append(path_item)
            except Exception as e:
                logger.debug(f"온톨로지 분류 실패 (무시됨): {e}")

        # 키워드 기반 추출 (백업 및 보완)
        code_keywords = [
            "함수", "클래스", "API", "구현", "버그", "수정", "테스트",
            "기능", "모듈", "컴포넌트", "서비스", "데이터", "설정",
            "인증", "보안", "성능", "최적화", "리팩토링", "배포"
        ]

        content_lower = content.lower()
        for keyword in code_keywords:
            if keyword in content_lower and keyword not in topics:
                topics.append(keyword)

        # 영어 키워드도 확인
        english_keywords = [
            "function", "class", "api", "implementation", "bug", "fix", "test",
            "feature", "module", "component", "service", "data", "config",
            "auth", "security", "performance", "optimization", "refactor", "deploy"
        ]

        for keyword in english_keywords:
            if keyword in content_lower and keyword not in topics:
                topics.append(keyword)

        # 최대 5개로 제한
        return list(set(topics))[:5]

    def _extract_semantic_relations(self, content: str, branch_id: str) -> List[Dict[str, Any]]:
        """
        내용에서 시맨틱 관계 추출 (Enterprise 전용)

        키워드 기반 관계 패턴:
        - "A는 B에 의존" → DEPENDS_ON
        - "A가 B를 참조" → REFERENCES
        - "A는 B의 일부" → PART_OF
        - "A는 B와 관련" → RELATED_TO
        - "A는 B와 충돌" → CONFLICTS_WITH
        """
        if not RelationType:
            return []

        relations = []
        patterns = {
            RelationType.DEPENDS_ON: [
                r"(\w+)(?:는|은|이|가)\s+(\w+)에?\s*의존",
                r"(\w+)\s+depends\s+on\s+(\w+)",
                r"(\w+)(?:는|은)\s+(\w+)(?:를|을)\s+필요",
            ],
            RelationType.EXTENDS: [
                r"(\w+)(?:는|은|이|가)\s+(\w+)(?:를|을)?\s*확장",
                r"(\w+)\s+extends?\s+(\w+)",
                r"(\w+)(?:는|은)\s+(\w+)(?:를|을)?\s*상속",
            ],
            RelationType.SUPERSEDES: [
                r"(\w+)(?:는|은|이|가)\s+(\w+)(?:를|을)?\s*대체",
                r"(\w+)\s+supersedes?\s+(\w+)",
                r"(\w+)\s+replaces?\s+(\w+)",
            ],
            RelationType.RELATED_TO: [
                r"(\w+)(?:는|은|이|가)\s+(\w+)(?:와|과)\s*관련",
                r"(\w+)\s+relates?\s+to\s+(\w+)",
            ],
            RelationType.CONFLICTS_WITH: [
                r"(\w+)(?:는|은|이|가)\s+(\w+)(?:와|과)\s*충돌",
                r"(\w+)\s+conflicts?\s+with\s+(\w+)",
            ],
        }

        for relation_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 2:
                        source = f"{branch_id}:{match[0]}"
                        target = f"{branch_id}:{match[1]}"
                        relations.append(
                            {
                                "source": source,
                                "target": target,
                                "relation_type": relation_type,
                                "confidence": 0.7,
                            }
                        )

        return relations[:10]  # 한 번에 최대 10개 관계만 추출

    def _detect_cross_branch_references(
        self, project_id: str, current_branch_id: str, content: str
    ) -> List[Dict[str, Any]]:
        """
        다른 브랜치에 대한 참조 감지 (Issue #4)

        패턴:
        - "이전에 작업한 [주제]"
        - "[브랜치명]에서 구현한"
        - "관련 작업: [주제]"

        Args:
            project_id: 프로젝트 ID
            current_branch_id: 현재 브랜치 ID
            content: 내용

        Returns:
            감지된 브랜치 간 관계 목록
        """
        if not RelationType:
            return []

        relations = []

        try:
            # 모든 브랜치 목록 조회
            all_branches = self.list_branches(project_id)

            for branch in all_branches:
                branch_id = branch.get("branch_id", "")
                if branch_id == current_branch_id:
                    continue

                # 브랜치 토픽이 내용에 언급되었는지 확인
                topic = branch.get("branch_topic", "")
                if topic and len(topic) >= 3:  # 최소 3글자 이상
                    # 대소문자 구분 없이 검색
                    if topic.lower() in content.lower():
                        relations.append({
                            "source": current_branch_id,
                            "target": branch_id,
                            "relation_type": RelationType.RELATED_TO,
                            "confidence": 0.6,
                            "metadata": {"detected_by": "cross_branch_reference"}
                        })
                        logger.info(f"브랜치 간 참조 감지: {current_branch_id} -> {branch_id} (토픽: {topic})")

        except Exception as e:
            logger.warning(f"브랜치 간 참조 감지 실패: {e}")

        return relations[:5]  # 최대 5개 관계만 반환

    def _log_audit(self, action: str, data: Dict[str, Any]):
        """감사 로그 기록"""
        audit_file = self.logs_dir / "audit.json"

        try:
            audit_data = json.loads(audit_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            audit_data = {"version": "1.0.0", "entries": []}

        audit_data["entries"].append(
            {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action, "data": data}
        )

        audit_file.write_text(
            json.dumps(audit_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ==================== Smart Context Public Methods ====================

    def load_context(
        self,
        project_id: str,
        branch_id: str,
        context_id: Optional[str] = None,
        force_full_load: bool = False,
    ) -> Dict[str, Any]:
        """
        특정 맥락 활성화 (압축 해제)

        Smart Context 기능 (Pro 이상):
        - metadata + summary만 유지 → full_content 로드
        - Lazy Loading으로 토큰 효율화

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_id: Context ID (없으면 브랜치 summary만)
            force_full_load: 전체 내용 강제 로드

        Returns:
            로드 결과
        """
        if not self.smart_context_enabled or not self.context_manager:
            return {
                "success": False,
                "error": "Smart Context 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.context_manager.load_context(
                project_id=project_id,
                branch_id=branch_id,
                context_id=context_id,
                force_full_load=force_full_load,
            )
            return result
        except Exception as e:
            return {"success": False, "error": f"맥락 로드 실패: {str(e)}"}

    def compress_context(self, project_id: str, branch_id: str, context_id: str) -> Dict[str, Any]:
        """
        Context 압축 (full_content 언로드, summary만 유지)

        Smart Context 기능 (Pro 이상):
        - 30분 미사용 맥락 자동 압축
        - 토큰 70% 절감 목표

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_id: Context ID

        Returns:
            압축 결과
        """
        if not self.smart_context_enabled or not self.context_manager:
            return {
                "success": False,
                "error": "Smart Context 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.context_manager.compress_context(
                project_id=project_id, branch_id=branch_id, context_id=context_id
            )
            return result
        except Exception as e:
            return {"success": False, "error": f"맥락 압축 실패: {str(e)}"}

    def get_context_summary(
        self, project_id: str, branch_id: str, context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Context의 summary만 반환 (full_content 로드 없이)

        Smart Context 기능 (Pro 이상):
        - 토큰 효율적인 빠른 조회
        - full_content 로드 없이 summary만 반환

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_id: Context ID (없으면 브랜치 summary)

        Returns:
            Summary 정보
        """
        if not self.smart_context_enabled or not self.context_manager:
            return {
                "success": False,
                "error": "Smart Context 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.context_manager.get_context_summary(
                project_id=project_id, branch_id=branch_id, context_id=context_id
            )
            return result
        except Exception as e:
            return {"success": False, "error": f"Summary 조회 실패: {str(e)}"}

    def get_loaded_contexts(self) -> Dict[str, Any]:
        """
        현재 로드된 모든 Context 정보 반환

        Smart Context 기능 (Pro 이상):
        - 활성 브랜치 목록
        - 각 브랜치의 로드된 Context
        - 마지막 접근 시간

        Returns:
            로드된 맥락 정보
        """
        if not self.smart_context_enabled or not self.context_manager:
            return {
                "success": False,
                "error": "Smart Context 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.context_manager.get_loaded_contexts()
            return {"success": True, "loaded_contexts": result}
        except Exception as e:
            return {"success": False, "error": f"로드된 맥락 조회 실패: {str(e)}"}

    def search_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        로컬 Vector RAG 검색

        과거 맥락을 의미 기반으로 정확히 검색합니다.

        Args:
            query: 검색 쿼리
            project_id: 프로젝트 ID (필터링용, 선택)
            branch_id: 브랜치 ID (필터링용, 선택)
            top_k: 반환할 최대 결과 수 (기본: 5)

        Returns:
            검색 결과 딕셔너리
        """
        # RAG Engine 확인 (Lazy loading)
        rag_engine = self._get_rag_engine()
        if not rag_engine:
            return {
                "success": False,
                "error": "RAG Engine이 초기화되지 않았습니다.",
                "query": query,
                "results": [],
            }

        try:
            # RAG Engine 사용하여 검색
            results = rag_engine.search(query=query, top_k=top_k)

            # project_id나 branch_id 필터링 (메타데이터 기반)
            if project_id or branch_id:
                filtered_results = []
                for result in results:
                    metadata = result.get("metadata", {})

                    # project_id 필터
                    if project_id and metadata.get("project_id") != project_id:
                        continue

                    # branch_id 필터
                    if branch_id and metadata.get("branch_id") != branch_id:
                        continue

                    filtered_results.append(result)

                results = filtered_results

            return {
                "success": True,
                "results": results,
                "query": query,
                "total_results": len(results),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"검색 실패: {str(e)}",
                "query": query,
                "results": [],
            }

    @track_call("memory_manager")
    def initialize_context(
        self, project_id: str, project_path: str, scan_mode: str = "LIGHT"
    ) -> Dict[str, Any]:
        """
        프로젝트 초기 맥락 스캔

        Args:
            project_id: 프로젝트 ID
            project_path: 프로젝트 경로
            scan_mode: FULL, LIGHT, NONE 중 선택

        Returns:
            초기화 결과
        """
        # Phase 9: ClaimVerifier의 project_path 업데이트 (CRITICAL)
        if self.claim_verifier:
            self.claim_verifier.project_path = Path(project_path)
            logger.debug(f"ClaimVerifier project_path 업데이트: {project_path}")

        # 입력 검증
        if scan_mode not in ["FULL", "LIGHT", "NONE"]:
            return {
                "success": False,
                "error": f"잘못된 scan_mode: {scan_mode}. FULL, LIGHT, NONE 중 하나를 선택하세요.",
            }

        # NONE 모드: 스캔은 건너뛰되 기본 브랜치는 생성
        if scan_mode == "NONE":
            try:
                # 기본 브랜치 생성 (첫 대화를 위해 필수)
                branch_result = self.create_branch(
                    project_id=project_id,
                    branch_topic="초기_프로젝트_맥락"
                )
                if not branch_result.get("success"):
                    return {"success": False, "error": "초기 브랜치 생성 실패"}

                return {
                    "success": True,
                    "message": "초기화를 건너뛰었습니다 (기본 브랜치 생성됨).",
                    "scan_mode": "NONE",
                    "files_scanned": 0,
                    "branch_id": branch_result["branch_id"],
                }
            except Exception as e:
                return {"success": False, "error": f"브랜치 생성 실패: {str(e)}"}

        # 프로젝트 경로 검증
        project_path_obj = Path(project_path)
        if not project_path_obj.exists():
            return {"success": False, "error": f"프로젝트 경로를 찾을 수 없습니다: {project_path}"}

        # 스캔할 파일 패턴 정의
        if scan_mode == "LIGHT":
            # 핵심 파일만 스캔
            patterns = [
                "README.md",
                "README.txt",
                "package.json",
                "pyproject.toml",
                "requirements.txt",
                "setup.py",
                "main.py",
                "app.py",
                "index.js",
                "index.ts",
            ]
        else:  # FULL
            # 모든 소스 파일 스캔
            patterns = [
                "**/*.py",
                "**/*.js",
                "**/*.ts",
                "**/*.jsx",
                "**/*.tsx",
                "**/*.md",
                "**/*.json",
                "**/*.yaml",
                "**/*.yml",
            ]

        # 파일 스캔
        scanned_files = []
        for pattern in patterns:
            try:
                if scan_mode == "LIGHT":
                    # 루트 디렉토리에서만 검색
                    file_path = project_path_obj / pattern
                    if file_path.exists() and file_path.is_file():
                        scanned_files.append(file_path)
                else:  # FULL
                    # 재귀적 검색
                    for file_path in project_path_obj.glob(pattern):
                        if file_path.is_file():
                            # 숨김 파일 및 제외 디렉토리 스킵
                            if any(
                                part.startswith(".")
                                or part in ["node_modules", "__pycache__", "venv", "dist", "build"]
                                for part in file_path.parts
                            ):
                                continue
                            scanned_files.append(file_path)
            except Exception:
                continue

        # 초기 브랜치 생성
        try:
            branch_result = self.create_branch(
                project_id=project_id, branch_topic="초기_프로젝트_스캔"
            )

            if not branch_result.get("success"):
                return {"success": False, "error": "초기 브랜치 생성 실패"}

            branch_id = branch_result["branch_id"]

            # 스캔한 파일 정보를 메모리에 추가
            summary_content = f"프로젝트 초기 스캔 완료\n\n"
            summary_content += f"스캔 모드: {scan_mode}\n"
            summary_content += f"스캔된 파일 수: {len(scanned_files)}\n\n"
            summary_content += "파일 목록:\n"

            for file_path in scanned_files[:50]:  # 최대 50개만
                relative_path = file_path.relative_to(project_path_obj)
                summary_content += f"- {relative_path}\n"

            if len(scanned_files) > 50:
                summary_content += f"... 외 {len(scanned_files) - 50}개 파일\n"

            # 메모리 업데이트
            self.update_memory(
                project_id=project_id,
                branch_id=branch_id,
                content=summary_content,
                role="assistant",
            )

            # Phase 9.4: Evidence Graph 초기 채우기 (Git 이력 + 코드베이스 스캔)
            evidence_stats = {}
            if PHASE94_AVAILABLE and PHASE92_AVAILABLE:
                try:
                    logger.info(f"Phase 9.4: Starting initial scan: {project_path}")

                    # 1. Git 이력 수집 (Phase 9.2)
                    git_stats = populate_from_git(
                        repo_path=project_path,
                        include_recent_commits=True
                    )
                    logger.info(f"Phase 9.2: Git evidence: {git_stats}")

                    # 2. 코드베이스 스캔 (Phase 9.4)
                    scan_stats = populate_from_scan(
                        project_path=project_path,
                        max_files=5000 if scan_mode == "FULL" else 100
                    )
                    logger.info(f"Phase 9.4: Scan evidence: {scan_stats}")

                    evidence_stats = {
                        "git_changes": git_stats.get("changes", 0),
                        "git_evidences": git_stats.get("evidences", 0),
                        "scan_files": scan_stats.get("files", 0),
                        "scan_evidences": scan_stats.get("evidences", 0),
                    }

                    # Evidence Graph 디스크 저장
                    if EVIDENCE_GRAPH_V2_AVAILABLE:
                        graph = get_evidence_graph_v2()
                        graph_stats = graph.get_statistics()
                        evidence_path = self.memory_dir / project_id / "evidence_graph.json"
                        graph.save_to_disk(evidence_path)
                        logger.info(f"Phase 9: Evidence Graph saved: {graph_stats}")

                        # CRITICAL: ClaimVerifier의 Evidence Graph도 업데이트
                        if self.claim_verifier:
                            # v2 Evidence Graph를 기존 v1 Evidence Graph로 변환하여 로드
                            # (claim_verifier는 v1 EvidenceGraph를 사용)
                            logger.info(f"Phase 9: ClaimVerifier Evidence Graph 업데이트 중...")
                            # 기존 v1 그래프에 v2의 파일 정보 추가
                            added_count = 0
                            for evidence_id, evidence in graph._evidence_index.items():
                                if evidence.evidence_type.value == "file_exists":
                                    file_path = evidence.metadata.get("file_path", evidence.source.replace("scan:", ""))
                                    # add_file_node 사용 (file_path, last_modified, content_hash, metadata)
                                    success = self.claim_verifier.evidence_graph.add_file_node(
                                        file_path=file_path,
                                        last_modified=evidence.timestamp,
                                        content_hash="scan_evidence",  # v2에서는 content_hash 없음
                                        metadata={
                                            "from_evidence_graph_v2": True,
                                            "evidence_id": evidence_id,
                                            "confidence": evidence.confidence
                                        }
                                    )
                                    if success:
                                        added_count += 1
                            logger.info(f"Phase 9: ClaimVerifier Evidence Graph 업데이트 완료: {added_count}개 파일 노드 추가")

                except Exception as e:
                    logger.info(f"Phase 9.4: Evidence collection failed: {e}")
                    evidence_stats = {"error": str(e)}

            return {
                "success": True,
                "message": f"프로젝트 초기화 완료 ({scan_mode} 모드)",
                "scan_mode": scan_mode,
                "files_scanned": len(scanned_files),
                "branch_id": branch_id,
                "evidence_stats": evidence_stats,
            }

        except Exception as e:
            return {"success": False, "error": f"초기화 중 오류 발생: {str(e)}"}

    def suggest_contexts(
        self, query: str, project_id: str, branch_id: Optional[str] = None, top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Reference History 기반 맥락 추천

        Args:
            query: 검색 쿼리
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID (선택)
            top_k: 반환할 최대 개수

        Returns:
            추천 결과
        """
        # Reference History 확인
        if not self.reference_history_enabled or not self.reference_history:
            return {
                "success": False,
                "error": "Reference History 기능이 비활성화되어 있습니다. Pro 이상 티어가 필요합니다.",
                "tier_required": "pro",
                "tier": 3,
                "tier_name": "Feature Disabled",
                "suggestions": [],
            }

        try:
            # Reference History의 suggest_contexts 메서드 호출
            result = self.reference_history.suggest_contexts(
                query=query, branch_id=branch_id, top_k=top_k
            )

            # 결과 포맷 조정
            if result.get("success"):
                # contexts를 suggestions로 변환하되, 각 요소가 딕셔너리인지 확인
                contexts = result.get("contexts", [])
                suggestions = []

                for ctx in contexts:
                    if isinstance(ctx, dict):
                        suggestions.append(ctx)
                    elif isinstance(ctx, str):
                        # 문자열인 경우 딕셔너리로 변환
                        suggestions.append({"context_id": ctx})
                    else:
                        # 알 수 없는 타입은 문자열로 변환
                        suggestions.append({"context_id": str(ctx)})

                return {
                    "success": True,
                    "tier": result.get("tier"),
                    "tier_name": result.get("tier_name"),
                    "confidence": result.get("confidence"),
                    "suggestions": suggestions,
                    "reason": result.get("reason"),
                    "message": result.get("message"),
                }
            else:
                # 실패한 경우에도 suggestions 필드 포함
                if "suggestions" not in result:
                    result["suggestions"] = []
                return result

        except Exception as e:
            return {"success": False, "error": f"맥락 추천 실패: {str(e)}", "suggestions": []}

    def accept_suggestions(
        self, project_id: str, session_id: str, contexts_used: List[str]
    ) -> Dict[str, Any]:
        """
        추천 수락 기록 (출처에 대한 책임)

        Args:
            project_id: 프로젝트 ID
            session_id: suggest_contexts에서 반환한 session_id
            contexts_used: 실제 사용된 맥락 ID 목록

        Returns:
            기록 결과
        """
        # Reference History 확인
        if not self.reference_history_enabled or not self.reference_history:
            return {
                "success": False,
                "error": "Reference History 기능이 비활성화되어 있습니다. Pro 이상 티어가 필요합니다.",
                "tier_required": "pro",
            }

        try:
            result = self.reference_history.record_suggestion_decision(
                session_id=session_id, decision="accepted", contexts_used=contexts_used, reason=""
            )
            return result
        except Exception as e:
            return {"success": False, "error": f"추천 수락 기록 실패: {str(e)}"}

    def reject_suggestions(self, project_id: str, session_id: str, reason: str) -> Dict[str, Any]:
        """
        추천 거부 기록 (출처에 대한 책임)

        Args:
            project_id: 프로젝트 ID
            session_id: suggest_contexts에서 반환한 session_id
            reason: 거부 이유 (필수)

        Returns:
            기록 결과
        """
        # Reference History 확인
        if not self.reference_history_enabled or not self.reference_history:
            return {
                "success": False,
                "error": "Reference History 기능이 비활성화되어 있습니다. Pro 이상 티어가 필요합니다.",
                "tier_required": "pro",
            }

        # 이유 필수 체크
        if not reason:
            return {"success": False, "error": "거부 이유(reason)는 필수 항목입니다."}

        try:
            result = self.reference_history.record_suggestion_decision(
                session_id=session_id, decision="rejected", contexts_used=[], reason=reason
            )
            return result
        except Exception as e:
            return {"success": False, "error": f"추천 거부 기록 실패: {str(e)}"}

    # ========================================================================
    # Smart Context Tools (Phase 1)
    # ========================================================================

    def compress_context(self, project_id: str, branch_id: str, context_id: str) -> Dict[str, Any]:
        """
        특정 Context 수동 압축 (full_content 언로드)

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_id: Context ID

        Returns:
            압축 결과
        """
        if not self.smart_context_enabled or not self.context_manager:
            return {
                "success": False,
                "error": "Smart Context 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.context_manager.compress_context(
                project_id=project_id, branch_id=branch_id, context_id=context_id
            )
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"Context 압축 실패: {str(e)}"}

    def scan_project_deep(
        self,
        project_id: str,
        project_path: str,
        scan_mode: str,
        file_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Context Graph 기반 프로젝트 심층 스캔

        Args:
            project_id: 프로젝트 ID
            project_path: 프로젝트 경로
            scan_mode: 스캔 모드 (FULL/LIGHT/NONE)
            file_patterns: 스캔할 파일 패턴

        Returns:
            스캔 결과
        """
        try:
            from core.initial_scanner import scan_project_deep as scanner_deep

            result = scanner_deep(
                project_id=project_id,
                project_path=project_path,
                scan_mode=scan_mode,
                file_patterns=file_patterns,
            )

            return {"success": True, **result}
        except ImportError:
            return {"success": False, "error": "Initial Scanner 모듈을 사용할 수 없습니다."}
        except Exception as e:
            return {"success": False, "error": f"프로젝트 스캔 실패: {str(e)}"}

    def rescan_project(
        self, project_id: str, project_path: str, force_full: bool = False
    ) -> Dict[str, Any]:
        """
        프로젝트 증분 재스캔

        Args:
            project_id: 프로젝트 ID
            project_path: 프로젝트 경로
            force_full: 강제 전체 재스캔 여부

        Returns:
            재스캔 결과
        """
        try:
            from core.initial_scanner import rescan_project as scanner_rescan

            result = scanner_rescan(
                project_id=project_id, project_path=project_path, force_full=force_full
            )

            return {"success": True, **result}
        except ImportError:
            return {"success": False, "error": "Initial Scanner 모듈을 사용할 수 없습니다."}
        except Exception as e:
            return {"success": False, "error": f"프로젝트 재스캔 실패: {str(e)}"}

    # ========================================================================
    # Reference History Tools (Phase 1)
    # ========================================================================

    def record_reference(
        self,
        project_id: str,
        branch_id: str,
        task_keywords: List[str],
        contexts_used: List[str],
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        맥락 참조 이력 기록

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            task_keywords: 작업 키워드 목록
            contexts_used: 사용된 맥락 ID 목록
            query: 원본 쿼리

        Returns:
            기록 결과
        """
        if not self.reference_history_enabled or not self.reference_history:
            return {
                "success": False,
                "error": "Reference History 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.reference_history.record_reference(
                project_id=project_id,
                branch_id=branch_id,
                task_keywords=task_keywords,
                contexts_used=contexts_used,
                query=query,
            )
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"참조 이력 기록 실패: {str(e)}"}

    def update_reference_feedback(
        self,
        project_id: str,
        feedback: str,
        entry_timestamp: Optional[str] = None,
        contexts_actually_used: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Reference History 피드백 업데이트

        Args:
            project_id: 프로젝트 ID
            feedback: 피드백 유형 (accepted/rejected/modified)
            entry_timestamp: 특정 엔트리 타임스탬프
            contexts_actually_used: 실제 사용된 맥락 (modified인 경우)

        Returns:
            업데이트 결과
        """
        if not self.reference_history_enabled or not self.reference_history:
            return {
                "success": False,
                "error": "Reference History 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.reference_history.update_feedback(
                feedback=feedback,
                entry_timestamp=entry_timestamp,
                contexts_actually_used=contexts_actually_used,
            )
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"피드백 업데이트 실패: {str(e)}"}

    def get_reference_statistics(self, project_id: str) -> Dict[str, Any]:
        """
        Reference History 통계 반환

        Args:
            project_id: 프로젝트 ID

        Returns:
            통계 정보
        """
        if not self.reference_history_enabled or not self.reference_history:
            return {
                "success": False,
                "error": "Reference History 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.reference_history.get_statistics()
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"통계 조회 실패: {str(e)}"}

    # ========================================================================
    # Git Integration Tools (Phase 1) - 5개 메서드
    # ========================================================================

    def link_git_branch(
        self,
        project_id: str,
        repo_path: str,
        git_branch: Optional[str] = None,
        cortex_branch_id: Optional[str] = None,
        auto_create: bool = True,
    ) -> Dict[str, Any]:
        """
        Git 브랜치와 Cortex 브랜치 연동

        Args:
            project_id: 프로젝트 ID
            repo_path: Git 저장소 경로
            git_branch: Git 브랜치 이름 (없으면 현재 브랜치)
            cortex_branch_id: 연동할 Cortex 브랜치 ID (없으면 자동 생성)
            auto_create: Cortex 브랜치 자동 생성 여부

        Returns:
            연동 결과
        """
        try:
            from core.git_sync import link_git_branch as git_link

            result = git_link(
                project_id=project_id,
                repo_path=repo_path,
                git_branch=git_branch,
                cortex_branch_id=cortex_branch_id,
                auto_create=auto_create,
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"Git 브랜치 연동 실패: {str(e)}"}

    def get_git_status(self, project_id: str, repo_path: str) -> Dict[str, Any]:
        """
        Git 저장소 상태 및 Cortex 연동 정보 반환

        Args:
            project_id: 프로젝트 ID
            repo_path: Git 저장소 경로

        Returns:
            Git 상태 및 연동 정보
        """
        try:
            from core.git_sync import get_git_status as git_status

            result = git_status(project_id=project_id, repo_path=repo_path)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"Git 상태 조회 실패: {str(e)}"}

    def check_git_branch_change(
        self, project_id: str, repo_path: str, auto_create: bool = True
    ) -> Dict[str, Any]:
        """
        Git 브랜치 변경 감지 및 자동 Cortex 전환

        Args:
            project_id: 프로젝트 ID
            repo_path: Git 저장소 경로
            auto_create: 새 브랜치일 경우 Cortex 브랜치 자동 생성

        Returns:
            브랜치 변경 감지 결과
        """
        try:
            from core.git_sync import check_git_branch_change as git_check

            result = git_check(project_id=project_id, repo_path=repo_path, auto_create=auto_create)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"Git 브랜치 변경 감지 실패: {str(e)}"}

    def list_git_links(self, project_id: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Git-Cortex 브랜치 연동 목록 반환

        Args:
            project_id: 프로젝트 ID
            repo_path: Git 저장소 경로 (필터링용, 선택)

        Returns:
            연동 목록
        """
        try:
            from core.git_sync import list_git_links as git_list

            result = git_list(project_id=project_id, repo_path=repo_path)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"Git 연동 목록 조회 실패: {str(e)}"}

    def unlink_git_branch(self, project_id: str, repo_path: str, git_branch: str) -> Dict[str, Any]:
        """
        Git-Cortex 브랜치 연동 해제

        Args:
            project_id: 프로젝트 ID
            repo_path: Git 저장소 경로
            git_branch: 연동 해제할 Git 브랜치 이름

        Returns:
            연동 해제 결과
        """
        try:
            from core.git_sync import unlink_git_branch as git_unlink

            result = git_unlink(project_id=project_id, repo_path=repo_path, git_branch=git_branch)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"Git 연동 해제 실패: {str(e)}"}

    # ========================================================================
    # Dashboard Tool (Phase 2) - 1개 메서드
    # ========================================================================

    def get_dashboard_url(
        self, start_if_not_running: bool = True, open_browser: bool = False
    ) -> Dict[str, Any]:
        """
        Audit Dashboard URL 반환

        Args:
            start_if_not_running: 서버가 실행 중이 아니면 자동 시작
            open_browser: 브라우저 자동 열기

        Returns:
            Dashboard URL 및 상태
        """
        try:
            from dashboard.server import get_dashboard_url as dash_url

            # dashboard.server.get_dashboard_url()가 이미 완전한 Dict 반환
            result = dash_url(start_if_not_running=start_if_not_running, open_browser=open_browser)

            return result  # 그대로 반환 (success 필드 이미 포함)
        except Exception as e:
            return {"success": False, "error": f"Dashboard URL 조회 실패: {str(e)}"}

    # ========================================================================
    # Backup/Snapshot Tools (Phase 2) - 4개 메서드
    # ========================================================================

    def create_snapshot(
        self,
        project_id: str,
        branch_id: Optional[str] = None,
        description: Optional[str] = None,
        snapshot_type: str = "manual",
    ) -> Dict[str, Any]:
        """
        프로젝트 스냅샷 생성

        Args:
            project_id: 프로젝트 ID
            branch_id: 특정 브랜치만 스냅샷 (선택)
            description: 스냅샷 설명
            snapshot_type: 스냅샷 유형 (manual/auto/git_commit)

        Returns:
            스냅샷 생성 결과
        """
        try:
            from core.backup_manager import create_snapshot as backup_create

            result = backup_create(
                project_id=project_id,
                branch_id=branch_id,
                description=description,
                snapshot_type=snapshot_type,
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"스냅샷 생성 실패: {str(e)}"}

    def restore_snapshot(
        self, project_id: str, snapshot_id: str, overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        스냅샷에서 복원

        Args:
            project_id: 프로젝트 ID
            snapshot_id: 복원할 스냅샷 ID
            overwrite: 자동 백업 없이 덮어쓰기

        Returns:
            복원 결과
        """
        try:
            from core.backup_manager import restore_snapshot as backup_restore

            result = backup_restore(
                project_id=project_id, snapshot_id=snapshot_id, overwrite=overwrite
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"스냅샷 복원 실패: {str(e)}"}

    def list_snapshots(
        self, project_id: str, snapshot_type: Optional[str] = None, limit: int = 20
    ) -> Dict[str, Any]:
        """
        스냅샷 목록 조회

        Args:
            project_id: 프로젝트 ID
            snapshot_type: 특정 타입만 필터링 (선택)
            limit: 최대 결과 수

        Returns:
            스냅샷 목록
        """
        try:
            from core.backup_manager import list_snapshots as backup_list

            result = backup_list(project_id=project_id, snapshot_type=snapshot_type, limit=limit)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"스냅샷 목록 조회 실패: {str(e)}"}

    def get_backup_history(self, project_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        백업 히스토리 조회

        Args:
            project_id: 프로젝트 ID
            limit: 최대 결과 수

        Returns:
            백업 히스토리 타임라인
        """
        try:
            from core.backup_manager import get_backup_history as backup_history

            result = backup_history(project_id=project_id, limit=limit)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"백업 히스토리 조회 실패: {str(e)}"}

    # ========================================================================
    # Automation Tools (Phase 2) - 4개 메서드
    # ========================================================================

    def get_automation_status(self, project_id: str) -> Dict[str, Any]:
        """
        자동화 상태 조회 (Plan A/B 모드)

        Args:
            project_id: 프로젝트 ID

        Returns:
            자동화 상태 (모드, 거부율, 성공률)
        """
        try:
            from core.automation_manager import get_automation_status as auto_status

            result = auto_status(project_id=project_id)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"자동화 상태 조회 실패: {str(e)}"}

    def record_automation_feedback(
        self, project_id: str, action_type: str, feedback: str, action_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        자동화 피드백 기록

        Args:
            project_id: 프로젝트 ID
            action_type: 작업 유형 (branch_create, context_load, etc.)
            feedback: 피드백 유형 (accepted, rejected, modified, ignored)
            action_id: 작업 ID (선택)

        Returns:
            피드백 기록 결과
        """
        try:
            from core.automation_manager import record_automation_feedback as auto_feedback

            result = auto_feedback(
                project_id=project_id,
                action_type=action_type,
                feedback=feedback,
                action_id=action_id,
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"피드백 기록 실패: {str(e)}"}

    def should_confirm_action(self, project_id: str, action_type: str) -> Dict[str, Any]:
        """
        작업 확인 필요 여부 판단

        Args:
            project_id: 프로젝트 ID
            action_type: 작업 유형

        Returns:
            확인 필요 여부 (Plan A: false, Plan B: true)
        """
        try:
            from core.automation_manager import should_confirm_action as auto_confirm

            result = auto_confirm(project_id=project_id, action_type=action_type)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"확인 필요 여부 판단 실패: {str(e)}"}

    def set_automation_mode(
        self, project_id: str, mode: str, disable_auto_switch: bool = False
    ) -> Dict[str, Any]:
        """
        자동화 모드 수동 설정

        Args:
            project_id: 프로젝트 ID
            mode: 설정할 모드 (auto/semi_auto)
            disable_auto_switch: 자동 전환 비활성화

        Returns:
            모드 설정 결과
        """
        try:
            from core.automation_manager import set_automation_mode as auto_mode

            result = auto_mode(
                project_id=project_id, mode=mode, disable_auto_switch=disable_auto_switch
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"자동화 모드 설정 실패: {str(e)}"}

    # ========================================================================
    # Boundary Protection Tools (Phase 3) - 6개 메서드
    # ========================================================================

    def set_boundary(
        self,
        project_id: str,
        task: str,
        project_path: Optional[str] = None,
        allowed_files: Optional[List[str]] = None,
        allowed_patterns: Optional[List[str]] = None,
        allowed_actions: Optional[List[str]] = None,
        strict_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        작업 경계 수동 설정

        Args:
            project_id: 프로젝트 ID
            task: 현재 작업 설명
            project_path: 프로젝트 루트 경로 (선택)
            allowed_files: 허용된 파일 목록
            allowed_patterns: 허용된 파일 패턴
            allowed_actions: 허용된 작업 유형 (READ, WRITE, CREATE, DELETE, MODIFY)
            strict_mode: 엄격 모드 활성화

        Returns:
            경계 설정 결과
        """
        try:
            from core.boundary_protection import set_boundary as boundary_set

            result = boundary_set(
                project_id=project_id,
                task=task,
                project_path=project_path,
                allowed_files=allowed_files,
                allowed_patterns=allowed_patterns,
                allowed_actions=allowed_actions,
                strict_mode=strict_mode,
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"작업 경계 설정 실패: {str(e)}"}

    def infer_boundary(
        self,
        project_id: str,
        task: str,
        project_path: Optional[str] = None,
        recent_files: Optional[List[str]] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        작업 경계 자동 추론

        Args:
            project_id: 프로젝트 ID
            task: 현재 작업 설명
            project_path: 프로젝트 루트 경로 (선택)
            recent_files: 최근 작업한 파일 목록 (선택)
            context: 추가 맥락 정보 (선택)

        Returns:
            추론된 경계 설정
        """
        try:
            from core.boundary_protection import infer_boundary as boundary_infer

            result = boundary_infer(
                project_id=project_id,
                task=task,
                project_path=project_path,
                recent_files=recent_files,
                context=context,
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"작업 경계 추론 실패: {str(e)}"}

    def validate_boundary_action(
        self, project_id: str, file_path: str, action: str, project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        파일 작업 유효성 검증

        Args:
            project_id: 프로젝트 ID
            file_path: 검증할 파일 경로
            action: 작업 유형 (READ, WRITE, CREATE, DELETE, MODIFY)
            project_path: 프로젝트 루트 경로 (선택)

        Returns:
            유효성 검증 결과
        """
        try:
            from core.boundary_protection import validate_boundary_action as boundary_validate

            result = boundary_validate(
                project_id=project_id, file_path=file_path, action=action, project_path=project_path
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"작업 유효성 검증 실패: {str(e)}"}

    def get_boundary_protocol(
        self, project_id: str, project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        System Prompt용 경계 프로토콜 생성

        Args:
            project_id: 프로젝트 ID
            project_path: 프로젝트 루트 경로 (선택)

        Returns:
            경계 프로토콜 문자열
        """
        try:
            from core.boundary_protection import get_boundary_protocol as boundary_protocol

            result = boundary_protocol(project_id=project_id, project_path=project_path)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"경계 프로토콜 조회 실패: {str(e)}"}

    def get_boundary_violations(
        self, project_id: str, project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        경계 위반 이력 조회

        Args:
            project_id: 프로젝트 ID
            project_path: 프로젝트 루트 경로 (선택)

        Returns:
            위반 이력 목록
        """
        try:
            from core.boundary_protection import get_boundary_violations as boundary_violations

            result = boundary_violations(project_id=project_id, project_path=project_path)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"경계 위반 조회 실패: {str(e)}"}

    def clear_boundary(self, project_id: str, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        경계 설정 초기화

        Args:
            project_id: 프로젝트 ID
            project_path: 프로젝트 루트 경로 (선택)

        Returns:
            초기화 결과
        """
        try:
            from core.boundary_protection import clear_boundary as boundary_clear

            result = boundary_clear(project_id=project_id, project_path=project_path)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"경계 초기화 실패: {str(e)}"}

    # ========================================================================
    # Context Graph Tools (Phase 1) - 2개 메서드
    # ========================================================================

    def get_scan_estimate(self, project_path: str, scan_mode: str) -> Dict[str, Any]:
        """
        스캔 예상 비용 조회

        Args:
            project_path: 프로젝트 루트 경로
            scan_mode: 예상할 스캔 모드 (FULL/LIGHT)

        Returns:
            예상 정보 (파일 수, 토큰, 비용)
        """
        try:
            from core.initial_scanner import get_scan_estimate as scanner_estimate

            result = scanner_estimate(project_path=project_path, scan_mode=scan_mode)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"스캔 예상 조회 실패: {str(e)}"}

    def get_context_graph_info(self, project_id: str) -> Dict[str, Any]:
        """
        Context Graph 통계 조회

        Args:
            project_id: 프로젝트 고유 식별자

        Returns:
            Context Graph 상태 (노드 수, 엣지 수, 언어별 분포 등)
        """
        try:
            from core.context_graph import get_context_graph_info as graph_info

            result = graph_info(project_id=project_id)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"Context Graph 정보 조회 실패: {str(e)}"}

    # ========================================================================
    # Semantic Web Enterprise Tools (Phase 3) - 5개 메서드
    # ========================================================================

    def add_semantic_relation(
        self, project_id: str, source: str, target: str, relation_type: str, confidence: float = 1.0
    ) -> Dict[str, Any]:
        """
        시맨틱 웹에 관계 추가 (Enterprise 전용)

        Args:
            project_id: 프로젝트 ID
            source: 소스 Context ID
            target: 타겟 Context ID
            relation_type: 관계 유형 (DEPENDS_ON, REFERENCES, PART_OF, etc.)
            confidence: 신뢰도 (0.0-1.0)

        Returns:
            관계 추가 결과
        """
        if not self.semantic_web_enabled:
            return {"success": False, "error": "Semantic Web 기능은 Enterprise 전용입니다."}

        try:
            from core.semantic_web import add_semantic_relation as semantic_add

            result = semantic_add(
                project_id=project_id,
                source=source,
                target=target,
                relation_type=relation_type,
                confidence=confidence,
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"시맨틱 관계 추가 실패: {str(e)}"}

    def infer_relations(
        self, project_id: str, context_id: str, relation_type: str, max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        전이적 관계 추론 (Enterprise 전용)

        Args:
            project_id: 프로젝트 ID
            context_id: 시작점 Context ID
            relation_type: 추론할 관계 유형
            max_depth: 최대 탐색 깊이

        Returns:
            추론된 관계 목록
        """
        if not self.semantic_web_enabled:
            return {"success": False, "error": "Semantic Web 기능은 Enterprise 전용입니다."}

        try:
            from core.semantic_web import infer_relations as semantic_infer

            result = semantic_infer(
                project_id=project_id,
                context_id=context_id,
                relation_type=relation_type,
                max_depth=max_depth,
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"관계 추론 실패: {str(e)}"}

    def detect_conflicts(self, project_id: str, context_id: Optional[str] = None) -> Dict[str, Any]:
        """
        충돌 감지 (Enterprise 전용)

        Args:
            project_id: 프로젝트 ID
            context_id: 특정 Context만 검사 (선택)

        Returns:
            충돌 목록 (정책 충돌, 버전 충돌 등)
        """
        if not self.semantic_web_enabled:
            return {"success": False, "error": "Semantic Web 기능은 Enterprise 전용입니다."}

        try:
            from core.semantic_web import detect_conflicts as semantic_conflicts

            result = semantic_conflicts(project_id=project_id, context_id=context_id)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"충돌 감지 실패: {str(e)}"}

    def suggest_related_contexts(
        self, project_id: str, context_id: str, max_depth: int = 3, min_confidence: float = 0.3
    ) -> Dict[str, Any]:
        """
        시맨틱 웹 기반 관련 맥락 추천 (Enterprise 전용)

        Args:
            project_id: 프로젝트 ID
            context_id: 시작점 Context ID
            max_depth: 최대 탐색 깊이
            min_confidence: 최소 신뢰도

        Returns:
            관련 맥락 추천 목록
        """
        if not self.semantic_web_enabled:
            return {"success": False, "error": "Semantic Web 기능은 Enterprise 전용입니다."}

        try:
            from core.semantic_web import suggest_related_contexts as semantic_suggest

            result = semantic_suggest(
                project_id=project_id,
                context_id=context_id,
                max_depth=max_depth,
                min_confidence=min_confidence,
            )

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"관련 맥락 추천 실패: {str(e)}"}

    def get_semantic_web_stats(self, project_id: str) -> Dict[str, Any]:
        """
        시맨틱 웹 통계 반환 (Enterprise 전용)

        Args:
            project_id: 프로젝트 ID

        Returns:
            통계 정보 (관계 수, 노드 수, 관계 유형별 분포 등)
        """
        if not self.semantic_web_enabled:
            return {"success": False, "error": "Semantic Web 기능은 Enterprise 전용입니다."}

        try:
            from core.semantic_web import get_semantic_web_stats as semantic_stats

            result = semantic_stats(project_id=project_id)

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": f"시맨틱 웹 통계 조회 실패: {str(e)}"}

    # ========================================================================
    # Hierarchy Tools (Phase 1) - 3개 메서드 추가
    # ========================================================================

    def create_node(
        self,
        project_id: str,
        branch_id: str,
        node_name: str,
        context_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Node 그룹 생성 (30+ Context 시)

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            node_name: Node 이름
            context_ids: 이 Node에 포함할 Context ID 목록 (선택)

        Returns:
            Node 생성 결과
        """
        try:
            # 브랜치 메타데이터 로드
            branch_index = self._load_branch_index(project_id, branch_id)

            # Node 생성
            node_id = f"node_{node_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S%f')}"
            node_data = {
                "node_id": node_id,
                "node_name": node_name,
                "context_ids": context_ids or [],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # 브랜치 인덱스에 Node 추가
            if "nodes" not in branch_index:
                branch_index["nodes"] = []
            branch_index["nodes"].append(node_data)

            # 저장
            self._save_branch_index(project_id, branch_id, branch_index)

            return {
                "success": True,
                "node_id": node_id,
                "node_name": node_name,
                "context_count": len(context_ids or []),
            }
        except Exception as e:
            return {"success": False, "error": f"Node 생성 실패: {str(e)}"}

    def suggest_node_grouping_v2(
        self, project_id: str, branch_id: str, auto_create: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Node 그룹핑 필요 여부 확인 및 제안 (v2 - deprecated, 2773라인 함수 사용 권장)

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            auto_create: None이면 Feature Flag에 따름, True/False면 강제 설정

        Returns:
            그룹핑 제안 (필요 여부, 제안된 그룹 등)
        """
        try:
            # 브랜치의 Context 개수 확인
            branch_index = self._load_branch_index(project_id, branch_id)
            context_count = len(branch_index.get("contexts", []))

            # 30개 미만이면 그룹핑 불필요
            if context_count < 30:
                return {
                    "success": True,
                    "needs_grouping": False,
                    "context_count": context_count,
                    "threshold": 30,
                    "recommendation": "현재 Context 개수가 적절합니다.",
                }

            # auto_create 결정 (Feature Flag 또는 파라미터)
            should_auto_create = auto_create
            if should_auto_create is None:
                should_auto_create = not config.feature_flags.node_grouping_confirm_required

            created_nodes = []
            if should_auto_create:
                # 자동 노드 생성
                node_name = f"auto_group_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                node_result = self.create_node(
                    project_id=project_id,
                    branch_id=branch_id,
                    node_name=node_name,
                    context_ids=[]
                )
                if node_result.get("success"):
                    created_nodes.append(node_result.get("node_id"))

            return {
                "success": True,
                "needs_grouping": True,
                "context_count": context_count,
                "threshold": 30,
                "auto_created": len(created_nodes) > 0,
                "created_nodes": created_nodes,
                "recommendation": f"{context_count}개의 Context가 있어 {'자동 그룹핑 완료' if created_nodes else 'Node 그룹핑을 권장합니다.'}",
            }
        except Exception as e:
            return {"success": False, "error": f"그룹핑 제안 실패: {str(e)}"}

    # ========================================================================
    # Phase 9: Evidence Graph Helper Methods
    # ========================================================================

    def _update_evidence_graph(self, content: str, branch_id: str, project_id: str):
        """
        Evidence Graph 자동 업데이트 (Phase 9 검증 전)

        Args:
            content: 응답 내용
            branch_id: 현재 브랜치 ID
            project_id: 프로젝트 ID
        """
        if not self.claim_verifier:
            return

        try:
            import time
            import os
            import hashlib

            # 1. ClaimVerifier의 파일 참조 추출 메서드 재사용
            file_refs = self.claim_verifier._extract_file_references(content)

            if not file_refs:
                return

            logger.debug(f"Evidence Graph 업데이트: {len(file_refs)}개 파일 참조 발견")

            # 2. 각 파일에 대해 Evidence Graph 노드 추가
            for file_path in file_refs:
                # ClaimVerifier의 project_path 기준으로 파일 존재 확인
                full_path = self.claim_verifier.project_path / file_path

                if not full_path.exists():
                    logger.debug(f"할루시네이션 감지: {file_path} 파일 존재하지 않음")
                    continue

                # 파일이 실제로 존재하면 Evidence 추가
                # 현재 시간을 메타데이터로 사용
                current_time = datetime.now(timezone.utc).isoformat()
                content_hash = hashlib.sha256(file_path.encode()).hexdigest()

                # File 노드 추가
                self.claim_verifier.evidence_graph.add_file_node(
                    file_path=file_path, last_modified=current_time, content_hash=content_hash
                )

                # Diff 노드 추가 (파일이 존재하고 LLM이 언급함)
                commit_hash = f"update_{int(time.time())}"
                self.claim_verifier.evidence_graph.add_diff_node(
                    commit_hash=commit_hash, file_path=file_path, diff_content="LLM 응답에서 파일 참조 발견"
                )

                logger.debug(f"Evidence Graph: {file_path} 노드 추가 완료")

            # 디버그: Evidence Graph 내용 확인
            total_nodes = self.claim_verifier.evidence_graph.graph.number_of_nodes()
            diff_nodes = [
                (nid, data)
                for nid, data in self.claim_verifier.evidence_graph.graph.nodes(data=True)
                if data.get("type") == "Diff"
            ]
            logger.debug(
                f"Evidence Graph: 총 {total_nodes}개 노드, {len(diff_nodes)}개 Diff 노드"
            )
            if diff_nodes:
                for nid, data in diff_nodes[:3]:  # 처음 3개만 출력
                    logger.debug(f"- Diff: {nid}, file_path={data.get('file_path')}")

        except Exception as e:
            logger.debug(f"Evidence Graph 업데이트 실패: {e}")
            import traceback
            traceback.print_exc()

    def _get_branch_context_ids(self, project_id: str, branch_id: str) -> List[str]:
        """현재 브랜치의 Context 노드 ID 목록 반환 (referenced_contexts용)

        Evidence Graph에서 해당 브랜치의 Context 타입 노드 ID 목록을 반환합니다.
        File 노드는 포함하지 않습니다 (grounding_scorer에서 Context→File 엣지로 추적).
        """
        try:
            # Evidence Graph에서 해당 브랜치의 Context 타입 노드 ID 목록 추출
            context_nodes = []
            if hasattr(self, 'claim_verifier') and self.claim_verifier:
                for node_id, node_data in self.claim_verifier.evidence_graph.graph.nodes(data=True):
                    node_type = node_data.get("type", "")
                    node_branch_id = node_data.get("branch_id", "")

                    # Context 타입 노드이고, 해당 브랜치에 속한 경우
                    if node_type in ["Context", "llm_response", "generic_context"] and node_branch_id == branch_id:
                        context_nodes.append(node_id)

            # [DEBUG] 반환하는 노드 ID 샘플 출력
            logger.debug(f"_get_branch_context_ids 반환 노드 수: {len(context_nodes)} (브랜치: {branch_id})")
            if context_nodes:
                logger.debug(f"_get_branch_context_ids 노드 샘플 (최대 3개): {context_nodes[:3]}")

            return context_nodes
        except Exception as e:
            logger.debug(f"Context ID 목록 가져오기 실패: {e}")
            import traceback
            traceback.print_exc()
            return []

    # NOTE: get_hierarchy 메서드 중복 정의 제거됨 (Line 1179에 통합된 버전 사용)
    # 이전 구현은 _load_project_index 기반이었으나,
    # list_branches 기반으로 통합되어 더 안정적입니다.

    def _find_file_in_project(self, project_path: Path, filename: str) -> Optional[Path]:
        """
        프로젝트 내에서 파일을 재귀적으로 찾기

        Args:
            project_path: 프로젝트 루트 경로
            filename: 찾을 파일명 (경로 포함 가능)

        Returns:
            찾은 파일의 절대 경로, 없으면 None
        """
        import os
        from pathlib import Path

        # 파일명만 추출 (경로가 포함되어 있을 수 있음)
        target_filename = Path(filename).name

        # 프로젝트 내에서 재귀적으로 탐색
        for root, dirs, files in os.walk(project_path):
            # 제외할 디렉토리 (.git, __pycache__, node_modules, .venv 등)
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build']]

            if target_filename in files:
                found_path = Path(root) / target_filename
                logger.debug(f"_find_file_in_project: '{filename}' → '{found_path}'")
                return found_path

        logger.debug(f"_find_file_in_project: '{filename}' 찾을 수 없음")
        return None

    def _parse_git_diff(self, diff_output: str) -> Dict[str, str]:
        """
        Git diff 출력을 파싱하여 파일별 변경사항 추출

        Args:
            diff_output: git diff 명령어 출력

        Returns:
            {
                "file_path": "diff content",
                ...
            }
        """
        changed_files = {}
        current_file = None
        current_diff = []

        for line in diff_output.split('\n'):
            if line.startswith('diff --git'):
                # 이전 파일 저장
                if current_file and current_diff:
                    changed_files[current_file] = '\n'.join(current_diff)

                # 새 파일 시작
                # "diff --git a/path/file.py b/path/file.py" 형식
                parts = line.split(' b/')
                if len(parts) >= 2:
                    current_file = parts[-1]
                    current_diff = []
            else:
                if current_file is not None:
                    current_diff.append(line)

        # 마지막 파일 저장
        if current_file and current_diff:
            changed_files[current_file] = '\n'.join(current_diff)

        return changed_files

    def _get_current_git_commit(self, project_path: Path) -> Optional[str]:
        """
        현재 Git 커밋 해시를 가져옵니다.

        Args:
            project_path: 프로젝트 루트 경로

        Returns:
            커밋 해시 (short), 또는 None (git이 없거나 커밋이 없는 경우)
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                commit_hash = result.stdout.strip()
                return commit_hash if commit_hash else None
            else:
                return None

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Git 커밋 해시 가져오기 실패: {e}")
            return None

    def _update_evidence_graph(
        self,
        project_id: str,
        branch_id: str,
        content: str
    ) -> dict:
        """
        LLM 응답에서 파일 참조를 추출하고 Evidence Graph 업데이트

        Phase 9 할루시네이션 검증을 위해 Evidence Graph를 실시간으로 업데이트합니다.

        Steps:
        1. 파일 참조 추출 (정규식: 일반적인 소스 파일 확장자)
        2. Git diff 파싱 (최근 변경사항 감지)
        3. File 노드 추가
        4. Diff 노드 추가 (변경사항 있을 때)
        5. Edge 연결

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            content: LLM 응답 텍스트

        Returns:
            dict: {"nodes_added": int, "edges_added": int}
        """
        # 카운터 초기화
        stats = {"nodes_added": 0, "edges_added": 0}

        try:
            import re
            import subprocess
            from pathlib import Path

            # 1. 파일 참조 추출 (일반적인 소스 파일 확장자)
            # 단어 경계 제거: 파일명에는 점(.)과 하이픈(-)이 포함되므로 \b가 작동하지 않음
            file_pattern = r'[a-zA-Z0-9_/.-]+\.(?:py|js|ts|tsx|jsx|md|json|txt|yaml|yml|toml|sh|html|css|scss)'
            file_refs = re.findall(file_pattern, content)
            file_refs = list(set(file_refs))  # 중복 제거

            if not file_refs:
                return stats

            logger.debug(f"Evidence Graph 업데이트: {len(file_refs)}개 파일 참조 발견")

            # CRITICAL FIX: Context 노드 생성 (엣지 연결을 위해 필수)
            # ============================================================
            import hashlib

            context_content = f"branch:{branch_id}|content_preview:{content[:100]}"
            context_hash = hashlib.sha256(context_content.encode()).hexdigest()
            context_id = f"context:{branch_id}:{datetime.now(timezone.utc).isoformat()[:19]}"  # 초 단위까지만

            # Context 노드를 Evidence Graph에 추가
            if hasattr(self, 'claim_verifier') and self.claim_verifier:
                try:
                    self.claim_verifier.evidence_graph.add_context_node(
                        context_id=context_id,
                        branch_id=branch_id,
                        content_hash=context_hash,
                        metadata={
                            "type": "llm_response",
                            "content_preview": content[:200],
                            "file_refs_count": len(file_refs)
                        }
                    )
                    stats["nodes_added"] += 1
                    logger.debug(f"Evidence Graph: Context 노드 추가 - {context_id}")
                except Exception as ctx_err:
                    logger.error(f"Context 노드 추가 실패: {ctx_err}")

            # 2. Git diff 파싱 (선택적 - Git 저장소가 없어도 작동)
            changed_files = {}
            project_path = None
            if hasattr(self, 'claim_verifier') and self.claim_verifier:
                project_path = str(self.claim_verifier.project_path)

            # CRITICAL FIX: project_path가 없으면 fallback to cwd()
            if not project_path:
                project_path = str(Path.cwd())
                logger.debug(f"Evidence Graph: project_path 미설정 → fallback to: {project_path}")

            try:
                if project_path:
                    # Git 저장소 확인
                    git_check = subprocess.run(
                        ["git", "rev-parse", "--git-dir"],
                        cwd=project_path,
                        capture_output=True,
                        timeout=5
                    )

                    if git_check.returncode == 0:
                        # Git diff 실행
                        result = subprocess.run(
                            ["git", "diff", "HEAD"],
                            cwd=project_path,
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            changed_files = self._parse_git_diff(result.stdout)
                            logger.debug(f"Git diff: {len(changed_files)}개 파일 변경 감지")
            except Exception as git_err:
                logger.debug(f"Git diff 실패 (무시하고 계속): {git_err}")

            # 3. changed_files를 파일명으로도 인덱싱 (매칭 성능 향상)
            changed_files_by_name = {}
            for full_path_str, content in changed_files.items():
                filename = Path(full_path_str).name
                if filename not in changed_files_by_name:
                    changed_files_by_name[filename] = (full_path_str, content)
                else:
                    # 동일한 파일명이 여러 경로에 있는 경우 경고
                    logger.warning(f"동일한 파일명 중복 발견: {filename} (첫 번째 매칭 사용)")

            # 4. Evidence Graph 업데이트
            import hashlib
            from datetime import datetime

            for file_ref in file_refs:
                matched_diff_path = None
                matched_diff_content = None
                actual_file_path = None

                # 4.1. 전체 경로 매칭 시도 (file_ref가 상대 경로인 경우)
                if file_ref in changed_files:
                    matched_diff_path = file_ref
                    matched_diff_content = changed_files[file_ref]
                    if project_path:
                        actual_file_path = Path(project_path) / file_ref
                    logger.debug(f"매칭 성공 (전체 경로): {file_ref}")

                # 4.2. 파일명 매칭 시도 (file_ref가 파일명만 있는 경우)
                # CRITICAL BUG FIX: 명시적 경로 제공 시 퍼지 매칭 비활성화
                # 예: "tests/core/file.py" vs "src/core/file.py" → 다른 파일로 취급
                # 예: "file.py" → 퍼지 매칭 허용 (사용자 편의성)
                else:
                    # 경로 구분자가 있으면 명시적 경로로 판단
                    is_explicit_path = '/' in file_ref or '\\' in file_ref

                    if not is_explicit_path:
                        # 파일명만 있는 경우에만 퍼지 매칭 허용
                        filename = Path(file_ref).name
                        if filename in changed_files_by_name:
                            matched_diff_path, matched_diff_content = changed_files_by_name[filename]
                            if project_path:
                                actual_file_path = Path(project_path) / matched_diff_path
                            logger.debug(f"매칭 성공 (파일명 only): {file_ref} → {matched_diff_path}")
                    else:
                        # 명시적 경로인데 전체 경로 매칭 실패 → 퍼지 매칭 비활성화
                        logger.debug(f"명시적 경로 퍼지 매칭 비활성화: {file_ref}")

                # 4.3. 프로젝트 내에서 파일 찾기 (Git diff에 없는 경우)
                # CRITICAL BUG FIX: 명시적 경로가 제공된 경우 파일명 기반 검색 비활성화
                # 예: "tests/core/file.py" → _find_file_in_project 실행 안 함
                # 예: "file.py" → _find_file_in_project 실행 (파일명만 제공된 경우)
                if not actual_file_path and project_path:
                    is_explicit_path = '/' in file_ref or '\\' in file_ref
                    if not is_explicit_path:
                        # 파일명만 제공된 경우에만 프로젝트 전체 검색
                        found_path = self._find_file_in_project(Path(project_path), file_ref)
                        if found_path:
                            actual_file_path = found_path
                            # Git diff에도 있는지 다시 확인
                            try:
                                relative_path = found_path.relative_to(project_path)
                                if str(relative_path) in changed_files:
                                    matched_diff_path = str(relative_path)
                                    matched_diff_content = changed_files[str(relative_path)]
                                    logger.debug(f"Git diff에서 재발견: {relative_path}")
                            except ValueError:
                                pass  # relative_to 실패 시 무시
                    else:
                        # 명시적 경로는 _find_file_in_project 건너뜀
                        logger.debug(f"명시적 경로는 _find_file_in_project 건너뜀: {file_ref}")

                # 4.4. actual_file_path 존재 여부 최종 확인
                if actual_file_path and not actual_file_path.exists():
                    actual_file_path = None

                # 5. Evidence Graph 노드 추가
                # CRITICAL BUG FIX: 명시적 경로 불일치 검사
                # 명시적 경로("tests/core/file.py")가 제공되었는데 실제로는 다른 경로("cortex_mcp/core/file.py")의 파일이 매칭된 경우 → 할루시네이션
                node_id = f"file://{file_ref}"
                is_explicit_path = '/' in file_ref or '\\' in file_ref
                path_exact_match = (file_ref == matched_diff_path) if matched_diff_path else False

                if matched_diff_path and matched_diff_content:
                    if is_explicit_path and not path_exact_match:
                        # 명시적 경로인데 정확히 매칭되지 않음 → Missing 노드 (할루시네이션)
                        self.claim_verifier.evidence_graph.add_missing_node(
                            file_path=node_id,
                            description=f"명시적 경로 불일치: 요청={file_ref}, 실제={matched_diff_path}",
                            metadata={"confidence": 0.1}
                        )
                        stats["nodes_added"] += 1
                        logger.debug(f"Evidence Graph: Missing 노드 (경로 불일치) - {node_id} (요청: {file_ref}, 실제: {matched_diff_path})")

                        # HALLUCINATION 엣지 추가
                        try:
                            self.claim_verifier.evidence_graph.add_hallucination_edge(
                                source=context_id,
                                target=node_id
                            )
                            stats["edges_added"] += 1
                            logger.debug(f"Evidence Graph: 엣지 추가 - {context_id} → {node_id} (REFERENCED - HALLUCINATION)")
                        except Exception as edge_err:
                            logger.error(f"HALLUCINATION 엣지 추가 실패: {edge_err}")
                    else:
                        # Case A: Git diff에 있음 + 경로 일치 (또는 파일명만 제공) → Diff 노드 (confidence: 0.9)
                        self.claim_verifier.evidence_graph.add_diff_node(
                            commit_hash="uncommitted",
                            file_path=node_id,
                            diff_content=matched_diff_content[:500],
                            metadata={"confidence": 0.9, "matched_path": matched_diff_path}
                        )
                        stats["nodes_added"] += 1
                        logger.debug(f"Evidence Graph: Diff 노드 추가 - {node_id} (매칭 경로: {matched_diff_path})")

                        # CRITICAL FIX: 엣지 추가 (Case A - Diff 노드)
                        # ============================================================
                        # 1. Context → File (REFERENCED): LLM이 파일을 참조함
                        try:
                            self.claim_verifier.evidence_graph.add_reference_edge(
                                source=context_id,
                                target=node_id
                            )
                            stats["edges_added"] += 1
                            logger.debug(f"Evidence Graph: 엣지 추가 - {context_id} → {node_id} (REFERENCED)")
                        except Exception as edge_err:
                            logger.error(f"REFERENCED 엣지 추가 실패: {edge_err}")

                        # 2. Diff → File (MODIFIED): Diff가 파일을 수정함
                        # Git 커밋 해시 기반 Diff 노드 ID 생성
                        project_path = Path(os.getcwd())
                        git_commit = self._get_current_git_commit(project_path)

                        if git_commit:
                            # Committed 변경: diff:{commit_hash}:{file_path}
                            diff_node_id = f"diff:{git_commit}:{node_id}"
                        else:
                            # Uncommitted 변경: diff:uncommitted:{timestamp}:{file_path}
                            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                            diff_node_id = f"diff:uncommitted:{timestamp}:{node_id}"

                        try:
                            self.claim_verifier.evidence_graph.add_modified_edge(
                                source=diff_node_id,
                                target=node_id
                            )
                            stats["edges_added"] += 1
                            logger.debug(f"Evidence Graph: 엣지 추가 - {diff_node_id} → {node_id} (MODIFIED)")
                        except Exception as edge_err:
                            logger.error(f"MODIFIED 엣지 추가 실패: {edge_err}")

                elif actual_file_path:
                    # Case B: 파일 존재 → File 노드 (confidence: 0.7)
                    content_hash = hashlib.sha256(file_ref.encode()).hexdigest()
                    self.claim_verifier.evidence_graph.add_file_node(
                        file_path=node_id,
                        last_modified=datetime.now(timezone.utc).isoformat(),
                        content_hash=content_hash,
                        metadata={"confidence": 0.7, "exists": True, "actual_path": str(actual_file_path)}
                    )
                    stats["nodes_added"] += 1
                    logger.debug(f"Evidence Graph: File 노드 추가 - {node_id} (실제 경로: {actual_file_path})")

                    # CRITICAL FIX: 엣지 추가 (Case B)
                    # ============================================================
                    # Context → File (REFERENCED): LLM이 파일을 참조함
                    try:
                        self.claim_verifier.evidence_graph.add_reference_edge(
                            source=context_id,
                            target=node_id
                        )
                        stats["edges_added"] += 1
                        logger.debug(f"Evidence Graph: 엣지 추가 - {context_id} → {node_id} (REFERENCED)")
                    except Exception as edge_err:
                        logger.error(f"REFERENCED 엣지 추가 실패: {edge_err}")

                else:
                    # Case C: 파일 없음 → Missing 노드 (confidence: 0.0)
                    content_hash = "missing"
                    self.claim_verifier.evidence_graph.add_file_node(
                        file_path=node_id,
                        last_modified=datetime.now(timezone.utc).isoformat(),
                        content_hash=content_hash,
                        metadata={"confidence": 0.0, "exists": False}
                    )
                    stats["nodes_added"] += 1
                    # 노드 타입을 Missing으로 변경
                    self.claim_verifier.evidence_graph.graph.nodes[node_id]["type"] = "Missing"
                    logger.debug(f"Evidence Graph: Missing 노드 추가 - {node_id} (할루시네이션 가능성)")

                    # CRITICAL FIX: 엣지 추가 (Case C)
                    # ============================================================
                    # Context → Missing (REFERENCED): LLM이 존재하지 않는 파일을 참조함 (할루시네이션)
                    try:
                        self.claim_verifier.evidence_graph.add_reference_edge(
                            source=context_id,
                            target=node_id
                        )
                        stats["edges_added"] += 1
                        logger.debug(f"Evidence Graph: 엣지 추가 - {context_id} → {node_id} (REFERENCED - HALLUCINATION)")
                    except Exception as edge_err:
                        logger.error(f"REFERENCED 엣지 추가 실패 (Missing 노드): {edge_err}")

            # 6. Git untracked 파일 자동 감지 (Problem 1 해결)
            # ============================================================
            # LLM 응답에 명시되지 않았지만 새로 생성된 파일을 자동으로 감지하여 Evidence Graph에 등록
            # 예: test_results_comprehensive.json, output_*.log 등
            untracked_files = []
            if project_path:
                try:
                    # Git status --porcelain으로 untracked 파일 감지
                    git_status_result = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if git_status_result.returncode == 0:
                        for line in git_status_result.stdout.splitlines():
                            # ?? = untracked file
                            if line.startswith("??"):
                                file_path = line[3:].strip()
                                # 특정 패턴만 자동 등록 (테스트 결과, 출력 파일 등)
                                if any(pattern in file_path for pattern in ["test_", "results", "output_", "_log", ".json"]):
                                    untracked_files.append(file_path)

                        if untracked_files:
                            logger.debug(f"Git untracked 파일 {len(untracked_files)}개 감지: {untracked_files}")

                        # Untracked 파일을 Evidence Graph에 등록
                        for file_path in untracked_files:
                            full_path = Path(project_path) / file_path
                            if full_path.exists():
                                node_id = f"file://{file_path}"
                                content_hash = hashlib.sha256(file_path.encode()).hexdigest()
                                self.claim_verifier.evidence_graph.add_file_node(
                                    file_path=node_id,
                                    last_modified=datetime.now(timezone.utc).isoformat(),
                                    content_hash=content_hash,
                                    metadata={"confidence": 0.8, "exists": True, "actual_path": str(full_path), "auto_detected": True}
                                )
                                stats["nodes_added"] += 1
                                logger.debug(f"Evidence Graph: Untracked 파일 자동 등록 - {node_id}")

                except Exception as untracked_err:
                    logger.debug(f"Git untracked 파일 감지 실패 (무시하고 계속): {untracked_err}")

            logger.debug(f"Evidence Graph 업데이트 완료: 노드 {stats['nodes_added']}개, 엣지 {stats['edges_added']}개 추가")
            return stats

        except Exception as e:
            logger.error(f"Evidence Graph 업데이트 실패: {e}")
            import traceback
            traceback.print_exc()
            return stats
