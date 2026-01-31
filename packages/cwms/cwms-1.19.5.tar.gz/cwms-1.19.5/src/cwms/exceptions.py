"""Exception hierarchy for cwms.

This module defines a structured exception hierarchy for all errors
that can occur during context window management operations. The hierarchy
is organized by functional area:

Exception Hierarchy:
--------------------
ContextWindowManagementError (base)
├── StorageError
│   ├── StorageCorruptionError
│   ├── StorageValidationError
│   └── LockTimeoutError
├── VectorStoreError
│   └── VectorStoreSyncError
├── CacheError
├── ConfigurationError
└── RetrievalError

Note: StorageCorruptionError, StorageValidationError, and LockTimeoutError
are currently defined in storage.py and will be migrated to this module
in a future refactoring.
"""

from __future__ import annotations


class ContextWindowManagementError(Exception):
    """Base exception for all cwms errors.

    All custom exceptions in this package should inherit from this class
    to allow for easy catching of any cwms-specific error.
    """

    pass


class StorageError(ContextWindowManagementError):
    """Base class for storage-related errors.

    Raised when operations on the storage layer (JSONL files, indexes, journals)
    encounter errors that prevent reading or writing data.
    """

    pass


class StorageCorruptionError(StorageError):
    """Raised when storage files are corrupted or unreadable.

    This indicates that the storage files (JSONL, index.json, or journal files)
    are in an invalid state and cannot be parsed or recovered automatically.
    Manual intervention may be required.
    """

    pass


class StorageValidationError(StorageError):
    """Raised when data fails storage validation checks.

    This occurs when data being stored or retrieved does not match the
    expected schema or constraints (e.g., missing required fields,
    invalid types, or data integrity violations).
    """

    pass


class LockTimeoutError(StorageError):
    """Raised when unable to acquire a file lock within the timeout period.

    This occurs when multiple processes or sessions attempt to access
    the same storage files concurrently, and the file lock cannot be
    acquired within the configured timeout.
    """

    pass


class VectorStoreError(ContextWindowManagementError):
    """Base class for vector store errors.

    Raised when operations on the vector store (ChromaDB) encounter errors
    that prevent storing, querying, or managing embeddings.
    """

    pass


class VectorStoreSyncError(VectorStoreError):
    """Raised when vector store becomes out of sync with storage.

    This occurs when the vector store's embeddings and metadata do not
    match the chunks stored in the JSONL storage layer. This can happen
    due to incomplete operations, crashes, or manual file modifications.
    """

    pass


class CacheError(ContextWindowManagementError):
    """Base class for cache-related errors.

    Raised when operations on internal caches (e.g., BM25 statistics cache,
    embedding cache) encounter errors that prevent proper caching behavior.
    """

    pass


class ConfigurationError(ContextWindowManagementError):
    """Raised for invalid configuration.

    This occurs when configuration files contain invalid values, required
    settings are missing, or configuration validation fails. Examples include
    invalid threshold values, unsupported embedding providers, or malformed
    config files.
    """

    pass


class RetrievalError(ContextWindowManagementError):
    """Raised for retrieval/search errors.

    This occurs when searching for or retrieving swapped context chunks
    fails due to issues with the retrieval system (BM25, semantic search,
    or hybrid search). This does not include storage-level errors.
    """

    pass
