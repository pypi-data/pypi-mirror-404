"""
Cortex MCP - Branch Manager

브랜치 관련 관리:
- 브랜치 목록 조회
- 브랜치 경로 탐색
- 활성 브랜치 관리

Note: 브랜치 생성은 memory_manager.create_branch()를 사용하세요.
      (검증, 롤백, .md 파일 생성 포함)
"""

import logging
from datetime import timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .file_io import FileIO

logger = logging.getLogger(__name__)


class BranchManager:
    """브랜치 조회 및 탐색 담당 (생성은 MemoryManager에서 처리)"""

    def __init__(self, memory_dir: Path, file_io: FileIO):
        """
        Args:
            memory_dir: 메모리 저장 디렉토리
            file_io: 파일 I/O 유틸리티
        """
        self.memory_dir = memory_dir
        self.file_io = file_io

    def list_branches(self, project_id: str) -> List[Dict[str, Any]]:
        """
        프로젝트의 모든 브랜치 목록 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            브랜치 메타데이터 리스트
        """
        index = self.file_io.load_project_index(project_id)
        return list(index.get("branches", {}).values())

    def _find_branch_path(self, project_id: str, branch_id: str) -> Optional[Path]:
        """
        브랜치 디렉토리 경로 찾기

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID

        Returns:
            브랜치 디렉토리 경로 (없으면 None)
        """
        branch_dir = self.memory_dir / project_id / "contexts" / branch_id
        return branch_dir if branch_dir.exists() else None

    def _find_latest_active_branch(self, project_id: str) -> Optional[Path]:
        """
        가장 최근 활성 브랜치 찾기

        Args:
            project_id: 프로젝트 ID

        Returns:
            브랜치 디렉토리 경로 (없으면 None)
        """
        index = self.file_io.load_project_index(project_id)
        active_branches = [
            (k, v)
            for k, v in index.get("branches", {}).items()
            if v.get("status") == "active"
        ]

        if not active_branches:
            return None

        # 가장 최근 생성된 브랜치
        latest = max(active_branches, key=lambda x: x[1].get("created_at", ""))
        return self._find_branch_path(project_id, latest[0])
