"""Hook definitions for turn processing.

Hooks allow apps to inject custom behavior at key points
in the turn processing flow.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TurnHooks:
    """Callbacks for turn processing events.

    Apps can provide these callbacks to customize behavior during
    turn processing (e.g., LLM calls, tool execution, summarization).
    """

    on_llm_request: Callable[[dict[str, Any]], None] | None = None
    """Called before making LLM request with messages."""

    on_llm_response: Callable[[dict[str, Any]], None] | None = None
    """Called when LLM response is received."""

    on_tool_call: Callable[[str, str, dict[str, Any]], Any] | None = None
    """Called when tool should be executed.

    Args:
        tool_name: Name of the tool to execute
        call_id: Unique call identifier
        input_data: Tool input parameters

    Returns:
        Tool execution result (output string or dict)
    """

    on_tool_result: Callable[[str, Any], None] | None = None
    """Called when tool execution completes.

    Args:
        call_id: Tool call identifier
        result: Tool execution result
    """

    on_tool_error: Callable[[str, Exception], None] | None = None
    """Called when tool execution fails.

    Args:
        call_id: Tool call identifier
        error: Exception that occurred
    """

    on_summarization_request: Callable[[list[dict[str, Any]]], dict[str, Any]] | None = None
    """Called when summarization is needed.

    Args:
        messages: Messages to summarize

    Returns:
        Summarization result with content and usage
    """

    on_doom_loop: Callable[[str, dict[str, Any], int], bool] | None = None
    """Called when doom loop is detected.

    Args:
        tool_name: Tool being called repeatedly
        input_data: Tool input
        count: Number of identical calls

    Returns:
        True to continue, False to stop
    """

    on_snapshot: Callable[[str], str] | None = None
    """Called to capture state snapshot.

    Args:
        event: Snapshot event type (start/finish)

    Returns:
        Snapshot identifier
    """

    metadata: dict[str, Any] = field(default_factory=dict)
    """Custom metadata for hooks."""
