"""In-memory storage implementation for testing."""

import time
from typing import Any


class MemoryStorage:
    """In-memory storage backend for testing.

    All data is stored in memory and lost when the process exits.
    """

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self.conversations: dict[str, dict[str, Any]] = {}
        self.messages: dict[str, dict[str, dict[str, Any]]] = {}
        self.parts: dict[str, dict[str, dict[str, Any]]] = {}
        self.truncated_outputs: dict[str, tuple[str, float]] = {}

    def save_conversation(self, conversation_id: str, data: dict[str, Any]) -> None:
        """Save conversation metadata."""
        self.conversations[conversation_id] = data.copy()

    def load_conversation(self, conversation_id: str) -> dict[str, Any]:
        """Load conversation metadata."""
        if conversation_id not in self.conversations:
            raise FileNotFoundError(f"Conversation {conversation_id} not found")
        return self.conversations[conversation_id].copy()

    def save_message(
        self,
        conversation_id: str,
        message_id: str,
        data: dict[str, Any]
    ) -> None:
        """Save message metadata."""
        if conversation_id not in self.messages:
            self.messages[conversation_id] = {}
        self.messages[conversation_id][message_id] = data.copy()

    def load_message(
        self,
        conversation_id: str,
        message_id: str
    ) -> dict[str, Any]:
        """Load message metadata."""
        if conversation_id not in self.messages:
            raise FileNotFoundError(
                f"Message {message_id} in conversation {conversation_id} not found"
            )
        if message_id not in self.messages[conversation_id]:
            raise FileNotFoundError(
                f"Message {message_id} in conversation {conversation_id} not found"
            )
        return self.messages[conversation_id][message_id].copy()

    def list_messages(self, conversation_id: str) -> list[str]:
        """List all message IDs for a conversation in chronological order."""
        if conversation_id not in self.messages:
            return []
        return sorted(self.messages[conversation_id].keys())

    def save_part(
        self,
        message_id: str,
        part_id: str,
        data: dict[str, Any]
    ) -> None:
        """Save message part."""
        if message_id not in self.parts:
            self.parts[message_id] = {}
        self.parts[message_id][part_id] = data.copy()

    def load_part(self, message_id: str, part_id: str) -> dict[str, Any]:
        """Load message part."""
        if message_id not in self.parts:
            raise FileNotFoundError(
                f"Part {part_id} in message {message_id} not found"
            )
        if part_id not in self.parts[message_id]:
            raise FileNotFoundError(
                f"Part {part_id} in message {message_id} not found"
            )
        return self.parts[message_id][part_id].copy()

    def list_parts(self, message_id: str) -> list[str]:
        """List all part IDs for a message in order."""
        if message_id not in self.parts:
            return []
        return sorted(self.parts[message_id].keys())

    def save_truncated_output(self, output_id: str, content: str) -> None:
        """Save full output that was truncated."""
        self.truncated_outputs[output_id] = (content, time.time())

    def load_truncated_output(self, output_id: str) -> str:
        """Load full truncated output."""
        if output_id not in self.truncated_outputs:
            raise FileNotFoundError(f"Truncated output {output_id} not found")
        return self.truncated_outputs[output_id][0]

    def cleanup_old_outputs(self, retention_days: int) -> int:
        """Clean up truncated outputs older than retention period."""
        cutoff_timestamp = time.time() - (retention_days * 24 * 60 * 60)
        to_delete = [
            output_id
            for output_id, (_, timestamp) in self.truncated_outputs.items()
            if timestamp < cutoff_timestamp
        ]

        for output_id in to_delete:
            del self.truncated_outputs[output_id]

        return len(to_delete)
