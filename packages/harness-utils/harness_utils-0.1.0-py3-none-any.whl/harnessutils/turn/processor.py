"""Turn processor for handling streaming LLM responses.

Processes stream events from LLM and manages tool execution,
state tracking, and doom loop detection.
"""

import time
from typing import Any

from harnessutils.models.message import Message
from harnessutils.models.parts import (
    ReasoningPart,
    StepFinishPart,
    StepStartPart,
    TextPart,
    TimeInfo,
    ToolPart,
    ToolState,
)
from harnessutils.models.usage import CacheUsage, Usage
from harnessutils.turn.hooks import TurnHooks
from harnessutils.turn.state_machine import ToolStateMachine


class TurnProcessor:
    """Processes streaming LLM events with hook-based customization.

    Handles:
    - Stream event processing
    - Tool state management
    - Doom loop detection (3 identical tool calls)
    - Snapshot tracking
    - Hook invocation
    """

    def __init__(
        self,
        message: Message,
        hooks: TurnHooks | None = None,
        doom_loop_threshold: int = 3,
    ):
        """Initialize turn processor.

        Args:
            message: Assistant message being built
            hooks: Optional hooks for customization
            doom_loop_threshold: Number of identical calls to trigger doom loop
        """
        self.message = message
        self.hooks = hooks or TurnHooks()
        self.doom_loop_threshold = doom_loop_threshold

        self.state_machine = ToolStateMachine()
        self.current_part: TextPart | ReasoningPart | None = None
        self.tool_calls: list[tuple[str, dict[str, Any]]] = []

    def process_stream_event(self, event: dict[str, Any]) -> None:
        """Process a single stream event from LLM.

        Args:
            event: Stream event from LLM

        Event types:
            - start: Stream started
            - text-start: Text content starting
            - text-delta: Text content delta
            - text-end: Text content finished
            - reasoning-start: Extended thinking starting
            - reasoning-delta: Reasoning delta
            - reasoning-end: Reasoning finished
            - tool-call: Tool should be executed
            - step-start: Turn starting
            - step-finish: Turn finished with usage info
        """
        event_type = event.get("type")

        if event_type == "start":
            self._handle_start()

        elif event_type == "step-start":
            self._handle_step_start()

        elif event_type == "text-start":
            self._handle_text_start()

        elif event_type == "text-delta":
            self._handle_text_delta(event.get("text", ""))

        elif event_type == "text-end":
            self._handle_text_end()

        elif event_type == "reasoning-start":
            self._handle_reasoning_start()

        elif event_type == "reasoning-delta":
            self._handle_reasoning_delta(event.get("text", ""))

        elif event_type == "reasoning-end":
            self._handle_reasoning_end()

        elif event_type == "tool-call":
            self._handle_tool_call(event)

        elif event_type == "step-finish":
            self._handle_step_finish(event)

    def _handle_start(self) -> None:
        """Handle stream start."""
        pass

    def _handle_step_start(self) -> None:
        """Handle step start - capture snapshot."""
        snapshot = ""
        if self.hooks.on_snapshot:
            snapshot = self.hooks.on_snapshot("start")

        part = StepStartPart(snapshot=snapshot)
        self.message.add_part(part)

    def _handle_text_start(self) -> None:
        """Handle text content start."""
        self.current_part = TextPart(text="", time=TimeInfo(start=int(time.time() * 1000)))

    def _handle_text_delta(self, text: str) -> None:
        """Handle text content delta."""
        if self.current_part and isinstance(self.current_part, TextPart):
            self.current_part.text += text

    def _handle_text_end(self) -> None:
        """Handle text content end."""
        if self.current_part and isinstance(self.current_part, TextPart):
            if self.current_part.time:
                self.current_part.time.end = int(time.time() * 1000)
            self.message.add_part(self.current_part)
            self.current_part = None

    def _handle_reasoning_start(self) -> None:
        """Handle reasoning start."""
        self.current_part = ReasoningPart(
            text="",
            time=TimeInfo(start=int(time.time() * 1000))
        )

    def _handle_reasoning_delta(self, text: str) -> None:
        """Handle reasoning delta."""
        if self.current_part and isinstance(self.current_part, ReasoningPart):
            self.current_part.text += text

    def _handle_reasoning_end(self) -> None:
        """Handle reasoning end."""
        if self.current_part and isinstance(self.current_part, ReasoningPart):
            if self.current_part.time:
                self.current_part.time.end = int(time.time() * 1000)
            self.message.add_part(self.current_part)
            self.current_part = None

    def _handle_tool_call(self, event: dict[str, Any]) -> None:
        """Handle tool call event."""
        tool_name = event.get("tool", "")
        call_id = event.get("call_id", "")
        tool_input = event.get("input", {})

        # Check for doom loop
        if self._check_doom_loop(tool_name, tool_input):
            return

        # Track tool call
        self.tool_calls.append((tool_name, tool_input))

        # Create tool part
        tool_part = ToolPart(
            tool=tool_name,
            call_id=call_id,
            state=ToolState(
                status="pending",
                input=tool_input,
                time=TimeInfo(start=int(time.time() * 1000)),
            ),
        )

        # Execute tool via hook
        if self.hooks.on_tool_call:
            try:
                self.state_machine.start_tool(call_id)
                tool_part.state.status = "running"

                result = self.hooks.on_tool_call(tool_name, call_id, tool_input)

                self.state_machine.complete_tool(call_id)
                tool_part.state.status = "completed"
                tool_part.state.output = str(result) if result is not None else ""

                if self.hooks.on_tool_result:
                    self.hooks.on_tool_result(call_id, result)

            except Exception as e:
                self.state_machine.fail_tool(call_id)
                tool_part.state.status = "error"
                tool_part.state.error = str(e)

                if self.hooks.on_tool_error:
                    self.hooks.on_tool_error(call_id, e)

            if tool_part.state.time:
                tool_part.state.time.end = int(time.time() * 1000)

        self.message.add_part(tool_part)

    def _handle_step_finish(self, event: dict[str, Any]) -> None:
        """Handle step finish - capture usage and snapshot."""
        usage_data = event.get("usage", {})
        cache_data = usage_data.get("cache", {})

        usage = Usage(
            input=usage_data.get("input", 0),
            output=usage_data.get("output", 0),
            reasoning=usage_data.get("reasoning", 0),
            cache=CacheUsage(
                read=cache_data.get("read", 0),
                write=cache_data.get("write", 0),
            ),
        )

        self.message.tokens = usage
        self.message.cost = event.get("cost", 0.0)

        snapshot = ""
        if self.hooks.on_snapshot:
            snapshot = self.hooks.on_snapshot("finish")

        part = StepFinishPart(
            reason=event.get("reason", "stop"),
            snapshot=snapshot,
            tokens=usage_data,
            cost=event.get("cost", 0.0),
        )
        self.message.add_part(part)

    def _check_doom_loop(self, tool_name: str, tool_input: dict[str, Any]) -> bool:
        """Check if doom loop is occurring.

        Args:
            tool_name: Tool being called
            tool_input: Tool input

        Returns:
            True if doom loop detected and should stop
        """
        if len(self.tool_calls) < self.doom_loop_threshold:
            return False

        # Check last N calls
        last_calls = self.tool_calls[-self.doom_loop_threshold:]

        # All must be identical
        all_identical = all(
            name == tool_name and inp == tool_input
            for name, inp in last_calls
        )

        if all_identical:
            # Invoke hook
            if self.hooks.on_doom_loop:
                should_continue = self.hooks.on_doom_loop(
                    tool_name,
                    tool_input,
                    self.doom_loop_threshold,
                )
                return not should_continue

            # Default: stop
            return True

        return False
