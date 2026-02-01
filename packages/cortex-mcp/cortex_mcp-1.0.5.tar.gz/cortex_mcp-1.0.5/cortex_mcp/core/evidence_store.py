"""
Evidence Store - 세션 내 Evidence 저장소

Evidence를 메모리에 저장하고, Claim과 관련된 Evidence를 검색합니다.

핵심 기능:
1. Evidence 저장 (Git, File, Execution)
2. Claim 기반 관련 Evidence 검색
3. 세션 간 Evidence 새로고침
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

from .evidence_collector import (
    GitEvidence,
    FileEvidence,
    ExecutionEvidence,
    EvidenceCollector
)

logger = logging.getLogger(__name__)

# Evidence 타입 통합
Evidence = Union[GitEvidence, FileEvidence, ExecutionEvidence]


class EvidenceStore:
    """
    세션 내 Evidence 저장소

    사용 예시:
        store = EvidenceStore(project_path="/path/to/project")

        # Evidence 새로고침 (현재 Git/File 상태 수집)
        store.refresh()

        # Claim과 관련된 Evidence 검색
        claim = {"type": "implementation_claim", "content": "added function foo to main.py"}
        relevant = store.get_relevant(claim)
    """

    def __init__(self, project_path: str):
        """
        EvidenceStore 초기화

        Args:
            project_path: 프로젝트 루트 경로
        """
        self.project_path = Path(project_path)
        self.collector = EvidenceCollector(project_path)

        # Evidence 저장소
        self._git_evidences: List[GitEvidence] = []
        self._file_evidences: Dict[str, FileEvidence] = {}  # file_path -> evidence
        self._execution_evidences: List[ExecutionEvidence] = []

        # 최근 refresh 시간
        self._last_refresh: Optional[datetime] = None

    def add(self, evidence: Evidence) -> None:
        """
        Evidence 추가

        Args:
            evidence: GitEvidence, FileEvidence, 또는 ExecutionEvidence
        """
        if isinstance(evidence, GitEvidence):
            self._git_evidences.append(evidence)
            logger.debug(f"[STORE] Added GitEvidence with {len(evidence.files_changed)} files")

        elif isinstance(evidence, FileEvidence):
            self._file_evidences[evidence.file_path] = evidence
            logger.debug(f"[STORE] Added FileEvidence for {evidence.file_path}")

        elif isinstance(evidence, ExecutionEvidence):
            self._execution_evidences.append(evidence)
            logger.debug(f"[STORE] Added ExecutionEvidence for '{evidence.command[:50]}...'")

    def add_batch(self, evidences: List[Evidence]) -> None:
        """
        여러 Evidence 일괄 추가

        Args:
            evidences: Evidence 목록
        """
        for evidence in evidences:
            self.add(evidence)

    def refresh(self) -> Dict[str, int]:
        """
        Evidence 새로고침 (현재 Git/File 상태 재수집)

        Returns:
            수집된 Evidence 개수 {type: count}
        """
        logger.info("[STORE] Refreshing evidence...")

        # 기존 데이터 클리어
        self._git_evidences.clear()
        self._file_evidences.clear()
        # Execution evidence는 유지 (수동으로 추가되는 것이므로)

        # 새로운 Evidence 수집
        collected = self.collector.collect_all()

        # 저장
        for git_ev in collected.get("git", []):
            self.add(git_ev)

        for file_ev in collected.get("files", []):
            self.add(file_ev)

        self._last_refresh = datetime.now(timezone.utc)

        result = {
            "git": len(self._git_evidences),
            "files": len(self._file_evidences),
            "execution": len(self._execution_evidences),
        }

        logger.info(f"[STORE] Refresh complete: {result}")
        return result

    def get_relevant(self, claim: Dict) -> List[Evidence]:
        """
        Claim과 관련된 Evidence 검색

        Args:
            claim: 검증할 Claim
                - type: claim 타입 (implementation_claim, existence_claim, etc.)
                - content: claim 내용
                - file_path: (선택) 관련 파일 경로
                - function_name: (선택) 관련 함수명

        Returns:
            관련 Evidence 목록
        """
        relevant = []

        claim_type = claim.get("type", "")
        claim_content = claim.get("content", "")
        claim_file = claim.get("file_path", "")
        claim_function = claim.get("function_name", "")

        # 1. File path가 명시된 경우 해당 파일의 Evidence 우선
        if claim_file:
            file_ev = self._file_evidences.get(claim_file)
            if file_ev:
                relevant.append(file_ev)

            # Git diff에서 해당 파일 찾기
            for git_ev in self._git_evidences:
                if claim_file in git_ev.files_changed:
                    relevant.append(git_ev)
                    break

        # 2. Claim 내용에서 파일 경로 추출하여 검색
        extracted_files = self._extract_file_paths(claim_content)
        for file_path in extracted_files:
            if file_path in self._file_evidences and file_path != claim_file:
                relevant.append(self._file_evidences[file_path])

        # 3. 함수/클래스명으로 검색
        if claim_function:
            for file_path, file_ev in self._file_evidences.items():
                if file_ev.content and claim_function in file_ev.content:
                    if file_ev not in relevant:
                        relevant.append(file_ev)

        # 4. Git diff 내용에서 키워드 검색
        keywords = self._extract_keywords(claim_content)
        for git_ev in self._git_evidences:
            for file_path, diff_content in git_ev.diff_content.items():
                if any(kw.lower() in diff_content.lower() for kw in keywords):
                    if git_ev not in relevant:
                        relevant.append(git_ev)
                        break

        # 5. Execution Evidence 검색 (performance claim인 경우)
        if claim_type == "performance_claim":
            for exec_ev in self._execution_evidences:
                # 숫자/시간 관련 내용이 있는 경우 추가
                if any(kw in exec_ev.output.lower() for kw in ["ms", "second", "time", "faster", "slower"]):
                    relevant.append(exec_ev)

        # 6. Evidence가 없으면 모든 Git Evidence 반환 (최소한의 컨텍스트)
        if not relevant and self._git_evidences:
            relevant.extend(self._git_evidences)

        logger.debug(f"[STORE] Found {len(relevant)} relevant evidences for claim type={claim_type}")
        return relevant

    def get_file_evidence(self, file_path: str) -> Optional[FileEvidence]:
        """
        특정 파일의 Evidence 반환

        Args:
            file_path: 파일 경로

        Returns:
            FileEvidence 또는 None
        """
        return self._file_evidences.get(file_path)

    def get_all_git_evidences(self) -> List[GitEvidence]:
        """모든 Git Evidence 반환"""
        return self._git_evidences.copy()

    def get_all_file_evidences(self) -> List[FileEvidence]:
        """모든 File Evidence 반환"""
        return list(self._file_evidences.values())

    def get_all_execution_evidences(self) -> List[ExecutionEvidence]:
        """모든 Execution Evidence 반환"""
        return self._execution_evidences.copy()

    def get_changed_files(self) -> List[str]:
        """변경된 파일 목록 반환"""
        all_files = set()
        for git_ev in self._git_evidences:
            all_files.update(git_ev.files_changed)
            all_files.update(git_ev.staged_files)
            all_files.update(git_ev.unstaged_files)
        return list(all_files)

    def has_file_change(self, file_path: str) -> bool:
        """특정 파일이 변경되었는지 확인"""
        for git_ev in self._git_evidences:
            if file_path in git_ev.files_changed:
                return True
            if file_path in git_ev.staged_files:
                return True
            if file_path in git_ev.unstaged_files:
                return True
        return False

    def get_file_diff(self, file_path: str) -> Optional[str]:
        """특정 파일의 diff 내용 반환"""
        for git_ev in self._git_evidences:
            if file_path in git_ev.diff_content:
                return git_ev.diff_content[file_path]
        return None

    def search_in_diffs(self, keyword: str) -> List[Dict]:
        """
        모든 diff에서 키워드 검색

        Args:
            keyword: 검색할 키워드

        Returns:
            매칭된 결과 목록 [{"file_path": str, "matched_lines": List[str]}]
        """
        results = []
        keyword_lower = keyword.lower()

        for git_ev in self._git_evidences:
            for file_path, diff_content in git_ev.diff_content.items():
                matched_lines = []
                for line in diff_content.split("\n"):
                    if keyword_lower in line.lower():
                        matched_lines.append(line.strip())

                if matched_lines:
                    results.append({
                        "file_path": file_path,
                        "matched_lines": matched_lines[:10],  # 최대 10줄
                    })

        return results

    def _extract_file_paths(self, text: str) -> List[str]:
        """텍스트에서 파일 경로 추출"""
        # 일반적인 파일 경로 패턴
        patterns = [
            r'[\w/\-_]+\.\w{1,10}',  # path/to/file.ext
            r'"([^"]+\.\w{1,10})"',  # "file.ext"
            r"'([^']+\.\w{1,10})'",  # 'file.ext'
            r'`([^`]+\.\w{1,10})`',  # `file.ext`
        ]

        paths = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                # 유효한 파일 확장자인지 확인
                if re.search(r'\.(py|js|ts|jsx|tsx|java|go|rs|rb|php|c|cpp|h|hpp|md|txt|json|yaml|yml)$', match):
                    paths.add(match)

        return list(paths)

    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 검색 키워드 추출"""
        # 영어/한국어 단어 추출 (2글자 이상)
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', text)

        # 일반적인 stop words 제외
        stop_words = {
            "the", "this", "that", "with", "from", "have", "has", "had",
            "was", "were", "are", "been", "being", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "function", "class", "method", "file", "code", "implement",
            "add", "added", "create", "created", "update", "updated",
        }

        keywords = [w for w in words if w.lower() not in stop_words]

        # 중복 제거 및 상위 10개만
        return list(dict.fromkeys(keywords))[:10]

    def to_dict(self) -> Dict[str, Any]:
        """저장소 상태를 딕셔너리로 반환"""
        return {
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "git_count": len(self._git_evidences),
            "file_count": len(self._file_evidences),
            "execution_count": len(self._execution_evidences),
            "changed_files": self.get_changed_files(),
        }

    def clear(self) -> None:
        """모든 Evidence 삭제"""
        self._git_evidences.clear()
        self._file_evidences.clear()
        self._execution_evidences.clear()
        self._last_refresh = None
        logger.info("[STORE] All evidences cleared")


# 편의 함수
def get_evidence_store(project_path: str) -> EvidenceStore:
    """EvidenceStore 인스턴스 생성"""
    return EvidenceStore(project_path)
