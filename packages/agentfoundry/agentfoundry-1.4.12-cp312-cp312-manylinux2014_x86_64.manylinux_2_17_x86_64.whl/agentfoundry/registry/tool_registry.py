import importlib
import importlib.util
import logging
import os
import sys
import warnings
from importlib.util import find_spec as _find_spec
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from langchain.agents import create_agent  # type: ignore
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool, Tool

from agentfoundry.utils.agent_config import AgentConfig


class ToolRegistry:
    """
    Registry to store and manage LangChain tools with unique names.

    Can be used as a singleton (backward compatible) or instantiated with explicit config.
    """

    _instance: "ToolRegistry | None" = None
    _initialised: bool = False

    def __new__(cls, config: AgentConfig = None):
        # For backward compatibility, return singleton if no config provided
        if config is None:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
        # With explicit config, create new instance (not singleton)
        return super().__new__(cls)

    def __init__(self, config: AgentConfig = None):
        # Handle singleton case - avoid re-init
        if config is None and self.__class__._initialised:
            return
        
        # Handle backward compatibility
        if config is None:
            warnings.warn(
                "ToolRegistry() without config is deprecated. "
                "Pass AgentConfig explicitly.",
                DeprecationWarning,
                stacklevel=2
            )
            config = AgentConfig.from_legacy_config()
        
        self.config = config
        self.logger = getLogger(__name__)
        self._tools: Dict[str, Tool] = {}
        
        if config is None:
            self.__class__._initialised = True

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        """Explicit accessor for the singleton instance (optional to use)."""
        return cls()

    def register_tool(self, tool: Tool | StructuredTool) -> None:
        """
        Registers a LangChain tool instance with validation.

        Args:
            tool (Tool): A LangChain Tool instance.
        """
        if not hasattr(tool, 'name'):
            tool.name = tool.__name__
            self.logger.error(f"Tool name set to default: {tool.__name__}")
        if (not hasattr(tool, 'description') or not isinstance(tool.description, str)
                or not tool.description or not tool.description.strip()):
            doc = tool.__doc__ if tool.__doc__ and tool.__doc__.strip() else "No description provided."
            tool.description = doc
            if not tool.__doc__ or not tool.__doc__.strip():
                tool.__doc__ = doc
            self.logger.warning(f"Tool '{tool.name}' has invalid or missing 'description' field. Using default description: {tool.description}")

        if tool.name in self._tools:
            self.logger.debug(f"Tool with name '{tool.name}' is already registered. Overriding.")

        self._tools[tool.name] = tool
        self.logger.debug(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Retrieve a registered tool by its name.

        Args:
            name (str): The tool name.

        Returns:
            Tool or None: The registered tool if found, else None.
        """
        return self._tools.get(name)

    def get_tools_by_names(self, names: List[str]) -> List[Tool]:
        """
        Retrieve a list of tools by their names. Ignores names that are not found.

        Args:
            names (List[str]): List of tool names to retrieve.

        Returns:
            List[Tool]: List of found Tool objects.
        """
        tools = []
        for name in names:
            tool = self._tools.get(name)
            if tool:
                tools.append(tool)
            else:
                self.logger.warning(f"Requested tool '{name}' not found in registry.")
        return tools

    def list_tools(self) -> List[str]:
        """
        List the names of all registered tools.

        Returns:
            List[str]: A list of tool names.
        """
        return list(self._tools.keys())

    def inspect_tools(self, *args, **kwargs) -> str:
        """
        Generate a formatted string listing all available tools with descriptions.

        Args:
            *args: Variable positional arguments (ignored if passed).
            **kwargs: Variable keyword arguments (ignored if passed).

        Returns:
            str: A formatted summary of registered tools.
        """
        if args:
            self.logger.warning(f"Received unexpected positional arguments in inspect_tools: {args}")
        if kwargs:
            self.logger.warning(f"Received unexpected arguments in inspect_tools: {kwargs}")
        if not self._tools:
            return "No tools are currently registered."
        self.logger.info(f"Inspecting tools, count: {len(self._tools)}")
        return "\n".join(f"{tool.name}: {tool.description}" for tool in self._tools.values())

    def as_langchain_tools(self) -> List[Tool]:
        """
        Returns all registered tools as a list of LangChain Tool instances.

        Returns:
            List[Tool]: A list of registered LangChain tools.
        """
        return list(self._tools.values())

    def load_tools_from_directory(
        self,
        directories: Optional[Union[str, Sequence[str]]] = None,
    ) -> None:
        """
        Load tools in several locations, in order:
          1) the built-in AgentFoundry shipped agents/tools directory;
          2) any application-provided static directories (one or more custom paths);
          3) (fallback) the configured TOOLS_DIR value from config.

        Args:
            directories (str or sequence of str, optional):
                One or more custom tool directories. If provided, these override
                the configured TOOLS_DIR; otherwise, looks for a TOOLS_DIR list in config,
                then falls back to TOOLS_DIR.
        """
        # 1) Load tools shipped with AgentFoundry itself
        shipped_tools_dir = os.path.join(
            os.path.dirname(__file__), '..', 'agents', 'tools'
        )
        self.logger.info(f"Loading shipped tools from: {shipped_tools_dir}")
        self._load_tools_from_single_directory(shipped_tools_dir, 'agentfoundry.agents.tools')

        # Determine custom static tool directories: explicit param or config TOOLS_DIR
        custom_dirs = directories
        if custom_dirs is None and self.config and self.config.tools_dir:
            custom_dirs = str(self.config.tools_dir)

        # Normalize to list
        if isinstance(custom_dirs, str):
            custom_dirs = [custom_dirs]

        # 2) Load from application-provided directories, if any
        if custom_dirs:
            for path in custom_dirs:
                self.logger.info(f"Loading tools from custom directory: {path}")
                self._load_tools_from_single_directory(path, None)
        elif self.config and self.config.tools_dir:
            # 3) Fallback to config TOOLS_DIR
            tools_dir = str(self.config.tools_dir)
            self.logger.info(f"Loading tools from configured TOOLS_DIR: {tools_dir}")
            self._load_tools_from_single_directory(tools_dir, None)

    def _load_tools_from_single_directory(self, tools_dir: str, module_prefix: Optional[str]) -> None:
        """
        A function to load tools from a single directory into the registry.

        Args:
            tools_dir (str): Directory containing tool modules.
            module_prefix (str, optional): Module prefix for import (e.g., 'agentfoundry.agents.tools'). None for absolute paths.
        """
        if not tools_dir:
            self.logger.warning("Tools directory is not configured (None). Skipping loading custom tools.")
            return

        if not os.path.isdir(tools_dir):
            self.logger.warning(f"Tools directory does not exist or is not a directory: {tools_dir}")
            try:
                os.makedirs(tools_dir, exist_ok=True)
                self.logger.info(f"Created tools directory: {tools_dir}")
            except Exception as e:
                self.logger.warning(f"Could not create tools directory {tools_dir}: {e}")
            return

        self.logger.info(f"Loading tools from directory: {tools_dir}")

        import re

        # Map tool modules to their required importable packages. If any are
        # missing, the tool is auto-disabled and skipped with a warning.
        REQUIRED_TOOL_DEPS: dict[str, list[str]] = {
            # cloud / databases
            "aws_cli_tool": ["awscli"],
            "postgres_tool": ["psycopg2"],
            "sql_server_query": ["pyodbc"],
            # data / docs
            "pandas_explorer": ["pandas"],
            "pdf_creator": ["markdown"],
        }
        for filename in os.listdir(tools_dir):
            if filename.startswith("__"):
                continue
            # Support Python source (.py) or compiled extension (.so, .pyd) modules
            if filename.endswith(".py"):
                tool_name = filename[:-3]
            # else:
                m = re.match(r"^(?P<name>.+?)(?:\..+)?\.(?:so|pyd|py)$", filename)  # including py for now
                if not m:
                    continue
                tool_name = m.group("name")
                if module_prefix:
                    full_module_name = f"{module_prefix}.{tool_name}"
                else:
                    # For DATA_DIR, use an absolute path
                    module_path = os.path.join(tools_dir, filename)
                    spec = importlib.util.spec_from_file_location(tool_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    if spec.loader is None:
                        self.logger.error(f"Loader missing for tool module {module_path}; skipping")
                        continue
                    sys.modules[spec.name] = module  # Ensure module is discoverable during class decoration
                    spec.loader.exec_module(module)
                    full_module_name = tool_name

                # Enforce per-tool optional dependency checks before import
                missing: list[str] = []
                for dep in REQUIRED_TOOL_DEPS.get(tool_name, []):
                    if _find_spec(dep) is None:
                        missing.append(dep)
                if missing:
                    self.logger.warning(
                        f"Skipping tool '{tool_name}' due to missing deps: {', '.join(missing)}"
                    )
                    continue

                self.logger.debug(f"Loading tool from file: {filename}")
                # Be lenient with optional tool dependencies: if a module is missing,
                # log a warning and skip instead of emitting a scary traceback.
                try:
                    module = (
                        importlib.import_module(full_module_name)
                        if module_prefix
                        else module
                    )
                except (ModuleNotFoundError, ImportError) as e:
                    self.logger.warning(
                        f"Failed to load optional tool module {full_module_name}: {e}"
                    )
                    module = None
                except Exception as e:
                    # Unexpected import error – include traceback for debugging
                    self.logger.error(
                        f"Failed to load tool module {full_module_name}: {e}",
                        exc_info=True,
                    )
                    module = None
                if not module:
                    continue
                self.logger.debug(f"Loaded module: {full_module_name}")
                tools_found = False
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, (Tool, StructuredTool)):
                        if "name" not in attr.__dict__ or "description" not in attr.__dict__:
                            self.logger.warning(
                                f"Tool {attr_name} missing 'name' or 'description'; skipping"
                            )
                            continue
                        self.register_tool(attr)
                        tools_found = True
                if not tools_found:
                    self.logger.info(f"No valid Tool instances found in {full_module_name}")

    def as_langchain_registry_tool(self):
        """
        Returns the registry as a LangChain Tool instance for use in the LLM.

        Returns:
            Tool: A LangChain Tool instance representing the registry.
        """
        return Tool(name="tool_registry", func=self.inspect_tools, description="List all registered tools")

def _flatten_toml_config(data: dict[str, Any], parent_key: str = "") -> dict[str, Any]:
    """
    Flatten nested TOML sections into a single-level dict using underscores.
    """
    items: dict[str, Any] = {}
    for key, value in data.items():
        new_key = f"{parent_key}_{key}" if parent_key else str(key)
        if isinstance(value, dict):
            items.update(_flatten_toml_config(value, new_key))
        else:
            flat_key = new_key.upper()
            # Coerce booleans to strings because AgentConfig expects string flags in some cases
            items[flat_key] = str(value) if isinstance(value, bool) else value
    return items


if __name__ == "__main__":
    print("STARTING +++++++++++++++++++++++++++++++++")
    from agentfoundry.llm.llm_factory import LLMFactory
    from agentfoundry.utils.config import load_config
    
    logging.basicConfig(level=logging.DEBUG);
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s - %(name)-32s:%(lineno)-5s  - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger("httpcore").setLevel(logging.WARNING);
    logging.getLogger("openai").setLevel(logging.WARNING);
    logging.getLogger("urllib3").setLevel(logging.WARNING);
    logging.getLogger("httpx").setLevel(logging.WARNING);
    logger = getLogger("agentfoundry.registry.tool_registry")

    config_path = Path.cwd() / "agentfoundry.toml"
    print(f"Loading config from: {config_path}")
    
    # Initialize Config singleton with the file path if it exists
    if config_path.exists():
        load_config(str(config_path))
    else:
        # load_config will look for default locations or env var AGENTFOUNDRY_CONFIG_FILE
        load_config()

    # Load AgentConfig using the robust Config loader (which handles Env Vars)
    config = AgentConfig.from_legacy_config()
    logger.info(f"Loaded AgentConfig. Provider: {config.llm.provider}")

    registry = ToolRegistry(config=config)
    registry.load_tools_from_directory()
    tools = registry.list_tools()
    print(f"Loaded tools: {tools}")

    llm = LLMFactory.get_llm_model(config=config)
    template = """
    You have access to the following tools:

    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, could be one or more of [{tool_names}] but DO NOT use the google_search_tool.
    Action Input: The required fields for the tool as specified by the tool.
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought: {agent_scratchpad}
    """
    react_prompt = template

    # Create the agent using LangChain's create_agent helper
    agent = create_agent(
        model=llm,
        tools=registry.as_langchain_tools(),
        system_prompt=react_prompt,
        checkpointer=None,  # Use MemorySaver() for persistent state if needed
    )

    try:
        # Prepare the input for streaming
        input_data = {
            "messages": [
                HumanMessage(content="Search for information about what AlphaSix Corp. does."),
                SystemMessage(content=f"Available tools: {', '.join(registry.list_tools())}")
            ],
            "tools": registry.inspect_tools(),
            "tool_names": ", ".join(registry.list_tools()),
            "agent_scratchpad": ""
        }

        # Stream events from the agent
        for event in agent.stream(input_data, stream_mode="values"):
            # Extract and print the latest message content
            if "messages" in event and event["messages"]:
                message = event["messages"][-1]
                content = message.content
                # Format tool calls if present
                if hasattr(message, "additional_kwargs") and "tool_calls" in message.additional_kwargs:
                    for tool_call in message.additional_kwargs["tool_calls"]:
                        content += f"\nAction: {tool_call['function']['name']}\nAction Input: {tool_call['function']['arguments']}"
                print(content)
                print('--' * 20)
    except Exception as ex:
        logger.error(f"Error streaming agent: {ex}", exc_info=True)
