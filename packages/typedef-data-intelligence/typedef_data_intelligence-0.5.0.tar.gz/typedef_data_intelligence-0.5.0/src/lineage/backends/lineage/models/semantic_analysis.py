"""Pydantic models for inferred semantic nodes (LLM-derived metadata).

These models represent LLM-generated business metadata extracted from SQL:
- InferredSemanticModel: Per-model analysis summary (container)
- InferredMeasure: Aggregated metrics (SUM, COUNT, AVG, etc.)
- InferredDimension: Non-aggregated attributes
- InferredFact: Factual data points
- InferredSegment: Filter rules and business logic
- TimeWindow: Time range filters
- TimeAttribute: Time-based filter attributes
- JoinEdge: Join relationships (stored as nodes, not edges)
- WindowFunction: Analytic/window functions

These are INFERRED by LLM analysis, separate from NATIVE semantic models
declared in the warehouse (see semantic_views.py).
"""

from typing import ClassVar, Optional

from pydantic import computed_field

from lineage.backends.lineage.models.base import BaseNode
from lineage.backends.types import NodeLabel


class InferredSemanticModel(BaseNode):
    """LLM-inferred semantic model per dbt model.

    Container for all inferred semantic metadata extracted from a model's SQL.
    Attached to DbtModel via HAS_INFERRED_SEMANTICS edge.

    This node stores the complete analysis results including grain, intent,
    and whether the model has aggregations/windows.

    Children:
        - InferredMeasure nodes (via HAS_MEASURE edges)
        - InferredDimension nodes (via HAS_DIMENSION edges)
        - InferredFact nodes (via HAS_FACT edges)
        - InferredSegment nodes (via HAS_SEGMENT edges)
        - TimeWindow, TimeAttribute, JoinEdge, WindowFunction nodes

    The ID is constructed as: {model_id}.inferred_semantics
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_SEMANTIC_MODEL

    # Core properties
    name: str  # Usually the model name
    model_id: str  # Parent DbtModel ID
    analyzed_at: str  # ISO 8601 timestamp
    analysis_version: str
    has_aggregations: bool
    has_time_window: bool
    has_window_functions: bool
    grain_human: str  # Human-readable grain description
    intent: str  # Business intent/purpose
    # full_analysis: str  # Complete JSON analysis
    analysis_summary: Optional[str] = None

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {model_id}.inferred_semantics."""
        return f"{self.model_id}.inferred_semantics"

    @staticmethod
    def build_id(model_id: str) -> str:
        """Build semantic model ID from model_id."""
        return f"{model_id}.inferred_semantics"


class InferredMeasure(BaseNode):
    """LLM-inferred aggregated business metric.

    Represents a calculated metric like SUM(revenue), COUNT(DISTINCT customers), etc.
    Extracted from SELECT clause of SQL by LLM analysis.

    Attached to InferredSemanticModel via HAS_MEASURE edge.
    Links to source DbtColumns via DERIVES_FROM edges.

    The ID is constructed as: {semantic_model_id}.measure.{name}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_MEASURE

    # Core properties
    name: str
    semantic_model_id: str  # Parent InferredSemanticModel ID
    expr: str  # Expression (e.g., "revenue", "customer_id")
    agg_function: str  # Aggregation function (SUM, COUNT, AVG, etc.)
    source_alias: Optional[str] = None  # Table alias where column comes from

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.measure.{name}."""
        return f"{self.semantic_model_id}.measure.{self.name}"


class InferredDimension(BaseNode):
    """LLM-inferred non-aggregated business attribute.

    Represents attributes used for grouping/filtering like customer_name,
    product_category, etc. Extracted from SELECT/GROUP BY clauses by LLM analysis.

    Attached to InferredSemanticModel via HAS_DIMENSION edge.
    Links to source DbtColumns via DERIVES_FROM edges.

    The ID is constructed as: {semantic_model_id}.dimension.{name}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_DIMENSION

    # Core properties
    name: str
    semantic_model_id: str  # Parent InferredSemanticModel ID
    source: str  # Column source (e.g., "customers.name")
    is_pii: bool = False  # Whether this contains personally identifiable information

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.dimension.{name}."""
        return f"{self.semantic_model_id}.dimension.{self.name}"


