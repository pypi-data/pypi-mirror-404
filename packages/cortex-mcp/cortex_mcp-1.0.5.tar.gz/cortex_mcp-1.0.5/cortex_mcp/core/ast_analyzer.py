"""
Cortex MCP - AST Analyzer

실행 없이 코드 구조를 분석하여 검증 지원

기능:
- Python AST 기반 코드 분석
- 함수/클래스 정의 추출
- import 문 분석
- 문법 오류 감지
- 주장-코드 일치 검증

지원 언어:
- Python: ast 모듈 사용 (완전 지원)
- JavaScript/TypeScript: 정규식 기반 (부분 지원)
- 기타: 정규식 기반 fallback
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ASTAnalyzer:
    """
    코드 구조 분석기

    코드 실행 없이 AST를 분석하여
    함수, 클래스, import 등의 정보를 추출
    """

    # 지원 언어 확장자 매핑
    LANGUAGE_EXTENSIONS = {
        "python": [".py", ".pyw"],
        "javascript": [".js", ".jsx", ".mjs"],
        "typescript": [".ts", ".tsx"],
    }

    def __init__(self):
        """분석기 초기화"""
        pass

    def detect_language(self, file_path: str) -> str:
        """
        파일 확장자로 언어 감지

        Args:
            file_path: 파일 경로

        Returns:
            언어명 (python, javascript, typescript, unknown)
        """
        ext = Path(file_path).suffix.lower()

        for language, extensions in self.LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                return language

        return "unknown"

    def analyze(self, code: str, language: str = "python") -> Dict:
        """
        코드 분석 수행

        Args:
            code: 분석할 코드 문자열
            language: 언어 (python, javascript, typescript)

        Returns:
            {
                "valid_syntax": bool,
                "syntax_error": str | null,
                "functions": [...],
                "classes": [...],
                "imports": [...],
                "variables": [...],
                "potential_issues": [...]
            }
        """
        if language == "python":
            return self._analyze_python(code)
        elif language in ("javascript", "typescript"):
            return self._analyze_javascript(code)
        else:
            return self._analyze_generic(code)

    def analyze_file(self, file_path: str) -> Dict:
        """
        파일 분석

        Args:
            file_path: 파일 경로

        Returns:
            분석 결과
        """
        path = Path(file_path)

        if not path.exists():
            return {
                "valid_syntax": False,
                "syntax_error": f"파일을 찾을 수 없음: {file_path}",
                "functions": [],
                "classes": [],
                "imports": [],
                "variables": [],
                "potential_issues": [],
            }

        try:
            code = path.read_text(encoding="utf-8")
            language = self.detect_language(file_path)
            result = self.analyze(code, language)
            result["file_path"] = file_path
            result["language"] = language
            return result
        except Exception as e:
            return {
                "valid_syntax": False,
                "syntax_error": f"파일 읽기 실패: {str(e)}",
                "functions": [],
                "classes": [],
                "imports": [],
                "variables": [],
                "potential_issues": [],
            }

    def _analyze_python(self, code: str) -> Dict:
        """
        Python 코드 AST 분석

        Args:
            code: Python 코드

        Returns:
            분석 결과
        """
        result = {
            "valid_syntax": True,
            "syntax_error": None,
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": [],
            "potential_issues": [],
        }

        # 구문 분석 시도
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result["valid_syntax"] = False
            result["syntax_error"] = f"Line {e.lineno}: {e.msg}"
            result["potential_issues"].append({
                "type": "syntax_error",
                "line": e.lineno,
                "message": e.msg,
            })
            return result

        # AST 순회
        for node in ast.walk(tree):
            # 함수 정의
            if isinstance(node, ast.FunctionDef):
                func_info = self._extract_function_info(node)
                result["functions"].append(func_info)

            # 비동기 함수 정의
            elif isinstance(node, ast.AsyncFunctionDef):
                func_info = self._extract_function_info(node, is_async=True)
                result["functions"].append(func_info)

            # 클래스 정의
            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node)
                result["classes"].append(class_info)

            # import 문
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                    })

            # from ... import 문
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    result["imports"].append({
                        "type": "from_import",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                    })

            # 전역 변수 할당 (모듈 레벨)
            elif isinstance(node, ast.Assign):
                if hasattr(node, "lineno"):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            result["variables"].append({
                                "name": target.id,
                                "line": node.lineno,
                            })

        # 잠재적 이슈 감지
        result["potential_issues"].extend(self._detect_python_issues(tree, code))

        return result

    def _extract_function_info(self, node: ast.FunctionDef, is_async: bool = False) -> Dict:
        """함수 정보 추출"""
        args = []
        for arg in node.args.args:
            arg_info = {"name": arg.arg}
            if arg.annotation:
                arg_info["type"] = ast.unparse(arg.annotation)
            args.append(arg_info)

        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        decorators = [ast.unparse(d) for d in node.decorator_list]

        return {
            "name": node.name,
            "args": args,
            "return_type": return_type,
            "decorators": decorators,
            "is_async": is_async,
            "line": node.lineno,
            "docstring": ast.get_docstring(node),
        }

    def _extract_class_info(self, node: ast.ClassDef) -> Dict:
        """클래스 정보 추출"""
        bases = [ast.unparse(b) for b in node.bases]
        decorators = [ast.unparse(d) for d in node.decorator_list]

        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        return {
            "name": node.name,
            "bases": bases,
            "decorators": decorators,
            "methods": methods,
            "line": node.lineno,
            "docstring": ast.get_docstring(node),
        }

    def _detect_python_issues(self, tree: ast.AST, code: str) -> List[Dict]:
        """Python 코드 잠재적 이슈 감지"""
        issues = []

        # bare except 감지
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        "type": "bare_except",
                        "line": node.lineno,
                        "message": "bare except는 피하는 것이 좋습니다. 특정 예외를 명시하세요.",
                        "severity": "warning",
                    })

            # mutable default argument 감지
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append({
                            "type": "mutable_default",
                            "line": node.lineno,
                            "message": f"함수 '{node.name}'에서 가변 기본 인자 사용",
                            "severity": "warning",
                        })

        return issues

    def _analyze_javascript(self, code: str) -> Dict:
        """
        JavaScript/TypeScript 정규식 기반 분석

        Args:
            code: JS/TS 코드

        Returns:
            분석 결과
        """
        result = {
            "valid_syntax": True,  # 정규식으로는 완전한 검증 불가
            "syntax_error": None,
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": [],
            "potential_issues": [],
        }

        # 함수 정의 추출
        # function name(...) { } 패턴
        func_pattern = r'(?:async\s+)?function\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(func_pattern, code):
            line = code[:match.start()].count('\n') + 1
            result["functions"].append({
                "name": match.group(1),
                "is_async": "async" in match.group(0),
                "line": line,
            })

        # 화살표 함수 (const name = ...)
        arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>'
        for match in re.finditer(arrow_pattern, code):
            line = code[:match.start()].count('\n') + 1
            result["functions"].append({
                "name": match.group(1),
                "is_async": "async" in match.group(0),
                "line": line,
            })

        # 클래스 정의 추출
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
        for match in re.finditer(class_pattern, code):
            line = code[:match.start()].count('\n') + 1
            result["classes"].append({
                "name": match.group(1),
                "bases": [match.group(2)] if match.group(2) else [],
                "line": line,
            })

        # import 문 추출
        # import ... from '...'
        import_pattern = r"import\s+(?:{[^}]+}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(import_pattern, code):
            line = code[:match.start()].count('\n') + 1
            result["imports"].append({
                "type": "import",
                "module": match.group(1),
                "line": line,
            })

        # require 문 추출
        require_pattern = r"(?:const|let|var)\s+(\w+)\s*=\s*require\(['\"]([^'\"]+)['\"]\)"
        for match in re.finditer(require_pattern, code):
            line = code[:match.start()].count('\n') + 1
            result["imports"].append({
                "type": "require",
                "name": match.group(1),
                "module": match.group(2),
                "line": line,
            })

        return result

    def _analyze_generic(self, code: str) -> Dict:
        """
        일반 언어 정규식 기반 분석

        Args:
            code: 코드

        Returns:
            기본 분석 결과
        """
        return {
            "valid_syntax": True,  # 검증 불가
            "syntax_error": None,
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": [],
            "potential_issues": [{
                "type": "unsupported_language",
                "message": "지원하지 않는 언어입니다. 정확한 분석이 어렵습니다.",
                "severity": "info",
            }],
        }

    def verify_claim(self, claim: str, code: str, language: str = "python") -> Dict:
        """
        주장과 코드 일치 여부 검증

        Args:
            claim: 검증할 주장 (예: "login 함수를 구현했습니다")
            code: 검증할 코드
            language: 언어

        Returns:
            {
                "verified": bool,
                "confidence": float,
                "evidence": [...],
                "reason": str
            }
        """
        analysis = self.analyze(code, language)

        result = {
            "verified": False,
            "confidence": 0.0,
            "evidence": [],
            "reason": "",
        }

        # 문법 오류가 있으면 검증 실패
        if not analysis["valid_syntax"]:
            result["reason"] = f"문법 오류: {analysis['syntax_error']}"
            return result

        # 주장에서 키워드 추출
        claim_lower = claim.lower()

        # 함수 관련 주장
        if any(kw in claim_lower for kw in ["함수", "function", "메서드", "method"]):
            # 함수명 추출 시도
            func_names = [f["name"].lower() for f in analysis["functions"]]

            for func in analysis["functions"]:
                if func["name"].lower() in claim_lower:
                    result["verified"] = True
                    result["confidence"] = 0.9
                    result["evidence"].append({
                        "type": "function_found",
                        "name": func["name"],
                        "line": func["line"],
                    })
                    result["reason"] = f"함수 '{func['name']}'가 {func['line']}번 라인에서 발견됨"
                    return result

        # 클래스 관련 주장
        if any(kw in claim_lower for kw in ["클래스", "class"]):
            for cls in analysis["classes"]:
                if cls["name"].lower() in claim_lower:
                    result["verified"] = True
                    result["confidence"] = 0.9
                    result["evidence"].append({
                        "type": "class_found",
                        "name": cls["name"],
                        "line": cls["line"],
                    })
                    result["reason"] = f"클래스 '{cls['name']}'가 {cls['line']}번 라인에서 발견됨"
                    return result

        # 구현/생성 관련 주장 (일반적인 검증)
        if any(kw in claim_lower for kw in ["구현", "생성", "추가", "작성"]):
            if analysis["functions"] or analysis["classes"]:
                result["verified"] = True
                result["confidence"] = 0.6
                result["evidence"].append({
                    "type": "code_structure_found",
                    "functions": len(analysis["functions"]),
                    "classes": len(analysis["classes"]),
                })
                result["reason"] = f"코드 구조 발견: {len(analysis['functions'])}개 함수, {len(analysis['classes'])}개 클래스"
                return result

        result["reason"] = "주장과 일치하는 코드 구조를 찾지 못함"
        return result

    def get_code_summary(self, code: str, language: str = "python") -> str:
        """
        코드 요약 문자열 생성

        Args:
            code: 코드
            language: 언어

        Returns:
            요약 문자열
        """
        analysis = self.analyze(code, language)

        if not analysis["valid_syntax"]:
            return f"[문법 오류] {analysis['syntax_error']}"

        parts = []

        if analysis["classes"]:
            class_names = [c["name"] for c in analysis["classes"]]
            parts.append(f"클래스: {', '.join(class_names)}")

        if analysis["functions"]:
            func_names = [f["name"] for f in analysis["functions"]]
            if len(func_names) > 5:
                parts.append(f"함수: {', '.join(func_names[:5])} 외 {len(func_names)-5}개")
            else:
                parts.append(f"함수: {', '.join(func_names)}")

        if analysis["imports"]:
            modules = list(set(i["module"] for i in analysis["imports"]))
            if len(modules) > 5:
                parts.append(f"import: {', '.join(modules[:5])} 외 {len(modules)-5}개")
            else:
                parts.append(f"import: {', '.join(modules)}")

        if not parts:
            return "코드 구조 없음"

        return " | ".join(parts)


# 싱글톤 인스턴스
_analyzer_instance: Optional[ASTAnalyzer] = None


def get_ast_analyzer() -> ASTAnalyzer:
    """
    ASTAnalyzer 싱글톤 인스턴스 반환

    Returns:
        ASTAnalyzer 인스턴스
    """
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ASTAnalyzer()
    return _analyzer_instance
