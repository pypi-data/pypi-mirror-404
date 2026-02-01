"""
Evidence Matcher - Claim과 Evidence의 의미적 매칭

Claim이 실제 Evidence에 의해 뒷받침되는지 검증합니다.

핵심 기능:
1. 의미적 유사도 매칭 (임베딩 기반)
2. 정확한 내용 매칭 (코드, 파일명)
3. Claim 타입별 맞춤 검증 전략
"""

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .evidence_collector import GitEvidence, FileEvidence, ExecutionEvidence

logger = logging.getLogger(__name__)

# Evidence 타입 통합
Evidence = Union[GitEvidence, FileEvidence, ExecutionEvidence]


@dataclass
class MatchResult:
    """Claim-Evidence 매칭 결과"""
    matched: bool  # 매칭 성공 여부
    score: float  # 매칭 점수 (0.0 ~ 1.0)
    claim_type: str  # Claim 타입
    evidence_used: List[Evidence] = field(default_factory=list)  # 사용된 Evidence
    reasoning: str = ""  # 매칭 근거 설명
    details: Dict[str, Any] = field(default_factory=dict)  # 추가 상세 정보

    def to_dict(self) -> Dict:
        return {
            "matched": self.matched,
            "score": self.score,
            "claim_type": self.claim_type,
            "evidence_count": len(self.evidence_used),
            "reasoning": self.reasoning,
            "details": self.details,
        }


