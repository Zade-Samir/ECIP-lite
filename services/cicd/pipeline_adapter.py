"""
Pipeline Adapter — Adapters for GitHub Actions, GitLab CI, Jenkins, and Webhooks.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class PipelinePlatform(str, Enum):
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    AZURE_DEVOPS = "azure_devops"
    CIRCLE_CI = "circle_ci"
    WEBHOOK = "webhook"


@dataclass
class PipelinePayload:
    platform: PipelinePlatform
    commit_sha: str
    branch: str
    pull_request_id: Optional[str] = None
    repository: str = "default-repo"


class PipelineAdapter:
    """
    Parses CI/CD payload events and formats pull-request annotations.
    """

    def parse_event(self, platform_str: str, raw_payload: Dict[str, Any]) -> PipelinePayload:
        try:
            platform = PipelinePlatform(platform_str)
            return PipelinePayload(
                platform=platform,
                commit_sha=raw_payload.get("commit_sha", "head"),
                branch=raw_payload.get("branch", "main"),
                pull_request_id=raw_payload.get("pr_id"),
                repository=raw_payload.get("repo", "default"),
            )
        except Exception as e:
            logger.error("Pipeline integration failed")
            raise ValueError(f"Failed to parse pipeline payload: {e}") from e

    def format_pr_annotations(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        annotations = []
        for f in findings:
            annotations.append({
                "path": f.get("file", "unknown"),
                "start_line": f.get("line", 1),
                "annotation_level": "warning" if f.get("severity") != "HIGH" else "failure",
                "message": f.get("message", "Quality issue detected"),
            })
        return annotations
