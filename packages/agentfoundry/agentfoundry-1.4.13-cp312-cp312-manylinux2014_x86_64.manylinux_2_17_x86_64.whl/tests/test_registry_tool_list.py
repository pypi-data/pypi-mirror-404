from agentfoundry.registry.tool_registry import ToolRegistry
registry = ToolRegistry()
registry.load_tools_from_directory()
print(registry.list_tools())
