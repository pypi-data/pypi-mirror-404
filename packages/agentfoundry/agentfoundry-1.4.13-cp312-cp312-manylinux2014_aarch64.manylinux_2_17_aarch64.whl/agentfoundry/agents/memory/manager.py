"""Unified facade for memory management."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agentfoundry.agents.memory.global_memory import GlobalMemory
from agentfoundry.agents.memory.org_memory import OrgMemory
from agentfoundry.agents.memory.user_memory import UserMemory
from agentfoundry.agents.memory.thread_memory import ThreadMemory
from agentfoundry.agents.memory.constants import SCOPE_GLOBAL, SCOPE_ORG, SCOPE_USER, SCOPE_THREAD
from agentfoundry.utils.config import Config

logger = logging.getLogger(__name__)


class MemoryManager:
    """Facade for managing access to all memory layers (Global, Org, User, Thread)."""

    def __init__(
        self, 
        user_id: str, 
        org_id: str | None = None, 
        thread_id: str | None = None, 
        data_dir: str | None = None
    ):
        """Initialize the memory manager. 
        
        Args:
            user_id: The ID of the current user.
            org_id: The ID of the organization. If None, fetched from config.
            thread_id: The ID of the current conversation thread.
            data_dir: Root directory for data storage.
        """
        self.user_id = user_id
        self.org_id = org_id or Config().get("ORG_ID")
        if not self.org_id:
             raise ValueError("MemoryManager requires org_id (param or config ORG_ID)")
        self.thread_id = thread_id
        self.data_dir = data_dir

        # Initialize layers
        self.global_mem = GlobalMemory(data_dir=data_dir)
        self.org_mem = OrgMemory(self.org_id, data_dir=data_dir)
        self.user_mem = UserMemory(user_id, self.org_id, data_dir=data_dir)
        
        if thread_id:
            self.thread_mem = ThreadMemory(
                user_id=user_id, 
                thread_id=thread_id, 
                org_id=self.org_id, 
                data_dir=data_dir
            )
        else:
            self.thread_mem = None
            
        logger.debug(f"MemoryManager initialized for user={user_id} org={self.org_id} thread={thread_id}")

    def add(self, text: str, scope: str = SCOPE_THREAD, metadata: Dict[str, Any] | None = None, **kwargs) -> str:
        """Add text to the specified memory scope. 
        
        Args:
            text: The content to store.
            scope: One of 'thread', 'user', 'org', 'global'.
            metadata: Additional metadata to store.
            **kwargs: Additional arguments passed to the specific memory layer (e.g. role_level).
        
        Returns:
            The ID of the stored item.
        """
        if scope == SCOPE_THREAD:
            if not self.thread_mem:
                raise ValueError("Cannot add to thread memory: no thread_id provided at init")
            return self.thread_mem.add(text, metadata=metadata)
            
        elif scope == SCOPE_USER:
            # UserMemory.add_semantic_item takes role_level as kwarg in our refactor (or explicit arg)
            # In facade, we pass it via kwargs
            role_level = kwargs.get("role_level", 0)
            return self.user_mem.add_semantic_item(text, role_level=role_level, metadata=metadata)
            
        elif scope == SCOPE_ORG:
            return self.org_mem.add_semantic_item(text, metadata=metadata)
            
        elif scope == SCOPE_GLOBAL:
            # Global usually read-only but this allows admin tools to use the manager
            return self.global_mem.add_semantic_item(text, metadata=metadata)
            
        else:
            raise ValueError(f"Unknown scope: {scope}")

    def search(
        self, 
        query: str, 
        scopes: List[str] | None = None, 
        k: int = 5, 
        **kwargs
    ) -> Dict[str, List[str]]:
        """Search across specified scopes. 
        
        Args:
            query: The search query.
            scopes: List of scopes to search. Defaults to [THREAD, USER, ORG, GLOBAL].
            k: Number of results per scope.
            **kwargs: Additional args (e.g. caller_role_level for User scope).
        
        Returns:
            Dictionary with scope names as keys and lists of result strings as values.
        """
        if scopes is None:
            scopes = [SCOPE_THREAD, SCOPE_USER, SCOPE_ORG, SCOPE_GLOBAL]
            
        results = {}
        
        # TODO: This could be parallelized
        
        if SCOPE_THREAD in scopes and self.thread_mem:
            results[SCOPE_THREAD] = self.thread_mem.similarity_search(query, k=k)
            
        if SCOPE_USER in scopes:
            # Handle role_level
            caller_role = kwargs.get("caller_role_level", 0)
            results[SCOPE_USER] = self.user_mem.semantic_search(query, caller_role_level=caller_role, k=k)
            
        if SCOPE_ORG in scopes:
            results[SCOPE_ORG] = self.org_mem.semantic_search(query, k=k)
            
        if SCOPE_GLOBAL in scopes:
            results[SCOPE_GLOBAL] = self.global_mem.search(query, k=k)
            
        return results

    def get_context(self, query: str, k: int = 5) -> str:
        """Retrieve a unified string context from all layers, prioritized. 
        
        Prioritization: Thread > User > Org > Global.
        """
        results = self.search(query, k=k)
        
        context_parts = []
        
        if results.get(SCOPE_THREAD):
            context_parts.append("--- Conversation Context ---")
            context_parts.extend(results[SCOPE_THREAD])
            
        if results.get(SCOPE_USER):
            context_parts.append("\n--- User Context ---")
            context_parts.extend(results[SCOPE_USER])
            
        if results.get(SCOPE_ORG):
            context_parts.append("\n--- Organization Context ---")
            context_parts.extend(results[SCOPE_ORG])
            
        if results.get(SCOPE_GLOBAL):
            context_parts.append("\n--- Global Knowledge ---")
            context_parts.extend(results[SCOPE_GLOBAL])
            
        return "\n".join(context_parts)
