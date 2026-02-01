#!/usr/bin/env python3
"""
SessionStart hook for cwms.

Injects bridge summary after /clear to maintain context continuity.

When Claude executes /clear after an auto-swap, this hook:
1. Detects that the session started due to a clear (source="clear")
2. Reads the bridge summary saved by auto-swap.py
3. Injects it as additionalContext so Claude has awareness of swapped content
4. Cleans up the temporary bridge file

This is part of the automated context management workflow.
"""

import contextlib
import glob
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def get_temp_dir() -> str:
    """Get consistent temp directory path.

    Uses tempfile.gettempdir() for cross-platform compatibility (Windows, macOS, Linux).
    All code (statusline.py, hooks, etc.) must use this same approach
    to ensure files are written to and read from the same location.
    """
    return tempfile.gettempdir()


def debug_log(msg: str) -> None:
    """Write debug message to log file."""
    try:
        temp_dir = get_temp_dir()
        debug_file = os.path.join(temp_dir, "cwms-session-start-debug.log")
        with open(debug_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:  # nosec B110
        pass


def get_working_dir_hash(working_dir: str | None = None) -> str:
    """Get a short hash of the working directory for file naming.

    Args:
        working_dir: The working directory to hash. If None, uses os.getcwd().
    """
    import hashlib

    cwd = working_dir if working_dir else os.getcwd()
    return hashlib.md5(cwd.encode()).hexdigest()[:12]  # nosec B324


def get_bridge_summary(_session_id: str, working_dir: str | None = None) -> tuple[str | None, bool]:
    """Read and remove bridge summary file if it exists.

    Uses working directory hash to find the file since session_id changes
    after /clear but working directory stays the same.

    Args:
        session_id: Session identifier (unused, kept for API compatibility)
        working_dir: The working directory to use for hashing

    Returns:
        Tuple of (summary_text, is_llm_generated)
        - summary_text: The summary content, or None if not found
        - is_llm_generated: True if summary was created by Claude via save-bridge-summary
    """
    # Use working directory hash - persists across /clear
    wd_hash = get_working_dir_hash(working_dir)
    temp_dir = get_temp_dir()
    bridge_file = Path(temp_dir) / f"cwms-bridge-{wd_hash}.txt"

    if not bridge_file.exists():
        return None, False

    try:
        summary = bridge_file.read_text()
        bridge_file.unlink()  # Clean up after reading

        # Check if this is an LLM-generated summary
        # The save-bridge-summary CLI command adds this marker
        is_llm_generated = summary.startswith("### LLM-Generated Summary")

        return summary, is_llm_generated
    except Exception:
        return None, False


def get_continuation_guide(_session_id: str, working_dir: str | None = None) -> str | None:
    """Read and remove continuation guide file if it exists.

    Uses working directory hash to find the file since session_id changes
    after /clear but working directory stays the same.

    Args:
        session_id: Session identifier (unused, kept for API compatibility)
        working_dir: The working directory to use for hashing
    """
    # Use working directory hash - persists across /clear
    wd_hash = get_working_dir_hash(working_dir)
    temp_dir = get_temp_dir()
    continuation_file = Path(temp_dir) / f"cwms-continuation-{wd_hash}.md"

    if not continuation_file.exists():
        return None

    try:
        content = continuation_file.read_text()
        continuation_file.unlink()  # Clean up after reading
        return content
    except Exception:
        return None


def get_project_name(working_dir: str | None = None) -> str:
    """Get current project name from working directory."""
    cwd = working_dir if working_dir else os.getcwd()
    return os.path.basename(cwd)


def find_previous_session_tokens(current_session_id: str) -> int:
    """Find cumulative tokens from a previous session in the same working directory.

    When /clear is issued, a new session_id is generated. The previous session's
    monitor file contains the cumulative token count we need to set as baseline.

    Args:
        current_session_id: The new session's ID (to exclude from search)

    Returns:
        Raw cumulative tokens from the most recent previous session, or 0 if not found
    """
    cwd = os.getcwd()
    temp_dir = get_temp_dir()
    monitor_files = glob.glob(os.path.join(temp_dir, "claude-context-*.json"))

    # Find all sessions for the same working directory, excluding current
    candidates: list[tuple[float, int, str]] = []
    for filepath in monitor_files:
        # Skip current session's file
        if current_session_id in filepath:
            continue

        try:
            with open(filepath) as f:
                data = json.load(f)

            # Only consider sessions from the same working directory
            if data.get("working_directory") != cwd:
                continue

            # Calculate raw cumulative tokens
            adjusted_total = data.get("total_tokens", 0)
            existing_baseline = data.get("token_baseline", 0)
            raw_cumulative = adjusted_total + existing_baseline

            # Get file modification time for sorting
            mtime = os.path.getmtime(filepath)
            candidates.append((mtime, raw_cumulative, filepath))
        except Exception:
            continue

    if not candidates:
        return 0

    # Return tokens from the most recently modified file
    candidates.sort(reverse=True)  # Most recent first
    return candidates[0][1]


def reset_swap_completed_flag(session_id: str, source: str = "") -> None:
    """Clear swap_completed flag to allow new swaps in fresh session.

    For /clear events (after swap): preserve the baseline to reset counter.
    For startup/resume: reset baseline to 0 since Claude's counters start fresh.

    Args:
        session_id: The session ID
        source: The session start source ("startup", "resume", "clear", "compact")
    """
    temp_dir = get_temp_dir()
    monitor_file = os.path.join(temp_dir, f"claude-context-{session_id}.json")

    # For startup/resume, Claude's token counters reset to 0
    # Only for /clear should we maintain a baseline (to show post-swap tokens)
    is_clear = source == "clear"

    try:
        if os.path.exists(monitor_file):
            with open(monitor_file) as f:
                metrics = json.load(f)

            # Clear the swap_completed flag for new session
            metrics["swap_completed"] = False
            metrics["swap_completed_at"] = None

            if is_clear:
                # For /clear: maintain baseline to reset counter after swap
                # Calculate raw cumulative tokens for correct baseline
                adjusted_total = metrics.get("total_tokens", 0)
                existing_baseline = metrics.get("token_baseline", 0)
                raw_cumulative = adjusted_total + existing_baseline
                metrics["token_baseline"] = raw_cumulative
            else:
                # For startup/resume: reset baseline since Claude's counters start fresh
                metrics["token_baseline"] = 0

            with open(monitor_file, "w") as f:
                json.dump(metrics, f)
        elif is_clear:
            # /clear creates new session_id - find previous session's tokens
            raw_cumulative = find_previous_session_tokens(session_id)

            if raw_cumulative > 0:
                metrics = {
                    "session_id": session_id,
                    "swap_completed": False,
                    "swap_completed_at": None,
                    "token_baseline": raw_cumulative,
                    "working_directory": os.getcwd(),
                }
                with open(monitor_file, "w") as f:
                    json.dump(metrics, f)
        # For startup/resume with no existing file, don't create one - statusline will create it with baseline=0
    except Exception:
        # If we can't update, try to delete to start fresh
        with contextlib.suppress(Exception):
            os.unlink(monitor_file)


def main() -> None:
    """Main hook entry point."""
    debug_log("=== SessionStart hook started ===")

    # Read hook input from stdin
    hook_data = json.load(sys.stdin)
    debug_log(f"Hook input keys: {list(hook_data.keys())}")

    session_id = hook_data.get("session_id")
    source = hook_data.get("source", "")
    working_dir = hook_data.get("cwd")  # Get working directory from hook data
    debug_log(f"session_id: {session_id}, source: {source}, working_dir: {working_dir}")

    if not session_id:
        debug_log("EXIT: No session_id")
        sys.exit(0)

    # CRITICAL: Reset swap_completed flag on any session start to allow new swaps
    # This prevents the infinite loop after /clear
    # Pass source so baseline is only maintained for /clear, not startup/resume
    reset_swap_completed_flag(session_id, source)
    debug_log(f"Reset swap_completed flag (source={source})")

    # Only inject context if this is a clear (not startup/resume/compact)
    # source values: "startup", "resume", "clear", "compact"
    if source != "clear":
        debug_log(f"EXIT: source is '{source}', not 'clear'")
        sys.exit(0)

    # Check for bridge summary from auto-swap
    wd_hash = get_working_dir_hash(working_dir)
    debug_log(f"Looking for bridge file with wd_hash: {wd_hash}")
    summary, is_llm_generated = get_bridge_summary(session_id, working_dir)
    debug_log(f"Bridge summary found: {summary is not None}, LLM-generated: {is_llm_generated}")

    if not summary:
        # No bridge summary - this was a manual /clear, not from auto-swap
        debug_log("EXIT: No bridge summary found")
        sys.exit(0)

    # Check for continuation guide (context recovery instructions)
    continuation_guide = get_continuation_guide(session_id, working_dir)
    debug_log(f"Continuation guide found: {continuation_guide is not None}")

    project = get_project_name(working_dir)
    debug_log(f"Project: {project}")

    # Build the context to inject with formatting instructions
    # IMPORTANT: Instructions MUST come BEFORE the summary so Claude reads them first
    if is_llm_generated:
        # LLM-generated summaries are higher quality - simpler instructions
        additional_context = f"""## ⚠️ CONTEXT RECOVERED FROM SWAP ⚠️

**Your context window was automatically swapped to disk.** The following summary was generated before the swap to preserve continuity.

---

{summary}

---

## Instructions

1. **Acknowledge** the recovered context briefly to the user
2. **Continue** with the user's request, using the context above to inform your response
3. If you need more details about swapped content, use `cwms retrieve --project "{project}" --query "<topic>"`

"""
    else:
        # Regex-generated summaries need more explicit formatting instructions
        additional_context = f"""## ⚠️ MANDATORY PRE-RESPONSE INSTRUCTIONS ⚠️

**STOP. READ THIS FIRST BEFORE RESPONDING TO THE USER.**

Your context window was automatically swapped to disk. Before doing ANYTHING else, you MUST:

1. **READ** the "Swapped Context Summary" section below in its entirety
2. **REPORT** it back to the user using the format specified below
3. **ONLY THEN** proceed to address the user's actual request

This is NOT optional. The user expects to see the bridge summary before you continue with their task.

---

## Required Output Format (STEP 1 - DO THIS FIRST)

You MUST begin your response with this summary report:

**📋 Context Recovered from Swap:**

- **Segments swapped:** [X conversation segments, Y tokens]
- **Key topics:** [extract from summary below]

**What we were working on:**
[1-2 sentence description from the summary]

1. [First activity]
2. [Second activity]
3. [Third activity if applicable]

**Files referenced:** [list files from summary]

---

## Swapped Context Summary (READ THIS TO GENERATE STEP 1)

{summary}

---

## STEP 2: After Reporting the Summary Above

Only after you have reported the bridge summary (Step 1), proceed to address the user's request. If the user's request relates to the previous work, use the context from the summary to continue seamlessly.
"""

    # Add continuation guide if available
    if continuation_guide:
        additional_context += f"\n{continuation_guide}\n"
    else:
        # Fallback if continuation guide wasn't created
        additional_context += f"""
### Accessing Previous Context

The full conversation history is searchable:
- **Search:** `cwms search --project "{project}" --query "<topic>"`
- **Retrieve:** `cwms retrieve --project "{project}" --query "<topic>"`
- **Status:** `cwms status --project "{project}"`
"""

    if is_llm_generated:
        additional_context += "\n---\n\n**Note:** This summary was generated by Claude before the context swap for high-quality continuity.\n"
    else:
        additional_context += "\n---\n\n**⚠️ FINAL REMINDER:** Your response MUST begin with the bridge summary report (Step 1). Do not skip directly to the user's request. The user is expecting to see a summary of what was swapped before you continue.\n"

    # Output plain text for context injection
    # Per GitHub Issue #16538 and Claude Code docs: "any non-JSON text written to stdout is added as context"
    # Plain text is simpler and more reliable than hookSpecificOutput.additionalContext
    debug_log(f"Outputting plain text context ({len(additional_context)} chars)")
    print(additional_context)
    debug_log("=== SessionStart hook finished (injected context) ===")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        debug_log(f"EXCEPTION: {type(e).__name__}: {e}")
        import traceback

        debug_log(f"TRACEBACK: {traceback.format_exc()}")
        # Fail gracefully - hooks shouldn't crash the session
        sys.exit(0)
