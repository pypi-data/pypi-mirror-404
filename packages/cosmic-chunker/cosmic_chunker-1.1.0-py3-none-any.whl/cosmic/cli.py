#!/usr/bin/env python3
"""Command-line interface for COSMIC chunker.

Usage:
    cosmic chunk FILE [--strategy STRATEGY] [--output OUTPUT]
    cosmic chunk FILE --config CONFIG_FILE
    cosmic chunk FILE --ollama [MODEL]  # Auto-manage Ollama for LLM verification
    cosmic version
    cosmic benchmark [--documents DIR]
    cosmic ollama list  # List available Ollama models
    cosmic ollama status  # Check Ollama status

Examples:
    cosmic chunk document.txt --strategy auto
    cosmic chunk document.txt --output chunks.json
    cosmic chunk document.txt --config custom.yaml
    cosmic chunk document.txt --strategy full --ollama auto
    cosmic chunk document.txt --strategy full --ollama gemma3:latest
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from cosmic import __version__
from cosmic.chunker import COSMICChunker
from cosmic.core.config import COSMICConfig
from cosmic.core.document import Document
from cosmic.models.ollama import OllamaManager


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def chunk_command(args: argparse.Namespace) -> int:
    """Process the chunk command."""
    # Load document
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    text = file_path.read_text(encoding="utf-8")
    doc = Document.from_text(text, doc_id=file_path.stem)

    # Load configuration
    if args.config:
        config = COSMICConfig.from_yaml(Path(args.config))
    else:
        config = COSMICConfig()

    # Apply CLI overrides
    if hasattr(args, "no_llm") and args.no_llm:
        config.llm.enabled = False
    if hasattr(args, "no_reference") and args.no_reference:
        config.reference.enabled = False

    # Handle Ollama integration
    ollama_manager: Optional[OllamaManager] = None
    ollama_started = False

    if hasattr(args, "ollama") and args.ollama:
        ollama_manager = OllamaManager()

        if not ollama_manager.is_installed():
            print("Error: Ollama is not installed", file=sys.stderr)
            print("Install from: https://ollama.com/download", file=sys.stderr)
            return 1

        if not ollama_manager.is_available():
            print("Error: No Ollama models available", file=sys.stderr)
            print("Pull a model with: ollama pull gemma3", file=sys.stderr)
            return 1

        # Select model
        if args.ollama == "auto":
            model = ollama_manager.auto_select_model()
            if not model:
                print("Error: Could not auto-select Ollama model", file=sys.stderr)
                return 1
            print(f"Auto-selected Ollama model: {model}")
        else:
            model = args.ollama
            # Verify model exists
            available = [m.name for m in ollama_manager.list_models()]
            if model not in available:
                # Try with :latest suffix
                if f"{model}:latest" in available:
                    model = f"{model}:latest"
                else:
                    print(f"Error: Model '{model}' not found", file=sys.stderr)
                    print(f"Available models: {', '.join(available)}", file=sys.stderr)
                    return 1

        # Start Ollama if needed
        ollama_started = ollama_manager.ensure_running()
        if ollama_started:
            print("Started Ollama server")

        if not ollama_manager.is_running():
            print("Error: Failed to start Ollama server", file=sys.stderr)
            return 1

        # Configure LLM settings for Ollama
        config.llm.enabled = True
        config.llm.base_url = ollama_manager.api_base_url
        config.llm.model_name = model
        config.llm.api_key = ""  # Ollama doesn't need API key
        print(f"Using Ollama model: {model}")

    try:
        # Create chunker and process
        chunker = COSMICChunker(config)
        chunks = chunker.chunk_document(doc, strategy=args.strategy)

        # Output results
        output_data = {
            "document_id": doc.id,
            "source_file": str(file_path),
            "strategy": args.strategy,
            "num_chunks": len(chunks),
            "chunks": [chunk.to_dict() for chunk in chunks],
        }

        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"Wrote {len(chunks)} chunks to {output_path}")
        else:
            # Print summary to stdout
            print(f"Document: {doc.id}")
            print(f"Strategy: {args.strategy}")
            print(f"Chunks: {len(chunks)}")
            print()
            for i, chunk in enumerate(chunks):
                print(f"--- Chunk {i} ---")
                print(f"  Tokens: {chunk.token_count}")
                print(f"  Coherence: {chunk.coherence_score:.3f}")
                print(f"  Domain: {chunk.domain}")
                print(f"  Mode: {chunk.processing_mode.name}")
                preview = chunk.text[:100].replace("\n", " ")
                print(f"  Preview: {preview}...")
                print()

        return 0

    finally:
        # Stop Ollama if we started it
        if ollama_manager and ollama_started:
            ollama_manager.stop()
            print("Stopped Ollama server")


def version_command(args: argparse.Namespace) -> int:
    """Print version information."""
    print(f"COSMIC v{__version__}")
    print("COncept-aware Semantic Meta-chunking with Intelligent Classification")
    return 0


def benchmark_command(args: argparse.Namespace) -> int:
    """Run benchmark suite."""
    print("Running COSMIC benchmark...")
    print("(Use benchmarks/run_validation.py for full benchmark)")

    # Quick sanity check
    from cosmic.chunker import COSMICChunker
    from cosmic.core.document import Document

    config = COSMICConfig()
    config.llm.enabled = False
    config.reference.enabled = False
    config.embedding.device = "cpu"

    chunker = COSMICChunker(config)
    doc = Document.from_text(
        "Machine learning is a branch of AI. It enables computers to learn from data. "
        "Neural networks are key techniques. Deep learning uses many layers."
    )

    chunks = chunker.chunk_document(doc, strategy="auto")
    print(f"Quick test: {len(chunks)} chunks created")

    return 0


def ollama_command(args: argparse.Namespace) -> int:
    """Handle Ollama-related commands."""
    manager = OllamaManager()

    if args.ollama_action == "list":
        if not manager.is_installed():
            print("Ollama is not installed")
            print("Install from: https://ollama.com/download")
            return 1

        models = manager.list_models()
        if not models:
            print("No Ollama models found")
            print("Pull a model with: ollama pull gemma3")
            return 0

        print("Available Ollama models:")
        print(f"{'NAME':<40} {'SIZE':<10}")
        print("-" * 50)
        for model in models:
            print(f"{model.name:<40} {model.size_gb:.1f} GB")

        # Show recommended model
        recommended = manager.auto_select_model()
        if recommended:
            print(f"\nRecommended for COSMIC: {recommended}")

        return 0

    elif args.ollama_action == "status":
        print("Ollama Status:")
        print(f"  Installed: {'Yes' if manager.is_installed() else 'No'}")
        print(f"  Running: {'Yes' if manager.is_running() else 'No'}")

        if manager.is_installed():
            models = manager.list_models()
            print(f"  Models available: {len(models)}")

            if models:
                recommended = manager.auto_select_model()
                print(f"  Recommended model: {recommended}")

        return 0

    elif args.ollama_action == "start":
        if not manager.is_installed():
            print("Error: Ollama is not installed", file=sys.stderr)
            return 1

        if manager.is_running():
            print("Ollama server is already running")
            return 0

        if manager.start():
            print("Ollama server started")
            return 0
        else:
            print("Failed to start Ollama server", file=sys.stderr)
            return 1

    elif args.ollama_action == "stop":
        # Note: We can only stop servers we started
        print("Note: Use 'ollama stop' or 'pkill ollama' to stop the server")
        return 0

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="cosmic",
        description="COSMIC: Concept-aware Semantic Meta-chunking with Intelligent Classification",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Chunk command
    chunk_parser = subparsers.add_parser("chunk", help="Chunk a document")
    chunk_parser.add_argument("file", help="Input file to chunk")
    chunk_parser.add_argument(
        "-s",
        "--strategy",
        choices=["auto", "full", "semantic", "sliding", "fixed"],
        default="auto",
        help="Chunking strategy (default: auto)",
    )
    chunk_parser.add_argument(
        "-o",
        "--output",
        help="Output JSON file for chunks",
    )
    chunk_parser.add_argument(
        "-c",
        "--config",
        help="Configuration YAML file",
    )
    chunk_parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM verification",
    )
    chunk_parser.add_argument(
        "--no-reference",
        action="store_true",
        help="Disable reference linking",
    )
    chunk_parser.add_argument(
        "--ollama",
        nargs="?",
        const="auto",
        metavar="MODEL",
        help="Use Ollama for LLM verification. Specify model name or 'auto' for auto-selection. "
        "Ollama server will be started if not running and stopped when done.",
    )

    # Version command
    subparsers.add_parser("version", help="Show version information")

    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run benchmarks")
    benchmark_parser.add_argument(
        "-d",
        "--documents",
        help="Directory containing documents to benchmark",
    )

    # Ollama command
    ollama_parser = subparsers.add_parser("ollama", help="Ollama management commands")
    ollama_subparsers = ollama_parser.add_subparsers(dest="ollama_action", help="Ollama actions")
    ollama_subparsers.add_parser("list", help="List available Ollama models")
    ollama_subparsers.add_parser("status", help="Show Ollama status")
    ollama_subparsers.add_parser("start", help="Start Ollama server")
    ollama_subparsers.add_parser("stop", help="Stop Ollama server")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    if args.command == "chunk":
        return chunk_command(args)
    elif args.command == "version":
        return version_command(args)
    elif args.command == "benchmark":
        return benchmark_command(args)
    elif args.command == "ollama":
        if not args.ollama_action:
            # Default to status if no action specified
            args.ollama_action = "status"
        return ollama_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
