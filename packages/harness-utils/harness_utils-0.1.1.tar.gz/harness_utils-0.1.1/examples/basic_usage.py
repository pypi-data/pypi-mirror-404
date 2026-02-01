"""Basic usage example for harness-utils.

Demonstrates creating conversations, adding messages, and using
the three-tier context management strategy.
"""

from harnessutils import (
    ConversationManager,
    FilesystemStorage,
    HarnessConfig,
    Message,
    TextPart,
    ToolPart,
    ToolState,
    Usage,
    generate_id,
)


def main() -> None:
    """Run basic usage example."""
    # Setup
    config = HarnessConfig()
    storage = FilesystemStorage(config.storage)
    manager = ConversationManager(storage, config)

    # Create conversation
    conv = manager.create_conversation(project_id="example")
    print(f"Created conversation: {conv.id}")

    # Add user message
    user_msg = Message(id=generate_id("msg"), role="user")
    user_msg.add_part(TextPart(text="Help me debug this code"))
    manager.add_message(conv.id, user_msg)
    print(f"Added user message: {user_msg.id}")

    # Prune before processing (Tier 2)
    result = manager.prune_before_turn(conv.id)
    print(f"Pruning: {result['pruned']} outputs, {result['tokens_saved']} tokens saved")

    # Convert to model format for LLM request
    model_messages = manager.to_model_format(conv.id)
    print(f"Model messages: {len(model_messages)}")

    # Simulate LLM response
    assistant_msg = Message(id=generate_id("msg"), role="assistant")
    assistant_msg.add_part(TextPart(text="I'll help you debug..."))

    # Simulate a tool call with large output
    tool_output = "DEBUG LOG:\n" + ("Line of debug output\n" * 3000)
    truncated_output = manager.truncate_tool_output(tool_output, "debug_tool")

    tool_part = ToolPart(
        tool="debug_tool",
        call_id="call_123",
        state=ToolState(
            status="completed",
            input={"command": "run_debug"},
            output=truncated_output,
            title="Run debug",
        )
    )
    assistant_msg.add_part(tool_part)
    manager.add_message(conv.id, assistant_msg)
    print(f"Added assistant message with tool call")

    # Check if summarization needed (Tier 3)
    usage = Usage(input=50000, output=2000)  # Simulate usage
    if manager.needs_compaction(conv.id, usage):
        print("Summarization needed (would call LLM here)")
    else:
        print("No summarization needed yet")

    print(f"\nConversation has {len(manager.get_messages(conv.id))} messages")


if __name__ == "__main__":
    main()
