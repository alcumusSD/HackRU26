"""Verify that a Gemini quote appears in the source text."""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def quote_in_source(
    quote: str,
    source: str,
    *,
    min_ratio: float = 0.86,
    min_quote_len: int = 12,
) -> bool:
    """Return True if quote is in source (normalized) or a strong fuzzy match."""
    q = _normalize(quote)
    s = _normalize(source)
    if not q or not s:
        return False
    if len(q) < min_quote_len:
        return q in s
    if q in s:
        return True
    window = min(len(s), max(len(q) + 40, int(len(q) * 1.3)))
    if len(s) <= window:
        return SequenceMatcher(None, q, s).ratio() >= min_ratio
    best = 0.0
    step = max(1, len(q) // 4)
    for i in range(0, len(s) - window + 1, step):
        chunk = s[i : i + window]
        best = max(best, SequenceMatcher(None, q, chunk).ratio())
        if best >= min_ratio:
            return True
    return best >= min_ratio
