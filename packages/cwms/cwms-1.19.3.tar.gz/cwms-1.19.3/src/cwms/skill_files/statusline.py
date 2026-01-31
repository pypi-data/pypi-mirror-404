#!/usr/bin/env python3
"""
Status line script for Claude Code that monitors context usage.
Writes context metrics to a monitoring file for hooks to check.
"""

import json
import os
import sys
import tempfile


def main() -> None:
    # Read status line input from Claude Code
    data = json.load(sys.stdin)

    # Extract context window information
    context = data.get("context_window", {})
    used_pct = context.get("used_percentage", 0)
    input_tokens = context.get("current_usage", {}).get("input_tokens", 0)
    total_tokens = context.get("total_input_tokens", 0) + context.get("total_output_tokens", 0)
    context_size = context.get("context_window_size", 200000)

    # Get session ID for unique monitoring file
    session_id = data.get("session_id", "unknown")

    # Load configured threshold from cwms config
    # Default uses DEFAULT_SWAP_TRIGGER_PERCENT from constants
    configured_threshold = 32000
    try:
        from cwms.constants import DEFAULT_SWAP_TRIGGER_PERCENT
        swap_trigger_percent = DEFAULT_SWAP_TRIGGER_PERCENT
    except ImportError:
        swap_trigger_percent = 0.80  # Fallback if constants not available

    try:
        from pathlib import Path

        import yaml

        config_paths = [
            Path(".claude/cwms/config.yaml"),
            Path.home() / ".claude" / "cwms" / "config.yaml",
        ]
        for config_path in config_paths:
            if config_path.exists():
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    if config and "context" in config:
                        threshold_value = config["context"].get("threshold_tokens", 32000)
                        # Handle "auto" value - use context window based threshold
                        if isinstance(threshold_value, str) and threshold_value.lower() == "auto":
                            # Auto-detect based on context window size
                            # Use 25% of context window as threshold (conservative)
                            configured_threshold = min(context_size // 4, 50000)
                        else:
                            configured_threshold = int(threshold_value)
                        swap_trigger_percent = config["context"].get("swap_trigger_percent", swap_trigger_percent)
                        break
    except Exception as e:  # nosec B110
        # Config load failure is non-critical - defaults will be used
        # Write to stderr for debugging (won't affect statusline output)
        print(f"[DEBUG] Config load failed (using defaults): {e}", file=sys.stderr)

    # Calculate swap threshold based on configured threshold, not context window size
    swap_threshold_tokens = int(configured_threshold * swap_trigger_percent)

    # Write to monitoring file (for hooks to read)
    temp_dir = tempfile.gettempdir()
    monitor_file = os.path.join(temp_dir, f"claude-context-{session_id}.json")

    # CRITICAL: Check if swap was already completed to prevent loop
    # If a swap was completed, don't trigger another until session restarts
    # Also read token baseline to reset counter after /clear
    existing_swap_completed = False
    token_baseline = 0
    current_cwd = os.getcwd()
    try:
        if os.path.exists(monitor_file):
            with open(monitor_file) as f:
                existing_data = json.load(f)
                # CRITICAL: Only preserve baseline if working directory matches
                # If user switched to a different repo, reset baseline to avoid
                # carrying over token counts from a different project
                existing_cwd = existing_data.get("working_directory", "")
                if existing_cwd == current_cwd:
                    existing_swap_completed = existing_data.get("swap_completed", False)
                    token_baseline = existing_data.get("token_baseline", 0)
                # else: working directory changed, reset baseline to 0 (default)
    except Exception as e:  # nosec B110
        # Reading existing state is non-critical - fresh state will be used
        print(f"[DEBUG] Monitor file read failed: {e}", file=sys.stderr)

    # Subtract token baseline to show only active (post-clear) tokens
    # This resets the counter after a swap+clear cycle
    # IMPORTANT: Do this BEFORE calculating should_swap so the threshold
    # check uses adjusted tokens, not raw cumulative tokens
    total_tokens = max(0, total_tokens - token_baseline)

    # Calculate should_swap using adjusted tokens (after baseline subtraction)
    should_swap = total_tokens > swap_threshold_tokens

    # If swap was completed, override should_swap to False to prevent loop
    if existing_swap_completed:
        should_swap = False

    monitor_data = {
        "timestamp": data.get("timestamp", 0),
        "session_id": session_id,
        "used_percentage": used_pct,
        "input_tokens": input_tokens,
        "total_tokens": total_tokens,
        "context_size": context_size,
        "should_swap": should_swap,
        "swap_threshold_tokens": swap_threshold_tokens,
        "configured_threshold": configured_threshold,
        "swap_threshold_pct": swap_trigger_percent * 100,
        "working_directory": os.getcwd(),
        "swap_completed": existing_swap_completed,  # Preserve swap_completed flag
        "token_baseline": token_baseline,  # Preserve baseline for next runs
    }

    try:
        with open(monitor_file, "w") as f:
            json.dump(monitor_data, f, indent=2)
    except Exception as e:  # nosec B110
        # Monitor file write failure is non-critical - hooks may not trigger
        print(f"[DEBUG] Monitor file write failed: {e}", file=sys.stderr)

    # Display status line output
    model = data.get("model", {}).get("display_name", "Claude")

    # Calculate usage percentage relative to configured threshold
    threshold_pct = (total_tokens / configured_threshold) * 100 if configured_threshold > 0 else 0

    # Format output based on usage against configured threshold
    if threshold_pct > 90:
        indicator = "🔴"
    elif threshold_pct > 80:
        indicator = "🟡"
    else:
        indicator = "🟢"

    # Show usage relative to configured threshold
    output = f"{indicator} [{model}] Context: {threshold_pct:.1f}% ({total_tokens:,}/{configured_threshold:,} tokens)"

    print(output)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Always output something, even on error
        print("[Claude] Status")
