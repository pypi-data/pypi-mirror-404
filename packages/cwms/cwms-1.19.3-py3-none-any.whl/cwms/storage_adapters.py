"""Storage adapters for vector store integration.

This module provides adapter protocols and implementations for integrating
vector stores with the storage layer. Adapters handle synchronization between
JSONL storage and vector stores (e.g., ChromaDB) during chunk operations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from cwms.exceptions import VectorStoreSyncError

if TYPE_CHECKING:
    from cwms.storage import Chunk
    from cwms.vector_store import VectorStore

logger = logging.getLogger(__name__)


class VectorStoreAdapter(Protocol):
    """Protocol for vector store integration with storage layer.

    Adapters handle synchronization between JSONL storage and vector stores
    during chunk lifecycle operations (add, delete, error rollback).
    """

    def on_chunk_added(self, chunk: Chunk, embeddings: list[float]) -> None:
        """Called when a chunk is successfully added to storage.

        Args:
            chunk: The chunk that was added
            embeddings: Embedding vector for the chunk

        Raises:
            VectorStoreSyncError: If vector store sync fails
        """
        ...

    def on_chunk_deleted(self, chunk_id: str) -> None:
        """Called when a chunk is successfully deleted from storage.

        Args:
            chunk_id: ID of the deleted chunk

        Raises:
            VectorStoreSyncError: If vector store sync fails
        """
        ...

    def on_storage_error(self, chunk_id: str, error: Exception) -> None:
        """Called when storage operation fails, allowing rollback.

        Args:
            chunk_id: ID of the chunk that failed to store
            error: The error that occurred
        """
        ...


class ChromaVectorStoreAdapter:
    """Adapter for ChromaDB vector store integration.

    Wraps ChromaVectorStore to provide storage lifecycle hooks for
    synchronizing chunks between JSONL storage and ChromaDB.

    Features:
    - Automatic vector store updates on chunk add/delete
    - Error rollback tracking for recovery
    - Proper metadata synchronization
    """

    def __init__(self, vector_store: VectorStore) -> None:
        """Initialize adapter.

        Args:
            vector_store: ChromaVectorStore instance to wrap
        """
        self._vector_store = vector_store
        self._pending_rollbacks: set[str] = set()

    def on_chunk_added(self, chunk: Chunk, embeddings: list[float]) -> None:  # noqa: ARG002
        """Add chunk to vector store when added to storage.

        Args:
            chunk: The chunk that was added to storage
            embeddings: Embedding vector for the chunk (unused - ChromaDB generates embeddings)

        Raises:
            VectorStoreSyncError: If adding to vector store fails
        """
        try:
            logger.debug("Adding chunk %s to vector store", chunk.id[:8])

            # Add to vector store with metadata
            self._vector_store.add(
                ids=[chunk.id],
                documents=[chunk.content],
                metadata=[
                    {
                        "project": chunk.project,
                        "timestamp": chunk.timestamp,
                        "token_count": chunk.token_count,
                        "summary": chunk.summary[:500] if chunk.summary else "",
                    }
                ],
            )

            logger.debug("Successfully added chunk %s to vector store", chunk.id[:8])

        except Exception as e:
            logger.error(
                "Failed to add chunk %s to vector store: %s",
                chunk.id[:8],
                str(e),
            )
            # Track for potential rollback
            self._pending_rollbacks.add(chunk.id)
            raise VectorStoreSyncError(
                f"Vector store sync failed for chunk {chunk.id[:8]}: {e}"
            ) from e

    def on_chunk_deleted(self, chunk_id: str) -> None:
        """Delete chunk from vector store when deleted from storage.

        Args:
            chunk_id: ID of the chunk to delete

        Raises:
            VectorStoreSyncError: If deletion from vector store fails
        """
        try:
            logger.debug("Deleting chunk %s from vector store", chunk_id[:8])

            self._vector_store.delete([chunk_id])

            # Remove from pending rollbacks if it was there
            self._pending_rollbacks.discard(chunk_id)

            logger.debug("Successfully deleted chunk %s from vector store", chunk_id[:8])

        except Exception as e:
            logger.error(
                "Failed to delete chunk %s from vector store: %s",
                chunk_id[:8],
                str(e),
            )
            raise VectorStoreSyncError(
                f"Vector store delete failed for chunk {chunk_id[:8]}: {e}"
            ) from e

    def on_storage_error(self, chunk_id: str, error: Exception) -> None:
        """Rollback vector store entry if storage operation failed.

        If a chunk was added to the vector store but storage failed,
        we need to remove it from the vector store to maintain consistency.

        Args:
            chunk_id: ID of the chunk that failed to store
            error: The storage error that occurred
        """
        if chunk_id in self._pending_rollbacks:
            try:
                logger.warning(
                    "Rolling back vector store entry for chunk %s due to storage error: %s",
                    chunk_id[:8],
                    str(error),
                )

                self._vector_store.delete([chunk_id])
                self._pending_rollbacks.discard(chunk_id)

                logger.debug("Successfully rolled back chunk %s from vector store", chunk_id[:8])

            except Exception as rollback_error:
                logger.error(
                    "Failed to rollback chunk %s from vector store: %s",
                    chunk_id[:8],
                    str(rollback_error),
                )
                # Keep in pending rollbacks for manual recovery


class NullVectorStoreAdapter:
    """Null adapter that does nothing.

    Used when no vector store is configured. All operations are no-ops.
    """

    def on_chunk_added(self, chunk: Chunk, embeddings: list[float]) -> None:
        """No-op."""
        pass

    def on_chunk_deleted(self, chunk_id: str) -> None:
        """No-op."""
        pass

    def on_storage_error(self, chunk_id: str, error: Exception) -> None:
        """No-op."""
        pass
