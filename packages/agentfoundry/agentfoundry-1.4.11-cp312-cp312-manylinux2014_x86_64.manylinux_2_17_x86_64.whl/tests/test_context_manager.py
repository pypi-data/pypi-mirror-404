import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from agentfoundry.context.context_manager import ContextManager

@dataclass
class MockDocument:
    page_content: str
    metadata: dict

@pytest.fixture
def context_manager():
    # Limit: 1000 tokens, overhead: 100 -> Budget: 900
    return ContextManager(model_token_limit=1000, prompt_overhead_tokens=100)

@pytest.fixture
def mock_memories():
    with patch("agentfoundry.context.context_manager.ThreadMemory") as MockThread, \
         patch("agentfoundry.context.context_manager.UserMemory") as MockUser, \
         patch("agentfoundry.context.context_manager.OrgMemory") as MockOrg, \
         patch("agentfoundry.context.context_manager.GlobalMemory") as MockGlobal, \
         patch("agentfoundry.context.context_manager.count_tokens", side_effect=lambda x: len(x)): # Mock token count = char count
        
        yield {
            "thread": MockThread,
            "user": MockUser,
            "org": MockOrg,
            "global": MockGlobal
        }

def test_build_context_simple(context_manager, mock_memories):
    # Setup mocks
    mock_thread_inst = mock_memories["thread"].return_value
    mock_user_inst = mock_memories["user"].return_value
    mock_org_inst = mock_memories["org"].return_value
    mock_global_inst = mock_memories["global"].return_value

    # Create dummy docs
    # Thread: 1 doc, high relevance
    thread_doc = MockDocument("Thread Info", {"created_at": datetime.now(timezone.utc)})
    mock_thread_inst.search.return_value = [(thread_doc, 0.9)]

    # User: 1 doc
    user_doc = MockDocument("User Info", {"created_at": datetime.now(timezone.utc)})
    mock_user_inst.search.return_value = [(user_doc, 0.8)]

    # Org: empty
    mock_org_inst.search.return_value = []
    
    # Global: empty
    mock_global_inst.search.return_value = []

    ctx = context_manager.build_context(
        query="test",
        thread_id="t1",
        user_id="u1",
        org_id="o1",
        user_role_level=1
    )

    assert len(ctx) == 2
    assert "Thread Info" in ctx
    assert "User Info" in ctx
    # Thread usually has higher weight, so it should be first if scoring works as expected
    assert ctx[0] == "Thread Info"

def test_build_context_token_limit(context_manager, mock_memories):
    # Setup mocks
    mock_thread_inst = mock_memories["thread"].return_value
    mock_memories["user"].return_value.search.return_value = []
    mock_memories["org"].return_value.search.return_value = []
    mock_memories["global"].return_value.search.return_value = []

    # Create a long document that exceeds budget (900 tokens)
    # 1 token approx 4 chars. 4000 chars ~ 1000 tokens.
    long_text = "a" * 4000 
    long_doc = MockDocument(long_text, {"created_at": datetime.now(timezone.utc)})
    
    short_text = "Short info"
    short_doc = MockDocument(short_text, {"created_at": datetime.now(timezone.utc)})

    # Return both. High score for long doc.
    mock_thread_inst.search.return_value = [
        (long_doc, 0.95),
        (short_doc, 0.90)
    ]

    ctx = context_manager.build_context(
        query="test",
        thread_id="t1",
        user_id="u1",
        org_id="o1",
        user_role_level=1
    )

    # Long doc should be skipped because it fits the budget? 
    # Logic: "if used_tokens + chunk.tokens > budget: continue"
    # long_text (1000 tokens) > 900 budget -> skip
    # short_text (small) < 900 -> include

    assert len(ctx) == 1
    assert ctx[0] == "Short info"

def test_build_context_deduplication(context_manager, mock_memories):
    mock_thread_inst = mock_memories["thread"].return_value
    mock_user_inst = mock_memories["user"].return_value
    mock_memories["org"].return_value.search.return_value = []
    mock_memories["global"].return_value.search.return_value = []

    # Same text in thread and user
    text = "Duplicate Info"
    doc1 = MockDocument(text, {"created_at": datetime.now(timezone.utc)})
    doc2 = MockDocument(text, {"created_at": datetime.now(timezone.utc)})

    # Thread has lower raw score, but higher tier weight
    mock_thread_inst.search.return_value = [(doc1, 0.5)] 
    # User has higher raw score, but lower tier weight
    mock_user_inst.search.return_value = [(doc2, 0.6)]

    ctx = context_manager.build_context(
        query="test",
        thread_id="t1",
        user_id="u1",
        org_id="o1",
        user_role_level=1
    )

    assert len(ctx) == 1
    assert ctx[0] == "Duplicate Info"

def test_recency_decay(context_manager, mock_memories):
    mock_user_inst = mock_memories["user"].return_value
    mock_memories["thread"].return_value.search.return_value = []
    mock_memories["org"].return_value.search.return_value = []
    mock_memories["global"].return_value.search.return_value = []

    # Old doc vs New doc
    now = datetime.now(timezone.utc)
    old_date = now - timedelta(hours=24) # 2 half-lives -> 0.25 decay
    new_date = now

    old_doc = MockDocument("Old Info", {"created_at": old_date})
    new_doc = MockDocument("New Info", {"created_at": new_date})

    # Even if old doc has higher vector score, decay might push it down
    # old: 0.9 * 0.25 = 0.225
    # new: 0.5 * 1.0 = 0.5
    mock_user_inst.search.return_value = [
        (old_doc, 0.9),
        (new_doc, 0.5)
    ]

    ctx = context_manager.build_context(
        query="test",
        thread_id="t1",
        user_id="u1",
        org_id="o1",
        user_role_level=1
    )

    # New info should come first due to decay
    assert ctx[0] == "New Info"
    assert ctx[1] == "Old Info"

