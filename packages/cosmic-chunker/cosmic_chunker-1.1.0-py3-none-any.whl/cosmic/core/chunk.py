"""COSMICChunk: The core data structure for chunked text with rich metadata."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from cosmic import __version__
from cosmic.core.enums import Intent, ProcessingMode, SectionType


@dataclass(frozen=True, slots=True)
class COSMICChunk:
    """Immutable chunk with full COSMIC metadata.

    This is the primary output of the COSMIC pipeline. Each chunk represents
    a self-contained conceptual unit with rich metadata for downstream tasks.

    Attributes:
        chunk_id: Unique identifier for this chunk
        document_id: Identifier of the source document
        chunk_index: Position of this chunk in the document (0-indexed)
        text: The actual text content of the chunk
        token_count: Number of tokens (using tiktoken cl100k_base)

        page_start: First page containing this chunk (1-indexed)
        page_end: Last page containing this chunk (1-indexed)
        char_start: Character offset from document start
        char_end: Character offset end position

        domain: Primary domain classification
        subdomain: Optional subdomain classification
        domain_confidence: Confidence score for domain classification (0-1)

        coherence_score: Internal coherence of the chunk (0-1)
        processing_mode: Which pipeline path produced this chunk
        processing_confidence: Overall confidence in chunk quality (0-1)

        references_chunks: IDs of chunks this chunk references
        referenced_by_chunks: IDs of chunks that reference this chunk
        has_unresolved_references: Whether chunk has references we couldn't resolve

        primary_intent: What this chunk is trying to do (define, explain, etc.)
        intent_confidence: Confidence in intent classification (0-1)

        contains_heading: Whether chunk contains a heading
        contains_list: Whether chunk contains bullet/numbered list
        contains_table: Whether chunk contains a table
        section_type: Type of section (intro, methods, etc.)

        processing_timestamp: When this chunk was created
        cosmic_version: Version of COSMIC that created this chunk
        dcs_weights_hash: Hash of DCS weights for reproducibility
        embedding_model: Name of embedding model used
    """

    # Identity
    chunk_id: str
    document_id: str
    chunk_index: int

    # Content
    text: str
    token_count: int

    # Location
    page_start: int
    page_end: int
    char_start: int
    char_end: int

    # Domain Classification
    domain: str = "unknown"
    subdomain: Optional[str] = None
    domain_confidence: float = 0.0

    # Quality Metrics
    coherence_score: float = 0.5
    processing_mode: ProcessingMode = ProcessingMode.FIXED_LENGTH
    processing_confidence: float = 0.5

    # Cross-References (using tuples for immutability)
    references_chunks: tuple[str, ...] = field(default_factory=tuple)
    referenced_by_chunks: tuple[str, ...] = field(default_factory=tuple)
    has_unresolved_references: bool = False

    # Intent Analysis
    primary_intent: Intent = Intent.UNKNOWN
    intent_confidence: float = 0.0

    # Structural Metadata
    contains_heading: bool = False
    contains_list: bool = False
    contains_table: bool = False
    section_type: Optional[SectionType] = None

    # Provenance
    processing_timestamp: datetime = field(default_factory=datetime.utcnow)
    cosmic_version: str = __version__
    dcs_weights_hash: str = ""
    embedding_model: str = ""

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON output."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "token_count": self.token_count,
            "location": {
                "page_start": self.page_start,
                "page_end": self.page_end,
                "char_start": self.char_start,
                "char_end": self.char_end,
            },
            "domain": {
                "primary": self.domain,
                "subdomain": self.subdomain,
                "confidence": self.domain_confidence,
            },
            "quality": {
                "coherence_score": self.coherence_score,
                "processing_mode": self.processing_mode.value,
                "processing_confidence": self.processing_confidence,
            },
            "references": {
                "references": list(self.references_chunks),
                "referenced_by": list(self.referenced_by_chunks),
                "has_unresolved": self.has_unresolved_references,
            },
            "intent": {
                "primary": self.primary_intent.value,
                "confidence": self.intent_confidence,
            },
            "structure": {
                "contains_heading": self.contains_heading,
                "contains_list": self.contains_list,
                "contains_table": self.contains_table,
                "section_type": self.section_type.value if self.section_type else None,
            },
            "provenance": {
                "timestamp": self.processing_timestamp.isoformat(),
                "cosmic_version": self.cosmic_version,
                "dcs_weights_hash": self.dcs_weights_hash,
                "embedding_model": self.embedding_model,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "COSMICChunk":
        """Deserialize from dictionary."""
        return cls(
            chunk_id=data["chunk_id"],
            document_id=data["document_id"],
            chunk_index=data["chunk_index"],
            text=data["text"],
            token_count=data["token_count"],
            page_start=data["location"]["page_start"],
            page_end=data["location"]["page_end"],
            char_start=data["location"]["char_start"],
            char_end=data["location"]["char_end"],
            domain=data["domain"]["primary"],
            subdomain=data["domain"]["subdomain"],
            domain_confidence=data["domain"]["confidence"],
            coherence_score=data["quality"]["coherence_score"],
            processing_mode=ProcessingMode(data["quality"]["processing_mode"]),
            processing_confidence=data["quality"]["processing_confidence"],
            references_chunks=tuple(data["references"]["references"]),
            referenced_by_chunks=tuple(data["references"]["referenced_by"]),
            has_unresolved_references=data["references"]["has_unresolved"],
            primary_intent=Intent(data["intent"]["primary"]),
            intent_confidence=data["intent"]["confidence"],
            contains_heading=data["structure"]["contains_heading"],
            contains_list=data["structure"]["contains_list"],
            contains_table=data["structure"]["contains_table"],
            section_type=(
                SectionType(data["structure"]["section_type"])
                if data["structure"]["section_type"]
                else None
            ),
            processing_timestamp=datetime.fromisoformat(data["provenance"]["timestamp"]),
            cosmic_version=data["provenance"]["cosmic_version"],
            dcs_weights_hash=data["provenance"]["dcs_weights_hash"],
            embedding_model=data["provenance"]["embedding_model"],
        )

    def __len__(self) -> int:
        """Return token count for len() compatibility."""
        return self.token_count

    def __repr__(self) -> str:
        """Concise representation for debugging."""
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return (
            f"COSMICChunk(id={self.chunk_id!r}, "
            f"tokens={self.token_count}, "
            f"domain={self.domain!r}, "
            f"coherence={self.coherence_score:.2f}, "
            f"text={text_preview!r})"
        )
