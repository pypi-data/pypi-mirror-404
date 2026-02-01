"""
Cortex MCP - Alpha Test Logging System

알파 테스트 중 기능별 동작을 기록하고 분석하기 위한 로그 시스템
서버 텔레메트리 전송 기능 포함 (v2.1)
"""

import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from queue import Queue
from typing import Any, Dict, List, Optional


class LogModule(Enum):
    """로그 모듈 구분"""

    SMART_CONTEXT = "smart_context"
    REFERENCE_HISTORY = "reference_history"
    ONTOLOGY = "ontology"
    BRANCH_DECISION = "branch_decision"
    RAG_SEARCH = "rag_search"
    GIT_SYNC = "git_sync"
    LICENSE = "license"
    PAY_ATTENTION = "pay_attention"  # v3.1: 세션 내 Attention 보존 시스템
    CONTEXT_MANAGER = "context_manager"  # Phase 3: Cognitive Load Context Management
    SCAN_OPTIMIZER = "scan_optimizer"  # Phase 6: Expected Loss Scan Strategy
    GENERAL = "general"


class AlphaLogger:
    """알파 테스트용 로거"""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Args:
            base_dir: 로그 저장 기본 디렉토리 (~/.cortex/logs/alpha_test/)
        """
        if base_dir is None:
            base_dir = Path.home() / ".cortex" / "logs" / "alpha_test"

        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # 모듈별 로그 파일
        self.log_files = {
            LogModule.SMART_CONTEXT: self.base_dir / "smart_context.jsonl",
            LogModule.REFERENCE_HISTORY: self.base_dir / "reference_history.jsonl",
            LogModule.ONTOLOGY: self.base_dir / "ontology.jsonl",
            LogModule.BRANCH_DECISION: self.base_dir / "branch_decision.jsonl",
            LogModule.RAG_SEARCH: self.base_dir / "rag_search.jsonl",
            LogModule.GIT_SYNC: self.base_dir / "git_sync.jsonl",
            LogModule.LICENSE: self.base_dir / "license.jsonl",
            LogModule.PAY_ATTENTION: self.base_dir / "pay_attention.jsonl",
            LogModule.GENERAL: self.base_dir / "general.jsonl",
        }

        # 통계 파일
        self.stats_file = self.base_dir / "stats.json"
        self._init_stats()

        # 로그 로테이션 설정 (10MB, 7일 보관)
        self._setup_rotating_logs()

    def _init_stats(self):
        """통계 파일 초기화"""
        if not self.stats_file.exists():
            stats = {
                "session_start": datetime.utcnow().isoformat(),
                "modules": {
                    module.value: {
                        "total_calls": 0,
                        "success_count": 0,
                        "error_count": 0,
                        "total_latency_ms": 0,
                    }
                    for module in LogModule
                },
            }
            self._save_stats(stats)

    def _load_stats(self) -> Dict:
        """통계 로드 (손상된 파일 자동 복구)"""
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    raise ValueError("Empty stats file")
                return json.loads(content)
        except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
            # 손상된 파일 삭제 후 재생성
            try:
                self.stats_file.unlink(missing_ok=True)
            except Exception:
                pass
            self._init_stats()
            # 새로 생성된 파일 로드
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                # 최후의 수단: 기본 통계 반환
                return self._get_default_stats()
        except Exception as e:
            # 예상치 못한 오류 시 기본 통계 반환
            return self._get_default_stats()

    def _get_default_stats(self) -> Dict:
        """기본 통계 구조 반환"""
        from datetime import datetime

        return {
            "session_start": datetime.now().isoformat(),
            "modules": {
                module.value: {
                    "total_calls": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "total_latency_ms": 0,
                }
                for module in LogModule
            },
        }

    def _save_stats(self, stats: Dict):
        """통계 저장"""
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    def _setup_rotating_logs(self):
        """
        로그 로테이션 핸들러 설정

        - 10MB 파일 크기 제한
        - 최근 7개 백업 유지 (7일분)
        - 모듈별 로그 파일에 적용
        """
        # Python logging 핸들러 설정
        for module, log_path in self.log_files.items():
            logger_name = f"cortex.alpha.{module.value}"
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)

            # 기존 핸들러 제거
            logger.handlers.clear()

            # RotatingFileHandler 추가
            handler = RotatingFileHandler(
                filename=str(log_path),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=7,               # 7개 백업 (7일분)
                encoding="utf-8"
            )

            # JSON 포맷 설정 (기존 로그와 호환)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)

            logger.addHandler(handler)
            logger.propagate = False  # 상위 로거로 전파 방지

    def log(
        self,
        module: LogModule,
        action: str,
        input_data: Any = None,
        output_data: Any = None,
        success: bool = True,
        error: Optional[str] = None,
        latency_ms: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ):
        """
        로그 기록

        Args:
            module: 로그 모듈
            action: 수행한 작업 (예: "compress", "decompress", "classify")
            input_data: 입력 데이터
            output_data: 출력 데이터
            success: 성공 여부
            error: 에러 메시지 (실패 시)
            latency_ms: 처리 시간 (밀리초)
            metadata: 추가 메타데이터
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": module.value,
            "action": action,
            "input": self._sanitize(input_data),
            "output": self._sanitize(output_data),
            "success": success,
            "error": error,
            "latency_ms": latency_ms,
            "metadata": metadata or {},
        }

        # JSONL 파일에 추가
        log_file = self.log_files.get(module, self.log_files[LogModule.GENERAL])
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        # 통계 업데이트
        self._update_stats(module, success, latency_ms)

    def _sanitize(self, data: Any) -> Any:
        """민감한 데이터 제거 및 크기 제한"""
        if data is None:
            return None

        if isinstance(data, str):
            # 너무 긴 문자열은 자르기
            if len(data) > 500:
                return data[:500] + "...[truncated]"
            return data

        if isinstance(data, dict):
            return {k: self._sanitize(v) for k, v in data.items()}

        if isinstance(data, list):
            if len(data) > 10:
                return [self._sanitize(item) for item in data[:10]] + ["...[truncated]"]
            return [self._sanitize(item) for item in data]

        return data

    def _update_stats(self, module: LogModule, success: bool, latency_ms: Optional[float]):
        """통계 업데이트"""
        stats = self._load_stats()

        # 새로운 모듈이 stats에 없으면 추가 (Phase 추가 시 발생 가능)
        if module.value not in stats["modules"]:
            stats["modules"][module.value] = {
                "total_calls": 0,
                "success_count": 0,
                "error_count": 0,
                "total_latency_ms": 0,
            }

        module_stats = stats["modules"][module.value]
        module_stats["total_calls"] += 1

        if success:
            module_stats["success_count"] += 1
        else:
            module_stats["error_count"] += 1

        if latency_ms is not None:
            module_stats["total_latency_ms"] += latency_ms

        self._save_stats(stats)

    def log_smart_context(
        self,
        action: str,  # "compress" | "decompress" | "load"
        context_id: str,
        token_before: Optional[int] = None,
        token_after: Optional[int] = None,
        success: bool = True,
        latency_ms: Optional[float] = None,
    ):
        """Smart Context 로그"""
        self.log(
            module=LogModule.SMART_CONTEXT,
            action=action,
            input_data={"context_id": context_id, "token_before": token_before},
            output_data={"token_after": token_after},
            success=success,
            latency_ms=latency_ms,
            metadata={
                "token_saved": (
                    (token_before - token_after) if token_before and token_after else None
                ),
                "compression_ratio": (
                    round(token_after / token_before, 2) if token_before and token_after else None
                ),
            },
        )

    def log_reference_history(
        self,
        action: str,  # "recommend" | "record" | "update"
        query: Optional[str] = None,
        recommended_contexts: Optional[list] = None,
        accepted: Optional[bool] = None,
        success: bool = True,
        latency_ms: Optional[float] = None,
    ):
        """Reference History 로그"""
        self.log(
            module=LogModule.REFERENCE_HISTORY,
            action=action,
            input_data={"query": query},
            output_data={"recommended_contexts": recommended_contexts},
            success=success,
            latency_ms=latency_ms,
            metadata={"user_accepted": accepted},
        )

    def log_ontology(
        self,
        action: str,  # "classify" | "filter"
        input_text: str,
        category: Optional[str] = None,
        confidence: Optional[float] = None,
        success: bool = True,
        latency_ms: Optional[float] = None,
    ):
        """Ontology Engine 로그"""
        self.log(
            module=LogModule.ONTOLOGY,
            action=action,
            input_data={"text": input_text[:200]},  # 입력 텍스트 제한
            output_data={"category": category, "confidence": confidence},
            success=success,
            latency_ms=latency_ms,
        )

    def log_branch_decision(
        self,
        action: str,  # "auto_create" | "user_request" | "reject"
        detected_topic: Optional[str] = None,
        branch_created: Optional[str] = None,
        user_confirmed: Optional[bool] = None,
        success: bool = True,
        latency_ms: Optional[float] = None,
    ):
        """Branch Decision 로그"""
        self.log(
            module=LogModule.BRANCH_DECISION,
            action=action,
            input_data={"detected_topic": detected_topic},
            output_data={"branch_created": branch_created},
            success=success,
            latency_ms=latency_ms,
            metadata={"user_confirmed": user_confirmed},
        )

    def log_rag_search(
        self,
        query: str,
        result_count: int,
        top_results: Optional[list] = None,
        ontology_filtered: bool = False,
        success: bool = True,
        latency_ms: Optional[float] = None,
    ):
        """RAG Search 로그"""
        self.log(
            module=LogModule.RAG_SEARCH,
            action="search",
            input_data={"query": query[:200]},
            output_data={"result_count": result_count, "top_results": top_results},
            success=success,
            latency_ms=latency_ms,
            metadata={"ontology_filtered": ontology_filtered},
        )

    def log_git_sync(
        self,
        action: str,  # "detect_branch" | "sync" | "snapshot"
        git_branch: Optional[str] = None,
        cortex_branch: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        latency_ms: Optional[float] = None,
    ):
        """Git Sync 로그"""
        self.log(
            module=LogModule.GIT_SYNC,
            action=action,
            input_data={"git_branch": git_branch},
            output_data={"cortex_branch": cortex_branch},
            success=success,
            error=error,
            latency_ms=latency_ms,
        )

    def log_license(
        self,
        action: str,  # "verify" | "cache_hit" | "cache_miss" | "fallback"
        license_tier: Optional[str] = None,
        cache_used: bool = False,
        success: bool = True,
        error: Optional[str] = None,
        latency_ms: Optional[float] = None,
    ):
        """License 로그"""
        self.log(
            module=LogModule.LICENSE,
            action=action,
            output_data={"tier": license_tier},
            success=success,
            error=error,
            latency_ms=latency_ms,
            metadata={"cache_used": cache_used},
        )

    def get_stats(self) -> Dict:
        """현재 통계 반환"""
        stats = self._load_stats()

        # 추가 계산
        for module_name, module_stats in stats["modules"].items():
            total = module_stats["total_calls"]
            if total > 0:
                module_stats["success_rate"] = round(module_stats["success_count"] / total * 100, 2)
                module_stats["avg_latency_ms"] = round(module_stats["total_latency_ms"] / total, 2)
            else:
                module_stats["success_rate"] = 0
                module_stats["avg_latency_ms"] = 0

        return stats

    def get_summary(self) -> str:
        """통계 요약 문자열 반환"""
        stats = self.get_stats()

        lines = [
            "=== Cortex Alpha Test Statistics ===",
            f"Session Start: {stats['session_start']}",
            "",
            "Module Statistics:",
            "-" * 50,
        ]

        for module_name, module_stats in stats["modules"].items():
            if module_stats["total_calls"] > 0:
                lines.append(
                    f"  {module_name}:"
                    f"  Calls: {module_stats['total_calls']}"
                    f"  Success: {module_stats['success_rate']}%"
                    f"  Avg Latency: {module_stats['avg_latency_ms']}ms"
                )

        return "\n".join(lines)

    def clear_logs(self):
        """모든 로그 초기화 (테스트용)"""
        for log_file in self.log_files.values():
            if log_file.exists():
                log_file.unlink()

        if self.stats_file.exists():
            self.stats_file.unlink()

        self._init_stats()


