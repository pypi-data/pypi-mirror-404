from __future__ import annotations

import hashlib
import logging
import os
import warnings
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from chromadb import HttpClient, PersistentClient
from langchain_chroma import Chroma

from agentfoundry.utils.agent_config import AgentConfig

# ---------------------------------------------------------------------------
# Backward compatibility shim: legacy tests monkeypatch
# `SentenceTransformerEmbeddingFunction` on this module. Provide a lightweight
# placeholder so monkeypatch.setattr can succeed without pulling the heavy
# dependency at import time.
# ---------------------------------------------------------------------------
try:  # pragma: no cover - defensive import
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction as _STEF
except Exception:  # pragma: no cover - fallback for minimal test environments
    class _STEF:
        def __call__(self, texts):  # type: ignore[override]
            return []

SentenceTransformerEmbeddingFunction = _STEF

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """Minimal Chroma client using the official Python API.

    - Local persistence: chromadb.PersistentClient(path=CHROMADB_PERSIST_DIR)
    - Remote (optional): chromadb.HttpClient when CHROMA.URL is set
    - Embeddings: Always server-side SentenceTransformers (never local, never OpenAI)

    The underlying Chroma collection is created with the chosen embedding
    function so the LangChain wrapper does not need its own embedding model.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *, config: AgentConfig = None, persist_directory: str | None = None):
        if getattr(self, "_initialized", False):
            return

        # Handle backward compatibility
        if config is None:
            warnings.warn(
                "ChromaDBClient() without config is deprecated. "
                "Pass AgentConfig explicitly.",
                DeprecationWarning,
                stacklevel=2
            )
            config = AgentConfig.from_legacy_config()
        
        self._config = config
        chroma_cfg = config.vector_store.chroma

        # ---------------- Connection (local or remote) -----------------
        url = (chroma_cfg.url or "").strip()
        if url:
            if "://" not in url:
                url = f"https://{url}"
            from urllib.parse import urlparse

            parsed = urlparse(url)
            host = parsed.hostname or "localhost"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            use_ssl = parsed.scheme == "https"
            logger.info("Chroma: remote %s:%s ssl=%s", host, port, use_ssl)
            # Merge optional configured headers with a predictable User-Agent.
            headers: dict[str, str] = {"User-Agent": "curl/8.5.0"}
            try:
                configured = chroma_cfg.headers or {}
                if isinstance(configured, dict):
                    headers.update({str(k): str(v) for k, v in configured.items()})
            except Exception:  # pragma: no cover – config lookups should not break init
                logger.debug("Chroma: failed to read configured headers", exc_info=True)
            self.client = HttpClient(host=host, port=port, ssl=use_ssl, headers=headers)
        else:
            # Local persistent store
            persist_dir = (persist_directory or chroma_cfg.persist_dir or "./chroma_data").strip()
            os.makedirs(persist_dir, exist_ok=True)
            logger.info("Chroma: local persistent path=%s", persist_dir)
            try:
                self.client = PersistentClient(path=persist_dir, anonymized_telemetry=False)
            except TypeError:
                self.client = PersistentClient(path=persist_dir)

        # ---------------- Embedding function (Chroma side) -------------
        # Always use SentenceTransformers on the server. Never compute locally; never use OpenAI.
        model_name = config.embedding.model_name or 'sentence-transformers/all-MiniLM-L6-v2'
        self._server_embedding_function = None
        self.model_tag = model_name.replace("/", "_").replace(" ", "_")
        logger.info(f"Chroma embeddings (server): SentenceTransformer model: {model_name}")

        # Ensure a simple default collection exists (suffix with model tag to avoid dim collisions)
        base_default = (chroma_cfg.collection_name or os.getenv("CHROMA_COLLECTION_NAME") or "global_memory").strip()
        default_collection = f"{base_default}__{self.model_tag}"
        try:
            self.client.get_or_create_collection(default_collection)
        except Exception as ex:  # noqa
            logger.error(f"ChromaDBClient: get_or_create_collection failed: {ex}")

        self._initialized = True

    # ---------------------- Helpers ------------------------------------
    @staticmethod
    def get_deterministic_id(text: str, user_id: str | None, org_id: str | None) -> str:
        h = hashlib.sha256()
        h.update(text.encode("utf-8"))
        h.update((user_id or "").encode("utf-8"))
        h.update((org_id or "").encode("utf-8"))
        return h.hexdigest()

    @lru_cache(maxsize=128)
    def as_vectorstore(self, *, org_id: str | None = None, collection: str | None = None) -> Chroma:
        """Return a LangChain-Chroma wrapper for a collection.

        - If org_id is provided and collection is None, use "<org_id>_memory__<model_tag>".
        - If neither is provided, use the default global collection suffixed with model tag.
        """
        if collection is None:
            if org_id:
                collection = f"{org_id}_memory__{self.model_tag}"
            else:
                base_default = os.getenv("CHROMA_COLLECTION_NAME") or "global_memory"
                collection = f"{base_default}__{self.model_tag}"

        # Ensure the collection exists with our embedding function using the
        # high-level client so the server stores EF in configuration.
        embed_fn = getattr(self, "_server_embedding_function", None)
        try:
            if embed_fn is not None:
                self.client.get_or_create_collection(collection, embedding_function=embed_fn)
            else:
                self.client.get_or_create_collection(collection)
        except Exception as exc:  # pragma: no cover – best effort
            logger.debug("Chroma: get_or_create_collection(%s) failed: %s", collection, exc)

        # Construct the LangChain wrapper with NO local embedding function.
        # This forces text queries and guarantees the server EF is used.
        return Chroma(
            client=self.client,
            collection_name=collection,
            create_collection_if_not_exists=False,
        )

    def purge_expired(self, retention_days: int = 90) -> None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
        for coll in self.client.list_collections():
            try:
                coll.delete(where={"created_at": {"$lt": cutoff}})
            except Exception:
                # Collections without that metadata can be skipped
                continue


if __name__ == "__main__":
    """Simple remote smoke test when run as a script.

    Steps:
      - Connect to chroma.quantify.alphasixdemo.com (override via env)
      - List collections
      - Create a new test collection
      - Add one document
      - Query for that document

    Environment variables (optional):
      - CHROMA_HOST: hostname (default: chroma.quantify.alphasixdemo.com)
      - CHROMA_PORT: port (default: 443)
      - CHROMA_SSL:  true/false (default: true)
      - CHROMA_TEST_COLLECTION: base name for collection (default: af_smoketest)
      - OPENAI_API_KEY or CHROMA_OPENAI_API_KEY: if set, enables fallback path
        that creates a collection with an OpenAI embedding function if the
        server does not provide embeddings.
    """

    import sys
    import time

    host = os.getenv("CHROMA_HOST", "chroma.quantify.alphasixdemo.com").strip() or "chroma.quantify.alphasixdemo.com"
    port = int(os.getenv("CHROMA_PORT", "443") or 443)
    use_ssl = (os.getenv("CHROMA_SSL", "true") or "true").strip().lower() in {"1", "true", "yes", "on"}
    base_name = os.getenv("CHROMA_TEST_COLLECTION", "af_smoketest").strip() or "af_smoketest"
    coll_name = f"{base_name}_{int(time.time())}"

    print(f"Connecting to Chroma at {host}:{port} ssl={use_ssl} ...")
    client = HttpClient(host=host, port=port, ssl=use_ssl)

    # 1) List collections
    try:
        cols = client.list_collections()
        names = [getattr(c, "name", str(c)) for c in cols]
        print(f"List collections OK ({len(names)}): {names}")
    except Exception as e:  # pragma: no cover - manual smoke path
        print(f"ERROR: listing collections failed: {e}")
        sys.exit(2)

    # 2) Create collection
    try:
        coll = client.get_or_create_collection(coll_name)
        print(f"Created test collection: {coll_name}")
    except Exception as e:  # pragma: no cover
        print(f"ERROR: creating collection '{coll_name}' failed: {e}")
        sys.exit(3)

    # 3) Add a document (server-side embedding preferred)
    doc_id = f"doc_{int(time.time())}"
    text = "hello from ChromaDBClient __main__ smoke test"
    meta = {"source": "main_guard", "created_at": datetime.now(timezone.utc).isoformat()}
    try:
        coll.add(ids=[doc_id], documents=[text], metadatas=[meta])
        print(f"Added document id={doc_id}")
    except Exception as e:
        print(
            "ERROR: add failed and server-side embedding not available on the collection. "
            "Ensure the Chroma server has a SentenceTransformers embedder configured for this collection."
        )
        print(f"Original error: {e}")
        sys.exit(4)

    # 4) Query
    try:
        out = coll.query(query_texts=["hello"], n_results=3)
        hits = len(out.get("ids", [[]])[0]) if out and out.get("ids") else 0
        keys = list(out.keys()) if isinstance(out, dict) else []
        print(f"Query OK; hits={hits}; keys={keys}")
    except Exception as e:  # pragma: no cover
        print(f"ERROR: query failed: {e}")
        sys.exit(6)

    print("Smoke test complete: success.")
    sys.exit(0)