class InferredFact(BaseNode):
    """LLM-inferred factual data point.

    Represents a factual attribute that describes an event or observation.
    Similar to dimensions but more specific to the grain of analysis.

    Attached to InferredSemanticModel via HAS_FACT edge.
    Links to source DbtColumns via DERIVES_FROM edges.

    The ID is constructed as: {semantic_model_id}.fact.{name}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_FACT

    # Core properties
    name: str
    semantic_model_id: str  # Parent InferredSemanticModel ID
    source: str  # Column source
    description: Optional[str] = None  # Business meaning

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.fact.{name}."""
        return f"{self.semantic_model_id}.fact.{self.name}"


class InferredSegment(BaseNode):
    """LLM-inferred filter rule or business logic.

    Represents WHERE clause filters that define business segments like
    "active customers", "completed orders", etc. Extracted by LLM analysis.

    Attached to InferredSemanticModel via HAS_SEGMENT edge.

    The ID is constructed as: {semantic_model_id}.segment.{name}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_SEGMENT

    # Core properties
    name: str
    semantic_model_id: str  # Parent InferredSemanticModel ID
    rule: str  # Filter condition (e.g., "status = 'active'")
    clause: str  # WHERE/HAVING clause type

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.segment.{name}."""
        return f"{self.semantic_model_id}.segment.{self.name}"


class TimeWindow(BaseNode):
    """Time range filter.

    Represents time-based filtering like "last 30 days", "YTD", etc.

    Attached to InferredSemanticModel via HAS_TIME_WINDOW edge.

    The ID is constructed as: {semantic_model_id}.timewindow.{column_qualified}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.TIME_WINDOW

    # Core properties
    name: str  # Usually the column name
    semantic_model_id: str  # Parent InferredSemanticModel ID
    column_qualified: str  # Qualified column name (e.g., "orders.order_date")
    start_value: Optional[str] = None  # Start of time window
    end_value: Optional[str] = None  # End of time window
    end_exclusive: bool = False  # Whether end is exclusive
    granularity: Optional[str] = None  # day, week, month, year

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.timewindow.{column_qualified}."""
        return f"{self.semantic_model_id}.timewindow.{self.column_qualified}"


class TimeAttribute(BaseNode):
    """Time-based filter attribute.

    Represents time filters that aren't full windows, like specific dates
    or time-based conditions.

    Attached to InferredSemanticModel via HAS_TIME_ATTRIBUTE edge.

    The ID is constructed as: {semantic_model_id}.timeattr.{column_qualified}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.TIME_ATTRIBUTE

    # Core properties
    name: str  # Usually the column name
    semantic_model_id: str  # Parent InferredSemanticModel ID
    column_qualified: str  # Qualified column name
    filter_expr: str  # Filter expression

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.timeattr.{column_qualified}."""
        return f"{self.semantic_model_id}.timeattr.{self.column_qualified}"


