"""
Cortex MCP Comprehensive Benchmark Runner

Runs all benchmark tests and generates comprehensive results.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all test classes
from test_hallucination_detection import TestHallucinationDetection
from test_reference_history import TestReferenceHistory
from test_branch_isolation import TestBranchIsolation
from test_grounding_score import TestGroundingScore
from test_claim_extraction import TestClaimExtraction
from test_contradiction_detection import TestContradictionDetection
from test_snapshot_restore import TestSnapshotRestore


def run_all_benchmarks():
    """Run all benchmark tests and aggregate results"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        CORTEX MCP COMPREHENSIVE BENCHMARK SUITE              ║
║                                                              ║
║  All tests are reproducible and publicly verifiable         ║
║  Results will be published on cortex-mcp.com/benchmarks     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    all_results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "tests": {}
    }

    # Define all tests
    tests = [
        # Category 1: Context Integrity
        ("smart_context_efficiency", None, "Simple benchmark - already run"),
        ("reference_history_accuracy", TestReferenceHistory, "test_reference_accuracy"),
        ("branch_organization", TestBranchIsolation, "test_branch_isolation"),

        # Category 2: Truth & Verification
        ("hallucination_detection", TestHallucinationDetection, "test_hallucination_detection"),
        ("grounding_score", TestGroundingScore, "test_grounding_correlation"),
        ("claim_extraction", TestClaimExtraction, "test_claim_extraction_accuracy"),
        ("contradiction_detection", TestContradictionDetection, "test_contradiction_detection_rate"),

        # Category 3: Stability & Recovery
        ("snapshot_restore", TestSnapshotRestore, "test_snapshot_restore_integrity"),

        # Category 4: Scalability & Continuity
        ("search_latency", None, "Simple benchmark - already run"),
        ("needle_in_haystack", None, "Simple benchmark - already run"),
    ]

    passed = 0
    failed = 0

    for test_name, test_class, test_method in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")

        try:
            if test_class is None:
                # Skip tests already run in simple_benchmark.py
                print(f"✓ SKIPPED (already tested in simple_benchmark.py)")
                all_results["tests"][test_name] = {
                    "status": "skipped",
                    "note": "Tested in simple_benchmark.py"
                }
                continue

            # Instantiate test class
            test = test_class()

            # Call setup with appropriate parameters
            if test_name == "reference_history_accuracy":
                from pathlib import Path
                test_dir = Path("/tmp/cortex_test/reference_history")
                test.setup(test_dir)
            else:
                test.setup()

            # Run test method
            method = getattr(test, test_method)
            result = method()

            # Add status
            result["test"] = test_name
            result["status"] = "passed"

            all_results["tests"][test_name] = result
            passed += 1

            print(f"✓ PASSED")
            for key, value in result.items():
                if key not in ["test", "status"]:
                    print(f"  {key}: {value}")

        except Exception as e:
            print(f"✗ FAILED: {e}")
            all_results["tests"][test_name] = {
                "test": test_name,
                "status": "failed",
                "error": str(e)
            }
            failed += 1

    # Summary
    total = passed + failed
    all_results["summary"] = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round((passed / total) * 100, 1) if total > 0 else 0
    }

    # Save results
    output_file = Path(__file__).parent.parent.parent / "benchmark_results_comprehensive_v2.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {all_results['summary']['total']}")
    print(f"Passed: {all_results['summary']['passed']}")
    print(f"Failed: {all_results['summary']['failed']}")
    print(f"Pass Rate: {all_results['summary']['pass_rate']}%")
    print(f"{'='*60}")
    print(f"\nResults saved to: {output_file}")
    print(f"{'='*60}\n")

    return all_results


if __name__ == "__main__":
    run_all_benchmarks()
