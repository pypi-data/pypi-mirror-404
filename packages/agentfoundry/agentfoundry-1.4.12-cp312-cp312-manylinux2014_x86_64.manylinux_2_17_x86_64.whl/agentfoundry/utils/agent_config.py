from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path
from typing import Optional, Dict, Any, Union

from pydantic import BaseModel, Field, SecretStr, model_validator

# Try to import Config for backward compatibility defaults
try:
    from agentfoundry.utils.config import Config
    _HAS_LEGACY_CONFIG = True
except ImportError:
    _HAS_LEGACY_CONFIG = False

logger = logging.getLogger(__name__)


class MilvusConfig(BaseModel):
    """Milvus-specific vector store configuration."""
    uri: Optional[str] = None
    host: Optional[str] = None
    port: int = 19530
    secure: bool = False
    user: Optional[str] = None
    password: Optional[SecretStr] = None
    token: Optional[SecretStr] = None
    collection_prefix: str = "agentfoundry_"
    timeout: float = 10.0
    auto_id: bool = True
    embedding_model: str = "text-embedding-ada-002"
    fallback_dim: int = 1536


class ChromaConfig(BaseModel):
    """ChromaDB-specific configuration."""
    url: Optional[str] = None
    collection_name: str = "agentfoundry"
    persist_dir: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)


class VectorStoreConfig(BaseModel):
    """Vector store configuration supporting multiple providers."""
    provider: str = "milvus"
    collection_name: str = "agentfoundry"
    url: Optional[str] = None
    persist_dir: Optional[str] = None
    api_key: Optional[SecretStr] = None
    index_path: Optional[str] = None  # For FAISS
    
    # Provider-specific configs
    milvus: MilvusConfig = Field(default_factory=MilvusConfig)
    chroma: ChromaConfig = Field(default_factory=ChromaConfig)


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = "openai"
    model_name: str = "gpt-4o"
    api_key: Optional[SecretStr] = None
    api_base: Optional[str] = None
    temperature: Optional[float] = None
    timeout: int = 120
    # Provider-specific extras (e.g. Ollama host)
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimensions: int = 384


