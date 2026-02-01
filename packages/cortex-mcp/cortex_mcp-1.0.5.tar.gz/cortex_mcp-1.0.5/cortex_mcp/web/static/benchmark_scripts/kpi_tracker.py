"""
KPI 추적기 (v3.0)

Cortex MCP 핵심 KPI 추적 및 모니터링

KPI 목표:
- 맥락 추천 정확도: 95%
- 토큰 절감율: 70%
- RAG 검색 정확도: 100% (Needle in Haystack)
- 자동화 성공률: 80%+
- 데이터 복구율: 100%
- P95 Latency: 50ms 이하
- Agent Decision Error Rate: 50% 감소
"""

import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class KPITarget:
    """KPI 목표"""

    name: str
    target_value: float
    unit: str
    comparison: str  # "gte" (>=), "lte" (<=), "eq" (==)
    description: str = ""


@dataclass
class KPIMeasurement:
    """KPI 측정값"""

    kpi_name: str
    value: float
    timestamp: str
    passed: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class KPITracker:
    """
    Cortex MCP KPI 추적기

    핵심 KPI:
    1. 맥락 추천 정확도: 95%
    2. 토큰 절감율: 70%
    3. RAG 검색 정확도: 100%
    4. 자동화 성공률: 80%+
    5. P95 Latency: 50ms
    6. Agent Decision Error Rate: 50% 감소
    """

    # KPI 목표 정의
    KPI_TARGETS = {
        "context_recommendation_accuracy": KPITarget(
            name="맥락 추천 정확도",
            target_value=0.95,
            unit="%",
            comparison="gte",
            description="Reference History 기반 맥락 추천 정확도",
        ),
        "token_savings": KPITarget(
            name="토큰 절감율",
            target_value=0.70,
            unit="%",
            comparison="gte",
            description="Smart Context 압축으로 인한 토큰 절감",
        ),
        "rag_accuracy": KPITarget(
            name="RAG 검색 정확도",
            target_value=1.00,
            unit="%",
            comparison="gte",
            description="Needle in Haystack 테스트 정확도",
        ),
        "automation_success_rate": KPITarget(
            name="자동화 성공률",
            target_value=0.80,
            unit="%",
            comparison="gte",
            description="Plan A 유지율 (자동화 작업 성공률)",
        ),
        "data_recovery_rate": KPITarget(
            name="데이터 복구율",
            target_value=1.00,
            unit="%",
            comparison="gte",
            description="스냅샷 복원 테스트 성공률",
        ),
        "p95_latency_ms": KPITarget(
            name="P95 Latency",
            target_value=50.0,
            unit="ms",
            comparison="lte",
            description="RAG 검색 P95 응답 시간",
        ),
        "error_rate_reduction": KPITarget(
            name="오류율 감소",
            target_value=0.50,
            unit="%",
            comparison="gte",
            description="Agent Decision Error Rate 감소율 (vs Baseline)",
        ),
        "branch_decision_accuracy": KPITarget(
            name="브랜치 결정 정확도",
            target_value=0.95,
            unit="%",
            comparison="gte",
            description="자동 브랜치 생성 결정 정확도",
        ),
        "rag_recall_rate": KPITarget(
            name="RAG Recall Rate",
            target_value=0.90,
            unit="%",
            comparison="gte",
            description="RAG 검색 재현율",
        ),
    }

    def __init__(self, storage_path: Optional[Path] = None):
        """
        KPI 추적기 초기화

        Args:
            storage_path: KPI 데이터 저장 경로
        """
        if storage_path is None:
            storage_path = Path.home() / ".cortex" / "kpi"

        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.measurements: List[KPIMeasurement] = []
        self._load_history()

    def _load_history(self) -> None:
        """기존 측정 기록 로드"""
        history_file = self.storage_path / "kpi_history.json"
        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("measurements", []):
                        self.measurements.append(KPIMeasurement(**item))
            except Exception:
                pass

    def _save_history(self) -> None:
        """측정 기록 저장"""
        history_file = self.storage_path / "kpi_history.json"
        data = {
            "measurements": [
                {
                    "kpi_name": m.kpi_name,
                    "value": m.value,
                    "timestamp": m.timestamp,
                    "passed": m.passed,
                    "metadata": m.metadata,
                }
                for m in self.measurements[-1000:]  # 최근 1000개만 유지
            ]
        }
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def record(
        self, kpi_name: str, value: float, metadata: Optional[Dict[str, Any]] = None
    ) -> KPIMeasurement:
        """
        KPI 측정값 기록

        Args:
            kpi_name: KPI 이름 (KPI_TARGETS 키)
            value: 측정값
            metadata: 추가 메타데이터

        Returns:
            KPIMeasurement: 기록된 측정값
        """
        if kpi_name not in self.KPI_TARGETS:
            raise ValueError(f"Unknown KPI: {kpi_name}")

        target = self.KPI_TARGETS[kpi_name]
        passed = self._check_target(value, target)

        measurement = KPIMeasurement(
            kpi_name=kpi_name,
            value=value,
            timestamp=datetime.now().isoformat(),
            passed=passed,
            metadata=metadata or {},
        )

        self.measurements.append(measurement)
        self._save_history()

        return measurement

    def _check_target(self, value: float, target: KPITarget) -> bool:
        """목표 달성 여부 확인"""
        if target.comparison == "gte":
            return value >= target.target_value
        elif target.comparison == "lte":
            return value <= target.target_value
        elif target.comparison == "eq":
            return abs(value - target.target_value) < 0.001
        return False

    def get_latest(self, kpi_name: str) -> Optional[KPIMeasurement]:
        """특정 KPI의 최신 측정값"""
        for m in reversed(self.measurements):
            if m.kpi_name == kpi_name:
                return m
        return None

    def get_history(self, kpi_name: str, limit: int = 100) -> List[KPIMeasurement]:
        """특정 KPI의 측정 이력"""
        history = [m for m in self.measurements if m.kpi_name == kpi_name]
        return history[-limit:]

    def get_dashboard(self) -> Dict[str, Any]:
        """
        KPI 대시보드 데이터 생성

        Returns:
            전체 KPI 현황
        """
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "kpis": {},
            "summary": {"total_kpis": len(self.KPI_TARGETS), "met": 0, "not_met": 0, "no_data": 0},
        }

        for kpi_name, target in self.KPI_TARGETS.items():
            latest = self.get_latest(kpi_name)

            kpi_data = {
                "name": target.name,
                "description": target.description,
                "target": target.target_value,
                "unit": target.unit,
                "comparison": target.comparison,
            }

            if latest:
                kpi_data["current"] = latest.value
                kpi_data["passed"] = latest.passed
                kpi_data["last_measured"] = latest.timestamp

                if latest.passed:
                    dashboard["summary"]["met"] += 1
                else:
                    dashboard["summary"]["not_met"] += 1
            else:
                kpi_data["current"] = None
                kpi_data["passed"] = None
                kpi_data["last_measured"] = None
                dashboard["summary"]["no_data"] += 1

            dashboard["kpis"][kpi_name] = kpi_data

        return dashboard

    def print_dashboard(self) -> None:
        """대시보드 출력"""
        dashboard = self.get_dashboard()

        print("\n" + "=" * 70)
        print("Cortex MCP KPI Dashboard")
        print("=" * 70)

        summary = dashboard["summary"]
        print(f"\nSummary: {summary['met']}/{summary['total_kpis']} KPIs met")
        print(f"  Met: {summary['met']}")
        print(f"  Not Met: {summary['not_met']}")
        print(f"  No Data: {summary['no_data']}")

        print("\n" + "-" * 70)
        print("Detailed KPIs:")
        print("-" * 70)

        for kpi_name, data in dashboard["kpis"].items():
            status = "N/A"
            if data["passed"] is True:
                status = "PASS"
            elif data["passed"] is False:
                status = "FAIL"

            current = data["current"]
            target = data["target"]

            if current is not None:
                # 퍼센트 단위는 100배로 표시
                if data["unit"] == "%":
                    current_display = f"{current * 100:.1f}%"
                    target_display = f"{target * 100:.1f}%"
                else:
                    current_display = f"{current:.2f}{data['unit']}"
                    target_display = f"{target:.2f}{data['unit']}"
            else:
                current_display = "No data"
                target_display = (
                    f"{target * 100:.0f}%" if data["unit"] == "%" else f"{target}{data['unit']}"
                )

            comp_symbol = (
                ">="
                if data["comparison"] == "gte"
                else "<=" if data["comparison"] == "lte" else "=="
            )

            print(f"\n[{status}] {data['name']}")
            print(f"      Current: {current_display}")
            print(f"      Target:  {comp_symbol} {target_display}")
            print(f"      {data['description']}")

        print("\n" + "=" * 70)

    def export_report(self, filepath: Path) -> None:
        """KPI 리포트 내보내기"""
        dashboard = self.get_dashboard()
        dashboard["history"] = {}

        for kpi_name in self.KPI_TARGETS.keys():
            history = self.get_history(kpi_name, limit=50)
            dashboard["history"][kpi_name] = [
                {"value": m.value, "timestamp": m.timestamp, "passed": m.passed} for m in history
            ]

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(dashboard, f, ensure_ascii=False, indent=2)


# 싱글톤 인스턴스
_kpi_tracker: Optional[KPITracker] = None


def get_kpi_tracker() -> KPITracker:
    """KPI 추적기 싱글톤 인스턴스"""
    global _kpi_tracker
    if _kpi_tracker is None:
        _kpi_tracker = KPITracker()
    return _kpi_tracker


def reset_kpi_tracker() -> None:
    """KPI 추적기 리셋 (테스트용)"""
    global _kpi_tracker
    _kpi_tracker = None
