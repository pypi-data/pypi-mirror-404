"""Hierarchical summarization for multi-level context summaries."""

from __future__ import annotations

from dataclasses import dataclass, field

from cwms.storage import Chunk
from cwms.summarizer import textrank_summarize


@dataclass
class SummaryHierarchy:
    """Multi-level summary hierarchy.

    Attributes:
        chunk_summaries: Individual chunk summaries (most detailed)
        session_summary: Aggregated session summary (medium detail)
        project_summary: High-level project summary (least detailed)
        chunk_count: Number of chunks summarized
        total_tokens: Approximate total tokens across all chunks
    """

    chunk_summaries: list[str] = field(default_factory=list)
    session_summary: str = ""
    project_summary: str = ""
    chunk_count: int = 0
    total_tokens: int = 0


def build_summary_hierarchy(
    chunks: list[Chunk],
    session_sentences: int = 5,
    project_sentences: int = 3,
) -> SummaryHierarchy:
    """Build multi-level summaries from chunks.

    Creates a three-level hierarchy:
    1. Chunk summaries (already exist in chunks)
    2. Session summary (aggregates chunk summaries)
    3. Project summary (further condenses session summary)

    Args:
        chunks: List of Chunk objects with existing summaries
        session_sentences: Number of sentences for session summary
        project_sentences: Number of sentences for project summary

    Returns:
        SummaryHierarchy with all three levels populated
    """
    if not chunks:
        return SummaryHierarchy()

    # Level 1: Chunk summaries (already exist)
    chunk_summaries = [c.summary for c in chunks if c.summary]

    # Calculate total tokens
    total_tokens = sum(getattr(c, "token_count", 0) or 0 for c in chunks)

    # Level 2: Session summary (aggregate chunk summaries)
    session_text = "\n\n".join(chunk_summaries)
    session_summary = textrank_summarize(session_text, num_sentences=session_sentences)

    # Level 3: Project summary (condense session summary further)
    # Only if session summary is substantial enough
    if len(session_summary.split(".")) > project_sentences:
        project_summary = textrank_summarize(session_summary, num_sentences=project_sentences)
    else:
        project_summary = session_summary

    return SummaryHierarchy(
        chunk_summaries=chunk_summaries,
        session_summary=session_summary,
        project_summary=project_summary,
        chunk_count=len(chunks),
        total_tokens=total_tokens,
    )


def get_summary_at_level(
    hierarchy: SummaryHierarchy,
    level: str = "session",
) -> str:
    """Get summary at specified detail level.

    Args:
        hierarchy: SummaryHierarchy object
        level: One of "chunk", "session", or "project"

    Returns:
        Summary string at requested level

    Raises:
        ValueError: If level is not recognized
    """
    if level == "chunk":
        return "\n\n".join(hierarchy.chunk_summaries)
    elif level == "session":
        return hierarchy.session_summary
    elif level == "project":
        return hierarchy.project_summary
    else:
        raise ValueError(f"Unknown level: {level}. Use 'chunk', 'session', or 'project'")


def format_hierarchy_for_display(hierarchy: SummaryHierarchy) -> str:
    """Format hierarchy for human-readable display.

    Args:
        hierarchy: SummaryHierarchy object

    Returns:
        Formatted string with all summary levels
    """
    lines = [
        f"=== Summary Hierarchy ({hierarchy.chunk_count} chunks, ~{hierarchy.total_tokens} tokens) ===",
        "",
        "## Project Summary (High-Level)",
        hierarchy.project_summary or "(No project summary)",
        "",
        "## Session Summary (Medium Detail)",
        hierarchy.session_summary or "(No session summary)",
        "",
        f"## Chunk Summaries ({len(hierarchy.chunk_summaries)} chunks)",
    ]

    for i, summary in enumerate(hierarchy.chunk_summaries, 1):
        lines.append(f"\n### Chunk {i}")
        lines.append(summary)

    return "\n".join(lines)
