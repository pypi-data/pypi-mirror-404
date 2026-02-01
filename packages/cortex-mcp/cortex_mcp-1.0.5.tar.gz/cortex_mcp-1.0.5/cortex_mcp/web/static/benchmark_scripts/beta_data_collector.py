"""
베타테스터 데이터 수집 시스템 (v3.0)

알파/베타 테스트 중 수집된 데이터를 분석하고 리포트 생성

핵심 기능:
1. 모듈별 사용 통계 분석
2. 오류율 및 성능 지표 집계
3. 사용자 패턴 분석
4. KPI 목표 달성도 추적
"""

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.alpha_logger import LogModule, get_alpha_logger


@dataclass
class ModuleUsageStats:
    """모듈별 사용 통계"""

    module_name: str
    total_calls: int = 0
    success_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.success_count / self.total_calls

    @property
    def avg_latency_ms(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_latency_ms / self.total_calls

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "total_calls": self.total_calls,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(self.success_rate * 100, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
        }


@dataclass
class BetaTestReport:
    """베타테스트 리포트"""

    report_id: str
    generated_at: str
    period_start: str
    period_end: str
    total_sessions: int
    total_actions: int
    module_stats: Dict[str, ModuleUsageStats] = field(default_factory=dict)
    kpi_achievement: Dict[str, Any] = field(default_factory=dict)
    user_feedback_summary: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "period": {"start": self.period_start, "end": self.period_end},
            "overview": {
                "total_sessions": self.total_sessions,
                "total_actions": self.total_actions,
            },
            "module_stats": {name: stats.to_dict() for name, stats in self.module_stats.items()},
            "kpi_achievement": self.kpi_achievement,
            "user_feedback_summary": self.user_feedback_summary,
            "recommendations": self.recommendations,
        }


