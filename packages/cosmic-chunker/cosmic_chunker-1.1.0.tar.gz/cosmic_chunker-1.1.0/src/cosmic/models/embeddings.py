"""Sentence embedding model wrapper with caching."""

import hashlib
import logging
from typing import Optional

import numpy as np
from cachetools import LRUCache
from sentence_transformers import SentenceTransformer

from cosmic.core.config import EmbeddingConfig
from cosmic.exceptions import EmbeddingModelError

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wrapper around sentence-transformers with LRU caching.

    Features:
    - Lazy loading of model
    - LRU cache for repeated texts
    - Batch encoding for efficiency
    - GPU/CPU device management

    Example:
        model = EmbeddingModel(config.embedding)
        embeddings = model.encode(["Hello world", "Test sentence"])
    """

    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._model: Optional[SentenceTransformer] = None
        self._cache: LRUCache = LRUCache(maxsize=config.cache_size)
        self._dimension: Optional[int] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                logger.info(f"Loading embedding model: {self.config.model_name}")
                self._model = SentenceTransformer(
                    self.config.model_name,
                    device=self.config.device,
                )
                # Get embedding dimension
                test_embedding = self._model.encode(["test"], convert_to_numpy=True)
                self._dimension = test_embedding.shape[1]
                logger.info(
                    f"Loaded model with dimension {self._dimension} on {self.config.device}"
                )
            except Exception as e:
                raise EmbeddingModelError(
                    f"Failed to load embedding model: {e}",
                    details={"model_name": self.config.model_name},
                )
        return self._model

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            # Trigger model loading
            _ = self.model
        return self._dimension  # type: ignore

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()

    def encode(
        self,
        texts: list[str],
        batch_size: Optional[int] = None,
        show_progress: bool = False,
    ) -> np.ndarray:
        """Encode texts to embeddings with caching.

        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding (default from config)
            show_progress: Show progress bar

        Returns:
            numpy array of shape (len(texts), dimension)
        """
        if not texts:
            return np.array([]).reshape(0, self.dimension)

        batch_size = batch_size or self.config.batch_size

        # Check cache for each text
        embeddings = []
        texts_to_encode = []
        text_indices = []  # Track which texts need encoding

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                embeddings.append((i, self._cache[cache_key]))
            else:
                texts_to_encode.append(text)
                text_indices.append(i)

        # Encode uncached texts
        if texts_to_encode:
            try:
                new_embeddings = self.model.encode(
                    texts_to_encode,
                    batch_size=batch_size,
                    show_progress_bar=show_progress,
                    convert_to_numpy=True,
                    normalize_embeddings=self.config.normalize,
                )

                # Cache and collect results
                for text, idx, emb in zip(texts_to_encode, text_indices, new_embeddings):
                    cache_key = self._get_cache_key(text)
                    self._cache[cache_key] = emb
                    embeddings.append((idx, emb))

            except Exception as e:
                raise EmbeddingModelError(
                    f"Encoding failed: {e}",
                    details={"num_texts": len(texts_to_encode)},
                )

        # Sort by original index and stack
        embeddings.sort(key=lambda x: x[0])
        return np.vstack([emb for _, emb in embeddings])

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text."""
        result: np.ndarray = self.encode([text])[0]
        return result

    def similarity(
        self,
        embeddings1: np.ndarray,
        embeddings2: np.ndarray,
    ) -> np.ndarray:
        """Compute cosine similarity between embedding sets.

        Args:
            embeddings1: Shape (n, dim) or (dim,)
            embeddings2: Shape (m, dim) or (dim,)

        Returns:
            Similarity matrix of shape (n, m) or scalar
        """
        # Ensure 2D
        if embeddings1.ndim == 1:
            embeddings1 = embeddings1.reshape(1, -1)
        if embeddings2.ndim == 1:
            embeddings2 = embeddings2.reshape(1, -1)

        # Normalize if not already
        if not self.config.normalize:
            embeddings1 = embeddings1 / np.linalg.norm(embeddings1, axis=1, keepdims=True)
            embeddings2 = embeddings2 / np.linalg.norm(embeddings2, axis=1, keepdims=True)

        result: np.ndarray = np.dot(embeddings1, embeddings2.T)
        return result

    def pairwise_similarity(self, embeddings: np.ndarray) -> np.ndarray:
        """Compute pairwise cosine similarity matrix.

        Args:
            embeddings: Shape (n, dim)

        Returns:
            Similarity matrix of shape (n, n)
        """
        return self.similarity(embeddings, embeddings)

    def consecutive_similarity(self, embeddings: np.ndarray) -> np.ndarray:
        """Compute similarity between consecutive embeddings.

        Args:
            embeddings: Shape (n, dim)

        Returns:
            Array of shape (n-1,) with similarity between adjacent pairs
        """
        if len(embeddings) < 2:
            return np.array([])

        # Compute dot product between consecutive embeddings
        similarities: np.ndarray = np.sum(embeddings[:-1] * embeddings[1:], axis=1)
        return similarities

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        """Current number of cached embeddings."""
        return len(self._cache)

    @property
    def cache_info(self) -> dict:
        """Get cache statistics."""
        return {
            "current_size": len(self._cache),
            "max_size": self._cache.maxsize,
        }

    def __repr__(self) -> str:
        return (
            f"EmbeddingModel(model={self.config.model_name}, "
            f"device={self.config.device}, "
            f"cache={self.cache_size}/{self.config.cache_size})"
        )
