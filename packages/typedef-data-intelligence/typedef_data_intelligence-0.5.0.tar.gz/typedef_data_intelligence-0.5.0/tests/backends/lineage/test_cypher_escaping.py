"""Tests for Cypher string literal escaping helpers."""


def test_escape_cypher_string_literal_escapes_backslashes_and_quotes() -> None:
    """Backslashes must be escaped before quotes to prevent breaking Cypher literals."""
    from lineage.backends.lineage.base import BaseLineageStorage

    assert BaseLineageStorage._escape_cypher_string_literal(None) == ""
    assert BaseLineageStorage._escape_cypher_string_literal("simple") == "simple"

    # Trailing backslash must become \\ inside the Cypher literal.
    assert BaseLineageStorage._escape_cypher_string_literal("test\\") == "test\\\\"

    # Mixed backslashes + single quotes should escape both (backslashes first).
    assert (
        BaseLineageStorage._escape_cypher_string_literal("ab\\c'd")
        == "ab\\\\c\\'d"
    )


def test_search_nodes_rejects_malicious_node_label() -> None:
    """node_label must be validated/whitelisted (labels cannot be parameterized safely)."""
    from lineage.backends.lineage.base import BaseLineageStorage
    from lineage.backends.lineage.models.base import GraphEdge

    class _DummyStorage(BaseLineageStorage):
        def upsert_node(self, node) -> None:  # type: ignore[no-untyped-def]
            raise NotImplementedError

        def create_edge(  # type: ignore[no-untyped-def]
            self, from_node, to_node, edge: GraphEdge
        ) -> None:
            raise NotImplementedError

        def execute_raw_query(self, query: str, params=None):  # type: ignore[no-untyped-def]
            raise AssertionError("execute_raw_query should not be called for invalid labels")

        def close(self) -> None:
            """Close connections (no-op for test dummy)."""
            pass

        def get_graph_schema(self):  # type: ignore[no-untyped-def]
            # Minimal schema allowlist for the test
            return {"node_tables": {"DbtModel": {}}}

    storage = _DummyStorage()
    malicious = "DbtModel') RETURN n; MATCH (x:User"

    try:
        storage.search_nodes(malicious, "x", limit=1)
        raise AssertionError("Expected ValueError for malicious node_label")
    except ValueError:
        pass
def test_falkordb_search_nodes_rejects_malicious_node_label() -> None:
    """FalkorDB adapter must also validate node_label before building Cypher."""
    from lineage.backends.lineage._base_falkordb_adapter import _BaseFalkorDBAdapter

    adapter = _BaseFalkorDBAdapter.__new__(_BaseFalkorDBAdapter)

    def _execute_raw_query(_query: str):  # type: ignore[no-untyped-def]
        raise AssertionError("execute_raw_query should not be called for invalid labels")

    adapter.execute_raw_query = _execute_raw_query  # type: ignore[method-assign]
    # Keep schema minimal and deterministic
    adapter.get_graph_schema = lambda: {"node_tables": {"DbtModel": {}}}  # type: ignore[method-assign]

    malicious = "DbtModel) RETURN n"

    try:
        adapter.search_nodes(malicious, "x", limit=1)
        raise AssertionError("Expected ValueError for malicious node_label")
    except ValueError:
        pass
