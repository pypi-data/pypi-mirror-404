"""
COSMIC: COncept-aware Semantic Meta-chunking with Intelligent Classification

A production-ready intelligent text chunking framework that achieves:
- Logical boundary detection using DCS (Discourse Coherence Score)
- Domain-aware segmentation with automatic classification
- Zero-overlap self-contained chunks with complete conceptual coherence
- Graceful degradation with multiple fallback strategies
"""

__version__ = "1.1.0"
__author__ = "Manceps Research Division"

from cosmic.core.chunk import COSMICChunk
from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document
from cosmic.core.enums import DomainType, Intent, ProcessingMode

__all__ = [
    "COSMICChunk",
    "COSMICConfig",
    "Document",
    "ProcessingMode",
    "Intent",
    "DomainType",
    "__version__",
]
