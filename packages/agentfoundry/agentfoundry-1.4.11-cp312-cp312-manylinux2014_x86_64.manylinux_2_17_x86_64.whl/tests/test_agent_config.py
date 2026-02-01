"""Tests for the modern AgentConfig class."""

import os
from unittest.mock import patch
from pydantic import SecretStr
from agentfoundry.utils.agent_config import AgentConfig

def test_agent_config_defaults():
    config = AgentConfig()
    assert config.org_id == "default"
    assert config.llm.provider == "openai"
    assert config.vector_store.provider == "milvus"

def test_agent_config_from_dict():
    data = {
        "AF_LLM_PROVIDER": "grok",
        "AF_XAI_API_KEY": "secret_key",
        "AF_MILVUS_URI": "http://milvus:19530",
        "AF_ORG_ID": "test_org"
    }
    
    config = AgentConfig.from_dict(data)
    
    assert config.llm.provider == "grok"
    assert config.xai_api_key.get_secret_value() == "secret_key"
    assert config.vector_store.milvus.uri == "http://milvus:19530"
    assert config.org_id == "test_org"

def test_agent_config_from_legacy_env():
    # Simulate legacy environment variables with UNDERSCORES
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "ollama",
        "OLLAMA_HOST": "http://ollama:11434",
        "ORG_ID": "legacy_org"
    }):
        config = AgentConfig.from_legacy_config()
        
        assert config.llm.provider == "ollama"
        assert config.llm.api_base == "http://ollama:11434"
        assert config.org_id == "legacy_org"

def test_get_api_key():
    config = AgentConfig()
    config.llm.provider = "openai"
    # Assign SecretStr, not string
    config.openai_api_key = SecretStr("sk-test")
    
    assert config.get_api_key() == "sk-test"
    
    config.llm.provider = "grok"
    config.xai_api_key = SecretStr("xai-test")
    assert config.get_api_key() == "xai-test"