"""Agentfoundry vector-store package.

This package provides a pluggable interface for different vector-store
back-ends (e.g., FAISS, Chroma, Milvus).  Concrete providers live in
`agentfoundry.vectorstores.providers`.  The `VectorStoreFactory` responsible
for choosing and instantiating a provider is located in
`agentfoundry.vectorstores.factory`.
"""

# Re-export commonly used API for convenience

from agentfoundry.vectorstores.factory import VectorStoreFactory  # noqa: F401
