"""SQLite implementation of ThreadsBackend."""
import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from lineage.backends.threads.models import (
    Artifact,
    RunSummary,
    StoredMessage,
    ThreadContext,
)
from lineage.backends.threads.protocol import ThreadsBackend

logger = logging.getLogger(__name__)


class SQLiteThreadsBackend(ThreadsBackend):
    """SQLite-backed thread storage."""

    def __init__(self, db_path: str | Path):
        """Initialize SQLite threads backend.

        Args:
            db_path: Path to SQLite database file
        """
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._conn:
            # Threads table (core identity)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS threads (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            
            # Runs table (summaries)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY(thread_id) REFERENCES threads(id)
                )
                """
            )
            
            # Artifacts table
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id),
                    FOREIGN KEY(thread_id) REFERENCES threads(id)
                )
                """
            )
            
            # Messages table (full history)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY(thread_id) REFERENCES threads(id)
                )
                """
            )
            
            # Metadata table (key-value store per thread)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS thread_metadata (
                    thread_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (thread_id, key),
                    FOREIGN KEY(thread_id) REFERENCES threads(id)
                )
                """
            )

    def get_or_create_thread(self, thread_id: str) -> ThreadContext:
        """Get existing thread context or create new one."""
        # Use the connection as a context manager so any writes (INSERT OR IGNORE)
        # are committed automatically, consistent with other mutating methods.
        with self._lock, self._conn:
            # Ensure thread exists
            self._conn.execute(
                "INSERT OR IGNORE INTO threads (id) VALUES (?)",
                (thread_id,)
            )
            
            # Fetch runs
            runs_cursor = self._conn.execute(
                "SELECT id, title, summary, created_at FROM runs WHERE thread_id = ? ORDER BY created_at ASC",
                (thread_id,)
            )
            runs = [
                RunSummary(
                    run_id=row["id"],
                    title=row["title"],
                    summary=row["summary"],
                    timestamp=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
                )
                for row in runs_cursor
            ]
            
            # Fetch artifacts
            artifacts_cursor = self._conn.execute(
                "SELECT id, run_id, type, title, created_at FROM artifacts WHERE thread_id = ?",
                (thread_id,)
            )
            artifacts = {
                Artifact(
                    id=row["id"],
                    run_id=row["run_id"],
                    type=row["type"],
                    title=row["title"],
                    created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
                )
                for row in artifacts_cursor
            }
            
            return ThreadContext(
                thread_id=thread_id,
                runs=runs,
                artifacts=artifacts
            )

    def add_artifact(self, thread_id: str, run_id: str, artifact: Artifact) -> None:
        """Add an artifact to storage."""
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO artifacts (id, run_id, thread_id, type, title, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (artifact.id, run_id, thread_id, artifact.type, artifact.title, artifact.created_at.isoformat())
            )

    def save_run_summary(self, thread_id: str, run_summary: RunSummary) -> None:
        """Save run summary."""
        with self._lock, self._conn:
            # Ensure thread exists (just in case)
            self._conn.execute("INSERT OR IGNORE INTO threads (id) VALUES (?)", (thread_id,))
            
            self._conn.execute(
                """
                INSERT INTO runs (id, thread_id, title, summary, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run_summary.run_id, 
                    thread_id, 
                    run_summary.title, 
                    run_summary.summary, 
                    run_summary.timestamp.isoformat()
                )
            )

    def thread_exists(self, thread_id: str) -> bool:
        """Check if thread exists."""
        cursor = self._conn.execute("SELECT 1 FROM threads WHERE id = ?", (thread_id,))
        return cursor.fetchone() is not None

    def add_message(self, thread_id: str, message: StoredMessage) -> None:
        """Add a message to the thread history."""
        with self._lock, self._conn:
            # Ensure thread exists
            self._conn.execute("INSERT OR IGNORE INTO threads (id) VALUES (?)", (thread_id,))
            
            metadata_json = json.dumps(message.metadata) if message.metadata else None
            self._conn.execute(
                """
                INSERT INTO messages (id, thread_id, role, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message.message_id,
                    thread_id,
                    message.role,
                    message.content,
                    metadata_json,
                    message.created_at.isoformat()
                )
            )

    def get_messages(self, thread_id: str) -> List[StoredMessage]:
        """Get message history."""
        cursor = self._conn.execute(
            "SELECT id, role, content, metadata, created_at FROM messages WHERE thread_id = ? ORDER BY created_at ASC",
            (thread_id,)
        )
        messages = []
        for row in cursor:
            metadata = json.loads(row["metadata"]) if row["metadata"] else None
            messages.append(StoredMessage(
                message_id=row["id"],
                role=row["role"],
                content=row["content"],
                metadata=metadata,
                created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
            ))
        return messages

    def set_metadata(self, thread_id: str, key: str, value: Any) -> None:
        """Set thread metadata."""
        value_json = json.dumps(value)
        with self._lock, self._conn:
            self._conn.execute("INSERT OR IGNORE INTO threads (id) VALUES (?)", (thread_id,))
            self._conn.execute(
                """
                INSERT INTO thread_metadata (thread_id, key, value)
                VALUES (?, ?, ?)
                ON CONFLICT(thread_id, key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (thread_id, key, value_json)
            )

    def get_metadata(self, thread_id: str, key: str) -> Optional[Any]:
        """Get thread metadata."""
        cursor = self._conn.execute(
            "SELECT value FROM thread_metadata WHERE thread_id = ? AND key = ?",
            (thread_id, key)
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row["value"])
        return None
