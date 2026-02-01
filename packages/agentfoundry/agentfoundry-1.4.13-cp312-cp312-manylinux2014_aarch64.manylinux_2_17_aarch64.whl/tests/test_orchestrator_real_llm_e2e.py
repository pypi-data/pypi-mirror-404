"""End-to-end tests for Orchestrator.run_task using a real LLM.

Skips when OPENAI_API_KEY is not present. Uses OpenAI Chat model via
LLMFactory with a small, inexpensive model to keep tests fast.
"""

from __future__ import annotations

import os
import pytest

from agentfoundry.agents.orchestrator import Orchestrator
from agentfoundry.registry.tool_registry import ToolRegistry


requires_openai = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not configured"
)


@pytest.fixture(autouse=True)
def _set_real_llm_env(monkeypatch):
    """Ensure we use the OpenAI provider and a small model for speed."""
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    # Prefer widely available small model name
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    # Keep summaries cheap if they get called indirectly
    monkeypatch.setenv("AF_SUMMARY_MAX_DOCS", "20")
    yield


@pytest.fixture
def orchestrator_fresh() -> Orchestrator:
    # Reset singleton to ensure no interference from other tests
    try:
        Orchestrator._instance = None  # type: ignore[attr-defined]
        Orchestrator._initialized = False  # type: ignore[attr-defined]
    except Exception:
        pass
    reg = ToolRegistry()
    reg.agent_tools = {}  # explicit, empty tool map
    return Orchestrator(reg)


@requires_openai
def test_run_task_basic_real_llm(orchestrator_fresh: Orchestrator):
    reply = orchestrator_fresh.run_task(
        "Respond with a one-word friendly greeting.",
        use_memory=False,
        allow_tools=False,
    )
    assert isinstance(reply, str) and len(reply.strip()) > 0


@requires_openai
def test_run_task_return_additional_real_llm(orchestrator_fresh: Orchestrator):
    out = orchestrator_fresh.run_task(
        "Say OK.",
        additional=True,
        use_memory=False,
        allow_tools=False,
    )
    assert isinstance(out, tuple) and len(out) == 2
    reply, responses = out
    assert isinstance(reply, str) and len(reply) > 0
    assert isinstance(responses, dict) and "messages" in responses and responses["messages"]


@requires_openai
def test_run_task_with_and_without_memory_real_llm(orchestrator_fresh: Orchestrator):
    # Without memory – should compile a no-memory supervisor and respond
    r1 = orchestrator_fresh.run_task(
        "State the word 'OK' once.",
        use_memory=False,
        allow_tools=False,
    )
    assert isinstance(r1, str) and len(r1) > 0

    # With memory – compiles a fresh supervisor with checkpointer
    r2 = orchestrator_fresh.run_task(
        "Acknowledge with a short response.",
        use_memory=True,
        allow_tools=False,
    )
    assert isinstance(r2, str) and len(r2) > 0


@requires_openai
def test_run_task_allow_tools_path_compiles_real_llm(orchestrator_fresh: Orchestrator):
    # Even with no tools registered, allow_tools=True exercises that code path
    reply = orchestrator_fresh.run_task(
        "Reply briefly with OK.",
        use_memory=False,
        allow_tools=True,
        allowed_tool_names=[],
    )
    assert isinstance(reply, str) and len(reply) > 0

