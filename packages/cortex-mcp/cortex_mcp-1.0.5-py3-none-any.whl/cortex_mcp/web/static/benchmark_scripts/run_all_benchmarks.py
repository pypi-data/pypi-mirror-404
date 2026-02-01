"""
Master Benchmark Test Runner

Executes all benchmark tests and generates comprehensive results.
Results are saved in JSON format for website display.
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import test classes
from test_smart_context import TestSmartContext
from test_reference_history import TestReferenceHistory
from test_hallucination_detection import TestHallucinationDetection


class BenchmarkRunner:
    """Run all benchmarks and collect results"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "tests": {}
        }

    def run_test(self, test_name, test_class, test_method):
        """Run a single test and capture results"""
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")

        try:
            # Create test instance
            test_instance = test_class()

            # Setup (using tmp directory)
            test_dir = Path("/tmp/cortex_benchmark") / test_name
            test_dir.mkdir(parents=True, exist_ok=True)
            test_instance.setup(test_dir)

            # Run test
            start_time = time.time()
            result = getattr(test_instance, test_method)()
            duration = time.time() - start_time

            # Record success
            self.results["tests"][test_name] = {
                "status": "passed",
                "duration_seconds": round(duration, 2),
                "results": result
            }

            print(f"✓ PASSED ({duration:.2f}s)")
            return True

        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            self.results["tests"][test_name] = {
                "status": "failed",
                "error": str(e)
            }
            return False

        except Exception as e:
            print(f"✗ ERROR: {e}")
            self.results["tests"][test_name] = {
                "status": "error",
                "error": str(e)
            }
            return False

    def run_all(self):
        """Run all benchmark tests"""
        tests = [
            # Category 1: Context Integrity
            ("smart_context_efficiency", TestSmartContext, "test_token_efficiency"),
            ("reference_history_accuracy", TestReferenceHistory, "test_reference_accuracy"),

            # Category 2: Truth & Verification
            ("hallucination_detection", TestHallucinationDetection, "test_hallucination_detection"),
        ]

        passed = 0
        failed = 0

        for test_name, test_class, test_method in tests:
            if self.run_test(test_name, test_class, test_method):
                passed += 1
            else:
                failed += 1

        # Summary
        total = passed + failed
        self.results["summary"] = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / total) * 100, 1) if total > 0 else 0
        }

        return self.results

    def save_results(self, output_file):
        """Save results to JSON file"""
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n{'='*60}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*60}")


def main():
    """Main entry point"""
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

    runner = BenchmarkRunner()

    # Run all tests
    results = runner.run_all()

    # Save results
    output_dir = Path(__file__).parent.parent.parent
    output_file = output_dir / "benchmark_results_comprehensive.json"
    runner.save_results(output_file)

    # Print summary
    print(f"\n{'='*60}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Pass Rate: {results['summary']['pass_rate']}%")
    print(f"{'='*60}\n")

    # Exit with appropriate code
    sys.exit(0 if results['summary']['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
