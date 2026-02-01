"""Part types for message decomposition.

Parts are the granular units that make up messages. This enables
selective compaction where tool outputs can be cleared while
preserving text and metadata.
"""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TimeInfo:
    """Timing information for parts."""

    start: int  # Unix timestamp in milliseconds
    end: int | None = None
    compacted: int | None = None  # When output was compacted


@dataclass
class ToolState:
    """State information for tool execution."""

    status: Literal["pending", "running", "completed", "error"]
    input: dict[str, Any] = field(default_factory=dict)
    output: str = ""
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    time: TimeInfo | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Part:
    """Base class for message parts."""

    type: str = field(init=False)
    time: TimeInfo | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TextPart(Part):
    """Text content part."""

    text: str = ""
    ignored: bool = False  # If true, skip when converting to model format

    def __post_init__(self) -> None:
        self.type = "text"


@dataclass
class ReasoningPart(Part):
    """Extended thinking/reasoning content part."""

    text: str = ""

    def __post_init__(self) -> None:
        self.type = "reasoning"


@dataclass
class ToolPart(Part):
    """Tool execution part."""

    tool: str = ""
    call_id: str = ""
    state: ToolState = field(default_factory=lambda: ToolState(status="pending"))

    def __post_init__(self) -> None:
        self.type = "tool"


@dataclass
class StepStartPart(Part):
    """Step boundary marker - start of LLM turn."""

    snapshot: str = ""  # State snapshot ID

    def __post_init__(self) -> None:
        self.type = "step-start"


@dataclass
class StepFinishPart(Part):
    """Step boundary marker - end of LLM turn."""

    reason: Literal["stop", "tool-calls", "length"] = "stop"
    snapshot: str = ""  # State snapshot ID
    tokens: dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0

    def __post_init__(self) -> None:
        self.type = "step-finish"


@dataclass
class CompactionPart(Part):
    """Marker for compaction request."""

    auto: bool = False  # Was this auto-triggered?

    def __post_init__(self) -> None:
        self.type = "compaction"


@dataclass
class PatchPart(Part):
    """Code change marker."""

    hash: str = ""  # Diff hash
    files: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.type = "patch"


@dataclass
class SubtaskPart(Part):
    """Subtask invocation marker."""

    prompt: str = ""
    description: str = ""
    agent: str = ""
    model: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.type = "subtask"
