"""
Client State Context Manager.

Provides a ContextVar storage for client context (page info, UI state)
passed from the frontend during a request. Uses contextvars for async safety.
"""
from __future__ import annotations
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Dict, Any

_client_context_var: ContextVar[Dict[str, Any]] = ContextVar("client_context", default={})

def set_client_context(context: Dict[str, Any]) -> None:
    """Set the client context for the current execution context."""
    _client_context_var.set(context)

def get_client_context() -> Dict[str, Any]:
    """Retrieve the client context for the current execution context."""
    return _client_context_var.get()

def clear_client_context() -> None:
    """Clear the client context (reset to empty)."""
    _client_context_var.set({})

@contextmanager
def client_context_scope(context: Dict[str, Any]):
    """Context manager for temporarily setting client context."""
    token = _client_context_var.set(context)
    try:
        yield
    finally:
        _client_context_var.reset(token)