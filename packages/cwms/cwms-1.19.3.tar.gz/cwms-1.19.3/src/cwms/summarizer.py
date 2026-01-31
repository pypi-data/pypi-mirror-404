"""Summary generation and keyword extraction for conversation chunks."""

from __future__ import annotations

import json
import logging
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from cwms.utils.text import (
    STOP_WORDS,
    TECHNICAL_TERMS,
    _extract_proper_nouns,
    extract_keywords,
)

if TYPE_CHECKING:
    from cwms.embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)

# Backward compatibility re-exports
__all__ = [
    "STOP_WORDS",
    "TECHNICAL_TERMS",
    "extract_keywords",
    "_extract_proper_nouns",
    # Phase 1: Summarizer abstraction
    "Summarizer",
    "RegexSummarizer",
    "get_summarizer",
    # Phase 2: API Summarizer
    "APISummarizer",
]


# =============================================================================
# Phase 1: Summarizer Protocol and Implementations
# =============================================================================


@runtime_checkable
class Summarizer(Protocol):
    """Protocol for summarization backends.

    This protocol defines the interface that all summarizer implementations
    must follow. It enables pluggable summarization backends (regex, API, etc.).
    """

    def summarize(
        self,
        content: str,
        max_length: int = 500,
        context: str | None = None,
    ) -> str:
        """Generate a summary of the content.

        Args:
            content: Text to summarize
            max_length: Maximum summary length in characters
            context: Optional context about what the content represents

        Returns:
            Summary text
        """
        ...

    def extract_keywords(
        self,
        content: str,
        max_keywords: int = 10,
    ) -> list[str]:
        """Extract key terms from content.

        Args:
            content: Text to extract keywords from
            max_keywords: Maximum number of keywords

        Returns:
            List of keywords/key phrases
        """
        ...


@dataclass
class SummarizerConfig:
    """Configuration options for the summarizer.

    These options control how summaries are generated.
    """

    max_length: int = 1000  # Maximum summary length in characters
    include_code_context: bool = True  # Include code block descriptions
    extract_questions: bool = True  # Extract user questions/requests
    min_keyword_length: int = 3  # Minimum keyword length


# Default configuration instance
DEFAULT_CONFIG = SummarizerConfig()


class RegexSummarizer:
    """Regex-based extractive summarizer (existing behavior).

    This class wraps the existing regex-based summarization functions
    to implement the Summarizer protocol. It provides backward-compatible
    summarization using pattern matching and text extraction.
    """

    def __init__(self, config: SummarizerConfig | None = None) -> None:
        """Initialize the regex summarizer.

        Args:
            config: Optional summarizer configuration. Uses DEFAULT_CONFIG if not provided.
        """
        self.config = config or DEFAULT_CONFIG

    def summarize(
        self,
        content: str,
        max_length: int = 500,
        context: str | None = None,  # noqa: ARG002 - unused, but required by protocol
    ) -> str:
        """Generate a summary using regex-based extraction.

        Args:
            content: Text to summarize
            max_length: Maximum summary length in characters
            context: Optional context (unused in regex implementation,
                     but will be used by API implementation in Phase 2)

        Returns:
            Summary text
        """
        return summarize_chunk(content, max_length=max_length, config=self.config)

    def extract_keywords(
        self,
        content: str,
        max_keywords: int = 10,
    ) -> list[str]:
        """Extract keywords using regex-based extraction.

        Args:
            content: Text to extract keywords from
            max_keywords: Maximum number of keywords

        Returns:
            List of keywords/key phrases
        """
        keywords: list[str] = extract_keywords(
            content, top_k=max_keywords, min_length=self.config.min_keyword_length
        )
        return keywords


# =============================================================================
# Phase 2: API Summarizer Implementation
# =============================================================================


