"""Ollama API integration example for harness-utils.

Demonstrates using the glm-4.7-flash model via Ollama API
with the three-tier context management strategy.
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
        """Initialize Ollama client.

        Args:
            base_url: Ollama server URL
            model: Model name to use
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts on timeout
        """
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
        """Invoke Ollama API with retry logic.

        Args:
            messages: List of messages in chat format
            system: Optional system prompt parts
            model: Optional model override

        Returns:
            Response with content, usage, and model info
        """
        model_to_use = model or self.model

        # Build request payload
        payload = {
            "model": model_to_use,
            "messages": [],
            "stream": False,
        }

        # Add system message if provided
        if system:
            payload["messages"].append({
                "role": "system",
                "content": "\n\n".join(system),
            })

        # Add conversation messages
        payload["messages"].extend(messages)

        # Retry logic for timeouts
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Make API request
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                data = response.json()

                # Extract token usage
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


def main() -> None:
    """Run Ollama integration example."""
    print("=== Ollama API Integration Example ===\n")

    # Setup
    config = HarnessConfig()
    storage = MemoryStorage()  # Use in-memory for this example
    manager = ConversationManager(storage, config)

    # Create Ollama client
    ollama = OllamaClient()
    print(f"Connected to Ollama at 10.6.12.18:11434")
    print(f"Using model: glm-4.7-flash\n")

    # Create conversation
    conv = manager.create_conversation(project_id="ollama-demo")
    print(f"Created conversation: {conv.id}\n")

    # Simulate a multi-turn conversation
    turns = [
        "What is Python?",
        "How do I create a list?",
        "What's the difference between a list and a tuple?",
    ]

    for i, user_input in enumerate(turns):
        print(f"--- Turn {i+1} ---")
        print(f"User: {user_input}")

        # Add user message
        user_msg = Message(id=generate_id("msg"), role="user")
        user_msg.add_part(TextPart(text=user_input))
        manager.add_message(conv.id, user_msg)

        # Prune before processing (Tier 2)
        prune_result = manager.prune_before_turn(conv.id)
        if prune_result['pruned'] > 0:
            print(f"  [Pruned {prune_result['pruned']} outputs, "
                  f"saved {prune_result['tokens_saved']} tokens]")

        # Get messages in model format
        model_messages = manager.to_model_format(conv.id)

        # Call Ollama API
        print("  [Calling Ollama API...]")
        response = ollama.invoke(model_messages)

        print(f"Assistant: {response['content'][:200]}...")
        print(f"  [Tokens - Input: {response['usage']['input']}, "
              f"Output: {response['usage']['output']}]")

        # Add assistant response
        assistant_msg = Message(id=generate_id("msg"), role="assistant")
        assistant_msg.add_part(TextPart(text=response['content']))

        # Track token usage
        assistant_msg.tokens = Usage(
            input=response['usage']['input'],
            output=response['usage']['output'],
        )
        assistant_msg.cost = response['cost']

        manager.add_message(conv.id, assistant_msg)

        # Check if summarization needed (Tier 3)
        if manager.needs_compaction(conv.id, assistant_msg.tokens):
            print("\n  [Context overflow detected - triggering summarization]")
            summary_result = manager.compact(
                conv.id,
                llm_client=ollama,
                parent_message_id=user_msg.id,
                model="glm-4.7-flash",
            )
            print(f"  [Summarized - Cost: ${summary_result['cost']:.4f}, "
                  f"Tokens: {summary_result['tokens_used']}]")

        print()

    # Final stats
    messages = manager.get_messages(conv.id)
    total_messages = len(messages)
    total_tokens = sum(
        msg.tokens.total if msg.tokens else 0
        for msg in messages
    )

    print(f"=== Conversation Complete ===")
    print(f"Total messages: {total_messages}")
    print(f"Total tokens: {total_tokens}")


if __name__ == "__main__":
    main()
