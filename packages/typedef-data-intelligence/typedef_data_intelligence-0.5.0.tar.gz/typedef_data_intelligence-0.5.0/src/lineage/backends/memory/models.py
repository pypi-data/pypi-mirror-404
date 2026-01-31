"""Pydantic models for memory backend.

This module defines the data structures used by the memory system:
- Episode: A discrete unit of memory (query, insight, preference, pattern)
- MemoryResult: A search result with relevance score and temporal context
- Specialized episode types: UserPreference, DataPattern
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class EpisodeType(str, Enum):
    """Types of memory episodes stored in the system."""

    # User-specific memory
    USER_PREFERENCE = "user_preference"  # User preferences (chart type, format, etc.)
    USER_QUERY = "user_query"  # User's query and results
    USER_CONTEXT = "user_context"  # Contextual information about user
    USER_SESSION_SUMMARY = "user_session_summary"  # Post-task summary with user feedback

    # Organization-wide memory
    DATA_PATTERN = "data_pattern"  # Discovered patterns in data models
    COMMON_JOIN = "common_join"  # Frequently used joins between models
    METRIC_DEFINITION = "metric_definition"  # Business metric definitions
    DATA_QUALITY_ISSUE = "data_quality_issue"  # Known data quality patterns
    QUERY_PATTERN = "query_pattern"  # Common query patterns
    ORG_SESSION_SUMMARY = "org_session_summary"  # Post-task summary with technical learnings

    # General
    INSIGHT = "insight"  # General insights or learnings
    ANNOTATION = "annotation"  # User or system annotations


class Episode(BaseModel):
    """A discrete unit of memory stored in the temporal knowledge graph.

    Episodes are the primary way to store information in the memory system.
    Each episode represents a bounded piece of information (text or structured data)
    with temporal and contextual metadata.

    Attributes:
        name: Short identifier for the episode (e.g., "arr_chart_preference")
        content: The actual content (text or structured JSON)
        episode_type: Type of episode (user preference, data pattern, etc.)
        source_description: Context about where this came from
        timestamp: When the episode occurred (defaults to now)
        metadata: Additional structured metadata
        entity_references: Named entities referenced in this episode (optional)

    Example:
        ```python
        episode = Episode(
            name="user_prefers_bar_charts",
            content="User alice prefers bar charts for ARR metrics",
            episode_type=EpisodeType.USER_PREFERENCE,
            source_description="Analyst chat session on 2025-01-24",
            entity_references=["alice", "ARR", "bar_chart"]
        )
        ```
    """

    name: str = Field(description="Short identifier for the episode")
    content: str = Field(description="The episode content (text or JSON)")
    episode_type: EpisodeType = Field(
        description="Type of episode", default=EpisodeType.INSIGHT
    )
    source_description: str = Field(
        description="Context about the source of this episode"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    entity_references: List[str] = Field(
        default_factory=list,
        description="Named entities referenced (e.g., model names, user names)",
    )


class MemoryResult(BaseModel):
    """A search result from the memory system.

    Represents a memory episode retrieved from search, with relevance scoring
    and temporal context.

    Attributes:
        episode: The original episode that was stored
        score: Relevance score from hybrid search (0.0-1.0)
        rank: Rank in search results (1-based)
        retrieval_context: Additional context about how this was retrieved

    Example:
        ```python
        result = MemoryResult(
            episode=Episode(...),
            score=0.87,
            rank=1,
            retrieval_context={
                "search_method": "hybrid",
                "graph_distance": 2
            }
        )
        ```
    """
    name: str
    fact: str = Field(description="The fact that was retrieved")
    source_episodes: list[str] = Field(description="The episodes that were used to retrieve the fact")
    rank: int = Field(ge=1, description="Rank in search results (1-based)")
    scope: Literal["user", "org"] = Field(description="The scope of the result")
    additional_context: Dict[str, Any] = Field(default_factory=dict, description="How this result was retrieved")


class UserPreference(BaseModel):
    """Specialized episode for user preferences.

    Captures user-specific preferences like visualization types, date formats,
    default filters, etc.

    Attributes:
        key: Preference key (e.g., "chart_type", "date_format")
        value: Preference value (e.g., "bar", "YYYY-MM-DD")
        category: Category of preference (e.g., "visualization", "formatting")
        description: Human-readable description
        learned_from: Context about how this preference was learned

    Example:
        ```python
        pref = UserPreference(
            key="default_chart_type",
            value="bar",
            category="visualization",
            description="User prefers bar charts for metrics",
            learned_from="Analyst session on 2025-01-24"
        )
        ```
    """

    key: str = Field(description="Preference key")
    value: str = Field(description="Preference value")
    category: str = Field(description="Category (e.g., visualization, formatting)")
    description: str = Field(description="Human-readable description")
    learned_from: str = Field(description="Context about how this was learned")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_episode(self) -> Episode:
        """Convert to Episode for storage."""
        return Episode(
            name=f"pref_{self.key}",
            content=f"{self.description}. Value: {self.value}",
            episode_type=EpisodeType.USER_PREFERENCE,
            source_description=self.learned_from,
            timestamp=self.timestamp,
            metadata={
                "key": self.key,
                "value": self.value,
                "category": self.category,
            },
            entity_references=[self.key, self.category],
        )

class MemoryResultCollection(BaseModel):
    """Collection of memory search results with compact markdown rendering.

    This wrapper around list[MemoryResult] provides a more readable representation
    for LLM tool outputs compared to verbose JSON serialization.

    Attributes:
        results: List of memory search results
        query: The original search query (optional)
        total_count: Total number of results found

    Example:
        ```python
        collection = MemoryResultCollection(
            results=[result1, result2, result3],
            query="ARR metric patterns",
            total_count=3
        )
        summary = collection.to_markdown_summary()
        # Returns compact ranked list with key details
        ```
    """

    results: List[MemoryResult] = Field(default_factory=list)
    query: Optional[str] = Field(None, description="Original search query")
    total_count: int = Field(0, description="Total number of results")

    def to_markdown_summary(self) -> str:
        """Generate compact markdown summary of memory results.

        Returns:
            Markdown-formatted string with ranked facts and metadata.

        Example output:
            ```
            MEMORY SEARCH RESULTS (query: "ARR patterns")
            Found 3 relevant facts:

            1. [org] fct_arr commonly joins to dim_customers on customer_id
               Sources: 3 episodes | Rank: 1

            2. [user] User prefers bar charts for ARR visualizations
               Sources: 1 episode | Rank: 2
            ```
        """
        if not self.results:
            return "No relevant memories found."

        lines = []

        # Header with query if available
        if self.query:
            lines.append(f"MEMORY SEARCH RESULTS (query: \"{self.query}\")")
        else:
            lines.append("MEMORY SEARCH RESULTS")

        lines.append(f"Found {self.total_count} relevant fact{'s' if self.total_count != 1 else ''}:\n")

        # Ranked results
        for result in self.results:
            # Result header with rank and scope
            scope_tag = f"[{result.scope}]"
            lines.append(f"{result.rank}. {scope_tag} {result.name}")

            # Fact content (indented)
            lines.append(f"   {result.fact}")

            # Metadata (compact, one line)
            source_count = len(result.source_episodes)
            metadata_parts = [
                f"Sources: {source_count} episode{'s' if source_count != 1 else ''}"
            ]

            # Add relevant additional context
            if result.additional_context:
                if "confidence" in result.additional_context:
                    conf = result.additional_context["confidence"]
                    metadata_parts.append(f"confidence: {conf:.2f}")
                if "valid_until" in result.additional_context:
                    metadata_parts.append(f"valid_until: {result.additional_context['valid_until']}")

            lines.append(f"   {' | '.join(metadata_parts)}\n")

        return "\n".join(lines)

    def __str__(self) -> str:
        """String representation uses markdown summary."""
        return self.to_markdown_summary()


class DataPattern(BaseModel):
    """Specialized episode for discovered data patterns.

    Captures organizational knowledge about data models, common joins,
    metric definitions, and other patterns discovered through agent interaction.

    Attributes:
        pattern_type: Type of pattern (join, metric, grain, etc.)
        pattern_name: Name of the pattern
        description: Detailed description of the pattern
        models_involved: Models/tables involved in this pattern
        example_usage: Example of how to use this pattern
        confidence: Confidence score (0-1) in this pattern
        discovered_by: Which agent or user discovered this

    Example:
        ```python
        pattern = DataPattern(
            pattern_type="common_join",
            pattern_name="fct_arr_to_dim_customers",
            description="ARR fact table commonly joined to customers dimension on customer_id",
            models_involved=["fct_arr_reporting_monthly", "dim_customers"],
            example_usage="JOIN dim_customers USING (customer_id)",
            confidence=0.95,
            discovered_by="analyst_agent"
        )
        ```
    """

    pattern_type: str = Field(
        description="Type of pattern (join, metric, grain, quality)"
    )
    pattern_name: str = Field(description="Name of the pattern")
    description: str = Field(description="Detailed description")
    models_involved: List[str] = Field(
        default_factory=list, description="Models/tables involved"
    )
    example_usage: Optional[str] = Field(None, description="Example usage")
    confidence: float = Field(
        ge=0.0, le=1.0, default=0.8, description="Confidence score (0-1)"
    )
    discovered_by: str = Field(description="Agent or user who discovered this")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_episode(self) -> Episode:
        """Convert to Episode for storage."""
        content = f"{self.description}"
        if self.example_usage:
            content += f"\n\nExample: {self.example_usage}"

        return Episode(
            name=f"pattern_{self.pattern_name}",
            content=content,
            episode_type=EpisodeType.DATA_PATTERN,
            source_description=f"Discovered by {self.discovered_by}",
            timestamp=self.timestamp,
            metadata={
                "pattern_type": self.pattern_type,
                "pattern_name": self.pattern_name,
                "models_involved": self.models_involved,
                "confidence": self.confidence,
            },
            entity_references=self.models_involved + [self.pattern_name],
        )


class SessionSummary(BaseModel):
    """Structured post-task summary for documenting agent work and learnings.

    Captures both user-specific feedback/preferences and org-wide technical
    learnings after completing complex tasks. Automatically splits content
    into user and org memory.

    Attributes:
        task_description: What the user asked (original question/task)
        decision_process: How agent decided on approach
        solution_approach: How the task was solved
        user_feedback: User corrections/clarifications during task (optional)
        technical_challenges: Tool errors, query issues discovered (optional)
        key_learnings: Bullet points of insights gained
        confidence: Confidence in this summary (0-1)
        discovered_by: Which agent created this summary

    Example:
        ```python
        summary = SessionSummary(
            task_description="User asked about ARR trends by customer segment",
            decision_process="Checked memory, found no patterns. Searched views, picked sv_arr_reporting.",
            solution_approach="Queried with total_arr measure grouped by customer_segment",
            user_feedback="User prefers line charts for trends, wants default 90 days",
            technical_challenges="First query failed combining facts with measures",
            key_learnings=[
                "sv_arr_reporting has customer_segment dimension",
                "User prefers line charts for trends"
            ],
            confidence=0.9,
            discovered_by="analyst_agent"
        )
        ```
    """

    task_description: str = Field(description="What the user asked")
    decision_process: str = Field(description="How agent decided on approach")
    solution_approach: str = Field(description="How the task was solved")
    user_feedback: Optional[str] = Field(
        None, description="User corrections/clarifications during task"
    )
    technical_challenges: Optional[str] = Field(
        None, description="Tool errors, query issues discovered"
    )
    key_learnings: List[str] = Field(
        default_factory=list, description="Bullet points of insights gained"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, default=0.8, description="Confidence in this summary (0-1)"
    )
    discovered_by: str = Field(
        default="agent", description="Which agent created this summary"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_user_episode(self) -> Optional[Episode]:
        """Convert user-specific parts to Episode for user memory.

        Returns Episode containing:
        - Task description
        - Decision process
        - User feedback (if provided)
        - User-specific learnings

        Returns None if no user-specific content exists.
        """
        # Build user-focused content
        content_parts = [
            f"Task: {self.task_description}",
            f"\nApproach: {self.decision_process}",
        ]

        if self.user_feedback:
            content_parts.append(f"\nUser Feedback: {self.user_feedback}")

        # Extract user-specific learnings (preferences, feedback-related)
        user_learnings = [
            learning
            for learning in self.key_learnings
            if any(
                keyword in learning.lower()
                for keyword in ["prefer", "user", "default", "always", "like"]
            )
        ]

        if user_learnings:
            content_parts.append("\nUser Preferences Learned:")
            for learning in user_learnings:
                content_parts.append(f"- {learning}")

        # Only create episode if we have user-specific content
        if not self.user_feedback and not user_learnings:
            return None

        return Episode(
            name=f"session_{self.task_description[:50]}",
            content="\n".join(content_parts),
            episode_type=EpisodeType.USER_SESSION_SUMMARY,
            source_description=f"Session summary from {self.discovered_by}",
            timestamp=self.timestamp,
            metadata={
                "confidence": self.confidence,
                "has_user_feedback": bool(self.user_feedback),
                "learning_count": len(user_learnings),
            },
            entity_references=[],
        )

    def to_org_episode(self) -> Optional[Episode]:
        """Convert org-specific parts to Episode for org memory.

        Returns Episode containing:
        - Task description (anonymized)
        - Solution approach
        - Technical challenges (if encountered)
        - Technical learnings

        Returns None if no org-specific content exists.
        """
        # Build org-focused content
        content_parts = [
            f"Task Type: {self.task_description}",
            f"\nSolution: {self.solution_approach}",
        ]

        if self.technical_challenges:
            content_parts.append(
                f"\nTechnical Challenges: {self.technical_challenges}"
            )

        # Extract technical learnings (patterns, issues, solutions)
        technical_learnings = [
            learning
            for learning in self.key_learnings
            if not any(
                keyword in learning.lower()
                for keyword in ["prefer", "user", "default", "always", "like"]
            )
        ]

        if technical_learnings:
            content_parts.append("\nTechnical Insights:")
            for learning in technical_learnings:
                content_parts.append(f"- {learning}")

        # Only create episode if we have org-specific content
        if not self.technical_challenges and not technical_learnings:
            return None

        return Episode(
            name=f"tech_solution_{self.task_description[:50]}",
            content="\n".join(content_parts),
            episode_type=EpisodeType.ORG_SESSION_SUMMARY,
            source_description=f"Technical summary from {self.discovered_by}",
            timestamp=self.timestamp,
            metadata={
                "confidence": self.confidence,
                "has_technical_challenges": bool(self.technical_challenges),
                "learning_count": len(technical_learnings),
                "solution_approach": self.solution_approach,
            },
            entity_references=[],
        )


__all__ = [
    "EpisodeType",
    "Episode",
    "MemoryResult",
    "MemoryResultCollection",
    "UserPreference",
    "DataPattern",
    "SessionSummary",
]
