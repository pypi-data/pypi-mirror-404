"""Constants used throughout cwms.

This module centralizes magic numbers and configuration defaults
to improve maintainability and make values easier to find and modify.
"""

# ============================================================================
# Cache Settings
# ============================================================================

CACHE_TTL_SECONDS: float = 300.0  # 5 minutes - TTL for retriever caches
QUERY_CACHE_MAX_ENTRIES: int = 100  # Maximum cached query results (LRU eviction)

# Embedding cache settings
EMBEDDING_CACHE_DEFAULT_TTL_DAYS: int = 30  # Default TTL for disk-based embedding cache
EMBEDDING_CACHE_DEFAULT_MAX_ENTRIES: int = 10000  # Default max entries in embedding cache

# ============================================================================
# Search Settings
# ============================================================================

HYBRID_SEARCH_CANDIDATE_MULTIPLIER: int = 3  # Fetch 3x top_k for hybrid reranking
SEMANTIC_SEARCH_EXTRA_FETCH_MULTIPLIER: int = 2  # Fetch 2x for semantic filtering

# Proactive retrieval settings
DEFAULT_PROACTIVE_TOP_K: int = 3  # Number of results for proactive injection
DEFAULT_RELEVANCE_THRESHOLD: float = 0.6  # Minimum relevance score for retrieval
MIN_MESSAGE_LENGTH_FOR_RETRIEVAL: int = 10  # Skip retrieval for short messages

# ============================================================================
# Context Window Defaults
# ============================================================================

DEFAULT_THRESHOLD_TOKENS: int = 32000  # Default context threshold
DEFAULT_SWAP_TRIGGER_PERCENT: float = 0.80  # Swap at 80% of threshold
DEFAULT_PRESERVE_RECENT_TOKENS: int = 8000  # Always keep recent context
DEFAULT_CONTEXT_WINDOW: int = 200000  # Default context window for unknown models

# Context window size categories and thresholds
CONTEXT_WINDOW_SMALL_THRESHOLD: int = 50000  # Below this is "small"
CONTEXT_WINDOW_MEDIUM_THRESHOLD: int = 100000  # Below this (>= small) is "medium"

# Optimal threshold percentages by context window size
OPTIMAL_THRESHOLD_PERCENT_SMALL: float = 0.80  # For context windows < 50k
OPTIMAL_THRESHOLD_PERCENT_MEDIUM: float = 0.50  # For context windows 50k-100k
OPTIMAL_THRESHOLD_PERCENT_LARGE: float = 0.25  # For context windows > 100k

# Preserve recent tokens percentages by context window size
PRESERVE_RECENT_PERCENT_SMALL: float = 0.25  # 25% of threshold for small windows
PRESERVE_RECENT_PERCENT_MEDIUM: float = 0.20  # 20% of threshold for medium windows
PRESERVE_RECENT_PERCENT_LARGE: float = 0.15  # 15% of threshold for large windows

# ============================================================================
# Chunking Defaults
# ============================================================================

DEFAULT_CHUNK_SIZE: int = 2000  # Default tokens per chunk
DEFAULT_CHUNK_OVERLAP: int = 200  # Default overlap between chunks

# ============================================================================
# Storage Limits
# ============================================================================

MAX_CHUNK_SIZE_BYTES: int = 1_000_000  # 1MB max chunk size
MAX_PROJECT_NAME_LENGTH: int = 1000  # Max project name length
STORAGE_CACHE_SIZE: int = 20  # Default chunk cache size
FILE_LOCK_TIMEOUT: float = 5.0  # Default lock timeout in seconds
FILE_LOCK_RETRY_INTERVAL_INITIAL: float = 0.05  # Initial retry interval (50ms)
FILE_LOCK_RETRY_INTERVAL_MAX: float = 0.5  # Max retry interval (500ms)
FILE_LOCK_RETRY_BACKOFF_MULTIPLIER: float = 1.5  # Exponential backoff multiplier

# ============================================================================
# Retry Settings
# ============================================================================

MAX_RETRY_ATTEMPTS: int = 3  # Maximum retry attempts for transient failures
RETRY_BASE_DELAY_SECONDS: float = 1.0  # Base delay for exponential backoff
RETRY_MAX_DELAY_SECONDS: float = 30.0  # Maximum delay between retries

# ============================================================================
# BM25 Defaults
# ============================================================================

DEFAULT_BM25_K1: float = 1.2  # Term frequency saturation (1.2-2.0 typical)
DEFAULT_BM25_B: float = 0.75  # Document length normalization (0-1)
BM25_KEYWORD_WEIGHT_MULTIPLIER: int = 3  # Multiplier for keyword importance in BM25

# ============================================================================
# Hybrid Search Defaults
# ============================================================================

DEFAULT_HYBRID_KEYWORD_WEIGHT: float = 0.3  # Weight for BM25 score in hybrid search
DEFAULT_HYBRID_SEMANTIC_WEIGHT: float = 0.7  # Weight for semantic similarity

# ============================================================================
# Recency Boost
# ============================================================================

DEFAULT_RECENCY_BOOST: float = 0.1  # Maximum recency boost for recent chunks
RECENCY_DECAY_FACTOR: float = 0.9  # Per-day decay factor for recency boost

# ============================================================================
# Summarizer Settings
# ============================================================================

DEFAULT_SUMMARIZER_MAX_LENGTH: int = 1000  # Maximum summary length in characters
DEFAULT_MIN_KEYWORD_LENGTH: int = 3  # Minimum keyword length for extraction
DEFAULT_SUMMARIZER_TOP_K_KEYWORDS: int = 12  # Number of keywords to extract

# ============================================================================
# Retrieval Settings
# ============================================================================

DEFAULT_RETRIEVAL_TOP_K: int = 5  # Number of results to return by default
DEFAULT_RETRIEVAL_MIN_SIMILARITY: float = 0.7  # Minimum similarity threshold

# ============================================================================
# ANN (Approximate Nearest Neighbors) Settings
# ============================================================================

DEFAULT_ANN_THRESHOLD: int = 100  # Minimum chunks before enabling ANN index

# ============================================================================
# Validation Settings
# ============================================================================

VALIDATION_EMPTY_MESSAGE_WARNING_THRESHOLD: float = 0.5  # Warn if >50% empty

# ============================================================================
# Maximum Age
# ============================================================================

DEFAULT_MAX_AGE_DAYS: int = 30  # Default maximum age for chunks (0 = never expire)

# ============================================================================
# Logging Defaults
# ============================================================================

DEFAULT_LOG_LEVEL: str = "WARNING"  # Default log level

# ============================================================================
# Subprocess Timeouts
# ============================================================================

CLI_QUERY_TIMEOUT_SECONDS: int = 10  # Timeout for CLI queries in hooks
