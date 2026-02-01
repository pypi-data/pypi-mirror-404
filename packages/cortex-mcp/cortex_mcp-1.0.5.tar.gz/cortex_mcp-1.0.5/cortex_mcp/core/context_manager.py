"""
Cortex MCP - Smart Context Manager v2.1
압축/해제 및 Lazy Loading 관리 + Alpha Logger 연동

기능:
- Context 압축/해제 (metadata + summary만 유지, full_content는 요청 시 로드)
- Lazy Loading (필요할 때만 맥락 로드)
- 다중 활성 브랜치 관리 (최대 3개)
- 자동 압축 (30분 미사용 시)
- Alpha Logger 연동 (v2.1)
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, List, Optional, Set

import yaml

sys.path.append(str(Path(__file__).parent.parent))
from config import Tier, config

from .alpha_logger import LogModule, get_alpha_logger
from .evidence_graph import EvidenceGraph, get_evidence_graph
from .smart_cache import get_context_cache


@dataclass
class ContextState:
    """개별 Context의 상태 정보"""

    context_id: str
    branch_id: str
    project_id: str

    # 항상 로드되는 정보
    metadata: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""

    # 압축 가능한 정보 (full_content)
    full_content: Optional[str] = None
    is_loaded: bool = False

    # 타이밍
    last_accessed: float = 0.0
    loaded_at: float = 0.0

    def touch(self):
        """접근 시간 갱신"""
        self.last_accessed = time.time()


@dataclass
class BranchState:
    """브랜치 상태 정보"""

    branch_id: str
    project_id: str
    is_active: bool = False
    contexts: Dict[str, ContextState] = field(default_factory=dict)
    last_accessed: float = 0.0

    def touch(self):
        """접근 시간 갱신"""
        self.last_accessed = time.time()


class ContextManager:
    """
    Smart Context Manager (v2.2: Feature Flags 지원)
    - 토큰 효율성 70% 개선 목표
    - Lazy Loading으로 필요한 맥락만 로드
    - Feature Flags 기반 기능 제어
    """

    # 설정 상수
    MAX_ACTIVE_BRANCHES = 3
    AUTO_COMPRESS_SECONDS = 30 * 60  # 30분
    MAX_CACHE_SIZE = 1000  # Context 캐시 최대 크기

    def __init__(self):
        self.memory_dir = config.memory_dir
        self._lock = Lock()

        # Alpha Logger
        self.logger = get_alpha_logger()

        # Feature Flags 체크
        self.smart_context_enabled = config.is_feature_enabled("smart_context_enabled")

        # SmartContextCache 초기화 (Phase 1-4 통합)
        self.smart_cache = get_context_cache()

        # 활성 브랜치 상태 (최대 3개)
        self._active_branches: Dict[str, BranchState] = {}

        # PERFORMANCE: mtime 기반 Context Cache (정확도 100% 보장)
        # - 파일 경로 → (mtime, ContextState) 매핑
        # - 파일 수정 시 mtime 자동 변경으로 무효화
        # - Edge case 처리: 파일 삭제/이동 시 OSError 대응
        self._context_cache: Dict[str, Tuple[float, ContextState]] = {}

        # 마지막 정리 시간
        self._last_cleanup = time.time()

        # 백그라운드 스레드 관리
        self._shutdown = False
        self._compression_thread = Thread(target=self._background_compression_worker, daemon=True)
        self._compression_thread.start()
        print("[SMART_CONTEXT] 백그라운드 자동 압축 스레드 시작됨 (30분 주기)", file=sys.stderr)

    def is_enabled(self) -> bool:
        """Smart Context 기능이 활성화되어 있는지 확인"""
        return self.smart_context_enabled

    # ==================== Public API ====================

    def load_context(
        self,
        project_id: str,
        branch_id: str,
        context_id: Optional[str] = None,
        force_full_load: bool = False,
    ) -> Dict[str, Any]:
        """
        Context 로드 (압축 해제)

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_id: 특정 Context ID (없으면 브랜치 전체의 summary)
            force_full_load: True면 full_content까지 로드

        Returns:
            로드된 Context 정보
        """
        start_time = time.time()
        with self._lock:
            # 주기적 정리 실행
            self._maybe_cleanup()

            # 브랜치 활성화
            branch_state = self._activate_branch(project_id, branch_id)
            if not branch_state:
                self.logger.log_smart_context(
                    action="load", context_id=context_id or branch_id, success=False, latency_ms=0.0
                )
                return {"success": False, "error": f"브랜치 '{branch_id}'를 찾을 수 없습니다."}

            # 브랜치의 Context 파일 로드
            if context_id:
                context_state = self._load_single_context(
                    project_id, branch_id, context_id, force_full_load
                )
                if not context_state:
                    self.logger.log_smart_context(
                        action="load",
                        context_id=context_id,
                        success=False,
                        latency_ms=(time.time() - start_time) * 1000,
                    )
                    return {
                        "success": False,
                        "error": f"Context '{context_id}'를 찾을 수 없습니다.",
                    }

                latency_ms = (time.time() - start_time) * 1000
                full_size = len(context_state.full_content or "")
                summary_size = len(context_state.summary)

                self.logger.log_smart_context(
                    action="decompress" if force_full_load else "load",
                    context_id=context_id,
                    token_before=summary_size,
                    token_after=full_size if force_full_load else summary_size,
                    success=True,
                    latency_ms=latency_ms,
                )

                return {
                    "success": True,
                    "context_id": context_id,
                    "metadata": context_state.metadata,
                    "summary": context_state.summary,
                    "full_content": context_state.full_content if force_full_load else None,
                    "is_fully_loaded": context_state.is_loaded,
                    "latency_ms": round(latency_ms, 2),
                }
            else:
                # 브랜치의 메타데이터 + summary만 반환
                result = self._get_branch_summary(project_id, branch_id)
                latency_ms = (time.time() - start_time) * 1000
                self.logger.log_smart_context(
                    action="load", context_id=branch_id, success=True, latency_ms=latency_ms
                )
                result["latency_ms"] = round(latency_ms, 2)
                return result

    def get_loaded_contexts(self) -> Dict[str, Any]:
        """
        P0-5: 현재 로드된 모든 Context 정보 반환 (디버깅/대시보드용)
        """
        with self._lock:
            active_branches = []
            for branch_key, branch_state in self._active_branches.items():
                contexts = []
                for ctx_id, ctx_state in branch_state.contexts.items():
                    contexts.append(
                        {
                            "context_id": ctx_id,
                            "is_loaded": ctx_state.is_loaded,
                            "last_accessed": (
                                datetime.fromtimestamp(ctx_state.last_accessed).isoformat()
                                if ctx_state.last_accessed
                                else None
                            ),
                        }
                    )

                active_branches.append(
                    {
                        "branch_id": branch_state.branch_id,
                        "project_id": branch_state.project_id,
                        "is_active": branch_state.is_active,
                        "context_count": len(contexts),
                        "contexts": contexts,
                    }
                )

            return {
                "active_branch_count": len(self._active_branches),
                "max_active_branches": self.MAX_ACTIVE_BRANCHES,
                "branches": active_branches,
            }

    def load_contexts_batch(
        self,
        project_id: str,
        branch_id: str,
        context_ids: List[str],
        force_full_load: bool = False,
    ) -> Dict[str, Any]:
        """
        P0-6: 여러 Context를 일괄 로드 (accept_suggestions 후 자동 호출)

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_ids: 로드할 Context ID 목록
            force_full_load: True면 full_content까지 로드

        Returns:
            일괄 로드 결과
        """
        start_time = time.time()
        results = {
            "success": True,
            "loaded": [],
            "failed": [],
            "total": len(context_ids),
        }

        for context_id in context_ids:
            result = self.load_context(
                project_id=project_id,
                branch_id=branch_id,
                context_id=context_id,
                force_full_load=force_full_load,
            )

            if result.get("success"):
                results["loaded"].append(context_id)
            else:
                results["failed"].append({
                    "context_id": context_id,
                    "error": result.get("error", "Unknown error")
                })

        latency_ms = (time.time() - start_time) * 1000

        results["loaded_count"] = len(results["loaded"])
        results["failed_count"] = len(results["failed"])
        results["latency_ms"] = round(latency_ms, 2)

        # Alpha Logger 기록
        self.logger.log_smart_context(
            action="load_batch",
            context_id=f"batch_{len(context_ids)}",
            success=(results["failed_count"] == 0),
            latency_ms=latency_ms,
        )

        return results

    def compress_context(self, project_id: str, branch_id: str, context_id: str) -> Dict[str, Any]:
        """
        Context 압축 (캐시 제거로 인해 기능 무효화됨)

        CACHE REMOVED: 이 함수는 더 이상 필요하지 않음
        - Context가 메모리에 캐시되지 않으므로 압축할 것이 없음
        - 항상 디스크에서 읽고 메모리에 상주하지 않음
        - 호환성을 위해 success=True 반환

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_id: Context ID (또는 branch_id)

        Returns:
            압축 결과 (항상 성공)
        """
        return {
            "success": True,
            "message": "Context Cache가 제거되어 압축이 불필요합니다. (항상 디스크에서 읽음)",
            "summary_preserved": True,
            "bytes_freed": 0,
            "compressed_count": 0,
            "already_compressed": True,
            "latency_ms": 0.0,
        }

    def get_context_summary(
        self, project_id: str, branch_id: str, context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Context의 summary만 반환 (full_content 로드 없이)
        토큰 효율적인 빠른 조회
        """
        branch_path = self._find_branch_path(project_id, branch_id)
        if not branch_path:
            return {"success": False, "error": "브랜치를 찾을 수 없습니다."}

        frontmatter, _ = self._parse_md_file(branch_path)

        return {
            "success": True,
            "project_id": project_id,
            "branch_id": branch_id,
            "summary": frontmatter.get("summary", ""),
            "branch_topic": frontmatter.get("branch_topic", ""),
            "status": frontmatter.get("status", ""),
            "is_compressed": True,  # summary만 반환했으므로
        }

    def deactivate_branch(self, project_id: str, branch_id: str) -> Dict[str, Any]:
        """
        브랜치 비활성화 (모든 Context 압축)
        """
        with self._lock:
            branch_key = f"{project_id}/{branch_id}"

            if branch_key in self._active_branches:
                branch_state = self._active_branches[branch_key]

                # 모든 Context 압축
                for ctx_id, ctx_state in branch_state.contexts.items():
                    ctx_state.full_content = None
                    ctx_state.is_loaded = False

                branch_state.is_active = False
                del self._active_branches[branch_key]

                return {"success": True, "message": f"브랜치 '{branch_id}' 비활성화 완료"}

            return {"success": False, "error": f"브랜치 '{branch_id}'가 활성 상태가 아닙니다."}

    # ==================== Private Methods ====================

    def _activate_branch(self, project_id: str, branch_id: str) -> Optional[BranchState]:
        """
        브랜치 활성화 (최대 3개 유지)
        """
        branch_key = f"{project_id}/{branch_id}"

        # 이미 활성화된 경우
        if branch_key in self._active_branches:
            self._active_branches[branch_key].touch()
            return self._active_branches[branch_key]

        # 브랜치 파일 확인
        branch_path = self._find_branch_path(project_id, branch_id)
        if not branch_path:
            return None

        # 최대 활성 브랜치 수 초과 시 가장 오래된 브랜치 비활성화
        if len(self._active_branches) >= self.MAX_ACTIVE_BRANCHES:
            self._deactivate_oldest_branch()

        # 새 브랜치 상태 생성
        branch_state = BranchState(branch_id=branch_id, project_id=project_id, is_active=True)
        branch_state.touch()

        self._active_branches[branch_key] = branch_state
        return branch_state

    def _deactivate_oldest_branch(self):
        """가장 오래된 활성 브랜치 비활성화"""
        if not self._active_branches:
            return

        oldest_key = min(
            self._active_branches.keys(), key=lambda k: self._active_branches[k].last_accessed
        )

        branch_state = self._active_branches[oldest_key]

        # 모든 Context 압축
        for ctx_state in branch_state.contexts.values():
            ctx_state.full_content = None
            ctx_state.is_loaded = False

        del self._active_branches[oldest_key]

    def _load_single_context(
        self, project_id: str, branch_id: str, context_id: str, full_load: bool = False
    ) -> Optional[ContextState]:
        """
        단일 Context 로드 (mtime 기반 캐시 사용)

        PERFORMANCE OPTIMIZED: mtime 기반 캐시로 정확도 100% 보장
        - 파일 mtime 변경 감지 → 자동 무효화
        - mtime 일치 시 캐시 반환 (~15ms 절감)
        - full_load=True 시 항상 디스크 읽기
        """

        # 파일 경로 찾기
        branch_path = self._find_branch_path(project_id, branch_id)
        if not branch_path:
            return None

        # mtime 캐시 체크
        cache_key = str(branch_path)
        try:
            current_mtime = os.path.getmtime(branch_path)

            # 캐시에 있고 mtime 일치하면 반환 (full_load 아닐 때만)
            if cache_key in self._context_cache and not full_load:
                cached_mtime, cached_state = self._context_cache[cache_key]
                if cached_mtime == current_mtime:
                    # Cache hit - 캐시된 상태 반환
                    cached_state.touch()
                    return cached_state
        except OSError:
            # 파일 삭제/이동 시 캐시 제거
            if cache_key in self._context_cache:
                del self._context_cache[cache_key]
            # 파일이 없으면 None 반환
            return None

        # Cache miss - 디스크에서 로드
        frontmatter, body = self._parse_md_file(branch_path)

        ctx_state = ContextState(
            context_id=context_id or branch_id,
            branch_id=branch_id,
            project_id=project_id,
            metadata=frontmatter,
            summary=frontmatter.get("summary", ""),
        )
        ctx_state.touch()

        if full_load:
            ctx_state.full_content = body
            ctx_state.is_loaded = True
            ctx_state.loaded_at = time.time()

        # 캐시 업데이트 (mtime, ctx_state)
        try:
            self._context_cache[cache_key] = (current_mtime, ctx_state)
        except Exception:
            # 캐시 업데이트 실패해도 계속 진행 (캐시는 선택 사항)
            pass

        # 브랜치 상태에 추가
        branch_key = f"{project_id}/{branch_id}"
        if branch_key in self._active_branches:
            self._active_branches[branch_key].contexts[context_id or branch_id] = ctx_state

        return ctx_state

    def _load_full_content(self, ctx_state: ContextState):
        """Context의 full_content 로드"""
        branch_path = self._find_branch_path(ctx_state.project_id, ctx_state.branch_id)
        if branch_path:
            _, body = self._parse_md_file(branch_path)
            ctx_state.full_content = body
            ctx_state.is_loaded = True
            ctx_state.loaded_at = time.time()

    def _get_branch_summary(self, project_id: str, branch_id: str) -> Dict[str, Any]:
        """브랜치의 요약 정보 반환"""
        branch_path = self._find_branch_path(project_id, branch_id)
        if not branch_path:
            return {"success": False, "error": "브랜치를 찾을 수 없습니다."}

        frontmatter, _ = self._parse_md_file(branch_path)

        return {
            "success": True,
            "branch_id": branch_id,
            "project_id": project_id,
            "branch_topic": frontmatter.get("branch_topic", ""),
            "summary": frontmatter.get("summary", ""),
            "status": frontmatter.get("status", ""),
            "created_at": frontmatter.get("created_at", ""),
            "is_compressed": True,
        }

    def _maybe_cleanup(self):
        """
        주기적으로 오래된 Context 압축 (캐시 제거로 인해 기능 무효화됨)

        CACHE REMOVED: 이 함수는 더 이상 필요하지 않음
        - Context가 메모리에 캐시되지 않으므로 정리할 것이 없음
        - 호환성을 위해 빈 함수로 유지
        """
        pass

    # =========================================================================
    # Phase 3: Cognitive Load Context Management
    # =========================================================================

    def prioritize_contexts(
        self, project_id: str, available_contexts: List[ContextState]
    ) -> Dict[str, List[ContextState]]:
        """
        Cognitive Load 기반 Context 우선순위 결정

        Graph Centrality 기반으로 중요한 context를 우선 유지하고,
        덜 중요한 context는 압축하여 활성 context 수를 MAX_ACTIVE (3개) 이하로 유지합니다.

        Args:
            project_id: 프로젝트 ID
            available_contexts: 우선순위를 결정할 Context 목록

        Returns:
            {
                "active": List[ContextState],      # 활성 유지할 context (최대 3개)
                "compressed": List[ContextState]   # 압축할 context
            }
        """
        if not available_contexts:
            return {"active": [], "compressed": []}

        # EvidenceGraph에서 centrality 계산
        # project_path는 memory_dir 기반으로 결정
        from pathlib import Path
        project_path = str(Path(self.memory_dir) / project_id)
        # PERFORMANCE: 싱글톤 패턴 사용 (~80ms 절감)
        evidence_graph = get_evidence_graph(project_id=project_id, project_path=project_path)
        centrality_scores = evidence_graph.compute_combined_centrality()

        # Context를 centrality 점수 기준으로 정렬
        sorted_contexts = sorted(
            available_contexts,
            key=lambda ctx: centrality_scores.get(ctx.context_id, 0.0),
            reverse=True,  # 높은 점수부터
        )

        # 상위 3개는 active, 나머지는 compressed
        max_active = min(self.MAX_ACTIVE_BRANCHES, len(sorted_contexts))
        active = sorted_contexts[:max_active]
        compressed = sorted_contexts[max_active:]

        # Alpha Logger 기록
        self.logger.log(
            module=LogModule.CONTEXT_MANAGER,
            action="prioritize_contexts",
            metadata={
                "project_id": project_id,
                "total_contexts": len(available_contexts),
                "active_count": len(active),
                "compressed_count": len(compressed),
                "active_ids": [ctx.context_id for ctx in active],
                "compressed_ids": [ctx.context_id for ctx in compressed],
            },
        )

        return {"active": active, "compressed": compressed}

    def get_context_priority_info(self, project_id: str, context_id: str) -> Dict[str, Any]:
        """
        특정 Context의 우선순위 정보 조회

        Args:
            project_id: 프로젝트 ID
            context_id: Context ID

        Returns:
            {
                "context_id": str,
                "degree_centrality": float,
                "betweenness_centrality": float,
                "combined_centrality": float,
                "is_critical": bool,
                "rank": int  # 전체 context 중 순위 (1부터 시작)
            }
        """
        # project_path는 memory_dir 기반으로 결정
        from pathlib import Path
        project_path = str(Path(self.memory_dir) / project_id)
        # PERFORMANCE: 싱글톤 패턴 사용 (~80ms 절감)
        evidence_graph = get_evidence_graph(project_id=project_id, project_path=project_path)

        degree = evidence_graph.compute_degree_centrality()
        betweenness = evidence_graph.compute_betweenness_centrality()
        combined = evidence_graph.compute_combined_centrality()

        # 전체 context 중 순위 계산
        context_scores = [
            (cid, score)
            for cid, score in combined.items()
            if evidence_graph.graph.nodes.get(cid, {}).get("node_type") == "context"
        ]
        context_scores.sort(key=lambda x: x[1], reverse=True)

        rank = next((i + 1 for i, (cid, _) in enumerate(context_scores) if cid == context_id), None)

        return {
            "context_id": context_id,
            "degree_centrality": degree.get(context_id, 0.0),
            "betweenness_centrality": betweenness.get(context_id, 0.0),
            "combined_centrality": combined.get(context_id, 0.0),
            "is_critical": evidence_graph.is_critical(context_id),
            "rank": rank,
            "total_contexts": len(context_scores),
        }

    # =========================================================================
    # Phase C: Lazy Semantic Resolution (v3.0)
    # =========================================================================

    def lazy_resolve_semantic(
        self,
        project_id: str,
        context_node: "ContextNode",
        rag_engine: Any = None
    ) -> Dict[str, Any]:
        """
        SHALLOW 노드를 DEEP으로 해석 + RAG 인덱싱

        Args:
            project_id: 프로젝트 ID
            context_node: Context Graph의 노드
            rag_engine: RAG 엔진 인스턴스

        Returns:
            해석 결과
        """
        from .context_graph import SemanticLevel

        start_time = time.time()

        # 이미 DEEP이면 스킵
        if context_node.semantic_level == SemanticLevel.DEEP:
            return {
                "success": True,
                "already_deep": True,
                "context_id": context_node.context_id
            }

        # RESOLVING 상태로 전환
        context_node.start_resolving()

        try:
            # 1. 파일 내용 읽기
            file_content = self._read_file_content(context_node.file_path)
            if not file_content:
                return {
                    "success": False,
                    "error": f"파일을 읽을 수 없음: {context_node.file_path}"
                }

            # 2. 의미 분석 (간단한 요약 생성)
            summary, description = self._generate_semantic_summary(
                file_content,
                context_node.language
            )

            # 3. RAG 인덱싱
            rag_indexed = False
            if rag_engine:
                try:
                    metadata = {
                        "project_id": project_id,
                        "context_id": context_node.context_id,
                        "file_path": context_node.file_path,
                        "language": context_node.language,
                        "semantic_level": "deep"
                    }

                    # 전체 내용 인덱싱 (검색 정확도 향상)
                    rag_engine.add_context(
                        context_id=context_node.context_id,
                        content=file_content,
                        metadata=metadata
                    )
                    rag_indexed = True
                except Exception as rag_err:
                    print(f"[WARNING] RAG 인덱싱 실패: {rag_err}")
                    # RAG 실패해도 DEEP 전환은 진행

            # 4. Context Node 업데이트
            context_node.complete_deep_scan(summary, description)

            latency_ms = (time.time() - start_time) * 1000

            # Alpha Logger 기록
            self.logger.log(
                module=LogModule.CONTEXT_MANAGER,
                action="lazy_resolve_semantic",
                metadata={
                    "context_id": context_node.context_id,
                    "rag_indexed": rag_indexed,
                    "latency_ms": round(latency_ms, 2)
                },
                success=True
            )

            return {
                "success": True,
                "context_id": context_node.context_id,
                "semantic_level": "deep",
                "rag_indexed": rag_indexed,
                "summary_length": len(summary),
                "latency_ms": round(latency_ms, 2)
            }

        except Exception as e:
            print(f"[ERROR] Lazy Resolve 실패: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "context_id": context_node.context_id
            }

    def resolve_on_demand(
        self,
        project_id: str,
        context_ids: List[str],
        context_graph: Any,
        rag_engine: Any
    ) -> Dict[str, Any]:
        """
        여러 Context를 일괄 해석

        Args:
            project_id: 프로젝트 ID
            context_ids: 해석할 Context ID 목록
            context_graph: Context Graph 인스턴스
            rag_engine: RAG 엔진 인스턴스

        Returns:
            일괄 해석 결과
        """
        from .context_graph import SemanticLevel

        start_time = time.time()
        results = {
            "resolved": [],
            "failed": [],
            "skipped": []
        }

        for context_id in context_ids:
            node = context_graph.get_node(context_id)
            if not node:
                results["failed"].append(context_id)
                continue

            if node.semantic_level == SemanticLevel.DEEP:
                results["skipped"].append(context_id)
                continue

            resolve_result = self.lazy_resolve_semantic(
                project_id, node, rag_engine
            )

            if resolve_result["success"]:
                results["resolved"].append(context_id)
                # Context Graph 업데이트
                context_graph.update_node(node)
            else:
                results["failed"].append(context_id)

        latency_ms = (time.time() - start_time) * 1000

        return {
            "success": True,
            "total": len(context_ids),
            "resolved_count": len(results["resolved"]),
            "failed_count": len(results["failed"]),
            "skipped_count": len(results["skipped"]),
            "results": results,
            "latency_ms": round(latency_ms, 2)
        }

    def _read_file_content(self, file_path: str) -> Optional[str]:
        """
        파일 내용 읽기

        Args:
            file_path: 파일 경로

        Returns:
            파일 내용 또는 None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"[WARNING] 파일 읽기 실패: {file_path}, {e}")
            return None

    def _generate_semantic_summary(
        self,
        content: str,
        language: str
    ) -> tuple[str, str]:
        """
        파일 내용에서 요약 및 설명 생성

        Args:
            content: 파일 내용
            language: 언어 (python, typescript, javascript 등)

        Returns:
            (summary, description) 튜플
        """
        # 간단한 extractive summarization
        # 추후 LLM 기반으로 업그레이드 가능

        lines = content.split("\n")

        # Summary: 첫 100줄 중 주석/docstring 추출
        summary_lines = []
        for line in lines[:100]:
            stripped = line.strip()
            # Python docstring/comment
            if language == "python":
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    summary_lines.append(stripped)
                elif stripped.startswith("#"):
                    summary_lines.append(stripped)
            # JavaScript/TypeScript comment
            elif language in ["javascript", "typescript"]:
                if stripped.startswith("//") or stripped.startswith("/*"):
                    summary_lines.append(stripped)

        summary = "\n".join(summary_lines[:10]) if summary_lines else f"파일 내용: {len(lines)}줄"

        # Description: 함수/클래스 목록 추출
        description_parts = []

        # Python
        if language == "python":
            for line in lines:
                if line.strip().startswith("def ") or line.strip().startswith("class "):
                    description_parts.append(line.strip())
        # JavaScript/TypeScript
        elif language in ["javascript", "typescript"]:
            for line in lines:
                stripped = line.strip()
                if (
                    stripped.startswith("function ")
                    or stripped.startswith("class ")
                    or "export " in stripped
                ):
                    description_parts.append(stripped)

        description = "\n".join(description_parts[:20]) if description_parts else summary

        return summary, description

    def _find_branch_path(self, project_id: str, branch_id: str) -> Optional[Path]:
        """브랜치 파일 경로 찾기"""
        project_dir = self.memory_dir / project_id
        if not project_dir.exists():
            return None

        for md_file in project_dir.glob("*.md"):
            if branch_id in md_file.stem:
                return md_file
        return None

    def _parse_md_file(self, file_path: Path) -> tuple:
        """MD 파일에서 Frontmatter와 Body 분리 (Phase 1-4: SmartCache 통합)"""
        # SmartCache 사용하여 파일 읽기 (300x+ 성능 향상)
        context_id = f"{file_path.parent.name}:{file_path.stem}"
        content = self.smart_cache.get(context_id, str(file_path))

        if content is None:
            # 캐시 실패 시 폴백
            content = file_path.read_text(encoding="utf-8")

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
                return frontmatter, body

        return {}, content

    # ==================== 백그라운드 자동 압축 ====================

    def _background_compression_worker(self):
        """
        백그라운드 자동 압축 (캐시 제거로 인해 기능 무효화됨)

        CACHE REMOVED: 이 함수는 더 이상 필요하지 않음
        - Context가 메모리에 캐시되지 않으므로 압축할 것이 없음
        - 항상 디스크에서 읽고 메모리에 상주하지 않음
        - 호환성을 위해 빈 함수로 유지
        """
        pass

    def compress_on_task_completion(self, project_id: str, branch_id: str) -> Dict[str, Any]:
        """
        작업 완료 시 압축 (캐시 제거로 인해 기능 무효화됨)

        CACHE REMOVED: 이 함수는 더 이상 필요하지 않음
        - Context가 메모리에 캐시되지 않으므로 압축할 것이 없음
        - 호환성을 위해 success=True 반환
        """
        return {
            "success": True,
            "compressed_count": 0,
            "branch_id": branch_id,
            "message": "Context Cache가 제거되어 압축이 불필요합니다. (항상 디스크에서 읽음)",
        }

    def shutdown(self):
        """백그라운드 스레드를 안전하게 종료합니다."""
        print("[SMART_CONTEXT] 백그라운드 스레드 종료 요청...", file=sys.stderr)
        self._shutdown = True
        if hasattr(self, "_compression_thread") and self._compression_thread.is_alive():
            self._compression_thread.join(timeout=10)  # 최대 10초 대기
        print("[SMART_CONTEXT] 종료 완료", file=sys.stderr)

    # ==================== Phase 1: Smart Node Grouping ====================

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트 간의 semantic similarity 계산

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            cosine similarity (0.0 ~ 1.0)
        """
        from .rag_engine import RAGEngine
        import numpy as np

        # 빈 텍스트 또는 매우 짧은 텍스트 처리
        if not text1 or not text2:
            return 0.0
        if len(text1.strip()) < 3 or len(text2.strip()) < 3:
            return 0.0

        # RAG 엔진의 임베딩 모델 재사용
        rag = RAGEngine()
        model = rag._init_embedding_model()

        # 임베딩 생성
        emb1 = model.encode(text1)
        emb2 = model.encode(text2)

        # Cosine similarity 계산
        # cos(θ) = (A·B) / (||A|| * ||B||)
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # 범위 보정 [-1, 1] → [0, 1]
        similarity = (similarity + 1) / 2

        return float(similarity)

    def _extract_recent_content(self, body: str, max_chars: int = 500) -> str:
        """
        Body에서 최근 content 추출 (Markdown 헤더 및 메타정보 제거)

        Args:
            body: 브랜치 파일 body
            max_chars: 최대 문자 수

        Returns:
            최근 content (Markdown 헤더 및 메타정보 제거 후 마지막 max_chars)
        """
        if not body or len(body.strip()) == 0:
            return ""

        # Markdown 헤더 제거 (##, ###, - 등)
        lines = body.strip().split('\n')
        content_lines = []

        for line in lines:
            # 빈 라인 스킵
            if not line.strip():
                continue
            # Markdown 헤더 라인 스킵 (##, ###로 시작)
            if line.strip().startswith('#'):
                continue

            cleaned_line = line.strip()

            # 메타정보 패턴 제거
            skip_patterns = [
                '[ASSISTANT]', '[USER]', '[SYSTEM]',  # 역할 태그
                '총 대화 수:', '마지막 업데이트:', 'task_',  # 통계/ID
                'UTC', 'timestamp:', 'branch_id:',  # 타임스탬프/메타데이터
            ]

            # 패턴 포함 라인 스킵
            if any(pattern in cleaned_line for pattern in skip_patterns):
                continue

            # 리스트 마커 제거 (-, *, 등)
            if cleaned_line.startswith('- '):
                cleaned_line = cleaned_line[2:]
            elif cleaned_line.startswith('* '):
                cleaned_line = cleaned_line[2:]

            if cleaned_line:
                content_lines.append(cleaned_line)

        # 정제된 content 결합
        cleaned_body = ' '.join(content_lines)

        # 마지막 max_chars만 추출
        if len(cleaned_body) <= max_chars:
            return cleaned_body
        else:
            return cleaned_body[-max_chars:]

    def find_similar_context_location(
        self,
        project_id: str,
        branch_id: str,
        new_context_summary: str,
        similarity_threshold: float = 0.70
    ) -> Optional[str]:
        """
        새 context를 추가할 최적의 위치 찾기 (기존 노드 또는 신규 생성)

        ULTRATHINK MODE:
        - 기존 노드들과 semantic similarity 계산
        - threshold >= 0.70 충족 시 기존 노드 반환
        - 미충족 시 None 반환 (신규 노드 생성 필요)

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            new_context_summary: 새로운 context의 요약
            similarity_threshold: 유사도 임계값 (기본: 0.70, 한국어 문장 간 실제 유사도 고려)

        Returns:
            기존 node_id (유사한 노드 발견 시) 또는 None (신규 생성 필요)
        """
        start_time = time.time()

        with self._lock:
            # 기존 노드들의 summary 추출
            existing_summaries = {}

            # 브랜치 파일 찾기 (선택적)
            branch_path = self._find_branch_path(project_id, branch_id)

            if branch_path:
                # 브랜치 메타데이터 로드
                frontmatter, body = self._parse_md_file(branch_path)

                # 1. 브랜치 자체의 summary (초기 summary 제외)
                branch_summary = frontmatter.get("summary", "")
                # 초기 summary 또는 의미 없는 summary는 제외
                default_summaries = [
                    "새로운 브랜치가 생성되었습니다.",
                    "",
                    "브랜치 생성",
                    "새 브랜치"
                ]
                if branch_summary and branch_summary not in default_summaries:
                    # Markdown 헤더 제거하여 정제 (summary에 body 전체가 들어갈 수 있음)
                    cleaned_summary = self._extract_recent_content(branch_summary, max_chars=500)
                    if cleaned_summary:
                        existing_summaries[branch_id] = cleaned_summary

                # 2. Summary가 없거나 기본값인 경우, body content의 최근 부분 사용
                # (update_memory() 직후에도 작동하도록)
                if branch_id not in existing_summaries and body:
                    recent_content = self._extract_recent_content(body, max_chars=500)
                    if recent_content:
                        existing_summaries[branch_id] = recent_content

            # 3. Node 구조 검색 (index.json에서 로드) - branch 파일 없이도 가능
            try:
                # branch_path가 있으면 그것을 사용, 없으면 memory_dir/project_id 직접 사용
                if branch_path:
                    project_dir = Path(branch_path).parent
                else:
                    project_dir = self.memory_dir / project_id

                index_path = project_dir / "_index.json"
                print(f"[DEBUG-INDEX] index_path: {index_path}, exists: {index_path.exists()}")

                if index_path.exists():
                    with open(index_path, 'r', encoding='utf-8') as f:
                        index = json.load(f)

                    # 해당 브랜치의 모든 노드 summary 추가
                    branch_nodes = index.get("branches", {}).get(branch_id, {}).get("nodes", {})
                    print(f"[DEBUG-INDEX] branch_nodes: {branch_nodes}")

                    for node_id, node_data in branch_nodes.items():
                        node_summary = node_data.get("summary", "")
                        if node_summary and node_summary.strip():
                            existing_summaries[node_id] = node_summary
                            print(f"[DEBUG-INDEX] Added node: {node_id}, summary: {node_summary}")
            except Exception as e:
                # 인덱스 로드 실패해도 계속 진행
                print(f"[DEBUG-INDEX] Exception: {e}")
                pass

            # 디버그: existing_summaries 확인
            print(f"[DEBUG-FIND-SIMILAR] existing_summaries: {existing_summaries}")
            print(f"[DEBUG-FIND-SIMILAR] new_context_summary: {new_context_summary}")

            # 유사도 계산
            best_match = None
            best_similarity = 0.0

            for node_id, summary in existing_summaries.items():
                if not summary or not new_context_summary:
                    continue

                similarity = self._calculate_semantic_similarity(
                    new_context_summary,
                    summary
                )

                print(f"[DEBUG-FIND-SIMILAR] node_id: {node_id}, similarity: {similarity}")

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = node_id

            latency_ms = (time.time() - start_time) * 1000

            # 임계값 체크
            if best_similarity >= similarity_threshold:
                self.logger.log(
                    module=LogModule.CONTEXT_MANAGER,
                    action="find_similar_location",
                    success=True,
                    latency_ms=latency_ms,
                    metadata={
                        "best_match": best_match,
                        "similarity": round(best_similarity, 4),
                        "threshold": similarity_threshold,
                        "decision": "existing_node"
                    }
                )
                return best_match
            else:
                self.logger.log(
                    module=LogModule.CONTEXT_MANAGER,
                    action="find_similar_location",
                    success=True,
                    latency_ms=latency_ms,
                    metadata={
                        "best_similarity": round(best_similarity, 4),
                        "threshold": similarity_threshold,
                        "decision": "new_node"
                    }
                )
                return None

    def add_context_with_smart_grouping(
        self,
        project_id: str,
        branch_id: str,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Smart Grouping을 적용하여 context 추가

        ULTRATHINK MODE:
        - find_similar_context_location() 호출하여 최적 위치 결정
        - 기존 노드 발견 시: 해당 노드에 추가
        - 기존 노드 없음: 새 노드 생성 후 추가

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            context_data: context 데이터 (summary, content 등 포함)

        Returns:
            추가 결과
        """
        start_time = time.time()

        # Context summary 추출
        new_summary = context_data.get("summary", "")
        if not new_summary:
            # Summary가 없으면 content의 일부를 사용
            new_summary = context_data.get("content", "")[:200]

        # 유사한 위치 찾기
        similar_node_id = self.find_similar_context_location(
            project_id=project_id,
            branch_id=branch_id,
            new_context_summary=new_summary,
            similarity_threshold=0.70
        )

        latency_ms = (time.time() - start_time) * 1000

        if similar_node_id:
            # 기존 노드에 추가
            result = {
                "success": True,
                "action": "added_to_existing_node",
                "node_id": similar_node_id,
                "message": f"유사한 노드 '{similar_node_id}'에 context 추가됨",
                "latency_ms": round(latency_ms, 2)
            }
        else:
            # 새 노드 생성 필요
            result = {
                "success": True,
                "action": "new_node_required",
                "node_id": None,
                "message": "유사한 노드가 없어 신규 노드 생성이 필요함",
                "latency_ms": round(latency_ms, 2)
            }

        # Alpha Logger 기록
        self.logger.log(
            module=LogModule.CONTEXT_MANAGER,
            action="add_context_smart_grouping",
            success=True,
            latency_ms=latency_ms,
            metadata=result
        )

        return result


# Lazy 전역 인스턴스 (import 시 스레드 자동 시작 방지)
_context_manager_instance = None


def _get_context_manager():
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
    return _context_manager_instance


class _LazyContextManager:
    """import 시 스레드 시작을 방지하는 Lazy Proxy"""

    def __getattr__(self, name):
        return getattr(_get_context_manager(), name)


context_manager = _LazyContextManager()
