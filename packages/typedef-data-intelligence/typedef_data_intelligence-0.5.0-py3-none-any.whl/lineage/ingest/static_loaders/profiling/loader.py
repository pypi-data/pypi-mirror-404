"""Profiling loader - stores data profiling statistics in the lineage graph."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Optional

from lineage.backends.lineage.models.base import NodeIdentifier
from lineage.backends.lineage.models.edges import (
    HasColumnProfile,
    HasProfile,
)
from lineage.backends.lineage.models.profiling import (
    ColumnProfile as ColumnProfileNode,
)
from lineage.backends.lineage.models.profiling import (
    TableProfile as TableProfileNode,
)
from lineage.backends.types import NodeLabel

if TYPE_CHECKING:
    from lineage.backends.data_query.protocol import (
        ColumnProfile,
        DataQueryBackend,
        TableProfile,
    )
    from lineage.backends.lineage.protocol import LineageStorage


class ProfilingLoader:
    """Loads data profiling statistics into the lineage graph."""

    def __init__(self, storage: LineageStorage):
        self.storage = storage

    def load_table_profile(self, model_id: str, profile: TableProfile) -> None:
        """Load a table profile and its column profiles into the graph.

        Args:
            model_id: dbt model unique ID (e.g., "model.demo_finance.fct_revenue")
            profile: TableProfile from data backend profiling
        """
        # Create TableProfile node using Pydantic model
        # Note: The protocol TableProfile dataclass is converted to our graph TableProfile node
        table_profile_node = TableProfileNode(
            name=profile.table_name,
            database_name=profile.database_name,
            schema_name=profile.schema_name,
            table_name=profile.table_name,
            row_count=profile.row_count,
            profiled_at=profile.profile_timestamp or "",
        )

        # Upsert table profile node
        self.storage.upsert_node(table_profile_node)

        # Link model to profile using typed edge
        model_identifier = NodeIdentifier(id=model_id, node_label=NodeLabel.DBT_MODEL)
        self.storage.create_edge(
            model_identifier,
            table_profile_node,
            HasProfile(),
        )

        # Load column profiles
        for col_profile in profile.column_profiles:
            self._load_column_profile(
                table_profile_node.id, model_id, col_profile
            )

    def _load_column_profile(
        self,
        table_profile_id: str,
        model_id: str,
        col_profile: ColumnProfile,
    ) -> None:
        """Load a single column profile into the graph.

        Args:
            table_profile_id: ID of the parent table profile
            model_id: dbt model unique ID (used to construct column ID)
            col_profile: ColumnProfile from data backend profiling (protocol dataclass)
        """
        # Serialize top_values to list of dicts if present
        top_values = []
        if col_profile.top_values:
            # Ensure it's serialized as list of dicts
            top_values = (
                col_profile.top_values
                if isinstance(col_profile.top_values, list)
                else []
            )

        # Convert numeric values to strings for storage
        min_value_str = (
            str(col_profile.min_value) if col_profile.min_value is not None else None
        )
        max_value_str = (
            str(col_profile.max_value) if col_profile.max_value is not None else None
        )
        avg_value_str = (
            str(col_profile.avg_value) if col_profile.avg_value is not None else None
        )

        # Create ColumnProfile node using Pydantic model
        col_profile_node = ColumnProfileNode(
            name=col_profile.column_name,
            column_name=col_profile.column_name,
            data_type=col_profile.data_type,
            null_count=col_profile.null_count or 0,
            distinct_count=col_profile.distinct_count or 0,
            min_value=min_value_str,
            max_value=max_value_str,
            avg_value=avg_value_str,
            top_values=json.dumps(top_values) if top_values else None,
            table_profile_id=table_profile_id,
        )

        # Upsert column profile node
        self.storage.upsert_node(col_profile_node)

        # Link table profile to column profile
        table_profile_identifier = NodeIdentifier(
            id=table_profile_id, node_label=NodeLabel.TABLE_PROFILE
        )
        self.storage.create_edge(
            table_profile_identifier,
            col_profile_node,
            HasColumnProfile(),
        )

        # Link column profile to dbt Column node
        # Column IDs follow pattern: {model_id}.{column_name.lower()}
        # Normalize to lowercase to match dbt loader's column ID pattern
        dbt_column_id = f"{model_id}.{col_profile.column_name.lower()}"
        dbt_column_identifier = NodeIdentifier(
            id=dbt_column_id, node_label=NodeLabel.DBT_COLUMN
        )

        # Reverse: Column → ColumnProfile (ownership/has relationship)
        # Note: We use the same HasProfile edge type for both Model→TableProfile and Column→ColumnProfile
        self.storage.create_edge(
            dbt_column_identifier,
            col_profile_node,
            HasProfile(),
        )

    async def profile_models_parallel(
        self,
        models_to_profile: list,
        data_backend: DataQueryBackend,
        max_workers: int = 10,
        sample_size: Optional[int] = None,
        top_k: int = 10,
        verbose: bool = False,
    ) -> tuple[int, int]:
        """Profile multiple models in parallel using asyncio.

        Since profiling is IO-bound (database queries), we use asyncio
        with a semaphore to run multiple profiles concurrently.

        Args:
            models_to_profile: List of dbt models to profile
            data_backend: DataQueryBackend instance
            max_workers: Maximum concurrent profiling operations (default: 10)
            sample_size: Optional sample size for profiling (None = full table)
            top_k: Number of top values to collect per column (default: 10)
            verbose: Enable verbose output

        Returns:
            Tuple of (profiled_count, failed_count)
        """
        asyncio.get_event_loop()
        semaphore = asyncio.Semaphore(max_workers)

        async def profile_one(idx: int, model, backend: DataQueryBackend) -> tuple[bool, Optional[str]]:
            """Profile a single model. Returns (success, error_message)."""
            async with semaphore:  # Limit concurrency
                model_name = model.name or model.unique_id.split(".")[-1]

                if verbose:
                     print(
                        f"   [{idx}/{len(models_to_profile)}] Profiling {model_name}..."
                    )

                try:
                    profile = await backend.profile_table(
                        model.database or "main",
                        model.schema or "main",
                        model.name,
                        sample_size,
                        top_k,
                    )

                    # Load profile into graph
                    self.load_table_profile(model.unique_id, profile)

                    if verbose:
                        print(f"       Row count: {profile.row_count:,}")
                        print(f"       Columns: {len(profile.column_profiles)}")

                    return True, None

                except Exception as e:
                    if verbose:
                        print(f"       ⚠️  Profiling failed: {e}")
                    return False, str(e)
        profiled_count = 0
        failed_count = 0
        # Create tasks for all models
        async with data_backend as backend:
            results = await asyncio.gather(
                *[profile_one(idx, model, backend) for idx, model in enumerate(models_to_profile, 1)],
                return_exceptions=True,
            )
            
            for result in results:
                # Check if result is an exception
                if isinstance(result, BaseException):
                    failed_count += 1
                # Check if result is a tuple (expected return type from profile_one)
                elif isinstance(result, tuple) and len(result) == 2:
                    if result[0]:  # success
                        profiled_count += 1
                    else:  # failed
                        failed_count += 1
                else:
                    # Unexpected result type, count as failed
                    failed_count += 1

        return profiled_count, failed_count
