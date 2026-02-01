"""LangChain tool wrappers around the new Memory classes.

These expose the classic `save_*_memory`, `search_*_memory` … names so that
existing prompts / agents continue to work while delegating to the modern
Memory layer (ThreadMemory, UserMemory, OrgMemory, GlobalMemory).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, Future, wait, FIRST_EXCEPTION
import threading
import atexit

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from typing_extensions import TypedDict

from agentfoundry.agents.memory.global_memory import GlobalMemory
from agentfoundry.agents.memory.org_memory import OrgMemory
from agentfoundry.agents.memory.thread_memory import ThreadMemory
from agentfoundry.agents.memory.user_memory import UserMemory
from agentfoundry.vectorstores.factory import VectorStoreFactory

# Import AgentConfig for module-level config
try:
    from agentfoundry.utils.agent_config import AgentConfig
except ImportError:
    AgentConfig = None

# Module-level config set by Orchestrator during initialization
_module_config: Optional["AgentConfig"] = None


def set_module_config(config: "AgentConfig") -> None:
    """Set the module-level config for memory tools.
    
    Called by Orchestrator during initialization to provide config
    for memory operations without requiring it in every tool call.
    """
    global _module_config
    _module_config = config
    logger.info("Memory tools module config set")


def get_module_config() -> Optional["AgentConfig"]:
    """Get the module-level config."""
    return _module_config


def _get_org_id_from_config() -> str:
    """Get org_id from module config or return empty string."""
    if _module_config:
        return _module_config.org_id or ""
    return ""


# ---------------------------------------------------------------------------
# Runtime helpers
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

class _Cfg(TypedDict):
    configurable: Dict[str, str]


def _get(cfg: RunnableConfig, key: str) -> str | None:  # noqa: D401
    return cfg.get("configurable", {}).get(key) if cfg else None


def _provider_for_level(cfg: RunnableConfig | None, *, level: str):  # noqa: D401
    """Return a VectorStore provider for *level* using org_id when needed."""

    # Provider is a singleton; selection of org is done via filters in calls
    return VectorStoreFactory.get_provider()


_EXECUTOR: ThreadPoolExecutor | None = None
_PENDING: set[Future] = set()


def _ensure_executor() -> ThreadPoolExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="memsave")
    return _EXECUTOR


def _run_bg(name: str, target, *args, **kwargs) -> None:
    ex = _ensure_executor()
    fut = ex.submit(target, *args, **kwargs)
    _PENDING.add(fut)


def flush_memory_saves(timeout: float | None = None) -> None:
    if not _PENDING:
        return
    done, not_done = wait(list(_PENDING), timeout=timeout, return_when=FIRST_EXCEPTION)
    _PENDING.difference_update(done)
    # cancel anything left if timeout elapsed
    for f in not_done:
        try:
            f.cancel()
        except Exception:
            pass


def _shutdown_executor():  # registered at exit
    try:
        flush_memory_saves(timeout=5.0)
    finally:
        if _EXECUTOR is not None:
            _EXECUTOR.shutdown(wait=False, cancel_futures=True)


atexit.register(_shutdown_executor)


def _bg_save_thread(text: str, uid: str, tid: str, oid: str) -> None:
    try:
        tm = ThreadMemory(user_id=uid, thread_id=tid, org_id=oid)
        tm.add(text)
    except Exception as e:  # pragma: no cover
        logger.warning(f"Background save_thread_memory failed: {e}")


def _bg_save_user(text: str, uid: str, oid: str, role_level: int) -> None:
    try:
        um = UserMemory(uid, org_id=oid)
        um.add_semantic_item(text, role_level=role_level)
    except Exception as e:  # pragma: no cover
        logger.warning(f"Background save_user_memory failed: {e}")


def _bg_save_org(text: str, oid: str) -> None:
    try:
        om = OrgMemory(oid)
        om.add_semantic_item(text)
    except Exception as e:  # pragma: no cover
        logger.warning(f"Background save_org_memory failed: {e}")


def _bg_save_global(text: str) -> None:
    try:
        GlobalMemory().add_document(text)
    except Exception as e:  # pragma: no cover
        logger.warning(f"Background save_global_memory failed: {e}")


# ---------------------------------------------------------------------------
# Simple in-process caches to avoid re-instantiating memory classes repeatedly
# within a single run. These are keyed by their natural identifiers.
# ---------------------------------------------------------------------------

_USER_MEM_CACHE: dict[tuple[str, str], UserMemory] = {}
_THREAD_MEM_CACHE: dict[tuple[str, str, str], ThreadMemory] = {}
_ORG_MEM_CACHE: dict[str, OrgMemory] = {}


def _user_mem(cfg: RunnableConfig) -> UserMemory:
    uid = _get(cfg, "user_id") or ""
    oid = _get(cfg, "org_id") or _get_org_id_from_config()
    key = (uid, str(oid))
    mem = _USER_MEM_CACHE.get(key)
    if mem is None:
        mem = UserMemory(uid, org_id=str(oid))
        _USER_MEM_CACHE[key] = mem
    return mem


def _thread_mem(cfg: RunnableConfig) -> ThreadMemory:
    uid = _get(cfg, "user_id") or ""
    tid = _get(cfg, "thread_id") or "default"
    oid = _get(cfg, "org_id") or _get_org_id_from_config()
    key = (uid, tid, str(oid))
    mem = _THREAD_MEM_CACHE.get(key)
    if mem is None:
        mem = ThreadMemory(user_id=uid, thread_id=tid, org_id=str(oid))
        _THREAD_MEM_CACHE[key] = mem
    return mem


def _org_mem(cfg: RunnableConfig) -> OrgMemory:
    oid = _get(cfg, "org_id") or _get_org_id_from_config()
    key = str(oid)
    mem = _ORG_MEM_CACHE.get(key)
    if mem is None:
        mem = OrgMemory(key)
        _ORG_MEM_CACHE[key] = mem
    return mem


# ---------------------------------------------------------------------------
# Thread-level tools
# ---------------------------------------------------------------------------
@tool
def save_thread_memory(text: str, config: RunnableConfig) -> str:  # noqa: D401
    """Save text in the current thread’s short-term memory."""

    uid = _get(config, "user_id") or ""
    tid = _get(config, "thread_id") or "default"
    oid = _get(config, "org_id") or _get_org_id_from_config()
    logger.info(f"Queue thread memory save for user {uid}, thread {tid}, org {oid}: {text[:80]}...")
    _run_bg("thread", _bg_save_thread, text, uid, tid, str(oid))
    return "thread memory saved"


@tool
def search_thread_memory(query: str, config: RunnableConfig, k: int = 5) -> List[str]:
    """Search within the current thread’s memory (returns text snippets)."""

    uid = _get(config, "user_id") or ""
    tid = _get(config, "thread_id") or "default"
    oid = _get(config, "org_id") or _get_org_id_from_config()
    logger.info(f"Searching thread memory for user {uid}, thread {tid}, org {oid}: {query[:80]}...")
    return _thread_mem(config).similarity_search(query, k)


@tool
def delete_thread_memory(query: str, config: RunnableConfig, k: int = 5) -> str:  # noqa: D401
    """Delete up to *k* matching snippets from the current thread memory."""

    uid = _get(config, "user_id") or ""
    tid = _get(config, "thread_id") or "default"
    oid = _get(config, "org_id") or _get_org_id_from_config()
    logger.info(f"Deleting thread memory for user {uid}, thread {tid}, org {oid}: {query[:80]}...")
    mem = _thread_mem(config)
    docs = mem.index.similarity_search(query, k=k, filter={"user_id": uid, "thread_id": tid})  # type: ignore[attr-defined]  # pylint: disable=protected-access
    ids = [d.metadata.get("id", "") or d.id for d in docs]
    valid_ids = [i for i in ids if i]
    
    if valid_ids:
        mem.index.delete(valid_ids)
        mem.persist_index()
    return f"deleted {len(valid_ids)} docs"


# ---------------------------------------------------------------------------
# User-level tools
# ---------------------------------------------------------------------------


@tool
def save_user_memory(text: str, config: RunnableConfig) -> str:  # noqa: D401
    """Save *text* into the caller’s user-level long-term memory."""

    uid = _get(config, "user_id")
    if not uid:
        return "user_id missing in config"
    oid = _get(config, "org_id") or _get_org_id_from_config()
    caller_level = int(_get(config, "role_level") or 0)
    logger.info(f"Queue user memory save for user {uid}, org {oid}: {text[:80]}...")
    _run_bg("user", _bg_save_user, text, str(uid), str(oid), caller_level)
    return "user memory saved"


@tool
def search_user_memory(query: str, config: RunnableConfig, k: int = 10) -> List[str]:
    """Search user memory and global memory, returning up to *k* snippets."""

    uid = _get(config, "user_id")
    if not uid:
        logger.error(f"No user_id found in config: {config}")
        return []
    oid = _get(config, "org_id") or _get_org_id_from_config()
    # Determine caller's role level if provided in the runnable configuration so that
    # the underlying memory implementation can enforce visibility restrictions.
    caller_level = int(_get(config, "role_level") or 0)
    try:
        local = _user_mem(config).semantic_search(query, caller_role_level=caller_level, k=k)
    except Exception as e:
        logger.warning(f"user semantic_search error: {e}")
        local = []
    logger.info(f"Searching user memory for user {uid}, org {oid}: {query[:80]}... -> {len(local)} local hits")
    if len(local) >= k:
        return local[:k]
    remaining = max(0, k - len(local))
    if remaining == 0:
        return local
    global_hits = GlobalMemory().search(query, remaining)
    logger.info(f"Found {len(global_hits)} global hits")
    return (local + global_hits)[:k]


@tool
def delete_user_memory(query: str, config: RunnableConfig, k: int = 5) -> str:  # noqa: D401
    """Delete up to *k* user-level memory snippets matching *query*."""

    uid = _get(config, "user_id")
    if not uid:
        return "user_id missing"
    oid = _get(config, "org_id") or _get_org_id_from_config()

    mem = _user_mem(config)
    docs = mem.vs_provider.similarity_search(query, k=k, where={"user_id": uid}, org_id=str(oid))  # type: ignore[attr-defined]  # pylint: disable=protected-access
    logger.info(f"Found {len(docs)} documents")
    
    ids = [d.metadata.get("id", "") or d.id for d in docs]
    valid_ids = [i for i in ids if i]
    
    if valid_ids:
        mem.vs_provider.delete(ids=valid_ids, org_id=str(oid))  # type: ignore[attr-defined]
        logger.info(f"Deleted {len(valid_ids)} documents")
    else:
        logger.info("No valid IDs found to delete")
        
    return f"deleted {len(valid_ids)} docs"


# ---------------------------------------------------------------------------
# Organisation-level tools
# ---------------------------------------------------------------------------


@tool
def save_org_memory(text: str, config: RunnableConfig) -> str:  # noqa: D401
    """Persist *text* in the organisation’s shared long-term memory."""

    oid = _get(config, "org_id")
    if not oid:
        return "org_id missing in config"
    logger.info(f"Queue org memory save for org {oid}: {text[:80]}...")
    _run_bg("org", _bg_save_org, text, str(oid))
    return "org memory saved"


@tool
def search_org_memory(query: str, config: RunnableConfig, k: int = 8) -> List[str]:
    """Search organisation + global memories for *query*.

    Returns up to *k* snippets sorted by relevance."""

    oid = _get(config, "org_id")
    if not oid:
        return []
    org_hits = _org_mem(config).semantic_search(query, k)
    logger.info(f"Found {len(org_hits)} organisation hits")
    global_hits = GlobalMemory().search(query, k)
    logger.info(f"Found {len(global_hits)} global hits")
    return (org_hits + global_hits)[:k]


@tool
def delete_org_memory(query: str, config: RunnableConfig, k: int = 5) -> str:  # noqa: D401
    """Delete up to *k* organisation-level memory snippets."""

    oid = _get(config, "org_id")
    if not oid:
        return "org_id missing"
    mem = _org_mem(config)
    docs = mem.vs_provider.similarity_search(query, k=k, org_id=str(oid))  # type: ignore[attr-defined]
    logger.info(f"Found {len(docs)} documents to delete")
    
    ids = [d.metadata.get("id", "") or d.id for d in docs]
    valid_ids = [i for i in ids if i]
    
    if valid_ids:
        mem.vs_provider.delete(ids=valid_ids, org_id=str(oid))  # type: ignore[attr-defined]
        logger.info(f"Deleted {len(valid_ids)} documents to delete")
    else:
        logger.info("No valid IDs found to delete")
        
    return f"deleted {len(valid_ids)} docs"


# ---------------------------------------------------------------------------
# Global-level tools
# ---------------------------------------------------------------------------


@tool
def save_global_memory(text: str) -> str:  # noqa: D401
    """Add *text* to the system-wide global memory store."""

    logger.info(f"Queue global memory save: {text[:80]}...")
    _run_bg("global", _bg_save_global, text)
    return "global memory saved"


@tool
def search_global_memory(query: str, k: int = 5) -> List[str]:
    """Search global memory for *query* (up to *k* results)."""
    logger.info(f"Searching global memory for global {query[:80]}...")
    return GlobalMemory().search(query, k)


@tool
def delete_global_memory(query: str, k: int = 5) -> str:  # noqa: D401
    """Delete up to *k* global memory snippets matching *query*."""

    mem = GlobalMemory()
    docs = mem.vs_provider.similarity_search(query, k=k)  # type: ignore[attr-defined]  # pylint: disable=protected-access
    logger.info(f"Found {len(docs)} documents to delete")
    
    ids = [d.metadata.get("id", "") or d.id for d in docs]
    valid_ids = [i for i in ids if i]
    
    if valid_ids:
        mem.vs_provider.delete(ids=valid_ids)  # type: ignore[attr-defined]
        logger.info(f"Deleted {len(valid_ids)} documents")
    else:
        logger.info("No valid IDs found to delete")
        
    return f"deleted {len(valid_ids)} docs"


# ---------------------------------------------------------------------------
# Summary helper (unchanged)
# ---------------------------------------------------------------------------


from agentfoundry.agents.memory.summary_utils import summarize_memory


@tool
def summarize_any_memory(level: str, config: RunnableConfig, max_tokens: int = 32_000) -> str:  # noqa: D401
    """Return a summarised view of the requested memory *level*.

    level can be one of ``thread``, ``user``, ``org`` or ``global``.
    The helper merges org/global data when appropriate and truncates to
    *max_tokens* tokens.
    """

    level = level.lower()
    mem_filter: Dict[str, str] = {}
    org_id = _get(config, "org_id") or ""
    if level == "user":
        mem_filter["user_id"] = _get(config, "user_id") or ""
    elif level == "org":
        mem_filter["org_id"] = org_id
    elif level == "thread":
        mem_filter["thread_id"] = _get(config, "thread_id") or ""
    logger.info(f"Summarizing {level} memory...")
    summarization = summarize_memory(mem_filter, org_id=org_id or None, max_tokens=max_tokens)
    logger.info(f"Summarized {level} memory: {summarization[:80]}...")

    return summarization
