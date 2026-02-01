"""
파일 변경 검증기

Git diff를 사용하여 파일이 실제로 변경되었는지 확인합니다.
AI가 "파일을 수정했습니다"라고 주장할 때 실제로 변경되었는지 독립적으로 검증.
"""
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseVerifier, Evidence, EvidenceType, VerificationResult

logger = logging.getLogger(__name__)


@dataclass
class GitDiff:
    """Git diff 결과"""
    file_path: str
    change_type: str  # "A" (added), "M" (modified), "D" (deleted), "R" (renamed)
    added_lines: List[str]
    removed_lines: List[str]
    raw_diff: str
    additions_count: int = 0
    deletions_count: int = 0

    def __post_init__(self):
        self.additions_count = len(self.added_lines)
        self.deletions_count = len(self.removed_lines)


class FileChangeVerifier(BaseVerifier):
    """
    파일 변경 검증기

    Git diff를 사용하여 파일 변경을 검증합니다.
    """

    # 파일 확장자 패턴
    FILE_EXTENSIONS = r'\.(?:py|js|ts|tsx|jsx|go|rs|java|cpp|c|h|hpp|md|json|yaml|yml|toml|xml|html|css|scss|sql|sh|bash|rb|php)'

    @property
    def verifier_type(self) -> str:
        return "file_change"

    def verify(self, claim: Any, context: Dict[str, Any]) -> VerificationResult:
        """
        Claim에서 언급된 파일 변경을 검증

        Args:
            claim: Claim 객체 (claim.text에서 파일 정보 추출)
            context: {
                "project_path": str,
                "mentioned_files": List[str] (선택),
                "expected_content": str (선택, 특정 내용 검증용)
            }

        Returns:
            VerificationResult
        """
        project_path = context.get("project_path", ".")
        mentioned_files = context.get("mentioned_files", [])
        expected_content = context.get("expected_content")

        # Claim 텍스트 추출
        claim_text = getattr(claim, 'text', str(claim))

        # Claim 텍스트에서 파일 경로 추출 (명시적으로 제공되지 않은 경우)
        if not mentioned_files:
            mentioned_files = self._extract_file_paths(claim_text)

        if not mentioned_files:
            logger.warning(f"[FileChangeVerifier] Claim에서 파일 경로를 찾을 수 없음: {claim_text[:100]}")
            return self._create_result(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason="Claim에서 파일 경로를 찾을 수 없음"
            )

        logger.info(f"[FileChangeVerifier] 검증할 파일: {mentioned_files}")

        # 각 파일에 대해 Git diff 확인
        evidence_list = []
        verified_files = []
        unverified_files = []

        for file_path in mentioned_files:
            # 상대 경로로 변환
            if os.path.isabs(file_path):
                rel_path = os.path.relpath(file_path, project_path)
            else:
                rel_path = file_path

            diff = self._get_git_diff(project_path, rel_path)

            if diff and (diff.added_lines or diff.removed_lines):
                # 변경 확인됨
                confidence = 0.95

                # 특정 내용이 예상되는 경우 추가 검증
                if expected_content:
                    added_text = '\n'.join(diff.added_lines)
                    if expected_content in added_text:
                        confidence = 0.98
                    else:
                        confidence = 0.7  # 변경은 있지만 예상 내용과 다름

                evidence = self._create_evidence(
                    type=EvidenceType.GIT_DIFF,
                    source=rel_path,
                    content=f"변경 감지: +{diff.additions_count} -{diff.deletions_count} lines",
                    confidence=confidence,
                    metadata={
                        "change_type": diff.change_type,
                        "added_lines_count": diff.additions_count,
                        "removed_lines_count": diff.deletions_count,
                        "raw_diff_preview": diff.raw_diff[:1000] if diff.raw_diff else "",
                        "added_lines_preview": diff.added_lines[:10],
                    }
                )
                evidence_list.append(evidence)
                verified_files.append(rel_path)
                logger.info(f"[FileChangeVerifier] 파일 변경 확인됨: {rel_path} (+{diff.additions_count} -{diff.deletions_count})")
            else:
                # 파일 존재 여부 확인
                full_path = os.path.join(project_path, rel_path)
                if os.path.exists(full_path):
                    # 파일은 존재하지만 변경 없음
                    evidence = self._create_evidence(
                        type=EvidenceType.FILE_EXISTS,
                        source=rel_path,
                        content=f"파일 존재하지만 변경 없음",
                        confidence=0.3,
                        metadata={"exists": True, "changed": False}
                    )
                    evidence_list.append(evidence)
                    logger.info(f"[FileChangeVerifier] 파일 존재하지만 변경 없음: {rel_path}")
                else:
                    logger.warning(f"[FileChangeVerifier] 파일 찾을 수 없음: {rel_path}")

                unverified_files.append(rel_path)

        # 결과 계산
        if verified_files:
            total = len(mentioned_files)
            verified_count = len(verified_files)
            confidence = verified_count / total

            # 종합 confidence 조정
            if evidence_list:
                avg_confidence = sum(e.confidence for e in evidence_list) / len(evidence_list)
                confidence = min(confidence, avg_confidence)

            return self._create_result(
                verified=confidence >= 0.5,  # 50% 이상 파일이 검증되면 성공
                confidence=confidence,
                evidence=evidence_list,
                reason=f"{verified_count}/{total} 파일 변경 확인됨: {verified_files}"
            )
        else:
            return self._create_result(
                verified=False,
                confidence=0.0 if not evidence_list else 0.2,
                evidence=evidence_list,
                reason=f"파일 변경을 확인할 수 없음: {unverified_files}"
            )

    def verify_specific_change(
        self,
        project_path: str,
        file_path: str,
        expected_content: str
    ) -> VerificationResult:
        """
        특정 내용이 추가되었는지 검증 (편의 메서드)

        Args:
            project_path: 프로젝트 경로
            file_path: 대상 파일
            expected_content: 추가되어야 할 내용

        Returns:
            VerificationResult
        """
        diff = self._get_git_diff(project_path, file_path)

        if not diff:
            return self._create_result(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason="Git diff를 가져올 수 없음"
            )

        # 추가된 라인에서 expected_content 검색
        added_text = '\n'.join(diff.added_lines)

        if expected_content in added_text:
            evidence = self._create_evidence(
                type=EvidenceType.GIT_DIFF,
                source=file_path,
                content=f"Expected content found in diff",
                confidence=0.98,
                metadata={
                    "matched_content": expected_content[:100],
                    "match_type": "exact"
                }
            )
            return self._create_result(
                verified=True,
                confidence=0.98,
                evidence=[evidence],
                reason=f"'{expected_content[:50]}...' 추가 확인됨"
            )
        else:
            # 부분 매칭 시도
            keywords = expected_content.split()[:5]  # 처음 5개 단어
            matched_keywords = [kw for kw in keywords if kw in added_text]

            if len(matched_keywords) >= len(keywords) * 0.6:
                evidence = self._create_evidence(
                    type=EvidenceType.GIT_DIFF,
                    source=file_path,
                    content=f"Partial match: {len(matched_keywords)}/{len(keywords)} keywords",
                    confidence=0.6,
                    metadata={
                        "matched_keywords": matched_keywords,
                        "match_type": "partial"
                    }
                )
                return self._create_result(
                    verified=True,
                    confidence=0.6,
                    evidence=[evidence],
                    reason=f"부분 매칭: {len(matched_keywords)}/{len(keywords)} 키워드"
                )

            return self._create_result(
                verified=False,
                confidence=0.1,
                evidence=[],
                reason=f"예상된 내용이 diff에서 발견되지 않음"
            )

    def get_changed_files(self, project_path: str, scope: str = "HEAD") -> List[str]:
        """
        변경된 파일 목록 반환

        Args:
            project_path: 프로젝트 경로
            scope: 비교 범위 (기본: HEAD)

        Returns:
            변경된 파일 경로 목록
        """
        try:
            # staged + unstaged 변경 파일
            cmd = ["git", "diff", "--name-only", scope]
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            files = []
            if result.returncode == 0 and result.stdout.strip():
                files.extend(result.stdout.strip().split('\n'))

            # staged 변경 파일
            cmd = ["git", "diff", "--cached", "--name-only"]
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                for f in result.stdout.strip().split('\n'):
                    if f not in files:
                        files.append(f)

            # unstaged 변경 파일
            cmd = ["git", "diff", "--name-only"]
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                for f in result.stdout.strip().split('\n'):
                    if f not in files:
                        files.append(f)

            return files

        except Exception as e:
            logger.error(f"[FileChangeVerifier] 변경 파일 목록 조회 실패: {e}")
            return []

    def _extract_file_paths(self, text: str) -> List[str]:
        """
        텍스트에서 파일 경로 추출

        패턴:
        - path/to/file.py
        - `file.py`
        - "file.py"
        - 'file.py'
        """
        patterns = [
            # 전체 경로 패턴 (예: cortex_mcp/core/verifiers/base.py)
            rf'[\w\-./]+{self.FILE_EXTENSIONS}',
            # 백틱으로 감싼 파일 (예: `file.py`)
            rf'`([^`]+{self.FILE_EXTENSIONS})`',
            # 큰따옴표로 감싼 파일 (예: "file.py")
            rf'"([^"]+{self.FILE_EXTENSIONS})"',
            # 작은따옴표로 감싼 파일 (예: 'file.py')
            rf"'([^']+{self.FILE_EXTENSIONS})'",
        ]

        files = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # 튜플인 경우 (그룹 캡처) 첫 번째 요소 사용
                file_path = match[0] if isinstance(match, tuple) else match
                # 공백, 특수문자 제거
                file_path = file_path.strip()
                if file_path and not file_path.startswith('.'):
                    files.add(file_path)

        return list(files)

    def _get_git_diff(
        self,
        project_path: str,
        file_path: str,
        scope: str = "HEAD"
    ) -> Optional[GitDiff]:
        """
        Git diff 수집

        Args:
            project_path: 프로젝트 경로
            file_path: 대상 파일 경로
            scope: 비교 범위 (기본: HEAD, 또는 "HEAD~1", "staged" 등)

        Returns:
            GitDiff 또는 None
        """
        try:
            diff_output = ""

            # 1. staged 변경 확인
            cmd = ["git", "diff", "--cached", "--", file_path]
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                diff_output = result.stdout

            # 2. unstaged 변경 확인
            if not diff_output:
                cmd = ["git", "diff", "--", file_path]
                result = subprocess.run(
                    cmd,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0 and result.stdout.strip():
                    diff_output = result.stdout

            # 3. HEAD와 비교 (커밋된 변경)
            if not diff_output and scope != "staged":
                cmd = ["git", "diff", scope, "--", file_path]
                result = subprocess.run(
                    cmd,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0 and result.stdout.strip():
                    diff_output = result.stdout

            # 4. 최근 커밋과 비교
            if not diff_output:
                cmd = ["git", "diff", "HEAD~1", "--", file_path]
                result = subprocess.run(
                    cmd,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0 and result.stdout.strip():
                    diff_output = result.stdout

            if not diff_output:
                return None

            # diff 파싱
            return self._parse_diff(file_path, diff_output)

        except subprocess.TimeoutExpired:
            logger.error(f"[FileChangeVerifier] Git diff 타임아웃: {file_path}")
            return None
        except Exception as e:
            logger.error(f"[FileChangeVerifier] Git diff 오류: {e}")
            return None

    def _parse_diff(self, file_path: str, diff_output: str) -> GitDiff:
        """
        Git diff 출력 파싱

        Args:
            file_path: 파일 경로
            diff_output: git diff 출력

        Returns:
            GitDiff 객체
        """
        added_lines = []
        removed_lines = []

        for line in diff_output.split('\n'):
            # 추가된 라인 (+로 시작, +++는 제외)
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:])
            # 삭제된 라인 (-로 시작, ---는 제외)
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines.append(line[1:])

        # 변경 유형 결정
        if added_lines and not removed_lines:
            change_type = "A"  # 추가만
        elif removed_lines and not added_lines:
            change_type = "D"  # 삭제만
        else:
            change_type = "M"  # 수정

        return GitDiff(
            file_path=file_path,
            change_type=change_type,
            added_lines=added_lines,
            removed_lines=removed_lines,
            raw_diff=diff_output[:3000]  # 너무 긴 diff truncate
        )

    def _check_file_in_git(self, project_path: str, file_path: str) -> bool:
        """파일이 Git에서 추적되고 있는지 확인"""
        try:
            cmd = ["git", "ls-files", file_path]
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return bool(result.stdout.strip())
        except Exception:
            return False