class APISummarizer:
    """LLM-powered summarizer using Anthropic API.

    Uses Claude (via the Anthropic API) to generate high-quality abstractive
    summaries of conversation content. Falls back to RegexSummarizer on errors.

    Requires:
        - anthropic package: pip install anthropic
        - API key: Set ANTHROPIC_API_KEY environment variable

    Example:
        >>> summarizer = APISummarizer(config)
        >>> summary = summarizer.summarize("conversation content...")
    """

    def __init__(
        self,
        config: SummarizerConfig | None = None,
        api_key: str | None = None,
        model: str = "claude-opus-4-5-20251101",
        max_api_tokens: int = 500,
        storage_dir: Path | None = None,
        monthly_cost_limit: float | None = None,
    ) -> None:
        """Initialize API summarizer.

        Args:
            config: Summarizer configuration (uses DEFAULT_CONFIG if not provided)
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use for summarization (default: claude-3-haiku)
            max_api_tokens: Maximum tokens for API response
            storage_dir: Directory for storing usage tracking data
            monthly_cost_limit: Optional monthly cost limit in USD

        Raises:
            ImportError: If anthropic package not installed
            ValueError: If no API key available
        """
        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic package required for API summarization. "
                "Install with: pip install anthropic"
            ) from e

        self.config = config or DEFAULT_CONFIG
        self.model = model
        self.max_api_tokens = max_api_tokens
        self.monthly_cost_limit = monthly_cost_limit

        # Storage for usage tracking
        self._storage_dir = storage_dir or Path("~/.claude/cwms").expanduser()
        self._usage_file = self._storage_dir / "summarization_usage.json"

        # Get API key from parameter or environment
        resolved_api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.client = anthropic.Anthropic(api_key=resolved_api_key)
        self._fallback = RegexSummarizer(config)

    def summarize(
        self,
        content: str,
        max_length: int = 500,
        context: str | None = None,
    ) -> str:
        """Generate summary using Claude API.

        Falls back to regex summarizer on API errors or if cost limit exceeded.

        Args:
            content: Text to summarize
            max_length: Maximum summary length in characters
            context: Optional context about what the content represents

        Returns:
            Summary text
        """
        if not content.strip():
            return ""

        # Check cost limit before making API call
        estimated_cost = self.estimate_cost(content)
        if not self._check_cost_limit(estimated_cost):
            logger.warning("Monthly API cost limit reached, using regex fallback")
            return self._fallback.summarize(content, max_length, context)

        system_prompt = """You are a technical summarizer for coding conversations.
Generate a concise summary that captures:
1. What task/problem was being worked on
2. Key decisions made
3. Files/code that was modified
4. Current state/next steps

Be specific about technical details. Use bullet points for clarity.
Do not include pleasantries or meta-commentary."""

        # Limit input to avoid token limits (roughly 8000 chars = ~2000 tokens)
        truncated_content = content[:8000]
        context_note = f"\nContext: {context}" if context else ""

        user_prompt = f"""Summarize this coding conversation segment:

{truncated_content}
{context_note}

Provide a summary in {max_length} characters or less."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_api_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            result: str = response.content[0].text
            # Record usage after successful API call
            self._record_usage(estimated_cost)
            return result
        except Exception as e:
            logger.warning("API summarization failed, falling back to regex: %s", e)
            return self._fallback.summarize(content, max_length, context)

    def extract_keywords(
        self,
        content: str,
        max_keywords: int = 10,
    ) -> list[str]:
        """Extract keywords using Claude API.

        Falls back to regex summarizer on API errors.

        Args:
            content: Text to extract keywords from
            max_keywords: Maximum number of keywords

        Returns:
            List of keywords/key phrases
        """
        if not content.strip():
            return []

        prompt = f"""Extract the {max_keywords} most important technical keywords
from this coding conversation. Include:
- Function/class/file names mentioned
- Technologies/frameworks discussed
- Key concepts/patterns used

Return ONLY the keywords, one per line, no numbering or explanation.

