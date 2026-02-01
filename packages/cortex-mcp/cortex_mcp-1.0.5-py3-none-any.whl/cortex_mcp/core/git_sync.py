"""
Cortex MCP - Git Sync Module v2.1
Git 브랜치와 Cortex 브랜치 동기화 + Alpha Logger 연동

기능:
- Git 브랜치 상태 감지
- Git-Cortex 브랜치 연동
- 브랜치 전환 시 자동 맥락 전환
- 팀 협업 지원 (커밋 기반 맥락 공유)
- Alpha Logger 연동 (v2.1)
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))
from config import config

from .alpha_logger import LogModule, get_alpha_logger

# Telemetry (사용 지표 자동 수집)
try:
    from .telemetry_decorator import track_call

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

    # Noop decorator when telemetry not available
    def track_call(module_name: str):
        def decorator(func):
            return func

        return decorator


class GitSync:
    """
    Git-Cortex 동기화 관리자

    기능:
    - Git 브랜치와 Cortex 브랜치 1:1 매핑
    - Git checkout 감지 및 자동 전환
    - 브랜치 생성 시 맥락 복제
    """

    def __init__(self, project_id: str = None):
        self.project_id = project_id
        self.memory_dir = config.memory_dir

        # Alpha Logger
        self.logger = get_alpha_logger()

        # Git-Cortex 매핑 파일
        if project_id:
            self.mapping_file = self.memory_dir / project_id / "_git_mapping.json"
        else:
            self.mapping_file = config.base_dir / "global_git_mapping.json"

        # 캐시
        self._mapping: Dict[str, Any] = {}
        self._last_known_branch: Optional[str] = None

        # 로드
        self._load_mapping()

    # ==================== Public API ====================

    def get_current_git_branch(self, repo_path: str) -> Dict[str, Any]:
        """
        현재 Git 브랜치 정보 반환

        Args:
            repo_path: Git 저장소 경로

        Returns:
            현재 브랜치 정보 또는 에러
        """
        try:
            # Git 저장소 확인
            git_dir = Path(repo_path) / ".git"
            if not git_dir.exists():
                return {"success": False, "error": "Git 저장소가 아닙니다.", "path": repo_path}

            # 현재 브랜치 가져오기
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return {"success": False, "error": f"Git 명령 실패: {result.stderr.strip()}"}

            branch_name = result.stdout.strip()

            # 추가 정보 수집
            commit_hash = self._get_commit_hash(repo_path)

            return {
                "success": True,
                "git_branch": branch_name,
                "commit_hash": commit_hash,
                "repo_path": repo_path,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git 명령 타임아웃"}
        except FileNotFoundError:
            return {"success": False, "error": "Git이 설치되어 있지 않습니다."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @track_call("git_sync")
    def link_git_branch(
        self,
        repo_path: str,
        git_branch: str = None,
        cortex_branch_id: str = None,
        auto_create: bool = True,
    ) -> Dict[str, Any]:
        """
        Git 브랜치와 Cortex 브랜치 연동

        Args:
            repo_path: Git 저장소 경로
            git_branch: Git 브랜치 이름 (없으면 현재 브랜치)
            cortex_branch_id: Cortex 브랜치 ID (없으면 자동 생성/매칭)
            auto_create: Cortex 브랜치 자동 생성 여부

        Returns:
            연동 결과
        """
        # 현재 Git 브랜치 확인
        if not git_branch:
            git_info = self.get_current_git_branch(repo_path)
            if not git_info["success"]:
                return git_info
            git_branch = git_info["git_branch"]

        # 이미 매핑된 경우 확인
        existing = self._get_mapping(repo_path, git_branch)
        if existing:
            return {
                "success": True,
                "action": "existing",
                "git_branch": git_branch,
                "cortex_branch_id": existing["cortex_branch_id"],
                "message": f"이미 연동된 브랜치입니다: {existing['cortex_branch_id']}",
            }

        # Cortex 브랜치 ID 결정
        if not cortex_branch_id:
            if auto_create:
                # 새 브랜치 ID 생성 (Git 브랜치 이름 기반)
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                cortex_branch_id = f"git_{git_branch}_{timestamp}"
            else:
                return {
                    "success": False,
                    "error": "cortex_branch_id가 필요합니다 (auto_create=False)",
                }

        # 매핑 저장
        self._set_mapping(repo_path, git_branch, cortex_branch_id)

        # 마지막 브랜치 업데이트
        self._mapping["_last_branch"] = {
            "repo_path": repo_path,
            "git_branch": git_branch,
            "cortex_branch_id": cortex_branch_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._save_mapping()

        # Git 연동 로깅
        self.logger.log_git_sync(
            action="link_created",
            git_branch=git_branch,
            cortex_branch=cortex_branch_id,
            success=True,
        )

        return {
            "success": True,
            "action": "created",
            "git_branch": git_branch,
            "cortex_branch_id": cortex_branch_id,
            "message": f"Git 브랜치 '{git_branch}'를 Cortex 브랜치 '{cortex_branch_id}'에 연동했습니다.",
        }

    def check_branch_change(self, repo_path: str) -> Dict[str, Any]:
        """
        Git 브랜치 변경 감지

        Args:
            repo_path: Git 저장소 경로

        Returns:
            브랜치 변경 여부 및 정보
        """
        # 현재 Git 브랜치
        git_info = self.get_current_git_branch(repo_path)
        if not git_info["success"]:
            return git_info

        current_branch = git_info["git_branch"]

        # 마지막 알려진 브랜치와 비교
        last_info = self._mapping.get("_last_branch", {})
        last_branch = (
            last_info.get("git_branch") if last_info.get("repo_path") == repo_path else None
        )

        if last_branch and last_branch != current_branch:
            # 브랜치 변경됨
            new_cortex_branch = self._get_mapping(repo_path, current_branch)
            old_cortex_branch = self._get_mapping(repo_path, last_branch)

            # 마지막 브랜치 업데이트
            new_cortex_id = new_cortex_branch.get("cortex_branch_id") if new_cortex_branch else None
            old_cortex_id = old_cortex_branch.get("cortex_branch_id") if old_cortex_branch else None

            self._mapping["_last_branch"] = {
                "repo_path": repo_path,
                "git_branch": current_branch,
                "cortex_branch_id": new_cortex_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._save_mapping()

            # 브랜치 변경 로깅
            self.logger.log_git_sync(
                action="branch_changed",
                git_branch=f"{last_branch}->{current_branch}",
                cortex_branch=new_cortex_id or "unmapped",
                success=True,
            )

            return {
                "success": True,
                "changed": True,
                "from_branch": last_branch,
                "to_branch": current_branch,
                "from_cortex_branch": old_cortex_id,
                "to_cortex_branch": new_cortex_id,
                "message": f"Git 브랜치가 '{last_branch}'에서 '{current_branch}'로 변경되었습니다.",
            }

        # 변경 없음
        return {
            "success": True,
            "changed": False,
            "current_branch": current_branch,
            "message": "브랜치 변경 없음",
        }

    def get_linked_cortex_branch(self, repo_path: str, git_branch: str = None) -> Dict[str, Any]:
        """
        Git 브랜치에 연동된 Cortex 브랜치 ID 반환

        Args:
            repo_path: Git 저장소 경로
            git_branch: Git 브랜치 이름 (없으면 현재 브랜치)

        Returns:
            연동된 Cortex 브랜치 정보
        """
        if not git_branch:
            git_info = self.get_current_git_branch(repo_path)
            if not git_info["success"]:
                return git_info
            git_branch = git_info["git_branch"]

        mapping = self._get_mapping(repo_path, git_branch)

        if mapping:
            return {
                "success": True,
                "git_branch": git_branch,
                "cortex_branch_id": mapping["cortex_branch_id"],
                "linked_at": mapping.get("linked_at"),
            }

        return {
            "success": False,
            "git_branch": git_branch,
            "error": f"Git 브랜치 '{git_branch}'에 연동된 Cortex 브랜치가 없습니다.",
        }

    def list_linked_branches(self, repo_path: str = None) -> Dict[str, Any]:
        """
        연동된 모든 브랜치 목록 반환

        Args:
            repo_path: Git 저장소 경로 (필터링용, 선택)

        Returns:
            연동된 브랜치 목록
        """
        branches = []

        for key, value in self._mapping.get("mappings", {}).items():
            if isinstance(value, dict) and "cortex_branch_id" in value:
                if repo_path and value.get("repo_path") != repo_path:
                    continue

                branches.append(
                    {
                        "git_branch": value.get("git_branch"),
                        "cortex_branch_id": value.get("cortex_branch_id"),
                        "repo_path": value.get("repo_path"),
                        "linked_at": value.get("linked_at"),
                    }
                )

        return {"success": True, "count": len(branches), "branches": branches}

    def unlink_git_branch(self, repo_path: str, git_branch: str) -> Dict[str, Any]:
        """
        Git-Cortex 브랜치 연동 해제

        Args:
            repo_path: Git 저장소 경로
            git_branch: Git 브랜치 이름

        Returns:
            해제 결과
        """
        mapping_key = self._make_mapping_key(repo_path, git_branch)

        if mapping_key not in self._mapping.get("mappings", {}):
            return {"success": False, "error": f"연동된 브랜치를 찾을 수 없습니다: {git_branch}"}

        del self._mapping["mappings"][mapping_key]
        self._save_mapping()

        return {
            "success": True,
            "git_branch": git_branch,
            "message": f"Git 브랜치 '{git_branch}' 연동이 해제되었습니다.",
        }

    def get_git_info(self, repo_path: str) -> Dict[str, Any]:
        """
        Git 저장소 전체 정보 반환

        Args:
            repo_path: Git 저장소 경로

        Returns:
            Git 저장소 정보
        """
        # 기본 정보
        branch_info = self.get_current_git_branch(repo_path)
        if not branch_info["success"]:
            return branch_info

        # 모든 로컬 브랜치
        try:
            result = subprocess.run(
                ["git", "branch", "--list"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            local_branches = []
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    branch = line.strip().lstrip("* ")
                    if branch:
                        local_branches.append(branch)
        except Exception:
            local_branches = []

        # 리모트 정보
        try:
            result = subprocess.run(
                ["git", "remote", "-v"], cwd=repo_path, capture_output=True, text=True, timeout=10
            )

            remotes = []
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            remotes.append({"name": parts[0], "url": parts[1]})
        except Exception:
            remotes = []

        # Cortex 연동 정보
        linked_branches = self.list_linked_branches(repo_path)

        return {
            "success": True,
            "current_branch": branch_info["git_branch"],
            "commit_hash": branch_info.get("commit_hash"),
            "local_branches": local_branches,
            "remotes": remotes,
            "cortex_linked_count": linked_branches.get("count", 0),
            "cortex_links": linked_branches.get("branches", []),
        }

    @track_call("git_sync")
    def auto_sync_on_checkout(self, repo_path: str, memory_manager=None) -> Dict[str, Any]:
        """
        Git checkout 시 자동 Cortex 브랜치 전환

        Args:
            repo_path: Git 저장소 경로
            memory_manager: MemoryManager 인스턴스 (브랜치 생성용)

        Returns:
            동기화 결과
        """
        # 브랜치 변경 확인
        change_result = self.check_branch_change(repo_path)
        if not change_result["success"]:
            return change_result

        if not change_result["changed"]:
            return {"success": True, "action": "none", "message": "브랜치 변경 없음"}

        new_git_branch = change_result["to_branch"]
        new_cortex_branch = change_result["to_cortex_branch"]

        # 새 브랜치에 Cortex 연동이 없으면 생성
        if not new_cortex_branch:
            link_result = self.link_git_branch(
                repo_path=repo_path, git_branch=new_git_branch, auto_create=True
            )

            if link_result["success"]:
                new_cortex_branch = link_result["cortex_branch_id"]

                # MemoryManager로 실제 브랜치 생성
                if memory_manager and self.project_id:
                    memory_manager.create_branch(
                        project_id=self.project_id,
                        branch_topic=new_git_branch,
                        parent_branch=change_result.get("from_cortex_branch"),
                    )

        return {
            "success": True,
            "action": "switched",
            "git_branch": new_git_branch,
            "cortex_branch_id": new_cortex_branch,
            "from_branch": change_result["from_branch"],
            "message": f"Cortex 브랜치가 '{new_cortex_branch}'로 전환되었습니다.",
        }

    def check_git_branch_change(
        self, project_id: str, repo_path: str, auto_create: bool = True
    ) -> Dict[str, Any]:
        """
        Git 브랜치 변경 감지 및 Cortex 브랜치 자동 전환

        Args:
            project_id: 프로젝트 ID
            repo_path: Git 저장소 경로
            auto_create: 새 브랜치 자동 생성 여부

        Returns:
            {
                "changed": bool,
                "old_branch": str,
                "new_branch": str,
                "cortex_branch_switched": bool
            }
        """
        # 브랜치 변경 확인
        change_result = self.check_branch_change(repo_path)
        if not change_result["success"]:
            return change_result

        if not change_result["changed"]:
            return {
                "changed": False,
                "old_branch": change_result["current_branch"],
                "new_branch": change_result["current_branch"],
                "cortex_branch_switched": False
            }

        # 브랜치가 변경됨
        old_branch = change_result["from_branch"]
        new_branch = change_result["to_branch"]
        new_cortex_branch = change_result["to_cortex_branch"]

        # 새 브랜치에 Cortex 연동이 없으면 자동 생성
        cortex_switched = False
        if not new_cortex_branch and auto_create:
            link_result = self.link_git_branch(
                repo_path=repo_path,
                git_branch=new_branch,
                auto_create=True
            )

            if link_result["success"]:
                new_cortex_branch = link_result["cortex_branch_id"]
                cortex_switched = True
        elif new_cortex_branch:
            cortex_switched = True

        return {
            "changed": True,
            "old_branch": old_branch,
            "new_branch": new_branch,
            "cortex_branch_switched": cortex_switched,
            "cortex_branch_id": new_cortex_branch
        }

    # ==================== Private Methods ====================

    def _get_commit_hash(self, repo_path: str) -> Optional[str]:
        """현재 커밋 해시 반환"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]  # 짧은 해시
        except Exception:
            pass
        return None

    def _make_mapping_key(self, repo_path: str, git_branch: str) -> str:
        """매핑 키 생성"""
        # 경로 정규화
        normalized_path = str(Path(repo_path).resolve())
        return f"{normalized_path}::{git_branch}"

    def _get_mapping(self, repo_path: str, git_branch: str) -> Optional[Dict]:
        """매핑 조회"""
        key = self._make_mapping_key(repo_path, git_branch)
        return self._mapping.get("mappings", {}).get(key)

    def _set_mapping(self, repo_path: str, git_branch: str, cortex_branch_id: str):
        """매핑 설정"""
        key = self._make_mapping_key(repo_path, git_branch)

        if "mappings" not in self._mapping:
            self._mapping["mappings"] = {}

        self._mapping["mappings"][key] = {
            "repo_path": str(Path(repo_path).resolve()),
            "git_branch": git_branch,
            "cortex_branch_id": cortex_branch_id,
            "linked_at": datetime.now(timezone.utc).isoformat(),
        }

    def _load_mapping(self):
        """매핑 파일 로드"""
        if not self.mapping_file.exists():
            self._mapping = {"version": "1.0", "mappings": {}}
            return

        try:
            self._mapping = json.loads(self.mapping_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            self._mapping = {"version": "1.0", "mappings": {}}

    def _save_mapping(self):
        """매핑 파일 저장"""
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)

        self._mapping["updated_at"] = datetime.now(timezone.utc).isoformat()

        self.mapping_file.write_text(
            json.dumps(self._mapping, ensure_ascii=False, indent=2), encoding="utf-8"
        )


