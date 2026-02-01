"""Utility for managing DuckDB connections.

This module provides a connection pool or factory to ensure efficient use of DuckDB connections
and prevent file locking issues.
"""

import duckdb
import logging
import threading
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class DuckDBConnectionFactory:
    """Factory to manage and reuse DuckDB connections."""

    _connections: Dict[str, duckdb.DuckDBPyConnection] = {}
    _lock = threading.Lock()

    @classmethod
    def get_connection(cls, db_path: str, read_only: bool = False) -> duckdb.DuckDBPyConnection:
        """Get a DuckDB connection for the specified path.

        Reuses existing connections if available.
        """
        # DuckDB handles multiple cursors from a single connection well,
        # but for file-based dbs, we want to avoid multiple processes/threads fighting over the lock
        # if they try to open independent connections to the same file.
        # However, DuckDB allows multiple connections to the same file in the same process?
        # Actually, DuckDB's standard recommendation is one connection per file per process,
        # and share that connection object.

        with cls._lock:
            if db_path not in cls._connections:
                logger.info(f"Opening new DuckDB connection to {db_path}")
                try:
                    conn = duckdb.connect(str(db_path), read_only=read_only)
                    cls._connections[db_path] = conn
                except Exception as e:
                    logger.error(f"Failed to connect to DuckDB at {db_path}: {e}")
                    raise
            return cls._connections[db_path]

    @classmethod
    def close_all(cls):
        """Close all cached connections."""
        with cls._lock:
            for path, conn in cls._connections.items():
                try:
                    conn.close()
                    logger.info(f"Closed DuckDB connection to {path}")
                except Exception as e:
                    logger.warning(f"Error closing connection to {path}: {e}")
            cls._connections.clear()
