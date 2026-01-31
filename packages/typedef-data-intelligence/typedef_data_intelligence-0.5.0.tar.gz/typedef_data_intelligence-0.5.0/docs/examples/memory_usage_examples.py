"""Memory System Usage Examples.

This module demonstrates how to use the memory system in different scenarios.

Prerequisites:
    - FalkorDB running on localhost:6379
    - Config with memory.enabled=true
    - Agents initialized with memory backend
"""

from datetime import datetime

from lineage.backends.memory.factory import create_memory_backend
from lineage.backends.memory.models import (
    Episode,
    EpisodeType,
    UserPreference,
    DataPattern,
)
from lineage.agent.pydantic.memory_observer import MemoryObserver


# ============================================================================
# Example 1: Basic Memory Backend Usage
# ============================================================================


def example_basic_usage():
    """Basic memory backend initialization and usage."""
    print("=" * 60)
    print("Example 1: Basic Memory Backend Usage")
    print("=" * 60)

    # Create memory backend
    memory = create_memory_backend(
        backend="falkordb",
        host="localhost",
        port=6379,
        username="",
        password="",
        default_org_id="example_org",
    )

    if not memory:
        print("❌ Memory backend not available")
        return

    print("✅ Memory backend initialized")

    # Store a user preference
    preference = UserPreference(
        key="default_chart_type",
        value="bar",
        category="visualization",
        description="User prefers bar charts for metric visualizations",
        learned_from="Interactive session with Alice",
    )

    memory.store_user_memory(user_id="alice", episode=preference.to_episode())
    print("✅ Stored user preference: default_chart_type=bar")

    # Search user memory
    results = memory.search_user_memory(user_id="alice", query="chart", limit=5)
    print(f"✅ Found {len(results)} memories for alice")

    for result in results:
        print(
            f"   - {result.episode.name} (score: {result.score:.2f}): "
            f"{result.episode.content[:50]}..."
        )

    # Store organization pattern
    pattern = DataPattern(
        pattern_type="common_join",
        pattern_name="customers_to_orders",
        description="Customers dimension commonly joined to orders fact on customer_id",
        models_involved=["dim_customers", "fct_orders"],
        example_usage="JOIN fct_orders USING (customer_id)",
        discovered_by="analyst_agent",
        confidence=0.95,
    )

    memory.store_org_memory(org_id="example_org", episode=pattern.to_episode())
    print("✅ Stored organization pattern: customers_to_orders join")

    # Search organization memory
    results = memory.search_org_memory(
        org_id="example_org", query="customer joins", limit=5
    )
    print(f"✅ Found {len(results)} org patterns")

    # Hybrid search (both user and org)
    results = memory.search_all(
        user_id="alice", org_id="example_org", query="customer", limit=10
    )
    print(f"✅ Hybrid search found {len(results)} total memories")

    print()


# ============================================================================
# Example 2: Memory Observer for Auto-Capture
# ============================================================================


def example_memory_observer():
    """Demonstrate automatic pattern capture with MemoryObserver."""
    print("=" * 60)
    print("Example 2: Memory Observer for Auto-Capture")
    print("=" * 60)

    memory = create_memory_backend(
        backend="falkordb",
        host="localhost",
        port=6379,
    )

    if not memory:
        print("❌ Memory backend not available")
        return

    # Create observer
    observer = MemoryObserver(memory_backend=memory)
    print("✅ Memory observer initialized")

    # Scenario 1: User queries a semantic view
    print("\n📊 Scenario: User queries ARR by customer segment")
    observer.observe_semantic_query(
        org_id="example_org",
        view_name="sv_arr_reporting",
        query_pattern="Group by customer_segment, aggregate total_arr",
        dimensions=["customer_segment"],
        measures=["total_arr"],
        discovered_by="analyst_agent",
    )
    print("✅ Auto-captured semantic query pattern")

    # Scenario 2: Agent discovers a join
    print("\n🔗 Scenario: Agent joins ARR to customer dimension")
    observer.observe_join_pattern(
        org_id="example_org",
        models=["fct_arr_reporting", "dim_customers"],
        join_condition="customer_id",
        discovered_by="analyst_agent",
    )
    print("✅ Auto-captured join pattern")

    # Scenario 3: Agent defines a metric
    print("\n📈 Scenario: Agent calculates MRR metric")
    observer.observe_metric_definition(
        org_id="example_org",
        metric_name="MRR",
        calculation="SUM(subscription_amount) / 12",
        source_model="fct_subscriptions",
        discovered_by="analyst_agent",
    )
    print("✅ Auto-captured metric definition")

    # Scenario 4: Agent finds data quality issue
    print("\n⚠️  Scenario: Agent finds null email addresses")
    observer.observe_data_quality_issue(
        org_id="example_org",
        issue_type="null_values",
        description="dim_customers has approximately 5% null email addresses",
        affected_models=["dim_customers"],
        discovered_by="quality_agent",
    )
    print("✅ Auto-captured data quality issue")

    # Verify patterns were stored
    results = memory.search_org_memory(org_id="example_org", query="patterns", limit=10)
    print(f"\n✅ Total patterns stored: {len(results)}")

    print()


