"""FAISS vector-store provider implementation."""

from __future__ import annotations

import logging
import os
import warnings

from agentfoundry.utils.agent_config import AgentConfig
from agentfoundry.vectorstores.base import VectorStore
from agentfoundry.vectorstores.factory import VectorStoreFactory

logger = logging.getLogger(__name__)


@VectorStoreFactory.register_provider("faiss")
class FAISSVectorStoreProvider(VectorStore):
    """Local persistent FAISS index wrapped as a LangChain VectorStore."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: AgentConfig = None, **kwargs):
        if getattr(self, "_initialized", False):
            return
        super().__init__(**kwargs)

        from langchain_community.vectorstores import FAISS  # local import to delay heavy deps
        from langchain_openai.embeddings import OpenAIEmbeddings

        # Handle backward compatibility
        if config is None:
            warnings.warn(
                "FAISSVectorStoreProvider() without config is deprecated. "
                "Pass AgentConfig explicitly.",
                DeprecationWarning,
                stacklevel=2
            )
            config = AgentConfig.from_legacy_config()
        
        self._config = config

        # Resolve index path from config
        index_path: str = str(config.vector_store.index_path or "").strip()
        if not index_path:
            if config.data_dir:
                index_path = os.path.join(str(config.data_dir), "faiss_index")
            else:
                index_path = "./faiss_index"
        
        embeddings = OpenAIEmbeddings()

        if os.path.exists(index_path):
            logger.info(f"Loading FAISS index from {index_path}")
            self._store = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        else:
            raise RuntimeError(f"FAISS index not found at '{index_path}'. Initialize the index with real data before use.")
        self._initialized = True

    def get_store(self, *args, **kwargs):
        logger.debug("FAISSVectorStoreProvider.get_store called")
        return self._store
