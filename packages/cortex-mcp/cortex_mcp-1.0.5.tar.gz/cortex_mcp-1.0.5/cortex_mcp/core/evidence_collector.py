"""
Evidence Collector - 실시간 Evidence 수집기

Hallucination Detection의 핵심 컴포넌트.
Git, File, Execution 상태에서 Evidence를 수집하여
Claim 검증에 사용할 수 있도록 구조화합니다.

핵심 기능:
1. Git Evidence: git diff, git log에서 변경 내용 수집
2. File Evidence: 파일 존재 여부, 내용, 해시 수집
3. Execution Evidence: 명령 실행 결과 수집
"""

import subprocess
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)


@dataclass
class GitEvidence:
    """Git 기반 Evidence"""
    commit_hash: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    diff_content: Dict[str, str] = field(default_factory=dict)  # file_path -> diff
    staged_files: List[str] = field(default_factory=list)
    unstaged_files: List[str] = field(default_factory=list)
    commit_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    evidence_type: str = "git"

    def to_dict(self) -> Dict:
        return {
            "evidence_type": self.evidence_type,
            "commit_hash": self.commit_hash,
            "files_changed": self.files_changed,
            "diff_content": self.diff_content,
            "staged_files": self.staged_files,
            "unstaged_files": self.unstaged_files,
            "commit_message": self.commit_message,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class FileEvidence:
    """파일 기반 Evidence"""
    file_path: str
    exists: bool
    content_hash: Optional[str] = None
    content: Optional[str] = None
    size_bytes: int = 0
    last_modified: Optional[datetime] = None
    evidence_type: str = "file"

    def to_dict(self) -> Dict:
        return {
            "evidence_type": self.evidence_type,
            "file_path": self.file_path,
            "exists": self.exists,
            "content_hash": self.content_hash,
            "content": self.content[:500] if self.content else None,  # 요약
            "size_bytes": self.size_bytes,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
        }


@dataclass
class ExecutionEvidence:
    """명령 실행 결과 기반 Evidence"""
    command: str
    output: str
    exit_code: int
    stderr: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    evidence_type: str = "execution"

    def to_dict(self) -> Dict:
        return {
            "evidence_type": self.evidence_type,
            "command": self.command,
            "output": self.output[:1000] if self.output else "",  # 요약
            "exit_code": self.exit_code,
            "stderr": self.stderr[:500] if self.stderr else "",
            "timestamp": self.timestamp.isoformat(),
        }


class EvidenceCollector:
    """
    실시간 Evidence 수집기

    사용 예시:
        collector = EvidenceCollector("/path/to/project")

        # 모든 Evidence 수집
        all_evidence = collector.collect_all()

        # Git Evidence만 수집
        git_evidence = collector.collect_git_evidence()

        # 특정 파일들의 Evidence 수집
        file_evidence = collector.collect_file_evidence(["src/main.py", "tests/test_main.py"])
    """

    def __init__(self, project_path: str, max_diff_size: int = 10000):
        """
        EvidenceCollector 초기화

        Args:
            project_path: 프로젝트 루트 경로
            max_diff_size: diff 내용 최대 크기 (문자 수)
        """
        self.project_path = Path(project_path)
        self.max_diff_size = max_diff_size

        if not self.project_path.exists():
            logger.warning(f"Project path does not exist: {project_path}")

    def collect_all(self) -> Dict[str, List]:
        """
        모든 타입의 Evidence 수집

        Returns:
            {
                "git": [GitEvidence, ...],
                "files": [FileEvidence, ...],
                "execution": []
            }
        """
        result = {
            "git": [],
            "files": [],
            "execution": [],
        }

        # Git Evidence 수집
        git_evidence = self.collect_git_evidence()
        if git_evidence:
            result["git"].append(git_evidence)

        # 변경된 파일들의 File Evidence 수집
        if git_evidence:
            all_changed = git_evidence.files_changed + git_evidence.staged_files + git_evidence.unstaged_files
            unique_files = list(set(all_changed))
            if unique_files:
                result["files"] = self.collect_file_evidence(unique_files)

        logger.info(
            f"[EVIDENCE] Collected: git={len(result['git'])}, "
            f"files={len(result['files'])}, execution={len(result['execution'])}"
        )

        return result

    def collect_git_evidence(self) -> Optional[GitEvidence]:
        """
        현재 Git 상태에서 Evidence 수집

        수집 항목:
        - Staged files (git diff --cached)
        - Unstaged files (git diff)
        - 변경된 파일 목록
        - 각 파일의 diff 내용
        - 최근 커밋 정보
        """
        if not self._is_git_repo():
            logger.debug("Not a git repository")
            return None

        evidence = GitEvidence()

        try:
            # 1. Staged files 목록
            staged_result = self._run_git_command(["diff", "--cached", "--name-only"])
            if staged_result:
                evidence.staged_files = [f.strip() for f in staged_result.split("\n") if f.strip()]

            # 2. Unstaged files 목록
            unstaged_result = self._run_git_command(["diff", "--name-only"])
            if unstaged_result:
                evidence.unstaged_files = [f.strip() for f in unstaged_result.split("\n") if f.strip()]

            # 3. 전체 변경 파일 목록
            evidence.files_changed = list(set(evidence.staged_files + evidence.unstaged_files))

            # 4. 각 파일의 diff 내용 수집
            for file_path in evidence.files_changed[:20]:  # 최대 20개 파일
                diff = self._get_file_diff(file_path)
                if diff:
                    evidence.diff_content[file_path] = diff

            # 5. 최근 커밋 정보
            log_result = self._run_git_command(["log", "-1", "--format=%H|%s"])
            if log_result:
                parts = log_result.strip().split("|", 1)
                if len(parts) >= 1:
                    evidence.commit_hash = parts[0]
                if len(parts) >= 2:
                    evidence.commit_message = parts[1]

            logger.info(
                f"[GIT_EVIDENCE] staged={len(evidence.staged_files)}, "
                f"unstaged={len(evidence.unstaged_files)}, "
                f"diffs={len(evidence.diff_content)}"
            )

            return evidence

        except Exception as e:
            logger.error(f"Failed to collect git evidence: {e}")
            return None

    def collect_file_evidence(self, file_paths: List[str]) -> List[FileEvidence]:
        """
        지정된 파일들의 Evidence 수집

        Args:
            file_paths: 수집할 파일 경로 목록

        Returns:
            FileEvidence 목록
        """
        evidences = []

        for file_path in file_paths:
            evidence = self._collect_single_file_evidence(file_path)
            evidences.append(evidence)

        return evidences

    def collect_execution_evidence(
        self,
        command: str,
        output: str,
        exit_code: int,
        stderr: str = ""
    ) -> ExecutionEvidence:
        """
        명령 실행 결과에서 Evidence 수집

        Args:
            command: 실행된 명령어
            output: stdout 결과
            exit_code: 종료 코드
            stderr: stderr 결과

        Returns:
            ExecutionEvidence
        """
        return ExecutionEvidence(
            command=command,
            output=output,
            exit_code=exit_code,
            stderr=stderr,
            timestamp=datetime.now(timezone.utc)
        )

    def _is_git_repo(self) -> bool:
        """Git 저장소인지 확인"""
        git_dir = self.project_path / ".git"
        return git_dir.exists()

    def _run_git_command(self, args: List[str], timeout: int = 10) -> Optional[str]:
        """Git 명령 실행"""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except subprocess.TimeoutExpired:
            logger.warning(f"Git command timeout: git {' '.join(args)}")
            return None
        except Exception as e:
            logger.error(f"Git command failed: {e}")
            return None

    def _get_file_diff(self, file_path: str) -> Optional[str]:
        """특정 파일의 diff 내용 가져오기"""
        # Staged diff 먼저 시도
        diff = self._run_git_command(["diff", "--cached", "--", file_path])

        # Staged가 없으면 unstaged diff
        if not diff:
            diff = self._run_git_command(["diff", "--", file_path])

        if diff and len(diff) > self.max_diff_size:
            diff = diff[:self.max_diff_size] + "\n... [truncated]"

        return diff

    def _collect_single_file_evidence(self, file_path: str) -> FileEvidence:
        """단일 파일의 Evidence 수집"""
        # 상대 경로인 경우 프로젝트 경로 기준으로 변환
        if not Path(file_path).is_absolute():
            full_path = self.project_path / file_path
        else:
            full_path = Path(file_path)

        evidence = FileEvidence(
            file_path=str(file_path),
            exists=full_path.exists()
        )

        if evidence.exists and full_path.is_file():
            try:
                stat = full_path.stat()
                evidence.size_bytes = stat.st_size
                evidence.last_modified = datetime.fromtimestamp(stat.st_mtime)

                # 파일 크기가 적당하면 내용 읽기
                if evidence.size_bytes < 50000:  # 50KB 이하
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    evidence.content = content
                    evidence.content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            except Exception as e:
                logger.debug(f"Failed to read file {file_path}: {e}")

        return evidence

    def get_function_content(self, file_path: str, function_name: str) -> Optional[str]:
        """
        파일에서 특정 함수의 내용 추출

        Args:
            file_path: 파일 경로
            function_name: 함수 이름

        Returns:
            함수 내용 또는 None
        """
        if not Path(file_path).is_absolute():
            full_path = self.project_path / file_path
        else:
            full_path = Path(file_path)

        if not full_path.exists():
            return None

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")

            # Python 함수 패턴
            if file_path.endswith(".py"):
                pattern = rf"(def {function_name}\s*\([^)]*\).*?(?=\ndef |\nclass |\Z))"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    return match.group(1).strip()

            # JavaScript/TypeScript 함수 패턴
            elif file_path.endswith((".js", ".ts", ".jsx", ".tsx")):
                patterns = [
                    rf"(function {function_name}\s*\([^)]*\)\s*\{{.*?\}})",
                    rf"(const {function_name}\s*=\s*\([^)]*\)\s*=>\s*\{{.*?\}})",
                    rf"({function_name}\s*\([^)]*\)\s*\{{.*?\}})",
                ]
                for pattern in patterns:
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        return match.group(1).strip()

            return None

        except Exception as e:
            logger.debug(f"Failed to extract function {function_name} from {file_path}: {e}")
            return None

    def get_class_content(self, file_path: str, class_name: str) -> Optional[str]:
        """
        파일에서 특정 클래스의 내용 추출

        Args:
            file_path: 파일 경로
            class_name: 클래스 이름

        Returns:
            클래스 내용 또는 None
        """
        if not Path(file_path).is_absolute():
            full_path = self.project_path / file_path
        else:
            full_path = Path(file_path)

        if not full_path.exists():
            return None

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")

            # Python 클래스 패턴
            if file_path.endswith(".py"):
                pattern = rf"(class {class_name}.*?(?=\nclass |\Z))"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    return match.group(1).strip()

            return None

        except Exception as e:
            logger.debug(f"Failed to extract class {class_name} from {file_path}: {e}")
            return None


# 편의 함수
def get_evidence_collector(project_path: str) -> EvidenceCollector:
    """EvidenceCollector 인스턴스 생성"""
    return EvidenceCollector(project_path)
