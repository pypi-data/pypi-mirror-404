"""Singleton configuration loader for AgentFoundry."""

from __future__ import annotations

import json
import logging
import os
import tomllib  # noqa
from pathlib import Path
from typing import Optional

from jinja2 import Template

logger = logging.getLogger(__name__)


class Config:
    """Singleton config manager."""

    _instance: Optional[Config] = None

    def __new__(cls, config_path: Optional[str] = None):
        if cls._instance is None:
            logger.info(f"Creating Config singleton with config_path: {config_path}")
            cls._instance = super().__new__(cls)
            # Ensure _config exists even if initialization fails so callers
            # never hit an AttributeError when accessing .get(...)
            try:
                cls._instance._config = {}
            except Exception:  # noqa
                pass
            try:
                cls._instance._initialize(config_path)
            except Exception as e:
                # Keep running with an empty config; callers can rely on env
                # overrides or computed defaults inside get().
                logger.error(f"Config initialization failed: {e}", exc_info=True)
        return cls._instance

    def _initialize(self, config_path: Optional[str]):
        logger.debug(f"Initializing Config (config_path={config_path!r})")

        # 1. Copy default TOML to CWD as template (best-effort) - NO - DO NOT DO THIS!

        # 2. Determine config file path
        cfg_file = None
        if config_path:
            cfg_file = Path(config_path)
        else:
            env_cfg = os.getenv("AGENTFOUNDRY_CONFIG_FILE")
            if env_cfg:
                cfg_file = Path(env_cfg)

        if not cfg_file:
            logger.info("No configuration file specified (AGENTFOUNDRY_CONFIG_FILE not set). Using defaults/env vars.")
            self._config = {}
            return

        # 3. Load Config
        if not cfg_file.exists():
            logger.warning(f"Specified configuration file not found: {cfg_file}")
            self._config = {}
            return

        logger.info(f"Loading configuration from {cfg_file}")
        try:
            if cfg_file.suffix.lower() == ".json":
                with cfg_file.open("r") as f:
                    self._config = json.load(f)
            else:
                with cfg_file.open("rb") as f:
                    self._config = tomllib.load(f)
            logger.debug(f"Configuration loaded, keys: {list(self._config.keys())}")
        except Exception as e:
            logger.error(f"Failed to load config from {cfg_file}: {e}", exc_info=True)
            self._config = {}

    def get(self, key: str, default=None):
        """Get a configuration value by key, checking env var override."""
        env_key = key.upper().replace(".", "_")
        logger.debug(f"Retrieving key {key!r} (env override={env_key!r})")
        val = os.getenv(env_key)
        if val is not None and val != "":
            logger.debug(f"Config Override: Key '{key}' loaded from environment variable '{env_key}'")
            return val
        # Check for project-prefixed env var, then legacy prefixes, then unprefixed
        prefixes = [Path(os.getcwd()).name.upper(), "AGENTFOUNDRY", "AGENTFORGE"]
        seen: set[str] = set()
        for prefix in prefixes:
            if not prefix or prefix in seen:
                continue
            seen.add(prefix)
            k = f"{prefix}_{env_key}"
            val = os.getenv(k)
            if val is not None and val != "":
                logger.info(f"Config Override: Key '{key}' loaded from project environment variable '{k}'")
                return val

        # Computed defaults for core directories
        if key == "PROJECT_ROOT":
            return os.getcwd()
        if key == "DATA_DIR":
            # Default data directory from config or XDG
            data_dir = os.path.expanduser(self._render(self._config.get("DATA_DIR","./data")))
            Path(data_dir).mkdir(parents=True, exist_ok=True)
            return data_dir
        if key == "CACHE_DIR":
            data_dir = self.get("DATA_DIR")
            cache = os.path.expanduser(self._render(f"{data_dir}/cache"))
            Path(cache).mkdir(parents=True, exist_ok=True)
            return cache
        if key == "CHROMADB_PERSIST_DIR":
            data_dir = self.get("DATA_DIR")
            chroma_dir = os.path.expanduser(self._render(f"{data_dir}/chromadb"))
            Path(chroma_dir).mkdir(parents=True, exist_ok=True)
            return chroma_dir

        # Traverse nested keys in TOML
        parts = key.split(".")
        cfg = getattr(self, "_config", {})
        for part in parts:
            if not isinstance(cfg, dict) or part not in cfg:
                logger.debug(f"Key {key!r} not found in config; checking fallback for default")
                # fallback defaults for well-known paths
                # use top-level DATA_DIR (flattened PATHS section)
                data_dir = self.get("DATA_DIR")
                if key == "AUTH_CACHE_FILE":
                    return os.path.expanduser(self._render(f"{data_dir}/auth_tokens.json"))
                if key == "MEMORY_CACHE_FILE":
                    return os.path.expanduser(self._render(f"{data_dir}/memory_cache.db"))
                if key == "registry_db_path":
                    # support top-level or legacy [PATHS] section
                    reg = self.get("REGISTRY_DB") or self.get("PATHS.REGISTRY_DB")
                    return os.path.expanduser(reg)
                if key == "TOOLS_DIR":
                    # Default tools directory relative to project root
                    proj = self.get("PROJECT_ROOT")
                    return os.path.expanduser(self._render(f"{proj}/tools"))
                val = self._render(default)
                if default is not None:
                    logger.warning(f"Key {key} not found; returning default value: {default}")
                    logger.info(f"Config Source: Key '{key}' used default fallback value")
                else:
                    error: str = f"Key {key} not found"
                    logger.error(f"{error}; raising exception")
                    raise Exception(error)
                return os.path.expanduser(val) if isinstance(val, str) else val
            cfg = cfg[part]
        logger.debug(f"Found config[{key}] = {cfg}")
        val = self._render(cfg)
        logger.info(f"Config Source: Key '{key}' loaded from configuration file")
        return os.path.expanduser(val) if isinstance(val, str) else val

    def _render(self, val):
        """Render any {{ VAR }} placeholders using the current config context."""
        if isinstance(val, str) and "{{" in val and "}}" in val:
            # Render placeholders with both raw config values and computed defaults
            ctx = dict(self._config)
            # inject computed directory keys
            for key in ("PROJECT_ROOT", "DATA_DIR", "CACHE_DIR",
                        "AUTH_CACHE_FILE", "MEMORY_CACHE_FILE"):
                try:
                    ctx[key] = self.get(key)
                except Exception:  # noqa
                    pass
            return Template(val).render(**ctx)
        return val

    def all(self) -> dict:
        """
        Return a flattened dict of key→value for core config entries and fallbacks.
        """
        result: dict = {}
        for k in ("PROJECT_ROOT", "DATA_DIR", "CACHE_DIR", "CHROMADB_PERSIST_DIR"):
            result[k] = self.get(k)
        # include simple top-level entries from loaded config
        for k, v in self._config.items():
            if not isinstance(v, dict):
                result[k] = self.get(k)
        return result


