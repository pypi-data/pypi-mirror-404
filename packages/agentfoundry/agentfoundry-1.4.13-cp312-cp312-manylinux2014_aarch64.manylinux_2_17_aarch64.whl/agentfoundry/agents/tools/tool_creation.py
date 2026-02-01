
"""Dynamic Python Tool Creation utility.

Allows an agent to submit Python source code that defines a new LangChain
``Tool``/``StructuredTool``.  The code is executed in a sandbox namespace
and, if successful, the tool is registered so it becomes immediately
invocable by the agent graph.
"""

from __future__ import annotations

import re
import traceback
from typing import Any
from agentfoundry.agents.tools.dynamic_invoker_tool import register_tool
import traceback
import re
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool, Tool


class _ToolCreateInput(BaseModel):
    """Input schema for the postgres_query_executor tool."""
    name: str = Field(..., description="The Tool name")
    code: str = Field(..., description="The Python source code defining one Tool instance")


def create_python_tool(
        name: str,
        code: str
) -> str:
    """
    Expects a JSON string with keys:
      - 'name': the Tool name
      - 'code': the Python source defining one Tool instance
    It will exec() the code, extract the Tool, and call register_tool().
    """
    # strip triple‐backtick fencing if present
    match = re.search(r"```(?:python)?\s*([\s\S]*?)```", code)
    code = match.group(1) if match else code


def _create_python_tool(name: str, code: str) -> str:  # noqa: D401
    # Remove ``` fencing if present
    match = re.search(r"```(?:python)?\s*([\s\S]*?)```", code)
    code_body = match.group(1) if match else code

    ns: dict[str, Any] = {}
    try:
        exec(code_body, ns)
    except Exception as exc:
        return f"Error executing code for {name}:\n{traceback.format_exc()}"

    tool_objs = [v for v in ns.values() if isinstance(v, (Tool, StructuredTool))]
    if not tool_objs:
        return "No Tool or StructuredTool instance found in the provided code."

    new_tool = tool_objs[0]
    register_tool(new_tool.name, new_tool.func, new_tool.description)
    return f"Registered new dynamic tool: {new_tool.name}"


tool_creation = StructuredTool(
    name="python_tool_creator",
    func=_create_python_tool,
    description=(
        "Register a new Python-based Tool for an Agentic AI. "
        "Input must be a JSON string with two keys:\n"
        "  • name: the unique identifier for the new tool\n"
        "  • code: the full Python source defining exactly one Tool instance, "
        "including all required imports (e.g. `from langchain_core.tools import Tool, StructuredTool`).\n"
        "The code should end by assigning a `Tool(...)` to a variable. "
        "If your tool requires multiple parameters, wrap them into a single JSON `args` object. "
        "Be mindful of quotes and f-strings, and ensure the code is safe—this tool will execute it directly."
    ),

    args_schema=_ToolCreateInput,
)
