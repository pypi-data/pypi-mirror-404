"""
Context Graph Module - Initial Context Scan System

Context Graph의 노드(Context)와 엣지(관계)를 관리합니다.
설계 원칙:
- P1: Global First, Deep Later (전체 구조 우선)
- P2: Structure over Semantics (구조 > 의미)
- P3: Zero-Token by Default (로컬 분석 우선)
- P5: Context Graph is Source of Truth (그래프가 진실의 원천)
"""

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SemanticLevel(str, Enum):
    """Context의 의미 분석 수준"""

    SHALLOW = "shallow"  # 구조만 알고 있음
    RESOLVING = "resolving"  # deep 분석 진행 중
    DEEP = "deep"  # 의미 포함


class ContextStatus(str, Enum):
    """Context의 상태"""

    ACTIVE = "active"  # 활성 상태
    STALE = "stale"  # 구조 변경 감지됨
    RESOLVING = "resolving"  # 분석 중


class EdgeRelation(str, Enum):
    """Edge의 관계 유형"""

    IMPORTS = "imports"  # A가 B를 import
    EXPORTS = "exports"  # A가 B를 export
    EXTENDS = "extends"  # A가 B를 상속
    IMPLEMENTS = "implements"  # A가 B를 구현
    USES = "uses"  # A가 B를 사용


