"""
코드 구조 분석 시스템

Cortex Phase 9: Hallucination Detection System
실제 코드 구조를 분석하여 LLM 응답의 정확성을 검증합니다.

핵심 기능:
- 프로젝트 파일 구조 분석
- 함수/클래스 존재 여부 확인
- Import 관계 검증
- 파일 경로 일치 확인
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CodeStructureAnalyzer:
    """
    코드 구조 분석 클래스

    프로젝트 코드베이스의 실제 구조를 분석하여
    LLM이 참조한 파일/함수/클래스가 실제로 존재하는지 검증합니다.
    """

    # 지원하는 파일 확장자
    SUPPORTED_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".cs",
    }

    # 함수/클래스 정의 패턴 (언어별)
    DEFINITION_PATTERNS = {
        "python": {
            "function": r"def\s+(\w+)\s*\(",
            "class": r"class\s+(\w+)\s*[:\(]",
            "import": r"(?:from\s+[\w.]+\s+)?import\s+([\w,\s]+)",
        },
        "javascript": {
            "function": r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:function|\())",
            "class": r"class\s+(\w+)\s*{",
            "import": r"import\s+.*?from\s+['\"](.+?)['\"]",
        },
        "typescript": {
            "function": r"(?:function\s+(\w+)|const\s+(\w+)\s*:\s*.*?=>)",
            "class": r"(?:class|interface)\s+(\w+)\s*{",
            "import": r"import\s+.*?from\s+['\"](.+?)['\"]",
        },
        "go": {
            "function": r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(",
            "class": r"type\s+(\w+)\s+struct",
            "import": r"import\s+[\"'](.+?)[\"']",
        },
        "java": {
            "function": r"(?:public|private|protected)\s+.*?\s+(\w+)\s*\(",
            "class": r"(?:public|private)?\s*class\s+(\w+)",
            "import": r"import\s+([\w.]+);",
        },
    }

    def __init__(self, project_path: str):
        """
        Code Structure Analyzer 초기화

        Args:
            project_path: 프로젝트 루트 경로
        """
        self.project_path = Path(project_path)
        self._file_cache = {}  # 파일 내용 캐시
        self._structure_cache = {}  # 구조 분석 캐시

    def analyze_project_structure(self) -> Dict:
        """
        프로젝트 전체 구조 분석

        Returns:
            프로젝트 구조 정보
        """
        files_by_ext = {}
        total_files = 0

        for ext in self.SUPPORTED_EXTENSIONS:
            pattern = f"**/*{ext}"
            files = list(self.project_path.glob(pattern))
            if files:
                files_by_ext[ext] = [str(f.relative_to(self.project_path)) for f in files]
                total_files += len(files)

        return {
            "project_path": str(self.project_path),
            "total_files": total_files,
            "files_by_extension": files_by_ext,
            "supported_languages": list(files_by_ext.keys()),
            "timestamp": datetime.now().isoformat(),
        }

    def verify_file_references(self, file_paths: List[str]) -> Dict:
        """
        파일 참조 검증

        Args:
            file_paths: 검증할 파일 경로 목록

        Returns:
            검증 결과
        """
        results = []

        for file_path in file_paths:
            exists = self._check_file_exists(file_path)

            if exists:
                # 파일이 존재하면 구조 분석
                structure = self._analyze_file_structure(file_path)
                results.append({"file_path": file_path, "exists": True, "structure": structure})
            else:
                # 파일이 없으면 유사 파일 찾기
                similar_files = self._find_similar_files(file_path)
                results.append(
                    {"file_path": file_path, "exists": False, "similar_files": similar_files}
                )

        verified = sum(1 for r in results if r["exists"])

        return {
            "total_references": len(file_paths),
            "verified": verified,
            "unverified": len(file_paths) - verified,
            "verification_rate": verified / len(file_paths) if len(file_paths) > 0 else 0.0,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    def verify_function_references(self, file_path: str, function_names: List[str]) -> Dict:
        """
        함수 참조 검증

        Args:
            file_path: 파일 경로
            function_names: 검증할 함수 이름 목록

        Returns:
            검증 결과
        """
        if not self._check_file_exists(file_path):
            return {
                "file_path": file_path,
                "file_exists": False,
                "functions": [],
                "verification_rate": 0.0,
            }

        # 파일 구조 분석
        structure = self._analyze_file_structure(file_path)
        functions_in_file = structure.get("functions", [])

        # 함수 존재 여부 확인
        results = []
        for func_name in function_names:
            exists = func_name in functions_in_file
            results.append({"function_name": func_name, "exists": exists})

        verified = sum(1 for r in results if r["exists"])

        return {
            "file_path": file_path,
            "file_exists": True,
            "total_references": len(function_names),
            "verified": verified,
            "unverified": len(function_names) - verified,
            "verification_rate": verified / len(function_names) if len(function_names) > 0 else 0.0,
            "results": results,
            "functions_in_file": functions_in_file,
            "timestamp": datetime.now().isoformat(),
        }

    def verify_class_references(self, file_path: str, class_names: List[str]) -> Dict:
        """
        클래스 참조 검증

        Args:
            file_path: 파일 경로
            class_names: 검증할 클래스 이름 목록

        Returns:
            검증 결과
        """
        if not self._check_file_exists(file_path):
            return {
                "file_path": file_path,
                "file_exists": False,
                "classes": [],
                "verification_rate": 0.0,
            }

        # 파일 구조 분석
        structure = self._analyze_file_structure(file_path)
        classes_in_file = structure.get("classes", [])

        # 클래스 존재 여부 확인
        results = []
        for class_name in class_names:
            exists = class_name in classes_in_file
            results.append({"class_name": class_name, "exists": exists})

        verified = sum(1 for r in results if r["exists"])

        return {
            "file_path": file_path,
            "file_exists": True,
            "total_references": len(class_names),
            "verified": verified,
            "unverified": len(class_names) - verified,
            "verification_rate": verified / len(class_names) if len(class_names) > 0 else 0.0,
            "results": results,
            "classes_in_file": classes_in_file,
            "timestamp": datetime.now().isoformat(),
        }

    def _check_file_exists(self, file_path: str) -> bool:
        """
        파일 존재 여부 확인

        Args:
            file_path: 파일 경로

        Returns:
            존재 여부
        """
        # 절대 경로로 변환
        if not os.path.isabs(file_path):
            file_path = self.project_path / file_path

        return os.path.isfile(file_path)

    def _analyze_file_structure(self, file_path: str) -> Dict:
        """
        파일 구조 분석

        Args:
            file_path: 파일 경로

        Returns:
            구조 정보
        """
        # 캐시 확인
        cache_key = str(file_path)
        if cache_key in self._structure_cache:
            return self._structure_cache[cache_key]

        # 절대 경로로 변환
        if not os.path.isabs(file_path):
            file_path = self.project_path / file_path

        try:
            # 파일 읽기
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 언어 감지
            language = self._detect_language(file_path)

            # 패턴 적용
            patterns = self.DEFINITION_PATTERNS.get(language, {})

            functions = []
            classes = []
            imports = []

            if "function" in patterns:
                func_pattern = re.compile(patterns["function"], re.MULTILINE)
                matches = func_pattern.findall(content)
                # 튜플일 경우 첫 번째 요소만 (JS/TS 패턴)
                for match in matches:
                    if isinstance(match, tuple):
                        func_name = next((m for m in match if m), None)
                        if func_name:
                            functions.append(func_name)
                    else:
                        functions.append(match)

            if "class" in patterns:
                class_pattern = re.compile(patterns["class"], re.MULTILINE)
                matches = class_pattern.findall(content)
                for match in matches:
                    if isinstance(match, tuple):
                        class_name = next((m for m in match if m), None)
                        if class_name:
                            classes.append(class_name)
                    else:
                        classes.append(match)

            if "import" in patterns:
                import_pattern = re.compile(patterns["import"], re.MULTILINE)
                matches = import_pattern.findall(content)
                imports = list(set(matches))  # 중복 제거

            structure = {
                "language": language,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "line_count": len(content.split("\n")),
            }

            # 캐시 저장
            self._structure_cache[cache_key] = structure

            return structure

        except Exception as e:
            print(f"Warning: Failed to analyze file structure: {e}")
            return {
                "language": "unknown",
                "functions": [],
                "classes": [],
                "imports": [],
                "error": str(e),
            }

    def _detect_language(self, file_path: str) -> str:
        """
        파일 언어 감지

        Args:
            file_path: 파일 경로

        Returns:
            언어 이름
        """
        ext = Path(file_path).suffix

        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".go": "go",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".rs": "rust",
        }

        return language_map.get(ext, "unknown")

    def _find_similar_files(self, file_path: str) -> List[str]:
        """
        유사한 파일 찾기

        Args:
            file_path: 파일 경로

        Returns:
            유사 파일 목록
        """
        # 파일명 추출
        file_name = Path(file_path).name
        name_without_ext = Path(file_path).stem

        similar_files = []

        # 같은 이름의 파일 찾기
        for ext in self.SUPPORTED_EXTENSIONS:
            pattern = f"**/{name_without_ext}{ext}"
            matches = list(self.project_path.glob(pattern))
            similar_files.extend([str(f.relative_to(self.project_path)) for f in matches])

        # 중복 제거 및 정렬
        similar_files = list(set(similar_files))
        similar_files.sort()

        return similar_files[:5]  # 최대 5개

    def get_project_stats(self) -> Dict:
        """
        프로젝트 통계

        Returns:
            통계 정보
        """
        structure = self.analyze_project_structure()

        total_functions = 0
        total_classes = 0

        # 모든 파일 분석
        for ext, files in structure["files_by_extension"].items():
            for file_path in files:
                file_structure = self._analyze_file_structure(file_path)
                total_functions += len(file_structure.get("functions", []))
                total_classes += len(file_structure.get("classes", []))

        return {
            "total_files": structure["total_files"],
            "total_functions": total_functions,
            "total_classes": total_classes,
            "files_by_extension": {
                ext: len(files) for ext, files in structure["files_by_extension"].items()
            },
            "timestamp": datetime.now().isoformat(),
        }
