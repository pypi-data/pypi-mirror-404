"""Providers sub-package (kept minimal – all heavy lifting in individual modules)."""

# Intentionally left almost empty; importing this package triggers provider
# modules indirectly via `agentfoundry.vectorstores.factory` which auto-imports
# the default providers.

# Re-export registry helpers for backward compatibility with older imports
from agentfoundry.vectorstores.factory import VectorStoreFactory
from agentfoundry.vectorstores.providers.chroma_client import ChromaDBClient
from agentfoundry.vectorstores.providers.chroma_provider import ChromaVectorStoreProvider
from agentfoundry.vectorstores.providers.milvus_provider import MilvusVectorStoreProvider

register_provider = VectorStoreFactory.register_provider  # type: ignore
get_provider_cls = VectorStoreFactory.get_provider_cls  # type: ignore
available_providers = VectorStoreFactory.available_providers  # type: ignore
