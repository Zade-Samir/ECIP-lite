"""
Tests for Task Graph (Prompt 079).
"""
import pytest
from services.task_graph.task_graph import TaskGraph, TaskNode


def test_topological_sort_order():
    graph = TaskGraph()
    t1 = TaskNode("t1", "Index Codebase")
    t2 = TaskNode("t2", "Build AST Graph", dependencies={"t1"})
    t3 = TaskNode("t3", "Run Retrieval Query", dependencies={"t2"})

    graph.add_task(t3)
    graph.add_task(t2)
    graph.add_task(t1)

    order = graph.get_execution_order()
    assert order == ["t1", "t2", "t3"]


def test_circular_dependency_detection():
    graph = TaskGraph()
    t1 = TaskNode("t1", "Task 1", dependencies={"t2"})
    t2 = TaskNode("t2", "Task 2", dependencies={"t1"})

    graph.add_task(t1)
    graph.add_task(t2)

    with pytest.raises(ValueError, match="Circular dependency"):
        graph.get_execution_order()
