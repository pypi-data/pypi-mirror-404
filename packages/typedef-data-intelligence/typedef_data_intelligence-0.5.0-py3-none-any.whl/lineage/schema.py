from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping


@dataclass(slots=True)
class GraphEndpoint:
    label: str
    identity_key: str
    identity_value: str

    def to_match_clause(self, variable: str) -> str:
        return f"({variable}:{self.label} {{{self.identity_key}: $${variable}_{self.identity_key}}})"

    def parameter_dict(self, variable: str) -> Dict[str, str]:
        return {f"{variable}_{self.identity_key}": self.identity_value}


@dataclass(slots=True)
class GraphNode:
    label: str
    identity_key: str
    properties: Dict[str, object]

    def __post_init__(self) -> None:
        if self.identity_key not in self.properties:
            raise ValueError(
                f"Identity key '{self.identity_key}' missing from properties for label '{self.label}'"
            )

    @property
    def identity_value(self) -> str:
        value = self.properties[self.identity_key]
        if not isinstance(value, str):
            raise TypeError(
                f"Identity property '{self.identity_key}' for node '{self.label}' must be a string"
            )
        return value


@dataclass(slots=True)
class GraphEdge:
    type: str
    start: GraphEndpoint
    end: GraphEndpoint
    properties: Dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class GraphSchema:
    node_requirements: Mapping[str, Iterable[str]]
    edge_requirements: Mapping[str, Iterable[str]]

    def validate_node(self, node: GraphNode) -> None:
        required = set(self.node_requirements.get(node.label, []))
        missing = [key for key in required if key not in node.properties]
        if missing:
            raise ValueError(
                f"Node '{node.label}' missing required properties: {', '.join(missing)}"
            )

    def validate_edge(self, edge: GraphEdge) -> None:
        required = set(self.edge_requirements.get(edge.type, []))
        missing = [key for key in required if key not in edge.properties]
        if missing:
            raise ValueError(
                f"Edge '{edge.type}' missing required properties: {', '.join(missing)}"
            )


UNIFIED_SCHEMA = GraphSchema(
    node_requirements={
        # dbt lineage
        "Model": ("dbt_unique_id", "name", "materialization"),
        "Source": ("dbt_unique_id", "name"),
        "Seed": ("dbt_unique_id", "name"),
        "Column": ("id", "name", "parent_id"),
        "LineageSnapshot": ("id", "generated_at"),
        # OpenLineage
        "Job": ("id", "name", "namespace", "job_type"),
        "Dataset": ("id", "name", "namespace"),
        "Run": ("run_id", "job_id", "status", "start_time"),
        "Error": ("error_signature", "error_type", "pattern"),
    },
    edge_requirements={
        # dbt lineage
        "DEPENDS_ON": ("type",),
        "DERIVES_FROM": ("confidence",),
        "MATERIALIZES": ("relation_name",),
        # OpenLineage
        "READS": ("run_id",),
        "WRITES": ("run_id",),
        "TRIGGERS": (),
        "INSTANCE_OF": (),
        "HAS_ERROR": ("occurred_at",),
        "BLOCKS": (),
        # Bridging
        "SAME_AS": ("confidence",),
        "EXECUTES": (),
    },
)



