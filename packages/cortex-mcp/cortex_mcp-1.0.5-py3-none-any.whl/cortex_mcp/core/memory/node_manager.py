"""
Cortex MCP - Node Manager

노드 그룹 관리:
- 노드 생성 및 목록 조회
- Context를 Node에 추가
- Node 그룹핑 자동 제안
"""

import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .file_io import FileIO

logger = logging.getLogger(__name__)

# NODE_GROUPING_ENGINE import
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from branch_decision_engine import NodeGroupingEngine
    NODE_GROUPING_AVAILABLE = True
except ImportError:
    NODE_GROUPING_AVAILABLE = False
    NodeGroupingEngine = None


class NodeManager:
    """Node 그룹 생성 및 관리 담당"""

    def __init__(self, memory_dir: Path, file_io: FileIO):
        """
        Args:
            memory_dir: 메모리 저장 디렉토리
            file_io: 파일 I/O 유틸리티
        """
        self.memory_dir = memory_dir
        self.file_io = file_io

        # Node Grouping Engine 초기화 (선택적)
        self.node_grouping_engine = None
        if NODE_GROUPING_AVAILABLE and NodeGroupingEngine is not None:
            try:
                self.node_grouping_engine = NodeGroupingEngine()
            except Exception as e:
                logger.warning(f"Failed to initialize NodeGroupingEngine: {e}")

    def create_node(
        self,
        project_id: str,
        branch_id: str,
        node_name: str,
        context_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Node 그룹 생성

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            node_name: Node 이름
            context_ids: 이 Node에 포함할 Context ID 목록

        Returns:
            생성된 Node 정보
        """
        # 브랜치 인덱스 로드
        branch_index = self.file_io.load_branch_index(project_id, branch_id)

        # Node ID 생성
        sanitized_name = re.sub(r"[^\w\s-]", "", node_name).strip().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
        node_id = f"node_{sanitized_name}_{timestamp}"

        # Node 메타데이터 생성
        node_metadata = {
            "node_id": node_id,
            "node_name": node_name,
            "context_ids": context_ids or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # 브랜치 인덱스 업데이트
        if "nodes" not in branch_index:
            branch_index["nodes"] = []
        branch_index["nodes"].append(node_metadata)

        self.file_io.save_branch_index(project_id, branch_id, branch_index)

        logger.info(f"Created node: {node_id} in branch: {branch_id}")

        return {"status": "success", "node_id": node_id, "node_metadata": node_metadata}

    def list_nodes(self, project_id: str, branch_id: str) -> Dict[str, Any]:
        """
        브랜치의 모든 Node 목록 조회

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID

        Returns:
            Node 목록
        """
        branch_index = self.file_io.load_branch_index(project_id, branch_id)
        return {"status": "success", "nodes": branch_index.get("nodes", [])}

    def add_context_to_node(
        self, project_id: str, branch_id: str, node_id: str, context_id: str
    ) -> Dict[str, Any]:
        """
        Node에 Context 추가

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            node_id: Node ID
            context_id: 추가할 Context ID

        Returns:
            처리 결과
        """
        branch_index = self.file_io.load_branch_index(project_id, branch_id)

        for node in branch_index.get("nodes", []):
            if node["node_id"] == node_id:
                if context_id not in node.get("context_ids", []):
                    node.setdefault("context_ids", []).append(context_id)

                self.file_io.save_branch_index(project_id, branch_id, branch_index)

                logger.info(f"Added context {context_id} to node {node_id}")
                return {"status": "success"}

        return {"status": "error", "message": f"Node {node_id} not found"}

    def get_context_count(self, project_id: str, branch_id: str) -> Dict[str, Any]:
        """
        브랜치의 전체 Context 개수 조회

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID

        Returns:
            Context 개수
        """
        branch_index = self.file_io.load_branch_index(project_id, branch_id)
        count = len(branch_index.get("contexts", []))
        return {"status": "success", "context_count": count}

    def suggest_node_grouping(self, project_id: str, branch_id: str) -> Dict[str, Any]:
        """
        Node 그룹핑 자동 제안

        30개 이상의 Context가 있을 때 Node 그룹핑을 제안합니다.

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID

        Returns:
            제안 결과
        """
        branch_index = self.file_io.load_branch_index(project_id, branch_id)
        context_count = len(branch_index.get("contexts", []))

        if context_count < 30:
            return {
                "status": "success",
                "should_group": False,
                "reason": f"Context count ({context_count}) is below threshold (30)",
            }

        # Node Grouping Engine 활용
        if self.node_grouping_engine:
            try:
                suggestion = self.node_grouping_engine.suggest_grouping(
                    contexts=branch_index.get("contexts", [])
                )
                return {
                    "status": "success",
                    "should_group": True,
                    "context_count": context_count,
                    "suggested_groups": suggestion.get("groups", []),
                }
            except Exception as e:
                logger.warning(f"Node grouping engine failed: {e}")

        # Fallback: 간단한 그룹핑 제안
        return {
            "status": "success",
            "should_group": True,
            "context_count": context_count,
            "message": f"{context_count} contexts found. Consider grouping into nodes.",
        }
