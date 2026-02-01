"""Tests for message conversion to model format."""

from harnessutils import (
    Message,
    TextPart,
    ToolPart,
    ToolState,
    generate_id,
)
from harnessutils.conversion.to_model import to_model_messages


def test_convert_simple_message():
    """Test converting simple message."""
    msg = Message(id=generate_id("msg"), role="user")
    msg.add_part(TextPart(text="Hello"))

    converted = to_model_messages([msg])

    assert len(converted) == 1
    assert converted[0]["role"] == "user"
    assert "Hello" in str(converted[0]["content"])


def test_convert_empty_messages():
    """Test converting empty message list."""
    converted = to_model_messages([])
    assert converted == []


def test_convert_multiple_messages():
    """Test converting multiple messages."""
    msg1 = Message(id=generate_id("msg"), role="user")
    msg1.add_part(TextPart(text="Question"))

    msg2 = Message(id=generate_id("msg"), role="assistant")
    msg2.add_part(TextPart(text="Answer"))

    converted = to_model_messages([msg1, msg2])

    assert len(converted) == 2
    assert converted[0]["role"] == "user"
    assert converted[1]["role"] == "assistant"


def test_convert_tool_message():
    """Test converting message with tool."""
    msg = Message(id=generate_id("msg"), role="assistant")
    tool_part = ToolPart(
        tool="bash",
        call_id="call_1",
        state=ToolState(
            status="completed",
            input={"command": "ls"},
            output="file1.txt",
        ),
    )
    msg.add_part(tool_part)

    converted = to_model_messages([msg])

    assert len(converted) == 1
    assert converted[0]["role"] == "assistant"
