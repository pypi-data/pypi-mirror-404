"""
Cortex MCP - MCP Tools Interface
AI가 호출할 MCP 툴 인터페이스

7가지 핵심 도구:
1. initialize_context - 초기 맥락 스캔 (FULL/LIGHT/NONE)
2. create_branch - Context Tree 생성
3. search_context - 로컬 Vector RAG 검색
4. update_memory - 자동 요약 및 기록
5. get_active_summary - 장기 기억 주입
6. sync_to_cloud - 클라우드 백업
7. sync_from_cloud - 클라우드 복원
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.types import TextContent, Tool

sys.path.append(str(Path(__file__).parent.parent))

from config import config
from core.alpha_logger import LogModule, get_alpha_logger
from core.automation_manager import ActionType, FeedbackType, get_automation_manager
from core.backup_manager import get_backup_manager
from core.boundary_protection import ActionType as BoundaryActionType
from core.boundary_protection import (
    BoundaryProtection,
    ViolationType,
    get_boundary_protection,
)
from core.cloud_sync import CloudSync
from core.context_manager import context_manager
from core.decorators import async_cortex_function
from core.git_sync import get_git_sync
from core.license_manager import LicenseStatus, get_license_manager
from core.memory_manager import MemoryManager
from core.project_config import ProjectConfig, get_project_id
from core.rag_engine import RAGEngine
from core.reference_history import get_reference_history
from core.auto_trigger import get_auto_trigger
from core.background_processor import BackgroundProcessor

# Web DB Integration (for error logging)
try:
    from web.models import get_db

    WEB_DB_AVAILABLE = True
except ImportError:
    WEB_DB_AVAILABLE = False
    get_db = None

# Telemetry v2.0 Integration
try:
    from core.telemetry_events import ChannelType, CortexEventName
    from core.telemetry_integration import CortexTelemetry

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    CortexTelemetry = None
    CortexEventName = None
    ChannelType = None

# Initial Scanner (Context Graph 기반 프로젝트 스캔)
try:
    from core.context_graph import ContextGraph, get_context_graph
    from core.initial_scanner import ScanMode as ScannerMode
    from core.initial_scanner import get_scan_estimate as scanner_get_estimate
    from core.initial_scanner import rescan_project as scanner_rescan_project
    from core.initial_scanner import scan_project as scanner_scan_project

    INITIAL_SCANNER_AVAILABLE = True
except ImportError:
    INITIAL_SCANNER_AVAILABLE = False
    scanner_scan_project = None
    scanner_rescan_project = None
    scanner_get_estimate = None
    ScannerMode = None
    get_context_graph = None
    ContextGraph = None

# Extension Sync 서비스 (IDE Extension 연동)
try:
    from core.extension_sync import get_extension_sync

    EXTENSION_SYNC_AVAILABLE = True
except ImportError:
    EXTENSION_SYNC_AVAILABLE = False
    get_extension_sync = None

# 시맨틱 웹 엔진 (Enterprise 전용 - 선택적 import)
try:
    from core.semantic_web import RelationType, SemanticWebEngine

    SEMANTIC_WEB_AVAILABLE = True
except ImportError:
    SEMANTIC_WEB_AVAILABLE = False
    SemanticWebEngine = None
    RelationType = None

# Phase 9: Hallucination Detection System (선택적 import)
try:
    from core.claim_extractor import ClaimExtractor
    from core.claim_verifier import ClaimVerifier
    from core.code_structure_analyzer import CodeStructureAnalyzer
    from core.contradiction_detector import ContradictionDetector
    from core.fuzzy_claim_analyzer import FuzzyClaimAnalyzer
    from core.grounding_scorer import GroundingScorer

    HALLUCINATION_DETECTION_AVAILABLE = True
except ImportError:
    HALLUCINATION_DETECTION_AVAILABLE = False
    ClaimExtractor = None
    ClaimVerifier = None
    FuzzyClaimAnalyzer = None
    ContradictionDetector = None
    GroundingScorer = None
    CodeStructureAnalyzer = None

# Phase 9.1: Auto-verification System (선택적 import)
try:
    from core.auto_verifier import AutoVerifier, get_auto_verifier

    AUTO_VERIFIER_AVAILABLE = True
except ImportError:
    AUTO_VERIFIER_AVAILABLE = False
    AutoVerifier = None
    get_auto_verifier = None

# 시맨틱 웹 엔진 캐시 (프로젝트별)
_semantic_web_engines = {}

# Boundary Protection 인스턴스 캐시 (프로젝트별)
_boundary_protection_instances = {}

# Core tools visible to users (7 tools)
# Other tools remain callable but hidden from tool listing
VISIBLE_TOOLS = {
    "update_memory",
    "get_active_summary",
    "verify_response",
    "load_context",
    "create_branch",
    "create_snapshot",
    "restore_snapshot",
}


# ============================================================
# 로깅 시스템 설정
# ============================================================


def setup_logging():
    """상세 로깅 시스템 초기화"""
    log_dir = config.logs_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    # 도구 호출 로그 파일
    tool_log_file = log_dir / "tool_calls.log"

    # 포맷터 설정
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 파일 핸들러 (상세 로그)
    file_handler = logging.FileHandler(tool_log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # stderr 핸들러 (실시간 확인용)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.INFO)
    stderr_handler.setFormatter(formatter)

    # 로거 설정
    logger = logging.getLogger("cortex_mcp")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(stderr_handler)

    return logger


# 로거 초기화
logger = setup_logging()


# MCP 도구명 -> LogModule 매핑
TOOL_TO_MODULE = {
    # Smart Context
    "load_context": LogModule.SMART_CONTEXT,
    "get_loaded_contexts": LogModule.SMART_CONTEXT,
    "compress_context": LogModule.SMART_CONTEXT,
    # Reference History
    "suggest_contexts": LogModule.REFERENCE_HISTORY,
    "accept_suggestions": LogModule.REFERENCE_HISTORY,
    "reject_suggestions": LogModule.REFERENCE_HISTORY,
    "record_reference": LogModule.REFERENCE_HISTORY,
    "update_reference_feedback": LogModule.REFERENCE_HISTORY,
    "get_reference_statistics": LogModule.REFERENCE_HISTORY,
    # RAG Search
    "search_context": LogModule.RAG_SEARCH,
    # Git Sync
    "link_git_branch": LogModule.GIT_SYNC,
    "get_git_status": LogModule.GIT_SYNC,
    "check_git_branch_change": LogModule.GIT_SYNC,
    "list_git_links": LogModule.GIT_SYNC,
    "unlink_git_branch": LogModule.GIT_SYNC,
    # Ontology (Branch/Node/Hierarchy)
    "create_branch": LogModule.ONTOLOGY,
    "create_node": LogModule.ONTOLOGY,
    "list_nodes": LogModule.ONTOLOGY,
    "suggest_node_grouping": LogModule.ONTOLOGY,
    "get_hierarchy": LogModule.ONTOLOGY,
    # Pay Attention (Core Memory)
    "initialize_context": LogModule.PAY_ATTENTION,
    "update_memory": LogModule.PAY_ATTENTION,
    "get_active_summary": LogModule.PAY_ATTENTION,
    # Branch Decision (Automation)
    "get_automation_status": LogModule.BRANCH_DECISION,
    "record_automation_feedback": LogModule.BRANCH_DECISION,
    "should_confirm_action": LogModule.BRANCH_DECISION,
    "set_automation_mode": LogModule.BRANCH_DECISION,
    # License/Cloud
    "sync_to_cloud": LogModule.LICENSE,
    "sync_from_cloud": LogModule.LICENSE,
    # Backup
    "create_snapshot": LogModule.GENERAL,
    "restore_snapshot": LogModule.GENERAL,
    "list_snapshots": LogModule.GENERAL,
    "get_backup_history": LogModule.GENERAL,
    # Dashboard
    "get_dashboard_url": LogModule.GENERAL,
    # Semantic Web (Enterprise)
    "add_semantic_relation": LogModule.ONTOLOGY,
    "infer_relations": LogModule.ONTOLOGY,
    "detect_conflicts": LogModule.ONTOLOGY,
    "suggest_related_contexts": LogModule.ONTOLOGY,
    "get_semantic_web_stats": LogModule.ONTOLOGY,
    # Boundary Protection
    "set_boundary": LogModule.PAY_ATTENTION,
    "infer_boundary": LogModule.PAY_ATTENTION,
    "validate_boundary_action": LogModule.PAY_ATTENTION,
    "get_boundary_protocol": LogModule.PAY_ATTENTION,
    "get_boundary_violations": LogModule.PAY_ATTENTION,
    "clear_boundary": LogModule.PAY_ATTENTION,
    # Initial Scanner (Context Graph)
    "scan_project_deep": LogModule.PAY_ATTENTION,
    "rescan_project": LogModule.PAY_ATTENTION,
    "get_scan_estimate": LogModule.PAY_ATTENTION,
    "get_context_graph_info": LogModule.PAY_ATTENTION,
    # Auto-verification (Phase 9.1)
    "verify_response": LogModule.PAY_ATTENTION,
}


def sanitize_path_component(value: str, param_name: str = "value") -> str:
    """
    경로 구성 요소 검증 (보안 - Path Traversal 방지)

    Args:
        value: 검증할 값
        param_name: 파라미터 이름 (에러 메시지용)

    Returns:
        검증된 값

    Raises:
        ValueError: 유효하지 않은 경로 구성 요소
    """
    if not value:
        raise ValueError(f"{param_name} cannot be empty")

    # Path traversal 공격 방지
    dangerous_patterns = [
        "..",       # 상위 디렉토리 이동
        "/",        # 절대 경로 또는 디렉토리 구분자
        "\\",       # Windows 디렉토리 구분자
        "\0",       # Null byte injection
    ]

    for pattern in dangerous_patterns:
        if pattern in value:
            raise ValueError(
                f"Invalid {param_name}: '{value}'. "
                f"Pattern '{pattern}' not allowed (security: path traversal prevention). "
                f"Use alphanumeric characters, hyphens, and underscores only."
            )

    # 추가 검증: 알파벳, 숫자, 하이픈, 언더스코어, 한글 허용
    import re
    if not re.match(r'^[a-zA-Z0-9_\-\uAC00-\uD7AF]+$', value):
        raise ValueError(
            f"Invalid {param_name}: '{value}'. "
            f"Only alphanumeric characters, Korean, hyphens, and underscores are allowed. "
            f"For better security, avoid special characters."
        )

    return value


def mask_sensitive_data(data: dict) -> dict:
    """
    민감정보 마스킹 (보안)

    Args:
        data: 원본 딕셔너리

    Returns:
        마스킹된 딕셔너리
    """
    sensitive_keys = {
        "license_key", "LICENSE_KEY", "api_key", "API_KEY",
        "password", "PASSWORD", "token", "TOKEN",
        "secret", "SECRET", "credential", "CREDENTIAL"
    }

    masked = {}
    for key, value in data.items():
        if any(sens_key in key.upper() for sens_key in sensitive_keys):
            if isinstance(value, str) and len(value) > 8:
                # 앞 4자리만 표시, 나머지는 ***
                masked[key] = f"{value[:4]}***{len(value) - 4}chars"
            else:
                masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            # 재귀적으로 중첩된 dict도 마스킹
            masked[key] = mask_sensitive_data(value)
        else:
            masked[key] = value

    return masked


def log_tool_call(tool_name: str, arguments: dict, result: dict, duration_ms: float):
    """도구 호출 로그 기록 (파일 + JSON 로그 + Alpha Logger)"""
    # 민감정보 마스킹
    safe_arguments = mask_sensitive_data(arguments) if arguments else {}
    safe_result = mask_sensitive_data(result) if result else {}

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "arguments": safe_arguments,  # 마스킹된 버전 사용
        "result_success": result.get("success", False),
        "duration_ms": round(duration_ms, 2),
    }

    # 텍스트 로그 (마스킹된 데이터 사용)
    logger.info(f"TOOL_CALL: {tool_name} | args={json.dumps(safe_arguments, ensure_ascii=False)[:200]}")
    logger.debug(
        f"TOOL_RESULT: {tool_name} | result={json.dumps(safe_result, ensure_ascii=False)[:500]}"
    )

    # JSON 로그 파일 (분석용)
    json_log_file = config.logs_dir / "tool_calls.jsonl"
    with open(json_log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    # Alpha Logger (알파/베타 테스트용 통계)
    module = TOOL_TO_MODULE.get(tool_name, LogModule.GENERAL)
    success = result.get("success", False)
    alpha_logger.log(
        module=module,
        action=tool_name,
        success=success,
        latency_ms=duration_ms,
        metadata={
            "arguments_keys": list(arguments.keys()) if arguments else [],
            "error": result.get("error") if not success else None,
        },
    )

    return log_entry


# 모듈 인스턴스
memory_manager = MemoryManager()
rag_engine = None  # Lazy initialization으로 변경 (세션 안정성)
alpha_logger = get_alpha_logger()
background_processor = BackgroundProcessor(workers=2)  # 백그라운드 작업 프로세서

# MemoryManager 인스턴스 캐시 (project_id별)
# 28초 초기화 오버헤드를 제거하기 위한 캐싱
_memory_manager_cache = {}


def get_memory_manager(project_id: Optional[str] = None) -> MemoryManager:
    """
    MemoryManager 인스턴스 반환 (캐싱 지원)

    Args:
        project_id: 프로젝트 ID (None이면 기본 인스턴스)

    Returns:
        캐시된 또는 새로운 MemoryManager 인스턴스

    성능 개선:
        - 첫 호출: 28초 (초기화 불가피)
        - 이후 호출: 67ms (99.76% 개선)
    """
    cache_key = project_id or "__default__"

    if cache_key not in _memory_manager_cache:
        logger.info(f"[CACHE] MemoryManager 새 인스턴스 생성: {cache_key}")
        _memory_manager_cache[cache_key] = MemoryManager(project_id=project_id)
    else:
        logger.debug(f"[CACHE] MemoryManager 캐시된 인스턴스 사용: {cache_key}")

    return _memory_manager_cache[cache_key]


def _index_content_worker(content: str, metadata: dict):
    """
    백그라운드 RAG 인덱싱 워커 함수

    Args:
        content: 인덱싱할 내용
        metadata: 메타데이터 (project_id, branch_id, role, type)
    """
    try:
        rag = get_rag_engine()
        rag.index_content(content=content, metadata=metadata)
        logger.info(f"[BACKGROUND] RAG 인덱싱 완료: branch={metadata.get('branch_id', 'unknown')[:30]}")
    except Exception as e:
        logger.error(f"[BACKGROUND] RAG 인덱싱 실패: {e}")


def get_rag_engine() -> RAGEngine:
    """
    RAGEngine 인스턴스 반환

    매번 새로운 인스턴스를 생성하여 ChromaDB 세션 안정성 보장
    (캐싱하지 않음 - collection UUID 불일치 방지)
    """
    return RAGEngine()

logger.info("=" * 60)
logger.info("Cortex MCP 서버 시작됨")
logger.info(f"메모리 디렉토리: {config.memory_dir}")
logger.info(f"로그 디렉토리: {config.logs_dir}")
logger.info("=" * 60)


# ============================================================
# 라이센스 검증 (런타임 보호)
# ============================================================

# 라이센스 검증 캐시 (5분 유효)
_license_check_cache: Optional[dict] = None
_license_check_time: Optional[datetime] = None
LICENSE_CACHE_MINUTES = 5


def _trigger_cache_invalidation(tool_name: str, arguments: dict, result: dict) -> None:
    """
    Phase 3: 도구 실행 후 캐시 무효화 트리거

    캐시 무효화 규칙:
    - Context 변경 도구 (update_memory, create_branch, resolve_context): 해당 context 무효화
    - 대규모 변경 도구 (scan_project_deep, rescan_project, initialize_context): 전체 클리어
    - 검색 도구 (search_context, suggest_contexts): 무효화 불필요 (읽기 전용)

    Args:
        tool_name: 실행된 도구 이름
        arguments: 도구 인자
        result: 도구 실행 결과
    """
    if not result.get("success"):
        return  # 실패한 도구는 캐시 무효화 안 함

    try:
        from core.smart_cache import get_context_cache
        from core.embedding_cache import get_embedding_cache

        smart_cache = get_context_cache()
        embedding_cache = get_embedding_cache()

        # 규칙 1: Context 변경 도구 → 해당 context 무효화
        if tool_name in ["update_memory", "create_branch", "resolve_context"]:
            context_id = result.get("context_id") or result.get("branch_id")
            if context_id:
                smart_cache.invalidate(context_id)
                logger.info(f"[CACHE_INVALIDATION] {tool_name}: {context_id}")

        # 규칙 2: 대규모 변경 → 전체 캐시 클리어
        elif tool_name in ["scan_project_deep", "rescan_project", "initialize_context"]:
            smart_cache.clear()
            embedding_cache.clear()
            logger.info(f"[CACHE_INVALIDATION] {tool_name}: Full clear")

    except Exception as e:
        logger.error(f"[CACHE_INVALIDATION] Failed: {e}")
        # Graceful degradation: 캐시 무효화 실패해도 도구는 정상 작동


def _verify_license_runtime() -> Optional[dict]:
    """
    런타임 라이센스 검증 (모든 MCP 도구 호출 시 실행)

    캐시 메커니즘으로 성능 유지 (5분 캐시)
    라이센스가 없거나 만료된 경우 에러 반환

    Returns:
        None: 라이센스 유효
        dict: 에러 정보 (라이센스 무효)
    """
    global _license_check_cache, _license_check_time

    # 캐시 확인
    now = datetime.now(timezone.utc)
    if _license_check_cache and _license_check_time:
        elapsed = (now - _license_check_time).total_seconds()
        if elapsed < LICENSE_CACHE_MINUTES * 60:
            # 캐시 유효 - 저장된 결과 반환
            return _license_check_cache

    # 라이센스 검증
    manager = get_license_manager()
    result = manager.validate_local_license()

    # 검증 실패 시 에러 정보 생성
    if not result.get("success"):
        error_info = {
            "success": False,
            "error": "License required. Cortex MCP cannot run without a valid license.",
            "license_status": result.get("status"),
            "message": "Activate with: python scripts/license_cli.py activate --key YOUR-LICENSE-KEY",
            "help_url": "https://github.com/syab726/cortex#license-activation",
        }

        # 캐시 저장
        _license_check_cache = error_info
        _license_check_time = now

        return error_info

    # 검증 성공 - 캐시에 None 저장 (라이센스 유효)
    _license_check_cache = None
    _license_check_time = now

    return None


# 스캔 모드별 파일 패턴
SCAN_PATTERNS = {
    "FULL": [
        "**/*.py",
        "**/*.js",
        "**/*.ts",
        "**/*.tsx",
        "**/*.jsx",
        "**/*.java",
        "**/*.go",
        "**/*.rs",
        "**/*.cpp",
        "**/*.c",
        "**/*.h",
        "**/*.hpp",
        "**/*.cs",
        "**/*.rb",
        "**/*.php",
        "**/*.swift",
        "**/*.kt",
        "**/*.scala",
        "**/*.vue",
        "**/*.svelte",
        "**/README*",
        "**/CHANGELOG*",
        "**/*.md",
        "**/*.json",
        "**/*.yaml",
        "**/*.yml",
        "**/*.toml",
        "**/*.ini",
        "**/*.cfg",
        "**/Dockerfile*",
        "**/*.sql",
    ],
    "LIGHT": [
        "**/README*",
        "**/CHANGELOG*",
        "**/main.*",
        "**/index.*",
        "**/app.*",
        "**/server.*",
        "**/package.json",
        "**/pyproject.toml",
        "**/setup.py",
        "**/requirements.txt",
        "**/Cargo.toml",
        "**/go.mod",
        "**/*.config.*",
        "**/config.*",
        "**/.env.example",
    ],
}

# 무시할 디렉토리
IGNORE_DIRS = [
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "vendor",
    ".idea",
    ".vscode",
    ".cache",
    "coverage",
    ".pytest_cache",
]


async def _handle_initialize_context(
    project_id: str, project_path: str, scan_mode: str, file_patterns: list = None
) -> dict:
    """
    프로젝트 초기 맥락 스캔 처리 - Initial Scanner 사용

    Args:
        project_id: 프로젝트 식별자 (선택, 없으면 .cortexrc에서 자동 로드)
        project_path: 프로젝트 루트 경로
        scan_mode: FULL / LIGHT / NONE
        file_patterns: 커스텀 파일 패턴 (선택, 현재 미사용)

    Returns:
        스캔 결과
    """
    from datetime import datetime, timezone

    # .cortexrc 기반 프로젝트 ID 자동 로드 (PC 마이그레이션 지원)
    if not project_id or project_id == "auto":
        proj_config = ProjectConfig(project_path)
        project_id = proj_config.get_project_id()
        logger.info(f"Auto-loaded project_id from .cortexrc: {project_id}")

    # 입력 검증은 call_tool에서 이미 수행됨 (중복 제거)

    # RAGEngine 재초기화 (ChromaDB 컬렉션 참조 리셋)
    global rag_engine
    rag_engine = RAGEngine()

    # Initial Scanner 사용 가능 여부 확인
    if INITIAL_SCANNER_AVAILABLE and scanner_scan_project is not None:
        # ScanMode enum으로 변환
        mode_map = {"FULL": ScannerMode.FULL, "LIGHT": ScannerMode.LIGHT, "NONE": ScannerMode.NONE}
        mode = mode_map.get(scan_mode, ScannerMode.LIGHT)

        # Initial Scanner로 프로젝트 스캔 (file_patterns는 scan_project에서 지원하지 않음)
        scan_result = scanner_scan_project(
            project_id=project_id, project_path=project_path, mode=mode
        )

        # 스캔 성공 시 브랜치 생성
        if scan_result.success:
            # 프로젝트 루트 브랜치 생성
            branch_result = memory_manager.create_branch(
                project_id=project_id, branch_topic="project_root"
            )
            branch_id = branch_result.get("branch_id")

            # 토큰 추정 계산 (파일당 평균 500 토큰으로 추정)
            tokens_estimated = scan_result.files_scanned * 500

            # 프로젝트 요약 저장
            summary = f"""프로젝트 초기화 완료 (Initial Scanner 사용)
