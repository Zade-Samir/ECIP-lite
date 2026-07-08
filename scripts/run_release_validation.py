import os
import sys
import json
import time
import unittest
from pathlib import Path

# Add project root directory to path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


class ReleaseValidationRunner:
    """
    Automated pre-release gate validation suite.
    Runs all tests, measures duration, formats terminal summaries,
    writes JSON reports, and manages exit statuses.
    """

    def __init__(self):
        self.report_path = PROJECT_ROOT / "release_validation_report.json"

    def run(self) -> int:
        print("======================================================================")
        print("🚀 Starting ECIP Lite Pre-Release Gating Validation Suite")
        print("======================================================================\n")

        start_time = time.perf_counter()

        # Discover tests under the tests/ directory
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=str(PROJECT_ROOT / "tests"), pattern="test_*.py")

        # Run tests collecting structured output
        result = unittest.TestResult()
        suite.run(result)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Calculate statistics
        total = result.testsRun
        errors = len(result.errors)
        failures = len(result.failures)
        passed = total - (errors + failures)

        status = "passed" if (errors == 0 and failures == 0) else "failed"

        # Prepare failing test details
        failed_list = []
        for test, tb in result.failures + result.errors:
            failed_list.append(f"{test.id()}: {tb.splitlines()[-1] if tb else 'Unknown error'}")

        # Human-Readable Terminal Summary Report
        print("\n======================================================================")
        print("📋 Pre-Release Validation Summary Report")
        print("======================================================================")
        print(f"Overall Status:   {status.upper()}")
        print(f"Total Tests Run:  {total}")
        print(f"Passed:           {passed} ✅")
        print(f"Failures:         {failures} ❌")
        print(f"Errors:           {errors} ⚠️")
        print(f"Duration:         {duration:.2f} seconds")
        print("======================================================================\n")

        if failed_list:
            print("❌ Failing Test Details:")
            for fail in failed_list:
                print(f"  - {fail}")
            print("\n======================================================================")

        # Machine-Readable JSON Report
        report_data = {
            "status": status,
            "total_tests": total,
            "passed_count": passed,
            "failed_count": failures,
            "error_count": errors,
            "duration_seconds": round(duration, 4),
            "failed_tests_details": failed_list
        }

        try:
            with open(self.report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)
            print(f"💾 Report saved successfully to: {self.report_path}")
        except Exception as e:
            print(f"⚠️ Failed to write report: {e}")

        # Return exit code (0 if passed, 1 if failed)
        return 0 if status == "passed" else 1


if __name__ == "__main__":
    runner = ReleaseValidationRunner()
    exit_code = runner.run()
    sys.exit(exit_code)
