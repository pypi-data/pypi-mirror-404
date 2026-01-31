"""Pass 9: Audit Analysis - validates all previous passes."""

from typing import List

import fenic as fc

from lineage.ingest.config import PipelineConfig

from ..models import AuditAnalysis
from ..prompts import AUDITOR_PROMPT
from .base import BasePass


class AuditAnalysisPass(BasePass):
    """Audit and validate all previous analysis passes."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        super().__init__(session, "audit_analysis", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(
            df,
            [
                "sql",
                "canonical_sql",
                "relation_analysis",
                "column_analysis",
                "join_analysis",
                "filter_analysis",
                "grouping_by_scope",
                "output_by_scope",
            ],
        )

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Audit all previous passes."""
        self.validate_inputs(df)

        # Run audit
        # Note: time_by_scope and window_by_scope columns always exist
        # (as empty arrays if their passes were skipped)
        df = df.with_column(
            "audit_analysis",
            fc.semantic.map(
                AUDITOR_PROMPT,
                response_format=AuditAnalysis,
                original_sql=fc.col("sql"),
                canonical_sql=fc.col("canonical_sql"),
                relation_analysis=fc.col("relation_analysis"),
                column_analysis=fc.col("column_analysis"),
                join_analysis=fc.col("join_analysis"),
                filter_analysis=fc.col("filter_analysis"),
                grouping_by_scope=fc.col("grouping_by_scope"),
                time_by_scope=fc.col("time_by_scope"),
                window_by_scope=fc.col("window_by_scope"),
                output_by_scope=fc.col("output_by_scope"),
                max_output_tokens=self.pipeline_config.pass_09.max_output_tokens,
                model_alias=self.pipeline_config.pass_09.model,
                request_timeout=600,
            ),
        )

        return df

    def get_required_passes(self) -> List[str]:
        """Requires output shape analysis (which requires all previous)."""
        return ["output_shape_analysis"]
