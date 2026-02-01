"""Smoke tests for memory tools using mocks.

Verifies that the LangChain tool wrappers in agentfoundry.agents.tools.memory_tools
correctly instantiate the underlying memory classes (ThreadMemory, UserMemory, etc.)
and pass parameters (user_id, thread_id, org_id) from the RunnableConfig.
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.runnables import RunnableConfig

from agentfoundry.agents.tools import memory_tools

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def mock_run_bg():
    """Patch _run_bg to run synchronously."""
    with patch("agentfoundry.agents.tools.memory_tools._run_bg") as mock:
        def side_effect(name, target, *args, **kwargs):
            target(*args, **kwargs)
        mock.side_effect = side_effect
        yield mock

@pytest.fixture
def mock_thread_memory():
    with patch("agentfoundry.agents.tools.memory_tools.ThreadMemory") as mock_cls:
        instance = mock_cls.return_value
        instance.similarity_search.return_value = ["thread_hit_1", "thread_hit_2"]
        instance.add.return_value = "doc_id_123"
        instance.index.similarity_search.return_value = []
        yield mock_cls

@pytest.fixture
def mock_user_memory():
    with patch("agentfoundry.agents.tools.memory_tools.UserMemory") as mock_cls:
        instance = mock_cls.return_value
        instance.semantic_search.return_value = ["user_hit_1"]
        instance.add_semantic_item.return_value = "doc_id_456"
        # Mock underlying vs_provider for delete
        instance.vs_provider.similarity_search.return_value = []
        yield mock_cls

@pytest.fixture
def mock_org_memory():
    with patch("agentfoundry.agents.tools.memory_tools.OrgMemory") as mock_cls:
        instance = mock_cls.return_value
        instance.semantic_search.return_value = ["org_hit_1"]
        instance.add_semantic_item.return_value = "doc_id_789"
        instance.vs_provider.similarity_search.return_value = []
        yield mock_cls

@pytest.fixture
def mock_global_memory():
    with patch("agentfoundry.agents.tools.memory_tools.GlobalMemory") as mock_cls:
        instance = mock_cls.return_value
        instance.search.return_value = ["global_hit_1"]
        instance.add_document.return_value = "doc_id_000"
        instance.vs_provider.similarity_search.return_value = []
        yield mock_cls

@pytest.fixture
def mock_vector_store_factory():
    with patch("agentfoundry.agents.tools.memory_tools.VectorStoreFactory") as mock_fac:
        yield mock_fac

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def test_save_thread_memory(mock_run_bg, mock_thread_memory):
    config = RunnableConfig(configurable={"user_id": "u1", "thread_id": "t1", "org_id": "o1"})
    
    # Act
    result = memory_tools.save_thread_memory.invoke({"text": "hello thread"}, config=config)
    
    # Assert
    assert "thread memory saved" in result
    # Verify ThreadMemory was instantiated with correct args
    mock_thread_memory.assert_called_with(user_id="u1", thread_id="t1", org_id="o1")
    # Verify add was called
    mock_thread_memory.return_value.add.assert_called_with("hello thread")

def test_search_thread_memory(mock_thread_memory):
    config = RunnableConfig(configurable={"user_id": "u1", "thread_id": "t1", "org_id": "o1"})
    
    # Act
    results = memory_tools.search_thread_memory.invoke({"query": "find me"}, config=config)
    
    # Assert
    assert results == ["thread_hit_1", "thread_hit_2"]
    mock_thread_memory.assert_called_with(user_id="u1", thread_id="t1", org_id="o1")
    mock_thread_memory.return_value.similarity_search.assert_called_with("find me", 5)

def test_save_user_memory(mock_run_bg, mock_user_memory):
    config = RunnableConfig(configurable={"user_id": "u2", "org_id": "o2", "role_level": "5"})
    
    # Act
    result = memory_tools.save_user_memory.invoke({"text": "i like pizza"}, config=config)
    
    # Assert
    assert "user memory saved" in result
    mock_user_memory.assert_called_with("u2", org_id="o2")
    mock_user_memory.return_value.add_semantic_item.assert_called_with("i like pizza", role_level=5)

def test_search_user_memory_searches_global_too(mock_user_memory, mock_global_memory):
    config = RunnableConfig(configurable={"user_id": "u2", "org_id": "o2"})
    
    # Act
    results = memory_tools.search_user_memory.invoke({"query": "preferences"}, config=config)
    
    # Assert
    # Should combine user hits + global hits
    assert "user_hit_1" in results
    assert "global_hit_1" in results
    mock_user_memory.return_value.semantic_search.assert_called_with("preferences", caller_role_level=0, k=10)
    mock_global_memory.return_value.search.assert_called()

def test_save_org_memory(mock_run_bg, mock_org_memory):
    config = RunnableConfig(configurable={"org_id": "o3"})
    
    # Act
    result = memory_tools.save_org_memory.invoke({"text": "policy update"}, config=config)
    
    # Assert
    assert "org memory saved" in result
    mock_org_memory.assert_called_with("o3")
    mock_org_memory.return_value.add_semantic_item.assert_called_with("policy update")

def test_search_org_memory(mock_org_memory, mock_global_memory):
    config = RunnableConfig(configurable={"org_id": "o3"})
    
    # Act
    results = memory_tools.search_org_memory.invoke({"query": "compliance"}, config=config)
    
    # Assert
    assert "org_hit_1" in results
    assert "global_hit_1" in results
    mock_org_memory.return_value.semantic_search.assert_called_with("compliance", 8)

def test_save_global_memory(mock_run_bg, mock_global_memory):
    # Act
    result = memory_tools.save_global_memory.invoke({"text": "world fact"})
    
    # Assert
    assert "global memory saved" in result
    mock_global_memory.return_value.add_document.assert_called_with("world fact")

def test_summarize_any_memory_thread(mock_thread_memory):
    # We need to mock summarize_memory utility
    with patch("agentfoundry.agents.tools.memory_tools.summarize_memory") as mock_sum:
        mock_sum.return_value = "Summary of thread..."
        config = RunnableConfig(configurable={"user_id": "u1", "thread_id": "t1", "org_id": "o1"})
        
        # Act
        res = memory_tools.summarize_any_memory.invoke({"level": "thread"}, config=config)
        
        # Assert
        assert res == "Summary of thread..."
        # Verify it was called with thread-specific filter
        mock_sum.assert_called()
        call_args = mock_sum.call_args
        assert call_args[0][0]["thread_id"] == "t1"
