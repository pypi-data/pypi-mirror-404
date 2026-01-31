"""Fallback chunking strategies for COSMIC framework."""

from cosmic.fallback.fixed_length import FixedLengthChunker
from cosmic.fallback.semantic_only import SemanticOnlyChunker
from cosmic.fallback.sliding_window import SlidingWindowChunker

__all__ = [
    "FixedLengthChunker",
    "SlidingWindowChunker",
    "SemanticOnlyChunker",
]
