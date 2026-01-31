"""Helper utilities for artifact widgets.

Contains temp directory management, text escaping/truncation, and type detection utilities.
"""
import atexit
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Track temp directories for cleanup on exit
_temp_directories: Set[Path] = set()


def _cleanup_temp_directories() -> None:
    """Clean up all tracked temp directories on exit."""
    for path in _temp_directories:
        try:
            if path.exists():
                shutil.rmtree(path)
        except Exception as e:
            logger.debug(f"Failed to cleanup temp directory {path}: {e}")


# Register cleanup function to run on exit
atexit.register(_cleanup_temp_directories)


def _create_temp_dir(prefix: str) -> Path:
    """Create a temp directory and track it for cleanup."""
    path = Path(tempfile.mkdtemp(prefix=prefix))
    _temp_directories.add(path)
    return path


def _truncate(value: str, max_len: int = 80) -> str:
    """Truncate long values, keeping the end (usually most meaningful part)."""
    if not value or len(value) <= max_len:
        return value or ""
    # Keep the last portion which is usually the most meaningful (e.g., table name)
    return f"...{value[-(max_len - 1):]}"


def _escape_markdown(text: Any) -> str:
    """Minimal escaping for markdown display - only escape characters that break rendering."""
    if not text:
        return ""
    s = str(text)
    # Only escape characters that actually break markdown tables/links
    return s.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def _get_node_type(node: dict) -> str:
    """Extract node type from normalized node dict or Pydantic model."""
    # Check for explicit type field first (from typed protocol results)
    if node_type := node.get("type"):
        return node_type
    # Fall back to labels (from raw Cypher results)
    labels = node.get("labels")
    if isinstance(labels, list) and labels:
        return labels[0]
    if isinstance(labels, str):
        return labels
    return "Unknown"


def _get_type_icon(node_type: str) -> str:
    """Icon mapping for node types."""
    return {
        "DbtModel": "📊",
        "DbtSource": "📥",
        "DbtColumn": "📍",
        "PhysicalTable": "📁",
        "PhysicalView": "📋",
        "PhysicalIncrementalModel": "📈",
        "PhysicalMaterializedView": "💎",
        "PhysicalEphemeral": "💨",
        "PhysicalColumn": "📍",
        "InferredSemanticModel": "🧠",
        "InferredMeasure": "📏",
        "InferredDimension": "📐",
        "JoinCluster": "🔗",
    }.get(node_type, "📦")


def _group_nodes_by_type(nodes: List[dict]) -> Dict[str, List[dict]]:
    """Group nodes by their type (first label)."""
    grouped: Dict[str, List[dict]] = {}
    for node in nodes:
        node_type = _get_node_type(node)
        grouped.setdefault(node_type, []).append(node)
    return grouped


def _detect_display_type(results: list, hint: Optional[str] = None) -> str:
    """Auto-detect how to display query results."""
    if hint:
        return hint
    if not results:
        return "empty"

    first = results[0]
    if not isinstance(first, dict):
        return "scalar"

    # Scalar/aggregation: flat dict with <=5 keys, no nested objects
    has_nested = any(isinstance(v, (dict, list)) for v in first.values() if v is not None)
    if len(first) <= 5 and not has_nested:
        return "table"

    # Has labels or many properties -> nodes
    if first.get("labels") or len(first) > 10:
        return "cards"

    return "cards"  # Default


def _render_as_table(results: List[dict]) -> str:
    """Render results as markdown table."""
    if not results:
        return "*No results*"

    # Get keys from first result
    keys = [k for k in results[0].keys() if k not in ("labels", "type")]
    if not keys:
        return "*No data to display*"

    # Build table
    header = "| " + " | ".join(keys) + " |"
    separator = "|" + "|".join(["---" for _ in keys]) + "|"

    rows = []
    for r in results[:20]:
        row_vals = [str(r.get(k, ""))[:120] for k in keys]  # Truncate long values
        rows.append("| " + " | ".join(row_vals) + " |")

    if len(results) > 20:
        rows.append(f"| ... and {len(results) - 20} more rows | |")

    return "\n".join([header, separator] + rows)


def _get_short_name(full_id: str) -> str:
    """Extract short name from a full model/node ID.

    Examples:
        "model.demo_finance.fct_revenue" -> "fct_revenue"
        "source.demo.raw.orders" -> "orders"
        "db.schema.table" -> "table"
    """
    if not full_id:
        return "?"
    parts = full_id.split(".")
    return parts[-1] if parts else full_id
