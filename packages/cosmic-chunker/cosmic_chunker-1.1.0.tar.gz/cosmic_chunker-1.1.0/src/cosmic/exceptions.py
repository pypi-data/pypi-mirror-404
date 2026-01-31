"""COSMIC exception hierarchy.

Error codes follow the convention COSMIC_E00X where:
- E001: Structure analysis errors
- E002: Embedding/semantic errors
- E003: LLM verification errors
- E004: Domain classification errors
- E005: Reference resolution errors
- E006: Configuration errors
"""


class COSMICError(Exception):
    """Base exception for all COSMIC errors."""

    error_code: str = "COSMIC_E000"

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(f"[{self.error_code}] {message}")


class StructureAnalysisError(COSMICError):
    """Error during structure analysis (Stage 1).

    Recovery: Fallback to semantic-only processing.
    """

    error_code = "COSMIC_E001"


class SemanticBoundaryError(COSMICError):
    """Error during semantic boundary detection (Stage 2).

    Recovery: Fallback to sliding window with basic similarity.
    """

    error_code = "COSMIC_E002"


class LLMVerificationError(COSMICError):
    """Error during LLM boundary verification (Stage 5).

    Recovery: Accept boundaries at 0.7 confidence threshold.
    """

    error_code = "COSMIC_E003"


class DomainClassificationError(COSMICError):
    """Error during domain classification (Stage 3).

    Recovery: Continue with domain='unknown'.
    """

    error_code = "COSMIC_E004"


class ReferenceResolutionError(COSMICError):
    """Error during reference linking (Stage 6).

    Recovery: Disable coreference, use regex-only detection.
    """

    error_code = "COSMIC_E005"


class ConfigurationError(COSMICError):
    """Error in configuration loading or validation.

    Recovery: Use default configuration values.
    """

    error_code = "COSMIC_E006"


class EmbeddingModelError(SemanticBoundaryError):
    """Embedding model unavailable or failed."""

    pass


class ClusteringError(DomainClassificationError):
    """Clustering produced invalid results (e.g., singleton clusters)."""

    pass


class DCSCalibrationError(SemanticBoundaryError):
    """DCS weight calibration failed due to insufficient structure."""

    pass


class LLMConnectionError(LLMVerificationError):
    """Failed to connect to LLM endpoint."""

    pass


class LLMTimeoutError(LLMVerificationError):
    """LLM verification timed out."""

    pass


class CoreferenceError(ReferenceResolutionError):
    """Coreference model failed or out of memory."""

    pass
