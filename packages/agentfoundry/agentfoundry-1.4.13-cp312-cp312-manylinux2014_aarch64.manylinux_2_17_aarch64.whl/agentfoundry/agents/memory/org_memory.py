"""Long-term organization-level memory shared across all users in an org.

Layers used
-----------
Semantic (RAG)
    • VectorStore (Chroma/FAISS) for company docs, historic chats, etc.

Structured
    • KGraph for compliance / policy triples and any other relational facts.

All data lives under DATA_DIR/org_memory/<org_id>/ so that removing that directory wipes all org-wide memory in one go.
"""

from __future__ import annotations

import logging
import pathlib
from typing import Any, Dict, List

from langchain_core.documents import Document

from agentfoundry.agents.memory.base_memory import BaseMemory
from agentfoundry.agents.memory.constants import SYSTEM_USER_ID

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


class OrgMemory(BaseMemory):
    """Persistent, shared memory for a whole organization/team."""

    # ------------------------------------------------------------------
    def __init__(self, org_id: str, *, data_dir: str | None = None):
        self.org_id = org_id

        root = pathlib.Path(data_dir or _get_data_dir()) / "org_memory" / org_id
        
        # Initialize BaseMemory with org-specific path and hashing
        super().__init__(root_path=root, hash_prefix=org_id)

        logger.info(f"OrgMemory initialized for org={org_id} (path={root})")

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    def _get_base_metadata(self) -> Dict[str, Any]:
        """Org items are tagged with org_id and user_id=0 (system)."""
        meta = super()._get_base_metadata()
        meta.update({
            "user_id": SYSTEM_USER_ID,
            "org_id": self.org_id
        })
        return meta

    def _add_to_vectorstore(self, docs: List[Document], ids: List[str], **kwargs):
        """Inject org_id into provider call."""
        # Ensure org_id is passed to the provider for proper partitioning/sharding
        kwargs["org_id"] = self.org_id
        super()._add_to_vectorstore(docs, ids, **kwargs)

    def semantic_search(self, query: str, k: int = 8) -> List[str]:
        """Return docs within org where user_id==0 (public org docs)."""
        # We pass arguments that the underlying CachingVectorProvider uses to filter
        return super().semantic_search(
            query, 
            k=k, 
            org_id=self.org_id,
            caller_role_level=10,
            user_id=SYSTEM_USER_ID
        )

    # ------------------------------------------------------------------
    # KGraph layer (BaseMemory handles upsert via _get_base_metadata)
    # ------------------------------------------------------------------
    def fact_search(self, query: str, k: int = 10):
        """Search org facts."""
        return super().fact_search(query, k=k, user_id="", org_id=self.org_id)

