#!/usr/bin/env python3
"""Reset git workspace to default branch.

Completely resets a git workspace:
1. Discards all local changes
2. Checks out the default branch (main/master)
3. Resets to origin, clearing local history
4. Deletes ALL local branches (except default)
5. Deletes corresponding non-default remote branches (except those under ``bench/``)

Usage:
    python reset_git_workspace.py /path/to/repo
    python reset_git_workspace.py  # Uses GITHUB_DBT_PROJECT_LOCAL_PATH/REPO_NAME
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_git_command(cwd: Path, *args: str, check: bool = False) -> tuple[str, int]:
    """Run a git command and return stdout and return code."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if check and result.returncode != 0:
            print(f"Git command failed: git {' '.join(args)}")
            print(f"  stderr: {result.stderr.strip()}")
        return result.stdout.strip(), result.returncode
    except FileNotFoundError:
        print("Error: git command not found")
        sys.exit(1)


def get_default_branch(cwd: Path) -> str:
    """Get the default branch name (main or master)."""
    # Try to get from origin/HEAD
    stdout, rc = run_git_command(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if rc == 0 and "/" in stdout:
        return stdout.split("/")[-1]

    # Fallback: check if main or master exists
    stdout, rc = run_git_command(cwd, "branch", "-r", "--list", "origin/main")
    if rc == 0 and stdout:
        return "main"

    stdout, rc = run_git_command(cwd, "branch", "-r", "--list", "origin/master")
    if rc == 0 and stdout:
        return "master"

    return "main"


def get_local_branches(cwd: Path) -> list[str]:
    """Get all local branch names."""
    stdout, rc = run_git_command(cwd, "branch", "--format", "%(refname:short)")
    if rc != 0:
        return []
    return [b.strip() for b in stdout.split("\n") if b.strip()]


def get_remote_branches(cwd: Path) -> set[str]:
    """Get all remote branch names (without origin/ prefix)."""
    stdout, rc = run_git_command(cwd, "branch", "-r", "--format", "%(refname:short)")
    if rc != 0:
        return set()
    branches = set()
    for line in stdout.split("\n"):
        line = line.strip()
        if line and line.startswith("origin/") and not line.endswith("/HEAD"):
            branches.add(line.replace("origin/", "", 1))
    return branches


def get_non_default_branches(cwd: Path, default_branch: str) -> list[str]:
    """Get all local branches except the default branch.

    For reset purposes, we delete ALL non-default branches - no need to
    detect which were "created locally" vs checked out from remote.
    """
    local_branches = get_local_branches(cwd)
    return [b for b in local_branches if b != default_branch]


def find_git_root(path: Path) -> Path | None:
    """Find the git root directory by walking up from the given path."""
    current = path.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


def reset_workspace(project_path: Path, dry_run: bool = False) -> bool:
    """Reset a git workspace completely.

    Args:
        project_path: Path to the git repository (or subdirectory within it)
        dry_run: If True, only show what would be done

    Returns:
        True if successful, False otherwise
    """
    if not project_path.exists():
        print(f"Path does not exist: {project_path}")
        return False

    if not project_path.is_dir():
        print(f"Path is not a directory: {project_path}")
        return False

    # Find git root by walking up from the given path
    git_root = find_git_root(project_path)
    if git_root is None:
        print(f"Not a git repository (or any parent): {project_path}")
        return False

    if git_root != project_path:
        print(f"Found git root: {git_root} (from {project_path})")

    project_path = git_root

    print(f"Repository: {project_path}")

    # Get default branch
    default_branch = get_default_branch(project_path)
    print(f"Default branch: {default_branch}")

    # Get current branch
    stdout, rc = run_git_command(project_path, "rev-parse", "--abbrev-ref", "HEAD")
    current_branch = stdout if rc == 0 else None
    print(f"Current branch: {current_branch}")

    # Find all non-default branches to delete
    branches_to_delete = get_non_default_branches(project_path, default_branch)

    if branches_to_delete:
        print(f"Branches to delete: {', '.join(branches_to_delete)}")
    else:
        print("No branches to delete")

    if dry_run:
        # Get remote branches for dry-run listing
        remote_branches = get_remote_branches(project_path)
        remote_to_delete = [
            b for b in branches_to_delete
            if b in remote_branches and not b.startswith("bench/")
        ]
        remote_to_preserve = [
            b for b in branches_to_delete
            if b in remote_branches and b.startswith("bench/")
        ]

        print("\nDRY RUN - would perform the following:")
        print("  1. Discard uncommitted changes")
        print(f"  2. Checkout {default_branch}")
        print(f"  3. Fetch and reset to origin/{default_branch}")
        print(f"  4. Delete {len(branches_to_delete)} local branches:")
        for b in branches_to_delete:
            print(f"       - {b}")
        print(f"  5. Delete {len(remote_to_delete)} remote branches:")
        for b in remote_to_delete:
            print(f"       - origin/{b}")
        if remote_to_preserve:
            print(f"     Preserve {len(remote_to_preserve)} bench/* remote branches:")
            for b in remote_to_preserve:
                print(f"       - origin/{b}")
        print("  6. Clean untracked files")
        print("  7. Prune reflog")
        return True

    # Step 1: Discard uncommitted changes
    stdout, rc = run_git_command(project_path, "status", "--porcelain")
    if stdout:
        print("Discarding uncommitted changes...")
        run_git_command(project_path, "reset", "--hard", "HEAD")
        run_git_command(project_path, "clean", "-fd")

    # Step 2: Fetch latest from origin
    print("Fetching from origin...")
    run_git_command(project_path, "fetch", "origin", "--prune")

    # Step 3: Checkout default branch
    if current_branch != default_branch:
        print(f"Checking out {default_branch}...")
        stdout, rc = run_git_command(project_path, "checkout", default_branch, check=True)
        if rc != 0:
            # Branch might not exist locally, try to create from origin
            stdout, rc = run_git_command(
                project_path, "checkout", "-B", default_branch, f"origin/{default_branch}"
            )
            if rc != 0:
                print(f"Error: Failed to checkout {default_branch}")
                return False

    # Step 4: Reset to origin (clears local history divergence)
    print(f"Resetting to origin/{default_branch}...")
    stdout, rc = run_git_command(
        project_path, "reset", "--hard", f"origin/{default_branch}", check=True
    )
    if rc != 0:
        print(f"Error: Failed to reset to origin/{default_branch}")
        return False

    # Step 5: Delete local branches
    deleted_local = 0
    for branch in branches_to_delete:
        print(f"  Deleting local branch: {branch}")
        stdout, rc = run_git_command(project_path, "branch", "-D", branch)
        if rc == 0:
            deleted_local += 1
        else:
            print(f"    Warning: Failed to delete {branch}")

    # Step 6: Delete remote branches (but preserve bench/* branches)
    deleted_remote = 0
    skipped_remote = 0
    remote_branches = get_remote_branches(project_path)
    for branch in branches_to_delete:
        if branch in remote_branches:
            # Preserve bench/* branches - these are benchmark branches
            if branch.startswith("bench/"):
                print(f"  Preserving remote branch: origin/{branch}")
                skipped_remote += 1
                continue
            print(f"  Deleting remote branch: origin/{branch}")
            stdout, rc = run_git_command(project_path, "push", "origin", "--delete", branch)
            if rc == 0:
                deleted_remote += 1
            else:
                print(f"    Warning: Failed to delete remote {branch}")

    # Step 7: Clean untracked files
    print("Cleaning untracked files...")
    run_git_command(project_path, "clean", "-fd")

    # Step 8: Prune reflog to clear local history
    print("Pruning reflog...")
    run_git_command(project_path, "reflog", "expire", "--expire=now", "--all")
    run_git_command(project_path, "gc", "--prune=now")

    print("\nReset complete:")
    print(f"  - Deleted {deleted_local} local branches")
    print(f"  - Deleted {deleted_remote} remote branches")
    if skipped_remote > 0:
        print(f"  - Preserved {skipped_remote} bench/* remote branches")
    print(f"  - Workspace reset to origin/{default_branch}")

    return True


def main():
    """Main function to reset git workspace."""
    parser = argparse.ArgumentParser(
        description="Reset a git workspace to default branch, deleting all non-default branches (local and remote, except bench/*)"
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Path to git repository (defaults to GITHUB_DBT_PROJECT_LOCAL_PATH/REPO_NAME)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    args = parser.parse_args()

    # Determine project path
    if args.path:
        project_path = args.path
    else:
        # Fallback to environment variables for backwards compatibility
        local_path = os.getenv("GITHUB_DBT_PROJECT_LOCAL_PATH")
        repo_name = os.getenv("GITHUB_DBT_PROJECT_REPO_NAME")

        if not local_path or not repo_name:
            print("Error: Either provide a path argument or set environment variables:")
            print("  GITHUB_DBT_PROJECT_LOCAL_PATH and GITHUB_DBT_PROJECT_REPO_NAME")
            sys.exit(1)

        project_path = Path(local_path) / repo_name

    # Find git root if path points to a subdirectory
    original_path = project_path
    while project_path != project_path.parent:
        if (project_path / ".git").exists():
            break
        project_path = project_path.parent

    if not (project_path / ".git").exists():
        print(f"Could not find git repository at or above: {original_path}")
        sys.exit(1)

    success = reset_workspace(project_path, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
