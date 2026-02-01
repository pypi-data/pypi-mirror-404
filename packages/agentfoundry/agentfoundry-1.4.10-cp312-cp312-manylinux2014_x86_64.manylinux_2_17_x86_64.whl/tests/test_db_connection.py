import pytest
import duckdb
from unittest.mock import patch, MagicMock
from agentfoundry.utils.db_connection import DuckDBConnectionFactory

@pytest.fixture
def clean_db_factory():
    DuckDBConnectionFactory.close_all()
    yield
    DuckDBConnectionFactory.close_all()

def test_get_connection_reuse(clean_db_factory):
    with patch("duckdb.connect") as mock_connect:
        mock_conn = MagicMock(spec=duckdb.DuckDBPyConnection)
        mock_connect.return_value = mock_conn
        
        c1 = DuckDBConnectionFactory.get_connection("test.db")
        c2 = DuckDBConnectionFactory.get_connection("test.db")
        
        assert c1 is c2
        mock_connect.assert_called_once() # Should reuse

def test_get_connection_different_paths(clean_db_factory):
    with patch("duckdb.connect") as mock_connect:
        mock_connect.side_effect = [MagicMock(), MagicMock()]
        c1 = DuckDBConnectionFactory.get_connection("db1.db")
        c2 = DuckDBConnectionFactory.get_connection("db2.db")
        
        assert c1 is not c2
        assert mock_connect.call_count == 2

def test_close_all(clean_db_factory):
    with patch("duckdb.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        DuckDBConnectionFactory.get_connection("test.db")
        DuckDBConnectionFactory.close_all()
        
        mock_conn.close.assert_called_once()
        assert len(DuckDBConnectionFactory._connections) == 0
