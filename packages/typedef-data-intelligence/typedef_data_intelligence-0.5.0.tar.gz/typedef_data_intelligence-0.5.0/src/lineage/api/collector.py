"""OpenLineage event collection API endpoints.

This module provides FastAPI endpoints for collecting and processing OpenLineage
events from dbt runs and other data pipeline tools.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from fastapi import Depends, HTTPException
from lineage.api.app import AppState, app, get_app_state
from openlineage.client.event_v2 import (
    Dataset,
    Job,
    Run,
    RunEvent,
    RunState,
)

logger = logging.getLogger(__name__)

# Capture configuration - set CAPTURE_EVENTS_DIR to enable
_capture_dir: Path | None = None
if capture_env := os.getenv("CAPTURE_EVENTS_DIR"):
    _capture_dir = Path(capture_env)
    _capture_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Event capture enabled: %s", _capture_dir)

def _capture_event(event: dict) -> None:
    """Save event to file for testing/replay."""
    if _capture_dir is None:
        return
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        run = event.get("run", {})
        run_id = run.get("runId") or "unknown"
        run_id_short = run_id[:8]
        filename = f"{timestamp}_{event.get('eventType')}_{run_id_short}.json"
        filepath = _capture_dir / filename
        
        # Write the event as JSON (use model_dump for Pydantic v2 or dict() for v1)
        with open(filepath, "w") as f:
            json.dump(event, f, indent=2, default=str)
        
        logger.debug("Captured event to %s", filepath)
    except Exception as exc:
        logger.error("Failed to capture event: %s", exc)


@app.post("/api/v1/lineage")
async def receive_event(event: dict, state: AppState = Depends(get_app_state)): #noqa: B008 expected for fastapi
    """Receive an OpenLineage event and load it into the lineage graph."""
    # Capture event to file if enabled
    _capture_event(event)
    
    try:
        # Build typed RunEvent using openlineage client models
        et = event.get("eventType", "OTHER")
        run_d = event.get("run", {}) or {}
        job_d = event.get("job", {}) or {}
        inputs_d = event.get("inputs", []) or []
        outputs_d = event.get("outputs", []) or []

        run_ev = RunEvent(
            eventType=RunState[et] if isinstance(et, str) else et,
            eventTime=event.get("eventTime"),
            run=Run(runId=run_d.get("runId", ""), facets=run_d.get("facets") or {}),
            job=Job(namespace=job_d.get("namespace", ""), name=job_d.get("name", "")),
            inputs=[Dataset(namespace=d.get("namespace", ""), name=d.get("name", ""), facets=d.get("facets") or {}) for d in inputs_d],
            outputs=[Dataset(namespace=d.get("namespace", ""), name=d.get("name", ""), facets=d.get("facets") or {}) for d in outputs_d],
            producer=event.get("producer", "lineage_prototype"),
        )

        logger.info("event=%s", run_ev)
        state.openlineage_loader.load_event(run_ev)
        logger.info("Event %s loaded successfully", run_ev.run.runId)
        return {"status": "ok", "run_id": run_ev.run.runId}
    except Exception as exc:
        logger.exception("Failed to ingest event: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


