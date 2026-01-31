"""Pass 2: Column Analysis - extracts column references and allow-lists."""

from typing import List

import fenic as fc

from lineage.ingest.config import PipelineConfig

from ..models import ColumnAnalysis
from .base import BasePass


class ColumnAnalysisPass(BasePass):
    """Extract column references and create allow-lists for each relation."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        super().__init__(session, "column_analysis", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(df, ["canonical_sql", "relation_analysis"])

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Extract column information using semantic extraction."""
        self.validate_inputs(df)

        # Use semantic.extract with relation_analysis as context
        df = df.with_column(
            "column_analysis",
            fc.semantic.extract(
                fc.col("canonical_sql"),
                ColumnAnalysis,
                max_output_tokens=self.pipeline_config.pass_02.max_output_tokens,
                model_alias=self.pipeline_config.pass_02.model,
                request_timeout=600,
            ),
        )

        return df

    def get_required_passes(self) -> List[str]:
        """Requires relation_analysis from Pass 1."""
        return ["relation_analysis"]
