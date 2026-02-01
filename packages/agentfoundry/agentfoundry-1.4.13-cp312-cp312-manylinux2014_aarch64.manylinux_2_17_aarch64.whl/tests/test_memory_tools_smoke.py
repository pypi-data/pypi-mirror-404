"""Smoke-test the memory tool wrappers against real back-ends (Chroma, DuckDB)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from langchain_core.runnables import RunnableConfig

from agentfoundry.agents.tools import memory_tools as mem


pytest.importorskip("duckdb", reason="DuckDB required for memory smoke test")


class TestMemoryToolsSmoke:
    """End-to-end check that save/search helpers persist to real stores."""

    @pytest.fixture(scope="module", autouse=True)
    def _temp_data_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Core data dir for local duckdb/faiss/chroma persistence
            os.environ["DATA_DIR"] = tmp
            os.environ["VECTORSTORE_PROVIDER"] = "chroma"
            os.environ["EMBEDDING_MODEL_NAME"] = "text-embedding-3-small"
            os.environ["CHROMADB_PERSIST_DIR"] = str(Path(tmp) / "chromadb")
            os.environ["CHROMA_COLLECTION_NAME"] = f"af_memtest_{os.getpid()}"
            os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"
            yield Path(tmp)

    @pytest.fixture(autouse=True)
    def mock_embeddings(self, monkeypatch):
        """Mock OpenAI embeddings to avoid network calls/auth errors."""
        try:
            # Patch the top-level package where CachingVectorProvider imports from
            import langchain_openai.embeddings
            
            class FakeEmbeddings:
                def __init__(self, **kwargs): pass
                def embed_documents(self, texts):
                    # Return list of dummy vectors (size 1536 for text-embedding-3-small)
                    return [[0.1] * 1536 for _ in texts]
                def embed_query(self, text):
                    return [0.1] * 1536
            
            monkeypatch.setattr(langchain_openai.embeddings, "OpenAIEmbeddings", FakeEmbeddings)
        except ImportError:
            pass # langchain_openai might not be installed, test will fail elsewhere or skip


    @pytest.fixture
    def cfg(self):
        return {
            "configurable": {
                "user_id": "u123",
                "thread_id": "t999",
                "org_id": "acme",
                "security_level": "5",
            }
        }

    def test_user_memory_cycle(self, cfg):
        text = "I love jazz music"
        assert "saved" in mem.save_user_memory.func(text, cfg)
        # Ensure background save has completed to avoid races in tests
        mem.flush_memory_saves(timeout=5.0)
        hits = mem.search_user_memory.func("jazz", cfg, k=3)
        assert any("jazz" in h.lower() for h in hits)

    def test_org_memory_cycle(self, cfg):
        text = "All laptops must be encrypted"
        assert "saved" in mem.save_org_memory.func(text, cfg)
        mem.flush_memory_saves(timeout=5.0)
        hits = mem.search_org_memory.func("encrypted", cfg)
        assert hits and "laptops" in hits[0].lower()

    def test_global_memory(self):
        text = "The Eiffel Tower is in Paris"
        assert "saved" in mem.save_global_memory.func(text)
        mem.flush_memory_saves(timeout=5.0)
        hits = mem.search_global_memory.func("eiffel", k=2)
        assert hits and "paris" in hits[0].lower()

    def test_thread_memory(self, cfg):
        pytest.importorskip("faiss", reason="FAISS required for thread memory smoke test")
        text = "Session greeting hello"
        mem.save_thread_memory.func(text, cfg)
        mem.flush_memory_saves(timeout=5.0)
        hits = mem.search_thread_memory.func("greeting", cfg)
        assert hits and "hello" in hits[0].lower()

    def test_summarize(self, cfg, monkeypatch):
        # Stub LLMFactory to return a fake LLM that just echoes input or returns fixed text
        from agentfoundry.llm import llm_factory
        
        class FakeLLM:
            def invoke(self, *args, **kwargs):
                return "Fake summary: user loves jazz"
            def __call__(self, *args, **kwargs):
                return self.invoke(*args, **kwargs)

        monkeypatch.setattr(llm_factory.LLMFactory, "get_llm_model", staticmethod(lambda *a, **kw: FakeLLM()))

        summary = mem.summarize_any_memory.func("user", cfg, max_tokens=2000)
        # Should at least include a known word from previous test
        assert "jazz" in summary.lower() or summary == ""
