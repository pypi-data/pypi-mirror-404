"""Session configuration and creation for SQL Analyzer."""

from pathlib import Path
from typing import Optional

import fenic as fc

from lineage.ingest.config import AnalysisModelConfig, AnalysisModelsConfig


def _create_language_model(config: AnalysisModelConfig):
    """Create a Fenic language model from configuration.

    Args:
        config: Analysis model configuration

    Returns:
        Configured Fenic language model
    """
    # Reasonable defaults for rate limits
    if config.type == "openai":
        return fc.OpenAILanguageModel(
            model_name=config.model_name,
            rpm=15_000,
            tpm=30_000_000,
            profiles={
                "default": fc.OpenAILanguageModel.Profile(
                    reasoning_effort=config.reasoning_effort,
                    verbosity="low" if config.reasoning_effort else None
                )
            }
        )
    elif config.type == "google":
        return fc.GoogleDeveloperLanguageModel(
            model_name=config.model_name,
            rpm=5000,
            tpm=5_000_000,
            profiles={
                "default": fc.GoogleDeveloperLanguageModel.Profile(
                    thinking_token_budget=config.thinking_tokens_budget
                )
            }
        )
    elif config.type == "openrouter":
        if config.reasoning_effort:
            profile = fc.OpenRouterLanguageModel.Profile(
                reasoning_effort=config.reasoning_effort,
                provider=fc.OpenRouterLanguageModel.Provider(
                    sort = "throughput"
                )

            )
        elif config.thinking_tokens_budget:
            profile = fc.OpenRouterLanguageModel.Profile(
                reasoning_max_tokens=config.thinking_tokens_budget,
                provider=fc.OpenRouterLanguageModel.Provider(
                    sort = "throughput"
                )
            )
        else:
            profile = fc.OpenRouterLanguageModel.Profile(
                provider=fc.OpenRouterLanguageModel.Provider(
                    sort = "throughput"
                )
            )
        return fc.OpenRouterLanguageModel(
            model_name=config.model_name,
            profiles={"default": profile}
        )
    elif config.type == "anthropic":
        return fc.AnthropicLanguageModel(
            model_name=config.model_name,
            rpm=5000,
            input_tpm=2_500_000,
            output_tpm=1_000_000,
            profiles={
                "default": fc.AnthropicLanguageModel.Profile(
                    thinking_token_budget=config.thinking_tokens_budget
                )
            }
        )
    else:
        raise ValueError(f"Unsupported model type: {config.type}")


def create_session(
    analysis_models: AnalysisModelsConfig,
    app_name: str = "sql_analyzer",
    db_path: Optional[Path] = None,
) -> fc.Session:
    """Create and configure a Fenic session with language models.

    Args:
        analysis_models: Analysis models configuration
        app_name: Name for the Fenic application
        db_path: Optional path for storing fenic database files (DuckDB, LLM cache).
                 If None, uses current working directory.

    Returns:
        Configured Fenic session
    """
    # Create language models for each size
    language_models = {
        "micro": _create_language_model(analysis_models.micro),
        "small": _create_language_model(analysis_models.small),
        "medium": _create_language_model(analysis_models.medium),
        "large": _create_language_model(analysis_models.large),
        "xlarge": _create_language_model(analysis_models.xlarge),
    }

    sem_config = fc.SemanticConfig(
        language_models=language_models,
        default_language_model="medium",
        llm_response_cache=fc.LLMResponseCacheConfig(
            max_size_mb=512,
            ttl="7d"
        )
    )

    # Build session config with optional db_path
    session_config = fc.SessionConfig(
        app_name=app_name,
        semantic=sem_config,
        db_path=str(db_path) if db_path else None,
    )

    return fc.Session.get_or_create(session_config)
