"""Shared fixtures for Linear tests."""
import os
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Load .env from monorepo root (one level above package root)
package_root = Path(__file__).parent.parent.parent
repo_root = package_root.parent
for candidate in [repo_root / ".env", repo_root / ".local.env", repo_root / ".test.env"]:
    if candidate.exists():
        load_dotenv(candidate)


@pytest.fixture
def linear_api_key():
    """Fixture for Linear API key."""
    key = os.getenv("LINEAR_DATA_ENGINEER_API_KEY")
    if not key:
        pytest.skip("LINEAR_DATA_ENGINEER_API_KEY environment variable is not set")
    return key


@pytest.fixture
def linear_team_id():
    """Fixture for Linear team ID."""
    team_id = os.getenv("LINEAR_TEAM_ID")
    if not team_id:
        pytest.skip("LINEAR_TEAM_ID environment variable is not set")
    return team_id


@pytest.fixture
def config_path():
    """Fixture for config.yml path."""
    repo_root = Path(__file__).parent.parent.parent
    config_path = repo_root / "config.yml"
    if not config_path.exists():
        pytest.skip("config.yml not found")
    return config_path

