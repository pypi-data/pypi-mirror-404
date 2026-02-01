"""
Background Processor - Multiprocessing 기반 백그라운드 작업 처리

GIL(Global Interpreter Lock) 우회를 위해 multiprocessing 사용
2 Workers로 CPU-bound 작업(Embedding 생성, RAG 인덱싱) 병렬 처리
"""
from multiprocessing import Pool, current_process
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class BackgroundProcessor:
    """
    Multiprocessing 기반 백그라운드 작업 처리기

    특징:
    - 2 Workers로 고정 (메모리 안정성)
    - Pool 패턴으로 Worker 재사용
    - Non-blocking: 작업 제출 후 즉시 반환
    """

    _instance: Optional['BackgroundProcessor'] = None

    def __init__(self, workers: int = 2):
        """
        Args:
            workers: Worker 프로세스 수 (기본: 2)
        """
        if BackgroundProcessor._instance is not None:
            raise RuntimeError("BackgroundProcessor는 싱글톤입니다. get_instance() 사용하세요.")

        self.workers = workers
        self.pool: Optional[Pool] = None
        self._initialize_pool()

        logger.info(f"[BackgroundProcessor] {workers} workers initialized")
        logger.info(f"[BackgroundProcessor] Expected memory: ~{470 * workers + 500}MB")

    def _initialize_pool(self):
        """Worker Pool 초기화"""
        try:
            self.pool = Pool(
                processes=self.workers,
                initializer=self._worker_init,
                maxtasksperchild=100  # 메모리 누수 방지: 100개 작업 후 재시작
            )
            logger.info(f"[BackgroundProcessor] Pool created with {self.workers} workers")
        except Exception as e:
            logger.error(f"[BackgroundProcessor] Pool 초기화 실패: {e}")
            raise

    @staticmethod
    def _worker_init():
        """
        Worker 프로세스 초기화
        각 Worker가 시작될 때 1회 실행
        """
        pid = os.getpid()
        process_name = current_process().name
        logger.info(f"[Worker-{process_name}] PID {pid} 시작됨")

    def submit_task(self, func, *args, **kwargs) -> None:
        """
        백그라운드 작업 제출 (Non-blocking)

        Args:
            func: 실행할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자

        Returns:
            None (즉시 반환)
        """
        if self.pool is None:
            logger.error("[BackgroundProcessor] Pool이 초기화되지 않음")
            return

        try:
            # apply_async: Non-blocking (즉시 반환)
            self.pool.apply_async(
                func,
                args=args,
                kwds=kwargs,
                error_callback=self._error_callback
            )
            logger.debug(f"[BackgroundProcessor] Task submitted: {func.__name__}")
        except Exception as e:
            logger.error(f"[BackgroundProcessor] Task 제출 실패: {e}")

    def _error_callback(self, error):
        """Worker에서 발생한 에러 처리"""
        logger.error(f"[BackgroundProcessor] Worker error: {error}")

    def shutdown(self, timeout: int = 30):
        """
        백그라운드 프로세서 종료

        Args:
            timeout: 대기 시간 (초)
        """
        if self.pool is None:
            return

        logger.info("[BackgroundProcessor] Shutting down...")

        try:
            self.pool.close()  # 새 작업 거부
            self.pool.join(timeout=timeout)  # 실행 중인 작업 완료 대기
            logger.info("[BackgroundProcessor] Shutdown complete")
        except Exception as e:
            logger.error(f"[BackgroundProcessor] Shutdown 중 오류: {e}")
            self.pool.terminate()  # 강제 종료
        finally:
            self.pool = None

    @classmethod
    def get_instance(cls, workers: int = 2) -> 'BackgroundProcessor':
        """
        싱글톤 인스턴스 반환

        Args:
            workers: Worker 수 (최초 생성 시에만 사용)

        Returns:
            BackgroundProcessor 인스턴스
        """
        if cls._instance is None:
            cls._instance = cls(workers=workers)
        return cls._instance

    def __del__(self):
        """소멸자: Pool 정리"""
        if self.pool is not None:
            try:
                self.pool.terminate()
            except:
                pass


# Worker 함수들 (별도 프로세스에서 실행)

def worker_indexing_task(
    content: str,
    metadata: Dict[str, Any],
    project_id: str,
    branch_id: str,
    timestamp: str,
    role: str
) -> Dict[str, Any]:
    """
    RAG 인덱싱 작업 (Worker 프로세스에서 실행)

    이 함수는 별도 프로세스에서 실행되므로:
    - 독립적인 메모리 공간
    - 독립적인 GIL
    - 모델을 여기서 로드해야 함

    Args:
        content: 인덱싱할 내용
        metadata: 메타데이터
        project_id: 프로젝트 ID
        branch_id: 브랜치 ID
        timestamp: 타임스탬프
        role: 역할 (user/assistant)

    Returns:
        작업 결과
    """
    import sys
    import time
    from pathlib import Path

    # Worker 프로세스는 별도 프로세스이므로 sys.path 설정 필요
    cortex_root = Path(__file__).parent.parent
    if str(cortex_root) not in sys.path:
        sys.path.insert(0, str(cortex_root))

    start_time = time.time()

    pid = os.getpid()
    process_name = current_process().name

    logger.info(f"[Worker-{process_name}] PID {pid} - Indexing task started")

    try:
        # 1. RAG Engine 초기화 (각 Worker마다)
        from core.rag_engine import RAGEngine
        rag_engine = RAGEngine(project_id=project_id)

        # 2. Embedding 생성 및 인덱싱
        rag_engine.add_context(
            context_id=f"{branch_id}_{timestamp}",
            content=content,
            metadata=metadata
        )

        # 3. Ontology 분류 (Feature Flag 확인)
        try:
            from config import config
            if config.is_feature_enabled("semantic_web_enabled"):
                from core.semantic_web import get_semantic_web
                semantic_web = get_semantic_web(project_id)

                # 내용 기반 관계 추출
                relations = semantic_web.extract_relations_from_content(
                    content=content,
                    context_id=f"{branch_id}_{timestamp}"
                )
                logger.debug(f"[Worker-{process_name}] {len(relations)} relations extracted")
        except Exception as e:
            logger.warning(f"[Worker-{process_name}] Ontology 분류 실패: {e}")

        elapsed = time.time() - start_time
        logger.info(f"[Worker-{process_name}] Indexing completed in {elapsed:.2f}s")

        return {
            "success": True,
            "elapsed": elapsed,
            "worker_pid": pid
        }

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Worker-{process_name}] Indexing failed: {e}")

        return {
            "success": False,
            "error": str(e),
            "elapsed": elapsed,
            "worker_pid": pid
        }


# 전역 인스턴스 (Lazy initialization)
_processor: Optional[BackgroundProcessor] = None


def get_background_processor() -> BackgroundProcessor:
    """
    전역 BackgroundProcessor 인스턴스 반환

    Returns:
        BackgroundProcessor 싱글톤 인스턴스
    """
    global _processor
    if _processor is None:
        _processor = BackgroundProcessor.get_instance(workers=2)
    return _processor


def shutdown_background_processor():
    """전역 BackgroundProcessor 종료"""
    global _processor
    if _processor is not None:
        _processor.shutdown()
        _processor = None
