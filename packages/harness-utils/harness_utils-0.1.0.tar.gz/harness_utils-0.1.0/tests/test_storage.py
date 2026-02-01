"""Tests for storage backends."""

import pytest

from harnessutils.storage.memory import MemoryStorage


def test_memory_storage_conversation() -> None:
    """Test conversation storage and retrieval."""
    storage = MemoryStorage()

    conv_data = {
        "id": "conv_123",
        "project_id": "test",
        "created": 1234567890,
    }

    storage.save_conversation("conv_123", conv_data)
    loaded = storage.load_conversation("conv_123")

    assert loaded == conv_data


def test_memory_storage_conversation_not_found() -> None:
    """Test loading non-existent conversation."""
    storage = MemoryStorage()

    with pytest.raises(FileNotFoundError):
        storage.load_conversation("nonexistent")


def test_memory_storage_messages() -> None:
    """Test message storage and listing."""
    storage = MemoryStorage()

    msg_data = {"id": "msg_1", "role": "user", "content": "Hello"}

    storage.save_message("conv_123", "msg_1", msg_data)
    loaded = storage.load_message("conv_123", "msg_1")

    assert loaded == msg_data

    messages = storage.list_messages("conv_123")
    assert messages == ["msg_1"]


def test_memory_storage_parts() -> None:
    """Test part storage and listing."""
    storage = MemoryStorage()

    part_data = {"type": "text", "text": "Hello world"}

    storage.save_part("msg_1", "part_1", part_data)
    loaded = storage.load_part("msg_1", "part_1")

    assert loaded == part_data

    parts = storage.list_parts("msg_1")
    assert parts == ["part_1"]


def test_memory_storage_truncated_output() -> None:
    """Test truncated output storage."""
    storage = MemoryStorage()

    output = "Very long output" * 1000

    storage.save_truncated_output("output_123", output)
    loaded = storage.load_truncated_output("output_123")

    assert loaded == output
