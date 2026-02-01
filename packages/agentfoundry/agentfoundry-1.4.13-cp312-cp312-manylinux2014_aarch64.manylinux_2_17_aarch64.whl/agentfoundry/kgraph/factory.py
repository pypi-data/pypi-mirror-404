# agentfoundry/kgraph/factory.py

"""
Singleton factory class to manage kgraph provider instances.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from agentfoundry.kgraph.base import KGraphBase
from agentfoundry.kgraph.providers.duckdb_sqlite.duck_graph import DuckSqliteGraph
import threading
import logging

# Import module-level config getter from memory_tools
try:
    from agentfoundry.agents.tools.memory_tools import get_module_config
except ImportError:
    get_module_config = lambda: None  # noqa: E731

logger = logging.getLogger(__name__)


def _get_data_dir() -> str:
    """Get data directory from module config or default."""
    cfg = get_module_config()
    if cfg and cfg.data_dir:
        return str(cfg.data_dir)
    return "./data"


class KGraphFactory:
    """
    Singleton factory to return kgraph provider instances.
    """
    _instance: Optional[KGraphFactory] = None
    _lock = threading.Lock()

    def __init__(self):
        self._providers: Dict[str, KGraphBase] = {}
        logger.debug("KGraphFactory initialized.")

    @classmethod
    def get_instance(cls) -> KGraphFactory:
        logger.debug("KGraphFactory.get_instance called")
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    logger.debug("Creating KGraphFactory singleton instance.")
                    cls._instance = cls()
        return cls._instance

    def get_kgraph(self, config_override: Dict[str, Any] = None) -> KGraphBase:
        """
        Returns a singleton KGraphBase provider instance per backend.

        Args:
            config_override: Optional configuration overrides for the provider.

        Returns:
            KGraphBase: The graph provider instance.
        """
        # Get backend from override, module config, or default
        backend = (config_override or {}).get("KGRAPH.BACKEND")
        if not backend:
            module_cfg = get_module_config()
            backend = module_cfg.extra.get("kgraph_backend", "duckdb_sqlite") if module_cfg else "duckdb_sqlite"
        
        logger.debug(f"get_kgraph called backend={backend} overrides={config_override}")
        key = backend

        if key not in self._providers:
            logger.info(f"Instantiating new KGraph provider for backend '{backend}'")
            if backend == "duckdb_sqlite":
                persist_path = (config_override or {}).get("DATA_DIR") or _get_data_dir()
                self._providers[key] = DuckSqliteGraph(persist_path=persist_path)
            else:
                raise ValueError(f"Unknown kgraph backend: {backend}")
        else:
            logger.debug(f"Returning cached KGraph provider for backend '{backend}'")
        return self._providers[key]


def get_graph(config_override: Dict[str, Any] | None = None) -> KGraphBase:
    """Convenience helper returning the configured KGraph provider."""
    return KGraphFactory.get_instance().get_kgraph(config_override=config_override)
