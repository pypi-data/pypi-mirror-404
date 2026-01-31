"""Document representation for COSMIC processing."""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Iterator, Optional


@dataclass
class Sentence:
    """A sentence within a document."""

    text: str
    index: int  # Position in document's sentence list
    char_start: int  # Character offset from document start
    char_end: int  # Character offset end
    page: int = 1  # Page number (1-indexed)

    def __len__(self) -> int:
        return len(self.text)

    def __repr__(self) -> str:
        preview = self.text[:40] + "..." if len(self.text) > 40 else self.text
        return f"Sentence(idx={self.index}, page={self.page}, text={preview!r})"


@dataclass
class Document:
    """Document representation for COSMIC processing.

    A document is a sequence of sentences with optional page information.
    This class handles text normalization and sentence segmentation.
    """

    id: str
    text: str
    sentences: list[Sentence] = field(default_factory=list)
    page_boundaries: list[int] = field(default_factory=list)  # Char offsets where pages start
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Segment into sentences if not already done."""
        if not self.sentences:
            self.sentences = self._segment_sentences()

    def _segment_sentences(self) -> list[Sentence]:
        """Segment document text into sentences.

        Uses a simple rule-based approach. For production, consider
        using spaCy's sentence segmentation.
        """
        # Simple sentence boundary detection
        # Handles: . ! ? followed by space and capital letter
        # Preserves: abbreviations like "Dr.", "Mr.", numbers like "3.14"
        sentence_pattern = re.compile(
            r"(?<=[.!?])\s+(?=[A-Z])|"  # Standard sentence boundary
            r"(?<=\n)\s*(?=\S)",  # Newline as boundary
            re.MULTILINE,
        )

        sentences: list[Sentence] = []
        parts = sentence_pattern.split(self.text)

        char_offset = 0
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue

            # Find actual position in original text
            start = self.text.find(part, char_offset)
            if start == -1:
                start = char_offset
            end = start + len(part)

            # Determine page number
            page = self._get_page_for_offset(start)

            sentences.append(
                Sentence(
                    text=part,
                    index=len(sentences),
                    char_start=start,
                    char_end=end,
                    page=page,
                )
            )

            char_offset = end

        return sentences

    def _get_page_for_offset(self, char_offset: int) -> int:
        """Get page number for a character offset."""
        if not self.page_boundaries:
            return 1

        page = 1
        for boundary in self.page_boundaries:
            if char_offset >= boundary:
                page += 1
            else:
                break
        return page

    @classmethod
    def from_text(
        cls,
        text: str,
        doc_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> "Document":
        """Create document from plain text."""
        if doc_id is None:
            # Generate ID from content hash
            doc_id = hashlib.md5(text.encode()).hexdigest()[:12]

        return cls(
            id=doc_id,
            text=text,
            metadata=metadata or {},
        )

    @classmethod
    def from_pages(
        cls,
        pages: list[str],
        doc_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> "Document":
        """Create document from list of page texts."""
        # Combine pages with page boundary tracking
        combined_text = ""
        page_boundaries = []

        for page_text in pages:
            if combined_text:
                page_boundaries.append(len(combined_text))
                combined_text += "\n\n"  # Page separator
            combined_text += page_text

        if doc_id is None:
            doc_id = hashlib.md5(combined_text.encode()).hexdigest()[:12]

        return cls(
            id=doc_id,
            text=combined_text,
            page_boundaries=page_boundaries,
            metadata=metadata or {},
        )

    def get_text_span(self, start: int, end: int) -> str:
        """Get text between character offsets."""
        return self.text[start:end]

    def get_sentences_in_range(self, char_start: int, char_end: int) -> list[Sentence]:
        """Get sentences that overlap with a character range."""
        return [s for s in self.sentences if s.char_end > char_start and s.char_start < char_end]

    def get_context_around(
        self, position: int, window_sentences: int = 3
    ) -> tuple[list[Sentence], list[Sentence]]:
        """Get sentences before and after a position.

        Args:
            position: Sentence index
            window_sentences: Number of sentences to include on each side

        Returns:
            Tuple of (before_sentences, after_sentences)
        """
        before_start = max(0, position - window_sentences)
        after_end = min(len(self.sentences), position + window_sentences)

        return (
            self.sentences[before_start:position],
            self.sentences[position:after_end],
        )

    def iter_sentence_pairs(self) -> Iterator[tuple[Sentence, Sentence]]:
        """Iterate over consecutive sentence pairs."""
        for i in range(len(self.sentences) - 1):
            yield self.sentences[i], self.sentences[i + 1]

    @property
    def num_sentences(self) -> int:
        """Number of sentences in document."""
        return len(self.sentences)

    @property
    def num_pages(self) -> int:
        """Number of pages in document."""
        return len(self.page_boundaries) + 1

    @property
    def total_chars(self) -> int:
        """Total character count."""
        return len(self.text)

    def __len__(self) -> int:
        """Return number of sentences."""
        return len(self.sentences)

    def __iter__(self) -> Iterator[Sentence]:
        """Iterate over sentences."""
        return iter(self.sentences)

    def __getitem__(self, index: int) -> Sentence:
        """Get sentence by index."""
        return self.sentences[index]

    def __repr__(self) -> str:
        return (
            f"Document(id={self.id!r}, "
            f"sentences={len(self.sentences)}, "
            f"pages={self.num_pages}, "
            f"chars={len(self.text)})"
        )
