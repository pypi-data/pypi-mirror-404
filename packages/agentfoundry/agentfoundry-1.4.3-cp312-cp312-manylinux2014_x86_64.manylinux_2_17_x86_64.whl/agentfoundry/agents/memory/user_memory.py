"""Long-term per-user memory combining semantic, graph and profile stores."""

from __future__ import annotations

import json
import logging
import pathlib
from datetime import datetime, timezone
from typing import Any, Dict, List

from langchain_core.documents import Document

from agentfoundry.agents.memory.base_memory import BaseMemory
from agentfoundry.utils.db_connection import DuckDBConnectionFactory

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


def _get_org_id() -> str:
    """Get org_id from module config or return empty string."""
    cfg = get_module_config()
    if cfg:
        return cfg.org_id or ""
    return ""


class UserMemory(BaseMemory):
    """Unified long-term user memory.

    Layers:
        • VectorStore  – semantic search across all user documents/utterances.
        • KGraph       – structured triples (facts, relationships).
        • Profile DB   – typed key/value records (preferences, settings …).
    """

    def __init__(self, user_id: str, org_id: str | None = None, *, data_dir: str | None = None):
        self.user_id = user_id
        # Resolve organization id – mandatory for namespacing collections/facts
        if org_id is None:
            org_id = _get_org_id()
        if not org_id:
            raise ValueError("UserMemory initialization requires org_id (either parameter or config ORG_ID)")
        self.org_id = str(org_id)

        root = pathlib.Path(data_dir or _get_data_dir()) / "user_memory" / user_id
        
        # Initialize BaseMemory (sets up _root, vs_provider, _kg, hash_prefix)
        super().__init__(root_path=root, hash_prefix=user_id)
        
        logger.info(f"Initializing UserMemory with data root: {root}")

        # ---------------- Profile DB (DuckDB) ------------------- #
        self._db_path = root / "profile.duckdb"
        # Use connection factory to prevent file locking issues
        self._conn = DuckDBConnectionFactory.get_connection(str(self._db_path))
        self._ensure_profile_schema()

        logger.info(f"UserMemory initialized for {user_id} (at {root})")

    # ------------------------------------------------------------------
    # Semantic layer overrides
    # ------------------------------------------------------------------

    def add_semantic_item(self, text: str, *, role_level: int = 0, metadata: Dict[str, Any] | None = None) -> str:
        """Store *text* with given role_level (default 0) for this user."""
        logger.info(f"Adding semantic item for user {self.user_id} with role_level {role_level}")
        
        # Use BaseMemory's hashing
        doc_id = self._det_id(text)
        
        try:
            meta = {
                **(metadata or {}),
                "user_id": self.user_id,
                "org_id": self.org_id,
                "role_level": role_level,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error preparing metadata for semantic item: {e}")
            raise e
            
        try:
            doc = Document(page_content=text, metadata=meta, id=doc_id)
            
            # --- Complex persistence logic preserved from original ---
            try:
                # Log target store/collection details for diagnostics
                store = self.vs_provider.remote.get_store(org_id=self.org_id)  # type: ignore[attr-defined]
                coll_name = getattr(getattr(store, "_collection", None), "name", None)
                logger.info(
                    "user_memory: writing doc id=%s user_id=%s org_id=%s collection=%s",
                    doc_id, self.user_id, self.org_id, coll_name or "<unknown>"
                )
            except Exception:
                logger.debug("user_memory: unable to introspect Chroma collection for logging")
            
            # Synchronous write-through to the remote store
            try:
                _ids = self.vs_provider.remote.add_documents([doc], ids=[doc_id], allow_update=False, org_id=self.org_id)  # type: ignore[attr-defined]
                try:
                    logger.info("user_memory: remote add ok ids=%s org=%s", _ids, self.org_id)
                except Exception:
                    pass
                # Persist FAISS index immediately if available
                try:
                    store = self.vs_provider.remote.get_store()  # type: ignore[attr-defined]
                    module_cfg = get_module_config()
                    
                    # Robust path resolution for FAISS persistence
                    path = None
                    if module_cfg and module_cfg.vector_store.index_path:
                        path = str(module_cfg.vector_store.index_path)
                    
                    if not path:
                        # Fallback to default FAISS path (must match FAISS provider defaults)
                        d_dir = _get_data_dir()
                        path = str(pathlib.Path(d_dir) / "faiss_index")

                    if hasattr(store, "save_local") and path:
                        store.save_local(path)
                        logger.debug("user_memory: persisted FAISS index to %s", path)
                except Exception:
                    logger.debug("user_memory: FAISS persist skipped (not available)")
            except Exception as e:
                # Non-fatal: fall back to staged async flush path
                try:
                    logger.warning("user_memory: remote add failed for org=%s id=%s: %s", self.org_id, doc_id, e, exc_info=True)
                except Exception:
                    pass
            
            # Always stage locally for read-your-writes and cache invalidation
            # Using _add_to_vectorstore via super or directly vs_provider
            self.vs_provider.add_documents([doc], ids=[doc_id], allow_update=True, org_id=self.org_id, local_only=True)
            logger.info(f"Semantic item added id={doc_id}")
            
        except ValueError:  # duplicate id
            logger.debug(f"Semantic item already existed id={doc_id}")
        except Exception as e:
            logger.error(f"Error adding semantic item: {e}")
            raise
        return doc_id

    def semantic_search(self, query: str, *, caller_role_level: int = 0, k: int = 5) -> List[str]:
        """Return docs for this user filtered by role_level ≤ caller_role_level."""
        
        # Primary filter (Chroma-friendly)
        where_primary = {
            "$and": [
                {"user_id": self.user_id},
                {"role_level": {"$lte": int(caller_role_level)}},
            ]
        }
        
        # Use BaseMemory's provider (self.vs_provider)
        results = self.vs_provider.similarity_search(query, k=k, filter=where_primary, org_id=self.org_id)
        
        # Fallback: if no hits, relax role_level filter
        if not results:
            where_relaxed = {"user_id": self.user_id}
            try:
                results = self.vs_provider.similarity_search(query, k=k, filter=where_relaxed, org_id=self.org_id)
            except Exception:
                results = []
                
        logger.info(f"Semantic search '{query}' returned {len(results)} hits")
        return [d.page_content for d in results]

    # ------------------------------------------------------------------
    # Structured knowledge-graph helpers
    # ------------------------------------------------------------------

    def upsert_fact(self, subject: str, predicate: str, obj: str) -> str:
        meta = {"user_id": self.user_id, "org_id": self.org_id}
        # Direct use of _kg from BaseMemory
        fid = self._kg.upsert_fact(subject, predicate, obj, meta)
        logger.debug(f"Fact upserted id={fid}")
        return fid

    def fact_search(self, query: str, k: int = 5):
        return super().fact_search(query, k=k, user_id=self.user_id, org_id=self.org_id)

    # ------------------------------------------------------------------
    # Profile helpers (DuckDB)
    # ------------------------------------------------------------------

    def _ensure_profile_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profile (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )

    def set_profile_field(self, key: str, value: Any) -> None:
        self._conn.execute("INSERT OR REPLACE INTO profile VALUES (?, ?)", [key, json.dumps(value)])
        logger.info(f"Profile field set {key}={value}")

    def get_profile_field(self, key: str, default: Any | None = None) -> Any:
        row = self._conn.execute("SELECT value FROM profile WHERE key = ?", [key]).fetchone()
        logger.info(f"Profile field get {key}={row[0] if row else 'None'}")
        return json.loads(row[0]) if row else default

    def profile_dict(self) -> Dict[str, Any]:
        rows = self._conn.execute("SELECT key, value FROM profile").fetchall()
        logger.info(f"Profile dict retrieved with {len(rows)} fields")
        return {k: json.loads(v) for k, v in rows}

    # ------------------------------------------------------------------
    # Summary/utility
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        logger.info(f"Summary {self}")
        return {
            "profile": self.profile_dict(),
            "facts": self.fact_search("*", k=10),
        }
