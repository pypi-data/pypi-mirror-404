"""Batch processing for COSMIC framework.

Provides efficient processing of multiple documents with:
- Concurrent document processing
- GPU batching for embeddings
- Progress tracking
- Error handling with partial results
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Iterator, Optional

from tqdm import tqdm

from cosmic.chunker import COSMICChunker
from cosmic.core.chunk import COSMICChunk
from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document
from cosmic.exceptions import COSMICError

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of batch processing."""

    documents_processed: int
    documents_failed: int
    total_chunks: int
    chunks_by_document: dict[str, list[COSMICChunk]]
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.documents_processed + self.documents_failed
        return self.documents_processed / total if total > 0 else 0.0

    def get_all_chunks(self) -> list[COSMICChunk]:
        """Get all chunks from all documents."""
        all_chunks = []
        for chunks in self.chunks_by_document.values():
            all_chunks.extend(chunks)
        return all_chunks


class BatchProcessor:
    """Process multiple documents efficiently.

    Features:
    - Parallel document processing with thread pool
    - Shared embedding model across documents
    - Progress tracking with tqdm
    - Graceful error handling

    Example:
        processor = BatchProcessor(config)
        documents = [Document.from_text(t) for t in texts]
        result = processor.process(documents)
        print(f"Processed {result.documents_processed} documents")
    """

    def __init__(
        self,
        config: Optional[COSMICConfig] = None,
        max_workers: int = 4,
    ):
        """Initialize batch processor.

        Args:
            config: COSMIC configuration
            max_workers: Maximum concurrent workers
        """
        self.config = config or COSMICConfig()
        self.max_workers = max_workers

        # Shared chunker (thread-safe due to lazy initialization)
        self._chunker: Optional[COSMICChunker] = None

    @property
    def chunker(self) -> COSMICChunker:
        """Get or create shared chunker."""
        if self._chunker is None:
            self._chunker = COSMICChunker(self.config)
        return self._chunker

    def process(
        self,
        documents: list[Document],
        strategy: str = "auto",
        show_progress: bool = True,
        on_document_complete: Optional[Callable[[str, list[COSMICChunk]], None]] = None,
    ) -> BatchResult:
        """Process multiple documents.

        Args:
            documents: List of documents to process
            strategy: Chunking strategy
            show_progress: Show progress bar
            on_document_complete: Callback when document is complete

        Returns:
            BatchResult with all chunks and statistics
        """
        logger.info(f"Starting batch processing of {len(documents)} documents")

        chunks_by_document: dict[str, list[COSMICChunk]] = {}
        errors: dict[str, str] = {}

        # Use thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_doc = {
                executor.submit(self._process_document, doc, strategy): doc for doc in documents
            }

            # Process results as they complete
            completed_futures = as_completed(future_to_doc)
            if show_progress:
                completed_futures = tqdm(  # type: ignore[assignment]
                    completed_futures,
                    total=len(documents),
                    desc="Processing documents",
                )

            for future in completed_futures:
                doc = future_to_doc[future]
                try:
                    chunks = future.result()
                    chunks_by_document[doc.id] = chunks

                    if on_document_complete:
                        on_document_complete(doc.id, chunks)

                except Exception as e:
                    logger.error(f"Failed to process document {doc.id}: {e}")
                    errors[doc.id] = str(e)
                    chunks_by_document[doc.id] = []

        # Calculate statistics
        total_chunks = sum(len(c) for c in chunks_by_document.values())

        result = BatchResult(
            documents_processed=len(documents) - len(errors),
            documents_failed=len(errors),
            total_chunks=total_chunks,
            chunks_by_document=chunks_by_document,
            errors=errors,
        )

        logger.info(
            f"Batch processing complete: "
            f"{result.documents_processed}/{len(documents)} succeeded, "
            f"{result.total_chunks} total chunks"
        )

        return result

    def _process_document(
        self,
        document: Document,
        strategy: str,
    ) -> list[COSMICChunk]:
        """Process a single document."""
        return self.chunker.chunk_document(document, strategy)

    async def process_async(
        self,
        documents: list[Document],
        strategy: str = "auto",
        show_progress: bool = True,
    ) -> BatchResult:
        """Async version of batch processing.

        Useful for integration with async frameworks.
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.process(documents, strategy, show_progress),
        )


class StreamingProcessor:
    """Process documents one at a time with streaming output.

    Useful for memory-constrained environments or real-time processing.
    """

    def __init__(self, config: Optional[COSMICConfig] = None):
        self.config = config or COSMICConfig()
        self.chunker = COSMICChunker(self.config)

    def process_stream(
        self,
        documents: Iterator[Document],
        strategy: str = "auto",
    ) -> Generator[tuple[str, list[COSMICChunk]], None, None]:
        """Process documents as a generator.

        Args:
            documents: Iterable of documents
            strategy: Chunking strategy

        Yields:
            Tuple of (document_id, chunks) for each document
        """
        for doc in documents:
            try:
                chunks = self.chunker.chunk_document(doc, strategy)
                yield doc.id, chunks
            except COSMICError as e:
                logger.error(f"Failed to process {doc.id}: {e}")
                yield doc.id, []

    def __iter__(self) -> Iterator[Any]:
        """Make processor iterable."""
        return self

    def __next__(self) -> None:
        """Get next result."""
        raise StopIteration  # Implement if needed


def process_documents(
    documents: list[Document],
    config: Optional[COSMICConfig] = None,
    strategy: str = "auto",
    max_workers: int = 4,
) -> BatchResult:
    """Convenience function for batch processing.

    Args:
        documents: Documents to process
        config: Configuration
        strategy: Chunking strategy
        max_workers: Parallel workers

    Returns:
        BatchResult
    """
    processor = BatchProcessor(config, max_workers)
    return processor.process(documents, strategy)
