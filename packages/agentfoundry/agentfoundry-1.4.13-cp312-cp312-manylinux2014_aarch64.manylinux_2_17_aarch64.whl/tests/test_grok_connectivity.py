from __future__ import annotations

import os
import pytest


pytestmark = pytest.mark.skipif(
    not (os.getenv("XAI_API_KEY") and os.getenv("GROK_TEST") == "1"),
    reason="Set XAI_API_KEY and GROK_TEST=1 to run live Grok connectivity tests",
)


def test_chatxai_basic():
    from langchain_xai.chat_models import ChatXAI

    api_key = os.environ["XAI_API_KEY"]
    model = os.getenv("GROK_MODEL", "grok-2-1212")
    client = ChatXAI(model=model, api_key=api_key)
    resp = client.invoke([{"role": "user", "content": "Say 'ok' only."}])
    text = getattr(resp, "content", None) or getattr(resp, "text", "") or str(resp)
    assert isinstance(text, str) and text.strip() != ""


def test_grokllm_basic():
    from agentfoundry.llm.grok_llm import GrokLLM

    api_key = os.environ["XAI_API_KEY"]
    model = os.getenv("GROK_MODEL", "grok-2-1212")
    llm = GrokLLM(api_key=api_key, model=model)
    res = llm.generate(["Respond with the single word: ok"])
    text = res.generations[0][0].text
    assert isinstance(text, str) and text.strip() != ""