class BetaDataCollector:
    """
    베타테스트 데이터 수집 및 분석

    KPI 목표 대비 실제 성능 추적
    """

    # KPI 목표
    KPI_TARGETS = {
        "context_recommendation_accuracy": 0.95,  # 95%
        "token_savings": 0.70,  # 70%
        "rag_accuracy": 1.00,  # 100%
        "automation_success_rate": 0.80,  # 80%
        "p95_latency_ms": 50.0,  # 50ms
        "error_rate_reduction": 0.50,  # 50% 감소
    }

    def __init__(self, log_base_dir: Optional[Path] = None):
        """
        Args:
            log_base_dir: 로그 디렉토리 (~/.cortex/logs/alpha_test/)
        """
        if log_base_dir is None:
            log_base_dir = Path.home() / ".cortex" / "logs" / "alpha_test"

        self.log_base_dir = Path(log_base_dir)
        self.logger = get_alpha_logger()

    def collect_module_stats(self) -> Dict[str, ModuleUsageStats]:
        """모듈별 사용 통계 수집"""
        stats = {}

        for module in LogModule:
            log_file = self.log_base_dir / f"{module.value}.jsonl"
            module_stats = ModuleUsageStats(module_name=module.value)

            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                entry = json.loads(line)
                                module_stats.total_calls += 1

                                if entry.get("success", True):
                                    module_stats.success_count += 1
                                else:
                                    module_stats.error_count += 1

                                latency = entry.get("latency_ms")
                                if latency is not None:
                                    module_stats.total_latency_ms += latency
                except Exception as e:
                    print(f"[WARN] Failed to read {log_file}: {e}")

            stats[module.value] = module_stats

        return stats

    def calculate_kpi_achievement(
        self, module_stats: Dict[str, ModuleUsageStats]
    ) -> Dict[str, Any]:
        """KPI 목표 달성도 계산"""
        achievement = {}

        # 1. 자동화 성공률 (Smart Context + Reference History)
        smart_ctx = module_stats.get("smart_context", ModuleUsageStats("smart_context"))
        ref_hist = module_stats.get("reference_history", ModuleUsageStats("reference_history"))

        total_auto_calls = smart_ctx.total_calls + ref_hist.total_calls
        total_auto_success = smart_ctx.success_count + ref_hist.success_count

        if total_auto_calls > 0:
            auto_success_rate = total_auto_success / total_auto_calls
            achievement["automation_success_rate"] = {
                "current": round(auto_success_rate, 4),
                "target": self.KPI_TARGETS["automation_success_rate"],
                "achieved": auto_success_rate >= self.KPI_TARGETS["automation_success_rate"],
            }

        # 2. RAG 검색 성능
        rag = module_stats.get("rag_search", ModuleUsageStats("rag_search"))
        if rag.total_calls > 0:
            achievement["rag_performance"] = {
                "success_rate": round(rag.success_rate, 4),
                "avg_latency_ms": round(rag.avg_latency_ms, 2),
                "p95_target_ms": self.KPI_TARGETS["p95_latency_ms"],
                "latency_achieved": rag.avg_latency_ms <= self.KPI_TARGETS["p95_latency_ms"],
            }

        # 3. 온톨로지 분류 성능
        ontology = module_stats.get("ontology", ModuleUsageStats("ontology"))
        if ontology.total_calls > 0:
            achievement["ontology_performance"] = {
                "success_rate": round(ontology.success_rate, 4),
                "avg_latency_ms": round(ontology.avg_latency_ms, 2),
            }

        # 4. 전체 오류율
        total_calls = sum(s.total_calls for s in module_stats.values())
        total_errors = sum(s.error_count for s in module_stats.values())

        if total_calls > 0:
            error_rate = total_errors / total_calls
            achievement["overall_error_rate"] = {
                "current": round(error_rate, 4),
                "error_count": total_errors,
                "total_calls": total_calls,
            }

        return achievement

    def analyze_user_patterns(self) -> Dict[str, Any]:
        """사용자 패턴 분석"""
        patterns = {"most_used_modules": [], "peak_hours": [], "common_actions": []}

        module_usage = []
        for module in LogModule:
            log_file = self.log_base_dir / f"{module.value}.jsonl"
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        count = sum(1 for line in f if line.strip())
                        if count > 0:
                            module_usage.append((module.value, count))
                except:
                    pass

        # 가장 많이 사용된 모듈 상위 3개
        module_usage.sort(key=lambda x: x[1], reverse=True)
        patterns["most_used_modules"] = module_usage[:3]

        return patterns

    def generate_recommendations(
        self, module_stats: Dict[str, ModuleUsageStats], kpi_achievement: Dict[str, Any]
    ) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []

        # 성공률이 낮은 모듈 식별
        for name, stats in module_stats.items():
            if stats.total_calls >= 10 and stats.success_rate < 0.9:
                recommendations.append(
                    f"[{name}] 모듈의 성공률이 {stats.success_rate*100:.1f}%로 "
                    f"목표(90%) 미달. 원인 분석 필요."
                )

        # Latency 문제 식별
        for name, stats in module_stats.items():
            if stats.total_calls >= 10 and stats.avg_latency_ms > 100:
                recommendations.append(
                    f"[{name}] 모듈의 평균 응답시간이 {stats.avg_latency_ms:.1f}ms로 "
                    f"느림. 최적화 검토 필요."
                )

        # KPI 미달성 항목
        auto_kpi = kpi_achievement.get("automation_success_rate", {})
        if auto_kpi.get("achieved") is False:
            recommendations.append(
                f"자동화 성공률 {auto_kpi.get('current', 0)*100:.1f}%로 "
                f"목표({self.KPI_TARGETS['automation_success_rate']*100:.0f}%) 미달성."
            )

        if not recommendations:
            recommendations.append("모든 KPI가 정상 범위입니다. 현재 상태를 유지하세요.")

        return recommendations

    def generate_report(self, period_days: int = 7) -> BetaTestReport:
        """
        베타테스트 리포트 생성

        Args:
            period_days: 분석 기간 (일)
        """
        now = datetime.utcnow()
        period_start = now - timedelta(days=period_days)

        # 데이터 수집
        module_stats = self.collect_module_stats()
        kpi_achievement = self.calculate_kpi_achievement(module_stats)
        user_patterns = self.analyze_user_patterns()
        recommendations = self.generate_recommendations(module_stats, kpi_achievement)

        # 전체 통계
        total_actions = sum(s.total_calls for s in module_stats.values())

        report = BetaTestReport(
            report_id=f"beta_report_{now.strftime('%Y%m%d_%H%M%S')}",
            generated_at=now.isoformat(),
            period_start=period_start.isoformat(),
            period_end=now.isoformat(),
            total_sessions=1,  # 단일 세션 기준
            total_actions=total_actions,
            module_stats=module_stats,
            kpi_achievement=kpi_achievement,
            user_feedback_summary={"positive": 0, "negative": 0, "neutral": 0},
            recommendations=recommendations,
        )

        return report

    def export_report(self, report: BetaTestReport, output_path: Optional[Path] = None) -> Path:
        """리포트 파일로 내보내기"""
        if output_path is None:
            output_path = self.log_base_dir / "reports" / f"{report.report_id}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

        return output_path

    def print_report_summary(self, report: BetaTestReport) -> None:
        """리포트 요약 출력"""
        print("\n" + "=" * 70)
        print("Cortex Beta Test Report")
        print("=" * 70)

        print(f"\nReport ID: {report.report_id}")
        print(f"Generated: {report.generated_at}")
        print(f"Period: {report.period_start} ~ {report.period_end}")

        print("\n" + "-" * 70)
        print("Overview")
        print("-" * 70)
        print(f"  Total Actions: {report.total_actions}")

        print("\n" + "-" * 70)
        print("Module Statistics")
        print("-" * 70)

        for name, stats in report.module_stats.items():
            if stats.total_calls > 0:
                print(f"\n  [{name}]")
                print(f"    Calls: {stats.total_calls}")
                print(f"    Success Rate: {stats.success_rate*100:.1f}%")
                print(f"    Avg Latency: {stats.avg_latency_ms:.2f}ms")

        print("\n" + "-" * 70)
        print("KPI Achievement")
        print("-" * 70)

        for kpi_name, kpi_data in report.kpi_achievement.items():
            print(f"\n  [{kpi_name}]")
            for key, value in kpi_data.items():
                if isinstance(value, float):
                    print(f"    {key}: {value:.4f}")
                elif isinstance(value, bool):
                    print(f"    {key}: {'PASS' if value else 'FAIL'}")
                else:
                    print(f"    {key}: {value}")

        print("\n" + "-" * 70)
        print("Recommendations")
        print("-" * 70)

        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")

        print("\n" + "=" * 70)


def main():
    """메인 실행"""
    collector = BetaDataCollector()

    print("Generating Beta Test Report...")
    report = collector.generate_report(period_days=7)

    # 출력
    collector.print_report_summary(report)

    # 파일로 내보내기
    output_path = collector.export_report(report)
    print(f"\nReport exported to: {output_path}")


if __name__ == "__main__":
    main()
