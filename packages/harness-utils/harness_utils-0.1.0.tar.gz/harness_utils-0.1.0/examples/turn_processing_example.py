"""Example of using TurnProcessor for streaming LLM responses.

Demonstrates hook-based turn processing with:
- Tool execution
- Doom loop detection
- Snapshot tracking
- Stream event handling
"""

from harnessutils import (
    ConversationManager,
    HarnessConfig,
    Message,
    MemoryStorage,
    TurnHooks,
    TurnProcessor,
    generate_id,
)


def main() -> None:
    """Run turn processing example."""
    print("=== Turn Processing Example ===\n")

    # Setup
    config = HarnessConfig()
    storage = MemoryStorage()
    manager = ConversationManager(storage, config)

    # Create conversation
    conv = manager.create_conversation(project_id="turn-demo")

    # Add user message
    user_msg = Message(id=generate_id("msg"), role="user")
    user_msg.parts.append(type("TextPart", (), {"type": "text", "text": "Help me debug"})())
    manager.add_message(conv.id, user_msg)

    # Define hooks for custom behavior
    def on_tool_call(tool_name: str, call_id: str, input_data: dict) -> str:
        """Execute tool."""
        print(f"  → Executing tool: {tool_name}")
        print(f"    Call ID: {call_id}")
        print(f"    Input: {input_data}")

        # Simulate tool execution
        if tool_name == "read_file":
            return "File contents here..."
        elif tool_name == "run_tests":
            return "All tests passed!"

        return "Tool executed"

    def on_tool_result(call_id: str, result: str) -> None:
        """Log tool result."""
        print(f"  ✓ Tool {call_id} completed")

    def on_tool_error(call_id: str, error: Exception) -> None:
        """Handle tool error."""
        print(f"  ✗ Tool {call_id} failed: {error}")

    def on_doom_loop(tool_name: str, input_data: dict, count: int) -> bool:
        """Handle doom loop."""
        print(f"\n  ⚠️  Doom loop detected!")
        print(f"     Tool '{tool_name}' called {count} times with same input")
        print(f"     Input: {input_data}")
        print(f"     Stopping execution...\n")
        return False  # Stop

    def on_snapshot(event: str) -> str:
        """Capture snapshot."""
        snapshot_id = f"snapshot_{event}_{generate_id('snap')}"
        print(f"  📸 Captured snapshot: {snapshot_id}")
        return snapshot_id

    # Create hooks
    hooks = TurnHooks(
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
        on_tool_error=on_tool_error,
        on_doom_loop=on_doom_loop,
        on_snapshot=on_snapshot,
    )

    # Create assistant message and processor
    assistant_msg = Message(id=generate_id("msg"), role="assistant")
    processor = TurnProcessor(assistant_msg, hooks)

    # Simulate streaming events from LLM
    print("Simulating LLM stream events:\n")

    events = [
        {"type": "step-start"},
        {"type": "text-start"},
        {"type": "text-delta", "text": "I'll help you debug. "},
        {"type": "text-delta", "text": "Let me read the file first."},
        {"type": "text-end"},
        {
            "type": "tool-call",
            "tool": "read_file",
            "call_id": "call_1",
            "input": {"path": "main.py"},
        },
        {"type": "text-start"},
        {"type": "text-delta", "text": "Now let's run the tests."},
        {"type": "text-end"},
        {
            "type": "tool-call",
            "tool": "run_tests",
            "call_id": "call_2",
            "input": {"suite": "all"},
        },
        {
            "type": "step-finish",
            "reason": "stop",
            "usage": {
                "input": 150,
                "output": 75,
                "reasoning": 0,
                "cache": {"read": 0, "write": 0},
            },
            "cost": 0.02,
        },
    ]

    for event in events:
        processor.process_stream_event(event)

    # Add completed message to conversation
    manager.add_message(conv.id, assistant_msg)

    print("\n=== Turn Complete ===")
    print(f"Message has {len(assistant_msg.parts)} parts")
    print(f"Tokens used: {assistant_msg.tokens.total if assistant_msg.tokens else 0}")
    print(f"Cost: ${assistant_msg.cost:.4f}")

    # Show parts
    print("\nParts breakdown:")
    for i, part in enumerate(assistant_msg.parts):
        print(f"  {i+1}. {part.type}")
        if part.type == "text":
            print(f"     Text: {part.text[:50]}...")
        elif part.type == "tool":
            print(f"     Tool: {part.tool}")
            print(f"     Status: {part.state.status}")

    # Demonstrate doom loop detection
    print("\n\n=== Doom Loop Detection Demo ===\n")

    assistant_msg2 = Message(id=generate_id("msg"), role="assistant")
    processor2 = TurnProcessor(assistant_msg2, hooks, doom_loop_threshold=3)

    print("Calling same tool 4 times with identical input:\n")

    for i in range(4):
        print(f"Call {i+1}:")
        processor2.process_stream_event({
            "type": "tool-call",
            "tool": "debug_tool",
            "call_id": f"call_{i}",
            "input": {"action": "check"},
        })

    print(f"\nResult: {len(assistant_msg2.parts)} tool parts created")
    print("(4th call was blocked by doom loop detection)")


if __name__ == "__main__":
    main()
