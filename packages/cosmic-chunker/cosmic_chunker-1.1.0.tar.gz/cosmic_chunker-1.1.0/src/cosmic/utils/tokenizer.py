"""Token counting utilities."""

from typing import Optional

import tiktoken

# Global encoder instance (lazy loaded)
_encoder: Optional[tiktoken.Encoding] = None


def get_encoder() -> tiktoken.Encoding:
    """Get or create tiktoken encoder."""
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken cl100k_base.

    Args:
        text: Text to count tokens for

    Returns:
        Number of tokens
    """
    encoder = get_encoder()
    return len(encoder.encode(text))


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to maximum token count.

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens allowed

    Returns:
        Truncated text
    """
    encoder = get_encoder()
    tokens = encoder.encode(text)

    if len(tokens) <= max_tokens:
        return text

    return encoder.decode(tokens[:max_tokens])


def estimate_tokens(text: str) -> int:
    """Fast token estimation without full encoding.

    Approximates ~4 characters per token for English text.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // 4
