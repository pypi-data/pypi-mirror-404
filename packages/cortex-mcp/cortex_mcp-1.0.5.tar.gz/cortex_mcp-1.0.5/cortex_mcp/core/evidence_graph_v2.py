"""
Evidence Graph v2.0 - 전문가 패널 설계

목적: AI 주장을 검증할 객관적 근거 저장
설계: Dr. Elena Rodriguez (Graph Theory Expert, Stanford)
최적화: Maria Silva (Performance Engineer, Netflix)
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

import networkx as nx

logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """Evidence 타입 (Dr. Sarah Chen 제안)"""

    FILE_EXISTS = "file_exists"  # 파일 존재 증명
    CODE_CONTENT = "code_content"  # 코드 내용 증명
    GIT_COMMIT = "git_commit"  # Git 커밋 이력
    FUNCTION_SIGNATURE = "function_signature"  # 함수 시그니처
    CLASS_DEFINITION = "class_definition"  # 클래스 정의
    IMPORT_STATEMENT = "import_statement"  # import 문
    FILE_MODIFICATION = "file_modification"  # 파일 수정


class NodeType(Enum):
    """그래프 노드 타입 (Dr. Elena Rodriguez 설계)"""

    FILE = "file"
    CODE_BLOCK = "code_block"
    FUNCTION = "function"
    CLASS = "class"
    IMPORT = "import"
    COMMIT = "commit"


class EdgeType(Enum):
    """그래프 엣지 관계 (Dr. Elena Rodriguez 설계)"""

    CONTAINS = "contains"  # 파일 → 코드 블록
    DEFINES = "defines"  # 코드 블록 → 함수/클래스
    IMPORTS = "imports"  # 파일 → 의존성
    MODIFIES = "modifies"  # Commit → 파일
    SUPPORTS = "supports"  # Evidence → Claim


@dataclass
class Evidence:
    """Evidence 데이터 클래스 (Lisa Park 제안)"""

    evidence_id: str
    evidence_type: EvidenceType
    content: str  # 실제 내용 (코드, 파일 경로 등)
    source: str  # 출처 (파일 경로, Git SHA 등)
    timestamp: str  # ISO 8601 format
    confidence: float  # 0.0 ~ 1.0
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        result = asdict(self)
        result["evidence_type"] = self.evidence_type.value
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "Evidence":
        """딕셔너리에서 복원"""
        data = data.copy()
        data["evidence_type"] = EvidenceType(data["evidence_type"])
        return cls(**data)


class EvidenceGraphV2:
    """
    Evidence Graph v2.0

    개선 사항:
    1. 파일 저장/로드 (Lisa Park)
    2. 배치 추가 (성능 최적화)
    3. 인덱싱 (쿼리 최적화)
    4. 크기 제한 (메모리 관리)
    """

    def __init__(self, max_nodes: int = 100000):
        """
        Args:
            max_nodes: 최대 노드 수 (메모리 관리)
        """
        self.graph = nx.DiGraph()
        self.max_nodes = max_nodes
        self._evidence_index: Dict[str, Evidence] = {}  # 빠른 조회

    def add_evidence(self, evidence: Evidence) -> bool:
        """
        Evidence 추가

        Returns:
            성공 여부
        """
        # 메모리 제한 체크
        if len(self.graph.nodes) >= self.max_nodes:
            logger.warning(f"Evidence Graph 크기 제한 도달: {self.max_nodes} nodes")
            return False

        # 노드 추가
        node_id = evidence.evidence_id
        self.graph.add_node(
            node_id,
            type=NodeType.FILE.value,  # 기본 타입
            evidence_type=evidence.evidence_type.value,
            content=evidence.content,
            source=evidence.source,
            timestamp=evidence.timestamp,
            confidence=evidence.confidence,
            metadata=evidence.metadata or {},
        )

        # 인덱스 추가
        self._evidence_index[evidence.evidence_id] = evidence

        return True

    def add_evidence_batch(self, evidences: List[Evidence]) -> int:
        """
        Evidence 배치 추가 (성능 최적화)

        Returns:
            추가된 개수
        """
        added_count = 0
        for evidence in evidences:
            if self.add_evidence(evidence):
                added_count += 1
            else:
                break  # 제한 도달 시 중단

        logger.info(f"Evidence 배치 추가: {added_count}/{len(evidences)}")
        return added_count

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Evidence 조회 (인덱싱으로 O(1))"""
        return self._evidence_index.get(evidence_id)

    def find_evidence_by_type(
        self, evidence_type: EvidenceType, limit: int = 100
    ) -> List[Evidence]:
        """타입별 Evidence 검색"""
        results = []
        for evidence_id, evidence in self._evidence_index.items():
            if evidence.evidence_type == evidence_type:
                results.append(evidence)
                if len(results) >= limit:
                    break
        return results

    def find_evidence_by_source(self, source: str) -> List[Evidence]:
        """출처별 Evidence 검색 (파일 경로, Git SHA 등)"""
        results = []
        for evidence in self._evidence_index.values():
            if evidence.source == source:
                results.append(evidence)
        return results

    def add_edge(self, from_id: str, to_id: str, edge_type: EdgeType):
        """엣지 추가"""
        if from_id in self.graph and to_id in self.graph:
            self.graph.add_edge(from_id, to_id, type=edge_type.value)

    def get_neighbors(self, node_id: str) -> List[str]:
        """이웃 노드 조회"""
        if node_id in self.graph:
            return list(self.graph.neighbors(node_id))
        return []

    def save_to_disk(self, path: Path):
        """
        그래프를 디스크에 저장 (Lisa Park 제안)

        Format: JSON (호환성)
        """
        try:
            data = {
                "nodes": [],
                "edges": [],
                "evidence_index": {},
                "metadata": {
                    "version": "2.0",
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                    "node_count": len(self.graph.nodes),
                    "edge_count": len(self.graph.edges),
                },
            }

            # 노드 저장
            for node_id, node_data in self.graph.nodes(data=True):
                data["nodes"].append({"id": node_id, "data": node_data})

            # 엣지 저장
            for from_id, to_id, edge_data in self.graph.edges(data=True):
                data["edges"].append({"from": from_id, "to": to_id, "data": edge_data})

            # Evidence 인덱스 저장
            for evidence_id, evidence in self._evidence_index.items():
                data["evidence_index"][evidence_id] = evidence.to_dict()

            # 파일 저장
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Evidence Graph 저장 완료: {path}")
            logger.info(
                f"  - Nodes: {len(data['nodes'])}, Edges: {len(data['edges'])}"
            )

        except Exception as e:
            logger.error(f"Evidence Graph 저장 실패: {e}")
            raise

    def load_from_disk(self, path: Path) -> bool:
        """
        그래프를 디스크에서 로드

        Returns:
            성공 여부
        """
        try:
            if not path.exists():
                logger.warning(f"Evidence Graph 파일 없음: {path}")
                return False

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 버전 체크
            version = data.get("metadata", {}).get("version", "1.0")
            if version != "2.0":
                logger.warning(f"Evidence Graph 버전 불일치: {version}")

            # 그래프 초기화
            self.graph.clear()
            self._evidence_index.clear()

            # 노드 복원
            for node_item in data.get("nodes", []):
                node_id = node_item["id"]
                node_data = node_item["data"]
                self.graph.add_node(node_id, **node_data)

            # 엣지 복원
            for edge_item in data.get("edges", []):
                from_id = edge_item["from"]
                to_id = edge_item["to"]
                edge_data = edge_item["data"]
                self.graph.add_edge(from_id, to_id, **edge_data)

            # Evidence 인덱스 복원
            for evidence_id, evidence_dict in data.get("evidence_index", {}).items():
                evidence = Evidence.from_dict(evidence_dict)
                self._evidence_index[evidence_id] = evidence

            logger.info(f"Evidence Graph 로드 완료: {path}")
            logger.info(
                f"  - Nodes: {len(self.graph.nodes)}, Edges: {len(self.graph.edges)}"
            )
            return True

        except Exception as e:
            logger.error(f"Evidence Graph 로드 실패: {e}")
            return False

    def get_statistics(self) -> Dict:
        """그래프 통계"""
        node_types = {}
        for _, node_data in self.graph.nodes(data=True):
            node_type = node_data.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

        edge_types = {}
        for _, _, edge_data in self.graph.edges(data=True):
            edge_type = edge_data.get("type", "unknown")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        return {
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "node_types": node_types,
            "edge_types": edge_types,
            "evidence_count": len(self._evidence_index),
        }


# 싱글톤 인스턴스
_evidence_graph_v2_instance: Optional[EvidenceGraphV2] = None


def get_evidence_graph_v2() -> EvidenceGraphV2:
    """EvidenceGraphV2 싱글톤 인스턴스 반환"""
    global _evidence_graph_v2_instance
    if _evidence_graph_v2_instance is None:
        _evidence_graph_v2_instance = EvidenceGraphV2()
    return _evidence_graph_v2_instance
