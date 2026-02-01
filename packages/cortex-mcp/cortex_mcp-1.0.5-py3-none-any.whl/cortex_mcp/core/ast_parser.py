"""
AST Parser Module - Initial Context Scan System

Python, JavaScript, TypeScript 파일의 AST를 파싱하여 구조 정보를 추출합니다.

설계 원칙:
- P2: Structure over Semantics (구조만 추출, 구현 내용 무시)
- P3: Zero-Token by Default (로컬 분석만, LLM 호출 없음)

추출 대상:
- imports / exports
- class / function 이름
- interface / type (TS)
- 함수 body는 무시
"""

import ast
import hashlib
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """AST 파싱 결과"""

    language: str
    imports: List[Dict[str, Any]] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    types: List[str] = field(default_factory=list)
    has_default_export: bool = False
    parse_error: bool = False
    error_message: Optional[str] = None
    ast_hash: Optional[str] = None
    line_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "imports": self.imports,
            "exports": self.exports,
            "classes": self.classes,
            "functions": self.functions,
            "interfaces": self.interfaces,
            "types": self.types,
            "has_default_export": self.has_default_export,
            "parse_error": self.parse_error,
            "error_message": self.error_message,
            "ast_hash": self.ast_hash,
            "line_count": self.line_count,
        }


class BaseParser(ABC):
    """파서 기본 클래스"""

    @abstractmethod
    def parse(self, content: str, file_path: str) -> ParseResult:
        """파일 내용을 파싱하여 구조 정보 추출"""
        pass

    @staticmethod
    def compute_ast_hash(content: str) -> str:
        """AST 관련 해시 계산 (구조적 변경 감지용)"""
        # 주석과 공백 제거 후 해시
        cleaned = re.sub(r"#.*$", "", content, flags=re.MULTILINE)
        cleaned = re.sub(r"//.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return hashlib.sha256(cleaned.encode()).hexdigest()[:16]


class PythonParser(BaseParser):
    """Python AST 파서"""

    def parse(self, content: str, file_path: str) -> ParseResult:
        result = ParseResult(language="python")
        result.line_count = content.count("\n") + 1

        try:
            tree = ast.parse(content)
            result.ast_hash = self.compute_ast_hash(content)

            for node in ast.walk(tree):
                # Import 추출
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result.imports.append(
                            {
                                "module": alias.name,
                                "name": alias.asname or alias.name,
                                "type": "import",
                            }
                        )

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        result.imports.append(
                            {
                                "module": module,
                                "name": alias.name,
                                "alias": alias.asname,
                                "type": "from_import",
                            }
                        )

                # 클래스 정의 (최상위만)
                elif isinstance(node, ast.ClassDef):
                    if self._is_top_level(node, tree):
                        result.classes.append(node.name)
                        # 클래스는 자동으로 export됨 (Python)
                        if not node.name.startswith("_"):
                            result.exports.append(node.name)

                # 함수 정의 (최상위만)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    if self._is_top_level(node, tree):
                        result.functions.append(node.name)
                        # private이 아닌 함수는 export
                        if not node.name.startswith("_"):
                            result.exports.append(node.name)

            # __all__ 확인
            all_exports = self._extract_all_exports(tree)
            if all_exports:
                result.exports = all_exports

        except SyntaxError as e:
            result.parse_error = True
            result.error_message = f"SyntaxError: {str(e)}"
            logger.warning(f"Python parse error in {file_path}: {e}")
        except Exception as e:
            result.parse_error = True
            result.error_message = str(e)
            logger.warning(f"Parse error in {file_path}: {e}")

        return result

    def _is_top_level(self, node: ast.AST, tree: ast.Module) -> bool:
        """노드가 최상위 레벨인지 확인"""
        return node in tree.body

    def _extract_all_exports(self, tree: ast.Module) -> Optional[List[str]]:
        """__all__ 변수에서 export 목록 추출"""
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, ast.List):
                            exports = []
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    exports.append(elt.value)
                                elif isinstance(elt, ast.Str):  # Python 3.7 이하 호환
                                    exports.append(elt.s)
                            return exports
        return None


