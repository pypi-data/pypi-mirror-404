"""
Cortex MCP - Ontology Engine

의미론적 분류 체계를 통한 맥락 관리 시스템

목표:
- Branch Decision 정확도: 80% → 95%
- RAG Recall Rate: 70% → 90%
- 토큰 비용: 15% 절감
- 맥락 추천 정확도: 50% → 95%
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .alpha_logger import LogModule, get_alpha_logger

# ============================================================================
# 상수 및 설정
# ============================================================================

# 임베딩 모델 (config.py와 동일)
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# 유사도 임계값
SIMILARITY_THRESHOLD_HIGH = 0.85  # 높은 확신
SIMILARITY_THRESHOLD_MEDIUM = 0.70  # 중간 확신
SIMILARITY_THRESHOLD_LOW = 0.55  # 낮은 확신

# 온톨로지 분류 최대 깊이
MAX_ONTOLOGY_DEPTH = 4

# 성능 목표
TARGET_LATENCY_MS = 1000  # 1초 이내 응답

# 재시도 설정
MAX_RETRY_ATTEMPTS = 3  # 최대 재시도 횟수
RETRY_BACKOFF_FACTOR = 0.5  # Exponential backoff 초기값 (초)


# ============================================================================
# 데이터 클래스
# ============================================================================


class OntologyCategory(Enum):
    """기본 온톨로지 카테고리 (1차 분류)"""

    DEVELOPMENT = "development"  # 개발 관련
    ARCHITECTURE = "architecture"  # 아키텍처/설계
    INFRASTRUCTURE = "infrastructure"  # 인프라/배포
    DATA = "data"  # 데이터/DB
    SECURITY = "security"  # 보안
    TESTING = "testing"  # 테스트/QA
    DOCUMENTATION = "documentation"  # 문서화
    PROJECT_MGMT = "project_mgmt"  # 프로젝트 관리
    GENERAL = "general"  # 일반


@dataclass
class OntologyNode:
    """온톨로지 트리의 노드"""

    id: str
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    level: int = 0
    context_count: int = 0  # 이 노드에 분류된 맥락 수
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        """직렬화"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "level": self.level,
            "context_count": self.context_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "OntologyNode":
        """역직렬화"""
        embedding = None
        if data.get("embedding") is not None:
            embedding = np.array(data["embedding"])

        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            keywords=data.get("keywords", []),
            embedding=embedding,
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            level=data.get("level", 0),
            context_count=data.get("context_count", 0),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )


@dataclass
class ClassificationResult:
    """분류 결과"""

    node_id: str
    node_name: str
    confidence: float
    path: List[str]  # 루트부터 현재 노드까지의 경로
    latency_ms: float

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "confidence": self.confidence,
            "path": self.path,
            "latency_ms": self.latency_ms,
        }


# ============================================================================
# 온톨로지 트리
# ============================================================================


