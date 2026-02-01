"""
Initial Scanner Module - Initial Context Scan System

프로젝트 전체를 스캔하여 Context Graph의 '빈 골격'을 생성합니다.

설계 원칙:
- P1: Global First, Deep Later (전체 구조 우선)
- P2: Structure over Semantics (구조 > 의미)
- P3: Zero-Token by Default (로컬 분석만, LLM 호출 없음)
- P4: Lazy Semantic Resolution (필요할 때만 깊이 분석)
- P5: Context Graph is Source of Truth

3-Phase 스캔 프로세스:
- Phase A: Global Shallow Scan (전수, 필수) - 모든 파일 구조 추출
- Phase B: Structural Linking (전수, 필수) - import/export 연결
- Phase C: Semantic Context (Lazy, 선택) - AI가 필요할 때만 실행
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from .ast_parser import (
    ASTParserFactory,
    ParseResult,
    resolve_import_path,
)
from .context_graph import (
    ContextEdge,
    ContextGraph,
    ContextMetadata,
    ContextNode,
    ContextStatus,
    EdgeRelation,
    SemanticLevel,
    get_context_graph,
)

logger = logging.getLogger(__name__)


class ScanMode(str, Enum):
    """스캔 모드"""

    FULL = "FULL"  # 전체 코드베이스 심층 분석 (토큰 소모 높음)
    LIGHT = "LIGHT"  # 핵심 파일만 스캔 (README, 진입점, 설정)
    NONE = "NONE"  # 스캔 건너뛰기


@dataclass
class ScanResult:
    """스캔 결과"""

    project_id: str
    project_path: str
    scan_mode: ScanMode
    success: bool
    files_scanned: int = 0
    files_failed: int = 0
    nodes_created: int = 0
    edges_created: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_path": self.project_path,
            "scan_mode": self.scan_mode.value,
            "success": self.success,
            "files_scanned": self.files_scanned,
            "files_failed": self.files_failed,
            "nodes_created": self.nodes_created,
            "edges_created": self.edges_created,
            "languages": self.languages,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class InitialScanner:
    """
    Initial Context Scanner

    프로젝트를 스캔하여 Context Graph를 생성합니다.

    사용법:
    ```python
    scanner = InitialScanner(project_id, project_path)
    result = scanner.scan(mode=ScanMode.FULL)
    ```
    """

    # 기본 무시 패턴
    DEFAULT_IGNORE_PATTERNS = {
        # 디렉토리
        "node_modules",
        ".git",
        ".svn",
        ".hg",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        ".nox",
        "venv",
        ".venv",
        "env",
        ".env",
        "virtualenv",
        ".virtualenv",
        "dist",
        "build",
        "target",
        ".next",
        ".nuxt",
        ".output",
        "out",
        ".cache",
        "coverage",
        ".coverage",
        "htmlcov",
        ".idea",
        ".vscode",
        ".vs",
        "*.egg-info",
        ".eggs",
        # 파일
        ".DS_Store",
        "Thumbs.db",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*.so",
        "*.dll",
        "*.dylib",
        "*.class",
        "*.o",
        "*.a",
        "*.lib",
        "*.exe",
        "*.log",
        "*.lock",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Pipfile.lock",
        "*.min.js",
        "*.min.css",
        "*.map",
        "*.chunk.js",
        "*.bundle.js",
    }

    # 소스 파일 확장자
    SOURCE_EXTENSIONS = {
        ".py",
        ".pyw",  # Python
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",  # JavaScript
        ".ts",
        ".tsx",
        ".mts",
        ".cts",  # TypeScript
        ".java",  # Java
        ".kt",
        ".kts",  # Kotlin
        ".go",  # Go
        ".rs",  # Rust
        ".rb",  # Ruby
        ".php",  # PHP
        ".c",
        ".h",  # C
        ".cpp",
        ".hpp",
        ".cc",
        ".cxx",  # C++
        ".cs",  # C#
        ".swift",  # Swift
        ".scala",  # Scala
        ".vue",  # Vue
        ".svelte",  # Svelte
    }

    # LIGHT 모드에서 스캔할 핵심 파일 패턴
    LIGHT_MODE_PATTERNS = {
        # 진입점
        "main.py",
        "app.py",
        "index.py",
        "__main__.py",
        "index.js",
        "index.ts",
        "main.js",
        "main.ts",
        "app.js",
        "app.ts",
        "server.js",
        "server.ts",
        "Main.java",
        "App.java",
        "main.go",
        "main.rs",
        # 설정
        "setup.py",
        "setup.cfg",
        "pyproject.toml",
        "package.json",
        "tsconfig.json",
        "jsconfig.json",
        "Cargo.toml",
        "go.mod",
        "build.gradle",
        "pom.xml",
        # 문서
        "README.md",
        "README.rst",
        "README.txt",
        "README",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        # 설정 파일
        "config.py",
        "config.js",
        "config.ts",
        "settings.py",
        "settings.js",
        "settings.ts",
        ".env.example",
    }

    def __init__(
        self,
        project_id: str,
        project_path: str,
        custom_ignore_patterns: Optional[Set[str]] = None,
        custom_extensions: Optional[Set[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ):
        """
        Args:
            project_id: 프로젝트 식별자
            project_path: 프로젝트 루트 경로
            custom_ignore_patterns: 추가 무시 패턴
            custom_extensions: 추가 소스 확장자
            progress_callback: 진행률 콜백 (current, total, message)
        """
        self.project_id = project_id
        self.project_path = Path(project_path).resolve()
        self.ignore_patterns = self.DEFAULT_IGNORE_PATTERNS.copy()
        self.source_extensions = self.SOURCE_EXTENSIONS.copy()
        self.progress_callback = progress_callback

        if custom_ignore_patterns:
            self.ignore_patterns.update(custom_ignore_patterns)
        if custom_extensions:
            self.source_extensions.update(custom_extensions)

        # .gitignore 파싱
        self._load_gitignore()

        # Context Graph
        self.graph = get_context_graph(project_id)

    def _load_gitignore(self) -> None:
        """프로젝트의 .gitignore 파일 로드"""
        gitignore_path = self.project_path / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # 간단한 패턴만 처리 (glob 패턴은 무시)
                            if not any(c in line for c in ["*", "?", "["]):
                                self.ignore_patterns.add(line.rstrip("/"))
            except Exception as e:
                logger.warning(f"Failed to load .gitignore: {e}")

    def _should_ignore(self, path: Path) -> bool:
        """경로가 무시 대상인지 확인"""
        name = path.name

        # 직접 매칭
        if name in self.ignore_patterns:
            return True

        # 숨김 파일/디렉토리 (. 시작)
        if name.startswith(".") and name not in {".env.example"}:
            return True

        # 확장자 패턴 매칭
        for pattern in self.ignore_patterns:
            if pattern.startswith("*."):
                ext = pattern[1:]  # *.pyc -> .pyc
                if name.endswith(ext):
                    return True

        # 상위 경로 확인
        for parent in path.parents:
            if parent.name in self.ignore_patterns:
                return True
            if parent == self.project_path:
                break

        return False

    def _is_source_file(self, path: Path) -> bool:
        """소스 파일인지 확인"""
        return path.suffix.lower() in self.source_extensions

    def _is_light_mode_file(self, path: Path) -> bool:
        """LIGHT 모드에서 스캔할 핵심 파일인지 확인"""
        return path.name in self.LIGHT_MODE_PATTERNS

    def _discover_files(self, mode: ScanMode) -> List[Path]:
        """스캔할 파일 목록 발견"""
        files = []

        if mode == ScanMode.NONE:
            return files

        for root, dirs, filenames in os.walk(self.project_path):
            root_path = Path(root)

            # 무시할 디렉토리 필터링
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]

            for filename in filenames:
                file_path = root_path / filename

                if self._should_ignore(file_path):
                    continue

                if mode == ScanMode.FULL:
                    # 모든 소스 파일
                    if self._is_source_file(file_path):
                        files.append(file_path)
                elif mode == ScanMode.LIGHT:
                    # 핵심 파일만
                    if self._is_light_mode_file(file_path):
                        files.append(file_path)

        return files

    def scan(self, mode: ScanMode = ScanMode.FULL) -> ScanResult:
        """
        프로젝트 스캔 실행

        Args:
            mode: 스캔 모드 (FULL, LIGHT, NONE)

        Returns:
            ScanResult: 스캔 결과
        """
        import time

        start_time = time.time()

        result = ScanResult(
            project_id=self.project_id,
            project_path=str(self.project_path),
            scan_mode=mode,
            success=True,
        )

        if mode == ScanMode.NONE:
            result.completed_at = datetime.now(timezone.utc).isoformat()
            result.duration_seconds = time.time() - start_time
            return result

        try:
            # Phase A: 파일 발견 및 구조 추출
            logger.info(f"[Phase A] Starting Global Shallow Scan for {self.project_id}")
            files = self._discover_files(mode)
            total_files = len(files)

            if self.progress_callback:
                self.progress_callback(0, total_files, "Starting scan...")

            # Phase A: Global Shallow Scan
            for i, file_path in enumerate(files):
                try:
                    self._scan_file(file_path, result)
                    if self.progress_callback:
                        self.progress_callback(i + 1, total_files, f"Scanning: {file_path.name}")
                except Exception as e:
                    result.files_failed += 1
                    result.errors.append(f"Error scanning {file_path}: {str(e)}")
                    logger.warning(f"Error scanning {file_path}: {e}")

            # Phase B: Structural Linking
            logger.info(f"[Phase B] Starting Structural Linking for {self.project_id}")
            if self.progress_callback:
                self.progress_callback(total_files, total_files, "Linking imports...")

            self._link_imports(result)

            logger.info(
                f"Scan completed: {result.nodes_created} nodes, {result.edges_created} edges"
            )

        except Exception as e:
            result.success = False
            result.errors.append(f"Scan failed: {str(e)}")
            logger.error(f"Scan failed for {self.project_id}: {e}")

        result.completed_at = datetime.now(timezone.utc).isoformat()
        result.duration_seconds = time.time() - start_time

        return result

    def _scan_file(self, file_path: Path, result: ScanResult) -> Optional[ContextNode]:
        """
        개별 파일 스캔 (Phase A)

        Args:
            file_path: 파일 경로
            result: 스캔 결과 객체

        Returns:
            생성된 ContextNode 또는 None
        """
        # 파일 정보 수집
        try:
            stat = file_path.stat()
            file_size = stat.st_size
        except OSError:
            file_size = 0

        # AST 파싱
        parse_result = ASTParserFactory.parse_file(str(file_path))

        # Context ID 생성
        context_id = ContextGraph.create_context_id(str(self.project_path), str(file_path))
        language = ContextGraph.get_language_from_extension(str(file_path))
        file_hash = ContextGraph.compute_file_hash(str(file_path))

        # 메타데이터 생성
        metadata = ContextMetadata(
            exports=parse_result.exports,
            imports=[imp.get("name", "") for imp in parse_result.imports if imp.get("name")],
            classes=parse_result.classes,
            functions=parse_result.functions,
            interfaces=parse_result.interfaces,
            types=parse_result.types,
            has_default_export=parse_result.has_default_export,
            parse_error=parse_result.parse_error,
            error_message=parse_result.error_message,
            file_hash=file_hash,
            ast_hash=parse_result.ast_hash,
            line_count=parse_result.line_count,
            size_bytes=file_size,
        )

        # Context Node 생성
        node = ContextNode(
            context_id=context_id,
            file_path=str(file_path),
            language=language,
            semantic_level=SemanticLevel.SHALLOW,
            status=ContextStatus.ACTIVE,
            metadata=metadata,
        )

        # 그래프에 추가
        self.graph.add_node(node)

        # 결과 업데이트
        result.files_scanned += 1
        result.nodes_created += 1
        result.languages[language] = result.languages.get(language, 0) + 1

        if parse_result.parse_error:
            result.warnings.append(
                f"Parse warning for {file_path.name}: {parse_result.error_message}"
            )

        return node

    def _link_imports(self, result: ScanResult) -> None:
        """
        Import 연결 생성 (Phase B)

        모든 노드의 import를 분석하여 edge 생성
        """
        for node in list(self.graph.nodes.values()):
            # import 정보 추출
            imports = node.metadata.imports
            if not imports:
                continue

            # 파싱 결과에서 원본 import 정보 가져오기
            parse_result = ASTParserFactory.parse_file(node.file_path)

            for imp in parse_result.imports:
                module = imp.get("module", "")
                if not module:
                    continue

                # import 경로 해결
                resolved_path = resolve_import_path(
                    node.file_path, module, str(self.project_path), node.language
                )

                if resolved_path:
                    # 해결된 파일의 context_id 찾기
                    target_context_id = ContextGraph.create_context_id(
                        str(self.project_path), resolved_path
                    )

                    # 타겟 노드가 존재하는지 확인
                    if target_context_id in self.graph.nodes:
                        # Edge 생성
                        edge = ContextEdge(
                            from_context=node.context_id,
                            to_context=target_context_id,
                            relation=EdgeRelation.IMPORTS,
                            import_name=imp.get("name"),
                        )
                        self.graph.add_edge(edge)
                        result.edges_created += 1

    def rescan(self) -> ScanResult:
        """
        재스캔 (변경된 파일만)

        Returns:
            ScanResult: 스캔 결과
        """
        import time

        start_time = time.time()

        result = ScanResult(
            project_id=self.project_id,
            project_path=str(self.project_path),
            scan_mode=ScanMode.FULL,
            success=True,
        )

        try:
            # 기존 노드들을 stale로 표시
            self.graph.mark_all_stale()

            # 전체 파일 발견
            files = self._discover_files(ScanMode.FULL)

            # 각 파일 스캔
            for file_path in files:
                try:
                    node = self._scan_file(file_path, result)
                    if node:
                        # 스캔된 파일은 다시 active로
                        node.status = ContextStatus.ACTIVE
                except Exception as e:
                    result.files_failed += 1
                    result.errors.append(f"Error scanning {file_path}: {str(e)}")

            # stale 노드 제거 (삭제된 파일)
            removed_count = self.graph.remove_stale_nodes()
            if removed_count > 0:
                result.warnings.append(f"Removed {removed_count} stale nodes (deleted files)")

            # Import 재연결
            self._link_imports(result)

        except Exception as e:
            result.success = False
            result.errors.append(f"Rescan failed: {str(e)}")

        result.completed_at = datetime.now(timezone.utc).isoformat()
        result.duration_seconds = time.time() - start_time

        return result

    def get_scan_estimate(self, mode: ScanMode) -> Dict[str, Any]:
        """
        스캔 예상 정보 반환 (토큰 경고용)

        Args:
            mode: 스캔 모드

        Returns:
            예상 정보 딕셔너리
        """
        files = self._discover_files(mode)
        total_size = 0
        languages = {}

        for file_path in files:
            try:
                total_size += file_path.stat().st_size
            except OSError:
                pass

            lang = ContextGraph.get_language_from_extension(str(file_path))
            languages[lang] = languages.get(lang, 0) + 1

        # 토큰 추정 (대략 4자 = 1토큰)
        estimated_tokens = total_size // 4

        return {
            "scan_mode": mode.value,
            "file_count": len(files),
            "total_size_bytes": total_size,
            "total_size_readable": self._format_size(total_size),
            "estimated_tokens": estimated_tokens,
            "languages": languages,
            "warning": mode == ScanMode.FULL and estimated_tokens > 50000,
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """바이트 크기를 읽기 좋은 형식으로 변환"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"


