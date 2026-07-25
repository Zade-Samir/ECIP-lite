"""
Tests for Execution Engine (Prompt 080).
"""
import pytest
from services.approval.approval_manager import ApprovalManager
from services.executor.execution_engine import ExecutionEngine
from services.planner.planner import PlanManifest
from services.task_graph.task_graph import TaskGraph, TaskNode
from services.tool_runtime.tool_runtime import Tool, ToolRuntime


@pytest.fixture
def plan():
    graph = TaskGraph()
    t1 = TaskNode("t1", "tool_a")
    t2 = TaskNode("t2", "tool_b", dependencies={"t1"})
    graph.add_task(t1)
    graph.add_task(t2)
    return PlanManifest(
        goal="Run Workflow",
        task_graph=graph,
        execution_order=["t1", "t2"]
    )


def test_execution_engine_success(plan):
    tr = ToolRuntime()
    tr.register_tool(Tool("tool_a", "A", lambda: "ok_a"))
    tr.register_tool(Tool("tool_b", "B", lambda: "ok_b"))

    ee = ExecutionEngine(tool_runtime=tr)
    res = ee.execute_plan(plan, execution_id="e1")

    assert res["status"] == "success"
    assert res["completed"] == ["t1", "t2"]
    assert "e1" in ee.checkpoints


def test_checkpoint_recovery(plan):
    ee = ExecutionEngine()
    ee.save_checkpoint("e2", ["t1"])

    recovered = ee.restore_checkpoint("e2")
    assert recovered == ["t1"]


def test_execution_failure_rollback(plan):
    tr = ToolRuntime()
    tr.register_tool(Tool("tool_a", "A", lambda: "ok_a"))
    tr.register_tool(Tool("tool_b", "B", lambda: "ok_b"))

    ee = ExecutionEngine(tool_runtime=tr)
    res = ee.execute_plan(plan, execution_id="e3", simulate_tool_failure=True)

    assert res["status"] == "failed"
    assert res["failed_task"] == "t2"
