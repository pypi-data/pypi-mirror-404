"""Vector store abstraction with ChromaDB backend.

This module provides a unified interface for vector storage and similarity search,
with ChromaDB as the primary backend. ChromaDB handles both embedding generation
(via sentence-transformers) and vector indexing (via HNSW).
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class VectorStore(Protocol):
    """Protocol for vector storage backends.

    All vector store implementations must provide these methods for
    storing embeddings and performing similarity search.
    """

    def add(
        self,
        ids: list[str],
        documents: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents to the store. Embeddings are generated automatically.

        Args:
            ids: Unique identifiers for each document
            documents: Text content to embed and store
            metadata: Optional metadata for each document
        """
        ...

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Query for similar documents.

        Args:
            query_text: Text to find similar documents for
            top_k: Number of results to return
            where: Optional metadata filter

        Returns:
            List of (id, distance, metadata) tuples, sorted by similarity
        """
        ...

    def delete(self, ids: list[str]) -> None:
        """Delete documents by ID.

        Args:
            ids: List of document IDs to delete
        """
        ...

    def count(self) -> int:
        """Return number of documents in store.

        Returns:
            Total document count
        """
        ...

    def get_ids(self) -> list[str]:
        """Get all document IDs in the store.

        Returns:
            List of all document IDs
        """
        ...


class NoVectorStore:
    """Null implementation that does nothing.

    Used when vector storage is disabled (provider: none).
    All operations are no-ops that return empty results.
    """

    def add(
        self,
        ids: list[str],
        documents: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """No-op add."""
        pass

    def query(
        self,
        query_text: str,  # noqa: ARG002
        top_k: int = 5,  # noqa: ARG002
        where: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Return empty results."""
        return []

    def delete(self, ids: list[str]) -> None:
        """No-op delete."""
        pass

    def count(self) -> int:
        """Return zero."""
        return 0

    def get_ids(self) -> list[str]:
        """Return empty list."""
        return []


