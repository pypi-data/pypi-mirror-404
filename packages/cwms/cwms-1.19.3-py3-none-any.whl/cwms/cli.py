"""Command-line interface for cwms.

Provides CLI commands for Claude Code to interact with the context cache system.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import click

from cwms.chunker import Message
from cwms.config import Config
from cwms.exceptions import (
    ConfigurationError,
    ContextWindowManagementError,
    RetrievalError,
    StorageCorruptionError,
    StorageError,
    StorageValidationError,
    VectorStoreSyncError,
)
from cwms.logging_config import LOG_LEVEL_ENV_VAR, setup_logging
from cwms.metrics import get_metrics
from cwms.skill import ContextWindowManagementSkill
from cwms.tokens import estimate_tokens
from cwms.validation import (
    validate_file_format,
)

logger = logging.getLogger(__name__)


class InputFormat(Enum):
    """Supported input file formats."""

    AUTO = "auto"
    JSON = "json"  # {"messages": [...]}
    JSONL = "jsonl"  # One message per line
    CLAUDE_SESSION = "claude-session"  # Claude Code session files


class FormatDetectionError(Exception):
    """Error during format detection or parsing."""

    pass


def detect_format(file_path: Path) -> InputFormat:
    """Auto-detect the format of an input file.

    Args:
        file_path: Path to the file to analyze

    Returns:
        Detected InputFormat

    Raises:
        FormatDetectionError: If format cannot be determined
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            first_line = f.readline().strip()

        if not first_line:
            raise FormatDetectionError("File is empty")

        # Try to parse first line as JSON
        try:
            first_obj = json.loads(first_line)
        except json.JSONDecodeError as e:
            raise FormatDetectionError(
                f"First line is not valid JSON: {e}\n"
                f"Hint: Ensure the file contains valid JSON or JSONL format."
            ) from e

        # Check for JSON format (has 'messages' key)
        if isinstance(first_obj, dict) and "messages" in first_obj:
            return InputFormat.JSON

        # Check for Claude session format (has 'type' and optionally 'message')
        if (
            isinstance(first_obj, dict)
            and "type" in first_obj
            and first_obj["type"] in ("user", "assistant")
        ):
            return InputFormat.CLAUDE_SESSION

        # Check for simple JSONL format (has 'role' and 'content')
        if isinstance(first_obj, dict) and "role" in first_obj:
            return InputFormat.JSONL

        # If it's a dict but we can't determine format, give helpful error
        if isinstance(first_obj, dict):
            keys = list(first_obj.keys())[:5]
            raise FormatDetectionError(
                f"Could not determine file format. First object has keys: {keys}\n"
                f"Expected formats:\n"
                f'  - JSON: {{"messages": [...]}}\n'
                f'  - JSONL: {{"role": "user", "content": "..."}}\n'
                f'  - Claude session: {{"type": "user", "message": ...}}'
            )

        raise FormatDetectionError(
            f"Invalid format: expected object, got {type(first_obj).__name__}"
        )

    except OSError as e:
        raise FormatDetectionError(f"Could not read file: {e}") from e


