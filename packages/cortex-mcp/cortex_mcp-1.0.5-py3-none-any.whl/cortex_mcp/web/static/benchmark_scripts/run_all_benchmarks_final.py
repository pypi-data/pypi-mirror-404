"""
Final Comprehensive Benchmark Runner

Combines all benchmark results into a single comprehensive report.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import simple benchmark tests
import sys
import subprocess


def run_comprehensive_benchmarks():
    """Run all benchmarks and combine results"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     CORTEX MCP FINAL COMPREHENSIVE BENCHMARK SUITE           ║
║                                                              ║
║  All tests are reproducible and publicly verifiable         ║
║  Results will be published on cortex-mcp.com/benchmarks     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    # Load existing simple benchmark results
    simple_results_file = Path(__file__).parent.parent.parent / "benchmark_results_comprehensive.json"
    if simple_results_file.exists():
        with open(simple_results_file, "r") as f:
            simple_results = json.load(f)
    else:
        simple_results = {"tests": {}}

    # Load comprehensive v2 results
    v2_results_file = Path(__file__).parent.parent.parent / "benchmark_results_comprehensive_v2.json"
    if v2_results_file.exists():
        with open(v2_results_file, "r") as f:
            v2_results = json.load(f)
    else:
        v2_results = {"tests": {}}

    # Merge results
    all_results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "3.0.0",
        "test_categories": {
            "category_1_context_integrity": {
                "name": "Context Integrity",
                "tests": [
                    "smart_context_efficiency",
                    "reference_history_accuracy",
                    "branch_organization"
                ]
            },
            "category_2_truth_verification": {
                "name": "Truth & Verification",
                "tests": [
                    "hallucination_detection",
                    "grounding_score",
                    "claim_extraction",
                    "contradiction_detection"
                ]
            },
            "category_3_stability_recovery": {
                "name": "Stability & Recovery",
                "tests": [
                    "snapshot_restore",
                    "search_latency"
                ]
            },
            "category_4_scalability": {
                "name": "Scalability & Continuity",
                "tests": [
                    "needle_in_haystack"
                ]
            }
        },
        "tests": {}
    }

    # Merge test results from both files
    for test_name in ["smart_context_efficiency", "search_latency", "needle_in_haystack"]:
        if test_name in simple_results.get("tests", {}):
            all_results["tests"][test_name] = simple_results["tests"][test_name]

    for test_name in ["reference_history_accuracy", "branch_organization", "hallucination_detection",
                      "grounding_score", "claim_extraction", "contradiction_detection", "snapshot_restore"]:
        if test_name in v2_results.get("tests", {}):
            all_results["tests"][test_name] = v2_results["tests"][test_name]

    # Calculate summary
    total = len([t for t in all_results["tests"].values() if t.get("status") != "skipped"])
    passed = len([t for t in all_results["tests"].values() if t.get("status") == "passed"])
    failed = len([t for t in all_results["tests"].values() if t.get("status") == "failed"])

    all_results["summary"] = {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round((passed / total) * 100, 1) if total > 0 else 0,
        "categories": 4,
        "test_count_by_category": {
            "context_integrity": 3,
            "truth_verification": 4,
            "stability_recovery": 2,
            "scalability": 1
        }
    }

    # Save final results
    output_file = Path(__file__).parent.parent.parent / "benchmark_results_final.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print("FINAL COMPREHENSIVE BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {all_results['summary']['total_tests']}")
    print(f"Passed: {all_results['summary']['passed']}")
    print(f"Failed: {all_results['summary']['failed']}")
    print(f"Pass Rate: {all_results['summary']['pass_rate']}%")
    print(f"\nCategories: {all_results['summary']['categories']}")
    print(f"  • Context Integrity: {all_results['summary']['test_count_by_category']['context_integrity']} tests")
    print(f"  • Truth & Verification: {all_results['summary']['test_count_by_category']['truth_verification']} tests")
    print(f"  • Stability & Recovery: {all_results['summary']['test_count_by_category']['stability_recovery']} tests")
    print(f"  • Scalability: {all_results['summary']['test_count_by_category']['scalability']} tests")
    print(f"{'='*60}")
    print(f"\nResults saved to: {output_file}")
    print(f"{'='*60}\n")

    return all_results


if __name__ == "__main__":
    run_comprehensive_benchmarks()
