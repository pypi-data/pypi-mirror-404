"""VectorStoreFactory – central point to obtain vector-store instances."""

from __future__ import annotations

import logging
import threading
import warnings

from agentfoundry.utils.agent_config import AgentConfig

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """Return a LangChain VectorStore instance from the configured provider."""

    # --------------------------------------------------------------
    # Provider registry helpers (moved from providers.__init__)
    # --------------------------------------------------------------

    _REGISTRY: dict[str, type] = {}
    _CACHE: dict[str, object] = {}
    _LOCK = threading.Lock()

    @classmethod
    def register_provider(cls, name: str):
        """Decorator to register *provider class* under the given name."""

        def decorator(provider_cls):  # type: ignore[missing-return-type-doc]
            lower = name.lower()
            if lower in cls._REGISTRY:
                raise ValueError(f"Provider '{name}' already registered")
            cls._REGISTRY[lower] = provider_cls
            logger.debug(f"Registered vector-store provider '{lower}' -> {provider_cls}")
            return provider_cls

        return decorator

    @classmethod
    def get_provider_cls(cls, name: str):  # noqa: D401
        logger.info(f"Getting vector-store provider '{name}'")
        return cls._REGISTRY.get(name.lower())

    # Best-effort on-demand import for providers following the
    # '<name>_provider' module naming convention.
    @classmethod
    def _lazy_import_provider(cls, name: str) -> None:
        from importlib import import_module as _import_module
        mod_name = f"agentfoundry.vectorstores.providers.{name.lower()}_provider"
        try:
            _import_module(mod_name)
            logger.info(f"Lazy-imported vector-store provider module '{mod_name}'")
        except ModuleNotFoundError as _err:
            logger.warning(f"Vector-store provider module '{mod_name}' not found: {_err}")
        except Exception as _err:  # pragma: no cover – defensive logging
            logger.warning(f"Vector-store provider module '{mod_name}' failed to import: {_err}", exc_info=True)

    @classmethod
    def available_providers(cls):
        logger.info(f"Available vector-store providers: {cls._REGISTRY}")
        return list(cls._REGISTRY.keys())

    # --------------------------------------------------------------
    # Public factory methods
    # --------------------------------------------------------------

    @classmethod
    def get_store(cls, config: AgentConfig = None, provider: str | None = None, *, org_id: str | None = None, **kwargs):
        """Return a store from a singleton provider instance.

        Args:
            config: AgentConfig object (required for new code).
            provider: Explicit provider override.
            org_id: Organization ID for multi-tenant stores.
            **kwargs: Additional provider-specific arguments.

        Returns:
            VectorStore instance for the specified org.
        """
        # Handle backward compatibility
        if config is None:
            warnings.warn(
                "VectorStoreFactory.get_store() without config is deprecated. "
                "Pass AgentConfig explicitly.",
                DeprecationWarning,
                stacklevel=2
            )
            config = AgentConfig.from_legacy_config()
        
        # Resolve provider name
        prov_name = provider or config.vector_store.provider or "milvus"
        logger.info(f"VectorStore provider: {prov_name}")
        
        # Get the provider instance
        prov = cls.get_provider(config=config, provider=prov_name)
        
        # Ask the provider for a store appropriate for this org
        try:
            return prov.get_store(org_id=org_id, **kwargs)
        except TypeError:
            logger.error(f"Provider '{prov_name}' does not support org_id; using global store")
            return prov.get_store()

    @classmethod
    def get_provider(cls, config: AgentConfig = None, provider: str | None = None, **kwargs):
        """Instantiate and return a VectorStore provider.

        Args:
            config: AgentConfig object (required for new code).
            provider: Explicit provider override.
            **kwargs: Provider-specific constructor arguments (e.g. persist_directory for Chroma).

        Returns:
            VectorStore provider instance.
        """
        # Handle backward compatibility
        if config is None:
            warnings.warn(
                "VectorStoreFactory.get_provider() without config is deprecated. "
                "Pass AgentConfig explicitly.",
                DeprecationWarning,
                stacklevel=2
            )
            config = AgentConfig.from_legacy_config()
        
        # Resolve provider name
        provider_name = (provider or config.vector_store.provider or "milvus").lower()
        logger.info(f"VectorStoreFactory: provider={provider_name}")
        
        provider_cls = cls.get_provider_cls(provider_name)
        if provider_cls is None:
            logger.warning(f"VectorStoreFactory: provider={provider_name} not found; trying lazy import")
            # Try a lazy import once – accommodates environments where the
            # initial auto-import failed due to optional deps not being
            # available at interpreter start.
            cls._lazy_import_provider(provider_name)
            provider_cls = cls.get_provider_cls(provider_name)
            
        if provider_cls is None:
            error_msg = f"Unknown vector-store provider '{provider_name}'. Available providers: {cls.available_providers()}"
            raise ValueError(error_msg)

        # Cache instantiated providers: one instance per provider type
        # WARNING: This caching assumes the provider configuration (URL, API keys) 
        # is global or handled internally by the provider per-request.
        # If config changes (e.g. different Chroma URL), this singleton cache might be stale.
        # Ideally, cache key should include hash of config if provider is stateful.
        cache_key = provider_name
        if kwargs:
            # Include kwargs in the cache key so callers can request provider instances
            # with different constructor parameters (e.g. custom persist_directory for tests).
            try:
                suffix = ",".join(f"{k}={kwargs[k]}" for k in sorted(kwargs))
                cache_key = f"{provider_name}|{suffix}"
            except Exception:  # pragma: no cover - defensive fallback
                logger.debug("VectorStoreFactory: failed to build cache key from kwargs", exc_info=True)

        # Double-checked locking for thread safety
        if cache_key not in cls._CACHE:
            with cls._LOCK:
                if cache_key not in cls._CACHE:
                    logger.info(f"VectorStoreFactory initialising provider '{provider_name}'")
                    # Construct provider without org-specific kwargs; per-org stores are requested via get_store(...)
                    # We pass config to the constructor if accepted, but most legacy providers don't accept it yet.
                    try:
                        cls._CACHE[cache_key] = provider_cls(config=config, **kwargs)
                    except TypeError:
                        logger.debug(
                            f"Provider {provider_name} does not accept provided kwargs; "
                            "falling back to config-only init"
                        )
                        try:
                            cls._CACHE[cache_key] = provider_cls(config=config)
                        except TypeError:
                            logger.debug(f"Provider {provider_name} does not accept config in __init__; falling back to no-arg init")
                            cls._CACHE[cache_key] = provider_cls()

        return cls._CACHE[cache_key]

# ---------------------------------------------------------------------------
# Auto-import default provider modules so they self-register.
# ---------------------------------------------------------------------------

from importlib import import_module as _import_module  # noqa: E402

for _mod in (
    "agentfoundry.vectorstores.providers.faiss_provider",
    "agentfoundry.vectorstores.providers.chroma_provider",
    "agentfoundry.vectorstores.providers.milvus_provider",
):
    try:
        _import_module(_mod)
    except ModuleNotFoundError as _err:  # pragma: no cover
        logger.warning(f"Optional vector-store provider '{_mod}' could not be imported: {_err}")
    except Exception as _err:  # pragma: no cover
        logger.warning(
            f"Optional vector-store provider '{_mod}' failed to import: {_err}",
            exc_info=True,
        )
