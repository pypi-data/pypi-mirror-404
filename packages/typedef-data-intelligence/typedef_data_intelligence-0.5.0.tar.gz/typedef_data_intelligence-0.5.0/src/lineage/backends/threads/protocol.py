"""Protocol definition for thread storage backend."""

from typing import Any, List, Optional, Protocol

from lineage.backends.threads.models import (
    Artifact,
    RunSummary,
    StoredMessage,
    ThreadContext,
)


class ThreadsBackend(Protocol):
    """Protocol for storing and retrieving thread context across agent runs.

    A thread represents a conversation with multiple agent runs. Each run
    creates a summary with artifacts (e.g., reports). The ThreadsBackend
    persists this context so agents can reference previous runs.
    """

    def get_or_create_thread(self, thread_id: str) -> ThreadContext:
        """Get all run summaries for a thread.

        Args:
            thread_id: Unique identifier for the thread

        Returns:
            ThreadContext with all previous run summaries, or empty context
            if thread doesn't exist yet
        """
        ...

    def add_artifact(self, thread_id: str, run_id: str, artifact: Artifact) -> None:
        """Add an artifact to the thread.

        Args:
            thread_id: Unique identifier for the thread
            run_id: Unique identifier for the run
            artifact: Artifact to add
        """
        ...

    def save_run_summary(self, thread_id: str, run_summary: RunSummary) -> None:
        """Save a run summary to the thread.

        Args:
            thread_id: Unique identifier for the thread
            run_summary: Summary of the completed run with artifacts
        """
        ...

    def thread_exists(self, thread_id: str) -> bool:
        """Check if a thread exists.

        Args:
            thread_id: Unique identifier for the thread

        Returns:
            True if thread has any saved runs, False otherwise
        """
        ...

    def add_message(self, thread_id: str, message: StoredMessage) -> None:
        """Persist a message to the thread history.

        Args:
            thread_id: Unique identifier for the thread
            message: The message to store
        """
        ...

    def get_messages(self, thread_id: str) -> List[StoredMessage]:
        """Get full message history for a thread.

        Args:
            thread_id: Unique identifier for the thread

        Returns:
            List of stored messages in chronological order
        """
        ...

    def set_metadata(self, thread_id: str, key: str, value: Any) -> None:
        """Store arbitrary metadata for a thread (e.g. active agent).

        Args:
            thread_id: Unique identifier for the thread
            key: Metadata key
            value: Metadata value (must be JSON serializable)
        """
        ...

    def get_metadata(self, thread_id: str, key: str) -> Optional[Any]:
        """Retrieve metadata for a thread.

        Args:
            thread_id: Unique identifier for the thread
            key: Metadata key

        Returns:
            The stored value or None if not found
        """
        ...