#!/usr/bin/env python
"""Migrate semantic cache to consolidated format (fingerprints in parquet).

This script migrates existing semantic caches from the old format
(checksums.json + analysis_results.parquet) to the new consolidated format
(analysis_results.parquet with fingerprint columns).

Usage:
    lineage-refingerprint-cache \
      --manifest-path /path/to/target/manifest.json \
      --cache-dir .lineage_workspace/semantic_cache/mattermost_analytics \
      --dialect snowflake
"""

import argparse
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

from lineage.ingest.static_loaders.dbt.config import DbtArtifactsConfig
from lineage.ingest.static_loaders.dbt.dbt_loader import DbtLoader
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
    compute_model_fingerprint_result,
)


def main() -> None:
    """Migrate semantic cache to consolidated format with fingerprints in parquet."""
    parser = argparse.ArgumentParser(
        description="Migrate semantic cache to consolidated format (fingerprints in parquet)"
    )
    parser.add_argument(
        "--manifest-path",
        required=True,
        help="Path to dbt manifest.json file",
    )
    parser.add_argument(
        "--cache-dir",
        required=True,
        help="Path to semantic cache directory (containing checksums.json and/or analysis_results.parquet)",
    )
    parser.add_argument(
        "--dialect",
        default="snowflake",
        help="SQL dialect for fingerprinting (default: snowflake)",
    )
    args = parser.parse_args()

    # Load manifest
    manifest_path = Path(args.manifest_path)
    if not manifest_path.exists():
        print(f"Error: manifest.json not found at {manifest_path}")
        return

    target_dir = manifest_path.parent
    config = DbtArtifactsConfig(target_path=target_dir)
    loader = DbtLoader(config)
    artifacts = loader.load()

    cache_dir = Path(args.cache_dir)
    parquet_file = cache_dir / "analysis_results.parquet"
    checksums_file = cache_dir / "checksums.json"

    if not parquet_file.exists():
        print(f"Error: analysis_results.parquet not found at {parquet_file}")
        return

    # Check if already migrated (has fingerprint column)
    table = pq.read_table(parquet_file)
    if "fingerprint" in table.column_names:
        print("Cache already has fingerprint column - checking if update needed...")
        # Still proceed to update fingerprints with latest logic
    else:
        print("Cache missing fingerprint column - will add it")

    # Build fingerprint lookup from manifest
    print("Computing fingerprints for models in manifest...")
    sqlglot_schema = artifacts.sqlglot_schema()
    fingerprints: dict[str, dict] = {}
    for model in artifacts.iter_models():
        checksum_value = model.checksum.checksum if model.checksum else None
        result = compute_model_fingerprint_result(
            resource_type=model.resource_type,
            compiled_sql=model.compiled_sql,
            checksum=checksum_value,
            dialect=args.dialect,
            schema=sqlglot_schema,
            model_id=model.unique_id,
        )

        if result:
            fingerprints[model.unique_id] = {
                "fingerprint": result.hash,
                "fingerprint_type": result.type,
                "fingerprint_dialect": result.dialect,
            }

    print(f"Computed {len(fingerprints)} fingerprints")

    # Read existing parquet as Polars DataFrame
    df = pl.read_parquet(parquet_file)
    model_ids = df["model_id"].to_list()

    # Build fingerprint columns aligned with model_id order
    fp_hashes = [fingerprints.get(mid, {}).get("fingerprint") for mid in model_ids]
    fp_types = [fingerprints.get(mid, {}).get("fingerprint_type") for mid in model_ids]
    fp_dialects = [fingerprints.get(mid, {}).get("fingerprint_dialect") for mid in model_ids]

    # Drop old fingerprint columns if they exist
    cols_to_drop = [c for c in ["fingerprint", "fingerprint_type", "fingerprint_dialect"] if c in df.columns]
    if cols_to_drop:
        df = df.drop(cols_to_drop)

    # Add new fingerprint columns
    df = df.with_columns([
        pl.Series("fingerprint", fp_hashes),
        pl.Series("fingerprint_type", fp_types),
        pl.Series("fingerprint_dialect", fp_dialects),
    ])

    # Write updated parquet
    df.write_parquet(parquet_file)
    print(f"Updated {parquet_file} with {len(model_ids)} fingerprints")

    # Delete checksums.json if it exists (no longer needed)
    if checksums_file.exists():
        checksums_file.unlink()
        print(f"Deleted {checksums_file} (no longer needed)")

    # Summary
    matched = sum(1 for fp in fp_hashes if fp is not None)
    unmatched = sum(1 for fp in fp_hashes if fp is None)
    print("\nMigration complete:")
    print(f"  - {matched} models with fingerprints")
    print(f"  - {unmatched} models without fingerprints (not in manifest)")


if __name__ == "__main__":
    main()
