"""Pass 8: Output Shape Analysis - analyzes ORDER BY, LIMIT, DISTINCT per scope."""

from typing import List

import fenic as fc

from lineage.ingest.config import PipelineConfig

from ..models import OutputShapeAnalysis
from ..prompts import OUTPUT_SHAPE_PROMPT
from .base import BasePass


class OutputShapeAnalysisPass(BasePass):
    """Extract output shape information per scope."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        """Initialize output shape analysis pass."""
        super().__init__(session, "output_shape_analysis", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(df, ["canonical_sql", "window_by_scope"])

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Extract output shape per scope."""
        self.validate_inputs(df)

        # Re-explode by scope (from window_by_scope)
        df_exploded = df.explode("window_by_scope")
        df_exploded = df_exploded.with_column(
            "current_scope", fc.col("window_by_scope")["scope"]
        )

        # Analyze output shape for each scope
        df_exploded = df_exploded.with_column(
            "output_for_scope",
            fc.semantic.map(
                OUTPUT_SHAPE_PROMPT,
                response_format=OutputShapeAnalysis,
                scope=fc.col("current_scope"),
                canonical_sql=fc.col("canonical_sql"),
                max_output_tokens=self.pipeline_config.pass_08.max_output_tokens,
                model_alias=self.pipeline_config.pass_08.model,
                request_timeout=300,
            ),
        )

        # Group back and add output results
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
            "window_by_scope",
        ).agg(
            fc.collect_list(
                fc.struct(
                    fc.col("current_scope").alias("scope"), fc.col("output_for_scope")
                )
            ).alias("output_by_scope")
        )

        return df_grouped

    def get_required_passes(self) -> List[str]:
        """Requires window analysis."""
        return ["window_analysis"]
