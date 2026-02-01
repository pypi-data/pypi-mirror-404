import sys
import types

import pytest

# Provide a lightweight fake for langgraph_supervisor to avoid import-time errors
fake_lgs = types.ModuleType("langgraph_supervisor")
_LGS_BUILDER_SINGLETON = None


class _FakeSupervisor:
    def invoke(self, init, config=None):
        class _Msg:
            def __init__(self, content):
                self.content = content
                self.additional_kwargs = {}

        return {"messages": [_Msg("FAKE_SUPERVISOR_REPLY")]}


class _FakeBuilder:
    def compile(self, checkpointer=None):
        return _FakeSupervisor()


def _fake_create_supervisor(**kwargs):
    return _FakeBuilder()


fake_lgs.create_supervisor = lambda **kw: _fake_create_supervisor()
sys.modules["langgraph_supervisor"] = fake_lgs

from agentfoundry.agents.orchestrator import Orchestrator
from agentfoundry.registry.tool_registry import ToolRegistry


def test_run_task_intercepts_dummy_prompt(monkeypatch):
    # Arrange: monkeypatch LLM factory and supervisor builder to avoid real LLM usage
    import agentfoundry.agents.orchestrator as orch_mod
    # Orchestrator uses create_agent; return a lightweight supervisor stub
    monkeypatch.setattr(orch_mod, "create_agent", lambda **kw: _FakeSupervisor())

    # Avoid creating real LLM in Orchestrator
    from agentfoundry.llm import llm_factory as llm_factory_mod
    monkeypatch.setattr(
        llm_factory_mod.LLMFactory,
        "get_llm_model",
        staticmethod(lambda *a, **kw: type("LLM", (), {"model_name": "dummy"})()),
    )

    registry = ToolRegistry()
    # Ensure expected attribute exists and is empty
    registry.agent_tools = {}

    # Reset singleton so this test gets a fresh supervisor
    try:
        Orchestrator._instance = None
        Orchestrator._initialized = False
    except Exception:
        pass
    orch = Orchestrator(registry)

    # Act: send the dummy test prompt
    out = orch.run_task("Hello World")

    # Assert: the fake supervisor reply is returned
    assert out == "FAKE_SUPERVISOR_REPLY"


def test_chat_intercepts_dummy_prompt(monkeypatch):
    # Arrange
    import agentfoundry.agents.orchestrator as orch_mod
    # Orchestrator uses create_agent; return a lightweight supervisor stub
    monkeypatch.setattr(orch_mod, "create_agent", lambda **kw: _FakeSupervisor())

    from agentfoundry.llm import llm_factory as llm_factory_mod
    monkeypatch.setattr(
        llm_factory_mod.LLMFactory,
        "get_llm_model",
        staticmethod(lambda *a, **kw: type("LLM", (), {"model_name": "dummy"})()),
    )

    registry = ToolRegistry()
    registry.agent_tools = {}
    # Reset singleton so this test gets a fresh supervisor
    try:
        Orchestrator._instance = None
        Orchestrator._initialized = False
    except Exception:
        pass
    orch = Orchestrator(registry)

    # Act
    out = orch.chat([
        {"role": "system", "content": "You are a test."},
        {"role": "user", "content": "Hello World"},
    ])

    # Assert
    assert out == "FAKE_SUPERVISOR_REPLY"
