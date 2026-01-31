"""Git tools for PydanticAI agents.

Provides git operations: status, diff, add, commit, branch, log.
All operations run via subprocess within the configured working directory.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from pydantic_ai import FunctionToolset, RunContext

from lineage.agent.pydantic.tools.common import ToolError, safe_tool, tool_error
from lineage.agent.pydantic.types import AgentDeps

logger = logging.getLogger(__name__)

# ============================================================================
# Helper Functions
# ============================================================================


def _get_repo_path(ctx: RunContext[AgentDeps], repo_path: Optional[str] = None) -> Path:
    """Get the git repository path from context or override.

    Returns resolved path to handle symlinks (e.g., /tmp -> /private/tmp on macOS).
    """
    if repo_path:
        return Path(repo_path).resolve()
    if ctx.deps.git_config and ctx.deps.git_config.working_directory:
        return Path(ctx.deps.git_config.working_directory).resolve()
    if ctx.deps.filesystem_config and ctx.deps.filesystem_config.working_directory:
        return Path(ctx.deps.filesystem_config.working_directory).resolve()
    return Path.cwd().resolve()


async def _run_git_command(args: List[str], cwd: Path, timeout: int = 30) -> tuple[int, str, str]:
    """Run a git command asynchronously.

    Args:
        args: Git command arguments (without 'git' prefix)
        cwd: Working directory for the command
        timeout: Command timeout in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return (
            proc.returncode or 0,
            stdout.decode("utf-8", errors="replace").strip(),
            stderr.decode("utf-8", errors="replace").strip(),
        )
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return -1, "", "git command not found"
    except Exception as e:
        return -1, "", str(e)


# ============================================================================
# Git Toolset
# ============================================================================

git_toolset = FunctionToolset()


@git_toolset.tool
@safe_tool
async def git_status(
    ctx: RunContext[AgentDeps],
    repo_path: Optional[str] = None,
) -> str | ToolError:
    """Get git repository status.

    Shows modified files, staged files, current branch, and untracked files.

    Args:
        ctx: Runtime context with agent dependencies
        repo_path: Optional path to git repository (defaults to working directory)

    Returns:
        Git status output, or ToolError on failure

    Example:
        git_status()
        git_status(repo_path="/path/to/repo")
    """
    cwd = _get_repo_path(ctx, repo_path)

    if not cwd.exists():
        return tool_error(f"Directory not found: {cwd}")

    code, stdout, stderr = await _run_git_command(["status"], cwd)

    if code != 0:
        return tool_error(f"git status failed: {stderr or stdout}")

    return stdout


@git_toolset.tool
@safe_tool
async def git_diff(
    ctx: RunContext[AgentDeps],
    staged: bool = False,
    file_path: Optional[str] = None,
    repo_path: Optional[str] = None,
) -> str | ToolError:
    """Show git diff for changes.

    Args:
        ctx: Runtime context with agent dependencies
        staged: If True, show staged changes (--cached). Default shows unstaged changes.
        file_path: Optional specific file to diff
        repo_path: Optional path to git repository (defaults to working directory)

    Returns:
        Git diff output, or ToolError on failure

    Example:
        git_diff()  # Unstaged changes
        git_diff(staged=True)  # Staged changes
        git_diff(file_path="models/marts/fct_revenue.sql")
    """
    cwd = _get_repo_path(ctx, repo_path)

    if not cwd.exists():
        return tool_error(f"Directory not found: {cwd}")

    args = ["diff"]
    if staged:
        args.append("--cached")
    if file_path:
        args.append(file_path)

    code, stdout, stderr = await _run_git_command(args, cwd)

    if code != 0:
        return tool_error(f"git diff failed: {stderr or stdout}")

    return stdout if stdout else "(no changes)"


@git_toolset.tool
@safe_tool
async def git_add(
    ctx: RunContext[AgentDeps],
    files: Optional[List[str]] = None,
    all: bool = False,
    repo_path: Optional[str] = None,
) -> str | ToolError:
    """Stage files for commit.

    Args:
        ctx: Runtime context with agent dependencies
        files: List of files to stage (e.g., ["models/marts/fct_revenue.sql"])
        all: If True, stage all modified files (git add -A)
        repo_path: Optional path to git repository (defaults to working directory)

    Returns:
        Success message or ToolError on failure

    Example:
        git_add(files=["models/marts/fct_revenue.sql", "models/schema.yml"])
        git_add(all=True)
    """
    cwd = _get_repo_path(ctx, repo_path)

    if not cwd.exists():
        return tool_error(f"Directory not found: {cwd}")

    if not files and not all:
        return tool_error("Must provide either 'files' or 'all=True'")

    args = ["add"]
    if all:
        args.append("-A")
    elif files:
        args.extend(files)

    code, stdout, stderr = await _run_git_command(args, cwd)

    if code != 0:
        return tool_error(f"git add failed: {stderr or stdout}")

    if all:
        return "✓ Staged all modified files"
    else:
        return f"✓ Staged {len(files)} file(s): {', '.join(files)}"


