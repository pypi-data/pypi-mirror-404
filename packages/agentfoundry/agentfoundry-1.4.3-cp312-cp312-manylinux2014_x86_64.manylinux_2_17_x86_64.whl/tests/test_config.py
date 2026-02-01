__author__ = "Chris Steel"
__copyright__ = "Copyright 2023, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "5/29/2023"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from agentfoundry.utils.config import Config, load_config


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"TEST_KEY": "test_value", "TEMPLATED": "{{ DATA_DIR }}/test"}, f)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def reset_config():
    """Reset Config singleton and load_config cache."""
    Config._instance = None
    yield


class TestConfig:
    """Test suite for Config class and load_config function."""

    def test_singleton(self, reset_config):
        """Test that Config and load_config return the same instance."""
        config1 = Config()
        config2 = Config()
        config3 = load_config()
        assert config1 is config2, "Config instances should be identical (singleton)"
        assert config1 is config3, "Config and load_config should return the same instance"

    def test_app_config_override(self, reset_config, temp_config_file):
        """Test overriding defaults with an application-supplied config file."""
        config = load_config(temp_config_file)
        assert config.get("TEST_KEY") == "test_value", "Should load TEST_KEY from app config"
        assert config.get("PROJECT_ROOT") == os.getcwd(), "PROJECT_ROOT should still be cwd"

    def test_env_variable_precedence(self, reset_config, temp_config_file):
        """Test environment variable precedence over config files."""
        with patch.dict(os.environ, {"AGENTFORGE_TEST_KEY": "env_value"}):
            config = load_config(temp_config_file)
            assert config.get("TEST_KEY") == "env_value", "Environment variable should override config file"

    def test_computed_directories(self, reset_config):
        """Test computed directory paths."""
        config = Config()
        assert config.get("PROJECT_ROOT") == os.getcwd(), "PROJECT_ROOT should be cwd"
        assert Path(config.get("DATA_DIR")).exists(), "DATA_DIR should exist"
        assert Path(config.get("CACHE_DIR")).exists(), "CACHE_DIR should exist"

    def test_fallback_defaults(self, reset_config):
        """Test fallback default values for specific keys."""
        config = Config()
        data_dir = config.get("DATA_DIR")
        assert config.get("CHROMADB_PERSIST_DIR") == f"{data_dir}/chromadb", "CHROMADB_PERSIST_DIR should use default"
        assert config.get("AUTH_CACHE_FILE") == f"{data_dir}/auth_tokens.json", "AUTH_CACHE_FILE should use default"
        assert config.get("MEMORY_CACHE_FILE") == f"{data_dir}/memory_cache.db", "MEMORY_CACHE_FILE should use default"

    def test_template_rendering(self, reset_config, temp_config_file):
        """Test rendering of {{ VAR }} placeholders."""
        config = load_config(temp_config_file)
        data_dir = config.get("DATA_DIR")
        assert config.get("TEMPLATED") == f"{data_dir}/test", "TEMPLATED should render with DATA_DIR"

    def test_all_method(self, reset_config):
        """Test the all() method returns a merged config dictionary."""
        config = Config()
        all_config = config.all()
        assert isinstance(all_config, dict), "all() should return a dictionary"
        for key in ("PROJECT_ROOT", "DATA_DIR", "CACHE_DIR", "CHROMADB_PERSIST_DIR"):
            assert key in all_config, f"all() should include {key}"
        assert all_config["CHROMADB_PERSIST_DIR"] == config.get("CHROMADB_PERSIST_DIR"), "all() should include fallback defaults"
