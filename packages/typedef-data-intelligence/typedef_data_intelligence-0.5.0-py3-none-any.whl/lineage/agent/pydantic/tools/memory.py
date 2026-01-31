"""Memory tools for PydanticAI agents.

This module provides tool functions that agents can use to interact with
the persistent memory system. Tools support both user-specific and
organization-wide memory storage and retrieval.

Available Tools:
- store_user_preference: Store user-specific preferences
- recall_user_context: Search user's recent queries and preferences
- store_data_pattern: Store discovered data model patterns
- recall_data_pattern: Search organization's discovered patterns
- search_memories: Hybrid search across user and/or org memory

All tools gracefully handle cases where memory backend is unavailable.
"""

from __future__ import annotations

import logging
from typing import Literal, Optional

from pydantic_ai import FunctionToolset, RunContext

from lineage.agent.pydantic.tools.common import ToolError, safe_tool, tool_error
from lineage.agent.pydantic.types import (
    AgentDeps,
    StoreDataPatternResult,
    StoreSessionSummaryResult,
    StoreUserPreferenceResult,
)
from lineage.backends.memory.models import (
    DataPattern,
    MemoryResultCollection,
    SessionSummary,
    UserPreference,
)

logger = logging.getLogger(__name__)


# ============================================================================
# User Memory Tools
# ============================================================================

memory_toolset = FunctionToolset()

@memory_toolset.tool
@safe_tool
async def store_user_preference(
    ctx: RunContext[AgentDeps],
    key: str,
    value: str,
    category: str,
    description: str,
) -> StoreUserPreferenceResult | ToolError:
    """Store a user-specific preference in memory.

    Use this tool to remember user preferences like:
    - Preferred chart types ("bar", "line", "pie")
    - Date formats ("YYYY-MM-DD", "MM/DD/YYYY")
    - Default filters or groupings
    - Visualization color schemes
    - Any other personalization settings

    Args:
        key: Preference key (e.g., "default_chart_type", "date_format")
        value: Preference value (e.g., "bar", "YYYY-MM-DD")
        category: Category (e.g., "visualization", "formatting", "filters")
        description: Human-readable description of the preference

    Returns:
        StoreUserPreferenceResult with status and details

    Example:
        ```python
        # User mentions they prefer bar charts
        result = store_user_preference(
            ctx,
            key="default_chart_type",
            value="bar",
            category="visualization",
            description="User prefers bar charts for metric visualizations"
        )
        ```

    Note:
        - Preferences are stored per user (identified by ctx.user_id)
        - If memory backend is unavailable, returns graceful error
        - Preferences persist across sessions
    """
    # Check if memory backend is available
    if not ctx.deps.memory_backend:
        logger.debug("Memory backend not available, skipping user preference storage")
        return StoreUserPreferenceResult(
            success=False,
            message="Memory backend not available (graceful degradation)",
        )

    # Check if user_id is set
    if not ctx.deps.user_id:
        logger.warning("Cannot store user preference: user_id not set")
        return StoreUserPreferenceResult(
            success=False,
            message="User ID not available",
        )

    try:
        # Create UserPreference and convert to Episode
        preference = UserPreference(
            key=key,
            value=value,
            category=category,
            description=description,
            learned_from=f"Agent interaction with {ctx.deps.user_id}",
        )
        episode = preference.to_episode()

        # Store in user memory (await to ensure completion)
        if ctx.deps.memory_backend:
            try:
                await ctx.deps.memory_backend.store_user_memory(
                    user_id=ctx.deps.user_id, episode=episode
                )
                logger.info(
                    f"Stored user preference: user={ctx.deps.user_id}, key={key}, value={value}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to store user preference in memory: {e}",
                    exc_info=True,
                )
                # Continue - memory storage failure shouldn't break the tool
        return StoreUserPreferenceResult(
            success=True,
            message=f"Preference '{key}' stored successfully",
            key=key,
            value=value,
            category=category,
        )

    except Exception as e:
        logger.error(f"Failed to store user preference: {e}")
        return tool_error(f"Failed to store preference: {str(e)}")

