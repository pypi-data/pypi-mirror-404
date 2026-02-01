"""
Cortex 텔레메트리 스토리지 - SQLite 저장소

Zero-Trust 원칙을 준수하는 로컬 데이터베이스 저장
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import CORTEX_HOME
from core.telemetry_base import TelemetryEvent


class TelemetryStorage:
    """텔레메트리 로컬 저장소 (SQLite)"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: SQLite DB 경로 (기본: ~/.cortex/telemetry.db)
        """
        if db_path is None:
            db_path = str(Path(CORTEX_HOME) / "telemetry.db")

        self.db_path = db_path
        self._lock = threading.Lock()

        # DB 디렉토리 생성
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 테이블 초기화
        self._initialize_db()

    @contextmanager
    def _get_connection(self):
        """스레드 안전한 DB 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _initialize_db(self):
        """
        데이터베이스 테이블 초기화

        additional_job.md 3-pipeline 구조:
        - telemetry_events: 핵심 이벤트 (17개)
        - telemetry_errors: 에러 전용
        - telemetry_traces: 성능 추적 전용
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()

            # telemetry_events 테이블 생성 (표준 스키마)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,

                    -- 표준화된 이벤트 이름 (17개 핵심 이벤트)
                    event_name TEXT NOT NULL,

                    -- 사용자 정보
                    user_id_hash TEXT NOT NULL,
                    user_tier TEXT NOT NULL,
                    is_paid_user BOOLEAN NOT NULL DEFAULT 0,

                    -- 세션/채널 정보
                    session_id TEXT NOT NULL,
                    channel TEXT NOT NULL,

                    -- 프로젝트/컨텍스트 정보
                    project_id TEXT,
                    branch_id TEXT,
                    context_id TEXT,

                    -- 이벤트 결과
                    result TEXT NOT NULL,
                    duration_ms INTEGER,

                    -- 메타데이터 (JSON)
                    metadata TEXT NOT NULL DEFAULT '{}',

                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # telemetry_errors 테이블 생성 (에러 전용)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,

                    -- 에러 정보
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    stack_hash TEXT,
                    severity TEXT NOT NULL,

                    -- 사용자 정보
                    user_id_hash TEXT NOT NULL,
                    user_tier TEXT NOT NULL,
                    is_paid_user BOOLEAN NOT NULL DEFAULT 0,

                    -- 컨텍스트 정보
                    session_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    project_id TEXT,
                    branch_id TEXT,
                    context_id TEXT,

                    -- 관련 이벤트
                    related_event_name TEXT,

                    -- 메타데이터 (JSON)
                    metadata TEXT NOT NULL DEFAULT '{}',

                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # telemetry_traces 테이블 생성 (성능 추적 전용)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,

                    -- 추적 정보
                    operation_name TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    success BOOLEAN NOT NULL DEFAULT 1,
                    result_count INTEGER,

                    -- 사용자 정보
                    user_id_hash TEXT NOT NULL,
                    user_tier TEXT NOT NULL,
                    is_paid_user BOOLEAN NOT NULL DEFAULT 0,

                    -- 컨텍스트 정보
                    session_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    project_id TEXT,
                    branch_id TEXT,
                    context_id TEXT,

                    -- 메타데이터 (JSON)
                    metadata TEXT NOT NULL DEFAULT '{}',

                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # telemetry_metrics 테이블 생성 (집계 데이터)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_date DATE NOT NULL,
                    service TEXT NOT NULL,
                    user_tier TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    total_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    avg_duration_ms REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(metric_date, service, user_tier, event_type)
                )
            """
            )

            # telemetry_user_sessions 테이블 생성 (v2.0 스키마)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    user_id_hash TEXT NOT NULL,
                    user_tier TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    started_at DATETIME NOT NULL,
                    last_activity DATETIME NOT NULL,
                    event_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 인덱스 생성 (검색 성능 향상) - v2.0 스키마
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_timestamp
                ON telemetry_events(timestamp)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_channel
                ON telemetry_events(channel)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_user_tier
                ON telemetry_events(user_tier)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_event_name
                ON telemetry_events(event_name)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_is_paid_user
                ON telemetry_events(is_paid_user)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_project
                ON telemetry_events(project_id)
            """
            )

            conn.commit()

    def save_event(self, event: TelemetryEvent):
        """
        텔레메트리 이벤트 저장 (v2.0 표준 스키마)

        Args:
            event: TelemetryEvent 객체
        """
        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()

                # 이벤트 저장 (NEW SCHEMA)
                cursor.execute(
                    """
                    INSERT INTO telemetry_events (
                        timestamp, event_name, user_id_hash, user_tier, is_paid_user,
                        session_id, channel, project_id, branch_id, context_id,
                        result, duration_ms, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event.timestamp,
                        event.event_name,
                        event.user_id_hash,
                        event.user_tier,
                        event.is_paid_user,
                        event.session_id,
                        event.channel,
                        event.project_id,
                        event.branch_id,
                        event.context_id,
                        event.result,
                        event.duration_ms,
                        json.dumps(event.metadata, ensure_ascii=False),
                    ),
                )

                # 세션 정보 업데이트 (UPSERT) - v2.0 스키마 (channel 사용)
                cursor.execute(
                    """
                    INSERT INTO telemetry_user_sessions (
                        session_id, user_id_hash, user_tier, channel,
                        started_at, last_activity, event_count
                    ) VALUES (?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT(session_id) DO UPDATE SET
                        last_activity = ?,
                        event_count = event_count + 1
                """,
                    (
                        event.session_id,
                        event.user_id_hash,
                        event.user_tier,
                        event.channel,
                        event.timestamp,
                        event.timestamp,
                        event.timestamp,
                    ),
                )

                conn.commit()

        except Exception as e:
            # Fail-Safe: 저장 실패는 무시 (텔레메트리는 핵심 기능에 영향 없음)
            print(f"[WARNING] Failed to save telemetry event: {e}")

    def save_error(self, error: "TelemetryError"):
        """
        텔레메트리 에러 저장 (v2.0 3-pipeline 구조)

        Args:
            error: TelemetryError 객체
        """
        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()

                # 에러 저장
                cursor.execute(
                    """
                    INSERT INTO telemetry_errors (
                        timestamp, error_type, error_message, stack_trace, stack_hash, severity,
                        user_id_hash, user_tier, is_paid_user,
                        session_id, channel, project_id, branch_id, context_id,
                        related_event_name, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        error.timestamp,
                        error.error_type,
                        error.error_message,
                        error.stack_trace,
                        error.stack_hash,
                        error.severity,
                        error.user_id_hash,
                        error.user_tier,
                        error.is_paid_user,
                        error.session_id,
                        error.channel,
                        error.project_id,
                        error.branch_id,
                        error.context_id,
                        error.related_event_name,
                        json.dumps(error.metadata, ensure_ascii=False),
                    ),
                )

                conn.commit()

        except Exception as e:
            # Fail-Safe: 저장 실패는 무시
            print(f"[WARNING] Failed to save telemetry error: {e}")

    def save_trace(self, trace: "TelemetryTrace"):
        """
        텔레메트리 추적 저장 (v2.0 3-pipeline 구조)

        Args:
            trace: TelemetryTrace 객체
        """
        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()

                # 추적 저장
                cursor.execute(
                    """
                    INSERT INTO telemetry_traces (
                        timestamp, operation_name, duration_ms, success, result_count,
                        user_id_hash, user_tier, is_paid_user,
                        session_id, channel, project_id, branch_id, context_id,
                        metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        trace.timestamp,
                        trace.operation_name,
                        trace.duration_ms,
                        trace.success,
                        trace.result_count,
                        trace.user_id_hash,
                        trace.user_tier,
                        trace.is_paid_user,
                        trace.session_id,
                        trace.channel,
                        trace.project_id,
                        trace.branch_id,
                        trace.context_id,
                        json.dumps(trace.metadata, ensure_ascii=False),
                    ),
                )

                conn.commit()

        except Exception as e:
            # Fail-Safe: 저장 실패는 무시
            print(f"[WARNING] Failed to save telemetry trace: {e}")

    def get_events(
        self,
        service: Optional[str] = None,
        user_tier: Optional[str] = None,
        event_type: Optional[str] = None,
        project_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        텔레메트리 이벤트 조회

        Args:
            service: 서비스 필터 ('mcp', 'extension', 'web')
            user_tier: 티어 필터 ('free', 'paid', 'enterprise')
            event_type: 이벤트 타입 필터
            project_id: 프로젝트 ID 필터
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 결과 수
            offset: 오프셋

        Returns:
            이벤트 딕셔너리 리스트
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 동적 쿼리 생성
                query = "SELECT * FROM telemetry_events WHERE 1=1"
                params = []

                if service:
                    query += " AND service = ?"
                    params.append(service)

                if user_tier:
                    query += " AND user_tier = ?"
                    params.append(user_tier)

                if event_type:
                    query += " AND event_type = ?"
                    params.append(event_type)

                if project_id:
                    query += " AND project_id = ?"
                    params.append(project_id)

                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())

                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())

                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Row를 딕셔너리로 변환
                events = []
                for row in rows:
                    event_dict = dict(row)
                    # JSON 파싱
                    if event_dict.get("event_data"):
                        event_dict["event_data"] = json.loads(event_dict["event_data"])
                    events.append(event_dict)

                return events

        except Exception as e:
            print(f"[WARNING] Failed to get telemetry events: {e}")
            return []

    def get_metrics(
        self,
        service: Optional[str] = None,
        user_tier: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        집계 메트릭 조회

        Args:
            service: 서비스 필터
            user_tier: 티어 필터
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            메트릭 딕셔너리 리스트
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM telemetry_metrics WHERE 1=1"
                params = []

                if service:
                    query += " AND service = ?"
                    params.append(service)

                if user_tier:
                    query += " AND user_tier = ?"
                    params.append(user_tier)

                if start_date:
                    query += " AND metric_date >= ?"
                    params.append(start_date.date().isoformat())

                if end_date:
                    query += " AND metric_date <= ?"
                    params.append(end_date.date().isoformat())

                query += " ORDER BY metric_date DESC"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [dict(row) for row in rows]

        except Exception as e:
            print(f"[WARNING] Failed to get telemetry metrics: {e}")
            return []

    def aggregate_daily_metrics(self, target_date: Optional[datetime] = None):
        """
        일일 메트릭 집계 (배치 작업)

        Args:
            target_date: 집계 대상 날짜 (기본: 어제)
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc) - timedelta(days=1)

        try:
            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()

                # 해당 날짜의 이벤트 집계
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO telemetry_metrics (
                        metric_date, service, user_tier, event_type,
                        total_count, success_count, error_count, avg_duration_ms
                    )
                    SELECT
                        DATE(timestamp) as metric_date,
                        service,
                        user_tier,
                        event_type,
                        COUNT(*) as total_count,
                        SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) as success_count,
                        SUM(CASE WHEN result = 'error' THEN 1 ELSE 0 END) as error_count,
                        AVG(duration_ms) as avg_duration_ms
                    FROM telemetry_events
                    WHERE DATE(timestamp) = ?
                    GROUP BY DATE(timestamp), service, user_tier, event_type
                """,
                    (target_date.date().isoformat(),),
                )

                conn.commit()

        except Exception as e:
            print(f"[WARNING] Failed to aggregate daily metrics: {e}")

    def cleanup_old_events(self, days_to_keep: int = 90):
        """
        오래된 이벤트 삭제 (GDPR 준수)

        Args:
            days_to_keep: 보관 기간 (일)
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

            with self._lock, self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    DELETE FROM telemetry_events
                    WHERE timestamp < ?
                """,
                    (cutoff_date.isoformat(),),
                )

                deleted_count = cursor.rowcount
                conn.commit()

                print(f"[INFO] Deleted {deleted_count} old telemetry events")

        except Exception as e:
            print(f"[WARNING] Failed to cleanup old events: {e}")

    def get_user_sessions(
        self,
        user_tier: Optional[str] = None,
        service: Optional[str] = None,
        active_only: bool = False,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        사용자 세션 조회

        Args:
            user_tier: 티어 필터
            service: 서비스 필터
            active_only: 최근 24시간 이내 활성 세션만 조회
            limit: 최대 결과 수

        Returns:
            세션 딕셔너리 리스트
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM telemetry_user_sessions WHERE 1=1"
                params = []

                if user_tier:
                    query += " AND user_tier = ?"
                    params.append(user_tier)

                if service:
                    query += " AND service = ?"
                    params.append(service)

                if active_only:
                    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
                    query += " AND last_activity >= ?"
                    params.append(cutoff)

                query += " ORDER BY last_activity DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [dict(row) for row in rows]

        except Exception as e:
            print(f"[WARNING] Failed to get user sessions: {e}")
            return []


# 전역 싱글톤 인스턴스
_storage_instance = None


def get_telemetry_storage() -> TelemetryStorage:
    """텔레메트리 저장소 싱글톤 반환"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = TelemetryStorage()
    return _storage_instance
