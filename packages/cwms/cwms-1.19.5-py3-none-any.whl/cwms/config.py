"""Configuration management for context_cache."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from cwms.constants import DEFAULT_SWAP_TRIGGER_PERCENT


@dataclass
class Config:
    """Configuration for context_cache context management.

    Context threshold can be configured via:
    1. CWMS_THRESHOLD environment variable (highest priority)
    2. threshold_tokens in config file (can be int or "auto")
    3. Default value (32000 tokens)

    When threshold_tokens is "auto" or not set, the system auto-detects
    the optimal threshold based on the Claude model being used.
    """

    # Context thresholds
    # Note: threshold_tokens can be overridden via CWMS_THRESHOLD env var
    threshold_tokens: int = 32000
    swap_trigger_percent: float = DEFAULT_SWAP_TRIGGER_PERCENT
    preserve_recent_tokens: int = 8000  # Always keep recent context

    # Whether threshold was set to "auto" (for auto-detection)
    _threshold_auto: bool = field(default=False, repr=False)

    # Chunking
    chunk_size: int = 2000
    chunk_overlap: int = 200

    # Storage
    storage_dir: Path = field(default_factory=lambda: Path("~/.claude/cwms").expanduser())
    max_age_days: int = 30  # 0 = never expire

    # Embeddings
    embedding_provider: str = "none"  # none | local
    local_model: str = "all-MiniLM-L6-v2"

    # Retrieval
    retrieval_top_k: int = 5
    retrieval_min_similarity: float = 0.7
    recency_boost: float = 0.1

    # BM25 parameters (for keyword search)
    bm25_k1: float = 1.2  # Term frequency saturation (1.2-2.0 typical)
    bm25_b: float = 0.75  # Document length normalization (0-1)

    # Hybrid search parameters
    search_mode: str = "auto"  # auto | keyword | semantic | hybrid
    hybrid_keyword_weight: float = 0.3  # Weight for BM25 keyword score
    hybrid_semantic_weight: float = 0.7  # Weight for semantic similarity score

    # ANN (Approximate Nearest Neighbors) parameters
    ann_enabled: bool = True  # Use ANN index when available
    ann_threshold: int = 100  # Minimum chunks before enabling ANN index

    # Summarizer parameters (regex-based)
    summarizer_max_length: int = 1000  # Maximum summary length in characters
    summarizer_include_code_context: bool = True  # Include code block descriptions
    summarizer_extract_questions: bool = True  # Extract user questions/requests
    summarizer_min_keyword_length: int = 3  # Minimum keyword length

    # Summarization API parameters (Phase 2)
    summarization_provider: str = "regex"  # regex | api
    summarization_api_model: str = "claude-opus-4-5-20251101"  # Model for API summarization
    summarization_api_max_tokens: int = 500  # Max tokens for API response
    summarization_monthly_cost_limit_usd: float | None = None  # Monthly cost limit

    @property
    def vector_store_dir(self) -> Path:
        """Get the directory for ChromaDB vector store persistence.

        Returns:
            Path to ChromaDB persist directory (storage_dir/chroma)
        """
        return self.storage_dir / "chroma"

    @property
    def uses_vector_store(self) -> bool:
        """Check if vector store is enabled.

        Returns:
            True if embedding_provider is 'local' (uses ChromaDB)
        """
        return self.embedding_provider.lower() == "local"

    @classmethod
    def from_yaml(cls, path: Path | str) -> Config:
        """Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            Config instance with loaded settings

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is malformed
        """
        path = Path(path).expanduser()

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return cls()

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create Config from nested dictionary structure.

        Args:
            data: Nested dictionary with config sections

        Returns:
            Config instance
        """
        # Flatten nested config structure
        flat_config: dict[str, Any] = {}
        threshold_auto = False

        # Context section
        if "context" in data:
            ctx = data["context"]

            # Handle threshold_tokens which can be int or "auto"
            threshold_value = ctx.get("threshold_tokens", 32000)
            if isinstance(threshold_value, str) and threshold_value.lower() == "auto":
                threshold_auto = True
                # Will be resolved later by apply_model_settings()
                threshold_value = 32000  # Temporary default

            flat_config.update(
                {
                    "threshold_tokens": threshold_value,
                    "swap_trigger_percent": ctx.get(
                        "swap_trigger_percent", DEFAULT_SWAP_TRIGGER_PERCENT
                    ),
                    "preserve_recent_tokens": ctx.get("preserve_recent_tokens", 8000),
                    "chunk_size": ctx.get("chunk_size", 2000),
                    "chunk_overlap": ctx.get("chunk_overlap", 200),
                }
            )

        # Storage section
        if "storage" in data:
            storage = data["storage"]
            storage_dir = storage.get("directory", "~/.claude/cwms")
            flat_config.update(
                {
                    "storage_dir": Path(storage_dir).expanduser(),
                    "max_age_days": storage.get("max_age_days", 30),
                }
            )

        # Embeddings section
        if "embeddings" in data:
            emb = data["embeddings"]
            flat_config.update(
                {
                    "embedding_provider": emb.get("provider", "none"),
                    "local_model": emb.get("local_model", "all-MiniLM-L6-v2"),
                }
            )

        # Retrieval section
        if "retrieval" in data:
            ret = data["retrieval"]
            flat_config.update(
                {
                    "retrieval_top_k": ret.get("top_k", 5),
                    "retrieval_min_similarity": ret.get("min_similarity", 0.7),
                    "recency_boost": ret.get("recency_boost", 0.1),
                    "bm25_k1": ret.get("bm25_k1", 1.2),
                    "bm25_b": ret.get("bm25_b", 0.75),
                    "search_mode": ret.get("search_mode", "auto"),
                    "hybrid_keyword_weight": ret.get("hybrid_keyword_weight", 0.3),
                    "hybrid_semantic_weight": ret.get("hybrid_semantic_weight", 0.7),
                    "ann_enabled": ret.get("ann_enabled", True),
                    "ann_threshold": ret.get("ann_threshold", 100),
                }
            )

        # Summarizer section (regex-based parameters)
        if "summarizer" in data:
            summ = data["summarizer"]
            flat_config.update(
                {
                    "summarizer_max_length": summ.get("max_length", 1000),
                    "summarizer_include_code_context": summ.get("include_code_context", True),
                    "summarizer_extract_questions": summ.get("extract_questions", True),
                    "summarizer_min_keyword_length": summ.get("min_keyword_length", 3),
                }
            )

        # Summarization section (Phase 2: API summarization)
        if "summarization" in data:
            sumz = data["summarization"]
            flat_config.update(
                {
                    "summarization_provider": sumz.get("provider", "regex"),
                    "summarization_api_model": sumz.get("api_model", "claude-opus-4-5-20251101"),
                    "summarization_api_max_tokens": sumz.get("api_max_tokens", 500),
                    "summarization_monthly_cost_limit_usd": sumz.get("monthly_cost_limit_usd"),
                }
            )

        config = cls(**flat_config)
        config._threshold_auto = threshold_auto
        return config

    def to_dict(self) -> dict[str, Any]:
        """Export config as nested dictionary.

        Returns:
            Nested dictionary matching YAML structure
        """
        # Export "auto" if threshold was set to auto-detect
        threshold_value: int | str = "auto" if self._threshold_auto else self.threshold_tokens

        return {
            "context": {
                "threshold_tokens": threshold_value,
                "swap_trigger_percent": self.swap_trigger_percent,
                "preserve_recent_tokens": self.preserve_recent_tokens,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
            },
            "storage": {
                "directory": str(self.storage_dir),
                "max_age_days": self.max_age_days,
            },
            "embeddings": {
                "provider": self.embedding_provider,
                "local_model": self.local_model,
            },
            "retrieval": {
                "top_k": self.retrieval_top_k,
                "min_similarity": self.retrieval_min_similarity,
                "recency_boost": self.recency_boost,
                "bm25_k1": self.bm25_k1,
                "bm25_b": self.bm25_b,
                "search_mode": self.search_mode,
                "hybrid_keyword_weight": self.hybrid_keyword_weight,
                "hybrid_semantic_weight": self.hybrid_semantic_weight,
                "ann_enabled": self.ann_enabled,
                "ann_threshold": self.ann_threshold,
            },
            "summarizer": {
                "max_length": self.summarizer_max_length,
                "include_code_context": self.summarizer_include_code_context,
                "extract_questions": self.summarizer_extract_questions,
                "min_keyword_length": self.summarizer_min_keyword_length,
            },
            "summarization": {
                "provider": self.summarization_provider,
                "api_model": self.summarization_api_model,
                "api_max_tokens": self.summarization_api_max_tokens,
                "monthly_cost_limit_usd": self.summarization_monthly_cost_limit_usd,
            },
        }

    def save_yaml(self, path: Path | str) -> None:
        """Save configuration to YAML file.

        Args:
            path: Path to save YAML configuration
        """
        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

    @classmethod
    def load_or_default(cls, path: Path | str | None = None) -> Config:
        """Load config from file or return default if not found.

        Args:
            path: Optional path to config file. If None, looks in standard locations.

        Returns:
            Config instance
        """
        if path:
            try:
                return cls.from_yaml(path)
            except FileNotFoundError:
                return cls()

        # Try standard locations
        # Project-specific first, then user-level
        standard_paths = [
            Path(".claude/cwms/config.yaml"),
            Path("~/.claude/cwms/config.yaml").expanduser(),
        ]

        for std_path in standard_paths:
            if std_path.exists():
                return cls.from_yaml(std_path)

        return cls()

    def apply_environment_overrides(self) -> Config:
        """Apply environment variable overrides to config.

        Environment variables take precedence over config file values.
        Supports:
        - CWMS_THRESHOLD: Override threshold_tokens (int or "auto")
        - CWMS_PRESERVE_RECENT: Override preserve_recent_tokens

        Returns:
            Self for chaining
        """
        # Import here to avoid circular imports
        from cwms.model_config import (
            get_preserve_recent_from_environment,
            get_threshold_from_environment,
        )

        # Check for threshold override
        env_threshold = get_threshold_from_environment()
        if env_threshold is not None:
            self.threshold_tokens = env_threshold
            self._threshold_auto = False  # Explicit value overrides auto

        # Check for preserve_recent override
        env_preserve = get_preserve_recent_from_environment()
        if env_preserve is not None:
            self.preserve_recent_tokens = env_preserve

        # Check if CWMS_THRESHOLD is set to "auto"
        threshold_str = os.environ.get("CWMS_THRESHOLD", "").lower()
        if threshold_str == "auto":
            self._threshold_auto = True

        return self

    def apply_model_settings(self, model_name: str | None = None) -> Config:
        """Apply model-aware settings if threshold is set to auto.

        This method should be called after loading config to resolve
        "auto" threshold values based on the detected or specified model.

        Args:
            model_name: Optional model name. If None, attempts auto-detection.

        Returns:
            Self for chaining
        """
        # Import here to avoid circular imports
        from cwms.model_config import get_model_context_config

        # Only apply auto-detection if threshold is set to "auto"
        # or if environment variable says "auto"
        threshold_str = os.environ.get("CWMS_THRESHOLD", "").lower()
        should_auto = self._threshold_auto or threshold_str == "auto"

        if should_auto:
            model_config = get_model_context_config(
                model_name=model_name,
                threshold_override="auto",
                swap_trigger_percent=self.swap_trigger_percent,
            )
            self.threshold_tokens = model_config.threshold_tokens
            self.preserve_recent_tokens = model_config.preserve_recent_tokens

        return self

    def with_model_adaptation(self, model_name: str | None = None) -> Config:
        """Apply both environment overrides and model settings.

        Convenience method that applies both environment overrides and
        model-aware settings in the correct order.

        Args:
            model_name: Optional model name for auto-detection

        Returns:
            Self for chaining
        """
        return self.apply_environment_overrides().apply_model_settings(model_name)

    @property
    def is_threshold_auto(self) -> bool:
        """Check if threshold is set to auto-detect mode.

        Returns:
            True if threshold should be auto-detected from model
        """
        threshold_str = os.environ.get("CWMS_THRESHOLD", "").lower()
        return self._threshold_auto or threshold_str == "auto"
