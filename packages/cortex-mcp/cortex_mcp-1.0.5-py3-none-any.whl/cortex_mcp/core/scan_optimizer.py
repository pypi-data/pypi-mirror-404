"""
Scan Optimizer - Expected Loss 기반 스캔 전략

Cortex Phase 6: Expected Loss Scan Strategy
초기 컨텍스트 스캔 시 최적의 모드(FULL/LIGHT/NONE)를 Expected Loss 계산을 통해 추천합니다.

핵심 기능:
- Expected Loss 계산 (Cost + Penalty)
- 파일 중요도 스코어링
- 변경 가능성 기반 스캔 순서 최적화
- FULL 스캔 정당성 로깅
"""

import fnmatch
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .alpha_logger import AlphaLogger, LogModule


class ScanMode(Enum):
    """스캔 모드"""

    FULL = "FULL"
    LIGHT = "LIGHT"
    NONE = "NONE"


class FileImportance(Enum):
    """파일 중요도"""

    CRITICAL = "critical"  # README, setup.py, main.py
    HIGH = "high"  # 진입점, 설정 파일
    MEDIUM = "medium"  # 핵심 비즈니스 로직
    LOW = "low"  # 테스트, 문서


class ScanOptimizer:
    """
    Expected Loss 기반 스캔 최적화

    초기 컨텍스트 스캔 시 프로젝트 크기와 복잡도를 고려하여
    최적의 스캔 모드를 추천합니다.
    """

    # Expected Loss 계산 상수
    MISS_PENALTY = 1000  # 놓친 파일당 페널티 (토큰)

    # 스캔 모드별 파라미터
    MODE_PARAMS = {
        ScanMode.FULL: {"cost_multiplier": 10, "miss_rate": 0.05},
        ScanMode.LIGHT: {"cost_multiplier": 1, "miss_rate": 0.20},
        ScanMode.NONE: {"cost_multiplier": 0, "miss_rate": 1.00},
    }

    # 파일 중요도 패턴
    IMPORTANCE_PATTERNS = {
        FileImportance.CRITICAL: [
            "README.md",
            "README.txt",
            "README",
            "setup.py",
            "pyproject.toml",
            "requirements.txt",
            "main.py",
            "__main__.py",
            "app.py",
            "index.js",
            "index.ts",
        ],
        FileImportance.HIGH: [
            "config.py",
            "settings.py",
            ".env.example",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "Dockerfile",
            "docker-compose.yml",
        ],
        FileImportance.MEDIUM: ["*.py", "*.js", "*.ts", "*.go", "*.rs", "*.java"],
        FileImportance.LOW: [
            "test_*.py",
            "*_test.py",
            "*.test.js",
            "*.spec.ts",
            "*.md",
            "*.txt",
            "LICENSE",
        ],
    }

    def __init__(self, project_id: str):
        """
        Scan Optimizer 초기화

        Args:
            project_id: 프로젝트 식별자
        """
        self.project_id = project_id
        self.logger = AlphaLogger()

    def compute_expected_loss(
        self, scan_mode: ScanMode, project_size: int, complexity: float
    ) -> float:
        """
        Expected Loss 계산

        Formula:
            L(mode) = Cost(mode) + Penalty(miss_rate | mode)

        Args:
            scan_mode: 스캔 모드 (FULL/LIGHT/NONE)
            project_size: 프로젝트 파일 수
            complexity: 프로젝트 복잡도 (1.0 ~ 5.0)

        Returns:
            Expected Loss 값 (토큰 단위)
        """
        params = self.MODE_PARAMS[scan_mode]

        # Cost: 스캔에 소요되는 토큰 비용
        cost_tokens = project_size * params["cost_multiplier"]

        # Penalty: 놓친 파일로 인한 미래 비용
        miss_rate = params["miss_rate"]
        penalty = miss_rate * project_size * self.MISS_PENALTY * complexity

        expected_loss = cost_tokens + penalty

        # 로깅
        self.logger.log(
            module=LogModule.SCAN_OPTIMIZER,
            action="compute_expected_loss",
            metadata={
                "scan_mode": scan_mode.value,
                "project_size": project_size,
                "complexity": complexity,
                "cost_tokens": cost_tokens,
                "penalty": penalty,
                "expected_loss": expected_loss,
            },
        )

        return expected_loss

    def recommend_scan_mode(
        self, project_size: int, complexity: float, user_budget_tokens: Optional[int] = None
    ) -> Dict:
        """
        최적 스캔 모드 추천

        모든 모드의 Expected Loss를 계산하여 가장 낮은 모드를 추천합니다.
        사용자 예산이 있는 경우 예산 내에서 최적 모드를 선택합니다.

        Args:
            project_size: 프로젝트 파일 수
            complexity: 프로젝트 복잡도 (1.0 ~ 5.0)
            user_budget_tokens: 사용자 토큰 예산 (Optional)

        Returns:
            추천 결과 딕셔너리
        """
        # 각 모드의 Expected Loss 계산
        losses = {}
        for mode in ScanMode:
            loss = self.compute_expected_loss(mode, project_size, complexity)
            losses[mode] = loss

        # Expected Loss 기준 최적 모드
        optimal_mode = min(losses, key=losses.get)

        # 예산 제약이 있는 경우
        if user_budget_tokens is not None:
            # 예산 내에서 Loss가 가장 낮은 모드 선택
            affordable_modes = {
                mode: loss
                for mode, loss in losses.items()
                if self.MODE_PARAMS[mode]["cost_multiplier"] * project_size <= user_budget_tokens
            }

            if affordable_modes:
                optimal_mode = min(affordable_modes, key=affordable_modes.get)
            else:
                optimal_mode = ScanMode.NONE  # 예산 부족

        # 로깅
        self.logger.log(
            module=LogModule.SCAN_OPTIMIZER,
            action="recommend_scan_mode",
            metadata={
                "project_size": project_size,
                "complexity": complexity,
                "user_budget_tokens": user_budget_tokens,
                "losses": {mode.value: loss for mode, loss in losses.items()},
                "recommended_mode": optimal_mode.value,
            },
        )

        return {
            "recommended_mode": optimal_mode,
            "expected_losses": losses,
            "optimal_loss": losses[optimal_mode],
            "justification": self._generate_justification(
                optimal_mode, project_size, complexity, losses
            ),
        }

    def score_file_importance(self, file_path: str) -> Tuple[FileImportance, float]:
        """
        파일 중요도 스코어링

        파일명과 확장자를 기반으로 중요도를 판단합니다.

        Args:
            file_path: 파일 경로

        Returns:
            (중요도 레벨, 점수) 튜플
        """
        file_name = Path(file_path).name

        # CRITICAL 체크
        if file_name in self.IMPORTANCE_PATTERNS[FileImportance.CRITICAL]:
            return FileImportance.CRITICAL, 1.0

        # HIGH 체크
        if file_name in self.IMPORTANCE_PATTERNS[FileImportance.HIGH]:
            return FileImportance.HIGH, 0.8

        # LOW 체크 (테스트 파일, 문서)
        for pattern in self.IMPORTANCE_PATTERNS[FileImportance.LOW]:
            if self._match_pattern(file_name, pattern):
                return FileImportance.LOW, 0.3

        # MEDIUM (기본)
        return FileImportance.MEDIUM, 0.5

    def optimize_scan_order(
        self, file_list: List[str], change_probabilities: Optional[Dict[str, float]] = None
    ) -> List[str]:
        """
        스캔 순서 최적화

        파일 중요도와 변경 가능성을 고려하여 스캔 순서를 결정합니다.

        Args:
            file_list: 스캔할 파일 목록
            change_probabilities: 파일별 변경 확률 (Optional)

        Returns:
            최적화된 파일 순서
        """
        # 파일별 우선순위 계산
        file_priorities = []

        for file_path in file_list:
            importance, importance_score = self.score_file_importance(file_path)

            # 변경 확률 (제공되지 않으면 기본값 0.5)
            change_prob = 0.5
            if change_probabilities and file_path in change_probabilities:
                change_prob = change_probabilities[file_path]

            # 우선순위 = 중요도 * 변경확률
            # (중요하고 자주 변경되는 파일을 먼저 스캔)
            priority = importance_score * change_prob

            file_priorities.append(
                {
                    "file_path": file_path,
                    "importance": importance.value,
                    "importance_score": importance_score,
                    "change_prob": change_prob,
                    "priority": priority,
                }
            )

        # 우선순위 내림차순 정렬
        file_priorities.sort(key=lambda x: x["priority"], reverse=True)

        optimized_order = [f["file_path"] for f in file_priorities]

        # 로깅
        self.logger.log(
            module=LogModule.SCAN_OPTIMIZER,
            action="optimize_scan_order",
            metadata={
                "total_files": len(file_list),
                "top_10_files": file_priorities[:10],
            },
        )

        return optimized_order

    def justify_full_scan(
        self, project_size: int, complexity: float, estimated_tokens: int, estimated_cost_usd: float
    ) -> Dict:
        """
        FULL 스캔 모드 정당성 설명

        사용자가 FULL 모드를 선택했을 때 왜 필요한지, 어떤 이점이 있는지 설명합니다.

        Args:
            project_size: 프로젝트 파일 수
            complexity: 프로젝트 복잡도
            estimated_tokens: 예상 토큰 소모량
            estimated_cost_usd: 예상 비용 (USD)

        Returns:
            정당성 설명 딕셔너리
        """
        # 모든 모드의 Expected Loss 계산
        losses = {}
        for mode in ScanMode:
            loss = self.compute_expected_loss(mode, project_size, complexity)
            losses[mode] = loss

        # LIGHT 모드 대비 이점 계산
        full_loss = losses[ScanMode.FULL]
        light_loss = losses[ScanMode.LIGHT]

        # FULL 모드가 더 나은 경우
        if full_loss < light_loss:
            benefit_tokens = light_loss - full_loss
            justification_reason = (
                f"프로젝트 복잡도({complexity:.1f})가 높아 FULL 스캔이 장기적으로 "
                f"{int(benefit_tokens)} 토큰을 절약합니다. "
                f"LIGHT 모드는 20%의 파일을 놓쳐 미래에 더 많은 비용이 발생합니다."
            )
            is_justified = True
        else:
            benefit_tokens = full_loss - light_loss
            justification_reason = (
                f"LIGHT 모드가 {int(benefit_tokens)} 토큰 더 효율적입니다. "
                f"그러나 FULL 스캔은 5% 누락률로 완벽한 맥락을 보장합니다."
            )
            is_justified = False

        justification = {
            "is_justified": is_justified,
            "reason": justification_reason,
            "full_scan_loss": full_loss,
            "light_scan_loss": light_loss,
            "benefit_tokens": abs(benefit_tokens),
            "estimated_tokens": estimated_tokens,
            "estimated_cost_usd": estimated_cost_usd,
            "timestamp": datetime.now().isoformat(),
        }

        # 로깅
        self.logger.log(
            module=LogModule.SCAN_OPTIMIZER, action="justify_full_scan", metadata=justification
        )

        return justification

    def _match_pattern(self, file_name: str, pattern: str) -> bool:
        """
        패턴 매칭 (fnmatch 사용)

        Args:
            file_name: 파일명
            pattern: 패턴 (예: "*.py", "test_*.py", "*_test.py")

        Returns:
            매칭 여부
        """
        return fnmatch.fnmatch(file_name, pattern)

    def _generate_justification(
        self,
        recommended_mode: ScanMode,
        project_size: int,
        complexity: float,
        losses: Dict[ScanMode, float],
    ) -> str:
        """
        추천 모드에 대한 정당성 설명 생성

        Args:
            recommended_mode: 추천된 모드
            project_size: 프로젝트 크기
            complexity: 복잡도
            losses: 각 모드의 Expected Loss

        Returns:
            정당성 설명 문자열
        """
        if recommended_mode == ScanMode.FULL:
            return (
                f"프로젝트 크기({project_size}개 파일)와 복잡도({complexity:.1f})를 고려할 때, "
                f"FULL 스캔의 Expected Loss({int(losses[ScanMode.FULL])} 토큰)가 "
                f"가장 낮습니다. 5% 누락률로 완벽한 초기 맥락을 구축합니다."
            )
        elif recommended_mode == ScanMode.LIGHT:
            return (
                f"프로젝트 크기({project_size}개 파일)가 적당하여 "
                f"LIGHT 스캔의 Expected Loss({int(losses[ScanMode.LIGHT])} 토큰)가 "
                f"최적입니다. 핵심 파일만 스캔하여 효율적입니다."
            )
        else:  # NONE
            return (
                f"프로젝트가 매우 작거나({project_size}개 파일) 단순하여 "
                f"초기 스캔 없이 진행하는 것이 가장 효율적입니다."
            )

    def export_statistics(self) -> Dict:
        """
        스캔 최적화 통계 내보내기

        Returns:
            통계 딕셔너리
        """
        return {
            "optimizer_version": "1.0.0",
            "miss_penalty": self.MISS_PENALTY,
            "mode_params": {mode.value: params for mode, params in self.MODE_PARAMS.items()},
            "timestamp": datetime.now().isoformat(),
        }
