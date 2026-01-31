"""Fixed-length chunking fallback strategy."""

import hashlib
import logging
from datetime import datetime

from cosmic import __version__
from cosmic.core.chunk import COSMICChunk
from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document, Sentence
from cosmic.core.enums import ProcessingMode
from cosmic.utils.tokenizer import count_tokens

logger = logging.getLogger(__name__)


class FixedLengthChunker:
    """Ultimate fallback: fixed-length token chunking.

    Splits document into chunks of approximately target_tokens size,
    respecting sentence boundaries where possible.
    """

    def __init__(self, config: COSMICConfig):
        self.config = config
        self.min_tokens = config.chunks.min_tokens
        self.max_tokens = config.chunks.max_tokens
        self.target_tokens = config.chunks.target_tokens

    def chunk(self, document: Document) -> list[COSMICChunk]:
        """Chunk document using fixed-length strategy.

        Args:
            document: Document to chunk

        Returns:
            List of COSMICChunk with minimal metadata
        """
        logger.info(f"Fixed-length chunking document {document.id}")

        chunks: list[COSMICChunk] = []
        current_sentences: list[Sentence] = []
        current_tokens = 0
        chunk_start_idx = 0

        for sentence in document.sentences:
            sentence_tokens = count_tokens(sentence.text)

            # Check if adding this sentence exceeds max
            if current_tokens + sentence_tokens > self.max_tokens and current_sentences:
                # Create chunk from current sentences
                chunk = self._create_chunk(
                    document=document,
                    sentences=current_sentences,
                    chunk_index=len(chunks),
                    start_sentence_idx=chunk_start_idx,
                )
                chunks.append(chunk)

                # Start new chunk
                current_sentences = [sentence]
                current_tokens = sentence_tokens
                chunk_start_idx = sentence.index
            else:
                current_sentences.append(sentence)
                current_tokens += sentence_tokens

        # Handle remaining sentences
        if current_sentences:
            chunk = self._create_chunk(
                document=document,
                sentences=current_sentences,
                chunk_index=len(chunks),
                start_sentence_idx=chunk_start_idx,
            )
            chunks.append(chunk)

        logger.info(f"Created {len(chunks)} fixed-length chunks")
        return chunks

    def _create_chunk(
        self,
        document: Document,
        sentences: list,
        chunk_index: int,
        start_sentence_idx: int,
    ) -> COSMICChunk:
        """Create a COSMICChunk from sentences."""
        text = " ".join(s.text for s in sentences)
        token_count = count_tokens(text)

        # Determine page range
        page_start = sentences[0].page if sentences else 1
        page_end = sentences[-1].page if sentences else 1

        # Generate chunk ID
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
            coherence_score=0.5,  # Neutral - no coherence analysis
            processing_mode=ProcessingMode.FIXED_LENGTH,
            processing_confidence=0.3,  # Low confidence for fallback
            processing_timestamp=datetime.utcnow(),
            cosmic_version=__version__,
        )
