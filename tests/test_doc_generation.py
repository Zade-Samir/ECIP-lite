"""
Tests for Doc Generation (Prompt 095).
"""
import pytest
from services.documentation.documentation_engine import DocumentationEngine


def test_stale_doc_detection():
    de = DocumentationEngine()
    is_stale = de.check_stale_docs(last_modified_doc=100.0, last_modified_code=150.0)
    assert is_stale is True
