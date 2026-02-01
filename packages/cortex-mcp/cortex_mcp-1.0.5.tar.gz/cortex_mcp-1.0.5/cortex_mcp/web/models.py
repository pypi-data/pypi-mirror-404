"""
Cortex MCP - Web Database Models
SQLite 기반 사용자 및 라이센스 관리 (수동 승인 방식)
"""

import hashlib
import secrets
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# DB 경로
DB_PATH = Path.home() / ".cortex" / "web" / "cortex_web.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class Database:
    """SQLite 데이터베이스 관리"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

        # v3: 계산 결과 캐싱 (5분 TTL)
        self._cache: Dict[str, tuple] = {}  # {cache_key: (value, timestamp)}
        self._cache_ttl = 300  # 5분 (초 단위)

    def _init_db(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 사용자 테이블
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_id INTEGER UNIQUE NOT NULL,
                github_login TEXT NOT NULL,
                email TEXT,
                avatar_url TEXT,
                license_key TEXT UNIQUE,
                license_type TEXT,
                approval_status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """
        )

        # 사용자 통계 테이블 (각 사용자별 AlphaLogger 데이터)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                module_name TEXT NOT NULL,
                total_calls INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                total_latency_ms REAL DEFAULT 0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, module_name)
            )
        """
        )

        # 세션 테이블
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
        )

        # 연구 메트릭 테이블 (structure.md 6.5 - 실제 측정 데이터)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS research_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                beta_phase TEXT NOT NULL,
                context_stability_score REAL,
                recovery_time_ms REAL,
                intervention_precision REAL,
                user_acceptance_count INTEGER DEFAULT 0,
                user_rejection_count INTEGER DEFAULT 0,
                session_id TEXT,
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
        )

        # 베타 페이즈 설정 테이블
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS beta_phase_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phase_name TEXT UNIQUE NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                max_users INTEGER,
                is_active BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """
        )

        # 기본 베타 페이즈 삽입
        cursor.execute(
            """
            INSERT OR IGNORE INTO beta_phase_config (phase_name, start_date, max_users, is_active, created_at)
            VALUES ('closed_beta', ?, 30, 1, ?)
        """,
            (datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()),
        )

        # 오류 로그 테이블 (전체 시스템 오류 수집)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                error_type TEXT NOT NULL,
                tool_name TEXT,
                error_message TEXT NOT NULL,
                stack_trace TEXT,
                context TEXT,
                severity TEXT DEFAULT 'error',
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
        )

        # 스키마 버전 테이블 (마이그레이션 관리)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
        """
        )

        # 현재 스키마 버전 확인
        cursor.execute("SELECT version FROM schema_version WHERE id = 1")
        row = cursor.fetchone()
        current_version = row[0] if row else 0

        # 마이그레이션 실행
        self._run_migrations(cursor, current_version)

        conn.commit()
        conn.close()

    def _run_migrations(self, cursor, current_version: int):
        """스키마 마이그레이션 실행

        Args:
            cursor: SQLite cursor
            current_version: 현재 데이터베이스 스키마 버전
        """
        TARGET_VERSION = 5  # 최신 스키마 버전

        if current_version >= TARGET_VERSION:
            return  # 이미 최신 버전

        # Migration v0 -> v1: 초기 버전 기록
        if current_version < 1:
            cursor.execute(
                """
                INSERT OR REPLACE INTO schema_version (id, version, updated_at)
                VALUES (1, 1, ?)
            """,
                (datetime.now(timezone.utc).isoformat(),),
            )
            current_version = 1

        # Migration v1 -> v2: user_stats와 sessions에 project_id 추가
        if current_version < 2:
            # user_stats 테이블에 project_id 컬럼 추가
            try:
                cursor.execute("ALTER TABLE user_stats ADD COLUMN project_id TEXT")
            except sqlite3.OperationalError:
                # 이미 컬럼이 존재하면 무시
                pass

            # sessions 테이블에 project_id 추가
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN project_id TEXT")
            except sqlite3.OperationalError:
                pass

            # sessions 테이블에 session_start, session_end 추가 (세션 시간 측정용)
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN session_start TEXT")
                cursor.execute("ALTER TABLE sessions ADD COLUMN session_end TEXT")
            except sqlite3.OperationalError:
                pass

            # UNIQUE 제약 조건 수정: (user_id, module_name) -> (user_id, module_name, project_id)
            # SQLite는 ALTER TABLE로 제약 조건을 수정할 수 없으므로 재생성 필요
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_stats'")
            if cursor.fetchone():
                # 임시 테이블로 데이터 백업
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_stats_backup AS
                    SELECT * FROM user_stats
                """
                )

                # 기존 테이블 삭제
                cursor.execute("DROP TABLE user_stats")

                # 새 스키마로 재생성
                cursor.execute(
                    """
                    CREATE TABLE user_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        module_name TEXT NOT NULL,
                        project_id TEXT,
                        total_calls INTEGER DEFAULT 0,
                        success_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0,
                        total_latency_ms REAL DEFAULT 0,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        UNIQUE(user_id, module_name, project_id)
                    )
                """
                )

                # 데이터 복원 (project_id는 NULL)
                cursor.execute(
                    """
                    INSERT INTO user_stats (id, user_id, module_name, total_calls,
                                          success_count, error_count, total_latency_ms, updated_at)
                    SELECT id, user_id, module_name, total_calls,
                           success_count, error_count, total_latency_ms, updated_at
                    FROM user_stats_backup
                """
                )

                # 백업 테이블 삭제
                cursor.execute("DROP TABLE user_stats_backup")

            # 버전 업데이트
            cursor.execute(
                """
                UPDATE schema_version
                SET version = 2, updated_at = ?
                WHERE id = 1
            """,
                (datetime.now(timezone.utc).isoformat(),),
            )
            current_version = 2

        # Migration v2 -> v3: 성능 최적화를 위한 인덱스 추가
        if current_version < 3:
            # user_stats 테이블 인덱스
            try:
                # updated_at 인덱스 (DAU/MAU 계산용)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_user_stats_updated_at
                    ON user_stats(updated_at)
                """
                )

                # project_id 인덱스 (Active Projects 계산용)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_user_stats_project_id
                    ON user_stats(project_id)
                """
                )

                # (updated_at, project_id) 복합 인덱스 (Active Projects 최적화)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_user_stats_updated_project
                    ON user_stats(updated_at, project_id)
                """
                )
            except sqlite3.OperationalError:
                pass

            # sessions 테이블 인덱스
            try:
                # session_start 인덱스 (Avg Session Duration 계산용)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_sessions_start
                    ON sessions(session_start)
                """
                )

                # session_end 인덱스 (Avg Session Duration 계산용)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_sessions_end
                    ON sessions(session_end)
                """
                )

                # (session_start, session_end) 복합 인덱스 (duration 계산 최적화)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_sessions_start_end
                    ON sessions(session_start, session_end)
                """
                )
            except sqlite3.OperationalError:
                pass

            # research_metrics 테이블 인덱스
            try:
                # recorded_at 인덱스 (최근 메트릭 조회용)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_research_metrics_recorded_at
                    ON research_metrics(recorded_at)
                """
                )

                # (user_id, recorded_at) 복합 인덱스 (사용자별 메트릭 조회 최적화)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_research_metrics_user_recorded
                    ON research_metrics(user_id, recorded_at)
                """
                )
            except sqlite3.OperationalError:
                pass

            # error_logs 테이블 인덱스
            try:
                # recorded_at 인덱스 (최근 에러 조회용)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_error_logs_recorded_at
                    ON error_logs(recorded_at)
                """
                )

                # severity 인덱스 (심각도별 필터링용)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_error_logs_severity
                    ON error_logs(severity)
                """
                )

                # (recorded_at, severity) 복합 인덱스 (최적화)
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_error_logs_recorded_severity
                    ON error_logs(recorded_at, severity)
                """
                )
            except sqlite3.OperationalError:
                pass

            # 버전 업데이트
            cursor.execute(
                """
                UPDATE schema_version
                SET version = 3, updated_at = ?
                WHERE id = 1
            """,
                (datetime.now(timezone.utc).isoformat(),),
            )
            current_version = 3

        # Migration v3 -> v4: Phase 9 Hallucination Detection 데이터 수집
        if current_version < 4:
            # research_metrics 테이블에 Phase 9 필드 추가
            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN grounding_score REAL")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN confidence_level TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN total_claims INTEGER")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN unverified_claims INTEGER")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN hallucination_detected INTEGER")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN hallucination_occurred_at TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN hallucination_detected_at TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN drift_occurred_at TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN drift_detected_at TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN requires_retry INTEGER")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN retry_reason TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN claim_types_json TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE research_metrics ADD COLUMN context_depth_avg REAL")
            except sqlite3.OperationalError:
                pass

            # 버전 업데이트
            cursor.execute(
                """
                UPDATE schema_version
                SET version = 4, updated_at = ?
                WHERE id = 1
            """,
                (datetime.now(timezone.utc).isoformat(),),
            )

        # Migration v4 -> v5: 베타 테스트 그룹 설정 (Control/Treatment)
        if current_version < 5:
            # users 테이블에 experiment_group 컬럼 추가
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN experiment_group TEXT DEFAULT 'treatment1'")
            except sqlite3.OperationalError:
                pass

            # 기존 사용자에게 무작위 그룹 할당 (균등 분배: 33.3% 각)
            import random
            cursor.execute("SELECT id FROM users")
            user_ids = [row[0] for row in cursor.fetchall()]

            groups = ['control', 'treatment1', 'treatment2']
            for user_id in user_ids:
                group = random.choice(groups)
                cursor.execute("UPDATE users SET experiment_group = ? WHERE id = ?", (group, user_id))

            # 버전 업데이트
            cursor.execute(
                """
                UPDATE schema_version
                SET version = 5, updated_at = ?
                WHERE id = 1
            """,
                (datetime.now(timezone.utc).isoformat(),),
            )

    def create_user(
        self,
        github_id: int,
        github_login: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """새 사용자 생성 (승인 대기 상태)"""
        import random

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 무작위 실험 그룹 할당 (균등 분배)
            experiment_group = random.choice(['control', 'treatment1', 'treatment2'])

            # DB에 사용자 삽입 (승인 대기 상태, 라이센스 없음)
            cursor.execute(
                """
                INSERT INTO users (github_id, github_login, email, avatar_url,
                                 approval_status, created_at, last_login, experiment_group)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    github_id,
                    github_login,
                    email,
                    avatar_url,
                    "pending",  # 승인 대기
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                    experiment_group,
                ),
            )

            conn.commit()
            user_id = cursor.lastrowid

            return {
                "success": True,
                "user_id": user_id,
                "approval_status": "pending",
                "github_login": github_login,
            }

        except sqlite3.IntegrityError:
            return {"success": False, "error": "User already exists"}
        finally:
            conn.close()

    def approve_user(self, user_id: int, license_type: str = "closed_beta") -> Dict[str, Any]:
        """사용자 승인 및 라이센스 발급"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # 사용자 조회
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()

            if not user:
                return {"success": False, "error": "User not found"}

            if user["approval_status"] == "approved":
                return {"success": False, "error": "User already approved"}

            # 라이센스 키 생성
            import sys
            from pathlib import Path

            # core 모듈 경로 추가
            core_path = Path(__file__).parent.parent / "core"
            if str(core_path) not in sys.path:
                sys.path.insert(0, str(core_path.parent))

            from core.license_manager import LicenseManager, LicenseType

            lm = LicenseManager()

            # 라이센스 타입 매핑
            license_type_enum = (
                LicenseType.CLOSED_BETA if license_type == "closed_beta" else LicenseType.ADMIN
            )

            license_result = lm.generate_license_key(
                license_type=license_type_enum,
                user_email=user["email"] or f"{user['github_login']}@github.user",
            )

            if not license_result["success"]:
                return {"success": False, "error": "Failed to generate license"}

            license_key = license_result["license_key"]

            # GitHub 계정 바인딩
            lm.bind_github_account(license_key, user["github_login"], user["github_id"])

            # DB 업데이트 (승인 상태로 변경, 라이센스 키 저장)
            cursor.execute(
                """
                UPDATE users
                SET approval_status = 'approved',
                    license_key = ?,
                    license_type = ?
                WHERE id = ?
            """,
                (license_key, license_type, user_id),
            )

            conn.commit()

            return {
                "success": True,
                "user_id": user_id,
                "license_key": license_key,
                "license_type": license_type,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def reject_user(self, user_id: int) -> Dict[str, Any]:
        """사용자 승인 거부"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE users SET approval_status = 'rejected' WHERE id = ?
            """,
                (user_id,),
            )

            conn.commit()

            return {"success": True, "user_id": user_id}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def reset_to_pending(self, user_id: int) -> Dict[str, Any]:
        """거절된 사용자를 다시 승인 대기 상태로 변경"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE users SET approval_status = 'pending' WHERE id = ?
            """,
                (user_id,),
            )

            conn.commit()

            return {"success": True, "user_id": user_id}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """사용자 완전 삭제 (Admin 전용)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 사용자 통계 먼저 삭제 (외래키 제약)
            cursor.execute("DELETE FROM user_stats WHERE user_id = ?", (user_id,))

            # 사용자 삭제
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

            conn.commit()

            return {"success": True, "user_id": user_id}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_pending_users(self) -> List[Dict[str, Any]]:
        """승인 대기 중인 사용자 목록"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE approval_status = 'pending'
            ORDER BY created_at ASC
        """
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_user_by_github_id(self, github_id: int) -> Optional[Dict[str, Any]]:
        """GitHub ID로 사용자 조회"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE github_id = ?", (github_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def update_last_login(self, user_id: int):
        """마지막 로그인 시간 업데이트"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users SET last_login = ? WHERE id = ?
        """,
            (datetime.now(timezone.utc).isoformat(), user_id),
        )

        conn.commit()
        conn.close()

    def create_session(self, user_id: int, expires_hours: int = 24) -> str:
        """세션 토큰 생성"""
        session_token = secrets.token_urlsafe(32)
        created_at = datetime.now(timezone.utc)
        expires_at = created_at.replace(hour=created_at.hour + expires_hours)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO sessions (user_id, session_token, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """,
            (user_id, session_token, created_at.isoformat(), expires_at.isoformat()),
        )

        conn.commit()
        conn.close()

        return session_token

    def validate_session(self, session_token: str) -> Optional[int]:
        """세션 유효성 검증 (user_id 반환)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT user_id, expires_at FROM sessions WHERE session_token = ?
        """,
            (session_token,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        user_id, expires_at_str = row
        expires_at = datetime.fromisoformat(expires_at_str)

        if datetime.now(timezone.utc) > expires_at:
            return None  # 세션 만료

        return user_id

    def get_user_stats(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자 통계 조회"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM user_stats WHERE user_id = ?
        """,
            (user_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_user_stats(
        self,
        user_id: int,
        module_name: str,
        total_calls: int,
        success_count: int,
        error_count: int,
        total_latency_ms: float,
        project_id: Optional[str] = None,
    ):
        """사용자 통계 업데이트

        Args:
            user_id: 사용자 ID
            module_name: 모듈 이름 (예: 'memory_manager', 'search_context')
            total_calls: 총 호출 횟수
            success_count: 성공 횟수
            error_count: 에러 횟수
            total_latency_ms: 총 지연 시간 (밀리초)
            project_id: 프로젝트 ID (선택, v2 스키마부터 지원)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO user_stats (user_id, module_name, project_id, total_calls, success_count, error_count, total_latency_ms, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, module_name, project_id) DO UPDATE SET
                total_calls = excluded.total_calls,
                success_count = excluded.success_count,
                error_count = excluded.error_count,
                total_latency_ms = excluded.total_latency_ms,
                updated_at = excluded.updated_at
        """,
            (
                user_id,
                module_name,
                project_id,
                total_calls,
                success_count,
                error_count,
                total_latency_ms,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    def list_all_users(self) -> List[Dict[str, Any]]:
        """모든 사용자 목록 (Admin용)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_all_stats(self) -> List[Dict[str, Any]]:
        """전체 사용자 통계 (Admin용)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_stats ORDER BY total_calls DESC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def record_research_metric(
        self,
        user_id: int,
        beta_phase: str,
        context_stability_score: float = None,
        recovery_time_ms: float = None,
        intervention_precision: float = None,
        user_acceptance_count: int = 0,
        user_rejection_count: int = 0,
        session_id: str = None,
        # Phase 9 Hallucination Detection 필드
        grounding_score: float = None,
        confidence_level: str = None,
        total_claims: int = None,
        unverified_claims: int = None,
        hallucination_detected: bool = None,
        hallucination_occurred_at: str = None,
        hallucination_detected_at: str = None,
        drift_occurred_at: str = None,
        drift_detected_at: str = None,
        requires_retry: bool = None,
        retry_reason: str = None,
        claim_types_json: str = None,
        context_depth_avg: float = None,
    ):
        """연구 메트릭 기록"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO research_metrics (
                user_id, beta_phase, context_stability_score, recovery_time_ms,
                intervention_precision, user_acceptance_count, user_rejection_count,
                session_id, recorded_at,
                grounding_score, confidence_level, total_claims, unverified_claims,
                hallucination_detected, hallucination_occurred_at, hallucination_detected_at,
                drift_occurred_at, drift_detected_at, requires_retry, retry_reason,
                claim_types_json, context_depth_avg
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user_id,
                beta_phase,
                context_stability_score,
                recovery_time_ms,
                intervention_precision,
                user_acceptance_count,
                user_rejection_count,
                session_id,
                datetime.now(timezone.utc).isoformat(),
                grounding_score,
                confidence_level,
                total_claims,
                unverified_claims,
                1 if hallucination_detected else 0 if hallucination_detected is not None else None,
                hallucination_occurred_at,
                hallucination_detected_at,
                drift_occurred_at,
                drift_detected_at,
                1 if requires_retry else 0 if requires_retry is not None else None,
                retry_reason,
                claim_types_json,
                context_depth_avg,
            ),
        )

        conn.commit()
        conn.close()

    def get_research_metrics(self, beta_phase: str = None) -> List[Dict[str, Any]]:
        """연구 메트릭 조회 (베타 페이즈별)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if beta_phase:
            cursor.execute(
                """
                SELECT * FROM research_metrics
                WHERE beta_phase = ?
                ORDER BY recorded_at DESC
            """,
                (beta_phase,),
            )
        else:
            cursor.execute("SELECT * FROM research_metrics ORDER BY recorded_at DESC")

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_current_beta_phase(self) -> Optional[str]:
        """현재 활성 베타 페이즈 조회"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT phase_name FROM beta_phase_config
            WHERE is_active = 1
            LIMIT 1
        """
        )
        row = cursor.fetchone()
        conn.close()

        return row["phase_name"] if row else "closed_beta"

    def set_beta_phase(self, phase_name: str, max_users: int = None):
        """베타 페이즈 전환"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 기존 활성 페이즈 비활성화
        cursor.execute(
            "UPDATE beta_phase_config SET is_active = 0, end_date = ?",
            (datetime.now(timezone.utc).isoformat(),),
        )

        # 새 페이즈 활성화 또는 생성
        cursor.execute(
            """
            INSERT INTO beta_phase_config (phase_name, start_date, max_users, is_active, created_at)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(phase_name) DO UPDATE SET
                is_active = 1,
                start_date = excluded.start_date
        """,
            (
                phase_name,
                datetime.now(timezone.utc).isoformat(),
                max_users,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    def record_error_log(
        self,
        error_type: str,
        error_message: str,
        user_id: int = None,
        tool_name: str = None,
        stack_trace: str = None,
        context: str = None,
        severity: str = "error",
    ):
        """오류 로그 기록

        Args:
            error_type: 오류 타입 (mcp_tool_error, server_error, client_error, db_error)
            error_message: 오류 메시지
            user_id: 사용자 ID (선택, 비로그인 오류도 기록 가능)
            tool_name: MCP 도구명 (MCP 도구 오류인 경우)
            stack_trace: 스택 트레이스
            context: 추가 컨텍스트 (JSON 문자열)
            severity: 심각도 (critical, error, warning, info)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO error_logs (
                user_id, error_type, tool_name, error_message,
                stack_trace, context, severity, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user_id,
                error_type,
                tool_name,
                error_message,
                stack_trace,
                context,
                severity,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    def get_error_logs(
        self, limit: int = 100, severity: str = None, error_type: str = None, user_id: int = None
    ) -> List[Dict[str, Any]]:
        """오류 로그 조회

        Args:
            limit: 조회 개수 제한
            severity: 심각도 필터 (critical, error, warning, info)
            error_type: 오류 타입 필터
            user_id: 사용자 ID 필터

        Returns:
            오류 로그 목록
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM error_logs WHERE 1=1"
        params = []

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        if error_type:
            query += " AND error_type = ?"
            params.append(error_type)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        query += " ORDER BY recorded_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_error_stats(self) -> Dict[str, Any]:
        """오류 통계 조회

        Returns:
            {
                "total_errors": 전체 오류 수,
                "by_severity": {severity: count},
                "by_type": {error_type: count},
                "recent_24h": 최근 24시간 오류 수
            }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 전체 오류 수
        cursor.execute("SELECT COUNT(*) FROM error_logs")
        total_errors = cursor.fetchone()[0]

        # 심각도별 집계
        cursor.execute(
            """
            SELECT severity, COUNT(*) as count
            FROM error_logs
            GROUP BY severity
        """
        )
        by_severity = {row[0]: row[1] for row in cursor.fetchall()}

        # 타입별 집계
        cursor.execute(
            """
            SELECT error_type, COUNT(*) as count
            FROM error_logs
            GROUP BY error_type
        """
        )
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        # 최근 24시간 오류
        twenty_four_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        cursor.execute(
            """
            SELECT COUNT(*) FROM error_logs
            WHERE recorded_at >= ?
        """,
            (twenty_four_hours_ago,),
        )
        recent_24h = cursor.fetchone()[0]

        conn.close()

        return {
            "total_errors": total_errors,
            "by_severity": by_severity,
            "by_type": by_type,
            "recent_24h": recent_24h,
        }

    # ========== M&A 비즈니스 지표 계산 함수 ==========

    def calculate_dau(self) -> int:
        """DAU (Daily Active Users) 계산

        Returns:
            오늘 활동한 고유 사용자 수
        """
        # v3: 캐시 체크 (5분 TTL)
        cache_key = "dau"
        cached_value = self._get_cached(cache_key)
        if cached_value is not None:
            return cached_value

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

        cursor.execute(
            """
            SELECT COUNT(DISTINCT user_id)
            FROM user_stats
            WHERE updated_at >= ?
        """,
            (today_start,),
        )

        dau = cursor.fetchone()[0]
        conn.close()

        # v3: 캐시 저장
        self._set_cache(cache_key, dau)

        return dau

    def calculate_mau(self) -> int:
        """MAU (Monthly Active Users) 계산

        Returns:
            최근 30일간 활동한 고유 사용자 수
        """
        # v3: 캐시 체크 (5분 TTL)
        cache_key = "mau"
        cached_value = self._get_cached(cache_key)
        if cached_value is not None:
            return cached_value

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

        cursor.execute(
            """
            SELECT COUNT(DISTINCT user_id)
            FROM user_stats
            WHERE updated_at >= ?
        """,
            (thirty_days_ago,),
        )

        mau = cursor.fetchone()[0]
        conn.close()

        # v3: 캐시 저장
        self._set_cache(cache_key, mau)

        return mau

    def calculate_retention_d7(self) -> float:
        """D7 Retention (7일 유지율) 계산

        Returns:
            7일 전 가입 사용자 중 오늘 활동한 비율 (0.0 ~ 1.0)
        """
        # v3: 캐시 체크 (5분 TTL)
        cache_key = "retention_d7"
        cached_value = self._get_cached(cache_key)
        if cached_value is not None:
            return cached_value

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        seven_days_ago_start = (datetime.now(timezone.utc) - timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        seven_days_ago_end = (datetime.now(timezone.utc) - timedelta(days=7)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        ).isoformat()
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

        # 7일 전 가입한 사용자 수
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= ? AND created_at <= ?
        """,
            (seven_days_ago_start, seven_days_ago_end),
        )
        cohort_size = cursor.fetchone()[0]

        if cohort_size == 0:
            conn.close()
            # v3: 캐시 저장
            self._set_cache(cache_key, 0.0)
            return 0.0

        # 7일 전 가입한 사용자 중 오늘 활동한 사용자 수
        cursor.execute(
            """
            SELECT COUNT(DISTINCT us.user_id)
            FROM user_stats us
            INNER JOIN users u ON us.user_id = u.id
            WHERE u.created_at >= ? AND u.created_at <= ?
              AND us.updated_at >= ?
        """,
            (seven_days_ago_start, seven_days_ago_end, today_start),
        )
        retained_users = cursor.fetchone()[0]
        conn.close()

        retention_rate = retained_users / cohort_size

        # v3: 캐시 저장
        self._set_cache(cache_key, retention_rate)

        return retention_rate

    def calculate_active_projects(self) -> int:
        """활성 프로젝트 수 계산

        Returns:
            최근 30일간 활동이 있는 고유 프로젝트 수
        """
        # v3: 캐시 체크 (5분 TTL)
        cache_key = "active_projects"
        cached_value = self._get_cached(cache_key)
        if cached_value is not None:
            return cached_value

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

        cursor.execute(
            """
            SELECT COUNT(DISTINCT project_id)
            FROM user_stats
            WHERE updated_at >= ?
              AND project_id IS NOT NULL
        """,
            (thirty_days_ago,),
        )

        active_projects = cursor.fetchone()[0]
        conn.close()

        # v3: 캐시 저장
        self._set_cache(cache_key, active_projects)

        return active_projects

    def calculate_avg_session_duration(self) -> float:
        """평균 세션 시간 계산

        Returns:
            평균 세션 시간 (초)
        """
        # v3: 캐시 체크 (5분 TTL)
        cache_key = "avg_session_duration"
        cached_value = self._get_cached(cache_key)
        if cached_value is not None:
            return cached_value

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # sessions 테이블에서 session_start와 session_end가 모두 있는 레코드 조회
        cursor.execute(
            """
            SELECT session_start, session_end
            FROM sessions
            WHERE session_start IS NOT NULL
              AND session_end IS NOT NULL
        """
        )

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            # v3: 캐시 저장 (0.0도 캐싱)
            self._set_cache(cache_key, 0.0)
            return 0.0

        # 각 세션의 duration 계산 (초 단위)
        total_duration_sec = 0.0
        valid_session_count = 0

        for row in rows:
            session_start_str, session_end_str = row
            try:
                # ISO 8601 형식 파싱
                start_dt = datetime.fromisoformat(session_start_str.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(session_end_str.replace("Z", "+00:00"))

                # duration 계산 (초)
                duration_sec = (end_dt - start_dt).total_seconds()

                # 음수 duration은 무시 (잘못된 데이터)
                if duration_sec >= 0:
                    total_duration_sec += duration_sec
                    valid_session_count += 1
            except (ValueError, AttributeError):
                # 파싱 실패 시 해당 레코드 무시
                continue

        if valid_session_count == 0:
            # v3: 캐시 저장
            self._set_cache(cache_key, 0.0)
            return 0.0

        # 평균 계산 (초)
        avg_duration = total_duration_sec / valid_session_count

        # v3: 캐시 저장
        self._set_cache(cache_key, avg_duration)

        return avg_duration

    # ========== 제품 품질 지표 계산 함수 ==========

    def calculate_hallucination_detection_rate(self) -> float:
        """할루시네이션 검출율 계산 (성공률)

        Returns:
            할루시네이션 검출 성공률 (0.0 ~ 1.0)
            실제로는 Context Stability Score의 평균으로 근사
        """
        # v3: 캐시 체크 (5분 TTL)
        cache_key = "hallucination_detection_rate"
        cached_value = self._get_cached(cache_key)
        if cached_value is not None:
            return cached_value

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT AVG(context_stability_score)
            FROM research_metrics
            WHERE context_stability_score IS NOT NULL
        """
        )

        avg_score = cursor.fetchone()[0]
        conn.close()

        result = avg_score if avg_score else 0.0

        # v3: 캐시 저장
        self._set_cache(cache_key, result)

        return result

    def calculate_reference_accuracy(self) -> float:
        """참조 정확도 계산 (Reference History 추천 수락률)

        Returns:
            참조 정확도 (0.0 ~ 1.0), 목표: 95%
        """
        # v3: 캐시 체크 (5분 TTL)
        cache_key = "reference_accuracy"
        cached_value = self._get_cached(cache_key)
        if cached_value is not None:
            return cached_value

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT SUM(user_acceptance_count), SUM(user_rejection_count)
            FROM research_metrics
        """
        )

        row = cursor.fetchone()
        conn.close()

        acceptance = row[0] if row[0] else 0
        rejection = row[1] if row[1] else 0

        total = acceptance + rejection

        if total == 0:
            # v3: 캐시 저장
            self._set_cache(cache_key, 0.0)
            return 0.0

        result = acceptance / total

        # v3: 캐시 저장
        self._set_cache(cache_key, result)

        return result

    def calculate_context_stability(self) -> float:
        """맥락 안정성 점수 계산

        Returns:
            평균 Context Stability Score (0.0 ~ 1.0)
        """
        # v3: 캐시 체크 (5분 TTL)
        cache_key = "context_stability"
        cached_value = self._get_cached(cache_key)
        if cached_value is not None:
            return cached_value

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT AVG(context_stability_score)
            FROM research_metrics
            WHERE context_stability_score IS NOT NULL
        """
        )

        avg_score = cursor.fetchone()[0]
        conn.close()

        result = avg_score if avg_score else 0.0

        # v3: 캐시 저장
        self._set_cache(cache_key, result)

        return result

    def calculate_rag_search_recall(self) -> float:
        """RAG 검색 재현율 계산

        Returns:
            RAG 검색 성공률 (0.0 ~ 1.0), 목표: 100%
        """
        # v3: 캐시 체크 (5분 TTL)
        cache_key = "rag_search_recall"
        cached_value = self._get_cached(cache_key)
        if cached_value is not None:
            return cached_value

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # search_context 모듈의 성공률
        cursor.execute(
            """
            SELECT SUM(success_count), SUM(total_calls)
            FROM user_stats
            WHERE module_name = 'search_context'
        """
        )

        row = cursor.fetchone()
        conn.close()

        success_count = row[0] if row[0] else 0
        total_calls = row[1] if row[1] else 0

        if total_calls == 0:
            # v3: 캐시 저장
            self._set_cache(cache_key, 0.0)
            return 0.0

        result = success_count / total_calls

        # v3: 캐시 저장
        self._set_cache(cache_key, result)

        return result

    def calculate_automation_success_rate(self) -> float:
        """자동화 성공률 계산

        Returns:
            전체 작업 성공률 (0.0 ~ 1.0), 목표: 80%+
        """
        # v3: 캐시 체크 (5분 TTL)
        cache_key = "automation_success_rate"
        cached_value = self._get_cached(cache_key)
        if cached_value is not None:
            return cached_value

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT SUM(success_count), SUM(total_calls)
            FROM user_stats
        """
        )

        row = cursor.fetchone()
        conn.close()

        success_count = row[0] if row[0] else 0
        total_calls = row[1] if row[1] else 0

        if total_calls == 0:
            # v3: 캐시 저장
            self._set_cache(cache_key, 0.0)
            return 0.0

        result = success_count / total_calls

        # v3: 캐시 저장
        self._set_cache(cache_key, result)

        return result

    # ========== 캐싱 헬퍼 메서드 (v3) ==========

    def _get_cached(self, cache_key: str) -> Optional[Any]:
        """캐시에서 값 가져오기 (TTL 체크)

        Args:
            cache_key: 캐시 키

        Returns:
            캐시된 값 (유효한 경우), 없거나 만료된 경우 None
        """
        if cache_key not in self._cache:
            return None

        value, timestamp = self._cache[cache_key]
        current_time = time.time()

        # TTL 체크 (5분 = 300초)
        if current_time - timestamp > self._cache_ttl:
            # 만료된 캐시 삭제
            del self._cache[cache_key]
            return None

        return value

    def _set_cache(self, cache_key: str, value: Any):
        """캐시에 값 저장

        Args:
            cache_key: 캐시 키
            value: 저장할 값
        """
        self._cache[cache_key] = (value, time.time())