class JoinEdge(BaseNode):
    """Join relationship between models (stored as node, not edge).

    Represents a JOIN in SQL between two tables. This is stored as a node
    so we can query join patterns and create join clusters.

    Attached to InferredSemanticModel via HAS_JOIN_EDGE edge.
    Can link to DbtModel nodes via INFERRED_JOINS_WITH, JOINS_LEFT_MODEL, JOINS_RIGHT_MODEL
    when aliases are resolved to actual models.

    The ID is constructed as: {semantic_model_id}.join.{left_alias}.{right_alias}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.JOIN_EDGE

    # Core properties
    name: str  # Usually "{left_alias}_to_{right_alias}"
    semantic_model_id: str  # Parent InferredSemanticModel ID
    join_type: str  # INNER, LEFT, RIGHT, FULL, CROSS
    left_alias: str  # Left table alias
    right_alias: str  # Right table alias
    equi_condition: str  # Equi-join condition (column-to-column only)
    effective_type: Optional[str] = None  # Effective join type after WHERE filters
    normalized_equi_condition: Optional[str] = None  # Normalized equi-join condition
    scope: Optional[str] = None  # Scope where join occurs (outer, subquery:*, cte:*)
    # Resolution properties (added when aliases resolve to models)
    left_model_id: Optional[str] = None  # Resolved DbtModel ID for left_alias
    right_model_id: Optional[str] = None  # Resolved DbtModel ID for right_alias
    confidence: Optional[str] = None  # high, medium, low (for resolution confidence)

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.join.{left_alias}.{right_alias}."""
        return f"{self.semantic_model_id}.join.{self.left_alias}.{self.right_alias}"


class WindowFunction(BaseNode):
    """Window/analytic function.

    Represents window functions like ROW_NUMBER(), RANK(), LAG(), etc.

    Attached to InferredSemanticModel via HAS_WINDOW_FUNCTION edge.

    The ID is constructed as: {semantic_model_id}.window.{func}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.WINDOW_FUNCTION

    # Core properties
    name: str  # Usually the function name
    semantic_model_id: str  # Parent InferredSemanticModel ID
    func: str  # Function name (ROW_NUMBER, RANK, LAG, etc.)
    partition_by: Optional[str] = None  # PARTITION BY clause
    order_by: Optional[str] = None  # ORDER BY clause
    frame: Optional[str] = None  # Window frame (ROWS BETWEEN, etc.)

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.window.{func}."""
        return f"{self.semantic_model_id}.window.{self.func}"


class InferredRelation(BaseNode):
    """Relation use in SQL (table/view/CTE/subquery).

    Represents a relation occurrence with its alias and scope.
    Extracted from Pass 1: Relation Analysis.

    Attached to InferredSemanticModel via HAS_RELATION edge.
    Can link to DbtModel via RESOLVES_TO_MODEL when alias is resolvable.

    The ID is constructed as: {semantic_model_id}.relation.{alias}.{scope}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_RELATION

    # Core properties
    name: str  # Usually the alias
    semantic_model_id: str  # Parent InferredSemanticModel ID
    alias: str  # Alias as used in SQL
    base: str  # Base relation name
    kind: str  # table, view, cte, subquery, table_function
    scope: str  # outer, subquery:<alias>, cte:<name>
    is_temp: bool = False
    confidence: Optional[str] = None  # high, medium, low (for resolution)

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.relation.{alias}.{scope}."""
        return f"{self.semantic_model_id}.relation.{self.alias}.{self.scope}"


