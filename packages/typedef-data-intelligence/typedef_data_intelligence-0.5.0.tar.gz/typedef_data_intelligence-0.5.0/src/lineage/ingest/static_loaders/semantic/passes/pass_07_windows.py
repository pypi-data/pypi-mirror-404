"""Pass 7: Window Analysis - analyzes window functions per scope."""

from typing import List

import fenic as fc

from lineage.ingest.config import PipelineConfig

from ..prompts import WINDOW_EXTRACTION_PROMPT
from .base import BasePass
from .pass_06_time import get_valid_aliases_for_scope


class WindowAnalysisPass(BasePass):
    """Extract window function specifications per scope."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        """Initialize window analysis pass."""
        super().__init__(session, "window_analysis", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(
            df,
            ["canonical_sql", "relation_analysis", "column_analysis", "time_by_scope"],
        )

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Extract window functions per scope."""
        self.validate_inputs(df)

        # Re-explode by scope (from time_by_scope)
        df_exploded = df.explode("time_by_scope")
        df_exploded = df_exploded.with_column(
            "current_scope", fc.col("time_by_scope")["scope"]
        )

        # Get valid aliases for each scope
        df_exploded = df_exploded.with_column(
            "valid_aliases",
            get_valid_aliases_for_scope(
                fc.col("relation_analysis"), fc.col("current_scope")
            ),
        )

        # Analyze windows for each scope - get JSON string directly
        # Modified prompt to request JSON output directly as string
        json_prompt = (
            WINDOW_EXTRACTION_PROMPT
            + """

Output your response as valid JSON matching this structure:
{
  "windows": [
    {
      "func": "function_name",
      "partition_by": ["col1", "col2"],
      "order_by": ["col1 DESC"],
      "frame": "frame_clause or empty string"
    }
  ]
}

If no window functions exist, return: {"windows": []}
"""
        )

        df_exploded = df_exploded.with_column(
            "window_json",
            fc.semantic.map(
                json_prompt,
                scope=fc.col("current_scope"),
                valid_aliases=fc.col("valid_aliases"),
                column_analysis=fc.col("column_analysis"),
                canonical_sql=fc.col("canonical_sql"),
                max_output_tokens=self.pipeline_config.pass_07.max_output_tokens,
                model_alias=self.pipeline_config.pass_07.model,
                request_timeout=300,
            ),
        ).drop("valid_aliases")

        # Group back and add window results - using JSON strings directly
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
            "time_by_scope",
        ).agg(
            fc.collect_list(
                fc.struct(
                    fc.col("current_scope").alias("scope"),
                    fc.col("window_json").alias("window_analysis_json"),
                )
            ).alias("window_by_scope")
        )

        return df_grouped

    def get_required_passes(self) -> List[str]:
        """Requires time analysis."""
        return ["time_analysis"]