class OntologyTree:
    """온톨로지 트리 구조 관리"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.nodes: Dict[str, OntologyNode] = {}
        self.root_ids: List[str] = []

        if storage_path is None:
            storage_path = Path.home() / ".cortex" / "ontology"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.tree_file = self.storage_path / "ontology_tree.json"

        # 기존 트리 로드 또는 기본 트리 생성
        if self.tree_file.exists():
            self._load_tree()
        else:
            self._create_default_tree()

    def _generate_node_id(self, name: str) -> str:
        """노드 ID 생성"""
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{name}:{timestamp}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]

    def _create_default_tree(self):
        """기본 온톨로지 트리 생성"""
        # 1차 분류 노드 생성
        default_categories = [
            {
                "name": "development",
                "description": "소프트웨어 개발 관련 (코딩, 디버깅, 리팩토링)",
                "keywords": ["코드", "함수", "클래스", "메서드", "변수", "버그", "에러", "구현"],
                "children": [
                    {
                        "name": "frontend",
                        "description": "프론트엔드 개발",
                        "keywords": ["React", "Vue", "HTML", "CSS", "UI", "컴포넌트"],
                    },
                    {
                        "name": "backend",
                        "description": "백엔드 개발",
                        "keywords": ["API", "서버", "엔드포인트", "라우팅", "미들웨어"],
                    },
                    {
                        "name": "mobile",
                        "description": "모바일 앱 개발",
                        "keywords": ["iOS", "Android", "앱", "모바일"],
                    },
                ],
            },
            {
                "name": "architecture",
                "description": "시스템 아키텍처 및 설계",
                "keywords": ["설계", "아키텍처", "패턴", "구조", "모듈"],
                "children": [
                    {
                        "name": "design_patterns",
                        "description": "디자인 패턴",
                        "keywords": ["패턴", "싱글톤", "팩토리", "옵저버"],
                    },
                    {
                        "name": "system_design",
                        "description": "시스템 설계",
                        "keywords": ["마이크로서비스", "모놀리식", "분산"],
                    },
                ],
            },
            {
                "name": "security",
                "description": "보안 관련",
                "keywords": ["보안", "인증", "암호화", "권한", "토큰"],
                "children": [
                    {
                        "name": "user_auth",
                        "description": "사용자 인증 (로그인, 세션)",
                        "keywords": ["로그인", "세션", "JWT", "OAuth", "SSO"],
                    },
                    {
                        "name": "api_auth",
                        "description": "API 인증",
                        "keywords": ["API키", "Bearer", "토큰"],
                    },
                    {
                        "name": "encryption",
                        "description": "암호화/복호화",
                        "keywords": ["AES", "RSA", "암호화", "복호화", "해시"],
                    },
                ],
            },
            {
                "name": "data",
                "description": "데이터 및 데이터베이스",
                "keywords": ["데이터", "DB", "쿼리", "스키마", "테이블"],
                "children": [
                    {
                        "name": "database",
                        "description": "데이터베이스 관리",
                        "keywords": ["MySQL", "PostgreSQL", "MongoDB", "쿼리"],
                    },
                    {
                        "name": "data_processing",
                        "description": "데이터 처리",
                        "keywords": ["ETL", "변환", "파싱", "검증"],
                    },
                ],
            },
            {
                "name": "infrastructure",
                "description": "인프라 및 배포",
                "keywords": ["배포", "서버", "클라우드", "CI/CD", "도커"],
                "children": [
                    {
                        "name": "deployment",
                        "description": "배포",
                        "keywords": ["배포", "릴리즈", "빌드"],
                    },
                    {
                        "name": "devops",
                        "description": "DevOps",
                        "keywords": ["CI", "CD", "파이프라인", "자동화"],
                    },
                    {
                        "name": "cloud",
                        "description": "클라우드 서비스",
                        "keywords": ["AWS", "GCP", "Azure", "클라우드"],
                    },
                ],
            },
            {
                "name": "testing",
                "description": "테스트 및 품질 관리",
                "keywords": ["테스트", "QA", "버그", "검증"],
                "children": [
                    {
                        "name": "unit_test",
                        "description": "단위 테스트",
                        "keywords": ["단위", "유닛", "모킹"],
                    },
                    {
                        "name": "integration_test",
                        "description": "통합 테스트",
                        "keywords": ["통합", "E2E", "시나리오"],
                    },
                ],
            },
            {
                "name": "documentation",
                "description": "문서화",
                "keywords": ["문서", "README", "API문서", "주석"],
                "children": [],
            },
            {
                "name": "project_mgmt",
                "description": "프로젝트 관리",
                "keywords": ["일정", "마일스톤", "태스크", "이슈", "기획"],
                "children": [],
            },
        ]

        for category in default_categories:
            # 1차 노드 생성
            parent_node = OntologyNode(
                id=self._generate_node_id(category["name"]),
                name=category["name"],
                description=category["description"],
                keywords=category["keywords"],
                level=0,
            )
            self.add_node(parent_node)
            self.root_ids.append(parent_node.id)

            # 2차 노드 생성
            for child in category.get("children", []):
                child_node = OntologyNode(
                    id=self._generate_node_id(child["name"]),
                    name=child["name"],
                    description=child["description"],
                    keywords=child["keywords"],
                    parent_id=parent_node.id,
                    level=1,
                )
                self.add_node(child_node)
                parent_node.children_ids.append(child_node.id)

        self._save_tree()

    def add_node(self, node: OntologyNode):
        """노드 추가"""
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[OntologyNode]:
        """노드 조회"""
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[OntologyNode]:
        """자식 노드 목록"""
        node = self.get_node(node_id)
        if node is None:
            return []
        return [self.nodes[cid] for cid in node.children_ids if cid in self.nodes]

    def get_path(self, node_id: str) -> List[str]:
        """루트부터 현재 노드까지의 경로"""
        path = []
        current = self.get_node(node_id)
        while current:
            path.insert(0, current.name)
            if current.parent_id:
                current = self.get_node(current.parent_id)
            else:
                break
        return path

    def get_all_nodes_at_level(self, level: int) -> List[OntologyNode]:
        """특정 레벨의 모든 노드"""
        return [n for n in self.nodes.values() if n.level == level]

    def get_root_nodes(self) -> List[OntologyNode]:
        """루트 노드 목록"""
        return [self.nodes[rid] for rid in self.root_ids if rid in self.nodes]

    def _save_tree(self):
        """트리 저장"""
        data = {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "root_ids": self.root_ids,
            "updated_at": datetime.utcnow().isoformat(),
        }
        with open(self.tree_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_tree(self):
        """트리 로드"""
        try:
            with open(self.tree_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.nodes = {
                nid: OntologyNode.from_dict(ndata) for nid, ndata in data.get("nodes", {}).items()
            }
            self.root_ids = data.get("root_ids", [])
        except Exception as e:
            # 로드 실패 시 기본 트리 생성
            self._create_default_tree()


# ============================================================================
# 온톨로지 엔진
# ============================================================================


class OntologyEngine:
    """
    온톨로지 기반 의미론적 분류 엔진

    주요 기능:
    1. 텍스트/맥락의 의미론적 분류
    2. RAG 검색 결과 필터링
    3. 브랜치 결정 보조
    """

    def __init__(self, storage_path: Optional[Path] = None, ontology_enabled: bool = True):
        """
        Args:
            storage_path: 온톨로지 저장 경로
            ontology_enabled: 온톨로지 활성화 여부 (라이센스 연동)
        """
        self.ontology_enabled = ontology_enabled
        self.logger = get_alpha_logger()

        # 온톨로지 트리 초기화
        self.tree = OntologyTree(storage_path)

        # 임베딩 모델 초기화
        self.embedding_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE and ontology_enabled:
            try:
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
                self._compute_node_embeddings()
            except Exception as e:
                self.logger.log(
                    module=LogModule.ONTOLOGY,
                    action="init_embedding_model",
                    success=False,
                    error=str(e),
                )

    def _compute_node_embeddings(self):
        """모든 노드의 임베딩 계산"""
        if self.embedding_model is None:
            return

        for node_id, node in self.tree.nodes.items():
            if node.embedding is None:
                # 노드 설명 + 키워드로 임베딩 생성
                text = f"{node.name} {node.description} {' '.join(node.keywords)}"
                node.embedding = self.embedding_model.encode(text, convert_to_numpy=True)

        # 임베딩이 계산된 트리 저장
        self.tree._save_tree()

    def _compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        if embedding1 is None or embedding2 is None:
            return 0.0

        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))

    def classify(self, text: str, max_depth: int = MAX_ONTOLOGY_DEPTH) -> ClassificationResult:
        """
        텍스트를 온톨로지 카테고리로 분류 (재시도 로직 포함)

        Args:
            text: 분류할 텍스트
            max_depth: 최대 분류 깊이

        Returns:
            ClassificationResult: 분류 결과
        """
        start_time = time.time()

        # 온톨로지 비활성화 시 기본 분류
        if not self.ontology_enabled or self.embedding_model is None:
            result = ClassificationResult(
                node_id="general",
                node_name="general",
                confidence=0.5,
                path=["general"],
                latency_ms=0,
            )
            return result

        # 재시도 로직
        last_exception = None
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                result = self._classify_internal(text, max_depth, start_time)

                # 성공 시 재시도 횟수 로그
                if attempt > 0:
                    self.logger.log_ontology(
                        action="classify_retry_success",
                        input_text=text[:200],
                        category=result.node_name,
                        confidence=result.confidence,
                        success=True,
                        metadata={"attempt": attempt + 1, "total_attempts": MAX_RETRY_ATTEMPTS},
                    )

                return result

            except Exception as e:
                last_exception = e

                # 재시도 로그
                self.logger.log_ontology(
                    action="classify_retry",
                    input_text=text[:200],
                    category="error",
                    confidence=0.0,
                    success=False,
                    metadata={
                        "attempt": attempt + 1,
                        "max_attempts": MAX_RETRY_ATTEMPTS,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )

                # 마지막 시도가 아니면 대기 후 재시도
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    backoff_time = RETRY_BACKOFF_FACTOR * (2**attempt)
                    time.sleep(backoff_time)

        # 모든 재시도 실패 시 general 분류 반환
        self.logger.log_ontology(
            action="classify_fallback",
            input_text=text[:200],
            category="general",
            confidence=0.0,
            success=False,
            metadata={
                "reason": "max_retries_exceeded",
                "last_error": str(last_exception),
                "error_type": type(last_exception).__name__ if last_exception else "Unknown",
            },
        )

        return ClassificationResult(
            node_id="general",
            node_name="general",
            confidence=0.0,
            path=["general"],
            latency_ms=(time.time() - start_time) * 1000,
        )

    def _classify_internal(
        self, text: str, max_depth: int, start_time: float
    ) -> ClassificationResult:
        """
        내부 분류 로직 (재시도 대상)

        Args:
            text: 분류할 텍스트
            max_depth: 최대 분류 깊이
            start_time: 시작 시간

        Returns:
            ClassificationResult: 분류 결과

        Raises:
            Exception: 분류 실패 시
        """
        # 텍스트 임베딩
        text_embedding = self.embedding_model.encode(text, convert_to_numpy=True)

        # 계층적 분류 수행
        best_node = None
        best_similarity = 0.0
        current_level_nodes = self.tree.get_root_nodes()
        path = []

        for depth in range(max_depth):
            if not current_level_nodes:
                break

            # 현재 레벨에서 가장 유사한 노드 찾기
            level_best_node = None
            level_best_similarity = 0.0

            for node in current_level_nodes:
                if node.embedding is not None:
                    similarity = self._compute_similarity(text_embedding, node.embedding)
                    if similarity > level_best_similarity:
                        level_best_similarity = similarity
                        level_best_node = node

            # 임계값 이상이면 해당 노드 선택
            if level_best_node and level_best_similarity >= SIMILARITY_THRESHOLD_LOW:
                best_node = level_best_node
                best_similarity = level_best_similarity
                path.append(level_best_node.name)

                # 다음 레벨로 이동
                current_level_nodes = self.tree.get_children(level_best_node.id)
            else:
                break

        # 결과 없으면 general 반환
        if best_node is None:
            root_nodes = self.tree.get_root_nodes()
            if root_nodes:
                best_node = root_nodes[0]
                best_similarity = 0.5
                path = [best_node.name]
            else:
                result = ClassificationResult(
                    node_id="general",
                    node_name="general",
                    confidence=0.5,
                    path=["general"],
                    latency_ms=(time.time() - start_time) * 1000,
                )
                self._log_classification(text, result)
                return result

        latency_ms = (time.time() - start_time) * 1000

        result = ClassificationResult(
            node_id=best_node.id,
            node_name=best_node.name,
            confidence=best_similarity,
            path=path,
            latency_ms=latency_ms,
        )

        # 로그 기록
        self._log_classification(text, result)

        return result

    def _log_classification(self, text: str, result: ClassificationResult):
        """분류 결과 로그"""
        self.logger.log_ontology(
            action="classify",
            input_text=text[:200],  # 입력 텍스트 일부만
            category=result.node_name,
            confidence=result.confidence,
            success=True,
            latency_ms=result.latency_ms,
        )

    def filter_results(
        self, query: str, results: List[Dict[str, Any]], relevance_boost: float = 0.2
    ) -> List[Dict[str, Any]]:
        """
        RAG 검색 결과를 온톨로지 기반으로 필터링/재정렬

        Args:
            query: 검색 쿼리
            results: RAG 검색 결과 목록 (각 항목은 'content', 'score' 포함)
            relevance_boost: 동일 카테고리 결과에 적용할 점수 부스트

        Returns:
            필터링/재정렬된 결과 목록
        """
        start_time = time.time()

        if not self.ontology_enabled:
            return results

        if not results:
            return results

        # 쿼리 분류
        query_classification = self.classify(query)
        query_category = query_classification.node_name

        # 각 결과에 온톨로지 점수 추가
        enhanced_results = []
        for result in results:
            content = result.get("content", "")
            original_score = result.get("score", 0.0)

            # 결과 콘텐츠 분류
            result_classification = self.classify(content)

            # 같은 카테고리면 점수 부스트
            ontology_bonus = 0.0
            if result_classification.node_name == query_category:
                ontology_bonus = relevance_boost
            elif result_classification.path and query_classification.path:
                # 부분 경로 일치 시 작은 부스트
                common_path = set(result_classification.path) & set(query_classification.path)
                if common_path:
                    ontology_bonus = relevance_boost * 0.5

            enhanced_result = result.copy()
            enhanced_result["original_score"] = original_score
            enhanced_result["ontology_score"] = ontology_bonus
            enhanced_result["final_score"] = original_score + ontology_bonus
            enhanced_result["ontology_category"] = result_classification.node_name
            enhanced_results.append(enhanced_result)

        # 최종 점수로 정렬
        enhanced_results.sort(key=lambda x: x["final_score"], reverse=True)

        latency_ms = (time.time() - start_time) * 1000

        # 필터 로그
        self.logger.log_ontology(
            action="filter",
            input_text=f"Query: {query[:100]}, Results: {len(results)}",
            category=query_category,
            confidence=query_classification.confidence,
            success=True,
            latency_ms=latency_ms,
        )

        return enhanced_results

    def suggest_branch_category(self, text: str) -> Tuple[str, float]:
        """
        브랜치 생성 시 카테고리 제안

        Args:
            text: 분석할 텍스트 (대화 내용, 작업 설명 등)

        Returns:
            (제안 카테고리, 신뢰도)
        """
        if not self.ontology_enabled:
            return ("general", 0.5)

        classification = self.classify(text)
        return (classification.node_name, classification.confidence)

    def get_related_categories(self, category_name: str) -> List[str]:
        """
        관련 카테고리 목록 반환 (같은 부모 아래 형제 카테고리)

        Args:
            category_name: 카테고리 이름

        Returns:
            관련 카테고리 이름 목록
        """
        related = []

        # 해당 카테고리 노드 찾기
        target_node = None
        for node in self.tree.nodes.values():
            if node.name == category_name:
                target_node = node
                break

        if target_node is None:
            return related

        # 부모가 있으면 형제 노드들 반환
        if target_node.parent_id:
            parent = self.tree.get_node(target_node.parent_id)
            if parent:
                for child_id in parent.children_ids:
                    child = self.tree.get_node(child_id)
                    if child and child.name != category_name:
                        related.append(child.name)

        # 자식 노드들도 포함
        for child_id in target_node.children_ids:
            child = self.tree.get_node(child_id)
            if child:
                related.append(child.name)

        return related

    def add_custom_category(
        self, name: str, description: str, keywords: List[str], parent_name: Optional[str] = None
    ) -> Optional[OntologyNode]:
        """
        사용자 정의 카테고리 추가

        Args:
            name: 카테고리 이름
            description: 설명
            keywords: 관련 키워드
            parent_name: 부모 카테고리 이름 (없으면 루트로 추가)

        Returns:
            생성된 노드 (실패 시 None)
        """
        # 부모 노드 찾기
        parent_node = None
        parent_id = None
        level = 0

        if parent_name:
            for node in self.tree.nodes.values():
                if node.name == parent_name:
                    parent_node = node
                    parent_id = node.id
                    level = node.level + 1
                    break

            if parent_node is None:
                return None

        # 새 노드 생성
        new_node = OntologyNode(
            id=self.tree._generate_node_id(name),
            name=name,
            description=description,
            keywords=keywords,
            parent_id=parent_id,
            level=level,
        )

        # 임베딩 계산
        if self.embedding_model:
            text = f"{name} {description} {' '.join(keywords)}"
            new_node.embedding = self.embedding_model.encode(text, convert_to_numpy=True)

        # 트리에 추가
        self.tree.add_node(new_node)

        if parent_node:
            parent_node.children_ids.append(new_node.id)
        else:
            self.tree.root_ids.append(new_node.id)

        # 저장
        self.tree._save_tree()

        # 로그
        self.logger.log_ontology(
            action="add_category",
            input_text=f"Added: {name}",
            category=name,
            confidence=1.0,
            success=True,
            latency_ms=0,
        )

        return new_node

    def update_context_count(self, category_name: str, delta: int = 1):
        """
        카테고리에 분류된 맥락 수 업데이트

        Args:
            category_name: 카테고리 이름
            delta: 증감값 (+1 또는 -1)
        """
        for node in self.tree.nodes.values():
            if node.name == category_name:
                node.context_count = max(0, node.context_count + delta)
                self.tree._save_tree()
                break

    def get_statistics(self) -> Dict[str, Any]:
        """
        온톨로지 통계 반환

        Returns:
            통계 정보 딕셔너리
        """
        total_nodes = len(self.tree.nodes)
        nodes_by_level = {}
        total_contexts = 0

        for node in self.tree.nodes.values():
            level = node.level
            if level not in nodes_by_level:
                nodes_by_level[level] = 0
            nodes_by_level[level] += 1
            total_contexts += node.context_count

        return {
            "total_nodes": total_nodes,
            "root_nodes": len(self.tree.root_ids),
            "nodes_by_level": nodes_by_level,
            "total_contexts_classified": total_contexts,
            "ontology_enabled": self.ontology_enabled,
            "embedding_model": EMBEDDING_MODEL if self.embedding_model else None,
        }

    def visualize_tree(self) -> str:
        """
        온톨로지 트리 시각화 (텍스트)

        Returns:
            트리 구조 문자열
        """
        lines = ["Ontology Tree", "=" * 40]

        def _add_node(node: OntologyNode, indent: int = 0):
            prefix = "  " * indent + ("├── " if indent > 0 else "")
            lines.append(f"{prefix}{node.name} ({node.context_count})")

            for child_id in node.children_ids:
                child = self.tree.get_node(child_id)
                if child:
                    _add_node(child, indent + 1)

        for root_id in self.tree.root_ids:
            root = self.tree.get_node(root_id)
            if root:
                _add_node(root)

        return "\n".join(lines)


# ============================================================================
# 라이센스 게이팅 래퍼
# ============================================================================


class LicenseGatedOntologyEngine:
    """
    라이센스 검증을 포함한 온톨로지 엔진 래퍼

    Tier별 동작:
    - Free: 비활성화 (Legacy RAG만 사용)
    - Tier 1 (Pro): 활성화
    - Tier 2 (Premium): 활성화 + Zero-Effort
    """

    def __init__(self, license_params: Optional[Dict] = None):
        """
        Args:
            license_params: 라이센스 파라미터 (ONTOLOGY_ON 등)
        """
        self.license_params = license_params or {}

        # ONTOLOGY_ON 파라미터 확인
        ontology_enabled = self.license_params.get("ONTOLOGY_ON", False)

        # 엔진 초기화
        self.engine = OntologyEngine(ontology_enabled=ontology_enabled)
        self.logger = get_alpha_logger()

        # 초기화 로그
        self.logger.log_license(
            action="ontology_init", license_tier=self._get_tier_name(), success=True
        )

    def _get_tier_name(self) -> str:
        """현재 티어 이름"""
        if not self.license_params.get("ONTOLOGY_ON", False):
            return "Free"
        elif self.license_params.get("BRANCHING_CONFIRM_REQUIRED", True):
            return "Tier 1 (Pro)"
        else:
            return "Tier 2 (Premium)"

    def is_enabled(self) -> bool:
        """온톨로지 활성화 여부"""
        return self.engine.ontology_enabled

    def classify(self, text: str) -> ClassificationResult:
        """분류 (라이센스 확인 포함)"""
        if not self.is_enabled():
            return ClassificationResult(
                node_id="general",
                node_name="general",
                confidence=0.5,
                path=["general"],
                latency_ms=0,
            )
        return self.engine.classify(text)

    def filter_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """결과 필터링 (라이센스 확인 포함)"""
        if not self.is_enabled():
            return results
        return self.engine.filter_results(query, results)

    def suggest_branch_category(self, text: str) -> Tuple[str, float]:
        """브랜치 카테고리 제안"""
        if not self.is_enabled():
            return ("general", 0.5)
        return self.engine.suggest_branch_category(text)

    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        stats = self.engine.get_statistics()
        stats["tier"] = self._get_tier_name()
        return stats


# ============================================================================
# 싱글톤 인스턴스
# ============================================================================

_ontology_engine: Optional[LicenseGatedOntologyEngine] = None


def get_ontology_engine(license_params: Optional[Dict] = None) -> LicenseGatedOntologyEngine:
    """
    온톨로지 엔진 싱글톤 인스턴스 반환

    Args:
        license_params: 라이센스 파라미터 (첫 호출 시만 사용)

    Returns:
        LicenseGatedOntologyEngine 인스턴스
    """
    global _ontology_engine

    if _ontology_engine is None:
        _ontology_engine = LicenseGatedOntologyEngine(license_params)

    return _ontology_engine


def reset_ontology_engine(license_params: Optional[Dict] = None):
    """
    온톨로지 엔진 재초기화 (라이센스 변경 시)

    Args:
        license_params: 새 라이센스 파라미터
    """
    global _ontology_engine
    _ontology_engine = LicenseGatedOntologyEngine(license_params)


# ============================================================================
# 퍼지 온톨로지 시스템 (v3.0 - M&A Premium IP)
# ============================================================================


@dataclass
class FuzzyMembership:
    """퍼지 멤버십 결과 - 다중 카테고리 소속도"""

    category: str
    membership_score: float  # 0.0 ~ 1.0
    confidence: float  # 분류 신뢰도
    path: List[str]  # 온톨로지 경로

    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "membership_score": round(self.membership_score, 4),
            "confidence": round(self.confidence, 4),
            "path": self.path,
        }


@dataclass
class FuzzyClassificationResult:
    """
    퍼지 분류 결과 - 다중 카테고리 동시 소속 지원

    기존 ClassificationResult와 달리:
    - 하나의 텍스트가 여러 카테고리에 동시 소속 가능
    - 각 카테고리별 멤버십 점수 (0.0~1.0) 제공
    - CoT Prompt 통합용 fuzzy_context 필드 포함
    """

    memberships: List[FuzzyMembership]
    primary_category: str  # 최고 점수 카테고리
    primary_score: float  # 최고 점수
    fuzzy_context: str  # CoT Prompt 주입용 문자열
    latency_ms: float
    total_categories_matched: int

    def to_dict(self) -> Dict:
        return {
            "memberships": [m.to_dict() for m in self.memberships],
            "primary_category": self.primary_category,
            "primary_score": round(self.primary_score, 4),
            "fuzzy_context": self.fuzzy_context,
            "latency_ms": round(self.latency_ms, 2),
            "total_categories_matched": self.total_categories_matched,
        }


class FuzzyOntologyEngine:
    """
    퍼지 온톨로지 엔진 (v3.0)

    기존 이진 분류(Binary Classification) 대신 연속 멤버십(Fuzzy Membership) 사용.
    하나의 맥락이 여러 카테고리에 동시에 소속될 수 있음.

    핵심 차별화:
    - 경쟁사 RAG: 단일 카테고리 분류 → 모호한 맥락에서 오류 발생
    - Cortex: 퍼지 멤버십 → 모호한 맥락도 정확히 처리

    M&A 가치:
    - 특허 가능한 핵심 알고리즘
    - 50% 이상 Agent Decision Error Rate 감소 목표
    """

    # 퍼지 멤버십 임계값
    MEMBERSHIP_THRESHOLD_PRIMARY = 0.7  # 주요 카테고리
    MEMBERSHIP_THRESHOLD_SECONDARY = 0.4  # 부차적 카테고리
    MEMBERSHIP_THRESHOLD_MIN = 0.2  # 최소 포함 임계값

    def __init__(
        self,
        base_engine: Optional[OntologyEngine] = None,
        storage_path: Optional[Path] = None,
        fuzzy_enabled: bool = True,
    ):
        """
        Args:
            base_engine: 기존 OntologyEngine (없으면 새로 생성)
            storage_path: 저장 경로
            fuzzy_enabled: 퍼지 기능 활성화 여부
        """
        self.fuzzy_enabled = fuzzy_enabled
        self.logger = get_alpha_logger()

        # 기존 엔진 재사용 또는 새로 생성
        if base_engine is not None:
            self.base_engine = base_engine
        else:
            self.base_engine = OntologyEngine(storage_path=storage_path, ontology_enabled=True)

    def calculate_fuzzy_membership(
        self, text: str, threshold: float = MEMBERSHIP_THRESHOLD_MIN
    ) -> FuzzyClassificationResult:
        """
        텍스트의 퍼지 멤버십 계산

        모든 카테고리에 대해 멤버십 점수를 계산하고,
        임계값 이상인 카테고리들을 반환.

        Args:
            text: 분류할 텍스트
            threshold: 최소 멤버십 임계값 (기본 0.2)

        Returns:
            FuzzyClassificationResult: 다중 카테고리 멤버십 결과
        """
        start_time = time.time()

        # 퍼지 비활성화 시 기본 분류 결과 반환
        if not self.fuzzy_enabled or self.base_engine.embedding_model is None:
            return self._fallback_result(text, start_time)

        # 텍스트 임베딩
        text_embedding = self.base_engine.embedding_model.encode(text, convert_to_numpy=True)

        # 모든 노드에 대해 멤버십 계산
        memberships: List[FuzzyMembership] = []

        for node in self.base_engine.tree.nodes.values():
            if node.embedding is None:
                continue

            # 코사인 유사도 계산
            similarity = self.base_engine._compute_similarity(text_embedding, node.embedding)

            # 임계값 이상인 경우만 포함
            if similarity >= threshold:
                membership = FuzzyMembership(
                    category=node.name,
                    membership_score=similarity,
                    confidence=self._calculate_confidence(similarity),
                    path=self.base_engine.tree.get_path(node.id),
                )
                memberships.append(membership)

        # 멤버십 점수 순으로 정렬
        memberships.sort(key=lambda m: m.membership_score, reverse=True)

        # 결과 생성
        latency_ms = (time.time() - start_time) * 1000

        if memberships:
            primary = memberships[0]
            fuzzy_context = self._generate_fuzzy_context(memberships)

            result = FuzzyClassificationResult(
                memberships=memberships,
                primary_category=primary.category,
                primary_score=primary.membership_score,
                fuzzy_context=fuzzy_context,
                latency_ms=latency_ms,
                total_categories_matched=len(memberships),
            )
        else:
            result = FuzzyClassificationResult(
                memberships=[],
                primary_category="general",
                primary_score=0.5,
                fuzzy_context="[Category: general (0.50)]",
                latency_ms=latency_ms,
                total_categories_matched=0,
            )

        # 로그 기록
        self._log_fuzzy_classification(text, result)

        return result

    def _calculate_confidence(self, similarity: float) -> float:
        """
        유사도를 신뢰도로 변환

        높은 유사도 → 높은 신뢰도
        중간 유사도 → 중간 신뢰도 (불확실성 반영)

        Args:
            similarity: 코사인 유사도 (0.0 ~ 1.0)

        Returns:
            신뢰도 (0.0 ~ 1.0)
        """
        if similarity >= self.MEMBERSHIP_THRESHOLD_PRIMARY:
            # 높은 유사도: 높은 신뢰도
            return 0.9 + (similarity - 0.7) * 0.33
        elif similarity >= self.MEMBERSHIP_THRESHOLD_SECONDARY:
            # 중간 유사도: 중간 신뢰도
            return 0.6 + (similarity - 0.4) * 0.5
        else:
            # 낮은 유사도: 낮은 신뢰도
            return similarity * 2.0

    def _generate_fuzzy_context(
        self, memberships: List[FuzzyMembership], max_categories: int = 3
    ) -> str:
        """
        CoT Prompt 주입용 퍼지 컨텍스트 문자열 생성

        형식:
        [Primary: security (0.85)] [Secondary: api_auth (0.62), encryption (0.48)]

        Args:
            memberships: 멤버십 목록
            max_categories: 최대 표시 카테고리 수

        Returns:
            CoT Prompt용 문자열
        """
        if not memberships:
            return "[Category: general (0.50)]"

        parts = []

        # Primary 카테고리
        primary = memberships[0]
        parts.append(f"[Primary: {primary.category} ({primary.membership_score:.2f})]")

        # Secondary 카테고리들
        if len(memberships) > 1:
            secondary = memberships[1:max_categories]
            secondary_str = ", ".join(f"{m.category} ({m.membership_score:.2f})" for m in secondary)
            parts.append(f"[Secondary: {secondary_str}]")

        return " ".join(parts)

    def _fallback_result(self, text: str, start_time: float) -> FuzzyClassificationResult:
        """퍼지 비활성화 시 기본 결과 반환"""
        latency_ms = (time.time() - start_time) * 1000

        return FuzzyClassificationResult(
            memberships=[
                FuzzyMembership(
                    category="general", membership_score=0.5, confidence=0.5, path=["general"]
                )
            ],
            primary_category="general",
            primary_score=0.5,
            fuzzy_context="[Category: general (0.50)]",
            latency_ms=latency_ms,
            total_categories_matched=1,
        )

    def _log_fuzzy_classification(self, text: str, result: FuzzyClassificationResult):
        """퍼지 분류 결과 로그"""
        self.logger.log_ontology(
            action="fuzzy_classify",
            input_text=text[:200],
            category=result.primary_category,
            confidence=result.primary_score,
            success=True,
            latency_ms=result.latency_ms,
        )

    def filter_results_fuzzy(
        self, query: str, results: List[Dict[str, Any]], membership_boost: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        퍼지 멤버십 기반 RAG 결과 필터링/재정렬

        기존 filter_results와 달리:
        - 다중 카테고리 매칭 고려
        - 멤버십 점수 가중치 적용
        - 부분 경로 일치 보너스

        Args:
            query: 검색 쿼리
            results: RAG 검색 결과 목록
            membership_boost: 동일 카테고리 결과에 적용할 부스트

        Returns:
            재정렬된 결과 목록
        """
        start_time = time.time()

        if not self.fuzzy_enabled or not results:
            return results

        # 쿼리의 퍼지 멤버십 계산
        query_fuzzy = self.calculate_fuzzy_membership(query)
        query_categories = {m.category: m.membership_score for m in query_fuzzy.memberships}

        enhanced_results = []
        for result in results:
            content = result.get("content", "")
            original_score = result.get("score", result.get("relevance_score", 0.0))

            # 결과 콘텐츠의 퍼지 멤버십 계산
            result_fuzzy = self.calculate_fuzzy_membership(content)
            result_categories = {m.category: m.membership_score for m in result_fuzzy.memberships}

            # 퍼지 보너스 계산
            fuzzy_bonus = 0.0

            # 카테고리 겹침 계산
            common_categories = set(query_categories.keys()) & set(result_categories.keys())

            for category in common_categories:
                # 두 멤버십 점수의 기하평균
                combined_score = (query_categories[category] * result_categories[category]) ** 0.5
                fuzzy_bonus += membership_boost * combined_score

            # 최종 점수 계산
            final_score = original_score + fuzzy_bonus

            enhanced_result = result.copy()
            enhanced_result["original_score"] = original_score
            enhanced_result["fuzzy_bonus"] = round(fuzzy_bonus, 4)
            enhanced_result["final_score"] = round(final_score, 4)
            enhanced_result["relevance_score"] = round(final_score, 4)
            enhanced_result["fuzzy_categories"] = list(result_categories.keys())[:3]
            enhanced_result["query_categories"] = list(query_categories.keys())[:3]

            enhanced_results.append(enhanced_result)

        # 최종 점수로 정렬
        enhanced_results.sort(key=lambda x: x["final_score"], reverse=True)

        latency_ms = (time.time() - start_time) * 1000

        # 필터 로그
        self.logger.log_ontology(
            action="fuzzy_filter",
            input_text=f"Query: {query[:100]}, Results: {len(results)}",
            category=query_fuzzy.primary_category,
            confidence=query_fuzzy.primary_score,
            success=True,
            latency_ms=latency_ms,
        )

        return enhanced_results

    def get_ambiguity_score(self, text: str) -> Dict[str, Any]:
        """
        텍스트의 모호성 점수 계산

        모호성이 높은 텍스트:
        - 여러 카테고리에 비슷한 점수로 소속
        - 기존 이진 분류에서 오류 발생 가능

        Args:
            text: 분석할 텍스트

        Returns:
            모호성 분석 결과
        """
        fuzzy_result = self.calculate_fuzzy_membership(text)

        if len(fuzzy_result.memberships) < 2:
            return {
                "ambiguity_score": 0.0,
                "is_ambiguous": False,
                "primary_category": fuzzy_result.primary_category,
                "competing_categories": [],
            }

        # 상위 2개 카테고리 점수 차이
        top_scores = [m.membership_score for m in fuzzy_result.memberships[:3]]
        score_gap = top_scores[0] - top_scores[1]

        # 모호성 점수: 점수 차이가 작을수록 높음
        # 0.0 = 확실한 분류, 1.0 = 매우 모호
        ambiguity_score = max(0, 1 - (score_gap / 0.3))

        # 경쟁 카테고리 (상위 카테고리와 점수 차이가 0.15 이하)
        competing = [
            m.category
            for m in fuzzy_result.memberships[1:]
            if (top_scores[0] - m.membership_score) < 0.15
        ]

        return {
            "ambiguity_score": round(ambiguity_score, 4),
            "is_ambiguous": ambiguity_score > 0.5,
            "primary_category": fuzzy_result.primary_category,
            "primary_score": round(top_scores[0], 4),
            "competing_categories": competing,
            "score_gap": round(score_gap, 4),
            "recommendation": (
                "FUZZY_MULTI_CATEGORY" if ambiguity_score > 0.5 else "SINGLE_CATEGORY"
            ),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """퍼지 온톨로지 통계"""
        base_stats = self.base_engine.get_statistics()

        base_stats["fuzzy_enabled"] = self.fuzzy_enabled
        base_stats["membership_thresholds"] = {
            "primary": self.MEMBERSHIP_THRESHOLD_PRIMARY,
            "secondary": self.MEMBERSHIP_THRESHOLD_SECONDARY,
            "minimum": self.MEMBERSHIP_THRESHOLD_MIN,
        }

        return base_stats


# ============================================================================
# 퍼지 온톨로지 싱글톤
# ============================================================================

_fuzzy_engine: Optional[FuzzyOntologyEngine] = None


def get_fuzzy_ontology_engine(license_params: Optional[Dict] = None) -> FuzzyOntologyEngine:
    """
    퍼지 온톨로지 엔진 싱글톤 인스턴스 반환

    Args:
        license_params: 라이센스 파라미터

    Returns:
        FuzzyOntologyEngine 인스턴스
    """
    global _fuzzy_engine

    if _fuzzy_engine is None:
        # 기존 온톨로지 엔진 가져오기
        gated_engine = get_ontology_engine(license_params)
        base_engine = gated_engine.engine if gated_engine.is_enabled() else None

        # 퍼지 활성화 여부 (Pro 이상에서만)
        fuzzy_enabled = license_params.get("FUZZY_ONTOLOGY_ON", True) if license_params else True

        _fuzzy_engine = FuzzyOntologyEngine(base_engine=base_engine, fuzzy_enabled=fuzzy_enabled)

    return _fuzzy_engine


def reset_fuzzy_ontology_engine(license_params: Optional[Dict] = None):
    """퍼지 온톨로지 엔진 재초기화"""
    global _fuzzy_engine
    _fuzzy_engine = None
    get_fuzzy_ontology_engine(license_params)
