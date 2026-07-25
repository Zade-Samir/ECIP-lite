"""
Tests for Code Transforms (Prompt 086).
"""
import pytest
from services.refactoring.source_rewriter import CodeTransformation, SourceRewriter


def test_code_transform_diff_generation():
    rewriter = SourceRewriter()
    t = CodeTransformation(
        transform_type="PACKAGE_RENAME",
        target_file="src/User.java",
        original_code="import javax.persistence.Entity;\n",
        target_pattern="javax.persistence",
        replacement_pattern="jakarta.persistence",
    )

    new_code, diff = rewriter.apply_transform(t)
    assert "jakarta.persistence" in new_code
    assert "-import javax.persistence.Entity;" in diff
    assert "+import jakarta.persistence.Entity;" in diff