# 싱글톤 인스턴스
_db: Optional[Database] = None


def get_db() -> Database:
    """Database 싱글톤 인스턴스 반환"""
    global _db
    if _db is None:
        _db = Database()
    return _db


# ============================================================
# Paper Data Analysis Functions (Phase 9 - 논문 지표 계산)
# ============================================================


def calculate_silent_failure_rate(beta_phase: str = "closed_beta") -> Dict[str, Any]:
    """
    Silent Failure Rate 계산

    Silent Failure = 할루시네이션 발생했지만 감지 안 됨
    Silent Failure Rate = Silent Failures / Total Hallucinations

    Args:
        beta_phase: 실험군 필터 (closed_beta, control, theory_enhanced 등)

    Returns:
        {
            "silent_failures": int,
            "detected_failures": int,
            "total_hallucinations": int,
            "silent_failure_rate": float (0.0-1.0)
        }
    """
    db = get_db()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()

    try:
        # hallucination_occurred_at이 NOT NULL인 경우 = 할루시네이션 발생
        # hallucination_detected = 0 (False) → Silent Failure
        # hallucination_detected = 1 (True) → Detected Failure
        cursor.execute(
            """
            SELECT
                COUNT(CASE WHEN hallucination_detected = 0 OR hallucination_detected IS NULL THEN 1 END) as silent,
                COUNT(CASE WHEN hallucination_detected = 1 THEN 1 END) as detected,
                COUNT(*) as total
            FROM research_metrics
            WHERE beta_phase = ?
              AND hallucination_occurred_at IS NOT NULL
        """,
            (beta_phase,),
        )

        row = cursor.fetchone()
        if not row:
            return {
                "silent_failures": 0,
                "detected_failures": 0,
                "total_hallucinations": 0,
                "silent_failure_rate": 0.0,
            }

        silent, detected, total = row
        rate = silent / total if total > 0 else 0.0

        return {
            "silent_failures": silent,
            "detected_failures": detected,
            "total_hallucinations": total,
            "silent_failure_rate": rate,
        }

    finally:
        conn.close()


