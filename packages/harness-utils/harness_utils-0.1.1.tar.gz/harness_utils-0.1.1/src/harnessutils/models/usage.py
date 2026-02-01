"""Token usage and cost tracking."""

from dataclasses import dataclass, field


@dataclass
class CacheUsage:
    """Cache token usage information."""

    read: int = 0  # Cached input tokens (discounted)
    write: int = 0  # Cache creation tokens (premium)


@dataclass
class Usage:
    """Token usage information for a turn."""

    input: int = 0  # Input tokens consumed
    output: int = 0  # Output tokens generated
    reasoning: int = 0  # Extended thinking tokens
    cache: CacheUsage = field(default_factory=CacheUsage)

    @property
    def total_input(self) -> int:
        """Total input tokens including cache reads."""
        return self.input + self.cache.read

    @property
    def total_output(self) -> int:
        """Total output tokens including reasoning."""
        return self.output + self.reasoning

    @property
    def total(self) -> int:
        """Total tokens across all categories."""
        return self.total_input + self.total_output
