"""Coreference resolution wrapper using spaCy."""

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

from cosmic.core.config import ReferenceConfig
from cosmic.exceptions import CoreferenceError

logger = logging.getLogger(__name__)

# Lazy imports to avoid loading spaCy at module level
_nlp: Any = None


def get_nlp(model_name: str = "en_core_web_trf") -> Any:
    """Lazy load spaCy model."""
    global _nlp
    if _nlp is None:
        try:
            import spacy

            _nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            # Model not installed - try smaller model
            import spacy

            try:
                _nlp = spacy.load("en_core_web_sm")
                logger.warning(f"Model {model_name} not found, using en_core_web_sm instead")
            except OSError:
                raise CoreferenceError(
                    f"No spaCy model available. Install with: python -m spacy download {model_name}",
                    details={"model": model_name},
                )
    return _nlp


@dataclass
class Mention:
    """A mention in a coreference chain."""

    text: str
    start_char: int
    end_char: int
    sentence_idx: int


@dataclass
class CoreferenceChain:
    """A chain of coreferent mentions."""

    chain_id: int
    mentions: list[Mention]

    @property
    def main_mention(self) -> Mention:
        """Get the main (longest) mention in the chain."""
        return max(self.mentions, key=lambda m: len(m.text))

    @property
    def spans_multiple_sentences(self) -> bool:
        """Check if chain spans multiple sentences."""
        sentence_indices = set(m.sentence_idx for m in self.mentions)
        return len(sentence_indices) > 1

    def get_sentence_indices(self) -> set[int]:
        """Get all sentence indices this chain spans."""
        return set(m.sentence_idx for m in self.mentions)


class CoreferenceResolver:
    """Resolve coreferences in text using spaCy.

    Note: Full neural coreference requires additional models.
    This implementation provides basic pronoun resolution and
    explicit reference detection.
    """

    # Pronouns that typically have antecedents
    PRONOUNS = {
        "it",
        "they",
        "them",
        "their",
        "its",
        "this",
        "these",
        "that",
        "those",
        "he",
        "she",
        "him",
        "her",
        "his",
    }

    def __init__(self, config: ReferenceConfig):
        self.config = config
        self._nlp = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize spaCy model."""
        if self.config.use_coreference:
            try:
                self._nlp = get_nlp(self.config.coreference_model)
                self._initialized = True
            except Exception as e:
                logger.warning(f"Failed to load coreference model: {e}")
                self._initialized = False
        else:
            self._initialized = True

    @property
    def nlp(self) -> Any:
        """Get spaCy model."""
        if self._nlp is None and self.config.use_coreference:
            self.initialize()
        return self._nlp

    def resolve(
        self,
        text: str,
        sentence_offsets: Optional[list[tuple[int, int]]] = None,
    ) -> list[CoreferenceChain]:
        """Resolve coreferences in text.

        Args:
            text: Full document text
            sentence_offsets: List of (start, end) char offsets for sentences

        Returns:
            List of CoreferenceChain objects
        """
        if not self.config.use_coreference:
            return []

        if not self._initialized:
            self.initialize()

        if self._nlp is None:
            return []

        try:
            doc = self._nlp(text)

            # Build sentence offset map if not provided
            if sentence_offsets is None:
                sentence_offsets = [(sent.start_char, sent.end_char) for sent in doc.sents]

            chains = self._extract_chains(doc, sentence_offsets)
            return chains

        except Exception as e:
            logger.warning(f"Coreference resolution failed: {e}")
            return []

    def _extract_chains(
        self,
        doc: Any,
        sentence_offsets: list[tuple[int, int]],
    ) -> list[CoreferenceChain]:
        """Extract coreference chains from spaCy doc.

        This is a simplified implementation that:
        1. Finds pronouns
        2. Links them to nearby noun phrases
        """
        chains: list[CoreferenceChain] = []

        # Find all noun chunks and pronouns
        noun_chunks = list(doc.noun_chunks)
        pronouns = [token for token in doc if token.lower_ in self.PRONOUNS]

        # Group pronouns with their likely antecedents
        for pronoun in pronouns:
            # Find nearest preceding noun chunk
            antecedent = None
            min_dist = float("inf")

            for chunk in noun_chunks:
                if chunk.end <= pronoun.i:  # Chunk is before pronoun
                    dist = pronoun.i - chunk.end
                    if dist < min_dist:
                        min_dist = dist
                        antecedent = chunk

            if antecedent and min_dist < 50:  # Within ~50 tokens
                # Create chain
                mentions = [
                    Mention(
                        text=antecedent.text,
                        start_char=antecedent.start_char,
                        end_char=antecedent.end_char,
                        sentence_idx=self._get_sentence_idx(
                            antecedent.start_char, sentence_offsets
                        ),
                    ),
                    Mention(
                        text=pronoun.text,
                        start_char=pronoun.idx,
                        end_char=pronoun.idx + len(pronoun.text),
                        sentence_idx=self._get_sentence_idx(pronoun.idx, sentence_offsets),
                    ),
                ]

                chains.append(CoreferenceChain(chain_id=len(chains), mentions=mentions))

        return chains

    def _get_sentence_idx(
        self,
        char_offset: int,
        sentence_offsets: list[tuple[int, int]],
    ) -> int:
        """Get sentence index for a character offset."""
        for i, (start, end) in enumerate(sentence_offsets):
            if start <= char_offset < end:
                return i
        return len(sentence_offsets) - 1


class ExplicitReferenceDetector:
    """Detect explicit references like 'Section 3' or 'Appendix A'."""

    def __init__(self, patterns: list[str]):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

    def find_references(
        self,
        text: str,
        sentence_offsets: list[tuple[int, int]],
    ) -> list[tuple[int, str]]:
        """Find explicit references in text.

        Args:
            text: Text to search
            sentence_offsets: Sentence boundaries

        Returns:
            List of (sentence_idx, reference_text) tuples
        """
        references = []

        for pattern in self.patterns:
            for match in pattern.finditer(text):
                sentence_idx = self._get_sentence_idx(match.start(), sentence_offsets)
                references.append((sentence_idx, match.group()))

        return references

    def _get_sentence_idx(
        self,
        char_offset: int,
        sentence_offsets: list[tuple[int, int]],
    ) -> int:
        """Get sentence index for a character offset."""
        for i, (start, end) in enumerate(sentence_offsets):
            if start <= char_offset < end:
                return i
        return len(sentence_offsets) - 1
