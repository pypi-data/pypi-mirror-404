"""Structural patterns for document analysis."""

import re
from dataclasses import dataclass
from typing import Any, Optional

from cosmic.core.enums import StructuralElement


@dataclass
class StructuralMatch:
    """A matched structural element in text."""

    element_type: StructuralElement
    start: int  # Character offset
    end: int
    text: str
    boundary_prior: float  # Prior probability this is a boundary
    level: int = 0  # Nesting level (for headings)


class StructuralPatterns:
    """Pattern matching for document structure detection.

    Detects headings, lists, tables, code blocks, and other
    structural elements that indicate potential chunk boundaries.
    """

    # Heading patterns with boundary priors
    PATTERNS: dict[StructuralElement, dict[str, Any]] = {
        # Numbered headings: "1.", "1.2.", "1.2.3."
        StructuralElement.HEADING_NUMBERED: {
            "pattern": r"^(\d+\.)+\s+\w",
            "prior": 0.95,
            "multiline": True,
        },
        # Letter headings: "A.", "B."
        StructuralElement.HEADING_LETTER: {
            "pattern": r"^[A-Z]\.\s+\w",
            "prior": 0.90,
            "multiline": True,
        },
        # Markdown headings: "# Title", "## Subtitle"
        StructuralElement.HEADING_HASH: {
            "pattern": r"^#{1,6}\s+\w",
            "prior": 0.95,
            "multiline": True,
        },
        # Bullet lists: "- item", "* item", "• item"
        StructuralElement.BULLET_LIST: {
            "pattern": r"^[\-\*•]\s+\w",
            "prior": 0.60,
            "multiline": True,
        },
        # Numbered lists: "1) item", "1. item" (but not section numbers)
        StructuralElement.NUMBERED_LIST: {
            "pattern": r"^\d+[)\]]\s+\w",
            "prior": 0.55,
            "multiline": True,
        },
        # Code blocks (markdown)
        StructuralElement.CODE_BLOCK: {
            "pattern": r"^```",
            "prior": 0.80,
            "multiline": True,
        },
        # Blockquotes
        StructuralElement.BLOCKQUOTE: {
            "pattern": r"^>\s+\w",
            "prior": 0.50,
            "multiline": True,
        },
    }

    # Discourse markers that suggest boundaries
    DISCOURSE_BOUNDARY_PATTERNS = [
        (r"^(However|But|Although|Despite|Nevertheless)\b", 0.75),
        (r"^(In contrast|On the other hand|Conversely)\b", 0.80),
        (r"^(Therefore|Thus|Hence|Consequently)\b", 0.70),
        (r"^(In conclusion|To summarize|In summary)\b", 0.85),
        (r"^(First(ly)?|Second(ly)?|Third(ly)?|Finally)\b", 0.65),
        (r"^(Moving on|Turning to|Regarding)\b", 0.75),
        (r"^(Note:|Important:|Warning:)\b", 0.70),
    ]

    # Section header keywords (case-insensitive)
    SECTION_KEYWORDS = {
        "abstract": 0.95,
        "introduction": 0.95,
        "background": 0.90,
        "related work": 0.90,
        "methodology": 0.95,
        "methods": 0.95,
        "materials and methods": 0.95,
        "results": 0.95,
        "discussion": 0.95,
        "conclusion": 0.95,
        "conclusions": 0.95,
        "references": 0.98,
        "bibliography": 0.98,
        "appendix": 0.95,
        "acknowledgments": 0.90,
        "acknowledgements": 0.90,
    }

    def __init__(self) -> None:
        self._compiled_patterns: dict[StructuralElement, re.Pattern[str]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile all regex patterns."""
        for element_type, config in self.PATTERNS.items():
            flags = re.MULTILINE if config.get("multiline") else 0
            self._compiled_patterns[element_type] = re.compile(
                config["pattern"], flags | re.IGNORECASE
            )

        # Compile discourse patterns
        self._discourse_patterns = [
            (re.compile(p, re.MULTILINE), prior) for p, prior in self.DISCOURSE_BOUNDARY_PATTERNS
        ]

    def find_structural_elements(self, text: str) -> list[StructuralMatch]:
        """Find all structural elements in text.

        Args:
            text: Document text to analyze

        Returns:
            List of StructuralMatch objects sorted by position
        """
        matches = []

        for element_type, pattern in self._compiled_patterns.items():
            config = self.PATTERNS[element_type]
            for match in pattern.finditer(text):
                matches.append(
                    StructuralMatch(
                        element_type=element_type,
                        start=match.start(),
                        end=match.end(),
                        text=match.group().strip(),
                        boundary_prior=float(config["prior"]),
                        level=self._get_heading_level(element_type, match.group()),
                    )
                )

        # Sort by position
        matches.sort(key=lambda m: m.start)
        return matches

    def _get_heading_level(self, element_type: StructuralElement, text: str) -> int:
        """Determine heading level (depth)."""
        if element_type == StructuralElement.HEADING_HASH:
            # Count # symbols
            return len(text) - len(text.lstrip("#"))
        elif element_type == StructuralElement.HEADING_NUMBERED:
            # Count dots in numbering
            return text.count(".")
        return 0

    def get_boundary_prior(self, sentence: str) -> float:
        """Get boundary prior probability for a sentence.

        Args:
            sentence: Sentence text to analyze

        Returns:
            Prior probability (0-1) that this sentence starts a new section
        """
        sentence = sentence.strip()
        max_prior = 0.0

        # Check structural patterns
        for element_type, pattern in self._compiled_patterns.items():
            if pattern.match(sentence):
                prior = float(self.PATTERNS[element_type]["prior"])
                max_prior = max(max_prior, prior)

        # Check discourse markers
        for pattern, prior in self._discourse_patterns:
            if pattern.match(sentence):
                max_prior = max(max_prior, prior)

        # Check section keywords
        sentence_lower = sentence.lower()
        for keyword, prior in self.SECTION_KEYWORDS.items():
            if sentence_lower.startswith(keyword):
                max_prior = max(max_prior, prior)

        return max_prior

    def compute_structure_score(self, text: str) -> float:
        """Compute overall structure score for document.

        Higher score indicates more structured document:
        - Many headings
        - Consistent list usage
        - Clear section markers

        Args:
            text: Full document text

        Returns:
            Structure score between 0 and 1
        """
        if not text:
            return 0.0

        # Count structural elements
        elements = self.find_structural_elements(text)

        # Count by type
        type_counts: dict[StructuralElement, int] = {}
        for elem in elements:
            type_counts[elem.element_type] = type_counts.get(elem.element_type, 0) + 1

        # Compute component scores
        text_length = len(text)
        num_lines = text.count("\n") + 1

        # Heading density (headings per 1000 chars)
        num_headings = sum(
            type_counts.get(t, 0)
            for t in [
                StructuralElement.HEADING_NUMBERED,
                StructuralElement.HEADING_LETTER,
                StructuralElement.HEADING_HASH,
            ]
        )
        heading_density = min(1.0, (num_headings / text_length) * 1000 / 10)

        # List prevalence
        num_lists = sum(
            type_counts.get(t, 0)
            for t in [StructuralElement.BULLET_LIST, StructuralElement.NUMBERED_LIST]
        )
        list_prevalence = min(1.0, num_lists / max(num_lines / 20, 1))

        # Paragraph structure (whitespace patterns)
        double_newlines = text.count("\n\n")
        para_structure = min(1.0, double_newlines / max(num_lines / 10, 1))

        # Combine scores
        structure_score = 0.4 * heading_density + 0.3 * list_prevalence + 0.3 * para_structure

        return min(1.0, structure_score)

    def detect_section_type(self, text: str) -> Optional[str]:
        """Detect section type from heading text.

        Args:
            text: Heading or section start text

        Returns:
            Section type string or None
        """
        text_lower = text.lower().strip()

        # Remove numbering
        text_lower = re.sub(r"^[\d\.]+\s*", "", text_lower)
        text_lower = re.sub(r"^[a-z]\.\s*", "", text_lower)
        text_lower = re.sub(r"^#+\s*", "", text_lower)

        for keyword in self.SECTION_KEYWORDS:
            if text_lower.startswith(keyword):
                return keyword.replace(" ", "_").upper()

        return None
