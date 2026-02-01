"""Storage layer for swapped context chunks using JSONL format."""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import re
import sys
import tempfile
import time
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cwms.exceptions import VectorStoreSyncError
from cwms.metrics import MetricsCollector, get_metrics

if TYPE_CHECKING:
    from cwms.bm25 import BM25Statistics
    from cwms.vector_store import VectorStore

# Set up module logger
logger = logging.getLogger(__name__)


class StorageCorruptionError(Exception):
    """Raised when storage corruption is detected."""

    pass


class StorageValidationError(Exception):
    """Raised when storage validation fails."""

    pass


class LockTimeoutError(Exception):
    """Raised when unable to acquire a file lock within the timeout period."""

    pass


class FileLock:
    """Cross-platform file locking with timeout and graceful degradation.

    Uses fcntl on Unix/macOS and msvcrt on Windows. Supports both blocking
    and non-blocking modes with configurable timeout.

    Example:
        with FileLock(project_dir / "chunks.lock") as lock:
            if lock.acquired:
                # Perform write operations
                pass
            else:
                # Lock contention - skip or retry
                logger.warning("Could not acquire lock, skipping operation")
    """

    def __init__(
        self,
        lock_path: Path,
        timeout: float = 5.0,
        blocking: bool = True,
    ):
        """Initialize file lock.

        Args:
            lock_path: Path to the lock file (will be created if needed)
            timeout: Maximum time in seconds to wait for lock (default: 5.0)
            blocking: If True, wait up to timeout; if False, fail immediately
        """
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self.blocking = blocking
        self._lock_file: Any = None
        self._acquired = False

    @property
    def acquired(self) -> bool:
        """Whether the lock was successfully acquired."""
        return self._acquired

    def _acquire_unix(self) -> bool:
        """Acquire lock on Unix/macOS using fcntl."""
        import fcntl

        start_time = time.time()
        retry_interval = 0.05  # 50ms between retries

        while True:
            try:
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                if not self.blocking:
                    return False
                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    return False
                time.sleep(min(retry_interval, self.timeout - elapsed))
                retry_interval = min(retry_interval * 1.5, 0.5)  # Exponential backoff

    def _acquire_windows(self) -> bool:
        """Acquire lock on Windows using msvcrt."""
        import msvcrt

        start_time = time.time()
        retry_interval = 0.05  # 50ms between retries

        while True:
            try:
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined]
                return True
            except OSError:
                if not self.blocking:
                    return False
                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    return False
                time.sleep(min(retry_interval, self.timeout - elapsed))
                retry_interval = min(retry_interval * 1.5, 0.5)

    def _release_unix(self) -> None:
        """Release lock on Unix/macOS."""
        import fcntl

        fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)

    def _release_windows(self) -> None:
        """Release lock on Windows."""
        import msvcrt

        with contextlib.suppress(OSError):
            # Already unlocked or file closed
            msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]

    def __enter__(self) -> FileLock:
        """Acquire the lock."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = open(self.lock_path, "w")

        try:
            if sys.platform == "win32":
                self._acquired = self._acquire_windows()
            else:
                self._acquired = self._acquire_unix()

            if not self._acquired:
                logger.warning(
                    f"Lock contention detected on {self.lock_path.name}. "
                    f"Another process may be writing to the same project."
                )
        except Exception as e:
            logger.error(f"Failed to acquire lock on {self.lock_path}: {e}")
            self._acquired = False

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Release the lock."""
        if self._lock_file:
            try:
                if self._acquired:
                    if sys.platform == "win32":
                        self._release_windows()
                    else:
                        self._release_unix()
            except Exception as e:
                logger.warning(f"Error releasing lock: {e}")
            finally:
                self._lock_file.close()
                self._lock_file = None
                self._acquired = False


@contextmanager
def project_lock(
    project_dir: Path,
    timeout: float = 5.0,
    required: bool = False,
) -> Iterator[bool]:
    """Context manager for locking a project directory.

    Provides a simpler interface for project-level locking.

    Args:
        project_dir: Project directory to lock
        timeout: Lock timeout in seconds
        required: If True, raise LockTimeoutError if lock can't be acquired

    Yields:
        True if lock was acquired, False otherwise

    Raises:
        LockTimeoutError: If required=True and lock couldn't be acquired
    """
    lock = FileLock(project_dir / "write.lock", timeout=timeout)
    with lock:
        if required and not lock.acquired:
            raise LockTimeoutError(
                f"Could not acquire lock on {project_dir} within {timeout}s. "
                "Another process may be writing to the same project."
            )
        yield lock.acquired


@contextmanager
def atomic_write(file_path: Path, mode: str = "w") -> Iterator[Any]:
    """Context manager for atomic file writes.

    Writes to a temporary file first, then atomically renames to the target.
    This ensures that if the process is interrupted, the original file
    remains intact.

    Args:
        file_path: Target file path
        mode: File mode ('w' for text, 'wb' for binary)

    Yields:
        File handle for writing

    Raises:
        Exception: Re-raises any exception after cleanup
    """
    # Create temp file in same directory to ensure same filesystem (for atomic rename)
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        dir=file_path.parent,
        prefix=f".{file_path.name}.",
        suffix=".tmp",
    )

    try:
        # Close the file descriptor, we'll open with proper mode
        os.close(fd)
        with open(temp_path, mode, encoding="utf-8" if "b" not in mode else None) as f:
            yield f
        # Atomic rename (POSIX guarantees this is atomic on same filesystem)
        os.replace(temp_path, file_path)
    except Exception:
        # Clean up temp file on any error
        with contextlib.suppress(OSError):
            os.unlink(temp_path)
        raise


