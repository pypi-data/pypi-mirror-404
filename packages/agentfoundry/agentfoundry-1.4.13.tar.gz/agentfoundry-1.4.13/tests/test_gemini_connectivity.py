from __future__ import annotations

import os

import pytest

pytest.importorskip(
    "langchain_google_genai",
    reason="langchain-google-genai package required for Gemini tests",
)

pytestmark = pytest.mark.skipif(
    not (
        (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        and os.getenv("GEMINI_TEST") == "1"
    ),
    reason="Set GEMINI_API_KEY (or GOOGLE_API_KEY) and GEMINI_TEST=1 to run live Gemini tests",
)


def _api_key() -> str:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""


def _response_text(response) -> str:
    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for chunk in content:
            if isinstance(chunk, dict):
                text = chunk.get("text") or chunk.get("content")
                if isinstance(text, str):
                    parts.append(text)
            else:
                text = getattr(chunk, "text", None) or getattr(chunk, "content", None)
                if isinstance(text, str):
                    parts.append(text)
        if parts:
            return "\n".join(parts)
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text
    return str(content or response)


def test_chatgoogle_basic():
    from langchain_google_genai import ChatGoogleGenerativeAI

    client = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3-pro-preview"),
        google_api_key=_api_key(),
        timeout=float(os.getenv("GEMINI_TIMEOUT", "45")),
    )
    resp = client.invoke([{"role": "user", "content": "Respond with 'ok' only."}])
    text = _response_text(resp)
    assert isinstance(text, str) and text.strip()


def test_geminillm_basic():
    from agentfoundry.llm.gemini_llm import GeminiLLM

    llm = GeminiLLM(
        api_key=_api_key(),
        model=os.getenv("GEMINI_MODEL", "gemini-3-pro-preview"),
        timeout=float(os.getenv("GEMINI_TIMEOUT", "45")),
    )
    res = llm.generate(["Say 'ok' only."])
    text = res.generations[0][0].text
    assert isinstance(text, str) and text.strip()
