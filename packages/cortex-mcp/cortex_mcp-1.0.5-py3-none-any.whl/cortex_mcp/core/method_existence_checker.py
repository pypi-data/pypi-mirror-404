"""
Phase 9.5.2: Method Existence Deep Check

answer.md 문제 해결: 메서드 존재 여부 AST 기반 검증

감지 문제:
- Line 148: context_manager.compress_content(large_content)
- Error: 'ContextManager' object has no attribute 'compress_content'

해결:
- AST 파싱으로 클래스 정의 분석
- 메서드가 실제로 존재하는지 확인
- Stub 메서드(pass only) 감지
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MethodDefinition:
    """메서드 정의 정보"""
    class_name: str
    method_name: str
    is_stub: bool  # pass만 있으면 True
    line_number: int
    file_path: str
    docstring: Optional[str] = None


@dataclass
class MethodCallClaim:
    """메서드 호출 주장"""
    object_name: str  # 예: context_manager
    class_name: Optional[str]  # 예: ContextManager (추론 필요)
    method_name: str  # 예: compress_content
    file_path: Optional[str]  # 예: core/context_manager.py


class MethodExistenceChecker:
    """
    AST 기반 메서드 존재 확인 (Phase 9.5 Enhanced with Multi-Strategy)

    answer.md Line 148 문제 해결:
    - AI가 "compress_content() 메서드 사용"이라고 주장
    - 실제로는 ContextManager 클래스에 해당 메서드 없음
    - AST 파싱으로 메서드 정의 확인

    Phase 9.5 개선 (Prof. Alex Kumar - Stanford):
    - Multi-Strategy Approach:
      1. AST type inference (var = ClassName() 분석)
      2. Method uniqueness check (메서드가 1개 클래스에만 있으면 자동 매칭)
      3. Import analysis (사용 가능한 클래스 확인)
      4. Heuristic matching (기존 snake_case 변환, fallback)
    - Class-Method Index 캐싱 (성능 향상)
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.class_method_cache: Dict[str, Dict] = {}  # {class_name: {methods: [], file: str}}
        self._build_index()

    def extract_method_calls_from_claim(
        self, claim_text: str
    ) -> List[MethodCallClaim]:
        """
        Claim 텍스트에서 메서드 호출 추출

        패턴:
        - object.method() 형식
        - ClassName.method() 형식

        Args:
            claim_text: Claim 텍스트

        Returns:
            메서드 호출 주장 목록
        """
        method_calls = []

        # 패턴 1: object.method() 형식
        # 예: context_manager.compress_content(large_content)
        # BUG FIX: 숫자로 시작하는 패턴 제외 (예: "1.00(" → 메서드 호출 아님)
        pattern1 = r"([a-zA-Z_]\w*)\.(\w+)\s*\("

        matches = re.findall(pattern1, claim_text)

        for object_name, method_name in matches:
            # 클래스 이름 추론 (예: context_manager → ContextManager)
            class_name = self._infer_class_name(object_name)

            method_call = MethodCallClaim(
                object_name=object_name,
                class_name=class_name,
                method_name=method_name,
                file_path=None,  # 나중에 추론
            )

            method_calls.append(method_call)

        return method_calls

    def _infer_class_name(self, object_name: str) -> Optional[str]:
        """
        객체 이름으로 클래스 이름 추론

        규칙:
        - context_manager → ContextManager
        - user_service → UserService

        Args:
            object_name: 객체 이름 (snake_case)

        Returns:
            클래스 이름 (PascalCase)
        """
        # Snake case → Pascal case 변환
        parts = object_name.split('_')
        class_name = ''.join(word.capitalize() for word in parts)

        return class_name

    def find_class_file(
        self, class_name: str, base_dir: Optional[str] = None
    ) -> Optional[Path]:
        """
        클래스 정의 파일 찾기

        검색 전략:
        1. {class_name}.py (예: ContextManager → context_manager.py)
        2. 파일 내용 검색 (class ClassName 패턴)

        Args:
            class_name: 클래스 이름
            base_dir: 검색 시작 디렉토리

        Returns:
            클래스 정의 파일 경로
        """
        # Snake case 파일명 추론
        # ContextManager → context_manager.py
        snake_case = re.sub(
            r'(?<!^)(?=[A-Z])', '_', class_name
        ).lower()

        search_path = base_dir or self.project_path

        # 패턴 1: 파일명 매칭
        potential_files = list(Path(search_path).rglob(f"{snake_case}.py"))

        if potential_files:
            # 첫 번째 매칭 파일 반환
            return potential_files[0]

        # 패턴 2: 파일 내용 검색 (class ClassName 패턴)
        pattern = f"class {class_name}"

        for py_file in Path(search_path).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    if pattern in content:
                        return py_file
            except (UnicodeDecodeError, PermissionError):
                continue

        return None

    def parse_class_methods(
        self, file_path: str, class_name: str
    ) -> List[MethodDefinition]:
        """
        클래스 파일에서 메서드 정의 추출

        Args:
            file_path: 클래스 파일 경로
            class_name: 클래스 이름

        Returns:
            메서드 정의 목록
        """
        path = Path(file_path)

        if not path.exists():
            return []

        # AST 파싱
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            return []

        methods = []

        # 클래스 노드 찾기
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                # 클래스 내 메서드 추출
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # 메서드 이름, 라인 번호
                        method_name = item.name
                        line_number = item.lineno

                        # Docstring 추출
                        docstring = ast.get_docstring(item)

                        # Stub 여부 확인 (pass만 있는지)
                        is_stub = self._is_stub_method(item)

                        method_def = MethodDefinition(
                            class_name=class_name,
                            method_name=method_name,
                            is_stub=is_stub,
                            line_number=line_number,
                            file_path=str(path),
                            docstring=docstring,
                        )

                        methods.append(method_def)

        return methods

    def _is_stub_method(self, func_node: ast.FunctionDef) -> bool:
        """
        메서드가 stub인지 확인 (pass만 있거나 비어있음)

        Args:
            func_node: 함수 AST 노드

        Returns:
            Stub 여부
        """
        # 함수 본문 확인
        body = func_node.body

        # Docstring 제외
        start_idx = 0
        if (body and isinstance(body[0], ast.Expr) and
            isinstance(body[0].value, ast.Constant)):
            # Docstring이 있으면 스킵
            start_idx = 1

        actual_body = body[start_idx:]

        # 본문이 없으면 stub
        if not actual_body:
            return True

        # pass만 있으면 stub
        if len(actual_body) == 1 and isinstance(actual_body[0], ast.Pass):
            return True

        # Ellipsis(...) 만 있어도 stub
        if (len(actual_body) == 1 and
            isinstance(actual_body[0], ast.Expr) and
            isinstance(actual_body[0].value, ast.Constant) and
            actual_body[0].value.value is ...):
            return True

        return False

    def _build_index(self):
        """
        프로젝트 전체 스캔하여 Class-Method 인덱스 구축

        Phase 9.5 개선 (Prof. Alex Kumar):
        - 모든 .py 파일의 클래스와 메서드를 캐시
        - 빠른 검색을 위한 인덱스 구조
        """
        for py_file in Path(self.project_path).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()

                tree = ast.parse(source)

                # 클래스 노드 찾기
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name

                        # 메서드 목록 추출
                        methods = []
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                methods.append(item.name)

                        # 캐시에 저장
                        self.class_method_cache[class_name] = {
                            "methods": methods,
                            "file": str(py_file),
                        }

            except (SyntaxError, UnicodeDecodeError, PermissionError):
                continue

    def _infer_type_from_ast(
        self, object_name: str, file_path: Optional[str] = None
    ) -> Optional[str]:
        """
        AST 분석으로 변수의 타입 추론

        패턴:
        - var = ClassName() 분석
        - var = ClassName.method() 분석

        Args:
            object_name: 변수 이름
            file_path: 검색할 파일 경로 (선택)

        Returns:
            추론된 클래스 이름
        """
        # 파일이 지정되지 않으면 전체 프로젝트 검색
        search_files = [Path(file_path)] if file_path else Path(self.project_path).rglob("*.py")

        for py_file in search_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()

                tree = ast.parse(source)

                # Assign 노드 찾기 (var = ClassName())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        # 변수 이름 확인
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == object_name:
                                # Call 노드 확인 (ClassName())
                                if isinstance(node.value, ast.Call):
                                    if isinstance(node.value.func, ast.Name):
                                        # ClassName() 패턴
                                        return node.value.func.id
                                    elif isinstance(node.value.func, ast.Attribute):
                                        # module.ClassName() 패턴
                                        return node.value.func.attr

            except (SyntaxError, UnicodeDecodeError, PermissionError):
                continue

        return None

    def _find_classes_with_method(self, method_name: str) -> List[str]:
        """
        특정 메서드를 가진 클래스 찾기 (Uniqueness Check)

        Args:
            method_name: 메서드 이름

        Returns:
            메서드를 가진 클래스 이름 목록
        """
        classes_with_method = []

        for class_name, info in self.class_method_cache.items():
            if method_name in info["methods"]:
                classes_with_method.append(class_name)

        return classes_with_method

    def _get_imported_classes(self, file_path: str) -> List[str]:
        """
        파일에서 import된 클래스 목록 반환

        패턴:
        - from module import ClassName
        - import module.ClassName

        Args:
            file_path: 파일 경로

        Returns:
            Import된 클래스 이름 목록
        """
        imported_classes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                # from module import ClassName
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imported_classes.append(alias.name)

                # import module.ClassName (as alias)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        # module.ClassName → ClassName
                        parts = alias.name.split('.')
                        if len(parts) > 1:
                            imported_classes.append(parts[-1])
                        else:
                            imported_classes.append(alias.name)

        except (SyntaxError, UnicodeDecodeError, PermissionError):
            pass

        return imported_classes

    def verify_method_exists(
        self, method_call: MethodCallClaim
    ) -> Tuple[bool, str, Optional[MethodDefinition]]:
        """
        메서드 존재 여부 검증 (Multi-Strategy Approach)

        Phase 9.5 개선 (Prof. Alex Kumar):
        4가지 전략을 순서대로 시도:
        1. AST Type Inference (가장 정확)
        2. Method Uniqueness Check (메서드가 1개 클래스에만 있으면 자동 매칭)
        3. Import Analysis (import된 클래스만 검색)
        4. Heuristic Fallback (snake_case 변환)

        Args:
            method_call: 메서드 호출 주장

        Returns:
            (존재 여부, 이유, 메서드 정의)
        """
        object_name = method_call.object_name
        method_name = method_call.method_name
        candidate_classes = []

        # Strategy 1: AST Type Inference
        inferred_class = self._infer_type_from_ast(object_name, method_call.file_path)
        if inferred_class:
            candidate_classes.append((inferred_class, "AST_inference"))

        # Strategy 2: Method Uniqueness Check
        classes_with_method = self._find_classes_with_method(method_name)
        if len(classes_with_method) == 1:
            # 메서드가 1개 클래스에만 있으면 자동 매칭
            candidate_classes.append((classes_with_method[0], "uniqueness"))
        elif len(classes_with_method) > 1:
            # 여러 클래스가 있으면 후보로 추가
            for cls in classes_with_method:
                candidate_classes.append((cls, "uniqueness_multi"))

        # Strategy 3: Import Analysis (file_path가 있을 경우)
        if method_call.file_path:
            imported_classes = self._get_imported_classes(method_call.file_path)
            for cls in imported_classes:
                if cls in self.class_method_cache:
                    if method_name in self.class_method_cache[cls]["methods"]:
                        candidate_classes.append((cls, "import_analysis"))

        # Strategy 4: Heuristic Fallback (snake_case → PascalCase)
        if method_call.class_name:
            candidate_classes.append((method_call.class_name, "heuristic"))

        # 후보가 없으면 실패
        if not candidate_classes:
            return False, f"클래스를 추론할 수 없음 (object: {object_name})", None

        # 후보 클래스들을 순서대로 검증
        for class_name, strategy in candidate_classes:
            # 클래스 파일 찾기
            if class_name in self.class_method_cache:
                class_file = Path(self.class_method_cache[class_name]["file"])
            else:
                class_file = self.find_class_file(class_name)

            if not class_file or not class_file.exists():
                continue

            # 메서드 추출
            methods = self.parse_class_methods(str(class_file), class_name)

            # 메서드 이름 매칭
            for method_def in methods:
                if method_def.method_name == method_name:
                    # 메서드 존재
                    if method_def.is_stub:
                        return False, f"메서드는 존재하지만 stub임 (미구현, strategy: {strategy})", method_def
                    else:
                        return True, f"메서드 존재하며 구현됨 (strategy: {strategy})", method_def

        # 모든 전략 실패
        tried_classes = [cls for cls, _ in candidate_classes]
        return False, f"메서드 '{method_name}'를 찾을 수 없음 (tried: {tried_classes})", None

    def verify_claim_method_calls(
        self, claim_text: str
    ) -> Dict[str, any]:
        """
        Claim에서 메서드 호출 추출 및 검증

        Args:
            claim_text: Claim 텍스트

        Returns:
            검증 결과
        """
        # 메서드 호출 추출
        method_calls = self.extract_method_calls_from_claim(claim_text)

        if not method_calls:
            return {
                "verified": True,  # 메서드 호출 없으면 검증 성공
                "reason": "no_method_calls",
                "method_calls": [],
            }

        # 각 메서드 호출 검증
        results = []
        all_verified = True

        for method_call in method_calls:
            exists, reason, method_def = self.verify_method_exists(
                method_call
            )

            results.append({
                "method_call": method_call,
                "exists": exists,
                "reason": reason,
                "method_definition": method_def,
            })

            if not exists:
                all_verified = False

        return {
            "verified": all_verified,
            "reason": "all_methods_exist" if all_verified else "missing_methods",
            "method_calls": results,
        }


# ====================================================================
# 유틸리티 함수
# ====================================================================

def check_method_existence_in_claim(
    claim_text: str, project_path: str
) -> Dict[str, any]:
    """
    Claim에서 메서드 존재 여부 검증

    answer.md Line 148 문제 감지:
    - context_manager.compress_content() 호출 주장
    - ContextManager 클래스에 compress_content 메서드 없음
    - False 반환

    Args:
        claim_text: Claim 텍스트
        project_path: 프로젝트 루트 경로

    Returns:
        검증 결과
    """
    checker = MethodExistenceChecker(project_path)
    return checker.verify_claim_method_calls(claim_text)
