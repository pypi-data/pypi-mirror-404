"""Analytical models for Passes 5-8."""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# Pass 5: Grouping Analysis Models


class SelectItem(BaseModel):
    """
    A single SELECT item with its expression, output alias, classification, and source aliases.
    """

    expr: str = Field(
        description=(
            "The SELECT expression exactly as written in SQL. "
            "Keep verbatim including functions, operators, etc."
        )
    )

    alias: str = Field(
        description=(
            "The output column name/alias. "
            "If no AS alias provided, this is the expression itself."
        )
    )

    source_aliases: List[str] = Field(
        description=(
            "List of relation aliases referenced in this expression. "
            "Must be valid aliases from RelationAnalysis and only use columns "
            "that appear in ColumnAnalysis allow-list for those aliases."
        )
    )

    is_literal: bool = Field(
        default=False,
        description=(
            "True if this SELECT item is a literal value (NULL, string constant, "
            "number, boolean). Literals have no source_aliases and that's expected."
        )
    )


class GroupingAnalysis(BaseModel):
    """
    Analysis of SELECT items, GROUP BY, and result grain for a specific scope.

    Rules:
    1. Extract SELECT items for the CURRENT scope only
    2. source_aliases must be valid per RelationAnalysis and ColumnAnalysis
    3. is_aggregated = (GROUP BY present) OR (any SELECT has aggregate)
    4. result_grain = dedup(GROUP BY ∪ non-aggregate SELECT expressions)
    """

    select: List[SelectItem] = Field(
        default_factory=list,
        description=(
            "SELECT items for this scope. "
            "Each item includes expression, output alias, and source aliases."
        ),
    )

    group_by: List[str] = Field(
        default_factory=list,
        description=(
            "GROUP BY expressions exactly as written for this scope. "
            "Empty list if no GROUP BY clause."
        ),
    )

    is_aggregated: bool = Field(
        description=(
            "True if this scope has GROUP BY clause OR any SELECT item contains "
            "an aggregate function. False otherwise."
        )
    )

    result_grain: List[str] = Field(
        default_factory=list,
        description=(
            "The grain of the result set: deduplicated union of GROUP BY expressions "
            "and non-aggregate SELECT expressions. Defines what makes each row unique."
        ),
    )

    measures: List[str] = Field(
        default_factory=list,
        description=(
            "List of aggregate expressions found in SELECT items (verbatim). "
            "E.g., ['SUM(ss_coupon_amt)', 'COUNT(*)']"
        ),
    )


# Pass 6: Time Analysis Models


class TimeScope(BaseModel):
    """
    A time range constraint from filter predicates for the CURRENT scope only.
    """

    column: str = Field(
        description=(
            "Qualified time column for THIS scope only (e.g., 'd1.d_year', 'orders.order_date'). "
            "The column's alias MUST be valid in the CURRENT scope (Pass 1) and the column MUST exist in the "
            "Pass 2 allow-list for that alias. For subquery aliases (e.g., 'ms'), the column MUST be one of the "
            "projected columns of that subquery. If these conditions are not met, this entire TimeScope should be null."
        )
    )

    start: str = Field(
        description=(
            "Start value of the time range (inclusive). "
            "Keep as string to preserve original format."
        )
    )

    end: str = Field(
        description=(
            "End value of the time range. Keep as string to preserve original format."
        )
    )

    end_inclusive: bool = Field(
        description=(
            "True if the end boundary is inclusive (e.g., BETWEEN, <=); "
            "False for strict <"
        )
    )


class NormalizedTimeScope(BaseModel):
    """
    Time range normalized to exclusive end for consistent handling.
    """

    column: str = Field(description="Same column as time_scope.column")

    start: str = Field(
        description="Normalized start in the same grain as column (verbatim if already normalized)"
    )

    end: str = Field(
        description=(
            "Exclusive end (e.g., year+1, date+1 day, month→first day of next month). "
            "E.g., year 2002 inclusive -> 2003 exclusive"
        )
    )

    end_exclusive: bool = Field(
        description="Always True; indicates that 'end' is exclusive"
    )


