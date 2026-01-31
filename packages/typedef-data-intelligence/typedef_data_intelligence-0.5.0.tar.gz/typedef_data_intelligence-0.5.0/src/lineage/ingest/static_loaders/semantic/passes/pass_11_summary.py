"""Analysis Summary Pass - Generates a concise text summary of the full semantic analysis."""

from typing import List
import fenic as fc
from lineage.ingest.config import PipelineConfig
from .base import BasePass


class AnalysisSummaryPass(BasePass):
    """Generate a concise text summary of the complete semantic analysis.

    This pass synthesizes all prior analysis results into a human-readable
    summary that can be used for:
    - Quick understanding of what the model does
    - LLM context about the model
    - Documentation generation
    - Model catalog descriptions
    """

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        """Initialize the AnalysisSummaryPass.

        Args:
            session: Fenic session for DataFrame operations
            pipeline_config: Pipeline configuration with model assignments and settings
        """
        super().__init__(session, "analysis_summary", pipeline_config)

    def validate_inputs(self, df: fc.DataFrame) -> bool:
        """Check that required columns exist."""
        return self._check_columns(
            df,
            [
                "business_semantics",
                "grain_humanization",
                "grouping_by_scope",
                "join_analysis",
                "relation_analysis",
            ],
        )

    def get_required_passes(self) -> List[str]:
        """This pass depends on grain humanization (which depends on all previous)."""
        return ["grain_humanization"]

    def execute(self, df: fc.DataFrame) -> fc.DataFrame:
        """Generate summary from all analysis results.

        Args:
            df: DataFrame with all prior analysis results

        Returns:
            DataFrame with added analysis_summary column
        """
        self.validate_inputs(df)

        # Define the summarization prompt using Jinja2 template syntax
        summary_prompt = """You are a data analyst reviewing the semantic analysis results for a SQL model.

Given the complete analysis results below, generate a concise 2-4 sentence summary that captures:
1. The primary purpose/intent of this model (what business question it answers)
2. The grain/level of detail (e.g., "per customer per month", "daily aggregated by region")
3. Key metrics/measures computed (if any)
4. Notable aspects like time windows, complex joins, or special transformations

IMPORTANT: When referencing tables, always use the full table names from the alias mappings, not just the aliases.
For example, instead of "join S-C", say "join STG_STRIPE__SUBSCRIPTIONS (S) to STG_STRIPE__CUSTOMERS (C)".

Be concise and focus on what's most important for understanding what this model does.

## Analysis Results

**Table Alias Mappings (use these to expand aliases to full table names):**
{{ relation_analysis }}

**Business Semantics:**
{{ business_semantics }}

**Grain:**
{{ grain_humanization }}

**Grouping:**
{{ grouping_by_scope }}

**Joins:**
{{ join_analysis }}

**Filters:**
{{ filter_analysis }}

**Time Analysis:**
{{ time_by_scope }}

**Window Functions:**
{{ window_by_scope }}

**Output Shape:**
{{ output_by_scope }}

---

Generate a concise summary (2-4 sentences):"""

        # Use Fenic's semantic.map to generate the summary
        df = df.with_column(
            "analysis_summary",
            fc.semantic.map(
                summary_prompt,
                strict=False,
                relation_analysis=fc.col("relation_analysis"),
                business_semantics=fc.col("business_semantics"),
                grain_humanization=fc.col("grain_humanization"),
                grouping_by_scope=fc.col("grouping_by_scope"),
                join_analysis=fc.col("join_analysis"),
                filter_analysis=fc.col("filter_analysis"),
                time_by_scope=fc.col("time_by_scope"),
                window_by_scope=fc.col("window_by_scope"),
                output_by_scope=fc.col("output_by_scope"),
                max_output_tokens=self.pipeline_config.pass_11.max_output_tokens,
                temperature=0.0,  # Deterministic output
                request_timeout=600,
                model_alias=self.pipeline_config.pass_11.model,
            ),
        )

        return df
