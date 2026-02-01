"""Text processing utilities for keyword extraction and text analysis.

This module provides shared text processing functionality used across the
cwms package, avoiding circular dependencies.
"""

from __future__ import annotations

import re

# Common stop words to filter from keywords
STOP_WORDS = {
    # Articles and conjunctions
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    # Prepositions
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "about",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "under",
    # Verbs (common auxiliary/linking)
    "is",
    "was",
    "are",
    "were",
    "been",
    "be",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    # Pronouns
    "this",
    "that",
    "these",
    "those",
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "me",
    "my",
    "your",
    "his",
    "her",
    "its",
    "our",
    "their",
    # Question words
    "what",
    "which",
    "who",
    "when",
    "where",
    "why",
    "how",
    # Quantifiers
    "all",
    "each",
    "every",
    "both",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "any",
    "many",
    "much",
    # Adverbs
    "so",
    "than",
    "too",
    "very",
    "just",
    "again",
    "further",
    "then",
    "once",
    "there",
    "here",
    "now",
    "also",
    "really",
    "still",
    "already",
    "always",
    "never",
    "often",
    # Generic conversation words (often produce poor summaries)
    "particularly",
    "interested",
    "understanding",
    "details",
    "context",
    "information",
    "something",
    "anything",
    "nothing",
    "everything",
    "thing",
    "things",
    "way",
    "ways",
    "like",
    "want",
    "need",
    "know",
    "think",
    "see",
    "look",
    "make",
    "get",
    "got",
    "going",
    "able",
    "sure",
    "good",
    "well",
    "new",
    "first",
    "last",
    "long",
    "great",
    "little",
    "right",
    "best",
    "different",
    "another",
    "even",
    "back",
    "come",
    "work",
    "use",
    "used",
    "using",
}

# Domain-specific technical terms that should be boosted
TECHNICAL_TERMS = {
    # Programming concepts
    "api",
    "sdk",
    "cli",
    "gui",
    "url",
    "uri",
    "json",
    "xml",
    "html",
    "css",
    "sql",
    "nosql",
    "rest",
    "graphql",
    "grpc",
    "websocket",
    "http",
    "https",
    "tcp",
    "udp",
    # Data structures
    "array",
    "list",
    "dict",
    "dictionary",
    "map",
    "set",
    "queue",
    "stack",
    "tree",
    "graph",
    "heap",
    "hash",
    "cache",
    # Software patterns
    "singleton",
    "factory",
    "observer",
    "decorator",
    "middleware",
    "handler",
    "controller",
    "model",
    "view",
    "service",
    # Operations
    "authentication",
    "authorization",
    "validation",
    "serialization",
    "encryption",
    "compression",
    "migration",
    "deployment",
    "integration",
    "configuration",
    # Testing
    "test",
    "tests",
    "unittest",
    "pytest",
    "mock",
    "stub",
    "fixture",
    "assertion",
    "coverage",
    # Languages/frameworks
    "python",
    "javascript",
    "typescript",
    "rust",
    "golang",
    "java",
    "react",
    "vue",
    "angular",
    "django",
    "flask",
    "fastapi",
    "express",
    "node",
    "npm",
    "pip",
    "poetry",
    "cargo",
    # Infrastructure
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "terraform",
    "ansible",
    "nginx",
    "redis",
    "postgres",
    "mongodb",
    "mysql",
    "elasticsearch",
    # Git/version control
    "git",
    "commit",
    "branch",
    "merge",
    "rebase",
    "pull",
    "push",
    "clone",
    "repository",
    # File types
    "yaml",
    "toml",
    "env",
    "dockerfile",
    "makefile",
}


def extract_keywords(text: str, top_k: int = 10, min_length: int = 3) -> list[str]:
    """Extract keywords from text using frequency and position analysis.

    Filters out stop words, code-like patterns, and short words.
    Prioritizes technical terms, identifiers, domain-specific language,
    and terms appearing early in the text.

    Args:
        text: Text to extract keywords from
        top_k: Maximum number of keywords to return
        min_length: Minimum word length to consider

    Returns:
        List of extracted keywords, sorted by relevance
    """
    if not text:
        return []

    # First, extract proper nouns (capitalized words not at sentence start)
    # before lowercasing
    proper_nouns = _extract_proper_nouns(text)

    # Split text into sentences for position weighting
    sentences = re.split(r"[.!?\n]+", text)

    # Track word scores with position weighting
    word_scores: dict[str, float] = {}

    for sent_idx, sentence in enumerate(sentences):
        # Position boost: first 3 sentences get higher weight
        position_boost = 1.5 if sent_idx < 3 else 1.0

        # Normalize and extract words
        sentence_lower = sentence.lower()
        words = re.findall(r"\b[a-z_][a-z0-9_]*\b", sentence_lower)

        # Filter out stop words and short words
        for word in words:
            if word in STOP_WORDS or len(word) < min_length:
                continue

            # Calculate score with boosts
            score = position_boost

            # Boost technical terms (contains underscore)
            if "_" in word:
                score *= 1.8

            # Boost words with numbers (version2, item1)
            if re.search(r"\d", word):
                score *= 1.4

            # Boost domain-specific technical terms
            if word in TECHNICAL_TERMS:
                score *= 2.0

            # Add to cumulative score
            word_scores[word] = word_scores.get(word, 0) + score

    # Add proper nouns with high boost (they're often important names)
    for noun in proper_nouns:
        noun_lower = noun.lower()
        if noun_lower not in STOP_WORDS and len(noun_lower) >= min_length:
            word_scores[noun_lower] = word_scores.get(noun_lower, 0) + 2.5

    # Sort by score
    sorted_keywords = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)

    # Return top_k unique keywords
    return [word for word, _ in sorted_keywords[:top_k]]


def _extract_proper_nouns(text: str) -> list[str]:
    """Extract proper nouns (capitalized words not at sentence start).

    Args:
        text: Text to extract from

    Returns:
        List of proper nouns found
    """
    proper_nouns = []

    # Split into sentences
    sentences = re.split(r"[.!?\n]+", text)

    for sentence in sentences:
        words = sentence.split()
        if len(words) < 2:
            continue

        # Skip first word (sentence start), check remaining for capitals
        for word in words[1:]:
            # Clean punctuation
            clean_word = re.sub(r"[^\w]", "", word)
            if not clean_word:
                continue

            # Check if it starts with uppercase, isn't all caps (acronym),
            # and isn't a common false positive
            if (
                clean_word[0].isupper()
                and not clean_word.isupper()
                and clean_word.lower() not in STOP_WORDS
            ):
                proper_nouns.append(clean_word)

    return proper_nouns
