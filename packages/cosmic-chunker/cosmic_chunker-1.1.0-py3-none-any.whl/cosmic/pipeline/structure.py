"""Stage 1: Structure Analysis for pathway selection."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document
from cosmic.core.enums import StructuralElement
from cosmic.exceptions import StructureAnalysisError
from cosmic.pipeline.base import BoundaryCandidate, PipelineStage, StageResult
from cosmic.utils.patterns import StructuralMatch, StructuralPatterns

logger = logging.getLogger(__name__)


@dataclass
class StructureAnalysis:
    """Result of structure analysis.

    Attributes:
        score: Overall structure score (0-1)
        pathway: Recommended processing pathway
        elements: Detected structural elements
        structural_boundaries: Boundary candidates from structure
    """

    score: float
    pathway: str  # "full", "semantic", "fallback"
    elements: list[StructuralMatch] = field(default_factory=list)
    structural_boundaries: list[BoundaryCandidate] = field(default_factory=list)

    @property
    def is_structured(self) -> bool:
        """Whether document has significant structure."""
        return self.score >= 0.4

    @property
    def heading_count(self) -> int:
        """Count of heading elements."""
        heading_types = {
            StructuralElement.HEADING_NUMBERED,
            StructuralElement.HEADING_LETTER,
            StructuralElement.HEADING_HASH,
        }
        return sum(1 for e in self.elements if e.element_type in heading_types)

    @property
    def list_count(self) -> int:
        """Count of list elements."""
        list_types = {
            StructuralElement.BULLET_LIST,
            StructuralElement.NUMBERED_LIST,
        }
        return sum(1 for e in self.elements if e.element_type in list_types)


class StructureAnalyzer(PipelineStage[Document, StructureAnalysis]):
    """Stage 1: Analyze document structure and select processing pathway.

    This stage:
    1. Detects structural elements (headings, lists, etc.)
    2. Computes overall structure score
    3. Selects processing pathway based on score
    4. Identifies structural boundary candidates

    Pathway selection:
    - score >= full_threshold: Full COSMIC pipeline
    - score >= semantic_threshold: Semantic-only (skip structural priors)
    - score < semantic_threshold: Fallback (sliding window)
    """

    stage_name = "structure_analysis"

    def __init__(self, config: COSMICConfig):
        super().__init__(config)
        self._patterns: Optional[StructuralPatterns] = None

    def initialize(self) -> None:
        """Initialize pattern matcher."""
        self._patterns = StructuralPatterns()
        self._initialized = True
        logger.info("Structure analyzer initialized")

    @property
    def patterns(self) -> StructuralPatterns:
        """Get pattern matcher, initializing if needed."""
        self.ensure_initialized()
        return self._patterns  # type: ignore

    def validate_input(self, input_data: Document) -> bool:
        """Validate document input."""
        if input_data is None:
            return False
        if not input_data.text:
            return False
        return True

    def process(self, document: Document) -> StageResult[StructureAnalysis]:
        """Analyze document structure.

        Args:
            document: Document to analyze

        Returns:
            StageResult containing StructureAnalysis
        """
        try:
            # Step 1: Find structural elements
            elements = self.patterns.find_structural_elements(document.text)
            logger.debug(f"Found {len(elements)} structural elements")

            # Step 2: Compute structure score
            score = self.patterns.compute_structure_score(document.text)
            logger.debug(f"Structure score: {score:.3f}")

            # Step 3: Select pathway
            pathway = self._select_pathway(score)
            logger.info(f"Document {document.id}: pathway={pathway}, score={score:.3f}")

            # Step 4: Create structural boundary candidates
            boundaries = self._create_boundary_candidates(document, elements)

            analysis = StructureAnalysis(
                score=score,
                pathway=pathway,
                elements=elements,
                structural_boundaries=boundaries,
            )

            return StageResult(
                data=analysis,
                confidence=score,  # Use structure score as confidence
                latency_ms=0.0,
                metadata={
                    "num_elements": len(elements),
                    "num_headings": analysis.heading_count,
                    "num_lists": analysis.list_count,
                    "pathway": pathway,
                },
            )

        except Exception as e:
            logger.error(f"Structure analysis failed: {e}")
            raise StructureAnalysisError(
                f"Failed to analyze structure: {e}",
                details={"document_id": document.id},
            )

    def _select_pathway(self, score: float) -> str:
        """Select processing pathway based on structure score."""
        if score >= self.config.structure.full_threshold:
            return "full"
        elif score >= self.config.structure.semantic_threshold:
            return "semantic"
        else:
            return "fallback"

    def _create_boundary_candidates(
        self,
        document: Document,
        elements: list[StructuralMatch],
    ) -> list[BoundaryCandidate]:
        """Create boundary candidates from structural elements.

        Maps structural elements to sentence positions.
        """
        candidates = []

        for element in elements:
            # Find sentence containing this element
            sentence_idx = self._find_sentence_for_offset(document, element.start)

            if sentence_idx is not None and sentence_idx > 0:
                candidates.append(
                    BoundaryCandidate(
                        position=sentence_idx,
                        confidence=element.boundary_prior,
                        source="structural",
                        metadata={
                            "element_type": element.element_type.value,
                            "text_preview": element.text[:50],
                            "level": element.level,
                        },
                    )
                )

        # Deduplicate by position (keep highest confidence)
        position_map: dict[int, BoundaryCandidate] = {}
        for candidate in candidates:
            pos = candidate.position
            if pos not in position_map or candidate.confidence > position_map[pos].confidence:
                position_map[pos] = candidate

        return list(position_map.values())

    def _find_sentence_for_offset(
        self,
        document: Document,
        char_offset: int,
    ) -> Optional[int]:
        """Find sentence index containing a character offset."""
        for i, sentence in enumerate(document.sentences):
            if sentence.char_start <= char_offset < sentence.char_end:
                return i
        return None

    def get_structural_priors(
        self,
        document: Document,
    ) -> dict[int, float]:
        """Get boundary prior probabilities for each sentence position.

        Returns:
            Dict mapping sentence index to boundary prior
        """
        priors = {}

        for i, sentence in enumerate(document.sentences):
            prior = self.patterns.get_boundary_prior(sentence.text)
            if prior > 0:
                priors[i] = prior

        return priors
