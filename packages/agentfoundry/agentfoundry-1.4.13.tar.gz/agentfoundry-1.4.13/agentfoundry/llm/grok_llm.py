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
import sys
from datetime import datetime
from logging import Logger
from typing import ClassVar, List, Optional

# Add the project root to sys.path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ------------------------------------------------------------------
# AgentFoundry optional cache shim
# Some AF builds import agentfoundry.cache.caching_layer which may not be
# present locally. Inject a minimal passthrough shim BEFORE importing
# any blueprints or AF modules to avoid import-time failures.
# ------------------------------------------------------------------
try:
    import importlib
    importlib.import_module("agentfoundry.cache.caching_layer")
except Exception:
    import sys as _sys
    import types as _types
    import logging as _logging
    _logging.getLogger(__name__).warning("[grok_llm] Injecting agentfoundry.cache.caching_layer shim (module not found)")
    _cache_pkg = _types.ModuleType("agentfoundry.cache")
    _caching_layer_mod = _types.ModuleType("agentfoundry.cache.caching_layer")

    class CachingVectorProvider:  # type: ignore
        def __init__(self, provider):
            self._p = provider

        def __getattr__(self, name):
            return getattr(self._p, name)

    class CachingKGraph:  # type: ignore
        def __init__(self, kgraph):
            self._kg = kgraph

        def __getattr__(self, name):
            return getattr(self._kg, name)

    _caching_layer_mod.CachingVectorProvider = CachingVectorProvider
    _caching_layer_mod.CachingKGraph = CachingKGraph
    _sys.modules.setdefault("agentfoundry.cache", _cache_pkg)
    _sys.modules["agentfoundry.cache.caching_layer"] = _caching_layer_mod

from langchain_core.language_models import LLM
from langchain_core.messages import HumanMessage
from langchain_core.outputs import Generation, LLMResult
from langchain_xai.chat_models import ChatXAI
from pydantic import Field

from agentfoundry.utils.config import Config

logger = logging.getLogger(__name__)


class GrokLLM(LLM):
    """
    A generic Grok LLM class that interfaces with xAI's ChatCompletion API using
    LangChain's ChatXAI wrapper. This implementation delegates generation to ChatXAI,
    which uses the xAI API.
    """
    api_key: str = Field(..., description="Your xAI API key")
    model: str = Field(default="grok-2-1212", description="Grok model to use")
    logger: Logger = Field(default=None, description="Logger instance")
    chat_model: ChatXAI = Field(default=None, description="ChatXAI model instance")
    # Mark HumanMessage as a class variable, so Pydantic ignores it as a field.
    HumanMessage: ClassVar[type] = HumanMessage

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create an instance of ChatXAI with the proper parameters.
        self.chat_model = ChatXAI(model=self.model, api_key=self.api_key)
        logger.info("GrokLLM initialized.")

    @property
    def _llm_type(self) -> str:
        """Return a string identifier for this LLM."""
        return "grok"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        logger.info(f"Calling Grok API with prompt: {prompt}")
        # If the prompt is a list, join the elements into a single string.
        if isinstance(prompt, list):
            prompt = "\n".join(prompt)
        # Prepare messages in the format required by ChatXAI.
        messages = [{"role": "user", "content": prompt}]
        try:
            result = self.chat_model.invoke(messages)
            return result.content.strip()
        except Exception as e:
            raise RuntimeError(f"Error calling Grok API: {e}")

    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs) -> LLMResult:
        """Override LangChain's internal generator to add logging."""
        generations: List[List[Generation]] = []
        for prompt in prompts:
            logger.info(f"Generating text with Grok model: {self.model}")
            start_time = datetime.now()
            text = self._call(prompt, stop=stop, **kwargs)
            logger.info(f"Text generated: {text}")
            logger.info("Generation completed in %s seconds.", datetime.now() - start_time)
            generations.append([Generation(text=text)])
        return LLMResult(generations=generations)


if __name__ == "__main__":
    # Quick test to connect to Grok and get a response (requires real API key)
    api_key = os.getenv("XAI_API_KEY")
    if api_key:
        llm = GrokLLM(api_key=api_key, model="grok-2-1212")
        response = llm.generate("Hello, Grok! Tell me a short joke.")
        print("Grok Response:", response.generations[0][0].text)
    else:
        print("XAI_API_KEY not set. Skipping real API test.")
