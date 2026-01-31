"""Sliding window chunking with basic semantic awareness."""

import hashlib
import logging
from datetime import datetime
from typing import Optional

import numpy as np

from cosmic import __version__
from cosmic.core.chunk import COSMICChunk
from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document
from cosmic.core.enums import ProcessingMode
from cosmic.models.embeddings import EmbeddingModel
from cosmic.utils.tokenizer import count_tokens

logger = logging.getLogger(__name__)


class SlidingWindowChunker:
    """Fallback: Sliding window with basic semantic boundaries.

    Uses embedding similarity to find natural break points within
    a sliding window. Simpler than full COSMIC but still respects
    semantic coherence.
    """

    def __init__(
        self,
        config: COSMICConfig,
        similarity_threshold: float = 0.5,
    ):
        self.config = config
        self.similarity_threshold = similarity_threshold
        self.min_tokens = config.chunks.min_tokens
        self.max_tokens = config.chunks.max_tokens
        self.target_tokens = config.chunks.target_tokens
        self._embedding_model: Optional[EmbeddingModel] = None

    @property
    def embedding_model(self) -> EmbeddingModel:
        """Lazy load embedding model."""
        if self._embedding_model is None:
            self._embedding_model = EmbeddingModel(self.config.embedding)
        return self._embedding_model

    def chunk(self, document: Document) -> list[COSMICChunk]:
        """Chunk document using sliding window strategy.

        Args:
            document: Document to chunk

        Returns:
            List of COSMICChunk with basic coherence scoring
        """
        logger.info(f"Sliding window chunking document {document.id}")

        if len(document.sentences) == 0:
            return []

        # Get sentence embeddings
        sentence_texts = [s.text for s in document.sentences]
        embeddings = self.embedding_model.encode(sentence_texts)

        # Compute consecutive similarities
        similarities = self.embedding_model.consecutive_similarity(embeddings)

        # Find break points
        break_points = self._find_break_points(document.sentences, similarities)

        # Create chunks from break points
        chunks = self._create_chunks_from_breaks(document, embeddings, break_points)

        logger.info(f"Created {len(chunks)} sliding window chunks")
        return chunks

    def _find_break_points(
        self,
        sentences: list,
        similarities: np.ndarray,
    ) -> list[int]:
        """Find natural break points based on similarity drops."""
        break_points = [0]  # Always start at beginning
        current_tokens = 0

        for i, sentence in enumerate(sentences):
            sentence_tokens = count_tokens(sentence.text)
            current_tokens += sentence_tokens

            # Check if we should break here
            should_break = False

            if current_tokens >= self.max_tokens:
                # Must break - exceeded max
                should_break = True
            elif current_tokens >= self.target_tokens:
                # Check for semantic break opportunity
                if i < len(similarities) and similarities[i] < self.similarity_threshold:
                    should_break = True

            if should_break and i + 1 < len(sentences):
                break_points.append(i + 1)
                current_tokens = 0

        return break_points

    def _create_chunks_from_breaks(
        self,
        document: Document,
        embeddings: np.ndarray,
        break_points: list[int],
    ) -> list[COSMICChunk]:
        """Create chunks from break points."""
        chunks: list[COSMICChunk] = []

        for i in range(len(break_points)):
            start_idx = break_points[i]
            end_idx = break_points[i + 1] if i + 1 < len(break_points) else len(document.sentences)

            sentences = document.sentences[start_idx:end_idx]
            if not sentences:
                continue

            # Compute coherence from embedding variance
            chunk_embeddings = embeddings[start_idx:end_idx]
            coherence = self._compute_coherence(chunk_embeddings)

            chunk = self._create_chunk(
                document=document,
                sentences=sentences,
                chunk_index=len(chunks),
                coherence_score=coherence,
            )
            chunks.append(chunk)

        return chunks

    def _compute_coherence(self, embeddings: np.ndarray) -> float:
        """Compute coherence score from embeddings."""
        if len(embeddings) < 2:
            return 1.0

        # Compute mean embedding
        mean_emb = embeddings.mean(axis=0)

        # Average similarity to mean
        similarities = np.dot(embeddings, mean_emb)
        return float(np.mean(similarities))

    def _create_chunk(
        self,
        document: Document,
        sentences: list,
        chunk_index: int,
        coherence_score: float,
    ) -> COSMICChunk:
        """Create a COSMICChunk from sentences."""
        text = " ".join(s.text for s in sentences)
        token_count = count_tokens(text)

        page_start = sentences[0].page if sentences else 1
        page_end = sentences[-1].page if sentences else 1

        chunk_id = hashlib.md5(f"{document.id}:{chunk_index}:{text[:100]}".encode()).hexdigest()[
            :12
        ]

        return COSMICChunk(
            chunk_id=chunk_id,
            document_id=document.id,
            chunk_index=chunk_index,
            text=text,
            token_count=token_count,
            page_start=page_start,
            page_end=page_end,
            char_start=sentences[0].char_start if sentences else 0,
            char_end=sentences[-1].char_end if sentences else 0,
            domain="unknown",
            subdomain=None,
            domain_confidence=0.0,
            coherence_score=coherence_score,
            processing_mode=ProcessingMode.SLIDING_WINDOW,
            processing_confidence=0.5,
            processing_timestamp=datetime.utcnow(),
            cosmic_version=__version__,
            embedding_model=self.config.embedding.model_name,
        )