Content:
{content[:4000]}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            keywords_text: str = response.content[0].text.strip()
            keywords = keywords_text.split("\n")
            return [kw.strip() for kw in keywords if kw.strip()][:max_keywords]
        except Exception as e:
            logger.warning("API keyword extraction failed, falling back to regex: %s", e)
            return self._fallback.extract_keywords(content, max_keywords)

    def estimate_cost(self, content: str) -> float:
        """Estimate API cost for summarizing content.

        Uses rough token estimates based on character count.

        Args:
            content: Content to be summarized

        Returns:
            Estimated cost in USD
        """
        # Rough token estimate (4 chars per token)
        input_tokens = min(len(content), 8000) // 4
        output_tokens = self.max_api_tokens

        # Opus 4.5 pricing (as of 2025): $15/1M input, $75/1M output
        input_cost = (input_tokens / 1_000_000) * 15.0
        output_cost = (output_tokens / 1_000_000) * 75.0

        return input_cost + output_cost

    # =========================================================================
    # Phase 4: Cost Controls and Monitoring
    # =========================================================================

    def _get_current_month_key(self) -> str:
        """Get the current month key for usage tracking.

        Returns:
            Month key in YYYY-MM format
        """
        return datetime.now().strftime("%Y-%m")

    def _load_usage(self) -> dict[str, Any]:
        """Load usage data from storage.

        Returns:
            Usage data dictionary with monthly stats
        """
        if not self._usage_file.exists():
            return {"months": {}}

        try:
            with open(self._usage_file, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load usage data: %s", e)
            return {"months": {}}

    def _save_usage(self, usage: dict[str, Any]) -> None:
        """Save usage data to storage.

        Args:
            usage: Usage data dictionary
        """
        try:
            self._storage_dir.mkdir(parents=True, exist_ok=True)
            with open(self._usage_file, "w", encoding="utf-8") as f:
                json.dump(usage, f, indent=2)
        except OSError as e:
            logger.warning("Failed to save usage data: %s", e)

    def _get_monthly_usage(self) -> dict[str, Any]:
        """Get current month's usage statistics.

        Returns:
            Dictionary with swaps, estimated_spend for current month
        """
        usage = self._load_usage()
        month_key = self._get_current_month_key()
        months: dict[str, Any] = usage.get("months", {})
        result: dict[str, Any] = months.get(month_key, {"swaps": 0, "estimated_spend": 0.0})
        return result

    def _record_usage(self, estimated_cost: float) -> None:
        """Record a summarization operation and its estimated cost.

        Args:
            estimated_cost: Estimated cost of the operation in USD
        """
        usage = self._load_usage()
        month_key = self._get_current_month_key()

        if "months" not in usage:
            usage["months"] = {}

        if month_key not in usage["months"]:
            usage["months"][month_key] = {"swaps": 0, "estimated_spend": 0.0}

        usage["months"][month_key]["swaps"] += 1
        usage["months"][month_key]["estimated_spend"] += estimated_cost
        usage["months"][month_key]["last_updated"] = datetime.now().isoformat()

        self._save_usage(usage)

    def _check_cost_limit(self, estimated_cost: float) -> bool:
        """Check if we're within monthly cost limit.

        Args:
            estimated_cost: Estimated cost of pending operation

        Returns:
            True if within limit (or no limit set), False if would exceed
        """
        if self.monthly_cost_limit is None:
            return True

        monthly = self._get_monthly_usage()
        current_spend: float = float(monthly["estimated_spend"])
        return (current_spend + estimated_cost) <= self.monthly_cost_limit

    def get_usage_stats(self) -> dict[str, Any]:
        """Get current usage statistics for monitoring.

        Returns:
            Dictionary with usage stats including:
            - swaps: Number of API summarizations this month
            - estimated_spend: Estimated USD spent this month
            - cost_limit: Monthly cost limit (if set)
            - remaining: USD remaining in budget (if limit set)
        """
        monthly = self._get_monthly_usage()
        stats: dict[str, Any] = {
            "swaps_this_month": monthly["swaps"],
            "estimated_spend": round(monthly["estimated_spend"], 4),
            "cost_limit": self.monthly_cost_limit,
        }

        if self.monthly_cost_limit is not None:
            stats["remaining"] = round(
                max(0, self.monthly_cost_limit - monthly["estimated_spend"]), 4
            )

        return stats


def get_summarizer(
    provider: str = "regex",
    config: SummarizerConfig | None = None,
    api_key: str | None = None,
    api_model: str = "claude-opus-4-5-20251101",
    api_max_tokens: int = 500,
    storage_dir: Path | None = None,
    monthly_cost_limit: float | None = None,
) -> Summarizer:
    """Factory function for summarizer instances.

    Args:
        provider: "regex" or "api"
        config: Optional summarizer configuration
        api_key: API key for API provider (falls back to ANTHROPIC_API_KEY env var)
        api_model: Model to use for API provider
        api_max_tokens: Max tokens for API responses
        storage_dir: Directory for usage tracking (API provider only)
        monthly_cost_limit: Monthly cost limit in USD (API provider only)

    Returns:
        Summarizer instance

    Raises:
        ValueError: If provider is unknown
        ImportError: If API provider requested but anthropic not installed
    """
    provider = provider.lower()

    if provider == "regex":
        return RegexSummarizer(config)

    if provider == "api":
        return APISummarizer(
            config=config,
            api_key=api_key,
            model=api_model,
            max_api_tokens=api_max_tokens,
            storage_dir=storage_dir,
            monthly_cost_limit=monthly_cost_limit,
        )

    raise ValueError(f"Unknown summarizer provider: {provider}. Valid options: regex, api")


# =============================================================================
# Existing Regex-based Functions (preserved for backward compatibility)
# =============================================================================


def extract_code_references(text: str) -> list[str]:
    """Extract file paths, function names, and other code references.

    Args:
        text: Text to extract references from

    Returns:
        List of code references found
    """
    references = []

    # Extract file paths (various patterns)
    # Matches: src/file.py, ./config.yaml, /absolute/path.txt
    file_paths = re.findall(r"(?:\.{0,2}/)?[\w\-]+(?:/[\w\-\.]+)*\.[\w]+", text, re.IGNORECASE)
    references.extend(file_paths)

    # Extract function/class definitions
    # Matches: def function_name, class ClassName
    definitions = re.findall(r"(?:def|class)\s+(\w+)", text)
    references.extend(definitions)

    # Extract import statements
    # Matches: import module, from module import thing
    imports = re.findall(r"(?:import|from)\s+([\w\.]+)", text)
    references.extend(imports)

    return list(set(references))  # Deduplicate


def extract_user_questions(user_messages: list[str]) -> list[str]:
    """Extract questions and requests from user messages.

    Looks for interrogative patterns and request indicators.

    Args:
        user_messages: List of user message content strings

    Returns:
        List of extracted questions/requests
    """
    questions = []

    # Patterns that indicate questions or requests
    question_patterns = [
        r"^(what|how|why|when|where|which|who|can you|could you|please|help|explain|show|tell)",
        r"\?$",  # Ends with question mark
        r"^(i want|i need|i'd like|can we|let's|implement|add|create|fix|update|remove|delete)",
    ]

    for msg in user_messages:
        if not msg:
            continue

        # Clean up the message
        msg_clean = msg.strip()
        sentences = re.split(r"[.!?]+", msg_clean)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue

            sentence_lower = sentence.lower()

            # Check if it matches question/request patterns
            for pattern in question_patterns:
                if re.search(pattern, sentence_lower):
                    # Truncate long sentences
                    if len(sentence) > 200:
                        sentence = sentence[:200] + "..."
                    questions.append(sentence)
                    break

    # Return unique questions, preserving order
    seen = set()
    unique_questions = []
    for q in questions:
        if q.lower() not in seen:
            seen.add(q.lower())
            unique_questions.append(q)

    return unique_questions[:5]  # Limit to 5 most relevant


def extract_assistant_actions(assistant_messages: list[str]) -> list[str]:
    """Extract actions and work descriptions from assistant messages.

    Looks for action statements indicating what was done.

    Args:
        assistant_messages: List of assistant message content strings

    Returns:
        List of extracted action descriptions
    """
    actions = []

    # Patterns that indicate assistant actions
    action_patterns = [
        r"^(i'll|i will|let me|i'm going to|i am going to)",
        r"^(created|implemented|added|fixed|updated|modified|removed|deleted|refactored)",
        r"^(here's|here is|i've|i have|done|finished|completed)",
        r"(the file|the function|the class|the module|the test)",
    ]

    for msg in assistant_messages:
        if not msg:
            continue

        # Clean up and split into sentences
        msg_clean = msg.strip()
        sentences = re.split(r"[.!?]+", msg_clean)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 15:
                continue

            sentence_lower = sentence.lower()

            # Check if it matches action patterns
            for pattern in action_patterns:
                if re.search(pattern, sentence_lower):
                    # Truncate long sentences
                    if len(sentence) > 200:
                        sentence = sentence[:200] + "..."
                    actions.append(sentence)
                    break

    # Return unique actions, preserving order
    seen = set()
    unique_actions = []
    for a in actions:
        if a.lower() not in seen:
            seen.add(a.lower())
            unique_actions.append(a)

    return unique_actions[:5]  # Limit to 5 most relevant


def extract_code_block_descriptions(text: str) -> list[str]:
    """Extract descriptions from code blocks (comments, docstrings).

    Looks for meaningful descriptions within code blocks that explain
    what the code does.

    Args:
        text: Text containing code blocks

    Returns:
        List of extracted descriptions
    """
    descriptions = []

    # Find all code blocks (```...```)
    code_blocks = re.findall(r"```[\w]*\n(.*?)```", text, re.DOTALL)

    for block in code_blocks:
        # Extract Python docstrings (triple quotes)
        docstrings = re.findall(r'"""(.*?)"""', block, re.DOTALL)
        docstrings.extend(re.findall(r"'''(.*?)'''", block, re.DOTALL))
        for doc in docstrings:
            # Get first line of docstring (usually the summary)
            first_line = doc.strip().split("\n")[0].strip()
            if first_line and len(first_line) >= 10 and len(first_line) <= 200:
                descriptions.append(first_line)

        # Extract single-line comments (# ...)
        comments = re.findall(r"#\s*(.+)$", block, re.MULTILINE)
        for comment in comments:
            comment = comment.strip()
            # Filter out noise (shebang, encoding, type hints, etc.)
            if (
                len(comment) >= 15
                and len(comment) <= 150
                and not comment.startswith("!")
                and not comment.startswith("-*-")
                and not comment.lower().startswith("type:")
                and not comment.lower().startswith("noqa")
                and not comment.lower().startswith("pylint")
                and not comment.lower().startswith("nosec")
                and "TODO" not in comment.upper()
                and "FIXME" not in comment.upper()
            ):
                descriptions.append(comment)

        # Extract JS/TS/Java style comments (// ...)
        js_comments = re.findall(r"//\s*(.+)$", block, re.MULTILINE)
        for comment in js_comments:
            comment = comment.strip()
            if len(comment) >= 15 and len(comment) <= 150:
                descriptions.append(comment)

    # Deduplicate while preserving order
    seen = set()
    unique_descriptions = []
    for desc in descriptions:
        desc_lower = desc.lower()
        if desc_lower not in seen:
            seen.add(desc_lower)
            unique_descriptions.append(desc)

    return unique_descriptions[:5]  # Limit to 5 descriptions


def get_chunk_position_label(chunk_index: int | None, total_chunks: int | None) -> str | None:
    """Get a human-readable position label for a chunk.

    Args:
        chunk_index: 0-based index of the chunk (None if unknown)
        total_chunks: Total number of chunks (None if unknown)

    Returns:
        Position label like "early", "middle", "late", or None if unknown
    """
    if chunk_index is None or total_chunks is None or total_chunks <= 0:
        return None

    if total_chunks == 1:
        return None  # No position context needed for single chunk

    # Calculate relative position (0.0 to 1.0)
    position = chunk_index / (total_chunks - 1) if total_chunks > 1 else 0.5

    if position <= 0.25:
        return "early in conversation"
    elif position >= 0.75:
        return "late in conversation"
    else:
        return "middle of conversation"


def extract_first_sentences(text: str, max_sentences: int = 3) -> str:
    """Extract first meaningful sentences from text as a fallback summary.

    Args:
        text: Full text to extract from
        max_sentences: Maximum number of sentences to extract

    Returns:
        Extracted sentences as a string
    """
    # Remove common markers
    cleaned = re.sub(r"\[(USER|ASSISTANT|TOOL_CALLS|TOOL_RESULTS)\]", "", text)
    cleaned = re.sub(r"(user:|assistant:|role:)", "", cleaned, flags=re.IGNORECASE)

    # Split into sentences
    sentences = re.split(r"[.!?]+", cleaned)

    # Filter meaningful sentences
    meaningful = []
    for s in sentences:
        s = s.strip()
        # Skip very short, code-heavy, or JSON-like content
        if len(s) < 20:
            continue
        if s.startswith("{") or s.startswith("["):
            continue
        if s.count("```") > 0:
            continue
        meaningful.append(s)
        if len(meaningful) >= max_sentences:
            break

    return ". ".join(meaningful) + "." if meaningful else ""


def _parse_conversation_messages(text: str) -> tuple[list[str], list[str]]:
    """Parse conversation text into user and assistant messages.

    Args:
        text: Full conversation text

    Returns:
        Tuple of (user_messages, assistant_messages)
    """
    lines = text.split("\n")

    # Collect messages by role
    user_messages: list[str] = []
    assistant_messages: list[str] = []

    # Look for user and assistant messages
    in_user_msg = False
    in_assistant_msg = False
    current_msg: list[str] = []

    # Define message boundary markers (order matters - check exact matches first)
    user_markers = ("[user]", "user:", "role: user", "# user")
    assistant_markers = ("[assistant]", "assistant:", "role: assistant", "# assistant")
    # Markers that indicate tool/system content to skip
    skip_markers = ("[tool_calls]", "[tool_results]", "tool_calls:", "tool_results:")

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Detect message boundaries
        if line_lower in user_markers or any(line_lower.startswith(m) for m in user_markers):
            # Save previous assistant message if any
            if current_msg and in_assistant_msg:
                assistant_messages.append(" ".join(current_msg))
            in_user_msg = True
            in_assistant_msg = False
            current_msg = []
        elif line_lower in assistant_markers or any(
            line_lower.startswith(m) for m in assistant_markers
        ):
            # Save previous user message if any
            if current_msg and in_user_msg:
                user_messages.append(" ".join(current_msg))
            in_assistant_msg = True
            in_user_msg = False
            current_msg = []
        elif any(line_lower.startswith(m) for m in skip_markers):
            # Save current message before skipping
            if current_msg and in_user_msg:
                user_messages.append(" ".join(current_msg))
            elif current_msg and in_assistant_msg:
                assistant_messages.append(" ".join(current_msg))
            in_user_msg = False
            in_assistant_msg = False
            current_msg = []
        elif (in_user_msg or in_assistant_msg) and line_stripped:
            current_msg.append(line_stripped[:200])

    # Add final message
    if current_msg:
        if in_user_msg:
            user_messages.append(" ".join(current_msg))
        elif in_assistant_msg:
            assistant_messages.append(" ".join(current_msg))

    return user_messages, assistant_messages


def _build_user_section(user_messages: list[str], cfg: SummarizerConfig) -> list[str]:
    """Build the user section of the summary.

    Args:
        user_messages: List of user messages
        cfg: Summarizer configuration

    Returns:
        List of summary lines for the user section
    """
    section = []

    # Use new extraction functions for better summaries (if enabled)
    user_questions = extract_user_questions(user_messages) if cfg.extract_questions else []

    if user_questions:
        section.append("User asked about:")
        for q in user_questions[:3]:
            section.append(f"  - {q}")
    elif user_messages:
        # Fallback: use first sentence of user messages
        first_user = user_messages[0][:200] if user_messages else ""
        if first_user:
            section.append(f"User discussed: {first_user}")

    return section


def _detect_actions(text: str) -> set[str]:
    """Detect actions mentioned in the text.

    Args:
        text: Text to analyze

    Returns:
        Set of detected action nouns
    """
    action_indicators = [
        ("implemented", "implementation"),
        ("created", "creation"),
        ("fixed", "bug fix"),
        ("updated", "update"),
        ("added", "addition"),
        ("removed", "removal"),
        ("refactored", "refactoring"),
        ("debugging", "debugging"),
        ("tested", "testing"),
        ("optimized", "optimization"),
        ("configured", "configuration"),
        ("installed", "installation"),
        ("deployed", "deployment"),
        ("analyzed", "analysis"),
        ("reviewed", "review"),
    ]

    text_lower = text.lower()
    detected_actions = set()

    for action_word, action_noun in action_indicators:
        if action_word in text_lower:
            detected_actions.add(action_noun)

    return detected_actions


def _build_assistant_section(assistant_messages: list[str], text: str) -> list[str]:
    """Build the assistant section of the summary.

    Args:
        assistant_messages: List of assistant messages
        text: Full conversation text

    Returns:
        List of summary lines for the assistant section
    """
    section = []

    assistant_actions = extract_assistant_actions(assistant_messages)
    detected_actions = _detect_actions(text)

    if assistant_actions:
        section.append("Assistant worked on:")
        for a in assistant_actions[:3]:
            section.append(f"  - {a}")
    elif detected_actions:
        section.append(f"Actions: {', '.join(sorted(detected_actions)[:5])}")

    return section


def _build_code_section(text: str, cfg: SummarizerConfig) -> list[str]:
    """Build the code section of the summary.

    Args:
        text: Full conversation text
        cfg: Summarizer configuration

    Returns:
        List of summary lines for the code section
    """
    section = []

    code_descriptions = extract_code_block_descriptions(text) if cfg.include_code_context else []

    if code_descriptions:
        section.append("Code context:")
        for desc in code_descriptions[:3]:
            section.append(f"  - {desc}")

    return section


def _extract_technical_details(text: str) -> list[str]:
    """Extract technical details like function names, config values, etc.

    Args:
        text: Text to analyze

    Returns:
        List of extracted technical details
    """
    technical_details: list[str] = []

    technical_patterns = [
        r"function[:\s]+(\w+)",
        r"class[:\s]+(\w+)",
        r"config[:\s]+(\w+)",
        r"timeout[:\s]+(\d+)",
        r"version[:\s]+([\d.]+)",
        r"port[:\s]+(\d+)",
    ]

    for pattern in technical_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        technical_details.extend(matches[:2])  # Limit per pattern

    return technical_details


def _build_technical_section(code_refs: list[str], technical_details: list[str]) -> list[str]:
    """Build the technical section of the summary.

    Args:
        code_refs: List of code references
        technical_details: List of technical details

    Returns:
        List of summary lines for the technical section
    """
    section = []

    # Files/Output produced
    if code_refs:
        files = [ref for ref in code_refs if "." in ref]
        unique_files = list(dict.fromkeys(files))  # Preserve order, remove dupes
        if unique_files:
            section.append(f"Files referenced: {', '.join(unique_files[:5])}")

    # Technical details
    if technical_details:
        unique_details = list(dict.fromkeys(technical_details))
        section.append(f"Technical details: {', '.join(str(d) for d in unique_details[:5])}")

    return section


def _build_fallback_content(text: str, keywords: list[str]) -> list[str]:
    """Build fallback content when no structured content is found.

    Args:
        text: Full conversation text
        keywords: Extracted keywords

    Returns:
        List of summary lines for fallback content
    """
    section = []

    # Try to extract first meaningful sentences as fallback
    fallback_text = extract_first_sentences(text, max_sentences=2)
    if fallback_text:
        section.append(f"Discussion: {fallback_text}")
    elif keywords:
        section.append(f"Topics: {', '.join(keywords[:5])}")

    return section


def summarize_chunk(
    text: str,
    max_length: int | None = None,
    chunk_index: int | None = None,
    total_chunks: int | None = None,
    config: SummarizerConfig | None = None,
) -> str:
    """Generate a concise summary of a conversation chunk.

    Creates a structured summary including:
    - Chunk position context (early/middle/late)
    - What the user asked about
    - What the assistant worked on
    - Code descriptions from code blocks (if enabled)
    - Files and code referenced
    - Key topics for search

    Args:
        text: Full conversation chunk text
        max_length: Maximum summary length (overrides config if provided)
        chunk_index: 0-based index of this chunk (for position context)
        total_chunks: Total number of chunks (for position context)
        config: Summarizer configuration options

    Returns:
        Formatted summary string optimized for Claude to understand context after /clear
    """
    if not text:
        return "Empty conversation"

    # Use provided config or default
    cfg = config or DEFAULT_CONFIG

    # max_length parameter overrides config if provided
    effective_max_length = max_length if max_length is not None else cfg.max_length

    # Extract key information using config options
    keywords = extract_keywords(text, top_k=12, min_length=cfg.min_keyword_length)
    code_refs = extract_code_references(text)
    position_label = get_chunk_position_label(chunk_index, total_chunks)

    # Parse conversation structure to understand user requests and assistant actions
    user_messages, assistant_messages = _parse_conversation_messages(text)

    # Extract technical context (function names, config changes, etc.)
    technical_details = _extract_technical_details(text)

    # Build comprehensive summary with structured sections
    summary_parts = []

    # Section 0: Position context (if available)
    if position_label:
        summary_parts.append(f"[Position: {position_label}]")

    # Section 1: What user asked about (most important for retrieval)
    user_section = _build_user_section(user_messages, cfg)
    summary_parts.extend(user_section)

    # Section 2: What assistant did
    assistant_section = _build_assistant_section(assistant_messages, text)
    summary_parts.extend(assistant_section)

    # Section 3: Code descriptions (from code blocks)
    code_section = _build_code_section(text, cfg)
    summary_parts.extend(code_section)

    # Fallback if no structured content extracted (excluding position label)
    content_parts = [p for p in summary_parts if not p.startswith("[Position:")]
    if not content_parts:
        fallback = _build_fallback_content(text, keywords)
        summary_parts.extend(fallback)

    # Section 4: Technical details
    technical_section = _build_technical_section(code_refs, technical_details)
    summary_parts.extend(technical_section)

    # Keywords for search
    if keywords:
        summary_parts.append(f"Search keywords: {', '.join(keywords[:8])}")

    # Join and truncate if needed
    summary = "\n".join(summary_parts)
    if len(summary) > effective_max_length:
        summary = summary[:effective_max_length] + "..."

    return summary


def generate_summary_and_keywords(
    text: str,
    max_summary_length: int | None = None,
    top_k_keywords: int = 12,
    config: SummarizerConfig | None = None,
) -> tuple[str, list[str]]:
    """Generate both summary and keywords for a chunk.

    Convenience function that combines summarization and keyword extraction.

    Args:
        text: Full conversation chunk text
        max_summary_length: Maximum summary length (overrides config if provided)
        top_k_keywords: Number of keywords to extract
        config: Summarizer configuration options

    Returns:
        Tuple of (summary, keywords)
    """
    cfg = config or DEFAULT_CONFIG
    summary = summarize_chunk(text, max_length=max_summary_length, config=cfg)
    keywords = extract_keywords(text, top_k=top_k_keywords, min_length=cfg.min_keyword_length)

    # Add code references as additional keywords
    code_refs = extract_code_references(text)
    # Add unique code refs that aren't already in keywords
    for ref in code_refs[:5]:  # Limit to 5 additional
        if ref not in keywords:
            keywords.append(ref)

    return summary, keywords[: top_k_keywords + 5]  # Allow extra for code refs


def config_from_main_config(main_config: object) -> SummarizerConfig:
    """Create a SummarizerConfig from a main Config object.

    Args:
        main_config: Main config object with summarizer_* attributes

    Returns:
        SummarizerConfig instance
    """
    return SummarizerConfig(
        max_length=getattr(main_config, "summarizer_max_length", 1000),
        include_code_context=getattr(main_config, "summarizer_include_code_context", True),
        extract_questions=getattr(main_config, "summarizer_extract_questions", True),
        min_keyword_length=getattr(main_config, "summarizer_min_keyword_length", 3),
    )


# =============================================================================
# Phase 7.1: TextRank-based Extractive Summarization
# =============================================================================

# Common abbreviations that should not be treated as sentence boundaries
ABBREVIATIONS = {
    "mr",
    "mrs",
    "ms",
    "dr",
    "prof",
    "sr",
    "jr",
    "vs",
    "etc",
    "inc",
    "ltd",
    "co",
    "corp",
    "st",
    "ave",
    "blvd",
    "rd",
    "apt",
    "no",
    "vol",
    "pg",
    "pp",
    "fig",
    "e.g",
    "i.e",
    "viz",
    "cf",
    "al",
    "et",
    "jan",
    "feb",
    "mar",
    "apr",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
    "mon",
    "tue",
    "wed",
    "thu",
    "fri",
    "sat",
    "sun",
}


def split_sentences(text: str) -> list[str]:
    """Split text into sentences, handling common edge cases.

    Handles:
    - Standard sentence boundaries (., !, ?)
    - Abbreviations (Dr., Mr., etc.)
    - Code blocks (don't split inside ```)
    - Decimal numbers (don't split on 3.14)
    - URLs and file paths

    Args:
        text: Text to split into sentences

    Returns:
        List of sentences
    """
    if not text or not text.strip():
        return []

    # First, protect code blocks by replacing them with placeholders
    code_blocks: list[str] = []
    code_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)

    def save_code_block(match: re.Match[str]) -> str:
        code_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

    protected_text = code_pattern.sub(save_code_block, text)

    # Protect decimal numbers (e.g., 3.14, 0.5)
    decimal_pattern = re.compile(r"(\d+)\.(\d+)")
    protected_text = decimal_pattern.sub(r"\1__DECIMAL__\2", protected_text)

    # Protect common abbreviations
    for abbr in ABBREVIATIONS:
        # Match abbreviation followed by period (case insensitive)
        pattern = re.compile(rf"\b({abbr})\.(?=\s|$)", re.IGNORECASE)
        protected_text = pattern.sub(r"\1__ABBR__", protected_text)

    # Protect URLs
    url_pattern = re.compile(r"https?://[^\s]+")
    protected_text = url_pattern.sub(lambda m: m.group(0).replace(".", "__DOT__"), protected_text)

    # Protect file paths (e.g., src/file.py, ./config.yaml)
    file_pattern = re.compile(r"(?:\.{0,2}/)?[\w\-]+(?:/[\w\-]+)*\.[\w]+")
    protected_text = file_pattern.sub(lambda m: m.group(0).replace(".", "__DOT__"), protected_text)

    # Now split on sentence boundaries
    # Split on . ! ? followed by whitespace or end of string
    sentence_pattern = re.compile(r"(?<=[.!?])\s+")
    raw_sentences = sentence_pattern.split(protected_text)

    # Restore protected content and clean up sentences
    sentences = []
    for sent in raw_sentences:
        # Restore code blocks
        for i, code_block in enumerate(code_blocks):
            sent = sent.replace(f"__CODE_BLOCK_{i}__", code_block)

        # Restore decimal numbers
        sent = sent.replace("__DECIMAL__", ".")

        # Restore abbreviations
        sent = sent.replace("__ABBR__", ".")

        # Restore URLs and file paths
        sent = sent.replace("__DOT__", ".")

        # Clean and validate
        sent = sent.strip()
        if sent and len(sent) >= 3:  # Minimum 3 chars for a valid sentence
            sentences.append(sent)

    return sentences


