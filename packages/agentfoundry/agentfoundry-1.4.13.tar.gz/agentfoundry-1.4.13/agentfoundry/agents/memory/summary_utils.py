"""Utility for summarising long-term memories using LangChain summarisation chains."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, List, Tuple

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from agentfoundry.llm.llm_factory import LLMFactory
from agentfoundry.vectorstores.factory import VectorStoreFactory

logger = logging.getLogger(__name__)


def _estimate_tokens(text: str) -> int:
    return len(text) // 4 + 1


# ---------------------------------------------------------------------------
# Simple in-process cache to avoid repeating the expensive LLM summarize chain
# for the same (org_id, filter) within a short TTL window.
# ---------------------------------------------------------------------------

_SUMMARY_CACHE: Dict[str, Tuple[float, str]] = {}
try:
    _SUMMARY_TTL_SECONDS = int(os.getenv("AF_SUMMARY_TTL", "120"))
except Exception:
    _SUMMARY_TTL_SECONDS = 120


def _cache_key(store_filter: dict | None, org_id: str | None) -> str:
    try:
        filt_str = json.dumps(store_filter or {}, sort_keys=True, separators=(",", ":"))
    except Exception:
        filt_str = str(store_filter)
    return f"org={org_id or ''}|flt={filt_str}"


def summarize_memory(store_filter: Dict[str, any] | None = None, *, org_id: str | None = None, max_tokens: int = 32000) -> str:
    """Summarize the vector-store documents that match *store_filter*.

    Parameters
    ----------
    store_filter : Dict[str, any] | None
        Metadata filter passed to `similarity_search`. Use `{}` to fetch all.
    org_id : str | None
        Organization ID for scoped vector store retrieval.
    max_tokens : int
        Hard cap on the returned summary size in estimated tokens.
    """
    # Cache key and early return
    key = _cache_key(store_filter, org_id)
    now = time.perf_counter()
    _SUMMARY_TTL_SECONDS = int(os.getenv("AF_SUMMARY_TTL_SECONDS", "90"))
    if _SUMMARY_TTL_SECONDS > 0:
        cached = _SUMMARY_CACHE.get(key)
        if cached and (now - cached[0]) < _SUMMARY_TTL_SECONDS:
            logger.info("summary_cache: hit for org_id=%s filter=%s", org_id, bool(store_filter))
            return cached[1]

    # Initialize LLM
    try:
        llm = LLMFactory.get_llm_model()
    except Exception as err:
        logger.warning(f"Summarization chain unavailable: {err}")
        raise

    # Collect documents from org and global stores
    docs: List[Document] = []
    try:
        max_docs = int(os.getenv("AF_SUMMARY_MAX_DOCS", "200"))
    except Exception:
        max_docs = 200

    try:
        # Prefer using the provider's similarity_search which, for Chroma,
        # avoids the /query endpoint (blocked in some deployments) and uses
        # /get with where/where_document instead.
        #
        # Note: We call get_provider() without arguments so it returns the
        # active singleton determined by global config, rather than trying to
        # re-read env vars or default to 'chroma'.
        t0_retr = time.perf_counter()
        provider = VectorStoreFactory.get_provider()

        try:
            logger.info(f"Store filter: {store_filter}")
            results = provider.similarity_search("*", k=max_docs, filter=store_filter or None, org_id=org_id)
            for r in results:
                docs.append(r if isinstance(r, Document) else Document(page_content=str(r)))
        except Exception as inner_err:
            logger.warning(f"Provider similarity_search failed on org scope: {inner_err}", exc_info=True)

        if org_id:
            try:
                results_g = provider.similarity_search("*", k=max_docs, filter=store_filter or {}, org_id=None)
                for r in results_g:
                    docs.append(r if isinstance(r, Document) else Document(page_content=str(r)))
            except Exception as inner_err:
                logger.warning(f"Provider similarity_search failed on global scope: {inner_err}")
                raise
    except Exception as ex:
        if "Embedding function is missing required methods" in str(ex):
            logger.error(f"Skipping summarization due to incompatible embedding backend: {ex}")
            raise
        logger.warning(f"Vector-store retrieval failed: {ex}", exc_info=True)

    retr_ms = int((time.perf_counter() - t0_retr) * 1000)
    if not docs:
        logger.info(f"summary: docs=0 org_id={org_id} filter={bool(store_filter)} took_ms={retr_ms}")
        if _SUMMARY_TTL_SECONDS > 0:
            _SUMMARY_CACHE[key] = (now, "")
        return ""

    total_chars = sum(len(d.page_content) for d in docs)
    est_tokens = _estimate_tokens("x" * total_chars)
    logger.info(f"summary: docs={len(docs)} est_tokens={est_tokens} retr_ms={retr_ms} max_docs={max_docs}")

    # Define summarization prompts
    map_prompt = ChatPromptTemplate.from_messages([
        ("system", "Summarize the following document concisely:\n\n{documents}")
    ])
    reduce_prompt = ChatPromptTemplate.from_messages([
        ("system", "Combine these summaries into a single, concise summary:\n\n{documents}")
    ])

    # Configure summarization chain
    parser = StrOutputParser()
    simple_chain: Runnable = map_prompt | llm | parser
    reduce_chain: Runnable = reduce_prompt | llm | parser

    try:
        t0 = time.perf_counter()
        if est_tokens < 4000:
            combined = "\n\n".join(d.page_content for d in docs)
            summary = simple_chain.invoke({"documents": combined})
            chain_type = "stuff"
        else:
            chain_type = "map_reduce"
            partials: List[str] = []
            for doc in docs:
                try:
                    partials.append(simple_chain.invoke({"documents": doc.page_content}))
                except Exception as map_err:  # pragma: no cover - per-doc failure
                    logger.warning("summary_map: skipping doc due to error: %s", map_err)

            if not partials:
                summary = ""
            else:
                chunk_size = int(os.getenv("AF_SUMMARY_REDUCE_CHUNK", "5") or "5")
                chunk_size = max(chunk_size, 2)
                rounds = 0
                while len(partials) > 1 and rounds < 10:
                    next_stage: List[str] = []
                    for i in range(0, len(partials), chunk_size):
                        chunk_text = "\n\n".join(partials[i : i + chunk_size])
                        try:
                            next_stage.append(reduce_chain.invoke({"documents": chunk_text}))
                        except Exception as red_err:  # pragma: no cover
                            logger.warning("summary_reduce: reduce chunk failed: %s", red_err)
                    partials = next_stage if next_stage else partials
                    chunk_size = max(2, chunk_size - 1)
                    rounds += 1
                summary = partials[0] if partials else ""

        chain_ms = int((time.perf_counter() - t0) * 1000)
        logger.info(f"summary_chain: type={chain_type} took_ms={chain_ms}")
        logger.debug(f"summary_chain: {summary}")
    except Exception as err:
        logger.warning(f"Summarization chain failed: {err}")
        summary = "\n".join(d.page_content for d in docs)

    # Truncate if over max_tokens
    if _estimate_tokens(summary) > max_tokens:
        summary = summary[:max_tokens * 4]

    # Store in cache
    if _SUMMARY_TTL_SECONDS > 0:
        _SUMMARY_CACHE[key] = (now, summary)
    return summary
