import pytest
import time
from unittest.mock import MagicMock, patch
from agentfoundry.cache.caching_layer import _LRU, CachingVectorProvider, Document
from agentfoundry.agents.memory.types import MemoryMetadata

# --- _LRU Tests ---

def test_lru_basic():
    lru = _LRU(cap=2, ttl_s=10)
    lru.set("a", 1)
    lru.set("b", 2)
    
    assert lru.get("a") == 1
    assert lru.get("b") == 2

    # Add 3rd item, should evict 'a' (oldest)
    lru.set("c", 3)
    assert lru.get("a") is None
    assert lru.get("b") == 2
    assert lru.get("c") == 3

def test_lru_ttl():
    lru = _LRU(cap=10, ttl_s=0.1)
    lru.set("a", 1)
    assert lru.get("a") == 1
    time.sleep(0.2)
    assert lru.get("a") is None

def test_lru_invalidate_prefix():
    lru = _LRU(cap=10, ttl_s=10)
    # Keys are tuples
    lru.set(("org1", "user1", "q1"), "res1")
    lru.set(("org1", "user2", "q2"), "res2")
    lru.set(("org2", "user1", "q3"), "res3")

    lru.invalidate_prefix(("org1",))
    
    assert lru.get(("org1", "user1", "q1")) is None
    assert lru.get(("org1", "user2", "q2")) is None
    assert lru.get(("org2", "user1", "q3")) == "res3"

def test_lru_invalidate_if():
    lru = _LRU(cap=10, ttl_s=10)
    lru.set(1, "one")
    lru.set(2, "two")
    lru.set(3, "three")

    # Remove even keys
    removed = lru.invalidate_if(lambda k: k % 2 == 0)
    assert removed == 1
    assert lru.get(1) == "one"
    assert lru.get(2) is None
    assert lru.get(3) == "three"


# --- CachingVectorProvider Tests ---

@pytest.fixture
def mock_remote_provider():
    provider = MagicMock()
    # Mocking id to be unique for singleton
    provider.__class__.__name__ = "MockProvider"
    return provider

@pytest.fixture
def caching_provider(mock_remote_provider):
    # Clear singleton to ensure fresh start
    CachingVectorProvider._INSTANCES = {}
    
    with patch("agentfoundry.cache.caching_layer._FlushThread") as MockFlushThread:
        # Mock the flusher so it doesn't run in background
        mock_flusher = MockFlushThread.return_value
        
        provider = CachingVectorProvider(mock_remote_provider, cache_dir="/tmp/test_cache")
        provider.emb = MagicMock() # Mock embeddings
        provider.emb.embed_query.return_value = [0.1, 0.2, 0.3]
        
        yield provider, mock_flusher

def test_add_documents(caching_provider):
    provider, mock_flusher = caching_provider
    doc = Document(page_content="test content", metadata={"id": "doc1", "org_id": "o1", "user_id": "u1", "role_level": 1})
    
    ids = provider.add_documents([doc])
    
    assert len(ids) == 1
    # Check if staged to local
    assert len(provider._local) == 1
    assert provider._local[0].doc.page_content == "test content"
    
    # Check if enqueued for flush
    mock_flusher.enqueue.assert_called()
    args = mock_flusher.enqueue.call_args[0][0]
    # args structure: ("add", doc, did, allow_update, kwargs)
    assert args[0] == "add"
    assert args[1].page_content == "test content"

def test_similarity_search_local_hit(caching_provider):
    provider, _ = caching_provider
    doc = Document(page_content="test content", metadata={"org_id": "o1", "user_id": "u1", "role_level": 1})
    
    # Add doc to local
    provider.add_documents([doc])
    
    # Search
    results = provider.similarity_search("test", k=1, org_id="o1", user_id="u1", caller_role_level=1)
    
    assert len(results) == 1
    assert results[0].page_content == "test content"
    # Remote should NOT be called if local hit is sufficient? 
    # Actually code says: "1) local ... 2) remote ... merged"
    # So remote IS called.
    provider.remote.similarity_search.assert_called()

def test_similarity_search_cache_hit(caching_provider):
    provider, _ = caching_provider
    provider.remote.similarity_search.return_value = [Document("remote doc")]
    
    # First search - miss
    res1 = provider.similarity_search("query", k=1, org_id="o1")
    assert len(res1) == 1
    assert res1[0].page_content == "remote doc"
    
    # Second search - hit
    provider.remote.similarity_search.reset_mock()
    res2 = provider.similarity_search("query", k=1, org_id="o1")
    assert len(res2) == 1
    # Remote should NOT be called
    provider.remote.similarity_search.assert_not_called()

def test_delete(caching_provider):
    provider, _ = caching_provider
    doc = Document(page_content="test", metadata={"__doc_id__": "d1", "org_id": "o1"})
    provider.add_documents([doc], ids=["d1"])
    
    assert len(provider._local) == 1
    
    provider.delete(ids=["d1"])
    
    assert len(provider._local) == 0
    provider.remote.delete.assert_called_with(ids=["d1"])