@memory_toolset.tool
@safe_tool
async def recall_user_context(ctx: RunContext[AgentDeps], query: str, limit: int = 25) -> str | ToolError:
    """Search and recall user's recent queries, preferences, and context.

    Use this tool to:
    - Remember what the user asked about previously
    - Recall user's stated preferences
    - Understand user's historical context
    - Personalize responses based on past interactions

    Args:
        query: Search query (e.g., "chart preferences", "previous ARR queries")
        limit: Maximum number of results to return (default: 25, increase if needed)

    Returns:
        Markdown-formatted summary of memory results (compact format)

    Example:
        ```python
        # Make multiple queries to understand user fully
        prefs = recall_user_context(ctx, query="chart visualization preferences")
        history = recall_user_context(ctx, query="previous ARR metric queries")
        # Each returns compact markdown with ranked facts
        ```

    Note:
        - Searches only the current user's memory (personalized)
        - Returns empty result if no relevant memories found
        - Make multiple queries with different phrasings to gather comprehensive user context
    """
    # Check if memory backend is available
    if not ctx.deps.memory_backend:
        logger.debug("Memory backend not available for user context recall")
        # Return empty collection for graceful degradation
        collection = MemoryResultCollection(
            results=[],
            query=query,
            total_count=0
        )
        return collection.to_markdown_summary()

    # Check if user_id is set
    if not ctx.deps.user_id:
        logger.warning("Cannot recall user context: user_id not set")
        collection = MemoryResultCollection(
            results=[],
            query=query,
            total_count=0
        )
        return collection.to_markdown_summary()

    try:
        # Search user memory
        results = await ctx.deps.memory_backend.search_user_memory(
            user_id=ctx.deps.user_id, query=query, limit=limit
        )

        logger.info(
            f"User context recall: user={ctx.deps.user_id}, query='{query}', "
            f"found={len(results)}"
        )

        # Wrap in collection for compact representation
        collection = MemoryResultCollection(
            results=results,
            query=query,
            total_count=len(results)
        )
        return collection.to_markdown_summary()

    except Exception as e:
        logger.error(f"Failed to recall user context: {e}")
        return tool_error(f"Search failed: {str(e)}")


# ============================================================================
# Organization Memory Tools
# ============================================================================


@memory_toolset.tool
@safe_tool
async def store_data_pattern(
    ctx: RunContext[AgentDeps],
    pattern_type: str,
    pattern_name: str,
    description: str,
    models_involved: list[str],
    example_usage: Optional[str] = None,
    confidence: float = 0.8,
) -> StoreDataPatternResult | ToolError:
    """Store a discovered data model pattern in organization memory.

    Use this tool when you discover patterns like:
    - Common joins between tables ("fct_arr often joins dim_customers on customer_id")
    - Metric definitions ("ARR is sum of subscription amounts")
    - Data grain patterns ("fct_orders is per order line item")
    - Common filters or aggregations
    - Data quality patterns

    This knowledge is shared across ALL users in the organization.

    Args:
        pattern_type: Type of pattern ("common_join", "metric", "grain", "quality")
        pattern_name: Name of the pattern (e.g., "arr_to_customers_join")
        description: Detailed description of the pattern
        models_involved: List of model/table names involved
        example_usage: Optional example SQL or usage
        confidence: Confidence score 0-1 (default: 0.8)

    Returns:
        StoreDataPatternResult with status and details

    Example:
        ```python
        # Agent discovers ARR commonly joins to customers
        result = store_data_pattern(
            ctx,
            pattern_type="common_join",
            pattern_name="arr_to_customers",
            description="ARR fact table commonly joined to customers dimension on customer_id",
            models_involved=["fct_arr_reporting_monthly", "dim_customers"],
            example_usage="JOIN dim_customers USING (customer_id)",
            confidence=0.95
        )
        ```

    Note:
        - Patterns are stored in organization memory (shared across users)
        - High-confidence patterns (>0.9) are prioritized in search
        - Duplicate patterns are merged automatically by Graphiti
    """
    # Check if memory backend is available
    if not ctx.deps.memory_backend:
        logger.debug("Memory backend not available for data pattern storage")
        return StoreDataPatternResult(
            success=False,
            message="Memory backend not available",
        )

    # Use org_id from context (defaults to "default")
    org_id = ctx.deps.org_id

    try:
        # Create DataPattern and convert to Episode
        pattern = DataPattern(
            pattern_type=pattern_type,
            pattern_name=pattern_name,
            description=description,
            models_involved=models_involved,
            example_usage=example_usage,
            confidence=confidence,
            discovered_by=f"agent_{ctx.deps.user_id or 'system'}",
        )
        episode = pattern.to_episode()

        # Store in org memory (await to ensure completion)
        if ctx.deps.memory_backend:
            try:
                await ctx.deps.memory_backend.store_org_memory(org_id=org_id, episode=episode)
                logger.info(
                    f"Stored data pattern: org={org_id}, type={pattern_type}, "
                    f"name={pattern_name}, confidence={confidence}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to store data pattern in memory: {e}",
                    exc_info=True,
                )
                # Continue - memory storage failure shouldn't break the tool

        return StoreDataPatternResult(
            success=True,
            message=f"Data pattern '{pattern_name}' stored successfully",
            pattern_type=pattern_type,
            pattern_name=pattern_name,
            confidence=confidence,
            models_involved=models_involved,
        )

    except Exception as e:
        logger.error(f"Failed to store data pattern: {e}")
        return tool_error(f"Failed to store pattern: {str(e)}")


