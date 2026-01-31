"""Discourse Coherence Score (DCS) for boundary detection.

DCS is the core scoring mechanism in COSMIC that combines:
- Topical coherence (embedding similarity)
- Coreference density (pronoun resolution)
- Discourse marker signals (linguistic cues)

Lower DCS indicates higher likelihood of a conceptual boundary.
"""

import hashlib
import re
from dataclasses import dataclass

import numpy as np

from cosmic.core.config import DCSConfig


@dataclass
class DCSWeights:
    """Calibrated DCS weights with hash for reproducibility.

    Attributes:
        alpha: Weight for topical coherence
        beta: Weight for coreference density
        gamma: Weight for discourse marker signals
        threshold: Score below which indicates boundary
    """

    alpha: float
    beta: float
    gamma: float
    threshold: float

    @classmethod
    def from_config(cls, config: DCSConfig) -> "DCSWeights":
        """Create weights from config."""
        return cls(
            alpha=config.alpha,
            beta=config.beta,
            gamma=config.gamma,
            threshold=config.threshold,
        )

    def get_hash(self) -> str:
        """Generate deterministic hash for versioning."""
        content = f"{self.alpha:.6f}:{self.beta:.6f}:{self.gamma:.6f}:{self.threshold:.6f}"
        return hashlib.sha256(content.encode()).hexdigest()[:8]

    def validate(self) -> None:
        """Validate weights sum to approximately 1.0."""
        total = self.alpha + self.beta + self.gamma
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"DCS weights must sum to 1.0, got {total}")


