"""Enumerations for COSMIC framework."""

from enum import Enum


class ProcessingMode(Enum):
    """Processing mode indicating which pipeline path was used."""

    FULL_COSMIC = "full_cosmic"
    SEMANTIC_ONLY = "semantic_only"
    SLIDING_WINDOW = "sliding_window"
    FIXED_LENGTH = "fixed_length"


class Intent(Enum):
    """Primary intent classification for chunks."""

    DEFINE = "define"
    EXPLAIN = "explain"
    LIST = "list"
    ARGUE = "argue"
    DESCRIBE = "describe"
    INSTRUCT = "instruct"
    SUMMARIZE = "summarize"
    COMPARE = "compare"
    NARRATE = "narrate"
    UNKNOWN = "unknown"


class DomainType(Enum):
    """Pre-defined domain categories."""

    MEDICAL = "medical"
    LEGAL = "legal"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    ACADEMIC = "academic"
    ADMINISTRATIVE = "administrative"
    GENERAL = "general"
    UNKNOWN = "unknown"


class BoundarySource(Enum):
    """Source of boundary detection."""

    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    FUSED = "fused"
    LLM_VERIFIED = "llm_verified"
    AUTO_ACCEPT = "auto_accept"


class StructuralElement(Enum):
    """Types of structural elements detected in documents."""

    HEADING_NUMBERED = "heading_numbered"
    HEADING_LETTER = "heading_letter"
    HEADING_HASH = "heading_hash"
    BULLET_LIST = "bullet_list"
    NUMBERED_LIST = "numbered_list"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    BLOCKQUOTE = "blockquote"
    PARAGRAPH = "paragraph"


class SectionType(Enum):
    """Common section types in academic/technical documents."""

    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    BACKGROUND = "background"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    APPENDIX = "appendix"
    UNKNOWN = "unknown"
