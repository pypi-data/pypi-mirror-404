"""
Cortex MCP - Context Loader

Context 로딩 및 압축 관리:
- Smart Context 로딩 (Pro 이상)
- Context 압축/해제
- RAG 검색
- Evidence 수집
"""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .file_io import FileIO

logger = logging.getLogger(__name__)

# Context Manager import (Pro+)
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from context_manager import ContextManager
    CONTEXT_MANAGER_AVAILABLE = True
except ImportError:
    CONTEXT_MANAGER_AVAILABLE = False
    ContextManager = None

# RAG Engine import
try:
    from rag_engine import RAGEngine
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    RAGEngine = None


class ContextLoader:
    """Context 로딩 및 압축 담당"""

    def __init__(
        self,
        memory_dir: Path,
        file_io: FileIO,
        smart_context_enabled: bool = False,
        rag_engine: Optional[Any] = None,
    ):
        """
        Args:
            memory_dir: 메모리 저장 디렉토리
            file_io: 파일 I/O 유틸리티
            smart_context_enabled: Smart Context 기능 활성화 여부 (Pro+)
            rag_engine: RAG 검색 엔진 (선택적)
        """
        self.memory_dir = memory_dir
        self.file_io = file_io
        self.smart_context_enabled = smart_context_enabled
        self.rag_engine = rag_engine

        # Context Manager 초기화 (Pro+)
        self.context_manager = None
        if smart_context_enabled and CONTEXT_MANAGER_AVAILABLE and ContextManager is not None:
            try:
                self.context_manager = ContextManager(memory_dir=memory_dir)
            except Exception as e:
                logger.warning(f"Failed to initialize ContextManager: {e}")

    def load_context(
        self,
        project_id: str,
        branch_id: str,
        context_id: Optional[str] = None,
        force_full_load: bool = False,
    ) -> Dict[str, Any]:
        """
        특정 맥락 활성화 (압축 해제)

        Smart Context 기능 (Pro 이상):
        - metadata + summary만 유지 → full_content 로드
        - Lazy Loading으로 토큰 효율화

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_id: Context ID (없으면 브랜치 summary만)
            force_full_load: 전체 내용 강제 로드

        Returns:
            로드 결과
        """
        if not self.smart_context_enabled or not self.context_manager:
            return {
                "success": False,
                "error": "Smart Context 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.context_manager.load_context(
                project_id=project_id,
                branch_id=branch_id,
                context_id=context_id,
                force_full_load=force_full_load,
            )
            return result
        except Exception as e:
            return {"success": False, "error": f"맥락 로드 실패: {str(e)}"}

    def compress_context(self, project_id: str, branch_id: str, context_id: str) -> Dict[str, Any]:
        """
        Context 압축 (full_content 언로드, summary만 유지)

        Smart Context 기능 (Pro 이상):
        - 30분 미사용 맥락 자동 압축
        - 토큰 70% 절감 목표

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_id: Context ID

        Returns:
            압축 결과
        """
        if not self.smart_context_enabled or not self.context_manager:
            return {
                "success": False,
                "error": "Smart Context 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.context_manager.compress_context(
                project_id=project_id, branch_id=branch_id, context_id=context_id
            )
            return result
        except Exception as e:
            return {"success": False, "error": f"맥락 압축 실패: {str(e)}"}

    def get_context_summary(
        self, project_id: str, branch_id: str, context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Context의 summary만 반환 (full_content 로드 없이)

        Smart Context 기능 (Pro 이상):
        - 토큰 효율적인 빠른 조회
        - full_content 로드 없이 summary만 반환

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_id: Context ID (없으면 브랜치 summary)

        Returns:
            Summary 정보
        """
        if not self.smart_context_enabled or not self.context_manager:
            return {
                "success": False,
                "error": "Smart Context 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.context_manager.get_context_summary(
                project_id=project_id, branch_id=branch_id, context_id=context_id
            )
            return result
        except Exception as e:
            return {"success": False, "error": f"Summary 조회 실패: {str(e)}"}

    def get_loaded_contexts(self) -> Dict[str, Any]:
        """
        현재 로드된 모든 Context 정보 반환

        Smart Context 기능 (Pro 이상):
        - 활성 브랜치 목록
        - 각 브랜치의 로드된 Context
        - 마지막 접근 시간

        Returns:
            로드된 맥락 정보
        """
        if not self.smart_context_enabled or not self.context_manager:
            return {
                "success": False,
                "error": "Smart Context 기능이 비활성화되어 있습니다. (Pro 이상 필요)",
            }

        try:
            result = self.context_manager.get_loaded_contexts()
            return {"success": True, "loaded_contexts": result}
        except Exception as e:
            return {"success": False, "error": f"로드된 맥락 조회 실패: {str(e)}"}

    def search_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        로컬 Vector RAG 검색

        과거 맥락을 의미 기반으로 정확히 검색합니다.

        Args:
            query: 검색 쿼리
            project_id: 프로젝트 ID (필터링용, 선택)
            branch_id: 브랜치 ID (필터링용, 선택)
            top_k: 반환할 최대 결과 수 (기본: 5)

        Returns:
            검색 결과 딕셔너리
        """
        if not self.rag_engine:
            return {
                "success": False,
                "error": "RAG Engine이 초기화되지 않았습니다.",
            }

        try:
            # RAG 검색 수행
            results = self.rag_engine.search(
                query=query,
                project_id=project_id,
                branch_id=branch_id,
                top_k=top_k,
            )

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return {"success": False, "error": f"검색 실패: {str(e)}"}

    def _auto_collect_context(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        프로젝트 경로에서 자동으로 Context 수집

        Evidence 수집용:
        - Git 정보
        - 파일 리스트
        - README 내용

        Args:
            project_path: 프로젝트 루트 경로

        Returns:
            수집된 Context 딕셔너리
        """
        collected = {
            "git_info": None,
            "files": [],
            "readme_content": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if not project_path:
            return collected

        project_root = Path(project_path)
        if not project_root.exists():
            logger.warning(f"Project path does not exist: {project_path}")
            return collected

        # Git 정보 수집
        git_dir = project_root / ".git"
        if git_dir.exists():
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                collected["git_info"] = {"current_branch": result.stdout.strip()}
            except Exception as e:
                logger.warning(f"Failed to collect git info: {e}")

        # 파일 리스트 수집 (상위 100개만)
        try:
            all_files = [
                str(f.relative_to(project_root))
                for f in project_root.rglob("*")
                if f.is_file() and not f.name.startswith(".")
            ]
            collected["files"] = sorted(all_files)[:100]
        except Exception as e:
            logger.warning(f"Failed to collect file list: {e}")

        # README 내용 수집
        for readme_name in ["README.md", "README.txt", "README"]:
            readme_path = project_root / readme_name
            if readme_path.exists():
                try:
                    collected["readme_content"] = readme_path.read_text(encoding="utf-8")[:5000]
                    break
                except Exception as e:
                    logger.warning(f"Failed to read README: {e}")

        return collected

    def _parse_context_to_evidence(
        self, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Context 내용을 Evidence 리스트로 파싱

        Hallucination Detection용:
        - Code blocks
        - File references
        - Implementation claims

        Args:
            content: Context 내용
            metadata: Context 메타데이터

        Returns:
            Evidence 리스트
        """
        evidences = []

        # 1. Code blocks 추출
        code_pattern = r"```(?P<lang>\w+)?\n(?P<code>.*?)```"
        for match in re.finditer(code_pattern, content, re.DOTALL):
            evidences.append(
                {
                    "type": "code_block",
                    "language": match.group("lang") or "unknown",
                    "content": match.group("code").strip(),
                    "source": "context_content",
                }
            )

        # 2. File references 추출
        file_pattern = r"`([a-zA-Z0-9_/\-\.]+\.(py|js|ts|md|json|yaml))`"
        for match in re.finditer(file_pattern, content):
            evidences.append(
                {
                    "type": "file_reference",
                    "filename": match.group(1),
                    "source": "context_content",
                }
            )

        # 3. Implementation claims 추출
        claim_keywords = ["구현했", "완료했", "수정했", "추가했", "생성했"]
        for keyword in claim_keywords:
            pattern = rf"[^.]*{keyword}[^.]*\."
            for match in re.finditer(pattern, content):
                evidences.append(
                    {
                        "type": "implementation_claim",
                        "claim": match.group(0).strip(),
                        "keyword": keyword,
                        "source": "context_content",
                    }
                )

        # 4. 메타데이터에서 추가 Evidence
        if metadata:
            if "ontology_category" in metadata:
                evidences.append(
                    {
                        "type": "ontology_category",
                        "category": metadata["ontology_category"],
                        "confidence": metadata.get("ontology_confidence", 0.0),
                        "source": "metadata",
                    }
                )

        return evidences
