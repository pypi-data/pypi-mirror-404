"""Short-term per-thread memory based on a dedicated FAISS index.

Each (user_id, thread_id) pair gets its own FAISS vector index persisted
beneath   DATA_DIR/memory_cache/threads/<user>/<thread>/.

Only *ephemeral* context is stored – typically the last few dozen messages –
so the index stays tiny and similarity search remains fast.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import pathlib
from datetime import datetime, timezone
from typing import Any, List

import duckdb  # require real duckdb; fail if missing
from langchain_core.documents import Document
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

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
    try:  # fall back to legacy Config (used in tests)
        from agentfoundry.utils.config import Config  # noqa: WPS433
        return str(Config().get("DATA_DIR", "./data"))
    except Exception:  # pragma: no cover - defensive fallback
        return "./data"


def _get_org_id() -> str:
    """Get org_id from module config or return empty string."""
    cfg = get_module_config()
    if cfg:
        return cfg.org_id or ""
    try:  # fall back to legacy Config for backwards compatibility
        from agentfoundry.utils.config import Config  # noqa: WPS433
        return str(Config().get("ORG_ID", "default") or "default")
    except Exception:  # pragma: no cover
        return "default"


def _use_simple_embeddings() -> bool:
    flag = os.getenv("AF_DISABLE_OPENAI_EMBEDDINGS", "0").lower() in ("1", "true", "yes", "on")
    has_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("AF_OPENAI_API_KEY"))
    return flag or not has_key


class _SimpleEmbeddings:
    """Deterministic, lightweight embedding fallback for offline/tests.

    Produces a fixed-size vector by hashing input text. Suitable only for
    approximate similarity during tests; not for production use.
    """

    def __init__(self, dim: int = 128):
        self.dim = int(dim)

    def _vec(self, s: str) -> list[float]:
        import itertools
        b = hashlib.sha256((s or "").encode("utf-8")).digest()
        # Repeat digest to fill dimension; normalize bytes to [-0.5, 0.5]
        vals = [((x / 255.0) - 0.5) for x in itertools.islice(itertools.cycle(b), self.dim)]
        return vals

    def embed_query(self, query: str) -> list[float]:
        return self._vec(query)

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        return [self._vec(d) for d in documents]

    def __call__(self, input):
        # Compatibility with vectorstores expecting a callable embedding fn
        if isinstance(input, str):
            return self.embed_query(input)
        try:
            return self.embed_documents(list(input))
        except Exception:
            return self.embed_documents([str(input)])


class ThreadMemory:  # pylint: disable=too-many-instance-attributes
    """Per-conversation short-term memory using FAISS + DuckDB."""

    if _use_simple_embeddings():
        _EMBEDDINGS = _SimpleEmbeddings(dim=128)
    else:
        try:
            _EMBEDDINGS = OpenAIEmbeddings()  # shared across instances – light weight
        except Exception as exc:  # pragma: no cover – missing deps or API key
            logger.warning(
                "OpenAI embeddings unavailable; falling back to simple hash embeddings for ThreadMemory",
                exc_info=True,
            )
            _EMBEDDINGS = _SimpleEmbeddings(dim=128)

    def __init__(self, *, user_id: str, thread_id: str, org_id: str | None = None, data_dir: str | None = None,) -> None:
        self.user_id = user_id
        self.thread_id = thread_id
        if org_id is None:
            org_id = _get_org_id()
        if not org_id:
            raise ValueError("ThreadMemory requires org_id (param or config ORG_ID)")
        self.org_id = str(org_id)

        root = (
            pathlib.Path(data_dir or _get_data_dir())
            / "memory_cache"
            / "threads"
            / f"org_{self.org_id}"
            / user_id
            / thread_id
        )
        root.mkdir(parents=True, exist_ok=True)

        self._db_path = root / "context.duckdb"
        self._index_path = root / "faiss.idx"

        # Use connection factory
        self._conn = DuckDBConnectionFactory.get_connection(str(self._db_path))
        self._ensure_schema()

        self.index = self._load_index()
        logger.info(f"ThreadMemory initialised user={user_id} thread={thread_id}")


    def add(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        """Add *text* to this thread-memory if not already present."""

        meta = {
            **(metadata or {}),
            "user_id": self.user_id,
            "thread_id": self.thread_id,
            "org_id": self.org_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "role_level": 0,
        }
        doc_id = self._det_id(text)

        if self._doc_exists(doc_id):
            logger.debug(f"skip duplicate message id={doc_id}")
            return doc_id

        # Lazily create the FAISS index on first real document
        if self.index is None:
            self.index = FAISS.from_documents([Document(page_content=text, metadata=meta, id=doc_id)], self._EMBEDDINGS)
            logger.info(f"added {text} to {doc_id}")
        else:
            self.index.add_documents([Document(page_content=text, metadata=meta, id=doc_id)], ids=[doc_id])
        self.persist_index()

        self._conn.execute("INSERT INTO turns VALUES (?, ?, ?)",[doc_id, text, json.dumps(meta)])
        logger.info(f"added message id={doc_id}")
        return doc_id

    def similarity_search(self, query: str, k: int = 5) -> List[str]:
        if self.index is None:
            return []
        docs = self.index.similarity_search(
            query,
            k=k,
            filter={"user_id": self.user_id, "thread_id": self.thread_id},
        )
        logger.info(f"found {len(docs)} similar messages")
        return [d.page_content for d in docs]

    def clear(self):  # noqa: D401
        self._conn.execute("DELETE FROM turns")
        self.index = None
        self.persist_index()
        logger.info(f"ThreadMemory cleared for {self.user_id}/{self.thread_id}")

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _ensure_schema(self):
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS turns (
                   id TEXT PRIMARY KEY,
                   text TEXT,
                   meta TEXT
               )"""
        )

    def _det_id(self, text: str) -> str:
        return hashlib.sha256(f"{self.user_id}|{self.thread_id}|{text}".encode()).hexdigest()

    def _doc_exists(self, doc_id: str) -> bool:
        row = self._conn.execute("SELECT 1 FROM turns WHERE id=?", [doc_id]).fetchone()
        return row is not None

    # ---------- FAISS persistence ------------------------------------
    def _load_index(self) -> FAISS | None:
        if self._index_path.exists():
            try:
                # Allow dangerous deserialization is safe here because the
                # index file is created by this process in a private data dir
                # under DATA_DIR, not from untrusted sources.
                return FAISS.load_local(
                    str(self._index_path), self._EMBEDDINGS, allow_dangerous_deserialization=True
                )
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    f"Failed to load FAISS index for {self.user_id}/{self.thread_id}: {exc}; recreating"
                )
        # No existing index – create lazily on first add
        return None

    def persist_index(self):
        if self.index is None:
            # Remove any stale index file if present
            try:
                self._index_path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:  # pragma: no cover
                logger.warning(f"Failed to remove FAISS index file at {self._index_path}")
            return
        self.index.save_local(str(self._index_path))
