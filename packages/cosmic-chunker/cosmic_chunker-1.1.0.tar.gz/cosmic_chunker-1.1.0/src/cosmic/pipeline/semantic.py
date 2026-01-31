"""Stage 2: Semantic Boundary Detection using DCS."""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document
from cosmic.exceptions import SemanticBoundaryError
from cosmic.models.embeddings import EmbeddingModel
from cosmic.pipeline.base import BoundaryCandidate, BoundaryResult, PipelineStage, StageResult
from cosmic.scoring.dcs import DCSWeights, DiscourseCoherenceScorer

logger = logging.getLogger(__name__)


@dataclass
class SemanticInput:
    """Input for semantic boundary detection."""

    document: Document
    structure_score: float = 0.5  # From Stage 1, influences processing


class SemanticBoundaryDetector(PipelineStage[SemanticInput, BoundaryResult]):
    """Stage 2: Detect semantic boundaries using Discourse Coherence Score.

    This stage:
    1. Encodes all sentences to embeddings
    2. Computes DCS at each position
    3. Identifies boundary candidates where DCS drops below threshold

    The stage uses the DCS formula:
    DCS = alpha * topical_coherence + beta * coreference_density + gamma * discourse_signal
    """

    stage_name = "semantic_boundary"

    def __init__(self, config: COSMICConfig):
        super().__init__(config)
        self._embedding_model: Optional[EmbeddingModel] = None
        self._dcs_scorer: Optional[DiscourseCoherenceScorer] = None

    def initialize(self) -> None:
        """Initialize embedding model and DCS scorer."""
        logger.info("Initializing semantic boundary detector")

        self._embedding_model = EmbeddingModel(self.config.embedding)
        self._dcs_scorer = DiscourseCoherenceScorer(DCSWeights.from_config(self.config.dcs))

        self._initialized = True
        logger.info(f"Initialized with DCS weights hash: {self._dcs_scorer.weights_hash}")

    @property
    def embedding_model(self) -> EmbeddingModel:
        """Get embedding model, initializing if needed."""
        self.ensure_initialized()
        return self._embedding_model  # type: ignore

    @property
    def dcs_scorer(self) -> DiscourseCoherenceScorer:
        """Get DCS scorer, initializing if needed."""
        self.ensure_initialized()
        return self._dcs_scorer  # type: ignore

    def validate_input(self, input_data: SemanticInput) -> bool:
        """Validate input has required fields."""
        if input_data is None:
            return False
        if input_data.document is None:
            return False
        if len(input_data.document.sentences) < 2:
            return False
        return True

    def process(self, input_data: SemanticInput) -> StageResult[BoundaryResult]:
        """Detect semantic boundaries in document.

        Args:
            input_data: SemanticInput with document and structure score

        Returns:
            StageResult containing BoundaryResult with candidates
        """
        document = input_data.document

        try:
            # Step 1: Get sentence texts
            sentences = [s.text for s in document.sentences]
            logger.debug(f"Processing {len(sentences)} sentences")

            # Step 2: Encode all sentences
            embeddings = self.embedding_model.encode(sentences)
            logger.debug(f"Generated embeddings shape: {embeddings.shape}")

            # Step 3: Detect boundaries using DCS
            raw_boundaries = self.dcs_scorer.detect_boundaries(
                sentences,
                embeddings,
                window_size=3,
            )

            # Step 4: Convert to BoundaryCandidate objects
            candidates = [
                BoundaryCandidate(
                    position=pos,
                    confidence=conf,
                    source="semantic",
                    dcs_score=dcs,
                    metadata={
                        "sentence_text": sentences[pos][:100] if pos < len(sentences) else "",
                    },
                )
                for pos, dcs, conf in raw_boundaries
            ]

            logger.info(
                f"Detected {len(candidates)} boundary candidates from {len(sentences)} sentences"
            )

            # Step 5: Compute overall confidence
            if candidates:
                avg_confidence = sum(c.confidence for c in candidates) / len(candidates)
            else:
                avg_confidence = 0.5

            result = BoundaryResult(
                candidates=candidates,
                total_sentences=len(sentences),
                processing_pathway="semantic",
            )

            return StageResult(
                data=result,
                confidence=avg_confidence,
                latency_ms=0.0,  # Will be set by __call__
                metadata={
                    "embedding_model": self.config.embedding.model_name,
                    "dcs_weights_hash": self.dcs_scorer.weights_hash,
                    "num_boundaries": len(candidates),
                    "embedding_cache_size": self.embedding_model.cache_size,
                },
            )

        except Exception as e:
            logger.error(f"Semantic boundary detection failed: {e}")
            raise SemanticBoundaryError(
                f"Failed to detect semantic boundaries: {e}",
                details={"document_id": document.id, "num_sentences": len(document.sentences)},
            )

    def get_embeddings(self, document: Document) -> np.ndarray:
        """Get embeddings for document sentences.

        Useful for downstream stages that need embeddings.
        """
        sentences = [s.text for s in document.sentences]
        return self.embedding_model.encode(sentences)

    def score_chunk_coherence(
        self,
        sentences: list[str],
        embeddings: Optional[np.ndarray] = None,
    ) -> float:
        """Score the coherence of a potential chunk.

        Args:
            sentences: List of sentence texts
            embeddings: Pre-computed embeddings (optional)

        Returns:
            Coherence score between 0 and 1
        """
        if embeddings is None:
            embeddings = self.embedding_model.encode(sentences)

        return self.dcs_scorer.score_span(sentences, embeddings)

    @property
    def weights_hash(self) -> str:
        """Get DCS weights hash for reproducibility."""
        return self.dcs_scorer.weights_hash


