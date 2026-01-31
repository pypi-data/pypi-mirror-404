"""Base classes for COSMIC pipeline stages."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

from cosmic.core.config import COSMICConfig

logger = logging.getLogger(__name__)

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


@dataclass
class StageResult(Generic[OutputT]):
    """Result from a pipeline stage.

    Attributes:
        data: The output data from the stage
        confidence: Confidence score for this result (0-1)
        latency_ms: Processing time in milliseconds
        metadata: Additional stage-specific metadata
    """

    data: OutputT
    confidence: float
    latency_ms: float
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"StageResult(confidence={self.confidence:.2f}, latency={self.latency_ms:.1f}ms)"


class PipelineStage(ABC, Generic[InputT, OutputT]):
    """Abstract base class for pipeline stages.

    Each COSMIC stage inherits from this class and implements:
    - process(): Main processing logic
    - validate_input(): Input validation
    - get_fallback(): Optional fallback stage

    Example:
        class SemanticBoundaryDetector(PipelineStage[Document, BoundaryResult]):
            stage_name = "semantic_boundary"

            def process(self, doc: Document) -> StageResult[BoundaryResult]:
                # Processing logic
                pass
    """

    stage_name: str = "base"

    def __init__(self, config: COSMICConfig):
        self.config = config
        self._initialized = False

    def initialize(self) -> None:
        """Initialize stage resources (models, caches, etc.).

        Override this method to load models lazily on first use.
        """
        self._initialized = True

    def ensure_initialized(self) -> None:
        """Ensure stage is initialized before processing."""
        if not self._initialized:
            self.initialize()

    @abstractmethod
    def process(self, input_data: InputT) -> StageResult[OutputT]:
        """Process input and return stage result.

        This is the main method to implement for each stage.
        """
        pass

    def validate_input(self, input_data: InputT) -> bool:
        """Validate input before processing.

        Override to add stage-specific validation.
        Returns True if input is valid.
        """
        return input_data is not None

    def get_fallback(self) -> Optional["PipelineStage[InputT, OutputT]"]:
        """Return fallback stage if this one fails.

        Override to provide a fallback strategy.
        """
        return None

    def __call__(self, input_data: InputT) -> StageResult[OutputT]:
        """Execute stage with timing and error handling."""
        self.ensure_initialized()

        if not self.validate_input(input_data):
            raise ValueError(f"Invalid input for stage {self.stage_name}")

        start_time = time.perf_counter()
        try:
            result = self.process(input_data)
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Update latency in result
            return StageResult(
                data=result.data,
                confidence=result.confidence,
                latency_ms=latency_ms,
                metadata=result.metadata,
            )

        except Exception as e:
            logger.error(f"Stage {self.stage_name} failed: {e}")
            fallback = self.get_fallback()
            if fallback:
                logger.info(f"Using fallback for stage {self.stage_name}")
                return fallback(input_data)
            raise

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(stage={self.stage_name})"


@dataclass
class BoundaryCandidate:
    """A candidate boundary position between chunks.

    Attributes:
        position: Sentence index where boundary would occur
        confidence: Confidence that this is a real boundary (0-1)
        source: What detected this boundary (structural, semantic, etc.)
        dcs_score: Discourse Coherence Score at this position
    """

    position: int
    confidence: float
    source: str
    dcs_score: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"Boundary(pos={self.position}, conf={self.confidence:.2f}, src={self.source})"


@dataclass
class BoundaryResult:
    """Result of boundary detection containing all candidates."""

    candidates: list[BoundaryCandidate]
    total_sentences: int
    processing_pathway: str = "full"

    @property
    def num_boundaries(self) -> int:
        return len(self.candidates)

    @property
    def boundary_positions(self) -> list[int]:
        return [b.position for b in self.candidates]

    def filter_by_confidence(self, min_confidence: float) -> "BoundaryResult":
        """Return new result with only boundaries above threshold."""
        filtered = [b for b in self.candidates if b.confidence >= min_confidence]
        return BoundaryResult(
            candidates=filtered,
            total_sentences=self.total_sentences,
            processing_pathway=self.processing_pathway,
        )