class JavaScriptTypeScriptParser(BaseParser):
    """JavaScript/TypeScript 정규식 기반 파서

    외부 의존성 없이 정규식으로 구조 추출
    정확도는 낮지만 Zero-Token 원칙 준수
    """

    # Import 패턴
    IMPORT_PATTERNS = [
        # import X from 'module'
        re.compile(r"""import\s+(\w+)\s+from\s+['"]([^'"]+)['"]"""),
        # import { X, Y } from 'module'
        re.compile(r"""import\s*\{([^}]+)\}\s*from\s*['"]([^'"]+)['"]"""),
        # import * as X from 'module'
        re.compile(r"""import\s*\*\s*as\s+(\w+)\s+from\s*['"]([^'"]+)['"]"""),
        # import 'module' (side effect)
        re.compile(r"""import\s+['"]([^'"]+)['"]"""),
        # const X = require('module')
        re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
        # const { X, Y } = require('module')
        re.compile(
            r"""(?:const|let|var)\s*\{([^}]+)\}\s*=\s*require\s*\(\s*['"]([^'"]+)['"]\s*\)"""
        ),
    ]

    # Export 패턴
    EXPORT_PATTERNS = [
        # export default X
        re.compile(r"""export\s+default\s+(?:class|function|const|let|var)?\s*(\w+)?"""),
        # export { X, Y }
        re.compile(r"""export\s*\{([^}]+)\}"""),
        # export const/let/var X
        re.compile(r"""export\s+(?:const|let|var)\s+(\w+)"""),
        # export function X
        re.compile(r"""export\s+(?:async\s+)?function\s+(\w+)"""),
        # export class X
        re.compile(r"""export\s+class\s+(\w+)"""),
        # export interface X (TS)
        re.compile(r"""export\s+interface\s+(\w+)"""),
        # export type X (TS)
        re.compile(r"""export\s+type\s+(\w+)"""),
        # module.exports = X
        re.compile(r"""module\.exports\s*=\s*(\w+)"""),
    ]

    # Class 패턴
    CLASS_PATTERN = re.compile(r"""(?:export\s+)?class\s+(\w+)""")

    # Function 패턴
    FUNCTION_PATTERNS = [
        re.compile(r"""(?:export\s+)?(?:async\s+)?function\s+(\w+)"""),
        re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>"""),
        re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function"""),
    ]

    # TypeScript Interface 패턴
    INTERFACE_PATTERN = re.compile(r"""(?:export\s+)?interface\s+(\w+)""")

    # TypeScript Type 패턴
    TYPE_PATTERN = re.compile(r"""(?:export\s+)?type\s+(\w+)\s*=""")

    def parse(self, content: str, file_path: str) -> ParseResult:
        is_ts = file_path.endswith((".ts", ".tsx"))
        result = ParseResult(language="typescript" if is_ts else "javascript")
        result.line_count = content.count("\n") + 1

        try:
            result.ast_hash = self.compute_ast_hash(content)

            # 문자열/템플릿 리터럴 내용 제거 (오탐 방지)
            cleaned = self._remove_strings_and_comments(content)

            # Imports 추출
            result.imports = self._extract_imports(cleaned)

            # Exports 추출
            exports, has_default = self._extract_exports(cleaned)
            result.exports = exports
            result.has_default_export = has_default

            # Classes 추출
            result.classes = self._extract_classes(cleaned)

            # Functions 추출
            result.functions = self._extract_functions(cleaned)

            # TypeScript 전용
            if is_ts:
                result.interfaces = self._extract_interfaces(cleaned)
                result.types = self._extract_types(cleaned)

        except Exception as e:
            result.parse_error = True
            result.error_message = str(e)
            logger.warning(f"Parse error in {file_path}: {e}")

        return result

    def _remove_strings_and_comments(self, content: str) -> str:
        """문자열과 주석 제거"""
        # 한 줄 주석
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        # 여러 줄 주석
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        # 템플릿 리터럴 (간단하게)
        content = re.sub(r"`[^`]*`", '""', content)
        # 큰따옴표 문자열
        content = re.sub(r'"(?:[^"\\]|\\.)*"', '""', content)
        # 작은따옴표 문자열
        content = re.sub(r"'(?:[^'\\]|\\.)*'", "''", content)
        return content

    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """Import 추출"""
        imports = []

        for pattern in self.IMPORT_PATTERNS:
            for match in pattern.finditer(content):
                groups = match.groups()
                if len(groups) == 2:
                    name, module = groups
                    if "{" in str(name) or name is None:
                        # Named imports
                        if name:
                            names = [
                                n.strip().split(" as ")[0].strip()
                                for n in name.split(",")
                                if n.strip()
                            ]
                            for n in names:
                                imports.append({"module": module, "name": n, "type": "named"})
                    else:
                        imports.append({"module": module, "name": name, "type": "default"})
                elif len(groups) == 1:
                    # Side effect import
                    imports.append({"module": groups[0], "name": None, "type": "side_effect"})

        return imports

    def _extract_exports(self, content: str) -> Tuple[List[str], bool]:
        """Export 추출"""
        exports = []
        has_default = False

        for pattern in self.EXPORT_PATTERNS:
            for match in pattern.finditer(content):
                text = match.group(0)

                if "default" in text:
                    has_default = True
                    name = match.group(1) if match.groups() else None
                    if name and name not in exports:
                        exports.append(name)
                elif match.groups():
                    names_str = match.group(1)
                    if "{" in text:
                        # Named exports: export { X, Y }
                        names = [
                            n.strip().split(" as ")[0].strip()
                            for n in names_str.split(",")
                            if n.strip()
                        ]
                        for n in names:
                            if n not in exports:
                                exports.append(n)
                    else:
                        # Single export
                        if names_str and names_str not in exports:
                            exports.append(names_str)

        return exports, has_default

    def _extract_classes(self, content: str) -> List[str]:
        """Class 추출"""
        classes = []
        for match in self.CLASS_PATTERN.finditer(content):
            name = match.group(1)
            if name and name not in classes:
                classes.append(name)
        return classes

    def _extract_functions(self, content: str) -> List[str]:
        """Function 추출"""
        functions = []
        for pattern in self.FUNCTION_PATTERNS:
            for match in pattern.finditer(content):
                name = match.group(1)
                if name and name not in functions:
                    functions.append(name)
        return functions

    def _extract_interfaces(self, content: str) -> List[str]:
        """TypeScript Interface 추출"""
        interfaces = []
        for match in self.INTERFACE_PATTERN.finditer(content):
            name = match.group(1)
            if name and name not in interfaces:
                interfaces.append(name)
        return interfaces

    def _extract_types(self, content: str) -> List[str]:
        """TypeScript Type 추출"""
        types = []
        for match in self.TYPE_PATTERN.finditer(content):
            name = match.group(1)
            if name and name not in types:
                types.append(name)
        return types


