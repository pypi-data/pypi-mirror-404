"""Memory observer for automatic pattern capture.

This module provides utilities for automatically capturing and storing
discovered patterns in agent memory. Patterns can be extracted from:
- Successful query results
- Graph query insights
- Semantic view relationships
- Data quality findings

The observer is designed to be lightweight and non-intrusive - if pattern
storage fails, it logs a warning but doesn't interrupt agent execution.
"""

from __future__ import annotations

import logging
from typing import Optional, List

from lineage.backends.memory.protocol import MemoryStorage
from lineage.backends.memory.models import DataPattern, Episode, EpisodeType

logger = logging.getLogger(__name__)


class MemoryObserver:
    """Observer for automatic pattern capture in agent workflows.

    This class provides utilities to automatically extract and store
    patterns discovered during agent execution, without requiring explicit
    tool calls from the agent.

    Example:
        ```python
        observer = MemoryObserver(memory_backend=memory)

        # After executing a semantic view query
        observer.observe_semantic_query(
            org_id="acme_corp",
            view_name="sv_arr_reporting",
            query_pattern="Group by customer, product",
            discovered_by="analyst_agent"
        )

        # After discovering a common join
        observer.observe_join_pattern(
            org_id="acme_corp",
            models=["fct_arr", "dim_customers"],
            join_condition="customer_id",
            discovered_by="data_engineer_agent"
        )
        ```

    Note:
        All methods fail silently with warnings - never interrupts agent flow.
    """

    def __init__(self, memory_backend: Optional[MemoryStorage] = None):
        """Initialize memory observer.

        Args:
            memory_backend: Optional memory backend for storing patterns
        """
        self.memory_backend = memory_backend
        self.enabled = memory_backend is not None

        if not self.enabled:
            logger.debug("MemoryObserver initialized but disabled (no memory backend)")

    def observe_semantic_query(
        self,
        org_id: str,
        view_name: str,
        query_pattern: str,
        dimensions: Optional[List[str]] = None,
        measures: Optional[List[str]] = None,
        discovered_by: str = "agent",
    ) -> None:
        """Observe and record a semantic view query pattern.

        Automatically stores patterns like:
        - Common dimension groupings
        - Frequently used measures
        - Filter patterns

        Args:
            org_id: Organization identifier
            view_name: Semantic view name
            query_pattern: Human-readable query pattern description
            dimensions: Dimensions used in the query
            measures: Measures used in the query
            discovered_by: Agent or user who discovered this pattern
        """
        if not self.enabled:
            return

        try:
            pattern = DataPattern(
                pattern_type="query_pattern",
                pattern_name=f"{view_name}_query",
                description=f"Common query on {view_name}: {query_pattern}",
                models_involved=[view_name],
                example_usage=query_pattern,
                discovered_by=discovered_by,
                confidence=0.7,  # Lower confidence for auto-captured patterns
            )
            episode = pattern.to_episode()

            # Add additional metadata
            if dimensions:
                episode.metadata["dimensions"] = dimensions
            if measures:
                episode.metadata["measures"] = measures

            self.memory_backend.store_org_memory(org_id=org_id, episode=episode)
            logger.debug(
                f"Stored query pattern: view={view_name}, pattern={query_pattern}"
            )

        except Exception as e:
            logger.warning(f"Failed to store semantic query pattern: {e}")

    def observe_join_pattern(
        self,
        org_id: str,
        models: List[str],
        join_condition: str,
        discovered_by: str = "agent",
    ) -> None:
        """Observe and record a join pattern between models.

        Args:
            org_id: Organization identifier
            models: List of models involved in the join (usually 2)
            join_condition: Join condition (e.g., "customer_id", "USING (order_id)")
            discovered_by: Agent or user who discovered this pattern
        """
        if not self.enabled:
            return

        try:
            pattern_name = "_to_".join(models)
            pattern = DataPattern(
                pattern_type="common_join",
                pattern_name=pattern_name,
                description=f"Common join between {', '.join(models)} on {join_condition}",
                models_involved=models,
                example_usage=f"JOIN {models[1]} ON {join_condition}",
                discovered_by=discovered_by,
                confidence=0.8,
            )
            episode = pattern.to_episode()
            episode.metadata["join_condition"] = join_condition

            self.memory_backend.store_org_memory(org_id=org_id, episode=episode)
            logger.debug(f"Stored join pattern: {models} on {join_condition}")

        except Exception as e:
            logger.warning(f"Failed to store join pattern: {e}")

    def observe_metric_definition(
        self,
        org_id: str,
        metric_name: str,
        calculation: str,
        source_model: str,
        discovered_by: str = "agent",
    ) -> None:
        """Observe and record a business metric definition.

        Args:
            org_id: Organization identifier
            metric_name: Name of the metric (e.g., "ARR", "MRR", "Churn")
            calculation: How the metric is calculated
            source_model: Source model/table for the metric
            discovered_by: Agent or user who discovered this definition
        """
        if not self.enabled:
            return

        try:
            pattern = DataPattern(
                pattern_type="metric_definition",
                pattern_name=metric_name,
                description=f"{metric_name} is calculated as: {calculation}",
                models_involved=[source_model],
                example_usage=calculation,
                discovered_by=discovered_by,
                confidence=0.9,  # Higher confidence for explicit definitions
            )
            episode = pattern.to_episode()
            episode.metadata["metric_name"] = metric_name
            episode.metadata["calculation"] = calculation

            self.memory_backend.store_org_memory(org_id=org_id, episode=episode)
            logger.debug(f"Stored metric definition: {metric_name}")

        except Exception as e:
            logger.warning(f"Failed to store metric definition: {e}")

    def observe_data_quality_issue(
        self,
        org_id: str,
        issue_type: str,
        description: str,
        affected_models: List[str],
        discovered_by: str = "agent",
    ) -> None:
        """Observe and record a data quality pattern/issue.

        Args:
            org_id: Organization identifier
            issue_type: Type of issue (e.g., "null_values", "duplicates", "outliers")
            description: Description of the issue
            affected_models: Models affected by this issue
            discovered_by: Agent or user who discovered this issue
        """
        if not self.enabled:
            return

        try:
            pattern = DataPattern(
                pattern_type="data_quality_issue",
                pattern_name=f"{issue_type}_issue",
                description=description,
                models_involved=affected_models,
                discovered_by=discovered_by,
                confidence=0.85,
            )
            episode = pattern.to_episode()
            episode.metadata["issue_type"] = issue_type

            self.memory_backend.store_org_memory(org_id=org_id, episode=episode)
            logger.debug(f"Stored data quality issue: {issue_type}")

        except Exception as e:
            logger.warning(f"Failed to store data quality issue: {e}")

    def observe_custom_pattern(
        self,
        org_id: str,
        pattern_type: str,
        pattern_name: str,
        description: str,
        models_involved: List[str],
        discovered_by: str = "agent",
        confidence: float = 0.75,
    ) -> None:
        """Observe and record a custom pattern.

        Use this for patterns that don't fit the predefined categories.

        Args:
            org_id: Organization identifier
            pattern_type: Custom pattern type
            pattern_name: Name of the pattern
            description: Description of the pattern
            models_involved: Models involved in this pattern
            discovered_by: Agent or user who discovered this pattern
            confidence: Confidence score (0-1)
        """
        if not self.enabled:
            return

        try:
            pattern = DataPattern(
                pattern_type=pattern_type,
                pattern_name=pattern_name,
                description=description,
                models_involved=models_involved,
                discovered_by=discovered_by,
                confidence=confidence,
            )
            episode = pattern.to_episode()

            self.memory_backend.store_org_memory(org_id=org_id, episode=episode)
            logger.debug(f"Stored custom pattern: {pattern_name} ({pattern_type})")

        except Exception as e:
            logger.warning(f"Failed to store custom pattern: {e}")


__all__ = ["MemoryObserver"]