class AgentConfig(BaseModel):
    """
    Explicit configuration object for AgentFoundry.
    
    This is the standard way to configure AgentFoundry components. Host applications
    (like Quantify) should create an AgentConfig and pass it to AgentForge entry points.
    
    For standalone/CLI usage, use AgentConfig.from_legacy_config() to load from
    environment variables and TOML files.
    """
    # Identity & Scope
    org_id: str = "default"
    user_id: str = "default_user"
    thread_id: str = "default_thread"
    security_level: int = 0

    # Core Components
    llm: LLMConfig = Field(default_factory=LLMConfig)
    llm_formatter: Optional[LLMConfig] = Field(
        default=None,
        description="Secondary LLM config for structured-output / formatting tasks. "
                    "When None, all roles fall back to the primary 'llm' config.",
    )
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    
    # API Keys for various services (all optional)
    openai_api_key: Optional[SecretStr] = None
    xai_api_key: Optional[SecretStr] = None
    serpapi_api_key: Optional[SecretStr] = None
    google_api_key: Optional[SecretStr] = None
    hf_token: Optional[SecretStr] = None
    gemini_api_key: Optional[SecretStr] = None
    
    # Microsoft credentials (for Entra/Graph tools)
    ms_tenant_id: Optional[str] = None
    ms_client_id: Optional[str] = None
    ms_client_secret: Optional[SecretStr] = None
    
    # Paths (if using local storage)
    data_dir: Optional[Path] = None
    tools_dir: Optional[Path] = None
    cache_dir: Optional[Path] = None
    registry_db: Optional[Path] = None
    
    # Global settings
    log_level: str = "INFO"
    
    # Allow arbitrary extra config for plugins
    extra: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_dict(cls, config: Dict[str, Any], prefix: str = "AF_") -> "AgentConfig":
        """
        Create AgentConfig from a flat dictionary with prefixed keys.
        
        This is the primary factory method for host applications like Quantify
        that load configuration from secrets backends and TOML files.
        
        Args:
            config: Flat dictionary with prefixed keys (e.g., AF_OPENAI_API_KEY)
            prefix: Key prefix to strip (default: "AF_")
        
        Returns:
            AgentConfig instance
        
        Example:
            config = {
                'AF_OPENAI_API_KEY': 'sk-...',
                'AF_LLM_PROVIDER': 'openai',
                'AF_OPENAI_MODEL': 'gpt-4o',
                'AF_VECTORSTORE_PROVIDER': 'milvus',
                'AF_MILVUS_URI': 'http://localhost:19530',
            }
            af_config = AgentConfig.from_dict(config)
        """
        def get(key: str, default=None):
            """Get value with or without prefix."""
            return config.get(f"{prefix}{key}") or config.get(key) or default
        
        def get_secret(key: str) -> Optional[SecretStr]:
            """Get value as SecretStr if present."""
            val = get(key)
            return SecretStr(val) if val else None
        
        # Determine LLM provider and model
        llm_provider = get("LLM_PROVIDER", "openai")
        if llm_provider == "openai":
            model_name = get("OPENAI_MODEL", "gpt-4o")
            api_key = get_secret("OPENAI_API_KEY")
            api_base = None
        elif llm_provider == "ollama":
            model_name = get("OLLAMA_MODEL", "gemma3:27b")
            api_key = None
            api_base = get("OLLAMA_HOST", "http://127.0.0.1:11434")
        elif llm_provider == "grok":
            model_name = get("GROK_MODEL", "grok-beta")
            api_key = get_secret("XAI_API_KEY")
            api_base = None
        elif llm_provider == "gemini":
            model_name = get("GEMINI_MODEL", "gemini-pro")
            api_key = get_secret("GEMINI_API_KEY") or get_secret("GOOGLE_API_KEY")
            api_base = None
        else:
            model_name = get("OPENAI_MODEL", "gpt-4o")
            api_key = get_secret("OPENAI_API_KEY")
            api_base = None
        
        # Determine formatter LLM (secondary model for structured output)
        fmt_provider = get("LLM_FORMATTER_PROVIDER")
        fmt_model = get("LLM_FORMATTER_MODEL")
        llm_formatter_cfg: Optional[LLMConfig] = None
        if fmt_provider or fmt_model:
            fmt_provider = fmt_provider or llm_provider
            if fmt_provider == "ollama":
                fmt_model = fmt_model or "gemma3:27b"
                fmt_api_key = None
                fmt_api_base = get("LLM_FORMATTER_HOST") or get("OLLAMA_HOST", "http://127.0.0.1:11434")
            elif fmt_provider == "openai":
                fmt_model = fmt_model or "gpt-4o"
                fmt_api_key = get_secret("OPENAI_API_KEY")
                fmt_api_base = None
            elif fmt_provider == "grok":
                fmt_model = fmt_model or "grok-beta"
                fmt_api_key = get_secret("XAI_API_KEY")
                fmt_api_base = None
            elif fmt_provider == "gemini":
                fmt_model = fmt_model or "gemini-pro"
                fmt_api_key = get_secret("GEMINI_API_KEY") or get_secret("GOOGLE_API_KEY")
                fmt_api_base = None
            else:
                fmt_model = fmt_model or "gpt-4o"
                fmt_api_key = get_secret("OPENAI_API_KEY")
                fmt_api_base = None
            llm_formatter_cfg = LLMConfig(
                provider=fmt_provider,
                model_name=fmt_model,
                api_key=fmt_api_key,
                api_base=fmt_api_base,
                timeout=int(get("LLM_FORMATTER_TIMEOUT", 120)),
            )

        # Build Milvus config
        milvus_config = MilvusConfig(
            uri=get("MILVUS_URI"),
            host=get("MILVUS_HOST"),
            port=int(get("MILVUS_PORT", 19530)),
            secure=get("MILVUS_SECURE", "false").lower() in ("true", "1", "yes"),
            user=get("MILVUS_USER"),
            password=get_secret("MILVUS_PASSWORD"),
            token=get_secret("MILVUS_TOKEN"),
            collection_prefix=get("MILVUS_COLLECTION_PREFIX", "agentfoundry_"),
            timeout=float(get("MILVUS_TIMEOUT", 10.0)),
            auto_id=get("MILVUS_AUTO_ID", "true").lower() in ("true", "1", "yes"),
            embedding_model=get("MILVUS_EMBEDDING_MODEL", "text-embedding-ada-002"),
            fallback_dim=int(get("MILVUS_FALLBACK_DIM", 1536)),
        )
        
        # Build Chroma config
        chroma_config = ChromaConfig(
            url=get("CHROMA_URL"),
            collection_name=get("CHROMA_COLLECTION_NAME", "agentfoundry"),
            persist_dir=get("CHROMADB_PERSIST_DIR"),
        )
        
        return cls(
            org_id=get("ORG_ID", "default"),
            user_id=get("USER_ID", "default_user"),
            thread_id=get("THREAD_ID", "default_thread"),
            security_level=int(get("SECURITY_LEVEL", 0)),
            llm=LLMConfig(
                provider=llm_provider,
                model_name=model_name,
                api_key=api_key,
                api_base=api_base,
                timeout=int(get("LLM_TIMEOUT", 120)),
            ),
            llm_formatter=llm_formatter_cfg,
            vector_store=VectorStoreConfig(
                provider=get("VECTORSTORE_PROVIDER", "milvus"),
                collection_name=get("COLLECTION_NAME", "agentfoundry"),
                url=get("CHROMA_URL") or get("MILVUS_URI"),
                persist_dir=get("CHROMADB_PERSIST_DIR"),
                index_path=get("FAISS_INDEX_PATH"),
                milvus=milvus_config,
                chroma=chroma_config,
            ),
            embedding=EmbeddingConfig(
                model_name=get("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"),
                dimensions=int(get("EMBEDDING_DIMENSIONS", 384)),
            ),
            openai_api_key=get_secret("OPENAI_API_KEY"),
            xai_api_key=get_secret("XAI_API_KEY"),
            serpapi_api_key=get_secret("SERPAPI_API_KEY"),
            google_api_key=get_secret("GOOGLE_API_KEY"),
            hf_token=get_secret("HF_TOKEN"),
            gemini_api_key=get_secret("GEMINI_API_KEY"),
            ms_tenant_id=get("MS_TENANT_ID"),
            ms_client_id=get("MS_CLIENT_ID"),
            ms_client_secret=get_secret("MS_CLIENT_SECRET"),
            data_dir=Path(get("DATA_DIR")) if get("DATA_DIR") else None,
            tools_dir=Path(get("TOOLS_DIR")) if get("TOOLS_DIR") else None,
            cache_dir=Path(get("CACHE_DIR")) if get("CACHE_DIR") else None,
            registry_db=Path(get("REGISTRY_DB")) if get("REGISTRY_DB") else None,
            log_level=get("LOG_LEVEL", "INFO"),
        )

    @classmethod
    def from_legacy_config(cls) -> "AgentConfig":
        """
        Factory to create an AgentConfig from the existing global/env system.
        
        This is for backward compatibility and standalone CLI usage. Host applications
        should use from_dict() instead.
        """
        if not _HAS_LEGACY_CONFIG:
            logger.warning("Legacy Config not available; returning default AgentConfig")
            return cls()
            
        legacy = Config()
        
        def get(k, default=None):
            try:
                return legacy.get(k, default)
            except Exception:
                return default

        # Map legacy keys to new structure
        llm_provider = get("LLM_PROVIDER", "openai")
        
        return cls(
            org_id=get("ORG_ID", "default"),
            llm=LLMConfig(
                provider=llm_provider,
                model_name=get("OPENAI_MODEL") or get("OLLAMA.MODEL") or "gpt-4o",
                api_key=SecretStr(get("OPENAI_API_KEY")) if get("OPENAI_API_KEY") else None,
                api_base=get("OLLAMA.HOST") if llm_provider == "ollama" else None,
            ),
            vector_store=VectorStoreConfig(
                provider=get("VECTORSTORE.PROVIDER", "milvus"),
                url=get("CHROMA.URL") or get("MILVUS.URI"),
                persist_dir=get("CHROMADB_PERSIST_DIR"),
                index_path=get("FAISS.INDEX_PATH"),
                milvus=MilvusConfig(
                    uri=get("MILVUS.URI"),
                    host=get("MILVUS.HOST"),
                    port=int(get("MILVUS.PORT", 19530)),
                    collection_prefix=get("MILVUS.COLLECTION_PREFIX", "agentfoundry_"),
                    timeout=float(get("MILVUS.TIMEOUT", 10.0)),
                ),
                chroma=ChromaConfig(
                    url=get("CHROMA.URL"),
                    collection_name=get("CHROMA.COLLECTION_NAME", "agentfoundry"),
                    persist_dir=get("CHROMA.PERSIST_DIR"),
                ),
            ),
            embedding=EmbeddingConfig(
                model_name=get("EMBEDDING.MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"),
            ),
            openai_api_key=SecretStr(get("OPENAI_API_KEY")) if get("OPENAI_API_KEY") else None,
            xai_api_key=SecretStr(get("XAI_API_KEY")) if get("XAI_API_KEY") else None,
            serpapi_api_key=SecretStr(get("SERPAPI_API_KEY")) if get("SERPAPI_API_KEY") else None,
            google_api_key=SecretStr(get("GOOGLE.API_KEY")) if get("GOOGLE.API_KEY") else None,
            hf_token=SecretStr(get("HF_TOKEN")) if get("HF_TOKEN") else None,
            ms_tenant_id=get("MS.TENANT_ID"),
            ms_client_id=get("MS.CLIENT_ID"),
            ms_client_secret=SecretStr(get("MS.CLIENT_SECRET")) if get("MS.CLIENT_SECRET") else None,
            data_dir=Path(get("DATA_DIR")) if get("DATA_DIR") else None,
            tools_dir=Path(get("TOOLS_DIR")) if get("TOOLS_DIR") else None,
            cache_dir=Path(get("CACHE_DIR")) if get("CACHE_DIR") else None,
            registry_db=Path(get("REGISTRY_DB")) if get("REGISTRY_DB") else None,
            log_level=get("LOGGING.LEVEL", "INFO"),
        )

    def get_api_key(self, provider: str = None) -> Optional[str]:
        """
        Get the API key for the specified or configured LLM provider.
        
        Args:
            provider: LLM provider name. If None, uses self.llm.provider.
        
        Returns:
            API key string or None
        """
        provider = provider or self.llm.provider
        
        if provider == "openai":
            key = self.llm.api_key or self.openai_api_key
        elif provider == "grok":
            key = self.llm.api_key or self.xai_api_key
        elif provider == "gemini":
            key = self.llm.api_key or self.gemini_api_key or self.google_api_key
        else:
            key = self.llm.api_key
        
        return key.get_secret_value() if key else None
    
    def get_api_key_for_config(self, llm_config: LLMConfig) -> Optional[str]:
        """Get the API key for an arbitrary LLMConfig using this AgentConfig's key store."""
        provider = llm_config.provider
        key = llm_config.api_key
        if not key:
            if provider == "openai":
                key = self.openai_api_key
            elif provider == "grok":
                key = self.xai_api_key
            elif provider == "gemini":
                key = self.gemini_api_key or self.google_api_key
        return key.get_secret_value() if key else None

    def get_secret(self, name: str) -> Optional[str]:
        """
        Get a secret value by name.
        
        Args:
            name: Secret name (e.g., 'serpapi_api_key', 'hf_token')
        
        Returns:
            Secret value string or None
        """
        attr = getattr(self, name, None)
        if isinstance(attr, SecretStr):
            return attr.get_secret_value()
        return attr
