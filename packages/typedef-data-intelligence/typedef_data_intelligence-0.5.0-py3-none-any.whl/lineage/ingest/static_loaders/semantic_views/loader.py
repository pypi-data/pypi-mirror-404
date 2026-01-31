"""Generic semantic view loader for lineage graph.

This loader is provider-agnostic and works with any NativeSemanticModelProvider
(Snowflake, Databricks, BigQuery, etc.).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

from lineage.backends.lineage.models.base import NodeIdentifier
from lineage.backends.lineage.models.edges import (
    DrawsFrom,
    HasDimension,
    HasFact,
    HasMeasure,
    HasSemanticTable,
)
from lineage.backends.lineage.models.semantic_views import (
    NativeBaseTable,
    NativeDimension,
    NativeFact,
    NativeMeasure,
    NativeSemanticModelData,
)
from lineage.backends.types import NodeLabel

if TYPE_CHECKING:
    from lineage.backends.data_query.protocol import DataQueryBackend
    from lineage.backends.lineage.models.semantic_views import NativeSemanticModel
    from lineage.backends.lineage.protocol import LineageStorage

class SemanticViewLoader:
    """Generic loader for semantic views from any data warehouse provider.

    This loader is provider-agnostic. It takes a DataQueryBackend
    (Snowflake, Databricks, etc.) and loads semantic views into the
    lineage graph with DRAWS_FROM edges to Model nodes.
    """

    def __init__(self, storage: LineageStorage):
        """Initialize the semantic view loader.

        Args:
            storage: LineageStorage implementation
        """
        self.storage = storage

    def load_semantic_views(
        self,
        provider: DataQueryBackend,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        verbose: bool = False,
    ) -> int:
        """Load all semantic views from a provider into the lineage graph.

        Args:
            provider: DataQueryBackend implementation (Snowflake, Databricks, etc.)
            database: Database name
            schema: Schema name
            verbose: Enable verbose output

        Returns:
            Number of semantic views successfully loaded
        """
        if verbose:
            print(f"🔍 Fetching semantic views from {provider.get_backend_type().value} ({database}.{schema})...")

        # Fetch semantic views from the provider
        semantic_views = asyncio.run(provider.get_semantic_views(database, schema))

        if not semantic_views:
            if verbose:
                print("   No semantic views found")
            return 0

        if verbose:
            print(f"   Found {len(semantic_views)} semantic views")

        # Load each view
        loaded_count = 0
        for data in semantic_views:
            try:
                self._load_single_view(data, verbose)
                loaded_count += 1
            except Exception as e:
                if verbose:
                    print(f"   ⚠️  Failed to load {data.model.name}: {e}")

        return loaded_count

    def _load_single_view(
        self,
        data: NativeSemanticModelData,
        verbose: bool = False,
    ) -> None:
        """Load a single semantic view into the graph.

        This method decomposes the DTO into individual nodes and edges:
        1. Creates/updates the NativeSemanticModel node (flat)
        2. Creates individual NativeMeasure nodes linked to the view
        3. Creates individual NativeDimension nodes linked to the view
        4. Creates individual NativeFact nodes linked to the view
        5. Creates DRAWS_FROM edges from view to underlying models

        Args:
            data: NativeSemanticModelData DTO with view node + components
            verbose: Enable verbose output
        """
        if verbose:
            print(f"   📊 Loading {data.model.name}...")

        # Upsert the NativeSemanticModel node (flat, no nested data)
        self.storage.upsert_node(data.model)

        # Create individual NativeMeasure nodes and link them
        if data.measures:
            self._create_measure_nodes(data.model, data.measures, verbose)

        # Create individual NativeDimension nodes and link them
        if data.dimensions:
            self._create_dimension_nodes(data.model, data.dimensions, verbose)

        # Create individual NativeFact nodes and link them
        if data.facts:
            self._create_fact_nodes(data.model, data.facts, verbose)

        # Create individual NativeBaseTable nodes and link them
        if data.tables:
            self._create_table_nodes(data.model, data.tables, verbose)

        # Link to underlying models using base_tables metadata
        if data.tables:
            self._link_view_to_models(data.model, data.tables, verbose)

    def _create_measure_nodes(
        self,
        view: NativeSemanticModel,
        measures: list[NativeMeasure],
        verbose: bool = False,
    ) -> None:
        """Create individual NativeMeasure nodes and link them to the view.

        Args:
            view: The NativeSemanticModel node
            measures: List of NativeMeasure Pydantic models
            verbose: Enable verbose output
        """
        for measure in measures:
            # Upsert the NativeMeasure node - just pass the node directly!
            self.storage.upsert_node(measure)

            # Create typed edge from NativeSemanticModel to NativeMeasure
            edge = HasMeasure()
            self.storage.create_edge(view, measure, edge)

            if verbose:
                print(f"       ✓ Created measure: {measure.name} ({measure.aggregation})")

    def _create_dimension_nodes(
        self,
        view: NativeSemanticModel,
        dimensions: list[NativeDimension],
        verbose: bool = False,
    ) -> None:
        """Create individual NativeDimension nodes and link them to the view.

        Args:
            view: The NativeSemanticModel node
            dimensions: List of NativeDimension Pydantic models
            verbose: Enable verbose output
        """
        for dimension in dimensions:
            # Upsert the NativeDimension node - just pass the node directly!
            self.storage.upsert_node(dimension)

            # Create typed edge from NativeSemanticModel to NativeDimension
            edge = HasDimension()
            self.storage.create_edge(view, dimension, edge)

            if verbose:
                time_label = " [TIME]" if dimension.is_time_dimension else ""
                print(f"       ✓ Created dimension: {dimension.name}{time_label}")

    def _create_fact_nodes(
        self,
        view: NativeSemanticModel,
        facts: list[NativeFact],
        verbose: bool = False,
    ) -> None:
        """Create individual NativeFact nodes and link them to the view.

        Args:
            view: The NativeSemanticModel node
            facts: List of NativeFact Pydantic models
            verbose: Enable verbose output
        """
        for fact in facts:
            # Upsert the NativeFact node - just pass the node directly!
            self.storage.upsert_node(fact)

            # Create typed edge from NativeSemanticModel to NativeFact
            edge = HasFact()
            self.storage.create_edge(view, fact, edge)

            if verbose:
                print(f"       ✓ Created fact: {fact.name}")
    
    def _create_table_nodes(
        self,
        view: NativeSemanticModel,
        tables: list[NativeBaseTable],
        verbose: bool = False,
    ) -> None:
        """Create individual NativeBaseTable nodes and link them to the view."""
        for table in tables:
            # Upsert the NativeBaseTable node - just pass the node directly!
            self.storage.upsert_node(table)

            # Create typed edge from NativeSemanticModel to NativeBaseTable
            edge = HasSemanticTable()
            self.storage.create_edge(view, table, edge)

            if verbose:
                print(f"       ✓ Created semantic table: {table.name}")

    def _link_view_to_models(
        self,
        view: NativeSemanticModel,
        base_tables: list[NativeBaseTable],
        verbose: bool = False,
    ) -> None:
        """Link semantic view to models based on base_tables metadata.

        Args:
            view: The NativeSemanticModel node
            base_tables: List of NativeBaseTable objects
            verbose: Enable verbose output
        """
        if not base_tables:
            if verbose:
                print("       No base tables found in semantic view metadata")
            return

        linked_count = 0
        for base_table in base_tables:
            # Find model by relation_name (case-insensitive matching)
            model_id = self.storage.find_model_for_physical_table(f"{base_table.base_table_database_name}.{base_table.base_table_schema_name}.{base_table.base_table_name}")

            if not model_id:
                if verbose:
                    print(f"       ⚠️  No model found for {base_table.base_table_name}")
                continue

            to_node = NodeIdentifier(id=model_id, node_label=NodeLabel.DBT_MODEL) # Use identifier since we only have model_id
            self.storage.create_edge(view, to_node, DrawsFrom())

            linked_count += 1

            if verbose:
                print(f"       ✓ Linked to {model_id}")

        if verbose and linked_count > 0:
            print(f"       Created {linked_count} DRAWS_FROM edges")
