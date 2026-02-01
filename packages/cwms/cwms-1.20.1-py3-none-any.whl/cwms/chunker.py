"""Conversation chunking with safe swap detection."""

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from cwms.tokens import estimate_tokens

if TYPE_CHECKING:
    from cwms.embeddings import EmbeddingProvider


@dataclass
class Message:
    """Represents a single message in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    tool_calls: list[dict[Any, Any]] = field(default_factory=list)
    tool_results: list[dict[Any, Any]] = field(default_factory=list)


@dataclass
class ConversationContext:
    """Represents the current state of a conversation for chunking decisions."""

    messages: list[Message]
    in_code_block: bool = False
    pending_tool_calls: bool = False
    last_message_type: str | None = None

    @property
    def token_count(self) -> int:
        """Estimate total token count of all messages."""
        total = 0
        for msg in self.messages:
            total += estimate_tokens(msg.content)
        return total


def is_safe_to_swap(context: ConversationContext) -> bool:
    """Check if we're at a safe point to swap context.

    A safe swap point is when:
    - Not mid-code-block
    - No pending tool calls
    - Last message was from assistant (completed exchange)

    Args:
        context: Current conversation context

    Returns:
        True if safe to swap, False otherwise
    """
    # Not mid-code-block
    if context.in_code_block:
        return False

    # Not mid-tool-execution
    if context.pending_tool_calls:
        return False

    # Prefer after assistant completes response
    # (complete user/assistant exchange)
    return context.last_message_type == "assistant"


def detect_code_blocks(text: str) -> bool:
    """Detect if text contains unclosed code blocks.

    Args:
        text: Text to check

    Returns:
        True if there are unclosed code blocks
    """
    # Count code fence markers (```)
    fence_count = text.count("```")
    # Odd number means unclosed block
    return fence_count % 2 != 0


def _is_safe_split_point(msg: Message) -> bool:
    """Check if a message is safe to split after.

    A message is safe to split after if:
    - It doesn't contain unclosed code blocks
    - It doesn't have pending tool calls (calls without results)

    Args:
        msg: Message to check

    Returns:
        True if safe to split after this message, False otherwise
    """
    # Don't split if message contains unclosed code blocks
    if detect_code_blocks(msg.content):
        return False

    # Don't split if message has pending tool calls
    return not (msg.tool_calls and not msg.tool_results)


def _calculate_overlap_start(messages: list[Message], split_index: int, overlap_tokens: int) -> int:
    """Calculate the starting index for chunk overlap.

    Works backwards from the split point to find where overlap should begin,
    accumulating messages until reaching the overlap token limit.

    Args:
        messages: List of all messages
        split_index: Index where the split will occur
        overlap_tokens: Target number of tokens to overlap

    Returns:
        Index where overlap should start
    """
    overlap_tokens_counted = 0
    overlap_start = split_index

    for j in range(split_index - 1, -1, -1):
        overlap_msg_tokens = estimate_tokens(messages[j].content)
        if overlap_tokens_counted + overlap_msg_tokens <= overlap_tokens:
            overlap_tokens_counted += overlap_msg_tokens
            overlap_start = j
        else:
            break

    return overlap_start


def find_chunk_boundary(
    messages: list[Message], target_tokens: int, overlap_tokens: int
) -> tuple[int, int]:
    """Find optimal boundary for chunking messages.

    Attempts to find a natural break point near the target token count,
    while preserving complete user/assistant exchanges and avoiding
    mid-code-block splits.

    Args:
        messages: List of messages to chunk
        target_tokens: Target token count for chunk
        overlap_tokens: Tokens to overlap between chunks

    Returns:
        Tuple of (split_index, overlap_start_index)
        split_index: Index where to split (exclusive)
        overlap_start_index: Index where overlap begins
    """
    if not messages:
        return 0, 0

    cumulative_tokens = 0
    last_safe_split = 0
    overlap_start = 0

    for i, msg in enumerate(messages):
        msg_tokens = estimate_tokens(msg.content)
        cumulative_tokens += msg_tokens

        # Check if this is a safe split point and is an assistant message
        if msg.role == "assistant" and _is_safe_split_point(msg):
            last_safe_split = i + 1
            overlap_start = _calculate_overlap_start(messages, last_safe_split, overlap_tokens)

        # If we've exceeded target, return last safe split
        if cumulative_tokens >= target_tokens and last_safe_split > 0:
            return last_safe_split, overlap_start

    # If we never reached target, return end
    return len(messages), max(0, len(messages) - 1)


def chunk_messages(
    messages: list[Message],
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
    preserve_recent: int = 8000,
) -> tuple[list[list[Message]], list[Message]]:
    """Split messages into chunks, preserving recent context.

    Args:
        messages: All messages to potentially chunk
        chunk_size: Target token size for each chunk
        chunk_overlap: Overlap tokens between chunks for continuity
        preserve_recent: Minimum recent tokens to always preserve

    Returns:
        Tuple of (chunks_to_swap, messages_to_keep)
        chunks_to_swap: List of message chunks that can be swapped
        messages_to_keep: Recent messages to keep in active context
    """
    if not messages:
        return [], []

    # Calculate how many tokens we need to preserve
    total_tokens = sum(estimate_tokens(msg.content) for msg in messages)

    # If total is under preserve threshold, keep everything
    if total_tokens <= preserve_recent:
        return [], messages

    # Work backwards to find preserve boundary
    preserve_tokens = 0
    preserve_start_idx = len(messages)

    for i in range(len(messages) - 1, -1, -1):
        msg_tokens = estimate_tokens(messages[i].content)
        if preserve_tokens + msg_tokens <= preserve_recent:
            preserve_tokens += msg_tokens
            preserve_start_idx = i
        else:
            break

    # Messages to chunk (everything before preserve boundary)
    messages_to_chunk = messages[:preserve_start_idx]
    messages_to_keep = messages[preserve_start_idx:]

    # If nothing to chunk, return early
    if not messages_to_chunk:
        return [], messages

    # Split messages_to_chunk into chunks
    chunks = []
    current_idx = 0

    while current_idx < len(messages_to_chunk):
        remaining = messages_to_chunk[current_idx:]
        split_idx, overlap_idx = find_chunk_boundary(remaining, chunk_size, chunk_overlap)

        # Create chunk from current_idx to split point
        chunk = remaining[:split_idx]
        chunks.append(chunk)

        # Move to next chunk, starting from overlap point
        if split_idx < len(remaining):
            # Ensure we always advance by at least 1 to avoid infinite loop
            current_idx += max(overlap_idx, 1)
        else:
            # No more messages
            break

    return chunks, messages_to_keep


def messages_to_text(messages: list[Message]) -> str:
    """Convert messages to plain text format for storage.

    Args:
        messages: List of messages

    Returns:
        Formatted text representation
    """
    lines = []
    for msg in messages:
        lines.append(f"[{msg.role.upper()}]")
        lines.append(msg.content)

        if msg.tool_calls:
            lines.append("[TOOL_CALLS]")
            lines.append(json.dumps(msg.tool_calls, indent=2))

        if msg.tool_results:
            lines.append("[TOOL_RESULTS]")
            lines.append(json.dumps(msg.tool_results, indent=2))

        lines.append("")  # Blank line between messages

    return "\n".join(lines)


def find_semantic_boundary(
    messages: list[Message],
    target_tokens: int,
    embedding_provider: "EmbeddingProvider",
) -> int:
    """Find chunk boundary at natural topic shift using semantic similarity.

    Uses embeddings to detect topic shifts by finding low similarity points
    between consecutive messages near the target token count.

    Args:
        messages: List of messages to analyze
        target_tokens: Target token count for chunk
        embedding_provider: Provider for generating embeddings

    Returns:
        Index where to split messages (1-based, so split at messages[index:])
        Returns 0 if no good boundary found or if provider is NoEmbeddings
    """
    from cwms.embeddings import NoEmbeddings

    # Return 0 immediately if no embeddings available
    if isinstance(embedding_provider, NoEmbeddings):
        return 0

    if len(messages) < 2:
        return 0

    # Generate embeddings for all message contents
    texts = [msg.content for msg in messages]
    try:
        embeddings = embedding_provider.embed(texts)
    except Exception:
        # If embedding fails, fall back to token-based chunking
        return 0

    # Check if embeddings are valid (non-empty)
    if not embeddings or not embeddings[0]:
        return 0

    # Calculate cumulative token counts to find target range
    cumulative_tokens: list[int] = []
    total = 0
    for msg in messages:
        total += estimate_tokens(msg.content)
        cumulative_tokens.append(total)

    # Define search range: 80-120% of target_tokens
    min_tokens = int(target_tokens * 0.8)
    max_tokens = int(target_tokens * 1.2)

    # Calculate cosine similarity between consecutive messages
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not a or not b:
            return 1.0  # No valid comparison, assume similar

        # Use numpy if available, otherwise pure Python
        try:
            import numpy as np

            a_arr = np.array(a)
            b_arr = np.array(b)
            dot_product = np.dot(a_arr, b_arr)
            norm_a = np.linalg.norm(a_arr)
            norm_b = np.linalg.norm(b_arr)
            if norm_a == 0 or norm_b == 0:
                return 1.0
            return float(dot_product / (norm_a * norm_b))
        except ImportError:
            # Pure Python fallback
            dot_product = sum(x * y for x, y in zip(a, b, strict=True))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(x * x for x in b) ** 0.5
            if norm_a == 0 or norm_b == 0:
                return 1.0
            return float(dot_product / (norm_a * norm_b))

    # Find lowest similarity point within target range
    best_boundary = 0
    lowest_similarity = 1.0

    for i in range(len(messages) - 1):
        # Check if this boundary is within target token range
        # cumulative_tokens[i] is tokens up to and including message i
        tokens_at_boundary = cumulative_tokens[i]

        if min_tokens <= tokens_at_boundary <= max_tokens:
            similarity = cosine_similarity(embeddings[i], embeddings[i + 1])
            if similarity < lowest_similarity:
                lowest_similarity = similarity
                best_boundary = i + 1  # 1-based index for split

    return best_boundary


def calculate_adaptive_overlap(messages: list[Message]) -> int:
    """Calculate overlap tokens based on content type.

    Analyzes message content to determine optimal overlap:
    - Code-heavy content (>50% with code blocks): 400 tokens
    - Medium code content (20-50% with code blocks): 300 tokens
    - Prose content (<20% with code blocks): 200 tokens

    Args:
        messages: List of messages to analyze

    Returns:
        Recommended overlap in tokens
    """
    if not messages:
        return 200  # Default for empty list

    # Count messages that contain code blocks (use ``` as marker)
    code_message_count = 0
    for msg in messages:
        if "```" in msg.content:
            code_message_count += 1

    # Calculate ratio
    total_messages = len(messages)
    code_ratio = code_message_count / total_messages

    # Return appropriate overlap based on ratio thresholds
    if code_ratio > 0.5:
        # Code-heavy content: more overlap for context preservation
        return 400
    elif code_ratio >= 0.2:
        # Medium code content
        return 300
    else:
        # Prose content: less overlap needed
        return 200
