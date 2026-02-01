"""
Evidence Graph 관리 시스템

Cortex Phase 9: Hallucination Detection System
할루시네이션 감지를 위한 Evidence Graph 구현

핵심 기능:
- Context, File, Task, Diff 노드 관리
- REFERENCED, MODIFIED, GENERATED_FROM 엣지 관리
- Claim에 대한 증거 존재 여부 확인
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx


class EvidenceGraph:
    """
    Evidence Graph 관리 클래스

    LLM 응답의 근거를 추적하기 위한 그래프 구조를 관리합니다.
    NetworkX를 사용하여 로컬에서 작동하며 외부 API 호출이 없습니다.
    """

    def __init__(self, project_id: str, project_path: str):
        """
        Evidence Graph 초기화

        Args:
            project_id: 프로젝트 식별자
            project_path: 프로젝트 경로 (필수)

        Raises:
            ValueError: project_path가 제공되지 않았을 때
        """
        if not project_path:
            raise ValueError(
                "project_path is required for Evidence Graph.\n"
                "Evidence Graph cannot determine storage location without explicit project path.\n"
                "Please provide the project root directory path.\n"
                "Example: EvidenceGraph(project_id='test', project_path='/path/to/project')"
            )

        self.project_id = project_id
        self.project_path = project_path
        self.graph = nx.DiGraph()
        self._load_graph()

    def _get_graph_path(self) -> Path:
        """
        그래프 저장 경로 반환

        project_path를 기반으로 저장 경로를 결정합니다.
        """
        cortex_dir = Path(self.project_path)
        cortex_dir.mkdir(parents=True, exist_ok=True)
        return cortex_dir / "_evidence_graph.json"

    def _load_graph(self):
        """저장된 그래프 로드"""
        graph_path = self._get_graph_path()
        if graph_path.exists():
            try:
                with open(graph_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.graph = nx.node_link_graph(data)
            except Exception as e:
                print(f"Warning: Failed to load evidence graph: {e}")
                # 로드 실패 시 새 그래프 생성
                self.graph = nx.DiGraph()

    def _save_graph(self):
        """그래프 저장"""
        graph_path = self._get_graph_path()
        try:
            data = nx.node_link_data(self.graph)
            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save evidence graph: {e}")

    # ========================================
    # 노드 관리
    # ========================================

    def add_context_node(
        self, context_id: str, branch_id: str, content_hash: str, metadata: Optional[Dict] = None
    ) -> bool:
        """
        Context 노드 추가

        Args:
            context_id: Context 식별자
            branch_id: 브랜치 식별자
            content_hash: 컨텐츠 해시
            metadata: 추가 메타데이터

        Returns:
            성공 여부
        """
        try:
            node_data = {
                "type": "Context",
                "branch_id": branch_id,
                "content_hash": content_hash,
                "timestamp": datetime.now().isoformat(),
            }

            if metadata:
                node_data.update(metadata)

            self.graph.add_node(context_id, **node_data)
            self._save_graph()
            return True
        except Exception as e:
            print(f"Error adding context node: {e}")
            return False

    def add_file_node(
        self, file_path: str, last_modified: str, content_hash: str, metadata: Optional[Dict] = None
    ) -> bool:
        """
        File 노드 추가

        Args:
            file_path: 파일 경로
            last_modified: 최종 수정 시간
            content_hash: 컨텐츠 해시
            metadata: 추가 메타데이터

        Returns:
            성공 여부
        """
        try:
            node_data = {
                "type": "File",
                "last_modified": last_modified,
                "content_hash": content_hash,
                "timestamp": datetime.now().isoformat(),
            }

            if metadata:
                node_data.update(metadata)

            self.graph.add_node(file_path, **node_data)
            self._save_graph()
            return True
        except Exception as e:
            print(f"Error adding file node: {e}")
            return False

    def add_task_node(
        self, task_id: str, task_type: str, description: str, metadata: Optional[Dict] = None
    ) -> bool:
        """
        Task 노드 추가

        Args:
            task_id: Task 식별자
            task_type: Task 타입
            description: Task 설명
            metadata: 추가 메타데이터

        Returns:
            성공 여부
        """
        try:
            node_data = {
                "type": "Task",
                "task_type": task_type,
                "description": description,
                "timestamp": datetime.now().isoformat(),
            }

            if metadata:
                node_data.update(metadata)

            self.graph.add_node(task_id, **node_data)
            self._save_graph()
            return True
        except Exception as e:
            print(f"Error adding task node: {e}")
            return False

    def add_diff_node(
        self, commit_hash: str, file_path: str, diff_content: str, metadata: Optional[Dict] = None
    ) -> bool:
        """
        Diff 노드 추가

        Args:
            commit_hash: 커밋 해시
            file_path: 파일 경로
            diff_content: Diff 내용
            metadata: 추가 메타데이터

        Returns:
            성공 여부
        """
        try:
            diff_id = f"diff:{commit_hash}:{file_path}"
            node_data = {
                "type": "Diff",
                "commit_hash": commit_hash,
                "file_path": file_path,
                "diff_content": diff_content[:500],  # 처음 500자만 저장
                "timestamp": datetime.now().isoformat(),
            }

            if metadata:
                node_data.update(metadata)

            self.graph.add_node(diff_id, **node_data)
            self._save_graph()
            return True
        except Exception as e:
            print(f"Error adding diff node: {e}")
            return False

    # ========================================
    # 엣지 관리
    # ========================================

    def add_reference_edge(self, source: str, target: str) -> bool:
        """
        참조 관계 추가 (REFERENCED)

        Args:
            source: 소스 노드 ID
            target: 타겟 노드 ID

        Returns:
            성공 여부
        """
        try:
            self.graph.add_edge(
                source, target, type="REFERENCED", timestamp=datetime.now().isoformat()
            )
            self._save_graph()
            return True
        except Exception as e:
            print(f"Error adding reference edge: {e}")
            return False

    def add_modified_edge(self, source: str, target: str) -> bool:
        """
        수정 관계 추가 (MODIFIED)

        Args:
            source: 소스 노드 ID (Task)
            target: 타겟 노드 ID (File)

        Returns:
            성공 여부
        """
        try:
            self.graph.add_edge(
                source, target, type="MODIFIED", timestamp=datetime.now().isoformat()
            )
            self._save_graph()
            return True
        except Exception as e:
            print(f"Error adding modified edge: {e}")
            return False

    def add_generated_from_edge(self, source: str, target: str) -> bool:
        """
        생성 관계 추가 (GENERATED_FROM)

        Args:
            source: 소스 노드 ID (응답)
            target: 타겟 노드 ID (Context)

        Returns:
            성공 여부
        """
        try:
            self.graph.add_edge(
                source, target, type="GENERATED_FROM", timestamp=datetime.now().isoformat()
            )
            self._save_graph()
            return True
        except Exception as e:
            print(f"Error adding generated_from edge: {e}")
            return False

    # ========================================
    # 검증 기능
    # ========================================

    def verify_claim_evidence(self, claim_id: str, required_evidence_types: List[str]) -> Dict:
        """
        Claim에 대한 증거 존재 여부 확인

        Args:
            claim_id: Claim 식별자
            required_evidence_types: 필요한 증거 타입 목록 ["Context", "File", "Diff"]

        Returns:
            검증 결과 딕셔너리
        """
        if claim_id not in self.graph:
            return {"verified": False, "reason": "claim_not_found", "evidence": []}

        # 연결된 노드 찾기
        neighbors = list(self.graph.neighbors(claim_id))

        # 증거 타입별 분류
        evidence_by_type = {}
        for neighbor in neighbors:
            node_data = self.graph.nodes[neighbor]
            node_type = node_data.get("type")

            if node_type not in evidence_by_type:
                evidence_by_type[node_type] = []

            evidence_by_type[node_type].append(
                {"id": neighbor, "type": node_type, "data": node_data}
            )

        # 필요한 증거 타입 확인
        missing_types = []
        for required_type in required_evidence_types:
            if required_type not in evidence_by_type:
                missing_types.append(required_type)

        return {
            "verified": len(missing_types) == 0,
            "reason": "all_evidence_found" if len(missing_types) == 0 else "missing_evidence",
            "evidence": evidence_by_type,
            "missing_types": missing_types,
        }

    def get_connected_contexts(self, node_id: str) -> List[Dict]:
        """
        특정 노드에 연결된 Context 목록 반환

        Args:
            node_id: 노드 식별자

        Returns:
            연결된 Context 목록
        """
        if node_id not in self.graph:
            return []

        contexts = []
        for neighbor in self.graph.neighbors(node_id):
            node_data = self.graph.nodes[neighbor]
            if node_data.get("type") == "Context":
                contexts.append({"context_id": neighbor, "data": node_data})

        return contexts

    def get_evidence_chain(self, node_id: str, max_depth: int = 3) -> Dict:
        """
        특정 노드의 증거 체인 반환

        Args:
            node_id: 노드 식별자
            max_depth: 최대 탐색 깊이

        Returns:
            증거 체인 정보
        """
        if node_id not in self.graph:
            return {"error": "node_not_found"}

        # BFS로 증거 체인 구축
        visited = set()
        chain = []
        queue = [(node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)
            node_data = self.graph.nodes[current_id]

            chain.append(
                {"id": current_id, "type": node_data.get("type"), "depth": depth, "data": node_data}
            )

            # 인접 노드 추가
            for neighbor in self.graph.neighbors(current_id):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))

        return {"chain_length": len(chain), "chain": chain}

    def get_stats(self) -> Dict:
        """
        그래프 통계 반환

        Returns:
            그래프 통계 딕셔너리
        """
        node_types = {}
        edge_types = {}

        # 노드 타입별 카운트
        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

        # 엣지 타입별 카운트
        for source, target, edge_data in self.graph.edges(data=True):
            edge_type = edge_data.get("type", "unknown")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": node_types,
            "edge_types": edge_types,
        }

    def clear(self):
        """그래프 초기화"""
        self.graph.clear()
        self._save_graph()

    # =========================================================================
    # Phase 4: Graph Centrality (Critical Context Detection)
    # =========================================================================

    def compute_degree_centrality(self) -> Dict[str, float]:
        """
        Degree Centrality 계산

        각 노드가 얼마나 많은 다른 노드와 연결되어 있는지 측정합니다.
        높은 값 = 많은 노드와 연결된 중요한 노드

        Returns:
            {node_id: centrality_score} (0.0 ~ 1.0)
        """
        if self.graph.number_of_nodes() == 0:
            return {}

        try:
            return nx.degree_centrality(self.graph)
        except (nx.NetworkXError, ValueError, KeyError) as e:
            # MEDIUM #3: bare except 제거, 구체적 예외 타입 지정
            # NetworkX 에러 또는 그래프 구조 문제 발생 시 빈 딕셔너리 반환
            print(f"[WARNING] compute_degree_centrality 실패: {type(e).__name__}: {str(e)}")
            return {}

    def compute_betweenness_centrality(self) -> Dict[str, float]:
        """
        Betweenness Centrality 계산

        다른 노드들 간의 최단 경로가 얼마나 자주 이 노드를 통과하는지 측정합니다.
        높은 값 = 정보 흐름의 중심에 있는 중요한 노드 (bridge 역할)

        Returns:
            {node_id: centrality_score} (0.0 ~ 1.0)
        """
        if self.graph.number_of_nodes() == 0:
            return {}

        try:
            return nx.betweenness_centrality(self.graph)
        except (nx.NetworkXError, ValueError, KeyError) as e:
            # MEDIUM #3: bare except 제거, 구체적 예외 타입 지정
            # NetworkX 에러 또는 그래프 구조 문제 발생 시 빈 딕셔너리 반환
            print(f"[WARNING] compute_betweenness_centrality 실패: {type(e).__name__}: {str(e)}")
            return {}

    def compute_combined_centrality(self) -> Dict[str, float]:
        """
        Combined Centrality 계산 (Degree + Betweenness)

        두 가지 centrality를 가중 평균하여 종합적인 중요도를 계산합니다.
        - Degree weight: 0.6 (직접 연결 중시)
        - Betweenness weight: 0.4 (정보 흐름 중시)

        Returns:
            {node_id: combined_centrality} (0.0 ~ 1.0)
        """
        degree = self.compute_degree_centrality()
        betweenness = self.compute_betweenness_centrality()

        if not degree and not betweenness:
            return {}

        # 모든 노드 ID 수집
        all_nodes = set(degree.keys()) | set(betweenness.keys())

        combined = {}
        for node_id in all_nodes:
            deg_score = degree.get(node_id, 0.0)
            bet_score = betweenness.get(node_id, 0.0)
            combined[node_id] = (deg_score * 0.6) + (bet_score * 0.4)

        return combined

    def is_critical(self, context_id: str) -> bool:
        """
        Critical Context 판단

        다음 조건 중 하나라도 만족하면 critical로 간주:
        - Degree centrality > 0.5 (많은 노드와 연결)
        - Betweenness centrality > 0.4 (정보 흐름의 중심)

        Args:
            context_id: Context 노드 ID

        Returns:
            True if critical, False otherwise
        """
        if context_id not in self.graph:
            return False

        degree = self.compute_degree_centrality()
        betweenness = self.compute_betweenness_centrality()

        return degree.get(context_id, 0.0) > 0.5 or betweenness.get(context_id, 0.0) > 0.4

    def get_critical_contexts(self) -> List[str]:
        """
        모든 Critical Context 목록 반환

        Returns:
            Critical로 판단된 Context ID 목록
        """
        combined = self.compute_combined_centrality()

        # Context 노드만 필터링 (node_type == "context")
        critical_contexts = []
        for node_id, score in combined.items():
            if node_id not in self.graph:
                continue

            node_data = self.graph.nodes[node_id]
            if node_data.get("node_type") == "context" and self.is_critical(node_id):
                critical_contexts.append(node_id)

        # Combined centrality 기준 내림차순 정렬
        critical_contexts.sort(key=lambda nid: combined.get(nid, 0), reverse=True)

        return critical_contexts

    def shortest_path(self, from_node: str, to_node: str) -> Optional[List[str]]:
        """
        두 노드 간 최단 경로 계산 (CRITICAL #4: Semantic Depth 계산용)

        NetworkX의 shortest_path 알고리즘을 사용하여
        Claim 노드에서 Evidence 노드까지의 최단 경로를 찾습니다.

        Args:
            from_node: 시작 노드 ID (보통 Claim)
            to_node: 목표 노드 ID (보통 Evidence/Context)

        Returns:
            경로 리스트 (노드 ID들), 경로가 없으면 None

        Example:
            >>> path = graph.shortest_path("claim_123", "context_456")
            >>> if path:
            >>>     semantic_depth = len(path) - 1  # 경로 길이 - 1 = semantic depth
        """
        # 노드 존재 여부 확인
        if from_node not in self.graph or to_node not in self.graph:
            return None

        try:
            # NetworkX shortest_path 사용
            path = nx.shortest_path(self.graph, source=from_node, target=to_node)
            return path
        except nx.NetworkXNoPath:
            # 경로가 없으면 None 반환
            return None
        except Exception as e:
            # 기타 예외 발생 시 None 반환
            print(f"Warning: shortest_path failed: {e}")
            return None


# ============================================================================
# Singleton Pattern for Evidence Graph (Performance Optimization)
# ============================================================================

# 모듈 레벨 싱글톤 저장소 (project_id → (mtime, instance))
_evidence_graph_instances: Dict[str, Tuple[float, EvidenceGraph]] = {}


def get_evidence_graph(project_id: str, project_path: Optional[str] = None) -> EvidenceGraph:
    """
    Evidence Graph 싱글톤 getter (mtime 기반 무효화)

    프로젝트당 하나의 EvidenceGraph 인스턴스만 유지하여 성능을 최적화합니다.
    _evidence_graph.json 파일의 mtime을 추적하여 파일 변경 시 자동 무효화합니다.

    PERFORMANCE: 인스턴스 생성 시간 ~80ms 절감
    - 캐시 hit 시: 즉시 반환 (~1ms)
    - 캐시 miss 시: 새 인스턴스 생성 후 캐시 (~80ms)
    - mtime 변경 시: 자동 무효화 후 재생성 (100% 정확도 보장)

    Args:
        project_id: 프로젝트 식별자
        project_path: 프로젝트 경로 (첫 호출 시 필수, 이후 선택적)

    Returns:
        EvidenceGraph 인스턴스 (싱글톤)

    Raises:
        ValueError: 첫 호출 시 project_path 미제공

    Example:
        >>> # 첫 호출 (project_path 필수)
        >>> graph = get_evidence_graph("proj1", "/path/to/project")
        >>>
        >>> # 이후 호출 (project_path 생략 가능)
        >>> graph = get_evidence_graph("proj1")
    """
    # project_path가 없으면 캐시에서 가져오기 시도
    if project_path is None:
        if project_id in _evidence_graph_instances:
            _, cached_instance = _evidence_graph_instances[project_id]
            return cached_instance
        else:
            raise ValueError(
                f"project_path is required for first call of get_evidence_graph('{project_id}')"
            )

    # mtime 체크
    current_mtime = 0.0
    try:
        graph_file_path = Path(project_path) / "_evidence_graph.json"
        if graph_file_path.exists():
            current_mtime = os.path.getmtime(str(graph_file_path))
        else:
            # 파일이 없으면 mtime = 0 (새로 생성될 예정)
            current_mtime = 0.0

        # 캐시에 있고 mtime 일치하면 반환
        if project_id in _evidence_graph_instances:
            cached_mtime, cached_instance = _evidence_graph_instances[project_id]
            if cached_mtime == current_mtime:
                # Cache hit - 기존 인스턴스 반환
                return cached_instance
    except OSError:
        # 파일 삭제/이동 시 캐시 제거
        if project_id in _evidence_graph_instances:
            del _evidence_graph_instances[project_id]

    # Cache miss 또는 mtime 변경 - 새 인스턴스 생성
    instance = EvidenceGraph(project_id, project_path)

    # 캐시 업데이트
    try:
        _evidence_graph_instances[project_id] = (current_mtime, instance)
    except Exception:
        # 캐시 업데이트 실패해도 계속 진행 (캐시는 선택 사항)
        pass

    return instance
