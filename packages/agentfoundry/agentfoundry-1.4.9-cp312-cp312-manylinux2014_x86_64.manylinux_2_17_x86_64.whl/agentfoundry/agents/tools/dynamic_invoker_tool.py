"""Runtime registration and invocation of user-generated tools."""

from __future__ import annotations
import json
from typing import Any, Callable, Dict, Optional
from langchain_core.tools import StructuredTool, Tool
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# In-memory registry
# ---------------------------------------------------------------------------

dynamic_registry: Dict[str, Tool] = {}
dynamic_info: Dict[str, str] = {}


def register_tool(name: str, func: Callable[..., Any], description: str) -> None:
    """Register *func* under *name* so it can be invoked dynamically."""
    dynamic_registry[name] = Tool(name=name, func=func, description=description)
    dynamic_info[name] = description


# ---------------------------------------------------------------------------
# Tool to list all registered dynamic tools
# ---------------------------------------------------------------------------


def _dynamic_tool_lister(_tool_input: Any | None = None, **_: Any) -> str:  # noqa: D401 – simple utility
    return json.dumps(dynamic_info)


# ---------------------------------------------------------------------------
# Structured invocation tool
# ---------------------------------------------------------------------------


class _InvokeSchema(BaseModel):
    tool_name: str = Field(..., description="Name of the registered tool to call")
    args: Optional[dict] = Field(None, description="Dictionary of arguments for the tool")


def _dynamic_execute(tool_name: str, args: Optional[dict] = None) -> Any:  # noqa: D401
    if tool_name not in dynamic_registry:
        return f"Tool '{tool_name}' not found. Call user_generated_tool_lister to see available tools."

    tool = dynamic_registry[tool_name]
    try:
        return tool.func(**(args or {}))
    except Exception as exc:  # pragma: no cover – runtime tool errors
        return f"Error executing tool '{tool_name}': {exc}"


dynamic_invoker = StructuredTool(
    name="user_generated_tool_invoker",
    description=(
        "Call any user-generated tool by specifying 'tool_name' and an optional 'args' dictionary."
    ),
    func=_dynamic_execute,
    args_schema=_InvokeSchema,
)

dynamic_lister = Tool(
    name="user_generated_tool_lister",
    func=_dynamic_tool_lister,
    description="Returns a JSON mapping of dynamically registered tool names to their descriptions.",
)
