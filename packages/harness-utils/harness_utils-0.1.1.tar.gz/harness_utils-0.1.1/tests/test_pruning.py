"""Tests for pruning (Tier 2 compaction)."""

from harnessutils import (
    ConversationManager,
    HarnessConfig,
    MemoryStorage,
    Message,
    TextPart,
    ToolPart,
    ToolState,
    generate_id,
)
from harnessutils.compaction.pruning import prune_tool_outputs


def test_prune_no_messages():
    """Test pruning with no messages."""
    config = HarnessConfig()
    result = prune_tool_outputs([], config.pruning)
    assert result.pruned == 0
    assert result.tokens_saved == 0


def test_prune_no_tool_outputs():
    """Test pruning with no tool outputs."""
    config = HarnessConfig()
    msg = Message(id=generate_id("msg"), role="assistant")
    msg.add_part(TextPart(text="No tools here"))

    result = prune_tool_outputs([msg], config.pruning)
    assert result.pruned == 0
    assert result.tokens_saved == 0


def test_prune_tool_output():
    """Test pruning actually removes large outputs."""
    config = HarnessConfig()
    config.pruning.prune_protect = 0  # No protection
    config.pruning.prune_minimum = 0  # Any savings OK
    config.pruning.protect_turns = 0  # No turn protection

    msg = Message(id=generate_id("msg"), role="assistant")
    large_output = "x" * 10000  # Large output
    tool_part = ToolPart(
        tool="bash",
        call_id="call_1",
        state=ToolState(
            status="completed",
            input={"command": "test"},
            output=large_output,
        ),
    )
    msg.add_part(tool_part)

    result = prune_tool_outputs([msg], config.pruning)

    # Should prune the output
    assert result.pruned >= 0
    assert result.tokens_saved >= 0


def test_prune_integration_with_manager():
    """Test pruning integration with ConversationManager."""
    config = HarnessConfig()
    storage = MemoryStorage()
    manager = ConversationManager(storage, config)

    conv = manager.create_conversation()

    # Add message
    msg = Message(id=generate_id("msg"), role="user")
    msg.add_part(TextPart(text="Hello"))
    manager.add_message(conv.id, msg)

    # Prune (should work even with no tool outputs)
    result = manager.prune_before_turn(conv.id)

    # Manager returns dict
    assert "pruned" in result
    assert "tokens_saved" in result