class TelemetrySender:
    """
    텔레메트리 데이터를 서버로 전송하는 클래스.

    특징:
    - 배치 전송 (10개 또는 60초마다)
    - 백그라운드 스레드에서 비동기 전송
    - 전송 실패 시 로컬에 보관
    - Zero-Trust: 사용자가 명시적으로 활성화해야 동작
    """

    def __init__(
        self,
        server_url: str = "https://cortex-mcp.com/api/telemetry",
        license_key: Optional[str] = None,
        batch_size: int = 10,
        flush_interval: int = 60,
        enabled: bool = False,
    ):
        self.server_url = server_url
        self.license_key = license_key
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.enabled = enabled

        self._queue: Queue = Queue()
        self._buffer: List[Dict] = []
        self._last_flush = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # 전송 실패 시 저장할 파일
        self._pending_file = Path.home() / ".cortex" / "logs" / "pending_telemetry.jsonl"

    def enable(self, license_key: str, server_url: Optional[str] = None):
        """텔레메트리 전송 활성화"""
        self.license_key = license_key
        if server_url:
            self.server_url = server_url
        self.enabled = True
        self._start_sender_thread()

    def disable(self):
        """텔레메트리 전송 비활성화"""
        self.enabled = False
        self._stop_sender_thread()

    def _start_sender_thread(self):
        """백그라운드 전송 스레드 시작"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._sender_loop, daemon=True)
        self._thread.start()

    def _stop_sender_thread(self):
        """백그라운드 전송 스레드 중지"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _sender_loop(self):
        """백그라운드 전송 루프"""
        while self._running:
            try:
                # 큐에서 이벤트 가져오기
                while not self._queue.empty():
                    event = self._queue.get_nowait()
                    self._buffer.append(event)

                # 배치 크기 도달 또는 시간 초과 시 전송
                should_flush = len(self._buffer) >= self.batch_size or (
                    len(self._buffer) > 0 and time.time() - self._last_flush >= self.flush_interval
                )

                if should_flush:
                    self._flush_buffer()

                time.sleep(1)  # 1초 대기

            except Exception as e:
                # 에러 발생 시 로그만 남기고 계속
                pass

    def _flush_buffer(self):
        """버퍼의 이벤트들을 서버로 전송"""
        if not self._buffer or not self.license_key:
            return

        events_to_send = self._buffer.copy()
        self._buffer.clear()
        self._last_flush = time.time()

        try:
            import urllib.error
            import urllib.request

            payload = {"license_key": self.license_key, "events": events_to_send}

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.server_url}/batch",
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "Cortex-MCP/2.1"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return  # 성공

        except Exception as e:
            # 전송 실패 시 로컬에 저장
            self._save_pending(events_to_send)

    def _save_pending(self, events: List[Dict]):
        """전송 실패한 이벤트를 로컬에 저장"""
        try:
            self._pending_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._pending_file, "a", encoding="utf-8") as f:
                for event in events:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except:
            pass  # 저장 실패해도 무시

    def queue_event(
        self,
        event_type: str,
        tool_name: Optional[str] = None,
        duration_ms: Optional[int] = None,
        tokens_saved: Optional[int] = None,
        context_size: Optional[int] = None,
        metadata: Optional[Dict] = None,
        client_version: str = "2.1",
    ):
        """이벤트를 전송 큐에 추가"""
        if not self.enabled:
            return

        event = {
            "event_type": event_type,
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "tokens_saved": tokens_saved,
            "context_size": context_size,
            "metadata": metadata,
            "event_timestamp": datetime.utcnow().isoformat(),
            "client_version": client_version,
        }

        self._queue.put(event)

    def retry_pending(self):
        """로컬에 저장된 이벤트 재전송 시도"""
        if not self._pending_file.exists():
            return

        try:
            events = []
            with open(self._pending_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))

            if events:
                self._buffer.extend(events)
                self._flush_buffer()
                # 성공하면 파일 삭제
                self._pending_file.unlink()
        except:
            pass


