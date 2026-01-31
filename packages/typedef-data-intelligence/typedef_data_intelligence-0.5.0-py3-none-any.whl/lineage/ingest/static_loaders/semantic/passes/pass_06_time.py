"""Pass 6: Time Analysis - analyzes time semantics per scope."""

from typing import List

import fenic as fc
from fenic.api.functions import udf
from fenic.core.types import ArrayType, StringType

from lineage.ingest.config import PipelineConfig

from ..models import TimeAnalysis
from ..prompts import TIME_ANALYSIS_PROMPT
from .base import BasePass


@udf(return_type=ArrayType(StringType))
def get_valid_aliases_for_scope(relation_analysis: dict, scope: str) -> List[str]:
    """Get valid aliases for a specific scope from RelationAnalysis."""
    if not relation_analysis or "relations" not in relation_analysis:
        return []

    valid_aliases = []
    for rel in relation_analysis["relations"]:
        if rel.get("scope") == scope:
            valid_aliases.append(rel["alias"])

    return valid_aliases


class TimeAnalysisPass(BasePass):
    """Extract time semantics per scope."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        """Initialize time analysis pass."""
        super().__init__(session, "time_analysis", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(
            df,
            [
                "canonical_sql",
                "relation_analysis",
                "column_analysis",
                "filter_analysis",
                "grouping_by_scope",
            ],
        )

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Extract time information per scope."""
        self.validate_inputs(df)

        # Re-explode by scope (from grouping_by_scope)
        df_exploded = df.explode("grouping_by_scope")
        df_exploded = df_exploded.with_column(
            "current_scope", fc.col("grouping_by_scope")["scope"]
        ).with_column(
            "grouping_for_scope", fc.col("grouping_by_scope")["grouping_for_scope"]
        )

        # Get valid aliases for each scope
        df_exploded = df_exploded.with_column(
            "valid_aliases",
            get_valid_aliases_for_scope(
                fc.col("relation_analysis"), fc.col("current_scope")
            ),
        )

        # Analyze time for each scope using semantic.map
        df_exploded = df_exploded.with_column(
            "time_for_scope",
            fc.semantic.map(
                TIME_ANALYSIS_PROMPT,
                response_format=TimeAnalysis,
                scope=fc.col("current_scope"),
                valid_aliases=fc.col("valid_aliases"),
                column_analysis=fc.col("column_analysis"),
                filter_analysis=fc.col("filter_analysis"),
                grouping_for_scope=fc.col("grouping_for_scope"),
                canonical_sql=fc.col("canonical_sql"),
                max_output_tokens=self.pipeline_config.pass_06.max_output_tokens,
                model_alias=self.pipeline_config.pass_06.model,
                request_timeout=300,
            ),
        ).drop("valid_aliases")

        # Group back and collect time results
        df_grouped = df_exploded.group_by(
            "model_id",
            "model_name",
            "path",
            "filename",
            "sql",
            "canonical_sql",
            "relation_analysis",
            "column_analysis",
            "join_analysis",
            "filter_analysis",
            "grouping_by_scope",
        ).agg(
            fc.collect_list(
                fc.struct(
                    fc.col("current_scope").alias("scope"), fc.col("time_for_scope")
                )
            ).alias("time_by_scope")
        )

        return df_grouped

    def get_required_passes(self) -> List[str]:
        """Requires grouping analysis."""
        return ["grouping_analysis"]