@git_toolset.tool
@safe_tool
async def git_commit(
    ctx: RunContext[AgentDeps],
    message: str,
    repo_path: Optional[str] = None,
) -> str | ToolError:
    """Create a git commit with staged changes.

    Args:
        ctx: Runtime context with agent dependencies
        message: Commit message
        repo_path: Optional path to git repository (defaults to working directory)

    Returns:
        Success message with commit info, or ToolError on failure

    Example:
        git_commit(message="Add new ARR calculation model")
    """
    cwd = _get_repo_path(ctx, repo_path)

    if not cwd.exists():
        return tool_error(f"Directory not found: {cwd}")

    if not message:
        return tool_error("Commit message is required")

    args = ["commit", "-m", message]
    code, stdout, stderr = await _run_git_command(args, cwd, timeout=60)

    if code != 0:
        error = stderr or stdout
        if "nothing to commit" in error.lower():
            return tool_error("Nothing to commit. Stage changes first with git_add.")
        return tool_error(f"git commit failed: {error}")

    return stdout


@git_toolset.tool
@safe_tool
async def git_branch(
    ctx: RunContext[AgentDeps],
    action: str,
    branch_name: Optional[str] = None,
    repo_path: Optional[str] = None,
) -> str | ToolError:
    """Manage git branches.

    Args:
        ctx: Runtime context with agent dependencies
        action: Action to perform: "list", "create", or "switch"
        branch_name: Branch name (required for create/switch)
        repo_path: Optional path to git repository (defaults to working directory)

    Returns:
        Branch list or success message, or ToolError on failure

    Example:
        git_branch(action="list")
        git_branch(action="create", branch_name="feature/new-model")
        git_branch(action="switch", branch_name="main")
    """
    cwd = _get_repo_path(ctx, repo_path)

    if not cwd.exists():
        return tool_error(f"Directory not found: {cwd}")

    if action not in ["list", "create", "switch"]:
        return tool_error(f"Unknown action: {action}. Use 'list', 'create', or 'switch'")

    if action in ["create", "switch"] and not branch_name:
        return tool_error(f"branch_name is required for '{action}' action")

    if action == "list":
        code, stdout, stderr = await _run_git_command(["branch", "-a"], cwd)
    elif action == "create":
        code, stdout, stderr = await _run_git_command(["branch", branch_name], cwd)
    else:  # switch
        code, stdout, stderr = await _run_git_command(["switch", branch_name], cwd)

    if code != 0:
        return tool_error(f"git branch failed: {stderr or stdout}")

    if action == "list":
        return stdout
    elif action == "create":
        return f"✓ Created branch: {branch_name}"
    else:
        return f"✓ Switched to branch: {branch_name}"


@git_toolset.tool
@safe_tool
async def git_log(
    ctx: RunContext[AgentDeps],
    limit: int = 10,
    repo_path: Optional[str] = None,
) -> str | ToolError:
    """Show recent git commit history.

    Args:
        ctx: Runtime context with agent dependencies
        limit: Number of commits to show (default: 10)
        repo_path: Optional path to git repository (defaults to working directory)

    Returns:
        Commit history, or ToolError on failure

    Example:
        git_log()
        git_log(limit=20)
    """
    cwd = _get_repo_path(ctx, repo_path)

    if not cwd.exists():
        return tool_error(f"Directory not found: {cwd}")

    args = ["log", f"-{limit}", "--oneline", "--decorate"]
    code, stdout, stderr = await _run_git_command(args, cwd)

    if code != 0:
        return tool_error(f"git log failed: {stderr or stdout}")

    return stdout if stdout else "(no commits yet)"


@git_toolset.tool
@safe_tool
async def git_push(
    ctx: RunContext[AgentDeps],
    remote: str = "origin",
    branch: Optional[str] = None,
    set_upstream: bool = False,
    repo_path: Optional[str] = None,
) -> str | ToolError:
    """Push commits to remote repository.

    Args:
        ctx: Runtime context with agent dependencies
        remote: Remote name (default: "origin")
        branch: Branch to push (default: current branch)
        set_upstream: If True, set upstream tracking (-u flag)
        repo_path: Optional path to git repository (defaults to working directory)

    Returns:
        Success message or ToolError on failure

    Example:
        git_push()
        git_push(set_upstream=True, branch="feature/new-model")
    """
    cwd = _get_repo_path(ctx, repo_path)

    if not cwd.exists():
        return tool_error(f"Directory not found: {cwd}")

    args = ["push"]
    if set_upstream:
        args.append("-u")
    args.append(remote)
    if branch:
        args.append(branch)

    code, stdout, stderr = await _run_git_command(args, cwd, timeout=120)

    if code != 0:
        return tool_error(f"git push failed: {stderr or stdout}")

    return stdout if stdout else f"✓ Pushed to {remote}"
