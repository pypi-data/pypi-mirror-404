"""
Cortex MCP - Automation Manager
Plan A/B 자동 전환 시스템

Phase 2 업그레이드: Control Theory Hysteresis 적용
- Plan A (자동 모드): 정상 작동 시 자동 처리
- Plan B (반자동 모드): 거부율 30%+ 시 확인 절차 추가
- Hysteresis 로직: 전환 안정성 확보
- 사용자 피드백 추적
- 자동화 성공률 모니터링
"""

import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from config import config

from .control_state import ControlStateManager
from .control_state import PlanMode
from .control_state import UserResponseType

# Research Logger import (Phase 9 integration - 논문 데이터 수집)
try:
    from .research_logger import log_event_sync, get_research_logger, EventType, ResearchEvent
    RESEARCH_LOGGER_AVAILABLE = True
except ImportError:
    RESEARCH_LOGGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """작업 유형"""

    BRANCH_CREATE = "branch_create"
    CONTEXT_LOAD = "context_load"
    CONTEXT_SUGGEST = "context_suggest"
    MEMORY_UPDATE = "memory_update"
    AUTO_COMPRESS = "auto_compress"
    AUTO_SUMMARY = "auto_summary"


class FeedbackType(Enum):
    """피드백 유형"""

    ACCEPTED = "accepted"  # 수락
    REJECTED = "rejected"  # 거부
    MODIFIED = "modified"  # 수정 후 수락
    IGNORED = "ignored"  # 무시


