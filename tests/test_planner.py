"""
Tests for Task Planner (Prompt 079).
"""
import pytest
from services.planner.planner import TaskPlanner
from services.task_graph.task_graph import TaskNode


def test_generate_and_validate_plan():
    planner = TaskPlanner()
    tasks = [
        TaskNode("step1", "Scan workspace"),
        TaskNode("step2", "Extract dependencies", dependencies={"step1"}),
    ]

    manifest = planner.generate_plan("Refactor User Module", tasks)
    assert manifest.execution_order == ["step1", "step2"]

    valid = planner.validate_plan(manifest)
    assert valid is True


def test_validate_plan_missing_dependency():
    planner = TaskPlanner()
    tasks = [
        TaskNode("step1", "Task 1", dependencies={"nonexistent_step"}),
    ]
    manifest = planner.generate_plan("Goal X", tasks)
    assert planner.validate_plan(manifest) is False
