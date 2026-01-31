"""Dependency management for SQL analysis passes."""

from typing import List, Set


class PassDependencies:
    """Manages dependencies between analysis passes."""

    # Define the dependency graph
    DEPENDENCIES = {
        "relation_analysis": [],
        "column_analysis": ["relation_analysis"],
        "join_analysis": ["relation_analysis", "column_analysis"],
        "filter_analysis": ["relation_analysis", "column_analysis", "join_analysis"],
        "grouping_analysis": [
            "relation_analysis",
            "column_analysis",
            "filter_analysis",
        ],
        "time_analysis": ["grouping_analysis"],
        "window_analysis": ["time_analysis"],
        "output_shape_analysis": ["window_analysis"],
        "audit_analysis": ["output_shape_analysis"],
        "business_semantics": ["audit_analysis"],
        "grain_humanization": ["business_semantics"],
        "analysis_summary": ["grain_humanization"],
    }

    @classmethod
    def get_dependencies(cls, pass_name: str) -> List[str]:
        """Get direct dependencies for a pass."""
        return cls.DEPENDENCIES.get(pass_name, [])

    @classmethod
    def get_all_dependencies(cls, pass_name: str) -> Set[str]:
        """Get all transitive dependencies for a pass."""
        visited = set()

        def visit(node):
            if node in visited:
                return
            visited.add(node)

            for dep in cls.get_dependencies(node):
                visit(dep)

        visit(pass_name)
        visited.discard(pass_name)  # Remove self
        return visited

    @classmethod
    def get_dependents(cls, pass_name: str) -> List[str]:
        """Get passes that depend on the given pass."""
        dependents = []

        for name, deps in cls.DEPENDENCIES.items():
            if pass_name in deps:
                dependents.append(name)

        return dependents

    @classmethod
    def validate_dependencies(cls, enabled_passes: Set[str]) -> bool:
        """Validate that all dependencies are satisfied.

        Args:
            enabled_passes: Set of enabled pass names

        Returns:
            True if all dependencies satisfied

        Raises:
            ValueError: If missing dependencies
        """
        for pass_name in enabled_passes:
            required = set(cls.get_dependencies(pass_name))
            missing = required - enabled_passes

            if missing:
                raise ValueError(
                    f"Pass '{pass_name}' requires {missing} which are not enabled"
                )

        return True
