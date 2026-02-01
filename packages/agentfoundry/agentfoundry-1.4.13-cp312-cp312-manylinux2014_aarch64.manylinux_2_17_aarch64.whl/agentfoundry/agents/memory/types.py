"""Common type definitions for the memory system."""

from __future__ import annotations

from typing import TypedDict, Optional, Any, Union, List

class MemoryMetadata(TypedDict, total=False):
    """Standard metadata fields for memory items."""
    user_id: str
    org_id: str
    scope: str
    role_level: int
    created_at: str
    thread_id: Optional[str]
    # Allow other arbitrary fields
    source: Optional[str]
    doc_id: Optional[str]

class SearchFilter(TypedDict, total=False):
    """Standard search filter fields."""
    user_id: str
    org_id: str
    thread_id: str
    scope: str
    # Complex filters often used by vector stores
    id: Union[str, dict]
    role_level: Union[int, dict]
    # Allow recursive structure for $and, $or queries
    # Use alternative syntax for keys with special characters
SearchFilter.__annotations__["$and"] = List[dict]
SearchFilter.__annotations__["$or"] = List[dict]
