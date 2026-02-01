__author__ = "Chris Steel"
__copyright__ = "Copyright 2023, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "2/9/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import logging
import sys

from langchain_openai import ChatOpenAI

from agentfoundry.llm.ollama_llm import OllamaLLM
from agentfoundry.utils.config import load_config

logger = logging.getLogger(__name__)


class LLMFactory:
    """Singleton factory caching LLM clients per (provider, model)."""

    _instance = None
    _CACHE: dict[tuple[str, str], object] = {}
    _LOGGED_CONFIG_ONCE: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def get_llm_model(provider: str | None = None, llm_model: str | None = None):
        """
        Returns an instance of an LLM based on configuration.

        The configuration should define:
          - LLM_PROVIDER: e.g., "ollama", "openai", "grok", or "gemini"
          - For Ollama:
              - OLLAMA.MODEL (default: "codegemma:7b-instruct")
              - OLLAMA.HOST (default: "http://127.0.0.1:11434")
          - For OpenAILLM:
              - OPENAI_API_KEY
              - OPENAI_MODEL (default: "o4-mini")
          - For Grok:
              - XAI_API_KEY
              - GROK_MODEL (default: "grok-2-1212")
          - For Gemini:
              - GEMINI_API_KEY (or GOOGLE_API_KEY)
              - GEMINI_MODEL (default: "gemini-3-pro-preview")

        Raises:
            ValueError: If the LLM provider is unknown, or the required settings are missing.
        """
        prelim_key = (str(provider or ""), str(llm_model or ""))
        if provider and prelim_key in LLMFactory._CACHE:
            return LLMFactory._CACHE[prelim_key]

        logger.debug("Getting LLM")
        config = load_config()
        if not LLMFactory._LOGGED_CONFIG_ONCE:
            # Avoid leaking secrets in logs; mask keys like *KEY, *SECRET, *TOKEN
            def _mask(val):
                try:
                    if isinstance(val, dict):
                        out = {}
                        for k, v in val.items():
                            if any(s in str(k).upper() for s in ("KEY", "SECRET", "TOKEN", "PASSWORD")):
                                out[k] = "***"
                            else:
                                out[k] = _mask(v)
                        return out
                except Exception:
                    pass
                return val
            try:
                cfg_dump = _mask(getattr(config, "_config", {}))
            except Exception:
                cfg_dump = {}
            logger.info(f"Loaded configuration (sanitized): {cfg_dump}")
            LLMFactory._LOGGED_CONFIG_ONCE = True
        provider = provider or config.get("LLM_PROVIDER", "openai")
        logger.info(f"Creating LLM model of type: {provider}")
        cache_key = (str(provider), str(llm_model or ""))
        if cache_key in LLMFactory._CACHE:
            return LLMFactory._CACHE[cache_key]

        if provider == "ollama":
            model_name = config.get("OLLAMA.MODEL", "gemma3:27b")
            host = config.get("OLLAMA.HOST", "http://127.0.0.1:11434")
            logger.info(f"Using ChatOllama model: {model_name}")
            try:
                llm = OllamaLLM(model=model_name, base_url=host)
                LLMFactory._CACHE[cache_key] = llm
                return llm
            except Exception as e:
                logger.error(f"Failed to create ChatOllama LLM: {e}")
                raise

        elif provider == "openai":
            openai_api_key = config.get("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY must be provided for OpenAILLM LLM.")
            model = llm_model or config.get("OPENAI_MODEL", "o4-mini")
            logger.info(f"Using OpenAI model: {model}")
            restricted_prefixes = ("o1", "o2", "o3", "o4", "gpt-4o")
            import os as _os
            temp_cfg = _os.getenv("TEMPERATURE", "")
            pass_temperature = True
            if isinstance(model, str) and model.lower().startswith(restricted_prefixes):
                pass_temperature = False
            if temp_cfg in (None, ""):
                pass_temperature = False
            try:
                if pass_temperature:
                    try:
                        temperature = float(temp_cfg)
                    except Exception:
                        temperature = None
                else:
                    temperature = None
                if temperature is None:
                    llm = ChatOpenAI(model=model, api_key=openai_api_key)
                else:
                    llm = ChatOpenAI(model=model, api_key=openai_api_key, temperature=temperature)
                LLMFactory._CACHE[cache_key] = llm
                return llm
            except Exception as e:
                logger.error(f"Failed to create OpenAI LLM: {e}")
                raise

        elif provider == "grok":
            import os as _os
            from agentfoundry.llm.grok_chatxai_logging import LoggingChatXAI as ChatXAI
            xai_api_key = _os.getenv("XAI_API_KEY") or config.get("XAI_API_KEY", "")
            if not xai_api_key:
                raise ValueError("XAI_API_KEY must be provided for Grok LLM.")
            model = llm_model or config.get("GROK_MODEL", "grok-2-1212")
            logger.info(f"Using Grok model: {model}")
            # Return logging-enabled ChatXAI so LangGraph receives a ChatModel
            llm = ChatXAI(model=model, api_key=xai_api_key)
            LLMFactory._CACHE[cache_key] = llm
            return llm
        elif provider == "gemini":
            import os as _os
            from agentfoundry.llm.gemini_llm import GeminiLLM

            gemini_api_key = (
                config.get("GEMINI_API_KEY", "")
                or config.get("GOOGLE_API_KEY", "")
                or _os.getenv("GOOGLE_API_KEY", "")
            )
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY must be provided for Gemini LLM.")
            model = llm_model or config.get("GEMINI_MODEL", "gemini-3-pro-preview")
            logger.info(f"Using Gemini model: {model}")
            llm = GeminiLLM(model=model, api_key=gemini_api_key)
            LLMFactory._CACHE[cache_key] = llm
            return llm

        else:
            raise ValueError(f"Unknown LLM provider: {provider}")


if __name__ == "__main__":
    logger = logging.getLogger("simple_logger")
    logger.setLevel(logging.DEBUG)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    messages = [{"role": "user", "content": "Write a short poem about the stars."}]

    openai_llm = LLMFactory.get_llm_model(provider="openai")
    print("OpenAI LLM instance created:", openai_llm)
    output = openai_llm.invoke(messages)
    print("OpenAI Generated output:", output)

    ollama_llm = LLMFactory.get_llm_model(provider="ollama")
    print("Ollama LLM instance created:", ollama_llm)
    ollama_output = ollama_llm.invoke(messages)
    print("Ollama Generated output:", ollama_output.content)
