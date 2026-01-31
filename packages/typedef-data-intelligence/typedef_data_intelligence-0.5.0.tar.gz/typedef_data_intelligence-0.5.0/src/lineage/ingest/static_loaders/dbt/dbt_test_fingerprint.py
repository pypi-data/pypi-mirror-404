"""Fingerprinting functions for dbt tests.

This module provides functions to compute stable fingerprints for dbt tests,
used for incremental change detection. When a test's fingerprint changes,
it indicates the test definition or configuration has changed and needs
to be re-processed.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional


def compute_test_fingerprint(
    test_type: str,
    test_name: Optional[str],
    column_name: Optional[str],
    model_id: Optional[str],
    test_kwargs: Optional[Dict[str, Any]],
    severity: str,
    where_clause: Optional[str],
    store_failures: bool,
) -> str:
    """Compute a fingerprint for a dbt data test.

    The fingerprint captures all aspects that affect test behavior:
    - Test type and name (what kind of test)
    - Target column and model (what it tests)
    - Test kwargs (test parameters like accepted_values list)
    - Config (severity, where, store_failures)

    Args:
        test_type: "generic" or "singular"
        test_name: For generic tests, the test macro name (unique, not_null, etc.)
        column_name: Column being tested (if column-scoped)
        model_id: Primary model/source being tested
        test_kwargs: For generic tests, the kwargs dict
        severity: Test severity ("error" or "warn")
        where_clause: Optional WHERE filter from test config
        store_failures: Whether test stores failures

    Returns:
        SHA-256 hash of the test configuration
    """
    components = {
        "test_type": test_type,
        "test_name": test_name,
        "column_name": column_name,
        "model_id": model_id,
        "test_kwargs": test_kwargs,
        "severity": severity,
        "where_clause": where_clause,
        "store_failures": store_failures,
    }
    # Stable JSON serialization
    content = json.dumps(components, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()


def compute_unit_test_fingerprint(
    model_id: Optional[str],
    given: Optional[List[Dict[str, Any]]],
    expect: Optional[Dict[str, Any]],
    overrides: Optional[Dict[str, Any]],
) -> str:
    """Compute a fingerprint for a dbt unit test.

    The fingerprint captures all aspects that affect unit test behavior:
    - Model being tested
    - Given input definitions (mocked data)
    - Expected output
    - Model overrides

    Args:
        model_id: Model being tested
        given: Input definitions (mocked data)
        expect: Expected output
        overrides: Model overrides

    Returns:
        SHA-256 hash of the unit test configuration
    """
    components = {
        "model_id": model_id,
        "given": given,
        "expect": expect,
        "overrides": overrides,
    }
    # Stable JSON serialization
    content = json.dumps(components, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()


__all__ = ["compute_test_fingerprint", "compute_unit_test_fingerprint"]
