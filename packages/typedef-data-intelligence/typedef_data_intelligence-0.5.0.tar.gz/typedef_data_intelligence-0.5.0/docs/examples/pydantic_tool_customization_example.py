"""Example: Customizing tool descriptions for different specialists.

This demonstrates how the same tool can have different descriptions
depending on which specialist is using it.
"""
from pydantic_ai import Agent
from lineage.agent.pydantic.orchestrator import AgentDeps
from lineage.agent.pydantic.tools.data import add_execute_query_tool
from lineage.agent.pydantic.tools.graph import add_query_graph_tool


# Example 1: Metadata Explorer - emphasizes semantic metadata
def create_metadata_explorer_example():
    agent = Agent(
        model="anthropic:claude-haiku-4-5-20251001",
        deps_type=AgentDeps,
        system_prompt="You are a metadata expert.",
        retries=2,
    )

    # Customize description to emphasize semantic queries
    agent = add_query_graph_tool(
        agent,
        description_prefix=(
            "Use this tool to explore semantic metadata and business lineage. "
            "Focus on models, columns, measures, dimensions, and join patterns."
        ),
    )

    return agent


# Example 2: Troubleshooter - emphasizes operational diagnostics
def create_troubleshooter_example():
    agent = Agent(
        model="anthropic:claude-haiku-4-5-20251001",
        deps_type=AgentDeps,
        system_prompt="You are a troubleshooting expert.",
        retries=2,
    )

    # Customize description to emphasize error diagnosis
    agent = add_query_graph_tool(
        agent,
        description_prefix=(
            "Use this tool to investigate operational issues and failures. "
            "Query Jobs, Runs, Errors, and their relationships to diagnose problems."
        ),
    )

    return agent


# Example 3: Data Explorer - emphasizes discovery
def create_data_explorer_example():
    agent = Agent(
        model="anthropic:claude-haiku-4-5-20251001",
        deps_type=AgentDeps,
        system_prompt="You are a data exploration expert.",
        retries=2,
    )

    # Customize description to emphasize data discovery
    agent = add_execute_query_tool(
        agent,
        description_prefix=(
            "Use this tool to discover and preview data in the warehouse. "
            "Perfect for validating hypotheses and sampling tables."
        ),
    )

    return agent


# Example 4: Analyst - emphasizes business analytics
def create_analyst_example():
    agent = Agent(
        model="anthropic:claude-sonnet-4-5-20250929",
        deps_type=AgentDeps,
        system_prompt="You are a business analyst.",
        retries=2,
    )

    # Customize description to emphasize business metrics
    agent = add_execute_query_tool(
        agent,
        description_prefix=(
            "Use this tool to query business metrics and KPIs. "
            "Execute analytical queries for reporting and insights."
        ),
    )

    return agent


if __name__ == "__main__":
    # The same tool (query_graph) gets different descriptions:
    metadata_agent = create_metadata_explorer_example()
    troubleshooter_agent = create_troubleshooter_example()

    print("Metadata Explorer's query_graph tool:")
    print("  → Focus on semantic metadata and business lineage")
    print()

    print("Troubleshooter's query_graph tool:")
    print("  → Focus on operational issues and error diagnosis")
    print()

    print("Both use the same underlying implementation,")
    print("but with tailored descriptions for their role!")