# 전역 인스턴스
def get_git_sync(project_id: str = None) -> GitSync:
    """프로젝트별 GitSync 인스턴스 반환"""
    return GitSync(project_id=project_id)


# ========================================================================
# MCP Tools Interface Functions
# ========================================================================


def link_git_branch(
    project_id: str,
    repo_path: str,
    git_branch: Optional[str] = None,
    cortex_branch_id: Optional[str] = None,
    auto_create: bool = True,
) -> Dict[str, Any]:
    """
    Git 브랜치와 Cortex 브랜치 연동

    Args:
        project_id: 프로젝트 ID
        repo_path: Git 저장소 경로
        git_branch: Git 브랜치 이름 (없으면 현재 브랜치)
        cortex_branch_id: 연동할 Cortex 브랜치 ID
        auto_create: Cortex 브랜치 자동 생성

    Returns:
        연동 결과
    """
    git_sync = get_git_sync(project_id)

    # 현재 Git 브랜치 가져오기
    if not git_branch:
        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            git_branch = result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return {"error": f"Git 브랜치 조회 실패: {e}", "git_branch": None}

    # 매핑 저장
    mapping = git_sync._mapping.get("mappings", {})

    if cortex_branch_id:
        mapping[git_branch] = cortex_branch_id
    elif auto_create:
        # 자동 생성 로직은 memory_manager에서 처리
        mapping[git_branch] = f"auto_{git_branch}"

    git_sync._mapping["mappings"] = mapping
    git_sync._save_mapping()

    return {
        "git_branch": git_branch,
        "cortex_branch_id": mapping.get(git_branch),
        "auto_created": auto_create and not cortex_branch_id,
    }


