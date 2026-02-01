from __future__ import annotations
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Dict, Any, Union

from agentfoundry.context.client_state import get_client_context

class ClientContextInput(BaseModel):
    key: str = Field(
        None, 
        description="Optional specific key to retrieve (e.g., 'url', 'page_title'). If omitted, returns all context."
    )

def get_client_ui_context(key: str = None) -> Union[Dict[str, Any], str]:
    """
    Get information about the user's current UI state (web page).
    
    This tool allows the assistant to 'see' what page the user is on, 
    what route is active, and any visible metadata passed by the frontend.
    Use this to understand the user's context when they ask 'What is on this page?' 
    or 'Where am I?'.
    """
    ctx = get_client_context()
    if not ctx:
        return "No client context available. The frontend may not be sending state information."
    
    if key:
        return ctx.get(key, f"Key '{key}' not found in client context.")
    
    return ctx

client_context_tool = StructuredTool.from_function(
    func=get_client_ui_context,
    name="client_context_tool",
    description=get_client_ui_context.__doc__,
    args_schema=ClientContextInput
)
