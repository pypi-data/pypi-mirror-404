"""Tests for ConversationManager."""

from harnessutils import (
    ConversationManager,
    Message,
    TextPart,
    generate_id,
)


def test_create_conversation() -> None:
    """Test conversation creation."""
    manager = ConversationManager()

    conv = manager.create_conversation(project_id="test")

    assert conv.id.startswith("conv_")
    assert conv.project_id == "test"
    assert conv.created is not None


def test_add_and_get_messages() -> None:
    """Test adding and retrieving messages."""
    manager = ConversationManager()
    conv = manager.create_conversation()

    msg = Message(id=generate_id("msg"), role="user")
    msg.add_part(TextPart(text="Hello"))

    manager.add_message(conv.id, msg)

    messages = manager.get_messages(conv.id)
    assert len(messages) == 1
    assert messages[0].id == msg.id
    assert len(messages[0].parts) == 1


def test_to_model_format() -> None:
    """Test converting messages to model format."""
    manager = ConversationManager()
    conv = manager.create_conversation()

    user_msg = Message(id=generate_id("msg"), role="user")
    user_msg.add_part(TextPart(text="Hello"))
    manager.add_message(conv.id, user_msg)

    assistant_msg = Message(id=generate_id("msg"), role="assistant")
    assistant_msg.add_part(TextPart(text="Hi there!"))
    manager.add_message(conv.id, assistant_msg)

    model_messages = manager.to_model_format(conv.id)

    assert len(model_messages) == 2
    assert model_messages[0]["role"] == "user"
    assert "Hello" in model_messages[0]["content"]
    assert model_messages[1]["role"] == "assistant"
    assert "Hi there!" in model_messages[1]["content"]


def test_truncate_tool_output() -> None:
    """Test tool output truncation."""
    manager = ConversationManager()

    short_output = "Short output"
    result = manager.truncate_tool_output(short_output, "test_tool")
    assert result == short_output

    long_output = "Line\n" * 3000
    result = manager.truncate_tool_output(long_output, "test_tool")
    assert "truncated" in result
    assert len(result) < len(long_output)
