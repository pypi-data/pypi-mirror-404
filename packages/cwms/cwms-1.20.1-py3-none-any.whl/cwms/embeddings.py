"""Embedding providers for semantic search."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Protocol

from cwms.metrics import MetricsCollector, get_metrics
from cwms.retry import (
    PermanentError,
    TransientError,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers.

    All embedding providers must implement this interface to generate
    vector embeddings from text for semantic search.
    """

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (one per input text)
        """
        ...  # pylint: disable=unnecessary-ellipsis


class NoEmbeddings:
    """Fallback provider that returns empty embeddings.

    Used when no embedding provider is configured. The retriever will
    automatically fall back to keyword-based search when embeddings are empty.
    """

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return empty embeddings for all texts.

        Args:
            texts: List of text strings (ignored)

        Returns:
            List of empty lists, one per input text
        """
        return [[] for _ in texts]


class LocalEmbeddings:
    """Local embeddings using sentence-transformers.

    Uses the sentence-transformers library to generate embeddings locally
    without requiring API calls. Supports offline usage.

    Default model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
    Other options: all-mpnet-base-v2 (768 dimensions, higher quality, slower)
    """

    def __init__(self, model: str = "all-MiniLM-L6-v2") -> None:
        """Initialize local embeddings with specified model.

        Args:
            model: Name of sentence-transformers model to use

        Raises:
            ImportError: If sentence-transformers is not installed
            PermanentError: If model cannot be loaded
        """
        try:
            # pylint: disable=import-outside-toplevel
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is required for local embeddings. "
                "Install with: pip install 'cwms[local]' or "
                "pip install sentence-transformers torch"
            ) from e

        try:
            self.model = SentenceTransformer(model)
        except Exception as e:
            raise PermanentError(
                f"Failed to load sentence-transformers model '{model}': {e}. "
                "Ensure the model name is correct and you have an internet "
                "connection for first-time model downloads.",
                original_error=e,
            ) from e

        self.model_name = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using local model.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors as nested lists

        Raises:
            TransientError: If encoding fails (e.g., memory issues)
        """
        if not texts:
            return []

        metrics = get_metrics()
        start_time = time.perf_counter()

        logger.debug(
            "Generating local embeddings for %d texts with model '%s'", len(texts), self.model_name
        )

        try:
            # Convert numpy arrays to lists for JSON serialization
            embeddings = self.model.encode(texts, show_progress_bar=False)
            result: list[list[float]] = embeddings.tolist()

            duration_ms = (time.perf_counter() - start_time) * 1000
            with metrics.measure(
                MetricsCollector.EMBED_BATCH,
                provider="local",
                model=self.model_name,
                text_count=len(texts),
            ) as ctx:
                ctx["duration_ms"] = duration_ms

            logger.info("Generated %d local embeddings in %.2fms", len(texts), duration_ms)
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Local embedding failed after %.2fms: %s", duration_ms, str(e))

            # Local encoding failures are usually not retryable (memory, etc.)
            # but we wrap them for consistent error handling
            error_str = str(e).lower()
            if "memory" in error_str or "cuda" in error_str:
                raise TransientError(
                    f"Local embedding failed (resource issue): {e}",
                    original_error=e,
                ) from e
            raise PermanentError(
                f"Local embedding failed: {e}",
                original_error=e,
            ) from e


def get_embedding_provider(
    provider: str,
    model: str | None = None,
) -> EmbeddingProvider:
    """Factory function to create embedding provider instances.

    Args:
        provider: Provider name ("none" or "local")
        model: Optional model name override

    Returns:
        EmbeddingProvider instance

    Raises:
        ValueError: If provider is unknown
        ImportError: If required dependencies are not installed

    Examples:
        >>> provider = get_embedding_provider("local")
        >>> provider = get_embedding_provider("local", "all-mpnet-base-v2")
        >>> provider = get_embedding_provider("none")  # Keyword search only
    """
    provider = provider.lower()

    if provider == "none":
        return NoEmbeddings()
    if provider == "local":
        return LocalEmbeddings(model) if model else LocalEmbeddings()

    raise ValueError(f"Unknown embedding provider: {provider}. Valid options: none, local")