def word_overlap_similarity(sent1: str, sent2: str) -> float:
    """Calculate Jaccard similarity between two sentences based on word overlap.

    Args:
        sent1: First sentence
        sent2: Second sentence

    Returns:
        Jaccard similarity score (0.0 to 1.0)
    """
    words1 = set(sent1.lower().split())
    words2 = set(sent2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (-1.0 to 1.0, typically 0.0 to 1.0 for embeddings)
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=True))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot_product / (norm1 * norm2)


def build_similarity_matrix(
    sentences: list[str],
    embeddings: list[list[float]] | None = None,
) -> list[list[float]]:
    """Build a similarity matrix from sentences.

    If embeddings are provided, uses cosine similarity.
    Otherwise, falls back to word overlap (Jaccard) similarity.

    Args:
        sentences: List of sentences
        embeddings: Optional list of embedding vectors (one per sentence)

    Returns:
        NxN similarity matrix where N is the number of sentences
    """
    n = len(sentences)
    if n == 0:
        return []

    matrix: list[list[float]] = [[0.0] * n for _ in range(n)]

    use_embeddings = embeddings is not None and len(embeddings) == n and all(embeddings)

    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 1.0  # Self-similarity
            elif j > i:
                # Calculate similarity
                if use_embeddings and embeddings is not None:
                    sim = cosine_similarity(embeddings[i], embeddings[j])
                else:
                    sim = word_overlap_similarity(sentences[i], sentences[j])

                # Matrix is symmetric
                matrix[i][j] = sim
                matrix[j][i] = sim

    return matrix


