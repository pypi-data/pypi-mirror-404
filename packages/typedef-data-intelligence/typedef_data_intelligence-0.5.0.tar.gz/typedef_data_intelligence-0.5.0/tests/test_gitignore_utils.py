from pathlib import Path

from lineage.utils.gitignore import ensure_gitignore_contains


def test_ensure_gitignore_contains_creates_file(tmp_path: Path) -> None:
    changed = ensure_gitignore_contains(tmp_path, ["profiles.yml"])
    assert changed is True
    assert (tmp_path / ".gitignore").read_text() == "profiles.yml\n"


def test_ensure_gitignore_contains_is_idempotent(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("profiles.yml\n")
    changed = ensure_gitignore_contains(tmp_path, ["profiles.yml"])
    assert changed is False
    assert (tmp_path / ".gitignore").read_text() == "profiles.yml\n"


def test_ensure_gitignore_contains_appends_missing(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("node_modules/\n")
    changed = ensure_gitignore_contains(tmp_path, ["profiles.yml"])
    assert changed is True
    assert (tmp_path / ".gitignore").read_text() == "node_modules/\nprofiles.yml\n"


def test_ensure_gitignore_contains_preserves_crlf(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("node_modules/\r\n")
    changed = ensure_gitignore_contains(tmp_path, ["profiles.yml"])
    assert changed is True
    with (tmp_path / ".gitignore").open("r", encoding="utf-8", newline="") as f:
        assert f.read() == "node_modules/\r\nprofiles.yml\r\n"

