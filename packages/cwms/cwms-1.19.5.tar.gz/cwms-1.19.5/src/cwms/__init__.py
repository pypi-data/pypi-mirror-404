"""
cwms - Extended context memory for Claude Code through swap-to-disk.

Inspired by Vannevar Bush's 1945 concept of extended memory.
"""

__version__ = "1.4.18"

from cwms.chunker import ConversationContext, Message
from cwms.config import Config
from cwms.embedding_cache import EmbeddingCache
from cwms.embeddings import (
    EmbeddingProvider,
    LocalEmbeddings,
    NoEmbeddings,
    get_embedding_provider,
)
from cwms.hierarchical_summarizer import (
    SummaryHierarchy,
    build_summary_hierarchy,
    format_hierarchy_for_display,
    get_summary_at_level,
)
from cwms.retriever import Retriever
from cwms.skill import (
    ContextWindowManagementSkill,
    ContextWindowManagementStatus,
    create_skill,
)
from cwms.storage import Chunk, ChunkMetadata, Storage
from cwms.summarizer import extract_keywords, summarize_chunk
from cwms.swapper import Swapper
from cwms.tokens import estimate_tokens

__all__ = [
    # Core classes
    "Config",
    "Storage",
    "Chunk",
    "ChunkMetadata",
    "Swapper",
    "Retriever",
    # Skill integration
    "ContextWindowManagementSkill",
    "ContextWindowManagementStatus",
    "create_skill",
    # Chunking
    "Message",
    "ConversationContext",
    # Embeddings
    "EmbeddingProvider",
    "EmbeddingCache",
    "NoEmbeddings",
    "LocalEmbeddings",
    "get_embedding_provider",
    # Hierarchical Summarization
    "SummaryHierarchy",
    "build_summary_hierarchy",
    "format_hierarchy_for_display",
    "get_summary_at_level",
    # Utilities
    "estimate_tokens",
    "extract_keywords",
    "summarize_chunk",
    # Version
    "__version__",
]
