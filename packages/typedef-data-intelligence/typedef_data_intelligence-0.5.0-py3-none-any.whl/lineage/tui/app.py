"""Main TUI Application."""
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Footer,
    Header,
    Label,
    LoadingIndicator,
    Static,
    TabbedContent,
    TabPane,
)

from lineage.ag_ui.client import AGUIClient as AguiClient
from lineage.tui.backend import BackendManager
from lineage.tui.screens.chat import AgentChat
from lineage.tui.screens.daemon import DaemonScreen
from lineage.tui.screens.help import HelpScreen
from lineage.tui.screens.tickets import OpenTicketInChat, TicketsScreen

# Configure logging - use typedef logs dir if available, else fallback
TYPEDEF_LOGS = Path.home() / ".typedef" / "logs"
if TYPEDEF_LOGS.exists():
    LOG_FILE = TYPEDEF_LOGS / "tui-client.log"
else:
    Path("logs").mkdir(exist_ok=True)
    LOG_FILE = Path("logs/tui-client.log")

logging.basicConfig(
    level=logging.INFO,
    filename=str(LOG_FILE),
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Path to shared CSS file
STYLES_PATH = Path(__file__).parent / "styles.tcss"


class StatusBar(Static):
    """Status bar showing connection states."""

    project_name = reactive("default")
    backend_status = reactive("⏳")
    graph_status = reactive("⏳")
    data_status = reactive("⏳")

    def render(self) -> str:
        """Render the status bar."""
        return (
            f"📁 {self.project_name}  │  Backend: {self.backend_status}  │  Graph: {self.graph_status}  │  Data: {self.data_status}"
        )

    def set_connected(self):
        """Set all statuses to connected."""
        self.backend_status = "✅ Ready"
        self.graph_status = "✅ Connected"
        self.data_status = "✅ Connected"

    def set_backend_error(self):
        """Set backend to error state."""
        self.backend_status = "❌ Error"
        self.graph_status = "❌"
        self.data_status = "❌"

    def set_loading(self):
        """Set all to loading."""
        self.backend_status = "⏳ Starting..."
        self.graph_status = "⏳"
        self.data_status = "⏳"


class DataConciergeApp(App):
    """The main TUI application."""

    CSS_PATH = STYLES_PATH
    TITLE = "typedef - Data Concierge"
    SUBTITLE = "The AI-powered data concierge for your organization."
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "cancel_agent", "Stop Agent"),
        ("f1", "help", "Help"),
        ("ctrl+h", "help", "Help"),
    ]

    def __init__(self, daemon_mode: bool = False):
        """Initialize the application.

        Args:
            daemon_mode: If True, auto-start daemon and switch to Tickets tab.
        """
        super().__init__()
        self.backend = BackendManager()
        self.client: Optional[AguiClient] = None
        self.status_bar: Optional[StatusBar] = None
        self.active_project = os.getenv("TYPEDEF_ACTIVE_PROJECT", "default")
        self.daemon_mode = daemon_mode
        self._ticketing_available = self._has_ticketing_backend()

    def _has_ticketing_backend(self) -> bool:
        """Check if any ticketing backend is enabled in the config."""
        from lineage.utils.env import load_env_file

        load_env_file()

        # Check if ticketing is enabled via unified config
        config_path = os.environ.get("UNIFIED_CONFIG")
        if not config_path:
            config_path = str(Path.home() / ".typedef" / "config.yaml")

        if Path(config_path).exists():
            try:
                import yaml

                with open(config_path) as f:
                    config = yaml.safe_load(f) or {}
                ticket_config = config.get("ticket", {})
                return ticket_config.get("enabled", False)
            except Exception as e:
                logger.error(f"Error loading ticketing config: {e}")
                return False

        return False

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        # Show project in header
        yield Header(show_clock=True, name=f"typedef - {self.active_project}")

        with Container(id="loading-screen"):
            yield LoadingIndicator()
            yield Label("Booting Data Concierge backend...", id="loading-label")
            yield Label(f"Logs: {self.backend.log_file}", id="loading-details")

        with TabbedContent(id="main-content", initial="analyst"):
            with TabPane("Analyst", id="analyst"):
                yield Container(id="analyst-container")
            with TabPane("Investigator", id="investigator"):
                yield Container(id="investigator-container")
            with TabPane("Insights", id="insights"):
                yield Container(id="insights-container")
            with TabPane("Copilot", id="copilot"):
                yield Container(id="copilot-container")
            if self._ticketing_available:
                with TabPane("Tickets", id="tickets"):
                    yield Container(id="tickets-container")
                with TabPane("Daemon", id="daemon"):
                    yield Container(id="daemon-container")

        # Bottom bars: status + keyboard shortcuts footer
        with Vertical(id="bottom-bars"):
            self.status_bar = StatusBar(id="status-bar")
            self.status_bar.set_loading()
            self.status_bar.project_name = self.active_project
            yield self.status_bar
            yield Footer()

    async def on_mount(self):
        """Start backend and wait for health."""
        self.query_one("#main-content").display = False

        self.backend.start()

        is_healthy = await self.backend.wait_for_health()
        if not is_healthy:
            self.query_one("#loading-label").update("Failed to start backend server!")
            self.query_one("#loading-details").update(f"Check logs at: {self.backend.log_file.absolute()}")
            if self.status_bar:
                self.status_bar.set_backend_error()
            return

        self.client = AguiClient(self.backend.base_url)

        # Mount agent chats
        await self.query_one("#analyst-container").mount(AgentChat("analyst", self.client))
        await self.query_one("#investigator-container").mount(AgentChat("investigator", self.client))
        await self.query_one("#insights-container").mount(AgentChat("insights", self.client))
        await self.query_one("#copilot-container").mount(AgentChat("copilot", self.client))
        if self._ticketing_available:
            await self.query_one("#tickets-container").mount(TicketsScreen(self.client))
            await self.query_one("#daemon-container").mount(DaemonScreen(self.client))

        self.query_one("#loading-screen").display = False
        self.query_one("#main-content").display = True

        # Update status bar
        if self.status_bar:
            self.status_bar.set_connected()

        # If daemon mode and ticketing is available, switch to daemon tab and auto-start
        if self.daemon_mode and self._ticketing_available:
            tabbed = self.query_one("#main-content", TabbedContent)
            tabbed.active = "daemon"
            # Auto-start daemon after a brief delay to ensure mounting is complete
            self.set_timer(0.5, self._schedule_auto_start_daemon)

    async def on_unmount(self):
        """Cleanup."""
        if self.client:
            await self.client.close()
        self.backend.stop()

    async def action_cancel_agent(self) -> None:
        """Cancel the currently running agent in the active tab."""
        # Find the active tab's AgentChat
        try:
            tabbed_content = self.query_one("#main-content", TabbedContent)
            active_tab_id = tabbed_content.active
            if active_tab_id:
                container = self.query_one(f"#{active_tab_id}-container", Container)
                for child in container.children:
                    if isinstance(child, AgentChat):
                        if child.is_agent_running():
                            await child.cancel_agent_run()
                            self.notify("Agent run cancelled", severity="warning")
                        return
        except Exception as e:
            logger.debug(f"Error cancelling agent: {e}")

    def action_help(self) -> None:
        """Show the help screen."""
        self.push_screen(HelpScreen())

    def _schedule_auto_start_daemon(self) -> None:
        """Schedule the async daemon auto-start (synchronous wrapper for set_timer)."""
        asyncio.create_task(self._auto_start_daemon())

    async def _auto_start_daemon(self) -> None:
        """Auto-start the daemon in autonomous mode."""
        try:
            daemon_container = self.query_one("#daemon-container", Container)
            for child in daemon_container.children:
                if isinstance(child, DaemonScreen):
                    await child.start_daemon()
                    self.notify("Daemon started in autonomous mode", severity="information")
                    break
        except Exception as e:
            logger.error(f"Failed to auto-start daemon: {e}")

    def on_open_ticket_in_chat(self, message: OpenTicketInChat) -> None:
        """Handle request to open a ticket in chat."""
        ticket = message.ticket
        agent_type = message.agent_type

        # Map agent type to tab ID
        tab_map = {
            "copilot": "copilot",
            "investigator": "investigator",
        }
        tab_id = tab_map.get(agent_type, "copilot")

        # Switch to the appropriate tab
        tabbed = self.query_one("#main-content", TabbedContent)
        tabbed.active = tab_id

        # Pre-fill the chat input with ticket context
        try:
            container = self.query_one(f"#{tab_id}-container", Container)
            for child in container.children:
                if isinstance(child, AgentChat):
                    # Build ticket context prompt
                    prompt = (
                        f"I'd like to work on ticket {ticket.id}:\n\n"
                        f"**Title**: {ticket.title}\n"
                        f"**Status**: {ticket.status}\n"
                        f"**Priority**: {ticket.priority}\n"
                    )
                    if ticket.tags:
                        prompt += f"**Tags**: {', '.join(ticket.tags)}\n"
                    prompt += "\nPlease help me understand and work on this ticket."

                    # Set the input value
                    child.set_input_value(prompt)
                    child.focus_input()
                    break
        except Exception as e:
            logger.error(f"Failed to open ticket in chat: {e}")
            self.notify(f"Error: {e}", severity="error")


