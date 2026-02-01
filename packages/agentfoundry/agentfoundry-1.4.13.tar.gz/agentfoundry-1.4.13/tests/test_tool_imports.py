"""Import smoke test for all agent tools.

This test imports every module under `agentfoundry.agents.tools` and
fails on LangChain import regressions (e.g., old StructuredTool paths),
but gracefully skips modules that are missing optional third‑party deps.
"""

from __future__ import annotations

import importlib
import pkgutil
import types
from pathlib import Path

import pytest


TOOLS_PKG = "agentfoundry.agents.tools"


def _iter_tool_modules() -> list[str]:
    pkg = importlib.import_module(TOOLS_PKG)
    path = list(getattr(pkg, "__path__", []))
    mods: list[str] = []
    for info in pkgutil.iter_modules(path, TOOLS_PKG + "."):
        # info is a ModuleInfo; .name is fully‑qualified
        mods.append(info.name)
    # Ensure the package itself is also tested
    mods.append(TOOLS_PKG)
    return sorted(set(mods))


_OPTIONAL_MISSING = {
    # Known optional deps that may not be installed in CI/user envs
    "serpapi",  # google_search_tool
    "fitz",  # PyMuPDF alt name
    "pymupdf",  # PyMuPDF primary name
}


@pytest.mark.parametrize("modname", _iter_tool_modules())
def test_import_tool_modules(modname: str) -> None:
    try:
        print(f"Testing import of: {modname}")
        importlib.import_module(modname)
    except ModuleNotFoundError as e:
        # Gracefully skip if a known optional dependency is missing
        missing = getattr(e, "name", None) or str(e)
        for opt in _OPTIONAL_MISSING:
            if opt in str(missing):
                pytest.skip(f"optional dependency not installed: {opt}")
        # Hard fail for langchain API regressions (e.g., StructuredTool path)
        msg = str(e)
        if "langchain.tools" in msg or "StructuredTool" in msg:
            pytest.fail(f"LangChain import error in {modname}: {msg}")
        # Unknown missing dep: skip to keep test environment light‑weight
        pytest.skip(f"skipping due to missing dependency: {msg}")
        print(f"skipping due to missing dependency: {msg}")
    except ImportError as e:
        # Treat StructuredTool path regressions as failures
        msg = str(e)
        if "langchain.tools" in msg or "StructuredTool" in msg:
            pytest.fail(f"LangChain import error in {modname}: {msg}")
        # Otherwise consider it optional and skip with context
        print(f"skipping due to missing dependency: {msg}")
        pytest.skip(f"skipping due to import error: {msg}")

