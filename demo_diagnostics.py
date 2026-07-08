import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from ecip_core.diagnostics.service import DiagnosticsService
from ecip_core.workspace.manager import workspace_manager
from ecip_core.storage.sqlite.database import Database
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile


def run_demo():
    print("======================================================================")
    print("⚡ Starting ECIP Lite Project Health & Diagnostics Demo")
    print("======================================================================\n")

    # Step 1: Initialize service
    service = DiagnosticsService()

    # Step 2: Run diagnostics on a clean healthy workspace
    print("1. Running diagnostics on the active workspace...")
    report = service.run_diagnostics()
    
    print(f"\nReport Overall Status: {report.overall_status.upper()}")
    print(f"Execution Latency:     {report.execution_time_ms:.2f} ms")
    print("\nChecks Passed:")
    for check in report.checks_passed:
        print(f"  ✅ {check}")

    print("\nRecommendations:")
    if report.recommendations:
        for rec in report.recommendations:
            print(f"  💡 {rec}")
    else:
        print("  None (Workspace is healthy!)")

    # Step 3: Verify JSON Export
    print("\n2. Exporting health report to JSON format:")
    json_report = report.model_dump_json(indent=2)
    print(json_report)

    # Step 4: Simulate a degraded workspace condition
    print("\n3. Simulating a degraded state (registering non-existent source file)...")
    workspace_manager.register_workspace("test_proj", "Test Project", "projects/non_existent_folder_abc")
    workspace_manager.set_active_workspace("test_proj")
    
    # Save a file in DB metadata that does not exist on disk
    repo = JavaRepository()
    file_dummy = ParsedJavaFile(
        file_name="MissingService.java",
        file_path="projects/non_existent_folder_abc/MissingService.java",
        package_name="com.test",
        class_name="MissingService",
        methods=[]
    )
    repo.save(file_dummy, file_hash="hash_missing")
    print("   Inserted metadata for 'MissingService.java' (File does not exist on disk).")

    # Step 5: Re-run diagnostics to verify detection
    print("\n4. Running diagnostics on the degraded workspace...")
    degraded_report = service.run_diagnostics()

    print(f"\nReport Overall Status: {degraded_report.overall_status.upper()}")
    print("\nErrors Detected:")
    for err in degraded_report.errors:
        print(f"  ❌ {err}")
    print("\nWarnings Detected:")
    for warn in degraded_report.warnings:
        print(f"  ⚠️ {warn}")
    print("\nRecommendations:")
    for rec in degraded_report.recommendations:
        print(f"  💡 {rec}")

    # Clean up test workspace
    workspace_manager.set_active_workspace("default")
    workspace_manager.delete_workspace("test_proj")

    print("\n======================================================================")
    print("🎉 Diagnostics Demo complete! Project health validation verified.")
    print("======================================================================")


if __name__ == "__main__":
    run_demo()
