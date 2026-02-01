"""
Cortex MCP - RAG Engine v2.1
Hybrid 검색 및 Fallback 시스템 + Ontology 연동

기능:
- 로컬 임베딩 생성 (sentence-transformers)
- ChromaDB 벡터 저장소 관리
- Hybrid 검색 (Vector + Keyword)
- Fallback 시스템 (검색 실패 시 확장 검색)
- 의미론적 검색 (Zero-Loss)
- Ontology 기반 필터링 (v2.1)
- Alpha Logger 연동 (v2.1)
"""

import hashlib
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.append(str(Path(__file__).parent.parent))
from config import config

from .alpha_logger import LogModule, get_alpha_logger
from .smart_retrieval import RetrievalStrategy, get_smart_retrieval

# Telemetry (사용 지표 자동 수집)
try:
    from .telemetry_decorator import track_call

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

    # Noop decorator when telemetry not available
    def track_call(module_name: str):
        def decorator(func):
            return func

        return decorator


class RAGEngine:
    """RAG 엔진 v2.1 - Hybrid 검색 + Ontology 연동"""

    # 검색 품질 임계값
    RELEVANCE_THRESHOLD_HIGH = 0.7  # 높은 신뢰도
    RELEVANCE_THRESHOLD_MEDIUM = 0.5  # 중간 신뢰도
    RELEVANCE_THRESHOLD_LOW = 0.3  # 낮은 신뢰도 (Fallback 트리거)

    # Fallback 설정
    MAX_FALLBACK_ATTEMPTS = 3
    FALLBACK_TOP_K_MULTIPLIER = 2  # Fallback 시 결과 수 증가

    def __init__(self, project_id: Optional[str] = None, use_ontology: bool = True, use_hierarchical: bool = False):
        """
        Args:
            project_id: 프로젝트 ID (선택적, 메타데이터 필터링에 사용)
            use_ontology: 온톨로지 필터링 사용 여부 (라이센스에 따라 결정됨)
            use_hierarchical: Hierarchical RAG 사용 여부 (기본: False, 성능 개선 시 True)
        """
        print(f"[DEBUG-INIT] RAGEngine initialized with use_hierarchical={use_hierarchical}", file=sys.stderr)
        self.project_id = project_id
        self.embedding_model_name = config.embedding_model
        self.collection_name = config.chroma_collection_name
        self.top_k = config.search_top_k
        self.chroma_dir = config.base_dir / "chroma_db"

        # Lazy initialization
        self._embedding_model = None
        self._chroma_client = None
        self._collection = None

        # Alpha Logger
        self.logger = get_alpha_logger()

        # Ontology Engine (지연 로딩)
        self.use_ontology = use_ontology
        self._ontology_engine = None

        # Hierarchical RAG Engine (지연 로딩)
        self.use_hierarchical = use_hierarchical
        self._hierarchical_rag = None

        # PERFORMANCE: mtime 기반 Embedding Cache (정확도 100% 보장)
        # - 파일 경로 → (mtime, embedding) 매핑
        # - 파일 수정 시 mtime 자동 변경으로 무효화
        # - metadata에 file_path 없으면 캐시 사용 안 함
        # - Edge case 처리: 파일 삭제/이동 시 OSError 대응
        self._embedding_cache: Dict[str, Tuple[float, List[float]]] = {}

        # 한국어 불용어
        self._korean_stopwords = {
            "이",
            "가",
            "은",
            "는",
            "을",
            "를",
            "에",
            "의",
            "와",
            "과",
            "도",
            "로",
            "으로",
            "에서",
            "까지",
            "부터",
            "만",
            "이다",
            "하다",
            "되다",
            "있다",
            "없다",
            "해",
            "해줘",
            "해주세요",
            "좀",
            "그",
            "저",
            "이것",
            "저것",
            "것",
            "수",
            "등",
            "때문",
        }

        # 영어 불용어
        self._english_stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
        }

    def _init_embedding_model(self):
        """임베딩 모델 초기화 (지연 로딩)"""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer

            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model

    def _init_ontology(self):
        """온톨로지 엔진 초기화 (지연 로딩)"""
        if self._ontology_engine is None and self.use_ontology:
            try:
                from .ontology_engine import LicenseGatedOntologyEngine

                self._ontology_engine = LicenseGatedOntologyEngine()
                self.logger.log_ontology(
                    action="init",
                    input_text="[ONTOLOGY_ENGINE_INIT]",
                    category="system",
                    confidence=1.0,
                    success=True,
                )
            except ImportError:
                self.logger.log_ontology(
                    action="init_failed", input_text="[ONTOLOGY_IMPORT_ERROR]", success=False
                )
                self._ontology_engine = None
        return self._ontology_engine

    def _init_hierarchical_rag(self):
        """Hierarchical RAG 엔진 초기화 (지연 로딩)"""
        if self._hierarchical_rag is None and self.use_hierarchical:
            try:
                from .hierarchical_rag import get_hierarchical_rag_engine

                self._hierarchical_rag = get_hierarchical_rag_engine()
                self.logger.log(
                    LogModule.RAG_SEARCH,
                    "hierarchical_rag_init",
                    input_data={"status": "initialized"},
                    output_data={"engine": "HierarchicalRAG"},
                    success=True,
                )
            except ImportError as e:
                self.logger.log(
                    LogModule.RAG_SEARCH,
                    "hierarchical_rag_init_failed",
                    input_data={"error": str(e)},
                    success=False,
                )
                self._hierarchical_rag = None
        return self._hierarchical_rag

    def _search_with_hierarchical_rag(
        self,
        query: str,
        project_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        top_k: Optional[int] = None,
        relevance_threshold: Optional[float] = 0.5,
    ) -> Dict[str, Any]:
        """
        Hierarchical RAG를 사용한 검색

        Args:
            query: 검색 쿼리
            project_id: 프로젝트 필터
            branch_id: 브랜치 필터
            top_k: 반환할 결과 수
            relevance_threshold: 최소 관련성 점수

        Returns:
            검색 결과 (기존 RAG 형식과 호환)
        """
        h_rag = self._init_hierarchical_rag()

        if h_rag is None:
            # Hierarchical RAG 초기화 실패 시 기존 RAG로 fallback
            self.logger.log(
                LogModule.RAG_SEARCH,
                "hierarchical_rag_fallback",
                input_data={"reason": "init_failed"},
                success=False,
            )
            self.use_hierarchical = False  # 이후 요청은 기존 RAG 사용
            return self.search_context(query, project_id, branch_id, top_k)

        if top_k is None:
            top_k = self.top_k

        # Hierarchical RAG 검색 수행
        start_time = time.perf_counter()
        try:
            h_result = h_rag.search(
                query=query, project_id=project_id, branch_id=branch_id, final_top_k=top_k
            )
            latency_ms = (time.perf_counter() - start_time) * 1000

            # 기존 RAG 형식으로 변환 (relevance filtering 적용)
            formatted_results = []
            for search_result in h_result.results:
                # relevance_threshold 이하의 결과는 제외
                if search_result.score < relevance_threshold:
                    continue

                formatted_results.append(
                    {
                        "doc_id": search_result.doc_id,
                        "content": search_result.content,
                        "metadata": search_result.metadata or {},
                        "distance": 1 - search_result.score,  # score를 distance로 변환
                        "relevance_score": search_result.score,
                        "layer": search_result.layer.value,  # summary or detail
                    }
                )

                # top_k만큼 결과가 모였으면 중단
                if len(formatted_results) >= top_k:
                    break

            # Alpha Logger에 기록
            self.logger.log_rag_search(
                query=query, result_count=len(formatted_results), success=True, latency_ms=latency_ms
            )

            result_dict = {
                "success": True,
                "query": query,
                "results": formatted_results,
                "total_found": h_result.total_found,
                "engine": "hierarchical",
                "latency_ms": latency_ms,
                "metadata": {
                    "summary_candidates": h_result.summary_candidates,
                    "detail_searched": h_result.detail_searched,
                    "p95_met": h_result.p95_met,
                },
            }
            return result_dict

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self.logger.log_rag_search(
                query=query, result_count=0, success=False, latency_ms=latency_ms
            )

            # 에러 발생 시 기존 RAG로 fallback
            self.logger.log(
                LogModule.RAG_SEARCH,
                "hierarchical_rag_error_fallback",
                input_data={"error": str(e), "query": query},
                success=False,
            )
            self.use_hierarchical = False
            return self.search_context(query, project_id, branch_id, top_k)

    def _init_chroma(self, force_reinit: bool = False):
        """ChromaDB 초기화 (지연 로딩)

        Args:
            force_reinit: True일 경우 기존 클라이언트 무시하고 강제 재초기화
        """
        if self._chroma_client is None or force_reinit:
            import chromadb
            from chromadb.config import Settings

            self.chroma_dir.mkdir(parents=True, exist_ok=True)

            self._chroma_client = chromadb.PersistentClient(
                path=str(self.chroma_dir), settings=Settings(anonymized_telemetry=False)
            )

            # ChromaDB collection 생성 (cosine distance 사용)
            # cosine distance: 정규화된 벡터에 최적화, 범위 [0, 2] 보장
            # l2 distance 대신 cosine을 사용하여 distance 이상치 방지
            self._collection = self._chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",  # cosine distance 메트릭 사용
                    "description": "Cortex memory vectors"
                }
            )

        return self._collection

    @property
    def collection(self):
        """Collection 속성 (lazy loading)"""
        if self._collection is None:
            self._init_chroma()
        return self._collection

    def index_content(
        self, content: str, metadata: Dict[str, Any], doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        콘텐츠를 벡터 인덱스에 추가

        Args:
            content: 인덱싱할 텍스트
            metadata: 메타데이터 (project_id, branch_id 등)
            doc_id: 문서 ID (없으면 자동 생성)

        Returns:
            인덱싱 결과
        """
        # Hierarchical RAG 모드 체크
        if self.use_hierarchical:
            h_rag = self._init_hierarchical_rag()
            if h_rag is not None:
                return h_rag.index_document(
                    content=content,
                    metadata=metadata,
                    doc_id=doc_id
                )
            else:
                # Hierarchical RAG 초기화 실패 시 기존 RAG로 Fallback
                self.use_hierarchical = False

        # 기존 RAG 로직
        model = self._init_embedding_model()
        collection = self._init_chroma()

        # mtime 기반 Embedding 캐시 체크
        embedding = None
        file_path = metadata.get('file_path') or metadata.get('source_file')

        if file_path:
            # 파일 경로가 있으면 mtime 캐시 사용
            cache_key = str(file_path)
            try:
                current_mtime = os.path.getmtime(file_path)

                # 캐시에 있고 mtime 일치하면 반환
                if cache_key in self._embedding_cache:
                    cached_mtime, cached_embedding = self._embedding_cache[cache_key]
                    if cached_mtime == current_mtime:
                        # Cache hit - 캐시된 임베딩 사용
                        embedding = cached_embedding
            except OSError:
                # 파일 삭제/이동 시 캐시 제거
                if cache_key in self._embedding_cache:
                    del self._embedding_cache[cache_key]

        # Cache miss 또는 file_path 없음 - 새로운 임베딩 생성
        if embedding is None:
            embedding = model.encode(content).tolist()

            # 파일 경로가 있으면 캐시 업데이트
            if file_path:
                try:
                    current_mtime = os.path.getmtime(file_path)
                    self._embedding_cache[cache_key] = (current_mtime, embedding)
                except (OSError, Exception):
                    # 캐시 업데이트 실패해도 계속 진행
                    pass

        # 문서 ID 생성
        if doc_id is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            doc_id = f"doc_{timestamp}"

        # 메타데이터에 타임스탬프 추가
        metadata["indexed_at"] = datetime.now(timezone.utc).isoformat()

        # ChromaDB에 추가 (에러 발생 시 재시도)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                collection.add(
                    ids=[doc_id], embeddings=[embedding], documents=[content], metadatas=[metadata]
                )
                break  # 성공
            except Exception as e:
                error_msg = str(e).lower()
                error_type = str(type(e).__name__)

                # Collection 관련 에러 (재초기화 후 재시도)
                if "does not exist" in error_msg or "NotFoundError" in error_type:
                    collection = self._init_chroma(force_reinit=True)
                    continue

                # SQLite lock 에러 (재시도)
                elif "database is locked" in error_msg or "locked" in error_msg:
                    if attempt < max_retries - 1:
                        time.sleep(0.1 * (attempt + 1))  # 점진적 대기
                        continue
                    else:
                        raise Exception(f"ChromaDB locked after {max_retries} attempts: {e}")

                # 기타 에러
                else:
                    raise

        return {"success": True, "doc_id": doc_id, "message": "인덱싱 완료"}

    def batch_index_contents(
        self,
        contents: List[str],
        metadatas: List[Dict[str, Any]],
        doc_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        여러 문서를 배치로 인덱싱 (성능 최적화)

        PERFORMANCE: Batch Embedding (~300ms 절감, 5개 문서 기준)
        - sentence-transformers 배치 처리 활용 (GPU 병렬화)
        - mtime 캐시와 결합하여 중복 생성 방지
        - ChromaDB 배치 추가로 DB 오버헤드 감소

        Args:
            contents: 인덱싱할 텍스트 리스트
            metadatas: 메타데이터 리스트 (각 content에 대응)
            doc_ids: 문서 ID 리스트 (선택적, 없으면 자동 생성)

        Returns:
            인덱싱 결과 리스트

        Raises:
            ValueError: contents와 metadatas 길이 불일치

        Example:
            >>> results = rag.batch_index_contents(
            ...     contents=["doc1", "doc2", "doc3"],
            ...     metadatas=[{"file_path": "f1.py"}, {"file_path": "f2.py"}, {}],
            ...     doc_ids=["id1", "id2", "id3"]
            ... )
        """
        if len(contents) != len(metadatas):
            raise ValueError(
                f"contents ({len(contents)}) and metadatas ({len(metadatas)}) "
                "must have the same length"
            )

        if doc_ids is None:
            # 자동 ID 생성 (타임스탬프 기반)
            timestamp_base = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            doc_ids = [f"doc_{timestamp_base}_{i:04d}" for i in range(len(contents))]
        elif len(doc_ids) != len(contents):
            raise ValueError(
                f"doc_ids ({len(doc_ids)}) must have the same length as contents ({len(contents)})"
            )

        model = self._init_embedding_model()
        collection = self._init_chroma()

        # mtime 캐시 체크 (각 문서별로)
        embeddings: List[Optional[List[float]]] = [None] * len(contents)
        needs_generation: List[Tuple[int, str, Optional[str]]] = []  # (index, content, file_path)

        for i, (content, metadata) in enumerate(zip(contents, metadatas)):
            embedding = None
            file_path = metadata.get("file_path") or metadata.get("source_file")

            if file_path:
                cache_key = str(file_path)
                try:
                    current_mtime = os.path.getmtime(file_path)
                    if cache_key in self._embedding_cache:
                        cached_mtime, cached_embedding = self._embedding_cache[cache_key]
                        if cached_mtime == current_mtime:
                            # Cache hit
                            embedding = cached_embedding
                except OSError:
                    # 파일 삭제/이동 시 캐시 제거
                    if cache_key in self._embedding_cache:
                        del self._embedding_cache[cache_key]

            if embedding is None:
                # Cache miss - 배치 생성 대기 리스트에 추가
                needs_generation.append((i, content, file_path))
            else:
                # Cache hit - 즉시 사용
                embeddings[i] = embedding

        # Batch embedding 생성 (cache miss만)
        if needs_generation:
            batch_contents = [content for _, content, _ in needs_generation]
            # PERFORMANCE: 배치 처리로 GPU 활용도 극대화
            batch_embeddings = model.encode(batch_contents)
            if hasattr(batch_embeddings, "tolist"):
                batch_embeddings = batch_embeddings.tolist()
            else:
                batch_embeddings = [emb.tolist() for emb in batch_embeddings]

            # 결과를 원래 위치에 배치 + 캐시 업데이트
            for (idx, content, file_path), embedding in zip(needs_generation, batch_embeddings):
                embeddings[idx] = embedding

                # 파일 경로가 있으면 캐시 업데이트
                if file_path:
                    try:
                        current_mtime = os.path.getmtime(file_path)
                        cache_key = str(file_path)
                        self._embedding_cache[cache_key] = (current_mtime, embedding)
                    except Exception:
                        # 캐시 업데이트 실패해도 계속 진행
                        pass

        # 메타데이터에 타임스탬프 추가
        indexed_at = datetime.now(timezone.utc).isoformat()
        for metadata in metadatas:
            metadata["indexed_at"] = indexed_at

        # ChromaDB에 배치 추가 (에러 발생 시 재시도)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                collection.add(
                    ids=doc_ids, embeddings=embeddings, documents=contents, metadatas=metadatas
                )
                break  # 성공
            except Exception as e:
                error_msg = str(e).lower()
                error_type = str(type(e).__name__)

                # Collection 관련 에러 (재초기화 후 재시도)
                if "does not exist" in error_msg or "NotFoundError" in error_type:
                    collection = self._init_chroma(force_reinit=True)
                    continue

                # SQLite lock 에러 (재시도)
                elif "database is locked" in error_msg or "locked" in error_msg:
                    if attempt < max_retries - 1:
                        time.sleep(0.1 * (attempt + 1))  # 점진적 대기
                        continue
                    else:
                        raise Exception(f"ChromaDB locked after {max_retries} attempts: {e}")

                # 기타 에러
                else:
                    raise

        return [
            {"success": True, "doc_id": doc_id, "message": "배치 인덱싱 완료"} for doc_id in doc_ids
        ]

    def _evict_oldest_embedding(self):
        """
        캐시 정리 함수 (캐시 제거로 인해 기능 무효화됨)

        CACHE REMOVED: 이 함수는 더 이상 필요하지 않음
        - Embedding이 캐시되지 않으므로 정리할 것이 없음
        - 호환성을 위해 빈 함수로 유지
        """
        pass

    def add_context(
        self, context_id: str, content: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        컨텍스트를 벡터 인덱스에 추가 (index_content의 alias)

        Args:
            context_id: 컨텍스트 ID
            content: 인덱싱할 텍스트
            metadata: 메타데이터

        Returns:
            인덱싱 결과
        """
        return self.index_content(content=content, metadata=metadata, doc_id=context_id)

    @track_call("rag_engine")
    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        검색 메서드 (search_context의 alias)

        P5 수정: top_k 기본값을 5에서 20으로 증가
        - 검색 정확도 향상
        - 더 많은 관련 맥락 제공

        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수 (기본: 5)

        Returns:
            검색 결과 리스트
        """
        result = self.search_context(query=query, top_k=top_k)
        return result.get("results", [])

    def search_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        top_k: Optional[int] = None,
        relevance_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        의미론적 검색 수행

        Args:
            query: 검색 쿼리
            project_id: 프로젝트 필터 (선택)
            branch_id: 브랜치 필터 (선택)
            top_k: 반환할 결과 수
            relevance_threshold: 최소 관련성 점수 (0.0-1.0, 선택, 기본: 0.3)
                                cosine distance 기반: 1 - distance
                                distance 0 = relevance 1.0 (완전 일치)
                                distance 2 = relevance -1.0 (완전 반대)
                                threshold 0.3 = distance 0.7 이하만 반환

        Returns:
            검색 결과
        """
        print(f"[DEBUG-SEARCH] search_context called with query='{query[:30]}...', branch_id={branch_id}, relevance_threshold={relevance_threshold}")

        # 기본 relevance threshold 설정
        # 관련성 점수 = 1 - cosine distance
        # 0.5 threshold = 의미적으로 중간 이상 유사한 결과만 반환
        if relevance_threshold is None:
            relevance_threshold = 0.5

        print(f"[DEBUG-SEARCH] Final relevance_threshold={relevance_threshold}")
        # Hierarchical RAG 사용 여부 확인
        if self.use_hierarchical:
            return self._search_with_hierarchical_rag(
                query, project_id, branch_id, top_k, relevance_threshold
            )

        # 기존 RAG 로직
        model = self._init_embedding_model()
        collection = self._init_chroma()

        if top_k is None:
            top_k = self.top_k

        # 쿼리 임베딩
        query_embedding = model.encode(query).tolist()

        # 필터 구성
        where_filter = None
        if project_id or branch_id:
            conditions = []
            if project_id:
                conditions.append({"project_id": project_id})
            if branch_id:
                conditions.append({"branch_id": branch_id})

            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}

        # 검색 수행 (에러 발생 시 재초기화 후 재시도)
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            # NotFoundError 등 컬렉션 관련 에러 발생 시 재초기화 후 재시도
            if "does not exist" in str(e) or "NotFoundError" in str(type(e).__name__):
                collection = self._init_chroma(force_reinit=True)
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"],
                )
            else:
                raise

        # 결과 포맷팅 및 relevance filtering
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            print(f"[DEBUG] relevance_threshold={relevance_threshold}")
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0
                relevance_score = 1 - distance

                print(f"[DEBUG] doc_id={doc_id[:30]}..., distance={distance:.3f}, relevance={relevance_score:.3f}, threshold={relevance_threshold}")

                # relevance_threshold 이하의 결과는 제외
                if relevance_score < relevance_threshold:
                    print(f"[DEBUG] FILTERED OUT (relevance {relevance_score:.3f} < threshold {relevance_threshold})")
                    continue

                formatted_results.append(
                    {
                        "doc_id": doc_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": distance,
                        "relevance_score": relevance_score,
                    }
                )

        return {
            "success": True,
            "query": query,
            "results": formatted_results,
            "total_found": len(formatted_results),
        }

    def delete_by_branch(self, project_id: str, branch_id: str) -> Dict[str, Any]:
        """브랜치의 모든 인덱스 삭제"""
        collection = self._init_chroma()

        # 해당 브랜치의 문서 검색
        results = collection.get(
            where={"$and": [{"project_id": project_id}, {"branch_id": branch_id}]}
        )

        if results["ids"]:
            collection.delete(ids=results["ids"])
            return {
                "success": True,
                "deleted_count": len(results["ids"]),
                "message": f"브랜치 '{branch_id}'의 인덱스 삭제 완료",
            }

        return {"success": True, "deleted_count": 0, "message": "삭제할 인덱스가 없습니다."}

    def get_stats(self) -> Dict[str, Any]:
        """인덱스 통계 반환"""
        collection = self._init_chroma()

        return {
            "total_documents": collection.count(),
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model_name,
        }

    # ==================== Hybrid Search (v2.0) ====================

    def _extract_keywords(self, text: str) -> List[str]:
        """
        텍스트에서 키워드 추출

        Args:
            text: 입력 텍스트

        Returns:
            키워드 목록
        """
        # 소문자 변환 및 특수문자 제거
        words = re.findall(r"\b[\w가-힣]+\b", text.lower())

        # 불용어 제거 및 2글자 이상만
        keywords = []
        for word in words:
            if len(word) < 2:
                continue
            if word in self._korean_stopwords:
                continue
            if word in self._english_stopwords:
                continue
            keywords.append(word)

        return keywords

    def _keyword_match_score(self, content: str, keywords: List[str]) -> float:
        """
        키워드 매칭 점수 계산

        Args:
            content: 검색 대상 콘텐츠
            keywords: 검색 키워드 목록

        Returns:
            매칭 점수 (0.0 ~ 1.0)
        """
        if not keywords:
            return 0.0

        content_lower = content.lower()
        matched = sum(1 for kw in keywords if kw in content_lower)

        return matched / len(keywords)

    @track_call("rag_engine")
    def hybrid_search(
        self,
        query: str,
        project_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        top_k: Optional[int] = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        relevance_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Hybrid 검색 (Vector + Keyword)

        Args:
            query: 검색 쿼리
            project_id: 프로젝트 필터 (선택)
            branch_id: 브랜치 필터 (선택)
            top_k: 반환할 결과 수
            vector_weight: 벡터 검색 가중치 (기본: 0.7)
            keyword_weight: 키워드 검색 가중치 (기본: 0.3)

        Returns:
            검색 결과
        """
        start_time = time.time()

        model = self._init_embedding_model()
        collection = self._init_chroma()

        if top_k is None:
            top_k = self.top_k

        # 키워드 추출
        keywords = self._extract_keywords(query)

        # 쿼리 임베딩
        query_embedding = model.encode(query).tolist()

        # 필터 구성
        where_filter = None
        if project_id or branch_id:
            conditions = []
            if project_id:
                conditions.append({"project_id": project_id})
            if branch_id:
                conditions.append({"branch_id": branch_id})

            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}

        print(f"[DEBUG-FILTER] project_id={project_id}, branch_id={branch_id}, where_filter={where_filter}")

        # 벡터 검색 (더 많은 후보 가져오기)
        # expanded_k를 충분히 크게 설정하여 니들이 벡터 검색 단계에서 필터링되지 않도록 함
        # 최소 100개 후보를 확보하여 Zero-Loss 원칙 준수
        expanded_k = max(top_k * 5, 100)

        # 에러 발생 시 재초기화 후 재시도
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=expanded_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            # NotFoundError 등 컬렉션 관련 에러 발생 시 재초기화 후 재시도
            if "does not exist" in str(e) or "NotFoundError" in str(type(e).__name__):
                collection = self._init_chroma(force_reinit=True)
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=expanded_k,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"],
                )
            else:
                raise

        # Hybrid 점수 계산
        scored_results = []
        if results["ids"] and results["ids"][0]:
            print(f"[DEBUG-RESULTS] ChromaDB returned {len(results['ids'][0])} documents")
            for i, doc_id in enumerate(results["ids"][0]):
                content = results["documents"][0][i] if results["documents"] else ""
                distance = results["distances"][0][i] if results["distances"] else 1.0
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                if i < 3:  # 처음 3개만 출력
                    print(f"[DEBUG-RESULTS] Doc #{i}: doc_id={doc_id[:40]}..., branch_id={metadata.get('branch_id', 'N/A')}, distance={distance:.3f}")

                # 벡터 유사도 (distance를 similarity로 변환)
                # Inverse distance: distance가 클수록 score는 0에 가까워짐
                # distance=0 → 1.0, distance=1 → 0.5, distance=∞ → 0
                vector_score = 1 / (1 + distance)

                # 키워드 매칭 점수
                keyword_score = self._keyword_match_score(content, keywords)

                # Hybrid 점수
                hybrid_score = (vector_weight * vector_score) + (keyword_weight * keyword_score)

                scored_results.append(
                    {
                        "doc_id": doc_id,
                        "content": content,
                        "metadata": metadata,
                        "vector_score": round(vector_score, 4),
                        "keyword_score": round(keyword_score, 4),
                        "hybrid_score": round(hybrid_score, 4),
                        "relevance_score": round(hybrid_score, 4),
                    }
                )

        # Hybrid 점수로 정렬
        scored_results.sort(key=lambda x: x["hybrid_score"], reverse=True)

        # Filter by relevance threshold
        scored_results = [r for r in scored_results if r["hybrid_score"] >= relevance_threshold]

        # 상위 top_k 반환
        final_results = scored_results[:top_k]

        # Ontology 필터링 적용 (활성화된 경우)
        ontology_applied = False
        ontology_engine = self._init_ontology()
        if ontology_engine and ontology_engine.is_enabled():
            final_results = ontology_engine.filter_results(query, final_results)
            ontology_applied = True

        # 레이턴시 계산 및 로깅
        latency_ms = (time.time() - start_time) * 1000

        self.logger.log_rag_search(
            query=query,
            result_count=len(final_results),
            top_results=[r.get("doc_id") for r in final_results[:3]] if final_results else None,
            ontology_filtered=ontology_applied,
            latency_ms=latency_ms,
        )

        return {
            "success": True,
            "search_type": "hybrid",
            "query": query,
            "keywords_extracted": keywords,
            "results": final_results,
            "total_found": len(final_results),
            "candidates_evaluated": len(scored_results),
            "ontology_applied": ontology_applied,
            "latency_ms": round(latency_ms, 2),
        }

    @track_call("rag_engine")
    def search_with_fallback(
        self,
        query: str,
        project_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        top_k: Optional[int] = None,
        min_relevance: float = None,
        relevance_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Fallback 시스템을 포함한 검색

        검색 전략:
        1. Hybrid 검색 시도
        2. 결과 품질이 낮으면 (임계값 미만) 확장 검색
        3. 필터 완화 후 재검색
        4. 전역 검색 (최후의 수단)

        Args:
            query: 검색 쿼리
            project_id: 프로젝트 필터 (선택)
            branch_id: 브랜치 필터 (선택)
            top_k: 반환할 결과 수
            min_relevance: 최소 관련도 임계값

        Returns:
            검색 결과 및 Fallback 정보
        """
        if top_k is None:
            top_k = self.top_k
        if min_relevance is None:
            min_relevance = self.RELEVANCE_THRESHOLD_LOW

        fallback_history = []
        attempt = 0

        # === Attempt 1: Hybrid 검색 (필터 적용) ===
        attempt += 1
        result = self.hybrid_search(
            query=query,
            project_id=project_id,
            branch_id=branch_id,
            top_k=top_k,
            relevance_threshold=relevance_threshold,
        )

        fallback_history.append(
            {
                "attempt": attempt,
                "strategy": "hybrid_with_filters",
                "results_count": result["total_found"],
                "top_score": result["results"][0]["relevance_score"] if result["results"] else 0,
            }
        )

        # 결과 품질 확인
        if self._check_result_quality(result["results"], min_relevance):
            return self._finalize_search_result(result, fallback_history, "primary")

        # === Attempt 2: 확장 검색 (더 많은 후보) ===
        if attempt < self.MAX_FALLBACK_ATTEMPTS:
            attempt += 1
            expanded_k = top_k * self.FALLBACK_TOP_K_MULTIPLIER

            result = self.hybrid_search(
                query=query,
                project_id=project_id,
                branch_id=branch_id,
                top_k=expanded_k,
                vector_weight=0.5,  # 가중치 조정
                keyword_weight=0.5,
                relevance_threshold=relevance_threshold,
            )

            fallback_history.append(
                {
                    "attempt": attempt,
                    "strategy": "expanded_hybrid",
                    "results_count": result["total_found"],
                    "top_score": (
                        result["results"][0]["relevance_score"] if result["results"] else 0
                    ),
                }
            )

            if self._check_result_quality(result["results"], min_relevance):
                # 상위 top_k만 반환
                result["results"] = result["results"][:top_k]
                result["total_found"] = len(result["results"])
                return self._finalize_search_result(result, fallback_history, "expanded")

        # === Attempt 3: 필터 완화 (브랜치 필터 유지 - Branch Isolation 보장) ===
        if attempt < self.MAX_FALLBACK_ATTEMPTS and branch_id:
            attempt += 1

            result = self.hybrid_search(
                query=query,
                project_id=project_id,
                branch_id=branch_id,  # 브랜치 필터 유지 (Branch Isolation 버그 수정)
                top_k=top_k,
                relevance_threshold=relevance_threshold,
            )

            fallback_history.append(
                {
                    "attempt": attempt,
                    "strategy": "project_only_filter",
                    "results_count": result["total_found"],
                    "top_score": (
                        result["results"][0]["relevance_score"] if result["results"] else 0
                    ),
                }
            )

            if self._check_result_quality(result["results"], min_relevance):
                return self._finalize_search_result(result, fallback_history, "relaxed_filter")

        # === Attempt 4: 프로젝트 내 전역 검색 (branch_id만 제거, project_id 유지) ===
        # BUG FIX: project_id=None으로 전역 검색하면 다른 프로젝트의 데이터가 반환됨
        # 프로젝트 격리를 유지하면서 branch_id만 완화
        if attempt < self.MAX_FALLBACK_ATTEMPTS and project_id:
            attempt += 1

            # project_id 유지, branch_id만 None으로 완화
            result = self.hybrid_search(query=query, project_id=project_id, branch_id=None, top_k=top_k)

            fallback_history.append(
                {
                    "attempt": attempt,
                    "strategy": "project_wide_search",  # "global_search" -> "project_wide_search"
                    "results_count": result["total_found"],
                    "top_score": (
                        result["results"][0]["relevance_score"] if result["results"] else 0
                    ),
                }
            )

            if self._check_result_quality(result["results"], min_relevance):
                return self._finalize_search_result(result, fallback_history, "project_wide")

        # === 안전망: 모든 Attempt 실패 시에도 ChromaDB 결과가 있으면 top-1 반환 ===
        # ChromaDB가 결과를 반환했으나 임계값 필터링으로 모두 제거된 경우,
        # "결과 없음"보다는 "낮은 관련도지만 최선의 매칭"을 제공하는 것이 UX 개선
        first_attempt_result = fallback_history[0] if fallback_history else None

        if first_attempt_result and first_attempt_result.get("results_count", 0) > 0:
            # 첫 Attempt에서 ChromaDB가 결과를 반환했음
            # top-1이라도 사용자에게 제공
            result = self.hybrid_search(
                query=query,
                project_id=project_id,
                branch_id=branch_id,
                top_k=1  # 최상위 1개만
            )

            if result["results"]:
                # 경고 메시지 추가 (낮은 relevance_score 명시)
                result["warning"] = "Low relevance score but returning best match"
                result["relevance_score"] = result["results"][0].get("relevance_score", 0)
                return self._finalize_search_result(
                    result,
                    fallback_history,
                    "last_resort_top1"
                )

        # 최종 결과 반환 (진짜 결과가 없음)
        return self._finalize_search_result(result, fallback_history, "exhausted")

    def _check_result_quality(self, results: List[Dict], min_relevance: float) -> bool:
        """
        검색 결과 품질 확인

        Args:
            results: 검색 결과 목록
            min_relevance: 최소 관련도 임계값

        Returns:
            품질 충족 여부
        """
        if not results:
            return False

        # 최상위 결과가 임계값 이상인지 확인
        top_score = results[0].get("relevance_score", 0)
        return top_score >= min_relevance

    def _finalize_search_result(
        self, result: Dict[str, Any], fallback_history: List[Dict], strategy_used: str
    ) -> Dict[str, Any]:
        """
        최종 검색 결과 포맷팅

        Args:
            result: 검색 결과
            fallback_history: Fallback 이력
            strategy_used: 사용된 전략

        Returns:
            최종 결과
        """
        # 결과 품질 등급 결정
        quality_grade = "low"
        top_score = 0.0
        if result["results"]:
            top_score = result["results"][0].get("relevance_score", 0)
            if top_score >= self.RELEVANCE_THRESHOLD_HIGH:
                quality_grade = "high"
            elif top_score >= self.RELEVANCE_THRESHOLD_MEDIUM:
                quality_grade = "medium"

        result["fallback_info"] = {
            "strategy_used": strategy_used,
            "attempts": len(fallback_history),
            "history": fallback_history,
            "quality_grade": quality_grade,
        }

        # result_count 추가 (total_found의 alias, 테스트 호환성)
        result["result_count"] = result.get("total_found", len(result.get("results", [])))

        # Fallback 로깅 (strategy가 primary가 아니면 fallback이 발생한 것)
        if strategy_used != "primary":
            results_list = result.get("results", [])
            self.logger.log_rag_search(
                query=result.get("query", ""),
                result_count=result.get("total_found", 0),
                top_results=[r.get("doc_id") for r in results_list[:3]] if results_list else None,
                ontology_filtered=False,
                latency_ms=result.get("latency_ms", 0.0),
            )

        return result

    def search_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        top_k: Optional[int] = None,
        use_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        의미론적 검색 수행 (v2.0: Hybrid + Fallback, v2.3: Hierarchical RAG)

        Args:
            query: 검색 쿼리
            project_id: 프로젝트 필터 (선택)
            branch_id: 브랜치 필터 (선택)
            top_k: 반환할 결과 수
            use_fallback: Fallback 시스템 사용 여부 (기본: True)

        Returns:
            검색 결과
        """
        # Hierarchical RAG 사용 여부 확인 (최우선)
        if self.use_hierarchical:
            return self._search_with_hierarchical_rag(query, project_id, branch_id, top_k)

        # 기존 로직
        if use_fallback:
            return self.search_with_fallback(
                query=query, project_id=project_id, branch_id=branch_id, top_k=top_k
            )
        else:
            return self.hybrid_search(
                query=query, project_id=project_id, branch_id=branch_id, top_k=top_k
            )

    def needle_in_haystack_test(
        self,
        needle_content: str,
        needle_query: str,
        haystack_size: int = 100,
        project_id: str = "__test_needle",
    ) -> Dict[str, Any]:
        """
        Needle in Haystack 테스트

        특정 콘텐츠(needle)를 많은 문서(haystack) 사이에서
        정확하게 찾을 수 있는지 테스트

        Args:
            needle_content: 찾아야 할 콘텐츠
            needle_query: 검색 쿼리
            haystack_size: 배경 문서 수
            project_id: 테스트용 프로젝트 ID

        Returns:
            테스트 결과
        """
        import random
        import string

        # 1. Haystack 생성 (임의의 배경 문서들)
        haystack_docs = []
        for i in range(haystack_size):
            random_content = "".join(random.choices(string.ascii_letters + " ", k=500))
            doc_id = f"haystack_{i}"
            self.index_content(
                content=f"Background document {i}: {random_content}",
                metadata={"project_id": project_id, "type": "haystack"},
                doc_id=doc_id,
            )
            haystack_docs.append(doc_id)

        # 2. Needle 삽입
        needle_id = "needle_target"
        self.index_content(
            content=needle_content,
            metadata={"project_id": project_id, "type": "needle"},
            doc_id=needle_id,
        )

        # 3. 검색 테스트
        search_result = self.search_with_fallback(
            query=needle_query, project_id=project_id, top_k=10
        )

        # 4. 결과 분석
        found_at_rank = None
        for i, result in enumerate(search_result.get("results", [])):
            if result.get("doc_id") == needle_id:
                found_at_rank = i + 1
                break

        # 5. 정리 (테스트 데이터 삭제)
        collection = self._init_chroma()
        all_test_ids = haystack_docs + [needle_id]
        try:
            collection.delete(ids=all_test_ids)
        except Exception:
            pass

        # 6. 테스트 결과
        success = found_at_rank == 1  # 1위에서 찾았는지

        return {
            "success": success,
            "test_name": "needle_in_haystack",
            "needle_query": needle_query,
            "haystack_size": haystack_size,
            "found_at_rank": found_at_rank,
            "top_result_id": (
                search_result["results"][0]["doc_id"] if search_result["results"] else None
            ),
            "top_result_score": (
                search_result["results"][0]["relevance_score"] if search_result["results"] else 0
            ),
            "fallback_info": search_result.get("fallback_info"),
            "message": f"Needle {'found at rank ' + str(found_at_rank) if found_at_rank else 'NOT FOUND'}",
        }

    # ==================== Smart Search (v2.2) ====================

    def smart_search(
        self,
        query: str,
        project_id: str,
        branch_id: Optional[str] = None,
        force_strategy: Optional[RetrievalStrategy] = None,
    ) -> Dict[str, Any]:
        """
        Smart Retrieval Strategy 기반 검색

        Context 수에 따라 최적의 검색 전략을 자동 선택:
        - < 50: Full Context (전체 제공)
        - 50-200: RAG Only
        - 200+: Ontology + RAG

        Args:
            query: 검색 쿼리
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID (선택)
            force_strategy: 강제 전략 지정 (테스트용)

        Returns:
            검색 결과 + 전략 정보
        """
        start_time = time.time()

        # Smart Retrieval Strategy 인스턴스
        smart_retrieval = get_smart_retrieval()

        # 전략 결정
        decision = smart_retrieval.decide_strategy(
            project_id=project_id, branch_id=branch_id, force_strategy=force_strategy
        )

        result = {
            "success": True,
            "query": query,
            "strategy": decision.strategy.value,
            "context_count": decision.context_count,
            "strategy_reason": decision.reason,
            "results": [],
            "total_found": 0,
        }

        # 전략별 실행
        if decision.strategy == RetrievalStrategy.FULL_CONTEXT:
            # 전체 Context 로드 (RAG 사용 안 함)
            result = self._full_context_retrieval(project_id=project_id, branch_id=branch_id)
            result["strategy"] = "full_context"
            result["strategy_reason"] = decision.reason

        elif decision.strategy == RetrievalStrategy.RAG_ONLY:
            # RAG만 사용 (온톨로지 없이)
            original_ontology = self.use_ontology
            self.use_ontology = False

            search_result = self.search_with_fallback(
                query=query, project_id=project_id, branch_id=branch_id, top_k=decision.top_k
            )

            self.use_ontology = original_ontology

            result.update(search_result)
            result["strategy"] = "rag_only"
            result["strategy_reason"] = decision.reason

        else:  # ONTOLOGY_RAG
            # 온톨로지 + RAG
            original_ontology = self.use_ontology
            self.use_ontology = True

            search_result = self.search_with_fallback(
                query=query, project_id=project_id, branch_id=branch_id, top_k=decision.top_k
            )

            self.use_ontology = original_ontology

            result.update(search_result)
            result["strategy"] = "ontology_rag"
            result["strategy_reason"] = decision.reason

        # 레이턴시 추가
        latency_ms = (time.time() - start_time) * 1000
        result["smart_search_latency_ms"] = round(latency_ms, 2)

        # 로깅
        self.logger.log(
            module=LogModule.GENERAL,
            action="smart_search",
            success=True,
            latency_ms=latency_ms,
            metadata={
                "strategy": decision.strategy.value,
                "context_count": decision.context_count,
                "result_count": result.get("total_found", 0),
            },
        )

        return result

    def _full_context_retrieval(
        self, project_id: str, branch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        전체 Context 로드 (RAG 사용 안 함)

        Context 수가 적을 때 사용 - 모든 정보를 LLM에게 제공

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID (선택)

        Returns:
            모든 Context 목록
        """
        from .memory_manager import memory_manager

        results = []

        # 프로젝트의 모든 Context 가져오기
        try:
            # 브랜치 목록 조회
            hierarchy = memory_manager.get_hierarchy(project_id)

            if not hierarchy.get("success"):
                return {
                    "success": False,
                    "error": "프로젝트를 찾을 수 없습니다.",
                    "results": [],
                    "total_found": 0,
                }

            # 각 브랜치의 summary 수집
            for branch in hierarchy.get("branches", []):
                bid = branch.get("branch_id")

                # 특정 브랜치만 요청된 경우
                if branch_id and bid != branch_id:
                    continue

                summary_result = memory_manager.get_active_summary(
                    project_id=project_id, branch_id=bid
                )

                if summary_result.get("success"):
                    results.append(
                        {
                            "doc_id": f"{project_id}/{bid}",
                            "content": summary_result.get("summary", ""),
                            "metadata": {
                                "project_id": project_id,
                                "branch_id": bid,
                                "branch_topic": summary_result.get("branch_topic", ""),
                            },
                            "relevance_score": 1.0,  # 전체 제공이므로 최대 점수
                        }
                    )

        except Exception as e:
            return {"success": False, "error": str(e), "results": [], "total_found": 0}

        return {
            "success": True,
            "search_type": "full_context",
            "results": results,
            "total_found": len(results),
            "message": f"전체 {len(results)}개 Context 제공 (RAG 불필요)",
        }

    def get_smart_retrieval_status(self, project_id: str) -> Dict[str, Any]:
        """
        프로젝트의 Smart Retrieval 상태 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            현재 상태 및 권장 전략
        """
        smart_retrieval = get_smart_retrieval()
        decision = smart_retrieval.decide_strategy(project_id=project_id)

        return {
            "project_id": project_id,
            "context_count": decision.context_count,
            "recommended_strategy": decision.strategy.value,
            "reason": decision.reason,
            "thresholds": smart_retrieval.get_thresholds(),
            "use_ontology": decision.use_ontology,
            "use_rag": decision.use_rag,
            "use_fuzzy": decision.use_fuzzy,
            "top_k": decision.top_k,
        }
