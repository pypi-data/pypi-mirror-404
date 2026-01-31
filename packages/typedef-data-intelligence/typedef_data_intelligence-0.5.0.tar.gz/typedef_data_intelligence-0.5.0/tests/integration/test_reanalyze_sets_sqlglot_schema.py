"""Regression test: reanalyze path must refresh SQLGlot schema for canonicalization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock

import lineage.integration as integration_mod
import pytest
from lineage.ingest.config import (
    ClusteringConfig,
    ProfilingConfig,
    SemanticAnalysisConfig,
    SemanticViewLoaderConfig,
)
from lineage.integration import LineageIntegration


@dataclass(frozen=True)
class _DummyPlan:
    """Minimal plan object used by the reanalyze path in this test."""

    run_clustering: bool = False


class _FakeSqlglotSchema:
    """Fake SqlglotSchema that mimics the real class interface."""

    def __init__(self, schema_dict: dict) -> None:
        self._schema_dict = schema_dict

    def to_dict(self) -> dict:
        return self._schema_dict


class _FakeArtifacts:
    def __init__(self, schema: _FakeSqlglotSchema) -> None:
        self._schema = schema

    def iter_models(self):  # type: ignore[no-untyped-def]
        return []

    def sqlglot_schema(self) -> _FakeSqlglotSchema:
        return self._schema


class _FakeBuilder:
    def __init__(self, artifacts: _FakeArtifacts) -> None:
        self.loader = Mock()
        self.loader.load = Mock(return_value=artifacts)


def _make_integration(mock_storage) -> LineageIntegration:  # type: ignore[no-untyped-def]
    return LineageIntegration(
        storage=mock_storage,
        semantic_config=SemanticAnalysisConfig(enabled=True),
        profiling_config=ProfilingConfig(enabled=False),
        clustering_config=ClusteringConfig(enabled=False),
        semantic_view_config=SemanticViewLoaderConfig(enabled=False),
        data_backend=None,
    )


def test_reanalyze_semantics_only_refreshes_sqlglot_schema(
    mock_storage, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure reanalyze path sets `_sqlglot_schema` before running derived work."""
    expected_schema_dict = {"tables": {"db.schema.some_table": {"columns": {"id": "int"}}}}
    expected_schema = _FakeSqlglotSchema(expected_schema_dict)
    artifacts = _FakeArtifacts(schema=expected_schema)
    builder = _FakeBuilder(artifacts=artifacts)

    # Artifacts loader path
    monkeypatch.setattr(
        integration_mod.LineageBuilder, "from_dbt_artifacts", Mock(return_value=builder)
    )

    # Avoid real planning + derived work; we only care that schema is refreshed.
    monkeypatch.setattr(
        integration_mod.SyncPlanner, "create_plan", Mock(return_value=_DummyPlan())
    )

    integration = _make_integration(mock_storage)

    dummy_session = Mock()
    dummy_session.stop = Mock()
    monkeypatch.setattr(integration, "_create_fenic_session_if_needed", Mock(return_value=dummy_session))
    monkeypatch.setattr(integration, "_execute_derived_work", Mock())

    # Start from a known bad value to ensure the call refreshes it.
    integration._sqlglot_schema = None

    integration.reanalyze_semantics_only(Path("/tmp/fake_target"), verbose=False)

    # Verify the schema was set and has the expected dict representation
    assert integration._sqlglot_schema is expected_schema
    assert integration._sqlglot_schema.to_dict() == expected_schema_dict


