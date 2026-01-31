"""Pass 10: Business Semantics - extracts business meaning from technical analysis."""

from typing import List

import fenic as fc

from lineage.ingest.config import PipelineConfig

from ..models import BusinessSemantics
from ..prompts import BUSINESS_SEMANTICS_PROMPT
from .base import BasePass


class BusinessSemanticsPass(BasePass):
    """Extract business semantics from technical analysis."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        super().__init__(session, "business_semantics", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(
            df,
            [
                "relation_analysis",
                "column_analysis",
                "join_analysis",
                "filter_analysis",
                "grouping_by_scope",
                "output_by_scope",
            ],
        )

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Extract business semantics focusing on outer scope."""
        self.validate_inputs(df)

        # Extract business semantics
        # Note: time_by_scope column always exists (as empty array if time pass was skipped)
        df = df.with_column(
            "business_semantics",
            fc.semantic.map(
                BUSINESS_SEMANTICS_PROMPT,
                response_format=BusinessSemantics,
                relation_analysis=fc.col("relation_analysis"),
                column_analysis=fc.col("column_analysis"),
                join_analysis=fc.col("join_analysis"),
                filter_analysis=fc.col("filter_analysis"),
                grouping_by_scope=fc.col("grouping_by_scope"),
                time_by_scope=fc.col("time_by_scope"),
                output_by_scope=fc.col("output_by_scope"),
                max_output_tokens=self.pipeline_config.pass_10.max_output_tokens,
                model_alias=self.pipeline_config.pass_10.model,
                request_timeout=600,
            ),
        )

        return df

    def get_required_passes(self) -> List[str]:
        """Requires audit analysis (which requires all previous)."""
        return ["audit_analysis"]