@dataclass
class ContextMetadata:
    """Context의 메타데이터"""

    exports: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    types: List[str] = field(default_factory=list)
    has_default_export: bool = False
    parse_error: bool = False
    error_message: Optional[str] = None
    file_hash: Optional[str] = None
    ast_hash: Optional[str] = None
    line_count: int = 0
    size_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextMetadata":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ContextNode:
    """
    Context Graph의 노드 (파일 단위 Context)

    context_id 형식: file://{relative_path}
    예: file://src/payment/retry.ts
    """

    context_id: str
    file_path: str
    language: str
    semantic_level: SemanticLevel = SemanticLevel.SHALLOW
    status: ContextStatus = ContextStatus.ACTIVE
    metadata: ContextMetadata = field(default_factory=ContextMetadata)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: Optional[str] = None  # Deep scan 시 채워짐
    description: Optional[str] = None  # Deep scan 시 채워짐

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "file_path": self.file_path,
            "language": self.language,
            "semantic_level": self.semantic_level.value,
            "status": self.status.value,
            "metadata": self.metadata.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "summary": self.summary,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextNode":
        metadata = ContextMetadata.from_dict(data.get("metadata", {}))
        return cls(
            context_id=data["context_id"],
            file_path=data["file_path"],
            language=data["language"],
            semantic_level=SemanticLevel(data.get("semantic_level", "shallow")),
            status=ContextStatus(data.get("status", "active")),
            metadata=metadata,
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            summary=data.get("summary"),
            description=data.get("description"),
        )

    def mark_stale(self) -> None:
        """구조 변경 감지 시 stale 상태로 전환"""
        self.status = ContextStatus.STALE
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def start_resolving(self) -> None:
        """Deep 분석 시작"""
        self.status = ContextStatus.RESOLVING
        self.semantic_level = SemanticLevel.RESOLVING
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def complete_deep_scan(self, summary: str, description: str) -> None:
        """Deep 분석 완료"""
        self.status = ContextStatus.ACTIVE
        self.semantic_level = SemanticLevel.DEEP
        self.summary = summary
        self.description = description
        self.updated_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ContextEdge:
    """
    Context Graph의 엣지 (Context 간 관계)
    """

    from_context: str  # source context_id
    to_context: str  # target context_id
    relation: EdgeRelation
    import_name: Optional[str] = None  # 실제 import된 이름
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_context,
            "to": self.to_context,
            "relation": self.relation.value,
            "import_name": self.import_name,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextEdge":
        return cls(
            from_context=data["from"],
            to_context=data["to"],
            relation=EdgeRelation(data.get("relation", "imports")),
            import_name=data.get("import_name"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )


class ContextGraph:
    """
    Context Graph 관리자

    프로젝트의 모든 Context(파일)와 그들 간의 관계(import/export)를 관리합니다.

    저장 구조:
    ~/.cortex/context_graphs/{project_id}/
    ├── nodes.json       # 모든 노드
    ├── edges.json       # 모든 엣지
    └── index.json       # 메타데이터 인덱스
    """

    def __init__(self, project_id: str, base_path: Optional[str] = None):
        self.project_id = project_id
        self.base_path = (
            Path(base_path)
            if base_path
            else Path.home() / ".cortex" / "context_graphs" / project_id
        )

        self.nodes: Dict[str, ContextNode] = {}  # context_id -> ContextNode
        self.edges: List[ContextEdge] = []
        self._edges_by_source: Dict[str, List[ContextEdge]] = {}  # from_context -> [edges]
        self._edges_by_target: Dict[str, List[ContextEdge]] = {}  # to_context -> [edges]

        self.base_path.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        """저장된 그래프 로드"""
        nodes_path = self.base_path / "nodes.json"
        edges_path = self.base_path / "edges.json"

        if nodes_path.exists():
            try:
                with open(nodes_path, "r", encoding="utf-8") as f:
                    nodes_data = json.load(f)
                    for node_data in nodes_data:
                        node = ContextNode.from_dict(node_data)
                        self.nodes[node.context_id] = node
            except Exception as e:
                logger.error(f"Failed to load nodes: {e}")

        if edges_path.exists():
            try:
                with open(edges_path, "r", encoding="utf-8") as f:
                    edges_data = json.load(f)
                    for edge_data in edges_data:
                        edge = ContextEdge.from_dict(edge_data)
                        self._add_edge_to_index(edge)
            except Exception as e:
                logger.error(f"Failed to load edges: {e}")

    def _save(self) -> None:
        """그래프 저장 (내부용)"""
        nodes_path = self.base_path / "nodes.json"
        edges_path = self.base_path / "edges.json"
        index_path = self.base_path / "index.json"

        try:
            # 디렉토리 자동 생성
            self.base_path.mkdir(parents=True, exist_ok=True)

            with open(nodes_path, "w", encoding="utf-8") as f:
                json.dump(
                    [node.to_dict() for node in self.nodes.values()],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            with open(edges_path, "w", encoding="utf-8") as f:
                json.dump([edge.to_dict() for edge in self.edges], f, indent=2, ensure_ascii=False)

            # 인덱스 메타데이터 저장
            index_data = {
                "project_id": self.project_id,
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "languages": list(set(n.language for n in self.nodes.values())),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save graph: {e}")

    def save(self) -> None:
        """그래프 저장 (외부 API)"""
        self._save()

    def _add_edge_to_index(self, edge: ContextEdge) -> None:
        """엣지를 인덱스에 추가"""
        self.edges.append(edge)

        if edge.from_context not in self._edges_by_source:
            self._edges_by_source[edge.from_context] = []
        self._edges_by_source[edge.from_context].append(edge)

        if edge.to_context not in self._edges_by_target:
            self._edges_by_target[edge.to_context] = []
        self._edges_by_target[edge.to_context].append(edge)

    @staticmethod
    def create_context_id(project_root: str, file_path: str) -> str:
        """
        파일 경로에서 context_id 생성

        Args:
            project_root: 프로젝트 루트 경로
            file_path: 파일 절대 경로

        Returns:
            context_id (예: file://src/payment/retry.ts)
        """
        rel_path = os.path.relpath(file_path, project_root)
        # Windows 경로 구분자를 Unix 스타일로 변환
        rel_path = rel_path.replace("\\", "/")
        return f"file://{rel_path}"

    @staticmethod
    def get_language_from_extension(file_path: str) -> str:
        """파일 확장자에서 언어 추출"""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".kt": "kotlin",
            ".kts": "kotlin",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".swift": "swift",
            ".scala": "scala",
            ".vue": "vue",
            ".svelte": "svelte",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".xml": "xml",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".less": "less",
            ".sql": "sql",
            ".sh": "shell",
            ".bash": "shell",
            ".zsh": "shell",
        }
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, "unknown")

    @staticmethod
    def compute_file_hash(file_path: str) -> Optional[str]:
        """파일 해시 계산"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception:
            return None

    def add_node(self, node: ContextNode) -> None:
        """노드 추가 (context_id 재사용 금지 원칙 적용)"""
        if node.context_id in self.nodes:
            # 기존 노드 업데이트
            existing = self.nodes[node.context_id]
            existing.metadata = node.metadata
            existing.updated_at = datetime.now(timezone.utc).isoformat()

            # 파일 삭제 감지: 새 노드의 file_hash가 None이면 파일이 삭제됨
            if existing.metadata.file_hash and not node.metadata.file_hash:
                logger.warning(f"File deleted detected for {node.context_id}, marking as stale")
                existing.mark_stale()
            # 파일 해시 변경 확인
            elif (
                existing.metadata.file_hash
                and node.metadata.file_hash
                and existing.metadata.file_hash != node.metadata.file_hash
            ):
                existing.mark_stale()
        else:
            self.nodes[node.context_id] = node

        self._save()

    def update_node(self, node: ContextNode) -> None:
        """노드 업데이트 (Phase C Lazy Resolution 등에서 사용)"""
        if node.context_id in self.nodes:
            self.nodes[node.context_id] = node
            self._save()
        else:
            raise ValueError(f"Node with context_id '{node.context_id}' does not exist")

    def add_edge(self, edge: ContextEdge) -> None:
        """엣지 추가 (중복 방지)"""
        # 중복 검사
        for existing in self.edges:
            if (
                existing.from_context == edge.from_context
                and existing.to_context == edge.to_context
                and existing.relation == edge.relation
            ):
                return  # 이미 존재하면 스킵

        self._add_edge_to_index(edge)
        self._save()

    def get_node(self, context_id: str) -> Optional[ContextNode]:
        """노드 조회"""
        return self.nodes.get(context_id)

    def get_outgoing_edges(self, context_id: str) -> List[ContextEdge]:
        """노드에서 나가는 엣지 조회 (이 파일이 import하는 것들)"""
        return self._edges_by_source.get(context_id, [])

    def get_incoming_edges(self, context_id: str) -> List[ContextEdge]:
        """노드로 들어오는 엣지 조회 (이 파일을 import하는 것들)"""
        return self._edges_by_target.get(context_id, [])

    def get_related_contexts(
        self, context_id: str, depth: int = 1, _visited: Optional[Set[str]] = None
    ) -> Set[str]:
        """
        관련 Context ID 조회 (Graph Traversal)

        Args:
            context_id: 시작 context_id
            depth: 탐색 깊이 (기본 1)
            _visited: 내부 사용, 이미 방문한 노드 (순환 참조 방지)

        Returns:
            관련된 context_id 집합
        """
        if depth <= 0:
            return set()

        # 순환 참조 방지: 방문 추적 초기화
        if _visited is None:
            _visited = set()

        # 이미 방문한 노드면 종료
        if context_id in _visited:
            return set()

        _visited.add(context_id)

        # 안전장치: 최대 탐색 노드 수 제한 (1000개)
        if len(_visited) > 1000:
            logger.warning(
                f"get_related_contexts: 최대 재귀 깊이 도달 (1000 nodes), context_id={context_id}"
            )
            return set()

        related = set()

        # 직접 연결된 노드
        for edge in self.get_outgoing_edges(context_id):
            related.add(edge.to_context)
        for edge in self.get_incoming_edges(context_id):
            related.add(edge.from_context)

        # 깊이가 1보다 크면 재귀 탐색
        if depth > 1:
            next_level = set()
            for related_id in related:
                # 이미 방문한 노드는 재방문 안 함
                if related_id not in _visited:
                    next_level.update(self.get_related_contexts(related_id, depth - 1, _visited))
            related.update(next_level)

        # 자기 자신 제외
        related.discard(context_id)
        return related

    def get_contexts_by_status(self, status: ContextStatus) -> List[ContextNode]:
        """상태별 Context 조회"""
        return [n for n in self.nodes.values() if n.status == status]

    def get_contexts_by_semantic_level(self, level: SemanticLevel) -> List[ContextNode]:
        """의미 분석 수준별 Context 조회"""
        return [n for n in self.nodes.values() if n.semantic_level == level]

    def get_all_nodes(self) -> List[ContextNode]:
        """모든 Context 노드 조회"""
        return list(self.nodes.values())

    def get_shallow_contexts(self) -> List[ContextNode]:
        """Shallow 상태 Context 조회"""
        return self.get_contexts_by_semantic_level(SemanticLevel.SHALLOW)

    def get_deep_contexts(self) -> List[ContextNode]:
        """Deep 상태 Context 조회"""
        return self.get_contexts_by_semantic_level(SemanticLevel.DEEP)

    def get_stale_contexts(self) -> List[ContextNode]:
        """Stale 상태 Context 조회"""
        return self.get_contexts_by_status(ContextStatus.STALE)

    def mark_all_stale(self) -> None:
        """모든 노드를 stale로 표시 (전체 재스캔 전)"""
        for node in self.nodes.values():
            node.mark_stale()
        self._save()

    def remove_stale_nodes(self) -> int:
        """Stale 노드 제거 (재스캔 후 업데이트되지 않은 노드)"""
        stale_ids = [n.context_id for n in self.nodes.values() if n.status == ContextStatus.STALE]
        for context_id in stale_ids:
            del self.nodes[context_id]

        # 관련 엣지도 제거
        self.edges = [
            e
            for e in self.edges
            if e.from_context not in stale_ids and e.to_context not in stale_ids
        ]
        self._rebuild_edge_index()
        self._save()
        return len(stale_ids)

    def _rebuild_edge_index(self) -> None:
        """엣지 인덱스 재구축"""
        self._edges_by_source = {}
        self._edges_by_target = {}
        for edge in self.edges:
            if edge.from_context not in self._edges_by_source:
                self._edges_by_source[edge.from_context] = []
            self._edges_by_source[edge.from_context].append(edge)

            if edge.to_context not in self._edges_by_target:
                self._edges_by_target[edge.to_context] = []
            self._edges_by_target[edge.to_context].append(edge)

    def clear(self) -> None:
        """그래프 초기화"""
        self.nodes.clear()
        self.edges.clear()
        self._edges_by_source.clear()
        self._edges_by_target.clear()
        self._save()

    def get_statistics(self) -> Dict[str, Any]:
        """그래프 통계"""
        languages = {}
        for node in self.nodes.values():
            languages[node.language] = languages.get(node.language, 0) + 1

        return {
            "project_id": self.project_id,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "shallow_count": len(self.get_shallow_contexts()),
            "deep_count": len(self.get_deep_contexts()),
            "stale_count": len(self.get_stale_contexts()),
            "languages": languages,
            "base_path": str(self.base_path),
        }

    def to_dict(self) -> Dict[str, Any]:
        """전체 그래프를 딕셔너리로 변환"""
        return {
            "project_id": self.project_id,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "statistics": self.get_statistics(),
        }

    def export_for_extension(self) -> Dict[str, Any]:
        """Extension UI용 데이터 내보내기 (경량화)"""
        return {
            "project_id": self.project_id,
            "contexts": [
                {
                    "context_id": n.context_id,
                    "file_path": n.file_path,
                    "language": n.language,
                    "semantic_level": n.semantic_level.value,
                    "status": n.status.value,
                    "has_summary": n.summary is not None,
                }
                for n in self.nodes.values()
            ],
            "statistics": {
                "total": len(self.nodes),
                "shallow": len(self.get_shallow_contexts()),
                "deep": len(self.get_deep_contexts()),
                "stale": len(self.get_stale_contexts()),
            },
        }


# 싱글톤 인스턴스 관리
_graph_instances: Dict[str, ContextGraph] = {}


def get_context_graph(project_id: str, base_path: Optional[str] = None) -> ContextGraph:
    """
    프로젝트별 Context Graph 인스턴스 반환 (싱글톤)
    """
    if project_id not in _graph_instances:
        _graph_instances[project_id] = ContextGraph(project_id, base_path)
    return _graph_instances[project_id]


def clear_context_graph(project_id: str) -> None:
    """
    프로젝트 Context Graph 인스턴스 제거 (메모리 누수 방지)

    메모리 정리 절차:
    1. clear() 호출: 모든 내부 컬렉션 비우기
    2. 명시적 None 할당: 순환 참조 해제
    3. 싱글톤 딕셔너리에서 제거
    4. GC 트리거: 즉시 메모리 회수
    """
    if project_id in _graph_instances:
        import gc

        graph = _graph_instances[project_id]

        # Step 1: 내부 컬렉션 정리 (clear() 메서드 사용)
        graph.clear()

        # Step 2: 순환 참조 해제를 위한 명시적 정리
        # (clear()가 이미 .clear()를 호출하지만, 인스턴스 자체의 참조를 끊기 위함)
        graph.nodes = {}
        graph.edges = []
        graph._edges_by_source = {}
        graph._edges_by_target = {}

        # Step 3: 싱글톤 딕셔너리에서 제거
        del _graph_instances[project_id]

        # Step 4: 즉시 가비지 컬렉션 실행
        # (대규모 그래프의 경우 즉시 메모리 회수가 중요)
        gc.collect()

        logger.info(f"[MEMORY] Context Graph cleared and GC triggered for project: {project_id}")


# ============================================================================
# MCP Tool Interface Functions
# ============================================================================


def get_context_graph_info(project_id: str) -> Dict[str, Any]:
    """
    Context Graph 통계 조회 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 고유 식별자

    Returns:
        Context Graph 상태 (노드 수, 엣지 수, 언어별 분포 등)
    """
    graph = get_context_graph(project_id)

    # 노드 통계
    nodes = graph.nodes
    total_nodes = len(nodes)

    # 언어별 분포
    language_distribution = {}
    for node in nodes.values():
        lang = node.metadata.get("language", "unknown")
        language_distribution[lang] = language_distribution.get(lang, 0) + 1

    # 레벨별 분포
    level_distribution = {}
    for node in nodes.values():
        level = node.level.value
        level_distribution[level] = level_distribution.get(level, 0) + 1

    # 엣지 통계
    total_edges = sum(len(node.dependencies) for node in nodes.values())

    # 최근 업데이트
    last_updated = None
    if nodes:
        latest_node = max(nodes.values(), key=lambda n: n.metadata.get("scanned_at", ""))
        last_updated = latest_node.metadata.get("scanned_at")

    return {
        "project_id": project_id,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "language_distribution": language_distribution,
        "level_distribution": level_distribution,
        "last_updated": last_updated,
        "has_graph": total_nodes > 0,
    }
