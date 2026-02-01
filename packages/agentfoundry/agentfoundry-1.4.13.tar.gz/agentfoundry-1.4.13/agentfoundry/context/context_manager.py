"""
ContextManager: builds the optimal memory pack for a fact-seeking query,
respecting model token limits and role-level visibility rules.

Scoring factors implemented:
  • similarity (vector store score)
  • recency decay
  • tier priority (Thread > User > Org > Global)
  • role_level filter (for UserMemory)
  • deduplication
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging

from agentfoundry.kgraph.factory import KGraphFactory
from agentfoundry.vectorstores.factory import VectorStoreFactory
from agentfoundry.context.token_utils import count_tokens
from agentfoundry.agents.memory.thread_memory import ThreadMemory
from agentfoundry.agents.memory.user_memory import UserMemory
from agentfoundry.agents.memory.org_memory import OrgMemory
from agentfoundry.agents.memory.global_memory import GlobalMemory

logger = logging.getLogger(__name__)


@dataclass
class MemoryChunk:
    text: str
    score: float      # composite score (higher = more relevant)
    tokens: int
    tier: str         # "thread" | "user" | "org" | "global"


class ContextManager:
    """
    Builds a context block that fits within the model's token window.
    """

    # --- weights (tweak via config if desired) -----------------
    TIER_WEIGHTS = {
        "thread": 3.0,
        "user":   2.0,
        "org":    1.2,
        "global": 1.0,
    }
    RECENCY_HALFLIFE_HOURS = 12  # weight halves every 12 h
    SIM_SCALE = 1.0              # similarity (already 0-1)
    # -----------------------------------------------------------
    MODEL_TOKEN_LIMITS = {
        "o1-mini":      128000,
        "gpt-4o":       128000,
        "gpt-4o mini":  128000,
        "o1":           200000,
        "o1-pro":       200000,
        "o3":           200000,
        "o3-mini":      200000,
        "o3-pro":       200000,
        "o4-mini":      200000,
        "gpt-4.1":      1047576,
        "gpt-4.1 mini": 1047576,
        "gpt-4.1 nano": 1047576,
        "o3-deep-research": 200000,
        "o4-mini-deep-research": 200000,
        "codex-mini-latest": 200000,
        "gpt-3.5 turbo": 16385,
        "gpt-4 turbo":  128000,
        "gpt-4":        8192
    }

    def __init__(
        self,
        model_token_limit: int,
        prompt_overhead_tokens: int = 800,
    ) -> None:
        self.model_limit = model_token_limit
        self.overhead = prompt_overhead_tokens

    # ---------- public API -------------------------------------
    def build_context(
        self,
        query: str,
        *,
        thread_id: str,
        user_id: str,
        org_id: str,
        user_role_level: int,
        k_per_tier: int = 20,
    ) -> List[str]:
        """
        Returns a list of memory strings ordered by relevance that
        together fit into (model_limit - overhead) tokens.
        """
        budget = self.model_limit - self.overhead
        logger.debug(f"Token budget for memories: {budget} tokens")

        # 1) Retrieve candidates from each tier
        candidates: List[MemoryChunk] = []
        candidates.extend(
            self._fetch_thread(query, thread_id, k_per_tier)
        )
        candidates.extend(
            self._fetch_user(query, user_id, org_id, user_role_level, k_per_tier)
        )
        candidates.extend(
            self._fetch_org(query, org_id, k_per_tier)
        )
        candidates.extend(
            self._fetch_global(query, k_per_tier)
        )

        # 2) Dedupe identical texts (keep highest score)
        dedup: Dict[str, MemoryChunk] = {}
        for c in candidates:
            if c.text not in dedup or dedup[c.text].score < c.score:
                dedup[c.text] = c
        dedupbed = list(dedup.values())

        # 3) Sort by composite score descending
        dedupbed.sort(key=lambda c: c.score, reverse=True)

        # 4) Greedy packing
        selected: List[str] = []
        used_tokens = 0
        for chunk in dedupbed:
            if used_tokens + chunk.tokens > budget:
                continue
            selected.append(chunk.text)
            used_tokens += chunk.tokens

        logger.info(f"ContextManager selected {len(selected)} chunks ({used_tokens} tokens)")
        return selected

    # ---------- internal helpers --------------------------------
    def _decay_by_recency(self, created_at: datetime) -> float:
        hrs = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600.0
        decay = 0.5 ** (hrs / self.RECENCY_HALFLIFE_HOURS)
        return decay

    def _combine_score(self, sim: float, recency_factor: float, tier: str) -> float:
        return (sim * self.SIM_SCALE) * recency_factor * self.TIER_WEIGHTS[tier]

    # -- fetchers per tier --
    def _fetch_thread(self, query: str, thread_id: str, k: int) -> List[MemoryChunk]:
        store = ThreadMemory(thread_id)
        docs = store.search(query, k=k, with_scores=True)
        return [
            MemoryChunk(
                text=doc.page_content,
                score=self._combine_score(score, 1.0, "thread"),
                tokens=count_tokens(doc.page_content),
                tier="thread"
            )
            for doc, score in docs
        ]

    def _fetch_user(
        self,
        query: str,
        user_id: str,
        org_id: str,
        role_level: int,
        k: int
    ) -> List[MemoryChunk]:
        store = UserMemory(user_id, org_id, role_level)
        docs = store.search(query, k=k, with_scores=True)
        chunks: List[MemoryChunk] = []
        for doc, score in docs:
            recency = self._decay_by_recency(doc.metadata["created_at"])
            chunks.append(
                MemoryChunk(
                    text=doc.page_content,
                    score=self._combine_score(score, recency, "user"),
                    tokens=count_tokens(doc.page_content),
                    tier="user"
                )
            )
        return chunks

    def _fetch_org(self, query: str, org_id: str, k: int) -> List[MemoryChunk]:
        store = OrgMemory(org_id)
        docs = store.search(query, k=k, with_scores=True)
        return [
            MemoryChunk(
                text=doc.page_content,
                score=self._combine_score(score, 1.0, "org"),
                tokens=count_tokens(doc.page_content),
                tier="org"
            )
            for doc, score in docs
        ]

    def _fetch_global(self, query: str, k: int) -> List[MemoryChunk]:
        store = GlobalMemory()
        docs = store.search(query, k=k, with_scores=True)
        return [
            MemoryChunk(
                text=doc.page_content,
                score=self._combine_score(score, 1.0, "global"),
                tokens=count_tokens(doc.page_content),
                tier="global"
            )
            for doc, score in docs
        ]

