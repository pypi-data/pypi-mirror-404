"""Regenerate semantic analysis goldens.

Runs deterministic analysis + classification on SQL fixtures.
Generates goldens in `tests/fixtures/semantic_expected/`.

By default, runs in hermetic mode (heuristics only, no LLM calls) for CI tests.
Use --with-llm to enable LLM-based column classification with heuristic fallback.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from lineage.devtools.semantic_goldens import (
    EXPECTED_DIR,
    fixture_dialect,
    fixture_schema,
    list_sql_fixtures,
    normalize_semantic_payload,
    read_sql_fixture,
)
from lineage.ingest.static_loaders.semantic.deterministic.executor import (
    DeterministicExecutor,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.column_classification import (
    heuristic_column_classification,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.incremental_watermark import (
    heuristic_watermark_classification,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.time_classification import (
    heuristic_time_classification,
)

# LLM imports - only used when --with-llm is specified
# Imported lazily to avoid requiring API keys for hermetic runs

logger = logging.getLogger(__name__)


def _get_outer_scope(scope_list: List[Dict], key: str) -> Optional[Dict]:
    """Extract outer scope value from a by-scope list."""
    if not scope_list:
        return None
    for item in scope_list:
        if item.get("scope") == "outer":
            return item.get(key)
    return None


def analyze_fixture_hermetic(
    sql: str,
    *,
    fixture_name: str,
    dialect: str = "duckdb",
    schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Analyze a single SQL fixture using hermetic (no LLM) approach.

    This runs:
    1. DeterministicExecutor - SQLGlot-based parsing
    2. Heuristic time classification - pattern-based time column detection
    3. Heuristic column classification - pattern-based semantic role + PII detection
    4. Heuristic watermark classification - pattern-based incremental watermark detection
    """
    executor = DeterministicExecutor(schema=schema)
    det = executor.run_all_passes(sql, dialect)

    if det.parse_error:
        raise RuntimeError(f"{fixture_name}: parse_error={det.parse_error}")

    # Extract outer scope grouping
    grouping_outer: Optional[Dict[str, Any]] = None
    if det.grouping_by_scope and "outer" in det.grouping_by_scope:
        grouping_outer = det.grouping_by_scope["outer"].model_dump()

    # Extract filter and relation analysis for heuristics
    filter_dict = det.filter_analysis.model_dump() if det.filter_analysis else {}
    relation_dict = det.relation_analysis.model_dump() if det.relation_analysis else {}

    # Run heuristic classification (PII is now part of column_classification)
    time_result = heuristic_time_classification(grouping_outer or {}, filter_dict)
    column_result = heuristic_column_classification(grouping_outer or {}, relation_dict)
    watermark_result = heuristic_watermark_classification(filter_dict)

    # Build payload
    payload: Dict[str, Any] = {
        "fixture": fixture_name,
        "dialect": dialect,
        "deterministic": {
            "relation_analysis": det.relation_analysis.model_dump() if det.relation_analysis else None,
            "column_analysis": det.column_analysis.model_dump() if det.column_analysis else None,
            "join_analysis": det.join_analysis.model_dump() if det.join_analysis else None,
            "filter_analysis": det.filter_analysis.model_dump() if det.filter_analysis else None,
            "grouping_outer": grouping_outer,
            "window_outer": det.window_by_scope["outer"].model_dump()
            if det.window_by_scope and "outer" in det.window_by_scope
            else None,
            "output_outer": det.output_by_scope["outer"].model_dump()
            if det.output_by_scope and "outer" in det.output_by_scope
            else None,
        },
        "heuristics": {
            "time": time_result.model_dump(),
            "semantic": column_result.model_dump(),  # Now includes PII fields
            "watermark": watermark_result.model_dump(),
        },
    }

    return normalize_semantic_payload(payload)


