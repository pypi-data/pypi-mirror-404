"""Extractor UDFs for SQL Analyzer."""

from typing import List, Dict, Any
from fenic.api.functions import udf
from fenic.core.types import ArrayType, StringType


@udf(return_type=ArrayType(StringType))
def extract_scopes(relation_analysis: Dict[str, Any]) -> List[str]:
    """
    Extract unique scopes from RelationAnalysis.

    Args:
        relation_analysis: Dictionary containing relations with their scopes

    Returns:
        List of unique scope strings (e.g., ['outer', 'subquery:ms', 'cte:customer_total'])
    """
    if not relation_analysis or "relations" not in relation_analysis:
        return ["outer"]  # Default to outer if no relations found

    scopes = set()
    for rel in relation_analysis["relations"]:
        if "scope" in rel:
            scopes.add(rel["scope"])

    # Always include 'outer' if not present
    if not scopes:
        scopes.add("outer")

    return sorted(list(scopes))  # Sort for deterministic order


@udf(return_type=ArrayType(StringType))
def get_valid_aliases_for_scope(
    relation_analysis: Dict[str, Any], scope: str
) -> List[str]:
    """
    Get valid aliases for a specific scope from RelationAnalysis.

    Args:
        relation_analysis: Dictionary containing relations with their scopes
        scope: The scope to filter for

    Returns:
        List of aliases valid in the specified scope
    """
    if not relation_analysis or "relations" not in relation_analysis:
        return []

    valid_aliases = []
    for rel in relation_analysis["relations"]:
        if rel.get("scope") == scope:
            valid_aliases.append(rel["alias"])

    return valid_aliases
