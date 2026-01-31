"""Semantic-only chunking without structural analysis."""

import hashlib
import logging
from datetime import datetime
from typing import Optional

import numpy as np

from cosmic import __version__
from cosmic.core.chunk import COSMICChunk
from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document, Sentence
from cosmic.core.enums import ProcessingMode
from cosmic.models.embeddings import EmbeddingModel
from cosmic.scoring.dcs import DCSWeights, DiscourseCoherenceScorer
from cosmic.utils.tokenizer import count_tokens

logger = logging.getLogger(__name__)


class SemanticOnlyChunker:
    """Semantic-only chunking using DCS without structural priors.

    Uses the full DCS scoring mechanism but skips structural analysis.
    Good for unstructured documents that lack clear formatting.
    """

    def __init__(self, config: COSMICConfig):
        self.config = config
        self.min_tokens = config.chunks.min_tokens
        self.max_tokens = config.chunks.max_tokens
        self._embedding_model: Optional[EmbeddingModel] = None
        self._dcs_scorer: Optional[DiscourseCoherenceScorer] = None

    @property
    def embedding_model(self) -> EmbeddingModel:
        """Lazy load embedding model."""
        if self._embedding_model is None:
            self._embedding_model = EmbeddingModel(self.config.embedding)
        return self._embedding_model

    @property
    def dcs_scorer(self) -> DiscourseCoherenceScorer:
        """Lazy load DCS scorer."""
        if self._dcs_scorer is None:
            weights = DCSWeights.from_config(self.config.dcs)
            self._dcs_scorer = DiscourseCoherenceScorer(weights)
        return self._dcs_scorer

    def chunk(self, document: Document) -> list[COSMICChunk]:
        """Chunk document using semantic-only strategy.

        Args:
            document: Document to chunk

        Returns:
            List of COSMICChunk with DCS-based coherence scoring
        """
        logger.info(f"Semantic-only chunking document {document.id}")

        if len(document.sentences) == 0:
            return []

        # Get sentence embeddings
        sentence_texts = [s.text for s in document.sentences]
        embeddings = self.embedding_model.encode(sentence_texts)

        # Detect boundaries using DCS
        boundaries = self.dcs_scorer.detect_boundaries(sentence_texts, embeddings, window_size=3)

        # Filter boundaries by token constraints
        valid_boundaries = self._filter_boundaries_by_tokens(document.sentences, boundaries)

        # Create chunks
        chunks = self._create_chunks(document, embeddings, valid_boundaries)

        logger.info(f"Created {len(chunks)} semantic-only chunks")
        return chunks

    def _filter_boundaries_by_tokens(
        self,
        sentences: list,
        boundaries: list[tuple[int, float, float]],
    ) -> list[int]:
        """Filter boundaries to respect token constraints.

        Ensures chunks are between min_tokens and max_tokens.
        """
        # Sort boundaries by confidence (descending)
        sorted_bounds = sorted(boundaries, key=lambda x: x[2], reverse=True)

        # Start with document boundaries
        accepted = [0]
        last_boundary = 0

        for pos, dcs, conf in sorted_bounds:
            # Calculate tokens since last boundary
            tokens_since_last = sum(count_tokens(s.text) for s in sentences[last_boundary:pos])

            # Check if boundary respects constraints
            if tokens_since_last >= self.min_tokens:
                accepted.append(pos)
                last_boundary = pos

        return sorted(set(accepted))

    def _create_chunks(
        self,
        document: Document,
        embeddings: np.ndarray,
        boundaries: list[int],
    ) -> list[COSMICChunk]:
        """Create chunks from boundary positions."""
        chunks: list[COSMICChunk] = []

        # Add end boundary
        all_boundaries = boundaries + [len(document.sentences)]

        for i in range(len(all_boundaries) - 1):
            start_idx = all_boundaries[i]
            end_idx = all_boundaries[i + 1]

            sentences = document.sentences[start_idx:end_idx]
            if not sentences:
                continue

            # Compute chunk coherence
            chunk_embeddings = embeddings[start_idx:end_idx]
            sentence_texts = [s.text for s in sentences]
            coherence = self.dcs_scorer.score_span(sentence_texts, chunk_embeddings)

            chunk = self._create_chunk(
                document=document,
                sentences=sentences,
                chunk_index=len(chunks),
                coherence_score=coherence,
            )
            chunks.append(chunk)

        # Enforce max_tokens by splitting large chunks
        final_chunks = []
        for chunk in chunks:
            if chunk.token_count > self.max_tokens:
                split_chunks = self._split_large_chunk(document, chunk)
                final_chunks.extend(split_chunks)
            else:
                final_chunks.append(chunk)

        # Re-index chunks
        for i, chunk in enumerate(final_chunks):
            # Create new chunk with updated index
            final_chunks[i] = COSMICChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                chunk_index=i,
                text=chunk.text,
                token_count=chunk.token_count,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                domain=chunk.domain,
                subdomain=chunk.subdomain,
                domain_confidence=chunk.domain_confidence,
                coherence_score=chunk.coherence_score,
                processing_mode=chunk.processing_mode,
                processing_confidence=chunk.processing_confidence,
                processing_timestamp=chunk.processing_timestamp,
                cosmic_version=chunk.cosmic_version,
                dcs_weights_hash=self.dcs_scorer.weights_hash,
                embedding_model=self.config.embedding.model_name,
            )

        return final_chunks

    def _split_large_chunk(
        self,
        document: Document,
        chunk: COSMICChunk,
    ) -> list[COSMICChunk]:
        """Split a chunk that exceeds max_tokens."""
        # Find sentences in this chunk
        sentences = [
            s
            for s in document.sentences
            if s.char_start >= chunk.char_start and s.char_end <= chunk.char_end
        ]

        # Split at roughly target_tokens
        result: list[COSMICChunk] = []
        current_sentences: list[Sentence] = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = count_tokens(sentence.text)

            if current_tokens + sentence_tokens > self.max_tokens and current_sentences:
                result.append(
                    self._create_chunk(
                        document=document,
                        sentences=current_sentences,
                        chunk_index=len(result),
                        coherence_score=0.6,  # Reduced confidence for forced splits
                    )
                )
                current_sentences = [sentence]
                current_tokens = sentence_tokens
            else:
                current_sentences.append(sentence)
                current_tokens += sentence_tokens

        if current_sentences:
            result.append(
                self._create_chunk(
                    document=document,
                    sentences=current_sentences,
                    chunk_index=len(result),
                    coherence_score=0.6,
                )
            )

        return result

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
            processing_mode=ProcessingMode.SEMANTIC_ONLY,
            processing_confidence=0.7,
            processing_timestamp=datetime.utcnow(),
            cosmic_version=__version__,
            dcs_weights_hash=self.dcs_scorer.weights_hash,
            embedding_model=self.config.embedding.model_name,
        )
