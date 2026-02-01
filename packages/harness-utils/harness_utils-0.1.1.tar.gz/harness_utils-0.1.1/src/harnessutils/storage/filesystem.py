"""Filesystem-based storage implementation."""

import json
import time
from pathlib import Path
from typing import Any

from harnessutils.config import StorageConfig


class FilesystemStorage:
    """Hierarchical filesystem storage backend.

    Storage structure:
        data/
        ├── conversations/{projectID}/{conversationID}.json
        ├── messages/{conversationID}/{messageID}.json
        ├── parts/{messageID}/{partID}.json
        └── truncated-outputs/{outputID}
    """

    def __init__(self, config: StorageConfig):
        """Initialize filesystem storage.

        Args:
            config: Storage configuration
        """
        self.base_path = Path(config.base_path)
        self.retention_days = config.retention_days

        self.conversations_dir = self.base_path / "conversations"
        self.messages_dir = self.base_path / "messages"
        self.parts_dir = self.base_path / "parts"
        self.outputs_dir = self.base_path / "truncated-outputs"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.messages_dir.mkdir(parents=True, exist_ok=True)
        self.parts_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def save_conversation(self, conversation_id: str, data: dict[str, Any]) -> None:
        """Save conversation metadata."""
        project_id = data.get("project_id", "default")
        project_dir = self.conversations_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        conv_file = project_dir / f"{conversation_id}.json"
        with open(conv_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_conversation(self, conversation_id: str) -> dict[str, Any]:
        """Load conversation metadata."""
        for project_dir in self.conversations_dir.iterdir():
            if not project_dir.is_dir():
                continue
            conv_file = project_dir / f"{conversation_id}.json"
            if conv_file.exists():
                with open(conv_file) as f:
                    data: dict[str, Any] = json.load(f)
                    return data

        raise FileNotFoundError(f"Conversation {conversation_id} not found")

    def save_message(self, conversation_id: str, message_id: str, data: dict[str, Any]) -> None:
        """Save message metadata."""
        msg_dir = self.messages_dir / conversation_id
        msg_dir.mkdir(parents=True, exist_ok=True)

        msg_file = msg_dir / f"{message_id}.json"
        with open(msg_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_message(self, conversation_id: str, message_id: str) -> dict[str, Any]:
        """Load message metadata."""
        msg_file = self.messages_dir / conversation_id / f"{message_id}.json"
        if not msg_file.exists():
            raise FileNotFoundError(
                f"Message {message_id} in conversation {conversation_id} not found"
            )

        with open(msg_file) as f:
            data: dict[str, Any] = json.load(f)
            return data

    def list_messages(self, conversation_id: str) -> list[str]:
        """List all message IDs for a conversation in chronological order."""
        msg_dir = self.messages_dir / conversation_id
        if not msg_dir.exists():
            return []

        message_ids = [f.stem for f in msg_dir.glob("*.json")]
        return sorted(message_ids)

    def save_part(self, message_id: str, part_id: str, data: dict[str, Any]) -> None:
        """Save message part."""
        part_dir = self.parts_dir / message_id
        part_dir.mkdir(parents=True, exist_ok=True)

        part_file = part_dir / f"{part_id}.json"
        with open(part_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_part(self, message_id: str, part_id: str) -> dict[str, Any]:
        """Load message part."""
        part_file = self.parts_dir / message_id / f"{part_id}.json"
        if not part_file.exists():
            raise FileNotFoundError(f"Part {part_id} in message {message_id} not found")

        with open(part_file) as f:
            data: dict[str, Any] = json.load(f)
            return data

    def list_parts(self, message_id: str) -> list[str]:
        """List all part IDs for a message in order."""
        part_dir = self.parts_dir / message_id
        if not part_dir.exists():
            return []

        part_ids = [f.stem for f in part_dir.glob("*.json")]
        return sorted(part_ids)

    def save_truncated_output(self, output_id: str, content: str) -> None:
        """Save full output that was truncated."""
        output_file = self.outputs_dir / output_id
        with open(output_file, "w") as f:
            f.write(content)

    def load_truncated_output(self, output_id: str) -> str:
        """Load full truncated output."""
        output_file = self.outputs_dir / output_id
        if not output_file.exists():
            raise FileNotFoundError(f"Truncated output {output_id} not found")

        with open(output_file) as f:
            return f.read()

    def cleanup_old_outputs(self, retention_days: int) -> int:
        """Clean up truncated outputs older than retention period."""
        cutoff_timestamp = time.time() - (retention_days * 24 * 60 * 60)
        deleted_count = 0

        for output_file in self.outputs_dir.iterdir():
            if output_file.is_file():
                if output_file.stat().st_mtime < cutoff_timestamp:
                    output_file.unlink()
                    deleted_count += 1

        return deleted_count
