"""Prompt loader for agents.

Loads prompts from YAML files, with optional Jinja template rendering.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, Optional

import yaml
from jinja2 import Template

from lineage.backends.config import GitConfig
from lineage.backends.data_query import DataQueryBackend
from lineage.backends.lineage import LineageStorage
from lineage.backends.tickets import TicketStorage

logger = logging.getLogger(__name__)


def load_prompt(
    agent_name: str,
    agent_type: str = "pydantic",
    data_backend: Optional[DataQueryBackend] = None,
    lineage_backend: Optional[LineageStorage] = None,
    ticket_storage: Optional[TicketStorage] = None,
    git_cfg: Optional[GitConfig] = None,
    role: Optional[Literal["copilot", "reconciler"]] = None,
    **extra_context,
) -> str:
    """Load agent prompt from YAML file, with optional Jinja template rendering.

    Loads YAML file and applies Jinja templating to the prompt string only.
    This avoids YAML syntax conflicts with Jinja template syntax.

    Args:
        agent_name: Name of agent (e.g., "metadata_explorer", "analyst", "gateway")
        agent_type: Type of agent - "pydantic" (WebUI) or "anthropic" (CLI). Default: "pydantic"
        data_backend: Optional data backend for injecting SQL hints
        lineage_backend: Optional lineage backend for injecting graph schema
        ticket_storage: Optional ticket storage backend for injecting ticket storage hints
        git_cfg: Optional git configuration for injecting git working directory (by default use cwd)
        role: Role of the agent - copilor or autonomous workflow. Used for data engineer agent.
        **extra_context: Additional context variables for Jinja template

    Returns:
        System prompt string (rendered from Jinja template if applicable)

    Raises:
        ValueError: If agent_type is not "pydantic" or "anthropic"
        FileNotFoundError: If prompt file not found
    """
    # Validate agent_type
    if agent_type not in ["pydantic", "anthropic"]:
        raise ValueError(f"agent_type must be 'pydantic' or 'anthropic', got: {agent_type}")

    # Determine prompts directory based on agent type
    if agent_type == "pydantic":
        prompts_dir = Path(__file__).parent / "pydantic" / "prompts"
    else:  # anthropic
        prompts_dir = Path(__file__).parent / "anthropic" / "prompts"

    base_name = agent_name.replace('-', '_')

    # For data_engineer agent, use role-specific prompt files
    if base_name == "data_engineer" and role:
        base_name = f"{base_name}_{role}"
        logger.info(f"Using role-specific prompt: {base_name} for role={role}")

    # Try .yaml.j2 first, then fall back to .yaml
    jinja_file = prompts_dir / f"{base_name}.yaml.j2"
    yaml_file = prompts_dir / f"{base_name}.yaml"

    logger.info(f"Loading prompt for agent: {agent_name} from directory: {prompts_dir} jinja file: {jinja_file}")
    target_file = jinja_file if jinja_file.exists() else yaml_file
    if not target_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {agent_name} (looking for {base_name})")

    # Load YAML file
    with open(target_file) as f:
        data = yaml.safe_load(f)

    prompt_template = data.get("prompt", "")
    if not prompt_template:
        return ""

    # Check if prompt contains Jinja syntax
    has_jinja = "{{" in prompt_template or "{%" in prompt_template

    if not has_jinja:
        # No templating needed
        return prompt_template

    # Apply Jinja templating to prompt string only
    template = Template(prompt_template)

    # Prepare context for injection
    context = {}

    # Add data backend hints if available
    if data_backend:
        # get_agent_hints() composes all backend-specific guidance
        agent_hints = data_backend.get_agent_hints()
        if agent_hints:
            context["data_backend_hints"] = agent_hints

    if ticket_storage:
        context["ticket_storage_enabled"] = True
        agent_hints = ticket_storage.get_agent_hints()
        if agent_hints:
            context["ticket_storage_hints"] = agent_hints
    else:
        context["ticket_storage_enabled"] = False

    # Add git backend context if available (for cli agents)
    if git_cfg:
        context["git_enabled"] = git_cfg.enabled
        context["git_working_directory"] = git_cfg.working_directory
    else:
        context["git_enabled"] = False
        # Use filesystem_config working_directory if available, otherwise cwd
        filesystem_config = extra_context.get("filesystem_config")
        if filesystem_config and hasattr(filesystem_config, "working_directory"):
            context["git_working_directory"] = filesystem_config.working_directory
        else:
            context["git_working_directory"] = Path.cwd()

    # Add lineage backend context if available
    if lineage_backend:
        try:
            # Add minimal schema summary for system prompts (~1,700 tokens)
            # Agents can call get_graph_schema(format="compact") for full details
            schema_summary = lineage_backend.get_graph_schema(format="summary")
            context["lineage_graph_schema"] = schema_summary

            # Add Cypher dialect hints
            lineage_hints = lineage_backend.get_agent_hints()
            if lineage_hints:
                context["lineage_cypher_hints"] = lineage_hints
        except Exception as e:
            logger.warning(f"Could not load lineage backend context: {e}")

    if role:
        context["role"] = role

    # Add any extra context variables
    context.update(extra_context)
    logger.debug(f"Context: {context}")
    # Render template
    rendered = template.render(**context)

    # Log key context variables for debugging
    has_schema = "lineage_graph_schema" in context and context["lineage_graph_schema"]
    has_cypher_hints = "lineage_cypher_hints" in context and context["lineage_cypher_hints"]
    logger.info(
        f"Loaded prompt for {agent_name}: "
        f"has_lineage_graph_schema={has_schema}, "
        f"has_cypher_hints={has_cypher_hints}, "
        f"prompt_length={len(rendered)} chars"
    )
    logger.debug(f"Rendered prompt (first 500 chars): {rendered[:500]}")
    return rendered
