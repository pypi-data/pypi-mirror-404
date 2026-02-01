"""Global (system-wide) memory shared across all organisations and users.

Intended for vendor-neutral documentation, reference policies, general world
knowledge, FAQs etc.  This is *read-only* for most agents, but write helpers are
provided to populate/curate the store.

Layers
------
Semantic  : VectorStore (Chroma/FAISS) – RAG over large public corpus.
Structured: KGraph                     – relationships between docs/policies.

Storage path  DATA_DIR/global_memory/
"""

from __future__ import annotations

import logging
import pathlib
from typing import Any, Dict, List, Optional

from agentfoundry.agents.memory.base_memory import BaseMemory
from agentfoundry.agents.memory.constants import SCOPE_GLOBAL

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


class GlobalMemory(BaseMemory):
    """Singleton-like global memory combining VectorStore + KGraph."""

    _instance: "GlobalMemory" | None = None

    # ------------------------------------------------------------------
    def __new__(cls, *args, **kwargs):  # noqa: D401  (singleton pattern)
        if cls._instance is None:
            cls._instance = super(BaseMemory, cls).__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    def __init__(self, *, data_dir: str | None = None):
        # Handle singleton initialization check
        if hasattr(self, "_initialized") and self._initialized:
            return
            
        root = pathlib.Path(data_dir or _get_data_dir()) / "global_memory"
        
        # Initialize BaseMemory (sets up _root, vs_provider, _kg)
        # GlobalMemory uses text-only hashing (no prefix)
        super().__init__(root_path=root, hash_prefix=None)

        self._initialized = True
        logger.info(f"GlobalMemory initialised at {root}")

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    def _get_base_metadata(self) -> Dict[str, Any]:
        """Global memory items are tagged with scope=global."""
        meta = super()._get_base_metadata()
        meta["scope"] = SCOPE_GLOBAL
        return meta

    def search(self, query: str, k: int = 10) -> List[str]:
        """Search global documents."""
        # Global search typically doesn't need filters if it's in a dedicated collection,
        # but explicit scope is safer if sharing indices.
        return self.semantic_search(query, k=k, filter={"scope": SCOPE_GLOBAL})

    # Alias for backward compatibility if needed, though semantic_search is standard
    def add_document(self, text: str, metadata: Dict[str, Any] | None = None) -> str:
        return self.add_semantic_item(text, metadata=metadata)

    def fact_search(self, query: str, k: int = 10):
        """Search global facts."""
        # Global KGraph searches explicitly with empty user/org
        return super().fact_search(query, k=k, user_id="", org_id="")

