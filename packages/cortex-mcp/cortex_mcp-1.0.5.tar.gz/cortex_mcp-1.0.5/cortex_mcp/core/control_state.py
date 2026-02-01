"""
Control State Manager
Cortex Phase 2: Track 1 - Product Engineering

설계 원칙 (Control Theory 적용):
1. Hysteresis (이력 현상): 전환 안정성 확보
2. State feedback: 거부율 기반 상태 변수 관리
3. Threshold with margin: Plan A/B 전환 임계치 분리

목적: 과잉 개입 방지, 사용자 경험 최적화
이론적 근거: Control Theory (Hysteresis, State Feedback)
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Deque, Dict, List, Optional

from config import config


class PlanMode(Enum):
    """Plan 모드"""

    PLAN_A = "auto"  # 자동 모드
    PLAN_B = "semi_auto"  # 반자동 모드 (확인 절차 추가)


class UserResponseType(Enum):
    """사용자 반응 타입"""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"
    IGNORED = "ignored"


@dataclass
class InteractionRecord:
    """사용자 상호작용 기록"""

    timestamp: str
    action_type: str  # "branch_create", "context_switch", "memory_update"
    user_response: UserResponseType
    response_time_sec: float
    metadata: Optional[Dict] = None


@dataclass
class ControlState:
    """
    Control 상태 변수

    Hysteresis 로직을 위한 상태 추적
    """

    # 현재 모드
    current_mode: PlanMode = PlanMode.PLAN_A

    # 거부율 이력 (최근 N회)
    recent_interactions: Deque[InteractionRecord] = field(default_factory=lambda: deque(maxlen=20))

    # 연속 high/low reject 카운터
    consecutive_high_reject: int = 0
    consecutive_low_reject: int = 0

    # 전환 이력
    mode_transitions: List[Dict] = field(default_factory=list)

    # 마지막 전환 시간
    last_transition: Optional[str] = None

    # 통계
    total_interactions: int = 0
    total_accepted: int = 0
    total_rejected: int = 0


class ControlStateManager:
    """
    Control Theory 기반 Plan A/B 관리자

    Hysteresis 로직:
    - Plan A → Plan B: 거부율 30%+ (3회 연속)
    - Plan B → Plan A: 거부율 15%- (5회 연속)

    과잉 전환 방지를 위한 최소 전환 간격: 10분
    """

    # Hysteresis Thresholds
    PLAN_A_TO_B_REJECT_RATE_5 = 0.30  # 최근 5회 거부율 30%
    PLAN_A_TO_B_REJECT_RATE_10 = 0.25  # 최근 10회 거부율 25%
    PLAN_A_TO_B_CONSECUTIVE = 3  # 3회 연속 high reject

    PLAN_B_TO_A_REJECT_RATE_10 = 0.15  # 최근 10회 거부율 15%
    PLAN_B_TO_A_REJECT_RATE_20 = 0.20  # 최근 20회 거부율 20%
    PLAN_B_TO_A_CONSECUTIVE = 5  # 5회 연속 low reject

    MIN_TRANSITION_INTERVAL_SEC = 600  # 최소 전환 간격 10분

    def __init__(self, project_id: str, initial_mode: PlanMode = PlanMode.PLAN_A):
        """
        Control State Manager 초기화

        Args:
            project_id: 프로젝트 식별자
            initial_mode: 초기 모드 (기본값: PLAN_A)
        """
        self.project_id = project_id
        self.state = ControlState(current_mode=initial_mode)

    def record_interaction(
        self,
        action_type: str,
        user_response: UserResponseType,
        response_time_sec: float,
        metadata: Optional[Dict] = None,
    ):
        """
        사용자 상호작용 기록

        Args:
            action_type: 행동 타입
            user_response: 사용자 반응
            response_time_sec: 응답 시간 (초)
            metadata: 추가 메타데이터
        """
        record = InteractionRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type=action_type,
            user_response=user_response,
            response_time_sec=response_time_sec,
            metadata=metadata,
        )

        self.state.recent_interactions.append(record)
        self.state.total_interactions += 1

        if user_response == UserResponseType.ACCEPTED:
            self.state.total_accepted += 1
        elif user_response == UserResponseType.REJECTED:
            self.state.total_rejected += 1

    def decide_mode(self) -> PlanMode:
        """
        현재 상태 기반 Plan Mode 결정

        Control law with hysteresis:
        - Plan A → Plan B: 거부율 높음 (3회 연속 확인)
        - Plan B → Plan A: 거부율 낮음 (5회 연속 확인)

        Returns:
            결정된 Plan Mode
        """
        # 최소 전환 간격 체크
        if not self._can_transition():
            return self.state.current_mode

        # 거부율 계산
        reject_rate_5 = self._calculate_reject_rate(lookback=5)
        reject_rate_10 = self._calculate_reject_rate(lookback=10)
        reject_rate_20 = self._calculate_reject_rate(lookback=20)

        current_mode = self.state.current_mode

        # Plan A → Plan B 전환 조건
        if current_mode == PlanMode.PLAN_A:
            if (
                reject_rate_5 > self.PLAN_A_TO_B_REJECT_RATE_5
                and reject_rate_10 > self.PLAN_A_TO_B_REJECT_RATE_10
            ):

                self.state.consecutive_high_reject += 1
                self.state.consecutive_low_reject = 0

                if self.state.consecutive_high_reject >= self.PLAN_A_TO_B_CONSECUTIVE:
                    self._transition_to(PlanMode.PLAN_B)
                    return PlanMode.PLAN_B
            else:
                # 조건 불만족 시 카운터 리셋
                self.state.consecutive_high_reject = 0

        # Plan B → Plan A 복귀 조건
        elif current_mode == PlanMode.PLAN_B:
            if (
                reject_rate_10 < self.PLAN_B_TO_A_REJECT_RATE_10
                and reject_rate_20 < self.PLAN_B_TO_A_REJECT_RATE_20
            ):

                self.state.consecutive_low_reject += 1
                self.state.consecutive_high_reject = 0

                if self.state.consecutive_low_reject >= self.PLAN_B_TO_A_CONSECUTIVE:
                    self._transition_to(PlanMode.PLAN_A)
                    return PlanMode.PLAN_A
            else:
                # 조건 불만족 시 카운터 리셋
                self.state.consecutive_low_reject = 0

        return current_mode

    def _calculate_reject_rate(self, lookback: int) -> float:
        """
        최근 N회 거부율 계산

        Args:
            lookback: 조회할 과거 상호작용 수

        Returns:
            거부율 (0.0 ~ 1.0)
        """
        if not self.state.recent_interactions:
            return 0.0

        recent = list(self.state.recent_interactions)[-lookback:]

        if not recent:
            return 0.0

        reject_count = sum(
            1
            for record in recent
            if record.user_response in [UserResponseType.REJECTED, UserResponseType.MODIFIED]
        )

        return reject_count / len(recent)

    def _can_transition(self) -> bool:
        """
        전환 가능 여부 확인 (최소 간격 체크)

        Returns:
            전환 가능 여부
        """
        if not self.state.last_transition:
            return True

        last_transition_time = datetime.fromisoformat(self.state.last_transition.replace("Z", "+00:00"))
        if last_transition_time.tzinfo is None:
            last_transition_time = last_transition_time.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - last_transition_time).total_seconds()

        return elapsed >= self.MIN_TRANSITION_INTERVAL_SEC

    def _transition_to(self, new_mode: PlanMode):
        """
        모드 전환 수행

        Args:
            new_mode: 새로운 모드
        """
        old_mode = self.state.current_mode

        # 전환 이력 기록
        transition_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_mode": old_mode.value,
            "to_mode": new_mode.value,
            "reject_rate_5": self._calculate_reject_rate(5),
            "reject_rate_10": self._calculate_reject_rate(10),
            "reject_rate_20": self._calculate_reject_rate(20),
            "consecutive_high_reject": self.state.consecutive_high_reject,
            "consecutive_low_reject": self.state.consecutive_low_reject,
        }

        self.state.mode_transitions.append(transition_record)

        # 상태 업데이트
        self.state.current_mode = new_mode
        self.state.last_transition = transition_record["timestamp"]

        # 카운터 리셋
        self.state.consecutive_high_reject = 0
        self.state.consecutive_low_reject = 0

    def get_current_mode(self) -> PlanMode:
        """현재 Plan Mode 반환"""
        return self.state.current_mode

    def get_statistics(self) -> Dict:
        """
        통계 정보 반환 (연구용)

        Returns:
            통계 딕셔너리
        """
        return {
            "current_mode": self.state.current_mode.value,
            "total_interactions": self.state.total_interactions,
            "total_accepted": self.state.total_accepted,
            "total_rejected": self.state.total_rejected,
            "overall_accept_rate": (
                self.state.total_accepted / max(1, self.state.total_interactions)
            ),
            "recent_reject_rate_5": self._calculate_reject_rate(5),
            "recent_reject_rate_10": self._calculate_reject_rate(10),
            "recent_reject_rate_20": self._calculate_reject_rate(20),
            "consecutive_high_reject": self.state.consecutive_high_reject,
            "consecutive_low_reject": self.state.consecutive_low_reject,
            "total_transitions": len(self.state.mode_transitions),
            "last_transition": self.state.last_transition,
        }

    def export_state(self) -> Dict:
        """
        상태 내보내기 (영속성)

        Returns:
            직렬화 가능한 상태 딕셔너리
        """
        return {
            "current_mode": self.state.current_mode.value,
            "recent_interactions": [
                {
                    "timestamp": r.timestamp,
                    "action_type": r.action_type,
                    "user_response": r.user_response.value,
                    "response_time_sec": r.response_time_sec,
                    "metadata": r.metadata,
                }
                for r in self.state.recent_interactions
            ],
            "consecutive_high_reject": self.state.consecutive_high_reject,
            "consecutive_low_reject": self.state.consecutive_low_reject,
            "mode_transitions": self.state.mode_transitions,
            "last_transition": self.state.last_transition,
            "total_interactions": self.state.total_interactions,
            "total_accepted": self.state.total_accepted,
            "total_rejected": self.state.total_rejected,
        }

    def import_state(self, state_dict: Dict):
        """
        상태 불러오기 (영속성)

        Args:
            state_dict: 내보낸 상태 딕셔너리
        """
        self.state.current_mode = PlanMode(state_dict["current_mode"])
        self.state.recent_interactions = deque(
            [
                InteractionRecord(
                    timestamp=r["timestamp"],
                    action_type=r["action_type"],
                    user_response=UserResponseType(r["user_response"]),
                    response_time_sec=r["response_time_sec"],
                    metadata=r.get("metadata"),
                )
                for r in state_dict["recent_interactions"]
            ],
            maxlen=20,
        )
        self.state.consecutive_high_reject = state_dict["consecutive_high_reject"]
        self.state.consecutive_low_reject = state_dict["consecutive_low_reject"]
        self.state.mode_transitions = state_dict["mode_transitions"]
        self.state.last_transition = state_dict.get("last_transition")
        self.state.total_interactions = state_dict["total_interactions"]
        self.state.total_accepted = state_dict["total_accepted"]
        self.state.total_rejected = state_dict["total_rejected"]
