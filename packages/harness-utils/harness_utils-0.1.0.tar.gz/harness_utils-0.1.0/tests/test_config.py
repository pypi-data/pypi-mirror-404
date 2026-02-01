"""Tests for configuration system."""

from pathlib import Path

from harnessutils.config import HarnessConfig, PruningConfig, TruncationConfig


def test_default_config() -> None:
    """Test default configuration values."""
    config = HarnessConfig()

    assert config.truncation.max_lines == 2000
    assert config.truncation.max_bytes == 50 * 1024
    assert config.truncation.direction == "head"

    assert config.pruning.prune_protect == 40_000
    assert config.pruning.prune_minimum == 20_000
    assert config.pruning.protect_turns == 2
    assert "skill_execution" in config.pruning.protected_tools

    assert config.tokens.chars_per_token == 4

    assert config.model_limits.default_context_limit == 200_000
    assert config.model_limits.default_output_limit == 8_192

    assert config.storage.retention_days == 7


def test_config_from_dict() -> None:
    """Test loading configuration from dictionary."""
    data = {
        "truncation": {"max_lines": 1000, "direction": "tail"},
        "pruning": {"prune_protect": 30_000},
    }

    config = HarnessConfig.from_dict(data)

    assert config.truncation.max_lines == 1000
    assert config.truncation.direction == "tail"
    assert config.pruning.prune_protect == 30_000
    assert config.pruning.prune_minimum == 20_000  # Should keep default
