"""Domain classification using taxonomy and embeddings."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import yaml

from cosmic.core.config import COSMICConfig
from cosmic.models.embeddings import EmbeddingModel

logger = logging.getLogger(__name__)


@dataclass
class DomainInfo:
    """Information about a domain."""

    name: str
    description: str
    subdomains: list[str]
    indicators: list[str]
    embedding: Optional[np.ndarray] = None


@dataclass
class DomainAssignment:
    """Domain assignment for a chunk."""

    domain: str
    subdomain: Optional[str]
    confidence: float
    is_emergent: bool = False  # True if domain was discovered, not from taxonomy

    def __repr__(self) -> str:
        sub = f"/{self.subdomain}" if self.subdomain else ""
        return f"Domain({self.domain}{sub}, conf={self.confidence:.2f})"


class DomainClassifier:
    """Classify text chunks into domains using taxonomy.

    Uses a combination of:
    - Keyword indicator matching
    - Embedding similarity to domain descriptions
    - Emergent domain detection for unknown domains
    """

    def __init__(
        self,
        config: COSMICConfig,
        embedding_model: Optional[EmbeddingModel] = None,
    ):
        self.config = config
        self._embedding_model = embedding_model
        self._domains: dict[str, DomainInfo] = {}
        self._domain_embeddings: Optional[np.ndarray] = None
        self._initialized = False

    def initialize(self, taxonomy_path: Optional[Path] = None) -> None:
        """Load taxonomy and compute domain embeddings."""
        # Load taxonomy
        path = taxonomy_path or self.config.taxonomy_path
        if path and path.exists():
            self._load_taxonomy(path)
        else:
            self._load_default_taxonomy()

        # Initialize embedding model if needed
        if self._embedding_model is None:
            self._embedding_model = EmbeddingModel(self.config.embedding)

        # Compute domain embeddings
        self._compute_domain_embeddings()

        self._initialized = True
        logger.info(f"Domain classifier initialized with {len(self._domains)} domains")

    def _load_taxonomy(self, path: Path) -> None:
        """Load domain taxonomy from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        for name, info in data.get("domains", {}).items():
            self._domains[name] = DomainInfo(
                name=name,
                description=info.get("description", ""),
                subdomains=info.get("subdomains", []),
                indicators=info.get("indicators", []),
            )

    def _load_default_taxonomy(self) -> None:
        """Load default domain taxonomy."""
        default_domains = {
            "medical": DomainInfo(
                name="medical",
                description="Healthcare, clinical, pharmaceutical content",
                subdomains=["clinical", "pharmaceutical", "diagnostic"],
                indicators=[
                    "patient",
                    "treatment",
                    "diagnosis",
                    "symptom",
                    "medication",
                ],
            ),
            "legal": DomainInfo(
                name="legal",
                description="Legal documents, contracts, regulations",
                subdomains=["contract", "litigation", "regulatory"],
                indicators=["clause", "party", "agreement", "liability", "jurisdiction"],
            ),
            "financial": DomainInfo(
                name="financial",
                description="Financial reports, investment, banking",
                subdomains=["accounting", "investment", "banking"],
                indicators=["revenue", "asset", "liability", "portfolio", "equity"],
            ),
            "technical": DomainInfo(
                name="technical",
                description="Technical documentation, software, engineering",
                subdomains=["software", "hardware", "network"],
                indicators=[
                    "system",
                    "implementation",
                    "architecture",
                    "protocol",
                    "algorithm",
                ],
            ),
            "academic": DomainInfo(
                name="academic",
                description="Research papers, scientific publications",
                subdomains=["methodology", "results", "discussion"],
                indicators=[
                    "study",
                    "hypothesis",
                    "analysis",
                    "findings",
                    "significance",
                ],
            ),
        }
        self._domains = default_domains

    def _compute_domain_embeddings(self) -> None:
        """Compute embeddings for domain descriptions."""
        if not self._embedding_model:
            return

        domain_texts = []
        domain_names = []

        for name, info in self._domains.items():
            # Combine description and indicators for embedding
            text = f"{info.description}. Keywords: {', '.join(info.indicators)}"
            domain_texts.append(text)
            domain_names.append(name)

        if domain_texts:
            embeddings = self._embedding_model.encode(domain_texts)
            self._domain_embeddings = embeddings

            # Store embeddings in domain info
            for i, name in enumerate(domain_names):
                self._domains[name].embedding = embeddings[i]

    @property
    def embedding_model(self) -> EmbeddingModel:
        """Get embedding model."""
        if self._embedding_model is None:
            self._embedding_model = EmbeddingModel(self.config.embedding)
        return self._embedding_model

    def classify(self, text: str) -> DomainAssignment:
        """Classify a text chunk into a domain.

        Args:
            text: Text to classify

        Returns:
            DomainAssignment with domain, subdomain, and confidence
        """
        if not self._initialized:
            self.initialize()

        # Method 1: Indicator matching
        indicator_scores = self._score_by_indicators(text)

        # Method 2: Embedding similarity
        embedding_scores = self._score_by_embedding(text)

        # Combine scores (weighted average)
        combined_scores = {}
        for domain in self._domains:
            ind_score = indicator_scores.get(domain, 0)
            emb_score = embedding_scores.get(domain, 0)
            combined_scores[domain] = 0.4 * ind_score + 0.6 * emb_score

        # Find best match
        if combined_scores:
            best_domain = max(combined_scores, key=lambda k: combined_scores[k])
            best_score = combined_scores[best_domain]

            if best_score > 0.3:  # Minimum confidence threshold
                subdomain = self._detect_subdomain(text, best_domain)
                return DomainAssignment(
                    domain=best_domain,
                    subdomain=subdomain,
                    confidence=best_score,
                    is_emergent=False,
                )

        # No confident match - return unknown
        return DomainAssignment(
            domain="unknown",
            subdomain=None,
            confidence=0.0,
            is_emergent=False,
        )

    def classify_batch(self, texts: list[str]) -> list[DomainAssignment]:
        """Classify multiple texts efficiently.

        Args:
            texts: List of texts to classify

        Returns:
            List of DomainAssignment objects
        """
        if not self._initialized:
            self.initialize()

        # Batch encode all texts
        text_embeddings = self.embedding_model.encode(texts)

        assignments = []
        for i, text in enumerate(texts):
            # Indicator matching
            indicator_scores = self._score_by_indicators(text)

            # Embedding similarity (using pre-computed embedding)
            embedding_scores = self._score_by_embedding_vector(text_embeddings[i])

            # Combine
            combined = {}
            for domain in self._domains:
                ind = indicator_scores.get(domain, 0)
                emb = embedding_scores.get(domain, 0)
                combined[domain] = 0.4 * ind + 0.6 * emb

            if combined:
                best = max(combined, key=lambda k: combined[k])
                score = combined[best]

                if score > 0.3:
                    subdomain = self._detect_subdomain(text, best)
                    assignments.append(
                        DomainAssignment(
                            domain=best,
                            subdomain=subdomain,
                            confidence=score,
                        )
                    )
                    continue

            assignments.append(DomainAssignment(domain="unknown", subdomain=None, confidence=0.0))

        return assignments

    def _score_by_indicators(self, text: str) -> dict[str, float]:
        """Score domains by indicator keyword presence."""
        text_lower = text.lower()
        scores = {}

        for name, info in self._domains.items():
            matches = sum(1 for ind in info.indicators if ind.lower() in text_lower)
            # Normalize by number of indicators
            scores[name] = min(1.0, matches / max(len(info.indicators), 1))

        return scores

    def _score_by_embedding(self, text: str) -> dict[str, float]:
        """Score domains by embedding similarity."""
        if self._domain_embeddings is None:
            return {}

        text_emb = self.embedding_model.encode_single(text)
        return self._score_by_embedding_vector(text_emb)

    def _score_by_embedding_vector(self, text_emb: np.ndarray) -> dict[str, float]:
        """Score domains given pre-computed text embedding."""
        if self._domain_embeddings is None:
            return {}

        # Compute similarities
        similarities = self.embedding_model.similarity(
            text_emb.reshape(1, -1), self._domain_embeddings
        )[0]

        # Map to domain names
        domain_names = list(self._domains.keys())
        scores = {name: float(similarities[i]) for i, name in enumerate(domain_names)}

        # Normalize to 0-1 range
        if scores:
            min_s = min(scores.values())
            max_s = max(scores.values())
            if max_s > min_s:
                scores = {k: (v - min_s) / (max_s - min_s) for k, v in scores.items()}

        return scores

    def _detect_subdomain(self, text: str, domain: str) -> Optional[str]:
        """Detect subdomain within a domain."""
        if domain not in self._domains:
            return None

        subdomains = self._domains[domain].subdomains
        if not subdomains:
            return None

        text_lower = text.lower()
        for sub in subdomains:
            if sub.lower() in text_lower:
                return sub

        return None