@memory_toolset.tool
@safe_tool
async def recall_data_pattern(ctx: RunContext[AgentDeps], query: str, limit: int = 10) -> str | ToolError:
    """Search and recall organization's discovered data patterns.

    IMPORTANT: Make queries with different phrasings to find all relevant facts before proceeding with tasks.

    Use this tool to:
    - Find common joins between tables
    - Look up metric definitions
    - Discover data grain patterns
    - Learn from previously discovered patterns

    This searches ORGANIZATION memory (shared across all users).

    Args:
        query: Search query (e.g., "ARR joins", "customer dimension", "grain patterns")
        limit: Maximum number of results to return (default: 25, increase if needed)

    Returns:
        Markdown-formatted summary of memory results (compact format)

    Example:
        ```python
        # Make multiple queries to gather comprehensive context
        arr_patterns = recall_data_pattern(ctx, query="ARR metric patterns")
        join_patterns = recall_data_pattern(ctx, query="common table joins")
        # Each returns compact markdown with ranked facts
        ```

    Note:
        - Searches organization memory (shared across users)
        - Returns patterns discovered by any agent or user
    """
    # Check if memory backend is available
    if not ctx.deps.memory_backend:
        logger.debug("Memory backend not available for data pattern recall")
        # Return empty collection for graceful degradation
        collection = MemoryResultCollection(
            results=[],
            query=query,
            total_count=0
        )
        return collection.to_markdown_summary()

    org_id = ctx.deps.org_id

    try:
        # Search org memory
        results = await ctx.deps.memory_backend.search_org_memory(
            org_id=org_id, query=query, limit=limit
        )
        logger.info(
            f"Data pattern recall: org={org_id}, query='{query}', "
            f"found={len(results)}"
        )

        # Wrap in collection for compact representation
        collection = MemoryResultCollection(
            results=results,
            query=query,
            total_count=len(results)
        )
        return collection.to_markdown_summary()

    except Exception as e:
        logger.error(f"Failed to recall data patterns: {e}")
        return tool_error(f"Search failed: {str(e)}")


# ============================================================================
# Hybrid Memory Search
# ============================================================================


