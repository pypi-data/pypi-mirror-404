"""
Cortex MCP - Pay Attention System v1.0

세션 내 LLM Attention 보존 시스템

문제:
- LLM은 긴 대화에서 초기 내용에 대한 attention이 약화됨
- "정리해줘" 요청 시 a, a', a'', b, b' 중 a, b만 반환
- "아까 말했잖아" 류의 참조 실패

해결:
- Topic-Version 트래킹: 동일 주제의 버전 이력 관리
- Attention Injector: 답변 전 관련 맥락 자동 주입
- Completeness Validator: 요약 시 누락 검증
- Consistency Checker: 모순 탐지

통합 모듈:
- ontology_engine: 주제 분류
- semantic_web: 관계 추론
- reference_history: 참조 이력
- fuzzy_prompt: 유사 검색
"""

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# 로컬 import
try:
    from ..config import config
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import config

from .alpha_logger import LogModule, get_alpha_logger

# =====================================================================
# 통합 모듈 Import (v1.1 - 완전 통합)
# =====================================================================

# 온톨로지 엔진 (주제 분류)
try:
    from .ontology_engine import OntologyEngine

    ONTOLOGY_AVAILABLE = True
except ImportError:
    ONTOLOGY_AVAILABLE = False
    OntologyEngine = None

# 시맨틱 웹 엔진 (관계 추론)
try:
    from .semantic_web import SemanticWebEngine, RelationType

    SEMANTIC_WEB_AVAILABLE = True
except ImportError:
    SEMANTIC_WEB_AVAILABLE = False
    SemanticWebEngine = None
    RelationType = None

# 참조 이력 (함께 참조된 맥락 추적)
try:
    from .reference_history import ReferenceHistory

    REFERENCE_HISTORY_AVAILABLE = True
except ImportError:
    REFERENCE_HISTORY_AVAILABLE = False
    ReferenceHistory = None

# 퍼지 프롬프트 (유사 검색 및 힌트 생성)
try:
    from .fuzzy_prompt import FuzzyPromptIntegrator, get_fuzzy_prompt_integrator

    FUZZY_PROMPT_AVAILABLE = True
except ImportError:
    FUZZY_PROMPT_AVAILABLE = False
    FuzzyPromptIntegrator = None
    get_fuzzy_prompt_integrator = None


class TriggerType(Enum):
    """Attention Injection 트리거 타입"""

    REFERENTIAL_QUERY = "referential_query"  # "아까", "그거", "이전에" 등
    LONG_CONVERSATION = "long_conversation"  # 20턴+ 대화
    MULTI_TOPIC = "multi_topic"  # 3개+ 주제 전환
    MODIFICATION_REQUEST = "modification_request"  # "바꿔", "수정해" 등
    SUMMARY_REQUEST = "summary_request"  # "정리해", "요약해" 등
    DEPENDENCY_CHECK = "dependency_check"  # "그거 기반으로" 등
    COMPARISON_REQUEST = "comparison_request"  # "비교해", "뭐가 달라" 등


class VersionStatus(Enum):
    """Topic Version 상태"""

    INITIAL = "initial"  # 최초 버전
    UPDATED = "updated"  # 업데이트됨
    SUPERSEDED = "superseded"  # 대체됨 (더 이상 최신 아님)
    FINAL = "final"  # 최종 확정


