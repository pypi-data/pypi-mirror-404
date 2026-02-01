"""Protocol definitions for harness-utils.

This module defines the interfaces that applications must implement
to integrate with harness-utils.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM client implementations.

    Applications must provide an implementation of this protocol to enable
    LLM-powered summarization (Tier 3 compaction).

    This is a callback-based design where the application owns the LLM client
    and the library requests LLM operations through this interface.
    """

    def invoke(
        self,
        messages: list[dict[str, Any]],
        system: list[str] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Invoke the LLM with the given messages.

        Args:
            messages: List of messages in model format (role, content)
            system: Optional system prompt parts
            model: Optional model identifier to use

        Returns:
            Dictionary containing:
                - content: The LLM response text
                - usage: Token usage information (input, output, cache, reasoning)
                - model: The model that was used
        """
        ...


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol for storage backend implementations.

    The library provides default implementations (filesystem, in-memory),
    but applications can provide custom implementations for different
    storage strategies (e.g., cloud storage, databases).
    """

    def save_conversation(self, conversation_id: str, data: dict[str, Any]) -> None:
        """Save conversation metadata.

        Args:
            conversation_id: Unique conversation identifier
            data: Conversation data to save
        """
        ...

    def load_conversation(self, conversation_id: str) -> dict[str, Any]:
        """Load conversation metadata.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Conversation data

        Raises:
            FileNotFoundError: If conversation doesn't exist
        """
        ...

    def save_message(self, conversation_id: str, message_id: str, data: dict[str, Any]) -> None:
        """Save message metadata.

        Args:
            conversation_id: Conversation the message belongs to
            message_id: Unique message identifier
            data: Message data to save
        """
        ...

    def load_message(self, conversation_id: str, message_id: str) -> dict[str, Any]:
        """Load message metadata.

        Args:
            conversation_id: Conversation the message belongs to
            message_id: Unique message identifier

        Returns:
            Message data

        Raises:
            FileNotFoundError: If message doesn't exist
        """
        ...

    def list_messages(self, conversation_id: str) -> list[str]:
        """List all message IDs for a conversation.

        Args:
            conversation_id: Conversation to list messages for

        Returns:
            List of message IDs in chronological order
        """
        ...

    def save_part(self, message_id: str, part_id: str, data: dict[str, Any]) -> None:
        """Save message part.

        Args:
            message_id: Message the part belongs to
            part_id: Unique part identifier
            data: Part data to save
        """
        ...

    def load_part(self, message_id: str, part_id: str) -> dict[str, Any]:
        """Load message part.

        Args:
            message_id: Message the part belongs to
            part_id: Unique part identifier

        Returns:
            Part data

        Raises:
            FileNotFoundError: If part doesn't exist
        """
        ...

    def list_parts(self, message_id: str) -> list[str]:
        """List all part IDs for a message.

        Args:
            message_id: Message to list parts for

        Returns:
            List of part IDs in order
        """
        ...

    def save_truncated_output(self, output_id: str, content: str) -> None:
        """Save full output that was truncated.

        Args:
            output_id: Unique output identifier
            content: Full output content
        """
        ...

    def load_truncated_output(self, output_id: str) -> str:
        """Load full truncated output.

        Args:
            output_id: Unique output identifier

        Returns:
            Full output content

        Raises:
            FileNotFoundError: If output doesn't exist
        """
        ...

    def cleanup_old_outputs(self, retention_days: int) -> int:
        """Clean up truncated outputs older than retention period.

        Args:
            retention_days: Number of days to retain outputs

        Returns:
            Number of outputs deleted
        """
        ...