def analyze_fixture_with_llm(
    sql: str,
    *,
    fixture_name: str,
    dialect: str = "duckdb",
    schema: Optional[Dict[str, Any]] = None,
    session: Any,
    config: Any,
) -> Dict[str, Any]:
    """Analyze a single SQL fixture using LLM-based classification.

    This runs:
    1. HybridPipelineExecutor - Full pipeline with LLM for business semantics
    2. Returns complete analysis including business_semantics and grain_humanization
    """
    from lineage.ingest.static_loaders.semantic.pipeline.hybrid_executor import (
        HybridPipelineExecutor,
    )

    # Create executor with this fixture's schema
    executor = HybridPipelineExecutor(
        session=session,
        pipeline_config=config,
        schema=schema,
        classification_model_size="micro",
    )

    # Build input row
    input_rows = [{
        "model_id": fixture_name,
        "model_name": fixture_name,
        "path": f"models/{fixture_name}.sql",
        "filename": f"{fixture_name}.sql",
        "sql": sql,
        "canonical_sql": sql,
        "materialization": "table",
        "model_description": "",
    }]

    # Run pipeline
    df = session.create_dataframe(input_rows)
    result_df = executor.run(
        df,
        session,
        dbt_model_name=fixture_name,
        dialect=dialect,
    )

    # Extract result
    rows = result_df.to_pylist()
    if not rows:
        raise RuntimeError(f"{fixture_name}: no results from pipeline")

    row = rows[0]

    # Extract outer scope values
    grouping_outer = _get_outer_scope(row.get("grouping_by_scope", []), "grouping_for_scope")

    window_outer = None
    for item in row.get("window_by_scope", []):
        if item.get("scope") == "outer":
            wj = item.get("window_analysis_json")
            if wj:
                window_outer = json.loads(wj) if isinstance(wj, str) else wj
            break

    output_outer = _get_outer_scope(row.get("output_by_scope", []), "output_for_scope")

    # Get business semantics
    bs = row.get("business_semantics", {}) or {}

    payload = {
        "fixture": fixture_name,
        "dialect": dialect,
        "deterministic": {
            "relation_analysis": row.get("relation_analysis"),
            "column_analysis": row.get("column_analysis"),
            "join_analysis": row.get("join_analysis"),
            "filter_analysis": row.get("filter_analysis"),
            "grouping_outer": grouping_outer,
            "window_outer": window_outer,
            "output_outer": output_outer,
        },
        "heuristics": {
            "time": row.get("time_classification") or {},
            "semantic": row.get("semantic_classification") or {},
            "watermark": row.get("incremental_watermark") or {},
        },
        "filter_intent": row.get("filter_intent"),
        "business_semantics": bs,
        "grain_humanization": row.get("grain_humanization"),
        "analysis_summary": row.get("analysis_summary"),
    }

    return normalize_semantic_payload(payload)


