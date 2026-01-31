"""SQL Analysis DAG definition."""

from typing import Dict, List

import fenic as fc

from lineage.ingest.config import PipelineConfig
from lineage.ingest.static_loaders.semantic.passes import (
    AnalysisSummaryPass,
    AuditAnalysisPass,
    BusinessSemanticsPass,
    ColumnAnalysisPass,
    FilterAnalysisPass,
    GrainHumanizationPass,
    GroupingAnalysisPass,
    JoinEdgeAnalysisPass,
    OutputShapeAnalysisPass,
    RelationAnalysisPass,
    TimeAnalysisPass,
    WindowAnalysisPass,
)
from lineage.ingest.static_loaders.semantic.passes.base import BasePass


class SQLAnalysisDAG:
    """Defines the DAG of SQL analysis passes."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        """Initialize the DAG with all passes.

        Args:
            session: Fenic session for DataFrame operations
            pipeline_config: Pipeline configuration with model assignments and settings
        """
        self.session = session
        self.pipeline_config = pipeline_config

        # Initialize all passes
        self.passes = self._initialize_passes()

        # Build dependency graph
        self.dependencies = self._build_dependencies()

    def _initialize_passes(self) -> Dict[str, BasePass]:
        """Initialize all pass instances."""
        passes: dict[str, BasePass] = {
            "relation_analysis": RelationAnalysisPass(self.session, self.pipeline_config),
            "column_analysis": ColumnAnalysisPass(self.session, self.pipeline_config),
            "join_analysis": JoinEdgeAnalysisPass(self.session, self.pipeline_config),
            "filter_analysis": FilterAnalysisPass(self.session, self.pipeline_config),
            "grouping_analysis": GroupingAnalysisPass(self.session, self.pipeline_config),
        }

        # Always initialize time and window passes (even if disabled)
        # so they can add stub columns when skipped
        passes["time_analysis"] = TimeAnalysisPass(self.session, self.pipeline_config)
        passes["window_analysis"] = WindowAnalysisPass(self.session, self.pipeline_config)

        passes["output_shape_analysis"] = OutputShapeAnalysisPass(self.session, self.pipeline_config)

        if self.pipeline_config.enable_audit:
            passes["audit_analysis"] = AuditAnalysisPass(self.session, self.pipeline_config)

        # Always enable business semantics and grain humanization
        passes["business_semantics"] = BusinessSemanticsPass(self.session, self.pipeline_config)
        passes["grain_humanization"] = GrainHumanizationPass(self.session, self.pipeline_config)
        passes["analysis_summary"] = AnalysisSummaryPass(self.session, self.pipeline_config)

        return passes

    def _build_dependencies(self) -> Dict[str, List[str]]:
        """Build dependency graph from pass requirements."""
        dependencies: dict[str, list[str]] = {}

        for name, pass_instance in self.passes.items():
            dependencies[name] = pass_instance.get_required_passes()

        return dependencies

    def get_execution_order(self) -> List[str]:
        """Get topologically sorted execution order.

        Returns:
            List of pass names in execution order
        """
        # Simple topological sort
        visited = set()
        order = []

        def visit(node):
            if node in visited:
                return
            visited.add(node)

            # Visit dependencies first
            if node in self.dependencies:
                for dep in self.dependencies[node]:
                    if dep in self.passes:  # Only visit if pass exists
                        visit(dep)

            order.append(node)

        # Visit all nodes
        for name in self.passes:
            visit(name)

        return order

    def get_pass(self, name: str):
        """Get a specific pass instance."""
        return self.passes.get(name)

    def get_all_passes(self) -> Dict[str, object]:
        """Get all pass instances."""
        return self.passes

    def validate_dag(self) -> bool:
        """Validate that the DAG has no cycles.

        Returns:
            True if DAG is valid

        Raises:
            ValueError: If cycles detected
        """
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            if node in self.dependencies:
                for neighbor in self.dependencies[node]:
                    if neighbor not in self.passes:
                        continue  # Skip missing passes

                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True

            rec_stack.remove(node)
            return False

        for node in self.passes:
            if node not in visited:
                if has_cycle(node):
                    raise ValueError(f"Cycle detected in DAG involving {node}")

        return True
