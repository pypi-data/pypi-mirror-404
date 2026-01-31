"""Token estimation utilities for context management."""


def estimate_tokens(text: str, encoding: str | None = None) -> int:
    """Estimate token count for text.

    Attempts to use tiktoken for accurate counting, falls back to character-based
    heuristic if tiktoken is not available.

    Args:
        text: Text to estimate tokens for
        encoding: Optional tiktoken encoding name (default: cl100k_base for GPT-4)

    Returns:
        Estimated token count
    """
    try:
        import tiktoken

        enc_name = encoding or "cl100k_base"
        enc = tiktoken.get_encoding(enc_name)
        return len(enc.encode(text))
    except ImportError:
        # Fallback: ~4 characters per token for English text
        # This is a rough approximation but works reasonably well
        return len(text) // 4
    except Exception:
        # If tiktoken fails for any reason, use fallback
        return len(text) // 4


def estimate_tokens_batch(texts: list[str], encoding: str | None = None) -> list[int]:
    """Estimate tokens for multiple texts efficiently.

    Args:
        texts: List of texts to estimate
        encoding: Optional tiktoken encoding name

    Returns:
        List of token counts corresponding to input texts
    """
    return [estimate_tokens(text, encoding) for text in texts]


def truncate_to_tokens(text: str, max_tokens: int, encoding: str | None = None) -> str:
    """Truncate text to fit within token limit.

    Args:
        text: Text to truncate
        max_tokens: Maximum token count
        encoding: Optional tiktoken encoding name

    Returns:
        Truncated text that fits within token limit
    """
    current_tokens = estimate_tokens(text, encoding)

    if current_tokens <= max_tokens:
        return text

    # Binary search for the right character length
    try:
        import tiktoken

        enc_name = encoding or "cl100k_base"
        enc = tiktoken.get_encoding(enc_name)

        # Approximate character count needed
        target_chars = int(len(text) * (max_tokens / current_tokens))

        # Try progressively smaller chunks
        while target_chars > 0:
            chunk = text[:target_chars]
            if len(enc.encode(chunk)) <= max_tokens:
                return chunk
            target_chars = int(target_chars * 0.9)  # Reduce by 10%

        return ""

    except ImportError:
        # Fallback: simple character-based truncation
        target_chars = max_tokens * 4
        return text[:target_chars]


def split_by_tokens(
    text: str, chunk_size: int, overlap: int = 0, encoding: str | None = None
) -> list[str]:
    """Split text into chunks with target token size.

    Args:
        text: Text to split
        chunk_size: Target tokens per chunk
        overlap: Number of overlapping tokens between chunks
        encoding: Optional tiktoken encoding name

    Returns:
        List of text chunks
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    total_tokens = estimate_tokens(text, encoding)

    if total_tokens <= chunk_size:
        return [text]

    # Approximate character positions
    chars_per_token = len(text) / total_tokens
    chunk_chars = int(chunk_size * chars_per_token)
    overlap_chars = int(overlap * chars_per_token)

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_chars
        chunk = text[start:end]

        # Verify token count and adjust if needed
        chunk_tokens = estimate_tokens(chunk, encoding)

        if chunk_tokens > chunk_size:
            # Chunk too large, reduce
            chunk = truncate_to_tokens(chunk, chunk_size, encoding)
        elif end < len(text) and chunk_tokens < chunk_size * 0.9:
            # Chunk too small (and not at end), expand
            extension = int((chunk_size - chunk_tokens) * chars_per_token)
            chunk = text[start : end + extension]

        chunks.append(chunk)

        # Move start position with overlap
        if end >= len(text):
            break

        start = end - overlap_chars

    return chunks
