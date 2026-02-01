"""
Cortex P4: 작업 사전 승인 시스템

무단 코드 수정을 방지하고 Zero-Trust 원칙을 강화하는 승인 시스템입니다.

핵심 기능:
- 파일 수정 전 사용자 승인 요청
- 승인 이력 기록 및 추적
- 거부율 기반 Plan A/B 자동 전환
- automation_manager와 연동

작동 방식:
- Plan A (자동 모드): 파일 수정 후 사용자에게 보고 (사후 확인)
- Plan B (승인 모드): 파일 수정 전 사용자 승인 받기 (사전 확인)
- 거부율 30%+ 시 자동으로 Plan B로 전환
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


# ============================================================
# P4 승인 시스템 상수
# ============================================================
APPROVAL_HISTORY_FILE = "~/.cortex/approval_history.json"
REJECTION_THRESHOLD = 0.30  # 30% 거부율 시 Plan B 전환
APPROVAL_WINDOW_DAYS = 7  # 최근 7일 이력만 고려


class ApprovalManager:
    """
    작업 사전 승인 관리자

    Plan A/B 모드에 따라 파일 수정 전후 승인을 처리합니다.
    """

    def __init__(self, project_id: str):
        """
        초기화

        Args:
            project_id: 프로젝트 고유 식별자
        """
        self.project_id = project_id
        self.history_file = Path(APPROVAL_HISTORY_FILE).expanduser()
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # 승인 이력 로드
        self._load_history()

    def _load_history(self) -> None:
        """승인 이력 파일 로드"""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.error(f"[APPROVAL] Failed to load history: {e}")
                self.history = {}
        else:
            self.history = {}

        # 프로젝트별 이력 초기화
        if self.project_id not in self.history:
            self.history[self.project_id] = {
                "approvals": [],
                "rejection_rate": 0.0,
                "last_mode_switch": None,
            }

    def _save_history(self) -> None:
        """승인 이력 파일 저장"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[APPROVAL] Failed to save history: {e}")

    def request_approval(
        self,
        action_type: str,
        file_path: str,
        description: str,
        is_plan_b: bool = False,
    ) -> Dict[str, Any]:
        """
        파일 수정 승인 요청

        Args:
            action_type: 작업 유형 (Edit, Write, Delete)
            file_path: 대상 파일 경로
            description: 작업 설명
            is_plan_b: Plan B 모드 여부 (True면 사전 승인, False면 사후 보고)

        Returns:
            승인 결과 딕셔너리
            {
                "approved": bool,  # 승인 여부
                "mode": str,  # "pre-approval" | "post-report"
                "message": str,  # 사용자 메시지
                "approval_id": str  # 승인 기록 ID
            }
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        approval_id = f"{int(time.time()*1000)}_{self.project_id}"

        if is_plan_b:
            # Plan B: 사전 승인 모드
            logger.info(
                f"[APPROVAL_PLAN_B] 파일 수정 승인 요청: {file_path} ({action_type})"
            )

            # 사용자에게 승인 요청 메시지 생성
            message = f"""
[Cortex 작업 승인 요청]

파일: {file_path}
작업: {action_type}
설명: {description}

이 작업을 진행하시겠습니까? (Y/N)
"""

            # 실제 구현에서는 MCP 도구로 사용자 입력을 받아야 함
            # 여기서는 시스템 메시지만 생성
            return {
                "approved": None,  # 사용자 응답 대기
                "mode": "pre-approval",
                "message": message,
                "approval_id": approval_id,
                "action_type": action_type,
                "file_path": file_path,
                "description": description,
                "timestamp": timestamp,
            }

        else:
            # Plan A: 사후 보고 모드
            logger.info(
                f"[APPROVAL_PLAN_A] 파일 수정 완료 보고: {file_path} ({action_type})"
            )

            # 자동 승인 (사후 보고)
            message = f"""
[Cortex 작업 보고]

파일: {file_path}
작업: {action_type}
설명: {description}

