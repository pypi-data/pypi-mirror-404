"""Tests for filesystem storage."""

import tempfile
import time
from pathlib import Path

import pytest

from harnessutils import FilesystemStorage
from harnessutils.config import StorageConfig


@pytest.fixture
def temp_storage():
    """Create temporary filesystem storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = StorageConfig(base_path=tmpdir)
        storage = FilesystemStorage(config)
        yield storage


def test_filesystem_storage_init(temp_storage):
    """Test filesystem storage initialization creates directories."""
    assert temp_storage.conversations_dir.exists()
    assert temp_storage.messages_dir.exists()
    assert temp_storage.parts_dir.exists()
    assert temp_storage.outputs_dir.exists()


def test_save_and_load_conversation(temp_storage):
    """Test saving and loading conversation."""
    conv_id = "conv_test_123"
    data = {
        "id": conv_id,
        "project_id": "test-project",
        "created": 1234567890,
    }

    temp_storage.save_conversation(conv_id, data)
    loaded = temp_storage.load_conversation(conv_id)

    assert loaded == data


def test_load_conversation_not_found(temp_storage):
    """Test loading nonexistent conversation raises error."""
    with pytest.raises(FileNotFoundError):
        temp_storage.load_conversation("nonexistent")


def test_save_and_load_message(temp_storage):
    """Test saving and loading message."""
    conv_id = "conv_123"
    msg_id = "msg_456"
    data = {
        "id": msg_id,
        "role": "user",
        "parts": [],
    }

    temp_storage.save_message(conv_id, msg_id, data)
    loaded = temp_storage.load_message(conv_id, msg_id)

    assert loaded == data


def test_load_message_not_found(temp_storage):
    """Test loading nonexistent message raises error."""
    with pytest.raises(FileNotFoundError):
        temp_storage.load_message("conv_123", "nonexistent")


def test_list_messages(temp_storage):
    """Test listing messages in chronological order."""
    conv_id = "conv_123"

    # Add messages out of order
    temp_storage.save_message(conv_id, "msg_003", {"id": "msg_003"})
    temp_storage.save_message(conv_id, "msg_001", {"id": "msg_001"})
    temp_storage.save_message(conv_id, "msg_002", {"id": "msg_002"})

    messages = temp_storage.list_messages(conv_id)
    assert messages == ["msg_001", "msg_002", "msg_003"]


def test_list_messages_empty(temp_storage):
    """Test listing messages for conversation with no messages."""
    messages = temp_storage.list_messages("nonexistent")
    assert messages == []


def test_save_and_load_part(temp_storage):
    """Test saving and loading message part."""
    msg_id = "msg_123"
    part_id = "part_456"
    data = {
        "type": "text",
        "text": "Hello world",
    }

    temp_storage.save_part(msg_id, part_id, data)
    loaded = temp_storage.load_part(msg_id, part_id)

    assert loaded == data


def test_load_part_not_found(temp_storage):
    """Test loading nonexistent part raises error."""
    with pytest.raises(FileNotFoundError):
        temp_storage.load_part("msg_123", "nonexistent")


def test_list_parts(temp_storage):
    """Test listing parts in order."""
    msg_id = "msg_123"

    temp_storage.save_part(msg_id, "part_003", {"id": "part_003"})
    temp_storage.save_part(msg_id, "part_001", {"id": "part_001"})
    temp_storage.save_part(msg_id, "part_002", {"id": "part_002"})

    parts = temp_storage.list_parts(msg_id)
    assert parts == ["part_001", "part_002", "part_003"]


def test_list_parts_empty(temp_storage):
    """Test listing parts for message with no parts."""
    parts = temp_storage.list_parts("nonexistent")
    assert parts == []


def test_save_and_load_truncated_output(temp_storage):
    """Test saving and loading truncated output."""
    output_id = "output_123"
    content = "Very long output content that was truncated..."

    temp_storage.save_truncated_output(output_id, content)
    loaded = temp_storage.load_truncated_output(output_id)

    assert loaded == content


def test_load_truncated_output_not_found(temp_storage):
    """Test loading nonexistent truncated output raises error."""
    with pytest.raises(FileNotFoundError):
        temp_storage.load_truncated_output("nonexistent")


def test_cleanup_old_outputs(temp_storage):
    """Test cleaning up old truncated outputs."""
    # Save some outputs
    temp_storage.save_truncated_output("old_1", "content 1")
    temp_storage.save_truncated_output("old_2", "content 2")

    # Make the files old by modifying their mtime
    old_time = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
    for output_file in temp_storage.outputs_dir.iterdir():
        Path(output_file).touch()
        import os
        os.utime(output_file, (old_time, old_time))

    # Cleanup outputs older than 7 days
    deleted_count = temp_storage.cleanup_old_outputs(7)
    assert deleted_count == 2

    # Verify files are gone
    assert list(temp_storage.outputs_dir.iterdir()) == []


def test_cleanup_preserves_recent_outputs(temp_storage):
    """Test cleanup preserves recent outputs."""
    temp_storage.save_truncated_output("recent", "recent content")

    # Cleanup outputs older than 7 days
    deleted_count = temp_storage.cleanup_old_outputs(7)
    assert deleted_count == 0

    # Verify file still exists
    loaded = temp_storage.load_truncated_output("recent")
    assert loaded == "recent content"


def test_conversation_with_project_id(temp_storage):
    """Test conversation storage with project grouping."""
    conv_id = "conv_123"
    data = {
        "id": conv_id,
        "project_id": "my-project",
    }

    temp_storage.save_conversation(conv_id, data)

    # Verify it's stored in project subdirectory
    project_dir = temp_storage.conversations_dir / "my-project"
    assert project_dir.exists()
    assert (project_dir / f"{conv_id}.json").exists()

    # Verify it can be loaded
    loaded = temp_storage.load_conversation(conv_id)
    assert loaded == data
