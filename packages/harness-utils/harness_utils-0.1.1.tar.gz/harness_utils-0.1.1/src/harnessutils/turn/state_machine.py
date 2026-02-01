"""Tool state machine for managing tool execution states.

State transitions:
    pending → running → completed
                     ↘ error
"""

from typing import Literal

ToolStatus = Literal["pending", "running", "completed", "error"]


def transition_state(
    current: ToolStatus,
    event: Literal["start", "complete", "fail"],
) -> ToolStatus:
    """Transition tool state based on event.

    Args:
        current: Current tool status
        event: Event that occurred

    Returns:
        New tool status

    Raises:
        ValueError: If transition is invalid
    """
    if current == "pending":
        if event == "start":
            return "running"
        raise ValueError(f"Invalid transition from pending with event {event}")

    elif current == "running":
        if event == "complete":
            return "completed"
        elif event == "fail":
            return "error"
        raise ValueError(f"Invalid transition from running with event {event}")

    elif current in ("completed", "error"):
        raise ValueError(f"Cannot transition from terminal state {current}")

    raise ValueError(f"Unknown state {current}")


class ToolStateMachine:
    """Manages tool execution state transitions."""

    def __init__(self) -> None:
        """Initialize state machine."""
        self.states: dict[str, ToolStatus] = {}

    def start_tool(self, call_id: str) -> None:
        """Mark tool as started.

        Args:
            call_id: Tool call identifier
        """
        if call_id not in self.states:
            self.states[call_id] = "pending"

        self.states[call_id] = transition_state(self.states[call_id], "start")

    def complete_tool(self, call_id: str) -> None:
        """Mark tool as completed.

        Args:
            call_id: Tool call identifier
        """
        if call_id not in self.states:
            raise ValueError(f"Tool {call_id} not found")

        self.states[call_id] = transition_state(self.states[call_id], "complete")

    def fail_tool(self, call_id: str) -> None:
        """Mark tool as failed.

        Args:
            call_id: Tool call identifier
        """
        if call_id not in self.states:
            raise ValueError(f"Tool {call_id} not found")

        self.states[call_id] = transition_state(self.states[call_id], "fail")

    def get_state(self, call_id: str) -> ToolStatus:
        """Get current state of tool.

        Args:
            call_id: Tool call identifier

        Returns:
            Current tool status
        """
        return self.states.get(call_id, "pending")

    def is_terminal(self, call_id: str) -> bool:
        """Check if tool is in terminal state.

        Args:
            call_id: Tool call identifier

        Returns:
            True if tool is completed or errored
        """
        state = self.get_state(call_id)
        return state in ("completed", "error")
