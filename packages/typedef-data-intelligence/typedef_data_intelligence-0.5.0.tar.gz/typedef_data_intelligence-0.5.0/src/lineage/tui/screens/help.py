"""Help screen for the TUI application."""

import logging
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Markdown, Static

logger = logging.getLogger(__name__)

# Path to the agent user guide documentation
DOCS_PATH = Path(__file__).parent.parent.parent.parent.parent / "docs" / "reference" / "AGENT_USER_GUIDE.md"

# Fallback content if the file is not found
FALLBACK_HELP = """
# Data Concierge Help

## Getting Started

If you haven't set up yet:

```text
typedef init    # Run setup wizard
typedef sync    # Sync dbt metadata
typedef chat    # Launch this TUI
```

## Agents Quick Reference

| Agent | Best For |
|-------|----------|
| **Analyst** | Business questions, reports, visualizations |
| **Investigator** | Troubleshooting data discrepancies |
| **Insights** | Understanding data architecture |
| **Copilot** | Building/modifying dbt models |

## Choosing an Agent

- **"What was ARR last month?"** → Analyst
- **"Why is ARR wrong?"** → Investigator
- **"How does ARR get calculated?"** → Insights
- **"Add region to the ARR model"** → Copilot

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `F1` / `Ctrl+H` | Show this help |
| `Escape` | Close help / Stop agent |
| `Enter` | Send message |
| `Shift+Enter` | Insert newline |
| `Q` | Quit application |

## Tips

- **Be specific** with your questions for better results
- **Analyst** only works with existing semantic views
- **Copilot** always asks for approval before making changes
- When in doubt, ask **Insights** to explain your data

Press `Escape` or click Close to dismiss this help.
"""


class HelpScreen(ModalScreen[None]):
    """Modal screen displaying help documentation."""

    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
        Binding("q", "close", "Close", show=False),
    ]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    HelpScreen > Container {
        width: 90%;
        height: 90%;
        background: $surface;
        border: tall $primary;
        padding: 1 2;
    }

    HelpScreen #help-header {
        dock: top;
        height: auto;
        padding: 1;
        background: $primary-darken-2;
        text-align: center;
    }

    HelpScreen #help-header Label {
        text-style: bold;
        width: 100%;
        text-align: center;
    }

    HelpScreen #help-content {
        height: 1fr;
        padding: 1;
    }

    HelpScreen #help-footer {
        dock: bottom;
        height: auto;
        padding: 1;
        align: center middle;
    }

    HelpScreen #help-footer Button {
        margin: 0 1;
    }

    HelpScreen .keyboard-hint {
        text-style: dim;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        """Initialize the help screen."""
        super().__init__()
        self._help_content = self._load_help_content()

    def _load_help_content(self) -> str:
        """Load help content from markdown file or use fallback."""
        if DOCS_PATH.exists():
            try:
                return DOCS_PATH.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Error loading help content from {DOCS_PATH}: {e}")
        return FALLBACK_HELP

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container():
            with Static(id="help-header"):
                yield Label("Data Concierge Help")
            with VerticalScroll(id="help-content"):
                yield Markdown(self._help_content)
            with Static(id="help-footer"):
                yield Button("Close", variant="primary", id="close-help")
                yield Label("Press Escape to close", classes="keyboard-hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-help":
            self.dismiss()

    def action_close(self) -> None:
        """Close the help screen."""
        self.dismiss()