# 편의 함수
def scan_project(
    project_id: str,
    project_path: str,
    mode: ScanMode = ScanMode.FULL,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> ScanResult:
    """
    프로젝트 스캔 편의 함수

    Args:
        project_id: 프로젝트 식별자
        project_path: 프로젝트 루트 경로
        mode: 스캔 모드
        progress_callback: 진행률 콜백

    Returns:
        ScanResult: 스캔 결과
    """
    scanner = InitialScanner(project_id, project_path, progress_callback=progress_callback)
    return scanner.scan(mode)


def rescan_project(project_id: str, project_path: str, force_full: bool = False) -> Dict[str, Any]:
    """
    프로젝트 재스캔 편의 함수 (변경 사항만)

    Args:
        project_id: 프로젝트 식별자
        project_path: 프로젝트 루트 경로
        force_full: 강제 전체 재스캔 여부 (기본: False)

    Returns:
        Dict: 스캔 결과 (memory_manager 호환을 위해 Dict 반환)
    """
    scanner = InitialScanner(project_id, project_path)
    if force_full:
        # 강제 전체 스캔
        result = scanner.scan(ScanMode.FULL)
    else:
        # 증분 재스캔
        result = scanner.rescan()

    # Dict로 변환하여 반환
    return result.to_dict()


def scan_project_deep(
    project_id: str, project_path: str, scan_mode: str, file_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Context Graph 기반 프로젝트 심층 스캔 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        project_path: 프로젝트 경로
        scan_mode: 스캔 모드 ('FULL', 'LIGHT', 'NONE')
        file_patterns: 스캔할 파일 패턴 (무시됨 - 호환성 목적)

    Returns:
        스캔 결과 딕셔너리
    """
    # ScanMode enum 변환
    mode_map = {"FULL": ScanMode.FULL, "LIGHT": ScanMode.LIGHT, "NONE": ScanMode.NONE}
    mode = mode_map.get(scan_mode, ScanMode.LIGHT)

    # 스캔 실행
    result = scan_project(project_id, project_path, mode)

    # ScanResult를 Dict으로 변환 (to_dict 메서드 사용)
    return result.to_dict()


def get_scan_estimate(project_path: str, scan_mode: str) -> Dict[str, Any]:
    """
    스캔 예상 정보 조회 편의 함수 (MCP 인터페이스)

    Args:
        project_path: 프로젝트 루트 경로
        scan_mode: 스캔 모드 ('FULL' or 'LIGHT')

    Returns:
        예상 정보 딕셔너리
    """
    # ScanMode enum 변환
    mode_map = {"FULL": ScanMode.FULL, "LIGHT": ScanMode.LIGHT}
    mode = mode_map.get(scan_mode, ScanMode.LIGHT)

    # project_id는 임시로 "temp" 사용 (추정에는 영향 없음)
    scanner = InitialScanner("temp", project_path)
    return scanner.get_scan_estimate(mode)