- 스캔 모드: {scan_mode}
- 스캔 파일 수: {scan_result.files_scanned}
- 예상 토큰: {tokens_estimated:,}
- 생성된 노드: {scan_result.nodes_created}
- 생성된 엣지: {scan_result.edges_created}
- 스캔 시간: {scan_result.duration_seconds:.2f}초
- 완료 시각: {datetime.now(timezone.utc).isoformat()}
"""
            memory_manager.update_summary(
                project_id=project_id, branch_id=branch_id, new_summary=summary
            )

            # warnings 리스트 처리
            warning_msg = None
            if scan_result.warnings:
                warning_msg = "; ".join(scan_result.warnings)

            return {
                "success": True,
                "scan_mode": scan_mode,
                "files_scanned": scan_result.files_scanned,
                "tokens_estimated": tokens_estimated,
                "nodes_created": scan_result.nodes_created,
                "edges_created": scan_result.edges_created,
                "languages": scan_result.languages,
                "branch_id": branch_id,
                "warning": warning_msg,
                "duration_seconds": scan_result.duration_seconds,
                "message": f"{scan_result.files_scanned}개 파일 스캔 완료. 이후 변경분만 추적됩니다.",
            }
        else:
            # 에러 메시지 처리
            error_msg = "스캔 실패"
            if scan_result.errors:
                error_msg = "; ".join(scan_result.errors)
            return {"success": False, "error": error_msg}

    # Initial Scanner 사용 불가 시 기존 방식으로 폴백
    import os

    # NONE 모드: 스캔 건너뛰기
    if scan_mode == "NONE":
        # 빈 프로젝트 브랜치만 생성
        result = memory_manager.create_branch(project_id=project_id, branch_topic="project_root")
        return {
            "success": True,
            "scan_mode": "NONE",
            "message": "스캔을 건너뛰었습니다. 빈 맥락으로 시작합니다.",
            "branch_id": result.get("branch_id"),
            "files_scanned": 0,
            "tokens_estimated": 0,
        }

    # 패턴 결정
    if file_patterns:
        patterns = file_patterns
    else:
        patterns = SCAN_PATTERNS.get(scan_mode, SCAN_PATTERNS["LIGHT"])

    # 파일 수집
    project_root = Path(project_path)
    if not project_root.exists():
        return {"success": False, "error": f"프로젝트 경로가 존재하지 않습니다: {project_path}"}

    scanned_files = []
    total_chars = 0

    for root, dirs, files in os.walk(project_root):
        # 무시할 디렉토리 제외
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        rel_root = Path(root).relative_to(project_root)

        for file in files:
            file_path = rel_root / file
            full_path = project_root / file_path

            # 패턴 매칭 (Path.match()는 ** 지원)
            matched = any(
                file_path.match(pattern) or full_path.match(pattern) for pattern in patterns
            )

            if matched:
                try:
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    file_size = len(content)

                    # LIGHT 모드는 파일당 최대 5KB
                    if scan_mode == "LIGHT" and file_size > 5000:
                        content = content[:5000] + "\n... (truncated)"

                    # RAG 인덱싱
                    get_rag_engine().index_content(
                        content=f"File: {file_path}\n\n{content}",
                        metadata={
                            "project_id": project_id,
                            "file_path": str(file_path),
                            "type": "source_file",
                            "scan_mode": scan_mode,
                        },
                    )

                    scanned_files.append(str(file_path))
                    total_chars += len(content)

                except Exception as e:
                    # 바이너리 파일 등 읽기 실패 무시
                    pass

    # 토큰 추정 (대략 4자 = 1토큰)
    estimated_tokens = total_chars // 4

    # 프로젝트 루트 브랜치 생성
    branch_result = memory_manager.create_branch(project_id=project_id, branch_topic="project_root")

    # 프로젝트 요약 저장
    summary = f"""프로젝트 초기화 완료
- 스캔 모드: {scan_mode}
- 스캔 파일 수: {len(scanned_files)}
- 예상 토큰: {estimated_tokens:,}
- 스캔 시간: {datetime.now(timezone.utc).isoformat()}

