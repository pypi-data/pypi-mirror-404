from __future__ import annotations

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
from datetime import datetime
from logging import Logger
from typing import Any, ClassVar, List, Optional

from langchain_core.language_models import LLM
from langchain_core.messages import HumanMessage
from langchain_core.outputs import Generation, LLMResult
from langchain_xai.chat_models import ChatXAI
from pydantic import Field

logger = logging.getLogger(__name__)


class GrokLLM(LLM):
    """
    Pure-Python Grok LLM wrapper using langchain-xai's ChatXAI client.

    This class intentionally implements `_call` with the modern LangChain
    signature to satisfy the ABC in langchain_core>=0.3.74.
    """

    api_key: str = Field(..., description="Your xAI API key")
    model: str = Field(default="grok-2-1212", description="Grok model to use")
    logger: Logger = Field(default=None, description="Logger instance")
    chat_model: ChatXAI = Field(default=None, description="ChatXAI model instance")
    HumanMessage: ClassVar[type] = HumanMessage

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        key = self.api_key or os.getenv("XAI_API_KEY")
        if not key:
            raise ValueError("XAI_API_KEY must be provided for GrokLLM")
        self.chat_model = ChatXAI(model=self.model, api_key=key)
        logger.info("GrokLLM (py) initialized for model %s", self.model)

    @property
    def _llm_type(self) -> str:
        return "grok"

    # Align with ChatOpenAI interface used in logs/debugging
    @property
    def model_name(self) -> str:  # pragma: no cover - trivial accessor
        return self.model

    @property
    def _identifying_params(self) -> dict:  # pragma: no cover
        return {"model_name": self.model}

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> str:
        # Prepare messages for ChatXAI; it expects OpenAI-style chat format
        if isinstance(prompt, list):  # defensive: accept list -> join
            prompt = "\n".join(prompt)
        messages = [{"role": "user", "content": prompt}]
        try:
            result = self.chat_model.invoke(messages)
            text = getattr(result, "content", None) or getattr(result, "text", "") or str(result)
            text = str(text).strip()
            if stop:
                for s in stop:
                    idx = text.find(s)
                    if idx != -1:
                        text = text[:idx]
                        break
            return text
        except Exception as e:
            raise RuntimeError(f"Error calling Grok API: {e}")

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> LLMResult:
        generations: List[List[Generation]] = []
        for prompt in prompts:
            start_time = datetime.now()
            text = self._call(prompt, stop=stop, run_manager=run_manager, **kwargs)
            logger.info("GrokLLM (py) generated text in %s", datetime.now() - start_time)
            generations.append([Generation(text=text)])
        return LLMResult(generations=generations)