class ChromaVectorStore:
    """ChromaDB-backed vector store with automatic embedding generation.

    Uses ChromaDB's PersistentClient for disk-based storage and HNSW indexing.
    Embeddings are generated automatically using sentence-transformers via
    ChromaDB's built-in embedding function.

    Features:
    - Automatic embedding generation (no manual embedding management)
    - HNSW index for O(log n) similarity search
    - Persistent storage with SQLite backend
    - Per-project collection isolation
    """

    def __init__(
        self,
        persist_dir: Path,
        collection_name: str,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        """Initialize ChromaDB vector store.

        Args:
            persist_dir: Directory for persistent storage
            collection_name: Name of the collection (typically project-based)
            model_name: Sentence-transformers model for embeddings

        Raises:
            ImportError: If chromadb is not installed
        """
        try:
            import chromadb
            from chromadb.utils.embedding_functions import (
                SentenceTransformerEmbeddingFunction,
            )
        except ImportError as e:
            raise ImportError(
                "chromadb is required for vector storage. " "Install with: pip install chromadb"
            ) from e

        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.collection_name = collection_name
        self.model_name = model_name

        logger.debug(
            "Initializing ChromaDB at %s with collection '%s'",
            self.persist_dir,
            self.collection_name,
        )

        # Initialize ChromaDB client with persistent storage
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))

        # Create embedding function using sentence-transformers
        self._embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=model_name,
        )

        # Get or create collection with cosine similarity
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embedding_fn,  # type: ignore[arg-type]
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            "ChromaDB initialized: collection '%s' with %d documents",
            self.collection_name,
            self._collection.count(),
        )

    def add(
        self,
        ids: list[str],
        documents: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents to ChromaDB. Embeddings are generated automatically.

        Args:
            ids: Unique identifiers for each document
            documents: Text content to embed and store
            metadata: Optional metadata for each document

        Raises:
            ValueError: If ids and documents have different lengths
        """
        if not ids:
            return

        if len(ids) != len(documents):
            raise ValueError(
                f"ids and documents must have same length: {len(ids)} != {len(documents)}"
            )

        if metadata is not None and len(metadata) != len(ids):
            raise ValueError(
                f"metadata must have same length as ids: {len(metadata)} != {len(ids)}"
            )

        logger.debug("Adding %d documents to collection '%s'", len(ids), self.collection_name)

        # Filter out any existing IDs to avoid duplicates
        existing_ids = set(self.get_ids())
        new_indices = [i for i, doc_id in enumerate(ids) if doc_id not in existing_ids]

        if not new_indices:
            logger.debug("All documents already exist, skipping add")
            return

        new_ids = [ids[i] for i in new_indices]
        new_documents = [documents[i] for i in new_indices]
        new_metadata = [metadata[i] for i in new_indices] if metadata else None

        # Add to ChromaDB (embeddings generated automatically)
        self._collection.add(
            ids=new_ids,
            documents=new_documents,
            metadatas=new_metadata,  # type: ignore[arg-type]
        )

        logger.info(
            "Added %d documents to '%s' (skipped %d existing)",
            len(new_ids),
            self.collection_name,
            len(ids) - len(new_ids),
        )

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Query for similar documents using ChromaDB's HNSW index.

        Args:
            query_text: Text to find similar documents for
            top_k: Number of results to return
            where: Optional metadata filter (ChromaDB where clause)

        Returns:
            List of (id, similarity_score, metadata) tuples.
            Scores are converted from distance to similarity (1 - distance for cosine).
        """
        if self._collection.count() == 0:
            return []

        logger.debug(
            "Querying collection '%s' for top %d similar to: %s...",
            self.collection_name,
            top_k,
            query_text[:50],
        )

        # Query ChromaDB
        results = self._collection.query(
            query_texts=[query_text],
            n_results=min(top_k, self._collection.count()),
            where=where,
            include=["distances", "metadatas"],
        )

        # Convert results to list of tuples
        output: list[tuple[str, float, dict[str, Any]]] = []

        if results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            # ChromaDB returns distances, convert to similarity for cosine
            # cosine distance = 1 - cosine_similarity, so similarity = 1 - distance
            distances = results["distances"][0] if results["distances"] else [0.0] * len(ids)
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)

            for doc_id, distance, meta in zip(ids, distances, metadatas, strict=True):
                # Convert distance to similarity score
                similarity = 1.0 - distance
                # Convert ChromaDB metadata type to dict[str, Any]
                meta_dict: dict[str, Any] = dict(meta) if meta else {}
                output.append((doc_id, similarity, meta_dict))

        logger.debug("Query returned %d results", len(output))
        return output

    def delete(self, ids: list[str]) -> None:
        """Delete documents from ChromaDB by ID.

        Args:
            ids: List of document IDs to delete
        """
        if not ids:
            return

        logger.debug("Deleting %d documents from collection '%s'", len(ids), self.collection_name)

        # Filter to only existing IDs
        existing_ids = set(self.get_ids())
        ids_to_delete = [doc_id for doc_id in ids if doc_id in existing_ids]

        if ids_to_delete:
            self._collection.delete(ids=ids_to_delete)
            logger.info("Deleted %d documents from '%s'", len(ids_to_delete), self.collection_name)

    def count(self) -> int:
        """Return number of documents in the collection.

        Returns:
            Total document count
        """
        count: int = self._collection.count()
        return count

    def get_ids(self) -> list[str]:
        """Get all document IDs in the collection.

        Returns:
            List of all document IDs
        """
        result = self._collection.get(include=[])
        ids: list[str] = result["ids"] if result["ids"] else []
        return ids

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary with collection stats
        """
        return {
            "collection_name": self.collection_name,
            "document_count": self._collection.count(),
            "persist_dir": str(self.persist_dir),
            "model_name": self.model_name,
        }


def get_collection_name(project: str) -> str:
    """Generate a valid ChromaDB collection name from project identifier.

    ChromaDB collection names must:
    - Be 3-63 characters
    - Start and end with alphanumeric
    - Contain only alphanumeric, underscores, hyphens
    - Not contain consecutive periods

    Args:
        project: Project identifier (may contain special characters)

    Returns:
        Valid collection name
    """
    # Hash the project name for consistency
    project_hash = hashlib.sha256(project.encode()).hexdigest()[:12]

    # Create a sanitized prefix from project name
    sanitized = "".join(c if c.isalnum() else "_" for c in project[:20])
    sanitized = sanitized.strip("_") or "project"

    # Combine: prefix + hash
    collection_name = f"cwm_{sanitized}_{project_hash}"

    # Ensure valid length (3-63 chars)
    if len(collection_name) > 63:
        collection_name = collection_name[:63]

    return collection_name


def get_vector_store(
    provider: str,
    persist_dir: Path | None = None,
    project: str | None = None,
    model_name: str = "all-MiniLM-L6-v2",
) -> VectorStore:
    """Factory function to create vector store instances.

    Args:
        provider: Provider name ("none" or "local")
        persist_dir: Directory for persistent storage (required for "local")
        project: Project identifier (required for "local")
        model_name: Sentence-transformers model name

    Returns:
        VectorStore instance

    Raises:
        ValueError: If provider is unknown or required args missing
        ImportError: If chromadb is not installed for "local" provider

    Examples:
        >>> store = get_vector_store("none")  # No-op store
        >>> store = get_vector_store("local", persist_dir=Path("./chroma"), project="my-project")
    """
    provider = provider.lower()

    if provider == "none":
        return NoVectorStore()

    if provider == "local":
        if persist_dir is None:
            raise ValueError("persist_dir is required for 'local' vector store")
        if project is None:
            raise ValueError("project is required for 'local' vector store")

        collection_name = get_collection_name(project)
        return ChromaVectorStore(
            persist_dir=persist_dir,
            collection_name=collection_name,
            model_name=model_name,
        )

    raise ValueError(f"Unknown vector store provider: {provider}. Valid options: none, local")
