"""Thread storage backend with factory function."""

from lineage.backends.config import (
    SQLiteThreadsConfig,
    ThreadsConfig,
)
from lineage.backends.threads.models import Artifact, RunSummary, ThreadContext
from lineage.backends.threads.protocol import ThreadsBackend
from lineage.backends.threads.sqlite import SQLiteThreadsBackend

__all__ = [
    "ThreadsBackend",
    "SQLiteThreadsBackend",
    "Artifact",
    "RunSummary",
    "ThreadContext",
    "create_threads_backend",
]


def create_threads_backend(config: ThreadsConfig) -> ThreadsBackend:
    """Factory function to create a threads backend from config.

    Args:
        config: ThreadsConfig (SQLite only)

    Returns:
        ThreadsBackend instance

    Raises:
        ValueError: If backend type is not supported
    """
    if isinstance(config, SQLiteThreadsConfig):
        return SQLiteThreadsBackend(db_path=config.db_path)

    raise ValueError(f"Unknown threads backend type: {type(config)}")