class InferredFilter(BaseNode):
    """Filter predicate from WHERE/HAVING/QUALIFY.

    Represents a single-table filter predicate.
    Extracted from Pass 4: Filter Analysis.

    Attached to InferredSemanticModel via HAS_FILTER edge.
    Can link to InferredRelation via FILTERS_RELATION when alias resolvable.

    The ID is constructed as: {semantic_model_id}.filter.{clause}.{index}.{scope}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_FILTER

    # Core properties
    name: str  # Usually the predicate (truncated)
    semantic_model_id: str  # Parent InferredSemanticModel ID
    predicate: str  # Verbatim predicate from SQL
    clause: str  # WHERE, HAVING, or QUALIFY
    scope: str  # Scope where filter applies
    alias: Optional[str] = None  # Single-table alias (if applicable)

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.filter.{clause}.{index}.{scope}."""
        # Use hash of predicate for uniqueness within scope
        import hashlib
        pred_hash = hashlib.md5(self.predicate.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"{self.semantic_model_id}.filter.{self.clause}.{pred_hash}.{self.scope}"


class InferredGroupingScope(BaseNode):
    """Grouping analysis for a specific scope.

    Represents SELECT items, GROUP BY, and result grain per scope.
    Extracted from Pass 5: Grouping Analysis.

    Attached to InferredSemanticModel via HAS_GROUPING_SCOPE edge.
    Links to InferredSelectItem nodes via HAS_SELECT_ITEM.

    The ID is constructed as: {semantic_model_id}.grouping.{scope}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_GROUPING_SCOPE

    # Core properties
    name: str  # Usually the scope
    semantic_model_id: str  # Parent InferredSemanticModel ID
    scope: str  # outer, subquery:<alias>, cte:<name>
    is_aggregated: bool  # True if GROUP BY or aggregates present
    group_by: Optional[str] = None  # JSON array of GROUP BY expressions
    result_grain: Optional[str] = None  # JSON array of grain expressions
    measures: Optional[str] = None  # JSON array of measure expressions

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.grouping.{scope}."""
        return f"{self.semantic_model_id}.grouping.{self.scope}"


class InferredSelectItem(BaseNode):
    """SELECT item with expression and classification.

    Represents a single SELECT item with its expression, alias, and kind.
    Extracted from Pass 5: Grouping Analysis.

    Attached to InferredGroupingScope via HAS_SELECT_ITEM edge.

    The ID is constructed as: {semantic_model_id}.select.{scope}.{alias}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_SELECT_ITEM

    # Core properties
    name: str  # Usually the output alias
    semantic_model_id: str  # Parent InferredSemanticModel ID
    scope: str  # Scope where this SELECT item appears
    expr: str  # SELECT expression exactly as written
    alias: str  # Output column name/alias
    kind: str  # dimension or measure
    source_aliases: Optional[str] = None  # JSON array of relation aliases

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.select.{scope}.{alias}."""
        return f"{self.semantic_model_id}.select.{self.scope}.{self.alias}"


class InferredTimeScope(BaseNode):
    """Time analysis for a specific scope.

    Represents time semantics including time windows, buckets, and columns.
    Extracted from Pass 6: Time Analysis.

    Attached to InferredSemanticModel via HAS_TIME_SCOPE edge.

    The ID is constructed as: {semantic_model_id}.time.{scope}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_TIME_SCOPE

    # Core properties
    name: str  # Usually the scope
    semantic_model_id: str  # Parent InferredSemanticModel ID
    scope: str  # outer, subquery:<alias>, cte:<name>
    time_scope: Optional[str] = None  # JSON string of TimeScope
    normalized_time_scope: Optional[str] = None  # JSON string of NormalizedTimeScope
    time_buckets: Optional[str] = None  # JSON array of bucketing expressions
    time_columns: Optional[str] = None  # JSON array of time column names

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.time.{scope}."""
        return f"{self.semantic_model_id}.time.{self.scope}"


class InferredWindowScope(BaseNode):
    """Window function analysis for a specific scope.

    Represents window function specifications per scope.
    Extracted from Pass 7: Window Analysis.

    Attached to InferredSemanticModel via HAS_WINDOW_SCOPE edge.
    Links to WindowFunction nodes via HAS_WINDOW_SPEC.

    The ID is constructed as: {semantic_model_id}.window_scope.{scope}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_WINDOW_SCOPE

    # Core properties
    name: str  # Usually the scope
    semantic_model_id: str  # Parent InferredSemanticModel ID
    scope: str  # outer, subquery:<alias>, cte:<name>
    windows: Optional[str] = None  # JSON array of WindowSpec objects

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.window_scope.{scope}."""
        return f"{self.semantic_model_id}.window_scope.{self.scope}"


class InferredOutputShape(BaseNode):
    """Output shape analysis for a specific scope.

    Represents ORDER BY, LIMIT, DISTINCT, and set operations per scope.
    Extracted from Pass 8: Output Shape Analysis.

    Attached to InferredSemanticModel via HAS_OUTPUT_SHAPE edge.

    The ID is constructed as: {semantic_model_id}.output.{scope}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_OUTPUT_SHAPE

    # Core properties
    name: str  # Usually the scope
    semantic_model_id: str  # Parent InferredSemanticModel ID
    scope: str  # outer, subquery:<alias>, cte:<name>
    order_by: Optional[str] = None  # JSON array of OrderByItem
    limit: Optional[int] = None
    offset: Optional[int] = None
    select_distinct: bool = False
    set_ops: Optional[str] = None  # JSON array of SetOperation

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.output.{scope}."""
        return f"{self.semantic_model_id}.output.{self.scope}"


class InferredAuditFinding(BaseNode):
    """Audit finding from validation pass.

    Represents an issue found during Pass 9: Audit Analysis.

    Attached to InferredSemanticModel via HAS_AUDIT_FINDING edge.

    The ID is constructed as: {semantic_model_id}.audit.{code}.{index}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_AUDIT_FINDING

    # Core properties
    name: str  # Usually "{code}: {message}"
    semantic_model_id: str  # Parent InferredSemanticModel ID
    code: str  # Stable machine-readable code (e.g., "JOIN_COND_HAS_LITERAL")
    severity: str  # error, warning, info
    message: str  # Human-readable explanation
    where: Optional[str] = None  # JSON pointer to offending field
    context: Optional[str] = None  # JSON string of FindingContext

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.audit.{code}.{hash}."""
        import hashlib
        msg_hash = hashlib.md5(self.message.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"{self.semantic_model_id}.audit.{self.code}.{msg_hash}"


class InferredAuditPatch(BaseNode):
    """Suggested patch from audit analysis.

    Represents a JSON Patch operation to fix an audit issue.
    Extracted from Pass 9: Audit Analysis.

    Attached to InferredSemanticModel via HAS_AUDIT_PATCH edge.

    The ID is constructed as: {semantic_model_id}.patch.{index}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_AUDIT_PATCH

    # Core properties
    name: str  # Usually "{op} {path}"
    semantic_model_id: str  # Parent InferredSemanticModel ID
    op: str  # add, replace, remove
    path: str  # JSON pointer where to apply patch
    value: Optional[str] = None  # New value for add/replace
    rationale: str  # Brief reason for patch

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.patch.{hash}."""
        import hashlib
        path_hash = hashlib.md5(self.path.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"{self.semantic_model_id}.patch.{path_hash}"


class InferredGrainToken(BaseNode):
    """Grain token from humanization pass.

    Represents a normalized token from the grain humanization process.
    Extracted from Pass 10a: Grain Humanization.

    Attached to InferredSemanticModel via HAS_GRAIN_TOKEN edge.

    The ID is constructed as: {semantic_model_id}.grain_token.{index}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.INFERRED_GRAIN_TOKEN

    # Core properties
    name: str  # Usually the normalized_term
    semantic_model_id: str  # Parent InferredSemanticModel ID
    input_expr: str  # Original expression from result_grain
    normalized_term: str  # Human-readable normalized term
    is_measure: bool  # True if token matches a measure
    dropped: bool  # True if excluded from final phrase

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {semantic_model_id}.grain_token.{hash}."""
        import hashlib
        expr_hash = hashlib.md5(self.input_expr.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"{self.semantic_model_id}.grain_token.{expr_hash}"


__all__ = [
    "InferredSemanticModel",
    "InferredMeasure",
    "InferredDimension",
    "InferredFact",
    "InferredSegment",
    "TimeWindow",
    "TimeAttribute",
    "JoinEdge",
    "WindowFunction",
    # New formalized nodes
    "InferredRelation",
    "InferredFilter",
    "InferredGroupingScope",
    "InferredSelectItem",
    "InferredTimeScope",
    "InferredWindowScope",
    "InferredOutputShape",
    "InferredAuditFinding",
    "InferredAuditPatch",
    "InferredGrainToken",
]