def parse_json_messages(file_path: Path) -> list[Message]:
    """Parse messages from JSON format: {"messages": [...]}.

    Args:
        file_path: Path to JSON file

    Returns:
        List of Message objects

    Raises:
        FormatDetectionError: On parse errors
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise FormatDetectionError(f"Expected JSON object, got {type(data).__name__}")

        if "messages" not in data:
            raise FormatDetectionError(
                'JSON file must contain "messages" key.\n' f"Found keys: {list(data.keys())}"
            )

        messages = []
        for i, msg_data in enumerate(data["messages"]):
            try:
                messages.append(_parse_message_dict(msg_data))
            except (KeyError, TypeError) as e:
                raise FormatDetectionError(
                    f"Invalid message at index {i}: {e}\n"
                    f'Expected format: {{"role": "user"|"assistant", "content": "..."}}'
                ) from e

        return messages

    except json.JSONDecodeError as e:
        raise FormatDetectionError(f"Invalid JSON: {e}") from e


def parse_jsonl_messages(file_path: Path) -> list[Message]:
    """Parse messages from JSONL format (one message per line).

    Args:
        file_path: Path to JSONL file

    Returns:
        List of Message objects

    Raises:
        FormatDetectionError: On parse errors
    """
    messages = []
    try:
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    msg_data = json.loads(line)
                    messages.append(_parse_message_dict(msg_data))
                except json.JSONDecodeError as e:
                    raise FormatDetectionError(f"Invalid JSON on line {line_num}: {e}") from e
                except (KeyError, TypeError) as e:
                    raise FormatDetectionError(
                        f"Invalid message on line {line_num}: {e}\n"
                        f'Expected format: {{"role": "user"|"assistant", "content": "..."}}'
                    ) from e

        return messages

    except OSError as e:
        raise FormatDetectionError(f"Could not read file: {e}") from e


def parse_claude_session(
    file_path: Path,
    project_filter: str | None = None,
) -> list[Message]:
    """Parse messages from Claude Code session JSONL format.

    Claude session files have entries like:
    - {"type": "user", "message": {"role": "user", "content": "..."}}
    - {"type": "assistant", "message": {"role": "assistant", "content": [...]}}

    Args:
        file_path: Path to Claude session JSONL file
        project_filter: Optional project path to filter by

    Returns:
        List of Message objects

    Raises:
        FormatDetectionError: On parse errors
    """
    messages = []
    try:
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue  # Skip non-JSON lines (like snapshot updates)

                # Skip non-message entries (snapshots, etc.)
                entry_type = entry.get("type")
                if entry_type not in ("user", "assistant"):
                    continue

                # Filter by project if specified
                if project_filter:
                    entry_project = entry.get("cwd") or entry.get("project")
                    # Skip entries without project info when filter is specified
                    if not entry_project or project_filter not in entry_project:
                        continue

                # Extract message
                message_data = entry.get("message")
                if not message_data:
                    continue

                try:
                    msg = _parse_claude_message(message_data, entry_type)
                    if msg:
                        messages.append(msg)
                except (KeyError, TypeError):
                    # Skip malformed messages
                    continue

        return messages

    except OSError as e:
        raise FormatDetectionError(f"Could not read file: {e}") from e


def _parse_message_dict(msg_data: dict[str, Any]) -> Message:
    """Parse a message dict into a Message object.

    Args:
        msg_data: Dictionary with role, content, and optional tool_calls/tool_results

    Returns:
        Message object
    """
    role = msg_data.get("role", "user")
    content = msg_data.get("content", "")

    # Handle content that might be a list (Claude API format)
    if isinstance(content, list):
        content = _extract_text_content(content)

    return Message(
        role=role,
        content=content,
        tool_calls=msg_data.get("tool_calls", []),
        tool_results=msg_data.get("tool_results", []),
    )


def _parse_claude_message(
    message_data: dict[str, Any] | str,
    entry_type: str,
) -> Message | None:
    """Parse a Claude Code message into a Message object.

    Args:
        message_data: The message dict or string from Claude session
        entry_type: "user" or "assistant"

    Returns:
        Message object or None if content is empty
    """
    # Handle user messages (can be string or dict)
    if entry_type == "user":
        content: str = ""
        if isinstance(message_data, str):
            content = message_data
        elif isinstance(message_data, dict):
            raw_content = message_data.get("content", "")
            if isinstance(raw_content, list):
                content = _extract_text_content(raw_content)
            elif isinstance(raw_content, str):
                content = raw_content

        if not content:
            return None
        return Message(role="user", content=content)

    # Handle assistant messages (Claude API format)
    if entry_type == "assistant" and isinstance(message_data, dict):
        raw_content = message_data.get("content", [])
        tool_calls: list[dict[str, Any]] = []
        content = ""

        if isinstance(raw_content, list):
            # Extract text and tool_use blocks
            text_parts: list[str] = []
            for block in raw_content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        tool_calls.append(block)
                elif isinstance(block, str):
                    text_parts.append(block)
            content = "\n".join(text_parts)
        elif isinstance(raw_content, str):
            content = raw_content

        if not content and not tool_calls:
            return None

        return Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls,
        )

    return None


def _extract_text_content(content_list: list[Any]) -> str:
    """Extract text content from a list of content blocks.

    Args:
        content_list: List of content blocks (strings or dicts with type/text)

    Returns:
        Combined text content
    """
    text_parts = []
    for block in content_list:
        if isinstance(block, str):
            text_parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(block.get("text", ""))
    return "\n".join(text_parts)


def load_messages(
    file_path: Path,
    format_type: InputFormat = InputFormat.AUTO,
    project_filter: str | None = None,
) -> list[Message]:
    """Load messages from a file, auto-detecting format if needed.

    Args:
        file_path: Path to the message file
        format_type: Format to use (or AUTO to detect)
        project_filter: For Claude sessions, filter by project path

    Returns:
        List of Message objects

    Raises:
        FormatDetectionError: On detection or parse errors
    """
    if format_type == InputFormat.AUTO:
        format_type = detect_format(file_path)

    if format_type == InputFormat.JSON:
        return parse_json_messages(file_path)
    elif format_type == InputFormat.JSONL:
        return parse_jsonl_messages(file_path)
    elif format_type == InputFormat.CLAUDE_SESSION:
        return parse_claude_session(file_path, project_filter)
    else:
        raise FormatDetectionError(f"Unknown format: {format_type}")


def get_skill() -> ContextWindowManagementSkill:
    """Create skill instance with appropriate config."""
    config = Config.load_or_default()
    # Use 'none' embeddings if the configured provider isn't available
    try:
        return ContextWindowManagementSkill(config=config)
    except ImportError:
        config.embedding_provider = "none"
        return ContextWindowManagementSkill(config=config)


def output_json(data: dict[str, Any]) -> None:
    """Output JSON to stdout."""
    click.echo(json.dumps(data, indent=2, default=str))


def output_error(message: str) -> None:
    """Output error as JSON to stderr."""
    error_data = {"success": False, "error": message}
    click.echo(json.dumps(error_data), err=True)
    sys.exit(1)


@click.group()
@click.version_option(package_name="cwms")
def main() -> None:
    """Context Cache - Extended context memory for Claude Code.

    Provides intelligent swap-to-disk context management for long conversations.

    Set CWMS_LOG_LEVEL environment variable to control logging verbosity:
    DEBUG, INFO, WARNING (default), ERROR, CRITICAL
    """
    # Initialize logging from environment variable
    # Only setup logging if LOG_LEVEL env var is explicitly set (avoid noise in CLI output)
    if os.environ.get(LOG_LEVEL_ENV_VAR):
        import logging as _logging

        _logger = _logging.getLogger("cwms")
        if not _logger.handlers:
            setup_logging()


@main.command()
@click.option("--project", required=True, help="Project identifier")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed status information including config and validation",
)
@click.option(
    "--summarization",
    is_flag=True,
    help="Show summarization configuration and monthly usage stats",
)
def status(project: str, verbose: bool, summarization: bool) -> None:
    """Show current context cache status for a project.

    Use --verbose for detailed information including configuration
    and storage validation.

    Use --summarization to see API summarization config and usage stats.
    """
    try:
        skill = get_skill()
        status_info = skill.get_status(project)

        response: dict[str, Any] = {
            "success": True,
            "project": status_info.project,
            "total_chunks": status_info.total_chunks,
            "total_tokens": status_info.total_tokens,
            "oldest_chunk": status_info.oldest_chunk,
            "newest_chunk": status_info.newest_chunk,
            "embedding_provider": status_info.embedding_provider,
            "storage_dir": str(status_info.storage_dir),
            "current_session_tokens": status_info.current_session_tokens,
        }

        if verbose:
            # Add configuration info
            cfg = Config.load_or_default()
            response["config"] = {
                "threshold_tokens": cfg.threshold_tokens,
                "swap_trigger_percent": cfg.swap_trigger_percent,
                "preserve_recent_tokens": cfg.preserve_recent_tokens,
                "search_mode": cfg.search_mode,
            }

            # Add quick validation check
            validation = skill.storage.validate_storage(project)
            response["storage_valid"] = validation["valid"]
            if not validation["valid"]:
                response["storage_issues"] = len(validation["errors"])
                response["storage_warnings"] = len(validation["warnings"])

        if summarization:
            # Add summarization configuration and usage
            cfg = Config.load_or_default()
            # Treat 0.00 as no cost limit (None)
            cost_limit = cfg.summarization_monthly_cost_limit_usd
            if cost_limit is not None and cost_limit == 0.0:
                cost_limit = None
            response["summarization"] = {
                "provider": cfg.summarization_provider,
                "model": cfg.summarization_api_model,
                "max_tokens": cfg.summarization_api_max_tokens,
                "cost_limit_usd": cost_limit,
            }

            # Get usage stats if API provider is configured
            if cfg.summarization_provider == "api":
                try:
                    from cwms.summarizer import APISummarizer

                    # Try to get usage stats (may fail if anthropic not installed)
                    summarizer = APISummarizer(
                        model=cfg.summarization_api_model,
                        max_api_tokens=cfg.summarization_api_max_tokens,
                        storage_dir=cfg.storage_dir,
                        monthly_cost_limit=cost_limit,
                    )
                    usage_stats = summarizer.get_usage_stats()
                    response["summarization"]["monthly_usage"] = usage_stats
                except ImportError:
                    response["summarization"]["monthly_usage"] = {
                        "error": "anthropic package not installed"
                    }
                except ValueError as e:
                    # API key not configured
                    response["summarization"]["monthly_usage"] = {"error": str(e)}
            else:
                response["summarization"]["monthly_usage"] = {
                    "note": "Usage tracking only available with 'api' provider"
                }

        output_json(response)
    except FileNotFoundError:
        output_error(
            f"Project '{project}' not found.\n"
            "Hint: Use 'cwms swap' to create a project, or check the project name."
        )
    except StorageError as e:
        output_error(f"Storage error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in status")
        output_error(f"Unexpected error: {e}")


@main.command()
@click.option("--project", required=True, help="Project identifier")
@click.option(
    "--messages-file",
    required=True,
    type=click.Path(exists=True),
    help="File containing messages to swap",
)
@click.option(
    "--format",
    "format_type",
    type=click.Choice(["auto", "json", "jsonl", "claude-session"]),
    default="auto",
    help="Input file format (auto-detected by default)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation and processing information",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Skip message validation before swap (faster but less safe)",
)
def swap(
    project: str,
    messages_file: str,
    format_type: str,
    verbose: bool,
    skip_validation: bool,
) -> None:
    """Swap messages to disk storage.

    Supported file formats (auto-detected by default):

    \b
    - json: {"messages": [{"role": "user", "content": "..."}]}
    - jsonl: One message per line: {"role": "user", "content": "..."}
    - claude-session: Claude Code session files with type/message structure

    Use --verbose for detailed validation output.
    Use --skip-validation for faster processing when you trust the input.
    """
    try:
        # Parse format type
        fmt = InputFormat(format_type)
        file_path = Path(messages_file)

        # Validate file format before processing
        if not skip_validation:
            validation_result = validate_file_format(file_path, verbose=verbose)
            if not validation_result.valid:
                error_msg = "Message validation failed:\n"
                for err in validation_result.errors[:5]:
                    error_msg += f"  - {err}\n"
                if len(validation_result.errors) > 5:
                    error_msg += f"  ... and {len(validation_result.errors) - 5} more errors\n"
                error_msg += "\nHint: Use --skip-validation to bypass validation (not recommended)"
                output_error(error_msg)
                return

            if verbose and validation_result.warnings:
                # Output warnings but continue
                click.echo("Validation warnings:", err=True)
                for warning in validation_result.warnings:
                    click.echo(f"  - {warning}", err=True)

        # Load messages using format detection
        messages = load_messages(file_path, fmt)

        if not messages:
            output_json(
                {
                    "success": True,
                    "chunks_stored": 0,
                    "tokens_stored": 0,
                    "summary": "No messages to swap",
                }
            )
            return

        skill = get_skill()
        chunks_count, tokens_count, summary = skill.swap_out(project, messages)

        result: dict[str, Any] = {
            "success": True,
            "chunks_stored": chunks_count,
            "tokens_stored": tokens_count,
            "summary": summary,
            "format_detected": fmt.value,
            "messages_loaded": len(messages),
        }

        # Add verbose stats
        if verbose and not skip_validation:
            result["validation"] = validation_result.stats

        output_json(result)

    except FormatDetectionError as e:
        error_msg = str(e)
        # Add suggestions for common errors
        if "empty" in error_msg.lower():
            error_msg += "\nHint: Ensure the file contains valid message data"
        elif "json" in error_msg.lower():
            error_msg += "\nHint: Check the file format matches the expected structure"
        output_error(error_msg)
    except VectorStoreSyncError as e:
        output_error(f"Vector store sync error: {e}")
    except StorageError as e:
        output_error(f"Storage error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in swap")
        output_error(
            f"Unexpected error: {e}\nHint: Use 'cwms validate --project {project}' to check storage integrity"
        )


@main.command()
@click.option("--project", required=True, help="Project identifier")
@click.option("--query", required=True, help="Search query")
@click.option("--top-k", default=5, type=int, help="Number of results to return")
@click.option(
    "--output-format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text for human-readable, json for programmatic use)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed search information including scores",
)
def search(project: str, query: str, top_k: int, output_format: str, verbose: bool) -> None:
    """Search stored context for relevant chunks.

    Returns JSON array of matching chunks with scores.

    Use --verbose for detailed scoring information.
    Use --output-format json for programmatic use (e.g., in hooks).

    Example:
        cwms search --project "my-project" --query "error handling"
        cwms search --project "my-project" --query "API" --top-k 10
        cwms search --project "my-project" --query "auth" --output-format json
    """
    try:
        skill = get_skill()

        # Check if project exists
        status_info = skill.get_status(project)
        if status_info.total_chunks == 0:
            output_json(
                {
                    "success": True,
                    "query": query,
                    "result_count": 0,
                    "results": [],
                    "message": f"No chunks stored for project '{project}'. Use 'cwms swap' to add data.",
                }
            )
            return

        results = skill.search(project, query, top_k=top_k)

        if output_format == "json":
            # JSON format for programmatic use (e.g., hooks)
            # Simplified structure: score, summary, timestamp
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "score": result.get("score", 0.0),
                        "summary": result.get("summary", ""),
                        "timestamp": result.get("timestamp", ""),
                    }
                )
            output_json(
                {
                    "success": True,
                    "query": query,
                    "result_count": len(formatted_results),
                    "results": formatted_results,
                }
            )
        else:
            # Text format for human-readable output (existing behavior)
            response: dict[str, Any] = {
                "success": True,
                "query": query,
                "result_count": len(results),
                "results": results,
            }

            if verbose:
                response["search_mode"] = skill.config.search_mode
                response["total_chunks_searched"] = status_info.total_chunks
                response["embedding_provider"] = status_info.embedding_provider

            if not results:
                response["message"] = (
                    "No matching chunks found. Try:\n"
                    "  - Using different keywords\n"
                    "  - Checking stored summaries with 'cwms summaries'"
                )

            output_json(response)
    except RetrievalError as e:
        output_error(f"Retrieval error: {e}")
    except StorageError as e:
        output_error(f"Storage error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in search")
        output_error(f"Unexpected error: {e}\nHint: Check if the project exists with 'cwms status'")


@main.command()
@click.option("--project", required=True, help="Project identifier")
@click.option("--query", required=True, help="Retrieval query")
@click.option("--top-k", default=5, type=int, help="Number of chunks to retrieve")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show retrieval details including matched chunks",
)
def retrieve(project: str, query: str, top_k: int, verbose: bool) -> None:
    """Retrieve and format context for injection.

    Returns formatted text ready to be injected into conversation.

    Use --verbose for detailed retrieval information.

    Example:
        cwms retrieve --project "my-project" --query "authentication"
    """
    try:
        skill = get_skill()

        # Check if project exists
        status_info = skill.get_status(project)
        if status_info.total_chunks == 0:
            output_json(
                {
                    "success": True,
                    "query": query,
                    "context": "",
                    "message": f"No context stored for project '{project}'. Use 'cwms swap' to add data.",
                }
            )
            return

        formatted_context = skill.retrieve(project, query, top_k=top_k)

        response: dict[str, Any] = {
            "success": True,
            "query": query,
            "context": formatted_context,
        }

        if verbose:
            response["chunks_retrieved"] = min(top_k, status_info.total_chunks)
            response["total_chunks_available"] = status_info.total_chunks
            response["context_length"] = len(formatted_context)

        if not formatted_context:
            response["message"] = (
                "No relevant context found. Try:\n"
                "  - Using different search terms\n"
                "  - Increasing --top-k value\n"
                "  - Checking stored content with 'cwms summaries'"
            )

        output_json(response)
    except RetrievalError as e:
        output_error(f"Retrieval error: {e}")
    except StorageError as e:
        output_error(f"Storage error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in retrieve")
        output_error(f"Unexpected error: {e}\nHint: Check if the project exists with 'cwms status'")


@main.command()
@click.option("--project", required=True, help="Project identifier")
def summaries(project: str) -> None:
    """List summaries of all stored chunks for a project."""
    try:
        skill = get_skill()
        chunk_summaries = skill.get_summaries(project)

        output_json(
            {
                "success": True,
                "project": project,
                "chunk_count": len(chunk_summaries),
                "summaries": chunk_summaries,
            }
        )
    except StorageError as e:
        output_error(f"Storage error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in summaries")
        output_error(f"Unexpected error: {e}")


@main.command()
@click.option("--project", required=True, help="Project identifier")
@click.option("--confirm", is_flag=True, help="Confirm deletion without prompt")
def clear(project: str, confirm: bool) -> None:
    """Clear all stored context for a project."""
    try:
        skill = get_skill()

        # Check if project has data
        status_info = skill.get_status(project)
        if status_info.total_chunks == 0:
            output_json(
                {
                    "success": True,
                    "message": "No context to clear for this project",
                    "chunks_deleted": 0,
                }
            )
            return

        if not confirm:
            # In non-interactive mode, require --confirm flag
            output_error(
                f"Project has {status_info.total_chunks} chunks. " "Use --confirm flag to delete."
            )
            return

        deleted = skill.clear_project(project)

        output_json(
            {
                "success": True,
                "message": f"Cleared context for project: {project}",
                "project_deleted": deleted,
                "chunks_deleted": status_info.total_chunks,
            }
        )
    except StorageError as e:
        output_error(f"Storage error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in clear")
        output_error(f"Unexpected error: {e}")


@main.command()
def config() -> None:
    """Display current configuration."""
    try:
        cfg = Config.load_or_default()

        output_json(
            {
                "success": True,
                "config": cfg.to_dict(),
            }
        )
    except ConfigurationError as e:
        output_error(f"Configuration error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in config")
        output_error(f"Unexpected error: {e}")


@main.command("context-window")
@click.option(
    "--model",
    default=None,
    help="Claude model name (auto-detects if not specified)",
)
def context_window(model: str | None) -> None:
    """Display context window configuration for current or specified model.

    Shows the threshold, preserve_recent, and other context-related settings
    based on the model's context window size.

    Example:
        cwms context-window
        cwms context-window --model claude-opus-4-5
    """
    try:
        from cwms.model_config import (
            format_model_config_summary,
            get_model_context_config,
        )

        # Get model configuration
        model_config = get_model_context_config(model_name=model)

        # Load current config for comparison
        cfg = Config.load_or_default()

        output_json(
            {
                "success": True,
                "model_name": model_config.model_name,
                "context_window": model_config.context_window,
                "threshold_tokens": model_config.threshold_tokens,
                "swap_trigger_percent": model_config.swap_trigger_percent,
                "preserve_recent_tokens": model_config.preserve_recent_tokens,
                "detected": model_config.detected,
                "current_config": {
                    "threshold_tokens": cfg.threshold_tokens,
                    "preserve_recent_tokens": cfg.preserve_recent_tokens,
                    "is_auto": cfg.is_threshold_auto,
                },
                "formatted_summary": format_model_config_summary(model_config),
            }
        )
    except ConfigurationError as e:
        output_error(f"Configuration error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in context_window")
        output_error(f"Unexpected error: {e}")


@main.command()
@click.option(
    "--messages-file",
    required=True,
    type=click.Path(exists=True),
    help="File containing messages to estimate",
)
@click.option(
    "--threshold",
    default=32000,
    type=int,
    help="Token threshold for swap recommendation",
)
@click.option(
    "--format",
    "format_type",
    type=click.Choice(["auto", "json", "jsonl", "claude-session"]),
    default="auto",
    help="Input file format (auto-detected by default)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed token breakdown and validation",
)
def estimate(messages_file: str, threshold: int, format_type: str, verbose: bool) -> None:
    """Estimate token count for messages and recommend swap.

    Useful for Claude to check if context should be swapped.
    Supports multiple file formats (auto-detected by default).

    Use --verbose for detailed token breakdown.

    Example:
        cwms estimate --messages-file conversation.json
        cwms estimate --messages-file session.jsonl --threshold 64000
    """
    try:
        # Parse format type
        fmt = InputFormat(format_type)
        file_path = Path(messages_file)

        # Validate before loading (quick check)
        validation_result = validate_file_format(file_path, verbose=verbose)
        if not validation_result.valid:
            error_msg = "File validation failed:\n"
            for err in validation_result.errors[:3]:
                error_msg += f"  - {err}\n"
            error_msg += "\nHint: Use 'cwms validate-messages' for detailed validation"
            output_error(error_msg)
            return

        # Load messages using format detection
        messages = load_messages(file_path, fmt)

        if not messages:
            output_json(
                {
                    "success": True,
                    "token_count": 0,  # nosec B105
                    "message_count": 0,
                    "should_swap": False,
                    "message": "No messages found in file",
                }
            )
            return

        # Calculate token count
        total_tokens = 0
        user_tokens = 0
        assistant_tokens = 0
        for msg in messages:
            tokens = estimate_tokens(msg.content)
            total_tokens += tokens
            if msg.role == "user":
                user_tokens += tokens
            elif msg.role == "assistant":
                assistant_tokens += tokens

        # Get config for swap threshold
        cfg = Config.load_or_default()
        swap_threshold = int(threshold * cfg.swap_trigger_percent)
        should_swap = total_tokens >= swap_threshold

        response: dict[str, Any] = {
            "success": True,
            "token_count": total_tokens,
            "message_count": len(messages),
            "threshold": threshold,
            "swap_threshold": swap_threshold,
            "should_swap": should_swap,
            "preserve_recent_tokens": cfg.preserve_recent_tokens,
            "format_detected": fmt.value,
        }

        if verbose:
            response["token_breakdown"] = {
                "user_tokens": user_tokens,
                "assistant_tokens": assistant_tokens,
                "user_messages": validation_result.stats.get("user_messages", 0),
                "assistant_messages": validation_result.stats.get("assistant_messages", 0),
            }
            response["threshold_percent"] = f"{cfg.swap_trigger_percent * 100:.0f}%"
            response["tokens_until_swap"] = max(0, swap_threshold - total_tokens)

        # Add recommendation message
        if should_swap:
            response["recommendation"] = (
                f"Swap recommended: {total_tokens} tokens exceeds swap threshold of {swap_threshold}"
            )
        else:
            response["recommendation"] = (
                f"No swap needed: {total_tokens} tokens is below threshold of {swap_threshold} "
                f"({swap_threshold - total_tokens} tokens remaining)"
            )

        output_json(response)
    except FormatDetectionError as e:
        error_msg = str(e)
        if "empty" in error_msg.lower():
            error_msg += "\nHint: Ensure the file contains message data"
        output_error(error_msg)
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in estimate")
        output_error(f"Unexpected error: {e}")


@main.command()
@click.option("--project", required=True, help="Project identifier")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation information",
)
@click.option(
    "--fix",
    is_flag=True,
    help="Attempt to fix detected issues (runs repair)",
)
def validate(project: str, verbose: bool, fix: bool) -> None:
    """Validate storage integrity for a project.

    Checks for corruption and inconsistencies in stored chunks:
    - Chunks file: Valid JSONL with required fields
    - Metadata file: Valid JSONL with required fields
    - Index file: Valid JSONL format
    - BM25 stats: Valid JSON
    - Consistency: All files have matching chunk IDs

    Use --verbose for detailed output.
    Use --fix to automatically repair issues.

    Example:
        cwms validate --project "my-project"
        cwms validate --project "my-project" --verbose
        cwms validate --project "my-project" --fix
    """
    try:
        skill = get_skill()
        result = skill.storage.validate_storage(project)

        # Build response with helpful messages
        response: dict[str, Any] = {
            "success": True,
            "project": project,
            "valid": result["valid"],
            "chunks_count": result["chunks_count"],
            "metadata_count": result["metadata_count"],
            "index_count": result["index_count"],
        }

        # Add errors with suggestions
        if result["errors"]:
            error_msgs = []
            for err in result["errors"]:
                if "Corrupted data" in err:
                    err += f" | Suggestion: Run 'cwms repair --project \"{project}\"'"
                elif "missing required fields" in err:
                    err += " | Suggestion: Check if data was partially written"
                error_msgs.append(err)
            response["errors"] = error_msgs

        # Add warnings with suggestions
        if result["warnings"]:
            warning_msgs = []
            for warn in result["warnings"]:
                if "missing from metadata" in warn or "missing from index" in warn:
                    warn += f" | Suggestion: Run 'cwms repair --project \"{project}\"'"
                warning_msgs.append(warn)
            response["warnings"] = warning_msgs

        if verbose:
            # Add detailed information
            status_info = skill.get_status(project)
            response["details"] = {
                "total_tokens": status_info.total_tokens,
                "storage_dir": str(status_info.storage_dir),
                "embedding_provider": status_info.embedding_provider,
            }

        # Auto-fix if requested
        if fix and (result["errors"] or result["warnings"]):
            repair_result = skill.storage.repair(project, dry_run=False)
            response["repair_performed"] = True
            response["repair_actions"] = repair_result["actions"]
            response["chunks_recovered"] = repair_result["chunks_recovered"]
            response["chunks_lost"] = repair_result["chunks_lost"]

            # Re-validate after repair
            new_result = skill.storage.validate_storage(project)
            response["valid_after_repair"] = new_result["valid"]

        # Add summary message
        if result["valid"]:
            response["message"] = "Storage is valid"
        elif fix:
            response["message"] = (
                "Storage repaired"
                if response.get("valid_after_repair")
                else "Some issues remain after repair"
            )
        else:
            response["message"] = (
                f"Storage has {len(result['errors'])} error(s) and "
                f"{len(result['warnings'])} warning(s). "
                "Use --fix to attempt automatic repair."
            )

        output_json(response)
    except StorageCorruptionError as e:
        output_error(f"Storage corrupted: {e}")
    except StorageValidationError as e:
        output_error(f"Validation error: {e}")
    except StorageError as e:
        output_error(f"Storage error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in validate")
        output_error(f"Unexpected error: {e}")


@main.command("validate-messages")
@click.option(
    "--messages-file",
    required=True,
    type=click.Path(exists=True),
    help="File containing messages to validate",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation information",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Use strict validation (warn about unexpected fields)",
)
def validate_messages_cmd(
    messages_file: str,
    verbose: bool,
    strict: bool,
) -> None:
    """Validate a messages file without swapping.

    Checks message format and content before swap:
    - File exists and is readable
    - Valid JSON/JSONL format
    - Required fields (role, content)
    - Valid field values
    - Content structure

    Use this to check a file before running swap.

    Example:
        cwms validate-messages --messages-file messages.json
        cwms validate-messages --messages-file session.jsonl --verbose
    """
    try:
        file_path = Path(messages_file)
        result = validate_file_format(file_path, verbose=verbose, strict=strict)

        response: dict[str, Any] = {
            "success": True,
            "valid": result.valid,
            "file": str(file_path),
        }

        if result.stats:
            response["format"] = result.stats.get("format", "unknown")
            response["message_count"] = result.stats.get("total_messages", 0)
            response["user_messages"] = result.stats.get("user_messages", 0)
            response["assistant_messages"] = result.stats.get("assistant_messages", 0)

        if result.errors:
            response["errors"] = [str(e) for e in result.errors]

        if result.warnings:
            response["warnings"] = result.warnings

        if verbose:
            response["stats"] = result.stats

        # Add helpful summary
        if result.valid:
            response["message"] = (
                f"File is valid. Ready to swap {result.stats.get('total_messages', 0)} messages."
            )
        else:
            response["message"] = (
                f"Validation failed with {len(result.errors)} error(s). "
                "Fix the errors above before swapping."
            )

        output_json(response)

    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in validate_messages_cmd")
        output_error(f"Unexpected error: {e}")


@main.command()
@click.option("--project", required=True, help="Project identifier")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm repair without prompt",
)
def repair(project: str, dry_run: bool, confirm: bool) -> None:
    """Repair storage for a project.

    Rebuilds secondary files (metadata, index, stats) from the primary
    chunks file. Use --dry-run to see what would be done first.

    Example:
        cwms repair --project "my-project" --dry-run
        cwms repair --project "my-project" --confirm
    """
    try:
        skill = get_skill()

        # First validate to show current state
        validation = skill.storage.validate_storage(project)

        if validation["valid"] and not validation["warnings"]:
            output_json(
                {
                    "success": True,
                    "message": "Storage is already valid, no repair needed",
                    "project": project,
                }
            )
            return

        if not confirm and not dry_run:
            output_error(
                f"Storage has {len(validation['errors'])} errors and "
                f"{len(validation['warnings'])} warnings. "
                "Use --dry-run to preview or --confirm to proceed."
            )
            return

        result = skill.storage.repair(project, dry_run=dry_run)

        output_json(
            {
                "success": True,
                "project": project,
                "dry_run": dry_run,
                "actions": result["actions"],
                "chunks_recovered": result["chunks_recovered"],
                "chunks_lost": result["chunks_lost"],
            }
        )
    except StorageError as e:
        output_error(f"Storage error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in repair")
        output_error(f"Unexpected error: {e}")


@main.command("import-history")
@click.option("--project", required=True, help="Project identifier to import into")
@click.option(
    "--history-file",
    type=click.Path(exists=True),
    help="Path to Claude Code session file or history.jsonl",
)
@click.option(
    "--sessions-dir",
    type=click.Path(exists=True),
    help="Path to Claude Code projects directory (default: ~/.claude/projects)",
)
@click.option(
    "--since",
    type=click.DateTime(formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]),
    help="Only import sessions after this date (YYYY-MM-DD or ISO format)",
)
@click.option(
    "--filter-project",
    help="Filter by project path (substring match)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be imported without making changes",
)
def import_history(
    project: str,
    history_file: str | None,
    sessions_dir: str | None,
    since: datetime | None,
    filter_project: str | None,
    dry_run: bool,
) -> None:
    """Import conversation history from Claude Code sessions.

    Import from a specific session file:

    \b
        cwms import-history --project "my-project" \\
            --history-file ~/.claude/projects/.../session-id.jsonl

    Import all sessions for a project path:

    \b
        cwms import-history --project "my-project" \\
            --filter-project "/path/to/project" \\
            --since "2025-01-01"

    Import from all sessions in a directory:

    \b
        cwms import-history --project "my-project" \\
            --sessions-dir ~/.claude/projects \\
            --since "2025-01-01"
    """
    try:
        # Collect session files to process
        session_files: list[Path] = []

        if history_file:
            # Single file specified
            session_files.append(Path(history_file))
        else:
            # Scan sessions directory
            sessions_path = (
                Path(sessions_dir) if sessions_dir else Path.home() / ".claude" / "projects"
            )

            if not sessions_path.exists():
                output_error(
                    f"Sessions directory not found: {sessions_path}\n"
                    "Hint: Specify --sessions-dir or --history-file"
                )
                return

            # Find all session JSONL files (exclude subagent files)
            for jsonl_file in sessions_path.rglob("*.jsonl"):
                # Skip subagent files
                if "subagents" in str(jsonl_file):
                    continue
                session_files.append(jsonl_file)

        if not session_files:
            output_error(
                "No session files found.\n"
                "Hint: Use --history-file to specify a file or check --sessions-dir path"
            )
            return

        # Filter by modification time if --since specified
        if since:
            filtered_files = []
            for f in session_files:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime >= since:
                    filtered_files.append(f)
            session_files = filtered_files

            if not session_files:
                output_json(
                    {
                        "success": True,
                        "message": f"No sessions found after {since.isoformat()}",
                        "sessions_scanned": 0,
                        "messages_imported": 0,
                    }
                )
                return

        # Process each session file
        all_messages: list[Message] = []
        sessions_processed = 0
        errors: list[str] = []

        for session_file in sorted(session_files, key=lambda f: f.stat().st_mtime):
            try:
                messages = parse_claude_session(session_file, filter_project)
                if messages:
                    all_messages.extend(messages)
                    sessions_processed += 1
            except FormatDetectionError as e:
                errors.append(f"{session_file.name}: {e}")
            except ContextWindowManagementError as e:
                errors.append(f"{session_file.name}: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error processing {session_file.name}")
                errors.append(f"{session_file.name}: Unexpected error: {e}")

        if not all_messages:
            output_json(
                {
                    "success": True,
                    "message": "No messages found matching criteria",
                    "sessions_scanned": len(session_files),
                    "sessions_with_matches": sessions_processed,
                    "messages_imported": 0,
                    "errors": errors if errors else None,
                }
            )
            return

        if dry_run:
            # Show what would be imported
            total_tokens = sum(estimate_tokens(m.content) for m in all_messages)
            output_json(
                {
                    "success": True,
                    "dry_run": True,
                    "sessions_scanned": len(session_files),
                    "sessions_with_matches": sessions_processed,
                    "messages_to_import": len(all_messages),
                    "estimated_tokens": total_tokens,
                    "errors": errors if errors else None,
                }
            )
            return

        # Import messages
        skill = get_skill()
        chunks_count, tokens_count, summary = skill.swap_out(project, all_messages)

        output_json(
            {
                "success": True,
                "project": project,
                "sessions_scanned": len(session_files),
                "sessions_with_matches": sessions_processed,
                "messages_imported": len(all_messages),
                "chunks_stored": chunks_count,
                "tokens_stored": tokens_count,
                "summary": summary,
                "errors": errors if errors else None,
            }
        )

    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in import_history")
        output_error(f"Unexpected error: {e}")


@main.command()
@click.option(
    "--auto-swap/--no-auto-swap",
    default=False,
    help="Install auto-swap hooks and statusline (optional)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing files",
)
def install_skill(auto_swap: bool, force: bool) -> None:
    """Install cwms skill to ~/.claude/skills/cwms/.

    This copies the SKILL.md file, config.yaml template, and optionally the
    auto-swap hooks to your Claude Code configuration directory.

    Files installed:
    - SKILL.md → ~/.claude/skills/cwms/
    - config.yaml → ~/.claude/cwms/

    The auto-swap feature (--auto-swap) also includes:
    - Status line monitor (tracks context usage)
    - Stop hook (triggers swap when threshold exceeded)
    - SessionStart hook (injects bridge summary after /clear)

    Example:
        cwms install-skill                    # Basic skill + config
        cwms install-skill --auto-swap       # Skill + config + auto-swap hooks
        cwms install-skill --auto-swap --force  # Overwrite existing
    """
    import shutil
    from importlib import resources

    try:
        # Target directories
        skill_dir = Path.home() / ".claude" / "skills" / "cwms"
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Get package resource path
        package_files = resources.files("cwms") / "skill_files"

        # Install SKILL.md
        skill_md_src = package_files / "SKILL.md"
        skill_md_dest = skill_dir / "SKILL.md"

        if skill_md_dest.exists() and not force:
            click.echo(f"⚠️  {skill_md_dest} already exists. Use --force to overwrite.")
        else:
            with resources.as_file(skill_md_src) as src_path:
                shutil.copy(src_path, skill_md_dest)
            click.echo(f"✅ Installed SKILL.md to {skill_md_dest}")

        # Install config.yaml to ~/.claude/cwms/
        config_src = package_files / "config.yaml"
        config_dir = Path.home() / ".claude" / "cwms"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_dest = config_dir / "config.yaml"

        if config_dest.exists() and not force:
            click.echo(f"⚠️  {config_dest} already exists. Use --force to overwrite.")
        else:
            with resources.as_file(config_src) as src_path:
                shutil.copy(src_path, config_dest)
            click.echo(f"✅ Installed config.yaml to {config_dest}")

        # Optionally install auto-swap components
        if auto_swap:
            # Install statusline to scripts directory
            statusline_src = package_files / "statusline.py"
            scripts_dir = Path.home() / ".claude" / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            statusline_dest = scripts_dir / "statusline.py"

            if statusline_dest.exists() and not force:
                click.echo(f"⚠️  {statusline_dest} already exists. Use --force to overwrite.")
            else:
                with resources.as_file(statusline_src) as src_path:
                    shutil.copy(src_path, statusline_dest)
                    statusline_dest.chmod(0o755)  # Make executable
                click.echo(f"✅ Installed statusline to {statusline_dest}")

            # Install hooks directory
            hooks_dir = Path.home() / ".claude" / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)

            # Install auto-swap hook (Stop event)
            hook_src = package_files / "hooks" / "auto-swap.py"
            hook_dest = hooks_dir / "cwms-auto-swap.py"

            if hook_dest.exists() and not force:
                click.echo(f"⚠️  {hook_dest} already exists. Use --force to overwrite.")
            else:
                with resources.as_file(hook_src) as src_path:
                    shutil.copy(src_path, hook_dest)
                    hook_dest.chmod(0o755)  # Make executable
                click.echo(f"✅ Installed auto-swap hook to {hook_dest}")

            # Install session-start hook (SessionStart event)
            session_start_src = package_files / "hooks" / "session-start.py"
            session_start_dest = hooks_dir / "session-start.py"

            if session_start_dest.exists() and not force:
                click.echo(f"⚠️  {session_start_dest} already exists. Use --force to overwrite.")
            else:
                with resources.as_file(session_start_src) as src_path:
                    shutil.copy(src_path, session_start_dest)
                    session_start_dest.chmod(0o755)  # Make executable
                click.echo(f"✅ Installed session-start hook to {session_start_dest}")

            # Install proactive-retrieval hook (UserPromptSubmit event)
            proactive_hook_src = package_files / "hooks" / "proactive-retrieval.py"
            proactive_hook_dest = hooks_dir / "cwms-proactive-retrieval.py"

            if proactive_hook_dest.exists() and not force:
                click.echo(f"⚠️  {proactive_hook_dest} already exists. Use --force to overwrite.")
            else:
                with resources.as_file(proactive_hook_src) as src_path:
                    shutil.copy(src_path, proactive_hook_dest)
                    proactive_hook_dest.chmod(0o755)  # Make executable
                click.echo(f"✅ Installed proactive-retrieval hook to {proactive_hook_dest}")

            # Install README
            readme_src = package_files / "AUTO_SWAP_README.md"
            readme_dest = skill_dir / "AUTO_SWAP_README.md"

            with resources.as_file(readme_src) as src_path:
                shutil.copy(src_path, readme_dest)
            click.echo(f"✅ Installed documentation to {readme_dest}")

            # Provide configuration instructions
            click.echo("\n📝 Next steps to enable auto-swap:")
            click.echo("   Add to ~/.claude/settings.json:\n")
            click.echo("   {")
            click.echo('     "statusLine": {')
            click.echo('       "type": "command",')
            click.echo(f'       "command": "{statusline_dest}"')
            click.echo("     },")
            click.echo('     "hooks": {')
            click.echo('       "Stop": [{')
            click.echo('         "hooks": [{')
            click.echo('           "type": "command",')
            click.echo(f'           "command": "{hook_dest}"')
            click.echo("         }]")
            click.echo("       }],")
            click.echo('       "SessionStart": [{')
            click.echo('         "matcher": "clear",')
            click.echo('         "hooks": [{')
            click.echo('           "type": "command",')
            click.echo(f'           "command": "{session_start_dest}"')
            click.echo("         }]")
            click.echo("       }],")
            click.echo('       "UserPromptSubmit": [{')
            click.echo('         "hooks": [{')
            click.echo('           "type": "command",')
            click.echo(f'           "command": "{proactive_hook_dest}"')
            click.echo("         }]")
            click.echo("       }]")
            click.echo("     }")
            click.echo("   }")
            click.echo(f"\n   See {readme_dest} for full documentation")

        output_json(
            {
                "success": True,
                "skill_installed": True,
                "skill_directory": str(skill_dir),
                "auto_swap_installed": auto_swap,
            }
        )

    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in install_skill")
        output_error(f"Unexpected error: {e}")


@main.command("save-bridge-summary")
@click.option("--project", required=True, help="Project identifier")
@click.option(
    "--summary",
    required=True,
    help="LLM-generated summary text to save for bridge injection",
)
def save_bridge_summary(project: str, summary: str) -> None:
    """Save an LLM-generated bridge summary for the next session.

    This command is called by Claude before /clear to save a high-quality
    summary that will be injected after the context reset. The summary
    replaces the auto-generated regex-based summary with a better one.

    Example:
        cwms save-bridge-summary --project "myapp" \\
            --summary "We implemented JWT auth in src/auth.py with bcrypt..."

    Note: This is typically called automatically by Claude when instructed
    by the auto-swap hook, not manually by users.
    """
    import hashlib
    import tempfile

    try:
        # Use working directory hash (same as auto-swap hook)
        cwd = os.getcwd()
        wd_hash = hashlib.md5(cwd.encode()).hexdigest()[:12]  # nosec B324

        temp_dir = tempfile.gettempdir()
        bridge_file = Path(temp_dir) / f"cwms-bridge-{wd_hash}.txt"

        # Format as LLM-generated summary with marker
        # The session-start hook will detect this marker
        llm_summary = f"""### LLM-Generated Summary

