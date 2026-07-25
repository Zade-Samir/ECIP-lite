"""
Tests for Review Engine (Prompt 092).
"""
import pytest
from services.code_review.review_engine import ReviewEngine


def test_code_review_findings():
    engine = ReviewEngine()
    diff = """--- a/src/App.java
+++ b/src/App.java
@@ -10,3 +10,4 @@
+System.out.println("Debug log");
"""

    res = engine.review_diff(diff)
    assert res["total_comments"] == 1
    assert res["comments"][0]["category"] == "Quality"
    assert res["status"] == "APPROVED"
