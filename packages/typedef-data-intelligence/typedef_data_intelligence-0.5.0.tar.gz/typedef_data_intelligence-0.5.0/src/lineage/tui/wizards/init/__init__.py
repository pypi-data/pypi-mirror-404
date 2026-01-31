"""Init wizard for typedef setup.

This module provides a full-screen TUI wizard for the `typedef init` command.
"""
from lineage.tui.wizards.base import BaseWizardApp, WizardScreen
from lineage.tui.wizards.init.steps import (
    DatabaseSelectionStep,
    DbtPathStep,
    DbtSubProjectStep,
    IntegrationsStep,
    LlmKeysStep,
    PreFlightCheckStep,
    ProfilesYmlStep,
    ProjectNameStep,
    SnowflakeConnectionStep,
    SummaryStep,
)

__all__ = [
    "create_init_wizard",
    "create_add_project_wizard",
    "InitWizardApp",
]


def create_init_wizard() -> WizardScreen:
    """Create the init wizard screen."""
    steps = [
        ProjectNameStep(),          # Step 1: Project name
        DbtPathStep(),              # Step 2: dbt project path or git URL
        DbtSubProjectStep(),        # Step 3: Select sub-project (if monorepo)
        SnowflakeConnectionStep(),  # Step 4: Snowflake credentials
        DatabaseSelectionStep(),    # Step 5: Select databases
        LlmKeysStep(),              # Step 6: Optional LLM API keys
        IntegrationsStep(),         # Step 7: Optional integrations (Linear, Logfire)
        ProfilesYmlStep(),          # Step 8: Preview profiles.yml (no write yet)
        PreFlightCheckStep(),       # Step 9: Setup & validation (profiles.yml + dbt docs + checks)
        SummaryStep(),              # Step 10: Final summary before completion
    ]

    return WizardScreen(
        steps=steps,
        title="typedef Setup Wizard",
    )


def create_add_project_wizard() -> WizardScreen:
    """Create the add project wizard screen.

    This is the same as the init wizard but for adding additional projects.
    Each project can have its own Snowflake database/schema configuration.
    """
    steps = [
        ProjectNameStep(),          # Step 1: Project name
        DbtPathStep(),              # Step 2: dbt project path or git URL
        DbtSubProjectStep(),        # Step 3: Select sub-project (if monorepo)
        SnowflakeConnectionStep(),  # Step 4: Snowflake credentials
        DatabaseSelectionStep(),    # Step 5: Select databases
        LlmKeysStep(),              # Step 6: Optional LLM API keys
        IntegrationsStep(),         # Step 7: Optional integrations (Linear, Logfire)
        ProfilesYmlStep(),          # Step 8: Preview profiles.yml (no write yet)
        PreFlightCheckStep(),       # Step 9: Setup & validation (profiles.yml + dbt docs + checks)
        SummaryStep(),              # Step 10: Final summary before completion
    ]

    return WizardScreen(
        steps=steps,
        title="Add New Project",
    )


class InitWizardApp(BaseWizardApp):
    """Full-screen init wizard application."""

    def __init__(self):
        """Initialize the init wizard app."""
        wizard_screen = create_init_wizard()
        super().__init__(wizard_screen)
