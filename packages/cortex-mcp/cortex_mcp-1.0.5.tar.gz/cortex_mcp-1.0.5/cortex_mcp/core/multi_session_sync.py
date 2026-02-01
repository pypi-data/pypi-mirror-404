"""
Cortex MCP - Multi-Session Parallel Development Engine (v1.0)
개인 개발자가 여러 터미널로 병렬 개발하며 맥락을 자동 머지

Pro 이상 전용 기능:
- 여러 Claude Code 세션 동시 실행
- 각 세션의 맥락 자동 감지 및 병합
- 충돌 감지 및 자동 해결
- 실시간 세션 모니터링

사용 시나리오:
Terminal 1: 인증 시스템 개발 (Claude Code)
Terminal 2: API 엔드포인트 개발 (Claude Code)
Terminal 3: 프론트엔드 개발 (Claude Code)
→ 모든 맥락이 자동으로 머지되어 전체 프로젝트 맥락 유지

핵심 기능:
1. 세션 자동 감지 (PID 기반)
2. 실시간 맥락 동기화
3. 자동 충돌 해결 (CONCATENATE 전략)
4. 세션 간 링크 생성
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.append(str(Path(__file__).parent.parent))
from config import config


class SessionStatus(Enum):
    """세션 상태"""

    ACTIVE = "active"  # 활성 중
    IDLE = "idle"  # 유휴 (30분 이상 미활동)
    CLOSED = "closed"  # 종료됨
    SYNCING = "syncing"  # 동기화 중


@dataclass
class SessionInfo:
    """세션 정보"""

    session_id: str  # 세션 고유 ID (PID_timestamp)
    project_id: str  # 프로젝트 ID
    branch_id: str  # 작업 중인 브랜치 ID
    pid: int  # 프로세스 ID
    status: SessionStatus  # 세션 상태
    created_at: str  # 생성 시간
    last_activity: str  # 마지막 활동 시간
    contexts_created: List[str] = field(default_factory=list)  # 생성한 맥락 목록
    enable_auto_sync: bool = True  # 자동 동기화 활성화 (새 브랜치는 False)
    merge_count: int = 0  # 머지 횟수

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "branch_id": self.branch_id,
            "pid": self.pid,
            "status": self.status.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "contexts_created": self.contexts_created,
            "merge_count": self.merge_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionInfo":
        return cls(
            session_id=data["session_id"],
            project_id=data["project_id"],
            branch_id=data["branch_id"],
            pid=data["pid"],
            status=SessionStatus(data["status"]),
            created_at=data["created_at"],
            last_activity=data["last_activity"],
            contexts_created=data.get("contexts_created", []),
            merge_count=data.get("merge_count", 0),
        )


class MultiSessionManager:
    """
    멀티세션 병렬 개발 관리자

    여러 터미널에서 동시에 작업해도 맥락을 자동으로 머지합니다.
    Pro 이상 전용 기능입니다.
    """

    def __init__(self, project_id: str, enable_auto_sync: bool = True):
        self.project_id = project_id
        self.enable_auto_sync = enable_auto_sync

        # 세션 디렉토리
        self.sessions_dir = config.base_dir / "sessions" / project_id
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # 현재 세션 정보
        self.current_session: Optional[SessionInfo] = None
        self.session_file: Optional[Path] = None

        # 자동 동기화 설정
        self.sync_interval = 30  # 초 (30초마다 동기화)
        self.last_sync_time = 0

        # TeamContextMerger 재사용
        from .team_merge import MergeStrategy, TeamContextMerger

        self.merger = TeamContextMerger(project_id)
        self.merge_strategy = MergeStrategy.INCREMENTAL  # 병렬 작업은 INCREMENTAL (새 내용만 추가)

    def create_session(self, branch_id: str, enable_auto_sync: bool = True) -> SessionInfo:
        """
        새 세션 생성

        Args:
            branch_id: 작업할 브랜치 ID
            enable_auto_sync: 자동 동기화 활성화 (새 브랜치는 False)

        Returns:
            생성된 세션 정보
        """
        # 세션 ID 생성 (PID + timestamp)
        pid = os.getpid()
        timestamp = int(time.time() * 1000)
        session_id = f"session_{pid}_{timestamp}"

        # 세션 정보 생성
        now = datetime.now(timezone.utc).isoformat()
        session = SessionInfo(
            session_id=session_id,
            project_id=self.project_id,
            branch_id=branch_id,
            pid=pid,
            status=SessionStatus.ACTIVE,
            created_at=now,
            last_activity=now,
            enable_auto_sync=enable_auto_sync,
        )

        # 세션 파일 저장
        self.session_file = self.sessions_dir / f"{session_id}.json"
        self._save_session(session)

        self.current_session = session
        return session

    def get_current_session(self) -> Optional[SessionInfo]:
        """현재 세션 정보 반환"""
        if self.current_session:
            # 세션 파일에서 최신 정보 로드
            if self.session_file and self.session_file.exists():
                data = json.loads(self.session_file.read_text(encoding="utf-8"))
                self.current_session = SessionInfo.from_dict(data)
        return self.current_session

    def update_session_activity(self, context_id: Optional[str] = None):
        """
        세션 활동 업데이트

        Args:
            context_id: 생성한 맥락 ID (선택)
        """
        if not self.current_session:
            return

        self.current_session.last_activity = datetime.now(timezone.utc).isoformat()
        self.current_session.status = SessionStatus.ACTIVE

        if context_id and context_id not in self.current_session.contexts_created:
            self.current_session.contexts_created.append(context_id)

        self._save_session(self.current_session)

    def get_active_sessions(self, exclude_current: bool = True) -> List[SessionInfo]:
        """
        활성 세션 목록 조회

        Args:
            exclude_current: 현재 세션 제외 여부

        Returns:
            활성 세션 목록
        """
        sessions = []
        current_time = datetime.now(timezone.utc)
        idle_threshold = timedelta(minutes=30)

        for session_file in self.sessions_dir.glob("session_*.json"):
            try:
                data = json.loads(session_file.read_text(encoding="utf-8"))
                session = SessionInfo.from_dict(data)

                # 현재 세션 제외
                if (
                    exclude_current
                    and self.current_session
                    and session.session_id == self.current_session.session_id
                ):
                    continue

                # 프로세스가 살아있는지 확인
                if not self._is_process_alive(session.pid):
                    session.status = SessionStatus.CLOSED
                    self._save_session_to_file(session, session_file)
                    continue

                # 유휴 상태 확인
                last_activity = datetime.fromisoformat(session.last_activity.replace("Z", "+00:00"))
                if current_time - last_activity > idle_threshold:
                    session.status = SessionStatus.IDLE
                    self._save_session_to_file(session, session_file)

                # 활성 또는 유휴 세션만 포함
                if session.status in [SessionStatus.ACTIVE, SessionStatus.IDLE]:
                    sessions.append(session)

            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        return sessions

    def sync_with_other_sessions(self, force: bool = False) -> Dict[str, Any]:
        """
        다른 활성 세션과 맥락 동기화

        Args:
            force: 강제 동기화 (시간 간격 무시)

        Returns:
            동기화 결과
        """
        # 자동 동기화 비활성화 시
        if not self.enable_auto_sync and not force:
            return {"success": False, "message": "Auto-sync disabled"}

        # 현재 세션 없으면 불가
        if not self.current_session:
            return {"success": False, "message": "No active session"}

        # 동기화 간격 체크
        current_time = time.time()
        if not force and (current_time - self.last_sync_time) < self.sync_interval:
            return {"success": False, "message": "Sync interval not reached"}

        # 다른 활성 세션 조회
        other_sessions = self.get_active_sessions(exclude_current=True)

        if not other_sessions:
            self.last_sync_time = current_time
            return {"success": True, "message": "No other sessions to sync", "merged_count": 0}

        # 세션 상태 업데이트
        if self.current_session:
            self.current_session.status = SessionStatus.SYNCING
            self._save_session(self.current_session)

        # 각 세션과 맥락 병합
        merge_results = []
        for session in other_sessions:
            try:
                result = self.merger.merge_team_context(
                    source_branch=session.branch_id,
                    target_branch=self.current_session.branch_id,
                    strategy=self.merge_strategy,
                    auto_resolve=True,
                )
                merge_results.append(
                    {
                        "session_id": session.session_id,
                        "branch_id": session.branch_id,
                        "success": result.success,
                        "conflicts": len(result.conflicts),
                    }
                )

                if result.success and self.current_session:
                    self.current_session.merge_count += 1

            except Exception as e:
                merge_results.append(
                    {
                        "session_id": session.session_id,
                        "branch_id": session.branch_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        # 세션 상태 복원
        if self.current_session:
            self.current_session.status = SessionStatus.ACTIVE
            self._save_session(self.current_session)

        self.last_sync_time = current_time

        return {
            "success": True,
            "message": f"Synced with {len(other_sessions)} sessions",
            "merged_count": len([r for r in merge_results if r["success"]]),
            "results": merge_results,
        }

    def auto_sync_on_activity(self, context_id: Optional[str] = None):
        """
        활동 시 자동 동기화 트리거 (조건부)

        update_memory 호출 시 자동으로 호출됩니다.

        조건:
        - 세션의 enable_auto_sync가 True
        - 최소 3개 컨텍스트 이상
        - 마지막 sync 이후 30초 이상 경과

        Args:
            context_id: 생성한 맥락 ID
        """
        # 세션 활동 업데이트
        self.update_session_activity(context_id)

        # 자동 동기화 조건 확인
        if not self.enable_auto_sync:
            return

        # 현재 세션의 enable_auto_sync 확인
        if self.current_session and not self.current_session.enable_auto_sync:
            return

        # 최소 컨텍스트 수 확인 (3개 이상)
        if self.current_session and len(self.current_session.contexts_created) < 3:
            return

        # 자동 동기화 시도
        self.sync_with_other_sessions(force=False)

    def close_session(self):
        """세션 종료 및 정리"""
        if not self.current_session:
            return

        # 최종 동기화
        self.sync_with_other_sessions(force=True)

        # 세션 상태 업데이트
        self.current_session.status = SessionStatus.CLOSED
        self._save_session(self.current_session)

        # 오래된 세션 파일 정리 (7일 이상)
        self._cleanup_old_sessions(days=7)

    def get_session_statistics(self) -> Dict[str, Any]:
        """세션 통계 조회"""
        all_sessions = []
        for session_file in self.sessions_dir.glob("session_*.json"):
            try:
                data = json.loads(session_file.read_text(encoding="utf-8"))
                all_sessions.append(SessionInfo.from_dict(data))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        active_count = len([s for s in all_sessions if s.status == SessionStatus.ACTIVE])
        idle_count = len([s for s in all_sessions if s.status == SessionStatus.IDLE])
        closed_count = len([s for s in all_sessions if s.status == SessionStatus.CLOSED])

        total_merges = sum(s.merge_count for s in all_sessions)

        return {
            "project_id": self.project_id,
            "total_sessions": len(all_sessions),
            "active_sessions": active_count,
            "idle_sessions": idle_count,
            "closed_sessions": closed_count,
            "total_merges": total_merges,
            "current_session": self.current_session.to_dict() if self.current_session else None,
        }

    # ==================== Private Methods ====================

    def _save_session(self, session: SessionInfo):
        """세션 정보 저장"""
        if not self.session_file:
            return

        self.session_file.write_text(
            json.dumps(session.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _save_session_to_file(self, session: SessionInfo, file_path: Path):
        """세션 정보를 특정 파일에 저장"""
        file_path.write_text(
            json.dumps(session.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _is_process_alive(self, pid: int) -> bool:
        """프로세스가 살아있는지 확인"""
        try:
            # Unix/Linux/Mac
            os.kill(pid, 0)
            return True
        except OSError:
            return False
        except Exception:
            # Windows는 다른 방식으로 확인 필요
            import psutil

            try:
                return psutil.pid_exists(pid)
            except Exception:
                return False

    def _cleanup_old_sessions(self, days: int = 7):
        """오래된 세션 파일 정리"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        for session_file in self.sessions_dir.glob("session_*.json"):
            try:
                data = json.loads(session_file.read_text(encoding="utf-8"))
                created = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

                if created < cutoff:
                    session_file.unlink()

            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                continue


def get_multi_session_manager(
    project_id: str, enable_auto_sync: bool = True
) -> MultiSessionManager:
    """프로젝트별 MultiSessionManager 인스턴스 반환"""
    return MultiSessionManager(project_id=project_id, enable_auto_sync=enable_auto_sync)
