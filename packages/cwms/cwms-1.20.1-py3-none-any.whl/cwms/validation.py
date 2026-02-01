"""Validation utilities for cwms.

Provides comprehensive validation with actionable error messages for:
- Message format validation before swap
- Chunk content validation
- Storage integrity checks
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationIssue:
    """A single validation error with context and suggestions."""

    message: str
    location: str | None = None  # e.g., "line 5", "message[2]"
    field: str | None = None  # e.g., "role", "content"
    suggestion: str | None = None  # Actionable fix

    def __str__(self) -> str:
        parts = []
        if self.location:
            parts.append(f"[{self.location}]")
        parts.append(self.message)
        if self.suggestion:
            parts.append(f"\n  Suggestion: {self.suggestion}")
        return " ".join(parts)


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    valid: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def add_error(
        self,
        message: str,
        location: str | None = None,
        field_name: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add an error to the validation result."""
        self.errors.append(
            ValidationIssue(
                message=message,
                location=location,
                field=field_name,
                suggestion=suggestion,
            )
        )
        self.valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning to the validation result."""
        self.warnings.append(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "valid": self.valid,
            "errors": [str(e) for e in self.errors],
            "warnings": self.warnings,
            "stats": self.stats,
        }


def validate_message_dict(
    msg_data: dict[str, Any],
    index: int,
    strict: bool = False,
) -> ValidationResult:
    """Validate a single message dictionary.

    Args:
        msg_data: Message dictionary to validate
        index: Index of message in list (for error messages)
        strict: If True, require all fields; if False, allow optional fields

    Returns:
        ValidationResult with any errors found
    """
    result = ValidationResult(valid=True)
    location = f"message[{index}]"

    # Check required fields
    if "role" not in msg_data:
        result.add_error(
            message="Missing 'role' field",
            location=location,
            field_name="role",
            suggestion="Add 'role' field with value 'user' or 'assistant'",
        )
    elif msg_data["role"] not in ("user", "assistant", "system"):
        result.add_error(
            message=f"Invalid role '{msg_data['role']}'",
            location=location,
            field_name="role",
            suggestion="Use 'user', 'assistant', or 'system' for role",
        )

    if "content" not in msg_data:
        result.add_error(
            message="Missing 'content' field",
            location=location,
            field_name="content",
            suggestion="Add 'content' field with message text",
        )
    else:
        content = msg_data["content"]
        # Content can be string or list (Claude API format)
        if not isinstance(content, (str, list)):
            result.add_error(
                message=f"Invalid content type '{type(content).__name__}'",
                location=location,
                field_name="content",
                suggestion="Content must be a string or list of content blocks",
            )
        elif isinstance(content, str) and not content.strip():
            result.add_warning(f"{location}: Empty content string")
        elif isinstance(content, list):
            # Validate content blocks
            text_found = False
            for i, block in enumerate(content):
                if isinstance(block, str):
                    if block.strip():
                        text_found = True
                elif isinstance(block, dict):
                    block_type = block.get("type")
                    if block_type == "text":
                        if block.get("text", "").strip():
                            text_found = True
                    elif block_type == "tool_use":
                        pass  # Tool use blocks are valid
                    elif block_type == "tool_result":
                        pass  # Tool result blocks are valid
                    elif block_type is None:
                        result.add_error(
                            message=f"Content block {i} missing 'type' field",
                            location=location,
                            suggestion="Add 'type' field (text, tool_use, or tool_result)",
                        )
                else:
                    result.add_error(
                        message=f"Invalid content block type at index {i}",
                        location=location,
                        suggestion="Content blocks must be strings or dicts with 'type' field",
                    )

            if not text_found and not any(
                isinstance(b, dict) and b.get("type") in ("tool_use", "tool_result")
                for b in content
            ):
                result.add_warning(f"{location}: No text content found in content list")

    # Check for unexpected fields in strict mode
    if strict:
        expected_fields = {"role", "content", "tool_calls", "tool_results", "metadata"}
        unexpected = set(msg_data.keys()) - expected_fields
        if unexpected:
            result.add_warning(
                f"{location}: Unexpected fields will be ignored: {sorted(unexpected)}"
            )

    return result


def validate_messages(
    messages: Any,
    strict: bool = False,
) -> ValidationResult:
    """Validate a list of messages.

    Args:
        messages: Data that should be a list of message dictionaries
        strict: If True, require all fields; if False, allow optional fields

    Returns:
        ValidationResult with any errors/warnings found
    """
    result = ValidationResult(valid=True)

    # Type check first - messages should be a list
    if not isinstance(messages, list):
        result.add_error(
            message=f"Expected list of messages, got {type(messages).__name__}",
            suggestion="Messages must be a JSON array/list",
        )
        return result

    if not messages:
        # Empty messages list is valid but generates a warning
        result.add_warning("Empty messages list - nothing to swap")
        result.stats = {
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "total_content_length": 0,
            "empty_messages": 0,
        }
        return result

    # Stats collection
    user_count = 0
    assistant_count = 0
    total_content_length = 0
    empty_messages = 0

    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            result.add_error(
                message=f"Expected message object, got {type(msg).__name__}",
                location=f"message[{i}]",
                suggestion="Each message must be a JSON object with 'role' and 'content'",
            )
            continue

        msg_result = validate_message_dict(msg, i, strict)

        # Merge errors and warnings
        result.errors.extend(msg_result.errors)
        result.warnings.extend(msg_result.warnings)
        if not msg_result.valid:
            result.valid = False

        # Collect stats
        role = msg.get("role", "")
        if role == "user":
            user_count += 1
        elif role == "assistant":
            assistant_count += 1

        content = msg.get("content", "")
        if isinstance(content, str):
            total_content_length += len(content)
            if not content.strip():
                empty_messages += 1
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, str):
                    total_content_length += len(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    total_content_length += len(block.get("text", ""))

    # Add stats
    result.stats = {
        "total_messages": len(messages),
        "user_messages": user_count,
        "assistant_messages": assistant_count,
        "total_content_length": total_content_length,
        "empty_messages": empty_messages,
    }

    # Add summary warnings
    if user_count == 0 and assistant_count > 0:
        result.add_warning("No user messages found - conversation may be incomplete")
    if assistant_count == 0 and user_count > 0:
        result.add_warning("No assistant messages found - conversation may be incomplete")
    if empty_messages > len(messages) * 0.5:
        result.add_warning(f"{empty_messages}/{len(messages)} messages have empty content")

    return result


def validate_file_format(
    file_path: Path,
    verbose: bool = False,
    strict: bool = False,
) -> ValidationResult:
    """Validate a messages file format and content.

    This performs a comprehensive validation of the file:
    1. Check file exists and is readable
    2. Detect and validate format (JSON, JSONL, Claude session)
    3. Parse and validate all messages
    4. Report summary statistics

    Args:
        file_path: Path to the messages file
        verbose: If True, include detailed stats (currently unused, reserved for future)
        strict: If True, use strict validation (warn about unexpected fields)

    Returns:
        ValidationResult with any errors/warnings found
    """
    _ = verbose  # Reserved for future use
    import json

    result = ValidationResult(valid=True)

    # Check file exists
    if not file_path.exists():
        result.add_error(
            message=f"File not found: {file_path}",
            suggestion="Check the file path is correct",
        )
        return result

    # Check file is readable
    try:
        with open(file_path, encoding="utf-8") as f:
            first_line = f.readline()
    except PermissionError:
        result.add_error(
            message=f"Permission denied: {file_path}",
            suggestion="Check file permissions",
        )
        return result
    except OSError as e:
        result.add_error(
            message=f"Could not read file: {e}",
            suggestion="Ensure the file is accessible",
        )
        return result

    if not first_line.strip():
        result.add_error(
            message="File is empty",
            suggestion="Provide a file with messages to validate",
        )
        return result

    # Try to detect format
    try:
        first_obj = json.loads(first_line.strip())
    except json.JSONDecodeError as e:
        result.add_error(
            message=f"Invalid JSON on first line: {e}",
            location="line 1",
            suggestion="Ensure the file contains valid JSON or JSONL format",
        )
        return result

    # Determine format and parse all messages
    messages: list[dict[str, Any]] = []
    detected_format = "unknown"

    try:
        if isinstance(first_obj, dict) and "messages" in first_obj:
            # JSON format: {"messages": [...]}
            detected_format = "json"
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data.get("messages"), list):
                messages = data["messages"]
            else:
                result.add_error(
                    message="'messages' field is not a list",
                    suggestion="Ensure 'messages' contains an array of message objects",
                )
                return result

        elif isinstance(first_obj, dict) and "type" in first_obj:
            # Claude session format
            detected_format = "claude-session"
            with open(file_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("type") in ("user", "assistant"):
                            msg_data = entry.get("message")
                            if isinstance(msg_data, dict):
                                messages.append(msg_data)
                            elif isinstance(msg_data, str):
                                messages.append({"role": entry["type"], "content": msg_data})
                    except json.JSONDecodeError as e:
                        result.add_warning(f"Skipped invalid JSON on line {line_num}: {e}")

        elif isinstance(first_obj, dict) and "role" in first_obj:
            # JSONL format
            detected_format = "jsonl"
            with open(file_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        result.add_error(
                            message=f"Invalid JSON: {e}",
                            location=f"line {line_num}",
                            suggestion="Each line must be valid JSON",
                        )

        else:
            result.add_error(
                message="Could not determine file format",
                suggestion=(
                    "Expected formats:\n"
                    '  - JSON: {"messages": [...]}\n'
                    '  - JSONL: {"role": "user", "content": "..."} per line\n'
                    '  - Claude session: {"type": "user", "message": {...}}'
                ),
            )
            return result

    except json.JSONDecodeError as e:
        result.add_error(
            message=f"Failed to parse file: {e}",
            suggestion="Ensure the file contains valid JSON",
        )
        return result

    # Validate parsed messages
    msg_result = validate_messages(messages, strict=strict)
    result.errors.extend(msg_result.errors)
    result.warnings.extend(msg_result.warnings)
    result.valid = result.valid and msg_result.valid
    result.stats = {
        "format": detected_format,
        "file_path": str(file_path),
        **msg_result.stats,
    }

    return result


class ValidationError(Exception):
    """Exception raised when validation fails."""

    def __init__(self, result: ValidationResult):
        self.result = result
        error_msgs = [str(e) for e in result.errors[:5]]  # Show first 5 errors
        if len(result.errors) > 5:
            error_msgs.append(f"... and {len(result.errors) - 5} more errors")
        super().__init__("\n".join(error_msgs))


def require_valid_messages(
    messages: list[dict[str, Any]],
    strict: bool = False,
) -> None:
    """Validate messages and raise if invalid.

    Args:
        messages: List of message dictionaries to validate
        strict: If True, use strict validation

    Raises:
        ValidationError: If messages are invalid
    """
    result = validate_messages(messages, strict=strict)
    if not result.valid:
        raise ValidationError(result)
