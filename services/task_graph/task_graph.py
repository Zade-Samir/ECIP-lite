"""
Task Graph — Directed Acyclic Graph (DAG) representation of task dependencies for planning.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TaskNode:
    task_id: str
    name: str
    description: str = ""
    dependencies: Set[str] = field(default_factory=set)
    estimated_cost: float = 1.0


class TaskGraph:
    """
    DAG tracking task dependencies and calculating execution order.
    """

    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}

    def add_task(self, task: TaskNode) -> None:
        self.nodes[task.task_id] = task

    def get_execution_order(self) -> List[str]:
        # Detect cycles using Kahn's algorithm or DFS
        in_degree = {t_id: 0 for t_id in self.nodes}
        graph = {t_id: [] for t_id in self.nodes}

        for t_id, node in self.nodes.items():
            for dep_id in node.dependencies:
                if dep_id in self.nodes:
                    graph[dep_id].append(t_id)
                    in_degree[t_id] += 1
                else:
                    logger.warning("Missing dependency")

        queue = [t_id for t_id, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            node_id = queue.pop(0)
            order.append(node_id)
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.nodes):
            logger.error("Circular dependency")
            logger.error("Planning failed")
            raise ValueError("Circular dependency detected in task graph")

        return order