작업이 완료되었습니다. 조정이 필요하면 알려주세요.
"""

            # 승인 기록 저장
            self._record_approval(
                approval_id=approval_id,
                action_type=action_type,
                file_path=file_path,
                description=description,
                approved=True,
                mode="post-report",
                timestamp=timestamp,
            )

            return {
                "approved": True,
                "mode": "post-report",
                "message": message,
                "approval_id": approval_id,
            }

    def record_user_response(
        self, approval_id: str, approved: bool, feedback: Optional[str] = None
    ) -> None:
        """
        사용자 응답 기록

        Args:
            approval_id: 승인 요청 ID
            approved: 승인 여부
            feedback: 거부 사유 (선택)
        """
        # 승인 이력 업데이트
        for approval in self.history[self.project_id]["approvals"]:
            if approval["approval_id"] == approval_id:
                approval["approved"] = approved
                approval["feedback"] = feedback
                approval["response_time"] = datetime.now(timezone.utc).isoformat()
                break

        # 거부율 재계산
        self._update_rejection_rate()

        # 이력 저장
        self._save_history()

        logger.info(
            f"[APPROVAL] User response recorded: {approval_id} -> {'Approved' if approved else 'Rejected'}"
        )

    def _record_approval(
        self,
        approval_id: str,
        action_type: str,
        file_path: str,
        description: str,
        approved: bool,
        mode: str,
        timestamp: str,
    ) -> None:
        """
        승인 기록 저장 (내부 메서드)

        Args:
            approval_id: 승인 ID
            action_type: 작업 유형
            file_path: 파일 경로
            description: 작업 설명
            approved: 승인 여부
            mode: 모드 (pre-approval | post-report)
            timestamp: 타임스탬프
        """
        approval_record = {
            "approval_id": approval_id,
            "action_type": action_type,
            "file_path": file_path,
            "description": description,
            "approved": approved,
            "mode": mode,
            "timestamp": timestamp,
            "feedback": None,
            "response_time": None,
        }

        self.history[self.project_id]["approvals"].append(approval_record)
        self._save_history()

    def _update_rejection_rate(self) -> None:
        """거부율 계산 및 업데이트"""
        # 최근 7일 이력만 고려
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=APPROVAL_WINDOW_DAYS)
        recent_approvals = []
        for a in self.history[self.project_id]["approvals"]:
            if a["approved"] is None:
                continue
            ts = datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts > cutoff_date:
                recent_approvals.append(a)

        if not recent_approvals:
            self.history[self.project_id]["rejection_rate"] = 0.0
            return

        rejected_count = sum(1 for a in recent_approvals if not a["approved"])
        total_count = len(recent_approvals)

        rejection_rate = rejected_count / total_count
        self.history[self.project_id]["rejection_rate"] = rejection_rate

        logger.info(
            f"[APPROVAL] Rejection rate updated: {rejection_rate:.2%} ({rejected_count}/{total_count})"
        )

    def should_switch_to_plan_b(self) -> bool:
        """
        Plan B로 전환 여부 판단

        Returns:
            True면 Plan B로 전환 필요
        """
        rejection_rate = self.history[self.project_id]["rejection_rate"]
        should_switch = rejection_rate >= REJECTION_THRESHOLD

        if should_switch:
            logger.warning(
                f"[APPROVAL] High rejection rate detected: {rejection_rate:.2%} >= {REJECTION_THRESHOLD:.0%}"
            )

        return should_switch

    def get_rejection_rate(self) -> float:
        """
        현재 거부율 반환

        Returns:
            거부율 (0.0 ~ 1.0)
        """
        return self.history[self.project_id]["rejection_rate"]

    def get_approval_stats(self) -> Dict[str, Any]:
        """
        승인 통계 반환

        Returns:
            통계 딕셔너리
            {
                "total_approvals": int,
                "recent_approvals": int,
                "rejection_rate": float,
                "last_mode_switch": str | None
            }
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=APPROVAL_WINDOW_DAYS)
        recent_approvals = []
        for a in self.history[self.project_id]["approvals"]:
            ts = datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts > cutoff_date:
                recent_approvals.append(a)

        return {
            "total_approvals": len(self.history[self.project_id]["approvals"]),
            "recent_approvals": len(recent_approvals),
            "rejection_rate": self.history[self.project_id]["rejection_rate"],
            "last_mode_switch": self.history[self.project_id]["last_mode_switch"],
        }


# ============================================================
# 전역 인스턴스 생성 함수
# ============================================================
def get_approval_manager(project_id: str) -> ApprovalManager:
    """
    ApprovalManager 인스턴스 반환

    Args:
        project_id: 프로젝트 ID

    Returns:
        ApprovalManager 인스턴스
    """
    return ApprovalManager(project_id=project_id)
