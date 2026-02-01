"""
코드 요소 존재 검증기

AST를 사용하여 함수, 클래스, 메서드 등의 존재를 확인합니다.
AI가 "메서드를 추가했습니다"라고 주장할 때 실제로 해당 요소가 존재하는지 독립적으로 검증.
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
class CodeElement:
    """코드 요소 정보"""
    name: str
    element_type: str  # "class", "function", "method", "async_function", "async_method", "variable"
    parent: Optional[str]  # 부모 클래스/함수 이름
    line_number: int
    signature: Optional[str]  # 함수 시그니처
    decorators: List[str]
    docstring: Optional[str] = None
    return_annotation: Optional[str] = None


class CodeElementVisitor(ast.NodeVisitor):
    """AST 순회하여 코드 요소 수집"""

    def __init__(self):
        self.elements: List[CodeElement] = []
        self._current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        """클래스 정의 방문"""
        # 독스트링 추출
        docstring = ast.get_docstring(node)

        self.elements.append(CodeElement(
            name=node.name,
            element_type="class",
            parent=None,
            line_number=node.lineno,
            signature=None,
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            docstring=docstring[:200] if docstring else None
        ))

        # 클래스 내부 순회
        old_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """함수/메서드 정의 방문"""
        element_type = "method" if self._current_class else "function"

        # 시그니처 추출
        args = self._extract_args(node.args)
        signature = f"({', '.join(args)})"

        # 반환 타입 추출
        return_annotation = None
        if node.returns:
            return_annotation = self._get_annotation_str(node.returns)

        # 독스트링 추출
        docstring = ast.get_docstring(node)

        self.elements.append(CodeElement(
            name=node.name,
            element_type=element_type,
            parent=self._current_class,
            line_number=node.lineno,
            signature=signature,
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            docstring=docstring[:200] if docstring else None,
            return_annotation=return_annotation
        ))

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """비동기 함수 정의 방문"""
        element_type = "async_method" if self._current_class else "async_function"

        # 시그니처 추출
        args = self._extract_args(node.args)
        signature = f"({', '.join(args)})"

        # 반환 타입 추출
        return_annotation = None
        if node.returns:
            return_annotation = self._get_annotation_str(node.returns)

        # 독스트링 추출
        docstring = ast.get_docstring(node)

        self.elements.append(CodeElement(
            name=node.name,
            element_type=element_type,
            parent=self._current_class,
            line_number=node.lineno,
            signature=signature,
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            docstring=docstring[:200] if docstring else None,
            return_annotation=return_annotation
        ))

        self.generic_visit(node)

    def _extract_args(self, args: ast.arguments) -> List[str]:
        """함수 인자 추출"""
        arg_list = []

        # positional arguments
        for arg in args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_annotation_str(arg.annotation)}"
            arg_list.append(arg_str)

        # *args
        if args.vararg:
            arg_str = f"*{args.vararg.arg}"
            if args.vararg.annotation:
                arg_str += f": {self._get_annotation_str(args.vararg.annotation)}"
            arg_list.append(arg_str)

        # **kwargs
        if args.kwarg:
            arg_str = f"**{args.kwarg.arg}"
            if args.kwarg.annotation:
                arg_str += f": {self._get_annotation_str(args.kwarg.annotation)}"
            arg_list.append(arg_str)

        return arg_list

    def _get_annotation_str(self, annotation) -> str:
        """타입 어노테이션을 문자열로 변환"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                return f"{annotation.value.id}[...]"
            return "complex_type"
        elif isinstance(annotation, ast.Attribute):
            return annotation.attr
        return "unknown"

    def _get_decorator_name(self, decorator) -> str:
        """데코레이터 이름 추출"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return "unknown"


class CodeElementVerifier(BaseVerifier):
    """
    코드 요소 존재 검증기

    AST를 사용하여 파일 내 함수, 클래스, 메서드의 존재를 검증합니다.
    """

    # 지원하는 언어 확장자
    SUPPORTED_EXTENSIONS = {'.py'}

    def __init__(self):
        self._element_cache: Dict[str, Tuple[List[CodeElement], float]] = {}
        self._cache_ttl = 60.0  # 캐시 TTL (초)

    @property
    def verifier_type(self) -> str:
        return "code_element"

    def verify(self, claim: Any, context: Dict[str, Any]) -> VerificationResult:
        """
        Claim에서 언급된 코드 요소 존재 검증

        Args:
            claim: Claim 객체 (claim.text에서 요소 정보 추출)
            context: {
                "project_path": str,
                "target_file": str (선택),
                "element_name": str (선택),
                "element_type": str (선택),
                "parent_class": str (선택)
            }

        Returns:
            VerificationResult
        """
        project_path = context.get("project_path", ".")
        target_file = context.get("target_file")
        element_name = context.get("element_name")
        element_type = context.get("element_type")
        parent_class = context.get("parent_class")

        # Claim 텍스트 추출
        claim_text = getattr(claim, 'text', str(claim))

        # Claim 텍스트에서 정보 추출 (명시적으로 제공되지 않은 경우)
        if not element_name:
            element_name, extracted_file, extracted_parent = self._extract_element_info(claim_text)
            if not target_file:
                target_file = extracted_file
            if not parent_class:
                parent_class = extracted_parent

        if not element_name:
            logger.warning(f"[CodeElementVerifier] Claim에서 코드 요소를 찾을 수 없음: {claim_text[:100]}")
            return self._create_result(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason="검증할 코드 요소를 찾을 수 없음"
            )

        logger.info(f"[CodeElementVerifier] 검증할 요소: {element_name} (parent: {parent_class}, file: {target_file})")

        # 대상 파일 결정
        if target_file:
            # 상대 경로 처리
            if not os.path.isabs(target_file):
                full_path = os.path.join(project_path, target_file)
            else:
                full_path = target_file

            if os.path.exists(full_path):
                files_to_check = [full_path]
            else:
                # 파일을 찾을 수 없으면 프로젝트에서 검색
                logger.warning(f"[CodeElementVerifier] 지정된 파일 없음, 프로젝트 검색: {target_file}")
                files_to_check = self._find_python_files(project_path)
        else:
            # 프로젝트 전체에서 검색
            files_to_check = self._find_python_files(project_path)

        # 요소 검색
        for file_path in files_to_check:
            elements = self._parse_file(file_path)

            for element in elements:
                if element.name == element_name:
                    # 부모 클래스 확인 (지정된 경우)
                    if parent_class and element.parent != parent_class:
                        continue

                    # 요소 타입 확인 (지정된 경우)
                    if element_type and not element.element_type.startswith(element_type):
                        continue

                    # 상대 경로 계산
                    try:
                        rel_path = os.path.relpath(file_path, project_path)
                    except ValueError:
                        rel_path = file_path

                    evidence = self._create_evidence(
                        type=EvidenceType.AST_ELEMENT,
                        source=rel_path,
                        content=f"{element.element_type} {element.name}{element.signature or ''}",
                        confidence=0.99,
                        metadata={
                            "element_type": element.element_type,
                            "line_number": element.line_number,
                            "parent": element.parent,
                            "decorators": element.decorators,
                            "signature": element.signature,
                            "return_annotation": element.return_annotation,
                            "has_docstring": element.docstring is not None,
                        }
                    )

                    logger.info(f"[CodeElementVerifier] 요소 발견: {element.name} in {rel_path}:{element.line_number}")

                    return self._create_result(
                        verified=True,
                        confidence=0.99,
                        evidence=[evidence],
                        reason=f"{element.element_type} '{element_name}' 발견됨 ({rel_path}:{element.line_number})"
                    )

        logger.warning(f"[CodeElementVerifier] 요소를 찾을 수 없음: {element_name}")
        return self._create_result(
            verified=False,
            confidence=0.0,
            evidence=[],
            reason=f"'{element_name}' 요소를 찾을 수 없음"
        )

    def verify_method_exists(
        self,
        file_path: str,
        method_name: str,
        class_name: Optional[str] = None
    ) -> VerificationResult:
        """
        특정 메서드 존재 확인 (편의 메서드)

        Args:
            file_path: 파일 경로
            method_name: 메서드 이름
            class_name: 클래스 이름 (선택)

        Returns:
            VerificationResult
        """
        if not os.path.exists(file_path):
            return self._create_result(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason=f"파일을 찾을 수 없음: {file_path}"
            )

        elements = self._parse_file(file_path)

        for element in elements:
            if element.name == method_name:
                if element.element_type in ("method", "async_method", "function", "async_function"):
                    if class_name and element.parent != class_name:
                        continue

                    evidence = self._create_evidence(
                        type=EvidenceType.AST_ELEMENT,
                        source=file_path,
                        content=f"Method {method_name} in class {element.parent or 'module'}",
                        confidence=0.99,
                        metadata={
                            "element_type": element.element_type,
                            "line_number": element.line_number,
                            "signature": element.signature,
                            "parent": element.parent,
                        }
                    )

                    return self._create_result(
                        verified=True,
                        confidence=0.99,
                        evidence=[evidence],
                        reason=f"메서드 '{method_name}' 존재 확인됨 (line {element.line_number})"
                    )

        return self._create_result(
            verified=False,
            confidence=0.0,
            evidence=[],
            reason=f"메서드 '{method_name}' 찾을 수 없음" + (f" (class: {class_name})" if class_name else "")
        )

    def verify_class_exists(
        self,
        file_path: str,
        class_name: str
    ) -> VerificationResult:
        """
        클래스 존재 확인 (편의 메서드)

        Args:
            file_path: 파일 경로
            class_name: 클래스 이름

        Returns:
            VerificationResult
        """
        if not os.path.exists(file_path):
            return self._create_result(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason=f"파일을 찾을 수 없음: {file_path}"
            )

        elements = self._parse_file(file_path)

        for element in elements:
            if element.name == class_name and element.element_type == "class":
                evidence = self._create_evidence(
                    type=EvidenceType.AST_ELEMENT,
                    source=file_path,
                    content=f"Class {class_name}",
                    confidence=0.99,
                    metadata={
                        "line_number": element.line_number,
                        "decorators": element.decorators,
                        "has_docstring": element.docstring is not None,
                    }
                )

                return self._create_result(
                    verified=True,
                    confidence=0.99,
                    evidence=[evidence],
                    reason=f"클래스 '{class_name}' 존재 확인됨 (line {element.line_number})"
                )

        return self._create_result(
            verified=False,
            confidence=0.0,
            evidence=[],
            reason=f"클래스 '{class_name}' 찾을 수 없음"
        )

    def verify_function_exists(
        self,
        file_path: str,
        function_name: str
    ) -> VerificationResult:
        """
        함수 존재 확인 (편의 메서드)

        Args:
            file_path: 파일 경로
            function_name: 함수 이름

        Returns:
            VerificationResult
        """
        if not os.path.exists(file_path):
            return self._create_result(
                verified=False,
                confidence=0.0,
                evidence=[],
                reason=f"파일을 찾을 수 없음: {file_path}"
            )

        elements = self._parse_file(file_path)

        for element in elements:
            if element.name == function_name:
                if element.element_type in ("function", "async_function"):
                    evidence = self._create_evidence(
                        type=EvidenceType.AST_ELEMENT,
                        source=file_path,
                        content=f"Function {function_name}{element.signature or ''}",
                        confidence=0.99,
                        metadata={
                            "element_type": element.element_type,
                            "line_number": element.line_number,
                            "signature": element.signature,
                            "return_annotation": element.return_annotation,
                        }
                    )

                    return self._create_result(
                        verified=True,
                        confidence=0.99,
                        evidence=[evidence],
                        reason=f"함수 '{function_name}' 존재 확인됨 (line {element.line_number})"
                    )

        return self._create_result(
            verified=False,
            confidence=0.0,
            evidence=[],
            reason=f"함수 '{function_name}' 찾을 수 없음"
        )

    def get_all_elements(self, file_path: str) -> List[CodeElement]:
        """
        파일의 모든 코드 요소 반환

        Args:
            file_path: 파일 경로

        Returns:
            CodeElement 목록
        """
        return self._parse_file(file_path)

    def _parse_file(self, file_path: str) -> List[CodeElement]:
        """
        파일을 AST로 파싱하여 코드 요소 추출

        캐싱을 통해 성능 최적화
        """
        import time

        # 캐시 확인
        if file_path in self._element_cache:
            cached_elements, cached_time = self._element_cache[file_path]
            if time.time() - cached_time < self._cache_ttl:
                return cached_elements

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            visitor = CodeElementVisitor()
            visitor.visit(tree)

            # 캐시 저장
            self._element_cache[file_path] = (visitor.elements, time.time())
            return visitor.elements

        except SyntaxError as e:
            logger.warning(f"[CodeElementVerifier] Syntax error in {file_path}: {e}")
            return []
        except FileNotFoundError:
            logger.warning(f"[CodeElementVerifier] File not found: {file_path}")
            return []
        except UnicodeDecodeError as e:
            logger.warning(f"[CodeElementVerifier] Encoding error in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"[CodeElementVerifier] Error parsing {file_path}: {e}")
            return []

    def _extract_element_info(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        텍스트에서 코드 요소 정보 추출

        패턴:
        - "calculate_score 메서드"
        - "GroundingScorer 클래스"
        - "GroundingScorer.calculate_score"
        - "grounding_scorer.py의 calculate_score"

        Returns:
            (element_name, file_path, parent_class)
        """
        # 패턴 1: file.py의 element
        match = re.search(r'(\S+\.py)(?:의|에서|에)\s+(\w+)', text)
        if match:
            return match.group(2), match.group(1), None

        # 패턴 2: ClassName.method_name
        match = re.search(r'(\w+)\.(\w+)', text)
        if match:
            # 파일 확장자가 있으면 건너뛰기
            if '.' in match.group(1) and not match.group(1)[0].isupper():
                pass
            else:
                return match.group(2), None, match.group(1)

        # 패턴 3: "method_name 메서드/함수"
        match = re.search(r'[`"\']?(\w+)[`"\']?\s*(?:메서드|함수|method|function)', text, re.IGNORECASE)
        if match:
            return match.group(1), None, None

        # 패턴 4: "ClassName 클래스"
        match = re.search(r'[`"\']?(\w+)[`"\']?\s*(?:클래스|class)', text, re.IGNORECASE)
        if match:
            return match.group(1), None, None

        # 패턴 5: 백틱으로 감싼 코드 요소
        match = re.search(r'`(\w+)`', text)
        if match:
            return match.group(1), None, None

        return None, None, None

    def _find_python_files(
        self,
        project_path: str,
        max_files: int = 200
    ) -> List[str]:
        """
        프로젝트에서 Python 파일 찾기

        Args:
            project_path: 프로젝트 경로
            max_files: 최대 파일 수

        Returns:
            Python 파일 경로 목록
        """
        python_files = []

        # 제외 디렉토리
        exclude_dirs = {
            '__pycache__', '.git', 'node_modules', 'venv', '.venv', 'env',
            '.env', '.tox', '.pytest_cache', '.mypy_cache', 'dist', 'build',
            'egg-info', '.eggs', 'site-packages'
        }

        try:
            for root, dirs, files in os.walk(project_path):
                # 제외 디렉토리 필터링
                dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

                for file in files:
                    if file.endswith('.py') and not file.startswith('.'):
                        python_files.append(os.path.join(root, file))
                        if len(python_files) >= max_files:
                            logger.info(f"[CodeElementVerifier] 최대 파일 수 도달: {max_files}")
                            return python_files
        except PermissionError:
            logger.warning(f"[CodeElementVerifier] 권한 없는 디렉토리 무시")

        return python_files

    def clear_cache(self):
        """캐시 초기화"""
        self._element_cache.clear()
        logger.info("[CodeElementVerifier] 캐시 초기화됨")
