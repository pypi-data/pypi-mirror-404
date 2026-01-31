"""Git utility functions for repository management."""
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def clone_repo(url: str, dest_path: Path) -> None:
    """Clone a git repository to the specified path.
    
    Args:
        url: Git repository URL
        dest_path: Destination path (must not exist or be empty)
        
    Raises:
        subprocess.CalledProcessError: If git clone fails
        ValueError: If destination exists and is not empty
    """
    if dest_path.exists() and any(dest_path.iterdir()):
        raise ValueError(f"Destination path {dest_path} exists and is not empty")
    
    dest_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Cloning {url} to {dest_path}")
    subprocess.run(
        ["git", "clone", url, str(dest_path)],
        check=True,
        capture_output=True,
        text=True
    )


def is_valid_git_url(url: str) -> bool:
    """Check if a string looks like a valid git URL.
    
    Args:
        url: URL string to check
        
    Returns:
        True if valid, False otherwise
    """
    return (
        url.startswith("http://") 
        or url.startswith("https://") 
        or url.startswith("git@")
        or url.endswith(".git")
    )




