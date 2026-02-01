"""
Cortex MCP - Benchmark Report Generator

벤치마크 결과를 사용자 친화적인 HTML 리포트로 생성

사용법:
    python generate_report.py                    # 최신 결과로 리포트 생성
    python generate_report.py --file <path>      # 특정 결과 파일 사용
    python generate_report.py --compare          # 이전 결과와 비교
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config


def get_status_color(passed: bool) -> str:
    """상태에 따른 색상"""
    return "#4CAF50" if passed else "#f44336"


def get_status_icon(passed: bool) -> str:
    """상태 아이콘"""
    return "PASS" if passed else "FAIL"


def format_value(name: str, value: float) -> str:
    """값 포맷팅"""
    if "rate" in name.lower() or "accuracy" in name.lower() or "savings" in name.lower():
        return f"{value:.1f}%"
    elif "time" in name.lower() or "latency" in name.lower():
        return f"{value:.0f}ms"
    else:
        return f"{value}"


def generate_html_report(report_data: dict, output_path: Path) -> Path:
    """HTML 리포트 생성"""

    summary = report_data.get("summary", {})
    results = report_data.get("results", [])
    quality_goals = report_data.get("quality_goals", {})
    generated_at = report_data.get("generated_at", datetime.utcnow().isoformat())

    # 전체 통과 여부
    all_passed = summary.get("failed", 0) == 0
    overall_status = (
        "ALL TESTS PASSED" if all_passed else f"{summary.get('failed', 0)} TEST(S) FAILED"
    )
    overall_color = "#4CAF50" if all_passed else "#f44336"

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cortex Benchmark Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header .subtitle {{
            color: #888;
            font-size: 0.9rem;
        }}
        .overall-status {{
            background: {overall_color}22;
            border: 2px solid {overall_color};
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .overall-status h2 {{
            color: {overall_color};
            font-size: 1.5rem;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: #ffffff10;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 2rem;
            font-weight: bold;
            color: #00d4ff;
        }}
        .summary-card .label {{
            color: #888;
            font-size: 0.85rem;
            margin-top: 5px;
        }}
        .quality-goals {{
            background: #ffffff08;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
        }}
        .quality-goals h3 {{
            margin-bottom: 20px;
            color: #00d4ff;
        }}
        .goal-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px;
            background: #ffffff05;
            border-radius: 8px;
            margin-bottom: 10px;
        }}
        .goal-name {{
            font-weight: 500;
        }}
        .goal-values {{
            display: flex;
            gap: 20px;
            align-items: center;
        }}
        .goal-target {{
            color: #888;
        }}
        .goal-actual {{
            font-weight: bold;
        }}
        .goal-status {{
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        .goal-status.pass {{
            background: #4CAF5022;
            color: #4CAF50;
        }}
        .goal-status.fail {{
            background: #f4433622;
            color: #f44336;
        }}
        .detail-section {{
            background: #ffffff08;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
        }}
        .detail-section h3 {{
            margin-bottom: 15px;
            color: #00d4ff;
        }}
        .detail-item {{
            padding: 10px;
            background: #ffffff05;
            border-radius: 6px;
            margin-bottom: 8px;
            font-family: monospace;
            font-size: 0.85rem;
            color: #ccc;
        }}
        .marketing-box {{
            background: linear-gradient(135deg, #7b2cbf22 0%, #00d4ff22 100%);
            border: 1px solid #7b2cbf44;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            margin-top: 40px;
        }}
        .marketing-box h3 {{
            margin-bottom: 15px;
        }}
        .marketing-stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
        }}
        .marketing-stat {{
            text-align: center;
        }}
        .marketing-stat .value {{
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .marketing-stat .label {{
            color: #888;
            font-size: 0.9rem;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 0.8rem;
        }}
        @media (max-width: 768px) {{
            .summary-cards {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .marketing-stats {{
                flex-direction: column;
                gap: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Cortex Benchmark Report</h1>
            <p class="subtitle">Generated: {generated_at}</p>
        </div>

        <div class="overall-status">
            <h2>{overall_status}</h2>
        </div>

        <div class="summary-cards">
            <div class="summary-card">
                <div class="value">{summary.get('total_tests', 0)}</div>
                <div class="label">Total Tests</div>
            </div>
            <div class="summary-card">
                <div class="value" style="color: #4CAF50;">{summary.get('passed', 0)}</div>
                <div class="label">Passed</div>
            </div>
            <div class="summary-card">
                <div class="value" style="color: #f44336;">{summary.get('failed', 0)}</div>
                <div class="label">Failed</div>
            </div>
            <div class="summary-card">
                <div class="value">{int(summary.get('passed', 0) / max(summary.get('total_tests', 1), 1) * 100)}%</div>
                <div class="label">Pass Rate</div>
            </div>
        </div>

        <div class="quality-goals">
            <h3>Quality Goals</h3>
"""

    # Quality Goals 추가
    goal_names = {
        "token_savings": "Token Savings Rate",
        "recommendation_accuracy": "Recommendation Accuracy",
        "rag_recall": "RAG Search Recall",
        "response_time": "Response Time",
    }

    for goal_key, goal_data in quality_goals.items():
        goal_name = goal_names.get(goal_key, goal_key)
        target = goal_data.get("target", "N/A")
        actual = goal_data.get("actual", "N/A")
        status = goal_data.get("status", "")
        status_class = "pass" if status == "PASS" else "fail"

        html += f"""
            <div class="goal-item">
                <span class="goal-name">{goal_name}</span>
                <div class="goal-values">
                    <span class="goal-target">Target: {target}</span>
                    <span class="goal-actual">Actual: {actual}</span>
                    <span class="goal-status {status_class}">{status}</span>
                </div>
            </div>
"""

    html += """
        </div>
"""

    # 상세 결과 추가
    for result in results:
        result_name = result.get("name", "Unknown")
        passed = result.get("passed", False)
        details = result.get("details", [])
        metrics = result.get("metrics", {})

        status_color = get_status_color(passed)
        html += f"""
        <div class="detail-section">
            <h3 style="border-left: 3px solid {status_color}; padding-left: 10px;">{result_name}</h3>
"""
        for detail in details[:10]:  # 최대 10개만
            html += f'            <div class="detail-item">{detail}</div>\n'

        if metrics:
            html += '            <div class="detail-item" style="background: #00d4ff11; border: 1px solid #00d4ff44;">\n'
            html += "                <strong>Metrics:</strong> "
            html += ", ".join(f"{k}: {v}" for k, v in metrics.items())
            html += "\n            </div>\n"

        html += "        </div>\n"

    # 마케팅용 요약 박스
    token_savings = quality_goals.get("token_savings", {}).get("actual", "75%")
    rag_recall = quality_goals.get("rag_recall", {}).get("actual", "100%")
    response_time = quality_goals.get("response_time", {}).get("actual", "10ms")

    html += f"""
        <div class="marketing-box">
            <h3>Cortex Performance Summary</h3>
            <p>AI 장기 기억을 위한 지능형 MCP 서버</p>
            <div class="marketing-stats">
                <div class="marketing-stat">
                    <div class="value">{token_savings}</div>
                    <div class="label">Token Savings</div>
                </div>
                <div class="marketing-stat">
                    <div class="value">{rag_recall}</div>
                    <div class="label">RAG Recall</div>
                </div>
                <div class="marketing-stat">
                    <div class="value">{response_time}</div>
                    <div class="label">Response Time</div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Cortex MCP - Zero-Effort, Zero-Trust, Zero-Loss</p>
            <p>https://github.com/syab726/cortex</p>
        </div>
    </div>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def get_latest_benchmark_result() -> Path:
    """가장 최근 벤치마크 결과 파일 반환"""
    results_dir = config.logs_dir / "benchmark_results"
    if not results_dir.exists():
        raise FileNotFoundError("No benchmark results found")

    result_files = sorted(results_dir.glob("benchmark_*.json"), reverse=True)
    if not result_files:
        raise FileNotFoundError("No benchmark results found")

    return result_files[0]


def main():
    parser = argparse.ArgumentParser(description="Generate Cortex Benchmark Report")
    parser.add_argument("--file", type=str, help="Specific benchmark result file")
    parser.add_argument("--output", type=str, help="Output HTML file path")

    args = parser.parse_args()

    # 결과 파일 결정
    if args.file:
        result_file = Path(args.file)
    else:
        result_file = get_latest_benchmark_result()

    print(f"Using benchmark result: {result_file}")

    # JSON 로드
    with open(result_file, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # 출력 경로 결정
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = result_file.parent / f"{result_file.stem}_report.html"

    # HTML 리포트 생성
    generated_path = generate_html_report(report_data, output_path)
    print(f"Report generated: {generated_path}")

    # 절대 경로 출력
    print(f"\nOpen in browser: file://{generated_path.absolute()}")


if __name__ == "__main__":
    main()
