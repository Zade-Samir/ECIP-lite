"""
Autonomous Task Planner — Decomposes high-level goals into DAG task manifests.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger
from services.task_graph.task_graph import TaskGraph, TaskNode

logger = get_logger(__name__)


@dataclass
class PlanManifest:
    goal: str
    task_graph: TaskGraph
    execution_order: List[str]
    total_cost: float = 0.0


class TaskPlanner:
    """
    Decomposes user objectives into valid task plans with execution ordering.
    """

    def analyze_goal(self, goal: str) -> Dict[str, Any]:
        if not goal or len(goal.strip()) < 5:
            logger.warning("Ambiguous objective")

        logger.info("Goal analyzed")
        return {"goal": goal, "is_complex": len(goal) > 30}

    def generate_plan(self, goal: str, tasks: List[TaskNode]) -> PlanManifest:
        self.analyze_goal(goal)
        graph = TaskGraph()

        for t in tasks:
            graph.add_task(t)

        try:
            exec_order = graph.get_execution_order()
            total_cost = sum(t.estimated_cost for t in tasks)
            manifest = PlanManifest(
                goal=goal,
                task_graph=graph,
                execution_order=exec_order,
                total_cost=total_cost,
            )
            logger.info("Plan generated")
            return manifest
        except Exception as e:
            logger.error("Planning failed")
            raise e

    def validate_plan(self, manifest: PlanManifest) -> bool:
        if not manifest.execution_order:
            logger.error("Validation error")
            return False

        for task_id in manifest.execution_order:
            node = manifest.task_graph.nodes.get(task_id)
            if not node:
                logger.error("Validation error")
                return False

            for dep in node.dependencies:
                if dep not in manifest.task_graph.nodes:
                    logger.warning("Missing dependency")
                    logger.error("Validation error")
                    return False

        logger.info("Validation passed")
        return True
