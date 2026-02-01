__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "2/9/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import logging
import os
import time
from datetime import datetime
from logging import Logger
from typing import Any, ClassVar, List, Optional

from langchain_core.language_models import LLM
from langchain_core.messages import HumanMessage
from langchain_core.outputs import Generation, LLMResult
from pydantic import Field

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError as exc:  # pragma: no cover - handled at runtime
    ChatGoogleGenerativeAI = None  # type: ignore[assignment]
    _GENAI_IMPORT_ERROR = exc
else:
    _GENAI_IMPORT_ERROR = None

from agentfoundry.utils.config import Config

logger = logging.getLogger(__name__)


def _truncate(text: str, limit: int) -> str:
    if limit <= 0:
        return text
    return text if len(text) <= limit else text[:limit] + "…"


def _coerce_text(payload: Any) -> str:
    """Best-effort extraction of textual content from Gemini responses."""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, (list, tuple)):
        collected: List[str] = []
        for item in payload:
            if isinstance(item, str):
                collected.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    collected.append(text)
                    continue
                content = item.get("content")
                if isinstance(content, str):
                    collected.append(content)
                    continue
            text = getattr(item, "text", None) or getattr(item, "content", None)
            if isinstance(text, str):
                collected.append(text)
        if collected:
            return "\n".join(collected)
        return " ".join(str(item) for item in payload)
    text_attr = getattr(payload, "text", None)
    if isinstance(text_attr, str):
        return text_attr
    content_attr = getattr(payload, "content", None)
    if isinstance(content_attr, str):
        return content_attr
    return str(payload)


def _summarize_input(payload: Any) -> tuple[int, int, str]:
    """Return (message_count, char_count, preview) for logging."""
    try:
        if isinstance(payload, str):
            return (1, len(payload), _truncate(payload, 200))
        if isinstance(payload, (list, tuple)):
            total = 0
            preview_parts: List[str] = []
            for item in payload:
                role = getattr(item, "type", None) or getattr(item, "role", "msg")
                content = getattr(item, "content", None)
                if content is None and isinstance(item, dict):
                    content = item.get("content", "")
                content_str = _coerce_text(content) if content is not None else ""
                total += len(content_str)
                preview_parts.append(f"{role}:{_truncate(content_str, 80)}")
            return (len(payload), total, " | ".join(preview_parts[:3]))
        if isinstance(payload, dict):
            content = _coerce_text(payload.get("content", ""))
            return (1, len(content), _truncate(content, 200))
    except Exception:
        pass
    payload_str = str(payload)
    return (1, len(payload_str), _truncate(payload_str, 200))


class GeminiLLM(LLM):
    """
    Gemini 3 wrapper that mirrors the OpenAI and Grok providers by delegating to
    LangChain's ChatGoogleGenerativeAI client.
    """

    api_key: str = Field(..., description="Your Gemini API key (aka Google API key)")
    model: str = Field(default="gemini-3-pro-preview", description="Gemini model to use")
    logger: Logger = Field(default=None, description="Logger instance")
    timeout: Optional[float] = Field(default=None, description="Timeout (seconds) for Gemini API calls")
    chat_model: ChatGoogleGenerativeAI = Field(default=None, description="ChatGoogleGenerativeAI model instance")
    HumanMessage: ClassVar[type] = HumanMessage

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if ChatGoogleGenerativeAI is None:
            raise ModuleNotFoundError(
                "langchain_google_genai is required for GeminiLLM. Install with `pip install langchain-google-genai`."
            ) from _GENAI_IMPORT_ERROR
        self.logger = self.logger or logging.getLogger("agentfoundry.llm.gemini")
        level = os.getenv("AF_GEMINI_LOG_LEVEL", "INFO").upper()
        try:
            self.logger.setLevel(getattr(logging, level, logging.INFO))
        except Exception:
            self.logger.setLevel(logging.INFO)
        if os.getenv("AF_GEMINI_LOG_CONTENT", "0") in ("1", "true", "True"):
            self._log_truncate = 0
        else:
            try:
                self._log_truncate = int(os.getenv("AF_GEMINI_LOG_TRUNCATE", "240"))
            except Exception:
                self._log_truncate = 240
        chat_kwargs: dict[str, Any] = {
            "model": self.model,
            "google_api_key": self.api_key,
            "convert_system_message_to_human": True,
        }
        if self.timeout is not None:
            chat_kwargs["timeout"] = self.timeout
        self.chat_model = ChatGoogleGenerativeAI(**chat_kwargs)
        self.logger.info("GeminiLLM initialized model=%s", self.model)

    @property
    def _llm_type(self) -> str:
        return "gemini"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        if isinstance(prompt, list):
            prompt = "\n".join(prompt)
        messages = [self.HumanMessage(content=prompt)]
        msg_count, char_count, preview = _summarize_input(messages)
        trunc_preview = preview if self._log_truncate == 0 else _truncate(preview, self._log_truncate)
        self.logger.info(
            "Gemini invoke:start model=%s msgs=%d prompt_chars=%d preview=%s",
            self.model,
            msg_count,
            char_count,
            trunc_preview,
        )
        t0 = time.perf_counter()
        try:
            result = self.chat_model.invoke(messages)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            raw = getattr(result, "content", None)
            if raw is None:
                raw = getattr(result, "text", None)
            if raw is None:
                raw = result
            text = _coerce_text(raw)
            text = str(text).strip()
            if stop:
                for s in stop:
                    idx = text.find(s)
                    if idx != -1:
                        text = text[:idx]
                        break
            resp_preview = text if self._log_truncate == 0 else _truncate(text, self._log_truncate)
            meta = getattr(result, "additional_kwargs", {}) or {}
            usage = meta.get("usage") or {}
            self.logger.info(
                "Gemini invoke:ok model=%s latency_ms=%d resp_chars=%d usage(input=%s, output=%s, total=%s) preview=%s",
                self.model,
                latency_ms,
                len(text),
                usage.get("prompt_tokens") or usage.get("input_tokens"),
                usage.get("completion_tokens") or usage.get("output_tokens"),
                usage.get("total_tokens"),
                resp_preview,
            )
            return text
        except Exception as e:
            self.logger.error("Gemini invoke:error model=%s err=%s", self.model, e, exc_info=True)
            raise RuntimeError(f"Error calling Gemini API: {e}") from e

    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs) -> LLMResult:
        generations: List[List[Generation]] = []
        for prompt in prompts:
            self.logger.info("Gemini generate:start model=%s", self.model)
            start_time = datetime.now()
            text = self._call(prompt, stop=stop, **kwargs)
            elapsed = datetime.now() - start_time
            preview = text if self._log_truncate == 0 else _truncate(text, self._log_truncate)
            self.logger.info(
                "Gemini generate:done model=%s duration=%s resp_chars=%d preview=%s",
                self.model,
                elapsed,
                len(text),
                preview,
            )
            generations.append([Generation(text=text)])
        return LLMResult(generations=generations)


if __name__ == "__main__":
    config = Config()
    key = config.get("GEMINI_API_KEY", "") or config.get("GOOGLE_API_KEY", "")
    if not key:
        raise ValueError("Please set the GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
    model = config.get("GEMINI_MODEL", "gemini-3-pro-preview")
    llm = GeminiLLM(api_key=key, model=model)
    response = llm.generate("Summarize why agent orchestration is useful in two sentences.")
    print("Gemini output:", response.generations[0][0].text)
