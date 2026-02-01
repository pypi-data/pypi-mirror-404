"""
Cortex MCP - Telemetry Integration Layer
기존 core/telemetry.py와 새로운 telemetry_base.py + telemetry_storage.py 통합
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from config import config
from core.telemetry_base import TelemetryClient, TelemetryEvent, get_user_id_hash, get_user_tier
from core.telemetry_storage import get_telemetry_storage

logger = logging.getLogger(__name__)


class CortexTelemetry:
    """
    통합 텔레메트리 시스템

    기존 core/telemetry.py의 API를 유지하면서 새로운 SQLite 저장소 사용
    """

    def __init__(self):
        """텔레메트리 초기화"""
        # 설정 파일 경로
        self.config_file = config.cortex_home / "telemetry_config.json"

        # 새로운 텔레메트리 클라이언트 (SQLite 저장소 사용)
        # v2.0: TelemetryClient는 service 파라미터를 받지만 자동으로 channel로 변환됨
        self.client = TelemetryClient(service="server")  # v2.0: "server" channel

        # 설정 로드
        self._config = self._load_config()

        # 사용자 정보 (익명화)
        self.user_id_hash = get_user_id_hash()
        self.user_tier = get_user_tier()

    def _load_config(self) -> Dict[str, Any]:
        """텔레메트리 설정 로드"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load telemetry config: {e}")

        # 기본 설정
        default_config = {
            "enabled": True,
            "opt_in": False,  # 기본값: Opt-out (로컬 저장만)
            "server_sync_enabled": False,  # 중앙 서버 전송 비활성화
        }

        # 설정 파일 생성
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save telemetry config: {e}")

        return default_config

    def is_enabled(self) -> bool:
        """텔레메트리 활성화 여부"""
        return self._config.get("enabled", True)

    def set_enabled(self, enabled: bool):
        """텔레메트리 활성화/비활성화"""
        self._config["enabled"] = enabled
        try:
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save telemetry config: {e}")

    def track_tool_call(
        self, tool_name: str, duration_ms: float, success: bool, result_count: int = 0
    ):
        """
        MCP 도구 호출 추적 (기존 API 호환)

        Args:
            tool_name: 도구 이름
            duration_ms: 실행 시간 (밀리초)
            success: 성공 여부
            result_count: 결과 개수
        """
        if not self.is_enabled():
            return

        # v2.0: service, event_type, event_data는 deprecated
        # channel, event_name, metadata를 사용하되 하위 호환성 유지
        event = TelemetryEvent(
            service="server",  # deprecated, channel로 자동 변환
            event_type="tool_call",  # deprecated, event_name으로 자동 변환
            user_tier=self.user_tier,
            user_id_hash=self.user_id_hash,
            session_id=self.client.session_id,
            tool_name=tool_name,  # deprecated, metadata로 이동 권장
            result="success" if success else "error",
            duration_ms=int(duration_ms),
            event_data={  # deprecated, metadata로 자동 병합
                "result_count": result_count,
                "tool_name": tool_name,  # v2.0: metadata에 명시적 저장
            },
        )

        self.client.track_event(event)

    def track_error(
        self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None
    ):
        """
        에러 추적 (기존 API 호환)

        Args:
            error_type: 에러 유형
            error_message: 에러 메시지
            context: 추가 컨텍스트
        """
        if not self.is_enabled():
            return

        # v2.0: Error 이벤트도 동일하게 deprecated 필드 사용
        event = TelemetryEvent(
            service="server",  # deprecated, channel로 자동 변환
            event_type="error",  # deprecated, event_name으로 자동 변환
            user_tier=self.user_tier,
            user_id_hash=self.user_id_hash,
            session_id=self.client.session_id,
            result="error",
            error_message=error_message,  # deprecated, TelemetryError 사용 권장
            event_data={  # deprecated, metadata로 자동 병합
                "error_type": error_type,
                "context": context or {},
            },
        )

        self.client.track_event(event)

    def track_performance(
        self, operation: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None
    ):
        """
        성능 메트릭 추적 (기존 API 호환)

        Args:
            operation: 작업 이름
            duration_ms: 실행 시간 (밀리초)
            metadata: 추가 메타데이터
        """
        if not self.is_enabled():
            return

        # v2.0: Performance 이벤트도 deprecated 필드 사용
        event = TelemetryEvent(
            service="server",  # deprecated, channel로 자동 변환
            event_type="performance",  # deprecated, event_name으로 자동 변환
            user_tier=self.user_tier,
            user_id_hash=self.user_id_hash,
            session_id=self.client.session_id,
            result="success",
            duration_ms=int(duration_ms),
            event_data={  # deprecated, metadata로 자동 병합
                "operation": operation,
                "metadata": metadata or {},
            },
        )

        self.client.track_event(event)

    def track_feature_usage(
        self, feature_name: str, action: str, properties: Optional[Dict[str, Any]] = None
    ):
        """
        기능 사용 추적 (기존 API 호환)

        Args:
            feature_name: 기능 이름
            action: 수행한 액션
            properties: 추가 속성
        """
        if not self.is_enabled():
            return

        # v2.0: Feature usage 이벤트도 deprecated 필드 사용
        event = TelemetryEvent(
            service="server",  # deprecated, channel로 자동 변환
            event_type="feature_usage",  # deprecated, event_name으로 자동 변환
            user_tier=self.user_tier,
            user_id_hash=self.user_id_hash,
            session_id=self.client.session_id,
            result="success",
            event_data={  # deprecated, metadata로 자동 병합
                "feature_name": feature_name,
                "action": action,
                "properties": properties or {},
            },
        )

        self.client.track_event(event)

    def shutdown(self):
        """텔레메트리 종료"""
        self.client.shutdown()


# 전역 텔레메트리 인스턴스
_telemetry_instance: Optional[CortexTelemetry] = None


def get_telemetry() -> CortexTelemetry:
    """텔레메트리 싱글톤 반환"""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = CortexTelemetry()
    return _telemetry_instance


# 하위 호환성을 위한 별칭
Telemetry = CortexTelemetry