async def process_fixture_hermetic(
    name: str,
    semaphore: asyncio.Semaphore,
    progress: List[int],
    total: int,
) -> None:
    """Process a single fixture in hermetic mode with concurrency control."""
    async with semaphore:
        try:
            # Run CPU-bound analysis in thread pool
            sql = await asyncio.to_thread(read_sql_fixture, name)
            schema = await asyncio.to_thread(fixture_schema, name)
            dialect = await asyncio.to_thread(fixture_dialect, name)

            payload = await asyncio.to_thread(
                analyze_fixture_hermetic,
                sql,
                fixture_name=name,
                dialect=dialect,
                schema=schema,
            )

            # Write result
            path = EXPECTED_DIR / f"{name}.json"
            await asyncio.to_thread(
                path.write_text,
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            # Update progress
            progress[0] += 1
            print(f"[{progress[0]}/{total}] Wrote golden: {name}" + (" (with schema)" if schema else ""))

        except Exception as e:
            progress[0] += 1
            print(f"[{progress[0]}/{total}] ✗ Failed {name}: {e}")
            raise


async def process_fixture_with_llm(
    name: str,
    semaphore: asyncio.Semaphore,
    config: Any,
    progress: List[int],
    total: int,
) -> None:
    """Process a single fixture with LLM mode and concurrency control.

    Each task creates its own Fenic session to avoid DuckDB transaction conflicts.
    """
    async with semaphore:
        session = None
        try:
            # Read fixture data
            sql = await asyncio.to_thread(read_sql_fixture, name)
            dialect = await asyncio.to_thread(fixture_dialect, name)
            schema = await asyncio.to_thread(fixture_schema, name)

            # Create a session per task to avoid DuckDB concurrency conflicts
            from lineage.ingest.config import AnalysisModelsConfig
            from lineage.ingest.static_loaders.semantic.config.session import (
                create_session as create_fenic_session,
            )

            db_path = Path(tempfile.mkdtemp(prefix=f"sql_analyzer_regen_{name}_"))
            session = await asyncio.to_thread(
                create_fenic_session,
                analysis_models=AnalysisModelsConfig(),
                app_name=f"regen_goldens_{name}",
                db_path=db_path,
            )

            # Run LLM analysis in thread pool (Fenic operations aren't async)
            payload = await asyncio.to_thread(
                analyze_fixture_with_llm,
                sql,
                fixture_name=name,
                dialect=dialect,
                schema=schema,
                session=session,
                config=config,
            )

            # Write result
            path = EXPECTED_DIR / f"{name}.json"
            await asyncio.to_thread(
                path.write_text,
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            # Update progress
            progress[0] += 1
            print(f"[{progress[0]}/{total}] Wrote golden: {name}" + (" (with schema)" if schema else ""))

        except Exception as e:
            progress[0] += 1
            print(f"[{progress[0]}/{total}] ✗ Failed {name}: {e}")
            raise
        finally:
            # Clean up session
            if session:
                try:
                    await asyncio.to_thread(session.stop)
                except Exception:
                    pass  # Ignore cleanup errors


def main(argv: Optional[List[str]] = None) -> None:
    """Generate golden JSON for all fixtures under tests/fixtures/semantic_sql."""
    parser = argparse.ArgumentParser(description="Regenerate semantic analysis goldens.")
    parser.add_argument(
        "--fixture",
        action="append",
        dest="fixtures",
        default=None,
        help="Fixture name to run (repeatable). If omitted, runs all fixtures.",
    )
    parser.add_argument(
        "--with-llm",
        action="store_true",
        default=False,
        help="Enable LLM-based classification (requires API keys, incurs cost).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Maximum number of fixtures to process concurrently (default: 10 for hermetic, 3 for LLM).",
    )
    args = parser.parse_args(argv)

    fixtures = args.fixtures or list_sql_fixtures()
    if not fixtures:
        raise RuntimeError("No SQL fixtures found.")

    mode = "LLM-enabled" if args.with_llm else "hermetic"

    # Set default concurrency based on mode
    concurrency = args.concurrency or (3 if args.with_llm else 10)
    print(f"Regenerating {mode} goldens for {len(fixtures)} fixtures (concurrency={concurrency})...")

    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    # Run async processing
    asyncio.run(_run_async(fixtures, args.with_llm, concurrency))

    print(f"Done. Generated {len(fixtures)} {mode} goldens.")


async def _run_async(fixtures: List[str], with_llm: bool, concurrency: int) -> None:
    """Run async processing of all fixtures."""
    semaphore = asyncio.Semaphore(concurrency)
    progress = [0]  # Mutable counter for progress tracking

    if with_llm:
        # LLM mode: each task creates its own Fenic session to avoid DuckDB conflicts
        from lineage.ingest.config import PipelineConfig

        config = PipelineConfig(enable_audit=False)

        # Process all fixtures concurrently (each creates its own session)
        tasks = [
            process_fixture_with_llm(
                name=name,
                semaphore=semaphore,
                config=config,
                progress=progress,
                total=len(fixtures),
            )
            for name in fixtures
        ]
        await asyncio.gather(*tasks)
    else:
        # Hermetic mode: no LLM calls, process in parallel
        tasks = [
            process_fixture_hermetic(
                name=name,
                semaphore=semaphore,
                progress=progress,
                total=len(fixtures),
            )
            for name in fixtures
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    main()