@memory_toolset.tool
@safe_tool
async def search_memories(
    ctx: RunContext[AgentDeps],
    query: str,
    scope: Literal["user", "org", "both"] = "both",
    limit: int = 10,
) -> str | ToolError:
    """Search across user and/or organization memory simultaneously.

    IMPORTANT: Make MULTIPLE queries with
    different phrasings at the START of tasks to gather all relevant context.

    This is the most powerful memory search tool - it can search:
    - Only user memory (scope="user") - preferences, past queries
    - Only organization memory (scope="org") - data patterns, metrics
    - Both user and org memory (scope="both", RECOMMENDED for comprehensive context)

    Use this when you want comprehensive memory search that includes
    both user preferences AND organizational knowledge.

    Args:
        query: Search query (natural language)
        scope: Search scope ("user", "org", or "both" - RECOMMENDED: "both")
        limit: Maximum total results to return (default: 25, increase to 50+ if needed)

    Returns:
        Markdown-formatted summary of memory results (compact format with [user]/[org] tags)

    Example:
        ```python
        # At task start: make multiple comprehensive queries
        metrics = search_memories(ctx, query="ARR metrics and calculations", scope="both")
        viz = search_memories(ctx, query="chart preferences visualizations", scope="both")
        joins = search_memories(ctx, query="table relationships joins", scope="both")
        # Each returns compact markdown - safe to request many results
        ```

    Note:
        - Results from both sources are merged and re-ranked by relevance
        - User memory results may be prioritized for personalization
        - This is the recommended tool for comprehensive memory search
    """
    # Check if memory backend is available
    if not ctx.deps.memory_backend:
        logger.debug("Memory backend not available for memory search")
        # Return empty collection for graceful degradation
        collection = MemoryResultCollection(
            results=[],
            query=query,
            total_count=0
        )
        return collection.to_markdown_summary()

    try:
        results = []

        if scope == "user":
            # Search only user memory
            if ctx.deps.user_id:
                results = await ctx.deps.memory_backend.search_user_memory(
                    user_id=ctx.deps.user_id, query=query, limit=limit
                )
        elif scope == "org":
            # Search only org memory
            org_id = ctx.deps.org_id
            results = await ctx.deps.memory_backend.search_org_memory(
                org_id=org_id, query=query, limit=limit
            )
        else:  # scope == "both"
            # Search both user and org memory
            if ctx.deps.user_id:
                org_id = ctx.deps.org_id
                results = await ctx.deps.memory_backend.search_all(
                    user_id=ctx.deps.user_id, org_id=org_id, query=query, limit=limit
                )

        logger.info(
            f"Memory search: scope={scope}, query='{query}', found={len(results)}"
        )

        # Wrap in collection for compact representation
        collection = MemoryResultCollection(
            results=results,
            query=query,
            total_count=len(results)
        )
        return collection.to_markdown_summary()

    except Exception as e:
        logger.error(f"Failed to search memories: {e}")
        return tool_error(f"Search failed: {str(e)}")


# ============================================================================
# Session Summary Tool (Post-Task Documentation)
# ============================================================================