@contextmanager
def atomic_append(file_path: Path) -> Iterator[Any]:
    """Context manager for atomic append operations.

    For append operations, we need to:
    1. Read existing content
    2. Write existing + new content to temp file
    3. Atomic rename

    Args:
        file_path: Target file path

    Yields:
        Tuple of (existing_lines, new_lines_list) where new_lines_list
        should be appended to by the caller
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing content
    existing_lines: list[str] = []
    if file_path.exists():
        with open(file_path, encoding="utf-8") as f:
            existing_lines = f.readlines()

    new_lines: list[str] = []

    yield new_lines

    # Write all content atomically
    fd, temp_path = tempfile.mkstemp(
        dir=file_path.parent,
        prefix=f".{file_path.name}.",
        suffix=".tmp",
    )
    try:
        os.close(fd)
        with open(temp_path, "w", encoding="utf-8") as f:
            f.writelines(existing_lines)
            f.writelines(new_lines)
        os.replace(temp_path, file_path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(temp_path)
        raise


@dataclass
class JournalEntry:
    """A journal entry for tracking multi-file operations."""

    operation: str  # 'append_chunk', 'delete_chunk', etc.
    chunk_id: str
    timestamp: str
    files_to_write: list[str]  # Files intended to be written
    files_written: list[str]  # Files successfully written
    status: str  # 'started', 'completed', 'failed'

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JournalEntry:
        """Create from dictionary."""
        # Handle legacy entries without files_to_write
        if "files_to_write" not in data:
            data["files_to_write"] = []
        return cls(**data)


class Journal:
    """Write-ahead journal for multi-file atomic operations.

    The journal ensures that multi-file operations can be recovered
    from interruption. On startup, incomplete operations are either
    rolled forward or rolled back to maintain consistency.
    """

    def __init__(self, journal_file: Path):
        """Initialize journal.

        Args:
            journal_file: Path to the journal file
        """
        self.journal_file = Path(journal_file)
        self.journal_file.parent.mkdir(parents=True, exist_ok=True)

    def start_operation(self, operation: str, chunk_id: str, files: list[str]) -> JournalEntry:
        """Record the start of a multi-file operation.

        Args:
            operation: Operation type (e.g., 'append_chunk')
            chunk_id: ID of chunk being operated on
            files: List of files that will be written

        Returns:
            JournalEntry for tracking progress
        """
        entry = JournalEntry(
            operation=operation,
            chunk_id=chunk_id,
            timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            files_to_write=files,
            files_written=[],
            status="started",
        )
        self._write_entry(entry)
        return entry

    def mark_file_written(self, entry: JournalEntry, file_path: str) -> None:
        """Mark a file as successfully written.

        Args:
            entry: Journal entry to update
            file_path: Path of file that was written
        """
        entry.files_written.append(file_path)
        self._write_entry(entry)

    def complete_operation(self, entry: JournalEntry) -> None:
        """Mark operation as completed successfully.

        Args:
            entry: Journal entry to complete
        """
        entry.status = "completed"
        self._write_entry(entry)
        # Clear journal after successful completion
        self._clear_journal()

    def fail_operation(self, entry: JournalEntry) -> None:
        """Mark operation as failed.

        Args:
            entry: Journal entry to mark failed
        """
        entry.status = "failed"
        self._write_entry(entry)

    def _write_entry(self, entry: JournalEntry) -> None:
        """Write entry to journal file atomically."""
        with atomic_write(self.journal_file) as f:
            json.dump(entry.to_dict(), f)
            f.write("\n")

    def _clear_journal(self) -> None:
        """Clear the journal file after successful operation."""
        if self.journal_file.exists():
            self.journal_file.unlink()

    def get_incomplete_operation(self) -> JournalEntry | None:
        """Get any incomplete operation from the journal.

        Returns:
            JournalEntry if there's an incomplete operation, None otherwise
        """
        if not self.journal_file.exists():
            return None

        try:
            with open(self.journal_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        entry = JournalEntry.from_dict(data)
                        if entry.status != "completed":
                            return entry
        except (json.JSONDecodeError, OSError):
            # Corrupted journal, clear it
            self._clear_journal()
            return None

        return None


def validate_jsonl_line(line: str, line_num: int, file_path: Path) -> dict[str, Any]:
    """Validate and parse a single JSONL line.

    Args:
        line: The line to parse
        line_num: Line number (for error messages)
        file_path: File path (for error messages)

    Returns:
        Parsed JSON data

    Raises:
        StorageCorruptionError: If the line is invalid JSON
    """
    try:
        data: dict[str, Any] = json.loads(line)
        return data
    except json.JSONDecodeError as e:
        raise StorageCorruptionError(
            f"Corrupted data in {file_path} at line {line_num}: {e}"
        ) from e


def validate_chunk_data(data: dict[str, Any], file_path: Path) -> None:
    """Validate that chunk data has required fields.

    Args:
        data: Chunk data dictionary
        file_path: File path (for error messages)

    Raises:
        StorageValidationError: If required fields are missing
    """
    required_fields = ["id", "project", "timestamp", "content", "summary", "keywords"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise StorageValidationError(f"Chunk in {file_path} missing required fields: {missing}")


def validate_metadata_data(data: dict[str, Any], file_path: Path) -> None:
    """Validate that metadata has required fields.

    Args:
        data: Metadata data dictionary
        file_path: File path (for error messages)

    Raises:
        StorageValidationError: If required fields are missing
    """
    required_fields = ["id", "project", "timestamp", "summary", "keywords"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise StorageValidationError(f"Metadata in {file_path} missing required fields: {missing}")


@dataclass
class Chunk:
    """A swapped context chunk with metadata."""

    id: str
    project: str
    timestamp: str
    content: str
    summary: str
    keywords: list[str]
    token_count: int
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        project: str,
        content: str,
        summary: str,
        keywords: list[str],
        token_count: int,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Chunk:
        """Create a new chunk with auto-generated ID and timestamp.

        Args:
            project: Project identifier
            content: Full conversation chunk text
            summary: Brief summary for retrieval
            keywords: Extracted keywords
            token_count: Token count of content
            embedding: Optional embedding vector
            metadata: Optional metadata dict

        Returns:
            New Chunk instance
        """
        import uuid

        return cls(
            id=str(uuid.uuid4()),
            project=project,
            timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            content=content,
            summary=summary,
            keywords=keywords,
            token_count=token_count,
            embedding=embedding or [],
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert chunk to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chunk:
        """Create chunk from dictionary."""
        return cls(**data)


@dataclass
class ChunkMetadata:
    """Chunk metadata without content - used for efficient searches.

    This dataclass contains all chunk fields except the large 'content' field,
    allowing for efficient memory usage during search operations.
    """

    id: str
    project: str
    timestamp: str
    summary: str
    keywords: list[str]
    token_count: int
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_chunk(cls, chunk: Chunk) -> ChunkMetadata:
        """Create metadata from full chunk."""
        return cls(
            id=chunk.id,
            project=chunk.project,
            timestamp=chunk.timestamp,
            summary=chunk.summary,
            keywords=chunk.keywords,
            token_count=chunk.token_count,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChunkMetadata:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ChunkIndex:
    """Lightweight index entry for fast lookup without loading full content.

    .. deprecated:: 1.14.0
        Use :class:`ChunkMetadata` instead, which includes embedding support.
        ChunkIndex will be removed in version 2.0.0.

    Note: This is deprecated in favor of ChunkMetadata which includes embeddings.
    Kept for backward compatibility.
    """

    id: str
    timestamp: str
    summary: str
    keywords: list[str]
    token_count: int
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Emit deprecation warning on instantiation."""
        warnings.warn(
            "ChunkIndex is deprecated and will be removed in version 2.0.0. "
            "Use ChunkMetadata instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    @classmethod
    def from_chunk(cls, chunk: Chunk) -> ChunkIndex:
        """Create index entry from full chunk."""
        return cls(
            id=chunk.id,
            timestamp=chunk.timestamp,
            summary=chunk.summary,
            keywords=chunk.keywords,
            token_count=chunk.token_count,
            metadata=chunk.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChunkIndex:
        """Create from dictionary."""
        return cls(**data)


class Storage:
    """JSONL-based storage for swapped context chunks.

    Supports multi-session safety through file locking. When multiple
    terminal windows access the same project, file locks prevent
    concurrent writes from corrupting storage.

    Optionally integrates with a VectorStore for efficient semantic search.
    When a vector store is provided, documents are automatically indexed
    with embeddings generated by the vector store (e.g., ChromaDB).
    """

    def __init__(
        self,
        base_dir: Path,
        cache_size: int = 20,
        validate_on_read: bool = True,
        lock_timeout: float = 5.0,
        use_locking: bool = True,
        vector_store: VectorStore | None = None,
    ):
        """Initialize storage with base directory.

        Args:
            base_dir: Base directory for all swapfiles
            cache_size: Maximum number of chunks to cache (default: 20)
            validate_on_read: Whether to validate data on read (default: True)
            lock_timeout: Seconds to wait for file lock (default: 5.0)
            use_locking: Whether to use file locking for writes (default: True)
            vector_store: Optional vector store for semantic search indexing
        """
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cache_size = cache_size
        self._validate_on_read = validate_on_read
        self._lock_timeout = lock_timeout
        self._use_locking = use_locking
        self._vector_store = vector_store
        # Cache stores (project, chunk_id) -> Chunk
        self._chunk_cache: dict[tuple[str, str], Chunk] = {}
        self._cache_order: list[tuple[str, str]] = []
        # Recover any incomplete operations on initialization
        self._recover_incomplete_operations()

    def _recover_incomplete_operations(self) -> None:
        """Recover from any incomplete operations on startup.

        Checks each project's journal for incomplete operations and
        either rolls them forward or rebuilds affected files.
        """
        for project_dir in self.base_dir.iterdir():
            if project_dir.is_dir():
                journal_file = project_dir / "journal.json"
                if journal_file.exists():
                    journal = Journal(journal_file)
                    incomplete = journal.get_incomplete_operation()
                    if incomplete:
                        # Get project name from mapping
                        mapping_file = project_dir / "project.txt"
                        if mapping_file.exists():
                            project = mapping_file.read_text(encoding="utf-8").strip()
                            self._recover_operation(project, incomplete, journal)

    def _recover_operation(self, project: str, entry: JournalEntry, journal: Journal) -> None:
        """Recover from an incomplete operation.

        For append_chunk operations with partial writes, rebuild secondary
        files (metadata, index, stats) from the primary chunks file.

        Args:
            project: Project identifier
            entry: The incomplete journal entry
            journal: Journal instance for cleanup
        """
        chunks_file = self._get_chunks_file(project)

        # If this was an append_chunk operation and chunks file was written,
        # rebuild secondary files from the primary data
        if entry.operation == "append_chunk" and str(chunks_file) in entry.files_written:
            self.rebuild_index(project)
            self.rebuild_bm25_statistics(project)

        # Clear the journal after recovery
        journal._clear_journal()

    def _get_journal(self, project: str) -> Journal:
        """Get journal for a project.

        Args:
            project: Project identifier

        Returns:
            Journal instance for the project
        """
        return Journal(self._get_project_dir(project) / "journal.json")

    def _get_project_dir(self, project: str) -> Path:
        """Get directory for project's swapfiles.

        Args:
            project: Project identifier

        Returns:
            Path to project directory
        """
        # Use hash of project name for directory (handles special chars)
        project_hash = hashlib.sha256(project.encode()).hexdigest()[:16]
        project_dir = self.base_dir / project_hash
        project_dir.mkdir(parents=True, exist_ok=True)

        # Store project name mapping
        mapping_file = project_dir / "project.txt"
        if not mapping_file.exists():
            mapping_file.write_text(project, encoding="utf-8")

        return project_dir

    def _get_chunks_file(self, project: str) -> Path:
        """Get path to chunks JSONL file."""
        return self._get_project_dir(project) / "chunks.jsonl"

    def _get_metadata_file(self, project: str) -> Path:
        """Get path to metadata JSONL file (chunk data without content)."""
        return self._get_project_dir(project) / "metadata.jsonl"

    def _get_index_file(self, project: str) -> Path:
        """Get path to index JSONL file (append-only, lightweight).

        Note: This now uses JSONL format for O(1) append operations.
        The old index.json format is kept for backward compatibility.
        """
        return self._get_project_dir(project) / "index.jsonl"

    def _get_legacy_index_file(self, project: str) -> Path:
        """Get path to legacy index JSON file (for migration)."""
        return self._get_project_dir(project) / "index.json"

    def _get_statistics_file(self, project: str) -> Path:
        """Get path to BM25 statistics file."""
        return self._get_project_dir(project) / "bm25_stats.json"

    def append_chunk(
        self,
        chunk: Chunk,
        use_journal: bool = True,
        skip_if_locked: bool = True,
    ) -> bool:
        """Append a chunk to project's swapfile with atomic writes.

        Uses journaling to ensure multi-file consistency. If interrupted,
        the operation can be recovered on next startup.

        Uses file locking to prevent concurrent writes from corrupting storage.
        If another process holds the lock, behavior depends on skip_if_locked:
        - If True (default): logs a warning and returns False
        - If False: raises LockTimeoutError after timeout

        Args:
            chunk: Chunk to append
            use_journal: Whether to use journaling (default: True)
            skip_if_locked: If True, skip operation if lock unavailable;
                           if False, raise LockTimeoutError (default: True)

        Returns:
            True if chunk was appended, False if skipped due to lock contention

        Raises:
            LockTimeoutError: If skip_if_locked=False and lock unavailable
        """
        project_dir = self._get_project_dir(chunk.project)
        chunks_file = self._get_chunks_file(chunk.project)
        metadata_file = self._get_metadata_file(chunk.project)
        index_file = self._get_index_file(chunk.project)
        stats_file = self._get_statistics_file(chunk.project)

        # Use file locking if enabled
        if self._use_locking:
            with project_lock(
                project_dir,
                timeout=self._lock_timeout,
                required=not skip_if_locked,
            ) as lock_acquired:
                if not lock_acquired:
                    logger.warning(
                        f"Skipping append for project {chunk.project}: "
                        "another process is writing."
                    )
                    return False
                return self._append_chunk_inner(
                    chunk,
                    use_journal,
                    chunks_file,
                    metadata_file,
                    index_file,
                    stats_file,
                )
        else:
            return self._append_chunk_inner(
                chunk,
                use_journal,
                chunks_file,
                metadata_file,
                index_file,
                stats_file,
            )

    def _append_chunk_inner(
        self,
        chunk: Chunk,
        use_journal: bool,
        chunks_file: Path,
        metadata_file: Path,
        index_file: Path,
        stats_file: Path,
    ) -> bool:
        """Inner implementation of append_chunk (called within lock context).

        Args:
            chunk: Chunk to append
            use_journal: Whether to use journaling
            chunks_file: Path to chunks file
            metadata_file: Path to metadata file
            index_file: Path to index file
            stats_file: Path to stats file

        Returns:
            True if successful
        """
        metrics = get_metrics()
        start_time = time.time()

        logger.debug(
            "Appending chunk %s to project '%s' (%d tokens)",
            chunk.id[:8],
            chunk.project,
            chunk.token_count,
        )

        files_to_write = [
            str(chunks_file),
            str(metadata_file),
            str(index_file),
            str(stats_file),
        ]

        journal = self._get_journal(chunk.project) if use_journal else None
        entry = None

        try:
            if journal:
                entry = journal.start_operation("append_chunk", chunk.id, files_to_write)

            # 1. Write to chunks JSONL file (primary data) - atomic append
            with atomic_append(chunks_file) as new_lines:
                new_lines.append(json.dumps(chunk.to_dict()) + "\n")
            if journal and entry:
                journal.mark_file_written(entry, str(chunks_file))

            # 2. Write to metadata JSONL file - atomic append
            metadata = ChunkMetadata.from_chunk(chunk)
            with atomic_append(metadata_file) as new_lines:
                new_lines.append(json.dumps(metadata.to_dict()) + "\n")
            if journal and entry:
                journal.mark_file_written(entry, str(metadata_file))

            # 3. Update index - atomic append
            index_entry = ChunkIndex.from_chunk(chunk)
            with atomic_append(index_file) as new_lines:
                new_lines.append(json.dumps(index_entry.to_dict()) + "\n")
            if journal and entry:
                journal.mark_file_written(entry, str(index_file))

            # 4. Update BM25 statistics - atomic write (full file)
            self._update_bm25_statistics(chunk)
            if journal and entry:
                journal.mark_file_written(entry, str(stats_file))

            # 5. Add to vector store if available (for semantic search)
            if self._vector_store is not None:
                try:
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
                    logger.debug("Added chunk %s to vector store", chunk.id[:8])
                except Exception as e:
                    # Log error and record desync for later recovery
                    logger.error(
                        "Vector store sync failed for chunk %s: %s. "
                        "Storage succeeded but vector store is out of sync.",
                        chunk.id[:8],
                        str(e),
                    )
                    self._record_vector_store_desync(chunk.id, chunk.project)
                    raise VectorStoreSyncError(
                        f"Storage succeeded but vector store failed for chunk "
                        f"{chunk.id[:8]}: {e}"
                    ) from e

            # Mark operation complete
            if journal and entry:
                journal.complete_operation(entry)

            # Invalidate cache for this project
            self._invalidate_cache(chunk.project)

            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            with metrics.measure(
                MetricsCollector.STORAGE_WRITE,
                project=chunk.project,
                chunk_id=chunk.id[:8],
                token_count=chunk.token_count,
            ) as ctx:
                ctx["duration_ms"] = duration_ms

            logger.debug("Chunk %s appended in %.2fms", chunk.id[:8], duration_ms)
            return True

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "Failed to append chunk %s after %.2fms: %s",
                chunk.id[:8],
                duration_ms,
                str(e),
            )
            if journal and entry:
                journal.fail_operation(entry)
            raise

    def _update_index(self, chunk: Chunk) -> None:
        """Update index with new chunk entry.

        Uses append-only JSONL format for O(1) performance.

        Args:
            chunk: Chunk to add to index
        """
        index_file = self._get_index_file(chunk.project)
        index_entry = ChunkIndex.from_chunk(chunk)

        # Append to JSONL index file (O(1) operation)
        with open(index_file, "a", encoding="utf-8") as f:
            json.dump(index_entry.to_dict(), f)
            f.write("\n")

    def _update_bm25_statistics(self, chunk: Chunk) -> None:
        """Update BM25 statistics with a new chunk.

        Args:
            chunk: Chunk to add to statistics
        """

        stats = self.get_bm25_statistics(chunk.project)

        # Collect terms from keywords and summary
        terms = [kw.lower() for kw in chunk.keywords]
        summary_tokens = re.findall(r"\b\w+\b", chunk.summary.lower())
        terms.extend(summary_tokens)

        stats.add_document(terms, chunk.token_count)
        self.save_bm25_statistics(chunk.project, stats)

    def get_bm25_statistics(self, project: str) -> BM25Statistics:
        """Load BM25 statistics for a project.

        Args:
            project: Project identifier

        Returns:
            BM25Statistics instance (empty if file doesn't exist)
        """
        from cwms.bm25 import BM25Statistics

        stats_file = self._get_statistics_file(project)

        if not stats_file.exists():
            return BM25Statistics()

        with open(stats_file, encoding="utf-8") as f:
            data = json.load(f)

        return BM25Statistics.from_dict(data)

    def save_bm25_statistics(self, project: str, stats: BM25Statistics) -> None:
        """Save BM25 statistics for a project atomically.

        Args:
            project: Project identifier
            stats: Statistics to save
        """
        stats_file = self._get_statistics_file(project)

        with atomic_write(stats_file) as f:
            json.dump(stats.to_dict(), f, indent=2)

    def rebuild_bm25_statistics(self, project: str) -> BM25Statistics:
        """Rebuild BM25 statistics from all chunks.

        Useful for:
        1. Initial migration when stats file doesn't exist
        2. Recovery from corruption
        3. After manual chunk modifications

        Args:
            project: Project identifier

        Returns:
            Rebuilt BM25Statistics instance
        """
        from cwms.bm25 import BM25Statistics

        stats = BM25Statistics()
        metadata_list = self.read_chunks_metadata(project)

        for metadata in metadata_list:
            # Collect terms from keywords and summary
            terms = [kw.lower() for kw in metadata.keywords]
            summary_tokens = re.findall(r"\b\w+\b", metadata.summary.lower())
            terms.extend(summary_tokens)

            stats.add_document(terms, metadata.token_count)

        # Save rebuilt statistics
        self.save_bm25_statistics(project, stats)

        return stats

    def _invalidate_cache(self, project: str | None = None) -> None:
        """Invalidate chunk cache for a project or all projects.

        Args:
            project: Project to invalidate, or None for all projects
        """
        if project is None:
            # Clear entire cache
            self._chunk_cache.clear()
            self._cache_order.clear()
        else:
            # Remove all entries for this project using dict comprehension (more efficient)
            self._chunk_cache = {k: v for k, v in self._chunk_cache.items() if k[0] != project}
            self._cache_order = [k for k in self._cache_order if k[0] != project]

    def _record_vector_store_desync(self, chunk_id: str, project: str) -> None:
        """Record a vector store desync for later recovery.

        When a chunk is successfully written to storage but fails to be added
        to the vector store, we record this desync in a JSON file. This allows
        for later recovery operations to resync the vector store with storage.

        Args:
            chunk_id: ID of the chunk that failed to sync to vector store
            project: Project identifier
        """
        project_dir = self._get_project_dir(project)
        desync_file = project_dir / "vector_store_desync.json"

        desync_entry = {
            "chunk_id": chunk_id,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

        # Read existing desyncs if file exists
        desyncs: list[dict[str, Any]] = []
        if desync_file.exists():
            try:
                with open(desync_file, encoding="utf-8") as f:
                    desyncs = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.debug("Could not read desync file, starting fresh: %s", str(e))
                desyncs = []

        # Append new entry
        desyncs.append(desync_entry)

        # Write atomically
        with atomic_write(desync_file) as f:
            json.dump(desyncs, f, indent=2)

        logger.debug("Recorded vector store desync for chunk %s", chunk_id[:8])

    def _add_to_cache(self, project: str, chunk_id: str, chunk: Chunk) -> None:
        """Add a chunk to the LRU cache.

        Args:
            project: Project identifier
            chunk_id: Chunk ID
            chunk: Chunk to cache
        """
        key = (project, chunk_id)

        # Remove if already in cache
        if key in self._chunk_cache:
            self._cache_order.remove(key)

        # Add to cache
        self._chunk_cache[key] = chunk
        self._cache_order.append(key)

        # Evict oldest if over limit
        while len(self._cache_order) > self._cache_size:
            oldest_key = self._cache_order.pop(0)
            del self._chunk_cache[oldest_key]

    def _get_from_cache(self, project: str, chunk_id: str) -> Chunk | None:
        """Get a chunk from cache if available.

        Args:
            project: Project identifier
            chunk_id: Chunk ID

        Returns:
            Cached chunk or None if not in cache
        """
        key = (project, chunk_id)
        if key in self._chunk_cache:
            # Move to end (most recently used)
            self._cache_order.remove(key)
            self._cache_order.append(key)
            return self._chunk_cache[key]
        return None

    def read_chunks(self, project: str) -> list[Chunk]:
        """Read all chunks for a project with optional validation.

        Warning: This loads ALL content into memory. For better performance,
        use read_chunks_metadata() for searches that don't need full content.

        Args:
            project: Project identifier

        Returns:
            List of all chunks for project

        Raises:
            StorageCorruptionError: If validation is enabled and corruption is detected
        """
        metrics = get_metrics()
        start_time = time.time()

        chunks_file = self._get_chunks_file(project)

        if not chunks_file.exists():
            logger.debug("No chunks file for project '%s'", project)
            return []

        logger.debug("Reading chunks for project '%s' from %s", project, chunks_file)

        chunks: list[Chunk] = []
        with open(chunks_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    if self._validate_on_read:
                        data = validate_jsonl_line(line, line_num, chunks_file)
                        validate_chunk_data(data, chunks_file)
                    else:
                        data = json.loads(line)
                    chunks.append(Chunk.from_dict(data))

        duration_ms = (time.time() - start_time) * 1000
        with metrics.measure(
            MetricsCollector.STORAGE_READ,
            project=project,
            chunk_count=len(chunks),
        ) as ctx:
            ctx["duration_ms"] = duration_ms

        logger.debug("Read %d chunks for '%s' in %.2fms", len(chunks), project, duration_ms)
        return chunks

    def read_chunks_metadata(self, project: str) -> list[ChunkMetadata]:
        """Read chunk metadata without loading content with optional validation.

        This is 80-90% more memory efficient than read_chunks() as it excludes
        the large 'content' field. Use this for search operations.

        Args:
            project: Project identifier

        Returns:
            List of chunk metadata (without content)

        Raises:
            StorageCorruptionError: If validation is enabled and corruption is detected
        """
        metadata_file = self._get_metadata_file(project)

        if not metadata_file.exists():
            # Fall back to reading from chunks file if metadata file doesn't exist
            # (for backward compatibility)
            return [ChunkMetadata.from_chunk(c) for c in self.read_chunks(project)]

        metadata_list: list[ChunkMetadata] = []
        with open(metadata_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    if self._validate_on_read:
                        data = validate_jsonl_line(line, line_num, metadata_file)
                        validate_metadata_data(data, metadata_file)
                    else:
                        data = json.loads(line)
                    metadata_list.append(ChunkMetadata.from_dict(data))

        return metadata_list

    def get_index(self, project: str) -> list[ChunkIndex]:
        """Load index (summaries + metadata) without full content.

        Supports both new JSONL format and legacy JSON format.

        Args:
            project: Project identifier

        Returns:
            List of index entries

        Raises:
            StorageCorruptionError: If validation is enabled and corruption is detected
        """
        index_file = self._get_index_file(project)
        legacy_index_file = self._get_legacy_index_file(project)

        # Try new JSONL format first
        if index_file.exists():
            index_entries: list[ChunkIndex] = []
            with open(index_file, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        if self._validate_on_read:
                            data = validate_jsonl_line(line, line_num, index_file)
                        else:
                            data = json.loads(line)
                        index_entries.append(ChunkIndex.from_dict(data))
            return index_entries

        # Fall back to legacy JSON format
        if legacy_index_file.exists():
            try:
                with open(legacy_index_file, encoding="utf-8") as f:
                    index_data = json.load(f)
                return [ChunkIndex.from_dict(entry) for entry in index_data]
            except json.JSONDecodeError as e:
                if self._validate_on_read:
                    raise StorageCorruptionError(
                        f"Corrupted legacy index file {legacy_index_file}: {e}"
                    ) from e
                raise

        return []

    def rebuild_index(self, project: str) -> None:
        """Rebuild index from chunks file.

        This can be used to:
        1. Migrate from legacy JSON format to new JSONL format
        2. Recover from index corruption
        3. Update index format after changes

        Args:
            project: Project identifier
        """
        chunks = self.read_chunks(project)

        # Clear existing index files
        index_file = self._get_index_file(project)
        if index_file.exists():
            index_file.unlink()

        # Rebuild index in JSONL format
        for chunk in chunks:
            self._update_index(chunk)

        # Also rebuild metadata file
        metadata_file = self._get_metadata_file(project)
        if metadata_file.exists():
            metadata_file.unlink()

        for chunk in chunks:
            metadata = ChunkMetadata.from_chunk(chunk)
            with open(metadata_file, "a", encoding="utf-8") as f:
                json.dump(metadata.to_dict(), f)
                f.write("\n")

    def search_keywords(self, project: str, keywords: list[str], limit: int = 10) -> list[Chunk]:
        """Search chunks by keyword overlap.

        Args:
            project: Project identifier
            keywords: Keywords to search for
            limit: Maximum number of results

        Returns:
            Chunks ordered by keyword overlap (most relevant first)
        """
        chunks = self.read_chunks(project)

        if not chunks or not keywords:
            return []

        # Normalize search keywords
        search_terms = {kw.lower() for kw in keywords}

        # Score each chunk by keyword overlap
        scored_chunks: list[tuple[int, Chunk]] = []
        for chunk in chunks:
            chunk_keywords = {kw.lower() for kw in chunk.keywords}
            overlap = len(search_terms & chunk_keywords)

            # Also check summary for keyword mentions
            summary_lower = chunk.summary.lower()
            summary_matches = sum(1 for term in search_terms if term in summary_lower)

            score = overlap + (summary_matches * 0.5)  # Weight exact keyword matches higher

            if score > 0:
                scored_chunks.append((int(score * 100), chunk))

        # Sort by score (descending) and return top results
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        return [chunk for _, chunk in scored_chunks[:limit]]

    def get_chunk_by_id(self, project: str, chunk_id: str) -> Chunk | None:
        """Retrieve specific chunk by ID with caching.

        Uses LRU cache for fast repeated access (100x speedup for cache hits).

        Args:
            project: Project identifier
            chunk_id: Chunk ID to retrieve

        Returns:
            Chunk if found, None otherwise

        Raises:
            StorageCorruptionError: If validation is enabled and corruption is detected
        """
        # Check cache first
        cached_chunk = self._get_from_cache(project, chunk_id)
        if cached_chunk is not None:
            return cached_chunk

        # Not in cache, read from disk
        chunks_file = self._get_chunks_file(project)
        if not chunks_file.exists():
            return None

        # Read through file to find chunk
        with open(chunks_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    if self._validate_on_read:
                        data = validate_jsonl_line(line, line_num, chunks_file)
                    else:
                        data = json.loads(line)
                    if data.get("id") == chunk_id:
                        if self._validate_on_read:
                            validate_chunk_data(data, chunks_file)
                        chunk = Chunk.from_dict(data)
                        # Add to cache before returning
                        self._add_to_cache(project, chunk_id, chunk)
                        return chunk

        return None

    def list_projects(self) -> list[str]:
        """List all projects with stored chunks.

        Returns:
            List of project identifiers
        """
        projects: list[str] = []

        for project_dir in self.base_dir.iterdir():
            if project_dir.is_dir():
                mapping_file = project_dir / "project.txt"
                if mapping_file.exists():
                    projects.append(mapping_file.read_text(encoding="utf-8").strip())

        return projects

    def get_total_tokens(self, project: str) -> int:
        """Get total token count for all chunks in project.

        Args:
            project: Project identifier

        Returns:
            Total token count
        """
        index = self.get_index(project)
        return sum(entry.token_count for entry in index)

    @property
    def vector_store(self) -> VectorStore | None:
        """Get the vector store if available.

        Returns:
            VectorStore instance or None if not configured
        """
        return self._vector_store

    def delete_project(self, project: str) -> None:
        """Delete all data for a project.

        Args:
            project: Project identifier
        """
        import shutil

        # Delete from vector store first if available
        if self._vector_store is not None:
            try:
                # Get all chunk IDs for this project and delete them
                chunk_ids = [c.id for c in self.read_chunks(project)]
                if chunk_ids:
                    self._vector_store.delete(chunk_ids)
                    logger.debug("Deleted %d chunks from vector store", len(chunk_ids))
            except Exception as e:
                logger.warning("Failed to delete from vector store: %s", str(e))

        project_dir = self._get_project_dir(project)
        if project_dir.exists():
            shutil.rmtree(project_dir)

    def validate_storage(self, project: str) -> dict[str, Any]:
        """Validate storage integrity for a project.

        Checks:
        1. Chunks file is valid JSONL with required fields
        2. Metadata file is valid JSONL with required fields
        3. Index file is valid JSONL
        4. BM25 stats file is valid JSON
        5. All files are consistent (same chunk IDs)

        Args:
            project: Project identifier

        Returns:
            Dict with validation results:
            {
                "valid": bool,
                "errors": list[str],
                "warnings": list[str],
                "chunks_count": int,
                "metadata_count": int,
                "index_count": int,
            }
        """
        errors: list[str] = []
        warnings: list[str] = []

        chunks_file = self._get_chunks_file(project)
        metadata_file = self._get_metadata_file(project)
        index_file = self._get_index_file(project)
        stats_file = self._get_statistics_file(project)

        chunk_ids: set[str] = set()
        metadata_ids: set[str] = set()
        index_ids: set[str] = set()
        chunks_count = 0
        metadata_count = 0
        index_count = 0

        # Validate chunks file
        if chunks_file.exists():
            with open(chunks_file, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            data = validate_jsonl_line(line, line_num, chunks_file)
                            validate_chunk_data(data, chunks_file)
                            chunk_ids.add(data["id"])
                            chunks_count += 1
                        except (StorageCorruptionError, StorageValidationError) as e:
                            errors.append(str(e))

        # Validate metadata file
        if metadata_file.exists():
            with open(metadata_file, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            data = validate_jsonl_line(line, line_num, metadata_file)
                            validate_metadata_data(data, metadata_file)
                            metadata_ids.add(data["id"])
                            metadata_count += 1
                        except (StorageCorruptionError, StorageValidationError) as e:
                            errors.append(str(e))

        # Validate index file
        if index_file.exists():
            with open(index_file, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            data = validate_jsonl_line(line, line_num, index_file)
                            index_ids.add(data.get("id", ""))
                            index_count += 1
                        except StorageCorruptionError as e:
                            errors.append(str(e))

        # Validate stats file
        if stats_file.exists():
            try:
                with open(stats_file, encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"Corrupted BM25 stats file {stats_file}: {e}")

        # Check consistency between files
        if chunk_ids and metadata_ids:
            missing_metadata = chunk_ids - metadata_ids
            extra_metadata = metadata_ids - chunk_ids
            if missing_metadata:
                warnings.append(f"Chunks missing from metadata file: {missing_metadata}")
            if extra_metadata:
                warnings.append(f"Extra entries in metadata file (orphaned): {extra_metadata}")

        if chunk_ids and index_ids:
            missing_index = chunk_ids - index_ids
            extra_index = index_ids - chunk_ids
            if missing_index:
                warnings.append(f"Chunks missing from index file: {missing_index}")
            if extra_index:
                warnings.append(f"Extra entries in index file (orphaned): {extra_index}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "chunks_count": chunks_count,
            "metadata_count": metadata_count,
            "index_count": index_count,
        }

    def repair(self, project: str, dry_run: bool = False) -> dict[str, Any]:
        """Repair storage for a project by rebuilding secondary files.

        This method:
        1. Validates the chunks file (primary data source)
        2. Rebuilds metadata file from valid chunks
        3. Rebuilds index file from valid chunks
        4. Rebuilds BM25 statistics from valid chunks
        5. Cleans up any temp files or incomplete operations

        Args:
            project: Project identifier
            dry_run: If True, only report what would be done without making changes

        Returns:
            Dict with repair results:
            {
                "success": bool,
                "actions": list[str],
                "chunks_recovered": int,
                "chunks_lost": int,
            }
        """
        actions: list[str] = []
        chunks_recovered = 0
        chunks_lost = 0

        project_dir = self._get_project_dir(project)
        chunks_file = self._get_chunks_file(project)
        metadata_file = self._get_metadata_file(project)
        index_file = self._get_index_file(project)
        journal_file = project_dir / "journal.json"

        # Clean up temp files
        for temp_file in project_dir.glob(".*tmp"):
            actions.append(f"Remove temp file: {temp_file.name}")
            if not dry_run:
                temp_file.unlink()

        # Clean up incomplete journal
        if journal_file.exists():
            actions.append("Remove incomplete journal")
            if not dry_run:
                journal_file.unlink()

        # Read valid chunks from primary file
        valid_chunks: list[Chunk] = []
        if chunks_file.exists():
            with open(chunks_file, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            data = validate_jsonl_line(line, line_num, chunks_file)
                            validate_chunk_data(data, chunks_file)
                            valid_chunks.append(Chunk.from_dict(data))
                            chunks_recovered += 1
                        except (StorageCorruptionError, StorageValidationError):
                            chunks_lost += 1
                            actions.append(f"Skip corrupted chunk at line {line_num}")

        if chunks_lost > 0:
            actions.append(f"Rewrite chunks file with {chunks_recovered} valid chunks")
            if not dry_run:
                # Rewrite chunks file with only valid chunks
                with atomic_write(chunks_file) as f:
                    for chunk in valid_chunks:
                        json.dump(chunk.to_dict(), f)
                        f.write("\n")

        # Rebuild metadata file
        actions.append(f"Rebuild metadata file with {chunks_recovered} entries")
        if not dry_run:
            with atomic_write(metadata_file) as f:
                for chunk in valid_chunks:
                    metadata = ChunkMetadata.from_chunk(chunk)
                    json.dump(metadata.to_dict(), f)
                    f.write("\n")

        # Rebuild index file
        actions.append(f"Rebuild index file with {chunks_recovered} entries")
        if not dry_run:
            with atomic_write(index_file) as f:
                for chunk in valid_chunks:
                    index_entry = ChunkIndex.from_chunk(chunk)
                    json.dump(index_entry.to_dict(), f)
                    f.write("\n")

        # Rebuild BM25 statistics
        actions.append("Rebuild BM25 statistics")
        if not dry_run:
            self.rebuild_bm25_statistics(project)

        # Invalidate cache
        if not dry_run:
            self._invalidate_cache(project)

        return {
            "success": True,
            "actions": actions,
            "chunks_recovered": chunks_recovered,
            "chunks_lost": chunks_lost,
        }
