import pytest
from unittest.mock import patch, MagicMock
from agentfoundry.llm.llm_factory import LLMFactory
from agentfoundry.utils.agent_config import AgentConfig

@pytest.fixture
def clean_llm_factory_cache():
    LLMFactory._CACHE.clear()
    yield
    LLMFactory._CACHE.clear()

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.llm.provider = "openai"
    config.llm.model_name = "gpt-4"
    config.llm.api_base = None
    config.get_api_key.return_value = "fake-key"
    return config

def test_get_llm_model_openai(clean_llm_factory_cache, mock_config):
    with patch("agentfoundry.llm.llm_factory.ChatOpenAI") as MockChat:
        llm = LLMFactory.get_llm_model(config=mock_config, provider="openai")
        MockChat.assert_called_once()
        assert llm == MockChat.return_value
        
        # Test Caching
        llm2 = LLMFactory.get_llm_model(config=mock_config, provider="openai")
        MockChat.assert_called_once() # Still called only once
        assert llm2 is llm

def test_get_llm_model_ollama(clean_llm_factory_cache, mock_config):
    mock_config.llm.provider = "ollama"
    with patch("agentfoundry.llm.llm_factory.OllamaLLM") as MockOllama:
        llm = LLMFactory.get_llm_model(config=mock_config, provider="ollama")
        MockOllama.assert_called_once()
        assert llm == MockOllama.return_value

def test_get_llm_model_missing_key(clean_llm_factory_cache, mock_config):
    mock_config.get_api_key.return_value = None
    with pytest.raises(ValueError):
        LLMFactory.get_llm_model(config=mock_config, provider="openai")

def test_get_llm_model_unknown_provider(clean_llm_factory_cache, mock_config):
    with pytest.raises(ValueError):
        LLMFactory.get_llm_model(config=mock_config, provider="unknown_provider")

def test_deprecated_call(clean_llm_factory_cache):
    with patch("agentfoundry.utils.agent_config.AgentConfig.from_legacy_config") as MockLegacy:
        # Should raise DeprecationWarning but not fail if legacy config works
        # mocking legacy config return
        mock_cfg = MockLegacy.return_value
        mock_cfg.llm.provider = "ollama"
        mock_cfg.get_api_key.return_value = "k"
        
        with patch("agentfoundry.llm.llm_factory.OllamaLLM"):
             with pytest.warns(DeprecationWarning):
                 LLMFactory.get_llm_model() # No config passed
