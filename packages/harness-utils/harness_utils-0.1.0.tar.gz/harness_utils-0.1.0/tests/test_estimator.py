"""Tests for token estimation."""

from harnessutils.tokens.estimator import estimate_tokens


def test_estimate_tokens_basic():
    """Test basic token estimation."""
    text = "Hello world"
    tokens = estimate_tokens(text)
    # "Hello world" = 11 chars / 4 = ~3 tokens
    assert tokens == 3


def test_estimate_tokens_empty():
    """Test token estimation for empty string."""
    tokens = estimate_tokens("")
    assert tokens == 0


def test_estimate_tokens_large():
    """Test token estimation for large text."""
    text = "x" * 1000
    tokens = estimate_tokens(text)
    # 1000 chars / 4 = 250 tokens
    assert tokens == 250


def test_estimate_tokens_custom_ratio():
    """Test token estimation with custom chars per token."""
    text = "x" * 100
    tokens = estimate_tokens(text, chars_per_token=5)
    # 100 chars / 5 = 20 tokens
    assert tokens == 20


def test_estimate_tokens_rounding():
    """Test token estimation rounding."""
    # 10 chars / 4 = 2.5, should round to 2 or 3
    text = "x" * 10
    tokens = estimate_tokens(text)
    assert tokens in [2, 3]


def test_estimate_tokens_negative_protection():
    """Test that estimation never returns negative."""
    tokens = estimate_tokens("", chars_per_token=4)
    assert tokens >= 0
