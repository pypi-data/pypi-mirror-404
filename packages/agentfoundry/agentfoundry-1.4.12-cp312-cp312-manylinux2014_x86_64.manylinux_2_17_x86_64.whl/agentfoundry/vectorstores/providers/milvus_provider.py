"""Milvus vector-store provider implementation."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import warnings
from typing import Any, Dict, Iterable, List, Optional, Union

from agentfoundry.utils.agent_config import AgentConfig
from agentfoundry.vectorstores.base import VectorStore
from agentfoundry.vectorstores.factory import VectorStoreFactory

logger = logging.getLogger(__name__)


class _HashEmbeddings:
    """Deterministic fallback embeddings when API-based models are unavailable."""

    def __init__(self, *, dim: int = 1536) -> None:
        self.dim = int(dim)

    def _vec(self, text: str) -> List[float]:
        import itertools

        digest = hashlib.sha256((text or "").encode("utf-8")).digest()
        # Repeat digest to fill the requested dimension and normalise bytes to [-0.5, 0.5]
        return [((byte / 255.0) - 0.5) for byte in itertools.islice(itertools.cycle(digest), self.dim)]

    def embed_query(self, text: str) -> List[float]:
        return self._vec(text)

    def embed_documents(self, texts: Iterable[str]) -> List[List[float]]:
        return [self._vec(t) for t in texts]


class MilvusVectorStoreProvider(VectorStore):
    """Wrap a Milvus collection so it can be used interchangeably with other providers."""

    _instance: "MilvusVectorStoreProvider | None" = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: AgentConfig = None, **kwargs: Any) -> None:
        if getattr(self, "_initialized", False):
            return
        super().__init__(**kwargs)

        # Handle backward compatibility
        if config is None:
            warnings.warn(
                "MilvusVectorStoreProvider() without config is deprecated. "
                "Pass AgentConfig explicitly.",
                DeprecationWarning,
                stacklevel=2
            )
            config = AgentConfig.from_legacy_config()
        
        self._config = config
        milvus_cfg = config.vector_store.milvus

        self._connection_args = self._build_connection_args(config)
        self._collection_prefix = self._resolve_collection_prefix(config)
        self._search_params = self._coerce_json(milvus_cfg.extra.get("search_params")) if hasattr(milvus_cfg, 'extra') else None
        self._index_params = self._coerce_json(milvus_cfg.extra.get("index_params")) if hasattr(milvus_cfg, 'extra') else None
        self._partition_names = None  # Can be added to MilvusConfig if needed
        self._replica_number = 1
        self._timeout = milvus_cfg.timeout
        self._auto_id = milvus_cfg.auto_id

        self._embedding = self._create_embedding(config)
        self._model_tag = self._normalise_tag(getattr(self._embedding, "model", None))
        self._milvus_stores: Dict[str, Any] = {}
        self._collection_names: Dict[str, str] = {}
        self._initialized = True
        logger.info(
            "MilvusVectorStoreProvider initialized host=%s port=%s uri=%s prefix=%s model_tag=%s partitions=%s replicas=%s timeout=%s auto_id=%s",
            self._connection_args.get("host"),
            self._connection_args.get("port"),
            self._connection_args.get("uri"),
            self._collection_prefix,
            self._model_tag,
            self._partition_names,
            self._replica_number,
            self._timeout,
            self._auto_id,
        )
        logger.debug(
            "MilvusVectorStoreProvider connection args=%s",
            self._sanitise_connection_args(self._connection_args),
        )

    # ------------------------------------------------------------------
    # Helper builders
    # ------------------------------------------------------------------
    @staticmethod
    def _truthy(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _safe_int(value: Any, *, default: int) -> int:
        try:
            if value is None:
                return default
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            if value in (None, "", "None"):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_list(value: Any) -> Optional[List[str]]:
        if value is None or value == "":
            return None
        if isinstance(value, (list, tuple, set)):
            return [str(v) for v in value]
        text = str(value)
        if not text:
            return None
        return [item.strip() for item in text.split(",") if item.strip()]

    @staticmethod
    def _coerce_json(value: Any) -> Optional[Dict[str, Any]]:
        if not value:
            return None
        if isinstance(value, dict):
            return value
        try:
            return json.loads(str(value))
        except Exception:
            logger.warning("Milvus provider: failed to parse JSON config value: %r", value)
            return None

    def _create_embedding(self, config: AgentConfig):
        milvus_cfg = config.vector_store.milvus
        model_name = milvus_cfg.embedding_model or config.embedding.model_name or ""
        fallback_dim = milvus_cfg.fallback_dim or 1536

        def _hash_fallback(reason: str):
            logger.warning(
                "MilvusVectorStoreProvider: using deterministic hash embeddings (dim=%s). Reason: %s",
                fallback_dim,
                reason,
            )
            return _HashEmbeddings(dim=fallback_dim)

        if model_name:
            if "/" in model_name or model_name.startswith("sentence-transformers"):
                try:
                    from langchain_huggingface import HuggingFaceEmbeddings as HFModern

                    return HFModern(model_name=model_name)
                except ImportError:
                    try:
                        from langchain_community.embeddings import HuggingFaceEmbeddings as HFLegacy
                        from langchain_core._api.deprecation import LangChainDeprecationWarning

                        warnings.filterwarnings(
                            "ignore",
                            category=LangChainDeprecationWarning,
                            message="The class `HuggingFaceEmbeddings` was deprecated",
                        )

                        return HFLegacy(model_name=model_name)
                    except Exception as exc:
                        return _hash_fallback(f"HuggingFace embeddings failed: {exc}")
                except Exception as exc:
                    return _hash_fallback(f"HuggingFace embeddings failed: {exc}")

            try:
                from langchain_openai.embeddings import OpenAIEmbeddings

                return OpenAIEmbeddings(model=model_name)
            except Exception as exc:
                return _hash_fallback(f"OpenAI embeddings failed: {exc}")

        try:
            from langchain_openai.embeddings import OpenAIEmbeddings

            return OpenAIEmbeddings()
        except Exception as exc:
            return _hash_fallback(f"OpenAI embeddings unavailable: {exc}")

    @staticmethod
    def _normalise_tag(tag: Optional[str]) -> str:
        text = tag or "hash"
        return re.sub(r"[^A-Za-z0-9_]+", "_", text)

    def _build_connection_args(self, config: AgentConfig) -> Dict[str, Any]:
        milvus_cfg = config.vector_store.milvus
        
        url = milvus_cfg.uri or ""
        if url:
            logger.info(f"connection info: {url}")
            return {"uri": url}

        host = milvus_cfg.host or None
        if not host:
            logger.error("Milvus host not configured")
            raise Exception("Milvus host not configured")
        port = milvus_cfg.port or 19530
        conn: Dict[str, Any] = {"host": host, "port": port}

        if milvus_cfg.secure:
            conn["secure"] = True

        user = milvus_cfg.user or ""
        password = milvus_cfg.password.get_secret_value() if milvus_cfg.password else ""
        if user:
            conn["user"] = user
            conn["password"] = password

        token = milvus_cfg.token.get_secret_value() if milvus_cfg.token else ""
        if token:
            conn["token"] = token
        logger.info(f"connection info: {conn}")
        return conn

    def _resolve_collection_prefix(self, config: AgentConfig) -> str:
        milvus_cfg = config.vector_store.milvus
        raw = milvus_cfg.collection_prefix or ""
        if raw:
            return re.sub(r"[^A-Za-z0-9_-]", "_", raw)
        base = config.org_id or "agentfoundry"
        return re.sub(r"[^A-Za-z0-9_-]", "_", base)

    # ------------------------------------------------------------------
    # Provider API
    # ------------------------------------------------------------------
    def get_store(self, org_id: str | None = None, **_: Any):
        org_key = str(org_id or "global")
        store = self._milvus_stores.get(org_key)
        if store is not None:
            logger.debug(
                "MilvusVectorStoreProvider reusing store org=%s collection=%s",
                org_key,
                self._collection_names.get(org_key, "<unknown>"),
            )
            return store

        collection = self._build_collection_name(org_key)
        logger.info(
            "MilvusVectorStoreProvider: connecting collection=%s host=%s",
            collection,
            self._connection_args.get("host", self._connection_args.get("uri", "")),
        )
        store = self._create_store(collection)
        self._milvus_stores[org_key] = store
        self._collection_names[org_key] = collection
        return store

    def _create_store(self, collection: str):
        errors = []

        try:
            from langchain_milvus import MilvusVectorStore as ModernMilvus

            logger.debug("Milvus provider: using langchain-milvus backend")
            start = time.perf_counter()
            store = ModernMilvus(
                embedding_function=self._embedding,
                connection_args=self._connection_args,
                collection_name=collection,
                text_field="text",
                vector_field="vector",
                primary_field="id",
                metadata_field="metadata",
                index_params=self._index_params or None,
                search_params=self._search_params or None,
                partition_names=self._partition_names or None,
                replica_number=self._replica_number,
                timeout=self._timeout,
                auto_id=self._auto_id,
            )
            duration = time.perf_counter() - start
            logger.info(
                "Milvus provider initialized langchain-milvus backend collection=%s duration=%.2fs",
                collection,
                duration,
            )
            return store
        except ImportError as exc:
            errors.append(exc)
        except Exception as exc:  # noqa: broad except - backend specific errors
            errors.append(exc)
            logger.debug("langchain-milvus backend unavailable: %s", exc, exc_info=True)

        try:
            from langchain_community.vectorstores import Milvus as LegacyMilvus
            from langchain_core._api.deprecation import LangChainDeprecationWarning

            warnings.filterwarnings(
                "ignore",
                category=LangChainDeprecationWarning,
                message="The class `Milvus` was deprecated",
            )

            start = time.perf_counter()
            store = LegacyMilvus(
                embedding_function=self._embedding,
                collection_name=collection,
                connection_args=self._connection_args,
                metadata_field="metadata",
                index_params=self._index_params,
                search_params=self._search_params,
                partition_names=self._partition_names,
                replica_number=self._replica_number,
                timeout=self._timeout,
                auto_id=self._auto_id,
                primary_field="id",
                text_field="text",
                vector_field="vector",
            )
            duration = time.perf_counter() - start
            logger.info(
                "Milvus provider initialized langchain-community backend collection=%s duration=%.2fs",
                collection,
                duration,
            )
            return store
        except ImportError as exc:
            errors.append(exc)

        raise RuntimeError(
            "MilvusVectorStoreProvider requires `langchain-milvus` or `langchain-community` with pymilvus installed."
        ) from (errors[-1] if errors else None)

    # ------------------------------------------------------------------
    # Custom similarity search to keep parity with other providers.
    # ------------------------------------------------------------------
    def similarity_search(self, query: str, k: int = 4, **kwargs: Any):  # type: ignore[override]
        org_id = kwargs.pop("org_id", None)
        filter_dict = kwargs.pop("filter", None) or kwargs.pop("where", None)

        # Treat any remaining keyword arguments (except internal helpers) as equality filters.
        extra_filters: Dict[str, Any] = {}
        for key in list(kwargs.keys()):
            if key in {"caller_role_level"}:
                kwargs.pop(key, None)
                continue
            extra_filters[key] = kwargs.pop(key)

        filter_dict = self._merge_filters(filter_dict, extra_filters)
        
        # Convert dict filter to Milvus boolean expression string
        milvus_expr = self._to_milvus_expr(filter_dict)

        store = self.get_store(org_id=org_id)

        try:
            start = time.perf_counter()
            # Pass 'expr' to Milvus for server-side filtering
            results = store.similarity_search(query, k=k, expr=milvus_expr)
            duration = time.perf_counter() - start
            logger.debug(
                "Milvus similarity_search org=%s expr=%r hits=%d duration=%.2fs",
                org_id or "global",
                milvus_expr,
                len(results),
                duration,
            )
            return results
        except Exception:
            logger.warning("Milvus provider: similarity search failed", exc_info=True)
            return []

    def _to_milvus_expr(self, filt: Optional[Dict[str, Any]]) -> str:
        """Convert a Mongo-style filter dictionary to a Milvus boolean expression string."""
        if not filt:
            return ""
            
        clauses = []
        for key, value in filt.items():
            if key in ("$and", "$or", "$not"):
                if key == "$and":
                    and_clauses = [self._to_milvus_expr(c) for c in value if c]
                    if and_clauses:
                        clauses.append(f"({' and '.join(and_clauses)})")
                elif key == "$or":
                    or_clauses = [self._to_milvus_expr(c) for c in value if c]
                    if or_clauses:
                        clauses.append(f"({' or '.join(or_clauses)})")
                elif key == "$not":
                    inner = self._to_milvus_expr(value)
                    if inner:
                        clauses.append(f"not ({inner})")
                continue

            # Identify target field (assume metadata if not primary fields)
            target = key
            if key not in ("id", "pk", "text"):
                target = f'metadata["{key}"]'

            # Field conditions
            # Check for operators dict
            if isinstance(value, dict):
                for op, val in value.items():
                    val_repr = json.dumps(val)  # Handles string quoting
                    if op == "$eq":
                        clauses.append(f"{target} == {val_repr}")
                    elif op == "$ne":
                        clauses.append(f"{target} != {val_repr}")
                    elif op == "$gt":
                        clauses.append(f"{target} > {val_repr}")
                    elif op == "$gte":
                        clauses.append(f"{target} >= {val_repr}")
                    elif op == "$lt":
                        clauses.append(f"{target} < {val_repr}")
                    elif op == "$lte":
                        clauses.append(f"{target} <= {val_repr}")
                    elif op == "$in":
                        # Milvus IN syntax: field in [1, 2]
                        list_repr = json.dumps(val)
                        clauses.append(f"{target} in {list_repr}")
            else:
                # Implicit equality
                val_repr = json.dumps(value)
                clauses.append(f"{target} == {val_repr}")
                    
        return " and ".join(clauses)

    # ------------------------------------------------------------------
    # Filter helpers
    # ------------------------------------------------------------------
    def _merge_filters(self, primary: Any, extras: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        base = primary if isinstance(primary, dict) else {}
        base = json.loads(json.dumps(base)) if base else {}
        for key, value in extras.items():
            base[key] = value
        return base or None

    def _filter_matches(self, metadata: Dict[str, Any], filt: Dict[str, Any]) -> bool:
        if not filt:
            return True
        if "$and" in filt:
            return all(self._filter_matches(metadata, clause) for clause in filt["$and"] if clause)
        if "$or" in filt:
            return any(self._filter_matches(metadata, clause) for clause in filt["$or"] if clause)
        if "$not" in filt:
            return not self._filter_matches(metadata, filt["$not"])

        for key, expected in filt.items():
            if key in {"$and", "$or", "$not"}:
                continue
            actual = metadata.get(key)
            if isinstance(expected, dict):
                if not self._match_operator(actual, expected):
                    return False
            else:
                if str(actual) != str(expected):
                    return False
        return True

    @staticmethod
    def _match_operator(actual: Any, condition: Dict[str, Any]) -> bool:
        for op, value in condition.items():
            if op == "$in":
                if str(actual) not in {str(v) for v in value}:
                    return False
            elif op == "$eq":
                if str(actual) != str(value):
                    return False
            elif op == "$ne":
                if str(actual) == str(value):
                    return False
            elif op == "$contains":
                if str(value) not in str(actual):
                    return False
            else:
                # Unknown operator – fail closed so filters remain strict
                return False
        return True

    # ------------------------------------------------------------------
    # Deterministic identifiers & utilities
    # ------------------------------------------------------------------
    @staticmethod
    def deterministic_id(text: str, user_id: str | None, org_id: str | None) -> str:  # noqa: D401
        digest = hashlib.sha256()
        digest.update((text or "").encode("utf-8"))
        digest.update((user_id or "").encode("utf-8"))
        digest.update((org_id or "").encode("utf-8"))
        return digest.hexdigest()

    def _build_collection_name(self, org_key: str) -> str:
        safe_org = re.sub(r"[^A-Za-z0-9_-]", "_", org_key)
        return f"{self._collection_prefix}_{safe_org}_{self._model_tag}"[:255]

    def purge_expired(self, retention_days: int = 0) -> None:  # noqa: D401
        logger.info("Milvus provider: purge_expired not implemented (no-op)")

    @staticmethod
    def _sanitise_connection_args(conn: Dict[str, Any]) -> Dict[str, Any]:
        redacted = dict(conn)
        for key in ("password", "token"):
            if key in redacted and redacted[key]:
                redacted[key] = "***"
        return redacted


# Register the provider exactly once (avoid duplicate registration when re-running main guard)
try:
    existing = VectorStoreFactory.get_provider_cls("milvus")
except Exception:  # pragma: no cover - factory may raise if registry empty
    existing = None

if existing is None:
    VectorStoreFactory.register_provider("milvus")(MilvusVectorStoreProvider)


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    import argparse
    import textwrap

    try:
        from langchain_core.documents import Document
    except ImportError as exc:
        raise RuntimeError("langchain-core is required for Milvus smoketest") from exc

    parser = argparse.ArgumentParser(
        description="Milvus provider smoketest – inserts and queries a document."
    )
    parser.add_argument("--org", default="smoke_org", help="Org identifier to scope collection")
    parser.add_argument("--text", default="hello Milvus", help="Text to insert and query")
    parser.add_argument("--query", default="hello", help="Query string to perform")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    print("=== Milvus Provider Smoketest ===")
    provider = MilvusVectorStoreProvider()
    store = provider.get_store(org_id=args.org)
    print(f"Collection ready: {provider._build_collection_name(args.org)}")

    doc_id = provider.deterministic_id(args.text, user_id="smoke_user", org_id=args.org)
    doc = Document(page_content=args.text, metadata={"org_id": args.org, "user_id": "smoke_user", "id": doc_id})
    print(f"Adding document id={doc_id}")
    store.add_documents([doc], ids=[doc_id])

    print(f"Querying Milvus for '{args.query}' ...")
    results = store.similarity_search(args.query, k=3)
    if not results:
        print("No results returned.")
    else:
        print(textwrap.dedent("\n".join(
            [
                f"Result {idx+1}: id={res.metadata.get('id')} score=N/A\n{res.page_content[:200]}"
                for idx, res in enumerate(results)
            ]
        )))

    print("Done. Consider cleaning up the test document manually if needed.")
