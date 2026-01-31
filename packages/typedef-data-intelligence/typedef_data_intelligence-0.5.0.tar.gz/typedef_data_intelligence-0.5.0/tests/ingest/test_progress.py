"""Tests for ingest progress helpers."""


# ruff: noqa: D103

def test_render_progress_details_prefers_message_and_combines() -> None:
    from lineage.ingest.progress import _render_progress_details

    assert _render_progress_details("", "") == ""
    assert _render_progress_details("  ", "   ") == ""

    # If only one is present, use it.
    assert _render_progress_details("hello", "") == "hello"
    assert _render_progress_details("", "world") == "world"

    # If both are present, combine in a stable, readable way.
    assert _render_progress_details("10 sources, 20 models", "pass 3/10") == (
        "10 sources, 20 models — pass 3/10"
    )

    # Whitespace should be stripped before rendering.
    assert _render_progress_details("  hello  ", "  world ") == "hello — world"


