"""Stage 6: Reference Linking between chunks."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from cosmic.core.chunk import COSMICChunk
from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document
from cosmic.exceptions import ReferenceResolutionError
from cosmic.models.coreference import (
    CoreferenceResolver,
    ExplicitReferenceDetector,
)
from cosmic.pipeline.base import PipelineStage, StageResult

logger = logging.getLogger(__name__)


@dataclass
class ChunkReference:
    """A reference between chunks."""

    from_chunk_idx: int
    to_chunk_idx: int
    reference_type: str  # "explicit", "coreference", "implicit"
    reference_text: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ReferenceGraph:
    """Graph of references between chunks."""

    references: list[ChunkReference]
    chunk_count: int

    # Adjacency lists
    outgoing: dict[int, list[int]] = field(default_factory=lambda: defaultdict(list))
    incoming: dict[int, list[int]] = field(default_factory=lambda: defaultdict(list))

    def __post_init__(self) -> None:
        """Build adjacency lists."""
        for ref in self.references:
            self.outgoing[ref.from_chunk_idx].append(ref.to_chunk_idx)
            self.incoming[ref.to_chunk_idx].append(ref.from_chunk_idx)

    def get_references_from(self, chunk_idx: int) -> list[int]:
        """Get chunks referenced by this chunk."""
        return self.outgoing.get(chunk_idx, [])

    def get_references_to(self, chunk_idx: int) -> list[int]:
        """Get chunks that reference this chunk."""
        return self.incoming.get(chunk_idx, [])

    def has_unresolved_references(self, chunk_idx: int) -> bool:
        """Check if chunk has references we couldn't resolve."""
        refs = self.get_references_from(chunk_idx)
        return -1 in refs  # -1 indicates unresolved reference


@dataclass
class ReferenceInput:
    """Input for reference linking stage."""

    document: Document
    chunk_boundaries: list[int]  # Sentence indices where chunks start


@dataclass
class ReferenceResult:
    """Result of reference linking."""

    graph: ReferenceGraph
    chains_found: int
    explicit_refs_found: int


