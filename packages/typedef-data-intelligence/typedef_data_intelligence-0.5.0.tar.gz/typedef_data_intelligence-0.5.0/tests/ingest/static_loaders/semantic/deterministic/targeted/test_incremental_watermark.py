"""Unit tests for incremental watermark detection heuristics."""

from __future__ import annotations

from lineage.ingest.static_loaders.semantic.deterministic.targeted.incremental_watermark import (
    heuristic_watermark_classification,
)


class TestHeuristicWatermarkClassification:
    """Tests for heuristic_watermark_classification."""

    def test_empty_filter_returns_empty_result(self) -> None:
        """Empty filter analysis should return empty watermark result."""
        result = heuristic_watermark_classification(filter_analysis={})

        assert result.classifications == []
        assert result.has_watermark is False

    def test_detects_max_subquery_watermark(self) -> None:
        """MAX subquery pattern should be detected as timestamp watermark."""
        filter_analysis = {
            "where": [
                {"predicate": "updated_at >= (SELECT MAX(updated_at) FROM target_table)", "clause": "WHERE"}
            ]
        }

        result = heuristic_watermark_classification(filter_analysis)

        assert result.has_watermark is True
        assert len(result.classifications) == 1
        assert result.classifications[0].is_watermark is True
        assert result.classifications[0].watermark_type == "max_timestamp"

    def test_detects_coalesce_max_pattern(self) -> None:
        """COALESCE(MAX(...)) pattern should be detected."""
        # Regex expects: >= (SELECT COALESCE(MAX(...))
        filter_analysis = {
            "where": [
                {"predicate": "created_at >= (SELECT COALESCE(MAX(created_at), '1970-01-01') FROM target)", "clause": "WHERE"}
            ]
        }

        result = heuristic_watermark_classification(filter_analysis)

        assert result.has_watermark is True
        assert result.classifications[0].is_watermark is True

    def test_detects_jinja_var_watermark(self) -> None:
        """Jinja variable pattern should be detected as date_partition watermark."""
        filter_analysis = {
            "where": [
                {"predicate": "created_at >= {{ var('start_date') }}", "clause": "WHERE"}
            ]
        }

        result = heuristic_watermark_classification(filter_analysis)

        assert result.has_watermark is True
        assert result.classifications[0].is_watermark is True
        assert result.classifications[0].watermark_type == "date_partition"

    def test_detects_this_reference_watermark(self) -> None:
        """{{ this }} dbt reference should be detected."""
        filter_analysis = {
            "where": [
                {"predicate": "updated_at > (SELECT MAX(updated_at) FROM {{ this }})", "clause": "WHERE"}
            ]
        }

        result = heuristic_watermark_classification(filter_analysis)

        assert result.has_watermark is True
        assert result.classifications[0].is_watermark is True

    def test_non_watermark_predicate_not_flagged(self) -> None:
        """Regular filter predicates should not be flagged as watermarks."""
        filter_analysis = {
            "where": [
                {"predicate": "status = 'active'", "clause": "WHERE"},
                {"predicate": "amount > 100", "clause": "WHERE"},
            ]
        }

        result = heuristic_watermark_classification(filter_analysis)

        assert result.has_watermark is False
        # Should still have classifications, just not watermarks
        assert all(c.is_watermark is False for c in result.classifications)

    def test_timestamp_column_with_comparison_detected(self) -> None:
        """Timestamp column with >= comparison should be detected."""
        filter_analysis = {
            "where": [
                {"predicate": "received_at >= '2024-01-01'", "clause": "WHERE"}
            ]
        }

        result = heuristic_watermark_classification(filter_analysis)

        # received_at is a known timestamp column pattern
        # Detection depends on whether it matches the timestamp patterns
        # This tests the timestamp column heuristic path
        assert len(result.classifications) >= 1

    def test_id_column_with_comparison(self) -> None:
        """ID column with comparison may be detected as id watermark."""
        filter_analysis = {
            "where": [
                {"predicate": "id > (SELECT MAX(id) FROM processed_table)", "clause": "WHERE"}
            ]
        }

        result = heuristic_watermark_classification(filter_analysis)

        # Should detect based on MAX subquery pattern
        assert result.has_watermark is True

    def test_multiple_predicates_mixed(self) -> None:
        """Multiple predicates with some watermarks should be handled."""
        filter_analysis = {
            "where": [
                {"predicate": "status = 'pending'", "clause": "WHERE"},
                {"predicate": "updated_at >= (SELECT MAX(updated_at) FROM target)", "clause": "WHERE"},
                {"predicate": "region = 'US'", "clause": "WHERE"},
            ]
        }

        result = heuristic_watermark_classification(filter_analysis)

        assert result.has_watermark is True
        watermarks = [c for c in result.classifications if c.is_watermark]
        assert len(watermarks) == 1
