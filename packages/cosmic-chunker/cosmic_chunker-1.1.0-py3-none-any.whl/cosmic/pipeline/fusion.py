"""Stage 4: Boundary Fusion combining structural and semantic signals."""

import logging
from dataclasses import dataclass

from cosmic.core.config import COSMICConfig
from cosmic.core.enums import BoundarySource
from cosmic.pipeline.base import (
    BoundaryCandidate,
    BoundaryResult,
    PipelineStage,
    StageResult,
)
from cosmic.pipeline.structure import StructureAnalysis

logger = logging.getLogger(__name__)


@dataclass
class FusionInput:
    """Input for boundary fusion stage."""

    structure_analysis: StructureAnalysis
    semantic_boundaries: BoundaryResult


@dataclass
class FusedBoundary:
    """A boundary after fusion of structural and semantic signals.

    Attributes:
        position: Sentence index for boundary
        confidence: Combined confidence score
        source: Which signals contributed (structural, semantic, both)
        structural_confidence: Confidence from structure (0 if not detected)
        semantic_confidence: Confidence from semantic (0 if not detected)
    """

    position: int
    confidence: float
    source: BoundarySource
    structural_confidence: float = 0.0
    semantic_confidence: float = 0.0
    dcs_score: float = 0.0

    def __repr__(self) -> str:
        return (
            f"FusedBoundary(pos={self.position}, "
            f"conf={self.confidence:.2f}, "
            f"src={self.source.value})"
        )


@dataclass
class FusionResult:
    """Result of boundary fusion."""

    boundaries: list[FusedBoundary]
    total_sentences: int
    fusion_stats: dict

    @property
    def num_boundaries(self) -> int:
        return len(self.boundaries)

    @property
    def positions(self) -> list[int]:
        return sorted(b.position for b in self.boundaries)

    def filter_by_confidence(self, min_confidence: float) -> "FusionResult":
        """Filter boundaries by minimum confidence."""
        filtered = [b for b in self.boundaries if b.confidence >= min_confidence]
        return FusionResult(
            boundaries=filtered,
            total_sentences=self.total_sentences,
            fusion_stats=self.fusion_stats,
        )


class BoundaryFusion(PipelineStage[FusionInput, FusionResult]):
    """Stage 4: Fuse structural and semantic boundary signals.

    Combines signals using weighted fusion:
    confidence = structural_weight * structural_conf + semantic_weight * semantic_conf

    Boundaries are accepted if combined confidence exceeds threshold.
    """

    stage_name = "boundary_fusion"

    def __init__(self, config: COSMICConfig):
        super().__init__(config)

    def initialize(self) -> None:
        """No initialization needed for fusion."""
        self._initialized = True
        logger.info(
            f"Boundary fusion initialized: "
            f"struct_weight={self.config.fusion.structural_weight}, "
            f"semantic_weight={self.config.fusion.semantic_weight}"
        )

    def validate_input(self, input_data: FusionInput) -> bool:
        """Validate fusion input."""
        if input_data is None:
            return False
        if input_data.semantic_boundaries is None:
            return False
        return True

    def process(self, input_data: FusionInput) -> StageResult[FusionResult]:
        """Fuse structural and semantic boundaries.

        Args:
            input_data: FusionInput with structure analysis and semantic boundaries

        Returns:
            StageResult containing FusionResult
        """
        structure = input_data.structure_analysis
        semantic = input_data.semantic_boundaries

        # Build position maps
        structural_map: dict[int, BoundaryCandidate] = {}
        if structure:
            for b in structure.structural_boundaries:
                structural_map[b.position] = b

        semantic_map: dict[int, BoundaryCandidate] = {}
        for b in semantic.candidates:
            semantic_map[b.position] = b

        # Get all unique positions
        all_positions = set(structural_map.keys()) | set(semantic_map.keys())

        # Fuse boundaries
        fused_boundaries = []
        stats = {
            "structural_only": 0,
            "semantic_only": 0,
            "both": 0,
            "rejected": 0,
        }

        for pos in sorted(all_positions):
            struct_b = structural_map.get(pos)
            sem_b = semantic_map.get(pos)

            struct_conf = struct_b.confidence if struct_b else 0.0
            sem_conf = sem_b.confidence if sem_b else 0.0
            dcs_score = sem_b.dcs_score if sem_b else 0.0

            # Weighted fusion
            fused_conf = (
                self.config.fusion.structural_weight * struct_conf
                + self.config.fusion.semantic_weight * sem_conf
            )

            # Determine source
            if struct_b and sem_b:
                source = BoundarySource.FUSED
                stats["both"] += 1
            elif struct_b:
                source = BoundarySource.STRUCTURAL
                stats["structural_only"] += 1
            else:
                source = BoundarySource.SEMANTIC
                stats["semantic_only"] += 1

            # Apply threshold
            if fused_conf >= self.config.fusion.acceptance_threshold:
                fused_boundaries.append(
                    FusedBoundary(
                        position=pos,
                        confidence=fused_conf,
                        source=source,
                        structural_confidence=struct_conf,
                        semantic_confidence=sem_conf,
                        dcs_score=dcs_score,
                    )
                )
            else:
                stats["rejected"] += 1

        logger.info(
            f"Fused {len(fused_boundaries)} boundaries from "
            f"{len(all_positions)} candidates "
            f"(rejected {stats['rejected']})"
        )

        result = FusionResult(
            boundaries=fused_boundaries,
            total_sentences=semantic.total_sentences,
            fusion_stats=stats,
        )

        # Calculate overall confidence
        avg_conf = (
            sum(b.confidence for b in fused_boundaries) / len(fused_boundaries)
            if fused_boundaries
            else 0.5
        )

        return StageResult(
            data=result,
            confidence=avg_conf,
            latency_ms=0.0,
            metadata={
                "num_fused": len(fused_boundaries),
                "num_structural": len(structural_map),
                "num_semantic": len(semantic_map),
                **stats,
            },
        )

    def fuse_with_priors(
        self,
        semantic_boundaries: BoundaryResult,
        structural_priors: dict[int, float],
    ) -> FusionResult:
        """Fuse semantic boundaries with structural prior probabilities.

        Alternative fusion method using priors instead of binary boundaries.

        Args:
            semantic_boundaries: Boundaries from Stage 2
            structural_priors: Dict mapping position to prior probability

        Returns:
            FusionResult
        """
        fused = []
        stats = {"from_prior": 0, "semantic_only": 0}

        for boundary in semantic_boundaries.candidates:
            pos = boundary.position
            prior = structural_priors.get(pos, 0.0)

            # Boost semantic confidence by structural prior
            boosted_conf = boundary.confidence + (self.config.fusion.structural_weight * prior)
            boosted_conf = min(1.0, boosted_conf)

            source = BoundarySource.FUSED if prior > 0 else BoundarySource.SEMANTIC
            if prior > 0:
                stats["from_prior"] += 1
            else:
                stats["semantic_only"] += 1

            if boosted_conf >= self.config.fusion.acceptance_threshold:
                fused.append(
                    FusedBoundary(
                        position=pos,
                        confidence=boosted_conf,
                        source=source,
                        structural_confidence=prior,
                        semantic_confidence=boundary.confidence,
                        dcs_score=boundary.dcs_score,
                    )
                )

        return FusionResult(
            boundaries=fused,
            total_sentences=semantic_boundaries.total_sentences,
            fusion_stats=stats,
        )
