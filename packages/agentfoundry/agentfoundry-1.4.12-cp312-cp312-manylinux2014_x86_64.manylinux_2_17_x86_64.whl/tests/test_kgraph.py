import pytest
from unittest.mock import patch, MagicMock
from agentfoundry.kgraph.factory import KGraphFactory, get_graph

@pytest.fixture
def clean_factory():
    # Reset singleton
    KGraphFactory._instance = None
    yield
    KGraphFactory._instance = None

@pytest.fixture
def mock_duck_graph():
    with patch("agentfoundry.kgraph.factory.DuckSqliteGraph") as MockClass:
        yield MockClass

@pytest.fixture
def mock_config():
    with patch("agentfoundry.kgraph.factory.get_module_config") as MockConfig:
        MockConfig.return_value = MagicMock()
        MockConfig.return_value.extra = {}
        MockConfig.return_value.data_dir = "/tmp/data"
        yield MockConfig

def test_singleton(clean_factory):
    f1 = KGraphFactory.get_instance()
    f2 = KGraphFactory.get_instance()
    assert f1 is f2

def test_get_kgraph_default(clean_factory, mock_duck_graph, mock_config):
    factory = KGraphFactory.get_instance()
    
    # Call
    graph = factory.get_kgraph()
    
    # Should instantiate DuckSqliteGraph
    mock_duck_graph.assert_called_once()
    assert graph == mock_duck_graph.return_value
    
    # Second call should return same instance
    graph2 = factory.get_kgraph()
    mock_duck_graph.assert_called_once() # Still once
    assert graph2 is graph

def test_get_kgraph_override(clean_factory, mock_duck_graph):
    factory = KGraphFactory.get_instance()
    
    # Override backend
    # If I pass "duckdb_sqlite", it works.
    graph = factory.get_kgraph(config_override={"KGRAPH.BACKEND": "duckdb_sqlite", "DATA_DIR": "/custom"})
    
    mock_duck_graph.assert_called_with(persist_path="/custom")

def test_get_graph_helper(clean_factory, mock_duck_graph, mock_config):
    graph = get_graph()
    mock_duck_graph.assert_called()
    assert graph == mock_duck_graph.return_value

def test_unknown_backend(clean_factory, mock_duck_graph):
    factory = KGraphFactory.get_instance()
    with pytest.raises(ValueError):
        factory.get_kgraph(config_override={"KGRAPH.BACKEND": "unknown"})