# ============================================================================
# Example 3: User Personalization Flow
# ============================================================================


def example_user_personalization():
    """Demonstrate building user personalization over time."""
    print("=" * 60)
    print("Example 3: User Personalization Flow")
    print("=" * 60)

    memory = create_memory_backend(
        backend="falkordb",
        host="localhost",
        port=6379,
    )

    if not memory:
        print("❌ Memory backend not available")
        return

    user_id = "bob@example.com"

    # Session 1: User asks about ARR
    print("\n📅 Session 1: Bob asks about ARR trends")
    memory.store_user_memory(
        user_id=user_id,
        episode=Episode(
            name="arr_trends_query",
            content="User asked: 'Show me ARR trends by customer segment for last quarter'",
            episode_type=EpisodeType.USER_QUERY,
            source_description="Analyst session",
        ),
    )
    print("✅ Stored query: ARR trends by segment")

    # Session 2: User expresses chart preference
    print("\n📅 Session 2: Bob mentions chart preference")
    memory.store_user_memory(
        user_id=user_id,
        episode=UserPreference(
            key="preferred_chart_for_trends",
            value="line",
            category="visualization",
            description="User prefers line charts for trend analysis",
            learned_from="Session 2 interaction",
        ).to_episode(),
    )
    print("✅ Stored preference: line charts for trends")

    # Session 3: User sets default date range
    print("\n📅 Session 3: Bob sets default date range")
    memory.store_user_memory(
        user_id=user_id,
        episode=UserPreference(
            key="default_date_range",
            value="last_90_days",
            category="filters",
            description="User's default date range is last 90 days",
            learned_from="Session 3 settings",
        ).to_episode(),
    )
    print("✅ Stored preference: last 90 days default")

    # Session 4: Recall context for personalization
    print("\n📅 Session 4: Bob returns, agent recalls preferences")
    results = memory.search_user_memory(user_id=user_id, query="preferences", limit=5)

    print(f"✅ Recalled {len(results)} preferences:")
    for result in results:
        print(f"   - {result.episode.name}: {result.episode.content[:60]}...")

    # Agent can now personalize:
    # - Use line charts for trend queries (not bar charts)
    # - Default to last 90 days
    # - Remember user recently looked at ARR by segment

    print()


# ============================================================================
# Example 4: Organization Knowledge Building
# ============================================================================