class FallbackParser(BaseParser):
    """Fallback 파서 (지원하지 않는 언어용)"""

    def __init__(self, language: str):
        self.language = language

    def parse(self, content: str, file_path: str) -> ParseResult:
        result = ParseResult(language=self.language)
        result.line_count = content.count("\n") + 1
        result.ast_hash = self.compute_ast_hash(content)
        # 구조 추출 없이 기본 Context만 생성
        return result


class ASTParserFactory:
    """AST 파서 팩토리"""

    LANGUAGE_PARSERS = {
        "python": PythonParser,
        "javascript": JavaScriptTypeScriptParser,
        "typescript": JavaScriptTypeScriptParser,
    }

    @classmethod
    def get_parser(cls, language: str) -> BaseParser:
        """언어에 맞는 파서 반환"""
        parser_class = cls.LANGUAGE_PARSERS.get(language)
        if parser_class:
            return parser_class()
        return FallbackParser(language)

    @classmethod
    def parse_file(cls, file_path: str, language: Optional[str] = None) -> ParseResult:
        """
        파일을 파싱하여 구조 정보 추출

        Args:
            file_path: 파일 경로
            language: 언어 (없으면 확장자에서 추론)

        Returns:
            ParseResult: 파싱 결과
        """
        if language is None:
            language = cls._detect_language(file_path)

        parser = cls.get_parser(language)

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return parser.parse(content, file_path)
        except FileNotFoundError:
            result = ParseResult(language=language)
            result.parse_error = True
            result.error_message = f"File not found: {file_path}"
            return result
        except Exception as e:
            result = ParseResult(language=language)
            result.parse_error = True
            result.error_message = str(e)
            return result

    @classmethod
    def _detect_language(cls, file_path: str) -> str:
        """확장자에서 언어 감지"""
        ext_map = {
            ".py": "python",
            ".pyw": "python",
            ".js": "javascript",
            ".mjs": "javascript",
            ".cjs": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".mts": "typescript",
            ".cts": "typescript",
        }
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, "unknown")


def resolve_import_path(
    importing_file: str, import_module: str, project_root: str, language: str
) -> Optional[str]:
    """
    Import 경로를 실제 파일 경로로 해결

    Args:
        importing_file: import하는 파일 경로
        import_module: import 모듈명
        project_root: 프로젝트 루트 경로
        language: 언어

    Returns:
        해결된 파일 경로 또는 None
    """
    project_root = Path(project_root)
    importing_dir = Path(importing_file).parent

    if language in ("javascript", "typescript"):
        return _resolve_js_import(importing_dir, import_module, project_root)
    elif language == "python":
        return _resolve_python_import(importing_dir, import_module, project_root)

    return None


def _resolve_js_import(
    importing_dir: Path, import_module: str, project_root: Path
) -> Optional[str]:
    """JavaScript/TypeScript import 경로 해결"""
    # 상대 경로
    if import_module.startswith("."):
        base = importing_dir / import_module
    else:
        # node_modules 또는 절대 경로
        # 프로젝트 내 파일인지 먼저 확인
        base = project_root / import_module

    # 확장자 시도
    extensions = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ""]

    for ext in extensions:
        candidate = Path(str(base) + ext)
        if candidate.exists() and candidate.is_file():
            return str(candidate)

        # index 파일 확인
        if ext == "":
            for idx_ext in ["/index.ts", "/index.tsx", "/index.js", "/index.jsx"]:
                idx_candidate = Path(str(base) + idx_ext)
                if idx_candidate.exists():
                    return str(idx_candidate)

    return None


def _resolve_python_import(
    importing_dir: Path, import_module: str, project_root: Path
) -> Optional[str]:
    """Python import 경로 해결"""
    # 상대 import는 . 개수로 판단
    if import_module.startswith("."):
        dots = len(import_module) - len(import_module.lstrip("."))
        remaining = import_module[dots:]
        base = importing_dir
        for _ in range(dots - 1):
            base = base.parent
        if remaining:
            parts = remaining.split(".")
            base = base.joinpath(*parts)
    else:
        # 절대 import
        parts = import_module.split(".")
        base = project_root.joinpath(*parts)

    # .py 파일 확인
    py_file = Path(str(base) + ".py")
    if py_file.exists():
        return str(py_file)

    # 패키지 __init__.py 확인
    init_file = base / "__init__.py"
    if init_file.exists():
        return str(init_file)

    return None
