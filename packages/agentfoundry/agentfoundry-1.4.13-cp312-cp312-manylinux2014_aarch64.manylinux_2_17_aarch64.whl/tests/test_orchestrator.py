import pytest

import agentfoundry.agents.orchestrator as orchestrator_module
from agentfoundry.agents.orchestrator import Orchestrator


class DummyRegistryNoAttr:
    """Registry stub without agent_tools attribute."""
    pass


class DummyRegistryWithInvalidAttr:
    """Registry stub with agent_tools attribute of wrong type."""
    agent_tools = ["not", "a", "dict"]


class DummyRegistryValid:
    """Registry stub with valid agent_tools mapping."""
    def __init__(self):
        self.agent_tools = {"agentA": []}


class DummySupervisorBuilder:
    """Stub for create_supervisor return value, with compile()."""
    def __init__(self, *args, **kwargs):
        pass

    def compile(self, checkpointer):
        return "compiled_supervisor"


@pytest.fixture(autouse=True)
def stub_orchestrator_dependencies(monkeypatch):
    """
    Stub out heavy dependencies for Orchestrator.__init__, so tests focus on agent_tools validation.
    """
    # Stub LLMFactory.get_llm_model to avoid external LLM initialization
    class DummyLLMFactory:
        @staticmethod
        def get_llm_model(*args, **kwargs):
            return "dummy_llm"

    monkeypatch.setattr(orchestrator_module, "LLMFactory", DummyLLMFactory)
    # Stub make_specialist to avoid building real agents
    monkeypatch.setattr(
        orchestrator_module,
        "make_specialist",
        lambda name, tools, llm, prompt=None: f"specialist_{name}",
    )
    # Orchestrator now uses create_agent (from langgraph.prebuilt) to build a compiled supervisor.
    # Return a simple sentinel so initialization completes without heavy deps.
    monkeypatch.setattr(
        orchestrator_module,
        "create_agent",
        lambda *args, **kwargs: "compiled_supervisor",
        raising=True,
    )
    # Stub MemorySaver
    monkeypatch.setattr(orchestrator_module, "MemorySaver", lambda *args, **kwargs: None)
    yield
    # Reset Orchestrator singleton to avoid test cross-talk
    try:
        orchestrator_module.Orchestrator._instance = None
        orchestrator_module.Orchestrator._initialized = False
    except Exception:
        pass


def test_missing_agent_tools_defaults():
    """Initializing with no agent_tools should now default to a general agent."""
    orch = Orchestrator(DummyRegistryNoAttr())
    # Should have auto-created a 'general_agent' key
    assert "general_agent" in orch.registry.agent_tools
    assert isinstance(orch.registry.agent_tools["general_agent"], list)


def test_agent_tools_not_dict_defaults():
    """Initializing with invalid agent_tools should fallback to defaults."""
    orch = Orchestrator(DummyRegistryWithInvalidAttr())
    # Should have overwritten the invalid attribute with a valid dict
    assert isinstance(orch.registry.agent_tools, dict)
    assert "general_agent" in orch.registry.agent_tools


def test_valid_agent_tools_initializes():
    """With a valid agent_tools dict, Orchestrator should initialize and set attributes."""
    dummy_registry = DummyRegistryValid()
    orch = Orchestrator(dummy_registry, llm="provided_llm")
    # Registry should be stored
    assert orch.registry is dummy_registry
    # Counter initialized to zero
    assert orch.curr_counter == 0
    # Supervisor should be our stub compiled return value
    assert orch.supervisor == "compiled_supervisor"
