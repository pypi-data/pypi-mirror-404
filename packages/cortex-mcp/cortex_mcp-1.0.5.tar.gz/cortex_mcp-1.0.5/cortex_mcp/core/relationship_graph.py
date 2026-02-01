#!/usr/bin/env python3
"""
Context Relationship Graph - Tier 1 Implementation

핵심 기능:
- Context 간 관계를 그래프로 관리
- 자동 관계 추출 (import, 폴더 구조, Reference History)
- Cross-Node Context Chain 추적
- BFS 기반 N-hop 탐색

Tier 1 (Free): 구조적 관계 (DEPENDS_ON, PART_OF, REFERENCES)
Tier 2 (Pro+): 의미적 관계 (RELATED_TO, FREQUENTLY_USED_WITH, PRECEDES)
Tier 3 (Enterprise): 명시적 관계 (REQUIRES, CONFLICTS_WITH, ENFORCES)

설계 원칙:
1. Zero-Effort: 관계 추출은 자동 (초기 스캔 시)
2. Zero-Loss: 관계 데이터는 JSON으로 영구 저장
3. Performance: NetworkX 인메모리 그래프 (10K 노드까지 빠름)

Author: Cortex Development Team
Date: 2026-01-02
Version: 1.0.0
"""

import json
import logging
import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class RelationshipGraph:
    """
    Context 간 관계를 방향성 그래프로 관리

    노드: Context (file:// URI)
    엣지: 관계 타입 + 메타데이터

    관계 타입:
    - DEPENDS_ON: import/require 의존성
    - PART_OF: 폴더 구조 포함 관계
    - REFERENCES: 함수/클래스 참조
    - IMPLEMENTS: 상속 관계
    - RELATED_TO: 임베딩 유사도 기반 (Tier 2)
    - FREQUENTLY_USED_WITH: Reference History 패턴 (Tier 2)
    - PRECEDES: 워크플로우 순서 (Tier 2)
    - REQUIRES: 비즈니스 규칙 (Tier 3)
    - CONFLICTS_WITH: 정책 충돌 (Tier 3)
    """

    # 관계 타입별 Tier 매핑
    TIER_MAPPING = {
        # Tier 1: Free (자동 추출)
        "DEPENDS_ON": 1,
        "PART_OF": 1,
        "REFERENCES": 1,
        "IMPLEMENTS": 1,

        # Tier 2: Pro+ (의미적 분석)
        "RELATED_TO": 2,
        "FREQUENTLY_USED_WITH": 2,
        "PRECEDES": 2,

        # Tier 3: Enterprise (수동 정의)
        "REQUIRES": 3,
        "CONFLICTS_WITH": 3,
        "ENFORCES": 3,
        "FORBIDS": 3,
    }

    def __init__(self, project_id: str, storage_path: Optional[Path] = None):
        """
        초기화

        Args:
            project_id: 프로젝트 고유 ID
            storage_path: 관계 데이터 저장 경로 (기본: ~/.cortex/memory/{project_id})
        """
        self.project_id = project_id
        self.graph = nx.DiGraph()

        # 저장 경로 설정
        if storage_path is None:
            home = Path.home()
            storage_path = home / ".cortex" / "memory" / project_id
        self.storage_path = storage_path if isinstance(storage_path, Path) else Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 관계 그래프 파일 경로
        self.graph_file = self.storage_path / "_relationship_graph.json"

        # 기존 그래프 로드
        self._load_graph()

        logger.info(f"[RelationshipGraph] Initialized for project {project_id}")
        logger.info(f"[RelationshipGraph] Nodes: {self.graph.number_of_nodes()}, Edges: {self.graph.number_of_edges()}")

    def add_relation(
        self,
        source_ctx: str,
        target_ctx: str,
        rel_type: str,
        confidence: float = 1.0,
        auto_extracted: bool = True,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        관계 추가

        Args:
            source_ctx: 출발 Context ID (file:// URI)
            target_ctx: 도착 Context ID (file:// URI)
            rel_type: 관계 타입 (DEPENDS_ON, PART_OF, ...)
            confidence: 신뢰도 (0.0 ~ 1.0)
            auto_extracted: 자동 추출 여부
            metadata: 추가 메타데이터

        Returns:
            bool: 성공 여부
        """
        # 관계 타입 검증
        if rel_type not in self.TIER_MAPPING:
            logger.warning(f"[RelationshipGraph] Unknown relation type: {rel_type}")
            return False

        # 노드 추가 (없으면)
        if source_ctx not in self.graph:
            self.graph.add_node(source_ctx)
        if target_ctx not in self.graph:
            self.graph.add_node(target_ctx)

        # 엣지 메타데이터 구성
        edge_data = {
            "type": rel_type,
            "confidence": confidence,
            "auto_extracted": auto_extracted,
            "created_at": datetime.utcnow().isoformat(),
            "tier": self.TIER_MAPPING[rel_type],
        }

        if metadata:
            edge_data.update(metadata)

        # 엣지 추가
        self.graph.add_edge(source_ctx, target_ctx, **edge_data)

        logger.debug(f"[RelationshipGraph] Added: {source_ctx} --[{rel_type}]--> {target_ctx}")
        return True

    def get_related_contexts(
        self,
        context_id: str,
        max_depth: int = 2,
        relation_types: Optional[List[str]] = None,
        min_confidence: float = 0.0
    ) -> List[Dict]:
        """
        특정 Context와 관련된 모든 Context 반환

        Args:
            context_id: 기준 Context ID
            max_depth: 탐색 깊이 (기본 2단계)
            relation_types: 필터링할 관계 타입 리스트
            min_confidence: 최소 신뢰도

        Returns:
            [
                {
                    "context_id": "file://auth.py",
                    "relation": "DEPENDS_ON",
                    "distance": 1,
                    "confidence": 0.95,
                    "path": ["login.py", "auth.py"]
                }
            ]
        """
        if context_id not in self.graph:
            logger.warning(f"[RelationshipGraph] Context not in graph: {context_id}")
            return []

        related = []

        # BFS로 N-hop 탐색
        try:
            # 모든 경로 찾기 (최대 깊이 제한)
            for target in self.graph.nodes():
                if target == context_id:
                    continue

                try:
                    # 최단 경로 찾기
                    path = nx.shortest_path(self.graph, context_id, target)

                    if len(path) <= max_depth + 1:  # +1은 출발점 포함
                        # 경로상의 관계 수집
                        relations = []
                        for i in range(len(path) - 1):
                            edge_data = self.graph[path[i]][path[i + 1]]

                            # 관계 타입 필터링
                            if relation_types and edge_data["type"] not in relation_types:
                                break

                            # 신뢰도 필터링
                            if edge_data["confidence"] < min_confidence:
                                break

                            relations.append(edge_data["type"])

                        # 필터 통과 시 추가
                        if len(relations) == len(path) - 1:
                            related.append({
                                "context_id": target,
                                "relation": relations[-1],  # 마지막 관계 타입
                                "distance": len(path) - 1,
                                "confidence": self.graph[path[-2]][path[-1]]["confidence"],
                                "path": path,
                                "relation_chain": relations,
                            })

                except nx.NetworkXNoPath:
                    continue

        except Exception as e:
            logger.error(f"[RelationshipGraph] Error in BFS traversal: {e}")

        # 거리 순으로 정렬
        related.sort(key=lambda x: (x["distance"], -x["confidence"]))

        logger.info(f"[RelationshipGraph] Found {len(related)} related contexts for {context_id}")
        return related

    def get_incoming_relations(self, context_id: str) -> List[Dict]:
        """
        특정 Context로 들어오는 관계 반환

        Args:
            context_id: 대상 Context ID

        Returns:
            [{"source": "...", "relation": "DEPENDS_ON", "confidence": 0.95}]
        """
        if context_id not in self.graph:
            return []

        incoming = []
        for source, target, data in self.graph.in_edges(context_id, data=True):
            incoming.append({
                "source": source,
                "relation": data["type"],
                "confidence": data["confidence"],
                "auto_extracted": data["auto_extracted"],
            })

        return incoming

    def get_outgoing_relations(self, context_id: str) -> List[Dict]:
        """
        특정 Context에서 나가는 관계 반환

        Args:
            context_id: 출발 Context ID

        Returns:
            [{"target": "...", "relation": "DEPENDS_ON", "confidence": 0.95}]
        """
        if context_id not in self.graph:
            return []

        outgoing = []
        for source, target, data in self.graph.out_edges(context_id, data=True):
            outgoing.append({
                "target": target,
                "relation": data["type"],
                "confidence": data["confidence"],
                "auto_extracted": data["auto_extracted"],
            })

        return outgoing

    def get_workflow_chain(
        self,
        start_ctx: str,
        end_ctx: Optional[str] = None,
        max_depth: int = 5
    ) -> List[List[str]]:
        """
        워크플로우 체인 추적 (PRECEDES 관계)

        Args:
            start_ctx: 시작 Context
            end_ctx: 종료 Context (없으면 모든 경로)
            max_depth: 최대 깊이

        Returns:
            [[ctx1, ctx2, ctx3], [ctx1, ctx4, ctx5]]
        """
        if start_ctx not in self.graph:
            return []

        chains = []

        if end_ctx:
            # 특정 종료점까지의 경로
            try:
                all_paths = nx.all_simple_paths(
                    self.graph,
                    start_ctx,
                    end_ctx,
                    cutoff=max_depth
                )
                for path in all_paths:
                    # PRECEDES 관계만 포함된 경로인지 확인
                    valid = True
                    for i in range(len(path) - 1):
                        edge_data = self.graph[path[i]][path[i + 1]]
                        if edge_data["type"] != "PRECEDES":
                            valid = False
                            break
                    if valid:
                        chains.append(path)
            except nx.NetworkXNoPath:
                pass
        else:
            # 모든 가능한 체인
            def dfs(current, path, depth):
                if depth > max_depth:
                    return

                # 현재 경로 저장
                if len(path) > 1:
                    chains.append(path.copy())

                # 다음 노드 탐색
                for _, next_node, data in self.graph.out_edges(current, data=True):
                    if data["type"] == "PRECEDES" and next_node not in path:
                        path.append(next_node)
                        dfs(next_node, path, depth + 1)
                        path.pop()

            dfs(start_ctx, [start_ctx], 0)

        logger.info(f"[RelationshipGraph] Found {len(chains)} workflow chains from {start_ctx}")
        return chains

    def get_statistics(self) -> Dict:
        """
        관계 그래프 통계 반환

        Returns:
            {
                "nodes": 100,
                "edges": 500,
                "relation_types": {"DEPENDS_ON": 200, ...},
                "tiers": {1: 300, 2: 150, 3: 50},
                "avg_degree": 5.0
            }
        """
        stats = {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "relation_types": defaultdict(int),
            "tiers": defaultdict(int),
            "avg_degree": 0.0,
        }

        # 관계 타입별 집계
        for u, v, data in self.graph.edges(data=True):
            rel_type = data["type"]
            stats["relation_types"][rel_type] += 1
            stats["tiers"][data["tier"]] += 1

        # 평균 차수 계산
        if stats["nodes"] > 0:
            stats["avg_degree"] = stats["edges"] / stats["nodes"]

        return dict(stats)

    def save(self) -> bool:
        """
        관계 그래프를 JSON 파일로 저장

        Returns:
            bool: 성공 여부
        """
        try:
            # NetworkX 그래프를 JSON 직렬화 가능한 형태로 변환
            data = {
                "project_id": self.project_id,
                "created_at": datetime.utcnow().isoformat(),
                "nodes": [
                    {"id": node, "metadata": self.graph.nodes[node]}
                    for node in self.graph.nodes()
                ],
                "edges": [
                    {
                        "source": u,
                        "target": v,
                        **data
                    }
                    for u, v, data in self.graph.edges(data=True)
                ],
                "statistics": self.get_statistics()
            }

            # JSON 저장
            with open(self.graph_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"[RelationshipGraph] Saved to {self.graph_file}")
            return True

        except Exception as e:
            logger.error(f"[RelationshipGraph] Failed to save: {e}")
            return False

    def _load_graph(self) -> bool:
        """
        저장된 관계 그래프 로드

        Returns:
            bool: 성공 여부
        """
        if not self.graph_file.exists():
            logger.info(f"[RelationshipGraph] No existing graph file: {self.graph_file}")
            return False

        try:
            with open(self.graph_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 노드 추가
            for node_data in data.get("nodes", []):
                node_id = node_data["id"]
                metadata = node_data.get("metadata", {})
                self.graph.add_node(node_id, **metadata)

            # 엣지 추가
            for edge_data in data.get("edges", []):
                source = edge_data.pop("source")
                target = edge_data.pop("target")
                self.graph.add_edge(source, target, **edge_data)

            logger.info(f"[RelationshipGraph] Loaded {len(data['nodes'])} nodes, {len(data['edges'])} edges")
            return True

        except Exception as e:
            logger.error(f"[RelationshipGraph] Failed to load graph: {e}")
            return False

    def visualize(self, output_path: Optional[Path] = None) -> str:
        """
        관계 그래프 시각화 (Mermaid 다이어그램)

        Args:
            output_path: 출력 파일 경로 (.md)

        Returns:
            str: Mermaid 다이어그램 코드
        """
        mermaid = ["graph LR"]

        # 엣지 추가
        for u, v, data in self.graph.edges(data=True):
            rel_type = data["type"]
            # 노드 ID 간소화 (파일명만)
            u_label = Path(u.replace("file://", "")).name
            v_label = Path(v.replace("file://", "")).name

            mermaid.append(f'    {u_label} -->|{rel_type}| {v_label}')

        mermaid_code = "\n".join(mermaid)

        # 파일 저장 (옵션)
        if output_path:
            output_path = Path(output_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("```mermaid\n")
                f.write(mermaid_code)
                f.write("\n```\n")
            logger.info(f"[RelationshipGraph] Visualization saved to {output_path}")

        return mermaid_code


# 자동 관계 추출 헬퍼 함수들

def extract_import_relations(file_path: str, project_root: Path) -> List[Tuple[str, str]]:
    """
    파일의 import 문을 분석하여 DEPENDS_ON 관계 추출

    Args:
        file_path: 분석할 파일 경로
        project_root: 프로젝트 루트 경로

    Returns:
        [(source_file, target_file), ...]
    """
    # TODO: AST 파서 통합 (ast_parser.py 활용)
    relations = []
    return relations


def extract_folder_relations(project_root: Path) -> List[Tuple[str, str]]:
    """
    폴더 구조를 분석하여 PART_OF 관계 추출

    Args:
        project_root: 프로젝트 루트 경로

    Returns:
        [(child_file, parent_folder), ...]
    """
    # TODO: 폴더 구조 분석 구현
    relations = []
    return relations
