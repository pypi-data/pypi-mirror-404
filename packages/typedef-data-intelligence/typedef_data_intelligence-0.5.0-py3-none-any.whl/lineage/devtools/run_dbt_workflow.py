#!/usr/bin/env python3
"""Run dbt workflow: deps, seed, run, docs generate.

This module provides functions to run the complete dbt build workflow,
reusing the venv management from the TUI.

Usage:
    python run_dbt_workflow.py /path/to/dbt/project --profiles-dir /path/to/profiles
    python run_dbt_workflow.py /path/to/dbt/project  # Uses project dir for profiles
"""
import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_workflow(
    project_path: Path,
    profiles_dir: Optional[Path] = None,
    dry_run: bool = False,
    skip_seed: bool = False,
    extra_env: Optional[dict[str, str]] = None,
) -> bool:
    """Run the complete dbt workflow: deps, seed, run, docs generate.

    Args:
        project_path: Path to the dbt project directory
        profiles_dir: Path to the profiles.yml directory (defaults to project_path)
        dry_run: If True, only show what would be done
        skip_seed: If True, skip the seed step
        extra_env: Optional additional environment variables (e.g., SNOWFLAKE_TRANSFORM_SCHEMA)

    Returns:
        True if successful, False otherwise
    """
    from lineage.utils.dbt import run_dbt_command

    if profiles_dir is None:
        profiles_dir = project_path

    if dry_run:
        print("DRY RUN - would perform the following dbt commands:")
        print(f"  1. dbt deps (project: {project_path})")
        if not skip_seed:
            print(f"  2. dbt seed (profiles: {profiles_dir})")
            print("  3. dbt run")
            print("  4. dbt docs generate")
        else:
            print("  2. dbt run")
            print("  3. dbt docs generate")
        return True

    # Show configuration
    print(f"  Project path: {project_path}")
    print(f"  Profiles dir: {profiles_dir}")
    profiles_yml = profiles_dir / "profiles.yml"
    if profiles_yml.exists():
        print(f"  Profiles file: {profiles_yml} (exists)")
    else:
        print(f"  WARNING: Profiles file not found: {profiles_yml}")

    # Build command list based on options
    commands = [
        (["deps"], "Running dbt deps..."),
    ]
    if not skip_seed:
        commands.append((["seed"], "Running dbt seed..."))
    commands.extend([
        (["run"], "Running dbt run..."),
        (["docs", "generate"], "Running dbt docs generate..."),
    ])

    for cmd, msg in commands:
        print(f"  {msg}")
        sys.stdout.flush()
        try:
            stdout, stderr = run_dbt_command(
                cmd,
                project_path,
                profiles_dir=profiles_dir,
                extra_env=extra_env,
            )
            # Show all output
            if stdout:
                print(stdout)
        except subprocess.CalledProcessError as e:
            print(f"  Error running dbt {cmd[0]}: {e}")
            if e.stdout:
                print("  --- dbt stdout ---")
                print(e.stdout)
            if e.stderr:
                print("  --- dbt stderr ---")
                print(e.stderr)
            return False

    print("  dbt workflow complete")
    return True


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Run dbt workflow: deps, seed, run, docs generate"
    )
    parser.add_argument(
        "project_path",
        type=Path,
        help="Path to the dbt project directory",
    )
    parser.add_argument(
        "--profiles-dir",
        type=Path,
        help="Path to profiles.yml directory (defaults to project_path)",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip the dbt seed step",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without running commands",
    )

    args = parser.parse_args()

    if not args.project_path.exists():
        print(f"Error: Project path does not exist: {args.project_path}")
        sys.exit(1)

    profiles_dir = args.profiles_dir or args.project_path
    if not args.dry_run and not profiles_dir.exists():
        print(f"Error: Profiles directory does not exist: {profiles_dir}")
        sys.exit(1)

    success = run_workflow(
        project_path=args.project_path,
        profiles_dir=profiles_dir,
        dry_run=args.dry_run,
        skip_seed=args.skip_seed,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