class ConsecutiveSimilarityDetector(PipelineStage[SemanticInput, BoundaryResult]):
    """Fallback: Simple consecutive similarity boundary detection.

    This is a simpler approach that only looks at embedding similarity
    between consecutive sentences, without the full DCS computation.
    Used as fallback when DCS fails.
    """

    stage_name = "consecutive_similarity"

    def __init__(self, config: COSMICConfig, similarity_threshold: float = 0.5):
        super().__init__(config)
        self._embedding_model: Optional[EmbeddingModel] = None
        self.similarity_threshold = similarity_threshold

    def initialize(self) -> None:
        self._embedding_model = EmbeddingModel(self.config.embedding)
        self._initialized = True

    @property
    def embedding_model(self) -> EmbeddingModel:
        self.ensure_initialized()
        return self._embedding_model  # type: ignore

    def validate_input(self, input_data: SemanticInput) -> bool:
        if input_data is None:
            return False
        return len(input_data.document.sentences) >= 2

    def process(self, input_data: SemanticInput) -> StageResult[BoundaryResult]:
        """Detect boundaries using consecutive sentence similarity."""
        document = input_data.document
        sentences = [s.text for s in document.sentences]

        # Encode sentences
        embeddings = self.embedding_model.encode(sentences)

        # Compute consecutive similarities
        similarities = self.embedding_model.consecutive_similarity(embeddings)

        # Find boundaries where similarity drops below threshold
        candidates = []
        for i, sim in enumerate(similarities):
            if sim < self.similarity_threshold:
                candidates.append(
                    BoundaryCandidate(
                        position=i + 1,  # Boundary after sentence i
                        confidence=1.0 - sim,  # Lower similarity = higher confidence
                        source="consecutive_similarity",
                        dcs_score=sim,
                    )
                )

        result = BoundaryResult(
            candidates=candidates,
            total_sentences=len(sentences),
            processing_pathway="fallback_similarity",
        )

        return StageResult(
            data=result,
            confidence=0.6,  # Lower confidence for fallback
            latency_ms=0.0,
            metadata={"method": "consecutive_similarity"},
        )
