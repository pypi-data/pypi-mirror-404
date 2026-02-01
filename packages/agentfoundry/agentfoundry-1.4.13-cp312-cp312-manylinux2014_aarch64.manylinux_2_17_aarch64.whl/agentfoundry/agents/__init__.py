"""AgentFoundry agent exports."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = ["HierarchicalAutoGenOrchestrator"]


if TYPE_CHECKING:  # pragma: no cover - static analyzers only
    from .autogen_hierarchical import HierarchicalAutoGenOrchestrator as _HierarchicalAutoGenOrchestrator


def __getattr__(name: str) -> Any:
    if name == "HierarchicalAutoGenOrchestrator":
        try:
            module = import_module(".autogen_hierarchical", __name__)
        except ImportError:  # pragma: no cover - surfaces during runtime config
            raise
        return module.HierarchicalAutoGenOrchestrator
    raise AttributeError(name)
