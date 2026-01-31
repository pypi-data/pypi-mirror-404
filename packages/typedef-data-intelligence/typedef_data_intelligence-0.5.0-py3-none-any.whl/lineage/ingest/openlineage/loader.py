from __future__ import annotations

import logging
from typing import Optional

from openlineage.client.event_v2 import RunEvent

from lineage.backends.lineage.protocol import LineageStorage
from lineage.backends.lineage.models import Job, Dataset, Run
from lineage.backends.lineage.models.edges import Reads, Writes, InstanceOf
from .parser import OpenLineageParser

logger = logging.getLogger(__name__)


class NamespaceResolver:
    """Resolves and normalizes namespaces from OpenLineage events."""

    def resolve_namespace(self, namespace: str) -> str:
        """Normalize namespace for consistent storage."""
        # Simple pass-through for now, can add mapping logic later
        return namespace.strip().lower()


class OpenLineageLoader:
    """Loads OpenLineage events into the lineage graph."""

    def __init__(self, storage: LineageStorage, resolver: NamespaceResolver):
        self.storage = storage
        self.resolver = resolver
        self.parser = OpenLineageParser()

    def load_event(self, event: RunEvent) -> None:
        """Parse and load an OpenLineage RunEvent into the graph."""
        logger.info(
            "Loading event: type=%s job=%s/%s run=%s",
            event.eventType,
            event.job.namespace,
            event.job.name,
            event.run.runId,
        )

        parsed = self.parser.parse_event(event)

        # Upsert job using Pydantic model
        job_node = Job(
            name=parsed.job.name,
            namespace=self.resolver.resolve_namespace(parsed.job.namespace),
            job_type=parsed.job.job_type,
            metadata=parsed.job.metadata,
        )
        self.storage.upsert_node(job_node)

        # Upsert input datasets and create READS edges
        for ds in parsed.input_datasets:
            dataset_node = Dataset(
                name=ds.name,
                namespace=self.resolver.resolve_namespace(ds.namespace),
                dataset_type=ds.dataset_type,
                metadata=ds.metadata,
            )
            self.storage.upsert_node(dataset_node)

            # Create READS relationship
            from_node = Job.identifier(job_node.namespace, job_node.name)
            to_node = Dataset.identifier(dataset_node.namespace, dataset_node.name)
            edge = Reads(run_id=parsed.run.run_id)
            self.storage.create_edge(from_node, to_node, edge)

        # Upsert output datasets and create WRITES edges
        for ds in parsed.output_datasets:
            dataset_node = Dataset(
                name=ds.name,
                namespace=self.resolver.resolve_namespace(ds.namespace),
                dataset_type=ds.dataset_type,
                metadata=ds.metadata,
            )
            self.storage.upsert_node(dataset_node)

            # Create WRITES relationship
            from_node = Job.identifier(job_node.namespace, job_node.name)
            to_node = Dataset.identifier(dataset_node.namespace, dataset_node.name)
            edge = Writes(run_id=parsed.run.run_id)
            self.storage.create_edge(from_node, to_node, edge)

        # Insert run using Pydantic model
        duration_ms = self._calculate_duration(parsed.run)
        run_node = Run(
            name=parsed.run.run_id,
            job_id=job_node.id,
            status=parsed.run.status,
            start_time=parsed.run.start_time,
            end_time=parsed.run.end_time,
            duration_ms=duration_ms,
            error_info=parsed.run.error_info,
            metadata=parsed.run.metadata,
        )
        self.storage.upsert_node(run_node)

        # Create INSTANCE_OF relationship
        from_node = Run.identifier(parsed.run.run_id)
        to_node = Job.identifier(job_node.namespace, job_node.name)
        edge_id = f"{parsed.run.run_id}::{job_node.id}"
        edge = InstanceOf(edge_id=edge_id)
        self.storage.create_edge(from_node, to_node, edge)

        logger.info("Event loaded successfully: run=%s", parsed.run.run_id)

    def _calculate_duration(self, run) -> Optional[int]:
        """Calculate run duration in milliseconds if both times are available."""
        if not run.end_time or not run.start_time:
            return None

        try:
            from datetime import datetime

            start = datetime.fromisoformat(run.start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(run.end_time.replace("Z", "+00:00"))
            delta = end - start
            return int(delta.total_seconds() * 1000)
        except Exception as exc:
            logger.warning("Failed to calculate duration: %s", exc)
            return None
