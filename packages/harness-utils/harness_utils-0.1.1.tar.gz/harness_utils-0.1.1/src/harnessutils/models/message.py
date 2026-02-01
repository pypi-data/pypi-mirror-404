"""Message model with part-based decomposition."""

from dataclasses import dataclass, field
from typing import Any, Literal

from harnessutils.models.parts import Part
from harnessutils.models.usage import Usage


@dataclass
class Message:
    """A message in the conversation.

    Messages are decomposed into parts for granular compaction.
    Each message can contain multiple parts (text, tool calls, reasoning, etc.).
    """

    id: str
    role: Literal["user", "assistant"]
    parts: list[Part] = field(default_factory=list)
    parent_id: str | None = None
    summary: bool = False  # Is this a summary message?
    agent: str | None = None
    model: dict[str, str] | None = None
    tokens: Usage | None = None
    cost: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_part(self, part: Part) -> None:
        """Add a part to this message.

        Args:
            part: The part to add
        """
        self.parts.append(part)

    def has_partial_output(self) -> bool:
        """Check if message has any partial output despite errors.

        Returns:
            True if there are text parts even with errors
        """
        return any(p.type == "text" for p in self.parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for storage.

        Returns:
            Dictionary representation
        """
        data: dict[str, Any] = {
            "id": self.id,
            "role": self.role,
            "parent_id": self.parent_id,
            "summary": self.summary,
            "agent": self.agent,
            "model": self.model,
            "cost": self.cost,
            "error": self.error,
            "metadata": self.metadata,
        }

        if self.tokens:
            data["tokens"] = {
                "input": self.tokens.input,
                "output": self.tokens.output,
                "reasoning": self.tokens.reasoning,
                "cache": {
                    "read": self.tokens.cache.read,
                    "write": self.tokens.cache.write,
                },
            }

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create message from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Message instance
        """
        tokens = None
        if "tokens" in data and data["tokens"]:
            from harnessutils.models.usage import CacheUsage, Usage

            cache_data = data["tokens"].get("cache", {})
            tokens = Usage(
                input=data["tokens"].get("input", 0),
                output=data["tokens"].get("output", 0),
                reasoning=data["tokens"].get("reasoning", 0),
                cache=CacheUsage(
                    read=cache_data.get("read", 0),
                    write=cache_data.get("write", 0),
                ),
            )

        return cls(
            id=data["id"],
            role=data["role"],
            parent_id=data.get("parent_id"),
            summary=data.get("summary", False),
            agent=data.get("agent"),
            model=data.get("model"),
            tokens=tokens,
            cost=data.get("cost", 0.0),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )
