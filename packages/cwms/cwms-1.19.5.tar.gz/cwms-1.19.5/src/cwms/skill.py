"""
cwms skill integration for Claude Code.

Provides the main ContextWindowManagementSkill class that coordinates context monitoring,
swapping, and retrieval operations. This module serves as the primary
interface between Claude Code and the cwms memory system.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cwms.chunker import ConversationContext, Message
from cwms.config import Config
from cwms.embedding_cache import EmbeddingCache
from cwms.embeddings import EmbeddingProvider, get_embedding_provider
from cwms.retriever import Retriever
from cwms.storage import Storage
from cwms.swapper import Swapper
from cwms.tokens import estimate_tokens


@dataclass
class ContextWindowManagementStatus:
    """Status information about the cwms system."""

    project: str
    total_chunks: int
    total_tokens: int
    oldest_chunk: str | None
    newest_chunk: str | None
    embedding_provider: str
    storage_dir: Path
    current_session_tokens: int


class ContextWindowManagementSkill:
    """
    Main skill class for cwms context memory management.

    Coordinates between storage, swapping, and retrieval components
    to provide transparent context management for Claude Code.

    Attributes:
        config: Configuration settings
        storage: Storage backend for chunks
        embedding_provider: Provider for generating embeddings
        swapper: Handles swap-out operations
        retriever: Handles context retrieval
        current_project: Current project identifier
    """

    def __init__(
        self,
        config: Config | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        model_name: str | None = None,
    ) -> None:
        """
        Initialize the cwms skill.

        Args:
            config: Configuration (loads default if not provided)
            embedding_provider: Embedding provider (creates from config if not provided)
            model_name: Optional model name for context window adaptation
        """
        self.config = config or Config.load_or_default()

        # Apply model-aware settings if threshold is set to "auto"
        self.config.with_model_adaptation(model_name)
        self.storage = Storage(self.config.storage_dir)

        # Initialize embedding provider
        if embedding_provider is None:
            self.embedding_provider = get_embedding_provider(
                self.config.embedding_provider,
                self._get_embedding_model(),
            )
        else:
            self.embedding_provider = embedding_provider

        # Initialize embedding cache (only if not using NoEmbeddings)
        self.embedding_cache: EmbeddingCache | None = None
        if self.config.embedding_provider.lower() != "none":
            cache_dir = self.config.storage_dir / "embedding_cache"
            self.embedding_cache = EmbeddingCache(
                cache_dir=cache_dir,
                ttl_days=self.config.max_age_days,
                max_entries=10000,  # Default max entries
            )

        # Initialize core components
        self.swapper = Swapper(self.storage, self.config, embedding_cache=self.embedding_cache)
        self.retriever = Retriever(
            self.storage, self.config, embedding_provider=self.embedding_provider
        )

        # Track current project and session state
        self.current_project: str | None = None
        self.current_session_tokens: int = 0

    def _get_embedding_model(self) -> str | None:
        """Get the embedding model name from config based on provider."""
        provider = self.config.embedding_provider.lower()
        models = {
            "none": None,
            "local": self.config.local_model,
        }
        return models.get(provider)

    def should_swap(self, context: ConversationContext) -> bool:
        """
        Check if context should be swapped out.

        Args:
            context: Current conversation context

        Returns:
            True if swap should be triggered
        """
        return self.swapper.should_swap(context)

    def swap_out(self, project: str, messages: list[Message]) -> tuple[int, int, str]:
        """
        Perform swap-out operation.

        Args:
            project: Project identifier
            messages: All conversation messages

        Returns:
            Tuple of (chunks_swapped, tokens_swapped, summary)
        """
        chunks, remaining, summary = self.swapper.swap_out(
            project, messages, embedding_provider=self.embedding_provider
        )

        # Update session tracking
        self.current_project = project
        self.current_session_tokens = sum(estimate_tokens(m.content) for m in remaining)

        return len(chunks), sum(c.token_count for c in chunks), summary

    def retrieve(self, project: str, query: str, top_k: int | None = None) -> str:
        """
        Retrieve relevant context for a query.

        Args:
            project: Project identifier
            query: Search query
            top_k: Number of results to return (uses config default if not specified)

        Returns:
            Formatted context string ready for injection
        """
        k = top_k or self.config.retrieval_top_k
        return self.retriever.retrieve_and_format(project, query, top_k=k)

    def search(self, project: str, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """
        Search for relevant chunks (returns structured results).

        Args:
            project: Project identifier
            query: Search query
            top_k: Number of results to return

        Returns:
            List of result dictionaries with score, summary, timestamp, etc.
        """
        k = top_k or self.config.retrieval_top_k
        results = self.retriever.query(project, query, top_k=k)

        return [
            {
                "timestamp": r.chunk.timestamp,
                "summary": r.chunk.summary,
                "keywords": r.chunk.keywords,
                "token_count": r.chunk.token_count,
                "score": r.score,
                "match_reason": r.match_reason,
            }
            for r in results
        ]

    def get_status(self, project: str) -> ContextWindowManagementStatus:
        """
        Get current status for a project.

        Args:
            project: Project identifier

        Returns:
            ContextWindowManagementStatus with current state
        """
        index = self.storage.get_index(project)

        if not index:
            return ContextWindowManagementStatus(
                project=project,
                total_chunks=0,
                total_tokens=0,
                oldest_chunk=None,
                newest_chunk=None,
                embedding_provider=self.config.embedding_provider,
                storage_dir=self.config.storage_dir,
                current_session_tokens=self.current_session_tokens,
            )

        # Calculate totals
        total_chunks = len(index)
        total_tokens = sum(idx.token_count for idx in index)

        # Find oldest and newest
        sorted_chunks = sorted(index, key=lambda x: x.timestamp)
        oldest = sorted_chunks[0].timestamp if sorted_chunks else None
        newest = sorted_chunks[-1].timestamp if sorted_chunks else None

        return ContextWindowManagementStatus(
            project=project,
            total_chunks=total_chunks,
            total_tokens=total_tokens,
            oldest_chunk=oldest,
            newest_chunk=newest,
            embedding_provider=self.config.embedding_provider,
            storage_dir=self.config.storage_dir,
            current_session_tokens=self.current_session_tokens,
        )

    def get_summaries(self, project: str) -> list[dict[str, Any]]:
        """
        Get summaries of all stored chunks for a project.

        Args:
            project: Project identifier

        Returns:
            List of summary dictionaries
        """
        index = self.storage.get_index(project)

        return [
            {
                "id": idx.id,
                "timestamp": idx.timestamp,
                "summary": idx.summary,
                "keywords": idx.keywords,
                "token_count": idx.token_count,
            }
            for idx in sorted(index, key=lambda x: x.timestamp, reverse=True)
        ]

    def clear_project(self, project: str) -> bool:
        """
        Clear all stored context for a project.

        Args:
            project: Project identifier

        Returns:
            True if project existed and was deleted, False otherwise
        """
        # Check if project has any chunks
        index = self.storage.get_index(project)
        if not index:
            return False

        # Delete the project
        self.storage.delete_project(project)
        return True

    def export_chunk(self, project: str, chunk_id: str) -> dict[str, Any] | None:
        """
        Export a specific chunk's full content.

        Args:
            project: Project identifier
            chunk_id: Chunk ID to export

        Returns:
            Chunk data as dictionary, or None if not found
        """
        chunks = self.storage.read_chunks(project)
        for chunk in chunks:
            if chunk.id == chunk_id:
                return {
                    "id": chunk.id,
                    "project": chunk.project,
                    "timestamp": chunk.timestamp,
                    "content": chunk.content,
                    "summary": chunk.summary,
                    "keywords": chunk.keywords,
                    "token_count": chunk.token_count,
                    "metadata": chunk.metadata,
                    "has_embedding": len(chunk.embedding) > 0,
                }
        return None

    def format_status_display(self, status: ContextWindowManagementStatus) -> str:
        """
        Format status information for display.

        Args:
            status: Status object

        Returns:
            Formatted status string
        """
        lines = [
            "=== Context Window Management Status ===",
            f"Project: {status.project}",
            f"Total Chunks: {status.total_chunks}",
            f"Total Tokens Stored: {status.total_tokens:,}",
            f"Current Session Tokens: {status.current_session_tokens:,}",
            f"Embedding Provider: {status.embedding_provider}",
            f"Storage Directory: {status.storage_dir}",
        ]

        if status.oldest_chunk:
            lines.append(f"Oldest Chunk: {status.oldest_chunk}")
        if status.newest_chunk:
            lines.append(f"Newest Chunk: {status.newest_chunk}")

        return "\n".join(lines)

    def format_search_results(self, results: list[dict[str, Any]]) -> str:
        """
        Format search results for display.

        Args:
            results: List of result dictionaries

        Returns:
            Formatted results string
        """
        if not results:
            return "No results found."

        lines = ["=== Context Window Management Search Results ==="]
        for i, result in enumerate(results, 1):
            lines.extend(
                [
                    f"\n{i}. [{result['timestamp']}] (Score: {result['score']:.2f})",
                    f"   {result['summary']}",
                    f"   Keywords: {', '.join(result['keywords'][:5])}",
                    f"   Tokens: {result['token_count']:,}",
                    f"   Match: {result['match_reason']}",
                ]
            )

        return "\n".join(lines)


def create_skill(
    config_path: Path | None = None,
    embedding_provider: str | None = None,
    model_name: str | None = None,
) -> ContextWindowManagementSkill:
    """
    Factory function to create a ContextWindowManagementSkill instance.

    Args:
        config_path: Optional path to configuration file
        embedding_provider: Optional embedding provider override
        model_name: Optional model name for context window adaptation

    Returns:
        Initialized ContextWindowManagementSkill instance
    """
    config = Config.from_yaml(config_path) if config_path else Config.load_or_default()

    # Override embedding provider if specified
    if embedding_provider:
        config.embedding_provider = embedding_provider

    return ContextWindowManagementSkill(config=config, model_name=model_name)
