"""Example of implementing custom storage adapter.

Demonstrates how to implement StorageBackend protocol for any data layer.
This example uses SQLite, but the same pattern works for any database,
API, or storage system.
"""

import json
import sqlite3
import time
from typing import Any

from harnessutils import (
    ConversationManager,
    HarnessConfig,
    Message,
    TextPart,
    generate_id,
)


class SQLiteStorage:
    """Custom storage adapter using SQLite.

    Users implement StorageBackend protocol for their own schema.
    This is just an example - adapt to your database structure.
    """

    def __init__(self, db_path: str = ":memory:"):
        """Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file (":memory:" for in-memory)
        """
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_conv_project
                ON conversations(project_id);

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
            CREATE INDEX IF NOT EXISTS idx_msg_conv
                ON messages(conversation_id);

            CREATE TABLE IF NOT EXISTS parts (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages(id)
            );
            CREATE INDEX IF NOT EXISTS idx_part_msg
                ON parts(message_id);

            CREATE TABLE IF NOT EXISTS truncated_outputs (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_output_time
                ON truncated_outputs(created_at);
        """)
        self.conn.commit()

    def save_conversation(self, conversation_id: str, data: dict[str, Any]) -> None:
        """Save conversation to database."""
        self.conn.execute(
            """INSERT OR REPLACE INTO conversations
               (id, project_id, data, created_at)
               VALUES (?, ?, ?, ?)""",
            (
                conversation_id,
                data.get("project_id", "default"),
                json.dumps(data),
                int(time.time()),
            ),
        )
        self.conn.commit()

    def load_conversation(self, conversation_id: str) -> dict[str, Any]:
        """Load conversation from database."""
        row = self.conn.execute(
            "SELECT data FROM conversations WHERE id = ?",
            (conversation_id,)
        ).fetchone()

        if not row:
            raise FileNotFoundError(f"Conversation {conversation_id} not found")

        return json.loads(row["data"])

    def save_message(
        self,
        conversation_id: str,
        message_id: str,
        data: dict[str, Any]
    ) -> None:
        """Save message to database."""
        self.conn.execute(
            """INSERT OR REPLACE INTO messages
               (id, conversation_id, data, created_at)
               VALUES (?, ?, ?, ?)""",
            (
                message_id,
                conversation_id,
                json.dumps(data),
                int(time.time()),
            ),
        )
        self.conn.commit()

    def load_message(
        self,
        conversation_id: str,
        message_id: str
    ) -> dict[str, Any]:
        """Load message from database."""
        row = self.conn.execute(
            """SELECT data FROM messages
               WHERE id = ? AND conversation_id = ?""",
            (message_id, conversation_id)
        ).fetchone()

        if not row:
            raise FileNotFoundError(
                f"Message {message_id} in conversation {conversation_id} not found"
            )

        return json.loads(row["data"])

    def list_messages(self, conversation_id: str) -> list[str]:
        """List all message IDs for a conversation."""
        rows = self.conn.execute(
            """SELECT id FROM messages
               WHERE conversation_id = ?
               ORDER BY id""",
            (conversation_id,)
        ).fetchall()

        return [row["id"] for row in rows]

    def save_part(
        self,
        message_id: str,
        part_id: str,
        data: dict[str, Any]
    ) -> None:
        """Save message part to database."""
        self.conn.execute(
            """INSERT OR REPLACE INTO parts
               (id, message_id, data, created_at)
               VALUES (?, ?, ?, ?)""",
            (
                part_id,
                message_id,
                json.dumps(data),
                int(time.time()),
            ),
        )
        self.conn.commit()

    def load_part(self, message_id: str, part_id: str) -> dict[str, Any]:
        """Load message part from database."""
        row = self.conn.execute(
            """SELECT data FROM parts
               WHERE id = ? AND message_id = ?""",
            (part_id, message_id)
        ).fetchone()

        if not row:
            raise FileNotFoundError(
                f"Part {part_id} in message {message_id} not found"
            )

        return json.loads(row["data"])

    def list_parts(self, message_id: str) -> list[str]:
        """List all part IDs for a message."""
        rows = self.conn.execute(
            """SELECT id FROM parts
               WHERE message_id = ?
               ORDER BY id""",
            (message_id,)
        ).fetchall()

        return [row["id"] for row in rows]

    def save_truncated_output(self, output_id: str, content: str) -> None:
        """Save truncated output to database."""
        self.conn.execute(
            """INSERT OR REPLACE INTO truncated_outputs
               (id, content, created_at)
               VALUES (?, ?, ?)""",
            (output_id, content, int(time.time())),
        )
        self.conn.commit()

    def load_truncated_output(self, output_id: str) -> str:
        """Load truncated output from database."""
        row = self.conn.execute(
            "SELECT content FROM truncated_outputs WHERE id = ?",
            (output_id,)
        ).fetchone()

        if not row:
            raise FileNotFoundError(f"Truncated output {output_id} not found")

        return row["content"]

    def cleanup_old_outputs(self, retention_days: int) -> int:
        """Clean up old truncated outputs."""
        cutoff = int(time.time()) - (retention_days * 24 * 60 * 60)
        cursor = self.conn.execute(
            "DELETE FROM truncated_outputs WHERE created_at < ?",
            (cutoff,)
        )
        self.conn.commit()
        return cursor.rowcount


def main() -> None:
    """Run custom storage example."""
    print("=== Custom Storage Example ===\n")

    # Use custom SQLite storage instead of filesystem
    storage = SQLiteStorage(":memory:")
    config = HarnessConfig()
    manager = ConversationManager(storage, config)

    # Create conversation
    conv = manager.create_conversation(project_id="sql-demo")
    print(f"Created conversation: {conv.id}")

    # Add messages
    user_msg = Message(id=generate_id("msg"), role="user")
    user_msg.add_part(TextPart(text="Hello from SQLite!"))
    manager.add_message(conv.id, user_msg)

    assistant_msg = Message(id=generate_id("msg"), role="assistant")
    assistant_msg.add_part(TextPart(text="Stored in SQL database"))
    manager.add_message(conv.id, assistant_msg)

    # Verify storage
    message_ids = storage.list_messages(conv.id)
    print(f"Added {len(message_ids)} messages")
    print(f"\nMessage IDs in database: {message_ids}")

    # Load messages from storage
    messages = manager.get_messages(conv.id)
    print(f"\nLoaded {len(messages)} messages from database")

    # Show message contents
    for msg in messages:
        role = msg.role
        text = msg.parts[0].text if msg.parts else ""
        print(f"  {role}: {text}")


if __name__ == "__main__":
    main()
