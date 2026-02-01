#!/usr/bin/env python3
"""
Git Branch Changed Hook Handler
Git 브랜치 전환 시 Cortex 브랜치 자동 연동

This script is called by the post-checkout Git hook.
It detects branch changes and automatically switches the corresponding Cortex branch.
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
from core.git_sync import GitSync
from core.memory_manager import get_memory_manager

logger = logging.getLogger(__name__)


def handle_branch_change(prev_ref: str, new_ref: str, checkout_type: str, repo_path: str) -> Dict[str, Any]:
    """
    Git 브랜치 전환 처리

    Args:
        prev_ref: 이전 브랜치 해시
        new_ref: 새 브랜치 해시
        checkout_type: 체크아웃 타입 (1=branch, 0=file)
        repo_path: Git 저장소 경로

    Returns:
        처리 결과
    """
    try:
        # 브랜치 체크아웃이 아니면 무시
        if checkout_type != "1":
            return {"success": True, "skipped": True, "reason": "Not a branch checkout"}

        # Git 저장소 경로 확인
        repo_path = Path(repo_path).resolve()
        if not (repo_path / ".git").exists():
            return {"success": False, "error": "Not a Git repository"}

        # GitSync 인스턴스 생성 (프로젝트 ID는 저장소 경로 기반)
        project_id = repo_path.name
        git_sync = GitSync(project_id=project_id)

        # 현재 Git 브랜치 정보 가져오기
        current_info = git_sync.get_current_git_branch(str(repo_path))
        if not current_info.get("success"):
            return current_info

        current_branch = current_info.get("branch_name")
        commit_hash = current_info.get("commit_hash")

        logger.info(f"Git branch changed: {prev_ref[:8]} -> {new_ref[:8]} (branch: {current_branch})")

        # Cortex 브랜치 전환 체크
        result = git_sync.check_git_branch_change(
            repo_path=str(repo_path),
            auto_create=True  # 매핑이 없으면 자동 생성
        )

        if not result.get("success"):
            logger.error(f"Failed to sync Cortex branch: {result.get('error')}")
            return result

        # 브랜치 전환 발생 시 로그
        if result.get("switched"):
            cortex_branch = result.get("cortex_branch_id")
            logger.info(f"Cortex branch switched to: {cortex_branch}")

            # Memory Manager에 브랜치 전환 기록
            try:
                mm = get_memory_manager(project_id)
                mm.update_memory(
                    project_id=project_id,
                    branch_id=cortex_branch,
                    content=f"Git 브랜치 전환 감지: {current_branch} (commit: {commit_hash[:8]})\n자동으로 Cortex 브랜치 전환됨.",
                    role="system"
                )
            except Exception as e:
                logger.warning(f"Failed to record branch switch: {e}")

        return {
            "success": True,
            "git_branch": current_branch,
            "cortex_branch": result.get("cortex_branch_id"),
            "switched": result.get("switched", False),
            "created": result.get("created", False)
        }

    except Exception as e:
        logger.error(f"Git branch change handler failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def main():
    """
    Git post-checkout hook entry point

    Args from Git:
        sys.argv[1]: Previous HEAD ref
        sys.argv[2]: New HEAD ref
        sys.argv[3]: Checkout type (1=branch, 0=file)
    """
    if len(sys.argv) < 4:
        print("Error: This script must be called by Git post-checkout hook", file=sys.stderr)
        print(f"Usage: {sys.argv[0]} <prev-ref> <new-ref> <checkout-type>", file=sys.stderr)
        sys.exit(1)

    prev_ref = sys.argv[1]
    new_ref = sys.argv[2]
    checkout_type = sys.argv[3]

    # Git 저장소 경로는 현재 작업 디렉토리
    import os
    repo_path = os.getcwd()

    # 브랜치 전환 처리
    result = handle_branch_change(prev_ref, new_ref, checkout_type, repo_path)

    if not result.get("success"):
        print(f"[Cortex] Warning: Failed to sync branch: {result.get('error')}", file=sys.stderr)
        # Git 작업은 계속 진행 (non-blocking)
        sys.exit(0)

    if result.get("switched") or result.get("created"):
        print(f"[Cortex] Branch synced: {result.get('cortex_branch')}")

    sys.exit(0)


if __name__ == "__main__":
    main()
