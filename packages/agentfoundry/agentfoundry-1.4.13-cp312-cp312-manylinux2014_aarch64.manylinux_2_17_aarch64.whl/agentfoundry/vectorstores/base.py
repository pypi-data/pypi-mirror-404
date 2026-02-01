"""Abstract base-class for vector-store providers.

Moved out of *providers/__init__.py* to follow the guideline that classes
belong in their own dedicated modules.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class VectorStore(ABC):  # noqa: D101  (minimal doc)
    """Base class for concrete vector-store provider wrappers."""

    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs
        logger.info(f"Initialized {type(self).__name__} with kwargs={kwargs}")

    # ------------------------------------------------------------------
    # Basic operations expected by *memory_tools* and other call-sites.
    # ------------------------------------------------------------------
    @abstractmethod
    def get_store(self, org_id: str = None):  # pragma: no cover
        """Abstract method implemented by derived classes"""
        raise NotImplementedError

    def add_documents(self, documents, **kwargs):  # type: ignore[no-self-use]
        """Robustly add documents across heterogeneous vector stores.

        - Prefer store.add_documents if available, filtering kwargs to the method's accepted parameters to avoid TypeError on unknown args (e.g., allow_update).
        - Fallback to store.add_texts if present by converting Documents to (texts, metadatas, ids).
        """
        logger.info(f"add_documents called for {len(documents)} docs")
        org_id = kwargs.pop("org_id", None)
        store = self.get_store(org_id=org_id) if org_id is not None else self.get_store()
        add_docs = getattr(store, "add_documents", None)
        if callable(add_docs):
            try:
                # Filter kwargs to those accepted by the store's signature
                import inspect

                sig = inspect.signature(add_docs)
                allowed = set(sig.parameters.keys())
                filt_kwargs = {k: v for k, v in kwargs.items() if k in allowed}
                return add_docs(documents, **filt_kwargs)
            except TypeError:
                # Retry with no extra kwargs
                return add_docs(documents)

        add_texts = getattr(store, "add_texts", None)
        if callable(add_texts):

            texts = []
            metadatas = []
            ids = []
            for d in documents:
                if isinstance(d, Document):
                    texts.append(d.page_content)
                    metadatas.append(getattr(d, "metadata", None) or {})
                    ids.append(getattr(d, "id", None))
                else:
                    texts.append(str(d))
                    metadatas.append({})
                    ids.append(None)
            try:
                return add_texts(texts, metadatas=metadatas, ids=ids)
            except TypeError:
                logger.warning(f"add_texts() does not support metadatas/ids; falling back to add_documents()")
                return add_texts(texts)

        logger.error(f"add_documents() not implemented for {type(self).__name__}")
        raise NotImplementedError("Underlying vector store does not support add_documents/add_texts")

    def similarity_search(self, query: str, k: int = 4, **kwargs):  # type: ignore[no-self-use]
        """Proxy to underlying store ensuring non-standard kwargs become filters.

        LangChain-compatible vector stores typically expose the signature

            similarity_search(query, k=4, filter=None, **kwargs)

        Internal AgentFoundry callers historically passed arbitrary metadata
        keywords (``org_id``, ``user_id`` …) directly – expecting the provider
        to interpret them as filter constraints.  Newer upstream versions,
        however, raise ``TypeError`` for unexpected parameters.  To stay
        backward-compatible, we convert *unknown* kwargs into the ``filter``
        dict accepted by modern stores before delegating.
        """
        logger.info(f"similarity_search called for query={query} k={k}")
        org_id = kwargs.pop("org_id", None)
        logger.info(f"similarity_search called for org_id={org_id}")
        store = self.get_store(org_id=org_id) if org_id is not None else self.get_store()

        # Extract existing filter dict or create empty one.
        raw = kwargs.pop("filter", None)
        flt = raw if raw is not None else {}

        # Any remaining keyword arguments are treated as filter criteria.
        flt.update(kwargs)
        # Internal scoping key – used by caching layer only; do not forward
        # to providers as a metadata predicate.
        if isinstance(flt, dict) and "caller_role_level" in flt:
            flt.pop("caller_role_level", None)

        # Chroma 1.x is strict about top-level where dict: it expects a single
        # logical operator ($and/$or/...) rather than multiple peer fields.
        # When callers provide multiple field predicates, wrap them in $and.
        if isinstance(flt, dict):
            top_ops = {"$and", "$or", "$not"}
            has_op = any(op in flt for op in top_ops)
            if not has_op and len(flt) > 1:
                flt = {"$and": [{k: v} for k, v in flt.items()]}
            # Avoid passing an empty dict; Chroma prefers None to mean "no filter"
            if len(flt) == 0:
                flt = None

        logger.debug(f"VectorStore.similarity_search: provider={type(self).__name__} k={k} filter={flt}")

        res = store.similarity_search(query, k=k, filter=flt)
        logger.debug(f"VectorStore.similarity_search: provider={type(self).__name__} returned {len(res) if hasattr(res, '__len__') else -1} docs")

        return res

    def delete(self, *args, **kwargs):  # type: ignore[no-self-use]
        org_id = kwargs.pop("org_id", None)
        store = self.get_store(org_id=org_id) if org_id is not None else self.get_store()
        return store.delete(*args, **kwargs)

    # ------------------------------------------------------------------
    # Helper utilities that concrete providers often expose.
    # ------------------------------------------------------------------

    @staticmethod
    def deterministic_id(text: str, user_id: str | None, org_id: str | None) -> str:  # noqa: D401
        raise NotImplementedError

    def purge_expired(self, retention_days: int = 0) -> None:  # noqa: D401
        # Optional – providers may override.
        return None
