"""Pydantic models for OpenLineage nodes (jobs, datasets, runs, errors).

These models represent runtime/operational metadata from OpenLineage events:
- Job: Executable units (dbt jobs, Airflow tasks, etc.)
- Dataset: Data assets read/written by jobs
- Run: Job executions with status and timing
- Error: Recurring error patterns across runs
"""

from typing import Any, ClassVar, Dict, Optional

from pydantic import Field, computed_field

from lineage.backends.lineage.models.base import BaseNode, NodeIdentifier
from lineage.backends.types import NodeLabel


class Job(BaseNode):
    """OpenLineage job node.

    Represents an executable unit like a dbt model run, Airflow task,
    Spark job, etc.

    The ID is constructed as: job://{namespace}/{name}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.JOB

    # Core properties from OpenLineage spec
    name: str
    namespace: str
    job_type: str  # "dbt", "airflow", "spark", etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: job://{namespace}/{name}."""
        return f"job://{self.namespace}/{self.name}"

    @classmethod
    def identifier(cls, namespace: str, name: str) -> "NodeIdentifier":
        """Create NodeIdentifier from namespace and name.

        Uses the id property to ensure single source of truth for ID format.

        Args:
            namespace: Job namespace
            name: Job name

        Returns:
            NodeIdentifier with correct ID and label

        Example:
            ```python
            identifier = Job.identifier("dbt://demo", "orders_model")
            storage.create_edge(identifier, dataset_id, edge)
            ```
        """
        temp = cls(name=name, namespace=namespace, job_type="")
        return temp.get_node_identifier()


class Dataset(BaseNode):
    """OpenLineage dataset node.

    Represents a data asset (table, file, topic) that is read or written
    by jobs.

    The ID is constructed as: dataset://{namespace}/{name}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.DATASET

    # Core properties from OpenLineage spec
    name: str
    namespace: str
    dataset_type: str  # "table", "file", "topic", etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: dataset://{namespace}/{name}."""
        return f"dataset://{self.namespace}/{self.name}"

    @classmethod
    def identifier(cls, namespace: str, name: str) -> "NodeIdentifier":
        """Create NodeIdentifier from namespace and name.

        Uses the id property to ensure single source of truth for ID format.

        Args:
            namespace: Dataset namespace
            name: Dataset name

        Returns:
            NodeIdentifier with correct ID and label

        Example:
            ```python
            identifier = Dataset.identifier("warehouse://prod", "analytics.orders")
            storage.create_edge(job_id, identifier, edge)
            ```
        """
        temp = cls(name=name, namespace=namespace, dataset_type="")
        return temp.get_node_identifier()

class Run(BaseNode):
    """OpenLineage run node.

    Represents a single execution of a job with status, timing, and
    error information.

    The ID is the run_id from OpenLineage (typically a UUID).
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.RUN

    # Core properties from OpenLineage spec
    name: str  # Run ID (UUID)
    job_id: str  # ID of the parent Job
    status: str  # "RUNNING", "COMPLETED", "FAILED", "ABORTED"
    start_time: str  # ISO 8601 timestamp
    end_time: Optional[str] = None  # ISO 8601 timestamp
    duration_ms: Optional[int] = None  # Run duration in milliseconds
    error_info: Optional[Dict[str, Any]] = None  # Error details if failed
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def id(self) -> str:
        """Run ID is the unique identifier."""
        return self.name

    @classmethod
    def identifier(cls, run_id: str) -> "NodeIdentifier":
        """Create NodeIdentifier from run_id.

        Uses the id property to ensure single source of truth for ID format.

        Args:
            run_id: Run ID (typically a UUID)

        Returns:
            NodeIdentifier with correct ID and label

        Example:
            ```python
            identifier = Run.identifier("550e8400-e29b-41d4-a716-446655440000")
            storage.create_edge(identifier, job_id, edge)
            ```
        """
        temp = cls(name=run_id, job_id="", status="", start_time="")
        return temp.get_node_identifier()

class Error(BaseNode):
    """Recurring error pattern node.

    Aggregates similar errors across multiple runs to identify patterns
    and track resolution.

    The ID is constructed as: error::{error_pattern_hash}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.ERROR

    # Core properties
    name: str  # Error pattern hash or identifier
    error_type: str  # "validation", "schema", "permission", etc.
    pattern: str  # Normalized error pattern
    message: str  # Example error message
    first_seen: str  # ISO 8601 timestamp
    last_seen: str  # ISO 8601 timestamp
    occurrence_count: int  # Number of times this error occurred
    resolution_status: Optional[str] = None  # "unresolved", "investigating", "resolved"

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: error::{name}."""
        return f"error::{self.name}"

    @classmethod
    def identifier(cls, error_name: str) -> "NodeIdentifier":
        """Create NodeIdentifier from error name/hash.

        Uses the id property to ensure single source of truth for ID format.

        Args:
            error_name: Error pattern hash or identifier

        Returns:
            NodeIdentifier with correct ID and label

        Example:
            ```python
            identifier = Error.identifier("connection_timeout_pattern_1")
            storage.create_edge(run_id, identifier, edge)
            ```
        """
        temp = cls(
            name=error_name,
            error_type="",
            pattern="",
            message="",
            first_seen="",
            last_seen="",
            occurrence_count=0
        )
        return temp.get_node_identifier()


__all__ = ["Job", "Dataset", "Run", "Error"]
