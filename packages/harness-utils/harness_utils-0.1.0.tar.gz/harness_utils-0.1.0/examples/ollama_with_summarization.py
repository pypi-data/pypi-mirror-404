"""Ollama example demonstrating all three tiers of context management.

This example simulates a long coding session that triggers:
- Tier 1: Output truncation (large tool outputs)
- Tier 2: Pruning (old tool outputs removed)
- Tier 3: Summarization (context overflow triggers LLM compression)
"""

import json
from typing import Any

import requests

from harnessutils import (
    ConversationManager,
    HarnessConfig,
    Message,
    MemoryStorage,
    TextPart,
    ToolPart,
    ToolState,
    Usage,
    generate_id,
)


class OllamaClient:
    """Ollama API client implementing LLMClient protocol."""

    def __init__(
        self,
        base_url: str = "http://10.6.12.18:11434",
        model: str = "glm-4.7-flash",
        timeout: int = 300,
        max_retries: int = 3,
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def invoke(
        self,
        messages: list[dict[str, Any]],
        system: list[str] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Invoke Ollama API with retry logic."""
        model_to_use = model or self.model

        payload = {
            "model": model_to_use,
            "messages": [],
            "stream": False,
        }

        if system:
            payload["messages"].append({
                "role": "system",
                "content": "\n\n".join(system),
            })

        payload["messages"].extend(messages)

        # Retry logic for timeouts
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                data = response.json()

                usage = {
                    "input": data.get("prompt_eval_count", 0),
                    "output": data.get("eval_count", 0),
                    "reasoning": 0,
                    "cache": {"read": 0, "write": 0},
                }

                return {
                    "content": data["message"]["content"],
                    "usage": usage,
                    "model": model_to_use,
                    "cost": 0.0,
                }

            except requests.exceptions.Timeout as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    print(f"  [Timeout on attempt {attempt + 1}/{self.max_retries}, retrying...]")
                    continue
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    print(f"  [Request error on attempt {attempt + 1}/{self.max_retries}, retrying...]")
                    continue

        raise RuntimeError(f"Failed after {self.max_retries} attempts: {last_error}")


def simulate_tool_output(tool_name: str, size: str = "small") -> str:
    """Simulate tool output of various sizes."""
    outputs = {
        "small": "Operation completed successfully.\n",
        "medium": "DEBUG OUTPUT:\n" + ("Line of debug info\n" * 500),
        "large": "FULL LOG FILE:\n" + ("Detailed log entry with timestamps\n" * 3000),
        "huge": "DATABASE DUMP:\n" + ("Record data with many fields\n" * 5000),
    }
    return outputs.get(size, outputs["small"])


def main() -> None:
    """Run comprehensive example with all three tiers."""
    print("=== Ollama Three-Tier Context Management Demo ===\n")

    # Setup with lower limits to trigger summarization sooner
    config = HarnessConfig()
    config.model_limits.default_context_limit = 8_000  # Lower limit for demo
    config.model_limits.default_output_limit = 1_000
    config.pruning.prune_protect = 2_000  # Protect only 2K tokens
    config.pruning.prune_minimum = 1_000  # Prune if saves 1K+ tokens

    storage = MemoryStorage()
    manager = ConversationManager(storage, config)
    ollama = OllamaClient()

    print(f"Config: Context limit = {config.model_limits.default_context_limit} tokens")
    print(f"Connected to Ollama: glm-4.7-flash\n")

    # Create conversation
    conv = manager.create_conversation(project_id="coding-session")
    print(f"Created conversation: {conv.id}\n")

    # Simulate a coding session with multiple turns and tool calls
    coding_tasks = [
        ("Read the main Python file", "read_file", "medium"),
        ("Run the test suite", "run_tests", "large"),
        ("Check the git history", "git_log", "medium"),
        ("Analyze the database schema", "db_inspect", "huge"),
        ("Run linter on all files", "lint", "large"),
        ("Check dependencies", "pip_list", "medium"),
        ("Review code coverage", "coverage", "large"),
        ("Search for TODO comments", "grep_todos", "medium"),
    ]

    total_tokens = 0
    summarization_count = 0

    for i, (task, tool_name, output_size) in enumerate(coding_tasks):
        print(f"\n{'='*60}")
        print(f"TURN {i+1}: {task}")
        print(f"{'='*60}")

        # User request
        user_msg = Message(id=generate_id("msg"), role="user")
        user_msg.add_part(TextPart(text=task))
        manager.add_message(conv.id, user_msg)
        print(f"User: {task}")

        # Tier 2: Prune before processing
        prune_result = manager.prune_before_turn(conv.id)
        if prune_result['pruned'] > 0:
            print(f"\n[TIER 2: PRUNING]")
            print(f"  Pruned {prune_result['pruned']} old tool outputs")
            print(f"  Saved {prune_result['tokens_saved']:,} tokens")

        # Get context for LLM
        model_messages = manager.to_model_format(conv.id)
        print(f"\nCalling LLM with {len(model_messages)} messages...")

        # Call LLM
        response = ollama.invoke(model_messages)
        assistant_response = response['content']

        # Simulate tool execution with large output
        raw_tool_output = simulate_tool_output(tool_name, output_size)

        # Tier 1: Truncate large output
        truncated_output = manager.truncate_tool_output(raw_tool_output, tool_name)
        was_truncated = len(truncated_output) < len(raw_tool_output)

        if was_truncated:
            print(f"\n[TIER 1: TRUNCATION]")
            print(f"  Output: {len(raw_tool_output):,} bytes → {len(truncated_output):,} bytes")
            print(f"  Saved: {len(raw_tool_output) - len(truncated_output):,} bytes")

        # Add assistant message with tool call
        assistant_msg = Message(id=generate_id("msg"), role="assistant")
        assistant_msg.add_part(TextPart(text=assistant_response[:100] + "..."))

        tool_part = ToolPart(
            tool=tool_name,
            call_id=f"call_{i}",
            state=ToolState(
                status="completed",
                input={"task": task},
                output=truncated_output,
                title=f"Execute: {tool_name}",
            )
        )
        assistant_msg.add_part(tool_part)

        # Track usage
        assistant_msg.tokens = Usage(
            input=response['usage']['input'],
            output=response['usage']['output'],
        )
        total_tokens += assistant_msg.tokens.total

        manager.add_message(conv.id, assistant_msg)

        print(f"Assistant response: {assistant_response[:80]}...")
        print(f"Tokens this turn: {assistant_msg.tokens.total:,}")
        print(f"Total tokens: {total_tokens:,}")

        # Tier 3: Check if summarization needed
        if manager.needs_compaction(conv.id, assistant_msg.tokens):
            print(f"\n[TIER 3: SUMMARIZATION TRIGGERED]")
            print(f"  Context overflow detected!")
            print(f"  Calling LLM to summarize conversation...")

            summary_result = manager.compact(
                conv.id,
                llm_client=ollama,
                parent_message_id=user_msg.id,
                model="glm-4.7-flash",
            )

            summarization_count += 1
            print(f"  ✓ Summary created (message {summary_result['summary_message_id']})")
            print(f"  Tokens used: {summary_result['tokens_used']:,}")
            print(f"  This reduces future context size significantly!")

    # Final statistics
    print(f"\n{'='*60}")
    print(f"SESSION COMPLETE")
    print(f"{'='*60}")

    messages = manager.get_messages(conv.id)
    print(f"\nTotal turns: {len(coding_tasks)}")
    print(f"Total messages: {len(messages)}")
    print(f"Total tokens processed: {total_tokens:,}")
    print(f"Summarizations triggered: {summarization_count}")

    # Show tier activation summary
    print(f"\n{'='*60}")
    print(f"TIER ACTIVATION SUMMARY")
    print(f"{'='*60}")
    print(f"✓ Tier 1 (Truncation): Activated on large outputs")
    print(f"✓ Tier 2 (Pruning): Activated {prune_result['pruned']} times" if prune_result['pruned'] > 0 else "  Tier 2 (Pruning): Ready but not needed")
    print(f"✓ Tier 3 (Summarization): Activated {summarization_count} times")
    print(f"\nAll three tiers working together to manage context!")


if __name__ == "__main__":
    main()
