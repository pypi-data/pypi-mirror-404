"""Stage 3: Domain Classification using MST clustering."""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document
from cosmic.exceptions import DomainClassificationError
from cosmic.models.domain_classifier import DomainAssignment, DomainClassifier
from cosmic.models.embeddings import EmbeddingModel
from cosmic.pipeline.base import PipelineStage, StageResult
from cosmic.scoring.clustering import Cluster, MSTClustering

logger = logging.getLogger(__name__)


@dataclass
class TextSpan:
    """A text span for domain classification."""

    text: str
    start_sentence: int
    end_sentence: int
    char_start: int
    char_end: int


@dataclass
class DomainInput:
    """Input for domain classification stage."""

    document: Document
    boundaries: list[int]  # Sentence indices where chunks start
    embeddings: Optional[np.ndarray] = None  # Pre-computed sentence embeddings


@dataclass
class DomainResult:
    """Result of domain classification."""

    assignments: list[DomainAssignment]  # One per chunk
    clusters: list[Cluster]  # Domain clusters
    chunk_to_cluster: dict[int, int]  # Map chunk index to cluster ID

    def get_assignment(self, chunk_index: int) -> DomainAssignment:
        """Get domain assignment for a chunk."""
        if 0 <= chunk_index < len(self.assignments):
            return self.assignments[chunk_index]
        return DomainAssignment(domain="unknown", subdomain=None, confidence=0.0)


class DomainClassificationStage(PipelineStage[DomainInput, DomainResult]):
    """Stage 3: Classify chunks into domains.

    This stage:
    1. Splits document into chunks based on boundaries
    2. Computes chunk embeddings
    3. Clusters chunks using MST
    4. Labels clusters with domain taxonomy
    """

    stage_name = "domain_classification"

    def __init__(self, config: COSMICConfig):
        super().__init__(config)
        self._embedding_model: Optional[EmbeddingModel] = None
        self._domain_classifier: Optional[DomainClassifier] = None
        self._clustering: Optional[MSTClustering] = None

    def initialize(self) -> None:
        """Initialize embedding model and classifier."""
        self._embedding_model = EmbeddingModel(self.config.embedding)
        self._domain_classifier = DomainClassifier(self.config, self._embedding_model)
        self._domain_classifier.initialize()
        self._clustering = MSTClustering(min_cluster_size=1)

        self._initialized = True
        logger.info("Domain classification stage initialized")

    @property
    def embedding_model(self) -> EmbeddingModel:
        self.ensure_initialized()
        return self._embedding_model  # type: ignore

    @property
    def domain_classifier(self) -> DomainClassifier:
        self.ensure_initialized()
        return self._domain_classifier  # type: ignore

    @property
    def clustering(self) -> MSTClustering:
        self.ensure_initialized()
        return self._clustering  # type: ignore

    def validate_input(self, input_data: DomainInput) -> bool:
        if input_data is None:
            return False
        if input_data.document is None:
            return False
        return True

    def process(self, input_data: DomainInput) -> StageResult[DomainResult]:
        """Classify chunks into domains.

        Args:
            input_data: DomainInput with document and boundary positions

        Returns:
            StageResult containing DomainResult
        """
        try:
            document = input_data.document
            boundaries = input_data.boundaries or [0]

            # Step 1: Create text spans from boundaries
            spans = self._create_spans(document, boundaries)
            logger.debug(f"Created {len(spans)} text spans for classification")

            if not spans:
                return self._empty_result()

            # Step 2: Get chunk embeddings
            chunk_texts = [span.text for span in spans]
            chunk_embeddings = self.embedding_model.encode(chunk_texts)

            # Step 3: Cluster chunks
            clusters, labels = self.clustering.cluster_with_labels(chunk_embeddings)
            logger.debug(f"Clustered into {len(clusters)} domain groups")

            # Step 4: Classify each cluster
            cluster_assignments = {}
            for cluster in clusters:
                # Use centroid text or first member for classification
                member_texts = [chunk_texts[i] for i in cluster.member_indices]
                combined_text = " ".join(member_texts[:3])  # Sample up to 3 members

                assignment = self.domain_classifier.classify(combined_text)
                cluster_assignments[cluster.cluster_id] = assignment

            # Step 5: Map assignments back to chunks
            assignments = []
            chunk_to_cluster = {}

            for i, label in enumerate(labels):
                cluster_id = int(label)
                chunk_to_cluster[i] = cluster_id

                if cluster_id in cluster_assignments:
                    assignments.append(cluster_assignments[cluster_id])
                else:
                    assignments.append(
                        DomainAssignment(domain="unknown", subdomain=None, confidence=0.0)
                    )

            result = DomainResult(
                assignments=assignments,
                clusters=clusters,
                chunk_to_cluster=chunk_to_cluster,
            )

            # Calculate confidence
            avg_confidence = (
                sum(a.confidence for a in assignments) / len(assignments) if assignments else 0.0
            )

            return StageResult(
                data=result,
                confidence=avg_confidence,
                latency_ms=0.0,
                metadata={
                    "num_chunks": len(spans),
                    "num_clusters": len(clusters),
                    "domains_found": list(set(a.domain for a in assignments)),
                },
            )

        except Exception as e:
            logger.error(f"Domain classification failed: {e}")
            raise DomainClassificationError(
                f"Failed to classify domains: {e}",
                details={"document_id": input_data.document.id},
            )

    def _create_spans(
        self,
        document: Document,
        boundaries: list[int],
    ) -> list[TextSpan]:
        """Create text spans from boundary positions."""
        spans = []

        # Ensure boundaries are sorted and include start
        boundaries = sorted(set([0] + boundaries))

        # Add end boundary if not present
        if boundaries[-1] != len(document.sentences):
            boundaries.append(len(document.sentences))

        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]

            if start_idx >= len(document.sentences):
                continue

            # Get sentences in span
            span_sentences = document.sentences[start_idx:end_idx]
            if not span_sentences:
                continue

            # Combine text
            text = " ".join(s.text for s in span_sentences)

            spans.append(
                TextSpan(
                    text=text,
                    start_sentence=start_idx,
                    end_sentence=end_idx,
                    char_start=span_sentences[0].char_start,
                    char_end=span_sentences[-1].char_end,
                )
            )

        return spans

    def _empty_result(self) -> StageResult[DomainResult]:
        """Return empty result for edge cases."""
        return StageResult(
            data=DomainResult(assignments=[], clusters=[], chunk_to_cluster={}),
            confidence=0.0,
            latency_ms=0.0,
            metadata={"num_chunks": 0},
        )

    def classify_single(self, text: str) -> DomainAssignment:
        """Classify a single text span."""
        self.ensure_initialized()
        return self.domain_classifier.classify(text)
