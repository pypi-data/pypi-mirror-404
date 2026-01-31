"""Pass 1: Relation Analysis - extracts tables, aliases, and scopes."""

from typing import List

import fenic as fc

from lineage.ingest.config import PipelineConfig

from ..models import RelationAnalysis
from .base import BasePass


class RelationAnalysisPass(BasePass):
    """Extract relations, aliases, and scopes from SQL."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        """Initialize the relation analysis pass."""
        super().__init__(session, "relation_analysis", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that canonical_sql column exists."""
        return self._check_columns(df, ["canonical_sql"])

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Extract relation information using semantic extraction."""
        self.validate_inputs(df)

        # Use semantic.extract to analyze relations
        df = df.with_column(
            "relation_analysis",
            fc.semantic.extract(
                fc.col("canonical_sql"),
                RelationAnalysis,
                max_output_tokens=self.pipeline_config.pass_01.max_output_tokens,
                model_alias=self.pipeline_config.pass_01.model,
                request_timeout=600,
            ),
        )

        return df

    def get_required_passes(self) -> List[str]:
        """No prerequisites for the first pass."""
        return []
