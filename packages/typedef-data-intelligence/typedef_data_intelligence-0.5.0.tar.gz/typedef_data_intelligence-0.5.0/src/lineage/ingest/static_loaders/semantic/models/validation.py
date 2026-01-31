"""Validation models for Pass 9."""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Ptr(BaseModel):
    """Small helper for addressing into prior-pass JSON."""

    path: str = Field(
        description=(
            "JSON pointer into prior outputs (e.g., '/joins/2/equi_condition', '/filters/where/3'). "
            "Use RFC 6901 semantics for lists and objects."
        )
    )


class FindingContext(BaseModel):
    """Context information for an audit finding."""

    details: Optional[str] = Field(
        default=None, description="Additional details about the finding"
    )
    affected_aliases: List[str] = Field(
        default_factory=list, description="Aliases affected by this finding"
    )
    affected_scopes: List[str] = Field(
        default_factory=list, description="Scopes affected by this finding"
    )


class AuditFinding(BaseModel):
    """A single audit finding from Pass 9."""

    code: str = Field(
        description="Stable machine-readable code, e.g., 'JOIN_COND_HAS_LITERAL'"
    )
    severity: Literal["error", "warning", "info"] = Field(description="Issue severity")
    message: str = Field(description="Human-readable explanation of the issue")
    where: Optional[Ptr] = Field(
        default=None, description="Pointer to the offending field, if applicable"
    )
    context: Optional[FindingContext] = Field(
        default=None, description="Additional context for the finding"
    )


class PatchValue(BaseModel):
    """Value for a patch operation."""

    value: str = Field(description="String representation of the value for the patch")


class PatchOp(BaseModel):
    """A JSON Patch operation to fix an issue."""

    op: Literal["add", "replace", "remove"] = Field(
        description="Patch operation per JSON Patch"
    )
    path: str = Field(description="JSON pointer where to apply the patch")
    value: Optional[PatchValue] = Field(
        default=None, description="New value for add/replace; omit for remove"
    )
    rationale: str = Field(description="Brief reason why this patch is suggested")


class AuditAnalysis(BaseModel):
    """
    PASS 9 — Audit Analysis: check invariants across earlier passes and propose minimal patches.

    You MUST evaluate these inputs (provided alongside canonical_sql):
      • Pass 1 — relations: aliases, scopes, from_clause_order
      • Pass 2 — columns_by_alias (allow-list)
      • Pass 3 — joins (JoinClause[])
      • Pass 4 — filters (WHERE/HAVING/QUALIFY)
      • Pass 5 — grouping_by_scope (per-scope analysis)
      • Pass 6 — time_by_scope (per-scope analysis) [optional]
      • Pass 7 — window_by_scope (per-scope analysis) [optional]
      • Pass 8 — output_by_scope (per-scope analysis)

    Approve only if all *error*-severity rules pass. Emit warnings for suspicious but legal cases.

    Invariants to check (codes):

    Aliases & columns
      - ALIAS_UNKNOWN (error): any alias in joins/filters/select/order_by not present in Pass-1 relations for the scope.
      - COLUMN_NOT_ALLOWED (error): a referenced column is not in Pass-2 columns_by_alias[alias] for that scope.
      - UNQUALIFIED_AMBIGUOUS (warning): unqualified reference that could belong to multiple aliases.

    Joins
      - JOIN_TYPE_INVALID (error): type ∉ {INNER, LEFT, RIGHT, FULL, CROSS}.
      - JOIN_DUP_PAIR (error): more than one edge per unordered pair (A,B) in the same scope.
      - JOIN_CROSS_SHADOWED (error): CROSS exists but there is also a column=column predicate between the same pair.
      - JOIN_COND_HAS_LITERAL (error): `equi_condition` contains literals/IN/BETWEEN/IS NULL etc. (`equi_condition` must be equi-only).
      - JOIN_COND_FOREIGN_ALIAS (error): `equi_condition` references aliases other than left/right.
      - JOIN_RAW_COND_FOREIGN_ALIAS (error): `raw_condition` references aliases other than left/right.
      - JOIN_INNER_NORMALIZATION_MISMATCH (error): INNER with effective_type ≠ INNER or normalized_equi_condition ≠ equi_condition.
      - JOIN_INNER_RAW_NORMALIZATION_MISMATCH (error): INNER with normalized_raw_condition ≠ raw_condition.
      - JOIN_OUTER_KILLED_WITHOUT_PUSH (error): OUTER join null-killed by filters but effective_type not flipped/pushed.
      - JOIN_SIDE_ORDER (warning): left/right ordering doesn't follow from_clause_order (left should appear earlier).

    Filters
      - WHERE_CONTAINS_JOIN (error): cross-table column=column predicate in WHERE/HAVING/QUALIFY (should be a join).
      - QUALIFY_WITHOUT_WINDOWS (warning): QUALIFY present but no windows in Pass-7.

    Grouping & result grain
      - AGG_FLAG_INCONSISTENT (error): is_aggregated disagrees with presence of GROUP BY or aggregates in SELECT.
      - DIMENSION_NOT_GROUPED (error): non-aggregate SELECT expr not listed in GROUP BY when aggregated.
      - RESULT_GRAIN_MISSING_KEYS (warning): result_grain doesn't cover all GROUP BY + non-aggregate SELECT exprs.

    Time
      - TIME_SCOPE_INVALID (error): start/end reversed; missing column; malformed bounds.
      - TIME_NORMALIZATION_MISMATCH (warning): inclusive end not converted to exclusive in normalized scope when appropriate.

    Output shape
      - ORDER_BY_UNKNOWN_ALIAS (error): ORDER BY references alias/column not in allow-list for the current scope.
      - LIMIT_NEGATIVE (error), OFFSET_NEGATIVE (error).

    Scope discipline
      - SCOPE_LEAK (error): using inner-table alias directly in outer scope (should use subquery alias).
      - SUBQUERY_COLUMN_NOT_PROJECTED (error): outer references ms.col that the subquery doesn't project.
      - DRIVERS_INCOMPLETE (warning): driving_relations missing a top-level alias.

    For *errors*, propose minimal PatchOp(s) that localize the fix (remove duplicate join, move predicate, flip effective_type, etc.).
    """

    approved: bool = Field(
        description="True if no error findings exist; False otherwise"
    )
    findings: List[AuditFinding] = Field(
        default_factory=list, description="All issues found (errors, warnings, infos)"
    )
    suggested_patches: List[PatchOp] = Field(
        default_factory=list,
        description="Minimal JSON patches to resolve errors automatically (optional but recommended)",
    )
