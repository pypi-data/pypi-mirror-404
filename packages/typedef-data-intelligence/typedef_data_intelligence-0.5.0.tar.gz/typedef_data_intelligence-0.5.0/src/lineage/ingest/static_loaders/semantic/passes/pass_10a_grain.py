"""Pass 10a: Grain Humanization - converts technical grain to human-readable format."""

from typing import List

import fenic as fc
from fenic.api.functions import udf
from fenic.core.types import ArrayType, StringType

from lineage.ingest.config import PipelineConfig

from ..models import GrainHumanization
from ..prompts import GRAIN_HUMANIZATION_PROMPT
from .base import BasePass


class GrainHumanizationPass(BasePass):
    """Convert technical grain keys to human-readable format."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        super().__init__(session, "grain_humanization", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(df, ["grouping_by_scope", "business_semantics"])

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Humanize the grain description."""
        self.validate_inputs(df)

        # Extract outer scope result_grain and measure names
        # First, filter to get the outer scope entry
        def normalize_expression(expr):
            """Normalize function-wrapped expressions."""
            import re

            if not expr:
                return expr

            # Strip common function wrappers
            # SUBSTRING(col, ...) -> col
            pattern = r"^SUBSTRING\s*\(\s*([^,]+),.*\)$"
            match = re.match(pattern, expr, re.IGNORECASE)
            if match:
                return match.group(1).strip()

            # LOWER/UPPER(col) -> col
            pattern = r"^(?:LOWER|UPPER)\s*\(\s*([^)]+)\s*\)$"
            match = re.match(pattern, expr, re.IGNORECASE)
            if match:
                return match.group(1).strip()

            # DATE_TRUNC('period', col) -> col
            pattern = r"^DATE_TRUNC\s*\([^,]+,\s*([^)]+)\s*\)$"
            match = re.match(pattern, expr, re.IGNORECASE)
            if match:
                return match.group(1).strip()

            # CAST(col AS type) -> col
            pattern = r"^CAST\s*\(\s*([^)]+)\s+AS\s+[^)]+\s*\)$"
            match = re.match(pattern, expr, re.IGNORECASE)
            if match:
                return match.group(1).strip()

            return expr

        @udf(return_type=ArrayType(StringType))
        def get_outer_result_grain(grouping_by_scope, business_semantics):
            """Extract grain candidates with proper fallback logic."""
            try:
                if not grouping_by_scope:
                    # Fallback to business_semantics grain_keys
                    if business_semantics and isinstance(business_semantics, dict):
                        grain_keys = business_semantics.get("grain_keys", [])
                        if grain_keys and isinstance(grain_keys, list):
                            return [normalize_expression(k) for k in grain_keys if k]
                    return []

                # Ensure grouping_by_scope is a list
                if not isinstance(grouping_by_scope, list):
                    return []

                for scope_data in grouping_by_scope:
                    if isinstance(scope_data, dict) and scope_data.get("scope") == "outer":
                        # Try both possible keys: grouping_for_scope and analysis
                        grouping_data = scope_data.get(
                            "grouping_for_scope"
                        ) or scope_data.get("analysis", {})

                        if grouping_data and isinstance(grouping_data, dict):
                            is_aggregated = grouping_data.get("is_aggregated", False)

                            if is_aggregated:
                                # Use GROUP BY columns for aggregated queries
                                group_by = grouping_data.get("group_by", [])
                                if group_by and isinstance(group_by, list):
                                    return [normalize_expression(g) for g in group_by if g]
                                # Fallback to result_grain
                                result_grain = grouping_data.get("result_grain", [])
                                if result_grain and isinstance(result_grain, list):
                                    return [normalize_expression(r) for r in result_grain if r]
                            else:
                                # For non-aggregated, use non-aggregate SELECT items
                                # Use the measures list to identify aggregate expressions
                                select_items = grouping_data.get("select", [])
                                measures = set(grouping_data.get("measures", []))
                                if select_items and isinstance(select_items, list):
                                    non_measure_items = []
                                    for item in select_items:
                                        if isinstance(item, dict):
                                            expr = item.get("expr", "")
                                            # Skip if this expression is in the measures list
                                            if expr and expr not in measures:
                                                normalized = normalize_expression(expr)
                                                non_measure_items.append(normalized)
                                    if non_measure_items:
                                        return non_measure_items

                # Final fallback to business_semantics grain_keys
                if business_semantics and isinstance(business_semantics, dict):
                    grain_keys = business_semantics.get("grain_keys", [])
                    if grain_keys and isinstance(grain_keys, list):
                        return [normalize_expression(k) for k in grain_keys if k]
                return []
            except Exception:
                # If any error occurs, return empty list to maintain consistent type
                return []

        @udf(return_type=ArrayType(StringType))
        def get_measure_names(business_semantics):
            try:
                if not business_semantics:
                    return []
                if (
                    isinstance(business_semantics, dict)
                    and "measures" in business_semantics
                ):
                    measures = business_semantics.get("measures", [])
                    if isinstance(measures, list):
                        return [
                            m.get("name")
                            for m in measures
                            if isinstance(m, dict) and "name" in m and m.get("name")
                        ]
                return []
            except Exception:
                # If any error occurs, return empty list to maintain consistent type
                return []

        df = df.with_column(
            "result_grain",
            get_outer_result_grain(
                fc.col("grouping_by_scope"), fc.col("business_semantics")
            ),
        ).with_column("measure_names", get_measure_names(fc.col("business_semantics")))

        # Humanize the grain
        df = df.with_column(
            "grain_humanization",
            fc.semantic.map(
                GRAIN_HUMANIZATION_PROMPT,
                response_format=GrainHumanization,
                result_grain=fc.col("result_grain"),
                measure_names=fc.col("measure_names"),
                model_alias=self.pipeline_config.pass_10a.model,
                max_output_tokens=self.pipeline_config.pass_10a.max_output_tokens,
                request_timeout=300,
            ),
        )

        # Drop temporary columns
        df = df.drop("result_grain", "measure_names")

        return df

    def get_required_passes(self) -> List[str]:
        """Requires business semantics."""
        return ["business_semantics"]