def calculate_drift_detection_latency(beta_phase: str = "closed_beta") -> Dict[str, Any]:
    """
    Drift Detection Latency 계산

    Drift Detection Latency = drift_detected_at - drift_occurred_at (평균)

    Args:
        beta_phase: 실험군 필터

    Returns:
        {
            "avg_latency_seconds": float,
            "sample_count": int,
            "min_latency_seconds": float,
            "max_latency_seconds": float
        }

    Note:
        drift_occurred_at, drift_detected_at 데이터 수집이 아직 구현되지 않음.
        Context stability tracking 시스템에서 데이터 수집 필요.
    """
    db = get_db()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()

    try:
        # SQLite에서 ISO 8601 타임스탬프 차이 계산 (초 단위)
        cursor.execute(
            """
            SELECT
                AVG(CAST((julianday(drift_detected_at) - julianday(drift_occurred_at)) * 86400 AS REAL)) as avg_latency,
                COUNT(*) as sample_count,
                MIN(CAST((julianday(drift_detected_at) - julianday(drift_occurred_at)) * 86400 AS REAL)) as min_latency,
                MAX(CAST((julianday(drift_detected_at) - julianday(drift_occurred_at)) * 86400 AS REAL)) as max_latency
            FROM research_metrics
            WHERE beta_phase = ?
              AND drift_occurred_at IS NOT NULL
              AND drift_detected_at IS NOT NULL
        """,
            (beta_phase,),
        )

        row = cursor.fetchone()
        if not row or row[0] is None:
            return {
                "avg_latency_seconds": 0.0,
                "sample_count": 0,
                "min_latency_seconds": 0.0,
                "max_latency_seconds": 0.0,
            }

        avg_latency, count, min_latency, max_latency = row

        return {
            "avg_latency_seconds": float(avg_latency) if avg_latency else 0.0,
            "sample_count": int(count),
            "min_latency_seconds": float(min_latency) if min_latency else 0.0,
            "max_latency_seconds": float(max_latency) if max_latency else 0.0,
        }

    finally:
        conn.close()


