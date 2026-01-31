"""Utilities for working with .gitignore files."""

from __future__ import annotations

from pathlib import Path


def ensure_gitignore_contains(project_root: Path, entries: list[str]) -> bool:
    """Ensure the project's .gitignore contains the provided entries.

    This function is idempotent: it only appends missing entries, preserving
    existing content and comments.

    Args:
        project_root: Directory that contains the project's `.gitignore`.
        entries: Lines/patterns to ensure exist (e.g., "profiles.yml").

    Returns:
        True if the file was modified, False if no changes were needed.
    """
    if not entries:
        return False

    gitignore_path = project_root / ".gitignore"

    # Detect newline style; default to '\n'
    if gitignore_path.exists():
        # Use newline="" to avoid universal newline translation so we can preserve CRLF if present.
        with gitignore_path.open("r", encoding="utf-8", newline="") as f:
            existing_text = f.read()
    else:
        existing_text = ""
    newline = "\r\n" if "\r\n" in existing_text else "\n"

    existing_lines = existing_text.splitlines()
    existing_norm = {line.strip() for line in existing_lines}

    to_add: list[str] = []
    for entry in entries:
        normalized = entry.strip()
        if not normalized:
            continue
        if normalized in existing_norm:
            continue
        to_add.append(normalized)

    if not to_add:
        return False

    # If there's existing content and it doesn't end with a newline, add one before appending.
    updated = existing_text
    if updated and not (updated.endswith("\n") or updated.endswith("\r\n")):
        updated += newline

    # If file exists and is non-empty, append a newline separator for readability.
    if updated and not updated.endswith(newline):
        updated += newline

    updated += newline.join(to_add) + newline
    with gitignore_path.open("w", encoding="utf-8", newline="") as f:
        f.write(updated)
    return True

