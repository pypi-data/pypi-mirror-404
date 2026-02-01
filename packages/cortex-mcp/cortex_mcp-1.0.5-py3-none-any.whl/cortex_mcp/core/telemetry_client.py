"""
Cortex MCP - Telemetry Client
웹 서버 API와 통합된 텔레메트리 클라이언트

자동으로 사용 지표, 에러 로그, 연구 메트릭을 수집하고 전송합니다.
"""

import json
import logging
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Dict, List, Optional
import urllib.request
import urllib.error


logger = logging.getLogger(__name__)


class TelemetryClient:
    """
    Cortex 웹 서버와 통합된 텔레메트리 클라이언트

    기능:
    - 모듈별 사용 통계 자동 집계 및 전송 (/api/telemetry)
    - 에러 발생 시 즉시 전송 (/api/errors)
    - 연구 메트릭 자동 수집 및 전송 (/api/research_metrics)
    """

    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        license_key: Optional[str] = None,
        enabled: bool = False,
        flush_interval: int = 60,  # 60초마다 전송
        project_id: Optional[str] = None,  # v2: 프로젝트 ID
    ):
        self.server_url = server_url.rstrip("/")
        self.license_key = license_key
        self.enabled = enabled
        self.flush_interval = flush_interval
        self.current_project_id = project_id  # v2: 현재 프로젝트 ID

        # 모듈별 통계 집계 ((module_name, project_id) -> stats)
        # v2: project_id를 키에 포함하여 프로젝트별 통계 분리
        self._module_stats = defaultdict(lambda: {
            "total_calls": 0,
            "success_count": 0,
            "error_count": 0,
            "total_latency_ms": 0.0,
        })

        # 에러 큐 (즉시 전송)
        self._error_queue: Queue = Queue()

        # 연구 메트릭 큐
        self._research_queue: Queue = Queue()

        # 백그라운드 스레드
        self._running = False
        self._stats_thread: Optional[threading.Thread] = None
        self._error_thread: Optional[threading.Thread] = None
        self._research_thread: Optional[threading.Thread] = None

        # 통계 락
        self._stats_lock = threading.Lock()

        # 마지막 전송 시간
        self._last_flush = time.time()

    def enable(self, license_key: str, server_url: Optional[str] = None):
        """텔레메트리 활성화"""
        self.license_key = license_key
        if server_url:
            self.server_url = server_url.rstrip("/")
        self.enabled = True
        self._start_threads()

    def disable(self):
        """텔레메트리 비활성화"""
        self.enabled = False
        self._stop_threads()

    def _start_threads(self):
        """백그라운드 스레드 시작"""
        if self._running:
            return

        self._running = True

        # 통계 전송 스레드
        self._stats_thread = threading.Thread(target=self._stats_sender_loop, daemon=True)
        self._stats_thread.start()

        # 에러 전송 스레드
        self._error_thread = threading.Thread(target=self._error_sender_loop, daemon=True)
        self._error_thread.start()

        # 연구 메트릭 전송 스레드
        self._research_thread = threading.Thread(target=self._research_sender_loop, daemon=True)
        self._research_thread.start()

    def _stop_threads(self):
        """백그라운드 스레드 중지"""
        self._running = False

        # 남은 데이터 즉시 전송
        self._flush_stats()

        if self._stats_thread:
            self._stats_thread.join(timeout=5)
        if self._error_thread:
            self._error_thread.join(timeout=5)
        if self._research_thread:
            self._research_thread.join(timeout=5)

    def record_call(
        self,
        module_name: str,
        success: bool = True,
        latency_ms: float = 0.0,
        project_id: Optional[str] = None  # v2: 프로젝트 ID (선택적)
    ):
        """
        모듈 호출 기록

        Args:
            module_name: 모듈 이름 (memory_manager, rag_engine 등)
            success: 성공 여부
            latency_ms: 처리 시간 (밀리초)
            project_id: 프로젝트 ID (선택적, 없으면 current_project_id 사용)
        """
        if not self.enabled:
            return

        # v2: project_id 결정 (파라미터 우선, 없으면 current_project_id)
        effective_project_id = project_id or self.current_project_id

        # v2: (module_name, project_id) 튜플을 키로 사용
        stats_key = (module_name, effective_project_id)

        with self._stats_lock:
            stats = self._module_stats[stats_key]
            stats["total_calls"] += 1
            if success:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1
            stats["total_latency_ms"] += latency_ms

    def record_error(
        self,
        error_type: str,
        error_message: str,
        tool_name: Optional[str] = None,
        stack_trace: Optional[str] = None,
        context: Optional[str] = None,
        severity: str = "error"
    ):
        """
        에러 기록 (즉시 전송)

        Args:
            error_type: 에러 타입
            error_message: 에러 메시지
            tool_name: 도구 이름
            stack_trace: 스택 트레이스
            context: 컨텍스트 정보
            severity: 심각도 (error, warning, critical)
        """
        if not self.enabled:
            return

        error_data = {
            "error_type": error_type,
            "error_message": error_message,
            "tool_name": tool_name,
            "stack_trace": stack_trace,
            "context": context,
            "severity": severity,
        }

        self._error_queue.put(error_data)

    def record_research_metric(
        self,
        beta_phase: str = "closed_beta",
        context_stability_score: Optional[float] = None,
        recovery_time_ms: Optional[float] = None,
        intervention_precision: Optional[float] = None,
        user_acceptance_count: int = 0,
        user_rejection_count: int = 0,
        session_id: Optional[str] = None,
        # Phase 9 Hallucination Detection 필드
        grounding_score: Optional[float] = None,
        confidence_level: Optional[str] = None,
        total_claims: Optional[int] = None,
        unverified_claims: Optional[int] = None,
        hallucination_detected: Optional[bool] = None,
        hallucination_occurred_at: Optional[str] = None,
        hallucination_detected_at: Optional[str] = None,
        drift_occurred_at: Optional[str] = None,
        drift_detected_at: Optional[str] = None,
        requires_retry: Optional[bool] = None,
        retry_reason: Optional[str] = None,
        claim_types_json: Optional[str] = None,
        context_depth_avg: Optional[float] = None,
    ):
        """
        연구 메트릭 기록

        Args:
            beta_phase: 베타 페이즈
            context_stability_score: 맥락 안정성 점수
            recovery_time_ms: 복구 시간
            intervention_precision: 개입 정밀도
            user_acceptance_count: 사용자 수락 횟수
            user_rejection_count: 사용자 거부 횟수
            session_id: 세션 ID
            grounding_score: Grounding Score (근거 충실도)
            confidence_level: 확신도 레벨 (very_high, high, medium, low, none)
            total_claims: 총 Claim 개수
            unverified_claims: 검증 실패한 Claim 개수
            hallucination_detected: 할루시네이션 감지 여부
            hallucination_occurred_at: 할루시네이션 발생 시각
            hallucination_detected_at: 할루시네이션 감지 시각
            drift_occurred_at: Drift 발생 시각
            drift_detected_at: Drift 감지 시각
            requires_retry: 재수행 필요 여부
            retry_reason: 재수행 사유
            claim_types_json: Claim 유형 분포 (JSON)
            context_depth_avg: 평균 Context 깊이
        """
        if not self.enabled:
            return

        metric_data = {
            "beta_phase": beta_phase,
            "context_stability_score": context_stability_score,
            "recovery_time_ms": recovery_time_ms,
            "intervention_precision": intervention_precision,
            "user_acceptance_count": user_acceptance_count,
            "user_rejection_count": user_rejection_count,
            "session_id": session_id,
            # Phase 9 필드
            "grounding_score": grounding_score,
            "confidence_level": confidence_level,
            "total_claims": total_claims,
            "unverified_claims": unverified_claims,
            "hallucination_detected": hallucination_detected,
            "hallucination_occurred_at": hallucination_occurred_at,
            "hallucination_detected_at": hallucination_detected_at,
            "drift_occurred_at": drift_occurred_at,
            "drift_detected_at": drift_detected_at,
            "requires_retry": requires_retry,
            "retry_reason": retry_reason,
            "claim_types_json": claim_types_json,
            "context_depth_avg": context_depth_avg,
        }

        self._research_queue.put(metric_data)

    def _stats_sender_loop(self):
        """통계 전송 루프 (주기적)"""
        while self._running:
            try:
                # flush_interval 경과 시 전송
                if time.time() - self._last_flush >= self.flush_interval:
                    self._flush_stats()

                time.sleep(5)  # 5초마다 체크
            except Exception:
                pass

    def _flush_stats(self):
        """집계된 통계와 연구 메트릭을 서버로 전송"""
        if not self.license_key:
            return

        # Save current buffer state to file for real-time dashboard display
        try:
            buffer_file = Path.home() / ".cortex" / "telemetry_buffer.json"
            buffer_file.parent.mkdir(parents=True, exist_ok=True)

            with self._stats_lock:
                buffer_snapshot = {
                    "timestamp": datetime.now().isoformat(),
                    "module_stats": {
                        f"{module}|{proj_id}": stats
                        for (module, proj_id), stats in self._module_stats.items()
                    },
                    "error_queue_size": self._error_queue.qsize(),
                    "research_queue_size": self._research_queue.qsize(),
                }

            with open(buffer_file, 'w') as f:
                json.dump(buffer_snapshot, f, indent=2)
        except Exception:
            # Don't fail flush if buffer file write fails
            pass

        # 1. 사용성 지표 전송
        with self._stats_lock:
            if self._module_stats:
                # 현재 통계 복사 후 초기화
                stats_to_send = dict(self._module_stats)
                self._module_stats.clear()

                # 각 (module_name, project_id)별로 개별 전송
                # v2: 키가 (module_name, project_id) 튜플로 변경됨
                for stats_key, stats in stats_to_send.items():
                    try:
                        module_name, project_id = stats_key

                        payload = {
                            "license_key": self.license_key,
                            "module_name": module_name,
                            "total_calls": stats["total_calls"],
                            "success_count": stats["success_count"],
                            "error_count": stats["error_count"],
                            "total_latency_ms": stats["total_latency_ms"],
                        }

                        # v2: project_id가 있으면 payload에 추가
                        if project_id:
                            payload["project_id"] = project_id

                        self._send_request(f"{self.server_url}/api/telemetry", payload)
                    except Exception:
                        # 전송 실패해도 계속 진행
                        pass

        # 2. 연구 메트릭 즉시 전송
        while not self._research_queue.empty():
            try:
                metric_data = self._research_queue.get_nowait()
                self._send_research_metric(metric_data)
            except Exception:
                pass

        self._last_flush = time.time()

    def _error_sender_loop(self):
        """에러 전송 루프 (즉시)"""
        while self._running:
            try:
                # 큐에서 에러 가져오기
                if not self._error_queue.empty():
                    error_data = self._error_queue.get(timeout=1)
                    self._send_error(error_data)
                else:
                    time.sleep(0.5)
            except Exception:
                pass

    def _send_error(self, error_data: Dict):
        """에러를 서버로 전송"""
        if not self.license_key:
            return

        try:
            payload = {
                "license_key": self.license_key,
                **error_data
            }

            self._send_request(f"{self.server_url}/api/errors", payload)
        except Exception:
            pass

    def _research_sender_loop(self):
        """연구 메트릭 전송 루프"""
        while self._running:
            try:
                # 큐에서 메트릭 가져오기
                if not self._research_queue.empty():
                    metric_data = self._research_queue.get(timeout=1)
                    self._send_research_metric(metric_data)
                else:
                    time.sleep(1)
            except Exception:
                pass

    def _send_research_metric(self, metric_data: Dict):
        """연구 메트릭을 서버로 전송"""
        if not self.license_key:
            logger.debug("No license_key, skipping research metric send")
            return

        try:
            payload = {
                "license_key": self.license_key,
                **metric_data
            }

            logger.debug(f"Sending research metric to {self.server_url}/api/research/metrics")
            result = self._send_request(f"{self.server_url}/api/research/metrics", payload)
            logger.debug(f"Send result: {result}")
        except Exception as e:
            logger.debug(f"Send error: {type(e).__name__}: {e}")
            pass

    def _send_request(self, url: str, payload: Dict) -> bool:
        """HTTP POST 요청 전송"""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Cortex-MCP/2.1"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                status_ok = response.status == 200
                print(f"[TELEMETRY_DEBUG] HTTP Response: status={response.status}, ok={status_ok}", file=sys.stderr)
                return status_ok
        except Exception as e:
            print(f"[TELEMETRY_DEBUG] HTTP Request failed: {type(e).__name__}: {e}", file=sys.stderr)
            return False


