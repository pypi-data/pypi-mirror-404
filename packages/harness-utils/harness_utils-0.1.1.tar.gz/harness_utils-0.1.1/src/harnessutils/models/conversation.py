"""Conversation model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Conversation:
    """A conversation containing multiple messages.

    Conversations track the overall context and metadata for a series
    of messages between user and assistant.
    """

    id: str
    project_id: str | None = None
    created: int | None = None  # Unix timestamp in milliseconds
    updated: int | None = None  # Unix timestamp in milliseconds
    pending_summarization: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert conversation to dictionary for storage.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "created": self.created,
            "updated": self.updated,
            "pending_summarization": self.pending_summarization,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Conversation":
        """Create conversation from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Conversation instance
        """
        return cls(
            id=data["id"],
            project_id=data.get("project_id"),
            created=data.get("created"),
            updated=data.get("updated"),
            pending_summarization=data.get("pending_summarization", False),
            metadata=data.get("metadata", {}),
        )
