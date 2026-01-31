"""Configuration system for COSMIC framework."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class DCSConfig:
    """Discourse Coherence Score weights and threshold.

    DCS = alpha * topical_coherence + beta * coreference_density + gamma * discourse_signal

    Lower DCS indicates higher likelihood of a boundary.
    """

    alpha: float = 0.4  # Topical coherence weight
    beta: float = 0.35  # Coreference density weight
    gamma: float = 0.25  # Discourse marker weight
    threshold: float = 0.5  # Below this = boundary candidate

    def validate(self) -> None:
        """Validate weights sum to 1.0."""
        total = self.alpha + self.beta + self.gamma
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"DCS weights must sum to 1.0, got {total}")


@dataclass
class StructureConfig:
    """Stage 1: Structure Analysis configuration."""

    enabled: bool = True
    full_threshold: float = 0.7  # Above this -> full COSMIC pipeline
    semantic_threshold: float = 0.4  # Above this -> semantic-only, below -> fallback


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""

    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    batch_size: int = 64
    cache_size: int = 10000
    device: str = field(default_factory=lambda: os.getenv("COSMIC_EMBEDDING_DEVICE", "cuda"))
    normalize: bool = True


@dataclass
class LLMConfig:
    """LLM verification configuration (Stage 5)."""

    enabled: bool = True
    provider: str = field(
        default_factory=lambda: os.getenv("COSMIC_LLM_PROVIDER", "openai")
    )  # "openai", "ollama", or "auto"
    base_url: str = field(
        default_factory=lambda: os.getenv("COSMIC_LLM_URL", "http://localhost:8000/v1")
    )
    model_name: str = field(default_factory=lambda: os.getenv("COSMIC_LLM_MODEL", "default"))
    api_key: str = field(default_factory=lambda: os.getenv("COSMIC_LLM_API_KEY", ""))
    confidence_threshold: float = 0.8  # Only verify boundaries below this
    batch_size: int = 10
    timeout_seconds: int = 30
    max_context_tokens: int = 512
    max_retries: int = 3

    # Ollama-specific settings
    ollama_host: str = field(
        default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
    ollama_auto_start: bool = False  # Auto-start Ollama if not running
    ollama_auto_stop: bool = False  # Auto-stop Ollama after processing
    ollama_model: str = field(
        default_factory=lambda: os.getenv("COSMIC_OLLAMA_MODEL", "auto")
    )  # "auto" or specific model name


@dataclass
class ReferenceConfig:
    """Reference linking configuration (Stage 6)."""

    enabled: bool = True
    use_coreference: bool = True
    coreference_model: str = "en_core_web_trf"  # spaCy transformer model
    explicit_patterns: list[str] = field(
        default_factory=lambda: [
            r"Section\s+(\d+(?:\.\d+)*)",
            r"Appendix\s+([A-Z])",
            r"(?:see|refer to|as (?:discussed|stated) in)\s+(\w+)",
            r"(?:Table|Figure|Exhibit)\s+(\d+(?:\.\d+)*)",
        ]
    )


@dataclass
class ChunkConstraints:
    """Size constraints for chunks."""

    min_tokens: int = 100
    max_tokens: int = 2000
    target_tokens: int = 500


@dataclass
class FusionConfig:
    """Boundary fusion weights (Stage 4)."""

    structural_weight: float = 0.6
    semantic_weight: float = 0.4
    acceptance_threshold: float = 0.5


@dataclass
class COSMICConfig:
    """Complete COSMIC configuration."""

    # Stage configurations
    dcs: DCSConfig = field(default_factory=DCSConfig)
    structure: StructureConfig = field(default_factory=StructureConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    reference: ReferenceConfig = field(default_factory=ReferenceConfig)
    fusion: FusionConfig = field(default_factory=FusionConfig)
    chunks: ChunkConstraints = field(default_factory=ChunkConstraints)

    # Runtime settings
    workers: int = 4
    gpu_memory_fraction: float = 0.5

    # Domain taxonomy path
    taxonomy_path: Optional[Path] = None

    @classmethod
    def from_yaml(cls, path: Path) -> "COSMICConfig":
        """Load configuration from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(
            dcs=DCSConfig(**data.get("dcs", {})),
            structure=StructureConfig(**data.get("structure", {})),
            embedding=EmbeddingConfig(**data.get("embedding", {})),
            llm=LLMConfig(**data.get("llm", {})),
            reference=ReferenceConfig(**data.get("reference", {})),
            fusion=FusionConfig(**data.get("fusion", {})),
            chunks=ChunkConstraints(**data.get("chunks", {})),
            workers=data.get("workers", 4),
            gpu_memory_fraction=data.get("gpu_memory_fraction", 0.5),
            taxonomy_path=Path(data["taxonomy_path"]) if "taxonomy_path" in data else None,
        )

    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file."""
        data = {
            "dcs": {
                "alpha": self.dcs.alpha,
                "beta": self.dcs.beta,
                "gamma": self.dcs.gamma,
                "threshold": self.dcs.threshold,
            },
            "structure": {
                "enabled": self.structure.enabled,
                "full_threshold": self.structure.full_threshold,
                "semantic_threshold": self.structure.semantic_threshold,
            },
            "embedding": {
                "model_name": self.embedding.model_name,
                "batch_size": self.embedding.batch_size,
                "cache_size": self.embedding.cache_size,
                "device": self.embedding.device,
                "normalize": self.embedding.normalize,
            },
            "llm": {
                "enabled": self.llm.enabled,
                "provider": self.llm.provider,
                "base_url": self.llm.base_url,
                "model_name": self.llm.model_name,
                "confidence_threshold": self.llm.confidence_threshold,
                "batch_size": self.llm.batch_size,
                "timeout_seconds": self.llm.timeout_seconds,
                "max_context_tokens": self.llm.max_context_tokens,
                "ollama_host": self.llm.ollama_host,
                "ollama_auto_start": self.llm.ollama_auto_start,
                "ollama_auto_stop": self.llm.ollama_auto_stop,
                "ollama_model": self.llm.ollama_model,
            },
            "reference": {
                "enabled": self.reference.enabled,
                "use_coreference": self.reference.use_coreference,
                "coreference_model": self.reference.coreference_model,
                "explicit_patterns": self.reference.explicit_patterns,
            },
            "fusion": {
                "structural_weight": self.fusion.structural_weight,
                "semantic_weight": self.fusion.semantic_weight,
                "acceptance_threshold": self.fusion.acceptance_threshold,
            },
            "chunks": {
                "min_tokens": self.chunks.min_tokens,
                "max_tokens": self.chunks.max_tokens,
                "target_tokens": self.chunks.target_tokens,
            },
            "workers": self.workers,
            "gpu_memory_fraction": self.gpu_memory_fraction,
        }

        if self.taxonomy_path:
            data["taxonomy_path"] = str(self.taxonomy_path)

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def validate(self) -> None:
        """Validate all configuration values."""
        self.dcs.validate()

        if not 0 <= self.structure.full_threshold <= 1:
            raise ValueError("structure.full_threshold must be between 0 and 1")

        if not 0 <= self.structure.semantic_threshold <= 1:
            raise ValueError("structure.semantic_threshold must be between 0 and 1")

        if self.structure.semantic_threshold >= self.structure.full_threshold:
            raise ValueError("structure.semantic_threshold must be less than full_threshold")

        if self.chunks.min_tokens >= self.chunks.max_tokens:
            raise ValueError("chunks.min_tokens must be less than max_tokens")