class TimeAnalysis(BaseModel):
    """
    Analysis of time semantics for a specific scope.

    Rules:
    1. time_scope: Single primary time range from filter predicates
    2. normalized_time_scope: Same range with exclusive end
    3. time_buckets: Bucketing expressions from SELECT/GROUP BY
    4. time_columns: All columns in time-related predicates
    """

    time_scope: Optional[TimeScope] = Field(
        default=None,
        description=(
            "Primary time range constraint if detectable. "
            "Only from filters that constrain a single time column with range predicates. "
            "Null if no clear time scope or multiple conflicting time columns."
        ),
    )

    normalized_time_scope: Optional[NormalizedTimeScope] = Field(
        default=None,
        description=(
            "Time scope normalized to exclusive end. Null if time_scope is null."
        ),
    )

    time_buckets: List[str] = Field(
        default_factory=list,
        description=(
            "Bucketing expressions in THIS scope (DATE_TRUNC/EXTRACT/YEAR/MONTH/etc.) "
            "gathered from SELECT/GROUP BY. E.g., ['DATE_TRUNC(month, order_date)', 'YEAR(d_date)']"
        ),
    )

    time_columns: List[str] = Field(
        default_factory=list,
        description=(
            "Columns referenced by time-like predicates in THIS scope (must be in allow-list). "
            "Include attributes like d_dow. Only include columns whose aliases are valid in CURRENT scope."
        ),
    )


# Pass 7: Window Analysis Models


class WindowSpec(BaseModel):
    """
    A single window function specification.
    """

    func: str = Field(
        description=(
            "The function call exactly as written. "
            "E.g., 'ROW_NUMBER()', 'SUM(ss_net_profit)', 'LAG(order_date, 7) IGNORE NULLS'"
        )
    )

    partition_by: List[str] = Field(
        default_factory=list,
        description=(
            "Expressions from PARTITION BY inside OVER, verbatim. "
            "E.g., ['user_id', 'region']"
        ),
    )

    order_by: List[str] = Field(
        default_factory=list,
        description=(
            "Expressions from ORDER BY inside OVER, verbatim. "
            "Include ASC/DESC and NULLS FIRST/LAST if present. "
            "E.g., ['event_time DESC', 'priority ASC NULLS LAST']"
        ),
    )

    frame: str = Field(
        default="",
        description=(
            "The frame clause inside OVER if explicitly present. "
            "E.g., 'ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW'. "
            "Empty string if no frame clause specified."
        ),
    )


class WindowAnalysis(BaseModel):
    """
    Analysis of window functions for a specific scope.

    Rules:
    1. Only include functions with OVER clause
    2. Keep all expressions verbatim
    3. Resolve named windows if present
    4. Maintain scope discipline
    """

    windows: List[WindowSpec] = Field(
        default_factory=list,
        description=(
            "List of window function specifications in THIS scope. "
            "Empty if no window functions present."
        ),
    )


# Pass 8: Output Shape Analysis Models


class OrderByItem(BaseModel):
    """
    A single ORDER BY expression with direction.
    """

    expr: str = Field(
        description=(
            "The ORDER BY expression exactly as written. "
            "E.g., 'c_last_name', 'SUBSTRING(s_city, 1, 30)', 'profit'"
        )
    )

    dir: Literal["ASC", "DESC"] = Field(
        description=(
            "Sort direction. ASC if not specified or explicit ASC; "
            "DESC only if explicitly DESC."
        )
    )


class SetOperation(BaseModel):
    """
    A set operation (UNION, INTERSECT, EXCEPT) at this scope.
    """

    op: Literal[
        "UNION", "UNION ALL", "INTERSECT", "INTERSECT ALL", "EXCEPT", "EXCEPT ALL"
    ] = Field(
        description=(
            "The set operation type. "
            "Include ALL keyword if present (e.g., 'UNION ALL')."
        )
    )

    position: int = Field(
        description=(
            "Position of this set operation in the query. "
            "1 for first UNION/INTERSECT/EXCEPT after initial SELECT, 2 for second, etc."
        )
    )


class OutputShapeAnalysis(BaseModel):
    """
    Analysis of output shape (ORDER BY, LIMIT, DISTINCT, set operations) for a specific scope.

    Rules:
    1. Only analyze clauses that belong to the CURRENT scope
    2. ORDER BY: Extract expressions at this scope's SELECT level
    3. LIMIT/OFFSET: Values from this scope only
    4. SELECT DISTINCT: True if DISTINCT keyword present
    5. Set operations: UNION/INTERSECT/EXCEPT at this scope
    """

    order_by: List[OrderByItem] = Field(
        default_factory=list,
        description=(
            "ORDER BY items for THIS scope. "
            "Empty if no ORDER BY clause at this scope level."
        ),
    )

    limit: Optional[int] = Field(
        default=None,
        description=("LIMIT value if present at THIS scope. Null if no LIMIT clause."),
    )

    offset: Optional[int] = Field(
        default=None,
        description=(
            "OFFSET value if present at THIS scope. Null if no OFFSET clause."
        ),
    )

    select_distinct: bool = Field(
        default=False,
        description=(
            "True if SELECT DISTINCT is used at THIS scope. False for regular SELECT."
        ),
    )

    set_ops: List[SetOperation] = Field(
        default_factory=list,
        description=(
            "Set operations (UNION/INTERSECT/EXCEPT) at THIS scope. "
            "Empty if no set operations."
        ),
    )
