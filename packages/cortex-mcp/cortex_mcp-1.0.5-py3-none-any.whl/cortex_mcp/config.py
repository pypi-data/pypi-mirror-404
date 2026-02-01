"""
Cortex MCP - Configuration Module
환경 설정, 트랙 모드 관리, Feature Flags (티어별 기능 분리)
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

# Cortex 홈 디렉토리 (프로젝트 폴더 기반 - 도구 간 맥락 공유 가능)
# 우선순위: CORTEX_PROJECT_PATH 환경변수 > 현재 작업 디렉토리 > 홈 디렉토리
def _get_cortex_home() -> str:
    """프로젝트 기반 Cortex 홈 디렉토리 결정"""
    # 1. 환경변수로 명시적 지정
    if os.getenv("CORTEX_PROJECT_PATH"):
        return str(Path(os.getenv("CORTEX_PROJECT_PATH")) / ".cortex")

    # 2. 현재 작업 디렉토리에서 프로젝트 루트 탐색
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        # .git, pyproject.toml, package.json 등 프로젝트 마커 확인
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return str(parent / ".cortex")

    # 3. 폴백: 홈 디렉토리 (기존 방식)
    return str(Path.home() / ".cortex")

CORTEX_HOME = _get_cortex_home()

# 라이센스키 (환경변수에서 로드)
LICENSE_KEY = os.getenv("CORTEX_LICENSE_KEY")


class TrackMode(Enum):
    """비즈니스 트랙 모드"""

    TRACK_A = "global_saas"  # Global SaaS (일반 사용자)
    TRACK_B = "legal_vertical"  # Legal/Vertical (고보안 시장)


class Tier(Enum):
    """사용자 티어 (v2.1: Free/Paid/Enterprise 3-tier)"""

    FREE = "free"
    PAID = "paid"  # 구 Pro/Premium 통합
    ENTERPRISE = "enterprise"

    def _tier_order(self) -> int:
        """티어 순서 반환 (비교 연산용)"""
        order = {"free": 0, "paid": 1, "enterprise": 2}
        return order.get(self.value, 0)

    def __lt__(self, other):
        if isinstance(other, Tier):
            return self._tier_order() < other._tier_order()
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Tier):
            return self._tier_order() <= other._tier_order()
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Tier):
            return self._tier_order() > other._tier_order()
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Tier):
            return self._tier_order() >= other._tier_order()
        return NotImplemented


@dataclass
class FeatureFlags:
    """
    티어별 기능 플래그 (v2.1: 3-tier 모델)

    Feature Flags 정책:
    - Free: 기본 기능만, 제한적
    - Paid: 모든 고급 기능 (구 Pro/Premium 통합)
    - Enterprise: Paid + 시맨틱 웹 + Multi-PC 동기화 + 우선 지원
    """

    # 핵심 기능 플래그
    ontology_enabled: bool = False
    reference_history_enabled: bool = False
    smart_context_enabled: bool = False
    relationship_graph_enabled: bool = False  # Context 관계 추적 (Pro+)
    semantic_web_enabled: bool = False
    multi_pc_sync: bool = False
    multi_session_enabled: bool = False  # 병렬 개발 지원 (Pro+)
    hallucination_detection_enabled: bool = False  # Phase 9 할루시네이션 검증 (기본값: 비활성화)
    fuzzy_prompt_enabled: bool = False  # 퍼지 검색 및 힌트 생성 (Pro+)

    # 제한 설정
    max_branches: int = 5
    max_rag_searches_per_day: int = 20  # -1 = unlimited
    max_contexts_per_branch: int = 50  # -1 = unlimited

    # 자동화 수준
    auto_mode: str = "manual"  # "manual", "semi_auto", "full_auto"

    # 확인 필요 여부 (클릭 세금)
    branching_confirm_required: bool = True
    summary_confirm_required: bool = True
    context_load_confirm_required: bool = True
    node_grouping_confirm_required: bool = True  # Issue #2: 노드 자동 그룹핑

    # 추가 기능
    cloud_backup_enabled: bool = False
    audit_dashboard_enabled: bool = False
    priority_support: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "ontology_enabled": self.ontology_enabled,
            "reference_history_enabled": self.reference_history_enabled,
            "smart_context_enabled": self.smart_context_enabled,
            "relationship_graph_enabled": self.relationship_graph_enabled,
            "semantic_web_enabled": self.semantic_web_enabled,
            "multi_pc_sync": self.multi_pc_sync,
            "multi_session_enabled": self.multi_session_enabled,
            "hallucination_detection_enabled": self.hallucination_detection_enabled,
            "fuzzy_prompt_enabled": self.fuzzy_prompt_enabled,
            "max_branches": self.max_branches,
            "max_rag_searches_per_day": self.max_rag_searches_per_day,
            "max_contexts_per_branch": self.max_contexts_per_branch,
            "auto_mode": self.auto_mode,
            "branching_confirm_required": self.branching_confirm_required,
            "summary_confirm_required": self.summary_confirm_required,
            "context_load_confirm_required": self.context_load_confirm_required,
            "node_grouping_confirm_required": self.node_grouping_confirm_required,
            "cloud_backup_enabled": self.cloud_backup_enabled,
            "audit_dashboard_enabled": self.audit_dashboard_enabled,
            "priority_support": self.priority_support,
        }


# 티어별 기본 Feature Flags (v2.1: 3-tier)
TIER_FLAGS: Dict[Tier, FeatureFlags] = {
    Tier.FREE: FeatureFlags(
        ontology_enabled=False,
        reference_history_enabled=False,
        smart_context_enabled=False,
        relationship_graph_enabled=False,  # Paid 이상
        semantic_web_enabled=False,
        multi_pc_sync=False,
        multi_session_enabled=False,  # Paid 이상
        hallucination_detection_enabled=False,  # 기본값: 비활성화
        fuzzy_prompt_enabled=False,  # Free: 비활성화
        max_branches=5,
        max_rag_searches_per_day=20,
        max_contexts_per_branch=50,
        auto_mode="manual",
        branching_confirm_required=True,
        summary_confirm_required=True,
        context_load_confirm_required=True,
        node_grouping_confirm_required=True,  # Free: 확인 필요
        cloud_backup_enabled=False,
        audit_dashboard_enabled=False,
        priority_support=False,
    ),
    Tier.PAID: FeatureFlags(
        # 모든 고급 기능 활성화 (구 Pro/Premium 통합)
        ontology_enabled=True,
        reference_history_enabled=True,
        smart_context_enabled=True,
        relationship_graph_enabled=True,  # Context 관계 추적
        semantic_web_enabled=False,  # Enterprise 전용
        multi_pc_sync=False,  # Enterprise 전용
        multi_session_enabled=True,  # 병렬 개발 지원
        hallucination_detection_enabled=False,  # 기본값: 비활성화 (성능 우선)
        fuzzy_prompt_enabled=True,  # Paid: 활성화 (퍼지 검색 및 힌트 생성)
        max_branches=-1,  # unlimited
        max_rag_searches_per_day=-1,  # unlimited
        max_contexts_per_branch=-1,  # unlimited
        auto_mode="semi_auto",  # 확신도 기반 자동 제안
        branching_confirm_required=False,  # 자동 생성 (보고만)
        summary_confirm_required=False,
        context_load_confirm_required=False,
        node_grouping_confirm_required=False,  # Paid: 자동 생성
        cloud_backup_enabled=True,
        audit_dashboard_enabled=True,
        priority_support=False,  # Enterprise 전용
    ),
    Tier.ENTERPRISE: FeatureFlags(
        ontology_enabled=True,
        reference_history_enabled=True,
        smart_context_enabled=True,
        relationship_graph_enabled=True,  # Context 관계 추적
        semantic_web_enabled=True,  # Enterprise 전용
        multi_pc_sync=True,
        multi_session_enabled=True,  # 병렬 개발 지원
        hallucination_detection_enabled=False,  # 기본값: 비활성화 (성능 우선)
        fuzzy_prompt_enabled=True,  # Enterprise: 활성화 (퍼지 검색 및 힌트 생성)
        max_branches=-1,  # unlimited
        max_rag_searches_per_day=-1,
        max_contexts_per_branch=-1,
        auto_mode="full_auto",  # Zero-Effort
        branching_confirm_required=False,  # Zero-Effort
        summary_confirm_required=False,
        context_load_confirm_required=False,
        node_grouping_confirm_required=False,  # Enterprise: 자동 생성
        cloud_backup_enabled=True,
        audit_dashboard_enabled=True,
        priority_support=True,
    ),
}


def get_tier_flags(tier: Tier) -> FeatureFlags:
    """티어에 해당하는 Feature Flags 반환"""
    return TIER_FLAGS.get(tier, TIER_FLAGS[Tier.FREE])


def check_feature(feature_name: str, tier: Optional[Tier] = None) -> bool:
    """
    런타임에서 기능 사용 가능 여부 확인

    Args:
        feature_name: 기능 이름 (ontology_enabled, semantic_web_enabled 등)
        tier: 사용자 티어 (None이면 현재 설정된 티어 사용)

    Returns:
        기능 사용 가능 여부
    """
    if tier is None:
        tier = config.current_tier

    flags = get_tier_flags(tier)
    return getattr(flags, feature_name, False)


@dataclass
class CortexConfig:
    """Cortex 설정 클래스 (v2.1: Feature Flags 지원)"""

    # 기본 경로
    base_dir: Path = Path.home() / ".cortex"
    memory_dir: Path = None
    logs_dir: Path = None

    # 트랙 모드
    track_mode: TrackMode = TrackMode.TRACK_A

    # 사용자 티어 (v2.1: 3-tier 모델)
    current_tier: Tier = Tier.FREE  # 기본값: Paid (개발/테스트용)

    # 메모리 관리
    max_context_size_kb: int = 100  # 자동 요약 트리거 임계치
    summary_target_size_kb: int = 20  # 요약 후 목표 크기

    # RAG 설정
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    chroma_collection_name: str = "cortex_memory"
    search_top_k: int = 5

    # 클라우드 동기화
    google_drive_folder: str = "Cortex_Backup"
    auto_sync_enabled: bool = True  # 자동 동기화 활성화
    auto_sync_interval_minutes: int = 5  # 자동 동기화 주기 (분)

    # 암호화 (Track B)
    encryption_enabled: bool = False

    # Smart Context 설정 (v2.0)
    max_active_branches: int = 3  # 최대 동시 활성 브랜치 수
    auto_compress_minutes: int = 30  # 자동 압축 시간 (분)
    lazy_load_enabled: bool = True  # Lazy Loading 활성화

    # 백업 설정
    backups_dir: Path = None
    max_local_versions: int = 30  # 로컬 버전 히스토리 수

    # Feature Flags (런타임에 설정됨)
    _feature_flags: FeatureFlags = None

    def __post_init__(self):
        """초기화 후 경로 설정"""
        if self.memory_dir is None:
            self.memory_dir = self.base_dir / "memory"
        if self.logs_dir is None:
            self.logs_dir = self.base_dir / "logs"
        if self.backups_dir is None:
            self.backups_dir = self.base_dir / "backups"

        # Track B 모드시 암호화 활성화
        if self.track_mode == TrackMode.TRACK_B:
            self.encryption_enabled = True

        # Feature Flags 초기화
        self._feature_flags = get_tier_flags(self.current_tier)

    @property
    def cortex_home(self) -> Path:
        """base_dir의 alias (호환성 유지)"""
        return self.base_dir

    @property
    def feature_flags(self) -> FeatureFlags:
        """현재 티어의 Feature Flags 반환"""
        if self._feature_flags is None:
            self._feature_flags = get_tier_flags(self.current_tier)
        return self._feature_flags

    def set_tier(self, tier: Tier) -> None:
        """티어 변경 및 Feature Flags 업데이트"""
        self.current_tier = tier
        self._feature_flags = get_tier_flags(tier)

    def is_feature_enabled(self, feature_name: str) -> bool:
        """기능 활성화 여부 확인"""
        return getattr(self.feature_flags, feature_name, False)

    def get_limit(self, limit_name: str) -> int:
        """제한값 조회 (-1은 무제한)"""
        return getattr(self.feature_flags, limit_name, 0)

    def ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def get_tier_info(self) -> Dict[str, Any]:
        """현재 티어 정보 반환"""
        return {
            "tier": self.current_tier.value,
            "track_mode": self.track_mode.value,
            "feature_flags": self.feature_flags.to_dict(),
        }


# 전역 설정 인스턴스
config = CortexConfig()
