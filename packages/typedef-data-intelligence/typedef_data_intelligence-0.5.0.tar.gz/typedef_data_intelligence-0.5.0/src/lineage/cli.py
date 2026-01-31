"""CLI commands for lineage prototype.

This module provides CLI commands for initializing databases, loading dbt projects,
and running semantic analysis on models.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

import click
import uvicorn

from lineage.backends.config import UnifiedConfig
from lineage.backends.data_query.factory import create_data_backend_for_cli
from lineage.backends.lineage.factory import create_storage_for_cli
from lineage.ingest.config import IngestConfig
from lineage.ingest.static_loaders.dbt.builder import LineageBuilder
from lineage.integration import load_full_lineage
from lineage.utils.drop_snowflake_objects import drop_objects
from lineage.utils.env import load_env_file
from lineage.utils.run_snowflake_query import execute_sql_file


@click.group()
def main() -> None:
    """Lineage prototype CLI."""
    pass


def load_config(config_path: Path) -> UnifiedConfig:
    """Load unified configuration from YAML file."""
    try:
        return UnifiedConfig.from_yaml(config_path)
    except FileNotFoundError as e:
        click.echo(f"Error: Config file not found: {config_path}", err=True)
        raise click.Abort() from e
    except ValueError as e:
        click.echo(f"Error: Invalid configuration: {e}", err=True)
        raise click.Abort() from e


def load_ingest_config(config_path: Path) -> IngestConfig:
    """Load ingest configuration from YAML file."""
    try:
        return IngestConfig.from_yaml(config_path)
    except FileNotFoundError as e:
        click.echo(f"Error: Ingest config file not found: {config_path}", err=True)
        raise click.Abort() from e
    except ValueError as e:
        click.echo(f"Error: Invalid ingest configuration: {e}", err=True)
        raise click.Abort() from e


def _discover_ingest_config(artifacts_dir: Path, verbose: bool = False) -> Path:
    """Discover ingest config file with fallback logic.

    Search order:
    1. ingest.yml in artifacts_dir
    2. config.yml in artifacts_dir
    3. config.ingest.default.yml in typedef_data_intelligence root

    Args:
        artifacts_dir: dbt artifacts directory (target/)
        verbose: Enable verbose output

    Returns:
        Path to ingest config file
    """
    # Try ingest.yml in artifacts dir
    ingest_yml = artifacts_dir / "ingest.yml"
    if ingest_yml.exists():
        if verbose:
            click.echo(f"📄 Using ingest config: {ingest_yml}")
        return ingest_yml

    # Try config.yml in artifacts dir
    config_yml = artifacts_dir / "config.yml"
    if config_yml.exists():
        if verbose:
            click.echo(f"📄 Using ingest config: {config_yml}")
        return config_yml

    # Fall back to default config in typedef_data_intelligence root
    default_config = Path(__file__).parent.parent.parent / "config.ingest.default.yml"
    if default_config.exists():
        if verbose:
            click.echo(f"📄 Using default ingest config: {default_config}")
        return default_config

    raise click.ClickException(
        f"No ingest config found. Searched:\n"
        f"  - {ingest_yml}\n"
        f"  - {config_yml}\n"
        f"  - {default_config}\n"
        f"Please create an ingest.yml or use --ingest-config"
    )


@main.command()
@click.argument("artifacts_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--ingest-config", type=click.Path(exists=True, path_type=Path), default=None, help="Path to ingest config YAML file (auto-discovers if not provided)")
def init(artifacts_dir: Path, ingest_config: Optional[Path] = None, verbose: bool = False) -> None:
    """`Init`ialize or recreate the database typed schema."""
    # Auto-discover or use provided ingest config
    if ingest_config is None:
        ingest_config = _discover_ingest_config(artifacts_dir, verbose=verbose)

    cfg = load_ingest_config(ingest_config)
    storage = create_storage_for_cli(cfg.lineage)

    # Recreate schema (supported by all adapters)
    try:
        storage.recreate_schema()
        click.echo(f"✅ Initialized database schema using {type(storage).__name__}")
    except AttributeError:
        click.echo(f"✅ Initialized database using {type(storage).__name__}")


@main.command()
@click.argument("sql_file", type=click.Path(exists=True, path_type=Path))
def run_snowflake_query(sql_file: Path) -> None:
    """Run a Snowflake query."""
    execute_sql_file(sql_file)

@main.command()
@click.option("--drop-staging", "drop_staging", is_flag=True, default=False, help="Drop staging schema (default: staging is ignored)")
def drop_snowflake_objects(drop_staging: bool) -> None:
    """Drop all Snowflake objects."""
    # Invert: if drop_staging is True, then ignore_staging is False
    drop_objects(ignore_staging=not drop_staging)


@main.command("load-dbt-models")
@click.argument("artifacts_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--ingest-config", type=click.Path(exists=True, path_type=Path), required=True, help="Path to unified config YAML file")
@click.option("--force-full", is_flag=True, default=False, help="Force full reload (disables incremental loading)")
def load_dbt_models(artifacts_dir: Path, ingest_config: Path, force_full: bool) -> None:
    """Load dbt lineage directly into typed tables from an artifacts directory (target/)."""
    load_env_file()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    cfg = load_ingest_config(ingest_config)
    storage = create_storage_for_cli(cfg.lineage)
    time_start = time.time()
    click.echo(f"Loading dbt artifacts from {artifacts_dir}...")
    builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
    builder_time = time.time() - time_start
    click.echo(f"Builder time: {builder_time:.2f} seconds")
    time_start = time.time()
    
    # Use incremental mode by default (unless --force-full is specified)
    if not force_full:
        from lineage.ingest.static_loaders.change_detection import ChangeDetector
        artifacts = builder.loader.load()
        detector = ChangeDetector()

        # Create dialect_resolver using builder's config to ensure fingerprints match
        # between change detection and graph storage (fixes dialect mismatch bug)
        def dialect_resolver(model_id: str) -> Optional[str]:
            return builder.config.sqlglot.per_model_dialects.get(
                model_id, builder.config.sqlglot.default_dialect
            )

        change_set = detector.detect_changes(artifacts, storage, dialect_resolver=dialect_resolver)
        if change_set.has_changes:
            builder.write_incremental(storage, change_set)
        else:
            click.echo("No changes detected - all models unchanged")

        # Handle tests incrementally.
        # Always run detection (even when counts are 0) so that removals are caught.
        test_changes = detector.detect_test_changes(artifacts, storage)
        unit_test_changes = detector.detect_unit_test_changes(artifacts, storage)
        if test_changes.has_changes or unit_test_changes.has_changes:
            builder.write_incremental_tests(
                storage, test_changes, unit_test_changes
            )
        else:
            click.echo("No test changes detected - all tests unchanged")
    else:
        builder.write_typed(storage)
    
    write_time = time.time() - time_start
    click.echo(f"Write time: {write_time:.2f} seconds")
    click.echo(f"Loaded dbt artifacts (typed) from {artifacts_dir}")


@main.command("load-dbt-full")
@click.argument("artifacts_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--ingest-config", type=click.Path(exists=True, path_type=Path), default=None, help="Path to ingest config YAML file (auto-discovers if not provided)")
@click.option("--export-cache/--no-export-cache", default=None, help="Override export_cache config setting")
@click.option("--force-full", is_flag=True, default=False, help="Force full reload (disables incremental loading)")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def load_dbt_full(
    artifacts_dir: Path,
    ingest_config: Path | None,
    export_cache: bool | None,
    force_full: bool,
    verbose: bool,
) -> None:
    """Load dbt lineage with semantic analysis, profiling, and clustering.

    This command:
    1. Loads dbt models, sources, columns, and dependencies
    2. [Optional] Loads semantic views from data warehouse (Snowflake/etc)
    3. [Optional] Profiles table data (row counts, column statistics)
    4. [Optional] Runs semantic SQL analysis on each model's compiled SQL
    5. [Optional] Clusters models based on join patterns (Louvain algorithm)

    Configuration auto-discovery:
    - Searches for ingest.yml in artifacts_dir
    - Falls back to config.yml in artifacts_dir
    - Falls back to config.ingest.default.yml in project root
    - Or use --ingest-config to specify explicitly

    Configuration fields:
    - population.models: LLM model configs for semantic analysis (micro/small/medium/large/xlarge)
    - population.semantic_analysis.enabled: Run semantic analysis
    - population.semantic_analysis.max_workers: Max concurrent workers
    - population.semantic_analysis.pipeline: Pipeline pass model assignments
    - population.clustering.enabled: Cluster by join patterns
    - population.profiling.enabled: Profile table data
    - population.semantic_view_loader.enabled: Load semantic views

    Example:
        uv run lineage load-dbt-full target/ --verbose
        uv run lineage load-dbt-full target/ --ingest-config ingest.yml --verbose
    """
    load_env_file()
    # Enable DEBUG logging for lineage module if verbose
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("google_genai.models").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.INFO)

    # Auto-discover or use provided ingest config
    if ingest_config is None:
        ingest_config = _discover_ingest_config(artifacts_dir, verbose=verbose)

    cfg = load_ingest_config(ingest_config)
    storage = create_storage_for_cli(cfg.lineage)

    # Get population settings from ingest config
    pop = cfg.population

    # Create data backend from ingest config
    data_backend_instance = create_data_backend_for_cli(cfg.data, read_only=True)

    if verbose:
        click.echo(f"🗄️  Lineage backend: {cfg.lineage.backend}")
        click.echo(f"📊 Data backend: {cfg.data.backend}")
        click.echo(f"🔧 Semantic analysis: {pop.semantic_analysis.enabled}")
        click.echo(f"🔧 Clustering: {pop.clustering.enabled}")
        click.echo(f"🔧 Profiling: {pop.profiling.enabled}")
        click.echo(f"🔧 Semantic views: {pop.semantic_view_loader.enabled}")
        models = pop.semantic_analysis.models
        click.echo(f"🤖 Analysis models: micro={models.micro.model_name}, small={models.small.model_name}, medium={models.medium.model_name}, large={models.large.model_name}, xlarge={models.xlarge.model_name}")
        click.echo(f"⚡ Max semantic workers: {pop.semantic_analysis.max_workers}")
        click.echo(f"⚡ Max profiling workers: {pop.profiling.max_workers}")

    load_full_lineage(
        artifacts_dir=artifacts_dir,
        storage=storage,
        semantic_config=pop.semantic_analysis,
        profiling_config=pop.profiling,
        clustering_config=pop.clustering,
        semantic_view_config=pop.semantic_view_loader,
        data_backend=data_backend_instance,
        model_filter=pop.semantic_analysis.model_filter,
        export_cache_override=export_cache,
        incremental=not force_full,
        verbose=verbose,
    )
    click.echo("\n✅ Load complete!")

@main.command("reanalyze-semantics")
@click.argument("artifacts_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--ingest-config", type=click.Path(exists=True, path_type=Path), default=None, help="Path to ingest config YAML file (auto-discovers if not provided)")
@click.option("--skip-clustering", is_flag=True, help="Skip join graph clustering (faster)")
@click.option("--export-cache/--no-export-cache", default=None, help="Override export_cache config setting")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def reanalyze_semantics(
    artifacts_dir: Path,
    ingest_config: Path | None,
    skip_clustering: bool,
    export_cache: bool | None,
    verbose: bool,
) -> None:
    """Re-run semantic analysis without reloading dbt graph data.

    This command is optimized for fast iteration on semantic analysis configuration.
    It loads dbt artifacts to get model metadata and compiled SQL, but skips
    writing dbt nodes to the graph storage (assumes they already exist from a
    previous load-dbt-full run).

    This command:
    1. Loads dbt artifacts (fast - ~2 seconds)
    2. Skips writing dbt nodes to graph (avoids slow step)
    3. Runs semantic SQL analysis on models
    4. [Optional] Runs join graph clustering (default: enabled, use --skip-clustering to disable)

    Skipped operations:
    - Writing dbt nodes/edges to graph storage (slow)
    - Loading semantic views from warehouse
    - Profiling table data

    Example:
        # Re-analyze with clustering
        uv run lineage reanalyze-semantics target/ --verbose

        # Re-analyze without clustering (fastest)
        uv run lineage reanalyze-semantics target/ --skip-clustering --verbose
    """
    load_env_file()
    # Enable logging if verbose
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("google_genai.models").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.INFO)

    # Auto-discover or use provided ingest config
    if ingest_config is None:
        ingest_config = _discover_ingest_config(artifacts_dir, verbose=verbose)

    cfg = load_ingest_config(ingest_config)
    storage = create_storage_for_cli(cfg.lineage)

    # Get population settings
    pop = cfg.population

    # Create data backend (needed for semantic analysis dialect detection)
    data_backend_instance = create_data_backend_for_cli(cfg.data, read_only=True)

    if verbose:
        click.echo(f"🗄️  Lineage backend: {cfg.lineage.backend}")
        click.echo(f"📊 Data backend: {cfg.data.backend}")
        click.echo(f"🔧 Semantic analysis: {pop.semantic_analysis.enabled}")
        click.echo(f"🔧 Clustering: {'SKIP' if skip_clustering else pop.clustering.enabled}")
        models = pop.semantic_analysis.models
        click.echo(f"🤖 Analysis models: micro={models.micro.model_name}, small={models.small.model_name}, medium={models.medium.model_name}")

    # Import integration here to avoid circular imports
    from lineage.integration import LineageIntegration

    integration = LineageIntegration(
        storage=storage,
        semantic_config=pop.semantic_analysis,
        profiling_config=pop.profiling,
        clustering_config=pop.clustering,
        semantic_view_config=pop.semantic_view_loader,
        data_backend=data_backend_instance,
    )

    integration.reanalyze_semantics_only(
        artifacts_dir=artifacts_dir,
        model_filter=pop.semantic_analysis.model_filter,
        skip_clustering=skip_clustering,
        export_cache_override=export_cache,
        verbose=verbose,
    )

    click.echo("\n✅ Re-analysis complete!")


@main.command("run-clustering")
@click.option("--ingest-config", type=click.Path(exists=True, path_type=Path), default=None, help="Path to ingest config YAML file")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def run_clustering(
    ingest_config: Path | None,
    verbose: bool,
) -> None:
    """Run join graph clustering only.

    This command runs only the join graph clustering step, useful for
    experimenting with clustering parameters without re-running semantic analysis.

    Requires:
    - dbt data already loaded in graph storage
    - Semantic analysis with join analysis already completed

    Example:
        uv run lineage run-clustering --verbose
    """
    load_env_file()
    # Enable logging if verbose
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Load config (no auto-discovery since we don't have artifacts_dir)
    if ingest_config is None:
        # Fall back to default config in typedef_data_intelligence root
        default_config = Path(__file__).parent.parent.parent / "config.ingest.default.yml"
        if default_config.exists():
            ingest_config = default_config
        else:
            raise click.ClickException(
                "No ingest config found. Please specify --ingest-config or create config.ingest.default.yml"
            )

    cfg = load_ingest_config(ingest_config)
    storage = create_storage_for_cli(cfg.lineage)

    # Get population settings
    pop = cfg.population

    # Create data backend (needed for clustering)
    data_backend_instance = create_data_backend_for_cli(cfg.data, read_only=True)

    if verbose:
        click.echo(f"🗄️  Lineage backend: {cfg.lineage.backend}")
        click.echo(f"🔧 Clustering: {pop.clustering.enabled}")

    if not pop.clustering.enabled:
        click.echo("⚠️  Clustering is disabled in configuration. Aborting.")
        raise click.Abort()

    # Import integration here to avoid circular imports
    from lineage.integration import LineageIntegration

    integration = LineageIntegration(
        storage=storage,
        semantic_config=pop.semantic_analysis,
        profiling_config=pop.profiling,
        clustering_config=pop.clustering,
        semantic_view_config=pop.semantic_view_loader,
        data_backend=data_backend_instance,
    )

    integration.run_clustering_only(verbose=verbose)

    click.echo("\n✅ Clustering complete!")


@main.command("create-snowflake-semantic-views")
@click.argument("artifacts_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
def create_snowflake_semantic_views(artifacts_dir: Path) -> None:
    """Create Snowflake semantic views."""
    semantic_views_dir = artifacts_dir / "semantic_views"
    load_env_file()
    for file in semantic_views_dir.glob("*.sql"):
        click.echo(f"Creating Snowflake semantic view from {file}")
        execute_sql_file(file)
    click.echo(f"Created Snowflake semantic views from {semantic_views_dir}")


@main.command("serve")
@click.option("--config", type=click.Path(exists=True, path_type=Path), required=True, help="Path to agent config YAML file")
@click.option("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
@click.option("--port", default=8000, type=int, help="Port to bind to (default: 8000)")
@click.option("--reload", is_flag=True, help="Enable auto-reload on code changes (development only)")
def serve(config: Path, host: str, port: int, reload: bool) -> None:
    """Start the backend API server."""
    # Set the config path as environment variable (app expects UNIFIED_CONFIG)
    os.environ["UNIFIED_CONFIG"] = str(config.absolute())

    click.echo(f"🚀 Starting backend API server on {host}:{port}")
    click.echo(f"📄 Using config: {config}")
    if reload:
        click.echo("🔄 Auto-reload enabled")

    # Import the app after setting env var
    from lineage.api.pydantic import app

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        reload=reload,
    )


def __main__():
    main()

if __name__ == "__main__":
    __main__()