# COSMIC: COncept-aware Semantic Meta-chunking with Intelligent Classification

A production-ready intelligent text chunking framework for Retrieval-Augmented Generation (RAG) systems.

**Developed by Manceps Research Division**

## Research Objectives

COSMIC addresses fundamental limitations in existing text chunking approaches for RAG systems:

### Problem Statement

Current chunking methods suffer from three critical issues:
1. **Semantic Fragmentation** - Fixed-length chunkers split mid-concept, breaking coherent ideas
2. **Context Loss** - Simple overlap strategies create redundancy without preserving meaning
3. **Domain Blindness** - One-size-fits-all approaches ignore domain-specific structure

### Our Approach

COSMIC introduces a 6-stage pipeline that combines:
- **Discourse Coherence Scoring (DCS)** - Multi-signal boundary detection using topical coherence, coreference density, and discourse markers
- **MST-based Domain Clustering** - Minimum spanning tree clustering for domain classification
- **Adaptive Boundary Fusion** - Weighted combination of structural and semantic signals
- **LLM Verification** - Optional verification of uncertain boundaries
- **Zero-Overlap Architecture** - Self-contained conceptual chunks without redundant overlap

### Target Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Coherence Score | > 0.85 | Semantic unity within chunks |
| Cross-Concept Splits | < 5% | Chunks that break conceptual boundaries |
| Latency | < 150ms/page | Processing speed |
| Fallback Rate | < 15% | Graceful degradation frequency |

## Installation

### Prerequisites

- Python 3.10+
- CUDA-capable GPU (recommended) or CPU
- 8GB+ RAM

### Install from Source

```bash
# Clone the repository
git clone https://github.com/manceps/cosmic.git
cd cosmic

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install with all dependencies
pip install -e ".[all]"

# Install spaCy model for coreference resolution
python -m spacy download en_core_web_trf
```

### Docker Installation

```bash
# Build container
docker build -t cosmic:latest .

# Run with GPU support
docker run --gpus all -v $(pwd):/workspace cosmic:latest
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```bash
# LLM Provider: "openai", "ollama", or "auto"
COSMIC_LLM_PROVIDER=openai

# LLM endpoint for Stage 5 verification (OpenAI-compatible API)
COSMIC_LLM_URL=http://localhost:8000/v1
COSMIC_LLM_MODEL=default

# Ollama configuration (when using provider=ollama)
OLLAMA_HOST=http://localhost:11434
COSMIC_OLLAMA_MODEL=auto  # "auto" or specific model

# Embedding computation device
COSMIC_EMBEDDING_DEVICE=cuda  # Options: cuda, cpu, mps
```

### Using Ollama for LLM Verification

COSMIC integrates with [Ollama](https://ollama.com) for local LLM verification. The CLI can automatically detect, start, and stop Ollama:

```bash
# Auto-detect and use the best available model
cosmic chunk document.txt --strategy full --ollama auto

# Use a specific model
cosmic chunk document.txt --strategy full --ollama gemma3:latest

# Check Ollama status and available models
cosmic ollama status
cosmic ollama list
```

When using `--ollama`:
1. COSMIC checks if Ollama is installed and has models available
2. If the server isn't running, it starts automatically
3. After chunking completes, the server is stopped (if COSMIC started it)

**Recommended models for verification** (in order of preference):
- `gemma3` - Fast, good quality (3.3 GB)
- `qwen2.5-coder:7b` - Good balance (4.7 GB)
- `llama3.2` - Versatile (various sizes)

### Configuration Files

**Default configuration:** `configs/default.yaml`

```yaml
dcs:
  alpha: 0.4    # Topical coherence weight
  beta: 0.35   # Coreference density weight
  gamma: 0.25  # Discourse signal weight

structure:
  heading_weight: 0.4
  list_weight: 0.3
  table_weight: 0.3

fusion:
  structural_weight: 0.6
  semantic_weight: 0.4
  acceptance_threshold: 0.5

chunk_constraints:
  min_tokens: 100
  max_tokens: 512
  target_tokens: 350
```

**Domain taxonomy:** `configs/taxonomies/default.yaml`

Defines domain-specific terminology and patterns for classification.

## Usage

### Basic Usage

```python
from cosmic import COSMICChunker, Document

# Initialize chunker with default configuration
chunker = COSMICChunker()

