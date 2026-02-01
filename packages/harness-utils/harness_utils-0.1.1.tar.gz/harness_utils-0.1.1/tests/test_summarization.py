"""Tests for summarization (Tier 3 compaction)."""

from typing import Any

from harnessutils import (
    ConversationManager,
    HarnessConfig,
    MemoryStorage,
    Message,
    TextPart,
    generate_id,
)


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, response: str = "Summary"):
        """Initialize mock client."""
        self.response = response

    def invoke(
        self,
        messages: list[dict[str, Any]],
        system: list[str] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Mock LLM invocation."""
        return {
            "content": self.response,
            "usage": {
                "input": 1000,
                "output": 100,
                "cache": {"read": 0, "write": 0},
                "reasoning": 0,
            },
            "model": model or "mock-model",
        }


def test_compact_with_manager():
    """Test compaction through manager."""
    config = HarnessConfig()
    storage = MemoryStorage()
    manager = ConversationManager(storage, config)

    conv = manager.create_conversation()

    # Add messages
    for i in range(3):
        msg = Message(id=generate_id("msg"), role="user")
        msg.add_part(TextPart(text=f"Message {i}"))
        manager.add_message(conv.id, msg)

    # Compact
    llm_client = MockLLMClient("Summary")
    result = manager.compact(conv.id, llm_client, generate_id("msg"))

    assert "summarized" in result
    assert "tokens_used" in result
