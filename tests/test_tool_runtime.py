"""
Tests for Tool Runtime (Prompt 080).
"""
import pytest
from services.tool_runtime.tool_runtime import Tool, ToolRuntime


def test_tool_registration_and_execution():
    tr = ToolRuntime()
    called = []

    def mock_fn(x, y):
        called.append(x + y)
        return x + y

    tool = Tool(name="add", description="Add numbers", fn=mock_fn)
    tr.register_tool(tool)

    res = tr.execute_tool("add", 10, 20)
    assert res == 30
    assert called == [30]


def test_tool_execution_failure():
    tr = ToolRuntime()

    def bad_fn():
        raise ValueError("Tool internal error")

    tr.register_tool(Tool(name="bad", description="Bad", fn=bad_fn))

    with pytest.raises(RuntimeError):
        tr.execute_tool("bad")