class EvidenceMatcher:
    """
    Claim과 Evidence의 의미적 매칭

    사용 예시:
        matcher = EvidenceMatcher(project_path="/path/to/project")

        claim = {
            "type": "implementation_claim",
            "content": "added function calculate_total to utils.py",
            "file_path": "utils.py"
        }

        evidences = [git_evidence, file_evidence, ...]
        result = matcher.match(claim, evidences)

        if result.matched and result.score >= 0.7:
            print("Claim is grounded!")
    """

    def __init__(self, project_path: str = None, embedder=None):
        """
        EvidenceMatcher 초기화

        Args:
            project_path: 프로젝트 루트 경로 (파일 시스템 직접 확인용)
            embedder: 임베딩 모델 (None이면 텍스트 매칭만 사용)
        """
        self.project_path = Path(project_path) if project_path else None
        self.embedder = embedder
        self._try_load_embedder()

    def _try_load_embedder(self):
        """임베더 로드 시도"""
        if self.embedder is not None:
            return

        try:
            from .shared_embedder import get_shared_embedder
            self.embedder = get_shared_embedder()
            logger.debug("Loaded shared embedder for semantic matching")
        except Exception as e:
            logger.debug(f"Embedder not available, using text matching only: {e}")
            self.embedder = None

    def match(self, claim: Dict, evidences: List[Evidence]) -> MatchResult:
        """
        Claim과 Evidence 매칭

        Args:
            claim: 검증할 Claim
                - type: claim 타입
                - content: claim 내용
                - file_path: (선택) 관련 파일
                - function_name: (선택) 관련 함수명

            evidences: 비교할 Evidence 목록

        Returns:
            MatchResult: 매칭 결과
        """
        if not evidences:
            return MatchResult(
                matched=False,
                score=0.0,
                claim_type=claim.get("type", "unknown"),
                reasoning="No evidence available for verification"
            )

        claim_type = claim.get("type", "unknown")

        # Claim 타입별 매칭 전략
        if claim_type == "implementation_claim":
            return self._match_implementation(claim, evidences)
        elif claim_type == "existence_claim":
            return self._match_existence(claim, evidences)
        elif claim_type == "modification_claim":
            return self._match_modification(claim, evidences)
        elif claim_type == "performance_claim":
            return self._match_performance(claim, evidences)
        elif claim_type == "bug_fix_claim":
            return self._match_bug_fix(claim, evidences)
        else:
            return self._match_generic(claim, evidences)

    def _match_implementation(self, claim: Dict, evidences: List[Evidence]) -> MatchResult:
        """
        구현 주장 매칭

        "added function foo to bar.py" 같은 주장을 검증

        검증 순서:
        1. 파일 시스템 직접 확인 (Git 상태와 무관)
        2. Evidence 기반 추가 검증
        """
        content = claim.get("content", "")
        file_path = claim.get("file_path", "")
        function_name = claim.get("function_name", "")

        score = 0.0
        matched_evidences = []
        reasons = []

        # 0. 파일 시스템 직접 확인 (최우선 - Git 상태와 무관)
        fs_score = 0.0
        if self.project_path:
            fs_score = self._check_filesystem_directly(content, file_path, function_name)
            if fs_score > 0:
                score += fs_score * 0.5  # 파일 시스템 확인이 가장 중요 (50%)
                reasons.append(f"Filesystem verified: {fs_score:.2f}")

        # 1. 파일 경로 매칭 (20%)
        file_score, file_evidence = self._check_file_in_evidence(file_path or content, evidences)
        if file_score > 0:
            score += file_score * 0.2
            if file_evidence:
                matched_evidences.append(file_evidence)
            reasons.append(f"File match: {file_score:.2f}")

        # 2. Diff 내용에서 함수/클래스명 검색 (15%)
        if function_name:
            diff_score = self._check_function_in_diffs(function_name, evidences)
        else:
            # Claim에서 함수명 추출 시도
            extracted_func = self._extract_function_name(content)
            diff_score = self._check_function_in_diffs(extracted_func, evidences) if extracted_func else 0.0

        score += diff_score * 0.15
        if diff_score > 0:
            reasons.append(f"Diff content match: {diff_score:.2f}")

        # 3. 의미적 유사도 (15%)
        semantic_score = self._semantic_match_with_evidences(content, evidences)
        score += semantic_score * 0.15
        if semantic_score > 0:
            reasons.append(f"Semantic match: {semantic_score:.2f}")

        # Git Evidence 추가
        for ev in evidences:
            if isinstance(ev, GitEvidence) and ev not in matched_evidences:
                matched_evidences.append(ev)
                break

        return MatchResult(
            matched=score >= 0.5,
            score=min(1.0, score),
            claim_type="implementation_claim",
            evidence_used=matched_evidences,
            reasoning=" | ".join(reasons) if reasons else "No matching evidence found",
            details={
                "filesystem_score": fs_score,
                "file_score": file_score,
                "diff_score": diff_score,
                "semantic_score": semantic_score,
            }
        )

    def _check_filesystem_directly(self, content: str, file_path: str, function_name: str) -> float:
        """
        파일 시스템을 직접 확인하여 구현 검증 (Git 상태와 무관)

        Returns:
            0.0 ~ 1.0 점수
        """
        if not self.project_path:
            return 0.0

        score = 0.0

        # 1. 파일 경로 추출
        target_files = []
        if file_path:
            target_files.append(file_path)

        # content에서도 파일 경로 추출
        extracted = self._extract_file_paths(content)
        target_files.extend(extracted)

        if not target_files:
            return 0.0

        # 2. 각 파일 확인
        for fp in target_files:
            # 여러 경로 시도 (상대 경로 처리)
            candidates = [
                self.project_path / fp,
                self.project_path / "cortex_mcp" / fp,
                self.project_path / "cortex_mcp" / "core" / Path(fp).name,
            ]

            for full_path in candidates:
                if full_path.exists() and full_path.is_file():
                    score = 0.8  # 파일 존재 확인 (existence_claim에서는 충분한 증거)

                    # 3. 클래스/함수명 확인
                    try:
                        file_content = full_path.read_text(encoding="utf-8", errors="ignore")

                        # function_name이 있으면 확인
                        if function_name and function_name in file_content:
                            score = 1.0
                            break

                        # content에서 클래스/함수명 추출해서 확인
                        class_match = re.search(r'(\w+)\s+클래스', content)
                        func_match = re.search(r'(\w+)\s+함수', content)

                        if class_match:
                            class_name = class_match.group(1)
                            if f"class {class_name}" in file_content:
                                score = 1.0
                                break

                        if func_match:
                            func_name = func_match.group(1)
                            if f"def {func_name}" in file_content:
                                score = 1.0
                                break

                    except Exception as e:
                        logger.debug(f"Error reading file {full_path}: {e}")

                    break  # 파일 찾으면 다음 파일로

        return score

    def _match_existence(self, claim: Dict, evidences: List[Evidence]) -> MatchResult:
        """
        존재 주장 매칭

        "file foo.py exists" 또는 "function bar is defined" 같은 주장 검증
        """
        content = claim.get("content", "")
        file_path = claim.get("file_path", "")
        function_name = claim.get("function_name", "")

        score = 0.0
        matched_evidences = []
        reasons = []

        # 0. 파일 시스템 직접 확인 (최우선 - Git 상태와 무관)
        if self.project_path:
            fs_score = self._check_filesystem_directly(content, file_path, function_name)
            if fs_score > 0:
                score = fs_score
                reasons.append(f"Filesystem verified: {fs_score:.2f}")

        # 1. Evidence 기반 파일 존재 확인 (보조)
        if file_path and score < 1.0:
            for ev in evidences:
                if isinstance(ev, FileEvidence) and ev.file_path == file_path:
                    if ev.exists:
                        score = max(score, 1.0)
                        matched_evidences.append(ev)
                        reasons.append(f"File exists: {file_path}")
                    break

        # 2. 파일 경로가 없으면 content에서 추출해서 Evidence 확인
        if not file_path and score < 0.8:
            extracted_files = self._extract_file_paths(content)
            for f in extracted_files:
                for ev in evidences:
                    if isinstance(ev, FileEvidence) and f in ev.file_path:
                        if ev.exists:
                            score = max(score, 0.8)
                            matched_evidences.append(ev)
                            reasons.append(f"Found file: {ev.file_path}")

        # 3. 함수/클래스 존재 확인
        if function_name and score < 0.9:
            for ev in evidences:
                if isinstance(ev, FileEvidence) and ev.content:
                    if function_name in ev.content:
                        score = max(score, 0.9)
                        if ev not in matched_evidences:
                            matched_evidences.append(ev)
                        reasons.append(f"Function '{function_name}' found in {ev.file_path}")

        return MatchResult(
            matched=score >= 0.5,
            score=score,
            claim_type="existence_claim",
            evidence_used=matched_evidences,
            reasoning=" | ".join(reasons) if reasons else "Existence not verified"
        )

    def _match_modification(self, claim: Dict, evidences: List[Evidence]) -> MatchResult:
        """
        수정 주장 매칭

        "updated function foo" 또는 "changed file bar.py" 같은 주장 검증
        """
        content = claim.get("content", "")
        file_path = claim.get("file_path", "")

        score = 0.0
        matched_evidences = []
        reasons = []

        # Git diff에서 변경 확인
        for ev in evidences:
            if isinstance(ev, GitEvidence):
                # 파일이 변경 목록에 있는지 확인
                if file_path:
                    if file_path in ev.files_changed or file_path in ev.staged_files:
                        score = max(score, 0.8)
                        matched_evidences.append(ev)
                        reasons.append(f"File {file_path} is in changed files")

                        # Diff 내용 확인
                        if file_path in ev.diff_content:
                            score = 1.0
                            reasons.append(f"Diff content available for {file_path}")

                # 파일 경로 없으면 content에서 추출
                else:
                    extracted_files = self._extract_file_paths(content)
                    for f in extracted_files:
                        if f in ev.files_changed or f in ev.staged_files:
                            score = max(score, 0.7)
                            if ev not in matched_evidences:
                                matched_evidences.append(ev)
                            reasons.append(f"Found modified file: {f}")

        return MatchResult(
            matched=score >= 0.5,
            score=score,
            claim_type="modification_claim",
            evidence_used=matched_evidences,
            reasoning=" | ".join(reasons) if reasons else "Modification not verified"
        )

    def _match_performance(self, claim: Dict, evidences: List[Evidence]) -> MatchResult:
        """
        성능 주장 매칭

        "improved performance by 50%" 같은 주장 검증
        주의: 이전에는 스킵되었던 부분 - 이제 제대로 검증
        """
        content = claim.get("content", "")

        score = 0.0
        matched_evidences = []
        reasons = []

        # 숫자 추출 (성능 수치)
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*(%|ms|s|seconds?|x|times?)', content, re.IGNORECASE)

        # Execution Evidence에서 성능 관련 출력 확인
        for ev in evidences:
            if isinstance(ev, ExecutionEvidence):
                output_lower = ev.output.lower()

                # 벤치마크/테스트 결과인지 확인
                if any(kw in output_lower for kw in ["benchmark", "test", "time", "ms", "seconds"]):
                    score = max(score, 0.6)
                    matched_evidences.append(ev)
                    reasons.append("Found execution evidence with timing data")

                # 숫자 매칭 시도
                for num, unit in numbers:
                    if num in ev.output:
                        score = max(score, 0.8)
                        reasons.append(f"Number {num}{unit} found in execution output")

                # 성공적인 종료
                if ev.exit_code == 0:
                    score = max(score, 0.5)
                    reasons.append("Command executed successfully")

        # Execution Evidence가 없으면 Warning
        if not any(isinstance(ev, ExecutionEvidence) for ev in evidences):
            reasons.append("WARNING: No execution evidence for performance claim")
            # 최소 점수 부여 (검증 불가능이지 거짓은 아님)
            score = max(score, 0.3)

        return MatchResult(
            matched=score >= 0.5,
            score=score,
            claim_type="performance_claim",
            evidence_used=matched_evidences,
            reasoning=" | ".join(reasons) if reasons else "Performance claim requires execution evidence"
        )

    def _match_bug_fix(self, claim: Dict, evidences: List[Evidence]) -> MatchResult:
        """
        버그 수정 주장 매칭

        "fixed bug in foo.py" 같은 주장 검증
        """
        content = claim.get("content", "")
        file_path = claim.get("file_path", "")

        score = 0.0
        matched_evidences = []
        reasons = []

        # 파일 변경 확인
        for ev in evidences:
            if isinstance(ev, GitEvidence):
                target_file = file_path or self._extract_file_paths(content)[0] if self._extract_file_paths(content) else ""

                if target_file and (target_file in ev.files_changed or target_file in ev.staged_files):
                    score = max(score, 0.6)
                    matched_evidences.append(ev)
                    reasons.append(f"File {target_file} was modified")

                    # Diff에서 수정 내용 확인
                    if target_file in ev.diff_content:
                        diff = ev.diff_content[target_file]
                        # 추가/삭제된 라인이 있는지 확인
                        additions = diff.count("\n+")
                        deletions = diff.count("\n-")
                        if additions > 0 or deletions > 0:
                            score = max(score, 0.8)
                            reasons.append(f"Diff shows +{additions}/-{deletions} lines")

        # 테스트 통과 확인
        for ev in evidences:
            if isinstance(ev, ExecutionEvidence):
                if ev.exit_code == 0 and "test" in ev.command.lower():
                    score = min(1.0, score + 0.2)
                    matched_evidences.append(ev)
                    reasons.append("Tests passed after fix")

        return MatchResult(
            matched=score >= 0.5,
            score=score,
            claim_type="bug_fix_claim",
            evidence_used=matched_evidences,
            reasoning=" | ".join(reasons) if reasons else "Bug fix not verified"
        )

    def _match_generic(self, claim: Dict, evidences: List[Evidence]) -> MatchResult:
        """
        일반적인 주장 매칭 (타입 미지정)
        """
        content = claim.get("content", "")

        score = 0.0
        matched_evidences = []
        reasons = []

        # 파일 경로 추출 및 매칭
        extracted_files = self._extract_file_paths(content)
        for f in extracted_files:
            for ev in evidences:
                if isinstance(ev, GitEvidence):
                    if f in ev.files_changed:
                        score = max(score, 0.6)
                        if ev not in matched_evidences:
                            matched_evidences.append(ev)
                        reasons.append(f"File {f} found in changes")
                elif isinstance(ev, FileEvidence):
                    if f in ev.file_path and ev.exists:
                        score = max(score, 0.5)
                        if ev not in matched_evidences:
                            matched_evidences.append(ev)
                        reasons.append(f"File {f} exists")

        # 키워드 매칭
        keywords = self._extract_keywords(content)
        for kw in keywords[:5]:  # 상위 5개 키워드만
            for ev in evidences:
                if isinstance(ev, GitEvidence):
                    for file_path, diff in ev.diff_content.items():
                        if kw.lower() in diff.lower():
                            score = max(score, 0.4)
                            if ev not in matched_evidences:
                                matched_evidences.append(ev)
                            reasons.append(f"Keyword '{kw}' found in diff")
                            break

        # 의미적 유사도
        semantic_score = self._semantic_match_with_evidences(content, evidences)
        score = max(score, semantic_score * 0.5)
        if semantic_score > 0.5:
            reasons.append(f"Semantic match: {semantic_score:.2f}")

        return MatchResult(
            matched=score >= 0.4,
            score=score,
            claim_type="generic",
            evidence_used=matched_evidences,
            reasoning=" | ".join(reasons) if reasons else "Generic matching"
        )

    def _check_file_in_evidence(self, file_ref: str, evidences: List[Evidence]) -> tuple:
        """파일이 Evidence에 있는지 확인"""
        extracted_files = self._extract_file_paths(file_ref)

        for f in extracted_files:
            # FileEvidence 확인
            for ev in evidences:
                if isinstance(ev, FileEvidence):
                    if f in ev.file_path or ev.file_path.endswith(f):
                        if ev.exists:
                            return 1.0, ev

            # GitEvidence 확인
            for ev in evidences:
                if isinstance(ev, GitEvidence):
                    if f in ev.files_changed or f in ev.staged_files:
                        return 0.8, ev

        return 0.0, None

    def _check_function_in_diffs(self, function_name: str, evidences: List[Evidence]) -> float:
        """함수명이 diff에 있는지 확인"""
        if not function_name:
            return 0.0

        for ev in evidences:
            if isinstance(ev, GitEvidence):
                for file_path, diff in ev.diff_content.items():
                    # 함수 정의 패턴 확인
                    patterns = [
                        rf'^\+.*def {function_name}\s*\(',  # Python 함수 추가
                        rf'^\+.*function {function_name}\s*\(',  # JS 함수 추가
                        rf'^\+.*{function_name}\s*=\s*\(',  # 화살표 함수 등
                        rf'^\+.*{function_name}\s*\([^)]*\)\s*\{{',  # 메서드
                    ]

                    for pattern in patterns:
                        if re.search(pattern, diff, re.MULTILINE):
                            return 1.0

                    # 함수명만 존재해도 부분 점수
                    if function_name in diff:
                        return 0.6

            # FileEvidence에서 함수 존재 확인
            if isinstance(ev, FileEvidence) and ev.content:
                if f"def {function_name}" in ev.content or f"function {function_name}" in ev.content:
                    return 0.8

        return 0.0

    def _semantic_match_with_evidences(self, claim_text: str, evidences: List[Evidence]) -> float:
        """임베딩 기반 의미적 유사도 계산"""
        if self.embedder is None:
            return 0.0

        try:
            # Evidence 텍스트 수집
            evidence_texts = []
            for ev in evidences:
                if isinstance(ev, GitEvidence):
                    for diff in ev.diff_content.values():
                        evidence_texts.append(diff[:1000])  # 최대 1000자
                elif isinstance(ev, FileEvidence) and ev.content:
                    evidence_texts.append(ev.content[:1000])
                elif isinstance(ev, ExecutionEvidence):
                    evidence_texts.append(ev.output[:500])

            if not evidence_texts:
                return 0.0

            # 임베딩 계산
            claim_embedding = self.embedder.encode(claim_text)
            evidence_embeddings = self.embedder.encode(evidence_texts)

            # 코사인 유사도 계산
            from numpy import dot
            from numpy.linalg import norm

            max_similarity = 0.0
            for ev_emb in evidence_embeddings:
                similarity = dot(claim_embedding, ev_emb) / (norm(claim_embedding) * norm(ev_emb))
                max_similarity = max(max_similarity, similarity)

            return float(max_similarity)

        except Exception as e:
            logger.debug(f"Semantic matching failed: {e}")
            return 0.0

    def _extract_file_paths(self, text: str) -> List[str]:
        """텍스트에서 파일 경로 추출 (한국어 조사 지원)"""
        # 지원하는 확장자 목록
        extensions = r'py|js|ts|jsx|tsx|java|go|rs|rb|php|c|cpp|h|hpp|md|json|yaml|yml'

        paths = []

        # 패턴 1: 일반 경로 (core/file.py, ./file.py, file.py 등)
        # 비캡처 그룹 사용하여 전체 매칭 반환
        pattern1 = rf'[\w./\-_]+\.(?:{extensions})(?=[^a-zA-Z0-9_]|$)'
        matches1 = re.findall(pattern1, text)
        paths.extend(matches1)

        # 패턴 2: 따옴표로 감싼 경로
        pattern2 = rf'"([^"]+\.(?:{extensions}))"'
        matches2 = re.findall(pattern2, text)
        paths.extend(matches2)

        # 패턴 3: 작은따옴표로 감싼 경로
        pattern3 = rf"'([^']+\.(?:{extensions}))'"
        matches3 = re.findall(pattern3, text)
        paths.extend(matches3)

        # 패턴 4: 백틱으로 감싼 경로
        pattern4 = rf'`([^`]+\.(?:{extensions}))`'
        matches4 = re.findall(pattern4, text)
        paths.extend(matches4)

        # 유효한 경로만 필터링 (최소한 확장자가 있어야 함)
        valid_paths = []
        for path in paths:
            if re.search(rf'\.(?:{extensions})$', path):
                valid_paths.append(path)

        return list(dict.fromkeys(valid_paths))  # 중복 제거

    def _extract_function_name(self, text: str) -> Optional[str]:
        """텍스트에서 함수명 추출"""
        patterns = [
            r'function\s+(\w+)',
            r'def\s+(\w+)',
            r'added\s+(\w+)\s+function',
            r'created\s+(\w+)\s+function',
            r'implemented\s+(\w+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 검색 키워드 추출"""
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', text)

        stop_words = {
            "the", "this", "that", "with", "from", "have", "has", "had",
            "was", "were", "are", "been", "will", "would", "could", "should",
            "function", "class", "method", "file", "code", "implement",
            "add", "added", "create", "created", "update", "updated",
        }

        keywords = [w for w in words if w.lower() not in stop_words]
        return list(dict.fromkeys(keywords))


# 편의 함수
def get_evidence_matcher(embedder=None) -> EvidenceMatcher:
    """EvidenceMatcher 인스턴스 생성"""
    return EvidenceMatcher(embedder)
