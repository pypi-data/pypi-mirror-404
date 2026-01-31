"""dbt CLI tools for PydanticAI agents.

Provides dbt command execution via subprocess within the configured dbt project.
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional

from pydantic_ai import FunctionToolset, RunContext

from lineage.agent.pydantic.tools.common import ToolError, safe_tool, tool_error
from lineage.agent.pydantic.types import AgentDeps, DbtResult
from lineage.utils.dbt import _dbt_venv_bin, get_adapter_venv_dir

logger = logging.getLogger(__name__)

# Maximum output size to prevent token overflow
MAX_OUTPUT_SIZE = 20000


# ============================================================================
# Helper Functions
# ============================================================================


def _get_dbt_project_path(ctx: RunContext[AgentDeps]) -> Path:
    """Get the dbt project path from context.

    Returns resolved path to handle symlinks (e.g., /tmp -> /private/tmp on macOS).
    """
    if ctx.deps.git_config and ctx.deps.git_config.working_directory:
        return Path(ctx.deps.git_config.working_directory).resolve()
    if ctx.deps.filesystem_config and ctx.deps.filesystem_config.working_directory:
        return Path(ctx.deps.filesystem_config.working_directory).resolve()
    return Path.cwd().resolve()


def _truncate_output(output: str, max_size: int = MAX_OUTPUT_SIZE) -> str:
    """Truncate output if it exceeds max size, keeping the tail."""
    if len(output) > max_size:
        return f"... (truncated, showing last {max_size} chars)\n" + output[-max_size:]
    return output


# ============================================================================
# dbt Toolset
# ============================================================================

dbt_toolset = FunctionToolset()


@dbt_toolset.tool
@safe_tool
async def dbt_cli(
    ctx: RunContext[AgentDeps],
    args: List[str],
    timeout_s: int = 1800,
) -> DbtResult | ToolError:
    """Execute a dbt command.

    Runs dbt CLI with the provided arguments in the configured dbt project directory.
    Prefers the project's venv dbt if available, otherwise uses 'uv run --no-project dbt'
    when uv is available, else falls back to 'dbt' directly.

    Args:
        ctx: Runtime context with agent dependencies
        args: List of dbt command arguments (e.g., ["run", "--select", "my_model"])
        timeout_s: Command timeout in seconds (default: 1800 = 30 minutes)

    Returns:
        DbtResult with exit code and output, or ToolError on failure

    Example:
        dbt_cli(args=["run"])
        dbt_cli(args=["test", "--select", "my_model"])
        dbt_cli(args=["build", "--select", "tag:daily"])
        dbt_cli(args=["compile", "--select", "fct_revenue"])
        dbt_cli(args=["run", "--select", "my_model+"])  # With downstream
    """
    project_dir = _get_dbt_project_path(ctx)

    if not project_dir.exists():
        return tool_error(f"dbt project directory not found: {project_dir}")

    # Build command - prefer shared adapter venv dbt, then uv without project mode
    adapter = os.getenv("TYPEDEF_DBT_ADAPTER", "snowflake")
    venv_dir = get_adapter_venv_dir(adapter)
    venv_dbt = _dbt_venv_bin(venv_dir)
    if venv_dbt:
        cmd = [str(venv_dbt), *args]
    elif shutil.which("uv"):
        # Use --no-project so uv doesn't treat the dbt repo as a uv project.
        cmd = ["uv", "run", "--no-project", "dbt", *args]
    else:
        cmd = ["dbt", *args]

    cmd_str = " ".join(cmd)
    logger.info(f"Running dbt command: {cmd_str} in {project_dir}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout_s,
        )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        exit_code = proc.returncode or 0

        # Truncate output if too long
        stdout = _truncate_output(stdout)
        if stderr:
            stderr = _truncate_output(stderr)

        return DbtResult(
            command=cmd_str,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr if stderr else None,
            project_dir=str(project_dir),
        )

    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()  # Clean up zombie process
        return tool_error(f"dbt command timed out after {timeout_s} seconds: {cmd_str}")
    except FileNotFoundError:
        return tool_error("dbt command not found. Ensure dbt is installed and in PATH.")
    except Exception as e:
        logger.error(f"Error running dbt command: {e}")
        return tool_error(f"Error running dbt: {e}")


@dbt_toolset.tool
@safe_tool
async def dbt_run(
    ctx: RunContext[AgentDeps],
    select: Optional[str] = None,
    exclude: Optional[str] = None,
    full_refresh: bool = False,
    timeout_s: int = 1800,
) -> DbtResult | ToolError:
    """Run dbt models.

    Convenience wrapper for `dbt run` with common options.

    Args:
        ctx: Runtime context with agent dependencies
        select: Model selection (e.g., "my_model", "my_model+", "tag:daily")
        exclude: Models to exclude
        full_refresh: If True, run with --full-refresh
        timeout_s: Command timeout in seconds (default: 1800)

    Returns:
        DbtResult with exit code and output, or ToolError on failure

    Example:
        dbt_run()  # Run all models
        dbt_run(select="fct_revenue")
        dbt_run(select="marts.*", full_refresh=True)
    """
    args = ["run"]
    if select:
        args.extend(["--select", select])
    if exclude:
        args.extend(["--exclude", exclude])
    if full_refresh:
        args.append("--full-refresh")

    return await dbt_cli(ctx, args=args, timeout_s=timeout_s)


@dbt_toolset.tool
@safe_tool
async def dbt_test(
    ctx: RunContext[AgentDeps],
    select: Optional[str] = None,
    exclude: Optional[str] = None,
    timeout_s: int = 600,
) -> DbtResult | ToolError:
    """Run dbt tests.

    Convenience wrapper for `dbt test` with common options.

    Args:
        ctx: Runtime context with agent dependencies
        select: Test selection (e.g., "my_model", "source:my_source")
        exclude: Tests to exclude
        timeout_s: Command timeout in seconds (default: 600)

    Returns:
        DbtResult with exit code and output, or ToolError on failure

    Example:
        dbt_test()  # Run all tests
        dbt_test(select="fct_revenue")
    """
    args = ["test"]
    if select:
        args.extend(["--select", select])
    if exclude:
        args.extend(["--exclude", exclude])

    return await dbt_cli(ctx, args=args, timeout_s=timeout_s)


@dbt_toolset.tool
@safe_tool
async def dbt_build(
    ctx: RunContext[AgentDeps],
    select: Optional[str] = None,
    exclude: Optional[str] = None,
    full_refresh: bool = False,
    timeout_s: int = 1800,
) -> DbtResult | ToolError:
    """Build dbt models (run + test).

    Convenience wrapper for `dbt build` with common options.
    Runs models and their tests in DAG order.

    Args:
        ctx: Runtime context with agent dependencies
        select: Model selection (e.g., "my_model", "my_model+", "tag:daily")
        exclude: Models to exclude
        full_refresh: If True, build with --full-refresh
        timeout_s: Command timeout in seconds (default: 1800)

    Returns:
        DbtResult with exit code and output, or ToolError on failure

    Example:
        dbt_build()  # Build all models
        dbt_build(select="fct_revenue+")  # Build model and downstream
    """
    args = ["build"]
    if select:
        args.extend(["--select", select])
    if exclude:
        args.extend(["--exclude", exclude])
    if full_refresh:
        args.append("--full-refresh")

    return await dbt_cli(ctx, args=args, timeout_s=timeout_s)


@dbt_toolset.tool
@safe_tool
async def dbt_compile(
    ctx: RunContext[AgentDeps],
    select: Optional[str] = None,
    timeout_s: int = 300,
) -> DbtResult | ToolError:
    """Compile dbt models to SQL without executing.

    Useful for reviewing generated SQL before running.

    Args:
        ctx: Runtime context with agent dependencies
        select: Model selection (e.g., "my_model")
        timeout_s: Command timeout in seconds (default: 300)

    Returns:
        DbtResult with compiled SQL info, or ToolError on failure

    Example:
        dbt_compile(select="fct_revenue")
    """
    args = ["compile"]
    if select:
        args.extend(["--select", select])

    return await dbt_cli(ctx, args=args, timeout_s=timeout_s)
