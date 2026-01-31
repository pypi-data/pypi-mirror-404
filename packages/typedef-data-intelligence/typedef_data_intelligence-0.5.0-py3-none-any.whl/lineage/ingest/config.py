"""Ingest-time configuration for data loading and population.

This module defines configuration for data ingestion operations:
- Semantic analysis settings (LLM models, parallelism)
- Profiling configuration
- Clustering configuration
- Semantic view loading
- Output settings

Separates ingest-time concerns from runtime agent configuration.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field

from lineage.backends.config import DataConfig, LineageConfig

# ============================================================================
# Model Size Enum (AWS-style instance sizes)
# ============================================================================

MODEL_SIZE = Literal["micro", "small", "medium", "large", "xlarge"]


# ============================================================================
# Analysis Model Configuration
# ============================================================================


class AnalysisModelConfig(BaseModel):
    """Configuration for a single LLM model used in semantic analysis.

    Defines the provider type, model name, and inference parameters.
    """

    type: Literal["openai", "google", "openrouter", "anthropic"] = Field(
        default="openrouter", description="LLM provider type"
    )
    model_name: str = Field(
        default="openai/gpt-5-nano",
        description="Model identifier (e.g., 'gpt-4o-mini', 'gemini-2.0-flash-thinking-exp-01-21')",
    )
    thinking_tokens_budget: Optional[int] = Field(
        default=None, description="Thinking token budget for the model"
    )
    reasoning_effort: Optional[Literal["minimal", "low", "medium", "high"]] = Field(
        default=None, description="Reasoning effort level for the model"
    )


class AnalysisModelsConfig(BaseModel):
    """Configuration for LLM models at different instance sizes.

    Maps AWS-style instance sizes to model configurations:
    - micro: Smallest, fastest models for trivial tasks
    - small: Fast models for simple tasks
    - medium: Balanced models for moderate reasoning
    - large: Powerful models for complex reasoning
    - xlarge: Most powerful models for very complex reasoning
    """

    micro: AnalysisModelConfig = Field(
        default_factory=lambda: AnalysisModelConfig(
            type="openai",
            model_name="gpt-5-nano",
            reasoning_effort="minimal",
        ),
        description="Micro instance - fastest, cheapest models",
    )
    small: AnalysisModelConfig = Field(
        default_factory=lambda: AnalysisModelConfig(
            type="openai",
            model_name="gpt-5-nano",
            reasoning_effort="medium",
        ),
        description="Small instance - fast models for simple tasks",
    )
    medium: AnalysisModelConfig = Field(
        default_factory=lambda: AnalysisModelConfig(
            type="openai",
            model_name="gpt-5-mini",
            reasoning_effort="medium",
        ),
        description="Medium instance - balanced models",
    )
    large: AnalysisModelConfig = Field(
        default_factory=lambda: AnalysisModelConfig(
            type="openai",
            model_name="gpt-5",
            reasoning_effort="low",
        ),
        description="Large instance - powerful models",
    )
    xlarge: AnalysisModelConfig = Field(
        default_factory=lambda: AnalysisModelConfig(
            type="openai",
            model_name="gpt-5",
            reasoning_effort="medium",
        ),
        description="XLarge instance - most powerful models",
    )


# ============================================================================
# Pipeline Configuration
# ============================================================================


class PassConfig(BaseModel):
    """Configuration for a single semantic analysis pass."""

    model: MODEL_SIZE = Field(default="small", description="Model size for this pass")
    max_output_tokens: int = Field(
        default=16384, ge=1024, le=128000, description="Max output tokens for this pass"
    )


class PipelineConfig(BaseModel):
    """Configuration for semantic analysis pipeline execution."""

    # Pass-specific configurations
    pass_01: PassConfig = Field(
        default_factory=lambda: PassConfig(model="small", max_output_tokens=32768),
        description="Relations extraction",
    )
    pass_02: PassConfig = Field(
        default_factory=lambda: PassConfig(model="small", max_output_tokens=16384),
        description="Column analysis. Column lists are typically compact.",
    )
    pass_03: PassConfig = Field(
        default_factory=lambda: PassConfig(model="medium", max_output_tokens=32768),
        description="Join analysis. Joins can be complex.",
    )
    pass_04: PassConfig = Field(
        default_factory=lambda: PassConfig(model="small", max_output_tokens=16384),
        description="Filter analysis",
    )
    pass_05: PassConfig = Field(
        default_factory=lambda: PassConfig(model="small", max_output_tokens=32768),
        description="Grouping analysis",
    )
    pass_06: PassConfig = Field(
        default_factory=lambda: PassConfig(model="small", max_output_tokens=8192),
        description="Time dimension analysis",
    )
    pass_07: PassConfig = Field(
        default_factory=lambda: PassConfig(model="small", max_output_tokens=8192),
        description="Window function analysis. Window specs are typically compact.",
    )
    pass_08: PassConfig = Field(
        default_factory=lambda: PassConfig(model="medium", max_output_tokens=8192),
        description="Output shape analysis",
    )
    pass_09: PassConfig = Field(
        default_factory=lambda: PassConfig(model="medium", max_output_tokens=32768),
        description="Audit analysis. Most audits fit in 8k tokens.",
    )
    pass_10: PassConfig = Field(
        default_factory=lambda: PassConfig(model="large", max_output_tokens=16384),
        description="Business semantics. Typically fits in 8k, plus room for reasoning.",
    )
    pass_10a: PassConfig = Field(
        default_factory=lambda: PassConfig(model="micro", max_output_tokens=16384),
        description="Grain analysis",
    )
    pass_11: PassConfig = Field(
        default_factory=lambda: PassConfig(model="small", max_output_tokens=8192),
        description="Analysis summary. Summaries should be concise.",
    )

    # Pipeline settings
    enable_audit: bool = Field(default=False, description="Enable audit logging")
    audit_dir: Optional[Path] = Field(
        default=None, description="Directory for audit logs"
    )


# ============================================================================
# Semantic Analysis Configuration
# ============================================================================


class SemanticAnalysisConfig(BaseModel):
    """Configuration for semantic SQL analysis."""

    enabled: bool = Field(default=True, description="Enable semantic analysis")
    use_hybrid: bool = Field(
        default=True,
        description="Use hybrid mode: deterministic SQLGlot + targeted LLM classification"
    )
    max_workers: int = Field(
        default=8, ge=1, le=128,
        description="Parallel workers (used by per-model fallback mode)"
    )
    model_filter: Optional[str] = Field(
        default=None,
        description="Filter models by substring (e.g., 'fct_' for facts only)",
    )

    # Batch processing configuration (always enabled)
    batch_size: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Number of models per batch"
    )

    # LLM model configurations for different pass complexities
    models: AnalysisModelsConfig = Field(
        default_factory=AnalysisModelsConfig,
        description="LLM model configurations (AWS-style instance sizes)",
    )

    # Pipeline configuration (which model size to use for each pass)
    pipeline: PipelineConfig = Field(
        default_factory=PipelineConfig, description="Pipeline pass assignments"
    )

    analysis_result_table: str = Field(
        default="batch_analysis", description="Table name for analysis results"
    )

    # Cache configuration
    cache_dir: Path = Field(
        default=Path(".lineage_workspace/semantic_cache"),
        description="Directory for semantic analysis cache"
    )
    use_cache: bool = Field(
        default=True,
        description="Use cached analysis results if available"
    )
    export_cache: bool = Field(
        default=True,
        description="Export analysis results to cache after completion"
    )


# ============================================================================
# Profiling Configuration
# ============================================================================


class ProfilingConfig(BaseModel):
    """Configuration for data profiling."""

    enabled: bool = Field(default=False, description="Enable table/column profiling")
    max_workers: int = Field(default=8, ge=1, le=64, description="Parallel workers")
    sample_size: int = Field(default=10000, description="Number of rows to sample")


# ============================================================================
# Clustering Configuration
# ============================================================================


class ClusteringConfig(BaseModel):
    """Configuration for join pattern clustering."""

    enabled: bool = Field(default=True, description="Enable join clustering")
    min_cluster_size: int = Field(default=2, description="Minimum models per cluster")
    similarity_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Join similarity threshold"
    )


# ============================================================================
# Semantic View Loader Configuration
# ============================================================================


class SemanticViewLoaderConfig(BaseModel):
    """Configuration for loading semantic views from data warehouse."""

    enabled: bool = Field(default=True, description="Enable semantic view loading")
    schema_pattern: Optional[str] = Field(
        default=None,
        description="Schema name pattern for semantic views (e.g., 'semantic_*')",
    )


# ============================================================================
# Population Configuration (Combines All Ingest Settings)
# ============================================================================


class PopulationConfig(BaseModel):
    """Configuration for data population during load-dbt-full.

    Combines all ingest-time settings:
    - Semantic analysis (including LLM model configurations)
    - Profiling
    - Clustering
    - Semantic view loading
    """

    semantic_analysis: SemanticAnalysisConfig = Field(
        default_factory=SemanticAnalysisConfig
    )
    profiling: ProfilingConfig = Field(default_factory=ProfilingConfig)
    clustering: ClusteringConfig = Field(default_factory=ClusteringConfig)
    semantic_view_loader: SemanticViewLoaderConfig = Field(
        default_factory=SemanticViewLoaderConfig
    )


# ============================================================================
# Output Configuration
# ============================================================================


class OutputConfig(BaseModel):
    """Configuration for output artifacts."""

    reports_dir: Optional[Path] = Field(
        default=None, description="Directory for generated reports"
    )
    artifacts_dir: Optional[Path] = Field(
        default=None, description="Directory for analysis artifacts"
    )


# ============================================================================
# Ingest Configuration (Top-Level)
# ============================================================================


class IngestConfig(BaseModel):
    """Top-level configuration for data ingestion operations.

    This configuration includes:
    - Full lineage backend config (to connect to graph database)
    - Full data backend config (to connect to data warehouse for profiling/semantic views)
    - Population settings (semantic analysis, profiling, clustering)
    - Output settings (where to write reports/artifacts)

    Configuration supports environment variable interpolation using ${VAR_NAME} syntax.

    Loaded from ingest.yml or config.ingest.default.yml.
    """

    lineage: LineageConfig
    data: DataConfig
    population: PopulationConfig = Field(default_factory=PopulationConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> IngestConfig:
        """Load configuration from YAML file with environment variable interpolation.

        Supports ${VAR_NAME} syntax for environment variable substitution.

        Args:
            path: Path to YAML configuration file

        Returns:
            Parsed and validated IngestConfig
        """
        with open(path, "r") as f:
            content = f.read()

        # Interpolate ${VAR_NAME} with environment variables
        def replace_env_var(match):
            var_name = match.group(1)
            value = os.environ.get(var_name)
            if value is None:
                raise ValueError(
                    f"Environment variable '{var_name}' is not set "
                    f"(required by {path})"
                )
            return value

        content = re.sub(r"\$\{([^}]+)\}", replace_env_var, content)
        data = yaml.safe_load(content)

        return cls(**data)
