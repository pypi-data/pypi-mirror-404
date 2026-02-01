"""
Cortex 텔레메트리 시스템 - 기반 인프라

Zero-Trust 원칙을 준수하는 로컬 기반 텔레메트리 시스템
모든 데이터는 로컬에만 저장하며, 중앙 서버 전송은 opt-in
"""

import asyncio
import hashlib
import json
import queue
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TelemetryEvent:
    """
    텔레메트리 이벤트 데이터 클래스

    additional_job.md 기반 표준 스키마 적용
    """

    # 표준화된 이벤트 이름 (17개 핵심 이벤트)
    event_name: str = ""  # CortexEventName enum 값 사용 권장 (하위 호환성을 위해 기본값 제공)

    # 사용자 정보
    user_id_hash: str = ""  # SHA256 hash of user ID (하위 호환성을 위해 기본값 제공)
    user_tier: str = "free"  # 'free', 'paid', 'enterprise'
    is_paid_user: bool = False  # Paid 여부 (간편 필터링용)

    # 세션/채널 정보
    session_id: str = ""
    channel: str = "server"  # 'extension', 'server', 'web' (기존 service → channel)

    # 프로젝트/컨텍스트 정보
    project_id: Optional[str] = None
    branch_id: Optional[str] = None
    context_id: Optional[str] = None

    # 이벤트 결과
    result: str = "success"  # 'success', 'error', 'timeout'
    duration_ms: Optional[int] = None

    # 메타데이터 (자유 형식)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 타임스탬프
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 하위 호환성 (deprecated, 제거 예정)
    service: Optional[str] = None  # 기존 코드 호환용 (channel과 동일)
    event_type: Optional[str] = None  # 기존 코드 호환용 (event_name과 동일)
    tool_name: Optional[str] = None  # metadata로 이동 권장
    event_data: Dict[str, Any] = field(default_factory=dict)  # metadata로 이동 권장
    error_message: Optional[str] = None  # TelemetryError로 분리 권장

    def __post_init__(self):
        """하위 호환성 유지"""
        # service → channel 자동 변환
        if self.service and self.channel == "server":
            self.channel = self.service

        # event_type → event_name 자동 변환
        if self.event_type and not self.event_name:
            self.event_name = self.event_type

        # user_tier → is_paid_user 자동 설정
        if self.user_tier in ["paid", "enterprise"]:
            self.is_paid_user = True

        # event_data → metadata 병합
        if self.event_data:
            self.metadata.update(self.event_data)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class TelemetryError:
    """
    에러 전용 텔레메트리 (additional_job.md 3-pipeline 구조)

    Event/Error/Trace 분리 원칙
    """

    # 기본 정보
    error_type: str  # ValueError, KeyError, etc.
    error_message: str
    stack_trace: Optional[str] = None
    stack_hash: Optional[str] = None  # 에러 그룹핑용

    # 심각도
    severity: str = "error"  # 'info', 'warning', 'error', 'critical'

    # 사용자 정보
    user_id_hash: str = ""
    user_tier: str = "free"
    is_paid_user: bool = False

    # 컨텍스트 정보
    session_id: str = ""
    channel: str = "server"
    project_id: Optional[str] = None
    branch_id: Optional[str] = None
    context_id: Optional[str] = None

    # 관련 이벤트 (에러 발생 시점의 이벤트)
    related_event_name: Optional[str] = None

    # 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 타임스탬프
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        """스택 해시 자동 생성"""
        if self.stack_trace and not self.stack_hash:
            import hashlib

            self.stack_hash = hashlib.sha256(self.stack_trace.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class TelemetryTrace:
    """
    성능 추적 전용 텔레메트리 (additional_job.md 3-pipeline 구조)

    Event/Error/Trace 분리 원칙
    """

    # 추적 정보
    operation_name: str  # "rag_search", "context_load", etc.
    duration_ms: int

    # 사용자 정보
    user_id_hash: str = ""
    user_tier: str = "free"
    is_paid_user: bool = False

    # 컨텍스트 정보
    session_id: str = ""
    channel: str = "server"
    project_id: Optional[str] = None
    branch_id: Optional[str] = None
    context_id: Optional[str] = None

    # 성능 메트릭
    success: bool = True
    result_count: Optional[int] = None  # 반환된 결과 수

    # 메타데이터 (쿼리 길이, 파라미터 등)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 타임스탬프
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


class TelemetryClient:
    """텔레메트리 클라이언트 베이스 클래스"""

    def __init__(self, service: str):
        """
        Args:
            service: 서비스 이름 ('mcp', 'extension', 'web')
        """
        self.service = service
        self.session_id = self._generate_session_id()
        self.event_queue: queue.Queue = queue.Queue(maxsize=10000)
        self.is_running = True

        # 백그라운드 워커 시작
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _generate_session_id(self) -> str:
        """세션 ID 생성 (SHA256 해시)"""
        session_str = f"{time.time()}_{id(self)}_{self.service}"
        return hashlib.sha256(session_str.encode()).hexdigest()[:16]

    def track_event(self, event: TelemetryEvent):
        """
        이벤트 추적 (비동기 큐에 추가)

        Args:
            event: TelemetryEvent 객체
        """
        try:
            # 세션 ID 자동 설정
            if not event.session_id:
                event.session_id = self.session_id

            # 큐에 추가 (Fail-Safe: 큐가 가득 차면 무시)
            self.event_queue.put_nowait(event)

        except queue.Full:
            # 큐가 가득 차면 무시 (텔레메트리 실패는 핵심 기능에 영향 없음)
            pass

        except Exception:
            # 모든 예외 무시 (Fail-Safe)
            pass

    def _worker(self):
        """백그라운드 워커 (큐에서 이벤트를 꺼내 저장)"""
        from core.telemetry_storage import TelemetryStorage

        storage = TelemetryStorage()

        while self.is_running:
            try:
                # 큐에서 이벤트 가져오기 (타임아웃 1초)
                item = self.event_queue.get(timeout=1.0)

                # 타입에 따라 적절한 저장 메서드 호출
                if isinstance(item, TelemetryError):
                    storage.save_error(item)
                elif isinstance(item, TelemetryTrace):
                    storage.save_trace(item)
                else:  # TelemetryEvent
                    storage.save_event(item)

                # 큐 작업 완료 표시
                self.event_queue.task_done()

            except queue.Empty:
                # 큐가 비어있으면 계속 대기
                continue

            except Exception as e:
                # 저장 실패 시 로그 (무시)
                print(f"[WARNING] Telemetry storage failed: {e}")
                continue

    def shutdown(self):
        """텔레메트리 클라이언트 종료"""
        self.is_running = False
        self.worker_thread.join(timeout=5.0)

    def emit_event(self, event_name: str, properties: Dict[str, Any] = None, channel: Optional[str] = None, **kwargs):
        """
        이벤트 발생 기록 (간편 메서드)

        Args:
            event_name: 이벤트 이름
            properties: 이벤트 속성 (메타데이터)
            channel: 채널 타입 (선택적, 기본값: self.service)
            **kwargs: 추가 파라미터 (하위 호환성을 위해 무시됨)
        """
        try:
            # metadata 파라미터 처리 (properties와 metadata 둘 다 지원)
            metadata = properties or kwargs.get('metadata', {})

            # TelemetryEvent 객체 생성
            event = TelemetryEvent(
                event_name=event_name,
                user_id_hash=get_user_id_hash(),
                user_tier=get_user_tier(),
                channel=channel or self.service,
                metadata=metadata,
            )

            # track_event로 위임
            self.track_event(event)

        except Exception:
            # Fail-Safe: 모든 예외 무시
            pass

    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """
        에러 추적 기록 (간편 메서드)

        Args:
            error: 발생한 예외
            context: 에러 발생 컨텍스트 정보
        """
        try:
            import traceback

            # TelemetryError 객체 생성
            error_data = TelemetryError(
                error_type=type(error).__name__,
                error_message=str(error),
                stack_trace=traceback.format_exc(),
                user_id_hash=get_user_id_hash(),
                user_tier=get_user_tier(),
                channel=self.service,
                metadata=context or {},
            )

            # 에러를 이벤트 큐에 추가 (통합 저장)
            # Note: TelemetryStorage가 Error 타입도 처리할 수 있어야 함
            self.event_queue.put_nowait(error_data)

        except Exception:
            # Fail-Safe: 모든 예외 무시
            pass


def get_user_id_hash() -> str:
    """
    사용자 ID 해시 반환 (익명화)

    Zero-Trust 원칙: 실제 User ID는 절대 저장하지 않음
    SHA256 해시만 저장
    """
    from core.license_manager import get_license_manager

    try:
        license_mgr = get_license_manager()
        license_info = license_mgr.get_license_info()

        # 라이센스키를 User ID로 사용
        license_key = license_info.get("license_key", "anonymous")
        user_id_hash = hashlib.sha256(license_key.encode()).hexdigest()

        return user_id_hash

    except Exception:
        # 실패 시 익명 사용자
        return hashlib.sha256(b"anonymous").hexdigest()


def get_user_tier() -> str:
    """
    사용자 티어 반환 ('free', 'paid', 'enterprise')
    """
    from core.license_manager import get_license_manager

    try:
        license_mgr = get_license_manager()
        license_info = license_mgr.get_license_info()

        if license_info.get("is_valid"):
            tier = license_info.get("tier", 1)

            if tier == 1:
                return "free"
            elif tier == 2:
                return "paid"
            elif tier == 3:
                return "enterprise"

        return "free"  # 기본값

    except Exception:
        # 실패 시 무료 사용자로 간주
        return "free"


# 전역 텔레메트리 설정
TELEMETRY_ENABLED = True  # config.py에서 설정 가능


def is_telemetry_enabled() -> bool:
    """텔레메트리 활성화 여부 확인"""
    try:
        from config import TELEMETRY_ENABLED as enabled

        return enabled
    except ImportError:
        return TELEMETRY_ENABLED
