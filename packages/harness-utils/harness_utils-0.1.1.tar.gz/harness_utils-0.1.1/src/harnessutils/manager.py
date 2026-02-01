"""Main ConversationManager API for harness-utils."""

import time
from typing import Any

from harnessutils.compaction.pruning import prune_tool_outputs
from harnessutils.compaction.summarization import is_overflow, summarize_conversation
from harnessutils.compaction.truncation import truncate_output
from harnessutils.config import HarnessConfig
from harnessutils.conversion.to_model import to_model_messages
from harnessutils.models.conversation import Conversation
from harnessutils.models.message import Message
from harnessutils.models.usage import Usage
from harnessutils.storage.memory import MemoryStorage
from harnessutils.types import LLMClient, StorageBackend
from harnessutils.utils.ids import generate_id


class ConversationManager:
    """Main interface for managing conversations with context window management.

    Provides high-level API for:
    - Creating and managing conversations
    - Adding messages
    - Automatic context compaction (truncation, pruning, summarization)
    - Message storage and retrieval
    """

    def __init__(
        self,
        storage: StorageBackend | None = None,
        config: HarnessConfig | None = None,
    ):
        """Initialize conversation manager.

        Args:
            storage: Storage backend (uses in-memory if None)
            config: Configuration (uses defaults if None)
        """
        self.config = config or HarnessConfig()
        self.storage = storage or MemoryStorage()
        self._message_cache: dict[str, list[Message]] = {}

    def create_conversation(
        self,
        conversation_id: str | None = None,
        project_id: str | None = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            conversation_id: Optional conversation ID (generated if None)
            project_id: Optional project ID for grouping

        Returns:
            New conversation object
        """
        if conversation_id is None:
            conversation_id = generate_id("conv")

        now = int(time.time() * 1000)
        conversation = Conversation(
            id=conversation_id,
            project_id=project_id,
            created=now,
            updated=now,
        )

        self.storage.save_conversation(conversation_id, conversation.to_dict())
        self._message_cache[conversation_id] = []

        return conversation

    def add_message(self, conversation_id: str, message: Message) -> None:
        """Add a message to a conversation.

        Args:
            conversation_id: Conversation to add message to
            message: Message to add
        """
        self.storage.save_message(conversation_id, message.id, message.to_dict())

        if conversation_id not in self._message_cache:
            self._message_cache[conversation_id] = []
        self._message_cache[conversation_id].append(message)

        conv = self.storage.load_conversation(conversation_id)
        conv["updated"] = int(time.time() * 1000)
        self.storage.save_conversation(conversation_id, conv)

    def get_messages(self, conversation_id: str) -> list[Message]:
        """Get all messages for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages in chronological order
        """
        if conversation_id in self._message_cache:
            return self._message_cache[conversation_id]

        message_ids = self.storage.list_messages(conversation_id)
        messages = [
            Message.from_dict(self.storage.load_message(conversation_id, msg_id))
            for msg_id in message_ids
        ]

        self._message_cache[conversation_id] = messages
        return messages

    def prune_before_turn(
        self,
        conversation_id: str,
    ) -> dict[str, Any]:
        """Proactively prune old tool outputs before processing a turn.

        This is Tier 2 compaction - removes old tool outputs while
        preserving conversation structure.

        Args:
            conversation_id: Conversation to prune

        Returns:
            Pruning result with count and tokens saved
        """
        if not self.config.compaction.prune:
            return {"pruned": 0, "tokens_saved": 0}

        messages = self.get_messages(conversation_id)
        result = prune_tool_outputs(
            messages,
            self.config.pruning,
            self.config.tokens.chars_per_token,
        )

        for msg in messages:
            self.storage.save_message(conversation_id, msg.id, msg.to_dict())

        return {"pruned": result.pruned, "tokens_saved": result.tokens_saved}

    def needs_compaction(
        self,
        conversation_id: str,
        usage: Usage,
    ) -> bool:
        """Check if conversation needs summarization (Tier 3).

        Args:
            conversation_id: Conversation to check
            usage: Token usage from last turn

        Returns:
            True if summarization needed
        """
        return is_overflow(
            usage,
            self.config.model_limits.default_context_limit,
            self.config.model_limits.default_output_limit,
        )

    def compact(
        self,
        conversation_id: str,
        llm_client: LLMClient,
        parent_message_id: str,
        model: str | None = None,
        auto_mode: bool = False,
    ) -> dict[str, Any]:
        """Compact conversation using LLM summarization (Tier 3).

        Args:
            conversation_id: Conversation to compact
            llm_client: LLM client for summarization
            parent_message_id: Message that triggered compaction
            model: Optional model to use for summarization
            auto_mode: Whether this was auto-triggered

        Returns:
            Compaction result with summary message and metrics
        """
        if not self.config.compaction.auto and not auto_mode:
            return {"summarized": False}

        messages = self.get_messages(conversation_id)
        summary_id = generate_id("msg")

        result = summarize_conversation(
            messages=messages,
            llm_client=llm_client,
            parent_message_id=parent_message_id,
            message_id=summary_id,
            model=model,
            auto_mode=auto_mode,
        )

        self.add_message(conversation_id, result.summary_message)

        return {
            "summarized": True,
            "summary_message_id": summary_id,
            "tokens_used": result.tokens_used.total,
            "cost": result.cost,
        }

    def to_model_format(self, conversation_id: str) -> list[dict[str, Any]]:
        """Convert conversation messages to model format for LLM requests.

        Args:
            conversation_id: Conversation to convert

        Returns:
            List of messages in model format
        """
        messages = self.get_messages(conversation_id)
        return to_model_messages(messages)

    def truncate_tool_output(
        self,
        output: str,
        tool_name: str,
    ) -> str:
        """Truncate tool output if it exceeds limits (Tier 1).

        Args:
            output: Tool output to truncate
            tool_name: Name of the tool

        Returns:
            Potentially truncated output
        """
        output_id = generate_id(f"output_{tool_name}")

        result = truncate_output(
            output=output,
            config=self.config.truncation,
            output_id=output_id,
        )

        if result.truncated and result.output_path:
            self.storage.save_truncated_output(result.output_path, output)

        return result.content