def get_hallucination_risk_model_data(beta_phase: str = "closed_beta") -> List[Dict[str, Any]]:
    """
    Hallucination Risk Model 검증 데이터 추출

    Risk = confidence × (1 - evidence) × (1 - context_consistency)

    Returns:
        List of {
            "grounding_score": float,
            "confidence_level": str,
            "context_stability_score": float,
            "hallucination_detected": bool,
            "calculated_risk": float
        }
    """
    db = get_db()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                grounding_score,
                confidence_level,
                context_stability_score,
                hallucination_detected
            FROM research_metrics
            WHERE beta_phase = ?
              AND grounding_score IS NOT NULL
              AND confidence_level IS NOT NULL
        """,
            (beta_phase,),
        )

        # Confidence level → numeric mapping
        confidence_map = {
            "very_high": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.3,
            "none": 0.0,
        }

        results = []
        for row in cursor.fetchall():
            grounding, conf_level, context_stability, detected = row

            confidence_numeric = confidence_map.get(conf_level, 0.0)
            context_consistency = context_stability if context_stability else 0.5

            # Risk = confidence × (1 - evidence) × (1 - context_consistency)
            calculated_risk = confidence_numeric * (1 - grounding) * (1 - context_consistency)

            results.append(
                {
                    "grounding_score": grounding,
                    "confidence_level": conf_level,
                    "context_stability_score": context_stability,
                    "hallucination_detected": bool(detected),
                    "calculated_risk": calculated_risk,
                }
            )

        return results

    finally:
        conn.close()