def example_org_knowledge_building():
    """Demonstrate building organization-wide knowledge base."""
    print("=" * 60)
    print("Example 4: Organization Knowledge Building")
    print("=" * 60)

    memory = create_memory_backend(
        backend="falkordb",
        host="localhost",
        port=6379,
    )

    if not memory:
        print("❌ Memory backend not available")
        return

    org_id = "acme_corp"

    # Pattern 1: Common fact-to-dimension joins
    print("\n🔗 Building knowledge: Common joins")
    common_joins = [
        ("fct_orders", "dim_customers", "customer_id"),
        ("fct_orders", "dim_products", "product_id"),
        ("fct_arr", "dim_subscriptions", "subscription_id"),
        ("fct_pipeline", "dim_accounts", "account_id"),
    ]

    for fact, dim, join_key in common_joins:
        pattern = DataPattern(
            pattern_type="common_join",
            pattern_name=f"{fact}_to_{dim}",
            description=f"{fact} commonly joined to {dim} on {join_key}",
            models_involved=[fact, dim],
            example_usage=f"JOIN {dim} USING ({join_key})",
            discovered_by="data_engineer_agent",
            confidence=0.95,
        )
        memory.store_org_memory(org_id=org_id, episode=pattern.to_episode())

    print(f"✅ Stored {len(common_joins)} common join patterns")

    # Pattern 2: Key metric definitions
    print("\n📊 Building knowledge: Metric definitions")
    metrics = [
        ("ARR", "Annual Recurring Revenue = SUM(subscription_amount)", "fct_arr"),
        (
            "Customer_LTV",
            "Lifetime Value = SUM(revenue) per customer",
            "fct_orders",
        ),
        ("Churn_Rate", "Churn = cancelled / total subscriptions", "fct_subscriptions"),
    ]

    for metric_name, calculation, source in metrics:
        pattern = DataPattern(
            pattern_type="metric_definition",
            pattern_name=metric_name,
            description=calculation,
            models_involved=[source],
            example_usage=calculation.split("=")[1].strip(),
            discovered_by="analyst_agent",
            confidence=0.99,
        )
        memory.store_org_memory(org_id=org_id, episode=pattern.to_episode())

    print(f"✅ Stored {len(metrics)} metric definitions")

    # Pattern 3: Data grain knowledge
    print("\n🌾 Building knowledge: Table grain patterns")
    grains = [
        ("fct_orders", "One row per order line item"),
        ("fct_arr", "One row per subscription per month"),
        ("dim_customers", "One row per customer"),
    ]

    for model, grain_desc in grains:
        pattern = DataPattern(
            pattern_type="grain",
            pattern_name=f"{model}_grain",
            description=f"{model}: {grain_desc}",
            models_involved=[model],
            discovered_by="data_engineer_agent",
            confidence=0.90,
        )
        memory.store_org_memory(org_id=org_id, episode=pattern.to_episode())

    print(f"✅ Stored {len(grains)} grain patterns")

    # Query the built knowledge
    print("\n🔍 Querying organization knowledge")
    results = memory.search_org_memory(org_id=org_id, query="ARR metric", limit=5)
    print(f"✅ ARR metric search: {len(results)} results")

    for result in results:
        print(
            f"   - {result.episode.metadata.get('pattern_type', 'unknown')}: "
            f"{result.episode.name} (confidence: {result.episode.metadata.get('confidence', 0):.2f})"
        )

    print()


# ============================================================================
# Example 5: Memory Statistics and Management
# ============================================================================


def example_memory_management():
    """Demonstrate memory statistics and management."""
    print("=" * 60)
    print("Example 5: Memory Statistics and Management")
    print("=" * 60)

    memory = create_memory_backend(
        backend="falkordb",
        host="localhost",
        port=6379,
    )

    if not memory:
        print("❌ Memory backend not available")
        return

    # Get user statistics
    print("\n📊 User Memory Statistics")
    stats = memory.get_stats(user_id="alice")
    print(f"User memory: {stats}")

    # Get organization statistics
    print("\n📊 Organization Memory Statistics")
    stats = memory.get_stats(org_id="example_org")
    print(f"Org memory: {stats}")

    # Clear user memory (GDPR compliance example)
    print("\n🗑️  GDPR: User requests memory deletion")
    memory.clear_user_memory(user_id="alice")
    print("✅ Alice's memory cleared")

    # Verify deletion
    stats = memory.get_stats(user_id="alice")
    print(f"Alice's memory after deletion: {stats}")

    print()


# ============================================================================
# Main
# ============================================================================


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MEMORY SYSTEM USAGE EXAMPLES")
    print("=" * 60 + "\n")

    # Run all examples
    example_basic_usage()
    example_memory_observer()
    example_user_personalization()
    example_org_knowledge_building()
    example_memory_management()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
