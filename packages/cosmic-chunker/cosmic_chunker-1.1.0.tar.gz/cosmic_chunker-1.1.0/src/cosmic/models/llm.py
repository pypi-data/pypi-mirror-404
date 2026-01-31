"""LLM client for boundary verification.

Uses OpenAI-compatible API format, with endpoint URL from .env file.
Supports both sync and async operations with connection pooling.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from cosmic.core.config import LLMConfig
from cosmic.exceptions import LLMConnectionError, LLMTimeoutError, LLMVerificationError

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM API."""

    text: str
    finish_reason: str
    usage: dict

    @property
    def is_boundary(self) -> bool:
        """Parse response to determine if boundary is confirmed."""
        text_lower = self.text.lower().strip()
        # Look for affirmative responses
        if any(
            word in text_lower
            for word in ["yes", "true", "boundary", "different topic", "new section"]
        ):
            return True
        if any(
            word in text_lower
            for word in ["no", "false", "same topic", "continuation", "continues"]
        ):
            return False
        # Default to True if uncertain
        return True


class LLMClient:
    """Client for LLM API with OpenAI-compatible format.

    The LLM endpoint URL is read from COSMIC_LLM_URL environment variable.
    Supports async batch operations for efficient verification.

    Example:
        client = LLMClient(config.llm)
        response = await client.verify_boundary(before_text, after_text)
    """

    BOUNDARY_PROMPT = """Analyze whether there is a conceptual boundary between these two text segments.

Text BEFORE potential boundary:
{before_text}

Text AFTER potential boundary:
{after_text}

Is there a significant topic shift or conceptual boundary between these texts?
Answer with just "Yes" if this is a boundary, or "No" if the texts are part of the same concept.
"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout_seconds),
                headers=self._get_headers(),
            )
        return self._client

    @property
    def sync_client(self) -> httpx.Client:
        """Get or create sync HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout_seconds),
                headers=self._get_headers(),
            )
        return self._sync_client

    def _get_headers(self) -> dict:
        """Get HTTP headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def complete(
        self,
        prompt: str,
        max_tokens: int = 50,
        temperature: float = 0.1,
    ) -> LLMResponse:
        """Send completion request to LLM.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            LLMResponse with text and metadata
        """
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                finish_reason=data["choices"][0].get("finish_reason", "unknown"),
                usage=data.get("usage", {}),
            )

        except httpx.ConnectError as e:
            raise LLMConnectionError(
                f"Failed to connect to LLM endpoint: {e}",
                details={"url": self.config.base_url},
            )
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(
                f"LLM request timed out: {e}",
                details={"timeout": self.config.timeout_seconds},
            )
        except httpx.HTTPStatusError as e:
            raise LLMVerificationError(
                f"LLM API error: {e.response.status_code}",
                details={"response": e.response.text},
            )

    def complete_sync(
        self,
        prompt: str,
        max_tokens: int = 50,
        temperature: float = 0.1,
    ) -> LLMResponse:
        """Synchronous completion request."""
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            response = self.sync_client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                finish_reason=data["choices"][0].get("finish_reason", "unknown"),
                usage=data.get("usage", {}),
            )

        except httpx.ConnectError as e:
            raise LLMConnectionError(
                f"Failed to connect to LLM endpoint: {e}",
                details={"url": self.config.base_url},
            )
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(
                f"LLM request timed out: {e}",
                details={"timeout": self.config.timeout_seconds},
            )

    async def verify_boundary(
        self,
        before_text: str,
        after_text: str,
    ) -> tuple[bool, float]:
        """Verify if a boundary exists between two text segments.

        Args:
            before_text: Text before the potential boundary
            after_text: Text after the potential boundary

        Returns:
            Tuple of (is_boundary, confidence)
        """
        # Truncate texts to max context
        max_chars = self.config.max_context_tokens * 4  # ~4 chars per token
        before_text = before_text[-max_chars:] if len(before_text) > max_chars else before_text
        after_text = after_text[:max_chars] if len(after_text) > max_chars else after_text

        prompt = self.BOUNDARY_PROMPT.format(
            before_text=before_text,
            after_text=after_text,
        )

        response = await self.complete(prompt)

        # Parse response
        is_boundary = response.is_boundary

        # Estimate confidence based on response clarity
        text_lower = response.text.lower()
        if text_lower.startswith("yes") or text_lower.startswith("no"):
            confidence = 0.9  # Clear answer
        else:
            confidence = 0.6  # Ambiguous

        return is_boundary, confidence

    async def verify_boundaries_batch(
        self,
        boundary_contexts: list[tuple[str, str]],
    ) -> list[tuple[bool, float]]:
        """Verify multiple boundaries concurrently.

        Args:
            boundary_contexts: List of (before_text, after_text) tuples

        Returns:
            List of (is_boundary, confidence) tuples
        """
        tasks = [self.verify_boundary(before, after) for before, after in boundary_contexts]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed: list[tuple[bool, float]] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.warning(f"Boundary verification failed: {result}")
                processed.append((True, 0.5))  # Default to boundary on error
            else:
                processed.append(result)

        return processed

    async def close(self) -> None:
        """Close HTTP client connections."""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    def __del__(self) -> None:
        """Cleanup on deletion."""
        if self._sync_client:
            try:
                self._sync_client.close()
            except Exception:
                pass


class MockLLMClient(LLMClient):
    """Mock LLM client for testing without actual API calls."""

    def __init__(self, config: LLMConfig, always_boundary: bool = True):
        super().__init__(config)
        self.always_boundary = always_boundary
        self.call_count = 0

    async def verify_boundary(
        self,
        before_text: str,
        after_text: str,
    ) -> tuple[bool, float]:
        """Mock boundary verification."""
        self.call_count += 1

        # Simple heuristic: if texts are very different lengths, likely boundary
        len_diff = abs(len(before_text) - len(after_text))
        if self.always_boundary or len_diff > 100:
            return True, 0.8
        return False, 0.7
