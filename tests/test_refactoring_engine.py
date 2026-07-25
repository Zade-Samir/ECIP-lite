"""
Tests for Refactoring Engine (Prompt 086).
"""
import pytest
from services.refactoring.refactoring_engine import RefactoringEngine
from services.refactoring.source_rewriter import CodeTransformation


def test_dry_run_refactoring():
    engine = RefactoringEngine()
    t = CodeTransformation(
        transform_type="IMPORT_CLEANUP",
        target_file="src/Main.java",
        original_code="import java.util.Date;\n",
        target_pattern="java.util.Date",
        replacement_pattern="java.time.Instant",
    )

    res = engine.execute_refactoring(t, dry_run=True)
    assert res.status == "success"
    assert res.dry_run is True
    assert "java.time.Instant" in res.diff


def test_refactoring_validation_failure_and_rollback():
    engine = RefactoringEngine()
    t = CodeTransformation(
        transform_type="DEPRECATED_API_REPLACEMENT",
        target_file="src/App.java",
        original_code="oldMethod();",
        target_pattern="oldMethod",
        replacement_pattern="newMethod",
    )

    res = engine.execute_refactoring(t, dry_run=False, simulate_validation_failure=True)
    assert res.status == "failed"
    assert "src/App.java" in engine.backups
