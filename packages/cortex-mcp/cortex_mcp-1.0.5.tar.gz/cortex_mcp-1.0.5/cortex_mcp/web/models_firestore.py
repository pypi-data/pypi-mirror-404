"""
Cortex MCP - Web Database Models (Firestore)
Cloud Run 배포용 Firestore 기반 사용자 및 라이센스 관리
"""

import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from google.cloud import firestore


class Database:
    """Firestore 데이터베이스 관리 (SQLite와 동일한 인터페이스)"""

    def __init__(self):
        self.db = firestore.Client()

    def create_user(
        self,
        github_id: int,
        github_login: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """새 사용자 생성 (승인 대기 상태)"""
        try:
            # 중복 체크
            existing_users = (
                self.db.collection("users")
                .where("github_id", "==", github_id)
                .limit(1)
                .stream()
            )

            if len(list(existing_users)) > 0:
                return {"success": False, "error": "User already exists"}

            # 새 사용자 생성
            user_ref = self.db.collection("users").document()
            user_data = {
                "id": int(user_ref.id[-8:], 16),  # ID는 문서 ID 해시값 사용
                "github_id": github_id,
                "github_login": github_login,
                "email": email,
                "avatar_url": avatar_url,
                "license_key": None,
                "license_type": None,
                "approval_status": "pending",
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_login": firestore.SERVER_TIMESTAMP,
                "is_active": True,
            }

            user_ref.set(user_data)

            return {
                "success": True,
                "user_id": user_data["id"],
                "approval_status": "pending",
                "github_login": github_login,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def approve_user(self, user_id: int, license_type: str = "closed_beta") -> Dict[str, Any]:
        """사용자 승인 및 라이센스 발급"""
        try:
            # 사용자 조회
            users = (
                self.db.collection("users")
                .where("id", "==", user_id)
                .limit(1)
                .stream()
            )

            user_docs = list(users)
            if not user_docs:
                return {"success": False, "error": "User not found"}

            user_doc = user_docs[0]
            user = user_doc.to_dict()

            if user["approval_status"] == "approved":
                return {"success": False, "error": "User already approved"}

            # 라이센스 키 생성
            import sys
            from pathlib import Path

            core_path = Path(__file__).parent.parent / "core"
            if str(core_path) not in sys.path:
                sys.path.insert(0, str(core_path.parent))

            from core.license_manager import LicenseManager, LicenseType

            lm = LicenseManager()

            license_type_enum = (
                LicenseType.CLOSED_BETA if license_type == "closed_beta" else LicenseType.ADMIN
            )

            license_result = lm.generate_license_key(
                license_type=license_type_enum,
                user_email=user.get("email") or f"{user['github_login']}@github.user",
            )

            if not license_result["success"]:
                return {"success": False, "error": "Failed to generate license"}

            license_key = license_result["license_key"]

            # GitHub 계정 바인딩
            lm.bind_github_account(license_key, user["github_login"], user["github_id"])

            # Firestore 업데이트
            user_doc.reference.update(
                {
                    "approval_status": "approved",
                    "license_key": license_key,
                    "license_type": license_type,
                }
            )

            return {
                "success": True,
                "user_id": user_id,
                "license_key": license_key,
                "license_type": license_type,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def reject_user(self, user_id: int) -> Dict[str, Any]:
        """사용자 승인 거부"""
        try:
            users = (
                self.db.collection("users")
                .where("id", "==", user_id)
                .limit(1)
                .stream()
            )

            user_docs = list(users)
            if not user_docs:
                return {"success": False, "error": "User not found"}

            user_docs[0].reference.update({"approval_status": "rejected"})

            return {"success": True, "user_id": user_id}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """사용자 완전 삭제 (Admin 전용)"""
        try:
            # 사용자 통계 먼저 삭제
            stats = (
                self.db.collection("user_stats")
                .where("user_id", "==", user_id)
                .stream()
            )
            for stat in stats:
                stat.reference.delete()

            # 사용자 삭제
            users = (
                self.db.collection("users")
                .where("id", "==", user_id)
                .limit(1)
                .stream()
            )

            user_docs = list(users)
            if user_docs:
                user_docs[0].reference.delete()

            return {"success": True, "user_id": user_id}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_pending_users(self) -> List[Dict[str, Any]]:
        """승인 대기 중인 사용자 목록"""
        docs = (
            self.db.collection("users")
            .where("approval_status", "==", "pending")
            .order_by("created_at")
            .stream()
        )

        users = []
        for doc in docs:
            user_data = doc.to_dict()
            # Timestamp를 ISO 형식 문자열로 변환
            if isinstance(user_data.get("created_at"), datetime):
                user_data["created_at"] = user_data["created_at"].isoformat()
            if isinstance(user_data.get("last_login"), datetime):
                user_data["last_login"] = user_data["last_login"].isoformat()
            users.append(user_data)

        return users

    def get_user_by_github_id(self, github_id: int) -> Optional[Dict[str, Any]]:
        """GitHub ID로 사용자 조회"""
        docs = (
            self.db.collection("users")
            .where("github_id", "==", github_id)
            .limit(1)
            .stream()
        )

        doc_list = list(docs)
        if not doc_list:
            return None

        user_data = doc_list[0].to_dict()

        # Timestamp 변환
        if isinstance(user_data.get("created_at"), datetime):
            user_data["created_at"] = user_data["created_at"].isoformat()
        if isinstance(user_data.get("last_login"), datetime):
            user_data["last_login"] = user_data["last_login"].isoformat()

        return user_data

    def update_last_login(self, user_id: int):
        """마지막 로그인 시간 업데이트"""
        users = (
            self.db.collection("users")
            .where("id", "==", user_id)
            .limit(1)
            .stream()
        )

        user_docs = list(users)
        if user_docs:
            user_docs[0].reference.update({"last_login": firestore.SERVER_TIMESTAMP})

    def create_session(self, user_id: int, expires_hours: int = 24) -> str:
        """세션 토큰 생성"""
        session_token = secrets.token_urlsafe(32)
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(hours=expires_hours)

        session_ref = self.db.collection("sessions").document(session_token)
        session_ref.set(
            {
                "user_id": user_id,
                "session_token": session_token,
                "created_at": created_at,
                "expires_at": expires_at,
            }
        )

        return session_token

    def validate_session(self, session_token: str) -> Optional[int]:
        """세션 유효성 검증 (user_id 반환)"""
        doc = self.db.collection("sessions").document(session_token).get()

        if not doc.exists:
            return None

        session_data = doc.to_dict()
        expires_at = session_data["expires_at"]

        if datetime.now(timezone.utc) > expires_at:
            return None  # 세션 만료

        return session_data["user_id"]

    def get_user_stats(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자 통계 조회"""
        docs = (
            self.db.collection("user_stats")
            .where("user_id", "==", user_id)
            .stream()
        )

        stats = []
        for doc in docs:
            stat_data = doc.to_dict()
            # Timestamp 변환
            if isinstance(stat_data.get("updated_at"), datetime):
                stat_data["updated_at"] = stat_data["updated_at"].isoformat()
            stats.append(stat_data)

        return stats

    def update_user_stats(
        self,
        user_id: int,
        module_name: str,
        total_calls: int,
        success_count: int,
        error_count: int,
        total_latency_ms: float,
    ):
        """사용자 통계 업데이트"""
        # 복합 키로 문서 ID 생성
        doc_id = f"{user_id}_{module_name}"

        self.db.collection("user_stats").document(doc_id).set(
            {
                "user_id": user_id,
                "module_name": module_name,
                "total_calls": total_calls,
                "success_count": success_count,
                "error_count": error_count,
                "total_latency_ms": total_latency_ms,
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

    def list_all_users(self) -> List[Dict[str, Any]]:
        """모든 사용자 목록 (Admin용)"""
        docs = self.db.collection("users").order_by("created_at", direction=firestore.Query.DESCENDING).stream()

        users = []
        for doc in docs:
            user_data = doc.to_dict()
            # Timestamp 변환
            if isinstance(user_data.get("created_at"), datetime):
                user_data["created_at"] = user_data["created_at"].isoformat()
            if isinstance(user_data.get("last_login"), datetime):
                user_data["last_login"] = user_data["last_login"].isoformat()
            users.append(user_data)

        return users

    def get_all_stats(self) -> List[Dict[str, Any]]:
        """전체 사용자 통계 (Admin용)"""
        docs = self.db.collection("user_stats").order_by("total_calls", direction=firestore.Query.DESCENDING).stream()

        stats = []
        for doc in docs:
            stat_data = doc.to_dict()
            # Timestamp 변환
            if isinstance(stat_data.get("updated_at"), datetime):
                stat_data["updated_at"] = stat_data["updated_at"].isoformat()
            stats.append(stat_data)

        return stats

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
    ):
        """연구 메트릭 기록"""
        self.db.collection("research_metrics").add(
            {
                "user_id": user_id,
                "beta_phase": beta_phase,
                "context_stability_score": context_stability_score,
                "recovery_time_ms": recovery_time_ms,
                "intervention_precision": intervention_precision,
                "user_acceptance_count": user_acceptance_count,
                "user_rejection_count": user_rejection_count,
                "session_id": session_id,
                "recorded_at": firestore.SERVER_TIMESTAMP,
            }
        )

    def get_research_metrics(self, beta_phase: str = None) -> List[Dict[str, Any]]:
        """연구 메트릭 조회 (베타 페이즈별)"""
        query = self.db.collection("research_metrics")

        if beta_phase:
            query = query.where("beta_phase", "==", beta_phase)

        docs = query.order_by("recorded_at", direction=firestore.Query.DESCENDING).stream()

        metrics = []
        for doc in docs:
            metric_data = doc.to_dict()
            # Timestamp 변환
            if isinstance(metric_data.get("recorded_at"), datetime):
                metric_data["recorded_at"] = metric_data["recorded_at"].isoformat()
            metrics.append(metric_data)

        return metrics

    def get_current_beta_phase(self) -> Optional[str]:
        """현재 활성 베타 페이즈 조회"""
        docs = (
            self.db.collection("beta_phase_config")
            .where("is_active", "==", True)
            .limit(1)
            .stream()
        )

        doc_list = list(docs)
        if not doc_list:
            return "closed_beta"

        return doc_list[0].to_dict()["phase_name"]

    def set_beta_phase(self, phase_name: str, max_users: int = None):
        """베타 페이즈 전환"""
        # 기존 활성 페이즈 비활성화
        active_phases = (
            self.db.collection("beta_phase_config")
            .where("is_active", "==", True)
            .stream()
        )

        for phase in active_phases:
            phase.reference.update(
                {
                    "is_active": False,
                    "end_date": firestore.SERVER_TIMESTAMP,
                }
            )

        # 새 페이즈 활성화 또는 생성
        phase_ref = self.db.collection("beta_phase_config").document(phase_name)
        phase_ref.set(
            {
                "phase_name": phase_name,
                "start_date": firestore.SERVER_TIMESTAMP,
                "max_users": max_users,
                "is_active": True,
                "created_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

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
        """오류 로그 기록"""
        self.db.collection("error_logs").add(
            {
                "user_id": user_id,
                "error_type": error_type,
                "tool_name": tool_name,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "context": context,
                "severity": severity,
                "recorded_at": firestore.SERVER_TIMESTAMP,
            }
        )

    def get_error_logs(
        self, limit: int = 100, severity: str = None, error_type: str = None, user_id: int = None
    ) -> List[Dict[str, Any]]:
        """오류 로그 조회"""
        query = self.db.collection("error_logs")

        if severity:
            query = query.where("severity", "==", severity)

        if error_type:
            query = query.where("error_type", "==", error_type)

        if user_id:
            query = query.where("user_id", "==", user_id)

        docs = query.order_by("recorded_at", direction=firestore.Query.DESCENDING).limit(limit).stream()

        logs = []
        for doc in docs:
            log_data = doc.to_dict()
            # Timestamp 변환
            if isinstance(log_data.get("recorded_at"), datetime):
                log_data["recorded_at"] = log_data["recorded_at"].isoformat()
            logs.append(log_data)

        return logs

    def get_error_stats(self) -> Dict[str, Any]:
        """오류 통계 조회"""
        # Firestore는 집계 함수가 제한적이므로 모든 문서를 읽어서 계산
        all_errors = self.db.collection("error_logs").stream()

        total_errors = 0
        by_severity = {}
        by_type = {}
        recent_24h = 0

        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)

        for doc in all_errors:
            error = doc.to_dict()
            total_errors += 1

            # 심각도별 집계
            severity = error.get("severity", "error")
            by_severity[severity] = by_severity.get(severity, 0) + 1

            # 타입별 집계
            error_type = error.get("error_type", "unknown")
            by_type[error_type] = by_type.get(error_type, 0) + 1

            # 최근 24시간
            recorded_at = error.get("recorded_at")
            if isinstance(recorded_at, datetime) and recorded_at >= twenty_four_hours_ago:
                recent_24h += 1

        return {
            "total_errors": total_errors,
            "by_severity": by_severity,
            "by_type": by_type,
            "recent_24h": recent_24h,
        }


# 싱글톤 인스턴스
_db: Optional[Database] = None


def get_db() -> Database:
    """Database 싱글톤 인스턴스 반환"""
    global _db
    if _db is None:
        _db = Database()
    return _db
