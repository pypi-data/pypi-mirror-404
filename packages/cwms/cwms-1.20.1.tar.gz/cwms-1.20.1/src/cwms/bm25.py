"""BM25 (Best Matching 25) ranking algorithm implementation.

BM25 is a probabilistic ranking function used in information retrieval.
It improves upon simple keyword counting by considering:
- Term frequency (TF): How often a term appears in a document
- Inverse document frequency (IDF): How rare a term is across all documents
- Document length normalization: Penalizes longer documents

Reference: Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance
Framework: BM25 and Beyond. Foundations and Trends in Information Retrieval.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BM25Statistics:
    """Document corpus statistics for BM25 scoring.

    Maintains statistics needed for IDF calculation and length normalization.
    Can be incrementally updated as new documents are added.
    """

    # Total number of documents in corpus
    total_docs: int = 0

    # Total tokens across all documents (for average length calculation)
    total_tokens: int = 0

    # Document frequency: term -> count of documents containing term
    doc_frequencies: dict[str, int] = field(default_factory=dict)

    @property
    def avg_doc_length(self) -> float:
        """Calculate average document length."""
        if self.total_docs == 0:
            return 0.0
        return self.total_tokens / self.total_docs

    def add_document(self, terms: list[str], token_count: int) -> None:
        """Update statistics with a new document.

        Args:
            terms: Unique terms in the document (lowercased)
            token_count: Total token count of the document
        """
        self.total_docs += 1
        self.total_tokens += token_count

        # Update document frequencies (count each term once per document)
        unique_terms = set(terms)
        for term in unique_terms:
            self.doc_frequencies[term] = self.doc_frequencies.get(term, 0) + 1

    def to_dict(self) -> dict:
        """Serialize statistics to dictionary."""
        return {
            "total_docs": self.total_docs,
            "total_tokens": self.total_tokens,
            "doc_frequencies": self.doc_frequencies,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BM25Statistics:
        """Deserialize statistics from dictionary."""
        return cls(
            total_docs=data.get("total_docs", 0),
            total_tokens=data.get("total_tokens", 0),
            doc_frequencies=data.get("doc_frequencies", {}),
        )


class BM25Scorer:
    """BM25 scoring implementation.

    The BM25 score for a document D given query Q is:
    score(D,Q) = Σ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D|/avgdl))

    Where:
    - f(qi,D) = term frequency of term qi in document D
    - |D| = length of document D (in tokens)
    - avgdl = average document length in corpus
    - k1 = term frequency saturation parameter (default: 1.2)
    - b = document length normalization parameter (default: 0.75)
    - IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1)
      - N = total number of documents
      - n(qi) = number of documents containing term qi
    """

    def __init__(self, k1: float = 1.2, b: float = 0.75) -> None:
        """Initialize BM25 scorer.

        Args:
            k1: Term frequency saturation parameter (1.2-2.0 typical)
                Higher values increase term frequency importance.
            b: Document length normalization parameter (0-1)
                0 = no length normalization, 1 = full normalization
        """
        self.k1 = k1
        self.b = b

    def idf(self, term: str, stats: BM25Statistics) -> float:
        """Calculate inverse document frequency for a term.

        Uses the BM25 IDF formula with smoothing:
        IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1)

        This variant ensures IDF is always positive, even for very common terms.

        Args:
            term: The term to calculate IDF for
            stats: Corpus statistics

        Returns:
            IDF score (always positive)
        """
        n = stats.doc_frequencies.get(term.lower(), 0)
        total_docs = stats.total_docs

        if total_docs == 0:
            return 0.0

        # BM25 IDF formula with +1 to ensure positive values
        idf_score = math.log((total_docs - n + 0.5) / (n + 0.5) + 1)
        return idf_score

    def score(
        self,
        query_terms: list[str],
        doc_terms: list[str],
        doc_length: int,
        stats: BM25Statistics,
    ) -> float:
        """Calculate BM25 score for a document given a query.

        Computes the BM25 relevance score by considering term frequency (TF),
        inverse document frequency (IDF), and document length normalization.

        Early Exit Conditions:
            - Returns 0.0 if query_terms is empty (no query to match)
            - Returns 0.0 if doc_terms is empty (no document content)
            - Returns 0.0 if corpus has no documents (stats.total_docs == 0)

        Edge Cases:
            - If average document length is 0 (all empty documents), uses 1.0
              to avoid division by zero in length normalization

        Args:
            query_terms: Terms from the query (lowercased)
            doc_terms: All terms from the document (lowercased, with duplicates)
            doc_length: Token count of the document
            stats: Corpus statistics for IDF calculation

        Returns:
            BM25 relevance score (higher is more relevant), or 0.0 for edge cases
        """
        # Early exit: empty query
        if not query_terms:
            logger.debug("BM25 score returning 0.0: empty query_terms")
            return 0.0

        # Early exit: empty document
        if not doc_terms:
            logger.debug("BM25 score returning 0.0: empty doc_terms")
            return 0.0

        # Early exit: empty corpus
        if stats.total_docs == 0:
            logger.debug("BM25 score returning 0.0: empty corpus (total_docs == 0)")
            return 0.0

        # Use 1.0 as minimum avgdl to avoid division by zero
        # This can happen if all documents in corpus are empty
        avgdl = max(stats.avg_doc_length, 1.0)

        # Count term frequencies in document
        doc_term_freq = Counter(doc_terms)

        score = 0.0
        for term in query_terms:
            term_lower = term.lower()

            # Get term frequency in document
            tf = doc_term_freq.get(term_lower, 0)

            if tf == 0:
                continue

            # Calculate IDF
            idf_score = self.idf(term_lower, stats)

            # Calculate TF component with length normalization
            # f(qi,D) * (k1 + 1) / (f(qi,D) + k1 * (1 - b + b * |D|/avgdl))
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / avgdl)

            # Add to score
            score += idf_score * (numerator / denominator)

        return score

    def score_from_keywords(
        self,
        query_terms: list[str],
        doc_keywords: list[str],
        doc_summary: str,
        doc_token_count: int,
        stats: BM25Statistics,
    ) -> float:
        """Calculate BM25 score using chunk keywords and summary.

        This is optimized for cwms chunks where we have:
        - Pre-extracted keywords (high value terms)
        - Summary text (additional context)
        - Token count (for length normalization)

        Keywords get a boost factor as they're already identified as important.

        Args:
            query_terms: Terms from the query
            doc_keywords: Keywords extracted from the chunk
            doc_summary: Summary text of the chunk
            doc_token_count: Token count of the chunk
            stats: Corpus statistics

        Returns:
            BM25 relevance score
        """
        if not query_terms:
            return 0.0

        # Build document terms list
        # Keywords are weighted higher by being repeated
        doc_terms: list[str] = []

        # Add keywords (each keyword counted multiple times for higher weight)
        keyword_weight = 3
        for kw in doc_keywords:
            doc_terms.extend([kw.lower()] * keyword_weight)

        # Add summary terms (each word once)
        summary_terms = self._tokenize(doc_summary.lower())
        doc_terms.extend(summary_terms)

        return self.score(query_terms, doc_terms, doc_token_count, stats)

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization for text.

        Splits on whitespace and removes punctuation.
        For more sophisticated tokenization, use an external tokenizer.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens (lowercased)
        """
        # Split on non-alphanumeric characters
        tokens = re.findall(r"\b\w+\b", text.lower())
        return tokens


def build_statistics_from_chunks(
    chunks_data: list[tuple[list[str], str, int]],
) -> BM25Statistics:
    """Build BM25 statistics from chunk data.

    Args:
        chunks_data: List of (keywords, summary, token_count) tuples

    Returns:
        Populated BM25Statistics instance
    """
    stats = BM25Statistics()

    for keywords, summary, token_count in chunks_data:
        # Collect all terms from keywords and summary
        all_terms = [kw.lower() for kw in keywords]

        # Tokenize summary
        summary_tokens = re.findall(r"\b\w+\b", summary.lower())
        all_terms.extend(summary_tokens)

        stats.add_document(all_terms, token_count)

    return stats
