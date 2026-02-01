"""Tests that organisation-scoped memories are isolated across org IDs.

We create separate OrgMemory and UserMemory instances for two different
organisations and assert that data stored in one organisation is not visible
from the other.
"""

from __future__ import annotations

import tempfile

# ---------------------------------------------------------------------------
# Monkey-patch Chroma embedding BEFORE any AgentFoundry imports pull it in.
# ---------------------------------------------------------------------------

from chromadb.utils import embedding_functions as _ef  # type: ignore

# ---------------------------------------------------------------------------
# Stub KGraphFactory to avoid pulling optional duckdb-based dependency in CI.
# ---------------------------------------------------------------------------

import types, sys


class _DummyKG:
    def upsert_fact(self, *_, **__):  # noqa: D401
        return "dummy"

    def search(self, *_, **__):  # noqa: D401
        return []


class _DummyKGFactory:
    _inst = None

    @classmethod
    def get_instance(cls):  # noqa: D401
        if cls._inst is None:
            cls._inst = cls()
        return cls

    def get_kgraph(self, *_args, **_kwargs):  # noqa: D401
        return _DummyKG()


sys.modules['agentfoundry.kgraph.factory'] = types.ModuleType('agentfoundry.kgraph.factory')
sys.modules['agentfoundry.kgraph.factory'].KGraphFactory = _DummyKGFactory


class _DummyEF:  # noqa: D401  (test helper)
    """Return zero vectors to avoid heavy model downloads during tests."""

    def __init__(self, *_, **__):
        pass

    def __call__(self, texts):  # type: ignore[no-self-use]
        import numpy as np

        return np.zeros((len(texts), 768)).tolist()


_ef.SentenceTransformerEmbeddingFunction = _DummyEF  # type: ignore[attr-defined]

# Now we can safely import memory classes.
from agentfoundry.agents.memory.org_memory import OrgMemory
from agentfoundry.agents.memory.user_memory import UserMemory


def test_org_memory_isolation():
    """Ensure OrgMemory data cannot be retrieved from a different org."""

    with tempfile.TemporaryDirectory() as tmpdir:
        org1 = OrgMemory("org1", data_dir=tmpdir)
        org2 = OrgMemory("org2", data_dir=tmpdir)

        org1.add_semantic_item("secret for org1")

        hits_org1 = " ".join(org1.semantic_search("secret", k=3)).lower()
        hits_org2 = " ".join(org2.semantic_search("secret", k=3)).lower()

        assert "secret" in hits_org1, "Org1 should retrieve its own data"
        assert "secret" not in hits_org2, "Org2 should NOT see Org1 data"


def test_user_memory_cross_org_isolation():
    """Same user_id in different orgs must have isolated stores."""

    with tempfile.TemporaryDirectory() as tmpdir:
        user_org1 = UserMemory("u1", org_id="org1", data_dir=tmpdir)
        user_org2 = UserMemory("u1", org_id="org2", data_dir=tmpdir)

        user_org1.add_semantic_item("personal note in org1")

        hits1 = " ".join(user_org1.semantic_search("personal", k=3)).lower()
        hits2 = " ".join(user_org2.semantic_search("personal", k=3)).lower()

        assert "personal" in hits1, "User memory should be retrievable in same org"
        assert "personal" not in hits2, "User memory must not leak across orgs"