def pagerank(
    similarity_matrix: list[list[float]],
    damping: float = 0.85,
    iterations: int = 100,
    tolerance: float = 1e-6,
) -> list[float]:
    """Run PageRank algorithm on similarity matrix to get sentence scores.

    Uses power iteration method with convergence check.

    Args:
        similarity_matrix: NxN similarity matrix
        damping: Damping factor (typically 0.85)
        iterations: Maximum number of iterations
        tolerance: Convergence tolerance

    Returns:
        List of PageRank scores (one per sentence)
    """
    n = len(similarity_matrix)
    if n == 0:
        return []

    if n == 1:
        return [1.0]

    # Initialize scores uniformly
    scores = [1.0 / n] * n

    # Normalize similarity matrix (create transition probabilities)
    # Each row should sum to 1 (or 0 if no outgoing links)
    normalized: list[list[float]] = []
    for row in similarity_matrix:
        row_sum = sum(row)
        if row_sum > 0:
            normalized.append([val / row_sum for val in row])
        else:
            # If no connections, distribute evenly (handle dangling nodes)
            normalized.append([1.0 / n] * n)

    # Power iteration
    for _ in range(iterations):
        new_scores = [0.0] * n

        for i in range(n):
            # Random jump component
            rank_sum = (1 - damping) / n

            # Link contribution
            for j in range(n):
                rank_sum += damping * normalized[j][i] * scores[j]

            new_scores[i] = rank_sum

        # Check for convergence
        diff = sum(abs(new_scores[i] - scores[i]) for i in range(n))
        scores = new_scores

        if diff < tolerance:
            break

    return scores