class ReferenceLinker(PipelineStage[ReferenceInput, ReferenceResult]):
    """Stage 6: Link references between chunks.

    This stage:
    1. Detects explicit references (Section X, Appendix Y)
    2. Resolves coreferences spanning chunk boundaries
    3. Builds a reference graph for chunk dependencies
    """

    stage_name = "reference_linking"

    def __init__(self, config: COSMICConfig):
        super().__init__(config)
        self._coref_resolver: Optional[CoreferenceResolver] = None
        self._explicit_detector: Optional[ExplicitReferenceDetector] = None

    def initialize(self) -> None:
        """Initialize reference detection models."""
        self._coref_resolver = CoreferenceResolver(self.config.reference)
        self._coref_resolver.initialize()

        self._explicit_detector = ExplicitReferenceDetector(self.config.reference.explicit_patterns)

        self._initialized = True
        logger.info("Reference linker initialized")

    @property
    def coref_resolver(self) -> CoreferenceResolver:
        self.ensure_initialized()
        return self._coref_resolver  # type: ignore

    @property
    def explicit_detector(self) -> ExplicitReferenceDetector:
        self.ensure_initialized()
        return self._explicit_detector  # type: ignore

    def validate_input(self, input_data: ReferenceInput) -> bool:
        if input_data is None:
            return False
        if input_data.document is None:
            return False
        return True

    def process(self, input_data: ReferenceInput) -> StageResult[ReferenceResult]:
        """Link references between chunks.

        Args:
            input_data: ReferenceInput with document and chunk boundaries

        Returns:
            StageResult containing ReferenceResult
        """
        try:
            document = input_data.document
            boundaries = input_data.chunk_boundaries or [0]

            # Ensure boundaries are sorted and include 0
            boundaries = sorted(set([0] + boundaries))

            # Build sentence to chunk mapping
            sentence_to_chunk = self._build_sentence_chunk_map(len(document.sentences), boundaries)

            references = []

            # Step 1: Find explicit references
            sentence_offsets = [(s.char_start, s.char_end) for s in document.sentences]

            explicit_refs = self.explicit_detector.find_references(document.text, sentence_offsets)
            logger.debug(f"Found {len(explicit_refs)} explicit references")

            for sent_idx, ref_text in explicit_refs:
                from_chunk = sentence_to_chunk.get(sent_idx)
                # Try to resolve reference to a chunk
                to_chunk = self._resolve_explicit_reference(
                    ref_text, document, boundaries, sentence_to_chunk
                )

                if from_chunk is not None:
                    references.append(
                        ChunkReference(
                            from_chunk_idx=from_chunk,
                            to_chunk_idx=to_chunk if to_chunk is not None else -1,
                            reference_type="explicit",
                            reference_text=ref_text,
                        )
                    )

            # Step 2: Find coreference chains spanning chunks
            if self.config.reference.use_coreference:
                chains = self.coref_resolver.resolve(document.text, sentence_offsets)

                # Find chains that span multiple chunks
                for chain in chains:
                    chunk_indices = set()
                    for mention in chain.mentions:
                        chunk_idx = sentence_to_chunk.get(mention.sentence_idx)
                        if chunk_idx is not None:
                            chunk_indices.add(chunk_idx)

                    # Create references between chunks in chain
                    if len(chunk_indices) > 1:
                        chunk_list = sorted(chunk_indices)
                        for i in range(len(chunk_list) - 1):
                            references.append(
                                ChunkReference(
                                    from_chunk_idx=chunk_list[i + 1],
                                    to_chunk_idx=chunk_list[i],
                                    reference_type="coreference",
                                    confidence=0.8,
                                )
                            )

                chains_count = len(chains)
            else:
                chains_count = 0

            # Build reference graph
            num_chunks = len(boundaries)
            graph = ReferenceGraph(
                references=references,
                chunk_count=num_chunks,
            )

            result = ReferenceResult(
                graph=graph,
                chains_found=chains_count,
                explicit_refs_found=len(explicit_refs),
            )

            return StageResult(
                data=result,
                confidence=0.8 if not references else 0.9,
                latency_ms=0.0,
                metadata={
                    "num_references": len(references),
                    "chains_found": chains_count,
                    "explicit_refs": len(explicit_refs),
                },
            )

        except Exception as e:
            logger.error(f"Reference linking failed: {e}")
            raise ReferenceResolutionError(
                f"Failed to link references: {e}",
                details={"document_id": input_data.document.id},
            )

    def _build_sentence_chunk_map(
        self,
        num_sentences: int,
        boundaries: list[int],
    ) -> dict[int, int]:
        """Map sentence indices to chunk indices."""
        mapping = {}
        chunk_idx = 0

        for sent_idx in range(num_sentences):
            # Move to next chunk if we've passed its boundary
            while chunk_idx < len(boundaries) - 1 and sent_idx >= boundaries[chunk_idx + 1]:
                chunk_idx += 1
            mapping[sent_idx] = chunk_idx

        return mapping

    def _resolve_explicit_reference(
        self,
        ref_text: str,
        document: Document,
        boundaries: list[int],
        sentence_to_chunk: dict[int, int],
    ) -> Optional[int]:
        """Try to resolve an explicit reference to a chunk index.

        This is a simplified implementation that looks for matching
        section numbers in headings.
        """
        # Extract reference target (e.g., "3" from "Section 3")
        import re

        match = re.search(r"(\d+(?:\.\d+)*|[A-Z])", ref_text)
        if not match:
            return None

        target = match.group(1)

        # Search for heading containing this target
        for i, sentence in enumerate(document.sentences):
            if target in sentence.text and self._looks_like_heading(sentence.text):
                return sentence_to_chunk.get(i)

        return None

    def _looks_like_heading(self, text: str) -> bool:
        """Check if text looks like a heading."""
        import re

        patterns = [
            r"^#{1,6}\s",  # Markdown heading
            r"^\d+\.\s",  # Numbered heading
            r"^[A-Z]\.\s",  # Letter heading
        ]

        for pattern in patterns:
            if re.match(pattern, text):
                return True

        # Short sentence starting with capital
        return len(text) < 100 and text[0].isupper() if text else False

    def enrich_chunks(
        self,
        chunks: list[COSMICChunk],
        graph: ReferenceGraph,
    ) -> list[COSMICChunk]:
        """Add reference metadata to chunks.

        Since COSMICChunk is frozen, this creates new instances with
        updated reference fields.
        """
        enriched = []

        for i, chunk in enumerate(chunks):
            refs_to = tuple(str(j) for j in graph.get_references_from(i) if j >= 0)
            refs_from = tuple(str(j) for j in graph.get_references_to(i))
            has_unresolved = graph.has_unresolved_references(i)

            # Create new chunk with updated references
            enriched.append(
                COSMICChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
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
                    references_chunks=refs_to,
                    referenced_by_chunks=refs_from,
                    has_unresolved_references=has_unresolved,
                    primary_intent=chunk.primary_intent,
                    intent_confidence=chunk.intent_confidence,
                    contains_heading=chunk.contains_heading,
                    contains_list=chunk.contains_list,
                    contains_table=chunk.contains_table,
                    section_type=chunk.section_type,
                    processing_timestamp=chunk.processing_timestamp,
                    cosmic_version=chunk.cosmic_version,
                    dcs_weights_hash=chunk.dcs_weights_hash,
                    embedding_model=chunk.embedding_model,
                )
            )

        return enriched
