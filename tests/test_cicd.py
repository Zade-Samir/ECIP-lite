"""
Tests for CI/CD Adapter (Prompt 088).
"""
import pytest
from services.cicd.pipeline_adapter import PipelineAdapter, PipelinePlatform


def test_pipeline_adapter_parse():
    adapter = PipelineAdapter()
    payload = adapter.parse_event("github_actions", {"commit_sha": "abc1234", "branch": "feature/1", "repo": "myrepo"})
    assert payload.platform == PipelinePlatform.GITHUB_ACTIONS
    assert payload.commit_sha == "abc1234"


def test_format_pr_annotations():
    adapter = PipelineAdapter()
    findings = [{"file": "App.java", "line": 42, "severity": "HIGH", "message": "SQL Injection pattern"}]
    annotations = adapter.format_pr_annotations(findings)
    assert len(annotations) == 1
    assert annotations[0]["annotation_level"] == "failure"