@dataclass
class TopicVersion:
    """토픽의 버전 정보"""

    version_id: str
    topic_id: str
    version_number: int
    content: str
    summary: str
    status: VersionStatus
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    turn_number: int = 0
    keywords: List[str] = field(default_factory=list)
    parent_version: Optional[str] = None  # 이전 버전 ID
    changes_from_parent: Optional[str] = None  # 변경 내용 요약

    def to_dict(self) -> Dict:
        return {
            "version_id": self.version_id,
            "topic_id": self.topic_id,
            "version_number": self.version_number,
            "content": self.content,
            "summary": self.summary,
            "status": self.status.value,
            "created_at": self.created_at,
            "turn_number": self.turn_number,
            "keywords": self.keywords,
            "parent_version": self.parent_version,
            "changes_from_parent": self.changes_from_parent,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TopicVersion":
        return cls(
            version_id=data["version_id"],
            topic_id=data["topic_id"],
            version_number=data["version_number"],
            content=data["content"],
            summary=data["summary"],
            status=VersionStatus(data["status"]),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            turn_number=data.get("turn_number", 0),
            keywords=data.get("keywords", []),
            parent_version=data.get("parent_version"),
            changes_from_parent=data.get("changes_from_parent"),
        )


@dataclass
class Topic:
    """대화 주제"""

    topic_id: str
    name: str
    category: str  # 온톨로지 카테고리
    versions: List[TopicVersion] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    first_mentioned_turn: int = 0
    last_updated_turn: int = 0
    mention_count: int = 0

    def get_latest_version(self) -> Optional[TopicVersion]:
        """최신 버전 반환"""
        if not self.versions:
            return None
        # 버전 번호 기준 최신
        return max(self.versions, key=lambda v: v.version_number)

    def get_all_versions_summary(self) -> str:
        """모든 버전의 변경 이력 요약"""
        if not self.versions:
            return ""

        lines = [f"[{self.name}] 변경 이력:"]
        for v in sorted(self.versions, key=lambda x: x.version_number):
            status_mark = "(*)" if v.status == VersionStatus.FINAL else ""
            lines.append(f"  v{v.version_number}{status_mark}: {v.summary}")
            if v.changes_from_parent:
                lines.append(f"    -> 변경: {v.changes_from_parent}")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "topic_id": self.topic_id,
            "name": self.name,
            "category": self.category,
            "versions": [v.to_dict() for v in self.versions],
            "related_topics": self.related_topics,
            "first_mentioned_turn": self.first_mentioned_turn,
            "last_updated_turn": self.last_updated_turn,
            "mention_count": self.mention_count,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Topic":
        topic = cls(
            topic_id=data["topic_id"],
            name=data["name"],
            category=data["category"],
            related_topics=data.get("related_topics", []),
            first_mentioned_turn=data.get("first_mentioned_turn", 0),
            last_updated_turn=data.get("last_updated_turn", 0),
            mention_count=data.get("mention_count", 0),
        )
        topic.versions = [TopicVersion.from_dict(v) for v in data.get("versions", [])]
        return topic


@dataclass
class InjectionContext:
    """주입할 컨텍스트"""

    trigger_type: TriggerType
    topics: List[Topic]
    versions_to_inject: List[TopicVersion]
    injection_text: str
    confidence: float
    reason: str


@dataclass
class CompletenessReport:
    """완전성 검증 리포트"""

    is_complete: bool
    missing_topics: List[str]
    missing_versions: List[str]
    coverage_ratio: float
    suggestion: str


@dataclass
class ConsistencyReport:
    """일관성 검증 리포트"""

    is_consistent: bool
    conflicts: List[Dict]  # {"topic": str, "old": str, "new": str, "type": str}
    warnings: List[str]


class PayAttentionEngine:
    """
    Pay Attention 시스템 메인 엔진

    세션 내 대화의 attention을 보존하고
    LLM의 기억 누락을 방지합니다.
    """

    # 참조 패턴 (한국어 + 영어)
    REFERENTIAL_PATTERNS = [
        r"아까",
        r"이전에",
        r"그거",
        r"그것",
        r"그게",
        r"방금",
        r"앞에서",
        r"위에서",
        r"말했",
        r"언급",
        r"before",
        r"earlier",
        r"previous",
        r"that",
        r"mentioned",
    ]

    # 요약 요청 패턴
    SUMMARY_PATTERNS = [
        r"정리",
        r"요약",
        r"종합",
        r"전체.*보여",
        r"다.*알려",
        r"summarize",
        r"summary",
        r"recap",
        r"overview",
    ]

    # 수정 요청 패턴
    MODIFICATION_PATTERNS = [
        r"바꿔",
        r"수정",
        r"변경",
        r"업데이트",
        r"고쳐",
        r"change",
        r"modify",
        r"update",
        r"fix",
        r"edit",
    ]

    # 비교 요청 패턴
    COMPARISON_PATTERNS = [
        r"비교",
        r"차이",
        r"다른",
        r"뭐가.*달라",
        r"어떻게.*바뀌",
        r"compare",
        r"difference",
        r"differ",
        r"what.*changed",
    ]

    def __init__(self, project_id: str, branch_id: str, enabled: bool = True):
        """
        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            enabled: 기능 활성화 여부
        """
        self.project_id = project_id
        self.branch_id = branch_id
        self.enabled = enabled
        self.logger = get_alpha_logger()

        # 저장 경로
        self.base_path = Path(config.memory_dir) / project_id / "contexts" / branch_id
        self.topics_path = self.base_path / "topics"
        self.session_log_path = self.base_path / "_session_attention.json"

        # 메모리 상태
        self.topics: Dict[str, Topic] = {}
        self.current_turn: int = 0
        self.session_start: str = datetime.now(timezone.utc).isoformat()

        # 트리거 히스토리
        self.trigger_history: List[Dict] = []

        # =====================================================================
        # 통합 모듈 초기화 (v1.1 - 완전 통합)
        # =====================================================================
        self.ontology_engine = None
        self.semantic_web_engine = None
        self.reference_history = None
        self.fuzzy_prompt = None

        self._init_integration_modules()

        # 초기화
        self._load_session()

    def _load_session(self) -> None:
        """세션 데이터 로드"""
        if not self.session_log_path.exists():
            return

        try:
            with open(self.session_log_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.current_turn = data.get("current_turn", 0)
            self.session_start = data.get("session_start", self.session_start)
            self.trigger_history = data.get("trigger_history", [])

            # 토픽 로드
            for topic_data in data.get("topics", []):
                topic = Topic.from_dict(topic_data)
                self.topics[topic.topic_id] = topic

        except Exception as e:
            self.logger.log(
                module=LogModule.PAY_ATTENTION, action="load_session", success=False, error=str(e)
            )

    def _init_integration_modules(self) -> None:
        """
        통합 모듈 초기화 (v1.1)

        4개 모듈과 연동하여 더 정확한 Attention Context 생성:
        - ontology_engine: 주제 분류 정확도 향상
        - semantic_web: 관계 기반 토픽 연결
        - reference_history: 참조 이력 기반 추천
        - fuzzy_prompt: 유사 검색 및 힌트 생성
        """
        # 온톨로지 엔진 초기화
        if ONTOLOGY_AVAILABLE:
            try:
                self.ontology_engine = OntologyEngine(ontology_enabled=True)
                self.logger.log(
                    module=LogModule.PAY_ATTENTION,
                    action="init_ontology",
                    success=True,
                )
            except Exception as e:
                self.logger.log(
                    module=LogModule.PAY_ATTENTION,
                    action="init_ontology",
                    success=False,
                    error=str(e),
                )

        # 시맨틱 웹 엔진 초기화
        if SEMANTIC_WEB_AVAILABLE:
            try:
                self.semantic_web_engine = SemanticWebEngine(
                    project_id=self.project_id, enabled=True
                )
                self.logger.log(
                    module=LogModule.PAY_ATTENTION,
                    action="init_semantic_web",
                    success=True,
                )
            except Exception as e:
                self.logger.log(
                    module=LogModule.PAY_ATTENTION,
                    action="init_semantic_web",
                    success=False,
                    error=str(e),
                )

        # 참조 이력 초기화
        if REFERENCE_HISTORY_AVAILABLE:
            try:
                self.reference_history = ReferenceHistory(project_id=self.project_id)
                self.logger.log(
                    module=LogModule.PAY_ATTENTION,
                    action="init_reference_history",
                    success=True,
                )
            except Exception as e:
                self.logger.log(
                    module=LogModule.PAY_ATTENTION,
                    action="init_reference_history",
                    success=False,
                    error=str(e),
                )

        # 퍼지 프롬프트 초기화
        if FUZZY_PROMPT_AVAILABLE and get_fuzzy_prompt_integrator:
            try:
                self.fuzzy_prompt = get_fuzzy_prompt_integrator()
                self.logger.log(
                    module=LogModule.PAY_ATTENTION,
                    action="init_fuzzy_prompt",
                    success=True,
                )
            except Exception as e:
                self.logger.log(
                    module=LogModule.PAY_ATTENTION,
                    action="init_fuzzy_prompt",
                    success=False,
                    error=str(e),
                )

    def _get_related_topics_from_semantic_web(
        self, topic_names: List[str]
    ) -> List[str]:
        """
        semantic_web에서 관련 토픽 조회

        Args:
            topic_names: 기준 토픽 이름 목록

        Returns:
            관련된 토픽 이름 목록
        """
        if not self.semantic_web_engine:
            return []

        related_topics = []
        try:
            for topic_name in topic_names:
                # semantic_web에서 관련 컨텍스트 조회
                suggestions = self.semantic_web_engine.suggest_related_contexts(
                    context_id=topic_name,
                    max_suggestions=3,
                )
                if suggestions.get("success") and suggestions.get("suggestions"):
                    for suggestion in suggestions["suggestions"]:
                        related_name = suggestion.get("context_id", "")
                        if related_name and related_name not in topic_names:
                            related_topics.append(related_name)

            self.logger.log(
                module=LogModule.PAY_ATTENTION,
                action="get_related_topics",
                success=True,
                metadata={"input_count": len(topic_names), "related_count": len(related_topics)},
            )
        except Exception as e:
            self.logger.log(
                module=LogModule.PAY_ATTENTION,
                action="get_related_topics",
                success=False,
                error=str(e),
            )

        return related_topics[:5]  # 최대 5개

    def _get_co_referenced_topics(self, topic_names: List[str]) -> Dict[str, float]:
        """
        reference_history에서 함께 참조된 토픽 조회

        Args:
            topic_names: 기준 토픽 이름 목록

        Returns:
            {토픽이름: 신뢰도} 딕셔너리
        """
        if not self.reference_history:
            return {}

        co_referenced = {}
        try:
            # 키워드 기반으로 추천 조회
            result = self.reference_history.suggest_contexts(
                task_keywords=topic_names,
                max_suggestions=5,
            )
            if result.get("success") and result.get("suggestions"):
                for suggestion in result["suggestions"]:
                    context_id = suggestion.get("context_id", "")
                    confidence = suggestion.get("confidence", 0.5)
                    if context_id and context_id not in topic_names:
                        co_referenced[context_id] = confidence

            self.logger.log(
                module=LogModule.PAY_ATTENTION,
                action="get_co_referenced",
                success=True,
                metadata={"input_count": len(topic_names), "co_ref_count": len(co_referenced)},
            )
        except Exception as e:
            self.logger.log(
                module=LogModule.PAY_ATTENTION,
                action="get_co_referenced",
                success=False,
                error=str(e),
            )

        return co_referenced

    def _generate_fuzzy_context(self, user_message: str) -> Optional[str]:
        """
        fuzzy_prompt로 퍼지 컨텍스트 생성

        Args:
            user_message: 사용자 메시지

        Returns:
            퍼지 컨텍스트 문자열 (없으면 None)
        """
        if not self.fuzzy_prompt:
            return None

        try:
            # 퍼지 분류 및 힌트 생성
            context = self.fuzzy_prompt.generate_context(user_message)
            if context:
                fuzzy_text = context.to_system_prompt()
                self.logger.log(
                    module=LogModule.PAY_ATTENTION,
                    action="generate_fuzzy_context",
                    success=True,
                )
                return fuzzy_text
        except Exception as e:
            self.logger.log(
                module=LogModule.PAY_ATTENTION,
                action="generate_fuzzy_context",
                success=False,
                error=str(e),
            )

        return None

    def _classify_with_ontology(self, content: str) -> Optional[Dict[str, Any]]:
        """
        ontology_engine으로 내용 분류

        Args:
            content: 분류할 내용

        Returns:
            분류 결과 딕셔너리 (없으면 None)
        """
        if not self.ontology_engine:
            return None

        try:
            result = self.ontology_engine.classify(content)
            if result.get("category"):
                self.logger.log(
                    module=LogModule.PAY_ATTENTION,
                    action="classify_ontology",
                    success=True,
                    metadata={"category": result.get("category")},
                )
                return result
        except Exception as e:
            self.logger.log(
                module=LogModule.PAY_ATTENTION,
                action="classify_ontology",
                success=False,
                error=str(e),
            )

        return None

    def _save_session(self) -> None:
        """세션 데이터 저장"""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)

            data = {
                "project_id": self.project_id,
                "branch_id": self.branch_id,
                "session_start": self.session_start,
                "current_turn": self.current_turn,
                "topics": [t.to_dict() for t in self.topics.values()],
                "trigger_history": self.trigger_history[-100:],  # 최근 100개만 유지
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            with open(self.session_log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.log(
                module=LogModule.PAY_ATTENTION, action="save_session", success=False, error=str(e)
            )

    def track_message(
        self,
        message: str,
        role: str,  # "user" or "assistant"
        detected_topics: Optional[List[str]] = None,
        topic_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        메시지 추적 및 토픽/버전 업데이트

        Args:
            message: 메시지 내용
            role: 역할 (user/assistant)
            detected_topics: 감지된 토픽 이름들
            topic_category: 온톨로지 카테고리

        Returns:
            트래킹 결과
        """
        start_time = time.time()

        if not self.enabled:
            return {"success": False, "reason": "disabled"}

        self.current_turn += 1

        # 토픽 감지 및 업데이트
        if detected_topics:
            for topic_name in detected_topics:
                self._update_topic(
                    topic_name=topic_name,
                    content=message,
                    category=topic_category or "general",
                    turn_number=self.current_turn,
                )

        self._save_session()

        latency_ms = (time.time() - start_time) * 1000
        self.logger.log(
            module=LogModule.PAY_ATTENTION,
            action="track_message",
            success=True,
            latency_ms=latency_ms,
            metadata={
                "turn": self.current_turn,
                "role": role,
                "topics_updated": detected_topics or [],
            },
        )

        return {
            "success": True,
            "turn": self.current_turn,
            "topics_tracked": len(detected_topics) if detected_topics else 0,
        }

    def _update_topic(
        self, topic_name: str, content: str, category: str, turn_number: int
    ) -> Topic:
        """토픽 업데이트 (버전 생성)"""
        topic_id = self._generate_topic_id(topic_name)

        if topic_id not in self.topics:
            # 새 토픽 생성
            topic = Topic(
                topic_id=topic_id,
                name=topic_name,
                category=category,
                first_mentioned_turn=turn_number,
                last_updated_turn=turn_number,
                mention_count=1,
            )
            self.topics[topic_id] = topic
        else:
            topic = self.topics[topic_id]
            topic.mention_count += 1
            topic.last_updated_turn = turn_number

        # 새 버전 생성
        version_number = len(topic.versions) + 1
        parent_version = topic.get_latest_version()

        # 이전 버전 상태 업데이트
        if parent_version:
            parent_version.status = VersionStatus.SUPERSEDED

        new_version = TopicVersion(
            version_id=f"{topic_id}_v{version_number}",
            topic_id=topic_id,
            version_number=version_number,
            content=content[:1000],  # 내용 제한
            summary=self._generate_summary(content),
            status=VersionStatus.UPDATED if version_number > 1 else VersionStatus.INITIAL,
            turn_number=turn_number,
            keywords=self._extract_keywords(content),
            parent_version=parent_version.version_id if parent_version else None,
            changes_from_parent=(
                self._detect_changes(parent_version, content) if parent_version else None
            ),
        )

        topic.versions.append(new_version)
        return topic

    def _generate_topic_id(self, name: str) -> str:
        """토픽 ID 생성"""
        # 한글/영어 모두 지원
        clean_name = re.sub(r"[^a-zA-Z0-9가-힣]", "_", name.lower())
        return f"topic_{clean_name}"

    def _generate_summary(self, content: str) -> str:
        """내용 요약 생성 (로컬, Zero-Trust)"""
        # 간단한 추출적 요약: 첫 문장 + 키워드
        sentences = re.split(r"[.!?。]", content)
        first_sentence = sentences[0].strip() if sentences else content[:100]

        if len(first_sentence) > 100:
            first_sentence = first_sentence[:100] + "..."

        return first_sentence

    def _extract_keywords(self, content: str) -> List[str]:
        """키워드 추출"""
        # 간단한 키워드 추출 (명사 중심)
        words = re.findall(r"[a-zA-Z가-힣]{2,}", content)
        # 빈도수 기반 상위 5개
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:5]]

    def _detect_changes(self, parent_version: TopicVersion, new_content: str) -> str:
        """이전 버전 대비 변경 사항 감지"""
        if not parent_version:
            return "초기 버전"

        parent_keywords = set(parent_version.keywords)
        new_keywords = set(self._extract_keywords(new_content))

        added = new_keywords - parent_keywords
        removed = parent_keywords - new_keywords

        changes = []
        if added:
            changes.append(f"추가: {', '.join(list(added)[:3])}")
        if removed:
            changes.append(f"제거: {', '.join(list(removed)[:3])}")

        return "; ".join(changes) if changes else "내용 업데이트"

    def detect_trigger(self, user_message: str) -> Optional[TriggerType]:
        """
        사용자 메시지에서 Attention Injection 트리거 감지

        Args:
            user_message: 사용자 메시지

        Returns:
            감지된 트리거 타입 (없으면 None)
        """
        if not self.enabled:
            return None

        message_lower = user_message.lower()

        # 수정 요청 감지 (우선순위 높음 - "그거 수정해줘" 처리)
        for pattern in self.MODIFICATION_PATTERNS:
            if re.search(pattern, message_lower):
                return TriggerType.MODIFICATION_REQUEST

        # 요약 요청 감지
        for pattern in self.SUMMARY_PATTERNS:
            if re.search(pattern, message_lower):
                return TriggerType.SUMMARY_REQUEST

        # 비교 요청 감지
        for pattern in self.COMPARISON_PATTERNS:
            if re.search(pattern, message_lower):
                return TriggerType.COMPARISON_REQUEST

        # 참조 쿼리 감지 (마지막 - 일반적인 참조)
        for pattern in self.REFERENTIAL_PATTERNS:
            if re.search(pattern, message_lower):
                return TriggerType.REFERENTIAL_QUERY

        # 긴 대화 감지
        if self.current_turn >= 20:
            return TriggerType.LONG_CONVERSATION

        # 다중 토픽 감지
        if len(self.topics) >= 3:
            return TriggerType.MULTI_TOPIC

        return None

    def inject_attention_context(
        self, trigger_type: TriggerType, user_message: str, max_topics: int = 5
    ) -> InjectionContext:
        """
        트리거에 맞는 Attention Context 생성

        Args:
            trigger_type: 트리거 타입
            user_message: 사용자 메시지
            max_topics: 최대 주입 토픽 수

        Returns:
            InjectionContext 객체
        """
        start_time = time.time()

        relevant_topics: List[Topic] = []
        versions_to_inject: List[TopicVersion] = []

        if trigger_type == TriggerType.SUMMARY_REQUEST:
            # 모든 토픽의 모든 버전 포함
            relevant_topics = list(self.topics.values())
            for topic in relevant_topics[:max_topics]:
                versions_to_inject.extend(topic.versions)
            reason = "요약 요청: 모든 토픽 및 버전 이력 포함"

        elif trigger_type == TriggerType.REFERENTIAL_QUERY:
            # 최근 언급된 토픽 + 모든 버전
            sorted_topics = sorted(
                self.topics.values(), key=lambda t: t.last_updated_turn, reverse=True
            )
            relevant_topics = sorted_topics[:max_topics]
            for topic in relevant_topics:
                versions_to_inject.extend(topic.versions)
            reason = "참조 쿼리: 최근 토픽 및 변경 이력 포함"

        elif trigger_type == TriggerType.MODIFICATION_REQUEST:
            # 관련 토픽 찾기 (키워드 매칭)
            message_words = set(self._extract_keywords(user_message))
            for topic in self.topics.values():
                latest = topic.get_latest_version()
                if latest and message_words & set(latest.keywords):
                    relevant_topics.append(topic)
                    versions_to_inject.extend(topic.versions)
            reason = "수정 요청: 관련 토픽 및 변경 이력 포함"

        elif trigger_type == TriggerType.COMPARISON_REQUEST:
            # 모든 버전 이력 필요
            relevant_topics = list(self.topics.values())[:max_topics]
            for topic in relevant_topics:
                versions_to_inject.extend(topic.versions)
            reason = "비교 요청: 버전 간 변경사항 포함"

        elif trigger_type in (TriggerType.LONG_CONVERSATION, TriggerType.MULTI_TOPIC):
            # 주요 토픽 요약
            sorted_topics = sorted(
                self.topics.values(), key=lambda t: t.mention_count, reverse=True
            )
            relevant_topics = sorted_topics[:max_topics]
            for topic in relevant_topics:
                # 최신 버전만
                latest = topic.get_latest_version()
                if latest:
                    versions_to_inject.append(latest)
            reason = "긴 대화/다중 토픽: 주요 토픽 최신 상태 포함"

        else:
            reason = "기본 주입"

        # =====================================================================
        # 통합 모듈 활용 (v1.1 - 완전 통합)
        # =====================================================================

        # 1. semantic_web: 관련 토픽 확장
        topic_names = [t.name for t in relevant_topics]
        related_from_semantic = self._get_related_topics_from_semantic_web(topic_names)

        # 관련 토픽을 기존 topics에서 찾아 추가
        for related_name in related_from_semantic:
            topic_id = self._generate_topic_id(related_name)
            if topic_id in self.topics and self.topics[topic_id] not in relevant_topics:
                relevant_topics.append(self.topics[topic_id])
                latest = self.topics[topic_id].get_latest_version()
                if latest:
                    versions_to_inject.append(latest)

        # 2. reference_history: 함께 참조된 토픽 우선순위 조정
        co_referenced = self._get_co_referenced_topics(topic_names)
        if co_referenced:
            # 신뢰도 높은 순으로 정렬하여 토픽 추가
            for co_ref_name, confidence_score in sorted(
                co_referenced.items(), key=lambda x: x[1], reverse=True
            ):
                topic_id = self._generate_topic_id(co_ref_name)
                if topic_id in self.topics and self.topics[topic_id] not in relevant_topics:
                    if len(relevant_topics) < max_topics + 2:  # 약간의 여유
                        relevant_topics.append(self.topics[topic_id])
                        latest = self.topics[topic_id].get_latest_version()
                        if latest:
                            versions_to_inject.append(latest)

        # 3. fuzzy_prompt: 퍼지 컨텍스트 생성
        fuzzy_context = self._generate_fuzzy_context(user_message)

        # 4. ontology: 분류 정보 추가
        ontology_info = self._classify_with_ontology(user_message)

        # max_topics 제한 적용
        relevant_topics = relevant_topics[:max_topics]

        # reason 업데이트 (통합 정보 추가)
        integration_info = []
        if related_from_semantic:
            integration_info.append(f"시맨틱관계 {len(related_from_semantic)}개")
        if co_referenced:
            integration_info.append(f"참조이력 {len(co_referenced)}개")
        if fuzzy_context:
            integration_info.append("퍼지힌트")
        if ontology_info:
            integration_info.append(f"분류:{ontology_info.get('category', 'N/A')}")

        if integration_info:
            reason += f" + 통합({', '.join(integration_info)})"

        # 주입 텍스트 생성 (퍼지 컨텍스트 및 온톨로지 정보 포함)
        injection_text = self._build_enhanced_injection_text(
            relevant_topics, versions_to_inject, trigger_type,
            fuzzy_context=fuzzy_context,
            ontology_info=ontology_info,
            related_topics=related_from_semantic,
            co_referenced=co_referenced,
        )

        # 신뢰도 계산 (통합 모듈 활용 시 보너스)
        base_confidence = min(1.0, len(versions_to_inject) / 10) if versions_to_inject else 0.5
        integration_bonus = 0.0
        if related_from_semantic:
            integration_bonus += 0.05
        if co_referenced:
            integration_bonus += 0.05
        if fuzzy_context:
            integration_bonus += 0.05
        if ontology_info:
            integration_bonus += 0.05
        confidence = min(1.0, base_confidence + integration_bonus)

        # 트리거 히스토리 기록
        self.trigger_history.append(
            {
                "trigger_type": trigger_type.value,
                "turn": self.current_turn,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "topics_injected": len(relevant_topics),
                "versions_injected": len(versions_to_inject),
            }
        )

        self._save_session()

        latency_ms = (time.time() - start_time) * 1000
        self.logger.log(
            module=LogModule.PAY_ATTENTION,
            action="inject_context",
            success=True,
            latency_ms=latency_ms,
            metadata={
                "trigger_type": trigger_type.value,
                "topics_count": len(relevant_topics),
                "versions_count": len(versions_to_inject),
            },
        )

        return InjectionContext(
            trigger_type=trigger_type,
            topics=relevant_topics,
            versions_to_inject=versions_to_inject,
            injection_text=injection_text,
            confidence=confidence,
            reason=reason,
        )

    def _build_injection_text(
        self, topics: List[Topic], versions: List[TopicVersion], trigger_type: TriggerType
    ) -> str:
        """주입 텍스트 생성 (기존 호환용)"""
        return self._build_enhanced_injection_text(topics, versions, trigger_type)

    def _build_enhanced_injection_text(
        self,
        topics: List[Topic],
        versions: List[TopicVersion],
        trigger_type: TriggerType,
        fuzzy_context: Optional[str] = None,
        ontology_info: Optional[Dict[str, Any]] = None,
        related_topics: Optional[List[str]] = None,
        co_referenced: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        향상된 주입 텍스트 생성 (v1.1 - 통합 모듈 포함)

        Args:
            topics: 주입할 토픽 목록
            versions: 주입할 버전 목록
            trigger_type: 트리거 타입
            fuzzy_context: 퍼지 컨텍스트 (fuzzy_prompt)
            ontology_info: 온톨로지 분류 정보
            related_topics: semantic_web에서 가져온 관련 토픽
            co_referenced: reference_history에서 가져온 함께 참조된 토픽

        Returns:
            향상된 주입 텍스트
        """
        if not topics:
            return ""

        lines = [
            "[CORTEX PAY_ATTENTION - Enhanced Context Injection v1.1]",
            f"트리거: {trigger_type.value}",
            f"현재 턴: {self.current_turn}",
        ]

        # 온톨로지 분류 정보 (있으면)
        if ontology_info:
            lines.append("")
            lines.append("[분류 정보]")
            lines.append(f"  카테고리: {ontology_info.get('category', 'N/A')}")
            if ontology_info.get('path'):
                lines.append(f"  경로: {' > '.join(ontology_info['path'])}")
            if ontology_info.get('confidence'):
                lines.append(f"  신뢰도: {ontology_info['confidence']:.2f}")

        # 관련 토픽 정보 (semantic_web)
        if related_topics:
            lines.append("")
            lines.append("[시맨틱 관계 토픽]")
            for rt in related_topics[:3]:
                lines.append(f"  - {rt}")

        # 함께 참조된 토픽 (reference_history)
        if co_referenced:
            lines.append("")
            lines.append("[과거 함께 참조된 토픽]")
            for co_name, co_conf in sorted(
                co_referenced.items(), key=lambda x: x[1], reverse=True
            )[:3]:
                lines.append(f"  - {co_name} (신뢰도: {co_conf:.2f})")

        # 퍼지 컨텍스트 (fuzzy_prompt)
        if fuzzy_context:
            lines.append("")
            lines.append("[퍼지 분류 힌트]")
            # 퍼지 컨텍스트에서 핵심 정보만 추출
            for line in fuzzy_context.split("\n"):
                if line.strip() and not line.startswith("[") and not line.startswith("/"):
                    lines.append(f"  {line.strip()}")
                    if len(lines) > 50:  # 너무 길면 중단
                        break

        lines.append("")

        # 토픽별 상세 정보
        for topic in topics:
            lines.append(f"=== {topic.name} ({topic.category}) ===")
            lines.append(f"언급 횟수: {topic.mention_count}회")
            lines.append(topic.get_all_versions_summary())
            lines.append("")

        lines.append("[/CORTEX PAY_ATTENTION]")

        return "\n".join(lines)

    def validate_completeness(
        self, response: str, expected_topics: Optional[List[str]] = None
    ) -> CompletenessReport:
        """
        응답의 완전성 검증

        Args:
            response: AI 응답
            expected_topics: 예상되는 토픽 목록 (None이면 전체)

        Returns:
            CompletenessReport 객체
        """
        if not self.enabled:
            return CompletenessReport(
                is_complete=True,
                missing_topics=[],
                missing_versions=[],
                coverage_ratio=1.0,
                suggestion="",
            )

        # 예상 토픽
        if expected_topics:
            check_topics = [t for t in self.topics.values() if t.name in expected_topics]
        else:
            check_topics = list(self.topics.values())

        if not check_topics:
            return CompletenessReport(
                is_complete=True,
                missing_topics=[],
                missing_versions=[],
                coverage_ratio=1.0,
                suggestion="",
            )

        response_lower = response.lower()

        # 토픽 커버리지 확인
        missing_topics = []
        missing_versions = []
        covered_count = 0

        for topic in check_topics:
            # 토픽 이름 또는 키워드가 응답에 있는지 확인
            topic_mentioned = topic.name.lower() in response_lower

            if not topic_mentioned:
                # 키워드로 재확인
                latest = topic.get_latest_version()
                if latest:
                    keyword_match = any(kw.lower() in response_lower for kw in latest.keywords)
                    topic_mentioned = keyword_match

            if topic_mentioned:
                covered_count += 1
                # 버전 커버리지 확인 (여러 버전이 있는 경우)
                if len(topic.versions) > 1:
                    for v in topic.versions:
                        if v.summary.lower() not in response_lower:
                            # 버전 변경사항이 언급되지 않음
                            if v.changes_from_parent:
                                missing_versions.append(f"{topic.name} v{v.version_number}")
            else:
                missing_topics.append(topic.name)

        coverage_ratio = covered_count / len(check_topics) if check_topics else 1.0
        is_complete = coverage_ratio >= 0.8 and len(missing_versions) == 0

        # 제안 생성
        suggestions = []
        if missing_topics:
            suggestions.append(f"누락된 토픽: {', '.join(missing_topics)}")
        if missing_versions:
            suggestions.append(f"누락된 버전 변경: {', '.join(missing_versions)}")

        self.logger.log(
            module=LogModule.PAY_ATTENTION,
            action="validate_completeness",
            success=True,
            metadata={
                "is_complete": is_complete,
                "coverage_ratio": coverage_ratio,
                "missing_topics": len(missing_topics),
                "missing_versions": len(missing_versions),
            },
        )

        return CompletenessReport(
            is_complete=is_complete,
            missing_topics=missing_topics,
            missing_versions=missing_versions,
            coverage_ratio=coverage_ratio,
            suggestion="; ".join(suggestions) if suggestions else "완전한 응답입니다.",
        )

    def check_consistency(
        self, new_content: str, topic_name: Optional[str] = None
    ) -> ConsistencyReport:
        """
        새 내용과 기존 내용의 일관성 검증

        Args:
            new_content: 새로운 내용
            topic_name: 확인할 토픽 (None이면 전체)

        Returns:
            ConsistencyReport 객체
        """
        if not self.enabled:
            return ConsistencyReport(is_consistent=True, conflicts=[], warnings=[])

        conflicts = []
        warnings = []

        check_topics = (
            [self.topics[self._generate_topic_id(topic_name)]]
            if topic_name and self._generate_topic_id(topic_name) in self.topics
            else list(self.topics.values())
        )

        new_keywords = set(self._extract_keywords(new_content))

        for topic in check_topics:
            latest = topic.get_latest_version()
            if not latest:
                continue

            old_keywords = set(latest.keywords)

            # 키워드 충돌 감지 (동일 토픽에서 완전히 다른 키워드)
            overlap = old_keywords & new_keywords
            if overlap:
                # 동일 토픽 언급 - 내용 비교
                # 간단한 모순 패턴 확인
                contradiction_pairs = [
                    (r"있", r"없"),
                    (r"했", r"안.*했"),
                    (r"true", r"false"),
                    (r"yes", r"no"),
                ]

                for pos, neg in contradiction_pairs:
                    old_has_pos = re.search(pos, latest.content)
                    new_has_neg = re.search(neg, new_content)
                    old_has_neg = re.search(neg, latest.content)
                    new_has_pos = re.search(pos, new_content)

                    if (old_has_pos and new_has_neg) or (old_has_neg and new_has_pos):
                        conflicts.append(
                            {
                                "topic": topic.name,
                                "old": latest.summary,
                                "new": new_content[:100],
                                "type": "contradiction",
                            }
                        )
                        break

        is_consistent = len(conflicts) == 0

        if not is_consistent:
            warnings.append("이전 내용과 모순되는 부분이 감지되었습니다. 확인이 필요합니다.")

        self.logger.log(
            module=LogModule.PAY_ATTENTION,
            action="check_consistency",
            success=True,
            metadata={"is_consistent": is_consistent, "conflicts_count": len(conflicts)},
        )

        return ConsistencyReport(
            is_consistent=is_consistent, conflicts=conflicts, warnings=warnings
        )

    def get_session_summary(self) -> Dict[str, Any]:
        """세션 요약 정보 반환"""
        return {
            "project_id": self.project_id,
            "branch_id": self.branch_id,
            "session_start": self.session_start,
            "current_turn": self.current_turn,
            "total_topics": len(self.topics),
            "total_versions": sum(len(t.versions) for t in self.topics.values()),
            "trigger_count": len(self.trigger_history),
            "topics": [
                {"name": t.name, "versions": len(t.versions), "mentions": t.mention_count}
                for t in self.topics.values()
            ],
        }

    def clear_session(self) -> None:
        """세션 초기화"""
        self.topics.clear()
        self.current_turn = 0
        self.trigger_history.clear()
        self.session_start = datetime.now(timezone.utc).isoformat()

        if self.session_log_path.exists():
            self.session_log_path.unlink()

        self.logger.log(module=LogModule.PAY_ATTENTION, action="clear_session", success=True)


# 싱글톤 관리
_pay_attention_instances: Dict[str, PayAttentionEngine] = {}


def get_pay_attention_engine(
    project_id: str, branch_id: str, enabled: bool = True
) -> PayAttentionEngine:
    """PayAttentionEngine 인스턴스 반환 (싱글톤 패턴)"""
    key = f"{project_id}/{branch_id}"

    if key not in _pay_attention_instances:
        _pay_attention_instances[key] = PayAttentionEngine(
            project_id=project_id, branch_id=branch_id, enabled=enabled
        )

    return _pay_attention_instances[key]


def reset_pay_attention_engine(project_id: str, branch_id: str) -> None:
    """인스턴스 리셋 (테스트용)"""
    key = f"{project_id}/{branch_id}"
    if key in _pay_attention_instances:
        del _pay_attention_instances[key]


# 테스트용 실행
if __name__ == "__main__":
    print("=== Pay Attention Engine Test ===")

    # 엔진 생성
    engine = PayAttentionEngine(project_id="__test__", branch_id="main", enabled=True)

    # 메시지 트래킹 시뮬레이션
    messages = [
        ("user", "React hooks에 대해 알려줘", ["React hooks"]),
        ("assistant", "React hooks는 함수형 컴포넌트에서...", ["React hooks"]),
        ("user", "useState 사용법 알려줘", ["React hooks", "useState"]),
        ("assistant", "useState는 상태 관리를 위한...", ["React hooks", "useState"]),
        ("user", "근데 아까 말한 거 다시 설명해줘", None),  # 참조 쿼리
    ]

    for role, msg, topics in messages:
        result = engine.track_message(
            message=msg, role=role, detected_topics=topics, topic_category="development"
        )
        print(f"[{role}] Tracked: {result}")

    # 트리거 감지
    trigger = engine.detect_trigger("아까 말한 거 다시 설명해줘")
    print(f"\nDetected trigger: {trigger}")

    # Attention Context 주입
    if trigger:
        injection = engine.inject_attention_context(trigger, "아까 말한 거")
        print(f"\nInjection text:\n{injection.injection_text}")

    # 요약 요청
    summary_trigger = engine.detect_trigger("지금까지 내용 정리해줘")
    print(f"\nSummary trigger: {summary_trigger}")

    if summary_trigger:
        injection = engine.inject_attention_context(summary_trigger, "정리해줘")
        print(f"\nSummary injection:\n{injection.injection_text}")

    # 세션 요약
    print(f"\nSession summary: {engine.get_session_summary()}")

    # 정리
    engine.clear_session()
    print("\nSession cleared.")
