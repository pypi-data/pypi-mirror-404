"""Tier 3: LLM-powered conversation summarization.

Uses LLM to semantically compress conversation when approaching limit.
Cost: Expensive (~$0.10-0.50), Latency: ~3-5s.
"""

from dataclasses import dataclass
from typing import Any

from harnessutils.models.message import Message
from harnessutils.models.usage import CacheUsage, Usage
from harnessutils.types import LLMClient


SUMMARIZATION_PROMPT = """You are a helpful AI assistant tasked with summarizing conversations.

When asked to summarize, provide a detailed but concise summary of the conversation.
Focus on information that would be helpful for continuing the conversation, including:
- What was done
- What is currently being worked on
- Which files are being modified
- What needs to be done next
- Key user requests, constraints, or preferences that should persist
- Important technical decisions and why they were made

Your summary should be comprehensive enough to provide context but concise enough
to be quickly understood."""


@dataclass
class SummarizationResult:
    """Result of summarization operation."""

    summary_message: Message
    tokens_used: Usage
    cost: float


def is_overflow(usage: Usage, context_limit: int, output_limit: int) -> bool:
    """Check if conversation has overflowed context window.

    Args:
        usage: Token usage from last turn
        context_limit: Maximum context tokens for model
        output_limit: Maximum output tokens for model

    Returns:
        True if overflow detected
    """
    total_input = usage.input + usage.cache.read
    total_output = usage.output + usage.reasoning

    total = total_input + total_output
    usable_input = context_limit - output_limit

    return total > usable_input


def summarize_conversation(
    messages: list[Message],
    llm_client: LLMClient,
    parent_message_id: str,
    message_id: str,
    model: str | None = None,
    auto_mode: bool = False,
) -> SummarizationResult:
    """Summarize conversation using LLM.

    Args:
        messages: Conversation messages to summarize
        llm_client: LLM client implementation (callback from app)
        parent_message_id: ID of message that triggered summarization
        message_id: ID for the summary message
        model: Optional model to use (cheaper/faster recommended)
        auto_mode: Whether this was auto-triggered

    Returns:
        SummarizationResult with summary message and metrics
    """
    model_messages = _convert_to_model_format(messages)

    model_messages.append({
        "role": "user",
        "content": "Provide a detailed summary for continuing our conversation."
    })

    response = llm_client.invoke(
        messages=model_messages,
        system=[SUMMARIZATION_PROMPT],
        model=model,
    )

    usage_data = response.get("usage", {})
    cache_data = usage_data.get("cache", {})

    usage = Usage(
        input=usage_data.get("input", 0),
        output=usage_data.get("output", 0),
        reasoning=usage_data.get("reasoning", 0),
        cache=CacheUsage(
            read=cache_data.get("read", 0),
            write=cache_data.get("write", 0),
        ),
    )

    cost = response.get("cost", 0.0)

    from harnessutils.models.parts import TextPart

    summary_message = Message(
        id=message_id,
        role="assistant",
        parent_id=parent_message_id,
        summary=True,
        agent="summarization",
        model={"model": response.get("model", model or "unknown")},
        tokens=usage,
        cost=cost,
    )

    summary_message.add_part(TextPart(text=response.get("content", "")))

    return SummarizationResult(
        summary_message=summary_message,
        tokens_used=usage,
        cost=cost,
    )


def _convert_to_model_format(messages: list[Message]) -> list[dict[str, Any]]:
    """Convert internal messages to model format for summarization.

    Args:
        messages: Internal message objects

    Returns:
        List of messages in model format
    """
    model_messages: list[dict[str, Any]] = []

    for msg in messages:
        if len(msg.parts) == 0:
            continue

        if msg.role == "user":
            content_parts = []
            for part in msg.parts:
                if part.type == "text" and not getattr(part, "ignored", False):
                    content_parts.append(part.text)

            if content_parts:
                model_messages.append({
                    "role": "user",
                    "content": "\n".join(content_parts),
                })

        elif msg.role == "assistant":
            if msg.error and not msg.has_partial_output():
                continue

            content_parts = []
            for part in msg.parts:
                if part.type == "text":
                    content_parts.append(part.text)
                elif part.type == "reasoning":
                    content_parts.append(f"[Thinking: {part.text}]")

            if content_parts:
                model_messages.append({
                    "role": "assistant",
                    "content": "\n".join(content_parts),
                })

    return model_messages