# 싱글톤 인스턴스
_telemetry_client: Optional[TelemetryClient] = None


def get_telemetry_client() -> TelemetryClient:
    """TelemetryClient 싱글톤 인스턴스 반환"""
    global _telemetry_client
    if _telemetry_client is None:
        _telemetry_client = TelemetryClient()
    return _telemetry_client


def enable_telemetry(license_key: str, server_url: Optional[str] = None):
    """텔레메트리 활성화"""
    client = get_telemetry_client()
    client.enable(license_key, server_url)


def disable_telemetry():
    """텔레메트리 비활성화"""
    client = get_telemetry_client()
    client.disable()


def record_call(
    module_name: str,
    success: bool = True,
    latency_ms: float = 0.0,
    project_id: Optional[str] = None  # v2: 프로젝트 ID
):
    """모듈 호출 기록 (v2: project_id 추가)"""
    client = get_telemetry_client()
    client.record_call(module_name, success, latency_ms, project_id)


def record_error(
    error_type: str,
    error_message: str,
    tool_name: Optional[str] = None,
    stack_trace: Optional[str] = None,
    context: Optional[str] = None,
    severity: str = "error"
):
    """에러 기록"""
    client = get_telemetry_client()
    client.record_error(error_type, error_message, tool_name, stack_trace, context, severity)


def record_research_metric(
    beta_phase: str = "closed_beta",
    context_stability_score: Optional[float] = None,
    recovery_time_ms: Optional[float] = None,
    intervention_precision: Optional[float] = None,
    user_acceptance_count: int = 0,
    user_rejection_count: int = 0,
    session_id: Optional[str] = None
):
    """연구 메트릭 기록"""
    client = get_telemetry_client()
    client.record_research_metric(
        beta_phase,
        context_stability_score,
        recovery_time_ms,
        intervention_precision,
        user_acceptance_count,
        user_rejection_count,
        session_id
    )
