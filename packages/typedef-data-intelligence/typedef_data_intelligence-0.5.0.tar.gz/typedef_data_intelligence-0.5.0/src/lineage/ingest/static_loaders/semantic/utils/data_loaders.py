"""Data loading utilities for SQL Analyzer."""

import os
from pathlib import Path
from typing import Union
import fenic as fc


def load_sql_files(path: Union[str, Path], session: fc.Session = None) -> fc.DataFrame:
    """
    Load SQL files from a path (file or directory) into a Fenic DataFrame.

    Args:
        path: Path to a SQL file or directory containing SQL files
        session: Optional Fenic session. If not provided, creates a new one

    Returns:
        A Fenic DataFrame with columns: path, filename, sql
    """
    from ..config.session import create_session

    path = Path(path)

    if session is None:
        session = create_session()

    sql_files = []

    if path.is_file():
        if path.suffix.lower() == ".sql":
            with open(path, "r", encoding="utf-8") as f:
                sql_files.append(
                    {
                        "path": str(path.absolute()),
                        "filename": path.name,
                        "sql": f.read(),
                    }
                )
    elif path.is_dir():
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".sql"):
                    file_path = Path(root) / file
                    with open(file_path, "r", encoding="utf-8") as f:
                        sql_files.append(
                            {
                                "path": str(file_path.absolute()),
                                "filename": file,
                                "sql": f.read(),
                            }
                        )
    else:
        raise ValueError(f"Path {path} does not exist")

    if not sql_files:
        sql_files = [{"path": None, "filename": None, "sql": None}]

    return session.create_dataframe(sql_files)