def main():
    """Run the TUI application."""
    import sys

    import yaml

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Data Concierge TUI")
        print("Usage: lineage-tui")
        print("\nRuns the Data Concierge TUI with a local backend server.")
        return

    # Load typedef config if not already configured via typedef chat
    # This ensures GIT_WORKING_DIR is set correctly when running lineage-tui directly
    typedef_config = Path.home() / ".typedef" / "config.yaml"
    if typedef_config.exists() and "GIT_WORKING_DIR" not in os.environ:
        try:
            with open(typedef_config) as f:
                config = yaml.safe_load(f)

            # Get active project (from env or default)
            active_project = os.environ.get("TYPEDEF_ACTIVE_PROJECT")
            if not active_project:
                active_project = config.get("default_project")
                if active_project:
                    os.environ["TYPEDEF_ACTIVE_PROJECT"] = active_project

            # Get dbt_path from project config
            projects = config.get("projects", {})
            if active_project and active_project in projects:
                project_config = projects[active_project]
                dbt_path = project_config.get("dbt_path")
                if dbt_path:
                    os.environ["GIT_WORKING_DIR"] = str(Path(dbt_path).expanduser().resolve())
                    logger.info(f"Set GIT_WORKING_DIR={os.environ['GIT_WORKING_DIR']}")

            # Set UNIFIED_CONFIG if not set
            if "UNIFIED_CONFIG" not in os.environ:
                os.environ["UNIFIED_CONFIG"] = str(typedef_config)

        except Exception as e:
            logger.warning(f"Failed to load typedef config: {e}")

    # Check for daemon mode
    daemon_mode = os.environ.get("TYPEDEF_DAEMON_MODE") == "1"

    app = DataConciergeApp(daemon_mode=daemon_mode)
    app.run()

if __name__ == "__main__":
    main()