class AutomationManager:
    """자동화 관리자 - Plan A/B 전환 시스템"""

    # 임계값 설정
    REJECTION_THRESHOLD = 0.30  # 거부율 30% 이상이면 Plan B로 전환
    RECOVERY_THRESHOLD = 0.15  # 거부율 15% 이하면 Plan A로 복귀
    MIN_SAMPLES = 10  # 최소 샘플 수 (이하면 Plan A 유지)
    WINDOW_HOURS = 24  # 피드백 분석 윈도우 (시간)

    def __init__(self, project_id: str = "default"):
        self.project_id = project_id
        self.data_dir = config.cortex_home / "automation"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._feedback_file = self.data_dir / f"{project_id}_feedback.json"
        self._settings_file = self.data_dir / f"{project_id}_settings.json"

        # Phase 2: Control Theory Hysteresis 통합
        self.control_state_manager = ControlStateManager(
            project_id=project_id, initial_mode=PlanMode.PLAN_A
        )

        self._load_settings()

    def _load_settings(self):
        """설정 로드"""
        self._settings = {
            "current_mode": PlanMode.PLAN_A.value,
            "mode_changed_at": None,
            "auto_switch_enabled": True,
        }

        if self._settings_file.exists():
            try:
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self._settings.update(saved)

                    # Phase 2: Control State 복원
                    if "control_state" in saved:
                        self.control_state_manager.import_state(saved["control_state"])
            except:
                pass

    def _save_settings(self):
        """설정 저장"""
        # Phase 2: Control State 포함
        settings_with_state = self._settings.copy()
        settings_with_state["control_state"] = self.control_state_manager.export_state()

        with open(self._settings_file, "w", encoding="utf-8") as f:
            json.dump(settings_with_state, f, ensure_ascii=False, indent=2)

    def _load_feedback(self) -> List[Dict]:
        """피드백 데이터 로드"""
        if not self._feedback_file.exists():
            return []

        try:
            with open(self._feedback_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("records", [])
        except:
            return []

    def _save_feedback(self, records: List[Dict]):
        """피드백 데이터 저장"""
        # 최근 1000개만 유지
        records = records[-1000:]

        with open(self._feedback_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "project_id": self.project_id,
                    "records": records,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    @property
    def current_mode(self) -> PlanMode:
        """현재 자동화 모드 (Control State Manager에서 직접 읽기)"""
        return self.control_state_manager.get_current_mode()

    def _map_feedback_to_user_response(self, feedback: str) -> UserResponseType:
        """
        FeedbackType → UserResponseType 매핑

        Args:
            feedback: FeedbackType enum 값 문자열

        Returns:
            UserResponseType
        """
        mapping = {
            FeedbackType.ACCEPTED.value: UserResponseType.ACCEPTED,
            FeedbackType.REJECTED.value: UserResponseType.REJECTED,
            FeedbackType.MODIFIED.value: UserResponseType.MODIFIED,
            FeedbackType.IGNORED.value: UserResponseType.IGNORED,
        }
        return mapping.get(feedback, UserResponseType.IGNORED)

    def record_feedback(
        self,
        action_type: str,
        feedback: str,
        action_id: Optional[str] = None,
        details: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        사용자 피드백 기록

        Args:
            action_type: 작업 유형 (ActionType enum 값)
            feedback: 피드백 유형 (FeedbackType enum 값)
            action_id: 작업 ID (선택)
            details: 추가 상세 정보 (선택)

        Returns:
            기록 결과 및 모드 전환 여부
        """
        records = self._load_feedback()

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_type": action_type,
            "feedback": feedback,
            "action_id": action_id,
            "details": details or {},
        }

        records.append(record)
        self._save_feedback(records)

        # Phase 2: Control State Manager에 상호작용 기록
        user_response = self._map_feedback_to_user_response(feedback)
        response_time_sec = details.get("response_time_sec", 0.0) if details else 0.0

        self.control_state_manager.record_interaction(
            action_type=action_type,
            user_response=user_response,
            response_time_sec=response_time_sec,
            metadata={"action_id": action_id, "details": details},
        )

        # 모드 전환 체크
        mode_switch = self._check_mode_switch()

        logger.info(f"Feedback recorded: {action_type} -> {feedback}")

        # Research Logger integration (Phase 9 - 논문 데이터 수집)
        if RESEARCH_LOGGER_AVAILABLE and log_event_sync and get_research_logger:
            try:
                res_logger = get_research_logger()
                if res_logger.enabled:
                    event = ResearchEvent(
                        event_id=res_logger._generate_event_id(),
                        event_type=EventType.USER_RESPONSE,
                        timestamp=datetime.now().isoformat(),
                        user_hash=res_logger.current_user_hash or "unknown",
                        session_id=res_logger.current_session_id or "unknown",
                        task_id=action_id,
                        context_state={
                            "action_type": action_type,
                            "feedback": feedback,
                            "action_id": action_id,
                            "project_id": self.project_id,
                        },
                        metrics={
                            "mode_switched": mode_switch.get("switched", False),
                            "current_mode": self.current_mode.value,
                            "new_mode": mode_switch.get("new_mode"),
                            "response_time_sec": response_time_sec,
                        },
                    )
                    log_event_sync(event)
            except Exception as log_err:
                pass  # Silent failure

        return {
            "success": True,
            "feedback_recorded": True,
            "current_mode": self.current_mode.value,
            "mode_switched": mode_switch.get("switched", False),
            "new_mode": mode_switch.get("new_mode"),
        }

    def _check_mode_switch(self) -> Dict[str, Any]:
        """
        모드 전환 필요 여부 체크 (Phase 2: Hysteresis 로직 적용)

        Returns:
            전환 결과
        """
        if not self._settings.get("auto_switch_enabled", True):
            return {"switched": False}

        # Phase 2: ControlStateManager를 통한 모드 결정
        current_mode = self.control_state_manager.get_current_mode()
        decided_mode = self.control_state_manager.decide_mode()

        # 모드 전환 발생 여부 확인
        if current_mode != decided_mode:
            # 통계 정보 가져오기
            control_stats = self.control_state_manager.get_statistics()

            # 로그 출력
            if decided_mode == PlanMode.PLAN_B:
                logger.warning(
                    f"Switching to Plan B: reject rates (5:{control_stats['recent_reject_rate_5']:.1%}, "
                    f"10:{control_stats['recent_reject_rate_10']:.1%}), "
                    f"consecutive high reject: {control_stats['consecutive_high_reject']}"
                )
            else:
                logger.info(
                    f"Switching back to Plan A: reject rates (10:{control_stats['recent_reject_rate_10']:.1%}, "
                    f"20:{control_stats['recent_reject_rate_20']:.1%}), "
                    f"consecutive low reject: {control_stats['consecutive_low_reject']}"
                )

            # 설정 업데이트
            self._settings["current_mode"] = decided_mode.value
            self._settings["mode_changed_at"] = datetime.now(timezone.utc).isoformat()
            self._save_settings()

            return {
                "switched": True,
                "previous_mode": current_mode.value,
                "new_mode": decided_mode.value,
                "control_stats": control_stats,
            }

        return {"switched": False}

    def get_feedback_stats(self, window_hours: Optional[int] = None) -> Dict[str, Any]:
        """
        피드백 통계 조회

        Args:
            window_hours: 분석 윈도우 (기본: WINDOW_HOURS)

        Returns:
            통계 정보
        """
        window = window_hours or self.WINDOW_HOURS
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window)
        cutoff_str = cutoff.isoformat()

        records = self._load_feedback()

        # 윈도우 내 기록만 필터링
        recent = [r for r in records if r.get("timestamp", "") >= cutoff_str]

        # 피드백 유형별 카운트
        counts = {
            FeedbackType.ACCEPTED.value: 0,
            FeedbackType.REJECTED.value: 0,
            FeedbackType.MODIFIED.value: 0,
            FeedbackType.IGNORED.value: 0,
        }

        action_counts = {}

        for record in recent:
            feedback = record.get("feedback", "")
            action = record.get("action_type", "unknown")

            if feedback in counts:
                counts[feedback] += 1

            if action not in action_counts:
                action_counts[action] = {"total": 0, "rejected": 0}
            action_counts[action]["total"] += 1
            if feedback == FeedbackType.REJECTED.value:
                action_counts[action]["rejected"] += 1

        total = len(recent)
        rejected = counts[FeedbackType.REJECTED.value]

        # 거부율 계산 (수정된 것도 일부 거부로 간주)
        modified = counts[FeedbackType.MODIFIED.value]
        effective_rejected = rejected + (modified * 0.3)  # 수정은 30% 가중치

        rejection_rate = effective_rejected / total if total > 0 else 0
        success_rate = counts[FeedbackType.ACCEPTED.value] / total if total > 0 else 1

        return {
            "total_in_window": total,
            "window_hours": window,
            "counts": counts,
            "rejection_rate": round(rejection_rate, 4),
            "success_rate": round(success_rate, 4),
            "by_action_type": action_counts,
            "current_mode": self.current_mode.value,
            "thresholds": {
                "rejection": self.REJECTION_THRESHOLD,
                "recovery": self.RECOVERY_THRESHOLD,
                "min_samples": self.MIN_SAMPLES,
            },
        }

    def should_confirm(self, action_type: str) -> Dict[str, Any]:
        """
        특정 작업에 대해 사용자 확인이 필요한지 판단

        Args:
            action_type: 작업 유형

        Returns:
            확인 필요 여부 및 이유
        """
        current = self.current_mode

        # Plan A: 확인 없이 자동 처리
        if current == PlanMode.PLAN_A:
            return {
                "confirm_required": False,
                "mode": current.value,
                "reason": "Plan A: automatic processing",
            }

        # Plan B: 모든 작업에 확인 필요
        stats = self.get_feedback_stats()
        action_stats = stats.get("by_action_type", {}).get(action_type, {})

        return {
            "confirm_required": True,
            "mode": current.value,
            "reason": f"Plan B: confirmation required (rejection rate: {stats.get('rejection_rate', 0):.1%})",
            "action_rejection_rate": (
                action_stats.get("rejected", 0) / action_stats.get("total", 1)
                if action_stats.get("total", 0) > 0
                else 0
            ),
        }

    def set_mode(self, mode: str, disable_auto_switch: bool = False) -> Dict[str, Any]:
        """
        수동으로 모드 설정

        Args:
            mode: 설정할 모드 ('auto' or 'semi_auto')
            disable_auto_switch: 자동 전환 비활성화 여부

        Returns:
            설정 결과
        """
        try:
            new_mode = PlanMode(mode)
        except ValueError:
            return {"success": False, "error": f"Invalid mode: {mode}. Use 'auto' or 'semi_auto'"}

        previous = self.current_mode

        # ControlStateManager 상태 업데이트 (수동 전환)
        self.control_state_manager._transition_to(new_mode)

        # 설정 파일에도 저장
        self._settings["current_mode"] = new_mode.value
        self._settings["mode_changed_at"] = datetime.now(timezone.utc).isoformat()

        if disable_auto_switch:
            self._settings["auto_switch_enabled"] = False

        self._save_settings()

        logger.info(f"Mode manually set: {previous.value} -> {new_mode.value}")

        return {
            "success": True,
            "previous_mode": previous.value,
            "current_mode": new_mode.value,
            "auto_switch_enabled": self._settings.get("auto_switch_enabled", True),
        }

    def enable_auto_switch(self, enabled: bool = True) -> Dict[str, Any]:
        """자동 전환 활성화/비활성화"""
        self._settings["auto_switch_enabled"] = enabled
        self._save_settings()

        return {
            "success": True,
            "auto_switch_enabled": enabled,
            "current_mode": self.current_mode.value,
        }

    def get_status(self) -> Dict[str, Any]:
        """현재 자동화 상태 조회"""
        stats = self.get_feedback_stats()

        return {
            "project_id": self.project_id,
            "current_mode": self.current_mode.value,
            "mode_changed_at": self._settings.get("mode_changed_at"),
            "auto_switch_enabled": self._settings.get("auto_switch_enabled", True),
            "stats": stats,
            "recommendation": self._get_recommendation(stats),
        }

    def _get_recommendation(self, stats: Dict) -> str:
        """현재 상태에 대한 권장 사항"""
        rejection_rate = stats.get("rejection_rate", 0)
        total = stats.get("total_in_window", 0)
        current = self.current_mode

        if total < self.MIN_SAMPLES:
            return "Insufficient data for analysis. Continue using current mode."

        if current == PlanMode.PLAN_A:
            if rejection_rate >= self.REJECTION_THRESHOLD:
                return f"High rejection rate ({rejection_rate:.1%}). Consider switching to Plan B for better user control."
            else:
                return "System performing well in automatic mode."
        else:  # Plan B
            if rejection_rate <= self.RECOVERY_THRESHOLD:
                return f"Low rejection rate ({rejection_rate:.1%}). Safe to switch back to Plan A."
            else:
                return "Continue with confirmation mode until rejection rate improves."

    def get_action_history(
        self, action_type: Optional[str] = None, limit: int = 50
    ) -> Dict[str, Any]:
        """
        작업 히스토리 조회

        Args:
            action_type: 필터링할 작업 유형
            limit: 최대 결과 수

        Returns:
            히스토리 목록
        """
        records = self._load_feedback()

        if action_type:
            records = [r for r in records if r.get("action_type") == action_type]

        # 최신순 정렬
        records = sorted(records, key=lambda x: x.get("timestamp", ""), reverse=True)

        return {
            "records": records[:limit],
            "count": len(records[:limit]),
            "total": len(records),
        }


# 프로젝트별 인스턴스 캐시
_automation_managers: Dict[str, AutomationManager] = {}


def get_automation_manager(project_id: str = "default") -> AutomationManager:
    """AutomationManager 인스턴스 획득 (프로젝트별)"""
    if project_id not in _automation_managers:
        _automation_managers[project_id] = AutomationManager(project_id)
    return _automation_managers[project_id]


# ============================================================================
# MCP Tool Interface Functions (4개)
# memory_manager.py에서 호출하는 모듈 레벨 함수들
# ============================================================================


def get_automation_status(project_id: str) -> Dict[str, Any]:
    """
    자동화 상태 조회 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID

    Returns:
        자동화 상태 (모드, 거부율, 성공률)
    """
    manager = get_automation_manager(project_id)
    return manager.get_status()


def record_automation_feedback(
    project_id: str, action_type: str, feedback: str, action_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    자동화 피드백 기록 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        action_type: 작업 유형 (branch_create, context_load, etc.)
        feedback: 피드백 유형 (accepted, rejected, modified, ignored)
        action_id: 작업 ID (선택)

    Returns:
        피드백 기록 결과
    """
    manager = get_automation_manager(project_id)
    return manager.record_feedback(action_type=action_type, feedback=feedback, action_id=action_id)


def should_confirm_action(project_id: str, action_type: str) -> Dict[str, Any]:
    """
    작업 확인 필요 여부 판단 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        action_type: 작업 유형

    Returns:
        확인 필요 여부 (Plan A: false, Plan B: true)
    """
    manager = get_automation_manager(project_id)
    return manager.should_confirm(action_type)


def set_automation_mode(
    project_id: str, mode: str, disable_auto_switch: bool = False
) -> Dict[str, Any]:
    """
    자동화 모드 수동 설정 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        mode: 설정할 모드 (auto/semi_auto)
        disable_auto_switch: 자동 전환 비활성화

    Returns:
        모드 설정 결과
    """
    manager = get_automation_manager(project_id)
    return manager.set_mode(mode=mode, disable_auto_switch=disable_auto_switch)
