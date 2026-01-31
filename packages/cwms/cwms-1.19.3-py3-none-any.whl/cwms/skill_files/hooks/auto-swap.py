#!/usr/bin/env python3
"""
Auto-swap hook for cwms.

Triggers on Stop event after Claude finishes responding.
Reads context metrics from status line monitor and swaps if threshold exceeded.

When swap occurs:
1. Swaps older context to disk via cwms CLI
2. Saves bridge summary for SessionStart hook
3. Returns JSON with decision: "block" to instruct Claude to execute /clear

This is part of the automated context management workflow based on research
showing LLM performance degrades after ~33k tokens.

Reference: "Recursive Language Models" (Zhang, Kraska, Khattab)
https://arxiv.org/abs/2512.24601
"""

import contextlib
import json
import os
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path


def get_temp_dir() -> str:
    """Get consistent temp directory path.

    Uses tempfile.gettempdir() for cross-platform compatibility (Windows, macOS, Linux).
    All code (statusline.py, hooks, etc.) must use this same approach
    to ensure files are written to and read from the same location.
    """
    return tempfile.gettempdir()


def read_monitor_file(session_id: str) -> dict[str, str] | None:
    """Read context metrics from status line monitor file."""
    temp_dir = get_temp_dir()
    monitor_file = os.path.join(temp_dir, f"claude-context-{session_id}.json")
    try:
        with open(monitor_file) as f:
            data: dict[str, str] = json.load(f)
            return data
    except Exception:
        return None


def parse_transcript_to_messages(transcript_path: str) -> list[dict]:
    """Convert transcript JSONL to messages JSON format.

    Claude Code transcript format:
    {"type": "user", "message": {"role": "user", "content": "..."}}
    {"type": "message", "message": {"role": "assistant", "content": [...]}}

    Note: Transcript may have multiple entries for same message (streamed updates),
    so we deduplicate by UUID to avoid inflated token counts.
    """
    messages = []
    seen_uuids: set[str] = set()

    try:
        with open(transcript_path) as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    entry = json.loads(line)

                    # Skip summary entries and other non-message types
                    entry_type = entry.get("type", "")
                    if entry_type == "summary":
                        continue

                    # Deduplicate by UUID (transcript has multiple entries per message)
                    uuid = entry.get("uuid", "")
                    if uuid and uuid in seen_uuids:
                        continue
                    if uuid:
                        seen_uuids.add(uuid)

                    # Claude Code nests messages in a "message" field
                    # Check for nested format first
                    msg = entry.get("message", entry)

                    # Extract user and assistant messages only
                    role = msg.get("role")
                    if role not in ("user", "assistant"):
                        continue

                    content = msg.get("content", "")

                    # Handle both string and list content formats
                    if isinstance(content, str):
                        # Already a string, use as-is
                        pass
                    elif isinstance(content, list):
                        # Extract text from content blocks
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict):
                                block_type = block.get("type", "")
                                if block_type == "text":
                                    text_parts.append(block.get("text", ""))
                                elif block_type == "tool_use":
                                    # Include tool calls for context
                                    tool_name = block.get("name", "tool")
                                    tool_input = block.get("input", {})
                                    # Include brief tool input (file paths, queries, etc.)
                                    if isinstance(tool_input, dict):
                                        input_str = ", ".join(
                                            f"{k}={v}" for k, v in list(tool_input.items())[:3]
                                        )
                                        text_parts.append(f"[Tool: {tool_name}({input_str})]")
                                    else:
                                        text_parts.append(f"[Tool: {tool_name}]")
                                elif block_type == "tool_result":
                                    # CRITICAL: Include tool results - these contain file reads,
                                    # grep outputs, etc. which are most of the context
                                    tool_content = block.get("content", "")
                                    if isinstance(tool_content, str) and tool_content:
                                        # Limit individual tool results to avoid huge chunks
                                        # but keep enough for meaningful context
                                        max_result_len = 10000
                                        if len(tool_content) > max_result_len:
                                            tool_content = (
                                                tool_content[:max_result_len]
                                                + f"\n... [truncated {len(tool_content) - max_result_len} chars]"
                                            )
                                        text_parts.append(f"[Tool Result]\n{tool_content}")
                                elif block_type == "thinking":
                                    # Include thinking for context continuity
                                    thinking = block.get("thinking", "")
                                    if thinking:
                                        # Truncate very long thinking blocks
                                        max_thinking_len = 2000
                                        if len(thinking) > max_thinking_len:
                                            thinking = thinking[:max_thinking_len] + "..."
                                        text_parts.append(f"[Thinking]\n{thinking}")
                        content = "\n".join(text_parts)
                    else:
                        # Unknown content type, convert to string
                        content = str(content) if content else ""

                    # Ensure content is always a string
                    if content and isinstance(content, str):
                        messages.append({"role": role, "content": content})
                except json.JSONDecodeError:
                    continue
    except Exception:
        # If we can't read transcript, return empty to avoid breaking
        return []

    return messages


