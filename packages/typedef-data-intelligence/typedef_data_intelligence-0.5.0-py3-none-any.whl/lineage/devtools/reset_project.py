#!/usr/bin/env python3
"""Reset a specific project's Snowflake objects, git workspace, and Linear tickets.

This script is designed to run from ~/.typedef/ using the TUI-created config.
It will:
1. Drop Snowflake objects for the specified project
2. Reset the git workspace to the default branch, discarding all local branches and history, and deleting corresponding non-default remote branches (except those under ``bench/``).
3. Reset Linear tickets (delete existing and seed demo tickets)
4. Run dbt build workflow (deps, seed, run, docs generate)

Usage:
    uv run python -m lineage.devtools.reset_project <project_name>
    uv run python -m lineage.devtools.reset_project mattermost
    uv run python -m lineage.devtools.reset_project --list-projects
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import yaml


def load_typedef_config(typedef_dir: Path) -> dict:
    """Load the config.yaml from ~/.typedef/"""
    config_path = typedef_dir / "config.yaml"
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        return yaml.safe_load(f)


def load_env_file(env_path: Path) -> dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env_vars[key.strip()] = value.strip()
    return env_vars


def load_profiles_yml(profiles_dir: Path, profile_name: str) -> dict:
    """Load Snowflake connection info from profiles.yml"""
    profiles_path = profiles_dir / "profiles.yml"
    if not profiles_path.exists():
        return {}

    with open(profiles_path) as f:
        profiles = yaml.safe_load(f)

    if profile_name not in profiles:
        return {}

    profile = profiles[profile_name]
    target = profile.get("target", "prod")
    outputs = profile.get("outputs", {})

    if target not in outputs:
        return {}

    return outputs[target]


def get_snowflake_credentials(config: dict, project_config: dict) -> dict:
    """Extract Snowflake credentials from config and profiles."""
    creds = {}

    # First, try to get from project's profile
    profiles_dir_str = project_config.get("profiles_dir")
    profile_name = project_config.get("profile_name", "snowflake")

    if profiles_dir_str:
        profiles_dir = Path(profiles_dir_str)
        profile_creds = load_profiles_yml(profiles_dir, profile_name)
        if profile_creds:
            creds = {
                "account": profile_creds.get("account"),
                "user": profile_creds.get("user"),
                "warehouse": profile_creds.get("warehouse"),
                "role": profile_creds.get("role"),
                "database": profile_creds.get("database"),
                "private_key_path": profile_creds.get("private_key_path"),
            }

    # Override with data section from config (shared defaults)
    data_config = config.get("data", {})
    if data_config.get("backend") == "snowflake":
        if data_config.get("account"):
            creds["account"] = data_config["account"]
        if data_config.get("user"):
            creds["user"] = data_config["user"]
        if data_config.get("warehouse"):
            creds["warehouse"] = data_config["warehouse"]
        if data_config.get("role"):
            creds["role"] = data_config["role"]
        if data_config.get("database"):
            creds["database"] = data_config["database"]
        if data_config.get("private_key_path"):
            creds["private_key_path"] = data_config["private_key_path"]

    # Override with project-specific data overrides
    project_data = project_config.get("data", {})
    for key in ["account", "user", "warehouse", "role", "database", "private_key_path"]:
        if project_data.get(key):
            creds[key] = project_data[key]

    # Also check allowed_databases for the project's database
    allowed_dbs = project_config.get("allowed_databases", [])
    default_db = project_config.get("default_database")
    if default_db:
        creds["database"] = default_db
    elif allowed_dbs:
        creds["database"] = allowed_dbs[0]

    return creds


def detect_project_type(project_config: dict) -> Optional[str]:
    """Detect project type from config (mattermost, medallion, etc.)."""
    dbt_path = project_config.get("dbt_path", "").lower()
    name = project_config.get("name", "").lower()
    graph_name = project_config.get("graph_name", "").lower()

    if "mattermost" in dbt_path or "mattermost" in name or "mattermost" in graph_name:
        return "mattermost"
    if "medallion" in dbt_path or "medallion" in name or "medallion" in graph_name:
        return "medallion"
    return None


def drop_snowflake_objects(
    creds: dict,
    project_type: Optional[str] = None,
    max_workers: int = 4,
    dry_run: bool = False,
) -> None:
    """Drop Snowflake objects in the specified database.

    Args:
        creds: Snowflake credentials dict
        project_type: "mattermost" or "medallion" to determine schema preservation
        max_workers: Number of parallel workers for dropping objects
        dry_run: If True, only show what would be dropped
    """
    from lineage.devtools.drop_snowflake_tables import drop_objects_from_config

    # Validate credentials
    required = ["account", "user", "warehouse", "role", "database", "private_key_path"]
    missing = [k for k in required if not creds.get(k)]
    if missing:
        print(f"Error: Missing Snowflake credentials: {missing}")
        for key in required:
            print(f"  {key}: {creds.get(key)}")
        sys.exit(1)

    drop_objects_from_config(
        creds=creds,
        project_type=project_type,
        max_workers=max_workers,
        dry_run=dry_run,
    )


def reset_git_workspace(project_path: Path, dry_run: bool = False) -> None:
    """Reset git workspace to default branch.

    Args:
        project_path: Path to the git repository (or subdirectory within it)
        dry_run: If True, only show what would be done
    """
    from lineage.devtools.reset_git_workspace import reset_workspace

    # Flush stdout to ensure correct output order
    sys.stdout.flush()
    reset_workspace(project_path, dry_run=dry_run)


def do_reset_linear_workspace(config: dict, dry_run: bool = False) -> None:
    """Reset Linear workspace - delete existing issues and seed demo tickets.

    Args:
        config: Typedef config dict containing ticket settings
        dry_run: If True, only show what would be done
    """
    from lineage.devtools.reset_linear_workspace import reset_workspace

    ticket_config = config.get("ticket", {})
    if not ticket_config.get("enabled"):
        print("Ticketing not enabled in config")
        return

    team_id = ticket_config.get("team_id")
    if not team_id:
        print("No team_id configured for ticketing")
        return

    # Flush stdout to ensure correct output order
    sys.stdout.flush()
    reset_workspace(team_id=team_id, dry_run=dry_run)


def do_run_dbt_workflow(
    project_path: Path,
    profiles_dir: Path,
    dry_run: bool = False,
    extra_env: Optional[dict[str, str]] = None,
) -> bool:
    """Run the complete dbt workflow: deps, seed, run, docs generate.

    Args:
        project_path: Path to the dbt project directory
        profiles_dir: Path to the profiles.yml directory
        dry_run: If True, only show what would be done
        extra_env: Optional environment variables for dbt (for env_var() in profiles)

    Returns:
        True if successful, False otherwise
    """
    from lineage.devtools.run_dbt_workflow import run_workflow

    # Flush stdout to ensure correct output order
    sys.stdout.flush()
    return run_workflow(
        project_path=project_path,
        profiles_dir=profiles_dir,
        dry_run=dry_run,
        extra_env=extra_env,
    )


def find_project_by_alias(config: dict, alias: str) -> tuple[Optional[str], Optional[dict]]:
    """Find a project by name or alias (mattermost, medallion, demo, etc.)"""
    projects = config.get("projects", {})

    # Direct match
    if alias in projects:
        return alias, projects[alias]

    # Check by dbt_path content
    alias_lower = alias.lower()
    for name, proj in projects.items():
        dbt_path = proj.get("dbt_path", "").lower()
        if alias_lower in dbt_path:
            return name, proj
        # Also check graph_name
        if proj.get("graph_name", "").lower() == alias_lower:
            return name, proj

    return None, None


def main():
    parser = argparse.ArgumentParser(
        description="Reset a project's Snowflake objects, git workspace, and Linear tickets"
    )
    parser.add_argument(
        "project",
        nargs="?",
        default=None,
        help="Project name or alias (mattermost, medallion, demo, etc.)"
    )
    parser.add_argument(
        "--typedef-dir",
        type=Path,
        default=Path.home() / ".typedef",
        help="Path to typedef directory (default: ~/.typedef)"
    )
    parser.add_argument(
        "--drop-staging",
        action="store_true",
        help="Also drop staging schemas (default: preserve staging)"
    )
    parser.add_argument(
        "--skip-snowflake",
        action="store_true",
        help="Skip Snowflake object cleanup"
    )
    parser.add_argument(
        "--skip-git",
        action="store_true",
        help="Skip git workspace reset"
    )
    parser.add_argument(
        "--skip-linear",
        action="store_true",
        help="Skip Linear ticket reset"
    )
    parser.add_argument(
        "--skip-dbt",
        action="store_true",
        help="Skip dbt build workflow (deps, seed, run, docs)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--list-projects",
        action="store_true",
        help="List available projects and exit"
    )
    parser.add_argument(
        "--source-database",
        type=str,
        default="RAW_YONI",
        help="Source database name for dbt sources (default: RAW_YONI). Only used for mattermost projects."
    )

    args = parser.parse_args()

    typedef_dir = args.typedef_dir
    if not typedef_dir.exists():
        print(f"Error: typedef directory not found: {typedef_dir}")
        sys.exit(1)

    # Load config
    config = load_typedef_config(typedef_dir)

    # Handle --list-projects
    if args.list_projects:
        projects = config.get("projects", {})
        print("Available projects:")
        for name, proj in projects.items():
            dbt_path = proj.get("dbt_path", "N/A")
            print(f"  {name}: {dbt_path}")
        sys.exit(0)

    # Require project argument if not listing
    if not args.project:
        print("Error: project argument is required")
        print("Use --list-projects to see available projects")
        sys.exit(1)

    # Load .env from typedef dir
    env_vars = load_env_file(typedef_dir / ".env")
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value

    # Find the project
    project_name, project_config = find_project_by_alias(config, args.project)
    if not project_config:
        print(f"Error: Project '{args.project}' not found in config")
        print(f"Available projects: {list(config.get('projects', {}).keys())}")
        sys.exit(1)

    dry_run = args.dry_run
    if dry_run:
        print("DRY RUN - no changes will be made\n")

    print(f"Resetting project: {project_name}")
    print(f"  dbt_path: {project_config.get('dbt_path')}")

    # Drop Snowflake objects
    if not args.skip_snowflake:
        print("\n--- Dropping Snowflake objects ---")
        creds = get_snowflake_credentials(config, project_config)
        project_type = detect_project_type(project_config)
        if project_type:
            print(f"  Project type: {project_type}")
        drop_snowflake_objects(
            creds=creds,
            project_type=project_type if not args.drop_staging else None,
            max_workers=4,
            dry_run=dry_run,
        )

    # Reset git workspace
    if not args.skip_git:
        print("\n--- Resetting git workspace ---")
        dbt_path = project_config.get("dbt_path")
        if dbt_path:
            # The script handles finding the git root from a subdirectory
            reset_git_workspace(Path(dbt_path), dry_run=dry_run)
        else:
            print("No dbt_path configured for this project")

    # Reset Linear workspace
    if not args.skip_linear:
        print("\n--- Resetting Linear workspace ---")
        do_reset_linear_workspace(config, dry_run=dry_run)

    # Run dbt build workflow
    if not args.skip_dbt:
        print("\n--- Running dbt build workflow ---")
        dbt_path = project_config.get("dbt_path")
        if dbt_path:
            dbt_project_path = Path(dbt_path)
            project_type = detect_project_type(project_config)

            # Use typedef-managed profiles directory
            profiles_dir_str = project_config.get("profiles_dir")
            if profiles_dir_str:
                profiles_dir = Path(profiles_dir_str)
            else:
                # Fallback to project's profile directory
                profiles_dir = dbt_project_path / "profile"

            # Get Snowflake credentials
            creds = get_snowflake_credentials(config, project_config)

            # Build env vars for dbt sources that use env_var() syntax
            dbt_env = {
                # MATTERMOST_ANALYTICS_DB is used by rudder_support sources
                "MATTERMOST_ANALYTICS_DB": creds.get("database", ""),
            }

            # For mattermost projects, also set source database
            if project_type == "mattermost":
                dbt_env["MATTERMOST_RAW_DB"] = args.source_database
                print(f"  MATTERMOST_RAW_DB: {args.source_database}")
                print(f"  MATTERMOST_ANALYTICS_DB: {dbt_env['MATTERMOST_ANALYTICS_DB']}")

            print(f"  profiles_dir: {profiles_dir}")

            if not dry_run and not profiles_dir.exists():
                print(f"Warning: profiles directory not found: {profiles_dir}")
                print("  Skipping dbt build")
            else:
                success = do_run_dbt_workflow(
                    project_path=dbt_project_path,
                    profiles_dir=profiles_dir,
                    dry_run=dry_run,
                    extra_env=dbt_env,
                )
                if not success and not dry_run:
                    print("Warning: dbt workflow failed")
        else:
            print("No dbt_path configured for this project")

    print("\nReset complete!" if not dry_run else "\nDry run complete!")


if __name__ == "__main__":
    main()