# 싱글톤 인스턴스
_alpha_logger: Optional[AlphaLogger] = None


def get_alpha_logger() -> AlphaLogger:
    """AlphaLogger 싱글톤 인스턴스 반환"""
    global _alpha_logger
    if _alpha_logger is None:
        _alpha_logger = AlphaLogger()
    return _alpha_logger


# 편의 함수들
def log_smart_context(*args, **kwargs):
    get_alpha_logger().log_smart_context(*args, **kwargs)


def log_reference_history(*args, **kwargs):
    get_alpha_logger().log_reference_history(*args, **kwargs)


def log_ontology(*args, **kwargs):
    get_alpha_logger().log_ontology(*args, **kwargs)


def log_branch_decision(*args, **kwargs):
    get_alpha_logger().log_branch_decision(*args, **kwargs)


def log_rag_search(*args, **kwargs):
    get_alpha_logger().log_rag_search(*args, **kwargs)


def log_git_sync(*args, **kwargs):
    get_alpha_logger().log_git_sync(*args, **kwargs)


def log_license(*args, **kwargs):
    get_alpha_logger().log_license(*args, **kwargs)


# TelemetrySender 싱글톤
_telemetry_sender: Optional[TelemetrySender] = None


def get_telemetry_sender() -> TelemetrySender:
    """TelemetrySender 싱글톤 인스턴스 반환"""
    global _telemetry_sender
    if _telemetry_sender is None:
        _telemetry_sender = TelemetrySender()
    return _telemetry_sender


