"""
Cortex MCP - Hierarchical RAG Engine v3.0 (M&A Premium IP)

2계층 벡터 검색 시스템:
- Layer 1: Summary Vector (요약 인덱스) - 빠른 후보 선정
- Layer 2: Detail Vector (상세 인덱스) - 정밀 검색

성능 목표:
- P95 Latency: 50ms 이하
- Recall@10: 95% 이상
- 대규모 맥락에서도 일관된 성능

M&A 가치:
- Scalability 확보 (50GB+ Vector DB 지원)
- 경쟁사 대비 검색 정확도 향상
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import config

from .alpha_logger import LogModule, get_alpha_logger

# ============================================================================
# 상수 및 설정
# ============================================================================

# 임베딩 모델
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# 계층별 컬렉션 이름
COLLECTION_SUMMARY = "cortex_summary_vectors"
COLLECTION_DETAIL = "cortex_detail_vectors"

# 검색 설정
DEFAULT_SUMMARY_TOP_K = 20  # 1차 검색 후보 수
DEFAULT_DETAIL_TOP_K = 10  # 2차 검색 결과 수
DEFAULT_RERANK_TOP_K = 5  # 최종 반환 수

# 성능 목표
TARGET_P95_LATENCY_MS = 50  # 50ms 목표

# 요약 생성 설정
SUMMARY_MAX_LENGTH = 200  # 요약 최대 길이 (characters)
CHUNK_SIZE = 1000  # 청크 크기


# ============================================================================
# 데이터 클래스
# ============================================================================


class IndexLayer(Enum):
    """인덱스 계층"""

    SUMMARY = "summary"
    DETAIL = "detail"


@dataclass
class HierarchicalDocument:
    """계층적 문서 구조"""

    doc_id: str
    content: str
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[str] = field(default_factory=list)
    chunk_ids: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "summary": self.summary,
            "metadata": self.metadata,
            "chunks": self.chunks,
            "chunk_ids": self.chunk_ids,
            "created_at": self.created_at,
        }


@dataclass
class SearchResult:
    """검색 결과"""

    doc_id: str
    content: str
    summary: str
    score: float
    layer: IndexLayer
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "summary": self.summary,
            "score": round(self.score, 4),
            "layer": self.layer.value,
            "metadata": self.metadata,
            "latency_ms": round(self.latency_ms, 2),
        }


@dataclass
class HierarchicalSearchResult:
    """계층적 검색 결과"""

    results: List[SearchResult]
    total_found: int
    summary_candidates: int
    detail_searched: int
    latency_breakdown: Dict[str, float]
    total_latency_ms: float
    p95_met: bool

    def to_dict(self) -> Dict:
        return {
            "results": [r.to_dict() for r in self.results],
            "total_found": self.total_found,
            "summary_candidates": self.summary_candidates,
            "detail_searched": self.detail_searched,
            "latency_breakdown": self.latency_breakdown,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "p95_met": self.p95_met,
        }


# ============================================================================
# 계층적 RAG 엔진
# ============================================================================


class HierarchicalRAGEngine:
    """
    계층적 RAG 엔진 (v3.0)

    2-Layer Vector Search:
    1. Summary Layer: 빠른 후보 선정 (N개)
    2. Detail Layer: 정밀 검색 및 Re-ranking

    HNSW 인덱스 최적화:
    - ef_construction: 200 (빌드 시 정확도)
    - ef_search: 100 (검색 시 정확도)
    - M: 16 (연결 수)
    """

    def __init__(
        self, storage_path: Optional[Path] = None, embedding_model_name: str = EMBEDDING_MODEL
    ):
        """
        Args:
            storage_path: 벡터 DB 저장 경로
            embedding_model_name: 임베딩 모델명
        """
        self.logger = get_alpha_logger()

        # 저장 경로
        if storage_path is None:
            storage_path = config.base_dir / "hierarchical_rag"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 임베딩 모델 (지연 로딩)
        self.embedding_model_name = embedding_model_name
        self._embedding_model = None

        # ChromaDB 클라이언트 (지연 로딩)
        self._chroma_client = None
        self._summary_collection = None
        self._detail_collection = None

        # 문서 인덱스 (doc_id → chunks 매핑)
        self._doc_index: Dict[str, HierarchicalDocument] = {}
        self._load_doc_index()

    def _init_embedding_model(self):
        """임베딩 모델 초기화 (지연 로딩)"""
        if self._embedding_model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model

    def _init_chroma(self):
        """ChromaDB 초기화 (지연 로딩)"""
        if self._chroma_client is None and CHROMADB_AVAILABLE:
            chroma_path = self.storage_path / "chroma_hierarchical"
            chroma_path.mkdir(parents=True, exist_ok=True)

            self._chroma_client = chromadb.PersistentClient(
                path=str(chroma_path), settings=Settings(anonymized_telemetry=False)
            )

            # Summary Collection (1차 검색용)
            self._summary_collection = self._chroma_client.get_or_create_collection(
                name=COLLECTION_SUMMARY,
                metadata={
                    "description": "Summary vectors for fast candidate selection",
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:search_ef": 100,
                    "hnsw:M": 16,
                },
            )

            # Detail Collection (2차 검색용)
            self._detail_collection = self._chroma_client.get_or_create_collection(
                name=COLLECTION_DETAIL,
                metadata={
                    "description": "Detail vectors for precise search",
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:search_ef": 100,
                    "hnsw:M": 16,
                },
            )

        return self._summary_collection, self._detail_collection

    def _load_doc_index(self):
        """문서 인덱스 로드"""
        index_file = self.storage_path / "doc_index.json"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._doc_index = {
                    doc_id: HierarchicalDocument(**doc_data) for doc_id, doc_data in data.items()
                }
            except Exception as e:
                self.logger.log(
                    module=LogModule.RAG_SEARCH,
                    action="load_doc_index",
                    success=False,
                    error=str(e),
                )

    def _save_doc_index(self):
        """문서 인덱스 저장"""
        index_file = self.storage_path / "doc_index.json"
        try:
            data = {doc_id: doc.to_dict() for doc_id, doc in self._doc_index.items()}
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.log(
                module=LogModule.RAG_SEARCH, action="save_doc_index", success=False, error=str(e)
            )

    def _generate_summary(self, content: str) -> str:
        """
        콘텐츠 요약 생성

        간단한 추출적 요약:
        - 첫 문장 + 키워드 추출
        - 최대 SUMMARY_MAX_LENGTH 글자

        Args:
            content: 원본 콘텐츠

        Returns:
            요약 문자열
        """
        # 문장 분리
        sentences = content.replace("\n", " ").split(".")
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return content[:SUMMARY_MAX_LENGTH]

        # 첫 1-2 문장 추출
        summary_parts = []
        current_length = 0

        for sentence in sentences[:3]:
            if current_length + len(sentence) > SUMMARY_MAX_LENGTH:
                break
            summary_parts.append(sentence)
            current_length += len(sentence) + 2  # ". " 포함

        summary = ". ".join(summary_parts)
        if summary and not summary.endswith("."):
            summary += "."

        return summary[:SUMMARY_MAX_LENGTH]

    def _chunk_content(self, content: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
        """
        콘텐츠 청킹

        Args:
            content: 원본 콘텐츠
            chunk_size: 청크 크기

        Returns:
            청크 리스트
        """
        chunks = []
        current_pos = 0

        while current_pos < len(content):
            # 청크 끝 위치 결정
            end_pos = min(current_pos + chunk_size, len(content))

            # 문장 경계에서 자르기 시도
            if end_pos < len(content):
                # 마지막 문장 종료 위치 찾기
                last_period = content.rfind(".", current_pos, end_pos)
                last_newline = content.rfind("\n", current_pos, end_pos)
                boundary = max(last_period, last_newline)

                if boundary > current_pos:
                    end_pos = boundary + 1

            chunk = content[current_pos:end_pos].strip()
            if chunk:
                chunks.append(chunk)

            current_pos = end_pos

        return chunks if chunks else [content]

    def index_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None,
        custom_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        문서 인덱싱 (2계층)

        1. Summary Layer: 요약 벡터 저장
        2. Detail Layer: 청크별 벡터 저장

        Args:
            content: 문서 내용
            metadata: 메타데이터
            doc_id: 문서 ID (없으면 자동 생성)
            custom_summary: 커스텀 요약 (없으면 자동 생성)

        Returns:
            인덱싱 결과
        """
        start_time = time.time()

        model = self._init_embedding_model()
        summary_coll, detail_coll = self._init_chroma()

        if model is None or summary_coll is None:
            return {"success": False, "error": "Required modules not available"}

        # 문서 ID 생성
        if doc_id is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            doc_id = f"doc_{hashlib.sha256(content[:100].encode()).hexdigest()[:8]}_{timestamp}"

        # 요약 생성
        summary = custom_summary if custom_summary else self._generate_summary(content)

        # 청킹
        chunks = self._chunk_content(content)

        # 메타데이터 보강
        metadata["doc_id"] = doc_id
        metadata["indexed_at"] = datetime.now(timezone.utc).isoformat()
        metadata["chunk_count"] = len(chunks)

        # 1. Summary Layer 인덱싱
        summary_embedding = model.encode(summary).tolist()
        summary_coll.add(
            ids=[f"{doc_id}_summary"],
            embeddings=[summary_embedding],
            documents=[summary],
            metadatas=[{**metadata, "layer": "summary", "full_doc_id": doc_id}],
        )

        # 2. Detail Layer 인덱싱 (청크별)
        chunk_ids = []
        chunk_embeddings = []
        chunk_metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            chunk_embeddings.append(model.encode(chunk).tolist())
            chunk_metadatas.append(
                {**metadata, "layer": "detail", "chunk_index": i, "parent_doc_id": doc_id}
            )

        if chunk_ids:
            detail_coll.add(
                ids=chunk_ids,
                embeddings=chunk_embeddings,
                documents=chunks,
                metadatas=chunk_metadatas,
            )

        # 문서 인덱스 저장
        hierarchical_doc = HierarchicalDocument(
            doc_id=doc_id,
            content=content,
            summary=summary,
            metadata=metadata,
            chunks=chunks,
            chunk_ids=chunk_ids,
        )
        self._doc_index[doc_id] = hierarchical_doc
        self._save_doc_index()

        latency_ms = (time.time() - start_time) * 1000

        # 로그
        self.logger.log(
            module=LogModule.RAG_SEARCH,
            action="index_hierarchical",
            success=True,
            latency_ms=latency_ms,
            metadata={"doc_id": doc_id, "summary_length": len(summary), "chunk_count": len(chunks)},
        )

        return {
            "success": True,
            "doc_id": doc_id,
            "summary": summary,
            "chunk_count": len(chunks),
            "latency_ms": round(latency_ms, 2),
        }

    def search(
        self,
        query: str,
        project_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        summary_top_k: int = DEFAULT_SUMMARY_TOP_K,
        detail_top_k: int = DEFAULT_DETAIL_TOP_K,
        final_top_k: int = DEFAULT_RERANK_TOP_K,
    ) -> HierarchicalSearchResult:
        """
        계층적 검색 수행

        1단계: Summary Layer에서 후보 선정 (summary_top_k개)
        2단계: 선정된 문서들의 Detail Layer 검색
        3단계: Re-ranking 후 최종 결과 반환

        Args:
            query: 검색 쿼리
            project_id: 프로젝트 필터
            branch_id: 브랜치 필터
            summary_top_k: 1차 검색 후보 수
            detail_top_k: 2차 검색 결과 수
            final_top_k: 최종 반환 수

        Returns:
            HierarchicalSearchResult
        """
        total_start = time.time()
        latency_breakdown = {}

        model = self._init_embedding_model()
        summary_coll, detail_coll = self._init_chroma()

        if model is None or summary_coll is None:
            return HierarchicalSearchResult(
                results=[],
                total_found=0,
                summary_candidates=0,
                detail_searched=0,
                latency_breakdown={},
                total_latency_ms=0,
                p95_met=False,
            )

        # 쿼리 임베딩
        embed_start = time.time()
        query_embedding = model.encode(query).tolist()
        latency_breakdown["embedding"] = (time.time() - embed_start) * 1000

        # 필터 구성
        where_filter = self._build_filter(project_id, branch_id)

        # === 1단계: Summary Layer 검색 ===
        summary_start = time.time()
        summary_results = summary_coll.query(
            query_embeddings=[query_embedding],
            n_results=summary_top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        latency_breakdown["summary_search"] = (time.time() - summary_start) * 1000

        # 후보 문서 ID 추출
        candidate_doc_ids = set()
        summary_scores = {}

        if summary_results["ids"] and summary_results["ids"][0]:
            for i, sum_id in enumerate(summary_results["ids"][0]):
                if summary_results["metadatas"] and summary_results["metadatas"][0]:
                    full_doc_id = summary_results["metadatas"][0][i].get("full_doc_id")
                    if full_doc_id:
                        candidate_doc_ids.add(full_doc_id)
                        distance = (
                            summary_results["distances"][0][i]
                            if summary_results["distances"]
                            else 1.0
                        )
                        summary_scores[full_doc_id] = 1 - distance

        summary_candidates = len(candidate_doc_ids)

        # === 2단계: Detail Layer 검색 ===
        detail_start = time.time()
        detail_results = []

        if candidate_doc_ids:
            # 후보 문서들의 청크만 검색
            detail_filter = self._build_filter(project_id, branch_id)
            if detail_filter:
                detail_filter = {
                    "$and": [detail_filter, {"parent_doc_id": {"$in": list(candidate_doc_ids)}}]
                }
            else:
                detail_filter = {"parent_doc_id": {"$in": list(candidate_doc_ids)}}

            raw_detail_results = detail_coll.query(
                query_embeddings=[query_embedding],
                n_results=detail_top_k * 2,  # 여유있게 가져오기
                where=detail_filter,
                include=["documents", "metadatas", "distances"],
            )

            if raw_detail_results["ids"] and raw_detail_results["ids"][0]:
                for i, chunk_id in enumerate(raw_detail_results["ids"][0]):
                    content = (
                        raw_detail_results["documents"][0][i]
                        if raw_detail_results["documents"]
                        else ""
                    )
                    metadata = (
                        raw_detail_results["metadatas"][0][i]
                        if raw_detail_results["metadatas"]
                        else {}
                    )
                    distance = (
                        raw_detail_results["distances"][0][i]
                        if raw_detail_results["distances"]
                        else 1.0
                    )

                    parent_doc_id = metadata.get("parent_doc_id", "")
                    summary_score = summary_scores.get(parent_doc_id, 0)

                    # Summary 점수와 Detail 점수 결합
                    detail_score = 1 - distance
                    combined_score = (0.3 * summary_score) + (0.7 * detail_score)

                    # 원본 문서에서 요약 가져오기
                    doc = self._doc_index.get(parent_doc_id)
                    summary = doc.summary if doc else ""

                    detail_results.append(
                        SearchResult(
                            doc_id=parent_doc_id,
                            content=content,
                            summary=summary,
                            score=combined_score,
                            layer=IndexLayer.DETAIL,
                            metadata=metadata,
                        )
                    )

        latency_breakdown["detail_search"] = (time.time() - detail_start) * 1000

        # === 3단계: Re-ranking ===
        rerank_start = time.time()

        # 점수 순 정렬
        detail_results.sort(key=lambda x: x.score, reverse=True)

        # 중복 제거 (같은 문서의 여러 청크)
        seen_docs = set()
        unique_results = []
        for result in detail_results:
            if result.doc_id not in seen_docs:
                seen_docs.add(result.doc_id)
                unique_results.append(result)
                if len(unique_results) >= final_top_k:
                    break

        latency_breakdown["reranking"] = (time.time() - rerank_start) * 1000

        # 총 레이턴시
        total_latency_ms = (time.time() - total_start) * 1000
        p95_met = total_latency_ms <= TARGET_P95_LATENCY_MS

        # 로그
        self.logger.log_rag_search(
            query=query,
            result_count=len(unique_results),
            top_results=[r.doc_id for r in unique_results[:3]],
            ontology_filtered=False,
            latency_ms=total_latency_ms,
        )

        return HierarchicalSearchResult(
            results=unique_results,
            total_found=len(unique_results),
            summary_candidates=summary_candidates,
            detail_searched=len(detail_results),
            latency_breakdown=latency_breakdown,
            total_latency_ms=total_latency_ms,
            p95_met=p95_met,
        )

    def _build_filter(self, project_id: Optional[str], branch_id: Optional[str]) -> Optional[Dict]:
        """필터 구성"""
        if not project_id and not branch_id:
            return None

        conditions = []
        if project_id:
            conditions.append({"project_id": project_id})
        if branch_id:
            conditions.append({"branch_id": branch_id})

        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """
        문서 삭제 (양쪽 계층에서)

        Args:
            doc_id: 문서 ID

        Returns:
            삭제 결과
        """
        summary_coll, detail_coll = self._init_chroma()

        if summary_coll is None:
            return {"success": False, "error": "ChromaDB not available"}

        deleted_summary = 0
        deleted_detail = 0

        # Summary Layer에서 삭제
        try:
            summary_coll.delete(ids=[f"{doc_id}_summary"])
            deleted_summary = 1
        except Exception:
            pass

        # Detail Layer에서 삭제
        doc = self._doc_index.get(doc_id)
        if doc and doc.chunk_ids:
            try:
                detail_coll.delete(ids=doc.chunk_ids)
                deleted_detail = len(doc.chunk_ids)
            except Exception:
                pass

        # 인덱스에서 제거
        if doc_id in self._doc_index:
            del self._doc_index[doc_id]
            self._save_doc_index()

        return {
            "success": True,
            "doc_id": doc_id,
            "deleted_summary": deleted_summary,
            "deleted_chunks": deleted_detail,
        }

    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        summary_coll, detail_coll = self._init_chroma()

        summary_count = summary_coll.count() if summary_coll else 0
        detail_count = detail_coll.count() if detail_coll else 0

        return {
            "total_documents": len(self._doc_index),
            "summary_vectors": summary_count,
            "detail_vectors": detail_count,
            "avg_chunks_per_doc": round(detail_count / max(len(self._doc_index), 1), 2),
            "storage_path": str(self.storage_path),
            "embedding_model": self.embedding_model_name,
            "target_p95_latency_ms": TARGET_P95_LATENCY_MS,
        }


# ============================================================================
# 싱글톤 인스턴스
# ============================================================================

_hierarchical_rag_engine: Optional[HierarchicalRAGEngine] = None


def get_hierarchical_rag_engine() -> HierarchicalRAGEngine:
    """계층적 RAG 엔진 싱글톤 인스턴스 반환"""
    global _hierarchical_rag_engine

    if _hierarchical_rag_engine is None:
        _hierarchical_rag_engine = HierarchicalRAGEngine()

    return _hierarchical_rag_engine


def reset_hierarchical_rag_engine():
    """계층적 RAG 엔진 재초기화"""
    global _hierarchical_rag_engine
    _hierarchical_rag_engine = None