주요 파일:
{chr(10).join('- ' + f for f in scanned_files[:20])}
{'... 외 ' + str(len(scanned_files) - 20) + '개' if len(scanned_files) > 20 else ''}
"""

    memory_manager.update_summary(
        project_id=project_id, branch_id=branch_result.get("branch_id"), new_summary=summary
    )

    return {
        "success": True,
        "scan_mode": scan_mode,
        "files_scanned": len(scanned_files),
        "tokens_estimated": estimated_tokens,
        "branch_id": branch_result.get("branch_id"),
        "warning": "FULL 모드: 토큰 소모가 높을 수 있습니다." if scan_mode == "FULL" else None,
        "message": f"{len(scanned_files)}개 파일 스캔 완료. 이후 변경분만 추적됩니다.",
    }


def register_tools(server: Server):
    """MCP 서버에 Cortex 도구 등록"""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """사용 가능한 도구 목록 반환"""
        tools = [
            Tool(
                name="initialize_context",
                description="""[MANDATORY - 새 프로젝트 첫 연결 시 호출 필수]
                프로젝트 초기 맥락 스캔.

                호출 시점:
                - 새 프로젝트에 처음 연결될 때 반드시 호출
                - Cortex 맥락이 없는 프로젝트 발견 시 호출
                - 사용자에게 스캔 모드(FULL/LIGHT/NONE) 선택 안내 후 호출

                3가지 모드:
                - FULL: 전체 심층 분석 (토큰 소모 높음 - 경고 표시)
                - LIGHT: 핵심 파일만 스캔 (README, 진입점, 설정)
                - NONE: 스캔 건너뛰기

                초기화 후에는 변경분만 증분 업데이트됩니다.
                초기화하지 않으면 맥락 관리가 불가능합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 식별자"},
                        "project_path": {"type": "string", "description": "프로젝트 루트 경로"},
                        "scan_mode": {
                            "type": "string",
                            "enum": ["FULL", "LIGHT", "NONE"],
                            "description": "스캔 모드 (FULL/LIGHT/NONE)",
                        },
                        "file_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "스캔할 파일 패턴 (선택, 기본: 언어별 소스 파일)",
                        },
                    },
                    "required": ["project_id", "project_path", "scan_mode"],
                },
            ),
            Tool(
                name="create_branch",
                description="""[MANDATORY - 주제 전환 시 호출 필수]
                Context Tree(브랜치) 생성.

                호출 시점:
                - 새로운 프로젝트/작업 시작 시 반드시 호출
                - 대화 주제가 전환되었을 때 반드시 호출
                - 사용자가 "브랜치 생성", "새 맥락" 요청 시 즉시 호출
                - 이전 대화와 무관한 주제로 전환 감지 시 호출

                대화 주제가 전환되었을 때 새로운 브랜치를 생성하여 맥락을 분리합니다.
                AI 감지 또는 유저 수동 요청으로 호출됩니다. (Zero-Effort)
                브랜치를 분리하지 않으면 맥락이 혼합되어 정확도가 저하됩니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 식별자"},
                        "branch_topic": {"type": "string", "description": "브랜치 주제/이름"},
                        "parent_branch": {"type": "string", "description": "부모 브랜치 ID (선택)"},
                    },
                    "required": ["project_id", "branch_topic"],
                },
            ),
            Tool(
                name="search_context",
                description="""로컬 Vector RAG 검색.
                과거의 깊은 맥락을 의미 기반으로 정확히 검색합니다.
                AI의 회상률을 극대화합니다. (Zero-Loss)""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "검색 쿼리"},
                        "project_id": {"type": "string", "description": "프로젝트 필터 (선택)"},
                        "branch_id": {"type": "string", "description": "브랜치 필터 (선택)"},
                        "top_k": {"type": "integer", "description": "반환할 결과 수 (기본: 5)"},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="update_memory",
                description="""[MANDATORY - 모든 응답 후 호출 필수]
                대화 내용을 메모리에 기록합니다.

                호출 시점:
                - 응답 완료 후 반드시 호출
                - 파일 수정(Edit/Write) 후 반드시 호출
                - 중요한 결정/변경사항 발생 시 즉시 호출

                호출하지 않으면 맥락이 손실됩니다.
                대화 기록을 .md 파일에 저장하고, 파일 크기 초과 시
                핵심 요약본을 자동 갱신하여 토큰 비용을 절감합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "branch_id": {"type": "string", "description": "브랜치 ID"},
                        "content": {"type": "string", "description": "저장할 대화 내용"},
                        "role": {
                            "type": "string",
                            "enum": ["user", "assistant"],
                            "description": "역할 (user/assistant)",
                        },
                        "verified": {
                            "type": "boolean",
                            "description": "AI 자기검증 완료 여부 (True면 검증 건너뛰기, Phase 9.2)",
                            "default": False
                        },
                    },
                    "required": ["project_id", "branch_id", "content"],
                },
            ),
            Tool(
                name="get_active_summary",
                description="""[MANDATORY - 세션 시작 시 호출 필수]
                현재 브랜치의 최신 요약 정보를 반환합니다.

                호출 시점:
                - 세션 시작 시 반드시 호출
                - 컨텍스트 압축 후 반드시 호출
                - 브랜치 전환 후 반드시 호출
                - 답변 전 맥락 확인이 필요할 때 호출

                System Prompt에 주입하여 AI가 맥락을 잊지 않도록 합니다.
                호출하지 않으면 이전 대화 맥락을 잃어버릴 수 있습니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "branch_id": {
                            "type": "string",
                            "description": "브랜치 ID (없으면 최신 활성 브랜치)",
                        },
                    },
                    "required": ["project_id"],
                },
            ),
            Tool(
                name="sync_to_cloud",
                description="""로컬 메모리를 Google Drive에 암호화 후 업로드.
                라이센스키 기반 E2E 암호화로 보안을 유지하며,
                환경 변경 시에도 맥락을 복구할 수 있습니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "license_key": {"type": "string", "description": "암호화용 라이센스 키"},
                        "project_id": {
                            "type": "string",
                            "description": "특정 프로젝트만 동기화 (선택)",
                        },
                    },
                    "required": ["license_key"],
                },
            ),
            Tool(
                name="sync_from_cloud",
                description="""Google Drive에서 암호화된 메모리를 복원.
                동일한 라이센스키로 복호화하여 맥락을 완벽히 복구합니다.
                새 환경에서도 100% 맥락 유지가 가능합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "license_key": {"type": "string", "description": "복호화용 라이센스 키"},
                        "project_id": {
                            "type": "string",
                            "description": "특정 프로젝트만 복원 (선택)",
                        },
                    },
                    "required": ["license_key"],
                },
            ),
            # ============ Smart Context Tools (v2.0) ============
            Tool(
                name="load_context",
                description="""특정 맥락 활성화 (압축 해제).
                Smart Context 시스템의 핵심 도구입니다.
                - 기본: metadata + summary만 로드 (토큰 효율적)
                - force_full_load=true: full_content까지 로드
                - 30분 미사용 시 자동 압축됩니다.
                - 최대 3개 브랜치 동시 활성화 가능.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "branch_id": {"type": "string", "description": "브랜치 ID"},
                        "context_id": {
                            "type": "string",
                            "description": "특정 Context ID (선택, 없으면 브랜치 summary)",
                        },
                        "force_full_load": {
                            "type": "boolean",
                            "description": "full_content까지 로드 (기본: false)",
                        },
                    },
                    "required": ["project_id", "branch_id"],
                },
            ),
            Tool(
                name="get_loaded_contexts",
                description="""현재 로드된 모든 Context 정보 반환.
                Smart Context 시스템 상태 모니터링용.
                - 활성 브랜치 목록
                - 각 브랜치의 로드된 Context
                - 마지막 접근 시간""",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="compress_context",
                description="""특정 Context 수동 압축.
                full_content를 언로드하고 summary만 유지합니다.
                토큰 사용량을 줄이기 위해 사용합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "branch_id": {"type": "string", "description": "브랜치 ID"},
                        "context_id": {"type": "string", "description": "Context ID"},
                    },
                    "required": ["project_id", "branch_id", "context_id"],
                },
            ),
            Tool(
                name="resolve_context",
                description="""[Phase C] SHALLOW 노드를 DEEP으로 수동 해석.

                호출 시점:
                - search_context 결과가 없을 때 수동으로 호출
                - 특정 파일의 심층 분석이 필요할 때
                - Phase C 자동 트리거 외에 명시적 제어가 필요할 때

                기능:
                - SHALLOW 노드 → DEEP 노드 전환
                - 파일 내용 의미 분석 + 요약 생성
                - RAG 인덱싱 (검색 가능하도록)

                Context Graph의 특정 노드를 선택적으로 심층 분석하여
                RAG 검색 정확도를 향상시킵니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "context_id": {
                            "type": "string",
                            "description": "Context ID (file:// 형식) - file_path와 둘 중 하나 필수",
                        },
                        "file_path": {
                            "type": "string",
                            "description": "파일 경로 (context_id 대신 사용 가능)",
                        },
                    },
                    "required": ["project_id"],
                },
            ),
            # ============ Reference History Tools (v2.0) ============
            Tool(
                name="suggest_contexts",
                description="""[RECOMMENDED - 작업 시작 전 호출 권장]
                Reference History 기반 맥락 추천.

                호출 시점:
                - 새로운 작업 시작 전 호출 권장
                - 검색/조회 작업 전 호출 권장
                - 파일 수정 전 관련 맥락 확인 시 호출

                3-Tier 추천 시스템:
                - Tier 1: Reference History 기반 (정확도 95%)
                - Tier 2: Co-occurrence 분석 (정확도 70%)
                - Tier 3: 사용자 선택 (정확도 100%)

                이전에 유사한 작업에서 함께 사용된 맥락을 추천합니다.
                추천된 맥락을 활용하면 작업 정확도가 향상됩니다.

                IMPORTANT: 추천 받은 후 반드시 accept_suggestions 또는 reject_suggestions 호출 필요.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "검색/작업 쿼리"},
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "branch_id": {"type": "string", "description": "브랜치 ID (선택)"},
                        "top_k": {"type": "integer", "description": "반환할 최대 개수 (기본: 5)"},
                    },
                    "required": ["query", "project_id"],
                },
            ),
            Tool(
                name="accept_suggestions",
                description="""[MANDATORY - suggest_contexts 후 호출 필수]
                추천 수락 기록 (출처에 대한 책임).

                호출 시점:
                - suggest_contexts 호출 후 추천을 사용하기로 결정한 경우 즉시 호출
                - 추천된 맥락을 실제로 사용한 경우 반드시 호출

                호출하지 않으면:
                - Reference History 추천 정확도 저하
                - 출처 책임 추적 불가

                이 도구는 '출처에 대한 책임' 강제 메커니즘입니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "session_id": {
                            "type": "string",
                            "description": "suggest_contexts에서 반환한 session_id",
                        },
                        "contexts_used": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "실제 사용된 맥락 ID 목록",
                        },
                    },
                    "required": ["project_id", "session_id", "contexts_used"],
                },
            ),
            Tool(
                name="reject_suggestions",
                description="""[MANDATORY - suggest_contexts 후 호출 필수]
                추천 거부 기록 (출처에 대한 책임).

                호출 시점:
                - suggest_contexts 호출 후 추천을 사용하지 않기로 결정한 경우 즉시 호출
                - 추천된 맥락이 적절하지 않은 경우 반드시 호출

                호출하지 않으면:
                - Reference History 추천 정확도 저하
                - 출처 책임 추적 불가

                거부 이유(reason) 입력은 필수입니다.
                이 도구는 '출처에 대한 책임' 강제 메커니즘입니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "session_id": {
                            "type": "string",
                            "description": "suggest_contexts에서 반환한 session_id",
                        },
                        "reason": {"type": "string", "description": "거부 이유 (필수)"},
                    },
                    "required": ["project_id", "session_id", "reason"],
                },
            ),
            Tool(
                name="record_reference",
                description="""[RECOMMENDED - 작업 완료 후 호출 권장]
                맥락 참조 이력 기록.

                호출 시점:
                - 중요한 작업 완료 후 호출 권장
                - 여러 맥락을 함께 사용한 경우 호출
                - update_memory 호출 후 함께 호출 권장

                작업에서 사용된 맥락 조합을 기록하여
                향후 유사한 작업에서 추천에 활용합니다.
                기록하지 않으면 Reference History 추천 정확도가 낮아집니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "task_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "작업 키워드 목록",
                        },
                        "contexts_used": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "사용된 맥락 ID 목록",
                        },
                        "branch_id": {"type": "string", "description": "브랜치 ID"},
                        "query": {"type": "string", "description": "원본 쿼리 (선택)"},
                    },
                    "required": ["project_id", "task_keywords", "contexts_used", "branch_id"],
                },
            ),
            Tool(
                name="update_reference_feedback",
                description="""Reference History 피드백 업데이트.
                추천 결과에 대한 사용자 피드백을 기록하여
                추천 정확도를 향상시킵니다.
                - accepted: 추천 수락
                - rejected: 추천 거부
                - modified: 수정 후 사용""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "feedback": {
                            "type": "string",
                            "enum": ["accepted", "rejected", "modified"],
                            "description": "피드백 유형",
                        },
                        "entry_timestamp": {
                            "type": "string",
                            "description": "특정 엔트리 타임스탬프 (선택, 없으면 최신)",
                        },
                        "contexts_actually_used": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "실제 사용된 맥락 (modified인 경우)",
                        },
                    },
                    "required": ["project_id", "feedback"],
                },
            ),
            Tool(
                name="get_reference_statistics",
                description="""Reference History 통계 반환.
                추천 수락률, 가장 많이 사용된 맥락 등
                통계 정보를 제공합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {"project_id": {"type": "string", "description": "프로젝트 ID"}},
                    "required": ["project_id"],
                },
            ),
            # ============ Hierarchy Tools (v2.0) ============
            Tool(
                name="create_node",
                description="""Node 그룹 생성.
                브랜치 내에서 관련 Context들을 그룹화합니다.
                30개 이상의 Context가 있을 때 사용을 권장합니다.
                계층 구조: Project → Branch → Node → Context""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "branch_id": {"type": "string", "description": "브랜치 ID"},
                        "node_name": {"type": "string", "description": "Node 이름"},
                        "context_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "이 Node에 포함할 Context ID 목록 (선택)",
                        },
                    },
                    "required": ["project_id", "branch_id", "node_name"],
                },
            ),
            Tool(
                name="list_nodes",
                description="""브랜치의 모든 Node 목록 반환.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "branch_id": {"type": "string", "description": "브랜치 ID"},
                    },
                    "required": ["project_id", "branch_id"],
                },
            ),
            Tool(
                name="suggest_node_grouping",
                description="""Node 그룹핑 필요 여부 확인 및 제안.
                Context가 30개 이상일 때 그룹핑을 제안합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "branch_id": {"type": "string", "description": "브랜치 ID"},
                    },
                    "required": ["project_id", "branch_id"],
                },
            ),
            Tool(
                name="get_hierarchy",
                description="""프로젝트의 전체 계층 구조 반환.
                Project → Branch → Node → Context 구조를 보여줍니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {"project_id": {"type": "string", "description": "프로젝트 ID"}},
                    "required": ["project_id"],
                },
            ),
            # ============ Git Integration Tools (v2.0) ============
            Tool(
                name="link_git_branch",
                description="""Git 브랜치와 Cortex 브랜치 연동.
                Git checkout 시 자동으로 Cortex 맥락이 전환됩니다.
                - auto_create=true: Cortex 브랜치 자동 생성
                - 팀 협업 시 동일한 맥락 공유 가능""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "repo_path": {"type": "string", "description": "Git 저장소 경로"},
                        "git_branch": {
                            "type": "string",
                            "description": "Git 브랜치 이름 (없으면 현재 브랜치)",
                        },
                        "cortex_branch_id": {
                            "type": "string",
                            "description": "연동할 Cortex 브랜치 ID (없으면 자동 생성)",
                        },
                        "auto_create": {
                            "type": "boolean",
                            "description": "Cortex 브랜치 자동 생성 (기본: true)",
                        },
                    },
                    "required": ["project_id", "repo_path"],
                },
            ),
            Tool(
                name="get_git_status",
                description="""Git 저장소 상태 및 Cortex 연동 정보 반환.
                현재 브랜치, 커밋 해시, 연동된 Cortex 브랜치 등을 확인합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "repo_path": {"type": "string", "description": "Git 저장소 경로"},
                    },
                    "required": ["project_id", "repo_path"],
                },
            ),
            Tool(
                name="check_git_branch_change",
                description="""Git 브랜치 변경 감지 및 자동 Cortex 전환.
                Git checkout 후 호출하면 자동으로 맥락이 전환됩니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "repo_path": {"type": "string", "description": "Git 저장소 경로"},
                        "auto_create": {
                            "type": "boolean",
                            "description": "새 브랜치일 경우 Cortex 브랜치 자동 생성 (기본: true)",
                        },
                    },
                    "required": ["project_id", "repo_path"],
                },
            ),
            Tool(
                name="list_git_links",
                description="""Git-Cortex 브랜치 연동 목록 반환.
                현재 프로젝트에서 연동된 모든 브랜치를 보여줍니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "repo_path": {
                            "type": "string",
                            "description": "Git 저장소 경로 (필터링용, 선택)",
                        },
                    },
                    "required": ["project_id"],
                },
            ),
            Tool(
                name="unlink_git_branch",
                description="""Git-Cortex 브랜치 연동 해제.
                특정 Git 브랜치의 Cortex 연동을 제거합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "repo_path": {"type": "string", "description": "Git 저장소 경로"},
                        "git_branch": {
                            "type": "string",
                            "description": "연동 해제할 Git 브랜치 이름",
                        },
                    },
                    "required": ["project_id", "repo_path", "git_branch"],
                },
            ),
            # ============ Dashboard Tools (Phase 6) ============
            Tool(
                name="get_dashboard_url",
                description="""Audit Dashboard URL 반환.
                localhost:8080에서 실행되는 대시보드의 URL을 반환합니다.
                서버가 실행 중이 아니면 자동으로 시작합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_if_not_running": {
                            "type": "boolean",
                            "description": "서버가 실행 중이 아니면 자동 시작 (기본: true)",
                        },
                        "open_browser": {
                            "type": "boolean",
                            "description": "브라우저 자동 열기 (기본: false)",
                        },
                    },
                    "required": [],
                },
            ),
            # ============ Backup Tools (Phase 7) ============
            Tool(
                name="create_snapshot",
                description="""프로젝트 스냅샷 생성.
                현재 프로젝트 상태를 백업합니다.
                - manual: 수동 스냅샷
                - auto: 자동 스냅샷
                - git_commit: Git 커밋 시 스냅샷""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "description": {"type": "string", "description": "스냅샷 설명"},
                        "snapshot_type": {
                            "type": "string",
                            "enum": ["manual", "auto", "git_commit"],
                            "description": "스냅샷 유형 (기본: manual)",
                        },
                        "branch_id": {
                            "type": "string",
                            "description": "특정 브랜치만 스냅샷 (선택)",
                        },
                    },
                    "required": ["project_id"],
                },
            ),
            Tool(
                name="restore_snapshot",
                description="""스냅샷에서 복원.
                이전 스냅샷으로 프로젝트를 복원합니다.
                복원 전 자동으로 현재 상태를 백업합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "snapshot_id": {"type": "string", "description": "복원할 스냅샷 ID"},
                        "overwrite": {
                            "type": "boolean",
                            "description": "자동 백업 없이 덮어쓰기 (기본: false)",
                        },
                    },
                    "required": ["project_id", "snapshot_id"],
                },
            ),
            Tool(
                name="list_snapshots",
                description="""스냅샷 목록 조회.
                프로젝트의 모든 스냅샷 목록을 반환합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "snapshot_type": {
                            "type": "string",
                            "description": "특정 타입만 필터링 (선택)",
                        },
                        "limit": {"type": "integer", "description": "최대 결과 수 (기본: 20)"},
                    },
                    "required": ["project_id"],
                },
            ),
            Tool(
                name="get_backup_history",
                description="""백업 히스토리 조회.
                스냅샷 생성/복원 이력을 타임라인으로 반환합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "limit": {"type": "integer", "description": "최대 결과 수 (기본: 50)"},
                    },
                    "required": ["project_id"],
                },
            ),
            # ============ Automation Tools (Phase 8) ============
            Tool(
                name="get_automation_status",
                description="""자동화 상태 조회.
                Plan A/B 모드, 거부율, 성공률 등을 반환합니다.
                - Plan A (auto): 자동 처리
                - Plan B (semi_auto): 확인 절차 포함""",
                inputSchema={
                    "type": "object",
                    "properties": {"project_id": {"type": "string", "description": "프로젝트 ID"}},
                    "required": ["project_id"],
                },
            ),
            Tool(
                name="record_automation_feedback",
                description="""자동화 피드백 기록.
                사용자의 수락/거부 피드백을 기록합니다.
                거부율 30% 이상이면 Plan B로 전환됩니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "action_type": {
                            "type": "string",
                            "enum": [
                                "branch_create",
                                "context_load",
                                "context_suggest",
                                "memory_update",
                                "auto_compress",
                                "auto_summary",
                            ],
                            "description": "작업 유형",
                        },
                        "feedback": {
                            "type": "string",
                            "enum": ["accepted", "rejected", "modified", "ignored"],
                            "description": "피드백 유형",
                        },
                        "action_id": {"type": "string", "description": "작업 ID (선택)"},
                    },
                    "required": ["project_id", "action_type", "feedback"],
                },
            ),
            Tool(
                name="should_confirm_action",
                description="""작업 확인 필요 여부 판단.
                Plan A/B 모드에 따라 사용자 확인이 필요한지 반환합니다.
                - Plan A: 확인 불필요
                - Plan B: 확인 필요""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "action_type": {"type": "string", "description": "작업 유형"},
                    },
                    "required": ["project_id", "action_type"],
                },
            ),
            Tool(
                name="set_automation_mode",
                description="""자동화 모드 수동 설정.
                Plan A/B를 수동으로 전환합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "mode": {
                            "type": "string",
                            "enum": ["auto", "semi_auto"],
                            "description": "설정할 모드",
                        },
                        "disable_auto_switch": {
                            "type": "boolean",
                            "description": "자동 전환 비활성화 (기본: false)",
                        },
                    },
                    "required": ["project_id", "mode"],
                },
            ),
            # ============ Semantic Web Tools (Enterprise Only) ============
            Tool(
                name="add_semantic_relation",
                description="""[Enterprise Only] 시맨틱 웹에 관계 추가.
                맥락 간의 관계를 OWL/RDF 스타일로 정의합니다.
                - DEPENDS_ON: 의존 관계
                - REFERENCES: 참조 관계
                - PART_OF: 포함 관계
                - RELATED_TO: 연관 관계
                - CONFLICTS_WITH: 충돌 관계
                - PRECEDES: 선후 관계
                - IMPLEMENTS: 구현 관계""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "source": {"type": "string", "description": "소스 Context ID"},
                        "target": {"type": "string", "description": "타겟 Context ID"},
                        "relation_type": {
                            "type": "string",
                            "enum": [
                                "DEPENDS_ON",
                                "REFERENCES",
                                "PART_OF",
                                "RELATED_TO",
                                "CONFLICTS_WITH",
                                "PRECEDES",
                                "IMPLEMENTS",
                            ],
                            "description": "관계 유형",
                        },
                        "confidence": {
                            "type": "number",
                            "description": "신뢰도 (0.0-1.0, 기본: 1.0)",
                        },
                    },
                    "required": ["project_id", "source", "target", "relation_type"],
                },
            ),
            Tool(
                name="infer_relations",
                description="""[Enterprise Only] 전이적 관계 추론.
                A->B, B->C 관계가 있으면 A->C 관계를 추론합니다.
                N-hop 탐색으로 간접 관계를 발견합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "context_id": {"type": "string", "description": "시작점 Context ID"},
                        "relation_type": {
                            "type": "string",
                            "enum": [
                                "DEPENDS_ON",
                                "REFERENCES",
                                "PART_OF",
                                "RELATED_TO",
                                "CONFLICTS_WITH",
                                "PRECEDES",
                                "IMPLEMENTS",
                            ],
                            "description": "추론할 관계 유형",
                        },
                        "max_depth": {"type": "integer", "description": "최대 탐색 깊이 (기본: 5)"},
                    },
                    "required": ["project_id", "context_id", "relation_type"],
                },
            ),
            Tool(
                name="detect_conflicts",
                description="""[Enterprise Only] 충돌 감지.
                정책 충돌, 버전 충돌 등을 자동으로 감지합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "context_id": {
                            "type": "string",
                            "description": "특정 Context만 검사 (선택)",
                        },
                    },
                    "required": ["project_id"],
                },
            ),
            Tool(
                name="suggest_related_contexts",
                description="""[Enterprise Only] 시맨틱 웹 기반 관련 맥락 추천.
                N-hop 관계 탐색으로 관련 맥락을 추천합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "context_id": {"type": "string", "description": "시작점 Context ID"},
                        "max_depth": {"type": "integer", "description": "최대 탐색 깊이 (기본: 3)"},
                        "min_confidence": {
                            "type": "number",
                            "description": "최소 신뢰도 (기본: 0.3)",
                        },
                    },
                    "required": ["project_id", "context_id"],
                },
            ),
            Tool(
                name="get_semantic_web_stats",
                description="""[Enterprise Only] 시맨틱 웹 통계 반환.
                관계 수, 노드 수, 관계 유형별 분포 등을 반환합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {"project_id": {"type": "string", "description": "프로젝트 ID"}},
                    "required": ["project_id"],
                },
            ),
            # ============ Boundary Protection Tools ============
            Tool(
                name="set_boundary",
                description="""작업 경계 수동 설정.
                AI가 수정할 수 있는 파일/디렉토리 범위를 명시적으로 제한합니다.
                Zero-Trust 보안의 핵심 기능으로, 범위 외 파일 수정 시도를 차단합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "project_path": {
                            "type": "string",
                            "description": "프로젝트 루트 경로 (선택)",
                        },
                        "task": {"type": "string", "description": "현재 작업 설명"},
                        "allowed_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "허용된 파일 목록",
                        },
                        "allowed_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "허용된 파일 패턴 (예: 'src/*.py')",
                        },
                        "allowed_actions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "허용된 작업 유형 (READ, WRITE, CREATE, DELETE, MODIFY)",
                        },
                        "strict_mode": {
                            "type": "boolean",
                            "description": "엄격 모드 활성화 (기본: false)",
                        },
                    },
                    "required": ["project_id", "task"],
                },
            ),
            Tool(
                name="infer_boundary",
                description="""작업 경계 자동 추론.
                AI가 작업 설명과 맥락을 분석하여 적절한 파일 범위를 자동으로 추론합니다.
                최근 작업 파일과 맥락을 기반으로 지능적 범위 설정.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "project_path": {
                            "type": "string",
                            "description": "프로젝트 루트 경로 (선택)",
                        },
                        "task": {"type": "string", "description": "현재 작업 설명"},
                        "context": {"type": "string", "description": "추가 맥락 정보 (선택)"},
                        "recent_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "최근 작업한 파일 목록 (선택)",
                        },
                    },
                    "required": ["project_id", "task"],
                },
            ),
            Tool(
                name="validate_boundary_action",
                description="""파일 작업 유효성 검증.
                특정 파일에 대한 작업이 현재 경계 내에서 허용되는지 검증합니다.
                위반 시 상세 사유와 함께 차단 여부를 반환합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "project_path": {
                            "type": "string",
                            "description": "프로젝트 루트 경로 (선택)",
                        },
                        "file_path": {"type": "string", "description": "검증할 파일 경로"},
                        "action": {
                            "type": "string",
                            "description": "작업 유형 (READ, WRITE, CREATE, DELETE, MODIFY)",
                        },
                    },
                    "required": ["project_id", "file_path", "action"],
                },
            ),
            Tool(
                name="get_boundary_protocol",
                description="""System Prompt용 경계 프로토콜 생성.
                현재 설정된 경계를 AI가 준수해야 할 프로토콜 형식으로 반환합니다.
                System Prompt에 삽입하여 AI의 파일 접근을 제한합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "project_path": {
                            "type": "string",
                            "description": "프로젝트 루트 경로 (선택)",
                        },
                    },
                    "required": ["project_id"],
                },
            ),
            Tool(
                name="get_boundary_violations",
                description="""경계 위반 이력 조회.
                현재 세션에서 발생한 모든 경계 위반 시도를 반환합니다.
                보안 감사 및 디버깅에 활용됩니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "project_path": {
                            "type": "string",
                            "description": "프로젝트 루트 경로 (선택)",
                        },
                    },
                    "required": ["project_id"],
                },
            ),
            Tool(
                name="clear_boundary",
                description="""경계 설정 초기화.
                현재 설정된 작업 경계를 제거하고 기본 상태로 복원합니다.
                작업 전환 시 호출하여 이전 경계를 정리합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "project_path": {
                            "type": "string",
                            "description": "프로젝트 루트 경로 (선택)",
                        },
                    },
                    "required": ["project_id"],
                },
            ),
            # ===== Initial Scanner (Context Graph) Tools =====
            Tool(
                name="scan_project_deep",
                description="""[Initial Context Scan] Context Graph 기반 프로젝트 심층 스캔.

                5P 설계 원칙에 따른 3-Phase 스캔:
                - Phase A: Global Shallow Scan (전체 파일 구조 파악)
                - Phase B: Structural Linking (import/export 관계 분석)
                - Phase C: Semantic Context (Lazy - 필요시 로드)

                스캔 모드:
                - FULL: 전체 코드베이스 심층 분석 (토큰 소모 높음)
                - LIGHT: 핵심 파일만 스캔 (README, 진입점, 설정)
                - NONE: 스캔 건너뛰기

                초기 1회만 수행, 이후 rescan_project로 변경분만 추적.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 고유 식별자"},
                        "project_path": {"type": "string", "description": "프로젝트 루트 경로"},
                        "scan_mode": {
                            "type": "string",
                            "enum": ["FULL", "LIGHT", "NONE"],
                            "description": "스캔 모드 (FULL/LIGHT/NONE)",
                        },
                        "file_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "스캔할 파일 패턴 (선택, 기본: 언어별 소스 파일)",
                        },
                    },
                    "required": ["project_id", "project_path", "scan_mode"],
                },
            ),
            Tool(
                name="rescan_project",
                description="""[Initial Context Scan] 프로젝트 증분 재스캔.

                이전 스캔 이후 변경된 파일만 선택적으로 재분석합니다.
                - 새로 추가된 파일 감지
                - 수정된 파일 업데이트
                - 삭제된 파일 Context Graph에서 제거

                기존 Context Graph에 증분 업데이트를 적용합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 고유 식별자"},
                        "project_path": {"type": "string", "description": "프로젝트 루트 경로"},
                        "force_full": {
                            "type": "boolean",
                            "description": "강제 전체 재스캔 여부 (기본: false)",
                        },
                    },
                    "required": ["project_id", "project_path"],
                },
            ),
            Tool(
                name="get_scan_estimate",
                description="""[Initial Context Scan] 스캔 예상 비용 조회.

                스캔 전 예상 정보를 제공합니다:
                - 예상 파일 수
                - 예상 토큰 소모량
                - 예상 비용 (모델별)
                - 권장 스캔 모드

                FULL 모드 선택 전 반드시 호출하여 비용을 확인하세요.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string", "description": "프로젝트 루트 경로"},
                        "scan_mode": {
                            "type": "string",
                            "enum": ["FULL", "LIGHT"],
                            "description": "예상할 스캔 모드",
                        },
                    },
                    "required": ["project_path", "scan_mode"],
                },
            ),
            Tool(
                name="get_context_graph_info",
                description="""[Initial Context Scan] Context Graph 통계 조회.

                현재 프로젝트의 Context Graph 상태를 조회합니다:
                - 총 노드(파일) 수
                - 총 엣지(관계) 수
                - 언어별 파일 분포
                - 시맨틱 레벨 분포
                - 마지막 스캔 시간

                Context Graph가 없으면 scan_project_deep 호출을 권장합니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 고유 식별자"}
                    },
                    "required": ["project_id"],
                },
            ),
            # ============ Multi-Session Parallel Development Tools ============
            Tool(
                name="sync_parallel_sessions",
                description="""[Pro+] 병렬 세션 맥락 동기화.

                여러 터미널에서 동시에 작업할 때 맥락을 자동으로 머지합니다.

                사용 시나리오:
                - Terminal 1: 인증 시스템 개발
                - Terminal 2: API 엔드포인트 개발
                - Terminal 3: 프론트엔드 개발
                → 모든 맥락이 자동으로 병합되어 전체 프로젝트 맥락 유지

                호출 시점:
                - 다른 터미널에서 작업한 내용을 가져올 때
                - 주기적 동기화 (30초 간격)
                - 작업 완료 후 최종 머지""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "force": {"type": "boolean", "description": "강제 동기화 (시간 간격 무시)"},
                    },
                    "required": ["project_id"],
                },
            ),
            Tool(
                name="get_active_sessions",
                description="""[Pro+] 활성 세션 목록 조회.

                현재 실행 중인 다른 Claude Code 세션을 조회합니다.

                반환 정보:
                - 세션 ID
                - 작업 중인 브랜치
                - 마지막 활동 시간
                - 생성한 맥락 개수
                - 머지 횟수

                이 정보로 병렬 작업 현황을 파악할 수 있습니다.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "프로젝트 ID"},
                        "include_statistics": {
                            "type": "boolean",
                            "description": "통계 정보 포함 여부 (기본: false)",
                        },
                    },
                    "required": ["project_id"],
                },
            ),
            # ============ Auto-verification Tool (Phase 9.1) ============
            Tool(
                name="verify_response",
                description="""[자동 할루시네이션 검증]
                AI 응답의 확신도를 의미적으로 분석하고 자동 검증합니다.

                검증 절차:
                1. 의미 기반 확신도 감지 (fuzzy_claim_analyzer)
                2. 확신도 >= 0.8이면 Claim 추출
                3. Claim-Evidence 매칭 검증
                4. Grounding Score 계산
                5. Score < 0.7이면 재수행 트리거

                사용 시나리오:
                - AI가 "확실합니다", "완료했습니다" 등 자신감 있는 표현 사용 시
                - 의미상으로 높은 확신도가 감지될 때
                - 대화 완료 후 전체 응답 검증 시

                재수행 트리거:
                - 할루시네이션 감지 시 자동으로 재작업 권장
                - 유저에게 검증 실패 사유 알림
                - 근거 부족 주장 목록 제공""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "response_text": {
                            "type": "string",
                            "description": "검증할 AI 응답 텍스트"
                        },
                        "context": {
                            "type": "object",
                            "description": "검증에 필요한 컨텍스트 (파일 내용, 테스트 결과 등)",
                        },
                    },
                    "required": ["response_text"],
                },
            ),
        ]

        # Filter to show only core tools (other tools remain callable via call_tool)
        tools = [t for t in tools if t.name in VISIBLE_TOOLS]

        return tools

    def _get_auto_trigger_reminder(tool_name: str, arguments: dict, result: dict) -> str | None:
        """
        Auto Trigger 시스템: MANDATORY 도구 호출 권장 메시지 생성

        Args:
            tool_name: 방금 실행된 도구 이름
            arguments: 도구 인자
            result: 도구 실행 결과

        Returns:
            권장 메시지 (없으면 None)
        """
        # MANDATORY 도구 목록
        MANDATORY_TOOLS = {
            "initialize_context",
            "create_branch",
            "update_memory",
            "get_active_summary",
        }

        # MANDATORY 도구는 reminder 불필요
        if tool_name in MANDATORY_TOOLS:
            return None

        # 실패한 도구는 reminder 불필요
        if not result.get("success", False):
            return None

        # 비-MANDATORY 도구 실행 후 update_memory 권장
        reminder = (
            f"[CORTEX AUTO-TRIGGER REMINDER]\n"
            f"'{tool_name}' 도구 실행이 완료되었습니다.\n"
            f"CORTEX_MEMORY_PROTOCOL에 따라 다음 작업을 권장합니다:\n"
            f"  - update_memory: 방금 작업 내용을 맥락에 기록\n"
            f"  - record_reference: 사용한 맥락 조합을 참조 이력에 기록\n"
        )

        return reminder

    @server.call_tool()
    @async_cortex_function(auto_load_context=True, auto_save=True, auto_record=True)
    async def call_tool(name: str, arguments: dict, _cortex_context: Optional[dict] = None) -> list[TextContent]:
        """
        도구 호출 처리

        Level 2 자동화 (Python-enforced):
        - 키워드 자동 추출
        - Reference History 자동 쿼리
        - 맥락 자동 로드
        - 이전 대화 자동 검색
        - 작업 후 자동 저장 (finally block)
        - 참조 이력 자동 기록 (finally block)
        """
        import time

        start_time = time.time()

        logger.info(f">>> 도구 호출 시작: {name}")

        # ============================================================
        # 입력 검증 (보안 - Path Traversal 방지)
        # ============================================================
        try:
            # project_id 검증
            if "project_id" in arguments and arguments["project_id"]:
                sanitize_path_component(arguments["project_id"], "project_id")

            # branch_id 검증
            if "branch_id" in arguments and arguments["branch_id"]:
                sanitize_path_component(arguments["branch_id"], "branch_id")

            # context_id 검증
            if "context_id" in arguments and arguments["context_id"]:
                # context_id는 file:// 형식일 수 있으므로 URL 디코딩 후 검증
                context_id = arguments["context_id"]
                if context_id.startswith("file://"):
                    # file:// 스킴은 허용하되 경로 부분만 검증
                    pass  # 파일 경로는 별도 검증 로직이 있음
                else:
                    sanitize_path_component(context_id, "context_id")

            # file_path 검증 (파일 경로는 절대 경로 허용, 하지만 .. 는 차단)
            if "file_path" in arguments and arguments["file_path"]:
                file_path = arguments["file_path"]
                if ".." in file_path or "\0" in file_path:
                    raise ValueError(
                        f"Invalid file_path: '{file_path}'. "
                        f"Path traversal patterns (.., null bytes) not allowed."
                    )

        except ValueError as e:
            # 검증 실패 시 즉시 에러 반환
            logger.error(f"[SECURITY] Input validation failed for tool '{name}': {e}")
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                            "tool_blocked": name,
                            "security_check": "path_traversal_prevention",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ]

        # ============================================================
        # Phase 3: Pre-Hook 자동 실행 (도구 실행 전 강제 처리)
        # ============================================================
        auto_trigger = get_auto_trigger()
        project_id = arguments.get("project_id")
        pre_hook_result = auto_trigger.pre_hook(name, arguments, project_id)

        # Pre-hook에서 제공하는 정보 로깅
        if pre_hook_result.get("claude_core_loaded"):
            logger.info(f"[PRE_HOOK] CLAUDE_CORE loaded: {pre_hook_result['claude_core_size']} bytes")
        if pre_hook_result.get("search_context_required"):
            logger.info(f"[PRE_HOOK] Search context recommended: {pre_hook_result['search_context_query']}")

        # ============================================================
        # Phase 10.2: Pending Suggestions 검증 (출처 책임 강제)
        # ============================================================
        # accept/reject 도구가 아닌 경우만 체크
        if name not in {"accept_suggestions", "reject_suggestions", "suggest_contexts"}:
            if project_id and auto_trigger.cache.has_pending_suggestions(project_id):
                pending_list = auto_trigger.cache.get_pending_suggestions(project_id)
                logger.warning(
                    f"[CORTEX] ⚠️⚠️⚠️  PENDING SUGGESTIONS DETECTED ⚠️⚠️⚠️\n"
                    f"도구 '{name}' 실행 전 미처리 suggest_contexts 세션 발견:\n"
                    f"  - {len(pending_list)}개의 pending session(s)\n"
                    f"  - 출처 책임 원칙: accept_suggestions 또는 reject_suggestions 호출 필수\n"
                    f"  - Pending sessions: {[p['session_id'] for p in pending_list]}"
                )
                # 경고만 하고 실행은 허용 (Plan B 모드)
                # 향후 엄격 모드에서는 차단 가능

        # ============================================================
        # 라이센스 검증 (런타임 보호 - 무단 사용 방지)
        # ============================================================
        license_error = _verify_license_runtime()
        if license_error:
            # 라이센스 없음 또는 만료 - 실행 차단
            logger.error(f"License check failed for tool '{name}': {license_error['error']}")

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": license_error["error"],
                            "license_status": license_error["license_status"],
                            "message": license_error["message"],
                            "help_url": license_error.get("help_url"),
                            "tool_blocked": name,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ]

        # Telemetry v2.0: Initialize telemetry client
        telemetry = None
        if TELEMETRY_AVAILABLE:
            try:
                telemetry = CortexTelemetry()
                # Emit SERVER_OPERATION_CALLED event for DAU tracking
                telemetry.client.emit_event(
                    event_name=CortexEventName.SERVER_OPERATION_CALLED,
                    channel=ChannelType.SERVER,
                    metadata={"tool_name": name, "arguments": arguments},
                )
            except Exception as e:
                logger.warning(f"Telemetry initialization error: {e}")

        try:
            if name == "initialize_context":
                result = await _handle_initialize_context(
                    project_id=arguments["project_id"],
                    project_path=arguments["project_path"],
                    scan_mode=arguments["scan_mode"],
                    file_patterns=arguments.get("file_patterns"),
                )

                # Telemetry v2.0: Emit events for initialize_context
                if result.get("success") and telemetry:
                    try:
                        # CONTEXT_CREATED: 초기 프로젝트 루트 브랜치 생성
                        telemetry.client.emit_event(
                            event_name=CortexEventName.CONTEXT_CREATED,
                            channel=ChannelType.SERVER,
                            metadata={
                                "project_id": arguments["project_id"],
                                "scan_mode": arguments["scan_mode"],
                                "result": result,
                            },
                        )
                        # SESSION_STARTED: 새 프로젝트 시작 = 새 세션
                        telemetry.client.emit_event(
                            event_name=CortexEventName.SESSION_STARTED,
                            channel=ChannelType.SERVER,
                            metadata={
                                "project_id": arguments["project_id"],
                                "scan_mode": arguments["scan_mode"],
                            },
                        )
                    except Exception as e:
                        logger.warning(f"Telemetry event emission error (initialize_context): {e}")

            elif name == "create_branch":
                result = memory_manager.create_branch(
                    project_id=arguments["project_id"],
                    branch_topic=arguments["branch_topic"],
                    parent_branch=arguments.get("parent_branch"),
                )

                # 새 브랜치 내용을 RAG에 인덱싱
                if result["success"]:
                    get_rag_engine().index_content(
                        content=f"Branch created: {arguments['branch_topic']}",
                        metadata={
                            "project_id": arguments["project_id"],
                            "branch_id": result["branch_id"],
                            "type": "branch_creation",
                        },
                    )

                    # Telemetry v2.0: Emit events for create_branch
                    if telemetry:
                        try:
                            # Determine if this was auto-created by AI or manual
                            auto_created = arguments.get("auto_created", False)
                            event_name = (
                                CortexEventName.CONTEXT_AUTO_CREATED
                                if auto_created
                                else CortexEventName.CONTEXT_CREATED
                            )

                            telemetry.client.emit_event(
                                event_name=event_name,
                                channel=ChannelType.SERVER,
                                metadata={
                                    "project_id": arguments["project_id"],
                                    "branch_id": result["branch_id"],
                                    "branch_topic": arguments["branch_topic"],
                                    "auto_created": auto_created,
                                    "parent_branch": arguments.get("parent_branch"),
                                },
                            )
                        except Exception as e:
                            logger.warning(f"Telemetry event emission error (create_branch): {e}")

                    # Extension Sync: 브랜치 생성 이벤트 전송
                    if EXTENSION_SYNC_AVAILABLE:
                        try:
                            ext_sync = get_extension_sync()
                            # Context Transition 기록 (created 이벤트)
                            await ext_sync.record_context_transition(
                                project_id=arguments["project_id"],
                                branch_id=result["branch_id"],
                                to_context_id=result["branch_id"],
                                event_type="created",
                                from_context_id=arguments.get("parent_branch"),
                            )
                            # Active Context 동기화
                            await ext_sync.sync_active_context(
                                project_id=arguments["project_id"],
                                branch_id=result["branch_id"],
                                context_id=result["branch_id"],
                                context_name=arguments["branch_topic"],
                                branch_topic=arguments["branch_topic"],
                            )
                        except Exception as e:
                            logger.warning(f"Extension sync error (create_branch): {e}")

            elif name == "search_context":
                result = get_rag_engine().search_context(
                    query=arguments["query"],
                    project_id=arguments.get("project_id"),
                    branch_id=arguments.get("branch_id"),
                    top_k=arguments.get("top_k"),
                )

                # =====================================================================
                # Phase C: Lazy Semantic Resolution (v3.0)
                # 검색 결과 없으면 자동으로 SHALLOW 노드들 해석 + RAG 인덱싱
                # =====================================================================
                project_id = arguments.get("project_id")
                result_count = result.get("result_count", 0)

                if (
                    result.get("success")
                    and result_count == 0
                    and project_id
                    and INITIAL_SCANNER_AVAILABLE
                ):
                    try:
                        logger.info(
                            f"[Phase C] 검색 결과 없음. Lazy Resolve 시도 (project: {project_id})"
                        )

                        # 1. Context Graph 로드
                        context_graph = get_context_graph(project_id)
                        if not context_graph:
                            logger.warning(f"[Phase C] Context Graph 없음: {project_id}")
                        else:
                            # 2. SHALLOW 노드들 찾기
                            from core.context_graph import SemanticLevel

                            shallow_nodes = [
                                node
                                for node in context_graph.get_all_nodes()
                                if node.semantic_level == SemanticLevel.SHALLOW
                            ]

                            if shallow_nodes:
                                logger.info(
                                    f"[Phase C] SHALLOW 노드 {len(shallow_nodes)}개 발견"
                                )

                                # 3. 최대 10개까지 일괄 해석
                                nodes_to_resolve = shallow_nodes[:10]
                                resolved_count = 0

                                for node in nodes_to_resolve:
                                    try:
                                        resolve_result = context_manager.lazy_resolve_semantic(
                                            project_id=project_id,
                                            context_node=node,
                                            rag_engine=rag_engine,
                                        )

                                        if resolve_result.get("success"):
                                            # Context Graph 업데이트
                                            context_graph.update_node(node)
                                            resolved_count += 1
                                    except Exception as node_err:
                                        logger.warning(
                                            f"[Phase C] 노드 해석 실패: {node.context_id}, {node_err}"
                                        )

                                # Context Graph 저장
                                if resolved_count > 0:
                                    context_graph.save()
                                    logger.info(
                                        f"[Phase C] {resolved_count}개 노드 해석 완료"
                                    )

                                    # 4. 재검색
                                    result = get_rag_engine().search_context(
                                        query=arguments["query"],
                                        project_id=arguments.get("project_id"),
                                        branch_id=arguments.get("branch_id"),
                                        top_k=arguments.get("top_k"),
                                    )
                                    logger.info(
                                        f"[Phase C] 재검색 결과: {result.get('result_count', 0)}개"
                                    )

                                    # Phase C 메타데이터 추가
                                    result["phase_c_triggered"] = True
                                    result["resolved_nodes"] = resolved_count
                            else:
                                logger.info("[Phase C] SHALLOW 노드 없음 (모두 DEEP)")

                    except Exception as phase_c_err:
                        logger.warning(f"[Phase C] Lazy Resolve 실패: {phase_c_err}")
                        import traceback

                        traceback.print_exc()
                        # Phase C 실패해도 원본 검색 결과는 반환

                # Telemetry v2.0: Emit CONTEXT_LOADED event for search_context
                if result.get("success") and result.get("results") and telemetry:
                    try:
                        result_count = len(result.get("results", []))
                        if result_count > 0:
                            telemetry.client.emit_event(
                                event_name=CortexEventName.CONTEXT_LOADED,
                                channel=ChannelType.SERVER,
                                metadata={
                                    "project_id": arguments.get("project_id"),
                                    "branch_id": arguments.get("branch_id"),
                                    "query": arguments["query"],
                                    "result_count": result_count,
                                    "top_k": arguments.get("top_k"),
                                },
                            )
                    except Exception as e:
                        logger.warning(f"Telemetry event emission error (search_context): {e}")

                # Extension Sync: 검색 결과 맥락들을 기록
                if result.get("success") and EXTENSION_SYNC_AVAILABLE:
                    try:
                        ext_sync = get_extension_sync()
                        # 검색 결과에서 context_id 추출
                        searched_ids = []
                        for item in result.get("results", []):
                            if isinstance(item, dict):
                                # metadata에서 context_id 추출 또는 id 필드 사용
                                ctx_id = item.get("context_id") or item.get("id")
                                if ctx_id:
                                    searched_ids.append(ctx_id)

                        if searched_ids:
                            await ext_sync.record_referenced_contexts(
                                project_id=arguments.get("project_id", ""),
                                branch_id=arguments.get("branch_id", ""),
                                referenced_context_ids=searched_ids,
                                query=arguments.get("query"),
                                task_keywords=[],  # search_context는 task_keywords가 없음
                            )
                    except Exception as e:
                        logger.warning(f"Extension sync error (search_context): {e}")

            elif name == "resolve_context":
                # Context ID 또는 file_path에서 노드 찾기
                project_id = arguments["project_id"]
                context_id = arguments.get("context_id")
                file_path = arguments.get("file_path")

                if not context_id and not file_path:
                    result = {
                        "success": False,
                        "error": "context_id 또는 file_path 중 하나는 필수입니다.",
                    }
                else:
                    try:
                        # Context Graph 로드
                        if not INITIAL_SCANNER_AVAILABLE:
                            result = {
                                "success": False,
                                "error": "Initial Scanner not available",
                            }
                        else:
                            context_graph = get_context_graph(project_id)
                            if not context_graph:
                                result = {
                                    "success": False,
                                    "error": f"Context Graph not found: {project_id}",
                                }
                            else:
                                # 노드 찾기
                                target_node = None
                                if context_id:
                                    target_node = context_graph.get_node(context_id)
                                elif file_path:
                                    # file_path에서 context_id 생성
                                    import os

                                    context_id = f"file://{os.path.basename(file_path)}"
                                    target_node = context_graph.get_node(context_id)

                                if not target_node:
                                    result = {
                                        "success": False,
                                        "error": f"Node not found: {context_id or file_path}",
                                    }
                                else:
                                    # Lazy Resolve 실행
                                    result = context_manager.lazy_resolve_semantic(
                                        project_id=project_id,
                                        context_node=target_node,
                                        rag_engine=rag_engine,
                                    )

                                    # Context Graph 업데이트 및 저장
                                    if result.get("success"):
                                        context_graph.update_node(target_node)
                                        context_graph.save()

                                        logger.info(
                                            f"[resolve_context] 노드 해석 완료: {target_node.context_id}"
                                        )
                    except Exception as e:
                        import traceback

                        result = {
                            "success": False,
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                        }
                        logger.error(f"[resolve_context] 에러: {e}")
                        traceback.print_exc()

            elif name == "update_memory":
                # Phase 9 할루시네이션 검증을 위해 project_id와 함께 MemoryManager 초기화
                try:
                    # [성능 개선] 인스턴스 캐싱 사용 (28초 → 67ms)
                    mm = get_memory_manager(arguments["project_id"])

                    # [UX 개선] 긴 내용 저장 시 처리 시간 안내
                    content_length = len(arguments["content"])
                    processing_time_notice = None
                    if content_length > 2000:
                        processing_time_notice = "수정한 내용이 많아서 업데이트에 시간이 좀 걸립니다"
                        logger.info(f"[UPDATE_MEMORY] 긴 내용 ({content_length:,}자) - {processing_time_notice}")

                    result = mm.update_memory(
                        project_id=arguments["project_id"],
                        branch_id=arguments["branch_id"],
                        content=arguments["content"],
                        role=arguments.get("role", "assistant"),
                        verified=arguments.get("verified", False),  # Phase 9.2: 할루시네이션 검증 건너뛰기 옵션
                    )
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    if logger is not None:
                        logger.error(f"update_memory failed: {e}\n{error_trace}")
                    return {
                        "success": False,
                        "error": f"Memory update failed: {str(e)}",
                        "traceback": error_trace
                    }

                # 방어적 코딩: result가 딕셔너리인지 확인
                if not isinstance(result, dict):
                    if logger is not None:
                        logger.error(f"update_memory returned non-dict type: {type(result)}")
                    return {"success": False, "error": "Invalid result type from update_memory"}

                # [UX 개선] 처리 시간 안내를 결과 메시지에 추가
                if processing_time_notice:
                    result["processing_time_notice"] = processing_time_notice
                    original_message = result.get("message", "")
                    result["message"] = f"{processing_time_notice}\n\n{original_message}"

                # Phase 9.2: AI 자기검증 - verification_required 처리
                if result.get("status") == "verification_required":
                    # AI에게 검증 요청 반환 (RAG 인덱싱 하지 않음)
                    if logger is not None:
                        logger.info("update_memory: verification required, skipping RAG indexing")
                    return result

                # =====================================================================
                # CRITICAL FIX: RAG 인덱싱 실패 처리 (즉시 사용자 알림)
                # =====================================================================
                if result.get("indexing_failed", False):
                    indexing_error = result.get("indexing_error", "Unknown error")
                    error_message = (
                        f"\n\n❌ RAG 인덱싱 실패 - 이 맥락은 검색되지 않습니다!\n"
                        f"원인: {indexing_error}\n"
                        f"영향: 향후 이 내용을 검색할 수 없습니다. 수동으로 재인덱싱이 필요합니다."
                    )
                    result["message"] = result.get("message", "") + error_message
                    result["indexing_status"] = "FAILED"

                    if logger is not None:
                        logger.error(
                            f"[RAG_INDEXING] CRITICAL: Indexing failed for branch {arguments.get('branch_id')}: {indexing_error}"
                        )

                # =====================================================================
                # Phase 9: 할루시네이션 검증 결과 자동 처리 (MANDATORY)
                # =====================================================================
                if result.get("success", False) and result.get("hallucination_check") is not None:
                    check = result.get("hallucination_check")

                    # check가 dict가 아니면 건너뜀 (verified=True인 경우 등)
                    if not isinstance(check, dict):
                        if logger is not None:
                            logger.info(f"hallucination_check is not dict, skipping Phase 9 warnings: {type(check)}")
                    else:
                        warnings = []

                        # 1. Grounding Score 검사
                        grounding_score = check.get("grounding_score", 1.0)
                        if grounding_score < 0.7:
                            severity = "CRITICAL" if grounding_score < 0.3 else "WARNING"
                            warnings.append(
                                f"[{severity}] 근거 부족 감지: Grounding Score {grounding_score:.2f}/1.0 "
                                f"({check.get('verified_claims', 0)}/{check.get('total_claims', 0)} 주장 검증됨)"
                            )

                        # 2. 모순 검사
                        contradictions = check.get("contradictions", 0)
                        if contradictions > 0:
                            warnings.append(
                                f"[CRITICAL] 응답 내 모순 발견: {contradictions}개"
                            )

                        # 3. Risk Level 검사
                        risk_level = check.get("risk_level", "unknown")
                        if risk_level in ["high", "critical"]:
                            warnings.append(
                                f"[ALERT] 위험 수준: {risk_level.upper()}"
                            )

                        # 4. 경고가 있으면 자동으로 결과에 추가 (AI가 무시할 수 없도록)
                        if warnings:
                            warning_message = "\n".join(warnings)
                            result["hallucination_warning"] = warning_message
                            result["verification_status"] = "PASSED_WITH_WARNINGS"

                            # 메시지에도 추가하여 눈에 띄게 표시
                            original_message = result.get("message", "")
                            result["message"] = f"{original_message}\n\n⚠️  할루시네이션 검증 경고:\n{warning_message}"

                            logger.warning(f"Hallucination warning: {warning_message}")
                        else:
                            # 검증 통과
                            result["verification_status"] = "PASSED"
                            result["message"] = result.get("message", "") + f"\n\n✅ 할루시네이션 검증 통과 (Grounding Score: {grounding_score:.2f})"
                        logger.info(f"Hallucination check passed: grounding_score={grounding_score:.2f}")

                # 대화 내용을 RAG에 인덱싱
                # [2026-01-04 성능 최적화] 백그라운드 인덱싱으로 변경 (5초 → 0ms)
                if result.get("success", False):
                    try:
                        # 백그라운드 인덱싱 제출 (즉시 반환)
                        background_processor.submit_task(
                            _index_content_worker,
                            arguments["content"],
                            {
                                "project_id": arguments["project_id"],
                                "branch_id": arguments["branch_id"],
                                "role": arguments.get("role", "assistant"),
                                "type": "conversation",
                            }
                        )
                        logger.info("[BACKGROUND] RAG 인덱싱 제출 완료 (백그라운드 처리)")
                    except Exception as e:
                        # Fallback: 백그라운드 실패 시 동기 실행
                        logger.warning(f"[BACKGROUND] RAG 제출 실패, 동기 Fallback 시도: {e}")
                        try:
                            get_rag_engine().index_content(
                                content=arguments["content"],
                                metadata={
                                    "project_id": arguments["project_id"],
                                    "branch_id": arguments["branch_id"],
                                    "role": arguments.get("role", "assistant"),
                                    "type": "conversation",
                                },
                            )
                            logger.info("[FALLBACK] RAG 동기 인덱싱 완료")
                        except Exception as fallback_error:
                            logger.error(f"[FALLBACK] RAG 인덱싱 완전 실패: {fallback_error}")
                            # 인덱싱 실패는 치명적 오류 아님 (검색만 불가능)

                    # Telemetry v2.0: Emit CONTEXT_MODIFIED event for update_memory
                    if telemetry:
                        try:
                            telemetry.client.emit_event(
                                event_name=CortexEventName.CONTEXT_MODIFIED,
                                channel=ChannelType.SERVER,
                                metadata={
                                    "project_id": arguments["project_id"],
                                    "branch_id": arguments["branch_id"],
                                    "role": arguments.get("role", "assistant"),
                                    "content_length": len(arguments["content"]),
                                },
                            )
                        except Exception as e:
                            logger.warning(f"Telemetry event emission error (update_memory): {e}")

                    # =====================================================================
                    # 자동 브랜치 생성 제안 처리 (핵심 기능 - Zero-Effort 구현)
                    # =====================================================================
                    auto_suggestion = result.get("auto_branch_suggestion")
                    if auto_suggestion and auto_suggestion.get("should_create"):
                        # Paid 티어에서는 자동으로 브랜치 생성
                        if not config.feature_flags.branching_confirm_required:
                            try:
                                # 자동으로 새 브랜치 생성
                                new_branch_result = memory_manager.create_branch(
                                    project_id=arguments["project_id"],
                                    branch_topic=auto_suggestion["suggested_name"],
                                )

                                if new_branch_result.get("success"):
                                    result["auto_branch_created"] = True
                                    result["new_branch_id"] = new_branch_result["branch_id"]
                                    result["new_branch_topic"] = auto_suggestion["suggested_name"]
                                    result["auto_branch_alert"] = (
                                        f"[자동 맥락 생성 완료] "
                                        f"주제 전환이 감지되어 새 브랜치 '{auto_suggestion['suggested_name']}'를 자동 생성했습니다. "
                                        f"확신도: {auto_suggestion['confidence']:.0%} | "
                                        f"이유: {auto_suggestion['reason']} | "
                                        f"새 브랜치 ID: {new_branch_result['branch_id']}"
                                    )
                                    logger.info(
                                        f"Auto-branch created: {result['auto_branch_alert']}"
                                    )
                                else:
                                    # 생성 실패 시 제안만 표시
                                    result["auto_branch_alert"] = (
                                        f"[자동 맥락 생성 실패] "
                                        f"브랜치 생성 시도 중 오류 발생. 수동으로 create_branch를 호출하세요."
                                    )
                                    logger.warning(
                                        f"Auto-branch creation failed: {new_branch_result}"
                                    )
                            except Exception as e:
                                logger.error(f"Auto-branch creation error: {e}")
                                result["auto_branch_alert"] = f"[자동 맥락 생성 오류] {str(e)}"
                        else:
                            # Free 티어 또는 확인 필요: 제안만 표시
                            result["auto_branch_alert"] = (
                                f"[자동 맥락 생성 감지] "
                                f"주제 전환이 감지되었습니다. "
                                f"확신도: {auto_suggestion['confidence']:.0%} | "
                                f"이유: {auto_suggestion['reason']} | "
                                f"제안 브랜치명: '{auto_suggestion['suggested_name']}' | "
                                f"새 브랜치를 생성하려면 create_branch 도구를 호출하세요."
                            )
                            logger.info(f"Auto-branch suggestion: {result['auto_branch_alert']}")

            elif name == "get_active_summary":
                result = memory_manager.get_active_summary(
                    project_id=arguments["project_id"], branch_id=arguments.get("branch_id")
                )

                # Telemetry v2.0: Emit events for get_active_summary
                if result.get("success") and telemetry:
                    try:
                        # SESSION_RESUMED_FROM_CONTEXT: 맥락에서 세션 재개 (Resurrection 계산용)
                        telemetry.client.emit_event(
                            event_name=CortexEventName.SESSION_RESUMED_FROM_CONTEXT,
                            channel=ChannelType.SERVER,
                            metadata={
                                "project_id": arguments["project_id"],
                                "branch_id": result.get("branch_id") or arguments.get("branch_id"),
                                "branch_topic": result.get("branch_topic"),
                            },
                        )
                        # CONTEXT_RESUMED: 기존 맥락 재개 (CDR 계산용)
                        telemetry.client.emit_event(
                            event_name=CortexEventName.CONTEXT_RESUMED,
                            channel=ChannelType.SERVER,
                            metadata={
                                "project_id": arguments["project_id"],
                                "branch_id": result.get("branch_id") or arguments.get("branch_id"),
                                "has_summary": bool(result.get("summary")),
                            },
                        )
                    except Exception as e:
                        logger.warning(f"Telemetry event emission error (get_active_summary): {e}")

                # Extension Sync: 현재 활성 컨텍스트 정보 동기화
                if result.get("success") and EXTENSION_SYNC_AVAILABLE:
                    try:
                        ext_sync = get_extension_sync()
                        branch_id = result.get("branch_id") or arguments.get("branch_id", "")
                        await ext_sync.sync_active_context(
                            project_id=arguments["project_id"],
                            branch_id=branch_id,
                            context_id=branch_id,  # branch가 현재 컨텍스트
                            context_name=result.get("branch_topic", branch_id),
                            summary=result.get("summary"),
                            branch_topic=result.get("branch_topic"),
                        )
                    except Exception as e:
                        logger.warning(f"Extension sync error (get_active_summary): {e}")

            elif name == "sync_to_cloud":
                cloud_sync = CloudSync(license_key=arguments["license_key"])
                result = cloud_sync.sync_to_cloud(project_id=arguments.get("project_id"))

                # Telemetry v2.0: sync_to_cloud only emits SERVER_OPERATION_CALLED (already done above)
                # No additional events needed per TELEMETRY_EVENTS_MAPPING.md

            elif name == "sync_from_cloud":
                # Research Metric: recovery_time_ms 측정 시작
                import time

                sync_start_time = time.time()

                cloud_sync = CloudSync(license_key=arguments["license_key"])
                result = cloud_sync.sync_from_cloud(project_id=arguments.get("project_id"))

                # Telemetry v2.0: Emit CONTEXT_LOADED event for sync_from_cloud
                if result.get("success") and telemetry:
                    try:
                        telemetry.client.emit_event(
                            event_name=CortexEventName.CONTEXT_LOADED,
                            channel=ChannelType.SERVER,
                            metadata={
                                "project_id": arguments.get("project_id"),
                                "source": "cloud_sync",
                            },
                        )
                    except Exception as e:
                        logger.warning(f"Telemetry event emission error (sync_from_cloud): {e}")

                # Research Metric: recovery_time_ms 기록
                if result.get("success"):
                    try:
                        from core.telemetry_client import record_research_metric

                        recovery_time_ms = (time.time() - sync_start_time) * 1000

                        record_research_metric(
                            recovery_time_ms=recovery_time_ms
                        )
                    except Exception as metric_error:
                        logger.warning(
                            f"Research metric collection error (sync_from_cloud): {metric_error}"
                        )

            # ============ Smart Context Tools (v2.0) ============
            elif name == "load_context":
                # Research Metric: recovery_time_ms 측정 시작
                import time

                load_start_time = time.time()

                result = context_manager.load_context(
                    project_id=arguments["project_id"],
                    branch_id=arguments["branch_id"],
                    context_id=arguments.get("context_id"),
                    force_full_load=arguments.get("force_full_load", False),
                )

                # Extension Sync: Active Context 상태 동기화
                if result.get("success") and EXTENSION_SYNC_AVAILABLE:
                    try:
                        ext_sync = get_extension_sync()
                        context_id = arguments.get("context_id") or arguments["branch_id"]
                        # Active Context 동기화
                        await ext_sync.sync_active_context(
                            project_id=arguments["project_id"],
                            branch_id=arguments["branch_id"],
                            context_id=context_id,
                            context_name=result.get("context_name", context_id),
                            summary=result.get("summary"),
                            branch_topic=result.get("branch_topic"),
                        )
                        # Context Transition 기록 (activated 이벤트)
                        await ext_sync.record_context_transition(
                            project_id=arguments["project_id"],
                            branch_id=arguments["branch_id"],
                            to_context_id=context_id,
                            event_type="activated",
                        )
                    except Exception as e:
                        logger.warning(f"Extension sync error (load_context): {e}")

                # Research Metric: recovery_time_ms 기록
                if result.get("success"):
                    try:
                        from core.telemetry_client import record_research_metric

                        recovery_time_ms = (time.time() - load_start_time) * 1000

                        record_research_metric(
                            recovery_time_ms=recovery_time_ms
                        )
                    except Exception as metric_error:
                        logger.warning(
                            f"Research metric collection error (load_context): {metric_error}"
                        )

            elif name == "get_loaded_contexts":
                result = context_manager.get_loaded_contexts()
                result["success"] = True

            elif name == "compress_context":
                result = context_manager.compress_context(
                    project_id=arguments["project_id"],
                    branch_id=arguments["branch_id"],
                    context_id=arguments["context_id"],
                )

                # Extension Sync: 압축 이벤트 기록
                if result.get("success") and EXTENSION_SYNC_AVAILABLE:
                    try:
                        ext_sync = get_extension_sync()
                        await ext_sync.record_context_transition(
                            project_id=arguments["project_id"],
                            branch_id=arguments["branch_id"],
                            to_context_id=arguments["context_id"],
                            event_type="compressed",
                        )
                    except Exception as e:
                        logger.warning(f"Extension sync error (compress_context): {e}")

            # ============ Reference History Tools (v2.0) ============
            elif name == "suggest_contexts":
                ref_history = get_reference_history(arguments["project_id"])
                result = ref_history.suggest_contexts(
                    query=arguments["query"],
                    branch_id=arguments.get("branch_id"),
                    top_k=arguments.get("top_k", 5),
                )

                # Extension Sync: 추천된 맥락 ID들을 기록
                if result.get("success") and EXTENSION_SYNC_AVAILABLE:
                    try:
                        ext_sync = get_extension_sync()
                        # 추천 결과에서 context_id 추출
                        suggested_ids = []
                        for suggestion in result.get("contexts", []):
                            if isinstance(suggestion, dict) and "context_id" in suggestion:
                                suggested_ids.append(suggestion["context_id"])
                            elif isinstance(suggestion, str):
                                suggested_ids.append(suggestion)

                        if suggested_ids:
                            await ext_sync.record_referenced_contexts(
                                project_id=arguments["project_id"],
                                branch_id=arguments.get("branch_id", ""),
                                referenced_context_ids=suggested_ids,
                                query=arguments.get("query"),
                                task_keywords=[],  # suggest_contexts는 task_keywords가 없음
                            )
                    except Exception as e:
                        logger.warning(f"Extension sync error (suggest_contexts): {e}")

                # Research Metric: context_stability_score (맥락 추천 안정성)
                if result.get("success"):
                    try:
                        from core.telemetry_client import record_research_metric

                        # contexts에서 confidence 평균 계산
                        contexts = result.get("contexts", [])
                        if contexts:
                            confidences = []
                            for context in contexts:
                                if isinstance(context, dict) and "confidence" in context:
                                    confidences.append(context["confidence"])

                            if confidences:
                                context_stability_score = sum(confidences) / len(confidences)

                                record_research_metric(
                                    context_stability_score=context_stability_score
                                )
                    except Exception as metric_error:
                        logger.warning(
                            f"Research metric collection error (suggest_contexts): {metric_error}"
                        )

            elif name == "accept_suggestions":
                ref_history = get_reference_history(arguments["project_id"])
                result = ref_history.accept_suggestions(
                    session_id=arguments["session_id"],
                    contexts_used=arguments["contexts_used"],
                )

                # Phase 10.2: Pending 제거 (출처 책임 완료)
                if result.get("success"):
                    session_id = arguments["session_id"]
                    auto_trigger.cache.remove_pending_suggestion(session_id)
                    logger.info(f"[CORTEX] ✅ accept_suggestions 완료 - Pending 제거: {session_id}")

            elif name == "reject_suggestions":
                ref_history = get_reference_history(arguments["project_id"])
                result = ref_history.reject_suggestions(
                    session_id=arguments["session_id"],
                    reason=arguments["reason"],
                )

                # Phase 10.2: Pending 제거 (출처 책임 완료)
                if result.get("success"):
                    session_id = arguments["session_id"]
                    auto_trigger.cache.remove_pending_suggestion(session_id)
                    logger.info(f"[CORTEX] ✅ reject_suggestions 완료 - Pending 제거: {session_id}")

            elif name == "record_reference":
                ref_history = get_reference_history(arguments["project_id"])
                result = ref_history.record(
                    task_keywords=arguments["task_keywords"],
                    contexts_used=arguments["contexts_used"],
                    branch_id=arguments["branch_id"],
                    query=arguments.get("query", ""),
                    project_id=arguments["project_id"],
                )

                # Extension Sync: 참조된 맥락 기록을 Extension API로 전송
                if result.get("success") and EXTENSION_SYNC_AVAILABLE:
                    try:
                        ext_sync = get_extension_sync()
                        await ext_sync.record_referenced_contexts(
                            project_id=arguments["project_id"],
                            branch_id=arguments["branch_id"],
                            referenced_context_ids=arguments["contexts_used"],
                            query=arguments.get("query"),
                            task_keywords=arguments["task_keywords"],
                        )
                    except Exception as e:
                        logger.warning(f"Extension sync error (record_reference): {e}")

            elif name == "update_reference_feedback":
                ref_history = get_reference_history(arguments["project_id"])
                result = ref_history.update_feedback(
                    entry_timestamp=arguments.get("entry_timestamp"),
                    feedback=arguments["feedback"],
                    contexts_actually_used=arguments.get("contexts_actually_used"),
                )

                # Research Metric: user_acceptance/rejection_count 기록
                if result.get("success"):
                    try:
                        from core.telemetry_client import record_research_metric

                        feedback = arguments["feedback"]
                        # feedback: "accepted", "partially_accepted", "rejected"
                        user_acceptance = 1 if feedback in ["accepted", "partially_accepted"] else 0
                        user_rejection = 1 if feedback == "rejected" else 0

                        record_research_metric(
                            user_acceptance_count=user_acceptance,
                            user_rejection_count=user_rejection
                        )
                    except Exception as metric_error:
                        logger.warning(
                            f"Research metric collection error (update_reference_feedback): {metric_error}"
                        )

            elif name == "get_reference_statistics":
                ref_history = get_reference_history(arguments["project_id"])
                result = ref_history.get_statistics()
                result["success"] = True

            # ============ Hierarchy Tools (v2.0) ============
            elif name == "create_node":
                result = memory_manager.create_node(
                    project_id=arguments["project_id"],
                    branch_id=arguments["branch_id"],
                    node_name=arguments["node_name"],
                    context_ids=arguments.get("context_ids"),
                )

            elif name == "list_nodes":
                nodes = memory_manager.list_nodes(
                    project_id=arguments["project_id"], branch_id=arguments["branch_id"]
                )
                result = {"success": True, "nodes": nodes, "count": len(nodes)}

            elif name == "suggest_node_grouping":
                result = memory_manager.suggest_node_grouping(
                    project_id=arguments["project_id"], branch_id=arguments["branch_id"]
                )

            elif name == "get_hierarchy":
                result = memory_manager.get_hierarchy(project_id=arguments["project_id"])

            # ============ Git Integration Tools (v2.0) ============
            elif name == "link_git_branch":
                git_sync = get_git_sync(arguments["project_id"])
                result = git_sync.link_git_branch(
                    repo_path=arguments["repo_path"],
                    git_branch=arguments.get("git_branch"),
                    cortex_branch_id=arguments.get("cortex_branch_id"),
                    auto_create=arguments.get("auto_create", True),
                )

                # auto_create이고 새 브랜치 생성된 경우 MemoryManager로 실제 브랜치 생성
                if result["success"] and result.get("action") == "created":
                    git_branch_name = result.get("git_branch", "git_branch")
                    memory_manager.create_branch(
                        project_id=arguments["project_id"], branch_topic=f"git_{git_branch_name}"
                    )

            elif name == "get_git_status":
                git_sync = get_git_sync(arguments["project_id"])
                result = git_sync.get_git_info(repo_path=arguments["repo_path"])

            elif name == "check_git_branch_change":
                git_sync = get_git_sync(arguments["project_id"])
                result = git_sync.auto_sync_on_checkout(
                    repo_path=arguments["repo_path"], memory_manager=memory_manager
                )

            elif name == "list_git_links":
                git_sync = get_git_sync(arguments["project_id"])
                result = git_sync.list_linked_branches(repo_path=arguments.get("repo_path"))

            elif name == "unlink_git_branch":
                git_sync = get_git_sync(arguments["project_id"])
                result = git_sync.unlink_git_branch(
                    repo_path=arguments["repo_path"], git_branch=arguments["git_branch"]
                )

            # ============ Dashboard Tools (Phase 6) ============
            elif name == "get_dashboard_url":
                from dashboard.server import get_dashboard_server, start_dashboard

                server = get_dashboard_server()

                if not server.is_running and arguments.get("start_if_not_running", True):
                    start_result = start_dashboard(
                        open_browser=arguments.get("open_browser", False)
                    )
                    result = {
                        "success": start_result.get("success", False),
                        "url": server.get_url(),
                        "started": True,
                        "message": start_result.get("message", ""),
                    }
                else:
                    result = {
                        "success": True,
                        "url": server.get_url(),
                        "running": server.is_running,
                    }

            # ============ Backup Tools (Phase 7) ============
            elif name == "create_snapshot":
                backup_mgr = get_backup_manager()
                result = backup_mgr.create_snapshot(
                    project_id=arguments["project_id"],
                    description=arguments.get("description", ""),
                    snapshot_type=arguments.get("snapshot_type", "manual"),
                    branch_id=arguments.get("branch_id"),
                )

            elif name == "restore_snapshot":
                # Research Metric: recovery_time_ms 측정 시작
                import time

                restore_start_time = time.time()

                backup_mgr = get_backup_manager()
                result = backup_mgr.restore_snapshot(
                    project_id=arguments["project_id"],
                    snapshot_id=arguments["snapshot_id"],
                    overwrite=arguments.get("overwrite", False),
                )

                # Research Metric: recovery_time_ms 기록
                if result.get("success"):
                    try:
                        from core.telemetry_client import record_research_metric

                        recovery_time_ms = (time.time() - restore_start_time) * 1000

                        record_research_metric(
                            recovery_time_ms=recovery_time_ms
                        )
                    except Exception as metric_error:
                        logger.warning(
                            f"Research metric collection error (restore_snapshot): {metric_error}"
                        )

            elif name == "list_snapshots":
                backup_mgr = get_backup_manager()
                result = backup_mgr.list_snapshots(
                    project_id=arguments["project_id"],
                    snapshot_type=arguments.get("snapshot_type"),
                    limit=arguments.get("limit", 20),
                )
                result["success"] = True

            elif name == "get_backup_history":
                backup_mgr = get_backup_manager()
                result = backup_mgr.get_history(
                    project_id=arguments["project_id"], limit=arguments.get("limit", 50)
                )
                result["success"] = True

            # ============ Automation Tools (Phase 8) ============
            elif name == "get_automation_status":
                auto_mgr = get_automation_manager(arguments["project_id"])
                result = auto_mgr.get_status()
                result["success"] = True

            elif name == "record_automation_feedback":
                auto_mgr = get_automation_manager(arguments["project_id"])
                result = auto_mgr.record_feedback(
                    action_type=arguments["action_type"],
                    feedback=arguments["feedback"],
                    action_id=arguments.get("action_id"),
                )

                # Research Metric: intervention_precision 기록
                if result.get("success"):
                    try:
                        from core.telemetry_client import record_research_metric

                        feedback = arguments["feedback"]
                        # intervention_precision: 자동화가 얼마나 정확했는지 (1=성공, 0=실패)
                        intervention_precision = 1.0 if feedback == "accepted" else 0.0

                        record_research_metric(
                            intervention_precision=intervention_precision
                        )
                    except Exception as metric_error:
                        logger.warning(
                            f"Research metric collection error (record_automation_feedback): {metric_error}"
                        )

            elif name == "should_confirm_action":
                auto_mgr = get_automation_manager(arguments["project_id"])
                result = auto_mgr.should_confirm(arguments["action_type"])
                result["success"] = True

            elif name == "set_automation_mode":
                auto_mgr = get_automation_manager(arguments["project_id"])
                result = auto_mgr.set_mode(
                    mode=arguments["mode"],
                    disable_auto_switch=arguments.get("disable_auto_switch", False),
                )

            # ============ Semantic Web Tools (Enterprise Only) ============
            elif name == "add_semantic_relation":
                if not SEMANTIC_WEB_AVAILABLE:
                    result = {
                        "success": False,
                        "error": "시맨틱 웹 엔진이 사용 불가능합니다.",
                        "tier_required": "enterprise",
                    }
                elif not config.is_feature_enabled("semantic_web_enabled"):
                    result = {
                        "success": False,
                        "error": "시맨틱 웹 기능이 비활성화되어 있습니다. Enterprise 티어가 필요합니다.",
                        "tier_required": "enterprise",
                    }
                else:
                    project_id = arguments["project_id"]
                    if project_id not in _semantic_web_engines:
                        _semantic_web_engines[project_id] = SemanticWebEngine(
                            project_id, enabled=True
                        )
                    sw_engine = _semantic_web_engines[project_id]

                    relation_type = RelationType[arguments["relation_type"]]
                    relation = sw_engine.add_relation(
                        source=arguments["source"],
                        target=arguments["target"],
                        relation_type=relation_type,
                        confidence=arguments.get("confidence", 1.0),
                    )
                    result = {
                        "success": True,
                        "relation_id": relation.id,
                        "message": f"관계 추가됨: {arguments['source']} --[{arguments['relation_type']}]--> {arguments['target']}",
                    }

            elif name == "infer_relations":
                if not SEMANTIC_WEB_AVAILABLE or not config.is_feature_enabled(
                    "semantic_web_enabled"
                ):
                    result = {
                        "success": False,
                        "error": "시맨틱 웹 기능이 비활성화되어 있습니다. Enterprise 티어가 필요합니다.",
                        "tier_required": "enterprise",
                    }
                else:
                    project_id = arguments["project_id"]
                    if project_id not in _semantic_web_engines:
                        _semantic_web_engines[project_id] = SemanticWebEngine(
                            project_id, enabled=True
                        )
                    sw_engine = _semantic_web_engines[project_id]

                    relation_type = RelationType[arguments["relation_type"]]
                    inference_result = sw_engine.infer_transitive_relations(
                        context_id=arguments["context_id"],
                        relation_type=relation_type,
                        max_depth=arguments.get("max_depth", 5),
                    )
                    result = {
                        "success": True,
                        "inferred_contexts": inference_result.inferred_contexts,
                        "paths": inference_result.paths,
                        "confidence": inference_result.confidence,
                        "depth": inference_result.depth,
                    }

            elif name == "detect_conflicts":
                if not SEMANTIC_WEB_AVAILABLE or not config.is_feature_enabled(
                    "semantic_web_enabled"
                ):
                    result = {
                        "success": False,
                        "error": "시맨틱 웹 기능이 비활성화되어 있습니다. Enterprise 티어가 필요합니다.",
                        "tier_required": "enterprise",
                    }
                else:
                    project_id = arguments["project_id"]
                    if project_id not in _semantic_web_engines:
                        _semantic_web_engines[project_id] = SemanticWebEngine(
                            project_id, enabled=True
                        )
                    sw_engine = _semantic_web_engines[project_id]

                    conflicts = sw_engine.detect_conflicts(context_id=arguments.get("context_id"))
                    result = {
                        "success": True,
                        "conflicts": [
                            {
                                "type": c.conflict_type.value,
                                "contexts": c.contexts,
                                "description": c.description,
                                "severity": c.severity,
                            }
                            for c in conflicts
                        ],
                        "conflict_count": len(conflicts),
                    }

            elif name == "suggest_related_contexts":
                if not SEMANTIC_WEB_AVAILABLE or not config.is_feature_enabled(
                    "semantic_web_enabled"
                ):
                    result = {
                        "success": False,
                        "error": "시맨틱 웹 기능이 비활성화되어 있습니다. Enterprise 티어가 필요합니다.",
                        "tier_required": "enterprise",
                    }
                else:
                    project_id = arguments["project_id"]
                    if project_id not in _semantic_web_engines:
                        _semantic_web_engines[project_id] = SemanticWebEngine(
                            project_id, enabled=True
                        )
                    sw_engine = _semantic_web_engines[project_id]

                    suggestions = sw_engine.suggest_related_contexts(
                        context_id=arguments["context_id"],
                        max_depth=arguments.get("max_depth", 3),
                        min_confidence=arguments.get("min_confidence", 0.3),
                    )
                    result = {
                        "success": True,
                        "suggestions": [
                            {"context_id": ctx_id, "confidence": conf, "path": path}
                            for ctx_id, conf, path in suggestions
                        ],
                        "count": len(suggestions),
                    }

            elif name == "get_semantic_web_stats":
                if not SEMANTIC_WEB_AVAILABLE or not config.is_feature_enabled(
                    "semantic_web_enabled"
                ):
                    result = {
                        "success": False,
                        "error": "시맨틱 웹 기능이 비활성화되어 있습니다. Enterprise 티어가 필요합니다.",
                        "tier_required": "enterprise",
                    }
                else:
                    project_id = arguments["project_id"]
                    if project_id not in _semantic_web_engines:
                        _semantic_web_engines[project_id] = SemanticWebEngine(
                            project_id, enabled=True
                        )
                    sw_engine = _semantic_web_engines[project_id]

                    stats = sw_engine.get_statistics()
                    result = {"success": True, "statistics": stats}

            # ============ Boundary Protection Handlers ============
            elif name == "set_boundary":
                project_id = arguments["project_id"]
                project_path = arguments.get("project_path")

                # 인스턴스 캐시에서 가져오거나 새로 생성
                cache_key = f"{project_id}:{project_path or 'default'}"
                if cache_key not in _boundary_protection_instances:
                    _boundary_protection_instances[cache_key] = get_boundary_protection(
                        project_id=project_id, project_path=project_path
                    )
                bp = _boundary_protection_instances[cache_key]

                # allowed_actions를 ActionType으로 변환
                allowed_actions = None
                if arguments.get("allowed_actions"):
                    allowed_actions = []
                    for action_str in arguments["allowed_actions"]:
                        try:
                            allowed_actions.append(BoundaryActionType[action_str.upper()])
                        except KeyError:
                            pass  # 잘못된 액션 타입은 무시

                boundary = bp.set_boundary(
                    task=arguments["task"],
                    allowed_files=arguments.get("allowed_files"),
                    allowed_patterns=arguments.get("allowed_patterns"),
                    allowed_actions=allowed_actions,
                    strict_mode=arguments.get("strict_mode", False),
                )

                result = {
                    "success": True,
                    "boundary": {
                        "task": boundary.task,
                        "allowed_files": list(boundary.allowed_files),
                        "allowed_patterns": list(boundary.allowed_patterns),
                        "forbidden_files": list(boundary.forbidden_files),
                        "allowed_actions": [a.value for a in boundary.allowed_actions],
                        "strict_mode": boundary.strict_mode,
                    },
                    "message": "작업 경계가 설정되었습니다.",
                }

            elif name == "infer_boundary":
                project_id = arguments["project_id"]
                project_path = arguments.get("project_path")

                cache_key = f"{project_id}:{project_path or 'default'}"
                if cache_key not in _boundary_protection_instances:
                    _boundary_protection_instances[cache_key] = get_boundary_protection(
                        project_id=project_id, project_path=project_path
                    )
                bp = _boundary_protection_instances[cache_key]

                boundary = bp.infer_boundary(
                    task=arguments["task"],
                    context=arguments.get("context"),
                    recent_files=arguments.get("recent_files"),
                )

                result = {
                    "success": True,
                    "boundary": {
                        "task": boundary.task,
                        "allowed_files": list(boundary.allowed_files),
                        "allowed_patterns": list(boundary.allowed_patterns),
                        "forbidden_files": list(boundary.forbidden_files),
                        "allowed_actions": [a.value for a in boundary.allowed_actions],
                        "strict_mode": boundary.strict_mode,
                    },
                    "message": "작업 경계가 자동 추론되었습니다.",
                }

            elif name == "validate_boundary_action":
                project_id = arguments["project_id"]
                project_path = arguments.get("project_path")

                cache_key = f"{project_id}:{project_path or 'default'}"
                if cache_key not in _boundary_protection_instances:
                    _boundary_protection_instances[cache_key] = get_boundary_protection(
                        project_id=project_id, project_path=project_path
                    )
                bp = _boundary_protection_instances[cache_key]

                # action 문자열을 ActionType으로 변환
                try:
                    action = BoundaryActionType[arguments["action"].upper()]
                except KeyError:
                    result = {
                        "success": False,
                        "error": f"잘못된 액션 타입: {arguments['action']}. 허용된 값: READ, WRITE, CREATE, DELETE, MODIFY",
                    }
                else:
                    validation = bp.validate_action(file_path=arguments["file_path"], action=action)

                    result = {
                        "success": True,
                        "validation": {
                            "allowed": validation.allowed,
                            "file_path": validation.file_path,
                            "action": validation.action.value,
                            "violation_type": (
                                validation.violation_type.value
                                if validation.violation_type
                                else None
                            ),
                            "reason": validation.reason,
                            "protection_level": (
                                validation.protection_level.value
                                if validation.protection_level
                                else None
                            ),
                        },
                    }

            elif name == "get_boundary_protocol":
                project_id = arguments["project_id"]
                project_path = arguments.get("project_path")

                cache_key = f"{project_id}:{project_path or 'default'}"
                if cache_key not in _boundary_protection_instances:
                    _boundary_protection_instances[cache_key] = get_boundary_protection(
                        project_id=project_id, project_path=project_path
                    )
                bp = _boundary_protection_instances[cache_key]

                protocol = bp.generate_boundary_protocol()

                result = {
                    "success": True,
                    "protocol": protocol,
                    "message": "System Prompt에 삽입할 경계 프로토콜이 생성되었습니다.",
                }

            elif name == "get_boundary_violations":
                project_id = arguments["project_id"]
                project_path = arguments.get("project_path")

                cache_key = f"{project_id}:{project_path or 'default'}"
                if cache_key not in _boundary_protection_instances:
                    _boundary_protection_instances[cache_key] = get_boundary_protection(
                        project_id=project_id, project_path=project_path
                    )
                bp = _boundary_protection_instances[cache_key]

                violations = bp.get_boundary_violations()

                result = {
                    "success": True,
                    "violations": [
                        {
                            "file_path": v.file_path,
                            "action": v.action.value,
                            "violation_type": v.violation_type.value if v.violation_type else None,
                            "reason": v.reason,
                            "timestamp": (
                                v.timestamp.isoformat() if hasattr(v, "timestamp") else None
                            ),
                        }
                        for v in violations
                    ],
                    "violation_count": len(violations),
                }

            elif name == "clear_boundary":
                project_id = arguments["project_id"]
                project_path = arguments.get("project_path")

                cache_key = f"{project_id}:{project_path or 'default'}"
                if cache_key not in _boundary_protection_instances:
                    _boundary_protection_instances[cache_key] = get_boundary_protection(
                        project_id=project_id, project_path=project_path
                    )
                bp = _boundary_protection_instances[cache_key]

                bp.clear_boundary()

                result = {"success": True, "message": "작업 경계가 초기화되었습니다."}

            # ===== Initial Scanner (Context Graph) Handlers =====
            elif name == "scan_project_deep":
                if not INITIAL_SCANNER_AVAILABLE:
                    result = {
                        "success": False,
                        "error": "Initial Scanner module not available. Please check installation.",
                    }
                else:
                    project_id = arguments["project_id"]
                    project_path = arguments["project_path"]
                    scan_mode_str = arguments["scan_mode"]
                    file_patterns = arguments.get("file_patterns")

                    # ScanMode enum 변환
                    try:
                        scan_mode = ScannerMode[scan_mode_str]
                    except KeyError:
                        result = {
                            "success": False,
                            "error": f"Invalid scan_mode: {scan_mode_str}. Must be FULL, LIGHT, or NONE",
                        }
                    else:
                        # 스캔 실행
                        scan_result = await scanner_scan_project(
                            project_id=project_id,
                            project_path=project_path,
                            scan_mode=scan_mode,
                            file_patterns=file_patterns,
                        )
                        result = {
                            "success": True,
                            "project_id": project_id,
                            "scan_mode": scan_mode_str,
                            "result": scan_result,
                        }

            elif name == "rescan_project":
                if not INITIAL_SCANNER_AVAILABLE:
                    result = {
                        "success": False,
                        "error": "Initial Scanner module not available. Please check installation.",
                    }
                else:
                    project_id = arguments["project_id"]
                    project_path = arguments["project_path"]
                    force_full = arguments.get("force_full", False)

                    rescan_result = await scanner_rescan_project(
                        project_id=project_id, project_path=project_path, force_full=force_full
                    )
                    result = {
                        "success": True,
                        "project_id": project_id,
                        "force_full": force_full,
                        "result": rescan_result,
                    }

            elif name == "get_scan_estimate":
                if not INITIAL_SCANNER_AVAILABLE:
                    result = {
                        "success": False,
                        "error": "Initial Scanner module not available. Please check installation.",
                    }
                else:
                    project_path = arguments["project_path"]
                    scan_mode_str = arguments["scan_mode"]

                    try:
                        scan_mode = ScannerMode[scan_mode_str]
                    except KeyError:
                        result = {
                            "success": False,
                            "error": f"Invalid scan_mode: {scan_mode_str}. Must be FULL or LIGHT",
                        }
                    else:
                        estimate = await scanner_get_estimate(
                            project_path=project_path, scan_mode=scan_mode
                        )
                        result = {
                            "success": True,
                            "project_path": project_path,
                            "scan_mode": scan_mode_str,
                            "estimate": estimate,
                        }

            elif name == "get_context_graph_info":
                if not INITIAL_SCANNER_AVAILABLE:
                    result = {
                        "success": False,
                        "error": "Initial Scanner module not available. Please check installation.",
                    }
                else:
                    project_id = arguments["project_id"]

                    # Context Graph 조회
                    graph = get_context_graph(project_id)
                    if graph is None:
                        result = {
                            "success": True,
                            "project_id": project_id,
                            "exists": False,
                            "message": "Context Graph not found. Run scan_project_deep first.",
                            "stats": None,
                        }
                    else:
                        stats = graph.get_statistics()
                        result = {
                            "success": True,
                            "project_id": project_id,
                            "exists": True,
                            "stats": stats,
                        }

            elif name == "sync_parallel_sessions":
                # 병렬 세션 맥락 동기화
                project_id = arguments["project_id"]
                force = arguments.get("force", False)

                try:
                    from core.multi_session_sync import get_multi_session_manager

                    manager = get_multi_session_manager(project_id)

                    # 현재 세션 확인
                    if not manager.current_session:
                        result = {
                            "success": False,
                            "error": "No active session. Create a session first with create_branch.",
                        }
                    else:
                        # 동기화 실행
                        sync_result = manager.sync_with_other_sessions(force=force)
                        result = {
                            "success": True,
                            "project_id": project_id,
                            "current_session": manager.current_session.session_id,
                            "sync_result": sync_result,
                        }
                except ImportError:
                    result = {"success": False, "error": "Multi-session sync module not available."}
                except Exception as e:
                    result = {"success": False, "error": f"Sync failed: {str(e)}"}

            elif name == "get_active_sessions":
                # 활성 세션 목록 조회
                project_id = arguments["project_id"]
                include_statistics = arguments.get("include_statistics", False)

                try:
                    from core.multi_session_sync import get_multi_session_manager

                    manager = get_multi_session_manager(project_id)

                    # 활성 세션 목록
                    sessions = manager.get_active_sessions(exclude_current=False)

                    # 통계 포함 여부
                    if include_statistics:
                        stats = manager.get_session_statistics()
                        result = {
                            "success": True,
                            "project_id": project_id,
                            "sessions": [s.to_dict() for s in sessions],
                            "statistics": stats,
                        }
                    else:
                        result = {
                            "success": True,
                            "project_id": project_id,
                            "sessions": [s.to_dict() for s in sessions],
                        }
                except ImportError:
                    result = {"success": False, "error": "Multi-session sync module not available."}
                except Exception as e:
                    result = {"success": False, "error": f"Failed to get sessions: {str(e)}"}

            elif name == "verify_response":
                # Phase 9.1: 자동 할루시네이션 검증
                response_text = arguments["response_text"]
                context = arguments.get("context", {})

                if not AUTO_VERIFIER_AVAILABLE:
                    result = {
                        "success": False,
                        "error": "Auto-verification system not available (Phase 9.1 not installed)",
                    }
                else:
                    try:
                        verifier = get_auto_verifier()
                        verification_result = verifier.verify_response(
                            response_text=response_text, context=context
                        )

                        # VerificationResult를 dict로 변환
                        result = {
                            "success": True,
                            "verified": verification_result.verified,
                            "grounding_score": verification_result.grounding_score,
                            "confidence_level": verification_result.confidence_level,
                            "requires_retry": verification_result.requires_retry,
                            "retry_reason": verification_result.retry_reason,
                            "claims_count": len(verification_result.claims),
                            "unverified_claims_count": len(verification_result.unverified_claims),
                            "unverified_claims": verification_result.unverified_claims,
                            # Phase 9 개선: 성능 주장 별도 표시
                            "performance_claims": verification_result.performance_claims,
                        }

                        # 재수행 필요 시 사용자 알림 메시지 포함
                        if verification_result.requires_retry:
                            result["alert_message"] = verifier.format_retry_message(
                                verification_result
                            )
                        else:
                            result["success_message"] = verifier.format_verified_message(
                                verification_result
                            )

                        logger.info(
                            f"[verify_response] 검증 완료: verified={verification_result.verified}, "
                            f"score={verification_result.grounding_score:.2f}, "
                            f"requires_retry={verification_result.requires_retry}"
                        )

                    except Exception as e:
                        import traceback

                        result = {
                            "success": False,
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                        }
                        logger.error(f"[verify_response] 에러: {e}")
                        traceback.print_exc()

            else:
                result = {"success": False, "error": f"Unknown tool: {name}"}

            # 실행 시간 계산 및 로깅
            duration_ms = (time.time() - start_time) * 1000
            log_tool_call(name, arguments, result, duration_ms)
            logger.info(f"<<< 도구 호출 완료: {name} ({duration_ms:.1f}ms)")

            # ============================================================
            # Phase 3: Post-Hook 자동 실행 (도구 실행 후 강제 처리)
            # ============================================================
            result = auto_trigger.post_hook(name, result, project_id)

            # Post-hook에서 제공하는 정보 처리
            if result.get("auto_verification_triggered"):
                logger.info(f"[POST_HOOK] Verification triggered for: {name}")
            if result.get("auto_trigger_reminder"):
                logger.info(f"[POST_HOOK] Reminder: {result['auto_trigger_reminder']}")

            # ============================================================
            # Phase 3: 캐시 무효화 자동 실행
            # ============================================================
            _trigger_cache_invalidation(name, arguments, result)

            # ============================================================
            # P1 수정: update_memory 자동 호출 시스템 (MANDATORY)
            # ============================================================
            # [2026-01-04 성능 최적화] DISABLED - 원인 분석:
            #   - 모든 도구 호출 후 update_memory를 자동 호출하여 cascading delay 발생
            #   - update_memory 내부: 878ms
            #   - wrapper layer + P1 auto call: 15-22초 (17x 느려짐)
            #   - 해결: AI가 명시적으로 update_memory를 호출하도록 변경
            # ============================================================
            # if name != "update_memory" and result.get("success"):
            #     try:
            #         project_id = arguments.get("project_id")
            #         branch_id = arguments.get("branch_id")
            #
            #         if project_id and branch_id:
            #             # update_memory 자동 호출
            #             content_parts = [f"Tool '{name}' executed successfully"]
            #
            #             # 도구별 핵심 정보 추출
            #             if result.get("message"):
            #                 content_parts.append(f"Result: {result['message']}")
            #             if result.get("branch_id") and name == "create_branch":
            #                 content_parts.append(f"Branch ID: {result['branch_id']}")
            #             if result.get("result_count") and name == "search_context":
            #                 content_parts.append(f"Found: {result['result_count']} results")
            #
            #             content = "\n".join(content_parts)
            #
            #             memory_manager.update_memory(
            #                 project_id=project_id,
            #                 branch_id=branch_id,
            #                 content=content,
            #                 role="assistant",
            #                 verified=True  # 자동 호출이므로 Phase 9 검증 생략
            #             )
            #             logger.info(f"[P1_AUTO_UPDATE_MEMORY] After '{name}': Memory updated automatically")
            #             result["__auto_memory_updated__"] = True
            #         else:
            #             logger.warning(f"[P1_AUTO_UPDATE_MEMORY] Skipped for '{name}': project_id or branch_id missing")
            #     except Exception as e:
            #         logger.error(f"[P1_AUTO_UPDATE_MEMORY] Failed after '{name}': {e}")
            #         # 실패해도 원래 결과는 반환 (치명적 오류 아님)

            # ============================================================
            # Pre-Hook 결과 병합 (cortex_injection 메시지 주입)
            # ============================================================
            if pre_hook_result.get("cortex_injection"):
                result["cortex_auto_report"] = pre_hook_result["cortex_injection"]
                logger.info("[PRE_HOOK] Cortex auto-report injected into result")

            if pre_hook_result.get("suggestions_data"):
                result["__suggestions_data__"] = pre_hook_result["suggestions_data"]
                logger.info("[PRE_HOOK] Suggestions data attached to result")

            # 결과를 TextContent로 반환
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        except Exception as e:
            import traceback

            duration_ms = (time.time() - start_time) * 1000
            error_result = {"success": False, "error": str(e), "traceback": traceback.format_exc()}
            log_tool_call(name, arguments, error_result, duration_ms)
            logger.error(f"!!! 도구 호출 실패: {name} - {str(e)}")

            # Telemetry v2.0: Track error
            if telemetry:
                try:
                    # FIXED: telemetry_base.py track_error 시그니처에 맞게 수정
                    # track_error(error: Exception, context: Dict[str, Any])
                    telemetry.client.track_error(
                        error=e,
                        context={
                            "tool_name": name,
                            "arguments": arguments,
                            "traceback": traceback.format_exc(),
                        },
                    )
                except Exception as telemetry_error:
                    logger.warning(f"Telemetry error tracking failed: {telemetry_error}")

            # DB Error Logging: Record MCP tool errors
            if WEB_DB_AVAILABLE:
                try:
                    db = get_db()
                    # user_id를 arguments에서 추출 (없으면 None)
                    user_id = None
                    # TODO: 실제 user_id를 license_key에서 조회하는 로직 추가 가능

                    db.record_error_log(
                        error_type="mcp_tool_error",
                        error_message=str(e),
                        user_id=user_id,
                        tool_name=name,
                        stack_trace=traceback.format_exc(),
                        context=json.dumps({"arguments": arguments}, ensure_ascii=False),
                        severity="error",
                    )
                except Exception as db_error:
                    logger.warning(f"DB error logging failed: {db_error}")

            return [
                TextContent(
                    type="text", text=json.dumps(error_result, ensure_ascii=False, indent=2)
                )
            ]
