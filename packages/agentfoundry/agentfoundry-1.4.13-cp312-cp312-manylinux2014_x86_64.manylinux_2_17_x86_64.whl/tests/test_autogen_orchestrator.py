from __future__ import annotations

import os
import sys
import types

import pytest

pytest.importorskip("autogen")

_license_core = types.ModuleType("agentfoundry.license._license_core")
_license_core.current_machine_id = lambda: b"test-machine"
_license_core.validate_license = lambda *args, **kwargs: (True, {})
sys.modules.setdefault("agentfoundry.license._license_core", _license_core)

from agentfoundry.agents.autogen_hierarchical import HierarchicalAutoGenOrchestrator
from agentfoundry.registry.tool_registry import ToolRegistry
from agentfoundry.llm.llm_factory import LLMFactory


def _ensure_openai_llm() -> None:
    try:
        LLMFactory.get_llm_model(provider="openai")
    except ValueError as exc:  # Missing API key or config
        pytest.skip(f"OpenAI configuration not available: {exc}")


def test_hierarchical_orchestrator_end_to_end():
    os.environ.setdefault("AGENTFOUNDRY_ENFORCE_LICENSE", "0")
    _ensure_openai_llm()

    registry = ToolRegistry()
    registry.agent_tools = {
        "data_retrieval": [],
        "data_processing": [],
        "decision_making": [],
        "output_generation": [],
    }

    orchestrator = HierarchicalAutoGenOrchestrator(registry)

    config = {
        "configurable": {
            "user_id": "pytest-user",
            "thread_id": "pytest-thread",
            "org_id": "pytest-org",
            "security_level": "10",
        }
    }
    message = {
        "role": "user",
        "content": (
            "Gather a brief project status summary, clean the findings, prioritise follow-up actions, "
            "and deliver a concise report."
        ),
    }

    reply, details = orchestrator.chat([message], config=config, additional=True)

    assert isinstance(reply, str) and reply.strip()
    stages = details.get("stages", {})
    assert {"data_retrieval", "data_processing", "decision_making", "output_generation"}.issubset(stages.keys())

