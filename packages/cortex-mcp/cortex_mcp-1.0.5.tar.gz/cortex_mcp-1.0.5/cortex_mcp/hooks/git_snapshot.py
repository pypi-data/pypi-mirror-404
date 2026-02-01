#!/usr/bin/env python3
"""
Git Snapshot Hook Handler
Git 커밋 전 Cortex 스냅샷 자동 생성

This script is called by the pre-commit Git hook.
It creates a Cortex snapshot before each commit for context recovery.
"""

import sys
from pathlib import Path

# Add parent directory to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

import logging
from datetime import datetime
from typing import Any, Dict

from config import config
from core.backup_manager import get_backup_manager
from core.git_sync import GitSync

logger = logging.getLogger(__name__)


def create_snapshot_on_commit(repo_path: str) -> Dict[str, Any]:
    """
    Git 커밋 전 스냅샷 생성

    Args:
        repo_path: Git 저장소 경로

    Returns:
        처리 결과
    """
    try:
        # Git 저장소 경로 확인
        repo_path = Path(repo_path).resolve()
        if not (repo_path / ".git").exists():
            return {"success": False, "error": "Not a Git repository"}

        # 프로젝트 ID (저장소 경로 기반)
        project_id = repo_path.name

        # GitSync 인스턴스 생성
        git_sync = GitSync(project_id=project_id)

        # 현재 Git 상태 정보
        current_info = git_sync.get_current_git_branch(str(repo_path))
        if not current_info.get("success"):
            return current_info

        current_branch = current_info.get("git_branch")
        commit_hash = current_info.get("commit_hash")

        logger.info(f"Pre-commit hook triggered: {current_branch} @ {commit_hash[:8]}")

        # Backup Manager 인스턴스
        backup_mgr = get_backup_manager(project_id)

        # 스냅샷 생성
        snapshot_desc = f"Auto snapshot before commit on {current_branch}"
        result = backup_mgr.create_snapshot(
            project_id=project_id,
            snapshot_type="git_commit",
            description=snapshot_desc,
            branch_id=None  # 전체 프로젝트 스냅샷
        )

        if not result.get("success"):
            logger.warning(f"Failed to create snapshot: {result.get('error')}")
            # 스냅샷 실패는 커밋을 차단하지 않음 (non-blocking)
            return {
                "success": True,
                "skipped": True,
                "reason": "Snapshot creation failed (non-blocking)"
            }

        snapshot_id = result.get("snapshot_id")
        logger.info(f"Snapshot created: {snapshot_id}")

        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "git_branch": current_branch,
            "commit_hash": commit_hash
        }

    except Exception as e:
        logger.error(f"Git snapshot handler failed: {e}", exc_info=True)
        # 예외 발생 시에도 커밋은 계속 진행 (non-blocking)
        return {
            "success": True,
            "skipped": True,
            "error": str(e),
            "reason": "Exception during snapshot (non-blocking)"
        }


def main():
    """
    Git pre-commit hook entry point

    No args from Git - this hook runs before every commit.
    """
    # Git 저장소 경로는 현재 작업 디렉토리
    import os
    repo_path = os.getcwd()

    # 스냅샷 생성
    result = create_snapshot_on_commit(repo_path)

    if not result.get("success"):
        print(f"[Cortex] Warning: Pre-commit snapshot failed: {result.get('error')}", file=sys.stderr)

    if result.get("skipped"):
        print(f"[Cortex] Snapshot skipped: {result.get('reason')}", file=sys.stderr)
    elif result.get("snapshot_id"):
        print(f"[Cortex] Snapshot created: {result['snapshot_id']}")

    # 항상 성공 (커밋 차단하지 않음)
    sys.exit(0)


if __name__ == "__main__":
    main()
