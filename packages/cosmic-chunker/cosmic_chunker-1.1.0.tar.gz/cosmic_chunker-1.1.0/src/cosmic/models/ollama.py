"""Ollama integration for COSMIC LLM verification.

Provides auto-detection, model selection, and lifecycle management for Ollama.
"""

import logging
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Ollama API base URL
OLLAMA_DEFAULT_HOST = "http://localhost:11434"
OLLAMA_API_ENDPOINT = f"{OLLAMA_DEFAULT_HOST}/v1"

# Model selection preferences (smaller/faster first)
MODEL_PREFERENCES = [
    "gemma3",
    "gemma2",
    "qwen2.5-coder:7b",
    "qwen2.5-coder",
    "llama3.2",
    "llama3.1",
    "mistral",
    "deepseek-coder-v2",
    "qwen3:30b",
    "llama4",
]


@dataclass
class OllamaModel:
    """Information about an available Ollama model."""

    name: str
    size_bytes: int
    modified: str

    @property
    def size_gb(self) -> float:
        """Model size in gigabytes."""
        return self.size_bytes / (1024**3)


class OllamaManager:
    """Manages Ollama server lifecycle and model selection.

    Provides functionality to:
    - Detect if Ollama is installed and running
    - List available models
    - Auto-select the best model for verification tasks
    - Start/stop the Ollama server

    Example:
        manager = OllamaManager()

        if manager.is_available():
            models = manager.list_models()
            model = manager.auto_select_model()

            # Start if needed
            started = manager.ensure_running()

            # ... use Ollama ...

            # Stop if we started it
            if started:
                manager.stop()
    """

    def __init__(self, host: str = OLLAMA_DEFAULT_HOST):
        """Initialize Ollama manager.

        Args:
            host: Ollama server host URL
        """
        self.host = host
        self._started_by_us = False
        self._process: Optional[subprocess.Popen] = None

    @property
    def api_base_url(self) -> str:
        """OpenAI-compatible API base URL."""
        return f"{self.host}/v1"

    def is_installed(self) -> bool:
        """Check if Ollama CLI is installed."""
        return shutil.which("ollama") is not None

    def is_running(self) -> bool:
        """Check if Ollama server is running and responsive."""
        try:
            response = httpx.get(f"{self.host}/api/tags", timeout=5.0)
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def is_available(self) -> bool:
        """Check if Ollama is installed and has models available."""
        if not self.is_installed():
            return False

        # Try to list models (works even if server isn't running)
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Check if there are any models (more than just the header line)
            lines = result.stdout.strip().split("\n")
            return len(lines) > 1
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def list_models(self) -> list[OllamaModel]:
        """List available Ollama models.

        Returns:
            List of OllamaModel objects
        """
        models: list[OllamaModel] = []

        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.warning(f"Failed to list Ollama models: {result.stderr}")
                return models

            lines = result.stdout.strip().split("\n")

            # Skip header line
            for line in lines[1:]:
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0]
                    # Parse size (e.g., "3.3 GB" -> bytes)
                    size_str = parts[2] if len(parts) >= 3 else "0"
                    unit = parts[3] if len(parts) >= 4 else "B"

                    try:
                        size = float(size_str)
                        if unit == "GB":
                            size *= 1024**3
                        elif unit == "MB":
                            size *= 1024**2
                        elif unit == "KB":
                            size *= 1024
                    except ValueError:
                        size = 0

                    modified = " ".join(parts[4:]) if len(parts) > 4 else ""

                    models.append(
                        OllamaModel(
                            name=name,
                            size_bytes=int(size),
                            modified=modified,
                        )
                    )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Failed to list Ollama models: {e}")

        return models

    def auto_select_model(self, prefer_small: bool = True) -> Optional[str]:
        """Auto-select the best available model.

        Args:
            prefer_small: If True, prefer smaller/faster models

        Returns:
            Model name or None if no models available
        """
        models = self.list_models()

        if not models:
            return None

        model_names = [m.name for m in models]

        # Try preferred models in order
        for preferred in MODEL_PREFERENCES:
            for model_name in model_names:
                # Match by prefix (e.g., "gemma3" matches "gemma3:latest")
                if model_name.startswith(preferred):
                    logger.info(f"Auto-selected Ollama model: {model_name}")
                    return model_name

        # Fall back to smallest model if prefer_small
        if prefer_small:
            models_sorted = sorted(models, key=lambda m: m.size_bytes)
            selected = models_sorted[0].name
        else:
            # Otherwise use first available
            selected = models[0].name

        logger.info(f"Auto-selected Ollama model (fallback): {selected}")
        return selected

    def start(self, timeout: float = 30.0) -> bool:
        """Start Ollama server.

        Args:
            timeout: Maximum time to wait for server to start

        Returns:
            True if server started successfully
        """
        if self.is_running():
            logger.info("Ollama server already running")
            return True

        if not self.is_installed():
            logger.error("Ollama is not installed")
            return False

        logger.info("Starting Ollama server...")

        try:
            # Start ollama serve in background
            self._process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Wait for server to become responsive
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.is_running():
                    self._started_by_us = True
                    logger.info("Ollama server started successfully")
                    return True
                time.sleep(0.5)

            logger.error("Ollama server failed to start within timeout")
            self.stop()
            return False

        except (FileNotFoundError, OSError) as e:
            logger.error(f"Failed to start Ollama server: {e}")
            return False

    def stop(self) -> bool:
        """Stop Ollama server if we started it.

        Returns:
            True if server was stopped
        """
        if not self._started_by_us:
            logger.debug("Ollama server was not started by us, not stopping")
            return False

        if self._process is not None:
            logger.info("Stopping Ollama server...")
            try:
                self._process.terminate()
                self._process.wait(timeout=10)
                self._process = None
                self._started_by_us = False
                logger.info("Ollama server stopped")
                return True
            except subprocess.TimeoutExpired:
                if self._process is not None:
                    self._process.kill()
                self._process = None
                self._started_by_us = False
                return True

        return False

    def ensure_running(self) -> bool:
        """Ensure Ollama server is running, starting it if needed.

        Returns:
            True if server was started by this call (caller should stop it later)
        """
        if self.is_running():
            return False

        if self.start():
            return True

        return False

    def __enter__(self) -> "OllamaManager":
        """Context manager entry."""
        self.ensure_running()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Context manager exit - stop server if we started it."""
        self.stop()


def detect_ollama() -> Optional[OllamaManager]:
    """Detect and return an OllamaManager if Ollama is available.

    Returns:
        OllamaManager instance or None if Ollama is not available
    """
    manager = OllamaManager()

    if manager.is_available():
        return manager

    return None