class DiscourseCoherenceScorer:
    """Compute Discourse Coherence Score for boundary detection.

    DCS = alpha * topical_coherence + beta * coreference_density + gamma * discourse_signal

    Higher DCS indicates more coherent text (less likely to be a boundary).
    Lower DCS indicates potential boundary between concepts.

    Example:
        scorer = DiscourseCoherenceScorer(DCSWeights.from_config(config.dcs))
        boundaries = scorer.detect_boundaries(sentences, embeddings)
    """

    # Discourse markers that indicate boundaries
    BOUNDARY_MARKERS_STRONG = [
        r"^(however|but|although|despite|nevertheless|nonetheless)\b",
        r"^(in contrast|on the other hand|conversely)\b",
        r"^(therefore|thus|hence|consequently|as a result)\b",
        r"^(in conclusion|to summarize|in summary|finally)\b",
        r"^(first(ly)?|second(ly)?|third(ly)?|finally|lastly)\b",
        r"^(moving on|turning to|regarding|concerning)\b",
    ]

    BOUNDARY_MARKERS_WEAK = [
        r"^(also|additionally|furthermore|moreover)\b",
        r"^(for example|for instance|specifically)\b",
        r"^(in fact|indeed|actually)\b",
        r"^(note that|importantly|significantly)\b",
    ]

    # Markers that indicate continuation (reduce boundary likelihood)
    CONTINUATION_MARKERS = [
        r"^(this|these|that|those|it|they)\b",
        r"^(the\s+\w+\s+(is|are|was|were))\b",
        r"^(such|said|same)\b",
    ]

    # Unresolved reference patterns (suggest boundary issues)
    UNRESOLVED_REFS = [
        r"\b(it|they|this|these|that|those)\b",
        r"\b(he|she|them|their|its)\b",
        r"\b(the former|the latter)\b",
    ]

    def __init__(self, weights: DCSWeights):
        self.weights = weights
        weights.validate()
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for efficiency."""
        self._strong_boundary = [re.compile(p, re.IGNORECASE) for p in self.BOUNDARY_MARKERS_STRONG]
        self._weak_boundary = [re.compile(p, re.IGNORECASE) for p in self.BOUNDARY_MARKERS_WEAK]
        self._continuation = [re.compile(p, re.IGNORECASE) for p in self.CONTINUATION_MARKERS]
        self._unresolved = re.compile("|".join(self.UNRESOLVED_REFS), re.IGNORECASE)

    def compute_topical_coherence(
        self,
        embeddings: np.ndarray,
    ) -> float:
        """Compute topical coherence as inverse of embedding variance.

        Higher coherence = lower variance in embedding space.

        Args:
            embeddings: Array of shape (n, dim) for sentences in window

        Returns:
            Coherence score between 0 and 1
        """
        if len(embeddings) < 2:
            return 1.0

        # Compute mean embedding
        mean_emb = embeddings.mean(axis=0)

        # Compute average cosine distance from mean
        # For normalized embeddings, this is 1 - dot product
        similarities = np.dot(embeddings, mean_emb)
        avg_similarity = similarities.mean()

        # Convert to coherence (higher similarity = higher coherence)
        coherence = float(max(0.0, min(1.0, avg_similarity)))
        return coherence

    def compute_coreference_density(
        self,
        sentences: list[str],
    ) -> float:
        """Compute coreference density using heuristics.

        Higher density indicates more references are likely resolved
        within the span, suggesting coherence.

        This is a heuristic approximation. For full coreference,
        use the ReferenceLinker stage.

        Args:
            sentences: List of sentences in the window

        Returns:
            Density score between 0 and 1
        """
        if not sentences:
            return 1.0

        total_refs = 0
        first_sentence_refs = 0

        for i, sent in enumerate(sentences):
            refs = len(self._unresolved.findall(sent))
            total_refs += refs
            if i == 0:
                first_sentence_refs = refs

        if total_refs == 0:
            return 1.0  # No references = fully coherent

        # References in first sentence without prior context are likely unresolved
        # More refs in later sentences (with antecedents) = more coherent
        resolved_ratio = 1.0 - (first_sentence_refs / total_refs)
        return max(0.0, min(1.0, resolved_ratio))

    def compute_discourse_signal(self, sentence: str) -> float:
        """Compute discourse marker signal for boundary detection.

        Returns a score where:
        - High score (0.8-1.0): Strong boundary marker present
        - Medium score (0.5-0.7): Weak boundary marker present
        - Low score (0.1-0.3): Continuation marker present
        - Neutral (0.5): No markers detected

        Args:
            sentence: The sentence to analyze (typically first in window)

        Returns:
            Boundary signal score between 0 and 1
        """
        sentence = sentence.strip()

        # Check for strong boundary markers
        for pattern in self._strong_boundary:
            if pattern.search(sentence):
                return 0.9

        # Check for weak boundary markers
        for pattern in self._weak_boundary:
            if pattern.search(sentence):
                return 0.65

        # Check for continuation markers (reduce boundary likelihood)
        for pattern in self._continuation:
            if pattern.search(sentence):
                return 0.2

        return 0.5  # Neutral

    def compute_dcs(
        self,
        sentences: list[str],
        embeddings: np.ndarray,
    ) -> float:
        """Compute full Discourse Coherence Score.

        DCS = alpha * topical + beta * coref + gamma * (1 - discourse_signal)

        Note: discourse_signal is inverted because high signal means boundary,
        but high DCS should mean coherence.

        Args:
            sentences: List of sentences in the analysis window
            embeddings: Corresponding sentence embeddings

        Returns:
            DCS score between 0 and 1 (higher = more coherent)
        """
        topical = self.compute_topical_coherence(embeddings)
        coref = self.compute_coreference_density(sentences)

        # Get discourse signal for first sentence (potential boundary point)
        discourse = self.compute_discourse_signal(sentences[0]) if sentences else 0.5

        # Invert discourse signal (high boundary signal = low coherence)
        discourse_coherence = 1.0 - discourse

        dcs = (
            self.weights.alpha * topical
            + self.weights.beta * coref
            + self.weights.gamma * discourse_coherence
        )

        return max(0.0, min(1.0, dcs))

    def detect_boundaries(
        self,
        sentences: list[str],
        embeddings: np.ndarray,
        window_size: int = 3,
    ) -> list[tuple[int, float, float]]:
        """Detect boundary candidates using DCS.

        Analyzes each position between sentences and identifies
        potential boundaries where DCS drops below threshold.

        Args:
            sentences: All sentences in document
            embeddings: Corresponding sentence embeddings
            window_size: Number of sentences on each side to analyze

        Returns:
            List of (position, dcs_score, boundary_confidence) tuples
            Position is the sentence index where boundary would occur
            (i.e., boundary between sentence[position-1] and sentence[position])
        """
        boundaries = []

        for i in range(1, len(sentences)):
            # Get window around potential boundary
            start = max(0, i - window_size)
            end = min(len(sentences), i + window_size)

            window_sentences = sentences[start:end]
            window_embeddings = embeddings[start:end]

            dcs = self.compute_dcs(window_sentences, window_embeddings)

            if dcs < self.weights.threshold:
                # Convert DCS to confidence (lower DCS = higher boundary confidence)
                confidence = 1.0 - dcs
                boundaries.append((i, dcs, confidence))

        return boundaries

    def score_span(
        self,
        sentences: list[str],
        embeddings: np.ndarray,
    ) -> float:
        """Score the coherence of a text span.

        Useful for evaluating whether a proposed chunk is coherent.

        Args:
            sentences: Sentences in the span
            embeddings: Corresponding embeddings

        Returns:
            Coherence score between 0 and 1
        """
        return self.compute_dcs(sentences, embeddings)

    @property
    def weights_hash(self) -> str:
        """Get hash of current weights for reproducibility."""
        return self.weights.get_hash()

    def __repr__(self) -> str:
        return (
            f"DCSScorer(alpha={self.weights.alpha}, "
            f"beta={self.weights.beta}, "
            f"gamma={self.weights.gamma}, "
            f"threshold={self.weights.threshold})"
        )