def load_config(config_path: Optional[str] = None) -> Config:  # noqa
    """Return the singleton Config instance."""
    logger.debug(f"load_config called with config_path={config_path!r}")
    return Config(config_path)


if __name__ == "__main__":
    # Example usage
    config = load_config()
    print(f"CONFIG_DIR: {config.get('CONFIG_DIR', 'NONE')}")
    print(f"DATA_DIR: {config.get('DATA_DIR', 'NONE')}")
    print(f"TOOLS_DIR: {config.get('TOOLS_DIR', 'NONE')}")
    print(f"REGISTRY_DB: {config.get('REGISTRY_DB', 'NONE')}")
    print(f"CHROMADB_PERSIST_DIR: {config.get('CHROMADB_PERSIST_DIR', 'NONE')}")
    print(f"CODING_MODEL: {config.get('CODING_MODEL', 'NONE')}")
    print(f"OPENAI_MODEL: {config.get('OPENAI_MODEL', 'NONE')}")
    print(f"OPENAI_API_KEY: {config.get('OPENAI_API_KEY', 'NONE')}")
    print(f"CHROMA.COLLECTION_NAME: {config.get('CHROMA.COLLECTION_NAME', 'NONE')}")
    print(f"MS.CLIENT_ID: {config.get('MS.CLIENT_ID', 'NONE')}")
    print(f"MS.TENANT_ID: {config.get('MS.TENANT_ID', 'NONE')}")
    print(f"MS.CLIENT_SECRET: {config.get('MS.CLIENT_SECRET', 'NONE')}")
    print(f"FAISS.INDEX_PATH: {config.get('FAISS.INDEX_PATH', 'NONE')}")
    print(f"OLLAMA.HOST: {config.get('OLLAMA.HOST', 'NONE')}")
    print(f"OLLAMA.MODEL: {config.get('OLLAMA.MODEL', 'NONE')}")
    print(config.get("EMBEDDING.MODEL_NAME", "default_value"))
