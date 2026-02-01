"""Model-specific configuration for context window adaptation.

This module provides model detection and configuration for adapting context
window settings based on the Claude model being used. It enables:

1. Auto-detection of context window size based on model name
2. Model-aware swap strategies (adjusting preserve_recent_tokens)
3. Environment variable overrides for threshold settings
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cwms.constants import (
    DEFAULT_SWAP_TRIGGER_PERCENT,
    OPTIMAL_THRESHOLD_PERCENT_LARGE,
    OPTIMAL_THRESHOLD_PERCENT_MEDIUM,
    OPTIMAL_THRESHOLD_PERCENT_SMALL,
)

if TYPE_CHECKING:
    from cwms.config import Config


# Known Claude models and their context window sizes (in tokens)
# Reference: https://docs.anthropic.com/claude/docs/models-overview
MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    # Claude 4 / Opus 4.5 models (200k context)
    "claude-opus-4-5": 200000,
    "claude-opus-4-5-20251101": 200000,
    "opus-4-5": 200000,
    "opus": 200000,  # Default to latest opus
    # Claude 4 / Sonnet 4 models (200k context)
    "claude-sonnet-4": 200000,
    "claude-sonnet-4-20250514": 200000,
    "sonnet-4": 200000,
    "sonnet": 200000,  # Default to latest sonnet
    # Claude 3.5 models (200k context)
    "claude-3-5-sonnet": 200000,
    "claude-3-5-sonnet-20241022": 200000,
    "claude-3-5-haiku": 200000,
    "claude-3-5-haiku-20241022": 200000,
    # Claude 3 models
    "claude-3-opus": 200000,
    "claude-3-opus-20240229": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-sonnet-20240229": 200000,
    "claude-3-haiku": 200000,
    "claude-3-haiku-20240307": 200000,
    # Claude 2 models (100k context)
    "claude-2.1": 100000,
    "claude-2.0": 100000,
    "claude-2": 100000,
    # Claude Instant (100k context)
    "claude-instant-1.2": 100000,
    "claude-instant": 100000,
}

# Default context window if model is unknown
DEFAULT_CONTEXT_WINDOW = 200000

# Optimal working threshold as percentage of context window
# Research shows LLM performance degrades significantly after ~33k tokens
# For larger context windows, we use a lower percentage
OPTIMAL_THRESHOLD_PERCENT: dict[str, float] = {
    "small": OPTIMAL_THRESHOLD_PERCENT_SMALL,
    "medium": OPTIMAL_THRESHOLD_PERCENT_MEDIUM,
    "large": OPTIMAL_THRESHOLD_PERCENT_LARGE,
}

# Preserve recent tokens as percentage of threshold
# Larger context windows can preserve more recent context
PRESERVE_RECENT_PERCENT: dict[str, float] = {
    "small": 0.25,  # 25% of threshold for small windows
    "medium": 0.20,  # 20% of threshold for medium windows
    "large": 0.15,  # 15% of threshold for large windows
}


@dataclass
class ModelContextConfig:
    """Configuration derived from model detection.

    Attributes:
        model_name: Detected or specified model name
        context_window: Total context window size in tokens
        threshold_tokens: Optimal threshold for triggering swap
        swap_trigger_percent: Percentage of threshold to trigger swap
        preserve_recent_tokens: Number of recent tokens to preserve
        detected: Whether the model was auto-detected vs specified
    """

    model_name: str | None
    context_window: int
    threshold_tokens: int
    swap_trigger_percent: float
    preserve_recent_tokens: int
    detected: bool


def get_context_window_size(model_name: str | None) -> int:
    """Get context window size for a model.

    Args:
        model_name: Claude model name or identifier

    Returns:
        Context window size in tokens
    """
    if not model_name:
        return DEFAULT_CONTEXT_WINDOW

    # Normalize model name for lookup
    normalized = model_name.lower().strip()

    # Direct lookup
    if normalized in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[normalized]

    # Partial matching for model families
    for key, window_size in MODEL_CONTEXT_WINDOWS.items():
        if key in normalized or normalized in key:
            return window_size

    # Try to extract model family from name
    if "opus" in normalized:
        return 200000
    if "sonnet" in normalized:
        return 200000
    if "haiku" in normalized:
        return 200000
    if "claude-3" in normalized:
        return 200000
    if "claude-2" in normalized:
        return 100000

    return DEFAULT_CONTEXT_WINDOW


def get_window_size_category(context_window: int) -> str:
    """Categorize context window size.

    Args:
        context_window: Context window size in tokens

    Returns:
        Size category: 'small', 'medium', or 'large'
    """
    if context_window < 50000:
        return "small"
    elif context_window <= 100000:
        return "medium"
    else:
        return "large"


def calculate_optimal_threshold(context_window: int) -> int:
    """Calculate optimal threshold for a given context window.

    Uses research-based percentages that account for LLM performance
    degradation at higher token counts.

    Args:
        context_window: Total context window size in tokens

    Returns:
        Optimal threshold in tokens
    """
    category = get_window_size_category(context_window)
    percent = OPTIMAL_THRESHOLD_PERCENT[category]

    # Cap the threshold at reasonable values based on research
    # Even with 200k context, swapping around 40-50k is optimal
    raw_threshold = int(context_window * percent)

    # Apply reasonable caps
    max_thresholds = {
        "small": 40000,
        "medium": 50000,
        "large": 64000,  # Max practical threshold
    }

    return min(raw_threshold, max_thresholds[category])


def calculate_preserve_recent(threshold_tokens: int, context_window: int) -> int:
    """Calculate optimal preserve_recent_tokens value.

    Larger context windows can preserve more recent context while
    still leaving room for swapped content retrieval.

    Args:
        threshold_tokens: The swap threshold in tokens
        context_window: Total context window size

    Returns:
        Number of recent tokens to preserve during swap
    """
    category = get_window_size_category(context_window)
    percent = PRESERVE_RECENT_PERCENT[category]

    preserve = int(threshold_tokens * percent)

    # Ensure minimum preservation
    min_preserve = 4000
    max_preserve = 16000

    return max(min_preserve, min(preserve, max_preserve))


def detect_model_from_environment() -> str | None:
    """Attempt to detect the Claude model from environment.

    Checks various environment variables that might indicate the model.

    Returns:
        Model name if detected, None otherwise
    """
    # Check common environment variables
    env_vars = [
        "CLAUDE_MODEL",
        "ANTHROPIC_MODEL",
        "CLAUDE_CODE_MODEL",
        "MODEL",
    ]

    for var in env_vars:
        model = os.environ.get(var)
        if model:
            return model

    return None


def get_threshold_from_environment() -> int | None:
    """Get threshold override from environment variable.

    Returns:
        Threshold in tokens if set, None otherwise
    """
    threshold_str = os.environ.get("CWMS_THRESHOLD")
    if not threshold_str:
        return None

    # Handle "auto" value
    if threshold_str.lower() == "auto":
        return None  # Signal to use auto-detection

    # Parse numeric value
    try:
        # Handle values with 'k' suffix (e.g., "32k", "64K")
        if threshold_str.lower().endswith("k"):
            return int(float(threshold_str[:-1]) * 1000)
        return int(threshold_str)
    except ValueError:
        return None


def get_preserve_recent_from_environment() -> int | None:
    """Get preserve_recent_tokens override from environment variable.

    Returns:
        Preserve recent tokens value if set, None otherwise
    """
    preserve_str = os.environ.get("CWMS_PRESERVE_RECENT")
    if not preserve_str:
        return None

    try:
        if preserve_str.lower().endswith("k"):
            return int(float(preserve_str[:-1]) * 1000)
        return int(preserve_str)
    except ValueError:
        return None


def get_model_context_config(
    model_name: str | None = None,
    threshold_override: int | str | None = None,
    preserve_recent_override: int | None = None,
    swap_trigger_percent: float = DEFAULT_SWAP_TRIGGER_PERCENT,
) -> ModelContextConfig:
    """Get full context configuration for a model.

    Combines model detection, environment variables, and overrides
    to produce the final context configuration.

    Args:
        model_name: Optional model name (auto-detects if None)
        threshold_override: Optional threshold override (int or "auto")
        preserve_recent_override: Optional preserve_recent override
        swap_trigger_percent: Percentage of threshold to trigger swap

    Returns:
        ModelContextConfig with all calculated values
    """
    # Detect model if not specified
    detected_model = model_name or detect_model_from_environment()
    detected = model_name is None and detected_model is not None

    # Get context window size
    context_window = get_context_window_size(detected_model)

    # Determine threshold
    env_threshold = get_threshold_from_environment()
    if threshold_override == "auto" or (threshold_override is None and env_threshold is None):
        # Auto-calculate threshold
        threshold_tokens = calculate_optimal_threshold(context_window)
    elif threshold_override is not None and threshold_override != "auto":
        threshold_tokens = int(threshold_override)
    elif env_threshold is not None:
        threshold_tokens = env_threshold
    else:
        threshold_tokens = calculate_optimal_threshold(context_window)

    # Determine preserve_recent_tokens
    env_preserve = get_preserve_recent_from_environment()
    if preserve_recent_override is not None:
        preserve_recent = preserve_recent_override
    elif env_preserve is not None:
        preserve_recent = env_preserve
    else:
        preserve_recent = calculate_preserve_recent(threshold_tokens, context_window)

    return ModelContextConfig(
        model_name=detected_model,
        context_window=context_window,
        threshold_tokens=threshold_tokens,
        swap_trigger_percent=swap_trigger_percent,
        preserve_recent_tokens=preserve_recent,
        detected=detected,
    )


def apply_model_config_to_config(model_config: ModelContextConfig, config: Config) -> Config:
    """Apply model-derived settings to a Config instance.

    This modifies the config in-place for convenience but also returns it.

    Args:
        model_config: Model-specific configuration
        config: Config instance to update

    Returns:
        Updated config (same instance, modified in place)
    """
    config.threshold_tokens = model_config.threshold_tokens
    config.preserve_recent_tokens = model_config.preserve_recent_tokens
    config.swap_trigger_percent = model_config.swap_trigger_percent
    return config


def format_model_config_summary(model_config: ModelContextConfig) -> str:
    """Format model configuration for display.

    Args:
        model_config: Model context configuration

    Returns:
        Formatted summary string
    """
    lines = [
        "=== Context Window Configuration ===",
        f"Model: {model_config.model_name or 'Unknown (using defaults)'}",
        f"Context Window: {model_config.context_window:,} tokens",
        f"Threshold: {model_config.threshold_tokens:,} tokens",
        f"Swap Trigger: {model_config.swap_trigger_percent:.0%}",
        f"Preserve Recent: {model_config.preserve_recent_tokens:,} tokens",
        f"Auto-detected: {'Yes' if model_config.detected else 'No'}",
    ]
    return "\n".join(lines)
