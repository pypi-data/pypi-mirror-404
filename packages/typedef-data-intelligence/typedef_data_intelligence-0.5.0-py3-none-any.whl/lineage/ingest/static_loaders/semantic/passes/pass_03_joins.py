"""Pass 3: Join Edge Analysis - extracts join relationships between tables."""

from typing import List

import fenic as fc

from lineage.ingest.config import PipelineConfig

from ..models import JoinEdgeAnalysis
from ..prompts import JOIN_EDGE_EXTRACTION_PROMPT
from .base import BasePass


class JoinEdgeAnalysisPass(BasePass):
    """Extract join edges and their conditions."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        super().__init__(session, "join_analysis", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(
            df, ["canonical_sql", "relation_analysis", "column_analysis"]
        )

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Extract join edges using templated prompt."""
        self.validate_inputs(df)

        # Use semantic.map with the prompt template directly
        df = df.with_column(
            "join_analysis",
            fc.semantic.map(
                JOIN_EDGE_EXTRACTION_PROMPT,
                response_format=JoinEdgeAnalysis,
                relation_analysis=fc.col("relation_analysis"),
                column_analysis=fc.col("column_analysis"),
                canonical_sql=fc.col("canonical_sql"),
                max_output_tokens=self.pipeline_config.pass_03.max_output_tokens,
                model_alias=self.pipeline_config.pass_03.model,
                request_timeout=600,
            ),
        )

        return df

    def get_required_passes(self) -> List[str]:
        """Requires relation and column analysis."""
        return ["relation_analysis", "column_analysis"]