def perform_swap(project: str, messages: list[dict]) -> dict:
    """Call cwms swap CLI command."""
    debug_log(f"Creating temp file for {len(messages)} messages")
    # Create temporary messages file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"messages": messages}, f)
        temp_file = f.name
    debug_log(f"Temp file created: {temp_file}")

    try:
        debug_log("Starting swap command...")
        # Call cwms swap (increased timeout for embedding generation)
        result = subprocess.run(  # nosec B603, B607
            [
                "cwms",
                "swap",
                "--project",
                project,
                "--messages-file",
                temp_file,
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        debug_log(f"Swap command completed with code {result.returncode}")
        if result.returncode == 0:
            try:
                response: dict = json.loads(result.stdout)
                debug_log(f"Swap successful: {response.get('chunks_stored', 0)} chunks")
                return response
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON response: {e}\nStdout: {result.stdout[:500]}"
                debug_log(f"JSON decode error: {error_msg}")
                return {"success": False, "error": error_msg}
        else:
            error_msg = result.stderr or result.stdout or "Unknown error (no output)"
            debug_log(f"Swap failed with code {result.returncode}: {error_msg[:500]}")
            return {"success": False, "error": error_msg}
    except subprocess.TimeoutExpired:
        error_msg = "Swap command timeout (exceeded 300s). Try disabling embeddings or reducing message count."
        debug_log(f"TIMEOUT: {error_msg}")
        return {"success": False, "error": error_msg}
    except FileNotFoundError:
        error_msg = "cwms CLI not found. Install with: pip install cwms"
        debug_log(f"CLI not found: {error_msg}")
        return {
            "success": False,
            "error": error_msg,
        }
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        debug_log(f"Swap exception: {error_msg}")
        return {"success": False, "error": error_msg}
    finally:
        # Cleanup temp file
        with contextlib.suppress(Exception):
            os.unlink(temp_file)


def get_working_dir_hash(working_dir: str | None = None) -> str:
    """Get a short hash of the working directory for file naming.

    Args:
        working_dir: The working directory to hash. If None, uses os.getcwd().
    """
    import hashlib

    cwd = working_dir if working_dir else os.getcwd()
    return hashlib.md5(cwd.encode()).hexdigest()[:12]  # nosec B324


def save_bridge_summary(_session_id: str, summary: str, working_dir: str | None = None) -> bool:
    """Save bridge summary for SessionStart hook to inject after /clear.

    Uses working directory hash instead of session_id because /clear creates
    a new session_id, but the working directory stays the same.

    Args:
        session_id: Session identifier (unused, kept for API compatibility)
        summary: The summary text to save
        working_dir: The working directory to use for hashing
    """
    # Use working directory hash - persists across /clear
    wd_hash = get_working_dir_hash(working_dir)
    temp_dir = get_temp_dir()
    bridge_file = Path(temp_dir) / f"cwms-bridge-{wd_hash}.txt"
    try:
        bridge_file.write_text(summary)
        return True
    except Exception:
        return False


def extract_search_queries(
    summary: str, _chunks: list[dict] | None = None
) -> list[tuple[str, str]]:
    """Extract relevant search queries from the swap summary.

    Analyzes the summary to identify key topics that should be searched
    in the next session to maintain context continuity.

    Returns:
        List of tuples (query, description) for context recovery
    """
    import re

    queries = []

    # Extract from structured summary sections
    lines = summary.split("\n")

    # Look for "Files Referenced:" section
    files_mentioned = []
    topics_mentioned = []
    actions_mentioned = []

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()

        # Extract files
        if line_lower.startswith("files referenced:"):
            files_text = line.split(":", 1)[1] if ":" in line else ""
            files_mentioned = [f.strip() for f in files_text.split(",") if f.strip()]

        # Extract key topics
        elif line_lower.startswith("key topics:"):
            topics_text = line.split(":", 1)[1] if ":" in line else ""
            topics_mentioned = [t.strip() for t in topics_text.split(",") if t.strip()]

        # Extract actions
        elif line_lower.startswith("actions:"):
            actions_text = line.split(":", 1)[1] if ":" in line else ""
            actions_mentioned = [a.strip() for a in actions_text.split(",") if a.strip()]

        # Extract "What was being worked on:" section
        elif line_lower.startswith("what was being worked on:"):
            # Next few lines are bullet points
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("-"):
                work_item = lines[j].strip().lstrip("- ").strip()
                if work_item and len(work_item) > 10:
                    # Extract key phrases
                    # Look for action verbs at start
                    match = re.match(r"^(\w+ed|ing)\s+(.+?)(?:\s*-|:|$)", work_item, re.IGNORECASE)
                    if match:
                        topic = match.group(2).strip()[:50]
                        if topic:
                            queries.append((topic, f"Work on: {work_item[:100]}"))
                j += 1

    # Add file-based queries if specific files were worked on
    for file in files_mentioned[:3]:
        if file and "." in file:  # Has extension, likely a real file
            # Extract filename without full path for cleaner query
            filename = file.split("/")[-1]
            queries.append((filename, f"Changes to {file}"))

    # Add action-based queries
    for action in actions_mentioned[:2]:
        if action and action not in ["update", "addition"]:  # Skip too generic
            queries.append((action, f"Work related to {action}"))

    # Add topic-based queries (filter out too generic ones)
    generic_topics = {"file", "code", "function", "class", "test", "config"}
    for topic in topics_mentioned[:3]:
        if topic and topic.lower() not in generic_topics:
            queries.append((topic, f"Discussion about {topic}"))

    # If we don't have enough specific queries, extract from segment summaries
    if len(queries) < 3:
        # Look for "Segment Summaries:" section
        in_segments = False
        for line in lines:
            if line.strip().lower().startswith("segment summaries:"):
                in_segments = True
                continue
            if in_segments and line.strip().startswith(("1.", "2.", "3.")):
                # Extract key terms from first segment summary
                segment_text = line.split(".", 1)[1] if "." in line else line
                # Extract file paths
                file_matches = re.findall(r"[\w/.-]+\.[\w]+", segment_text)
                for match in file_matches[:2]:
                    if match not in [q[0] for q in queries]:
                        queries.append((match, f"Work involving {match}"))

    # Deduplicate and return top 5
    seen = set()
    unique_queries = []
    for query, desc in queries:
        if query.lower() not in seen:
            seen.add(query.lower())
            unique_queries.append((query, desc))

    return unique_queries[:5]


def generate_todo_list(_messages: list[dict], chunks: int, tokens: int) -> str:
    """Generate a todo list of next steps to continue the work."""
    todo_items = [
        f"✅ Context successfully swapped: {chunks} chunk(s), {tokens:,} tokens",
        "📋 Continuation guide with recovery queries will be automatically injected",
        "🔍 Run suggested searches to recall swapped context",
        "💾 Continue with your task in this fresh context window",
    ]

    todo_md = "## Context Swap TODO List\n\n"
    for item in todo_items:
        todo_md += f"- {item}\n"

    return todo_md


def save_continuation_file(
    _session_id: str,
    project: str,
    queries: list[tuple[str, str]],
    summary: str,
    working_dir: str | None = None,
) -> bool:
    """Save continuation.md with cwms search commands.

    This file guides Claude on how to retrieve swapped context in the next session,
    including what was being worked on and specific search queries.

    Uses working directory hash instead of session_id because /clear creates
    a new session_id, but the working directory stays the same.

    Args:
        session_id: Session identifier (unused, kept for API compatibility)
        project: Project name
        queries: List of (query, description) tuples
        summary: Full swap summary for context
        working_dir: The working directory to use for hashing
    """
    # Use working directory hash - persists across /clear
    wd_hash = get_working_dir_hash(working_dir)
    temp_dir = get_temp_dir()
    continuation_file = Path(temp_dir) / f"cwms-continuation-{wd_hash}.md"

    # Build markdown content with context and search commands
    content = "# Context Recovery Guide\n\n"

    # Add context about what was being worked on
    content += "## What You Were Working On\n\n"

    # Extract and format the key information from summary
    summary_lines = summary.split("\n")
    in_segment_summary = False

    for line in summary_lines:
        line_lower = line.lower().strip()

        # Include key sections from the summary
        if line_lower.startswith(("**key topics:", "**files referenced:", "**actions:")):
            content += f"{line}\n"
        elif line_lower.startswith("**segment summaries:**"):
            in_segment_summary = True
            content += "\n**Recent work:**\n"
        elif in_segment_summary and line.strip().startswith(("1.", "2.", "3.")):
            # Include first 3 segment summaries
            content += f"{line}\n"

    content += "\n---\n\n"

    # Add search queries with descriptions
    if queries:
        content += "## Suggested Context Recovery Queries\n\n"
        content += "Run these queries to retrieve the most relevant context:\n\n"
        for i, (query, description) in enumerate(queries, 1):
            content += f"### {i}. {description}\n\n"
            content += "```bash\n"
            content += f'cwms retrieve --project "{project}" --query "{query}"\n'
            content += "```\n\n"
    else:
        # Fallback if no specific queries
        content += "## Context Recovery\n\n"
        content += "Search for relevant topics:\n"
        content += f'```bash\ncwms search --project "{project}" --query "<topic>"\n```\n\n'

    # Add manual search options
    content += "## Other Options\n\n"
    content += "**View all summaries:**\n"
    content += f'```bash\ncwms summaries --project "{project}"\n```\n\n'
    content += "**Custom search:**\n"
    content += f'```bash\ncwms retrieve --project "{project}" --query "<your-search>"\n```\n\n'

    # Add usage tip
    content += "---\n\n"
    content += (
        "*Tip: Use `retrieve` instead of `search` to get formatted context ready for injection.*\n"
    )

    try:
        continuation_file.write_text(content)
        return True
    except Exception:
        return False


def reset_metrics_after_swap(session_id: str, swap_successful: bool = False) -> None:
    """Reset metrics file to prevent hook re-triggering (loop prevention).

    After a swap attempt (success or failure), we must reset should_swap to False
    to prevent the hook from looping continuously on subsequent Stop events.
    The metrics will be updated again by the status line monitor when context
    actually builds up again in a new session.

    If swap was successful, also sets a token_baseline so the statusline counter
    resets to show only tokens accumulated after the swap.
    """
    temp_dir = get_temp_dir()
    monitor_file = os.path.join(temp_dir, f"claude-context-{session_id}.json")
    try:
        with open(monitor_file) as f:
            metrics = json.load(f)

        # Mark swap as completed to prevent re-trigger
        metrics["should_swap"] = False
        metrics["swap_completed"] = True
        metrics["swap_completed_at"] = __import__("datetime").datetime.now().isoformat()

        # CRITICAL: Reset token counter on successful swap
        # The statusline stores adjusted total_tokens (raw - existing_baseline)
        # To get raw cumulative, add back the existing baseline
        if swap_successful:
            adjusted_total = metrics.get("total_tokens", 0)
            existing_baseline = metrics.get("token_baseline", 0)
            raw_cumulative = adjusted_total + existing_baseline
            # Set new baseline so next statusline shows: raw_new - raw_cumulative = small number
            metrics["token_baseline"] = raw_cumulative
            debug_log(f"Token counter reset: baseline set to {raw_cumulative}")

        with open(monitor_file, "w") as f:
            json.dump(metrics, f)
    except Exception:
        # If we can't update metrics, try to delete the file to prevent loop
        with contextlib.suppress(Exception):
            os.unlink(monitor_file)


def output_block_with_clear_instruction(
    session_id: str,
    project: str,
    chunks: int,
    tokens: int,
    summary: str,
    used_pct: float,
    input_tokens: int,
    messages: list[dict] | None = None,
    working_dir: str | None = None,
) -> None:
    """Output JSON with multi-step instruction for LLM summarization before /clear."""
    # Save regex-based bridge summary as fallback
    # This will be overwritten if Claude saves an LLM-generated summary
    save_bridge_summary(session_id, summary, working_dir)

    # Generate todo list and save continuation file with improved queries
    todo_list = generate_todo_list(messages or [], chunks, tokens)
    queries = extract_search_queries(summary)
    save_continuation_file(session_id, project, queries, summary, working_dir)

    # Build the instruction message - this is shown to the user and instructs Claude
    # The systemMessage below tells Claude what to do; this reason explains what happened
    reason = f"""🔄 **CONTEXT SWAP COMPLETE**

Context was at {used_pct:.1f}% ({input_tokens:,} tokens) - exceeds optimal threshold.
Successfully swapped {chunks} chunk(s) ({tokens:,} tokens) to disk.

{todo_list}

---

**Next:** Claude will generate a session summary and execute `/clear` to reset the context window.
The summary will be automatically injected when you continue working.

---"""

    output = {
        "decision": "block",
        "reason": reason,
        "systemMessage": f"""🔄 Auto-swap triggered at {used_pct:.1f}% ({input_tokens:,} tokens). Swapped {chunks} chunk(s) ({tokens:,} tokens).

INSTRUCTIONS FOR CLAUDE:
1. Generate a concise summary of this session covering: task/problem, key decisions, files modified, current state
2. Save the summary: cwms save-bridge-summary --project "{project}" --summary "YOUR_SUMMARY"
3. Execute /clear to reset the context window

The summary will be injected automatically when the user continues.""",
    }

    print(json.dumps(output))


def output_swap_failed(error: str) -> None:
    """Output notification when swap fails (non-blocking)."""
    # Don't block on failure - just warn
    output = {"systemMessage": f"⚠️ Context swap attempted but failed: {error}"}
    print(json.dumps(output))
    # Also output to stderr for debugging
    sys.stderr.write(f"Auto-swap failed: {error}\n")


def debug_log(msg: str) -> None:
    """Write debug message to log file."""
    try:
        temp_dir = get_temp_dir()
        debug_file = os.path.join(temp_dir, "cwms-hook-debug.log")
        with open(debug_file, "a") as f:
            from datetime import datetime

            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:  # nosec B110
        pass


def main() -> None:
    """Main hook entry point."""
    debug_log("=== Hook started ===")

    # Read hook input from stdin
    hook_data = json.load(sys.stdin)
    debug_log(f"Hook input keys: {list(hook_data.keys())}")

    session_id = hook_data.get("session_id")
    transcript_path = hook_data.get("transcript_path")
    debug_log(f"session_id: {session_id}, transcript_path: {transcript_path}")

    if not session_id or not transcript_path:
        debug_log("EXIT: Missing session_id or transcript_path")
        sys.exit(0)

    # Read context metrics from status line monitor
    metrics = read_monitor_file(session_id)
    debug_log(f"Metrics: {metrics}")

    if not metrics:
        debug_log("EXIT: No metrics file found")
        sys.exit(0)

    # Check if swap is needed
    should_swap = metrics.get("should_swap", False)
    used_pct = float(metrics.get("used_percentage", "0"))
    total_tokens = int(metrics.get("total_tokens", "0"))
    debug_log(f"should_swap: {should_swap}, used_pct: {used_pct}, total_tokens: {total_tokens}")

    if not should_swap:
        debug_log("EXIT: should_swap is False")
        sys.exit(0)

    # Parse transcript to messages
    debug_log(f"Parsing transcript from: {transcript_path}")
    messages = parse_transcript_to_messages(transcript_path)
    debug_log(f"Parsed {len(messages)} messages")

    if not messages:
        debug_log("EXIT: No messages parsed from transcript")
        sys.exit(0)

    # Get working directory and project name
    working_dir = metrics.get("working_directory") or hook_data.get("cwd") or os.getcwd()
    project = os.path.basename(working_dir)
    debug_log(f"Project: {project}, working_dir: {working_dir}")

    # Perform the swap
    debug_log("Performing swap...")
    result = perform_swap(project, messages)
    debug_log(f"Swap result: {result}")

    # Check if swap succeeded and chunks were actually stored
    swap_succeeded = result.get("success", False)
    chunks = result.get("chunks_stored", 0) if swap_succeeded else 0
    actually_swapped = swap_succeeded and chunks > 0

    # CRITICAL: Reset metrics to prevent loop, and reset counter if swap succeeded
    debug_log(f"Resetting metrics (swap_successful={actually_swapped})")
    reset_metrics_after_swap(session_id, swap_successful=actually_swapped)

    if swap_succeeded:
        tokens = result.get("tokens_stored", 0)
        summary = result.get("summary", "Context swapped to disk")
        debug_log(f"Swap successful: {chunks} chunks, {tokens} tokens")

        # Only output block/clear instruction if we actually swapped something
        if chunks > 0:
            debug_log("Outputting block with clear instruction")
            output_block_with_clear_instruction(
                session_id=session_id,
                project=project,
                chunks=chunks,
                tokens=tokens,
                summary=summary,
                used_pct=used_pct,
                input_tokens=total_tokens,
                messages=messages,
                working_dir=working_dir,
            )
        else:
            # Swap succeeded but nothing to swap - just log, don't block
            debug_log("Nothing to swap (under preserve threshold), skipping block")
            output = {
                "systemMessage": f"Context check: {total_tokens:,} tokens ({used_pct:.1f}%), "
                "but nothing swappable (content under preserve threshold)."
            }
            print(json.dumps(output))
    else:
        # Swap failed - output warning but don't block
        error = result.get("error", "Unknown error")
        debug_log(f"Swap failed: {error}")
        output_swap_failed(error)

    debug_log("=== Hook finished ===")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        debug_log(f"EXCEPTION: {type(e).__name__}: {e}")
        import traceback

        debug_log(f"TRACEBACK: {traceback.format_exc()}")
        # Output error message as JSON so Claude Code doesn't fail the hook
        error_output = {"systemMessage": f"⚠️ Auto-swap hook error: {type(e).__name__}: {str(e)}"}
        print(json.dumps(error_output))
        # Fail gracefully - hooks shouldn't crash the session
        sys.exit(0)
