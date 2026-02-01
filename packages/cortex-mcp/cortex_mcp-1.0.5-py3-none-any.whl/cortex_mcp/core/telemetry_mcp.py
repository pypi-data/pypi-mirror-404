"""
Cortex MCP - MCP Service Telemetry (v2.0)
MCP 서비스 전용 텔레메트리 수집 및 추적

v2.0 변경 사항:
- telemetry_integration.py를 통해 v2.0 스키마 자동 적용
- 17개 핵심 이벤트 매핑 지원
- Event/Error/Trace 3-pipeline 자동 분류
"""

import logging
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Optional

from core.telemetry_base import TelemetryEvent
from core.telemetry_integration import get_telemetry

logger = logging.getLogger(__name__)


class MCPTelemetry:
    """
    MCP 서비스 전용 텔레메트리

    모든 MCP 도구 호출을 자동으로 추적하고 성능/에러를 기록합니다.
    """

    def __init__(self):
        """텔레메트리 초기화"""
        self.telemetry = get_telemetry()

    def track_tool_execution(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        duration_ms: float,
        success: bool,
        error: Optional[Exception] = None,
    ):
        """
        MCP 도구 실행 추적

        v2.0: telemetry_integration.track_tool_call()을 통해
        자동으로 v2.0 스키마(channel, event_name, metadata) 적용

        Args:
            tool_name: 도구 이름
            args: 도구 인자
            result: 실행 결과
            duration_ms: 실행 시간 (밀리초)
            success: 성공 여부
            error: 에러 (실패 시)
        """
        # 결과 카운트 계산
        result_count = 0
        if success and result:
            if isinstance(result, list):
                result_count = len(result)
            elif isinstance(result, dict):
                result_count = len(result)
            else:
                result_count = 1

        # 기본 도구 호출 추적
        self.telemetry.track_tool_call(
            tool_name=tool_name, duration_ms=duration_ms, success=success, result_count=result_count
        )

        # 에러가 있으면 별도 추적
        if error:
            self.telemetry.track_error(
                error_type=type(error).__name__,
                error_message=str(error),
                context={"tool_name": tool_name, "args": self._sanitize_args(args)},
            )

    def track_rag_search(
        self, query: str, top_k: int, results_count: int, duration_ms: float, success: bool
    ):
        """
        RAG 검색 추적

        v2.0: telemetry_integration.track_performance()를 통해
        자동으로 v2.0 스키마 적용 (TelemetryTrace 파이프라인)

        Args:
            query: 검색 쿼리
            top_k: 요청한 결과 수
            results_count: 실제 반환된 결과 수
            duration_ms: 검색 시간
            success: 성공 여부
        """
        self.telemetry.track_performance(
            operation="rag_search",
            duration_ms=duration_ms,
            metadata={
                "query_length": len(query),
                "top_k": top_k,
                "results_count": results_count,
                "success": success,
            },
        )

    def track_context_operation(
        self,
        operation: str,
        project_id: str,
        branch_id: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        컨텍스트 작업 추적 (생성, 로드, 압축 등)

        Args:
            operation: 작업 유형 (create, load, compress, etc.)
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            metadata: 추가 메타데이터
        """
        self.telemetry.track_feature_usage(
            feature_name="context_management",
            action=operation,
            properties={"project_id": project_id, "branch_id": branch_id, **(metadata or {})},
        )

    def track_reference_history(
        self,
        operation: str,
        accuracy: Optional[float] = None,
        suggestion_count: Optional[int] = None,
    ):
        """
        Reference History 작업 추적

        Args:
            operation: 작업 유형 (suggest, record, feedback)
            accuracy: 추천 정확도 (suggest 시)
            suggestion_count: 추천 개수 (suggest 시)
        """
        self.telemetry.track_feature_usage(
            feature_name="reference_history",
            action=operation,
            properties={"accuracy": accuracy, "suggestion_count": suggestion_count},
        )

    def track_smart_context(
        self,
        operation: str,
        contexts_loaded: Optional[int] = None,
        contexts_compressed: Optional[int] = None,
    ):
        """
        Smart Context 작업 추적

        Args:
            operation: 작업 유형 (load, compress, suggest)
            contexts_loaded: 로드된 컨텍스트 수
            contexts_compressed: 압축된 컨텍스트 수
        """
        self.telemetry.track_feature_usage(
            feature_name="smart_context",
            action=operation,
            properties={
                "contexts_loaded": contexts_loaded,
                "contexts_compressed": contexts_compressed,
            },
        )

    def track_git_sync(
        self, operation: str, branch_name: Optional[str] = None, auto_created: bool = False
    ):
        """
        Git 동기화 작업 추적

        Args:
            operation: 작업 유형 (link, unlink, check)
            branch_name: Git 브랜치 이름
            auto_created: 자동 생성 여부
        """
        self.telemetry.track_feature_usage(
            feature_name="git_sync",
            action=operation,
            properties={"branch_name": branch_name, "auto_created": auto_created},
        )

    def track_cloud_sync(
        self,
        operation: str,
        size_bytes: Optional[int] = None,
        duration_ms: Optional[float] = None,
        success: bool = True,
    ):
        """
        클라우드 동기화 작업 추적

        Args:
            operation: 작업 유형 (upload, download)
            size_bytes: 전송 크기 (바이트)
            duration_ms: 전송 시간
            success: 성공 여부
        """
        if duration_ms:
            self.telemetry.track_performance(
                operation=f"cloud_sync_{operation}",
                duration_ms=duration_ms,
                metadata={"size_bytes": size_bytes, "success": success},
            )
        else:
            self.telemetry.track_feature_usage(
                feature_name="cloud_sync",
                action=operation,
                properties={"size_bytes": size_bytes, "success": success},
            )

    def track_automation(
        self, action_type: str, feedback: Optional[str] = None, plan_mode: Optional[str] = None
    ):
        """
        자동화 작업 추적 (Plan A/B)

        Args:
            action_type: 작업 유형
            feedback: 사용자 피드백 (accepted, rejected, modified)
            plan_mode: 현재 플랜 모드 (auto, semi_auto)
        """
        self.telemetry.track_feature_usage(
            feature_name="automation",
            action=action_type,
            properties={"feedback": feedback, "plan_mode": plan_mode},
        )

    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        텔레메트리용 인자 정제 (민감한 정보 제거)

        Args:
            args: 원본 인자

        Returns:
            정제된 인자
        """
        sanitized = {}
        for key, value in args.items():
            # 민감한 키 필터링
            if any(
                sensitive in key.lower() for sensitive in ["password", "key", "secret", "token"]
            ):
                sanitized[key] = "[REDACTED]"
            # 긴 문자열 요약
            elif isinstance(value, str) and len(value) > 100:
                sanitized[key] = f"{value[:100]}... ({len(value)} chars)"
            # 리스트/딕셔너리 크기만 기록
            elif isinstance(value, (list, dict)):
                sanitized[key] = f"<{type(value).__name__}: {len(value)} items>"
            else:
                sanitized[key] = value

        return sanitized


# 전역 MCP 텔레메트리 인스턴스
_mcp_telemetry_instance: Optional[MCPTelemetry] = None


def get_mcp_telemetry() -> MCPTelemetry:
    """MCP 텔레메트리 싱글톤 반환"""
    global _mcp_telemetry_instance
    if _mcp_telemetry_instance is None:
        _mcp_telemetry_instance = MCPTelemetry()
    return _mcp_telemetry_instance


# 데코레이터: MCP 도구 자동 추적
def track_mcp_tool(tool_name: str):
    """
    MCP 도구 자동 텔레메트리 데코레이터

    사용법:
        @track_mcp_tool("initialize_context")
        def initialize_context(args):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            result = None
            success = False

            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = e
                success = False
                raise
            finally:
                # 실행 시간 계산
                duration_ms = (time.time() - start_time) * 1000

                # 텔레메트리 추적
                telemetry = get_mcp_telemetry()
                telemetry.track_tool_execution(
                    tool_name=tool_name,
                    args=kwargs,
                    result=result,
                    duration_ms=duration_ms,
                    success=success,
                    error=error,
                )

        return wrapper

    return decorator
