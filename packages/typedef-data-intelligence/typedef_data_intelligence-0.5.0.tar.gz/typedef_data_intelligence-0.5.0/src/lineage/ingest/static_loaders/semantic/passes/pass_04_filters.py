"""Pass 4: Filter Analysis - extracts WHERE, HAVING, and QUALIFY predicates."""

from typing import List

import fenic as fc

from lineage.ingest.config import PipelineConfig

from ..models import FilterAnalysis
from ..prompts import FILTER_EXTRACTION_PROMPT
from .base import BasePass


class FilterAnalysisPass(BasePass):
    """Extract filter predicates by clause."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        super().__init__(session, "filter_analysis", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(
            df,
            ["canonical_sql", "relation_analysis", "column_analysis", "join_analysis"],
        )

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Extract filters using templated prompt."""
        self.validate_inputs(df)

        # Use semantic.map with the prompt template directly
        df = df.with_column(
            "filter_analysis",
            fc.semantic.map(
                FILTER_EXTRACTION_PROMPT,
                response_format=FilterAnalysis,
                relation_analysis=fc.col("relation_analysis"),
                column_analysis=fc.col("column_analysis"),
                join_analysis=fc.col("join_analysis"),
                canonical_sql=fc.col("canonical_sql"),
                max_output_tokens=self.pipeline_config.pass_04.max_output_tokens,
                model_alias=self.pipeline_config.pass_04.model,
                request_timeout=600,
            ),
        )

        return df

    def get_required_passes(self) -> List[str]:
        """Requires relation, column, and join analysis."""
        return ["relation_analysis", "column_analysis", "join_analysis"]
