"""Tests for turn processing."""

import pytest

from harnessutils import (
    Message,
    ToolStateMachine,
    TurnHooks,
    TurnProcessor,
    generate_id,
    transition_state,
)


def test_state_transitions() -> None:
    """Test tool state transitions."""
    assert transition_state("pending", "start") == "running"
    assert transition_state("running", "complete") == "completed"
    assert transition_state("running", "fail") == "error"

    with pytest.raises(ValueError):
        transition_state("pending", "complete")

    with pytest.raises(ValueError):
        transition_state("completed", "start")


def test_state_machine() -> None:
    """Test tool state machine."""
    machine = ToolStateMachine()

    machine.start_tool("call_1")
    assert machine.get_state("call_1") == "running"
    assert not machine.is_terminal("call_1")

    machine.complete_tool("call_1")
    assert machine.get_state("call_1") == "completed"
    assert machine.is_terminal("call_1")


def test_state_machine_error() -> None:
    """Test tool state machine error handling."""
    machine = ToolStateMachine()

    machine.start_tool("call_1")
    machine.fail_tool("call_1")

    assert machine.get_state("call_1") == "error"
    assert machine.is_terminal("call_1")


def test_turn_processor_text() -> None:
    """Test processing text events."""
    msg = Message(id=generate_id("msg"), role="assistant")
    processor = TurnProcessor(msg)

    processor.process_stream_event({"type": "text-start"})
    processor.process_stream_event({"type": "text-delta", "text": "Hello"})
    processor.process_stream_event({"type": "text-delta", "text": " world"})
    processor.process_stream_event({"type": "text-end"})

    assert len(msg.parts) == 1
    assert msg.parts[0].type == "text"
    assert msg.parts[0].text == "Hello world"


def test_turn_processor_reasoning() -> None:
    """Test processing reasoning events."""
    msg = Message(id=generate_id("msg"), role="assistant")
    processor = TurnProcessor(msg)

    processor.process_stream_event({"type": "reasoning-start"})
    processor.process_stream_event({"type": "reasoning-delta", "text": "Thinking..."})
    processor.process_stream_event({"type": "reasoning-end"})

    assert len(msg.parts) == 1
    assert msg.parts[0].type == "reasoning"
    assert "Thinking" in msg.parts[0].text


def test_turn_processor_tool_call() -> None:
    """Test processing tool call events."""
    msg = Message(id=generate_id("msg"), role="assistant")

    tool_executed = False

    def on_tool_call(tool_name: str, call_id: str, input_data: dict) -> str:
        nonlocal tool_executed
        tool_executed = True
        return "Tool result"

    hooks = TurnHooks(on_tool_call=on_tool_call)
    processor = TurnProcessor(msg, hooks)

    processor.process_stream_event(
        {
            "type": "tool-call",
            "tool": "test_tool",
            "call_id": "call_1",
            "input": {"param": "value"},
        }
    )

    assert tool_executed
    assert len(msg.parts) == 1
    assert msg.parts[0].type == "tool"
    assert msg.parts[0].state.status == "completed"
    assert msg.parts[0].state.output == "Tool result"


def test_turn_processor_doom_loop() -> None:
    """Test doom loop detection."""
    msg = Message(id=generate_id("msg"), role="assistant")

    call_count = 0
    doom_detected = False

    def on_tool_call(tool_name: str, call_id: str, input_data: dict) -> str:
        nonlocal call_count
        call_count += 1
        return "result"

    def on_doom_loop(tool_name: str, input_data: dict, count: int) -> bool:
        nonlocal doom_detected
        doom_detected = True
        return False  # Stop execution

    hooks = TurnHooks(on_tool_call=on_tool_call, on_doom_loop=on_doom_loop)
    processor = TurnProcessor(msg, hooks, doom_loop_threshold=3)

    # Call same tool 4 times
    for i in range(4):
        processor.process_stream_event(
            {
                "type": "tool-call",
                "tool": "test_tool",
                "call_id": f"call_{i}",
                "input": {"same": "input"},
            }
        )

    # Should execute 3 times, then detect doom loop on 4th
    assert call_count == 3
    assert doom_detected


def test_turn_processor_step_events() -> None:
    """Test step start/finish events."""
    msg = Message(id=generate_id("msg"), role="assistant")

    snapshots = []

    def on_snapshot(event: str) -> str:
        snapshots.append(event)
        return f"snapshot_{event}"

    hooks = TurnHooks(on_snapshot=on_snapshot)
    processor = TurnProcessor(msg, hooks)

    processor.process_stream_event({"type": "step-start"})
    processor.process_stream_event(
        {
            "type": "step-finish",
            "reason": "stop",
            "usage": {
                "input": 100,
                "output": 50,
                "reasoning": 0,
                "cache": {"read": 0, "write": 0},
            },
            "cost": 0.01,
        }
    )

    assert snapshots == ["start", "finish"]
    assert len(msg.parts) == 2
    assert msg.parts[0].type == "step-start"
    assert msg.parts[1].type == "step-finish"
    assert msg.tokens.input == 100
    assert msg.tokens.output == 50
    assert msg.cost == 0.01
