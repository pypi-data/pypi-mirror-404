import pytest
from unittest.mock import MagicMock, patch

import agentfoundry.agents.orchestrator as orchestrator_module
from agentfoundry.agents.orchestrator import Orchestrator
from agentfoundry.agents.architect import ExecutionPlan, SubTask


class DummyRegistryNoAttr:
    """Registry stub without agent_tools attribute."""
    def inspect_tools(self):
        return "tool info"
    def get_tools_by_names(self, names):
        return []


class DummyRegistryWithInvalidAttr:
    """Registry stub with agent_tools attribute of wrong type."""
    agent_tools = ["not", "a", "dict"]
    def inspect_tools(self):
        return "tool info"


class DummyRegistryValid:
    """Registry stub with valid agent_tools mapping."""
    def __init__(self):
        self.agent_tools = {"agentA": []}
    def inspect_tools(self):
        return "tool info"
    def get_tools_by_names(self, names):
        return []


@pytest.fixture(autouse=True)
def stub_orchestrator_dependencies(monkeypatch):
    """
    Stub out heavy dependencies for Orchestrator.__init__, so tests focus on logic.
    """
    # Stub LLMFactory.get_llm_model to avoid external LLM initialization
    class DummyLLMFactory:
        @staticmethod
        def get_llm_model(*args, **kwargs):
            return "dummy_llm"

    monkeypatch.setattr(orchestrator_module, "LLMFactory", DummyLLMFactory)
    
    # Stub create_agent to return a mock runnable
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {"messages": [MagicMock(content="Agent output")]}
    
    monkeypatch.setattr(
        orchestrator_module,
        "create_agent",
        lambda *args, **kwargs: mock_agent,
    )
    
    # Stub MemorySaver
    monkeypatch.setattr(orchestrator_module, "MemorySaver", lambda *args, **kwargs: None)
    
    # Stub AgentArchitect to avoid LLM calls
    mock_architect_cls = MagicMock()
    monkeypatch.setattr(orchestrator_module, "AgentArchitect", mock_architect_cls)
    
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


def test_process_request_single_task():
    """Verify process_request handles a single-task plan."""
    orch = Orchestrator(DummyRegistryValid())
    
    # Mock the architect's plan
    mock_plan = ExecutionPlan(
        goal="Say hello",
        tasks=[
            SubTask(id="1", description="Say hello", tool_names=[], system_prompt="You are a greeter")
        ]
    )
    orch.architect.plan_task.return_value = mock_plan
    
    # Mock the agent created inside process_request
    mock_runner = MagicMock()
    mock_runner.invoke.return_value = {"messages": [MagicMock(content="Hello there!")]}
    
    with patch("agentfoundry.agents.orchestrator.create_agent", return_value=mock_runner) as mock_create:
        response = orch.process_request("Say hello")
        
        assert response == "Hello there!"
        # Verify create_agent was called once
        assert mock_create.call_count == 1
        # Verify invoke was called
        mock_runner.invoke.assert_called_once()

def test_process_request_multi_task():
    """Verify process_request handles a multi-task plan sequentially."""
    orch = Orchestrator(DummyRegistryValid())
    
    # Mock a 2-step plan
    mock_plan = ExecutionPlan(
        goal="Research and Write",
        tasks=[
            SubTask(id="1", description="Research topic", tool_names=["google"], system_prompt="Researcher"),
            SubTask(id="2", description="Write summary", tool_names=["writer"], system_prompt="Writer")
        ]
    )
    orch.architect.plan_task.return_value = mock_plan
    
    # Mock agent execution
    mock_runner = MagicMock()
    # First call returns research, second returns summary
    mock_runner.invoke.side_effect = [
        {"messages": [MagicMock(content="Found info")]},
        {"messages": [MagicMock(content="Written summary")]}
    ]
    
    with patch("agentfoundry.agents.orchestrator.create_agent", return_value=mock_runner) as mock_create:
        response = orch.process_request("Do research")
        
        assert response == "Written summary"
        # Should create an agent for each task
        assert mock_create.call_count == 2
        
        # Verify inputs to second agent include output from first
        calls = mock_runner.invoke.call_args_list
        second_call_arg = calls[1][0][0] # args[0] is the input dict
        input_text = second_call_arg["messages"][0].content
        assert "Found info" in input_text