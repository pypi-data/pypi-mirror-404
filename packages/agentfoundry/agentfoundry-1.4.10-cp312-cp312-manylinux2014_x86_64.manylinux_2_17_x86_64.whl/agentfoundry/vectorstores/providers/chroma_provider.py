"""ChromaDB vector-store provider implementation."""

from __future__ import annotations

import logging
import warnings
from typing import Any, Dict, List

from agentfoundry.utils.agent_config import AgentConfig
from agentfoundry.vectorstores.base import VectorStore
from agentfoundry.vectorstores.factory import VectorStoreFactory
from agentfoundry.vectorstores.providers.chroma_client import ChromaDBClient
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


@VectorStoreFactory.register_provider("chroma")
class ChromaVectorStoreProvider(VectorStore):
    """Wrap `ChromaDBClient` to fit the VectorStore provider interface."""

    def __init__(self, config: AgentConfig = None, persist_directory: str | None = None, **kwargs):
        # Allow multiple instances (factory-level caching manages reuse)
        if getattr(self, "_initialized", False):
            logger.info("ChromaVectorStoreProvider already initialized.")
            return
        super().__init__(**kwargs)
        
        # Handle backward compatibility
        if config is None:
            warnings.warn(
                "ChromaVectorStoreProvider() without config is deprecated. "
                "Pass AgentConfig explicitly.",
                DeprecationWarning,
                stacklevel=2
            )
            config = AgentConfig.from_legacy_config()
        
        self._config = config
        # Single client per provider; stores are created per-org on demand
        self.client = ChromaDBClient(config=config, persist_directory=persist_directory)
        self._stores: Dict[str, Any] = {}
        self._initialized = True
        logger.info("ChromaVectorStoreProvider initialized.")

    # ------------------------------------------------------------------
    # Provider API
    # ------------------------------------------------------------------

    def get_store(self, org_id: str | None = None, **kwargs):
        """Return the LangChain VectorStore instance for the given org."""
        logger.debug(f"ChromaVectorStoreProvider.get_store called org_id: {org_id}")
        org = org_id or "global"
        if org not in self._stores:
            store = self.client.as_vectorstore(org_id=org)
            # Attempt to log the underlying collection name for diagnostics
            try:
                coll_name = getattr(getattr(store, "_collection", None), "name", None)
                logger.info("ChromaVectorStoreProvider: created store for org=%s collection=%s", org, coll_name or "<unknown>")
            except Exception as ex:
                logger.warning(f"Failed to get ChromaDB collection name: {ex}")
            self._stores[org] = store
        return self._stores[org]

    # ------------------------------------------------------------------
    # Helpers that memory_tools expects
    # ------------------------------------------------------------------

    @staticmethod
    def deterministic_id(text: str, user_id: str | None, org_id: str | None) -> str:  # noqa: D401,E501
        """Expose ChromaDBClient's deterministic ID helper."""
        deterministic_id: str = ChromaDBClient.get_deterministic_id(text, user_id, org_id)
        logger.debug(f"ChromaVectorStoreProvider.deterministic_id: {deterministic_id}")

        return deterministic_id

    def purge_expired(self, retention_days: int = 90) -> None:
        logger.debug(f"ChromaVectorStoreProvider.purge_expired days={retention_days}")
        self.client.purge_expired(retention_days=retention_days)
        logger.info(f"ChromaVectorStoreProvider purged expired entries.")

    # ------------------------------------------------------------------
    # Override similarity_search to AVOID embeddings entirely.
    # Use server-side text/FTS filter via where_document + where metadata.
    # ------------------------------------------------------------------
    def similarity_search(self, query: str, k: int = 4, **kwargs) -> List[Document]:  # type: ignore[override]
        """Perform retrieval without passing embeddings.

        - Uses Chroma 'get' with metadata 'where' and textual 'where_document'.
        - Never calls vector similarity or sends query_embeddings.
        """
        org_id = kwargs.pop("org_id", None)
        store = self.get_store(org_id=org_id) if org_id is not None else self.get_store()
        # langchain_chroma has used both `_collection` and `_chroma_collection` across versions
        collection = getattr(store, "_collection", None) or getattr(store, "_chroma_collection", None)
        if collection is None:
            logger.warning("similarity_search (text-only): no underlying collection; returning empty result")
            return []

        # Accept both 'filter' (LangChain name) and 'where' (Chroma name)
        meta_where = kwargs.pop("filter", None) or kwargs.pop("where", None)

        # Tokenize the query to improve recall for phrase/typo variants.
        import re

        q = (query or "").strip()
        # If user passed wildcard, skip where_document and rely on metadata-only fetch.
        wildcard = q == "*"
        words = [] if wildcard else [w for w in re.findall(r"[A-Za-z0-9]+", q.lower()) if len(w) > 2]

        # Small synonym/plural hints for common terms to improve matching.
        aliases = {
            "eye": ["eye", "eyes"],
            "color": ["color", "colour"],
            "green": ["green"],
            "blue": ["blue"],
            "brown": ["brown"],
            "hazel": ["hazel"],
            "gray": ["gray", "grey"],
            "grey": ["grey", "gray"],
        }

        # Expand tokens using aliases; preserve order by scanning words
        tokens: List[str] = []
        for w in words:
            if w in aliases:
                for a in aliases[w]:
                    if a not in tokens:
                        tokens.append(a)
            else:
                if w not in tokens:
                    tokens.append(w)

        # Helper to run collection.get and append results
        def _fetch(where_document):
            try:
                return collection.get(
                    where=meta_where,
                    where_document=where_document,
                    limit=int(max(k, 1)),
                    include=["documents", "metadatas"],
                )
            except Exception:
                logger.debug("similarity_search (text-only): collection.get failed", exc_info=True)
                return {"ids": [], "documents": [], "metadatas": []}

        # Accumulate results; de-duplicate by id
        seen: set[str] = set()
        out_docs: List[Document] = []

        # If no tokens (wildcard or too short), do a metadata-only fetch
        token_list = tokens if tokens else [None]

        for tk in token_list:
            where_doc = None if tk is None else {"$contains": tk}
            res = _fetch(where_doc)
            ids_batches = res.get("ids") or []
            docs_batches = res.get("documents") or []
            meta_batches = res.get("metadatas") or []
            if not ids_batches:
                continue
            ids_row = ids_batches if isinstance(ids_batches[0], str) else ids_batches[0]
            docs_row = (
                docs_batches
                if (docs_batches and isinstance(docs_batches[0], str))
                else (docs_batches[0] if docs_batches else [])
            )
            meta_row = (
                meta_batches
                if (meta_batches and isinstance(meta_batches[0], dict))
                else (meta_batches[0] if meta_batches else [])
            )

            for i, pc in enumerate(docs_row):
                if len(out_docs) >= k:
                    break
                did = ids_row[i] if i < len(ids_row) else None
                if not did or did in seen:
                    continue
                md = meta_row[i] if i < len(meta_row) and isinstance(meta_row[i], dict) else {}
                md = {**md, "__doc_id__": did}
                out_docs.append(Document(page_content=str(pc or ""), metadata=md))
                seen.add(did)

            if len(out_docs) >= k:
                break

        return out_docs
