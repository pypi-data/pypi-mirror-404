"""Base classes for all graph nodes and edges.

This module defines the foundational Pydantic models that all nodes and edges inherit from:
- NodeIdentifier: Lightweight identifier (ID + label) for edge creation
- BaseNode: All graph nodes (DbtModel, Job, SemanticView, etc.)
- GraphEdge: All graph edges with type validation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Union

from pydantic import BaseModel, computed_field

from lineage.backends.types import EdgeType, NodeLabel


@dataclass
class NodeIdentifier:
    """Lightweight node identifier for edge creation.

    When creating edges, we often only have the node ID and label,
    not the full node object. NodeIdentifier provides a clean way
    to specify edge endpoints without creating fake stub nodes.

    Args:
        id: Node unique identifier
        node_label: Node type label

    Example:
        ```python
        # Create edge between nodes we only know by ID
        from_node = NodeIdentifier(id="model.demo.orders", node_label=NodeLabel.DBT_MODEL)
        to_node = NodeIdentifier(id="model.demo.customers", node_label=NodeLabel.DBT_MODEL)
        edge = DependsOn(type="model", direct=True)
        storage.create_edge(from_node, to_node, edge)
        ```
    """
    id: str
    node_label: NodeLabel


class BaseNode(BaseModel):
    """Base class for all graph database nodes.

    All node types inherit from this and must:
    1. Set node_label as a ClassVar
    2. Override the id property to generate unique IDs
    3. Have a name field

    Example:
        ```python
        class DbtModel(BaseNode):
            node_label: ClassVar[NodeLabel] = NodeLabel.DBT_MODEL

            name: str
            database: str
            schema: str

            @computed_field
            @property
            def id(self) -> str:
                return f"model.{self.database}.{self.schema}.{self.name}"
        ```
    """

    node_label: ClassVar[NodeLabel]
    name: str

    @computed_field(repr=True)
    @property
    def search_tokenized_name(self) -> str:
        """Search-only tokenized variant of name for full-text recall."""
        return (self.name or "").replace("_", " ")

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID for this node.

        Must be overridden in subclasses to provide node-specific ID generation.

        Raises:
            NotImplementedError: If not overridden in subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement the id property"
        )

    def get_node_identifier(self) -> NodeIdentifier:
        """Convert this node to a lightweight NodeIdentifier.

        Useful when creating edges where only ID and label are needed.

        Returns:
            NodeIdentifier with this node's ID and label

        Example:
            ```python
            model = DbtModel(name="orders", database="db", schema="schema", ...)
            identifier = model.get_node_identifier()
            # NodeIdentifier(id="model.db.schema.orders", node_label=NodeLabel.DBT_MODEL)
            ```
        """
        return NodeIdentifier(id=self.id, node_label=self.node_label)

    class Config:
        frozen = False  # Allow mutation for post_init injection


class GraphEdge(BaseModel):
    """Base class for all graph edges with pair-based type validation.

    All edge types inherit from this and must:
    1. Set edge_type as a ClassVar
    2. Set allowed_pairs as a list of (from_type, to_type) tuples
    3. Define any edge-specific properties

    Pair-based validation prevents cartesian product issues and enforces
    exact combinations of allowed node types.

    Example:
        ```python
        class DerivesFrom(GraphEdge):
            edge_type: ClassVar[EdgeType] = EdgeType.DERIVES_FROM
            allowed_pairs: ClassVar[list[tuple[type[BaseNode], type[BaseNode]]]] = [
                (DbtColumn, DbtColumn),
                (PhysicalColumn, DbtColumn),
                (InferredMeasure, DbtColumn),
                (InferredDimension, DbtColumn),
            ]

            confidence: Optional[str] = None
            transformation: Optional[str] = None
        ```

    Usage:
        ```python
        edge = DerivesFrom(confidence="high")
        edge.validate_nodes(measure, column)  # Raises TypeError if incompatible
        storage.create_edge(measure, column, edge)
        ```
    """

    edge_type: ClassVar[EdgeType]
    allowed_pairs: ClassVar[list[tuple[type[BaseNode], type[BaseNode]]]]

    def validate_nodes(
        self,
        from_node: Union[BaseNode, NodeIdentifier],
        to_node: Union[BaseNode, NodeIdentifier]
    ) -> None:
        """Validate that the given nodes match an allowed pair for this edge type.

        Validates the specific (from_type, to_type) pair against allowed_pairs.
        Accepts either full BaseNode objects or lightweight NodeIdentifier objects.

        Args:
            from_node: Source node or identifier
            to_node: Target node or identifier

        Raises:
            TypeError: If the node pair is not in allowed_pairs

        Example:
            ```python
            measure = InferredMeasure(name="total_revenue", ...)
            column = DbtColumn(name="revenue", ...)
            edge = DerivesFrom(confidence="high")
            edge.validate_nodes(measure, column)  # OK - (InferredMeasure, DbtColumn) in allowed_pairs

            edge.validate_nodes(measure, measure)  # Raises TypeError - invalid pair
            ```
        """
        # Extract concrete types from nodes (handle both BaseNode and NodeIdentifier)
        if isinstance(from_node, NodeIdentifier):
            from_label = from_node.node_label
            from_type = None  # We'll match by label
        else:
            from_type = type(from_node)
            from_label = from_type.node_label

        if isinstance(to_node, NodeIdentifier):
            to_label = to_node.node_label
            to_type = None  # We'll match by label
        else:
            to_type = type(to_node)
            to_label = to_type.node_label

        # Check if (from_type, to_type) is in allowed_pairs
        valid_pair_found = False

        for allowed_from, allowed_to in self.allowed_pairs:
            # Check if this pair matches
            from_matches = (from_type == allowed_from if from_type else allowed_from.node_label == from_label)
            to_matches = (to_type == allowed_to if to_type else allowed_to.node_label == to_label)

            if from_matches and to_matches:
                valid_pair_found = True
                break

        if not valid_pair_found:
            # Build helpful error message
            valid_pairs = ", ".join(
                f"({from_t.__name__}, {to_t.__name__})"
                for from_t, to_t in self.allowed_pairs
            )
            from_desc = from_type.__name__ if from_type else f"NodeIdentifier({from_label.value})"
            to_desc = to_type.__name__ if to_type else f"NodeIdentifier({to_label.value})"
            raise TypeError(
                f"{self.edge_type.value} edges require node pair to be one of "
                f"[{valid_pairs}], but got ({from_desc}, {to_desc})"
            )


__all__ = ["NodeIdentifier", "BaseNode", "GraphEdge"]
