from __future__ import annotations

import logging
import os
import time
from typing import Any, Iterable

from langchain_xai.chat_models import ChatXAI
from pydantic import PrivateAttr


def _truncate(s: str, limit: int) -> str:
    if limit <= 0:
        return s
    return s if len(s) <= limit else s[:limit] + "…"


def _summarize_input(input: Any) -> tuple[int, int, str]:
    """Return (message_count, total_chars, preview) for typical LC inputs."""
    try:
        # string prompt
        if isinstance(input, str):
            return (1, len(input), _truncate(input, 200))
        # list of dicts or messages
        if isinstance(input, (list, tuple)):
            msgs = []
            total = 0
            for m in input:
                role = getattr(m, "type", None) or getattr(m, "role", "")
                content = getattr(m, "content", None)
                if content is None and isinstance(m, dict):
                    content = m.get("content", "")
                s = str(content)
                total += len(s)
                msgs.append(f"{role or 'msg'}:{_truncate(s, 80)}")
            preview = " | ".join(msgs[:3])
            return (len(input), total, preview)
        # dict(single message)
        if isinstance(input, dict):
            content = str(input.get("content", ""))
            return (1, len(content), _truncate(content, 200))
    except Exception:
        pass
    # fallback
    s = str(input)
    return (1, len(s), _truncate(s, 200))


class LoggingChatXAI(ChatXAI):
    """
    ChatXAI with verbose logging for debugging Grok requests.

    Controlled by env:
      - AF_GROK_LOG_CONTENT: when "1" logs full content; else truncates
      - AF_GROK_LOG_TRUNCATE: max chars to log (default 240)
      - AF_GROK_LOG_LEVEL: logging level name (default INFO)
    """

    # Private logger to avoid Pydantic field enforcement
    _logger: logging.Logger = PrivateAttr(default_factory=lambda: logging.getLogger("agentfoundry.llm.grok"))

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        level = os.getenv("AF_GROK_LOG_LEVEL", "INFO").upper()
        try:
            self._logger.setLevel(getattr(logging, level, logging.INFO))
        except Exception:
            self._logger.setLevel(logging.INFO)
        self._logger.info(
            "Grok client ready model=%s base_url=%s timeout=%s",
            getattr(self, "model", None),
            getattr(self, "base_url", None),
            getattr(self, "timeout", None),
        )

    # Runnable.invoke
    def invoke(self, input: Any, config: Any | None = None, **kwargs: Any):  # type: ignore[no-untyped-def]
        content_all = os.getenv("AF_GROK_LOG_CONTENT", "0") in ("1", "true", "True")
        trunc = 0 if content_all else int(os.getenv("AF_GROK_LOG_TRUNCATE", "240"))
        mc, chars, preview = _summarize_input(input)
        self._logger.info(
            "invoke:start model=%s msgs=%d req_chars=%d preview=%s",
            getattr(self, "model", None),
            mc,
            chars,
            preview if trunc else _truncate(preview, trunc),
        )
        t0 = time.perf_counter()
        out = super().invoke(input, config=config, **kwargs)
        dt = int((time.perf_counter() - t0) * 1000)
        text = str(getattr(out, "content", None) or getattr(out, "text", ""))
        meta = getattr(out, "additional_kwargs", {}) or {}
        # Usage / metadata extraction (best-effort)
        usage = meta.get("usage") or {}
        pt = usage.get("prompt_tokens") or usage.get("input_tokens")
        ct = usage.get("completion_tokens") or usage.get("output_tokens")
        tt = usage.get("total_tokens")
        rid = meta.get("id") or meta.get("response_id") or meta.get("xai_id")
        finish = None
        try:
            ch = meta.get("choices")
            if isinstance(ch, list) and ch:
                finish = ch[0].get("finish_reason")
        except Exception:
            pass
        tool_calls = meta.get("tool_calls")
        calls = 0
        if isinstance(tool_calls, (list, tuple)):
            calls = len(tool_calls)
        elif tool_calls:
            calls = 1
        self._logger.info(
            "invoke:ok model=%s time_ms=%d resp_chars=%d tool_calls=%d finish=%s usage(p=%s c=%s t=%s) id=%s resp_preview=%s",
            getattr(self, "model", None),
            dt,
            len(text),
            calls,
            finish,
            pt,
            ct,
            tt,
            rid,
            text if trunc == 0 else _truncate(text, trunc),
        )
        if os.getenv("AF_GROK_LOG_JSON", "0") in ("1", "true", "True"):
            try:
                import json as _json
                self._logger.debug("invoke:raw_meta %s", _json.dumps(meta)[:4000])
            except Exception:
                pass
        return out

    # Runnable.stream
    def stream(self, input: Any, config: Any | None = None, **kwargs: Any):  # type: ignore[no-untyped-def]
        content_all = os.getenv("AF_GROK_LOG_CONTENT", "0") in ("1", "true", "True")
        trunc = 0 if content_all else int(os.getenv("AF_GROK_LOG_TRUNCATE", "240"))
        mc, chars, preview = _summarize_input(input)
        self._logger.info(
            "stream:start model=%s msgs=%d req_chars=%d preview=%s",
            getattr(self, "model", None),
            mc,
            chars,
            preview if trunc == 0 else _truncate(preview, trunc),
        )
        t0 = time.perf_counter()
        size = 0
        for chunk in super().stream(input, config=config, **kwargs):
            s = getattr(chunk, "content", None) or getattr(chunk, "text", "")
            s = str(s)
            size += len(s)
            self._logger.debug("stream:chunk size=%d preview=%s", len(s), s if trunc == 0 else _truncate(s, trunc))
            yield chunk
        dt = int((time.perf_counter() - t0) * 1000)
        self._logger.info("stream:done model=%s time_ms=%d total_chars=%d", getattr(self, "model", None), dt, size)

    # Async wrappers
    async def ainvoke(self, input: Any, config: Any | None = None, **kwargs: Any):  # type: ignore[no-untyped-def]
        content_all = os.getenv("AF_GROK_LOG_CONTENT", "0") in ("1", "true", "True")
        trunc = 0 if content_all else int(os.getenv("AF_GROK_LOG_TRUNCATE", "240"))
        mc, chars, preview = _summarize_input(input)
        self._logger.info(
            "ainvoke:start model=%s msgs=%d req_chars=%d preview=%s",
            getattr(self, "model", None),
            mc,
            chars,
            preview if trunc == 0 else _truncate(preview, trunc),
        )
        t0 = time.perf_counter()
        out = await super().ainvoke(input, config=config, **kwargs)
        dt = int((time.perf_counter() - t0) * 1000)
        text = str(getattr(out, "content", None) or getattr(out, "text", ""))
        meta = getattr(out, "additional_kwargs", {}) or {}
        usage = meta.get("usage") or {}
        pt = usage.get("prompt_tokens") or usage.get("input_tokens")
        ct = usage.get("completion_tokens") or usage.get("output_tokens")
        tt = usage.get("total_tokens")
        self._logger.info(
            "ainvoke:ok model=%s time_ms=%d resp_chars=%d usage(p=%s c=%s t=%s) resp_preview=%s",
            getattr(self, "model", None),
            dt,
            len(text),
            pt,
            ct,
            tt,
            text if trunc == 0 else _truncate(text, trunc),
        )
        if os.getenv("AF_GROK_LOG_JSON", "0") in ("1", "true", "True"):
            try:
                import json as _json
                self._logger.debug("ainvoke:raw_meta %s", _json.dumps(meta)[:4000])
            except Exception:
                pass
        return out
