"""
Semantic Web Engine for Cortex MCP (Enterprise Only)

OWL/RDF 스타일의 지식 그래프 추론 엔진.
Enterprise 고객을 위한 고급 맥락 관계 분석 기능 제공.

Features:
- 전이적 관계 추론 (A→B, B→C ⇒ A→C)
- 충돌 감지 (정책 충돌, 버전 충돌)
- N-hop 관계 탐색
- 관계 타입 정의 (depends_on, conflicts_with, extends, related_to)
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# 로컬 config import
try:
    from ..config import config
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import config


class RelationType(Enum):
    """관계 타입 정의"""

    DEPENDS_ON = "depends_on"  # A가 B에 의존 (A → B)
    CONFLICTS_WITH = "conflicts_with"  # A와 B가 충돌
    EXTENDS = "extends"  # A가 B를 확장
    RELATED_TO = "related_to"  # A와 B가 관련됨
    SUPERSEDES = "supersedes"  # A가 B를 대체함


@dataclass
class Relation:
    """맥락 간 관계"""

    source: str  # 소스 맥락 ID
    target: str  # 타겟 맥락 ID
    relation_type: RelationType  # 관계 타입
    confidence: float = 1.0  # 신뢰도 (0.0 ~ 1.0)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: "")

    def __post_init__(self):
        """ID 자동 생성"""
        if not self.id:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S%f")[:20]
            self.id = f"rel_{self.source}_{self.target}_{timestamp}"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type.value,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Relation":
        return cls(
            id=data.get("id", ""),
            source=data["source"],
            target=data["target"],
            relation_type=RelationType(data["relation_type"]),
            confidence=data.get("confidence", 1.0),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Conflict:
    """충돌 정보"""

    context_a: str
    context_b: str
    conflict_type: str  # "policy", "version", "semantic"
    description: str
    severity: str = "warning"  # "info", "warning", "error"
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        return {
            "context_a": self.context_a,
            "context_b": self.context_b,
            "conflict_type": self.conflict_type,
            "description": self.description,
            "severity": self.severity,
            "detected_at": self.detected_at,
        }


@dataclass
class InferenceResult:
    """추론 결과"""

    inferred_relations: List[Relation]
    conflicts: List[Conflict]
    path: List[str]  # 추론 경로
    confidence: float  # 전체 신뢰도


class SemanticWebEngine:
    """
    시맨틱 웹 추론 엔진 (Enterprise 전용)

    OWL/RDF 스타일의 지식 그래프를 구축하고
    맥락 간 관계를 추론합니다.
    """

    def __init__(self, project_id: str, enabled: bool = True):
        """
        Args:
            project_id: 프로젝트 식별자
            enabled: 기능 활성화 여부 (Enterprise 전용)
        """
        self.project_id = project_id
        self.enabled = enabled

        # 관계 그래프 저장 경로
        self.graph_path = Path(config.memory_dir) / project_id / "_semantic_graph.json"

        # 관계 저장소
        self.relations: List[Relation] = []
        self.conflicts: List[Conflict] = []

        # 그래프 인덱스 (빠른 조회용)
        self._outgoing: Dict[str, List[Relation]] = {}  # source → relations
        self._incoming: Dict[str, List[Relation]] = {}  # target → relations

        # 기존 그래프 로드
        self._load_graph()

    def _load_graph(self) -> None:
        """저장된 그래프 로드"""
        if not self.graph_path.exists():
            return

        try:
            with open(self.graph_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.relations = [Relation.from_dict(r) for r in data.get("relations", [])]
            self.conflicts = [Conflict(**c) for c in data.get("conflicts", [])]

            # 인덱스 재구축
            self._rebuild_index()

        except Exception as e:
            print(f"[SemanticWeb] 그래프 로드 실패: {e}")

    def _save_graph(self) -> None:
        """그래프 저장"""
        try:
            self.graph_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "project_id": self.project_id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "relations": [r.to_dict() for r in self.relations],
                "conflicts": [c.to_dict() for c in self.conflicts],
            }

            with open(self.graph_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[SemanticWeb] 그래프 저장 실패: {e}")

    def _rebuild_index(self) -> None:
        """그래프 인덱스 재구축"""
        self._outgoing.clear()
        self._incoming.clear()

        for relation in self.relations:
            if relation.source not in self._outgoing:
                self._outgoing[relation.source] = []
            self._outgoing[relation.source].append(relation)

            if relation.target not in self._incoming:
                self._incoming[relation.target] = []
            self._incoming[relation.target].append(relation)

    def add_relation(
        self,
        source: str,
        target: str,
        relation_type: RelationType,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None,
    ) -> Relation:
        """
        관계 추가

        Args:
            source: 소스 맥락 ID
            target: 타겟 맥락 ID
            relation_type: 관계 타입
            confidence: 신뢰도 (0.0 ~ 1.0)
            metadata: 추가 메타데이터

        Returns:
            생성된 Relation 객체
        """
        if not self.enabled:
            raise RuntimeError("SemanticWebEngine is disabled (Enterprise only)")

        # 중복 체크
        for r in self.relations:
            if r.source == source and r.target == target and r.relation_type == relation_type:
                # 기존 관계 업데이트
                r.confidence = max(r.confidence, confidence)
                if metadata:
                    r.metadata.update(metadata)
                self._save_graph()
                return r

        # 새 관계 생성
        relation = Relation(
            source=source,
            target=target,
            relation_type=relation_type,
            confidence=confidence,
            metadata=metadata or {},
        )

        self.relations.append(relation)

        # 인덱스 업데이트
        if source not in self._outgoing:
            self._outgoing[source] = []
        self._outgoing[source].append(relation)

        if target not in self._incoming:
            self._incoming[target] = []
        self._incoming[target].append(relation)

        # 충돌 체크
        self._check_conflicts(relation)

        self._save_graph()
        return relation

    def remove_relation(
        self, source: str, target: str, relation_type: Optional[RelationType] = None
    ) -> bool:
        """
        관계 제거

        Args:
            source: 소스 맥락 ID
            target: 타겟 맥락 ID
            relation_type: 관계 타입 (None이면 모든 타입 제거)

        Returns:
            제거 성공 여부
        """
        if not self.enabled:
            return False

        removed = False
        new_relations = []

        for r in self.relations:
            if r.source == source and r.target == target:
                if relation_type is None or r.relation_type == relation_type:
                    removed = True
                    continue
            new_relations.append(r)

        if removed:
            self.relations = new_relations
            self._rebuild_index()
            self._save_graph()

        return removed

    def _check_conflicts(self, new_relation: Relation) -> None:
        """
        새 관계 추가 시 충돌 체크

        충돌 유형:
        1. 순환 의존성: A depends_on B, B depends_on A
        2. 충돌 관계: A conflicts_with B (명시적)
        3. 의미적 충돌: A supersedes B인데 A depends_on B
        """
        source = new_relation.source
        target = new_relation.target
        rel_type = new_relation.relation_type

        # 1. 순환 의존성 체크
        if rel_type == RelationType.DEPENDS_ON:
            path = self._find_path(target, source, RelationType.DEPENDS_ON)
            if path:
                conflict = Conflict(
                    context_a=source,
                    context_b=target,
                    conflict_type="circular_dependency",
                    description=f"순환 의존성 감지: {' → '.join(path + [source])}",
                    severity="error",
                )
                self.conflicts.append(conflict)

        # 2. 충돌 관계 전파 체크
        if rel_type == RelationType.CONFLICTS_WITH:
            # 양방향 충돌 확인
            conflict = Conflict(
                context_a=source,
                context_b=target,
                conflict_type="explicit_conflict",
                description=f"명시적 충돌 관계: {source} ↔ {target}",
                severity="warning",
            )
            self.conflicts.append(conflict)

        # 3. supersedes + depends_on 충돌
        if rel_type == RelationType.SUPERSEDES:
            # A supersedes B인데 A depends_on B이면 충돌
            for r in self._outgoing.get(source, []):
                if r.target == target and r.relation_type == RelationType.DEPENDS_ON:
                    conflict = Conflict(
                        context_a=source,
                        context_b=target,
                        conflict_type="semantic",
                        description=f"의미적 충돌: {source}가 {target}를 대체하면서 동시에 의존",
                        severity="warning",
                    )
                    self.conflicts.append(conflict)

    def _find_path(
        self, start: str, end: str, relation_type: RelationType, max_depth: int = 10
    ) -> Optional[List[str]]:
        """
        두 맥락 간 경로 탐색 (BFS)

        Args:
            start: 시작 맥락 ID
            end: 끝 맥락 ID
            relation_type: 탐색할 관계 타입
            max_depth: 최대 탐색 깊이

        Returns:
            경로가 있으면 맥락 ID 리스트, 없으면 None
        """
        if start == end:
            return [start]

        visited: Set[str] = set()
        queue: List[Tuple[str, List[str]]] = [(start, [start])]

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            for relation in self._outgoing.get(current, []):
                if relation.relation_type != relation_type:
                    continue

                next_node = relation.target
                new_path = path + [next_node]

                if next_node == end:
                    return new_path

                if next_node not in visited:
                    queue.append((next_node, new_path))

        return None

    def infer_transitive_relations(
        self,
        context_id: str,
        relation_type: RelationType = RelationType.DEPENDS_ON,
        max_depth: int = 5,
    ) -> InferenceResult:
        """
        전이적 관계 추론

        A depends_on B, B depends_on C → A depends_on C (암묵적)

        Args:
            context_id: 시작 맥락 ID
            relation_type: 추론할 관계 타입
            max_depth: 최대 추론 깊이

        Returns:
            InferenceResult 객체
        """
        if not self.enabled:
            return InferenceResult([], [], [], 0.0)

        inferred: List[Relation] = []
        visited: Set[str] = set()
        path: List[str] = [context_id]

        def dfs(current: str, depth: int, cumulative_confidence: float):
            if depth > max_depth:
                return
            if current in visited:
                return

            visited.add(current)

            for relation in self._outgoing.get(current, []):
                if relation.relation_type != relation_type:
                    continue

                next_node = relation.target
                new_confidence = cumulative_confidence * relation.confidence

                # 직접 관계가 아닌 경우만 추론 관계로 추가
                if next_node != context_id and depth > 0:
                    inferred_relation = Relation(
                        source=context_id,
                        target=next_node,
                        relation_type=relation_type,
                        confidence=new_confidence,
                        metadata={"inferred": True, "depth": depth + 1, "path": path + [next_node]},
                    )
                    inferred.append(inferred_relation)

                path.append(next_node)
                dfs(next_node, depth + 1, new_confidence)
                path.pop()

        dfs(context_id, 0, 1.0)

        # 평균 신뢰도 계산
        avg_confidence = sum(r.confidence for r in inferred) / len(inferred) if inferred else 0.0

        return InferenceResult(
            inferred_relations=inferred, conflicts=[], path=path, confidence=avg_confidence
        )

    def detect_conflicts(self, context_id: Optional[str] = None) -> List[Conflict]:
        """
        충돌 감지

        Args:
            context_id: 특정 맥락에 대한 충돌만 조회 (None이면 전체)

        Returns:
            Conflict 리스트
        """
        if not self.enabled:
            return []

        if context_id is None:
            return self.conflicts.copy()

        return [c for c in self.conflicts if c.context_a == context_id or c.context_b == context_id]

    def suggest_related_contexts(
        self, context_id: str, max_depth: int = 3, min_confidence: float = 0.3
    ) -> List[Tuple[str, float, List[str]]]:
        """
        N-hop 관계까지 탐색하여 관련 맥락 추천

        Args:
            context_id: 기준 맥락 ID
            max_depth: 최대 탐색 깊이
            min_confidence: 최소 신뢰도

        Returns:
            (맥락 ID, 관련도 점수, 경로) 튜플 리스트
        """
        if not self.enabled:
            return []

        results: Dict[str, Tuple[float, List[str]]] = {}
        visited: Set[str] = set()

        def bfs():
            queue: List[Tuple[str, float, List[str], int]] = [(context_id, 1.0, [context_id], 0)]

            while queue:
                current, confidence, path, depth = queue.pop(0)

                if depth > max_depth:
                    continue
                if current in visited:
                    continue

                visited.add(current)

                # 모든 관계 탐색 (양방향)
                relations = self._outgoing.get(current, []) + [
                    Relation(
                        source=r.target,
                        target=r.source,
                        relation_type=r.relation_type,
                        confidence=r.confidence,
                    )
                    for r in self._incoming.get(current, [])
                ]

                for relation in relations:
                    next_node = relation.target if relation.source == current else relation.source
                    if next_node == context_id:
                        continue

                    # 거리에 따른 감쇠
                    decay = 0.7**depth
                    new_confidence = confidence * relation.confidence * decay

                    if new_confidence < min_confidence:
                        continue

                    new_path = path + [next_node]

                    # 더 높은 신뢰도로 갱신
                    if next_node not in results or results[next_node][0] < new_confidence:
                        results[next_node] = (new_confidence, new_path)

                    queue.append((next_node, new_confidence, new_path, depth + 1))

        bfs()

        # 신뢰도 순으로 정렬
        sorted_results = sorted(
            [(ctx, score, path) for ctx, (score, path) in results.items()],
            key=lambda x: x[1],
            reverse=True,
        )

        return sorted_results

    def get_graph_stats(self) -> Dict:
        """그래프 통계 반환"""
        if not self.enabled:
            return {"enabled": False}

        relation_counts = {}
        for r in self.relations:
            rel_type = r.relation_type.value
            relation_counts[rel_type] = relation_counts.get(rel_type, 0) + 1

        return {
            "enabled": True,
            "project_id": self.project_id,
            "total_relations": len(self.relations),
            "total_conflicts": len(self.conflicts),
            "unique_contexts": len(
                set([r.source for r in self.relations] + [r.target for r in self.relations])
            ),
            "relation_counts": relation_counts,
            "conflict_severities": {
                "error": len([c for c in self.conflicts if c.severity == "error"]),
                "warning": len([c for c in self.conflicts if c.severity == "warning"]),
                "info": len([c for c in self.conflicts if c.severity == "info"]),
            },
        }

    def clear_graph(self) -> None:
        """그래프 초기화"""
        self.relations.clear()
        self.conflicts.clear()
        self._outgoing.clear()
        self._incoming.clear()
        self._save_graph()


# 테스트용 실행
if __name__ == "__main__":
    # Enterprise 시뮬레이션
    engine = SemanticWebEngine("test_project", enabled=True)

    # 관계 추가 테스트
    engine.add_relation("context_auth", "context_user", RelationType.DEPENDS_ON)
    engine.add_relation("context_user", "context_db", RelationType.DEPENDS_ON)
    engine.add_relation("context_api", "context_auth", RelationType.DEPENDS_ON)

    # 전이적 추론 테스트
    result = engine.infer_transitive_relations("context_api")
    print(f"전이적 추론 결과: {len(result.inferred_relations)}개")
    for r in result.inferred_relations:
        print(f"  {r.source} → {r.target} (confidence: {r.confidence:.2f})")

    # 관련 맥락 추천 테스트
    suggestions = engine.suggest_related_contexts("context_api")
    print(f"\n관련 맥락 추천: {len(suggestions)}개")
    for ctx, score, path in suggestions:
        print(f"  {ctx}: {score:.2f} ({' → '.join(path)})")

    # 통계 출력
    stats = engine.get_graph_stats()
    print(f"\n그래프 통계: {stats}")
