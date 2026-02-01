"""
Cortex MCP - Telemetry System
익명화된 사용 통계 수집 (옵트인)

수집하는 데이터:
- 도구 호출 빈도 및 응답 시간
- 에러 발생 패턴 (스택트레이스 없음)
- 기능 사용 통계
- 성능 메트릭

수집하지 않는 데이터:
- 맥락 내용, 파일 내용
- 개인 식별 정보 (PII)
- 라이센스 키, 이메일
- IP 주소
"""

import hashlib
import json
import logging
import os
import platform
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 텔레메트리 서버 (향후 구현)
TELEMETRY_ENDPOINT = os.environ.get(
    "CORTEX_TELEMETRY_URL", "https://telemetry.cortex-mcp.com/v1/events"
)


class TelemetryEvent:
    """텔레메트리 이벤트"""

    def __init__(self, event_type: str, event_name: str, properties: Dict[str, Any] = None):
        self.event_type = event_type
        self.event_name = event_name
        self.properties = properties or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()


class Telemetry:
    """텔레메트리 관리자"""

    def __init__(self):
        from config import config

        self.config_file = config.cortex_home / "telemetry_config.json"
        self.data_file = config.cortex_home / "telemetry_data.json"

        # 세션 ID (익명, 재시작 시 변경)
        self.session_id = hashlib.sha256(f"{time.time()}_{id(self)}".encode()).hexdigest()[:16]

        # 설치 ID (익명, 영구)
        self.install_id = self._get_or_create_install_id()

        # 메트릭 버퍼
        self._events: List[Dict] = []
        self._metrics: Dict[str, Any] = defaultdict(int)
        self._lock = threading.Lock()

        # 설정 로드
        self._config = self._load_config()

        # 백그라운드 전송 스레드
        self._sender_thread = None
        self._stop_sender = threading.Event()

    def _get_or_create_install_id(self) -> str:
        """익명 설치 ID 생성 또는 로드"""
        install_id_file = self.config_file.parent / ".install_id"

        if install_id_file.exists():
            try:
                return install_id_file.read_text().strip()
            except:
                pass

        # 새 ID 생성 (완전 익명)
        import secrets

        install_id = secrets.token_hex(16)

        try:
            install_id_file.parent.mkdir(parents=True, exist_ok=True)
            install_id_file.write_text(install_id)
        except:
            pass

        return install_id

    def _load_config(self) -> Dict:
        """설정 로드"""
        default_config = {
            "enabled": True,  # 기본 활성화 (옵트아웃 가능)
            "send_errors": True,
            "send_performance": True,
            "send_usage": True,
            "batch_size": 50,
            "send_interval_seconds": 3600,  # 1시간
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except:
                pass

        return default_config

    def _save_config(self):
        """설정 저장"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save telemetry config: {e}")

    def is_enabled(self) -> bool:
        """텔레메트리 활성화 여부"""
        return self._config.get("enabled", False)

    def enable(self):
        """텔레메트리 활성화"""
        self._config["enabled"] = True
        self._save_config()
        logger.info("Telemetry enabled")

    def disable(self):
        """텔레메트리 비활성화"""
        self._config["enabled"] = False
        self._save_config()
        self._clear_data()
        logger.info("Telemetry disabled")

    def _clear_data(self):
        """저장된 텔레메트리 데이터 삭제"""
        try:
            if self.data_file.exists():
                self.data_file.unlink()
        except:
            pass

        with self._lock:
            self._events.clear()
            self._metrics.clear()

    def track_event(self, event_type: str, event_name: str, properties: Dict[str, Any] = None):
        """
        이벤트 추적

        Args:
            event_type: 이벤트 유형 (tool_call, error, performance, etc.)
            event_name: 이벤트 이름
            properties: 추가 속성 (민감 정보 제외)
        """
        if not self.is_enabled():
            return

        # 민감 정보 필터링
        safe_properties = self._sanitize_properties(properties or {})

        event = {
            "type": event_type,
            "name": event_name,
            "properties": safe_properties,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
        }

        with self._lock:
            self._events.append(event)

            # 배치 크기 초과 시 저장
            if len(self._events) >= self._config.get("batch_size", 50):
                self._persist_events()

    def track_tool_call(
        self, tool_name: str, duration_ms: float, success: bool, result_count: int = 0
    ):
        """도구 호출 추적"""
        if not self._config.get("send_usage", True):
            return

        self.track_event(
            "tool_call",
            tool_name,
            {
                "duration_ms": round(duration_ms, 2),
                "success": success,
                "result_count": result_count,
            },
        )

        # 집계 메트릭 업데이트
        with self._lock:
            self._metrics[f"tool_{tool_name}_count"] += 1
            self._metrics[f"tool_{tool_name}_total_ms"] += duration_ms
            if not success:
                self._metrics[f"tool_{tool_name}_errors"] += 1

    def track_error(self, error_type: str, error_message: str, context: str = None):
        """에러 추적 (스택트레이스 없음)"""
        if not self._config.get("send_errors", True):
            return

        # 에러 메시지에서 민감 정보 제거
        safe_message = self._sanitize_error_message(error_message)

        self.track_event(
            "error",
            error_type,
            {
                "message": safe_message[:200],  # 최대 200자
                "context": context,
            },
        )

    def track_performance(self, metric_name: str, value: float, unit: str = "ms"):
        """성능 메트릭 추적"""
        if not self._config.get("send_performance", True):
            return

        self.track_event(
            "performance",
            metric_name,
            {
                "value": round(value, 2),
                "unit": unit,
            },
        )

    def track_feature_usage(self, feature_name: str):
        """기능 사용 추적"""
        if not self._config.get("send_usage", True):
            return

        self.track_event("feature", feature_name, {})

        with self._lock:
            self._metrics[f"feature_{feature_name}"] += 1

    def _sanitize_properties(self, properties: Dict) -> Dict:
        """민감 정보 제거"""
        safe = {}
        sensitive_keys = {
            "license_key",
            "email",
            "password",
            "token",
            "secret",
            "api_key",
            "content",
            "text",
            "file_path",
            "path",
        }

        for key, value in properties.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_keys):
                continue
            if isinstance(value, str) and len(value) > 100:
                continue
            safe[key] = value

        return safe

    def _sanitize_error_message(self, message: str) -> str:
        """
        에러 메시지에서 민감 정보 제거 (강화)

        Args:
            message: 원본 에러 메시지

        Returns:
            익명화된 에러 메시지
        """
        import re

        # 모든 형태의 라이센스 키 패턴 매칭 (형식 변경에 대비)
        message = re.sub(r"(?i)(cortex|license)[-_]?[a-z0-9-]+", "[LICENSE]", message, flags=re.IGNORECASE)

        # 파일 경로에서 사용자 이름 제거
        message = re.sub(r"/Users/[^/]+/", "/Users/[USER]/", message)
        message = re.sub(r"C:\\Users\\[^\\]+\\", "C:\\Users\\[USER]\\", message)
        message = re.sub(r"/home/[^/]+/", "/home/[USER]/", message)

        # 이메일 주소 마스킹
        message = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]", message)

        # 파일 경로 제거 (남은 경로들)
        message = re.sub(r"/[^\s]+", "[PATH]", message)
        message = re.sub(r"\\[^\s]+", "[PATH]", message)

        # IP 주소 마스킹
        message = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[IP]", message)

        # API 키 패턴 (일반적인 형태)
        message = re.sub(r"(?i)(api[_-]?key|token|secret)[:=]\s*['\"]?[a-z0-9-]+['\"]?", "[API_KEY]", message, flags=re.IGNORECASE)

        return message

    def _persist_events(self):
        """이벤트를 파일에 저장"""
        if not self._events:
            return

        try:
            existing_data = []
            if self.data_file.exists():
                try:
                    with open(self.data_file, "r") as f:
                        existing_data = json.load(f)
                except:
                    pass

            existing_data.extend(self._events)

            # 최대 1000개 이벤트 유지
            if len(existing_data) > 1000:
                existing_data = existing_data[-1000:]

            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump(existing_data, f)

            self._events.clear()

        except Exception as e:
            logger.debug(f"Failed to persist telemetry events: {e}")

    def get_local_stats(self) -> Dict[str, Any]:
        """
        로컬 통계 반환 (분석용)

        Returns:
            수집된 통계 요약
        """
        with self._lock:
            metrics_copy = dict(self._metrics)

        stats = {
            "install_id": self.install_id[:8] + "...",  # 일부만 표시
            "session_id": self.session_id,
            "telemetry_enabled": self.is_enabled(),
            "events_pending": len(self._events),
            "metrics": metrics_copy,
            "system": {
                "os": platform.system(),
                "python": platform.python_version(),
            },
        }

        return stats

    def send_to_server(self, max_retries: int = 5) -> bool:
        """
        텔레메트리 데이터를 서버로 전송 (Exponential Backoff 포함)

        최대 5회 재시도, exponential backoff (1s, 2s, 4s, 8s, 16s)

        Args:
            max_retries: 최대 재시도 횟수 (기본 5회)

        Returns:
            전송 성공 여부
        """
        if not self.is_enabled():
            return False

        # 파일에 저장된 이벤트 로드
        events_to_send = []
        if self.data_file.exists():
            try:
                with open(self.data_file, "r") as f:
                    events_to_send = json.load(f)
            except:
                pass

        if not events_to_send:
            return True

        # 페이로드 구성
        payload = {
            "install_id": self.install_id,
            "events": events_to_send,
            "metrics": dict(self._metrics),
            "system": {
                "os": platform.system(),
                "os_version": platform.version()[:50],
                "python": platform.python_version(),
                "cortex_version": "1.0.0",
            },
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

        # Exponential Backoff 재시도
        for attempt in range(max_retries):
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    TELEMETRY_ENDPOINT,
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "cortex-mcp/1.0.0",
                    },
                    method="POST",
                )

                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        # 전송 성공 - 로컬 데이터 삭제
                        self._clear_data()
                        logger.debug("Telemetry sent successfully")
                        return True

            except urllib.error.URLError as e:
                # 네트워크 오류 - 재시도
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # exponential backoff
                    logger.debug(f"Telemetry send failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    # 영구 실패 - ErrorReport에 기록 필요
                    logger.error(f"Telemetry send permanently failed after {max_retries} attempts: {e}")
                    self._record_telemetry_failure(str(e))
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.debug(f"Telemetry send error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Telemetry send permanently failed after {max_retries} attempts: {e}")
                    self._record_telemetry_failure(str(e))

        return False

    def _record_telemetry_failure(self, error_message: str):
        """
        텔레메트리 전송 실패를 ErrorReport에 기록

        Args:
            error_message: 오류 메시지
        """
        try:
            # 로컬 파일에 기록 (다음 전송 때 같이 전송)
            failure_log_file = self.config_file.parent / "telemetry_failures.json"

            failure_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_message": error_message,
                "install_id": self.install_id[:8] + "...",  # 일부만 기록
            }

            existing_failures = []
            if failure_log_file.exists():
                try:
                    with open(failure_log_file, "r") as f:
                        existing_failures = json.load(f)
                except:
                    pass

            existing_failures.append(failure_entry)

            # 최대 100개만 유지
            if len(existing_failures) > 100:
                existing_failures = existing_failures[-100:]

            failure_log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(failure_log_file, "w") as f:
                json.dump(existing_failures, f, indent=2)

            logger.info(f"Telemetry failure recorded to {failure_log_file}")

        except Exception as e:
            logger.error(f"Failed to record telemetry failure: {e}")

    def flush(self):
        """버퍼의 모든 이벤트를 저장"""
        with self._lock:
            self._persist_events()


# 전역 인스턴스
_telemetry: Optional[Telemetry] = None


def get_telemetry() -> Telemetry:
    """Telemetry 싱글톤"""
    global _telemetry
    if _telemetry is None:
        _telemetry = Telemetry()
    return _telemetry


# 편의 함수
def track_tool(tool_name: str, duration_ms: float, success: bool, result_count: int = 0):
    """도구 호출 추적 헬퍼"""
    get_telemetry().track_tool_call(tool_name, duration_ms, success, result_count)


def track_error(error_type: str, message: str, context: str = None):
    """에러 추적 헬퍼"""
    get_telemetry().track_error(error_type, message, context)


def track_feature(feature_name: str):
    """기능 사용 추적 헬퍼"""
    get_telemetry().track_feature_usage(feature_name)
