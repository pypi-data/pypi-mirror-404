"""
Tiny helper: estimate token count for a piece of text.
Uses `tiktoken` if available; falls back to len(text)//4.
"""
from functools import lru_cache

try:
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
except ModuleNotFoundError:  # graceful fallback
    enc = None


@lru_cache(maxsize=2048)
def count_tokens(text: str) -> int:
    if enc:
        return len(enc.encode(text))
    return max(1, len(text) // 4)  # crude but OK for budgeting