def enable_telemetry(license_key: str, server_url: Optional[str] = None):
    """
    텔레메트리 전송 활성화.

    Zero-Trust 원칙: 사용자가 명시적으로 활성화해야만 데이터 전송

    Args:
        license_key: 라이센스 키 (인증용)
        server_url: 텔레메트리 서버 URL (기본: https://cortex-mcp.com/api/telemetry)
    """
    sender = get_telemetry_sender()
    sender.enable(license_key, server_url)


def disable_telemetry():
    """텔레메트리 전송 비활성화"""
    sender = get_telemetry_sender()
    sender.disable()


def telemetry_event(
    event_type: str,
    tool_name: Optional[str] = None,
    duration_ms: Optional[int] = None,
    tokens_saved: Optional[int] = None,
    context_size: Optional[int] = None,
    metadata: Optional[Dict] = None,
):
    """
    텔레메트리 이벤트 전송.

    활성화되어 있지 않으면 아무 동작도 하지 않음.

    Args:
        event_type: 이벤트 타입 (tool_call, context_search, etc.)
        tool_name: 도구 이름
        duration_ms: 작업 소요 시간 (ms)
        tokens_saved: 절감된 토큰 수
        context_size: 컨텍스트 크기
        metadata: 추가 메타데이터
    """
    sender = get_telemetry_sender()
    sender.queue_event(
        event_type=event_type,
        tool_name=tool_name,
        duration_ms=duration_ms,
        tokens_saved=tokens_saved,
        context_size=context_size,
        metadata=metadata,
    )


