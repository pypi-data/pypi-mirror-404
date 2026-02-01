import os
import textwrap

import pytest

from agentfoundry.registry.tool_registry import ToolRegistry
from agentfoundry.utils.config import Config


def _make_tool_file(directory, module_name, tool_name):
    """Create a minimal Python module that defines a LangChain Tool instance."""
    path = directory / f"{module_name}.py"
    path.write_text(textwrap.dedent(f"""
        from langchain_core.tools import Tool

        {tool_name}_tool = Tool(
            name="{tool_name}",
            func=lambda *args, **kwargs: "{tool_name}_result",
            description="Description for {tool_name}"
        )
    """))
    return path


def test_load_single_custom_dir(tmp_path):
    # Prepare a single custom tools directory with one tool
    custom_dir = tmp_path / "dir1"
    custom_dir.mkdir()
    _make_tool_file(custom_dir, "foo_module", "foo")

    registry = ToolRegistry()
    registry._tools.clear()
    # Load from an explicit directory string
    registry.load_tools_from_directory(str(custom_dir))
    tools = registry.list_tools()
    assert "foo" in tools, f"Expected custom tool 'foo' to be registered, got {tools}"


def test_load_multiple_custom_dirs(tmp_path):
    # Prepare two custom directories, each with a distinct tool
    d1 = tmp_path / "dir1"
    d2 = tmp_path / "dir2"
    d1.mkdir(); d2.mkdir()
    _make_tool_file(d1, "foo_mod", "foo")
    _make_tool_file(d2, "bar_mod", "bar")

    registry = ToolRegistry()
    registry._tools.clear()
    # Load from a list of directories
    registry.load_tools_from_directory([str(d1), str(d2)])
    tools = registry.list_tools()
    assert {"foo", "bar"}.issubset(set(tools)), f"Expected 'foo' and 'bar' in {tools}"


def test_fallback_to_configured_tools_dir(monkeypatch, tmp_path):
    # Prepare a fallback directory with one tool
    fallback = tmp_path / "fallback"
    fallback.mkdir()
    _make_tool_file(fallback, "baz_mod", "baz")

    # Reset singleton and monkey-patch Config.get to return our dirs
    Config._instance = None
    monkeypatch.setattr(
        Config,
        "get",
        lambda self, key, default=None: [] if key == "TOOLS_DIRS"
        else str(fallback) if key == "TOOLS_DIR"
        else default,
    )

    registry = ToolRegistry()
    registry._tools.clear()
    # No explicit directories -> should pick up fallback via Config
    registry.load_tools_from_directory()
    tools = registry.list_tools()
    assert "baz" in tools, f"Expected fallback tool 'baz' in {tools}"


def test_override_config_with_explicit_dirs(monkeypatch, tmp_path):
    # Even if TOOLS_DIRS is set in config, passing explicit dirs should override it
    d1 = tmp_path / "d1"
    d1.mkdir()
    _make_tool_file(d1, "foo_mod", "foo")

    # Config would point elsewhere, but explicit argument wins
    Config._instance = None
    monkeypatch.setattr(
        Config,
        "get",
        lambda self, key, default=None: ["/nonexistent"] if key == "TOOLS_DIRS"
        else "/nonexistent"
        if key == "TOOLS_DIR"
        else default,
    )

    registry = ToolRegistry()
    registry._tools.clear()
    registry.load_tools_from_directory(str(d1))
    tools = registry.list_tools()
    assert "foo" in tools, f"Expected explicit tool 'foo' in {tools}"