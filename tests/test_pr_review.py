"""
Tests for PR Review (Prompt 092).
"""
import pytest
from services.code_review.review_engine import ReviewEngine


def test_pr_review_security_issue():
    engine = ReviewEngine()
    diff = """--- a/src/Exec.java
+++ b/src/Exec.java
@@ -5,2 +5,3 @@
+eval(userInput);
"""

    res = engine.review_diff(diff)
    assert res["status"] == "CHANGES_REQUESTED"
    assert res["comments"][0]["severity"] == "HIGH"