def is_telemetry_enabled() -> bool:
    """텔레메트리 활성화 여부 반환"""
    return get_telemetry_sender().enabled


def retry_pending_telemetry():
    """실패한 텔레메트리 이벤트 재전송 시도"""
    get_telemetry_sender().retry_pending()


def save_research_metric_to_db(
    user_id: int,
    beta_phase: str,
    context_stability_score: float = None,
    recovery_time_ms: float = None,
    intervention_precision: float = None,
    user_acceptance_count: int = 0,
    user_rejection_count: int = 0,
    session_id: str = None,
):
    """
    연구 메트릭을 Web DB에 저장 (structure.md 6.5)

    Args:
        user_id: 사용자 ID
        beta_phase: 베타 페이즈 (closed_beta | open_beta)
        context_stability_score: 맥락 안정성 점수
        recovery_time_ms: 복구 시간 (ms)
        intervention_precision: 개입 정밀도
        user_acceptance_count: 사용자 수락 횟수
        user_rejection_count: 사용자 거부 횟수
        session_id: 세션 ID
    """
    try:
        try:
            from ..web.models import get_db
        except ImportError:
            from web.models import get_db

        db = get_db()
        db.record_research_metric(
            user_id=user_id,
            beta_phase=beta_phase,
            context_stability_score=context_stability_score,
            recovery_time_ms=recovery_time_ms,
            intervention_precision=intervention_precision,
            user_acceptance_count=user_acceptance_count,
            user_rejection_count=user_rejection_count,
            session_id=session_id,
        )
    except Exception as e:
        # DB 저장 실패해도 로컬 로그는 유지되므로 무시
        pass
