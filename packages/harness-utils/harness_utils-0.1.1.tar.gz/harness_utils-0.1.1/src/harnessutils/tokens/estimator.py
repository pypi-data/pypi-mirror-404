"""Token estimation using simple heuristic.

Uses chars/4 approximation which is fast and good enough for
pruning decisions. Actual token counts from LLM responses are
used for overflow detection.
"""


def estimate_tokens(text: str, chars_per_token: int = 4) -> int:
    """Estimate token count for text using simple heuristic.

    Uses chars_per_token ratio (default 4) for fast estimation.
    This is good enough for pruning decisions. For accurate counts,
    use actual LLM response token counts.

    Args:
        text: Text to estimate tokens for
        chars_per_token: Characters per token ratio (default: 4)

    Returns:
        Estimated token count
    """
    return max(0, round(len(text) / chars_per_token))
