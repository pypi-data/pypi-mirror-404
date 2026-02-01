"""Test organization isolation in memory tools.

Ensures that memory operations (save/search) are strictly scoped to the 
organization ID provided in the configuration, preventing data leakage.
"""

import pytest
from unittest.mock import patch, MagicMock
from langchain_core.runnables import RunnableConfig

from agentfoundry.agents.tools import memory_tools
from agentfoundry.utils.agent_config import AgentConfig

@pytest.fixture
def mock_memories():
    with patch("agentfoundry.agents.tools.memory_tools.OrgMemory") as mock_om, \
         patch("agentfoundry.agents.tools.memory_tools.UserMemory") as mock_um, \
         patch("agentfoundry.agents.tools.memory_tools.ThreadMemory") as mock_tm, \
         patch("agentfoundry.agents.tools.memory_tools.GlobalMemory") as mock_gm, \
         patch("agentfoundry.agents.tools.memory_tools._run_bg") as mock_bg:
        
        # Make _run_bg run synchronously
        def side_effect(name, target, *args, **kwargs):
            target(*args, **kwargs)
        mock_bg.side_effect = side_effect
        
        yield mock_om, mock_um, mock_tm, mock_gm

def test_org_memory_isolation(mock_memories):
    mock_om, _, _, _ = mock_memories
    
    # User 1 in Org A
    config_a = RunnableConfig(configurable={"org_id": "OrgA"})
    memory_tools.search_org_memory.invoke({"query": "secrets"}, config=config_a)
    
    # Assert OrgMemory was instantiated with OrgA
    mock_om.assert_called_with("OrgA")
    
    # User 2 in Org B
    config_b = RunnableConfig(configurable={"org_id": "OrgB"})
    memory_tools.search_org_memory.invoke({"query": "secrets"}, config=config_b)
    
    # Assert OrgMemory was instantiated with OrgB (new call)
    mock_om.assert_called_with("OrgB")

def test_user_memory_isolation(mock_memories):
    _, mock_um, _, _ = mock_memories
    
    # User in Org A
    config = RunnableConfig(configurable={"user_id": "u1", "org_id": "OrgA"})
    memory_tools.save_user_memory.invoke({"text": "my secret"}, config=config)
    
    # Verify UserMemory init received correct org_id
    mock_um.assert_called_with("u1", org_id="OrgA")
    
    # Verify we didn't use a global or wrong org
    assert mock_um.call_args.kwargs['org_id'] == "OrgA"

def test_module_config_fallback(mock_memories):
    """Test that if org_id is missing in runnable config, it falls back to module config."""
    mock_om, _, _, _ = mock_memories
    
    # Setup module config
    fake_config = MagicMock(spec=AgentConfig)
    fake_config.org_id = "GlobalCorp"
    memory_tools.set_module_config(fake_config)
    
    try:
        # Call with no org_id in runtime config
        config = RunnableConfig(configurable={"user_id": "u1"}) # No org_id
        memory_tools.search_org_memory.invoke({"query": "policy"}, config=config)
        
        # Should use "GlobalCorp" from module config
        mock_om.assert_called_with("GlobalCorp")
        
    finally:
        # Reset module config
        memory_tools.set_module_config(None)

def test_thread_memory_isolation(mock_memories):
    _, _, mock_tm, _ = mock_memories
    
    config = RunnableConfig(configurable={"user_id": "u1", "thread_id": "t1", "org_id": "OrgA"})
    memory_tools.save_thread_memory.invoke({"text": "hi"}, config=config)
    
    mock_tm.assert_called_with(user_id="u1", thread_id="t1", org_id="OrgA")

