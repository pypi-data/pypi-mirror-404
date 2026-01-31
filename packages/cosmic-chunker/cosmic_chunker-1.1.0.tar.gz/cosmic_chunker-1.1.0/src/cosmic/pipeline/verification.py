"""Stage 5: LLM Boundary Verification."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document
from cosmic.core.enums import BoundarySource
from cosmic.exceptions import LLMVerificationError
from cosmic.models.llm import LLMClient, MockLLMClient
from cosmic.pipeline.base import PipelineStage, StageResult
from cosmic.pipeline.fusion import FusedBoundary, FusionResult

logger = logging.getLogger(__name__)


@dataclass
class VerificationInput:
    """Input for LLM verification stage."""

    document: Document
    fusion_result: FusionResult


@dataclass
class VerifiedBoundary:
    """A boundary after LLM verification.

    Attributes:
        position: Sentence index for boundary
        confidence: Final confidence after verification
        source: Final source classification
        was_verified: Whether LLM was used to verify
        llm_agreed: Whether LLM agreed with the boundary
    """

    position: int
    confidence: float
    source: BoundarySource
    was_verified: bool = False
    llm_agreed: Optional[bool] = None
    original_confidence: float = 0.0

    def __repr__(self) -> str:
        verified = "LLM" if self.was_verified else "auto"
        return f"VerifiedBoundary(pos={self.position}, conf={self.confidence:.2f}, {verified})"


@dataclass
class VerificationResult:
    """Result of LLM verification."""

    boundaries: list[VerifiedBoundary]
    total_sentences: int
    verification_stats: dict

    @property
    def num_boundaries(self) -> int:
        return len(self.boundaries)

    @property
    def positions(self) -> list[int]:
        return sorted(b.position for b in self.boundaries)

    @property
    def num_verified(self) -> int:
        return sum(1 for b in self.boundaries if b.was_verified)

    @property
    def llm_agreement_rate(self) -> float:
        verified = [b for b in self.boundaries if b.was_verified]
        if not verified:
            return 1.0
        agreed = sum(1 for b in verified if b.llm_agreed)
        return agreed / len(verified)


class LLMVerifier(PipelineStage[VerificationInput, VerificationResult]):
    """Stage 5: Verify uncertain boundaries using LLM.

    Only boundaries with confidence below threshold are sent to LLM.
    High-confidence boundaries are auto-accepted.

    This stage:
    1. Filters boundaries needing verification (confidence < threshold)
    2. Extracts context around each boundary
    3. Sends to LLM for verification
    4. Updates confidence based on LLM response
    """

    stage_name = "llm_verification"

    def __init__(self, config: COSMICConfig, mock: bool = False):
        super().__init__(config)
        self._client: Optional[LLMClient] = None
        self._mock = mock

    def initialize(self) -> None:
        """Initialize LLM client."""
        if self._mock:
            self._client = MockLLMClient(self.config.llm)
        else:
            self._client = LLMClient(self.config.llm)

        self._initialized = True
        logger.info(
            f"LLM verifier initialized "
            f"(threshold={self.config.llm.confidence_threshold}, "
            f"mock={self._mock})"
        )

    @property
    def client(self) -> LLMClient:
        self.ensure_initialized()
        return self._client  # type: ignore

    def validate_input(self, input_data: VerificationInput) -> bool:
        if input_data is None:
            return False
        if input_data.document is None:
            return False
        if input_data.fusion_result is None:
            return False
        return True

    def process(self, input_data: VerificationInput) -> StageResult[VerificationResult]:
        """Verify boundaries using LLM.

        Args:
            input_data: VerificationInput with document and fused boundaries

        Returns:
            StageResult containing VerificationResult
        """
        # Run async verification in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self._process_async(input_data))

    async def _process_async(
        self, input_data: VerificationInput
    ) -> StageResult[VerificationResult]:
        """Async implementation of verification."""
        document = input_data.document
        fusion = input_data.fusion_result

        # Separate high and low confidence boundaries
        threshold = self.config.llm.confidence_threshold
        auto_accept = []
        needs_verification = []

        for boundary in fusion.boundaries:
            if boundary.confidence >= threshold:
                auto_accept.append(boundary)
            else:
                needs_verification.append(boundary)

        logger.info(
            f"Verification: {len(auto_accept)} auto-accept, {len(needs_verification)} need LLM"
        )

        # Create verified boundaries for auto-accept
        verified = [
            VerifiedBoundary(
                position=b.position,
                confidence=b.confidence,
                source=BoundarySource.AUTO_ACCEPT,
                was_verified=False,
                original_confidence=b.confidence,
            )
            for b in auto_accept
        ]

        # Verify uncertain boundaries with LLM
        if needs_verification and self.config.llm.enabled:
            try:
                llm_verified = await self._verify_with_llm(document, needs_verification)
                verified.extend(llm_verified)
            except LLMVerificationError as e:
                logger.warning(f"LLM verification failed: {e}")
                # Fall back to accepting at reduced confidence
                for b in needs_verification:
                    verified.append(
                        VerifiedBoundary(
                            position=b.position,
                            confidence=b.confidence * 0.8,  # Reduce confidence
                            source=b.source,
                            was_verified=False,
                            original_confidence=b.confidence,
                        )
                    )
        else:
            # LLM disabled - accept at current confidence
            for b in needs_verification:
                verified.append(
                    VerifiedBoundary(
                        position=b.position,
                        confidence=b.confidence,
                        source=b.source,
                        was_verified=False,
                        original_confidence=b.confidence,
                    )
                )

        # Sort by position
        verified.sort(key=lambda b: b.position)

        # Compute stats
        num_verified = sum(1 for b in verified if b.was_verified)
        num_agreed = sum(1 for b in verified if b.was_verified and b.llm_agreed)

        result = VerificationResult(
            boundaries=verified,
            total_sentences=fusion.total_sentences,
            verification_stats={
                "auto_accepted": len(auto_accept),
                "llm_verified": num_verified,
                "llm_agreed": num_agreed,
                "llm_rejected": num_verified - num_agreed,
            },
        )

        avg_conf = sum(b.confidence for b in verified) / len(verified) if verified else 0.5

        return StageResult(
            data=result,
            confidence=avg_conf,
            latency_ms=0.0,
            metadata=result.verification_stats,
        )

    async def _verify_with_llm(
        self,
        document: Document,
        boundaries: list[FusedBoundary],
    ) -> list[VerifiedBoundary]:
        """Verify boundaries using LLM.

        Args:
            document: Source document
            boundaries: Boundaries needing verification

        Returns:
            List of VerifiedBoundary objects
        """
        # Extract context for each boundary
        contexts = []
        for boundary in boundaries:
            before_text, after_text = self._get_boundary_context(document, boundary.position)
            contexts.append((before_text, after_text))

        # Batch verify
        results = await self.client.verify_boundaries_batch(contexts)

        # Create verified boundaries
        verified = []
        for boundary, (is_boundary, llm_conf) in zip(boundaries, results):
            if is_boundary:
                # LLM agrees - boost confidence
                new_conf = min(1.0, boundary.confidence + 0.2)
                verified.append(
                    VerifiedBoundary(
                        position=boundary.position,
                        confidence=new_conf,
                        source=BoundarySource.LLM_VERIFIED,
                        was_verified=True,
                        llm_agreed=True,
                        original_confidence=boundary.confidence,
                    )
                )
            else:
                # LLM disagrees - reduce confidence but keep if still above threshold
                new_conf = boundary.confidence * 0.5
                if new_conf >= 0.3:  # Minimum threshold for keeping
                    verified.append(
                        VerifiedBoundary(
                            position=boundary.position,
                            confidence=new_conf,
                            source=BoundarySource.LLM_VERIFIED,
                            was_verified=True,
                            llm_agreed=False,
                            original_confidence=boundary.confidence,
                        )
                    )
                # Else: boundary is rejected (not added to verified list)

        return verified

    def _get_boundary_context(
        self,
        document: Document,
        position: int,
        context_sentences: int = 3,
    ) -> tuple[str, str]:
        """Get text context around a boundary position.

        Args:
            document: Source document
            position: Sentence index of boundary
            context_sentences: Number of sentences on each side

        Returns:
            Tuple of (before_text, after_text)
        """
        before_start = max(0, position - context_sentences)
        after_end = min(len(document.sentences), position + context_sentences)

        before_sentences = document.sentences[before_start:position]
        after_sentences = document.sentences[position:after_end]

        before_text = " ".join(s.text for s in before_sentences)
        after_text = " ".join(s.text for s in after_sentences)

        return before_text, after_text

    async def close(self) -> None:
        """Close LLM client connections."""
        if self._client:
            await self._client.close()
