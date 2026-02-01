"""
Phase 9.2: Git Diff-Based Evidence Collection

목적: Git 변경 이력에서 Evidence 추출
설계: Alex Kim (Git Expert)
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .evidence_graph_v2 import Evidence, EvidenceType, get_evidence_graph_v2

logger = logging.getLogger(__name__)

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    logger.warning("GitPython not installed. Phase 9.2 disabled.")
    GIT_AVAILABLE = False


@dataclass
class GitChange:
    """Git 변경 정보"""
    file_path: str
    change_type: str  # A(add), M(modify), D(delete)
    diff_content: str
    commit_sha: str
    commit_message: str
    author: str
    timestamp: str


class GitEvidenceCollector:
    """
    Git 변경 이력에서 Evidence 추출

    Alex Kim's Strategy:
    1. Unstaged changes 우선 수집 (현재 작업)
    2. Recent commits 수집 (최근 10개)
    3. 변경된 파일별로 Evidence 생성
    """

    def __init__(self, repo_path: str):
        """
        Args:
            repo_path: Git 저장소 경로
        """
        if not GIT_AVAILABLE:
            raise RuntimeError("GitPython not installed. Install: pip install gitpython")

        self.repo_path = Path(repo_path)
        self.repo: Optional[git.Repo] = None

        try:
            self.repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            logger.warning(f"Not a Git repository: {repo_path}")
            self.repo = None

    def is_git_repo(self) -> bool:
        """Git 저장소 여부 확인"""
        return self.repo is not None

    def collect_unstaged_changes(self) -> List[GitChange]:
        """
        Unstaged 변경사항 수집 (현재 작업 중인 파일)

        Returns:
            GitChange 리스트
        """
        if not self.repo:
            return []

        changes = []

        try:
            # Unstaged files (modified but not staged)
            diff_index = self.repo.index.diff(None)

            for diff_item in diff_index:
                if diff_item.a_path.endswith(('.py', '.js', '.ts', '.java', '.go', '.cpp', '.c')):
                    change = GitChange(
                        file_path=diff_item.a_path,
                        change_type='M',  # Modified
                        diff_content=self._get_diff_content(diff_item),
                        commit_sha='unstaged',
                        commit_message='Current work in progress',
                        author='current_user',
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    changes.append(change)

            # Untracked files
            for untracked_path in self.repo.untracked_files:
                if untracked_path.endswith(('.py', '.js', '.ts', '.java', '.go', '.cpp', '.c')):
                    file_path = self.repo_path / untracked_path
                    if file_path.exists():
                        change = GitChange(
                            file_path=untracked_path,
                            change_type='A',  # Added
                            diff_content=file_path.read_text(encoding='utf-8', errors='ignore'),
                            commit_sha='unstaged',
                            commit_message='New file (untracked)',
                            author='current_user',
                            timestamp=datetime.now(timezone.utc).isoformat()
                        )
                        changes.append(change)

        except Exception as e:
            logger.error(f"Failed to collect unstaged changes: {e}")

        return changes

    def collect_recent_commits(self, limit: int = 10) -> List[GitChange]:
        """
        최근 커밋 수집

        Args:
            limit: 수집할 커밋 개수

        Returns:
            GitChange 리스트
        """
        if not self.repo:
            return []

        changes = []

        try:
            for commit in list(self.repo.iter_commits())[:limit]:
                # 각 커밋의 변경 파일
                if commit.parents:
                    parent = commit.parents[0]
                    diff_index = parent.diff(commit)

                    for diff_item in diff_index:
                        if diff_item.a_path and diff_item.a_path.endswith(('.py', '.js', '.ts', '.java', '.go', '.cpp', '.c')):
                            change = GitChange(
                                file_path=diff_item.a_path,
                                change_type=diff_item.change_type,
                                diff_content=self._get_diff_content(diff_item),
                                commit_sha=commit.hexsha[:8],
                                commit_message=commit.message.strip(),
                                author=commit.author.name,
                                timestamp=datetime.fromtimestamp(commit.committed_date, tz=timezone.utc).isoformat()
                            )
                            changes.append(change)

        except Exception as e:
            logger.error(f"Failed to collect recent commits: {e}")

        return changes

    def _get_diff_content(self, diff_item) -> str:
        """Diff 내용 추출"""
        try:
            if hasattr(diff_item, 'diff'):
                diff_bytes = diff_item.diff
                if isinstance(diff_bytes, bytes):
                    return diff_bytes.decode('utf-8', errors='ignore')
                return str(diff_bytes)
            return ""
        except Exception as e:
            logger.error(f"Failed to get diff content: {e}")
            return ""

    def extract_evidence_from_change(self, change: GitChange) -> List[Evidence]:
        """
        Git 변경에서 Evidence 추출

        Args:
            change: Git 변경 정보

        Returns:
            Evidence 리스트
        """
        evidences = []

        # 1. FILE_MODIFICATION Evidence
        file_evidence = Evidence(
            evidence_id=f"git:file:{change.commit_sha}:{change.file_path}",
            evidence_type=EvidenceType.FILE_MODIFICATION,
            content=f"File {change.change_type}: {change.file_path}",
            source=f"git:{change.commit_sha}",
            timestamp=change.timestamp,
            confidence=0.95,  # Git 이력은 신뢰도 높음
            metadata={
                "commit_sha": change.commit_sha,
                "commit_message": change.commit_message,
                "author": change.author,
                "change_type": change.change_type,
            }
        )
        evidences.append(file_evidence)

        # 2. 함수 정의 추출 (간단한 정규식)
        if change.change_type in ('A', 'M'):  # Added or Modified
            functions = self._extract_functions(change.diff_content, change.file_path)
            for func_name, func_signature in functions:
                func_evidence = Evidence(
                    evidence_id=f"git:func:{change.commit_sha}:{change.file_path}:{func_name}",
                    evidence_type=EvidenceType.FUNCTION_SIGNATURE,
                    content=func_signature,
                    source=f"git:{change.commit_sha}:{change.file_path}",
                    timestamp=change.timestamp,
                    confidence=0.85,
                    metadata={
                        "function_name": func_name,
                        "file_path": change.file_path,
                        "commit_sha": change.commit_sha,
                    }
                )
                evidences.append(func_evidence)

        # 3. 클래스 정의 추출
        if change.change_type in ('A', 'M'):
            classes = self._extract_classes(change.diff_content, change.file_path)
            for class_name, class_signature in classes:
                class_evidence = Evidence(
                    evidence_id=f"git:class:{change.commit_sha}:{change.file_path}:{class_name}",
                    evidence_type=EvidenceType.CLASS_DEFINITION,
                    content=class_signature,
                    source=f"git:{change.commit_sha}:{change.file_path}",
                    timestamp=change.timestamp,
                    confidence=0.85,
                    metadata={
                        "class_name": class_name,
                        "file_path": change.file_path,
                        "commit_sha": change.commit_sha,
                    }
                )
                evidences.append(class_evidence)

        return evidences

    def _extract_functions(self, content: str, file_path: str) -> List[tuple]:
        """함수 정의 추출 (간단한 패턴)"""
        functions = []

        if file_path.endswith('.py'):
            # Python: def function_name(...)
            pattern = r'^\+?\s*def\s+(\w+)\s*\([^)]*\)'
            for match in re.finditer(pattern, content, re.MULTILINE):
                func_name = match.group(1)
                func_signature = match.group(0).lstrip('+').strip()
                functions.append((func_name, func_signature))

        elif file_path.endswith(('.js', '.ts')):
            # JavaScript/TypeScript: function name(...) or const name = (...)
            pattern = r'^\+?\s*(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)'
            for match in re.finditer(pattern, content, re.MULTILINE):
                func_name = match.group(1) or match.group(2)
                if func_name:
                    functions.append((func_name, match.group(0).lstrip('+').strip()))

        return functions

    def _extract_classes(self, content: str, file_path: str) -> List[tuple]:
        """클래스 정의 추출"""
        classes = []

        if file_path.endswith('.py'):
            # Python: class ClassName
            pattern = r'^\+?\s*class\s+(\w+)'
            for match in re.finditer(pattern, content, re.MULTILINE):
                class_name = match.group(1)
                class_signature = match.group(0).lstrip('+').strip()
                classes.append((class_name, class_signature))

        elif file_path.endswith(('.js', '.ts')):
            # JavaScript/TypeScript: class ClassName
            pattern = r'^\+?\s*class\s+(\w+)'
            for match in re.finditer(pattern, content, re.MULTILINE):
                class_name = match.group(1)
                classes.append((class_name, match.group(0).lstrip('+').strip()))

        return classes

    def populate_evidence_graph(self, include_recent_commits: bool = True) -> Dict[str, int]:
        """
        Evidence Graph에 Git 변경사항 추가

        Args:
            include_recent_commits: 최근 커밋 포함 여부

        Returns:
            통계 (changes, evidences)
        """
        if not self.repo:
            logger.warning("Not a Git repository. Skipping Phase 9.2.")
            return {"changes": 0, "evidences": 0}

        graph = get_evidence_graph_v2()

        # 1. Unstaged 변경사항 수집
        changes = self.collect_unstaged_changes()

        # 2. 최근 커밋 수집 (선택)
        if include_recent_commits:
            changes.extend(self.collect_recent_commits(limit=10))

        logger.info(f"[Phase 9.2] Collected {len(changes)} Git changes")

        # 3. Evidence 추출 및 추가
        all_evidences = []
        for change in changes:
            evidences = self.extract_evidence_from_change(change)
            all_evidences.extend(evidences)

        # 4. 배치 추가
        added_count = graph.add_evidence_batch(all_evidences)

        logger.info(f"[Phase 9.2] Added {added_count}/{len(all_evidences)} evidences to graph")

        return {
            "changes": len(changes),
            "evidences": added_count,
        }


def populate_from_git(repo_path: str, include_recent_commits: bool = True) -> Dict[str, int]:
    """
    Git 저장소에서 Evidence 수집

    Args:
        repo_path: Git 저장소 경로
        include_recent_commits: 최근 커밋 포함 여부

    Returns:
        통계 딕셔너리
    """
    try:
        collector = GitEvidenceCollector(repo_path)

        if not collector.is_git_repo():
            logger.warning(f"Not a Git repository: {repo_path}")
            return {"changes": 0, "evidences": 0}

        return collector.populate_evidence_graph(include_recent_commits)

    except Exception as e:
        logger.error(f"[Phase 9.2] Failed to populate from Git: {e}")
        return {"changes": 0, "evidences": 0}
