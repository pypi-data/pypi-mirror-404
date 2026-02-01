"""
Cortex MCP - 표준 이벤트 정의
additional_job.md 기반 핵심 이벤트 17개 정의
"""

from enum import Enum


class CortexEventName(str, Enum):
    """
    Cortex 핵심 이벤트 (additional_job.md 기준)

    17개 필수 이벤트로 CDR, Resurrection, DAU/WAU 계산 가능
    """

    # Context Lifecycle (7개)
    CONTEXT_CREATED = "context_created"
    CONTEXT_AUTO_CREATED = "context_auto_created"
    CONTEXT_LOADED = "context_loaded"
    CONTEXT_RESUMED = "context_resumed"
    CONTEXT_MODIFIED = "context_modified"
    CONTEXT_MERGED = "context_merged"
    CONTEXT_DELETED = "context_deleted"

    # Dependency / Protection (3개)
    CONTEXT_PROTECTION_TRIGGERED = "context_protection_triggered"
    CONTEXT_PROTECTION_BLOCKED = "context_protection_blocked"
    CONTEXT_OVERRIDE_MANUAL = "context_override_manual"

    # Session Continuity (3개)
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SESSION_RESUMED_FROM_CONTEXT = "session_resumed_from_context"

    # Channel Usage (3개)
    EXTENSION_ACTIVATED = "extension_activated"
    SERVER_OPERATION_CALLED = "server_operation_called"
    WEB_VIEW_OPENED = "web_view_opened"

    # Monetization (2개)
    PAID_SUBSCRIPTION_STARTED = "paid_subscription_started"
    PAID_SUBSCRIPTION_CANCELED = "paid_subscription_canceled"


class ChannelType(str, Enum):
    """채널 타입"""

    EXTENSION = "extension"
    SERVER = "server"
    WEB = "web"


class EventSeverity(str, Enum):
    """이벤트 심각도"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# 이벤트 → KPI 매핑 (설명용)
EVENT_TO_KPI_MAPPING = {
    "CDR (Context Dependency Rate)": [
        CortexEventName.CONTEXT_LOADED,
        CortexEventName.CONTEXT_RESUMED,
    ],
    "Resurrection": [
        CortexEventName.SESSION_RESUMED_FROM_CONTEXT,
    ],
    "DAU/WAU": [
        CortexEventName.SESSION_STARTED,
        CortexEventName.EXTENSION_ACTIVATED,
        CortexEventName.SERVER_OPERATION_CALLED,
        CortexEventName.WEB_VIEW_OPENED,
    ],
    "Paid Conversion": [
        CortexEventName.PAID_SUBSCRIPTION_STARTED,
        CortexEventName.PAID_SUBSCRIPTION_CANCELED,
    ],
}
