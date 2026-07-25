"""
Tool Runtime — Registry and invoker for agent execution tools.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., Any]
    is_destructive: bool = False


class ToolRuntime:
    """
    Registry for tools available to autonomous execution agents.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def execute_tool(self, name: str, *args, **kwargs) -> Any:
        tool = self._tools.get(name)
        if not tool:
            logger.error("Tool execution failed")
            raise ValueError(f"Tool {name} not found")

        try:
            return tool.fn(*args, **kwargs)
        except Exception as e:
            logger.error("Tool execution failed")
            raise RuntimeError(f"Tool {name} execution failed: {e}") from e
