"""Tests for Tier 1 truncation."""

from harnessutils.compaction.truncation import truncate_output
from harnessutils.config import TruncationConfig


def test_no_truncation_needed() -> None:
    """Test output that doesn't need truncation."""
    output = "Short output\nWith few lines"
    config = TruncationConfig()

    result = truncate_output(output, config)

    assert not result.truncated
    assert result.content == output
    assert result.bytes_removed == 0


def test_truncation_by_lines() -> None:
    """Test truncation based on line limit."""
    lines = ["Line " + str(i) for i in range(3000)]
    output = "\n".join(lines)
    config = TruncationConfig(max_lines=2000, max_bytes=1_000_000)

    result = truncate_output(output, config, output_id="test_output")

    assert result.truncated
    assert "...2000" in result.content or "bytes truncated" in result.content
    assert result.bytes_removed > 0


def test_truncation_head_direction() -> None:
    """Test truncation keeps head (beginning)."""
    lines = ["Line " + str(i) for i in range(100)]
    output = "\n".join(lines)
    config = TruncationConfig(max_lines=10, direction="head")

    result = truncate_output(output, config)

    assert result.truncated
    assert "Line 0" in result.content
    assert "Line 9" in result.content or "Line 8" in result.content


def test_truncation_tail_direction() -> None:
    """Test truncation keeps tail (end)."""
    lines = ["Line " + str(i) for i in range(100)]
    output = "\n".join(lines)
    config = TruncationConfig(max_lines=10, direction="tail")

    result = truncate_output(output, config)

    assert result.truncated
    assert "Line 99" in result.content
    assert "Line 90" in result.content or "Line 91" in result.content
