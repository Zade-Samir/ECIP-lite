"""
Tests for Documentation Assistant (Prompt 095).
"""
import pytest
from services.documentation.documentation_engine import DocumentationEngine


def test_generate_api_doc():
    de = DocumentationEngine()
    endpoints = [
        {"method": "GET", "path": "/api/users", "description": "Get user list"},
        {"method": "POST", "path": "/api/users", "description": "Create user"},
    ]

    doc = de.generate_api_doc("User Service", endpoints)
    assert doc.doc_type == "API_REFERENCE"
    assert "`GET /api/users`" in doc.markdown_content
    assert doc.quality_score > 90.0