# Create document from text
doc = Document.from_text("""
Your document text here. COSMIC will analyze the structure,
detect semantic boundaries, and create coherent chunks.
""")

# Chunk with automatic strategy selection
chunks = chunker.chunk_document(doc, strategy="auto")

# Access chunk data
for chunk in chunks:
    print(f"Domain: {chunk.domain}")
    print(f"Coherence: {chunk.coherence_score:.2f}")
    print(f"Text: {chunk.text[:100]}...")
    print("---")
```

### Strategy Selection

```python
# Full 6-stage pipeline (highest quality)
chunks = chunker.chunk_document(doc, strategy="full")

# Semantic-only (faster, DCS without structure analysis)
chunks = chunker.chunk_document(doc, strategy="semantic")

# Sliding window (basic similarity-based)
chunks = chunker.chunk_document(doc, strategy="sliding")

# Fixed-length (fastest, token-based splitting)
chunks = chunker.chunk_document(doc, strategy="fixed")

# Auto (recommended) - selects based on document structure
chunks = chunker.chunk_document(doc, strategy="auto")
```

### Batch Processing

```python
from cosmic import BatchProcessor, Document, COSMICConfig

# Initialize batch processor
processor = BatchProcessor(
    config=COSMICConfig(),
    max_workers=4,
)

# Process multiple documents
documents = [Document.from_text(text) for text in texts]
result = processor.process(documents, strategy="auto", show_progress=True)

print(f"Processed: {result.documents_processed}")
print(f"Failed: {result.documents_failed}")
print(f"Total chunks: {result.total_chunks}")

for doc_id, chunks in result.chunks_by_document.items():
    print(f"Document {doc_id}: {len(chunks)} chunks")
```

### Custom Configuration

```python
from cosmic import COSMICChunker, COSMICConfig
from cosmic.core.config import DCSConfig, ChunkConstraints

# Create custom configuration
config = COSMICConfig(
    dcs=DCSConfig(
        alpha=0.5,   # Increase topical coherence weight
        beta=0.3,
        gamma=0.2,
    ),
    chunk_constraints=ChunkConstraints(
        min_tokens=50,
        max_tokens=1024,
        target_tokens=512,
    ),
)

chunker = COSMICChunker(config=config)
```

### Loading from YAML

```python
from cosmic import COSMICChunker, COSMICConfig

config = COSMICConfig.from_yaml("configs/custom.yaml")
chunker = COSMICChunker(config=config)
```

## Architecture

### 6-Stage Pipeline

```
Document → Structure Analysis → Semantic Boundaries → Domain Classification
                                                              ↓
              Reference Linking ← LLM Verification ← Boundary Fusion
                      ↓
               COSMICChunks (with rich metadata)
```

#### Stage 1: Structure Analysis
- Detects headings, lists, tables, and other structural elements
- Computes structure score (0-1)
- Selects processing pathway based on document structure

#### Stage 2: Semantic Boundary Detection
- Computes Discourse Coherence Score (DCS) between sentences
- Identifies candidate boundaries where coherence drops

#### Stage 3: Domain Classification
- Uses MST-based clustering on chunk embeddings
- Matches clusters to domain taxonomy
- Assigns domain labels to chunks

#### Stage 4: Boundary Fusion
- Merges structural (weight: 0.6) and semantic (weight: 0.4) signals
- Applies acceptance threshold filtering

#### Stage 5: LLM Verification
- Verifies uncertain boundaries (confidence < 0.8) via external LLM
- Auto-accepts high-confidence boundaries
- Supports OpenAI-compatible APIs and Ollama
- Use `--ollama` flag for automatic Ollama integration
- Skipped if no LLM endpoint configured

#### Stage 6: Reference Linking
- Detects explicit references (regex patterns)
- Resolves coreferences using spaCy
- Links related chunks for retrieval

### DCS Formula

```
DCS = α × topical_coherence + β × coreference_density + γ × discourse_signal
```

Where:
- **α = 0.4**: Topical coherence from embedding similarity
- **β = 0.35**: Coreference density measuring entity continuity
- **γ = 0.25**: Discourse markers indicating transitions

**Lower DCS → Higher boundary confidence**

### Fallback Chain

COSMIC implements graceful degradation:

```
Full COSMIC → Semantic-only → Sliding window → Fixed-length
(structure)   (DCS only)     (basic similarity) (token split)
```

Each fallback level maintains chunking quality while reducing computational requirements.

## Benchmarks

### Running Benchmarks

```bash
# Run full benchmark suite
python -m benchmarks.runner

