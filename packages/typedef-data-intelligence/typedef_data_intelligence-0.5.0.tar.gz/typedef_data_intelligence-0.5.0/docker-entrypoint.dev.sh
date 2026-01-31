#!/bin/bash
set -e

# Reinstall the package in editable mode to ensure mounted volumes work correctly
echo "Installing package in editable mode..."
uv pip install -e .

# Start uvicorn with hot reload
echo "Starting uvicorn..."
exec uvicorn lineage.api.pydantic:app --host 0.0.0.0 --port 8000 --reload --log-level info
