"""Tier 2: Selective pruning of tool outputs.

Removes old tool outputs while preserving conversation structure.
Cost: Cheap (~50ms), Latency: ~50ms.
"""

from dataclasses import dataclass

from harnessutils.config import PruningConfig
from harnessutils.models.message import Message
from harnessutils.models.parts import ToolPart
from harnessutils.tokens.estimator import estimate_tokens


@dataclass
class PruningResult:
    """Result of pruning operation."""

    pruned: int
    tokens_saved: int


def prune_tool_outputs(
    messages: list[Message],
    config: PruningConfig,
    chars_per_token: int = 4,
) -> PruningResult:
    """Prune tool outputs from conversation history.

    Selectively removes old tool outputs while preserving:
    - Tool call metadata (name, input, title, timing)
    - Recent outputs (within protection window)
    - Protected tool outputs
    - Last N turns

    Args:
        messages: Conversation messages (newest first recommended)
        config: Pruning configuration
        chars_per_token: Characters per token ratio for estimation

    Returns:
        PruningResult with count and tokens saved
    """
    total_tokens = 0
    prunable_tokens = 0
    to_prune: list[tuple[Message, ToolPart]] = []
    turns_skipped = 0

    for msg in reversed(messages):
        if msg.role == "user":
            turns_skipped += 1

        if turns_skipped < config.protect_turns:
            continue

        if msg.summary:
            break

        for part in msg.parts:
            if not isinstance(part, ToolPart):
                continue

            if part.state.status != "completed":
                continue

            if part.tool in config.protected_tools:
                continue

            if part.state.time and part.state.time.compacted:
                continue

            token_estimate = estimate_tokens(part.state.output, chars_per_token)
            total_tokens += token_estimate

            if total_tokens > config.prune_protect:
                prunable_tokens += token_estimate
                to_prune.append((msg, part))

    if prunable_tokens > config.prune_minimum:
        for msg, part in to_prune:
            part.state.output = ""
            part.state.attachments = []
            if part.state.time:
                import time

                part.state.time.compacted = int(time.time() * 1000)

        return PruningResult(pruned=len(to_prune), tokens_saved=prunable_tokens)

    return PruningResult(pruned=0, tokens_saved=0)