# Run with specific datasets
python -m benchmarks.runner --datasets arxiv pubmed

# Run with limited samples
python -m benchmarks.runner --limit 100
```

### Available Baselines

- **Fixed-length (512 tokens)** - Standard token-based splitting
- **LangChain Recursive** - RecursiveCharacterTextSplitter
- **Semantic Chunking** - Embedding similarity-based splitting
- **Percentile Semantic** - Adaptive threshold semantic chunking

### Metrics

- **Coherence Score** - Average intra-chunk semantic similarity
- **Cross-Concept Splits** - Percentage of boundaries breaking concepts
- **Latency** - Processing time per page (ms)
- **Throughput** - Documents per second

## Project Structure

```
cosmic/
├── src/cosmic/
│   ├── core/           # Data structures
│   │   ├── chunk.py    # COSMICChunk dataclass
│   │   ├── config.py   # Configuration system
│   │   ├── document.py # Document representation
│   │   └── enums.py    # Enumerations
│   │
│   ├── pipeline/       # 6 pipeline stages
│   │   ├── structure.py    # Stage 1
│   │   ├── semantic.py     # Stage 2
│   │   ├── domain.py       # Stage 3
│   │   ├── fusion.py       # Stage 4
│   │   ├── verification.py # Stage 5
│   │   └── reference.py    # Stage 6
│   │
│   ├── scoring/        # Scoring algorithms
│   │   ├── dcs.py      # Discourse Coherence Score
│   │   └── clustering.py # MST clustering
│   │
│   ├── models/         # ML model wrappers
│   │   ├── embeddings.py # Sentence-transformers
│   │   ├── llm.py        # LLM client
│   │   ├── ollama.py     # Ollama integration
│   │   └── coreference.py # spaCy coreference
│   │
│   ├── fallback/       # Degradation strategies
│   ├── chunker.py      # Main entry point
│   ├── cli.py          # Command-line interface
│   └── batch.py        # Batch processing
│
├── benchmarks/
│   ├── runner.py       # Benchmark orchestration
│   ├── metrics/        # Evaluation metrics
│   ├── baselines/      # Comparison methods
│   └── datasets/       # Data loaders
│
├── configs/
│   ├── default.yaml    # Default configuration
│   └── taxonomies/     # Domain taxonomies
│
└── tests/              # Unit and integration tests
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=cosmic --cov-report=html

# Run specific test module
pytest tests/unit/test_dcs.py -v
```

### Type Checking

```bash
mypy src/cosmic/
```

### Code Style

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
ruff check src/ tests/
```

## API Reference

### COSMICChunker

```python
class COSMICChunker:
    def __init__(
        self,
        config: Optional[COSMICConfig] = None,
        taxonomy_path: Optional[Path] = None,
    ) -> None: ...

    def chunk_document(
        self,
        document: Document,
        strategy: str = "auto",
    ) -> list[COSMICChunk]: ...
```

### COSMICChunk

```python
@dataclass(frozen=True)
class COSMICChunk:
    chunk_id: str
    text: str
    token_count: int
    char_start: int
    char_end: int
    sentence_indices: tuple[int, ...]
    domain: str
    coherence_score: float
    boundary_confidence: float
    cross_references: tuple[str, ...]
    intent: Intent
    metadata: dict
```

### Document

```python
class Document:
    @classmethod
    def from_text(
        cls,
        text: str,
        doc_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Document: ...

    @classmethod
    def from_file(cls, path: Path) -> Document: ...
```

## Citation

If you use COSMIC in your research, please cite:

```bibtex
@article{cosmic2026,
  title={COSMIC: COncept-aware Semantic Meta-chunking with Intelligent Classification},
  author={Al Kari, Manceps Research Division},
  journal={arXiv preprint},
  year={2026}
}
```

## License

Apache 2.0 License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Complete API reference and user guide
- [CLI.md](CLI.md) - Command-line interface reference
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing guidelines
- [SECURITY.md](SECURITY.md) - Security policy
- [paper/COSMIC_Research_Paper.md](paper/COSMIC_Research_Paper.md) - Research background

## Acknowledgments

COSMIC builds upon research in:
- Meta-Chunking (Yu et al., 2024)
- S² Chunking (Shi et al., 2024)
- Discourse Coherence Scoring (Ji et al., 2023)
