#!/usr/bin/env python3
"""
UserPromptSubmit hook for proactive context retrieval.

Automatically injects relevant swapped context when users submit queries.
This makes extended memory transparent - users don't need to manually search.

When a user submits a prompt, this hook:
1. Reads the user's message from hook input
2. Determines if retrieval is warranted (filters short/command messages)
3. Queries cwms for relevant context
4. Filters by minimum relevance threshold (0.6)
5. Injects formatted context via additionalContext

This is part of Phase 2: Proactive Retrieval for transparent extended memory.
"""

import json
import os
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path


def get_temp_dir() -> str:
    """Get consistent temp directory path.

    Uses tempfile.gettempdir() for cross-platform compatibility.
    """
    return tempfile.gettempdir()


def debug_log(msg: str) -> None:
    """Write debug message to log file."""
    try:
        temp_dir = get_temp_dir()
        debug_file = Path(temp_dir) / "cwms-proactive-retrieval-debug.log"
        with open(debug_file, "a") as f:
            from datetime import datetime

            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:  # nosec B110
        pass


def get_project_name(working_dir: str) -> str:
    """Get project name from working directory.

    Uses the directory basename as the project identifier,
    matching the convention used by other hooks.

    Args:
        working_dir: The working directory path
    """
    return os.path.basename(working_dir)


def should_retrieve(message: str) -> bool:
    """Determine if proactive retrieval should be performed.

    Filters out:
    - Very short messages (< 10 chars)
    - Commands (starting with /)
    - Simple acknowledgments ("ok", "yes", "no", "thanks", etc.)
    - Empty messages

    Args:
        message: User's message text

    Returns:
        True if retrieval should be performed
    """
    if not message or len(message.strip()) < 10:
        return False

    message_lower = message.strip().lower()

    # Skip commands
    if message_lower.startswith("/"):
        return False

    # Skip simple acknowledgments
    simple_responses = {
        "ok",
        "okay",
        "yes",
        "no",
        "sure",
        "thanks",
        "thank you",
        "got it",
        "understood",
        "continue",
        "proceed",
        "next",
        "go ahead",
        "sounds good",
        "perfect",
        "great",
        "nice",
        "cool",
    }

    return message_lower not in simple_responses


def query_context(project: str, query: str, top_k: int = 3) -> list[dict]:
    """Query cwms CLI for relevant chunks.

    Args:
        project: Project identifier
        query: Search query
        top_k: Number of results to retrieve

    Returns:
        List of result dicts with score, summary, timestamp
    """
    try:
        result = subprocess.run(  # nosec B603, B607
            [
                "cwms",
                "search",
                "--project",
                project,
                "--query",
                query,
                "--top-k",
                str(top_k),
                "--output-format",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("success"):
                results_list: list[dict] = data.get("results", [])
                return results_list

    except subprocess.TimeoutExpired:
        debug_log("Query timeout after 10s")
    except FileNotFoundError:
        debug_log("cwms CLI not found")
    except json.JSONDecodeError as e:
        debug_log(f"Invalid JSON from CLI: {e}")
    except Exception as e:
        debug_log(f"Query failed: {type(e).__name__}: {e}")

    return []


def format_context_injection(results: list[dict]) -> str:
    """Format search results for injection into conversation.

    Args:
        results: List of search result dicts

    Returns:
        Formatted markdown string for additionalContext
    """
    if not results:
        return ""

    context = "## Relevant Context from Extended Memory\n\n"
    context += (
        "_The following context was automatically retrieved from swapped conversation history:_\n\n"
    )

    for i, result in enumerate(results, 1):
        score = result.get("score", 0.0)
        summary = result.get("summary", "No summary available")
        timestamp = result.get("timestamp", "Unknown time")

        context += f"### {i}. Context Segment (relevance: {score:.2f})\n\n"
        context += f"**When:** {timestamp}\n\n"
        context += f"**Summary:** {summary}\n\n"

    context += "---\n\n"
    context += "_This context was automatically retrieved based on your query. "
    context += "Use it to inform your response where relevant._\n"

    return context


def main() -> None:
    """Main hook entry point."""
    debug_log("=== UserPromptSubmit hook started ===")

    try:
        # Read hook input from stdin
        hook_data = json.load(sys.stdin)
        debug_log(f"Hook input keys: {list(hook_data.keys())}")

        # Extract message from hook data (try multiple keys)
        message = hook_data.get("prompt") or hook_data.get("message")
        working_dir = hook_data.get("cwd")

        debug_log(f"Message length: {len(message) if message else 0}, cwd: {working_dir}")

        if not message or not working_dir:
            debug_log("EXIT: Missing message or cwd")
            sys.exit(0)

        # Check if retrieval is warranted
        if not should_retrieve(message):
            debug_log("EXIT: Message filtered (too short/simple/command)")
            sys.exit(0)

        # Get project identifier from working directory
        project = get_project_name(working_dir)
        debug_log(f"Project: {project}")

        # Query for relevant context
        results = query_context(project, message, top_k=3)
        debug_log(f"Query returned {len(results)} results")

        if not results:
            debug_log("EXIT: No results found")
            sys.exit(0)

        # Filter by minimum relevance threshold
        min_threshold = 0.6
        filtered_results = [r for r in results if r.get("score", 0.0) >= min_threshold]
        debug_log(f"Filtered to {len(filtered_results)} results (threshold={min_threshold})")

        if not filtered_results:
            debug_log("EXIT: No results above threshold")
            sys.exit(0)

        # Format and inject context
        context = format_context_injection(filtered_results)
        debug_log(f"Formatted context length: {len(context)}")

        # Output JSON with additionalContext for injection
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        }

        print(json.dumps(output))
        debug_log("=== Hook finished (injected context) ===")

    except Exception as e:
        debug_log(f"EXCEPTION: {type(e).__name__}: {e}")
        import traceback

        debug_log(f"TRACEBACK: {traceback.format_exc()}")

    # Always exit 0 (fail silently to avoid breaking session)
    sys.exit(0)


if __name__ == "__main__":
    main()
