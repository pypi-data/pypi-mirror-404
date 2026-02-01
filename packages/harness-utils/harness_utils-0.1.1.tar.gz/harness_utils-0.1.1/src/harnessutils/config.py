"""Configuration schema for harness-utils."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TruncationConfig:
    """Configuration for Tier 1: Output truncation."""

    max_lines: int = 2000
    max_bytes: int = 50 * 1024  # 50KB
    direction: str = "head"  # "head" or "tail"


@dataclass
class PruningConfig:
    """Configuration for Tier 2: Selective pruning."""

    prune_protect: int = 40_000  # Keep recent 40K tokens
    prune_minimum: int = 20_000  # Only prune if saves 20K+ tokens
    protect_turns: int = 2  # Protect last 2 turns
    protected_tools: list[str] = field(
        default_factory=lambda: ["skill_execution", "subtask_invocation"]
    )


@dataclass
class TokenConfig:
    """Configuration for token estimation."""

    chars_per_token: int = 4


@dataclass
class ModelLimitsConfig:
    """Configuration for model limits."""

    default_context_limit: int = 200_000
    default_output_limit: int = 8_192


@dataclass
class StorageConfig:
    """Configuration for storage layer."""

    base_path: Path = field(default_factory=lambda: Path("data"))
    retention_days: int = 7  # For truncated outputs


@dataclass
class CompactionConfig:
    """Configuration for context compaction."""

    auto: bool = True  # Enable auto-summarization
    prune: bool = True  # Enable pruning


@dataclass
class HarnessConfig:
    """Main configuration for harness-utils.

    Provides all configuration parameters for context window management
    with sensible defaults from the CTXWINARCH.md specification.
    """

    truncation: TruncationConfig = field(default_factory=TruncationConfig)
    pruning: PruningConfig = field(default_factory=PruningConfig)
    tokens: TokenConfig = field(default_factory=TokenConfig)
    model_limits: ModelLimitsConfig = field(default_factory=ModelLimitsConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    compaction: CompactionConfig = field(default_factory=CompactionConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HarnessConfig":
        """Create configuration from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            HarnessConfig instance
        """
        config = cls()

        if "truncation" in data:
            config.truncation = TruncationConfig(**data["truncation"])
        if "pruning" in data:
            protected = data["pruning"].get("protected_tools")
            pruning_data = {k: v for k, v in data["pruning"].items() if k != "protected_tools"}
            if protected:
                pruning_data["protected_tools"] = protected
            config.pruning = PruningConfig(**pruning_data)
        if "tokens" in data:
            config.tokens = TokenConfig(**data["tokens"])
        if "model_limits" in data:
            config.model_limits = ModelLimitsConfig(**data["model_limits"])
        if "storage" in data:
            storage_data = data["storage"].copy()
            if "base_path" in storage_data:
                storage_data["base_path"] = Path(storage_data["base_path"])
            config.storage = StorageConfig(**storage_data)
        if "compaction" in data:
            config.compaction = CompactionConfig(**data["compaction"])

        return config

    @classmethod
    def from_toml(cls, path: Path) -> "HarnessConfig":
        """Load configuration from TOML file.

        Args:
            path: Path to TOML configuration file

        Returns:
            HarnessConfig instance
        """
        import tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)

        return cls.from_dict(data)

    @classmethod
    def from_json(cls, path: Path) -> "HarnessConfig":
        """Load configuration from JSON file.

        Args:
            path: Path to JSON configuration file

        Returns:
            HarnessConfig instance
        """
        import json

        with open(path) as f:
            data = json.load(f)

        return cls.from_dict(data)
