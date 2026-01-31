"""Main COSMIC Chunker - Entry point for the framework.

COSMICChunker orchestrates the 6-stage pipeline with graceful degradation.
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from cosmic import __version__
from cosmic.core.chunk import COSMICChunk
from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document
from cosmic.core.enums import ProcessingMode
from cosmic.exceptions import (
    DomainClassificationError,
    LLMVerificationError,
    ReferenceResolutionError,
    SemanticBoundaryError,
    StructureAnalysisError,
)
from cosmic.fallback.fixed_length import FixedLengthChunker
from cosmic.fallback.semantic_only import SemanticOnlyChunker
from cosmic.fallback.sliding_window import SlidingWindowChunker
from cosmic.pipeline.base import BoundaryResult
from cosmic.pipeline.domain import DomainClassificationStage, DomainInput, DomainResult
from cosmic.pipeline.fusion import BoundaryFusion, FusionInput
from cosmic.pipeline.reference import ReferenceInput, ReferenceLinker
from cosmic.pipeline.semantic import SemanticBoundaryDetector, SemanticInput
from cosmic.pipeline.structure import StructureAnalysis, StructureAnalyzer
from cosmic.pipeline.verification import LLMVerifier, VerificationInput
from cosmic.utils.tokenizer import count_tokens

logger = logging.getLogger(__name__)


class COSMICChunker:
    """Main COSMIC chunker with full 6-stage pipeline and fallbacks.

    This is the primary entry point for the COSMIC framework. It orchestrates:
    1. Structure Analysis (pathway selection)
    2. Semantic Boundary Detection (DCS)
    3. Domain Classification (MST clustering)
    4. Boundary Fusion (structural + semantic)
    5. LLM Verification (optional)
    6. Reference Linking (coreference)

    Implements graceful degradation:
    - Full COSMIC -> Semantic-only -> Sliding window -> Fixed-length

    Example:
        chunker = COSMICChunker()
        document = Document.from_text("Your document text here...")
        chunks = chunker.chunk_document(document)

        for chunk in chunks:
            print(f"{chunk.chunk_id}: {chunk.domain} ({chunk.coherence_score:.2f})")
    """

    def __init__(
        self,
        config: Optional[COSMICConfig] = None,
        config_path: Optional[Path] = None,
    ):
        """Initialize COSMIC chunker.

        Args:
            config: COSMICConfig instance
            config_path: Path to YAML config file
        """
        if config_path:
            self.config = COSMICConfig.from_yaml(config_path)
        else:
            self.config = config or COSMICConfig()

        # Pipeline stages (lazy initialized)
        self._structure_analyzer: Optional[StructureAnalyzer] = None
        self._semantic_detector: Optional[SemanticBoundaryDetector] = None
        self._domain_classifier: Optional[DomainClassificationStage] = None
        self._boundary_fusion: Optional[BoundaryFusion] = None
        self._llm_verifier: Optional[LLMVerifier] = None
        self._reference_linker: Optional[ReferenceLinker] = None

        # Fallback chunkers
        self._semantic_only: Optional[SemanticOnlyChunker] = None
        self._sliding_window: Optional[SlidingWindowChunker] = None
        self._fixed_length: Optional[FixedLengthChunker] = None

        logger.info("COSMICChunker initialized")

    # Lazy initialization properties
    @property
    def structure_analyzer(self) -> StructureAnalyzer:
        if self._structure_analyzer is None:
            self._structure_analyzer = StructureAnalyzer(self.config)
        return self._structure_analyzer

    @property
    def semantic_detector(self) -> SemanticBoundaryDetector:
        if self._semantic_detector is None:
            self._semantic_detector = SemanticBoundaryDetector(self.config)
        return self._semantic_detector

    @property
    def domain_classifier(self) -> DomainClassificationStage:
        if self._domain_classifier is None:
            self._domain_classifier = DomainClassificationStage(self.config)
        return self._domain_classifier

    @property
    def boundary_fusion(self) -> BoundaryFusion:
        if self._boundary_fusion is None:
            self._boundary_fusion = BoundaryFusion(self.config)
        return self._boundary_fusion

    @property
    def llm_verifier(self) -> Optional[LLMVerifier]:
        if self._llm_verifier is None and self.config.llm.enabled:
            self._llm_verifier = LLMVerifier(self.config)
        return self._llm_verifier

    @property
    def reference_linker(self) -> Optional[ReferenceLinker]:
        if self._reference_linker is None and self.config.reference.enabled:
            self._reference_linker = ReferenceLinker(self.config)
        return self._reference_linker

    @property
    def semantic_only(self) -> SemanticOnlyChunker:
        if self._semantic_only is None:
            self._semantic_only = SemanticOnlyChunker(self.config)
        return self._semantic_only

    @property
    def sliding_window(self) -> SlidingWindowChunker:
        if self._sliding_window is None:
            self._sliding_window = SlidingWindowChunker(self.config)
        return self._sliding_window

    @property
    def fixed_length(self) -> FixedLengthChunker:
        if self._fixed_length is None:
            self._fixed_length = FixedLengthChunker(self.config)
        return self._fixed_length

    def chunk_document(
        self,
        document: Document,
        strategy: str = "auto",
    ) -> list[COSMICChunk]:
        """Chunk a document using COSMIC framework.

        Args:
            document: Document to chunk
            strategy: Chunking strategy
                - "auto": Automatic pathway selection (default)
                - "full": Force full COSMIC pipeline
                - "semantic": Semantic-only (skip structure)
                - "sliding": Sliding window with basic semantics
                - "fixed": Fixed-length fallback

        Returns:
            List of COSMICChunk with rich metadata
        """
        logger.info(f"Chunking document {document.id} with strategy={strategy}")

        if strategy == "fixed":
            return self.fixed_length.chunk(document)
        elif strategy == "sliding":
            return self.sliding_window.chunk(document)
        elif strategy == "semantic":
            return self.semantic_only.chunk(document)
        elif strategy == "full":
            return self._run_full_pipeline(document)
        else:  # auto
            return self._run_auto_pipeline(document)

    def _run_auto_pipeline(self, document: Document) -> list[COSMICChunk]:
        """Run pipeline with automatic pathway selection."""
        try:
            # Stage 1: Structure analysis
            structure_result = self.structure_analyzer(document)
            structure = structure_result.data

            logger.info(
                f"Document structure score: {structure.score:.3f}, pathway: {structure.pathway}"
            )

            if structure.pathway == "full":
                return self._run_full_pipeline(document, structure)
            elif structure.pathway == "semantic":
                return self._run_semantic_pipeline(document)
            else:
                return self._run_fallback_pipeline(document)

        except StructureAnalysisError as e:
            logger.warning(f"Structure analysis failed: {e}")
            return self._run_semantic_pipeline(document)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return self._run_fallback_pipeline(document)

    def _run_full_pipeline(
        self,
        document: Document,
        structure: Optional[StructureAnalysis] = None,
    ) -> list[COSMICChunk]:
        """Run full 6-stage COSMIC pipeline."""
        try:
            # Stage 1: Structure analysis (if not provided)
            if structure is None:
                structure_result = self.structure_analyzer(document)
                structure = structure_result.data

            # Stage 2: Semantic boundary detection
            semantic_input = SemanticInput(
                document=document,
                structure_score=structure.score,
            )
            semantic_result = self.semantic_detector(semantic_input)

            # Stage 3: Domain classification (on preliminary chunks)
            boundary_positions = semantic_result.data.boundary_positions
            domain_input = DomainInput(
                document=document,
                boundaries=boundary_positions,
            )
            domain_result = self.domain_classifier(domain_input)

            # Stage 4: Boundary fusion
            fusion_input = FusionInput(
                structure_analysis=structure,
                semantic_boundaries=semantic_result.data,
            )
            fusion_result = self.boundary_fusion(fusion_input)

            # Stage 5: LLM verification (if enabled)
            if self.llm_verifier:
                try:
                    verify_input = VerificationInput(
                        document=document,
                        fusion_result=fusion_result.data,
                    )
                    verify_result = self.llm_verifier(verify_input)
                    final_boundaries = verify_result.data.positions
                except LLMVerificationError as e:
                    logger.warning(f"LLM verification failed: {e}")
                    final_boundaries = fusion_result.data.positions
            else:
                final_boundaries = fusion_result.data.positions

            # Create chunks from final boundaries
            chunks = self._create_chunks(
                document=document,
                boundaries=final_boundaries,
                domain_result=domain_result.data,
                mode=ProcessingMode.FULL_COSMIC,
            )

            # Stage 6: Reference linking (if enabled)
            if self.reference_linker:
                try:
                    ref_input = ReferenceInput(
                        document=document,
                        chunk_boundaries=final_boundaries,
                    )
                    ref_result = self.reference_linker(ref_input)
                    chunks = self.reference_linker.enrich_chunks(chunks, ref_result.data.graph)
                except ReferenceResolutionError as e:
                    logger.warning(f"Reference linking failed: {e}")

            logger.info(f"Full pipeline created {len(chunks)} chunks")
            return chunks

        except SemanticBoundaryError as e:
            logger.warning(f"Semantic detection failed: {e}")
            return self._run_semantic_pipeline(document)
        except DomainClassificationError as e:
            logger.warning(f"Domain classification failed: {e}")
            # Continue without domain info
            return self._continue_without_domains(document, semantic_result.data)
        except Exception as e:
            logger.error(f"Full pipeline failed: {e}")
            return self._run_fallback_pipeline(document)

    def _run_semantic_pipeline(self, document: Document) -> list[COSMICChunk]:
        """Run semantic-only pipeline."""
        try:
            return self.semantic_only.chunk(document)
        except Exception as e:
            logger.warning(f"Semantic-only failed: {e}")
            return self._run_fallback_pipeline(document)

    def _run_fallback_pipeline(self, document: Document) -> list[COSMICChunk]:
        """Run fallback pipeline (sliding window or fixed)."""
        try:
            return self.sliding_window.chunk(document)
        except Exception as e:
            logger.warning(f"Sliding window failed: {e}")
            return self.fixed_length.chunk(document)

    def _continue_without_domains(
        self,
        document: Document,
        semantic_result: BoundaryResult,
    ) -> list[COSMICChunk]:
        """Continue pipeline without domain classification."""
        boundaries = semantic_result.boundary_positions

        chunks = self._create_chunks(
            document=document,
            boundaries=boundaries,
            domain_result=None,
            mode=ProcessingMode.SEMANTIC_ONLY,
        )

        return chunks

    def _create_chunks(
        self,
        document: Document,
        boundaries: list[int],
        domain_result: Optional[DomainResult],
        mode: ProcessingMode,
    ) -> list[COSMICChunk]:
        """Create COSMICChunk objects from boundaries."""
        chunks: list[COSMICChunk] = []

        # Ensure boundaries are sorted and include start
        boundaries = sorted(set([0] + boundaries))

        for i in range(len(boundaries)):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1] if i + 1 < len(boundaries) else len(document.sentences)

            sentences = document.sentences[start_idx:end_idx]
            if not sentences:
                continue

            text = " ".join(s.text for s in sentences)
            token_count = count_tokens(text)

            # Get domain assignment if available
            if domain_result and i < len(domain_result.assignments):
                domain_assignment = domain_result.assignments[i]
                domain = domain_assignment.domain
                subdomain = domain_assignment.subdomain
                domain_conf = domain_assignment.confidence
            else:
                domain = "unknown"
                subdomain = None
                domain_conf = 0.0

            # Compute chunk coherence
            coherence = self._estimate_coherence(sentences)

            chunk_id = hashlib.md5(f"{document.id}:{i}:{text[:100]}".encode()).hexdigest()[:12]

            chunk = COSMICChunk(
                chunk_id=chunk_id,
                document_id=document.id,
                chunk_index=i,
                text=text,
                token_count=token_count,
                page_start=sentences[0].page,
                page_end=sentences[-1].page,
                char_start=sentences[0].char_start,
                char_end=sentences[-1].char_end,
                domain=domain,
                subdomain=subdomain,
                domain_confidence=domain_conf,
                coherence_score=coherence,
                processing_mode=mode,
                processing_confidence=0.8 if mode == ProcessingMode.FULL_COSMIC else 0.6,
                processing_timestamp=datetime.utcnow(),
                cosmic_version=__version__,
                dcs_weights_hash=self.semantic_detector.weights_hash,
                embedding_model=self.config.embedding.model_name,
            )
            chunks.append(chunk)

        return chunks

    def _estimate_coherence(self, sentences: list) -> float:
        """Estimate coherence for sentences without full DCS computation."""
        if len(sentences) <= 1:
            return 1.0

        # Simple heuristic: shorter spans are more coherent
        avg_length = sum(len(s.text) for s in sentences) / len(sentences)
        coherence = min(1.0, 200 / max(avg_length, 50))
        return coherence


def chunk_text(
    text: str,
    config: Optional[COSMICConfig] = None,
    strategy: str = "auto",
) -> list[COSMICChunk]:
    """Convenience function to chunk plain text.

    Args:
        text: Text to chunk
        config: Optional configuration
        strategy: Chunking strategy

    Returns:
        List of COSMICChunk objects
    """
    chunker = COSMICChunker(config)
    document = Document.from_text(text)
    return chunker.chunk_document(document, strategy)