@memory_toolset.tool
@safe_tool
async def store_session_summary(
    ctx: RunContext[AgentDeps],
    task_description: str,
    decision_process: str,
    solution_approach: str,
    user_feedback: Optional[str] = None,
    technical_challenges: Optional[str] = None,
    key_learnings: Optional[list[str]] = None,
    confidence: float = 0.8,
) -> StoreSessionSummaryResult | ToolError:
    """Store post-task summary in both user and org memory.

    Use this AFTER completing complex tasks to document your work, learnings,
    and feedback. This tool automatically splits content into:
    - **User memory**: Task context, decision process, user feedback, preferences
    - **Org memory**: Technical challenges, solution patterns, query insights

    **WHEN TO USE (Agent discretion):**
    - ✅ Complex multi-step tasks requiring multiple tools
    - ✅ When you discovered something non-obvious or learned new patterns
    - ✅ When user provided corrections/feedback during the task
    - ✅ When you encountered and resolved technical challenges
    - ✅ When learnings would help future queries or other users

    **WHEN TO SKIP:**
    - ❌ Simple single-query tasks (e.g., list tables, preview data)
    - ❌ Routine operations with no novel learnings
    - ❌ Tasks that failed or were abandoned without completion
    - ❌ Nothing noteworthy was learned

    Args:
        task_description: What the user asked (original question/task)
        decision_process: How you decided on your approach
        solution_approach: How you solved the task (tools used, queries executed)
        user_feedback: User corrections/clarifications during task (optional)
        technical_challenges: Tool errors, query issues discovered (optional)
        key_learnings: List of insights gained (will be auto-split into user vs org)
        confidence: Confidence in this summary, 0-1 (default: 0.8)

    Returns:
        StoreSessionSummaryResult with storage results

    Example:
        ```python
        # After completing ARR analysis with user feedback
        store_session_summary(
            task_description="User asked about ARR trends by customer segment for 2024",
            decision_process="Checked memory first (no results), searched semantic views, identified sv_arr_reporting as best match, explored schema to find customer_segment dimension",
            solution_approach="Used query_semantic_view with total_arr measure grouped by customer_segment and month, filtered to year=2024, created line chart visualization",
            user_feedback="User initially wanted bar chart but preferred line chart after seeing it. User wants to default to 'last 90 days' for future date queries",
            technical_challenges="First query failed because I tried to combine facts with measures - learned measures require aggregation context, cannot mix with row-level facts",
            key_learnings=[
                "sv_arr_reporting has customer_segment dimension for analysis",
                "User prefers line charts for trend analysis over time",
                "User's default time range preference is last 90 days",
                "Cannot combine facts with measures in same query",
                "sv_arr_reporting commonly queried for customer segmentation"
            ],
            confidence=0.9
        )
        ```

    Note:
        - Tool auto-splits learnings: user preferences → user memory, technical → org memory
        - Only stores to each memory if relevant content exists
        - User feedback always goes to user memory
        - Technical challenges always go to org memory
        - Learnings split by keywords ("prefer", "user", "default" → user; technical terms → org)
    """
    # Check if memory backend is available
    if not ctx.deps.memory_backend:
        logger.debug("Memory backend not available for session summary")
        return StoreSessionSummaryResult(
            success=False,
            message="Memory backend not available (graceful degradation)",
            user_stored=False,
            org_stored=False,
        )

    # Check if user_id is set (needed for user memory)
    user_id = ctx.deps.user_id
    org_id = ctx.deps.org_id

    try:
        # Create SessionSummary object
        summary = SessionSummary(
            task_description=task_description,
            decision_process=decision_process,
            solution_approach=solution_approach,
            user_feedback=user_feedback,
            technical_challenges=technical_challenges,
            key_learnings=key_learnings or [],
            confidence=confidence,
            discovered_by=f"agent_{user_id or 'system'}",
        )

        # Convert to episodes
        user_episode = summary.to_user_episode()
        org_episode = summary.to_org_episode()

        # Storage results
        user_stored = False
        org_stored = False

        # Store user episode if exists and user_id is set
        if user_episode and user_id and ctx.deps.memory_backend:
            try:
                await ctx.deps.memory_backend.store_user_memory(
                    user_id=user_id, episode=user_episode
                )
                user_stored = True
                logger.info(
                    f"Stored user session summary: user={user_id}, "
                    f"task={task_description[:50]}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to store user session summary in memory: {e}",
                    exc_info=True,
                )
                # Continue - memory storage failure shouldn't break the tool

        # Store org episode if exists
        if org_episode and ctx.deps.memory_backend:
            try:
                await ctx.deps.memory_backend.store_org_memory(
                    org_id=org_id, episode=org_episode
                )
                org_stored = True
                logger.info(
                    f"Stored org session summary: org={org_id}, "
                    f"task={task_description[:50]}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to store org session summary in memory: {e}",
                    exc_info=True,
                )
                # Continue - memory storage failure shouldn't break the tool

        # Build response message
        messages = []
        if user_stored:
            messages.append("User context updated with task summary and feedback")
        if org_stored:
            messages.append("Org knowledge updated with technical insights")

        if not user_stored and not org_stored:
            messages.append(
                "No actionable learnings to store (neither user feedback nor technical insights)"
            )

        return StoreSessionSummaryResult(
            success=user_stored or org_stored,
            message=". ".join(messages),
            user_stored=user_stored,
            org_stored=org_stored,
            learning_count=len(key_learnings or []),
        )

    except Exception as e:
        logger.error(f"Failed to store session summary: {e}")
        return tool_error(f"Failed to store summary: {str(e)}")


__all__ = [
    "store_user_preference",
    "recall_user_context",
    "store_data_pattern",
    "recall_data_pattern",
    "search_memories",
    "store_session_summary",
]
