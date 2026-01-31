"""Orchestrates the swap-out process for conversation chunks."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, TypedDict, cast

from cwms import chunker
from cwms.chunker import (
    ConversationContext,
    Message,
    is_safe_to_swap,
    messages_to_text,
)
from cwms.config import Config
from cwms.embedding_cache import EmbeddingCache
from cwms.embeddings import EmbeddingProvider
from cwms.metrics import MetricsCollector, get_metrics
from cwms.retry import PermanentError, TransientError
from cwms.storage import Chunk, Storage
from cwms.summarizer import (
    Summarizer,
    config_from_main_config,
    get_summarizer,
)
from cwms.tokens import estimate_tokens

logger = logging.getLogger(__name__)


class SwappedChunkMetadata(TypedDict, total=False):
    """Metadata extracted from a conversation chunk.

    All fields are optional (total=False) because they are only
    set when the corresponding data is present in the chunk.
    """

    tool_calls_count: int
    files_referenced: list[str]
    message_count: int


class ChunkData(TypedDict):
    """Intermediate chunk data structure."""

    text: str
    summary: str
    keywords: list[str]
    token_count: int
    metadata: SwappedChunkMetadata


class Swapper:
    """Manages the swap-out process for conversation context.

    Monitors conversation token count and swaps older chunks to disk
    when threshold is reached, preserving recent context.
    """

    def __init__(
        self,
        storage: Storage,
        config: Config,
        embedding_cache: EmbeddingCache | None = None,
        summarizer: Summarizer | None = None,
    ):
        """Initialize swapper.

        Args:
            storage: Storage instance for persisting chunks
            config: Configuration settings
            embedding_cache: Optional embedding cache for performance
            summarizer: Optional summarizer instance (uses config.summarization_provider if None)
        """
        self.storage = storage
        self.config = config
        self.embedding_cache = embedding_cache

        # Initialize summarizer from config if not provided
        if summarizer is not None:
            self.summarizer = summarizer
        else:
            try:
                summarizer_config = config_from_main_config(config)
                # Treat 0.00 as no cost limit (None)
                cost_limit = config.summarization_monthly_cost_limit_usd
                if cost_limit is not None and cost_limit == 0.0:
                    cost_limit = None
                self.summarizer = get_summarizer(
                    provider=config.summarization_provider,
                    config=summarizer_config,
                    api_model=config.summarization_api_model,
                    api_max_tokens=config.summarization_api_max_tokens,
                    storage_dir=config.storage_dir,
                    monthly_cost_limit=cost_limit,
                )
                logger.debug(
                    "Initialized summarizer with provider: %s",
                    config.summarization_provider,
                )
            except (ImportError, ValueError) as e:
                # Fall back to regex summarizer if API setup fails
                logger.warning(
                    "Failed to initialize %s summarizer, falling back to regex: %s",
                    config.summarization_provider,
                    e,
                )
                summarizer_config = config_from_main_config(config)
                self.summarizer = get_summarizer(
                    provider="regex",
                    config=summarizer_config,
                )

    def should_swap(self, context: ConversationContext) -> bool:
        """Determine if swap-out should be triggered.

        Args:
            context: Current conversation context

        Returns:
            True if swap should be triggered
        """
        # Calculate current token count
        current_tokens = context.token_count

        # Calculate threshold
        threshold = int(self.config.threshold_tokens * self.config.swap_trigger_percent)

        # Check if we've exceeded threshold and it's safe
        return current_tokens > threshold and is_safe_to_swap(context)

    def swap_out(
        self,
        project: str,
        messages: list[Message],
        embedding_provider: EmbeddingProvider | None = None,
    ) -> tuple[list[Chunk], list[Message], str]:
        """Perform swap-out operation.

        Chunks older messages, generates summaries, stores to disk,
        and returns summary for session continuity.

        Args:
            project: Project identifier
            messages: All conversation messages
            embedding_provider: Optional embedding provider for semantic search

        Returns:
            Tuple of (swapped_chunks, remaining_messages, combined_summary)
            swapped_chunks: Chunks that were swapped to disk
            remaining_messages: Messages to keep in active context
            combined_summary: Summary of swapped content for continuity
        """
        metrics = get_metrics()
        swap_start = time.perf_counter()

        logger.info(
            "Starting swap operation for project '%s' with %d messages",
            project,
            len(messages),
        )

        # Chunk messages, preserving recent context
        chunk_start = time.perf_counter()
        chunks_to_swap, messages_to_keep = chunker.chunk_messages(
            messages,
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            preserve_recent=self.config.preserve_recent_tokens,
        )
        chunk_time = (time.perf_counter() - chunk_start) * 1000
        logger.debug(
            "Chunking completed in %.2fms: %d chunks to swap", chunk_time, len(chunks_to_swap)
        )

        if not chunks_to_swap:
            # Nothing to swap
            logger.info("No chunks to swap (under threshold)")
            return [], messages, "No context swapped (under threshold)"

        # Phase 1: Process all chunks and collect texts for batched embedding
        chunk_data: list[ChunkData] = []
        chunk_texts: list[str] = []

        for chunk_messages in chunks_to_swap:
            # Convert to text
            chunk_text = messages_to_text(chunk_messages)

            # Generate summary and keywords using configured summarizer
            summary = self.summarizer.summarize(
                chunk_text,
                max_length=self.config.summarization_api_max_tokens,
                context=f"Project: {project}",
            )
            keywords = self.summarizer.extract_keywords(chunk_text, max_keywords=12)

            # Estimate tokens
            token_count = estimate_tokens(chunk_text)

            # Extract metadata
            metadata = self._extract_metadata(chunk_messages)

            # Store chunk data for later
            chunk_data.append(
                ChunkData(
                    text=chunk_text,
                    summary=summary,
                    keywords=keywords,
                    token_count=token_count,
                    metadata=metadata,
                )
            )
            chunk_texts.append(chunk_text)

        # Phase 2: Generate embeddings in a single batched API call
        # Skip if vector store is in use (ChromaDB generates embeddings automatically)
        # First check cache, then generate remaining embeddings
        embeddings: list[list[float]] = []
        uses_vector_store = self.storage.vector_store is not None
        if uses_vector_store:
            logger.debug(
                "Vector store enabled - skipping manual embedding generation "
                "(ChromaDB will generate embeddings automatically)"
            )
            embeddings = [[] for _ in chunk_texts]  # Empty embeddings, ChromaDB handles it
        elif embedding_provider is not None and chunk_texts:
            # Check cache for existing embeddings
            cached_embeddings = []
            texts_to_generate = []
            text_indices_to_generate = []

            if self.embedding_cache:
                cached_embeddings = self.embedding_cache.batch_get(chunk_texts)
                # Identify which texts need generation
                for i, cached in enumerate(cached_embeddings):
                    if cached is None:
                        texts_to_generate.append(chunk_texts[i])
                        text_indices_to_generate.append(i)
            else:
                # No cache, generate all
                texts_to_generate = chunk_texts
                text_indices_to_generate = list(range(len(chunk_texts)))
                cached_embeddings = [None] * len(chunk_texts)

            # Generate embeddings for texts not in cache
            generated_embeddings: list[list[float]] = []
            if texts_to_generate:
                try:
                    generated_embeddings = embedding_provider.embed(texts_to_generate)

                    # Cache newly generated embeddings
                    if self.embedding_cache:
                        self.embedding_cache.batch_put(texts_to_generate, generated_embeddings)

                    logger.info(
                        "Successfully generated %d embeddings for swap",
                        len(generated_embeddings),
                    )

                except PermanentError as e:
                    # Permanent errors (e.g., invalid API key) - log and continue
                    logger.warning(
                        "Embedding generation failed permanently "
                        "(continuing without embeddings): %s",
                        str(e),
                    )
                    generated_embeddings = [[] for _ in texts_to_generate]

                except TransientError as e:
                    # Transient errors after retries exhausted - log and continue
                    logger.warning(
                        "Embedding generation failed after retries "
                        "(continuing without embeddings): %s",
                        str(e),
                    )
                    generated_embeddings = [[] for _ in texts_to_generate]

                except Exception as e:
                    # Unknown errors - log with full details and continue
                    logger.exception(
                        "Unexpected error during embedding generation "
                        "(continuing without embeddings): %s",
                        str(e),
                    )
                    generated_embeddings = [[] for _ in texts_to_generate]

            # Combine cached and generated embeddings
            embeddings = []
            generated_idx = 0
            for cached in cached_embeddings:
                if cached is not None:
                    embeddings.append(cached)
                elif generated_idx < len(generated_embeddings):
                    embeddings.append(generated_embeddings[generated_idx])
                    generated_idx += 1
                else:
                    embeddings.append([])

        # Ensure we have the right number of embeddings (fallback to empty if batch failed)
        if len(embeddings) != len(chunk_texts):
            embeddings = [[] for _ in chunk_texts]

        # Phase 3: Create and store chunks with embeddings
        storage_start = time.perf_counter()
        swapped_chunks = []
        for i, data in enumerate(chunk_data):
            embedding = embeddings[i] if i < len(embeddings) else []

            # Create chunk
            chunk = Chunk.create(
                project=project,
                content=data["text"],
                summary=data["summary"],
                keywords=data["keywords"],
                token_count=data["token_count"],
                embedding=embedding,
                metadata=cast(dict[str, Any], data["metadata"]),
            )

            # Store chunk
            self.storage.append_chunk(chunk)
            swapped_chunks.append(chunk)

        storage_time = (time.perf_counter() - storage_start) * 1000
        logger.debug("Storage write completed in %.2fms", storage_time)

        # Generate combined summary
        combined_summary = self._create_combined_summary(swapped_chunks)

        # Record metrics
        total_time = (time.perf_counter() - swap_start) * 1000
        total_tokens = sum(c.token_count for c in swapped_chunks)

        with metrics.measure(
            MetricsCollector.SWAP,
            project=project,
            chunks_swapped=len(swapped_chunks),
            tokens_swapped=total_tokens,
            messages_kept=len(messages_to_keep),
        ) as ctx:
            ctx["duration_ms"] = total_time

        logger.info(
            "Swap completed for '%s': %d chunks, %d tokens in %.2fms",
            project,
            len(swapped_chunks),
            total_tokens,
            total_time,
        )

        return swapped_chunks, messages_to_keep, combined_summary

    def _extract_metadata(self, messages: list[Message]) -> SwappedChunkMetadata:
        """Extract metadata from chunk messages.

        Args:
            messages: Messages in the chunk

        Returns:
            Metadata dictionary with structured type information
        """
        metadata: SwappedChunkMetadata = {}

        # Count tool calls
        total_tool_calls = sum(len(msg.tool_calls) for msg in messages)
        if total_tool_calls > 0:
            metadata["tool_calls_count"] = total_tool_calls

        # Extract file references from content
        # Simple heuristic: look for common file patterns
        files: set[str] = set()
        for msg in messages:
            content = msg.content
            # Look for file paths (simple pattern)
            matches = re.findall(r"(?:\.{0,2}/)?[\w\-]+(?:/[\w\-\.]+)*\.[\w]+", content)
            files.update(matches)

        if files:
            metadata["files_referenced"] = list(files)[:10]  # Limit to 10

        # Add message count
        metadata["message_count"] = len(messages)

        return metadata

    def _create_combined_summary(self, chunks: list[Chunk]) -> str:
        """Create a combined summary optimized for post-clear bridge.

        This summary is used by the SessionStart hook to maintain context
        continuity after /clear is executed. It should provide enough
        information for Claude to understand what was discussed without
        being too verbose.

        Args:
            chunks: List of chunks that were swapped

        Returns:
            Combined summary text optimized for context bridge
        """
        if not chunks:
            return "No chunks swapped."

        # Collect all topics and key information
        all_keywords: set[str] = set()
        all_files: set[str] = set()
        summaries: list[str] = []
        user_topics: list[str] = []
        work_items: list[str] = []

        for chunk in chunks:
            # Gather keywords (limit per chunk to avoid noise)
            all_keywords.update(chunk.keywords[:5])

            # Gather file references
            if chunk.metadata.get("files_referenced"):
                all_files.update(chunk.metadata["files_referenced"])

            # Collect summaries and extract structured info
            summary = chunk.summary
            summaries.append(summary)

            # Parse structured information from summaries
            lines = summary.split("\n")
            for line in lines:
                line_stripped = line.strip()
                # Extract user topics
                if line_stripped.startswith("User asked about:"):
                    continue  # Header line
                elif line_stripped.startswith("User discussed:"):
                    topic = line_stripped.replace("User discussed:", "").strip()
                    if topic and len(topic) > 10:
                        user_topics.append(topic[:150])
                elif line_stripped.startswith("- ") and "User" in summary[:50]:
                    # Bullet under "User asked about"
                    item = line_stripped[2:].strip()
                    if item and len(item) > 5:
                        user_topics.append(item[:150])

                # Extract work items from assistant actions
                if line_stripped.startswith("Assistant worked on:"):
                    continue  # Header line
                elif line_stripped.startswith("Discussion:"):
                    work = line_stripped.replace("Discussion:", "").strip()
                    if work and len(work) > 10:
                        work_items.append(work[:150])
                elif line_stripped.startswith("- ") and "Assistant" in summary[:100]:
                    item = line_stripped[2:].strip()
                    if item and len(item) > 5:
                        work_items.append(item[:150])

        total_tokens = sum(c.token_count for c in chunks)

        # Build structured bridge summary
        lines = [
            "### Swapped Context Summary",
            "",
            f"**Scope:** {len(chunks)} conversation segment(s), {total_tokens:,} tokens",
            "",
        ]

        # Add key topics if we have keywords
        if all_keywords:
            sorted_keywords = sorted(all_keywords)[:12]  # Limit to 12 keywords
            lines.append("**Key Topics:** " + ", ".join(sorted_keywords))

        # Add file references if present
        if all_files:
            sorted_files = sorted(all_files)[:8]  # Limit to 8 files
            lines.append("**Files Referenced:** " + ", ".join(sorted_files))

        # Add "What You Were Working On" section
        lines.extend(["", "**What You Were Working On:**"])

        # Combine user topics and work items, deduplicate
        seen_items: set[str] = set()
        combined_items: list[str] = []

        for item in user_topics + work_items:
            item_lower = item.lower()[:50]  # Use first 50 chars for dedup
            if item_lower not in seen_items:
                seen_items.add(item_lower)
                combined_items.append(item)

        if combined_items:
            for i, item in enumerate(combined_items[:5], 1):  # Limit to 5 items
                lines.append(f"{i}. {item}")
        else:
            # Fallback: extract from segment summaries
            lines.append("(See segment summaries below)")

        # Add segment summaries
        lines.extend(["", "**Segment Summaries:**"])

        for i, summary in enumerate(summaries, 1):
            # Truncate long summaries to keep bridge concise
            short_summary = summary[:197] + "..." if len(summary) > 200 else summary
            lines.append(f"{i}. {short_summary}")

        return "\n".join(lines)
