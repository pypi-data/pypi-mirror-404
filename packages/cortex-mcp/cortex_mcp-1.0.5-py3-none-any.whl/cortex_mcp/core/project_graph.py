"""
Cortex MCP - Project Graph

프로젝트 전체 구조를 그래프로 관리하여 파일 간 의존성 분석

기능:
- 파일 간 의존성 파악
- 수정 시 영향 범위 분석
- AI에게 프로젝트 맥락 제공
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import portalocker

from .ast_analyzer import ASTAnalyzer, get_ast_analyzer

logger = logging.getLogger(__name__)


class ProjectGraph:
    """
    프로젝트 지식 그래프

    프로젝트의 파일 구조, import 관계, 함수/클래스 정의를 추적하여
    변경 영향 분석 및 맥락 제공
    """

    # 분석 대상 확장자
    SUPPORTED_EXTENSIONS = {
        ".py", ".pyw",  # Python
        ".js", ".jsx", ".mjs",  # JavaScript
        ".ts", ".tsx",  # TypeScript
    }

    def __init__(self, project_id: str, project_root: Optional[Path] = None, memory_dir: Optional[Path] = None):
        """
        Args:
            project_id: 프로젝트 ID
            project_root: 프로젝트 루트 디렉토리
            memory_dir: 메모리 저장 디렉토리 (기본: ~/.cortex/memory)
        """
        self.project_id = project_id
        self.project_root = project_root

        if memory_dir is None:
            memory_dir = Path.home() / ".cortex" / "memory"

        self.memory_dir = memory_dir / project_id
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.graph_file = self.memory_dir / "_project_graph.json"
        self._graph = self._load_graph()
        self._analyzer = get_ast_analyzer()

    def _load_graph(self) -> Dict:
        """그래프 파일 로드"""
        if self.graph_file.exists():
            try:
                with open(self.graph_file, "r", encoding="utf-8") as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    data = json.load(f)
                    portalocker.unlock(f)
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"[ProjectGraph] 그래프 로드 실패: {e}")

        return {
            "files": {},
            "dependencies": {},
            "reverse_dependencies": {},
            "last_scan": None,
        }

    def _save_graph(self) -> None:
        """그래프 파일 저장"""
        try:
            with open(self.graph_file, "w", encoding="utf-8") as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                json.dump(self._graph, f, ensure_ascii=False, indent=2)
                portalocker.unlock(f)
        except IOError as e:
            logger.error(f"[ProjectGraph] 그래프 저장 실패: {e}")

    def scan_project(self, root_path: Optional[Path] = None, exclude_patterns: Optional[List[str]] = None) -> Dict:
        """
        프로젝트 전체 스캔

        Args:
            root_path: 스캔할 루트 경로 (미지정 시 project_root 사용)
            exclude_patterns: 제외할 패턴 (예: ["__pycache__", "node_modules"])

        Returns:
            스캔 결과 요약
        """
        if root_path is None:
            root_path = self.project_root

        if root_path is None:
            logger.error("[ProjectGraph] 프로젝트 루트 미지정")
            return {"error": "프로젝트 루트가 지정되지 않았습니다"}

        root_path = Path(root_path)
        if not root_path.exists():
            return {"error": f"경로를 찾을 수 없음: {root_path}"}

        if exclude_patterns is None:
            exclude_patterns = [
                "__pycache__", "node_modules", ".git", ".venv", "venv",
                "dist", "build", ".tox", ".pytest_cache", ".mypy_cache",
            ]

        # 그래프 초기화
        self._graph["files"] = {}
        self._graph["dependencies"] = {}
        self._graph["reverse_dependencies"] = {}

        scanned_count = 0
        error_count = 0

        # 파일 스캔
        for file_path in root_path.rglob("*"):
            # 디렉토리 건너뛰기
            if file_path.is_dir():
                continue

            # 제외 패턴 체크
            if any(pattern in str(file_path) for pattern in exclude_patterns):
                continue

            # 지원 확장자 체크
            if file_path.suffix not in self.SUPPORTED_EXTENSIONS:
                continue

            try:
                self._analyze_file(file_path, root_path)
                scanned_count += 1
            except Exception as e:
                logger.warning(f"[ProjectGraph] 파일 분석 실패: {file_path} - {e}")
                error_count += 1

        # 역방향 의존성 구축
        self._build_reverse_dependencies()

        self._graph["last_scan"] = datetime.now(timezone.utc).isoformat()
        self._save_graph()

        logger.info(f"[ProjectGraph] 스캔 완료: {scanned_count}개 파일, {error_count}개 오류")

        return {
            "scanned_files": scanned_count,
            "error_count": error_count,
            "total_files": len(self._graph["files"]),
            "last_scan": self._graph["last_scan"],
        }

    def _analyze_file(self, file_path: Path, root_path: Path) -> None:
        """단일 파일 분석 및 그래프 추가"""
        relative_path = str(file_path.relative_to(root_path))

        # AST 분석
        analysis = self._analyzer.analyze_file(str(file_path))

        # 파일 정보 저장
        self._graph["files"][relative_path] = {
            "functions": [f["name"] for f in analysis.get("functions", [])],
            "classes": [c["name"] for c in analysis.get("classes", [])],
            "imports": analysis.get("imports", []),
            "valid_syntax": analysis.get("valid_syntax", True),
            "last_modified": datetime.now(timezone.utc).isoformat(),
        }

        # 의존성 추출
        dependencies = self._extract_dependencies(analysis, relative_path, root_path)
        if dependencies:
            self._graph["dependencies"][relative_path] = dependencies

    def _extract_dependencies(self, analysis: Dict, current_file: str, root_path: Path) -> List[str]:
        """import 문에서 의존성 추출"""
        dependencies = []

        for imp in analysis.get("imports", []):
            module = imp.get("module", "")

            # 상대 import 처리
            if imp.get("type") == "from_import" and module.startswith("."):
                # 상대 경로를 절대 경로로 변환 시도
                dep_path = self._resolve_relative_import(current_file, module)
                if dep_path:
                    dependencies.append(dep_path)
            else:
                # 프로젝트 내부 모듈인지 확인
                potential_path = self._module_to_path(module, root_path)
                if potential_path and potential_path in self._graph["files"]:
                    dependencies.append(potential_path)

        return list(set(dependencies))

    def _resolve_relative_import(self, current_file: str, relative_module: str) -> Optional[str]:
        """상대 import를 경로로 변환"""
        current_dir = str(Path(current_file).parent)

        # 점 개수로 상위 디렉토리 결정
        dots = len(relative_module) - len(relative_module.lstrip("."))
        module_name = relative_module.lstrip(".")

        # 상위 디렉토리로 이동
        parts = current_dir.split("/")
        if dots > 1 and len(parts) >= dots - 1:
            parts = parts[:-(dots - 1)]

        if module_name:
            target = "/".join(parts) + "/" + module_name.replace(".", "/") + ".py"
        else:
            target = "/".join(parts) + "/__init__.py"

        return target if target in self._graph.get("files", {}) else None

    def _module_to_path(self, module: str, root_path: Path) -> Optional[str]:
        """모듈명을 파일 경로로 변환"""
        # 예: cortex_mcp.core.memory_manager -> cortex_mcp/core/memory_manager.py
        path_parts = module.split(".")
        potential_paths = [
            "/".join(path_parts) + ".py",
            "/".join(path_parts) + "/__init__.py",
        ]

        for path in potential_paths:
            if (root_path / path).exists():
                return path

        return None

    def _build_reverse_dependencies(self) -> None:
        """역방향 의존성 구축 (이 파일을 import하는 파일들)"""
        reverse = defaultdict(list)

        for file_path, deps in self._graph["dependencies"].items():
            for dep in deps:
                reverse[dep].append(file_path)

        self._graph["reverse_dependencies"] = dict(reverse)

    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        파일 정보 조회

        Args:
            file_path: 파일 경로 (상대 경로)

        Returns:
            파일 정보 딕셔너리
        """
        return self._graph["files"].get(file_path)

    def get_dependencies(self, file_path: str) -> List[str]:
        """
        파일의 의존성 목록 반환 (이 파일이 import하는 파일들)

        Args:
            file_path: 파일 경로

        Returns:
            의존성 파일 목록
        """
        return self._graph["dependencies"].get(file_path, [])

    def get_dependents(self, file_path: str) -> List[str]:
        """
        이 파일을 import하는 파일 목록 반환

        Args:
            file_path: 파일 경로

        Returns:
            이 파일에 의존하는 파일 목록
        """
        return self._graph["reverse_dependencies"].get(file_path, [])

    def get_impact_analysis(self, file_path: str, max_depth: int = 3) -> Dict:
        """
        파일 수정 시 영향 범위 분석

        Args:
            file_path: 수정할 파일 경로
            max_depth: 최대 탐색 깊이

        Returns:
            {
                "directly_affected": [...],  # 직접 의존하는 파일
                "transitively_affected": [...],  # 간접적으로 영향 받는 파일
                "total_affected": int,
                "impact_level": "low" | "medium" | "high"
            }
        """
        directly_affected = set(self.get_dependents(file_path))
        all_affected = set(directly_affected)

        # BFS로 간접 영향 탐색
        current_level = directly_affected
        for _ in range(max_depth - 1):
            next_level = set()
            for f in current_level:
                dependents = self.get_dependents(f)
                for d in dependents:
                    if d not in all_affected:
                        next_level.add(d)
                        all_affected.add(d)
            current_level = next_level
            if not current_level:
                break

        transitively_affected = all_affected - directly_affected

        # 영향 수준 결정
        total = len(all_affected)
        if total == 0:
            impact_level = "low"
        elif total <= 3:
            impact_level = "low"
        elif total <= 10:
            impact_level = "medium"
        else:
            impact_level = "high"

        return {
            "directly_affected": sorted(list(directly_affected)),
            "transitively_affected": sorted(list(transitively_affected)),
            "total_affected": total,
            "impact_level": impact_level,
        }

    def get_context_for_file(self, file_path: str) -> Dict:
        """
        파일 작업 시 관련 맥락 제공

        Args:
            file_path: 작업할 파일 경로

        Returns:
            {
                "file_info": {...},
                "dependencies": [...],
                "dependents": [...],
                "related_files": [...],
                "context_summary": str
            }
        """
        file_info = self.get_file_info(file_path)
        dependencies = self.get_dependencies(file_path)
        dependents = self.get_dependents(file_path)

        # 관련 파일 (같은 디렉토리)
        file_dir = str(Path(file_path).parent)
        related_files = [
            f for f in self._graph["files"].keys()
            if str(Path(f).parent) == file_dir and f != file_path
        ]

        # 맥락 요약 생성
        summary_parts = []

        if file_info:
            if file_info.get("functions"):
                summary_parts.append(f"함수: {', '.join(file_info['functions'][:5])}")
            if file_info.get("classes"):
                summary_parts.append(f"클래스: {', '.join(file_info['classes'][:5])}")

        if dependencies:
            summary_parts.append(f"의존성: {len(dependencies)}개 파일")

        if dependents:
            summary_parts.append(f"영향받는 파일: {len(dependents)}개")

        return {
            "file_info": file_info,
            "dependencies": dependencies,
            "dependents": dependents,
            "related_files": related_files[:10],
            "context_summary": " | ".join(summary_parts) if summary_parts else "정보 없음",
        }

    def validate_modification(self, file_path: str, added_imports: Optional[List[str]] = None) -> Dict:
        """
        수정이 프로젝트 구조와 일치하는지 검증

        Args:
            file_path: 수정할 파일 경로
            added_imports: 추가된 import 목록

        Returns:
            {
                "valid": bool,
                "warnings": [...],
                "suggestions": [...]
            }
        """
        result = {
            "valid": True,
            "warnings": [],
            "suggestions": [],
        }

        # 파일 존재 확인
        if file_path not in self._graph["files"]:
            result["warnings"].append({
                "type": "unknown_file",
                "message": f"파일이 프로젝트 그래프에 없음: {file_path}",
            })

        # 추가된 import 검증
        if added_imports:
            for imp in added_imports:
                # 순환 의존성 체크
                if self._would_create_cycle(file_path, imp):
                    result["valid"] = False
                    result["warnings"].append({
                        "type": "circular_dependency",
                        "message": f"순환 의존성 발생: {file_path} <-> {imp}",
                    })

        # 영향 범위 분석
        impact = self.get_impact_analysis(file_path)
        if impact["impact_level"] == "high":
            result["warnings"].append({
                "type": "high_impact",
                "message": f"이 파일 수정 시 {impact['total_affected']}개 파일에 영향",
            })
            result["suggestions"].append("변경 전 충분한 테스트를 권장합니다")

        return result

    def _would_create_cycle(self, from_file: str, to_file: str) -> bool:
        """새 import 추가 시 순환 의존성 발생 여부 확인"""
        # to_file이 from_file에 의존하는지 확인 (직접 또는 간접)
        visited = set()
        stack = [to_file]

        while stack:
            current = stack.pop()
            if current == from_file:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self.get_dependencies(current))

        return False

    def get_project_summary(self) -> Dict:
        """
        프로젝트 전체 요약

        Returns:
            프로젝트 요약 정보
        """
        total_files = len(self._graph["files"])
        total_functions = sum(
            len(f.get("functions", [])) for f in self._graph["files"].values()
        )
        total_classes = sum(
            len(f.get("classes", [])) for f in self._graph["files"].values()
        )

        # 가장 많이 import되는 파일
        most_imported = sorted(
            self._graph["reverse_dependencies"].items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )[:5]

        return {
            "total_files": total_files,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "last_scan": self._graph.get("last_scan"),
            "most_imported_files": [
                {"file": f, "imported_by": len(deps)}
                for f, deps in most_imported
            ],
        }

    def get_context_for_ai(self) -> str:
        """
        AI에게 제공할 프로젝트 컨텍스트 생성

        Returns:
            프로젝트 구조 요약 문자열
        """
        summary = self.get_project_summary()

        lines = [
            f"프로젝트 구조: {summary['total_files']}개 파일, "
            f"{summary['total_functions']}개 함수, {summary['total_classes']}개 클래스",
        ]

        if summary["most_imported_files"]:
            lines.append("핵심 파일 (가장 많이 import됨):")
            for item in summary["most_imported_files"][:3]:
                lines.append(f"  - {item['file']} ({item['imported_by']}개 파일에서 사용)")

        return "\n".join(lines)

    def clear(self) -> None:
        """그래프 초기화"""
        self._graph = {
            "files": {},
            "dependencies": {},
            "reverse_dependencies": {},
            "last_scan": None,
        }
        self._save_graph()
        logger.info("[ProjectGraph] 그래프 초기화 완료")


# 싱글톤 인스턴스 관리
_graph_instances: Dict[str, ProjectGraph] = {}


def get_project_graph(
    project_id: str,
    project_root: Optional[Path] = None,
    memory_dir: Optional[Path] = None,
) -> ProjectGraph:
    """
    ProjectGraph 싱글톤 인스턴스 반환

    Args:
        project_id: 프로젝트 ID
        project_root: 프로젝트 루트
        memory_dir: 메모리 디렉토리

    Returns:
        ProjectGraph 인스턴스
    """
    if project_id not in _graph_instances:
        _graph_instances[project_id] = ProjectGraph(project_id, project_root, memory_dir)

    return _graph_instances[project_id]
