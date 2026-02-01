from __future__ import annotations

import datetime
import os
import platform
import logging
from pathlib import Path
from typing import Dict, List, Optional
import toml

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from agentfoundry.utils.agent_config import AgentConfig
from agentfoundry.registry.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class SystemIntrospectionInput(BaseModel):
    action: str = Field(
        ..., 
        description=(
            "Action to perform. Options:\n"
            "- 'app_info': Get application name, version, and description.\n"
            "- 'system_context': Get current time, OS, and environment info.\n"
            "- 'list_tools': List all available tools and their descriptions.\n"
            "- 'list_docs': List available documentation files.\n"
            "- 'read_doc': Read a specific documentation file (requires 'target').\n"
            "- 'agent_config': Get the current agent configuration (sanitized)."
        )
    )
    target: Optional[str] = Field(
        None, 
        description="Target for the action (e.g., filename for 'read_doc')."
    )

def system_introspection(action: str, target: Optional[str] = None) -> Dict[str, object]:
    """
    Introspect the system, application, and agent state. 
    Allows the agent to understand its own environment, capabilities, and configuration.
    """
    logger.info(f"SystemIntrospection called with action='{action}', target='{target}'")
    
    root_dir = Path.cwd()
    
    try:
        if action == "app_info":
            info = {}
            # PyProject.toml
            pyproject_path = root_dir / "pyproject.toml"
            if pyproject_path.exists():
                try:
                    data = toml.load(pyproject_path)
                    project = data.get("project", {})
                    info["name"] = project.get("name")
                    info["version"] = project.get("version", "dynamic")
                    info["description"] = project.get("description")
                except Exception as e:
                    logger.warning(f"Failed to parse pyproject.toml: {e}")
                    info["error_pyproject"] = str(e)
            
            # README.md
            readme_path = root_dir / "README.md"
            if readme_path.exists():
                # Read first 1kb to get the gist
                info["readme_snippet"] = readme_path.read_text(encoding="utf-8")[:1000]
            
            return info

        elif action == "system_context":
            return {
                "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": str(datetime.datetime.now().astimezone().tzinfo),
                "os": platform.system(),
                "os_release": platform.release(),
                "python_version": platform.python_version(),
                "user": os.getenv("USER", "unknown"),
                "cwd": str(root_dir)
            }

        elif action == "list_tools":
            # Access the singleton registry
            try:
                registry = ToolRegistry.get_instance()
                # If not initialized, it might return an empty registry depending on how it's used.
                # But typically in a running agent, it should be populated.
                # If we are running this tool *from* an agent, the registry should be active.
                tools_map = registry._tools
                return {
                    "count": len(tools_map),
                    "tools": {name: tool.description for name, tool in tools_map.items()}
                }
            except Exception as e:
                return {"error": f"Failed to access ToolRegistry: {str(e)}"}

        elif action == "list_docs":
            docs_dir = root_dir / "docs"
            if not docs_dir.exists():
                return {"error": "docs directory not found"}
            
            files = [f.name for f in docs_dir.iterdir() if f.is_file()]
            return {"docs": sorted(files)}

        elif action == "read_doc":
            if not target:
                return {"error": "Action 'read_doc' requires 'target' parameter."}
            
            docs_dir = root_dir / "docs"
            doc_path = docs_dir / target
            
            # Security check: prevent directory traversal
            try:
                doc_path = doc_path.resolve()
                if not str(doc_path).startswith(str(docs_dir.resolve())):
                     return {"error": "Access denied: Target must be within docs directory."}
            except Exception as e:
                return {"error": f"Path resolution error: {e}"}

            if not doc_path.exists():
                 return {"error": f"Document not found: {target}"}
            
            return {"content": doc_path.read_text(encoding="utf-8")}

        elif action == "agent_config":
            # Attempt to load or access config
            try:
                # We try to load it fresh or get the singleton if we could.
                # Config is often passed around, but we can try loading from default path or env.
                # AgentConfig.load() isn't a standard method based on the snippet I saw, 
                # but let's try instantiating with defaults or seeing what we can get.
                # Actually, best effort is to load from standard locations if we can't get the running instance.
                # However, for this tool, let's just return what we can find in env vars or basic settings.
                
                # If we are inside the running app, we might check if AgentConfig has a singleton accessor?
                # The snippets showed `AgentConfig` usage but not a global singleton accessor explicitly.
                # But `from agentfoundry.utils.agent_config import AgentConfig` was used.
                
                # Let's return a subset of env vars related to the agent
                env_config = {k: v for k, v in os.environ.items() if k.startswith("AGENT_") or k.startswith("OPENAI_")}
                # Sanitize
                for k in env_config:
                    if "KEY" in k or "SECRET" in k or "PASSWORD" in k:
                        env_config[k] = "***REDACTED***"
                
                return {"environment_config": env_config}

            except Exception as e:
                return {"error": f"Failed to retrieve config: {e}"}

        else:
            return {"error": f"Unknown action: {action}"}

    except Exception as e:
        logger.error(f"Error in system_introspection: {e}", exc_info=True)
        return {"error": str(e)}


system_introspection_tool = StructuredTool.from_function(
    func=system_introspection,
    name="system_introspection",
    description=system_introspection.__doc__,
    args_schema=SystemIntrospectionInput,
)