def get_git_status(project_id: str, repo_path: str) -> Dict[str, Any]:
    """
    Git 저장소 상태 및 Cortex 연동 정보 반환

    Args:
        project_id: 프로젝트 ID
        repo_path: Git 저장소 경로

    Returns:
        Git 상태 및 연동 정보
    """
    git_sync = get_git_sync(project_id)

    # 현재 Git 브랜치
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
        current_branch = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return {"error": f"Git 상태 조회 실패: {e}", "current_branch": None}

    # 커밋 해시
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = result.stdout.strip()
    except subprocess.CalledProcessError:
        commit_hash = None

    # Cortex 연동 정보
    mapping = git_sync._mapping.get("mappings", {})
    cortex_branch_id = mapping.get(current_branch)

    return {
        "current_branch": current_branch,
        "commit_hash": commit_hash,
        "cortex_branch_id": cortex_branch_id,
        "is_linked": cortex_branch_id is not None,
    }


def check_git_branch_change(
    project_id: str, repo_path: str, auto_create: bool = True
) -> Dict[str, Any]:
    """
    Git 브랜치 변경 감지 및 자동 Cortex 전환

    Args:
        project_id: 프로젝트 ID
        repo_path: Git 저장소 경로
        auto_create: 새 브랜치일 경우 Cortex 브랜치 자동 생성

    Returns:
        브랜치 변경 감지 결과
    """
    status = get_git_status(project_id, repo_path)

    if status.get("error"):
        return status

    current_branch = status["current_branch"]
    cortex_branch_id = status.get("cortex_branch_id")

    if not cortex_branch_id and auto_create:
        # 연동 생성
        link_result = link_git_branch(
            project_id=project_id, repo_path=repo_path, git_branch=current_branch, auto_create=True
        )
        cortex_branch_id = link_result.get("cortex_branch_id")

        return {
            "changed": True,
            "current_branch": current_branch,
            "cortex_branch_id": cortex_branch_id,
            "auto_created": True,
        }

    return {
        "changed": False,
        "current_branch": current_branch,
        "cortex_branch_id": cortex_branch_id,
        "auto_created": False,
    }


