"""
코드 패턴 검증기

특정 코드 패턴(import문, 데코레이터, 함수 호출 등)의 존재를 검증합니다.
AI가 "로깅을 추가했습니다" 또는 "에러 핸들링을 구현했습니다" 등을 주장할 때
실제 코드 패턴을 독립적으로 검증.
"""
import ast
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from .base import BaseVerifier, Evidence, EvidenceType, VerificationResult

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """패턴 매칭 결과"""
    pattern_type: str  # "import", "decorator", "function_call", "exception_handler", "string_literal", "regex"
    matched_text: str
    file_path: str
    line_number: int
    context: str  # 주변 코드


class CodePatternVisitor(ast.NodeVisitor):
    """AST 순회하여 코드 패턴 수집"""

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.imports: List[Tuple[str, int]] = []  # (import_name, line_number)
        self.decorators: List[Tuple[str, int]] = []
        self.function_calls: List[Tuple[str, int]] = []
        self.exception_handlers: List[Tuple[str, int]] = []  # (exception_type, line_number)
        self.string_literals: List[Tuple[str, int]] = []

    def visit_Import(self, node: ast.Import):
        """import 문 방문"""
        for alias in node.names:
            self.imports.append((alias.name, node.lineno))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """from ... import 문 방문"""
        module = node.module or ""
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self.imports.append((full_name, node.lineno))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """함수 정의 - 데코레이터 수집"""
        for decorator in node.decorator_list:
            dec_name = self._get_decorator_name(decorator)
            self.decorators.append((dec_name, decorator.lineno))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """비동기 함수 정의 - 데코레이터 수집"""
        for decorator in node.decorator_list:
            dec_name = self._get_decorator_name(decorator)
            self.decorators.append((dec_name, decorator.lineno))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """클래스 정의 - 데코레이터 수집"""
        for decorator in node.decorator_list:
            dec_name = self._get_decorator_name(decorator)
            self.decorators.append((dec_name, decorator.lineno))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """함수 호출 방문"""
        call_name = self._get_call_name(node.func)
        if call_name:
            self.function_calls.append((call_name, node.lineno))
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """예외 핸들러 방문"""
        if node.type:
            exc_name = self._get_name(node.type)
            self.exception_handlers.append((exc_name, node.lineno))
        else:
            self.exception_handlers.append(("Exception", node.lineno))
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        """문자열 리터럴 방문"""
        if isinstance(node.value, str) and len(node.value) > 3:
            self.string_literals.append((node.value[:100], node.lineno))
        self.generic_visit(node)

    def _get_decorator_name(self, decorator) -> str:
        """데코레이터 이름 추출"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_call_name(decorator.func)
        return "unknown"

    def _get_call_name(self, node) -> Optional[str]:
        """함수 호출 이름 추출"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            obj_name = self._get_name(node.value)
            return f"{obj_name}.{node.attr}" if obj_name else node.attr
        return None

    def _get_name(self, node) -> str:
        """AST 노드에서 이름 추출"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "unknown"


class CodePatternVerifier(BaseVerifier):
    """
    코드 패턴 검증기

    특정 코드 패턴의 존재를 검증합니다:
    - Import 문
    - 데코레이터 사용
    - 함수 호출
    - 예외 처리
    - 특정 문자열/정규식 패턴
    """

    # 일반적인 패턴과 키워드 매핑
    PATTERN_KEYWORDS = {
        # 로깅 관련
        "logging": ["logging", "logger", "log", "getLogger"],
        "로깅": ["logging", "logger", "log", "getLogger"],
        # 에러 핸들링 관련
        "error handling": ["try", "except", "Exception", "Error"],
        "에러 핸들링": ["try", "except", "Exception", "Error"],
        "예외 처리": ["try", "except", "Exception", "Error"],
        # 타입 힌트 관련
        "type hint": ["typing", "Optional", "List", "Dict", "Any"],
        "타입 힌트": ["typing", "Optional", "List", "Dict", "Any"],
        # 테스트 관련
        "test": ["pytest", "unittest", "test_", "assert"],
        "테스트": ["pytest", "unittest", "test_", "assert"],
        # 비동기 관련
        "async": ["async", "await", "asyncio"],
        "비동기": ["async", "await", "asyncio"],
        # 데이터 클래스 관련
        "dataclass": ["dataclass", "@dataclass"],
    }

    def __init__(self):
        self._pattern_cache: Dict[str, Tuple[CodePatternVisitor, float]] = {}
        self._cache_ttl = 60.0

    @property
    def verifier_type(self) -> str:
        return "code_pattern"

    def verify(self, claim: Any, context: Dict[str, Any]) -> VerificationResult:
        """
        Claim에서 언급된 코드 패턴 검증

        Args:
            claim: Claim 객체
            context: {
                "project_path": str,
                "target_file": str (선택),
                "pattern": str (선택) - 검색할 패턴,
                "pattern_type": str (선택) - "import", "decorator", "function_call", "exception", "regex"
            }

        Returns:
            VerificationResult
        """
        project_path = context.get("project_path", ".")
        target_file = context.get("target_file")
        pattern = context.get("pattern")
        pattern_type = context.get("pattern_type")

        # Claim 텍스트 추출
        claim_text = getattr(claim, 'text', str(claim))

        # 패턴이 명시되지 않은 경우 Claim에서 추출
        if not pattern:
            pattern, pattern_type = self._extract_pattern_from_claim(claim_text)

        if not pattern:
            return self._create_result(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason="검증할 코드 패턴을 찾을 수 없음"
            )

        logger.info(f"[CodePatternVerifier] 검증할 패턴: {pattern} (type: {pattern_type})")

        # 대상 파일 결정
        if target_file:
            if not os.path.isabs(target_file):
                full_path = os.path.join(project_path, target_file)
            else:
                full_path = target_file

            if os.path.exists(full_path):
                files_to_check = [full_path]
            else:
                files_to_check = self._find_python_files(project_path)
        else:
            files_to_check = self._find_python_files(project_path)

        # 패턴 검색
        matches = []
        for file_path in files_to_check:
            file_matches = self._search_pattern_in_file(file_path, pattern, pattern_type, project_path)
            matches.extend(file_matches)

        if matches:
            # 증거 생성
            evidence_list = []
            for match in matches[:10]:  # 최대 10개
                evidence = self._create_evidence(
                    type=EvidenceType.CODE_PATTERN,
                    source=match.file_path,
                    content=f"{match.pattern_type}: {match.matched_text}",
                    confidence=0.95,
                    metadata={
                        "pattern_type": match.pattern_type,
                        "line_number": match.line_number,
                        "matched_text": match.matched_text[:100],
                        "context": match.context[:200],
                    }
                )
                evidence_list.append(evidence)

            return self._create_result(
                verified=True,
                confidence=0.95,
                evidence=evidence_list,
                reason=f"'{pattern}' 패턴 {len(matches)}개 발견됨"
            )
        else:
            return self._create_result(
                verified=False,
                confidence=0.1,
                evidence=[],
                reason=f"'{pattern}' 패턴을 찾을 수 없음"
            )

    def verify_import_exists(
        self,
        file_path: str,
        import_name: str
    ) -> VerificationResult:
        """
        특정 import 존재 확인 (편의 메서드)

        Args:
            file_path: 파일 경로
            import_name: import 이름 (예: "logging", "os.path")

        Returns:
            VerificationResult
        """
        matches = self._search_pattern_in_file(file_path, import_name, "import", os.path.dirname(file_path))

        if matches:
            match = matches[0]
            evidence = self._create_evidence(
                type=EvidenceType.CODE_PATTERN,
                source=file_path,
                content=f"import {match.matched_text}",
                confidence=0.99,
                metadata={
                    "line_number": match.line_number,
                    "import_name": import_name,
                }
            )
            return self._create_result(
                verified=True,
                confidence=0.99,
                evidence=[evidence],
                reason=f"import '{import_name}' 존재 확인됨 (line {match.line_number})"
            )

        return self._create_result(
            verified=False,
            confidence=0.0,
            evidence=[],
            reason=f"import '{import_name}' 찾을 수 없음"
        )

    def verify_decorator_exists(
        self,
        file_path: str,
        decorator_name: str
    ) -> VerificationResult:
        """
        특정 데코레이터 존재 확인 (편의 메서드)

        Args:
            file_path: 파일 경로
            decorator_name: 데코레이터 이름 (예: "dataclass", "property")

        Returns:
            VerificationResult
        """
        matches = self._search_pattern_in_file(file_path, decorator_name, "decorator", os.path.dirname(file_path))

        if matches:
            match = matches[0]
            evidence = self._create_evidence(
                type=EvidenceType.CODE_PATTERN,
                source=file_path,
                content=f"@{match.matched_text}",
                confidence=0.99,
                metadata={
                    "line_number": match.line_number,
                    "decorator_name": decorator_name,
                }
            )
            return self._create_result(
                verified=True,
                confidence=0.99,
                evidence=[evidence],
                reason=f"데코레이터 '@{decorator_name}' 존재 확인됨 (line {match.line_number})"
            )

        return self._create_result(
            verified=False,
            confidence=0.0,
            evidence=[],
            reason=f"데코레이터 '@{decorator_name}' 찾을 수 없음"
        )

    def verify_function_call_exists(
        self,
        file_path: str,
        function_name: str
    ) -> VerificationResult:
        """
        특정 함수 호출 존재 확인 (편의 메서드)

        Args:
            file_path: 파일 경로
            function_name: 함수 이름 (예: "print", "logger.info")

        Returns:
            VerificationResult
        """
        matches = self._search_pattern_in_file(file_path, function_name, "function_call", os.path.dirname(file_path))

        if matches:
            match = matches[0]
            evidence = self._create_evidence(
                type=EvidenceType.CODE_PATTERN,
                source=file_path,
                content=f"call {match.matched_text}",
                confidence=0.95,
                metadata={
                    "line_number": match.line_number,
                    "function_name": function_name,
                }
            )
            return self._create_result(
                verified=True,
                confidence=0.95,
                evidence=[evidence],
                reason=f"함수 호출 '{function_name}' 존재 확인됨 (line {match.line_number})"
            )

        return self._create_result(
            verified=False,
            confidence=0.0,
            evidence=[],
            reason=f"함수 호출 '{function_name}' 찾을 수 없음"
        )

    def verify_exception_handling(
        self,
        file_path: str,
        exception_type: Optional[str] = None
    ) -> VerificationResult:
        """
        예외 처리 존재 확인 (편의 메서드)

        Args:
            file_path: 파일 경로
            exception_type: 예외 타입 (선택, 예: "ValueError")

        Returns:
            VerificationResult
        """
        pattern = exception_type or "Exception"
        matches = self._search_pattern_in_file(file_path, pattern, "exception", os.path.dirname(file_path))

        if matches:
            evidence_list = []
            for match in matches[:5]:
                evidence = self._create_evidence(
                    type=EvidenceType.CODE_PATTERN,
                    source=file_path,
                    content=f"except {match.matched_text}",
                    confidence=0.95,
                    metadata={
                        "line_number": match.line_number,
                        "exception_type": match.matched_text,
                    }
                )
                evidence_list.append(evidence)

            return self._create_result(
                verified=True,
                confidence=0.95,
                evidence=evidence_list,
                reason=f"예외 처리 {len(matches)}개 확인됨"
            )

        return self._create_result(
            verified=False,
            confidence=0.0,
            evidence=[],
            reason="예외 처리를 찾을 수 없음"
        )

    def verify_regex_pattern(
        self,
        file_path: str,
        regex_pattern: str
    ) -> VerificationResult:
        """
        정규식 패턴 검증 (편의 메서드)

        Args:
            file_path: 파일 경로
            regex_pattern: 검색할 정규식 패턴

        Returns:
            VerificationResult
        """
        matches = self._search_pattern_in_file(file_path, regex_pattern, "regex", os.path.dirname(file_path))

        if matches:
            match = matches[0]
            evidence = self._create_evidence(
                type=EvidenceType.CODE_PATTERN,
                source=file_path,
                content=f"regex match: {match.matched_text}",
                confidence=0.9,
                metadata={
                    "line_number": match.line_number,
                    "pattern": regex_pattern,
                    "matched_text": match.matched_text[:100],
                }
            )
            return self._create_result(
                verified=True,
                confidence=0.9,
                evidence=[evidence],
                reason=f"정규식 패턴 매칭됨 (line {match.line_number})"
            )

        return self._create_result(
            verified=False,
            confidence=0.0,
            evidence=[],
            reason=f"정규식 패턴 '{regex_pattern}' 찾을 수 없음"
        )

    def _search_pattern_in_file(
        self,
        file_path: str,
        pattern: str,
        pattern_type: Optional[str],
        project_path: str
    ) -> List[PatternMatch]:
        """파일에서 패턴 검색"""
        matches = []

        if not os.path.exists(file_path):
            return matches

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                source_lines = source.split('\n')

            # 상대 경로 계산
            try:
                rel_path = os.path.relpath(file_path, project_path)
            except ValueError:
                rel_path = file_path

            # 정규식 패턴인 경우 직접 검색
            if pattern_type == "regex":
                try:
                    regex = re.compile(pattern, re.MULTILINE)
                    for i, line in enumerate(source_lines, 1):
                        match = regex.search(line)
                        if match:
                            matches.append(PatternMatch(
                                pattern_type="regex",
                                matched_text=match.group(),
                                file_path=rel_path,
                                line_number=i,
                                context=self._get_context(source_lines, i)
                            ))
                except re.error:
                    logger.warning(f"[CodePatternVerifier] 잘못된 정규식: {pattern}")
                return matches

            # AST 기반 검색
            try:
                tree = ast.parse(source)
                visitor = CodePatternVisitor(source_lines)
                visitor.visit(tree)
            except SyntaxError:
                # 문법 오류 시 텍스트 검색으로 폴백
                return self._text_search(source_lines, pattern, pattern_type, rel_path)

            # 패턴 타입별 검색
            pattern_lower = pattern.lower()

            if pattern_type in (None, "import"):
                for import_name, line_no in visitor.imports:
                    if pattern_lower in import_name.lower():
                        matches.append(PatternMatch(
                            pattern_type="import",
                            matched_text=import_name,
                            file_path=rel_path,
                            line_number=line_no,
                            context=self._get_context(source_lines, line_no)
                        ))

            if pattern_type in (None, "decorator"):
                for dec_name, line_no in visitor.decorators:
                    if pattern_lower in dec_name.lower():
                        matches.append(PatternMatch(
                            pattern_type="decorator",
                            matched_text=dec_name,
                            file_path=rel_path,
                            line_number=line_no,
                            context=self._get_context(source_lines, line_no)
                        ))

            if pattern_type in (None, "function_call"):
                for call_name, line_no in visitor.function_calls:
                    if pattern_lower in call_name.lower():
                        matches.append(PatternMatch(
                            pattern_type="function_call",
                            matched_text=call_name,
                            file_path=rel_path,
                            line_number=line_no,
                            context=self._get_context(source_lines, line_no)
                        ))

            if pattern_type in (None, "exception"):
                for exc_name, line_no in visitor.exception_handlers:
                    if pattern_lower in exc_name.lower():
                        matches.append(PatternMatch(
                            pattern_type="exception_handler",
                            matched_text=exc_name,
                            file_path=rel_path,
                            line_number=line_no,
                            context=self._get_context(source_lines, line_no)
                        ))

            # 텍스트 검색 (AST로 못 찾은 경우)
            if not matches and pattern_type is None:
                matches.extend(self._text_search(source_lines, pattern, None, rel_path))

        except Exception as e:
            logger.error(f"[CodePatternVerifier] 파일 검색 오류 {file_path}: {e}")

        return matches

    def _text_search(
        self,
        source_lines: List[str],
        pattern: str,
        pattern_type: Optional[str],
        rel_path: str
    ) -> List[PatternMatch]:
        """텍스트 기반 패턴 검색"""
        matches = []
        pattern_lower = pattern.lower()

        for i, line in enumerate(source_lines, 1):
            if pattern_lower in line.lower():
                matches.append(PatternMatch(
                    pattern_type=pattern_type or "text",
                    matched_text=line.strip()[:100],
                    file_path=rel_path,
                    line_number=i,
                    context=self._get_context(source_lines, i)
                ))

        return matches

    def _get_context(self, lines: List[str], line_no: int, context_size: int = 2) -> str:
        """해당 라인 주변 컨텍스트 반환"""
        start = max(0, line_no - context_size - 1)
        end = min(len(lines), line_no + context_size)
        return '\n'.join(lines[start:end])

    def _extract_pattern_from_claim(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Claim 텍스트에서 패턴 추출

        Returns:
            (pattern, pattern_type)
        """
        text_lower = text.lower()

        # 키워드 매핑 확인
        for keyword, patterns in self.PATTERN_KEYWORDS.items():
            if keyword in text_lower:
                return patterns[0], None

        # 특정 패턴 추출
        # "logging 추가" -> "logging"
        match = re.search(r'[`"\']?(\w+(?:\.\w+)?)[`"\']?\s*(?:을|를|추가|구현|사용)', text)
        if match:
            return match.group(1), None

        # "import X" -> X
        match = re.search(r'import\s+(\w+(?:\.\w+)*)', text)
        if match:
            return match.group(1), "import"

        # "@decorator" -> decorator
        match = re.search(r'@(\w+)', text)
        if match:
            return match.group(1), "decorator"

        return None, None

    def _find_python_files(
        self,
        project_path: str,
        max_files: int = 100
    ) -> List[str]:
        """프로젝트에서 Python 파일 찾기"""
        python_files = []

        exclude_dirs = {
            '__pycache__', '.git', 'node_modules', 'venv', '.venv', 'env',
            '.env', '.tox', '.pytest_cache', '.mypy_cache', 'dist', 'build',
        }

        try:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

                for file in files:
                    if file.endswith('.py') and not file.startswith('.'):
                        python_files.append(os.path.join(root, file))
                        if len(python_files) >= max_files:
                            return python_files
        except PermissionError:
            pass

        return python_files

    def clear_cache(self):
        """캐시 초기화"""
        self._pattern_cache.clear()