**Project:** {project}

{summary}

---
*This summary was generated by Claude before context swap.*
"""

        bridge_file.write_text(llm_summary)

        output_json(
            {
                "success": True,
                "message": "Bridge summary saved successfully",
                "project": project,
                "summary_length": len(summary),
                "file": str(bridge_file),
            }
        )

    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in save_bridge_summary")
        output_error(f"Unexpected error: {e}")


@main.command()
@click.option("--project", required=True, help="Project identifier")
@click.option(
    "--recent",
    default=10,
    type=int,
    help="Number of recent operations to show",
)
@click.option(
    "--failures-only",
    is_flag=True,
    help="Only show failed operations",
)
def debug(project: str, recent: int, failures_only: bool) -> None:
    """Show debug information for a project.

    Displays detailed debugging information including:
    - Storage statistics and validation status
    - Performance metrics (swap time, search time, embedding time)
    - Recent operations and errors
    - Configuration summary

    Use CWMS_LOG_LEVEL=DEBUG for verbose logging.

    Example:
        cwms debug --project "my-project"
        cwms debug --project "my-project" --recent 20
        cwms debug --project "my-project" --failures-only
    """
    try:
        skill = get_skill()
        metrics = get_metrics()

        # Get status info
        status_info = skill.get_status(project)

        # Get validation info
        validation = skill.storage.validate_storage(project)

        # Get metrics summary
        metrics_summary = metrics.get_summary()

        # Get recent operations
        recent_ops = metrics.get_recent_operations(
            count=recent,
            failures_only=failures_only,
        )

        # Build comprehensive debug response
        response: dict[str, Any] = {
            "success": True,
            "project": project,
            "storage": {
                "total_chunks": status_info.total_chunks,
                "total_tokens": status_info.total_tokens,
                "oldest_chunk": status_info.oldest_chunk,
                "newest_chunk": status_info.newest_chunk,
                "storage_dir": str(status_info.storage_dir),
                "validation_status": "valid" if validation["valid"] else "invalid",
                "validation_errors": len(validation["errors"]),
                "validation_warnings": len(validation["warnings"]),
            },
            "config": {
                "embedding_provider": status_info.embedding_provider,
                "threshold_tokens": skill.config.threshold_tokens,
                "swap_trigger_percent": skill.config.swap_trigger_percent,
                "search_mode": skill.config.search_mode,
                "log_level": os.environ.get(LOG_LEVEL_ENV_VAR, "WARNING"),
            },
            "performance": {
                "uptime_seconds": round(metrics_summary.get("uptime_seconds", 0), 2),
                "total_operations": metrics_summary.get("total_operations", 0),
                "total_failures": metrics_summary.get("total_failures", 0),
                "operations": metrics_summary.get("operations", {}),
            },
            "recent_operations": recent_ops,
        }

        # Add validation details if there are issues
        if not validation["valid"]:
            response["validation_details"] = {
                "errors": validation["errors"][:5],
                "warnings": validation["warnings"][:5],
            }

        # Add helpful message
        if metrics_summary.get("total_operations", 0) == 0:
            response["message"] = (
                "No operations recorded yet. "
                "Performance metrics will appear after swap/search operations."
            )
        elif failures_only and not recent_ops:
            response["message"] = "No failed operations found."

        output_json(response)

    except FileNotFoundError:
        output_error(
            f"Project '{project}' not found.\n" "Hint: Use 'cwms swap' to create a project first."
        )
    except StorageError as e:
        output_error(f"Storage error: {e}")
    except ContextWindowManagementError as e:
        output_error(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error in debug")
        output_error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
