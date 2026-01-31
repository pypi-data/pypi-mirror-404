#!/usr/bin/env python3
"""CLI runner for PydanticAI agents with pre-configured backends.

Configuration:
    By default uses config.cli.yml in the project root.
    Override with UNIFIED_CONFIG environment variable.

Usage:
    uv run python -m lineage.agent.pydantic.cli_runner analyst                  # Interactive mode
    uv run python -m lineage.agent.pydantic.cli_runner analyst "What views?"    # Single question
    uv run python -m lineage.agent.pydantic.cli_runner investigator "Why is ARR wrong?"  # Troubleshooting
    uv run python -m lineage.agent.pydantic.cli_runner insights "Explain this model"  # Architecture
    uv run python -m lineage.agent.pydantic.cli_runner copilot                  # Interactive with file/git
    uv run python -m lineage.agent.pydantic.cli_runner reconciler "Work on TICKET-123"  # Autonomous
"""
import os
import sys
import argparse

import logfire

# Configure logfire once at startup (before importing agents which trigger orchestrator.py)
# This ensures span context propagates correctly through asyncio.
logfire_token = os.getenv('LOGFIRE_TOKEN')
if logfire_token:
    logfire.configure(token=logfire_token, console=False)

# Import pre-configured agents and deps
from lineage.agent.pydantic.cli_agents import (
    analyst,
    analyst_deps,
    copilot,
    copilot_deps,
    investigator,
    investigator_deps,
    insights,
    insights_deps,
    reconciler,
    reconciler_deps,
)


def run_interactive(agent, deps, agent_name: str):
    """Run agent in interactive mode (REPL) with conversation history."""
    print(f"\n{'=' * 60}")
    print(f"{agent_name.upper()} AGENT - Interactive Mode")
    print(f"{'=' * 60}")
    print("\nType your questions and press Enter. Type 'exit' or 'quit' to stop.\n")

    # Maintain conversation history across turns
    message_history = None

    while True:
        try:
            user_input = input(f"{agent_name}> ").strip()

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye! 👋\n")
                break

            if not user_input:
                continue

            # Run agent with user input and previous conversation history
            result = agent.run_sync(user_input, deps=deps, message_history=message_history)

            # Update message history with all messages from this conversation
            message_history = result.all_messages()

            # Print response - extract output from AgentRunResult
            output = result.output if hasattr(result, 'output') else str(result)
            print(f"\n{output}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def run_single(agent, deps, question: str) -> str:
    """Run agent with a single question."""
    result = agent.run_sync(question, deps=deps)
    # Extract output from AgentRunResult
    return result.output if hasattr(result, 'output') else str(result)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CLI runner for lineage agents with pre-configured backends"
    )
    parser.add_argument(
        "agent",
        choices=["analyst", "investigator", "insights", "copilot", "reconciler"],
        help="Which agent to run (copilot/reconciler require git config)",
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Single question to ask (if omitted, enters interactive mode)",
    )

    args = parser.parse_args()

    # Select agent and deps
    if args.agent == "analyst":
        selected_agent = analyst
        selected_deps = analyst_deps
    elif args.agent == "investigator":
        selected_agent = investigator
        selected_deps = investigator_deps
    elif args.agent == "insights":
        selected_agent = insights
        selected_deps = insights_deps
    elif args.agent == "copilot":
        if copilot is None:
            print("\n❌ Copilot agent not available - git must be enabled in config\n", file=sys.stderr)
            print("Add the following to config.cli.yml:", file=sys.stderr)
            print("  git:", file=sys.stderr)
            print("    enabled: true", file=sys.stderr)
            print("    working_directory: /path/to/dbt/project\n", file=sys.stderr)
            sys.exit(1)
        selected_agent = copilot
        selected_deps = copilot_deps
    else:  # reconciler
        if reconciler is None:
            print("\n❌ Reconciler agent not available - git must be enabled in config\n", file=sys.stderr)
            print("Add the following to config.cli.yml:", file=sys.stderr)
            print("  git:", file=sys.stderr)
            print("    enabled: true", file=sys.stderr)
            print("    working_directory: /path/to/dbt/project\n", file=sys.stderr)
            sys.exit(1)
        selected_agent = reconciler
        selected_deps = reconciler_deps

    # Run in appropriate mode
    if args.question:
        # Single question mode
        try:
            response = run_single(selected_agent, selected_deps, args.question)
            print(f"\n{response}\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n", file=sys.stderr)
            sys.exit(1)
    else:
        # Interactive mode
        run_interactive(selected_agent, selected_deps, args.agent)


if __name__ == "__main__":
    main()
