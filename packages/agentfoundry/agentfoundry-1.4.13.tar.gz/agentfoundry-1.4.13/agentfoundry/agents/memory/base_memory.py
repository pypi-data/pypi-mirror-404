"""Abstract base class for memory management layers."""

from __future__ import annotations

import hashlib
import logging
import pathlib
from abc import ABC
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from agentfoundry.vectorstores.factory import VectorStoreFactory
from agentfoundry.kgraph.factory import KGraphFactory
from agentfoundry.cache.caching_layer import CachingVectorProvider, CachingKGraph
from agentfoundry.agents.memory.constants import SYSTEM_USER_ID

logger = logging.getLogger(__name__)


class BaseMemory(ABC):
    """Base class for memory layers providing common storage and hashing logic."""

    def __init__(self, root_path: pathlib.Path, hash_prefix: str | None = None):
        """Initialize the base memory.
        
        Args:
            root_path: Directory where this memory scope stores data (mostly for KGraph/DuckDB).
            hash_prefix: Prefix used for deterministic ID generation (e.g. org_id or user_id).
                         If None, only the text is hashed.
        """
        self._root = root_path
        self._root.mkdir(parents=True, exist_ok=True)
        self.hash_prefix = hash_prefix

        # Vector store provider (cached wrapper)
        # Note: VectorStoreFactory returns a singleton provider. Scoping is handled via metadata/filters.
        self.vs_provider = CachingVectorProvider(VectorStoreFactory.get_provider())

        # KGraph provider (cached wrapper)
        # Note: KGraph factory returns a provider often tied to the DATA_DIR.
        self._kg = CachingKGraph(KGraphFactory.get_instance().get_kgraph({"DATA_DIR": str(self._root)}))
        
        logger.debug(f"BaseMemory initialized at {self._root} with prefix {hash_prefix}")

    def _det_id(self, text: str) -> str:
        """Generate a deterministic ID based on text and the configured prefix."""
        if self.hash_prefix:
            content = f"{self.hash_prefix}|{text}"
        else:
            content = text
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_base_metadata(self) -> Dict[str, Any]:
        """Return base metadata to be attached to every document/fact.
        
        Override this in subclasses to add scope-specific fields (user_id, org_id, etc.).
        """
        return {"created_at": datetime.now(timezone.utc).isoformat()}

    # ------------------------------------------------------------------
    # Semantic layer (Vector Store)
    # ------------------------------------------------------------------
    def add_semantic_item(self, text: str, metadata: Dict[str, Any] | None = None, **kwargs) -> str:
        """Add a document to the vector store."""
        doc_id = self._det_id(text)
        base_meta = self._get_base_metadata()
        full_meta = {**(metadata or {}), **base_meta}
        
        try:
            # Create Document
            doc = Document(page_content=text, metadata=full_meta, id=doc_id)
            
            # Helper for subclasses to inject specific args into vs_provider.add_documents
            # e.g., org_id for partitioning
            self._add_to_vectorstore([doc], [doc_id], **kwargs)
            
            logger.debug(f"{self.__class__.__name__} semantic item added id={doc_id}")
        except ValueError:
            logger.debug(f"{self.__class__.__name__} semantic item duplicate ignored id={doc_id}")
        except Exception as e:
            logger.error(f"Error adding semantic item in {self.__class__.__name__}: {e}", exc_info=True)
            raise e
            
        return doc_id

    def _add_to_vectorstore(self, docs: List[Document], ids: List[str], **kwargs):
        """Internal method to push to vector store. Can be overridden for complex logic."""
        self.vs_provider.add_documents(docs, ids=ids, allow_update=False, **kwargs)

    def semantic_search(self, query: str, k: int = 10, filter: Dict[str, Any] | None = None, **kwargs) -> List[str]:
        """Search the vector store."""
        docs = self.vs_provider.similarity_search(query, k=k, filter=filter, **kwargs)
        logger.debug(f"{self.__class__.__name__} search '{query}' hits={len(docs)}")
        return [d.page_content for d in docs]

    # ------------------------------------------------------------------
    # KGraph layer
    # ------------------------------------------------------------------
    def upsert_fact(self, subject: str, predicate: str, obj: str) -> str:
        """Insert a fact into the knowledge graph."""
        meta = self._get_base_metadata()
        # Clean up meta for KGraph if needed (KGraph implementation might expect specific keys)
        # For now we pass the base metadata which usually contains user_id/org_id/scope
        fid = self._kg.upsert_fact(subject, predicate, obj, meta)
        logger.debug(f"{self.__class__.__name__} fact upsert id={fid}")
        return fid

    def fact_search(self, query: str, k: int = 10, **kwargs):
        """Search the knowledge graph."""
        # Subclasses should provide user_id/org_id in kwargs if required by underlying KGraph
        return self._kg.search(query, k=k, **kwargs)

    def summary(self, k: int = 5) -> Dict[str, Any]:
        """Default summary implementation."""
        return {
            "docs": self.semantic_search("*", k=k),
            "facts": self.fact_search("*", k=k)
        }
