__author__ = "Chris Steel"
__copyright__ = "Copyright 2023, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "2/9/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import logging
import os
import warnings

from langchain_openai import ChatOpenAI

from agentfoundry.llm.ollama_llm import OllamaLLM
from agentfoundry.utils.agent_config import AgentConfig

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM clients, with caching per (provider, model, api_key)."""

    _CACHE: dict[tuple[str, str, str], object] = {}

    @staticmethod
    def get_llm_model(
        config: AgentConfig = None,
        provider: str | None = None,
        llm_model: str | None = None,
        api_base: str | None = None,
    ):
        """
        Returns an instance of an LLM based on configuration.

        Args:
            config: AgentConfig object containing credentials and settings.
                    Required for new code. If None, falls back to legacy config with deprecation warning.
            provider: Explicit provider override (e.g. 'openai').
            llm_model: Explicit model override (e.g. 'gpt-4').
            api_base: Explicit API base URL override (e.g. Ollama host).

        Returns:
            LLM instance (ChatOpenAI, OllamaLLM, etc.)
        """
        # Handle backward compatibility
        if config is None:
            warnings.warn(
                "LLMFactory.get_llm_model() without config is deprecated. "
                "Pass AgentConfig explicitly or use AgentConfig.from_legacy_config().",
                DeprecationWarning,
                stacklevel=2
            )
            config = AgentConfig.from_legacy_config()
        
        # Extract configuration
        provider = provider or config.llm.provider
        llm_model = llm_model or config.llm.model_name
        api_key_val = config.get_api_key(provider) or ""
        api_base = api_base or config.llm.api_base

        # Create a cache key that includes the API key (hashed or raw) to prevent tenant leakage
        cache_key = (str(provider), str(llm_model), str(api_key_val))
        
        if cache_key in LLMFactory._CACHE:
            return LLMFactory._CACHE[cache_key]

        logger.info(f"Creating LLM model: provider={provider} model={llm_model}")

        if provider == "ollama":
            model_name = llm_model or "gemma3:27b"
            host = api_base or "http://127.0.0.1:11434"
            try:
                llm = OllamaLLM(model=model_name, base_url=host)
                LLMFactory._CACHE[cache_key] = llm
                return llm
            except Exception as e:
                logger.error(f"Failed to create ChatOllama LLM: {e}")
                raise

        elif provider == "openai":
            if not api_key_val:
                raise ValueError("OPENAI_API_KEY must be provided for OpenAI LLM.")
            
            # Temperature handling
            restricted_prefixes = ("o1", "o2", "o3", "o4", "gpt-4o")
            temp_cfg = os.getenv("TEMPERATURE", "")
            pass_temperature = True
            if isinstance(llm_model, str) and llm_model.lower().startswith(restricted_prefixes):
                pass_temperature = False
            if temp_cfg in (None, ""):
                pass_temperature = False
            
            try:
                temperature = float(temp_cfg) if pass_temperature else None
                if temperature is None:
                    llm = ChatOpenAI(model=llm_model, api_key=api_key_val)
                else:
                    llm = ChatOpenAI(model=llm_model, api_key=api_key_val, temperature=temperature)
                LLMFactory._CACHE[cache_key] = llm
                return llm
            except Exception as e:
                logger.error(f"Failed to create OpenAI LLM: {e}")
                raise

        elif provider == "grok":
            if not api_key_val:
                raise ValueError("XAI_API_KEY must be provided for Grok LLM.")
            # Return logging-enabled ChatXAI to integrate cleanly with LangGraph
            from agentfoundry.llm.grok_chatxai_logging import LoggingChatXAI
            llm = LoggingChatXAI(model=llm_model, api_key=api_key_val)
            LLMFactory._CACHE[cache_key] = llm
            return llm

        elif provider == "gemini":
            from agentfoundry.llm.gemini_llm import GeminiLLM
            if not api_key_val:
                raise ValueError("GEMINI_API_KEY must be provided for Gemini LLM.")
            llm = GeminiLLM(model=llm_model, api_key=api_key_val)
            LLMFactory._CACHE[cache_key] = llm
            return llm

        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    @staticmethod
    def get_llm_by_role(config: AgentConfig = None, role: str = "reasoning"):
        """Return an LLM instance for the given role.

        Roles:
            "reasoning" (default) -> config.llm  (primary model)
            "formatting"          -> config.llm_formatter (structured-output model)

        If no formatter config is present, falls back to the primary model.
        """
        if config is None:
            from agentfoundry.utils.agent_config import AgentConfig as _AC
            config = _AC.from_legacy_config()

        if role == "formatting" and config.llm_formatter is not None:
            fmt = config.llm_formatter
            return LLMFactory.get_llm_model(
                config=config,
                provider=fmt.provider,
                llm_model=fmt.model_name,
                api_base=fmt.api_base,
            )
        return LLMFactory.get_llm_model(config=config)


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    try:
        openai_llm = LLMFactory.get_llm_model(provider="openai")
        print("OpenAI LLM:", openai_llm)
    except Exception as e:
        print(f"Skipping OpenAI test: {e}")