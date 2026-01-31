"""dbt utility functions for project management."""
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TYPEDEF_HOME = Path.home() / ".typedef"
TYPEDEF_VENVS = TYPEDEF_HOME / "venvs"


def get_adapter_venv_dir(adapter: str) -> Path:
    """Return the venv directory for a dbt adapter.

    Venvs are shared across projects that use the same adapter.

    Args:
        adapter: The dbt adapter name (e.g., "snowflake", "bigquery")

    Returns:
        Path to the venv directory (e.g., ~/.typedef/venvs/dbt-snowflake/)
    """
    return TYPEDEF_VENVS / f"dbt-{adapter}"


def _dbt_venv_bin(venv_dir: Path) -> Optional[Path]:
    """Return the dbt binary path from the venv, if present.

    Args:
        venv_dir: Path to the virtual environment directory

    Returns:
        Path to dbt binary if found, None otherwise
    """
    if not venv_dir.exists():
        return None

    unix_bin = venv_dir / "bin" / "dbt"
    if unix_bin.exists():
        return unix_bin

    win_bin = venv_dir / "Scripts" / "dbt.exe"
    if win_bin.exists():
        return win_bin

    return None


def run_dbt_command(
    command: list[str],
    project_dir: Path,
    profiles_dir: Optional[Path] = None,
    venv_dir: Optional[Path] = None,
    extra_env: Optional[dict[str, str]] = None,
) -> tuple[str, str]:
    """Run a dbt command in the specified project directory.

    Args:
        command: dbt command arguments (e.g., ["deps"], ["docs", "generate"])
        project_dir: dbt project directory
        profiles_dir: Optional profiles directory override
        venv_dir: Optional venv directory containing dbt installation
        extra_env: Optional additional environment variables to set

    Returns:
        Tuple of (stdout, stderr)

    Raises:
        subprocess.CalledProcessError: If command fails
    """
    # Build env vars
    env = {}
    if profiles_dir:
        env["DBT_PROFILES_DIR"] = str(profiles_dir)
    if extra_env:
        env.update(extra_env)

    # Build base command
    venv_dbt = _dbt_venv_bin(venv_dir) if venv_dir else None
    if venv_dbt:
        cmd = [str(venv_dbt)] + command
    elif shutil.which("uv"):
        # Use --no-project so uv doesn't treat the dbt repo as a uv project.
        cmd = ["uv", "run", "--no-project", "dbt"] + command
    else:
        cmd = ["dbt"] + command

    logger.info(f"Running dbt command: {' '.join(cmd)} in {project_dir}")

    # If we have env vars, merge with system env
    run_env = None
    if env:
        import os
        run_env = os.environ.copy()
        run_env.update(env)

    result = subprocess.run(
        cmd,
        cwd=project_dir,
        check=True,
        capture_output=True,
        text=True,
        env=run_env
    )

    return result.stdout, result.stderr


