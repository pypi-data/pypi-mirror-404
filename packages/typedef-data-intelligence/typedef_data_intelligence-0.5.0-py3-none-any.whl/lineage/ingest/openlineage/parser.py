from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict

from .models import OpenLineageEvent


@dataclass
class ParsedJob:
    id: str
    name: str
    namespace: str
    job_type: str
    metadata: Dict


@dataclass
class ParsedDataset:
    id: str
    name: str
    namespace: str
    dataset_type: str
    metadata: Dict


@dataclass
class ParsedRun:
    run_id: str
    job_id: str
    status: str
    start_time: str
    end_time: Optional[str]
    error_info: Optional[Dict]
    metadata: Dict


@dataclass
class ParsedEvent:
    job: ParsedJob
    run: ParsedRun
    input_datasets: List[ParsedDataset]
    output_datasets: List[ParsedDataset]


class OpenLineageParser:
    def parse_event(self, event: OpenLineageEvent) -> ParsedEvent:
        job = self._parse_job(event.job)
        # Convert EventType enum to string value
        event_type_str = event.eventType.value if hasattr(event.eventType, 'value') else str(event.eventType)
        run = self._parse_run(event.run, job.id, event_type_str, event.eventTime)
        inputs = [self._parse_dataset(d, "input") for d in event.inputs]
        outputs = [self._parse_dataset(d, "output") for d in event.outputs]
        return ParsedEvent(job=job, run=run, input_datasets=inputs, output_datasets=outputs)

    def _parse_job(self, job_facet) -> ParsedJob:
        job_type = self._infer_job_type(job_facet.namespace)
        return ParsedJob(
            id=f"{job_facet.namespace}::{job_facet.name}",
            name=job_facet.name,
            namespace=job_facet.namespace,
            job_type=job_type,
            metadata=job_facet.facets,
        )

    def _parse_run(self, run_facet, job_id: str, event_type: str, event_time: str) -> ParsedRun:
        error_info = None
        if event_type in ["FAIL", "ABORT"]:
            error_info = run_facet.facets.get("errorMessage", {})
        end_time = event_time if event_type in ["COMPLETE", "FAIL", "ABORT"] else None
        return ParsedRun(
            run_id=run_facet.runId,
            job_id=job_id,
            status=event_type,
            start_time=event_time,
            end_time=end_time,
            error_info=error_info,
            metadata=run_facet.facets,
        )

    def _parse_dataset(self, dataset_facet, direction: str) -> ParsedDataset:
        return ParsedDataset(
            id=f"{dataset_facet.namespace}::{dataset_facet.name}",
            name=dataset_facet.name,
            namespace=dataset_facet.namespace,
            dataset_type=self._infer_dataset_type(dataset_facet.namespace),
            metadata={"direction": direction, **dataset_facet.facets},
        )

    def _infer_job_type(self, namespace: str) -> str:
        ns = namespace.lower()
        if "airflow" in ns:
            return "airflow"
        if "spark" in ns:
            return "spark"
        if "dbt" in ns:
            return "dbt"
        if "flink" in ns:
            return "flink"
        return "unknown"

    def _infer_dataset_type(self, namespace: str) -> str:
        ns = namespace.lower()
        if any(x in ns for x in ("snowflake", "duckdb", "postgres")):
            return "table"
        if any(x in ns for x in ("s3", "gcs")):
            return "file"
        if "kafka" in ns:
            return "stream"
        return "unknown"



