"""Convert internal messages to model format.

Transforms internal message format (granular, storage-optimized)
to model format (LLM-compatible).
"""

from typing import Any

from harnessutils.models.message import Message
from harnessutils.models.parts import ToolPart


def to_model_messages(messages: list[Message]) -> list[dict[str, Any]]:
    """Convert internal messages to model format.

    Handles:
    - Compacted tool outputs (replace with marker)
    - Interrupted tool calls (inject error)
    - Two-part system prompts
    - Stop at summary message

    Args:
        messages: Internal message objects

    Returns:
        List of messages in model format
    """
    model_messages: list[dict[str, Any]] = []
    summary_found = False
    summary_parent_id: str | None = None

    for msg in reversed(messages):
        if summary_found and msg.role == "user" and msg.id == summary_parent_id:
            break

        if msg.role == "assistant" and msg.summary:
            summary_found = True
            summary_parent_id = msg.parent_id

        if len(msg.parts) == 0:
            continue

        if msg.role == "user":
            model_msg = _convert_user_message(msg)
            if model_msg and model_msg.get("content"):
                model_messages.insert(0, model_msg)

        elif msg.role == "assistant":
            model_msg = _convert_assistant_message(msg)
            if model_msg and model_msg.get("content"):
                model_messages.insert(0, model_msg)

    return model_messages


def _convert_user_message(msg: Message) -> dict[str, Any] | None:
    """Convert user message to model format.

    Args:
        msg: User message

    Returns:
        Model format message or None if empty
    """
    content_parts: list[str] = []

    for part in msg.parts:
        if part.type == "text" and not getattr(part, "ignored", False):
            content_parts.append(getattr(part, "text", ""))
        elif part.type == "compaction":
            content_parts.append("What did we do so far?")

    if not content_parts:
        return None

    return {
        "role": "user",
        "content": "\n".join(content_parts),
    }


def _convert_assistant_message(msg: Message) -> dict[str, Any] | None:
    """Convert assistant message to model format.

    Args:
        msg: Assistant message

    Returns:
        Model format message or None if empty
    """
    if msg.error and not msg.has_partial_output():
        return None

    content_parts: list[str] = []

    for part in msg.parts:
        if part.type == "text":
            content_parts.append(getattr(part, "text", ""))

        elif part.type == "reasoning":
            content_parts.append(f"[Extended thinking: {len(getattr(part, 'text', ''))} chars]")

        elif part.type == "tool":
            tool_part = part
            assert isinstance(tool_part, ToolPart)

            if tool_part.state.status == "completed":
                if tool_part.state.time and tool_part.state.time.compacted:
                    output = "[Old tool result content cleared]"
                else:
                    output = tool_part.state.output

                content_parts.append(f"[Tool: {tool_part.tool}] {tool_part.state.title}\n{output}")

            elif tool_part.state.status == "error":
                content_parts.append(f"[Tool Error: {tool_part.tool}] {tool_part.state.error}")

            elif tool_part.state.status in ["pending", "running"]:
                content_parts.append(f"[Tool execution was interrupted: {tool_part.tool}]")

    if not content_parts:
        return None

    return {
        "role": "assistant",
        "content": "\n\n".join(content_parts),
    }
