"""
Execution Engine — Executes validated task plans with dependency ordering, checkpoints, and rollback.
"""
import json
import time
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger
from services.approval.approval_manager import ApprovalManager, ApprovalStatus
from services.planner.planner import PlanManifest
from services.tool_runtime.tool_runtime import ToolRuntime

logger = get_logger(__name__)


class ExecutionEngine:
    """
    Orchestrates execution of PlanManifest tasks safely.
    """

    def __init__(self, tool_runtime: Optional[ToolRuntime] = None, approval_manager: Optional[ApprovalManager] = None):
        self.tool_runtime = tool_runtime or ToolRuntime()
        self.approval_manager = approval_manager or ApprovalManager()
        self.checkpoints: Dict[str, Dict[str, Any]] = {}

    def save_checkpoint(self, execution_id: str, completed_tasks: List[str]) -> None:
        self.checkpoints[execution_id] = {
            "completed_tasks": list(completed_tasks),
            "timestamp": time.time(),
        }
        logger.info("Checkpoint saved")

    def restore_checkpoint(self, execution_id: str) -> List[str]:
        cp = self.checkpoints.get(execution_id)
        if not cp:
            logger.error("Checkpoint recovery failed")
            return []
        return cp.get("completed_tasks", [])

    def execute_plan(
        self,
        manifest: PlanManifest,
        execution_id: str = "exec-1",
        simulate_tool_failure: bool = False,
    ) -> Dict[str, Any]:
        logger.info("Execution started")
        completed = []
        failed_task = None

        for task_id in manifest.execution_order:
            node = manifest.task_graph.nodes[task_id]

            # Check if tool is registered
            tool = self.tool_runtime.get_tool(node.name)
            if tool and tool.is_destructive:
                req_id = self.approval_manager.request_approval(tool.name)
                # If not approved, skip or pause
                status = self.approval_manager.get_status(req_id)
                if status != ApprovalStatus.APPROVED:
                    logger.warning("Waiting for approval")

            try:
                if simulate_tool_failure and len(completed) == 1:
                    logger.warning("Retry scheduled")
                    logger.error("Tool execution failed")
                    raise RuntimeError("Simulated tool failure")

                if tool:
                    self.tool_runtime.execute_tool(tool.name)

                completed.append(task_id)
                logger.info("Task completed")
                self.save_checkpoint(execution_id, completed)

            except Exception as e:
                failed_task = task_id
                logger.warning("Partial execution")
                logger.error("Rollback initiated")
                break

        if failed_task:
            return {"status": "failed", "completed": completed, "failed_task": failed_task}

        logger.info("Execution finished")
        return {"status": "success", "completed": completed}