def list_git_links(project_id: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Git-Cortex 브랜치 연동 목록 반환

    Args:
        project_id: 프로젝트 ID
        repo_path: Git 저장소 경로 (필터링용)

    Returns:
        연동 목록
    """
    git_sync = get_git_sync(project_id)
    mapping = git_sync._mapping.get("mappings", {})

    links = []
    for git_branch, cortex_branch_id in mapping.items():
        links.append({"git_branch": git_branch, "cortex_branch_id": cortex_branch_id})

    return {"links": links, "total_count": len(links)}


def unlink_git_branch(project_id: str, repo_path: str, git_branch: str) -> Dict[str, Any]:
    """
    Git-Cortex 브랜치 연동 해제

    Args:
        project_id: 프로젝트 ID
        repo_path: Git 저장소 경로
        git_branch: 연동 해제할 Git 브랜치 이름

    Returns:
        연동 해제 결과
    """
    git_sync = get_git_sync(project_id)
    mapping = git_sync._mapping.get("mappings", {})

    if git_branch in mapping:
        cortex_branch_id = mapping.pop(git_branch)
        git_sync._mapping["mappings"] = mapping
        git_sync._save_mapping()

        return {"unlinked": True, "git_branch": git_branch, "cortex_branch_id": cortex_branch_id}
    else:
        return {"unlinked": False, "git_branch": git_branch, "error": "연동이 존재하지 않습니다."}