def textrank_summarize(
    text: str,
    num_sentences: int = 3,
    embedding_provider: EmbeddingProvider | None = None,
) -> str:
    """Extract key sentences using TextRank algorithm.

    Uses PageRank-style scoring to identify the most important sentences.
    If an embedding provider is available, uses semantic similarity.
    Otherwise, falls back to word overlap (Jaccard) similarity.

    Args:
        text: Text to summarize
        num_sentences: Number of sentences to extract
        embedding_provider: Optional embedding provider for semantic similarity.
                          If None or NoEmbeddings, falls back to word overlap.

    Returns:
        Extracted key sentences as a single string, preserving original order.
    """
    if not text or not text.strip():
        return ""

    # Split text into sentences
    sentences = split_sentences(text)

    if not sentences:
        return ""

    # If we have fewer sentences than requested, return original text
    if len(sentences) <= num_sentences:
        return " ".join(sentences)

    # Get embeddings if provider is available and not NoEmbeddings
    embeddings: list[list[float]] | None = None

    if embedding_provider is not None:
        # Check if it's a NoEmbeddings instance (returns empty lists)
        try:
            test_embeddings = embedding_provider.embed(["test"])
            if test_embeddings and test_embeddings[0]:
                # Real embeddings available, get them for all sentences
                embeddings = embedding_provider.embed(sentences)
        except Exception:
            # If embedding fails, fall back to word overlap
            embeddings = None

    # Build similarity matrix
    matrix = build_similarity_matrix(sentences, embeddings)

    # Run PageRank to score sentences
    scores = pagerank(matrix)

    # Get indices of top-scored sentences
    scored_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    top_indices = sorted(scored_indices[:num_sentences])  # Sort by position to preserve order

    # Extract and join the top sentences
    selected_sentences = [sentences[i] for i in top_indices]
    return " ".join(selected_sentences)
