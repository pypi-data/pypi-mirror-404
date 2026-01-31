"""Focused tests for Fenic behavior when merging complex struct columns.

These are hermetic (no LLM calls): we create a Session with semantic=None and
exercise builtin functions like coalesce/when/array_size on struct and
array<struct> columns.
"""

from __future__ import annotations

import fenic as fc
import polars as pl
from fenic.api.session.config import SessionConfig
from fenic.core.types.datatypes import (
    ArrayType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


def _local_session() -> fc.Session:
    # semantic=None => no model clients needed; safe for CI
    return fc.Session.get_or_create(SessionConfig(app_name="fenic_struct_merge_tests", semantic=None))


def test_coalesce_struct_picks_first_non_null_struct() -> None:
    session = _local_session()
    df = session.create_dataframe(
        [
            {"s1": {"a": 1, "b": "x"}, "s2": None},
            {"s1": None, "s2": {"a": 2, "b": "y"}},
        ]
    )

    out = df.select(fc.coalesce("s1", "s2").alias("s")).to_pylist()
    assert out == [{"s": {"a": 1, "b": "x"}}, {"s": {"a": 2, "b": "y"}}]


def test_coalesce_array_struct_does_not_treat_empty_array_as_missing() -> None:
    """Demonstrates the brittleness: [] is not null, so coalesce returns []."""
    session = _local_session()
    # Important: build via Polars with an explicit List(Struct) dtype.
    # Otherwise Polars may infer List(Null) for rows like []/None, and Fenic
    # will reject unsupported Null element types when importing.
    scope_struct = pl.Struct([pl.Field("scope", pl.Utf8), pl.Field("n", pl.Int64)])
    scope_list = pl.List(scope_struct)
    pl_df = pl.DataFrame(
        {
            "det": [[], None],
            "llm": [[{"scope": "outer", "n": 1}], [{"scope": "outer", "n": 2}]],
        },
        schema={"det": scope_list, "llm": scope_list},
    )
    df = session.create_dataframe(pl_df)

    out = df.select(fc.coalesce("det", "llm").alias("merged")).to_pylist()
    assert out[0]["merged"] == []  # important: does NOT fall back
    assert out[1]["merged"] == [{"scope": "outer", "n": 2}]


def test_coalesce_array_struct_can_fall_back_if_empty_is_converted_to_typed_null() -> None:
    """Workaround: convert [] -> null(ArrayType(StructType(...))) before coalesce."""
    session = _local_session()
    df = session.create_dataframe(
        [
            {"det": [], "llm": [{"scope": "outer", "n": 1}]},
            {"det": [{"scope": "cte:x", "n": 9}], "llm": [{"scope": "outer", "n": 2}]},
        ]
    )

    scope_struct = StructType(
        [
            StructField("scope", StringType),
            StructField("n", IntegerType),
        ]
    )
    arr_scope_struct = ArrayType(scope_struct)

    det_norm = (
        fc.when(fc.array_size("det") == 0, fc.null(arr_scope_struct))
        .otherwise(fc.col("det"))
        .alias("det_norm")
    )

    out = (
        df.select(det_norm, fc.col("llm"))
        .select(fc.coalesce(fc.col("det_norm"), fc.col("llm")).alias("merged"))
        .to_pylist()
    )

    assert out[0]["merged"] == [{"scope": "outer", "n": 1}]
    assert out[1]["merged"] == [{"scope": "cte:x", "n": 9}]


