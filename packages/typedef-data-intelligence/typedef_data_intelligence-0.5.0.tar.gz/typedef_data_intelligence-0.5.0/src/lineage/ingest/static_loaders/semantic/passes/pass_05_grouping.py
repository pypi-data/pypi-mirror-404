"""Pass 5: Grouping Analysis - analyzes SELECT, GROUP BY, and result grain per scope."""

from typing import List

import fenic as fc
from fenic.api.functions import udf
from fenic.core.types import ArrayType, StringType

from lineage.ingest.config import PipelineConfig

from ..models import GroupingAnalysis
from ..prompts import GROUPING_EXTRACTION_PROMPT
from .base import BasePass


# UDF to extract scopes from relation analysis
@udf(return_type=ArrayType(StringType))
def extract_scopes(relation_analysis: dict) -> List[str]:
    """Extract unique scopes from RelationAnalysis."""
    if not relation_analysis or "relations" not in relation_analysis:
        return ["outer"]

    scopes = set()
    for rel in relation_analysis["relations"]:
        if "scope" in rel:
            scopes.add(rel["scope"])

    if not scopes:
        scopes.add("outer")

    return sorted(list(scopes))


class GroupingAnalysisPass(BasePass):
    """Extract grouping information per scope using explode pattern."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        """Initialize grouping analysis pass."""
        super().__init__(session, "grouping_analysis", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(
            df, ["canonical_sql", "relation_analysis", "column_analysis"]
        )

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Extract grouping using explode pattern for per-scope analysis."""
        self.validate_inputs(df)

        # Extract scopes and explode to create one row per scope
        df = df.with_column("scopes", extract_scopes(fc.col("relation_analysis")))
        df_exploded = df.explode("scopes").with_column(
            "current_scope", fc.col("scopes")
        )

        # Analyze each scope using semantic.map
        df_exploded = df_exploded.with_column(
            "grouping_for_scope",
            fc.semantic.map(
                GROUPING_EXTRACTION_PROMPT,
                response_format=GroupingAnalysis,
                scope=fc.col("current_scope"),
                relation_analysis=fc.col("relation_analysis"),
                column_analysis=fc.col("column_analysis"),
                canonical_sql=fc.col("canonical_sql"),
                max_output_tokens=self.pipeline_config.pass_05.max_output_tokens,
                model_alias=self.pipeline_config.pass_05.model,
                request_timeout=600,
            ),
        )

        # Group by original row and collect results
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
        ).agg(
            fc.collect_list(
                fc.struct(
                    fc.col("current_scope").alias("scope"), fc.col("grouping_for_scope")
                )
            ).alias("grouping_by_scope")
        )

        return df_grouped

    def get_required_passes(self) -> List[str]:
        """Requires previous technical passes."""
        return ["relation_analysis", "column_analysis", "filter_analysis"]
