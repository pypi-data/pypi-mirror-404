import importlib
import os

# Dynamically determine package version in both installed and source layouts
try:
    # Prefer installed package metadata (works for wheels & sdist installs)
    from importlib.metadata import version as _version, PackageNotFoundError  # type: ignore
except Exception:  # pragma: no cover
    from importlib_metadata import version as _version, PackageNotFoundError  # type: ignore


class LicenseError(RuntimeError):
    pass


try:
    # When running from source, the top-level package name may not be installed;
    # attempt the canonical distribution name first, then fallback to module name.
    try:
        __version__ = _version("agentfoundry")
    except PackageNotFoundError:
        __version__ = _version(__name__)
except PackageNotFoundError:
    # Fallback to VERSION file in source tree; final fallback is a dev tag
    here = os.path.dirname(__file__)
    try:
        with open(os.path.join(here, '..', 'VERSION'), 'r') as vf:
            __version__ = vf.read().strip()
    except Exception:
        __version__ = "0.0.0-dev"

# ---------------------------------------------------------------------------
# Enforce license at import time for all entry points.
# This guarantees that classes like Orchestrator are gated by a valid license.
# ---------------------------------------------------------------------------
try:
    if os.getenv("AGENTFOUNDRY_ENFORCE_LICENSE", "1") != "0":
        from agentfoundry.license.license import enforce_license as _af_enforce_license  # type: ignore
        _af_enforce_license()
except Exception as _lic_err:
    # Fail fast – users must provide a valid, unexpired license.
    raise LicenseError(f"{_lic_err}")

# Public API exports
from agentfoundry.registry.tool_registry import ToolRegistry
from agentfoundry.agents.base_agent import BaseAgent
from agentfoundry.agents.orchestrator import Orchestrator
from agentfoundry.license.license import enforce_license, verify_license
from agentfoundry.license.key_manager import get_license_key

__all__ = [
    "ToolRegistry",
    "BaseAgent",
    "Orchestrator",
    "enforce_license",
    "get_license_key",
]
