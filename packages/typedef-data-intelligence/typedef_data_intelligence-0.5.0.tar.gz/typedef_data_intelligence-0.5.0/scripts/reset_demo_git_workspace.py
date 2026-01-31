#!/usr/bin/env python3
"""Reset git workspace to main branch.

Checks if GITHUB_DBT_PROJECT_LOCAL_PATH/GITHUB_DBT_PROJECT_REPO_NAME exists,
and if it's a git repo on a non-main branch, deletes that branch and checks out main.
"""
import os
import subprocess
import sys
from pathlib import Path


def run_git_command(cwd: Path, *args: str) -> tuple[str, int]:
    """Run a git command and return stdout and return code."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip(), result.returncode
    except FileNotFoundError:
        print("Error: git command not found")
        sys.exit(1)


def get_current_branch(cwd: Path) -> str | None:
    """Get the current git branch name."""
    stdout, returncode = run_git_command(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    if returncode == 0:
        return stdout
    return None

def get_default_branch(cwd: Path) -> str:
    """Get the default branch name."""
    stdout, returncode = run_git_command(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    split_stdout = stdout.split("/")
    if returncode == 0 and len(split_stdout) > 0:
        return split_stdout[1]
    return "main"


def main():
    """Main function to reset git workspace."""
    local_path = os.getenv("GITHUB_DBT_PROJECT_LOCAL_PATH")
    repo_name = os.getenv("GITHUB_DBT_PROJECT_REPO_NAME")

    if not local_path or not repo_name:
        print("Error: GITHUB_DBT_PROJECT_LOCAL_PATH and GITHUB_DBT_PROJECT_REPO_NAME must be set")
        sys.exit(1)

    project_path = Path(local_path) / repo_name

    if not project_path.exists():
        print(f"Path does not exist: {project_path}")
        sys.exit(0)

    if not project_path.is_dir():
        print(f"Path is not a directory: {project_path}")
        sys.exit(1)

    # Check if it's a git repository
    git_dir = project_path / ".git"
    if not git_dir.exists():
        print(f"Not a git repository: {project_path}")
        sys.exit(0)

    default_branch_name = get_default_branch(project_path)
    # Get current branch
    current_branch = get_current_branch(project_path)
    if not current_branch:
        print(f"Error: Could not determine current branch in {project_path}")
        sys.exit(1)

    print(f"Repository: {project_path}")
    print(f"Current branch: {current_branch}")

    # Get all local branches
    stdout, returncode = run_git_command(project_path, "branch", "--format", "%(refname:short)")
    if returncode != 0:
        print(f"Error: Failed to list branches: {stdout}")
        sys.exit(1)

    all_branches = [b.strip() for b in stdout.split("\n") if b.strip()]
    branches_to_delete = [
        b for b in all_branches
        if b != default_branch_name and not b.startswith("bench/")
    ]
    preserved_branches = [b for b in all_branches if b.startswith("bench/")]

    if preserved_branches:
        print(f"Preserving {len(preserved_branches)} branch(es) starting with 'bench/': {', '.join(preserved_branches)}")

    if not branches_to_delete:
        print(f"No branches to delete (only {default_branch_name} exists)")
    else:
        print(f"Found {len(branches_to_delete)} branch(es) to delete: {', '.join(branches_to_delete)}")

    # stash any changes that are not committed
    stdout, returncode = run_git_command(project_path, "diff", "--name-only")
    if returncode == 0 and stdout:
        print(f"Warning: Found uncommitted changes: {stdout}. Throwing away changes...")
        stdout, returncode = run_git_command(project_path, "reset", "--hard", "HEAD")
        if returncode != 0:
            print(f"Error: Failed to reset changes: {stdout}")
            sys.exit(1)

    # Checkout main if not already on it
    if current_branch != default_branch_name:
        print(f"Checking out {default_branch_name} branch")
        stdout, returncode = run_git_command(project_path, "checkout", default_branch_name)
        if returncode != 0:
            print(f"Error: Failed to checkout {default_branch_name}: {stdout}")
            sys.exit(1)
    else:
        print(f"Already on {default_branch_name} branch")

    # Pull main from origin
    print(f"Pulling {default_branch_name} from origin")
    stdout, returncode = run_git_command(project_path, "pull", "origin", default_branch_name)
    if returncode != 0:
        print(f"Error: Failed to pull {default_branch_name} from origin: {stdout}")
        sys.exit(1)

    # Reset main to origin/main (or origin/master, or whatever the default branch is)
    print(f"Resetting {default_branch_name} to origin/{default_branch_name}")
    stdout, returncode = run_git_command(project_path, "reset", "--hard", f"origin/{default_branch_name}")
    if returncode != 0:
        print(f"Error: Failed to reset {default_branch_name} to origin/{default_branch_name}: {stdout}")
        sys.exit(1)

    # Delete all local branches except main
    deleted_branches = []
    failed_branches = []

    for branch in branches_to_delete:
        print(f"Deleting local branch: {branch}")
        stdout, returncode = run_git_command(project_path, "branch", "-D", branch)
        if returncode != 0:
            print(f"Warning: Failed to force delete local branch {branch}: {stdout}")
            # Try without -D (force delete)
            stdout, returncode = run_git_command(project_path, "branch", "-d", branch)
            if returncode != 0:
                print(f"Warning: Could not delete local branch {branch}: {stdout}")
                failed_branches.append(branch)
            else:
                deleted_branches.append(branch)
        else:
            deleted_branches.append(branch)

    # Delete remote branches for all deleted local branches
    remote_branches_deleted = 0
    for branch in deleted_branches:
        stdout, returncode = run_git_command(project_path, "ls-remote", "--heads", "origin", branch)
        if returncode == 0 and stdout:
            print(f"Deleting remote branch: origin/{branch}")
            stdout, returncode = run_git_command(project_path, "push", "origin", "--delete", branch)
            if returncode == 0:
                remote_branches_deleted += 1
            else:
                print(f"Warning: Failed to delete remote branch origin/{branch}: {stdout}")

    if failed_branches:
        print(f"⚠️  Warning: Failed to delete {len(failed_branches)} branch(es): {', '.join(failed_branches)}")

    if deleted_branches:
        remote_info = f" and {remote_branches_deleted} remote branch(es)" if remote_branches_deleted > 0 else ""
        print(f"✅ Successfully deleted {len(deleted_branches)} local branch(es){remote_info} and reset to {default_branch_name} branch")
    else:
        print(f"✅ Successfully reset to {default_branch_name} branch (no branches to delete)")


if __name__ == "__main__":
    main()
