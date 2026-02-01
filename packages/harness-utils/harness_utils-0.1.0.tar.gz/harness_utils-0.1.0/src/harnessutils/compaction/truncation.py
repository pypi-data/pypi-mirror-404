"""Tier 1: Output truncation at tool execution boundary.

Prevents large outputs from entering context by truncating at source.
Cost: Free, Latency: 0ms.
"""

from dataclasses import dataclass
from typing import Literal

from harnessutils.config import TruncationConfig


@dataclass
class TruncationResult:
    """Result of truncation operation."""

    content: str
    truncated: bool
    output_path: str | None = None
    bytes_removed: int = 0


def truncate_output(
    output: str,
    config: TruncationConfig,
    output_id: str | None = None,
) -> TruncationResult:
    """Truncate tool output if it exceeds limits.

    Args:
        output: The tool output to potentially truncate
        config: Truncation configuration
        output_id: ID for saving full output (if None, full output not saved)

    Returns:
        TruncationResult with content and metadata
    """
    lines = output.split("\n")
    total_bytes = len(output.encode("utf-8"))

    if len(lines) <= config.max_lines and total_bytes <= config.max_bytes:
        return TruncationResult(
            content=output,
            truncated=False,
        )

    preview_lines: list[str] = []
    bytes_accumulated = 0

    if config.direction == "head":
        for i, line in enumerate(lines):
            if i >= config.max_lines:
                break
            line_bytes = len(line.encode("utf-8")) + 1  # +1 for newline
            if bytes_accumulated + line_bytes > config.max_bytes:
                break
            preview_lines.append(line)
            bytes_accumulated += line_bytes
    else:  # tail
        for i in range(len(lines) - 1, -1, -1):
            if len(preview_lines) >= config.max_lines:
                break
            line = lines[i]
            line_bytes = len(line.encode("utf-8")) + 1  # +1 for newline
            if bytes_accumulated + line_bytes > config.max_bytes:
                break
            preview_lines.insert(0, line)
            bytes_accumulated += line_bytes

    preview = "\n".join(preview_lines)
    bytes_removed = total_bytes - bytes_accumulated

    message = _format_truncated_message(
        preview,
        bytes_removed,
        output_id,
        config.direction,
    )

    return TruncationResult(
        content=message,
        truncated=True,
        output_path=output_id,
        bytes_removed=bytes_removed,
    )


def _format_truncated_message(
    preview: str,
    bytes_removed: int,
    output_path: str | None,
    direction: Literal["head", "tail"],
) -> str:
    """Format the truncated output message.

    Args:
        preview: Preview content (head or tail)
        bytes_removed: Number of bytes that were removed
        output_path: Path where full output was saved
        direction: Direction of truncation

    Returns:
        Formatted message string
    """
    parts = [preview]

    if bytes_removed > 0:
        parts.append("")
        parts.append(f"...{bytes_removed} bytes truncated...")
        parts.append("")

        if output_path:
            parts.append(f"Full output saved to: {output_path}")
            parts.append("Use search tools to query the full content or read specific sections.")
            parts.append("Delegate large file processing to specialized exploration agents.")

    return "\n".join(parts)
