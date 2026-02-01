"""
Phase 9.4: Initial Codebase Scan

목적: 기존 코드베이스에서 Evidence 추출
설계: Maria Silva (Performance Engineer, Netflix)
"""

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

from .evidence_graph_v2 import Evidence, EvidenceType, get_evidence_graph_v2

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """스캔된 파일 정보"""
    file_path: str
    file_size: int
    language: str
    last_modified: str
    functions: List[tuple]  # (name, signature)
    classes: List[tuple]    # (name, signature)
    imports: List[str]


class InitialScanner:
    """
    기존 코드베이스 스캔

    Maria Silva's Performance Strategy:
    1. 허용된 확장자만 스캔 (.py, .js, .ts 등)
    2. 제외 디렉토리 필터링 (node_modules, .git, __pycache__ 등)
    3. 배치 처리 (1000개씩)
    4. 파일 크기 제한 (10MB 초과 시 스킵)
    """

    # 허용된 파일 확장자
    ALLOWED_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.cpp', '.c', '.h', '.hpp'}

    # 제외 디렉토리
    EXCLUDED_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        '.env', 'dist', 'build', 'target', '.next', '.nuxt',
        'coverage', '.pytest_cache', '.mypy_cache', 'logs',
        'vendor', 'tmp', 'temp', '.idea', '.vscode'
    }

    # 파일 크기 제한 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(self, project_path: str):
        """
        Args:
            project_path: 프로젝트 루트 경로
        """
        self.project_path = Path(project_path)
        self._scanned_files: List[FileInfo] = []

    def scan_directory(self, max_files: int = 10000) -> Dict[str, int]:
        """
        디렉토리 재귀 스캔

        Args:
            max_files: 최대 스캔 파일 수

        Returns:
            통계 딕셔너리
        """
        if not self.project_path.exists():
            logger.error(f"Project path does not exist: {self.project_path}")
            return {"files": 0, "evidences": 0}

        logger.info(f"[Phase 9.4] Starting initial scan: {self.project_path}")

        scanned_count = 0
        skipped_count = 0

        for root, dirs, files in os.walk(self.project_path):
            # 제외 디렉토리 필터링 (in-place 수정)
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]

            for file_name in files:
                if scanned_count >= max_files:
                    logger.info(f"[Phase 9.4] Reached max files limit: {max_files}")
                    break

                file_path = Path(root) / file_name
                file_ext = file_path.suffix

                # 확장자 체크
                if file_ext not in self.ALLOWED_EXTENSIONS:
                    continue

                # 파일 크기 체크
                try:
                    file_size = file_path.stat().st_size
                    if file_size > self.MAX_FILE_SIZE:
                        logger.debug(f"Skipping large file: {file_path} ({file_size} bytes)")
                        skipped_count += 1
                        continue
                except Exception as e:
                    logger.warning(f"Cannot stat file: {file_path} - {e}")
                    continue

                # 파일 스캔
                file_info = self._scan_file(file_path)
                if file_info:
                    self._scanned_files.append(file_info)
                    scanned_count += 1

            if scanned_count >= max_files:
                break

        logger.info(f"[Phase 9.4] Scanned {scanned_count} files, skipped {skipped_count}")

        return {
            "files": scanned_count,
            "skipped": skipped_count,
            "evidences": 0  # 업데이트 예정
        }

    def _scan_file(self, file_path: Path) -> Optional[FileInfo]:
        """
        단일 파일 스캔

        Args:
            file_path: 파일 경로

        Returns:
            FileInfo 또는 None
        """
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            stat = file_path.stat()

            # 언어 감지
            language = self._detect_language(file_path.suffix)

            # 함수 추출
            functions = self._extract_functions(content, language)

            # 클래스 추출
            classes = self._extract_classes(content, language)

            # import 문 추출
            imports = self._extract_imports(content, language)

            return FileInfo(
                file_path=str(file_path.relative_to(self.project_path)),
                file_size=stat.st_size,
                language=language,
                last_modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                functions=functions,
                classes=classes,
                imports=imports
            )

        except Exception as e:
            logger.error(f"Failed to scan file: {file_path} - {e}")
            return None

    def _detect_language(self, ext: str) -> str:
        """파일 확장자로 언어 감지"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.go': 'go',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
        }
        return ext_map.get(ext, 'unknown')

    def _extract_functions(self, content: str, language: str) -> List[tuple]:
        """함수 정의 추출"""
        functions = []

        if language == 'python':
            # Python: def function_name(...)
            pattern = r'^\s*def\s+(\w+)\s*\([^)]*\)'
            for match in re.finditer(pattern, content, re.MULTILINE):
                func_name = match.group(1)
                func_signature = match.group(0).strip()
                functions.append((func_name, func_signature))

        elif language in ('javascript', 'typescript'):
            # JS/TS: function name(...) or const name = (...) =>
            pattern = r'^\s*(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)'
            for match in re.finditer(pattern, content, re.MULTILINE):
                func_name = match.group(1) or match.group(2)
                if func_name:
                    functions.append((func_name, match.group(0).strip()))

        return functions

    def _extract_classes(self, content: str, language: str) -> List[tuple]:
        """클래스 정의 추출"""
        classes = []

        if language == 'python':
            # Python: class ClassName
            pattern = r'^\s*class\s+(\w+)'
            for match in re.finditer(pattern, content, re.MULTILINE):
                class_name = match.group(1)
                classes.append((class_name, match.group(0).strip()))

        elif language in ('javascript', 'typescript'):
            # JS/TS: class ClassName
            pattern = r'^\s*class\s+(\w+)'
            for match in re.finditer(pattern, content, re.MULTILINE):
                class_name = match.group(1)
                classes.append((class_name, match.group(0).strip()))

        return classes

    def _extract_imports(self, content: str, language: str) -> List[str]:
        """import 문 추출"""
        imports = []

        if language == 'python':
            # Python: import ... or from ... import ...
            pattern = r'^\s*(?:import|from)\s+[\w\.]+(?:\s+import\s+.+)?'
            for match in re.finditer(pattern, content, re.MULTILINE):
                imports.append(match.group(0).strip())

        elif language in ('javascript', 'typescript'):
            # JS/TS: import ... from '...'
            pattern = r'^\s*import\s+.*from\s+[\'"].*[\'"]'
            for match in re.finditer(pattern, content, re.MULTILINE):
                imports.append(match.group(0).strip())

        return imports

    def populate_evidence_graph(self, batch_size: int = 1000) -> Dict[str, int]:
        """
        Evidence Graph에 스캔 결과 추가

        Args:
            batch_size: 배치 크기

        Returns:
            통계 딕셔너리
        """
        graph = get_evidence_graph_v2()
        timestamp = datetime.now(timezone.utc).isoformat()

        all_evidences = []

        for file_info in self._scanned_files:
            # 1. FILE_EXISTS Evidence
            file_evidence = Evidence(
                evidence_id=f"scan:file:{file_info.file_path}",
                evidence_type=EvidenceType.FILE_EXISTS,
                content=f"File exists: {file_info.file_path}",
                source=f"scan:{file_info.file_path}",
                timestamp=file_info.last_modified,
                confidence=1.0,
                metadata={
                    "file_size": file_info.file_size,
                    "language": file_info.language,
                }
            )
            all_evidences.append(file_evidence)

            # 2. FUNCTION_SIGNATURE Evidence
            for func_name, func_signature in file_info.functions:
                func_evidence = Evidence(
                    evidence_id=f"scan:func:{file_info.file_path}:{func_name}",
                    evidence_type=EvidenceType.FUNCTION_SIGNATURE,
                    content=func_signature,
                    source=f"scan:{file_info.file_path}",
                    timestamp=timestamp,
                    confidence=0.9,
                    metadata={
                        "function_name": func_name,
                        "file_path": file_info.file_path,
                    }
                )
                all_evidences.append(func_evidence)

            # 3. CLASS_DEFINITION Evidence
            for class_name, class_signature in file_info.classes:
                class_evidence = Evidence(
                    evidence_id=f"scan:class:{file_info.file_path}:{class_name}",
                    evidence_type=EvidenceType.CLASS_DEFINITION,
                    content=class_signature,
                    source=f"scan:{file_info.file_path}",
                    timestamp=timestamp,
                    confidence=0.9,
                    metadata={
                        "class_name": class_name,
                        "file_path": file_info.file_path,
                    }
                )
                all_evidences.append(class_evidence)

            # 4. IMPORT_STATEMENT Evidence
            for import_stmt in file_info.imports:
                import_evidence = Evidence(
                    evidence_id=f"scan:import:{file_info.file_path}:{hash(import_stmt)}",
                    evidence_type=EvidenceType.IMPORT_STATEMENT,
                    content=import_stmt,
                    source=f"scan:{file_info.file_path}",
                    timestamp=timestamp,
                    confidence=0.95,
                    metadata={
                        "file_path": file_info.file_path,
                    }
                )
                all_evidences.append(import_evidence)

        # 배치 추가
        added_count = 0
        for i in range(0, len(all_evidences), batch_size):
            batch = all_evidences[i:i + batch_size]
            added_count += graph.add_evidence_batch(batch)
            logger.info(f"[Phase 9.4] Added batch {i//batch_size + 1}: {added_count}/{len(all_evidences)}")

        logger.info(f"[Phase 9.4] Total evidences added: {added_count}")

        return {
            "files": len(self._scanned_files),
            "evidences": added_count,
        }


def populate_from_scan(project_path: str, max_files: int = 10000) -> Dict[str, int]:
    """
    프로젝트 스캔 후 Evidence Graph 채우기

    Args:
        project_path: 프로젝트 루트 경로
        max_files: 최대 스캔 파일 수

    Returns:
        통계 딕셔너리
    """
    try:
        scanner = InitialScanner(project_path)

        # 1. 디렉토리 스캔
        scan_stats = scanner.scan_directory(max_files=max_files)
        logger.info(f"[Phase 9.4] Scan completed: {scan_stats}")

        # 2. Evidence Graph 채우기
        populate_stats = scanner.populate_evidence_graph()
        logger.info(f"[Phase 9.4] Populate completed: {populate_stats}")

        return populate_stats

    except Exception as e:
        logger.error(f"[Phase 9.4] Failed to populate from scan: {e}")
        return {"files": 0, "evidences": 0}
