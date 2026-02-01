"""Disk-based cache for embeddings to avoid redundant generation.

This module provides a cache for embeddings keyed by content hash (SHA256).
Useful for reducing API costs and improving performance when similar content
is encountered multiple times.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


class EmbeddingCache:
    """Disk-based cache for embeddings.

    Stores embeddings keyed by SHA256 hash of content. Supports TTL and size limits.
    Cache entries are stored as JSONL for efficient append operations.

    Attributes:
        cache_dir: Directory where cache files are stored
        ttl_days: Time-to-live in days (None = no expiration)
        max_entries: Maximum number of cache entries (None = unlimited)
    """

    def __init__(
        self,
        cache_dir: Path,
        ttl_days: int | None = 30,
        max_entries: int | None = 10000,
    ):
        """Initialize embedding cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_days: Cache entry time-to-live in days (None = no expiration)
            max_entries: Maximum number of cache entries (None = unlimited)
        """
        self.cache_dir = cache_dir
        self.ttl_days = ttl_days
        self.max_entries = max_entries

        # Create cache directory if needed
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory index for fast lookups (hash -> cache entry)
        self._index: dict[str, dict[str, Any]] = {}
        self._load_index()

    def get(self, text: str) -> list[float] | None:
        """Get cached embedding for text.

        Args:
            text: Text content to look up

        Returns:
            Cached embedding vector, or None if not found or expired
        """
        content_hash = self._hash_text(text)

        # Check in-memory index
        if content_hash not in self._index:
            return None

        entry = self._index[content_hash]

        # Check if expired
        if self._is_expired(entry):
            # Remove from index (will be excluded from next save)
            del self._index[content_hash]
            return None

        embedding: list[float] = entry["embedding"]
        return embedding

    def put(self, text: str, embedding: list[float]) -> None:
        """Cache an embedding for text.

        Args:
            text: Text content
            embedding: Embedding vector to cache
        """
        content_hash = self._hash_text(text)

        # Create cache entry
        entry = {
            "hash": content_hash,
            "embedding": embedding,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "text_length": len(text),
        }

        # Add to in-memory index
        self._index[content_hash] = entry

        # Check if we need to prune
        if self.max_entries and len(self._index) > self.max_entries:
            self._prune_oldest()
            # Pruning rebuilds the entire file, so no need to append
            return

        # Persist to disk (only if we didn't prune)
        self._save_entry(entry)

    def batch_get(self, texts: list[str]) -> list[list[float] | None]:
        """Get cached embeddings for multiple texts.

        Args:
            texts: List of text content to look up

        Returns:
            List of embeddings (or None for cache misses), one per input text
        """
        return [self.get(text) for text in texts]

    def batch_put(self, texts: list[str], embeddings: list[list[float]]) -> None:
        """Cache embeddings for multiple texts.

        Args:
            texts: List of text content
            embeddings: List of embedding vectors (same length as texts)

        Raises:
            ValueError: If texts and embeddings have different lengths
        """
        if len(texts) != len(embeddings):
            raise ValueError(
                f"texts and embeddings must have same length: {len(texts)} != {len(embeddings)}"
            )

        for text, embedding in zip(texts, embeddings, strict=True):
            self.put(text, embedding)

    def clear(self) -> int:
        """Clear all cached embeddings.

        Returns:
            Number of entries cleared
        """
        count = len(self._index)
        self._index.clear()

        # Remove cache file
        cache_file = self.cache_dir / "embeddings.jsonl"
        if cache_file.exists():
            cache_file.unlink()

        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self._index)
        expired_count = sum(1 for entry in self._index.values() if self._is_expired(entry))

        cache_file = self.cache_dir / "embeddings.jsonl"
        file_size = cache_file.stat().st_size if cache_file.exists() else 0

        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_count,
            "expired_entries": expired_count,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
            "ttl_days": self.ttl_days,
            "max_entries": self.max_entries,
        }

    def _hash_text(self, text: str) -> str:
        """Generate SHA256 hash of text content.

        Args:
            text: Text to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _is_expired(self, entry: dict[str, Any]) -> bool:
        """Check if cache entry is expired.

        Args:
            entry: Cache entry dictionary

        Returns:
            True if expired, False otherwise
        """
        if self.ttl_days is None:
            return False

        timestamp = datetime.fromisoformat(entry["timestamp"])
        now = datetime.now(tz=UTC)
        age = now - timestamp

        return age > timedelta(days=self.ttl_days)

    def _load_index(self) -> None:
        """Load cache index from disk."""
        cache_file = self.cache_dir / "embeddings.jsonl"

        if not cache_file.exists():
            return

        # Load all entries from JSONL
        with open(cache_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)

                    # Skip expired entries
                    if not self._is_expired(entry):
                        self._index[entry["hash"]] = entry

    def _save_entry(self, entry: dict[str, Any]) -> None:
        """Append cache entry to disk.

        Args:
            entry: Cache entry to save
        """
        cache_file = self.cache_dir / "embeddings.jsonl"

        # Append entry to JSONL file
        with open(cache_file, "a", encoding="utf-8") as f:
            json.dump(entry, f)
            f.write("\n")

    def _prune_oldest(self) -> None:
        """Prune oldest cache entries to stay under max_entries limit."""
        if not self.max_entries:
            return

        # Sort by timestamp (oldest first)
        sorted_entries = sorted(self._index.values(), key=lambda e: e["timestamp"])

        # Calculate how many to remove
        to_remove = len(sorted_entries) - self.max_entries

        if to_remove <= 0:
            return

        # Remove oldest entries from index
        for entry in sorted_entries[:to_remove]:
            del self._index[entry["hash"]]

        # Rebuild cache file without removed entries
        self._rebuild_cache_file()

    def _rebuild_cache_file(self) -> None:
        """Rebuild cache file from current index (removes pruned/expired entries)."""
        cache_file = self.cache_dir / "embeddings.jsonl"

        # Write all current index entries to file
        with open(cache_file, "w", encoding="utf-8") as f:
            for entry in self._index.values():
                json.dump(entry, f)
                f.write("\n")
