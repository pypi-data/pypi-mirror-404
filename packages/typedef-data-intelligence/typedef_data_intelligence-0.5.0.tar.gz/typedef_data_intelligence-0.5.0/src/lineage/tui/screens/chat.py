"""Chat screen components."""
import asyncio
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ValidationError
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.css.query import NoMatches
from textual.message import Message as TextualMessage
from textual.widgets import Button, Label, Markdown, Static, TextArea

from lineage.ag_ui.client import AGUIClient as AguiClient
from lineage.ag_ui.client import AGUIRequestError
from lineage.agent.pydantic.types import (
    AddTicketCommentResult,
    BashResult,
    ChartCellResult,
    CreateReportResult,
    CreateTicketResult,
    DbtResult,
    DownstreamImpactResult,
    ExecuteQueryResult,
    GetTicketResult,
    GraphSearchResult,
    JoinPatternsResult,
    ListTicketsResult,
    MarkdownCellResult,
    MermaidCellResult,
    PreviewTableResult,
    QueryGraphResult,
    SearchModelsResult,
    TableCellResult,
    UpdateTicketResult,
)
from lineage.backends.lineage.protocol import (
    ModelDetailsResult,
    ModelMaterializationsResult,
    RelationLineageResult,
)
from lineage.tui.screens.placeholders import AGENT_PLACEHOLDERS
from lineage.tui.widgets.artifacts import (
    ArtifactViewer,
    ExportReportRequest,
    TOOL_DISPLAY_INFO,
    _convert_mermaid_to_ascii,
)

logger = logging.getLogger(__name__)

# Debounce interval for markdown updates (seconds)
MARKDOWN_UPDATE_INTERVAL = 0.2

# Export directory for markdown files
EXPORT_DIR = Path.home() / ".typedef" / "exports"

# Autoscroll bottom detection threshold (pixels)
AUTOSCROLL_BOTTOM_THRESHOLD_PX = 10


@dataclass
class ToolCallRecord:
    """Record of a single tool call during an agent run."""

    tool_call_id: str
    tool_name: str
    display_text: str
    start_time: datetime
    end_time: Optional[datetime] = None
    artifact_id: Optional[str] = None  # Link to generated artifact

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get duration in seconds if completed."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class RunStats:
    """Statistics for a single agent run (user prompt → response)."""

    run_id: str
    agent_name: str
    start_time: datetime
    user_message: str
    end_time: Optional[datetime] = None
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    response_char_count: int = 0

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get total run duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def tool_call_count(self) -> int:
        """Get number of tool calls."""
        return len(self.tool_calls)


class ChatContentFlushed(TextualMessage):
    """Event emitted when streaming content flushes to the UI."""

    def __init__(self) -> None:
        """Initialize the flush event."""
        super().__init__()


class SamplePromptClicked(TextualMessage):
    """Event emitted when a sample prompt is clicked."""

    def __init__(self, prompt: str) -> None:
        """Initialize with the prompt text."""
        super().__init__()
        self.prompt = prompt


class AgentPlaceholder(Container):
    """Placeholder widget shown when chat is empty, with agent intro and sample prompts."""

    def __init__(self, agent_name: str) -> None:
        """Initialize the placeholder for a specific agent."""
        super().__init__()
        self.agent_name = agent_name
        self._content = AGENT_PLACEHOLDERS.get(agent_name, {
            "title": agent_name.title(),
            "intro": "Ask me anything about your data.",
            "prompts": [],
        })

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Decorative header with title
        yield Static("~ ~ ~", classes="placeholder-decoration")
        yield Label(self._content["title"], classes="placeholder-title")
        yield Static("~ ~ ~", classes="placeholder-decoration")

        # Intro text
        yield Label(self._content["intro"], classes="placeholder-intro")

        # Sample prompts section
        prompts = self._content.get("prompts", [])
        if prompts:
            yield Static("", classes="placeholder-spacer")
            yield Label("Try asking:", classes="placeholder-section-header")
            with Container(classes="sample-prompts"):
                for i, prompt in enumerate(prompts):
                    btn = Button(
                        f'"{prompt}"',
                        id=f"sample-prompt-{i}",
                        classes="sample-prompt-btn",
                    )
                    btn.tooltip = "Click to use this prompt"
                    yield btn

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle sample prompt button clicks."""
        if event.button.id and event.button.id.startswith("sample-prompt-"):
            try:
                idx = int(event.button.id.replace("sample-prompt-", ""))
                prompts = self._content.get("prompts", [])
                if 0 <= idx < len(prompts):
                    self.post_message(SamplePromptClicked(prompts[idx]))
            except ValueError:
                logger.debug(
                    "Invalid sample prompt button id '%s'",
                    event.button.id,
                    exc_info=True,
                )
            event.stop()


def _process_mermaid_in_content(content: str) -> str:
    """Process content to convert mermaid blocks to ASCII for terminal display."""
    def replace_mermaid(match: re.Match) -> str:
        mermaid_code = match.group(1).strip()
        ascii_art = _convert_mermaid_to_ascii(mermaid_code)
        if ascii_art != mermaid_code:
            # We got a useful conversion, show ASCII art and original
            return (
                f"**Diagram:**\n```\n{ascii_art}\n```\n\n"
                f"*Mermaid source (copy to mermaid.live):*\n```\n{mermaid_code}\n```"
            )
        else:
            # No conversion available, just show as code block
            return f"```\n{mermaid_code}\n```"

    pattern = r"```mermaid\s*([\s\S]*?)```"
    return re.sub(pattern, replace_mermaid, content)


def _format_tool_display(tool_name: str, args: Dict[str, Any]) -> str:
    """Format a tool call for friendly display in the chat."""
    info = TOOL_DISPLAY_INFO.get(tool_name, {"verb": f"Using {tool_name}", "icon": "🔨"})

    # Handle ticket-specific formatting
    if tool_name == "create_ticket":
        title = args.get("title", "")
        priority = args.get("priority", "")
        if title:
            priority_str = f" [{priority}]" if priority else ""
            return f"{info['icon']} {info['verb']}{priority_str}: \"{title}\""
        return f"{info['icon']} {info['verb']}..."

    if tool_name == "get_ticket":
        ticket_id = args.get("ticket_id", "")
        if ticket_id:
            return f"{info['icon']} {info['verb']}: {ticket_id}"
        return f"{info['icon']} {info['verb']}..."

    if tool_name == "list_tickets":
        filters = []
        if args.get("status"):
            filters.append(f"status={args['status']}")
        if args.get("assigned_to"):
            filters.append(f"assigned={args['assigned_to']}")
        if args.get("priority"):
            filters.append(f"priority={args['priority']}")
        if filters:
            return f"{info['icon']} {info['verb']} ({', '.join(filters)})"
        return f"{info['icon']} {info['verb']}..."

    if tool_name == "update_ticket":
        ticket_id = args.get("ticket_id", "")
        updates = []
        if args.get("status"):
            updates.append(f"status→{args['status']}")
        if args.get("assigned_to"):
            updates.append(f"assign→{args['assigned_to']}")
        if args.get("priority"):
            updates.append(f"priority→{args['priority']}")
        if ticket_id and updates:
            return f"{info['icon']} {info['verb']} {ticket_id}: {', '.join(updates)}"
        elif ticket_id:
            return f"{info['icon']} {info['verb']}: {ticket_id}"
        return f"{info['icon']} {info['verb']}..."

    if tool_name == "add_ticket_comment":
        ticket_id = args.get("ticket_id", "")
        comment = args.get("comment", args.get("content", ""))
        if ticket_id:
            # Truncate comment preview
            preview = comment[:40] + "..." if len(comment) > 40 else comment
            if preview:
                return f"{info['icon']} {info['verb']} to {ticket_id}: \"{preview}\""
            return f"{info['icon']} {info['verb']} to {ticket_id}"
        return f"{info['icon']} {info['verb']}..."

    # Default: Extract human-readable description if available
    description = (
        args.get("query_description")
        or args.get("query_name")
        or args.get("title")
        or ""
    )

    if description:
        return f"{info['icon']} {info['verb']}: \"{description}\""
    else:
        return f"{info['icon']} {info['verb']}..."


class Message(Static):
    """A chat message widget with debounced markdown updates."""

    def __init__(
        self,
        role: str,
        content: str,
        tool_call_id: Optional[str] = None,
        has_artifact: bool = False,
        **kwargs,
    ):
        """Initialize the message widget."""
        super().__init__(**kwargs)
        self.role = role
        self.content_text = content
        self.tool_call_id = tool_call_id  # For tool messages, links to artifact
        self.has_artifact = has_artifact  # Whether tool produced viewable artifact
        self._pending_update = False
        self._update_timer = None
        self._finalized = False
        # Process mermaid blocks for display
        display_content = _process_mermaid_in_content(content)
        self.markdown = Markdown(display_content)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Label(f"[{self.role}]", classes=f"role-label {self.role}")
        yield self.markdown
        # Add action buttons for assistant messages (shown after finalize)
        if self.role == "assistant":
            with Horizontal(classes="message-actions"):
                yield Button("📋 Copy", id="msg-copy-btn", variant="default")
                yield Button("💾 Export", id="msg-export-btn", variant="default")
        # Add view button for tool messages with artifacts
        elif self.role == "tool" and self.tool_call_id and self.has_artifact:
            with Horizontal(classes="message-actions"):
                yield Button(
                    "🔍 View Result",
                    id=f"view-artifact-{self.tool_call_id}",
                    variant="default",
                )

    def on_mount(self) -> None:
        """Hide action buttons until message is finalized."""
        if self.role == "assistant":
            try:
                actions = self.query_one(".message-actions")
                actions.display = False
            except NoMatches:
                pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for copy/export/view."""
        button_id = event.button.id
        if button_id == "msg-copy-btn":
            await self._copy_to_clipboard()
            event.stop()
        elif button_id == "msg-export-btn":
            await self._export_to_markdown()
            event.stop()
        elif button_id and button_id.startswith("view-artifact-"):
            # Bubble up to AgentChat to handle artifact navigation
            pass  # Event will bubble up

    async def _copy_to_clipboard(self) -> None:
        """Copy message content to clipboard."""
        try:
            self.app.copy_to_clipboard(self.content_text)
            self.app.notify("Copied to clipboard", title="✓")
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            self.app.notify(f"Copy failed: {e}", severity="error")

    async def _export_to_markdown(self) -> None:
        """Export message content to a markdown file."""
        try:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.md"
            filepath = EXPORT_DIR / filename
            filepath.write_text(self.content_text, encoding="utf-8")
            self.app.notify(f"Exported to {filepath}", title="💾 Saved")
        except Exception as e:
            logger.error(f"Failed to export: {e}")
            self.app.notify(f"Export failed: {e}", severity="error")

    def update_content(self, new_content: str):
        """Update the message content immediately."""
        self.content_text = new_content
        display_content = _process_mermaid_in_content(new_content)
        self.markdown.update(display_content)

    def append_content(self, chunk: str):
        """Append content to the message (debounced for performance)."""
        self.content_text += chunk
        self._pending_update = True
        # Schedule update if not already scheduled
        if self._update_timer is None:
            self._update_timer = self.set_timer(
                MARKDOWN_UPDATE_INTERVAL, self._flush_update
            )

    def _flush_update(self):
        """Flush pending markdown update."""
        self._update_timer = None
        if self._pending_update:
            display_content = _process_mermaid_in_content(self.content_text)
            self.markdown.update(display_content)
            self._pending_update = False
            if self.role == "assistant":
                self.post_message(ChatContentFlushed())

    def finalize(self):
        """Force final update when streaming completes."""
        if self._update_timer is not None:
            self._update_timer.stop()
            self._update_timer = None
        if self._pending_update:
            display_content = _process_mermaid_in_content(self.content_text)
            self.markdown.update(display_content)
            self._pending_update = False
        # Show action buttons for assistant messages
        self._finalized = True
        if self.role == "assistant":
            self.post_message(ChatContentFlushed())
        if self.role == "assistant":
            try:
                actions = self.query_one(".message-actions")
                actions.display = True
            except NoMatches:
                pass


# Spinner frames for animated progress
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
SPINNER_INTERVAL = 0.25  # seconds between frames
MAX_ERROR_MESSAGE_LENGTH = 300


class ToolMessage(Static):
    """Widget for tool calls with live spinner and timing."""

    def __init__(
        self,
        tool_name: str,
        display_text: str,
        tool_call_id: str,
        **kwargs,
    ):
        """Initialize the tool message widget."""
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.display_text = display_text
        self.tool_call_id = tool_call_id
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.result_summary: Optional[str] = None
        self._spinner_index = 0
        self._spinner_timer = None
        self._is_running = True

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Label("", id="tool-status", classes="tool-status")
        with Horizontal(classes="message-actions"):
            yield Button(
                "🔍 View Result",
                id=f"view-artifact-{self.tool_call_id}",
                variant="default",
            )

    def on_mount(self) -> None:
        """Start the spinner animation."""
        self._update_display()
        self._spinner_timer = self.set_interval(SPINNER_INTERVAL, self._advance_spinner)
        # Hide view button until complete
        try:
            actions = self.query_one(".message-actions")
            actions.display = False
        except NoMatches:
            pass

    def _advance_spinner(self) -> None:
        """Advance the spinner animation frame."""
        if not self._is_running:
            return
        self._spinner_index = (self._spinner_index + 1) % len(SPINNER_FRAMES)
        self._update_display()

    def _update_display(self) -> None:
        """Update the status label with current state."""
        try:
            label = self.query_one("#tool-status", Label)
        except NoMatches:
            return

        elapsed = (datetime.now() - self.start_time).total_seconds()

        if self._is_running:
            spinner = SPINNER_FRAMES[self._spinner_index]
            label.update(f"{spinner} {self.display_text} ({int(elapsed)}s)")
        else:
            duration = (
                (self.end_time - self.start_time).total_seconds()
                if self.end_time
                else elapsed
            )
            result_text = f" → {self.result_summary}" if self.result_summary else ""
            label.update(f"✓ {self.display_text} ({duration:.1f}s){result_text}")

    def complete(self, result_summary: Optional[str] = None, has_artifact: bool = False) -> None:
        """Mark the tool call as complete.

        Args:
            result_summary: Summary text to display
            has_artifact: Whether this tool produced a viewable artifact
        """
        self._is_running = False
        self.end_time = datetime.now()
        self.result_summary = result_summary

        # Stop spinner
        if self._spinner_timer:
            self._spinner_timer.stop()
            self._spinner_timer = None

        self._update_display()

        # Only show view button if there's an artifact to view
        if has_artifact:
            try:
                actions = self.query_one(".message-actions")
                actions.display = True
            except NoMatches:
                pass


class ThinkingBlock(Static):
    """Collapsible widget to display thinking process."""

    def __init__(self, content: str):
        """Initialize the thinking block."""
        super().__init__(classes="thinking-block")
        self.content_text = content
        self._pending_update = False
        self._update_timer = None
        self._expanded = False
        self._finalized = False
        self.header = Label("▶ Thinking...", id="thinking-header", classes="thinking-header")
        self.markdown = Markdown(content, id="thinking-content", classes="thinking-content")

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield self.header
        yield self.markdown

    def on_mount(self) -> None:
        """Collapse by default."""
        self.markdown.display = False

    def on_click(self) -> None:
        """Toggle expansion on click."""
        self._toggle_expanded()

    def _toggle_expanded(self) -> None:
        """Toggle the expanded state."""
        self._expanded = not self._expanded
        self.markdown.display = self._expanded
        self._update_header()

    def _update_header(self) -> None:
        """Update the header to show current state."""
        arrow = "▼" if self._expanded else "▶"
        if self._finalized:
            # Show word count when finalized
            word_count = len(self.content_text.split())
            self.header.update(f"{arrow} Thinking ({word_count} words)")
        else:
            self.header.update(f"{arrow} Thinking...")

    def update_content(self, new_content: str):
        """Update the thinking content immediately."""
        self.content_text = new_content
        self.markdown.update(new_content)

    def append_content(self, chunk: str):
        """Append content to the thinking block (debounced for performance)."""
        self.content_text += chunk
        self._pending_update = True
        # Schedule update if not already scheduled
        if self._update_timer is None:
            self._update_timer = self.set_timer(
                MARKDOWN_UPDATE_INTERVAL, self._flush_update
            )

    def _flush_update(self):
        """Flush pending markdown update."""
        self._update_timer = None
        if self._pending_update:
            self.markdown.update(self.content_text)
            self._pending_update = False

    def finalize(self):
        """Force final update when streaming completes."""
        if self._update_timer is not None:
            self._update_timer.stop()
            self._update_timer = None
        if self._pending_update:
            self.markdown.update(self.content_text)
            self._pending_update = False
        self._finalized = True
        self._update_header()


class ErrorPrompt(Static):
    """Widget for displaying errors with retry/restart actions."""

    def __init__(self, message: str, **kwargs):
        """Initialize the error prompt."""
        super().__init__(**kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Markdown(self.message, classes="error-message")
        with Horizontal(classes="message-actions"):
            yield Button("🔁 Retry", id="retry-last-run", variant="primary")
            yield Button("🧹 Restart Chat", id="restart-chat", variant="default")


class ChatInput(TextArea):
    """Multiline chat input that submits on Enter, Shift+Enter for newline."""

    BINDINGS = [
        ("ctrl+enter", "submit", "Send"),
    ]

    MIN_HEIGHT = 3
    MAX_HEIGHT = 12

    def __init__(self, **kwargs):
        """Initialize text area with dynamic height behavior."""
        super().__init__(**kwargs)
        # Start with minimal height
        self.styles.height = self.MIN_HEIGHT

    def on_key(self, event) -> None:
        """Handle Enter to submit, Shift+Enter for newline."""
        # Shift+Enter inserts newline explicitly
        if event.key == "shift+enter":
            event.prevent_default()
            event.stop()
            self.insert("\n")
            return
        # Plain Enter submits
        if event.key == "enter":
            event.prevent_default()
            event.stop()
            self.action_submit()

    def on_text_area_changed(self, event) -> None:
        """Auto-expand height based on content."""
        self._adjust_height()

    def _adjust_height(self) -> None:
        """Adjust height based on number of lines."""
        line_count = self.text.count("\n") + 1
        # Add 2 for padding/border
        new_height = min(max(line_count + 2, self.MIN_HEIGHT), self.MAX_HEIGHT)
        self.styles.height = new_height

    def action_submit(self) -> None:
        """Submit the input text."""
        self.post_message(ChatInput.Submitted(self.text))

    class Submitted(TextualMessage):
        """Event posted when user submits the input."""

        def __init__(self, value: str):
            """Initialize submitted message with input value."""
            super().__init__()
            self.value = value


class ChatArea(Container):
    """Container for chat history and input."""

    def __init__(self, agent_chat: "AgentChat"):
        """Initialize the chat area."""
        super().__init__(classes="chat-area")
        self.agent_chat = agent_chat
        self.chat_log = VerticalScroll(classes="chat-log")
        self.input = ChatInput(classes="chat-input")
        self.input.styles.height = 3
        # Track autoscroll state - toggled via button
        self.autoscroll_enabled = True
        # Track placeholder for removal
        self._placeholder: Optional[AgentPlaceholder] = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield self.chat_log
        with Horizontal(classes="input-row"):
            yield self.input
            autoscroll_button = Button(
                "↓", id="autoscroll-btn", variant="default", classes="autoscroll-on"
            )
            autoscroll_button.tooltip = "Autoscroll on (click to pause)"
            yield autoscroll_button
            yield Button("Send", id="send-btn", variant="primary")

    def on_mount(self) -> None:
        """Mount the placeholder after chat_log is in the DOM."""
        self._placeholder = AgentPlaceholder(self.agent_chat.agent_name)
        self.chat_log.mount(self._placeholder)

    def remove_placeholder(self) -> None:
        """Remove the placeholder widget if present."""
        if self._placeholder is not None:
            self._placeholder.remove()
            self._placeholder = None

    def restore_placeholder(self) -> None:
        """Restore the placeholder widget if it was removed."""
        if self._placeholder is None:
            self._placeholder = AgentPlaceholder(self.agent_chat.agent_name)
            self.chat_log.mount(self._placeholder)

    def reset_placeholder(self) -> None:
        """Reset the placeholder reference (e.g., after remove_children)."""
        self._placeholder = None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle autoscroll toggle button."""
        if event.button.id == "autoscroll-btn":
            self.autoscroll_enabled = not self.autoscroll_enabled
            self._update_autoscroll_button()
            state = "enabled" if self.autoscroll_enabled else "disabled"
            self.app.notify(f"Autoscroll {state}", timeout=1)
            event.stop()

    def _update_autoscroll_button(self) -> None:
        """Update autoscroll button appearance based on state."""
        try:
            btn = self.query_one("#autoscroll-btn", Button)
            if self.autoscroll_enabled:
                btn.label = "↓"
                btn.tooltip = "Autoscroll on (click to pause)"
                btn.remove_class("autoscroll-off")
                btn.add_class("autoscroll-on")
            else:
                btn.label = "⏸"
                btn.tooltip = "Autoscroll off (click to resume)"
                btn.remove_class("autoscroll-on")
                btn.add_class("autoscroll-off")
        except NoMatches:
            # Button may not exist yet or was removed; safe to ignore.
            pass

    @property
    def value(self) -> str:
        """Get the input value (compatibility with Input widget)."""
        return self.input.text

    @value.setter
    def value(self, val: str) -> None:
        """Set the input value (compatibility with Input widget)."""
        self.input.text = val


class AgentChat(Container):
    """Chat interface for a specific agent with artifact viewing."""

    def __init__(self, agent_name: str, client: AguiClient):
        """Initialize the agent chat."""
        super().__init__()
        self.agent_name = agent_name
        self.client = client
        self.thread_id = f"tui-{uuid.uuid4().hex[:8]}"

        self.chat_area = ChatArea(self)
        self.artifact_viewer = ArtifactViewer()
        # Initially hide artifact viewer
        self.artifact_viewer.display = False

        self.current_response: Optional[Message] = None
        self.thinking_widget: Optional[ThinkingBlock] = None

        # Track active tool widgets to update them instead of duplicating
        self.active_tool_widgets: dict[str, Message] = {}

        # Track full message history for context
        self.messages: list[dict] = []
        self.current_response_text: str = ""

        # Run stats tracking
        self.current_run_stats: Optional[RunStats] = None
        self.tool_call_to_artifact: Dict[str, str] = {}  # tool_call_id -> artifact_id
        self.active_tool_records: Dict[str, ToolCallRecord] = {}  # tool_call_id -> record

        # Report cell tracking - accumulate cells for cellular report viewer
        self.active_report_id: Optional[str] = None
        self.active_report_title: Optional[str] = None
        self.active_report_cells: List[Dict] = []
        self.active_report_artifact_id: Optional[str] = None  # Track artifact to update

        # Task reference for cancellation support
        self._current_task: Optional[asyncio.Task] = None
        self.last_user_message: Optional[str] = None
        # Debounced autoscroll request flag (prevents redundant scroll_end calls per refresh)
        self._autoscroll_pending: bool = False

    def _request_autoscroll(self) -> None:
        """Request a scroll-to-bottom after the next refresh (debounced).

        Textual can render artifacts/overdraw when we mount/update many widgets inside a
        scrollable and immediately call scroll_end(). Scheduling after refresh reduces
        layout churn and keeps scrolling stable.
        """
        if not self.chat_area.autoscroll_enabled:
            return
        if self._autoscroll_pending:
            return
        self._autoscroll_pending = True
        # Textual 6.x supports call_after_refresh; keep a fallback just in case.
        try:
            self.call_after_refresh(self._perform_autoscroll)
        except Exception:
            self.call_later(self._perform_autoscroll)

    def _perform_autoscroll(self) -> None:
        """Perform the actual scroll-to-bottom (if still enabled)."""
        self._autoscroll_pending = False
        if self.chat_area.autoscroll_enabled:
            self.chat_area.chat_log.scroll_end(animate=False)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Horizontal():
            yield self.chat_area
            yield self.artifact_viewer

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses, including 'View Result' and 'Send' buttons."""
        button_id = event.button.id
        if button_id == "send-btn":
            await self._submit_message()
            event.stop()
        elif button_id == "retry-last-run":
            await self._retry_last_run()
            event.stop()
        elif button_id == "restart-chat":
            self._restart_chat()
            event.stop()
        elif button_id and button_id.startswith("view-artifact-"):
            # Extract tool_call_id from button ID
            tool_call_id = button_id.replace("view-artifact-", "")
            artifact_id = self.tool_call_to_artifact.get(tool_call_id)
            if artifact_id:
                self.artifact_viewer.display = True
                self.artifact_viewer.select_artifact_by_id(artifact_id)
            event.stop()

    def on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        """Handle ChatInput submission (Ctrl+Enter)."""
        asyncio.create_task(self._submit_message())

    def on_chat_content_flushed(self, event: ChatContentFlushed) -> None:
        """Autoscroll after streaming content flushes."""
        self._request_autoscroll()

    def on_sample_prompt_clicked(self, event: SamplePromptClicked) -> None:
        """Handle sample prompt button click - insert prompt into input."""
        self.chat_area.input.text = event.prompt
        self.chat_area.input.focus()

    async def cancel_agent_run(self) -> bool:
        """Cancel the currently running agent task.

        Returns:
            True if a task was cancelled, False if no task was running.
        """
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass
            return True
        return False

    def is_agent_running(self) -> bool:
        """Check if an agent task is currently running."""
        return self._current_task is not None and not self._current_task.done()

    def set_input_value(self, value: str) -> None:
        """Set the chat input value programmatically."""
        self.chat_area.input.text = value

    def focus_input(self) -> None:
        """Focus the chat input."""
        self.chat_area.input.focus()

    async def on_export_report_request(self, event: ExportReportRequest) -> None:
        """Handle Export HTML button click from report viewer."""
        report_id = event.report_id
        artifact_id = event.artifact_id

        if not self.active_report_cells:
            self.app.notify("No report content to export", severity="warning")
            return

        try:
            # Sort cells by tool call start time to ensure correct order
            sorted_cells = sorted(self.active_report_cells, key=lambda c: c.get("_order", 0))
            # Generate HTML locally
            html_path = self._export_report_to_html(
                report_id=report_id,
                title=self.active_report_title or "Report",
                cells=sorted_cells,
            )

            # Update the artifact with the HTML path
            self.artifact_viewer.update_report_html_path(artifact_id, str(html_path))
            self.app.notify(f"Exported to {html_path.name}", title="Exported")

        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            self.app.notify(f"Export failed: {e}", severity="error")

    def _export_report_to_html(self, report_id: str, title: str, cells: List[Dict]) -> Path:
        """Generate HTML file from report cells.

        Args:
            report_id: Report identifier
            title: Report title
            cells: List of cell dicts with 'type' and 'data' keys

        Returns:
            Path to the generated HTML file
        """
        import json as json_module

        # Create export directory
        export_dir = Path.home() / ".typedef" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = export_dir / f"report_{report_id}_{timestamp}.html"

        cells_json = json_module.dumps(cells, indent=2)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked@11.1.1/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
    <style>
        :root {{
            --bg-primary: #111111;
            --bg-card: rgba(17, 17, 17, 0.8);
            --border-light: rgba(130, 157, 243, 0.3);
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --analyst-color: #829df3;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .report-container {{ max-width: 1200px; margin: 0 auto; }}
        .report-header {{
            margin-bottom: 40px;
            border-bottom: 1px solid var(--border-light);
            padding-bottom: 20px;
        }}
        .report-title {{ font-size: 32px; font-weight: 600; margin: 0 0 10px 0; }}
        .report-meta {{ color: var(--text-secondary); font-size: 14px; }}
        .cell {{
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .cell-markdown h1, .cell-markdown h2, .cell-markdown h3 {{ color: var(--analyst-color); margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1em 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid var(--border-light); }}
        th {{ color: var(--analyst-color); font-weight: 600; }}
        canvas {{ max-width: 100%; height: auto !important; }}
        pre {{ background: rgba(0,0,0,0.3); padding: 16px; border-radius: 8px; overflow-x: auto; }}
        code {{ font-family: 'SF Mono', Monaco, monospace; }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1 class="report-title">{title}</h1>
            <p class="report-meta">Generated from typedef Data Intelligence TUI</p>
        </div>
        <div id="cells"></div>
    </div>
    <script>
        const cells = {cells_json};
        mermaid.initialize({{ startOnLoad: false, theme: 'dark' }});

        function renderCells() {{
            const container = document.getElementById('cells');
            cells.forEach((cell, idx) => {{
                const div = document.createElement('div');
                div.className = 'cell cell-' + cell.type;

                if (cell.type === 'markdown') {{
                    div.innerHTML = marked.parse(cell.data.content || '');
                }} else if (cell.type === 'table') {{
                    let html = cell.data.title ? '<h3>' + cell.data.title + '</h3>' : '';
                    html += '<table><thead><tr>';
                    (cell.data.columns || []).forEach(col => html += '<th>' + col + '</th>');
                    html += '</tr></thead><tbody>';
                    (cell.data.rows || []).forEach(row => {{
                        html += '<tr>';
                        if (Array.isArray(row)) {{
                            row.forEach(val => html += '<td>' + (val ?? '') + '</td>');
                        }} else {{
                            (cell.data.columns || []).forEach(col => html += '<td>' + (row[col] ?? '') + '</td>');
                        }}
                        html += '</tr>';
                    }});
                    html += '</tbody></table>';
                    div.innerHTML = html;
                }} else if (cell.type === 'chart') {{
                    const title = cell.data.title || 'Chart';
                    const chartType = cell.data.chart_type || 'line';
                    const data = cell.data.data || [];
                    const xCol = cell.data.x_column;
                    const yCol = cell.data.y_column;

                    div.innerHTML = '<h3>' + title + '</h3><canvas id="chart-' + idx + '"></canvas>';
                    container.appendChild(div);

                    setTimeout(() => {{
                        const ctx = document.getElementById('chart-' + idx);
                        if (ctx && data.length && xCol && yCol) {{
                            new Chart(ctx, {{
                                type: chartType === 'area' ? 'line' : chartType,
                                data: {{
                                    labels: data.map(r => r[xCol]),
                                    datasets: [{{
                                        label: yCol,
                                        data: data.map(r => r[yCol]),
                                        borderColor: '#829df3',
                                        backgroundColor: chartType === 'area' ? 'rgba(130, 157, 243, 0.3)' : '#829df3',
                                        fill: chartType === 'area'
                                    }}]
                                }},
                                options: {{ responsive: true, plugins: {{ legend: {{ labels: {{ color: '#fff' }} }} }} }}
                            }});
                        }}
                    }}, 100);
                    return;
                }} else if (cell.type === 'mermaid') {{
                    const title = cell.data.title || 'Diagram';
                    div.innerHTML = '<h3>' + title + '</h3><pre class="mermaid">' + (cell.data.diagram || '') + '</pre>';
                    container.appendChild(div);
                    return;
                }}
                container.appendChild(div);
            }});
            mermaid.run();
        }}
        renderCells();
    </script>
</body>
</html>"""

        html_path.write_text(html, encoding="utf-8")
        return html_path

    async def _submit_message(self) -> None:
        """Submit the current input message."""
        message = self.chat_area.input.text.strip()
        if not message:
            return

        self.chat_area.input.text = ""
        self.chat_area.input.disabled = True

        # Re-enable autoscroll when user submits a new message
        self.chat_area.autoscroll_enabled = True

        # Add user message to history
        user_msg = {
            "role": "user",
            "content": message,
            "id": str(uuid.uuid4()),
        }
        self.messages.append(user_msg)
        self.last_user_message = message

        # Remove placeholder on first message
        self.chat_area.remove_placeholder()

        # Add user message to UI
        self.chat_area.chat_log.mount(Message("user", message, classes="message user"))
        self._request_autoscroll()

        # Reset state
        self.current_response = None
        self.thinking_widget = None
        self.current_response_text = ""

        # Initialize run stats
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        self.current_run_stats = RunStats(
            run_id=run_id,
            agent_name=self.agent_name,
            start_time=datetime.now(),
            user_message=message,
        )
        self.active_tool_records = {}

        # Stream response (store task for cancellation support)
        self._current_task = asyncio.create_task(self.stream_response(message, run_id))

    async def stream_response(self, message: str, run_id: str):
        """Stream response from the agent."""
        try:
            async for event in self.client.stream_agent(
                self.agent_name, message, self.thread_id, run_id,
                messages=self.messages  # Pass full conversation history
            ):
                event_type = event.get("type")

                if event_type == "TEXT_MESSAGE_START":
                    self.current_response = Message("assistant", "", classes="message assistant")
                    self.chat_area.chat_log.mount(self.current_response)
                    self._request_autoscroll()

                elif event_type == "TEXT_MESSAGE_CONTENT":
                    chunk = event.get("delta", "")
                    self.current_response_text += chunk  # Track full response
                    if self.current_response:
                        self.current_response.append_content(chunk)
                    else:
                        self.current_response = Message("assistant", chunk, classes="message assistant")
                        self.chat_area.chat_log.mount(self.current_response)

                elif event_type == "THINKING_TEXT_MESSAGE_CONTENT":
                    chunk = event.get("delta", "")
                    if not self.thinking_widget:
                        self.thinking_widget = ThinkingBlock(chunk)
                        if self.current_response:
                            self.chat_area.chat_log.mount(self.thinking_widget, before=self.current_response)
                        else:
                            self.chat_area.chat_log.mount(self.thinking_widget)
                        self._request_autoscroll()
                    else:
                        self.thinking_widget.append_content(chunk)

                elif event_type == "TOOL_CALL_START":
                    tool_name = event.get("toolCallName", "Unknown Tool")
                    tool_call_id = event.get("toolCallId", "unknown")
                    tool_args = event.get("toolCallArgs", {})

                    # Parse args if they're a string
                    if isinstance(tool_args, str):
                        try:
                            tool_args = json.loads(tool_args)
                        except json.JSONDecodeError:
                            tool_args = {}

                    # Format friendly display message
                    display_text = _format_tool_display(tool_name, tool_args)

                    # Create tool message with live spinner
                    tool_msg = ToolMessage(
                        tool_name=tool_name,
                        display_text=display_text,
                        tool_call_id=tool_call_id,
                        classes="message tool",
                        id=f"tool-{tool_call_id}",
                    )
                    self.chat_area.chat_log.mount(tool_msg)
                    self.active_tool_widgets[tool_call_id] = tool_msg
                    self._request_autoscroll()

                    # Track tool call for run stats
                    tool_record = ToolCallRecord(
                        tool_call_id=tool_call_id,
                        tool_name=tool_name,
                        display_text=display_text,
                        start_time=datetime.now(),
                    )
                    self.active_tool_records[tool_call_id] = tool_record
                    if self.current_run_stats:
                        self.current_run_stats.tool_calls.append(tool_record)

                elif event_type == "TOOL_CALL_RESULT":
                    tool_call_id = event.get("toolCallId", "unknown")
                    content = event.get("content", "{}")

                    # Update tool record end time
                    if tool_call_id in self.active_tool_records:
                        self.active_tool_records[tool_call_id].end_time = datetime.now()

                    # Handle Artifacts and get artifact_id if created
                    artifact_id = self._handle_artifact(tool_call_id, content)

                    # Link tool call to artifact
                    if artifact_id and tool_call_id in self.active_tool_records:
                        self.active_tool_records[tool_call_id].artifact_id = artifact_id
                        self.tool_call_to_artifact[tool_call_id] = artifact_id

                    # Generate result summary from content
                    result_summary = self._generate_result_summary(content)

                    # Complete tool message with result summary
                    if tool_call_id in self.active_tool_widgets:
                        tool_widget = self.active_tool_widgets[tool_call_id]
                        if isinstance(tool_widget, ToolMessage):
                            tool_widget.complete(result_summary, has_artifact=artifact_id is not None)
                        else:
                            # Fallback for old Message widgets
                            tool_widget.append_content("\n✅ Completed.")
                    else:
                        # Should rarely happen, but fallback
                        self.chat_area.chat_log.mount(
                            Message("tool", "Tool finished", classes="message tool")
                        )

                elif event_type in {"RUN_ERROR", "ERROR"}:
                    error_text = event.get("error") or event.get("message") or "Unknown error"
                    error_message = self._format_error_message(RuntimeError(error_text))
                    self.chat_area.chat_log.mount(
                        ErrorPrompt(error_message, classes="message error")
                    )
                    self._request_autoscroll()
                    # Mark any running tool widgets as failed
                    for tool_widget in self.active_tool_widgets.values():
                        if isinstance(tool_widget, ToolMessage) and tool_widget._is_running:
                            tool_widget.complete(result_summary="failed", has_artifact=False)

        except asyncio.CancelledError:
            logger.info("Agent run cancelled by user")
            # Show cancellation message in chat
            self.chat_area.chat_log.mount(
                Message("system", "⚠ Agent run cancelled", classes="message system")
            )
            # Append truncation marker to response text so agent knows it was interrupted
            if self.current_response_text:
                self.current_response_text += "\n\n[Response interrupted by user]"
            # Don't re-raise - let finally block clean up
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            error_message = self._format_error_message(e)
            self.chat_area.chat_log.mount(
                ErrorPrompt(error_message, classes="message error")
            )
        finally:
            self._current_task = None  # Clear task reference
            # Finalize any pending markdown updates
            if self.current_response:
                self.current_response.finalize()
            if self.thinking_widget:
                self.thinking_widget.finalize()

            # Add assistant response to message history for context
            if self.current_response_text:
                assistant_msg = {
                    "role": "assistant",
                    "content": self.current_response_text,
                    "id": str(uuid.uuid4()),
                }
                self.messages.append(assistant_msg)

            # Finalize run stats and show activity summary
            if self.current_run_stats:
                self.current_run_stats.end_time = datetime.now()
                self.current_run_stats.response_char_count = len(self.current_response_text)
                # Show activity summary in artifact viewer
                self.artifact_viewer.display = True
                self.artifact_viewer.show_activity_summary(self.current_run_stats)

            # Mark active report as ready for export (shows Export button)
            if self.active_report_artifact_id:
                self.artifact_viewer.mark_report_ready(self.active_report_artifact_id)

            self.chat_area.input.disabled = False
            self.chat_area.input.focus()

    async def _retry_last_run(self) -> None:
        """Retry the last user message without duplicating it in history."""
        if self.is_agent_running():
            self.app.notify("An agent run is already in progress.", severity="warning")
            return
        if not self.last_user_message:
            self.app.notify("No previous message to retry.", severity="warning")
            return

        # Remove any stale assistant response from a failed run
        if self.messages and self.messages[-1].get("role") == "assistant":
            self.messages.pop()

        self.current_response = None
        self.thinking_widget = None
        self.current_response_text = ""

        run_id = f"run-{uuid.uuid4().hex[:8]}"
        self.current_run_stats = RunStats(
            run_id=run_id,
            agent_name=self.agent_name,
            start_time=datetime.now(),
            user_message=self.last_user_message,
        )
        self.active_tool_records = {}
        # Re-enable autoscroll when user retries (same as new message submission)
        self.chat_area.autoscroll_enabled = True
        self._request_autoscroll()
        self.chat_area.input.disabled = True
        self._current_task = asyncio.create_task(
            self.stream_response(self.last_user_message, run_id)
        )

    def _restart_chat(self) -> None:
        """Clear chat history and start a new thread."""
        if self.is_agent_running():
            self.app.notify("Stop the current run before restarting chat.", severity="warning")
            return

        self.thread_id = f"tui-{uuid.uuid4().hex[:8]}"
        self.messages = []
        self.current_response = None
        self.thinking_widget = None
        self.current_response_text = ""
        self.active_tool_widgets = {}
        self.active_tool_records = {}
        self.tool_call_to_artifact = {}
        self.active_report_id = None
        self.active_report_title = None
        self.active_report_cells = []
        self.active_report_artifact_id = None
        self.last_user_message = None

        self.chat_area.chat_log.remove_children()
        # Reset placeholder reference since widget was removed from DOM
        self.chat_area.reset_placeholder()
        self.artifact_viewer.display = False

        # Restore the placeholder
        self.chat_area.restore_placeholder()

        self.app.notify("Chat restarted.", severity="information")

    def _format_error_message(self, error: Exception) -> str:
        """Create a user-facing error message with retry guidance."""
        if isinstance(error, AGUIRequestError):
            detail = error.detail or "Unknown error"
            detail = detail.replace("\n", " ").strip()
            if len(detail) > MAX_ERROR_MESSAGE_LENGTH:
                detail = detail[:MAX_ERROR_MESSAGE_LENGTH] + "..."
            status = f"HTTP {error.status_code}" if error.status_code is not None else "Request error"
            return (
                f"**Agent request failed** ({status}).\n\n"
                f"**Details**: {detail}\n\n"
                "You can retry this request or restart the chat."
            )

        message = str(error).strip() or "Unknown error"
        if len(message) > MAX_ERROR_MESSAGE_LENGTH:
            message = message[:MAX_ERROR_MESSAGE_LENGTH] + "..."
        return (
            "**Agent request failed**.\n\n"
            f"**Details**: {message}\n\n"
            "You can retry this request or restart the chat."
        )

    def _handle_artifact(self, tool_call_id: str, content: str) -> Optional[str]:
        """Process tool result content and update artifact viewer.

        Uses Pydantic models for type-safe parsing when tool_name is available,
        with structural detection for protocol types and heuristic fallback.

        Args:
            tool_call_id: ID of the tool call that produced this result
            content: JSON string of tool result

        Returns:
            artifact_id if an artifact was created, None otherwise
        """
        if not content:
            return None

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return None

        # Handle list results
        if isinstance(data, list):
            # Check if it's a list of todos (from get_todos)
            if data and isinstance(data[0], dict) and all(k in data[0] for k in ("id", "content", "status", "priority")):
                self.artifact_viewer.display = True
                return self.artifact_viewer.show_todos(
                    todos=data,
                    tool_call_id=tool_call_id,
                )
            # Other list results don't have typed parsing - just return None for artifacts
            return None

        # Try typed parsing first
        tool_name = data.get("tool_name")
        model_class = self.TOOL_RESULT_MODELS.get(tool_name) if tool_name else None

        if model_class:
            try:
                result = model_class.model_validate(data)
                artifact_id = self._handle_typed_artifact(tool_call_id, result)
                if artifact_id:
                    return artifact_id
            except ValidationError:
                pass  # Fall through to structural/heuristic parsing

        # Try structural detection for protocol types (no tool_name)
        artifact_id = self._handle_protocol_artifact(tool_call_id, data)
        if artifact_id:
            return artifact_id

        # Fallback to heuristic detection
        return self._handle_untyped_artifact(tool_call_id, data)

    def _add_report_cell(
        self,
        cell_type: str,
        cell_data: Dict[str, Any],
        tool_call_id: str,
    ) -> None:
        """Add a cell to the active report with proper ordering.

        Args:
            cell_type: Type of cell (chart, table, mermaid, markdown)
            cell_data: Cell-specific data
            tool_call_id: Tool call ID for ordering
        """
        # Get tool call start time for ordering (cells may arrive out of order)
        tool_record = self.active_tool_records.get(tool_call_id)
        # Use current time as fallback if tool record not found (avoids cells at position 0)
        order_time = (
            tool_record.start_time.timestamp()
            if tool_record
            else datetime.now().timestamp()
        )

        cell = {
            "cell_type": cell_type,
            "_order": order_time,  # For sorting cells by intended order
            "data": cell_data,
        }
        self.active_report_cells.append(cell)

        # Sort cells by tool call start time, then update artifact
        sorted_cells = sorted(
            self.active_report_cells, key=lambda c: c.get("_order", 0)
        )
        if self.active_report_artifact_id:
            self.artifact_viewer.update_report_cells(
                artifact_id=self.active_report_artifact_id,
                cells=sorted_cells,
            )

    def _handle_typed_artifact(
        self, tool_call_id: str, result: BaseModel
    ) -> Optional[str]:
        """Handle artifact display for typed Pydantic model results."""
        self.artifact_viewer.display = True

        # Table results
        if isinstance(result, (PreviewTableResult, ExecuteQueryResult)):
            return self.artifact_viewer.show_table(
                title="Query Result",
                columns=result.columns,
                rows=result.rows,
                tool_call_id=tool_call_id,
            )

        # Graph query results
        if isinstance(result, QueryGraphResult):
            return self.artifact_viewer.show_graph_result(
                title=result.query_description or "Graph Query Results",
                nodes=result.nodes,
                query_description=result.query_description or "",
                display_hint=result.display_hint,
                tool_call_id=tool_call_id,
            )

        # Graph search results
        if isinstance(result, GraphSearchResult):
            return self.artifact_viewer.show_search_results(
                search_term=result.term,
                results=result.matches,
                tool_call_id=tool_call_id,
            )

        # Model search results
        if isinstance(result, SearchModelsResult):
            return self.artifact_viewer.show_search_results(
                search_term=result.search_term,
                results=result.results,
                tool_call_id=tool_call_id,
            )

        # Model details (replaces get_model_semantics)
        if isinstance(result, ModelDetailsResult):
            return self.artifact_viewer.show_model_details(
                title=f"Model: {result.model_name or result.model_id}",
                model_details=result.model_dump(),
                tool_call_id=tool_call_id,
            )

        # Join patterns
        if isinstance(result, JoinPatternsResult):
            return self.artifact_viewer.show_join_patterns(
                model_id=result.model_id,
                model_name=result.model_name or "",
                cluster_id=result.cluster_id or "",
                cluster_pattern=result.cluster_pattern or "",
                join_partners=result.join_partners,
                join_edges=result.join_edges,
                tool_call_id=tool_call_id,
            )

        # Downstream impact
        if isinstance(result, DownstreamImpactResult):
            return self.artifact_viewer.show_impact_tree(
                model_id=result.model_id,
                model_name=result.model_name or "",
                affected_models=result.affected_models,
                total=result.total_affected,
                tool_call_id=tool_call_id,
            )

        # Report creation - create ONE artifact that will be updated as cells are added
        if isinstance(result, CreateReportResult):
            self.active_report_id = result.report_id
            self.active_report_title = result.title
            self.active_report_cells = []  # Reset cells for new report
            # Create the report artifact (empty initially) and track its ID
            self.active_report_artifact_id = self.artifact_viewer.show_report_cells(
                title=result.title,
                report_id=result.report_id,
                cells=[],  # Empty initially, will be updated as cells are added
                html_path=None,
                tool_call_id=tool_call_id,
            )
            return self.active_report_artifact_id

        # CLI output (bash/dbt)
        if isinstance(result, (BashResult, DbtResult)):
            working_dir = getattr(result, "working_dir", None) or getattr(result, "project_dir", "")
            title = "dbt command" if isinstance(result, DbtResult) else "bash command"
            self.artifact_viewer.display = True
            return self.artifact_viewer.show_command_output(
                title=title,
                command=result.command,
                working_dir=working_dir,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                tool_call_id=tool_call_id,
            )

        # Chart cell - update existing report (no new artifact)
        if isinstance(result, ChartCellResult):
            self._add_report_cell(
                cell_type="chart",
                cell_data={
                    "title": result.title,
                    "chart_type": result.chart_type,
                    "data": result.data,
                    "x_column": result.x_column,
                    "y_column": result.y_column,
                },
                tool_call_id=tool_call_id,
            )
            return None  # No new artifact

        # Table cell - update existing report (no new artifact)
        if isinstance(result, TableCellResult):
            self._add_report_cell(
                cell_type="table",
                cell_data={
                    "title": result.title,
                    "columns": result.columns,
                    "rows": result.data,
                },
                tool_call_id=tool_call_id,
            )
            return None  # No new artifact

        # Mermaid cell - update existing report (no new artifact)
        if isinstance(result, MermaidCellResult):
            self._add_report_cell(
                cell_type="mermaid",
                cell_data={
                    "title": result.title,
                    "diagram": result.diagram,
                },
                tool_call_id=tool_call_id,
            )
            return None  # No new artifact

        # Markdown cell - update existing report (no new artifact)
        if isinstance(result, MarkdownCellResult):
            self._add_report_cell(
                cell_type="markdown",
                cell_data={"content": result.content},
                tool_call_id=tool_call_id,
            )
            return None  # No new artifact

        # Ticket creation
        if isinstance(result, CreateTicketResult):
            self.artifact_viewer.display = True
            return self.artifact_viewer.show_ticket_update(
                ticket_id=result.ticket_id,
                action="created",
                message=f"Created ticket **{result.title}**\n\nStatus: {result.status} | Priority: {result.priority}",
                tool_call_id=tool_call_id,
            )

        # Ticket list
        if isinstance(result, ListTicketsResult):
            self.artifact_viewer.display = True
            return self.artifact_viewer.show_ticket_list(
                tickets=result.tickets,
                count=result.count,
                tool_call_id=tool_call_id,
            )

        # Get ticket details
        if isinstance(result, GetTicketResult):
            self.artifact_viewer.display = True
            ticket = result.ticket
            return self.artifact_viewer.show_ticket(
                ticket_id=ticket.get("id", ""),
                title=ticket.get("title", "Untitled"),
                status=ticket.get("status", "unknown"),
                priority=ticket.get("priority", "medium"),
                description=ticket.get("description", ""),
                assigned_to=ticket.get("assigned_to"),
                tags=ticket.get("tags", []),
                created_by=ticket.get("created_by"),
                tool_call_id=tool_call_id,
            )

        # Update ticket
        if isinstance(result, UpdateTicketResult):
            self.artifact_viewer.display = True
            return self.artifact_viewer.show_ticket_update(
                ticket_id=result.ticket_id,
                action="updated",
                message=result.message,
                tool_call_id=tool_call_id,
            )

        # Add ticket comment
        if isinstance(result, AddTicketCommentResult):
            self.artifact_viewer.display = True
            return self.artifact_viewer.show_ticket_update(
                ticket_id=result.ticket_id,
                action="commented",
                message=result.message,
                tool_call_id=tool_call_id,
            )

        return None

    def _handle_protocol_artifact(
        self, tool_call_id: str, data: Dict[str, Any]
    ) -> Optional[str]:
        """Handle artifacts from protocol types that don't have tool_name."""
        # RelationLineageResult - has identifier, direction, nodes, node_type
        if all(k in data for k in ("identifier", "direction", "nodes", "node_type")):
            try:
                result = RelationLineageResult.model_validate(data)
                self.artifact_viewer.display = True
                return self.artifact_viewer.show_lineage(
                    title=f"Lineage: {result.identifier}",
                    root=result.identifier,
                    nodes=[n.model_dump() for n in result.nodes],
                    direction=result.direction,
                    query_description=result.query_description,
                    hops=[],
                    edges=[e.model_dump() for e in result.edges],
                    tool_call_id=tool_call_id,
                )
            except ValidationError:
                pass

        return None

    def _handle_untyped_artifact(
        self, tool_call_id: str, data: Dict[str, Any]
    ) -> Optional[str]:
        """Fallback heuristic handling for unrecognized result formats."""
        # Report with html_path
        if "html_path" in data:
            self.artifact_viewer.display = True
            return self.artifact_viewer.show_report(
                title=data.get("title") or data.get("report_id") or "Report",
                report_path=data.get("html_path"),
                message=data.get("message"),
                tool_call_id=tool_call_id,
            )

        # Table with rows/columns
        if "rows" in data and "columns" in data:
            self.artifact_viewer.display = True
            return self.artifact_viewer.show_table(
                title=data.get("query_name") or "Query Result",
                columns=data["columns"],
                rows=data["rows"],
                tool_call_id=tool_call_id,
            )

        # Graph nodes
        if "nodes" in data and isinstance(data["nodes"], list):
            self.artifact_viewer.display = True
            return self.artifact_viewer.show_graph_result(
                title=data.get("query_description") or "Results",
                nodes=data["nodes"],
                query_description=data.get("query_description") or "",
                display_hint=data.get("display_hint"),
                tool_call_id=tool_call_id,
            )

        # Todo results - check for todo-like structure
        # Single todo item (from add_todo/update_todo)
        if all(k in data for k in ("id", "content", "status", "priority")):
            self.artifact_viewer.display = True
            return self.artifact_viewer.show_todos(
                todos=[data],
                tool_call_id=tool_call_id,
            )

        # Todo summary (from get_summary)
        if all(k in data for k in ("total", "pending", "in_progress", "completed")):
            # This is a summary, but we need the actual todos to display
            # The summary alone isn't enough - we'll just show it in the summary text
            # and not create an artifact (the summary will be shown in the tool message)
            return None

        return None

    # Tool result model registry - maps tool_name to Pydantic model class
    TOOL_RESULT_MODELS: Dict[str, type] = {
        "query_graph": QueryGraphResult,
        "search_graph": GraphSearchResult,
        "preview_table": PreviewTableResult,
        "execute_query": ExecuteQueryResult,
        "search_models": SearchModelsResult,
        "get_model_details": ModelDetailsResult,
        "get_join_patterns": JoinPatternsResult,
        "get_downstream_impact": DownstreamImpactResult,
        "create_report": CreateReportResult,
        "add_chart_cell": ChartCellResult,
        "add_table_cell": TableCellResult,
        "add_mermaid_cell": MermaidCellResult,
        "add_markdown_cell": MarkdownCellResult,
        # CLI tools
        "bash": BashResult,
        "dbt_cli": DbtResult,
        # Ticket tools
        "create_ticket": CreateTicketResult,
        "list_tickets": ListTicketsResult,
        "get_ticket": GetTicketResult,
        "update_ticket": UpdateTicketResult,
        "add_ticket_comment": AddTicketCommentResult,
    }

    def _generate_result_summary(self, content: str) -> Optional[str]:
        """Generate a human-readable summary from tool result content.

        Uses Pydantic models from lineage.agent.pydantic.types for type-safe parsing.

        Args:
            content: JSON string of tool result

        Returns:
            Short summary like "12 rows", "15 results", etc.
        """
        if not content:
            return None

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return None

        # Handle list results
        if isinstance(data, list):
            # Check if it's a list of todos (from get_todos)
            if data and isinstance(data[0], dict) and all(k in data[0] for k in ("id", "content", "status", "priority")):
                count = len(data)
                # Count by status
                pending = sum(1 for t in data if t.get("status") == "pending")
                in_progress = sum(1 for t in data if t.get("status") == "in_progress")
                completed = sum(1 for t in data if t.get("status") == "completed")

                parts = []
                if pending > 0:
                    parts.append(f"{pending} pending")
                if in_progress > 0:
                    parts.append(f"{in_progress} in progress")
                if completed > 0:
                    parts.append(f"{completed} completed")

                if parts:
                    return f"{count} todo{'s' if count != 1 else ''} ({', '.join(parts)})"
                return f"{count} todo{'s' if count != 1 else ''}"
            # Other list results (e.g., list_semantic_views returns List[Dict])
            count = len(data)
            return f"{count} item{'s' if count != 1 else ''}"

        # Try to parse into typed model using tool_name
        tool_name = data.get("tool_name")
        model_class = self.TOOL_RESULT_MODELS.get(tool_name) if tool_name else None

        if model_class:
            try:
                result = model_class.model_validate(data)
                return self._summarize_typed_result(result)
            except ValidationError:
                # Fall through to heuristic parsing if model validation fails
                pass

        # Fallback: heuristic parsing for results without tool_name
        return self._summarize_untyped_result(data)

    def _summarize_typed_result(self, result: Any) -> Optional[str]:
        """Generate summary from a typed Pydantic model result."""
        # Query results with rows
        if isinstance(result, (PreviewTableResult, ExecuteQueryResult)):
            count = result.row_count
            return f"{count} row{'s' if count != 1 else ''}"

        # Graph query results
        if isinstance(result, QueryGraphResult):
            count = result.node_count
            return f"{count} result{'s' if count != 1 else ''}"

        # Graph search results
        if isinstance(result, GraphSearchResult):
            count = result.match_count
            return f"{count} match{'es' if count != 1 else ''}"

        # Model search results
        if isinstance(result, SearchModelsResult):
            count = result.result_count
            return f"{count} match{'es' if count != 1 else ''}"

        # Model details
        if isinstance(result, ModelDetailsResult):
            parts = []
            if result.measures:
                parts.append(f"{len(result.measures)} measures")
            if result.dimensions:
                parts.append(f"{len(result.dimensions)} dims")
            if result.facts:
                parts.append(f"{len(result.facts)} facts")
            if result.columns:
                parts.append(f"{len(result.columns)} cols")
            if result.canonical_sql or result.raw_sql:
                parts.append("SQL")
            return ", ".join(parts) if parts else "basic info"

        if isinstance(result, ModelMaterializationsResult):
            materialization_count = len(result.materializations)
            if materialization_count == 0:
                return "no materializations"
            environments = list(dict.fromkeys(
                m.environment for m in result.materializations
            ))
            count_part = f"{materialization_count} materialization{'s' if materialization_count != 1 else ''}"
            if environments:
                return f"{count_part} across {', '.join(environments)}"
            return count_part

        # Join patterns
        if isinstance(result, JoinPatternsResult):
            count = len(result.join_partners)
            return f"{count} join partner{'s' if count != 1 else ''}"

        # Downstream impact
        if isinstance(result, DownstreamImpactResult):
            count = result.total_affected
            return f"{count} affected model{'s' if count != 1 else ''}"

        # Report creation
        if isinstance(result, CreateReportResult):
            return "report created"

        # Chart cell
        if isinstance(result, ChartCellResult):
            return f"{result.chart_type} chart added"

        # Table cell
        if isinstance(result, TableCellResult):
            count = len(result.data)
            return f"table added ({count} rows)"

        # Mermaid cell
        if isinstance(result, MermaidCellResult):
            return "diagram added"

        # Markdown cell
        if isinstance(result, MarkdownCellResult):
            word_count = len(result.content.split())
            return f"content added ({word_count} words)"

        # Ticket creation
        if isinstance(result, CreateTicketResult):
            return f"ticket {result.ticket_id} created"

        # Ticket list
        if isinstance(result, ListTicketsResult):
            count = result.count
            return f"{count} ticket{'s' if count != 1 else ''}"

        # Get ticket
        if isinstance(result, GetTicketResult):
            return "ticket loaded"

        # Update ticket
        if isinstance(result, UpdateTicketResult):
            return "ticket updated"

        # Add ticket comment
        if isinstance(result, AddTicketCommentResult):
            return "comment added"

        # CLI tools
        if isinstance(result, (BashResult, DbtResult)):
            stdout_len = len(result.stdout or "")
            stderr_len = len(result.stderr or "")
            status = "exit 0" if result.exit_code == 0 else f"exit {result.exit_code}"
            extras = []
            if stdout_len:
                extras.append(f"stdout {stdout_len} chars")
            if stderr_len:
                extras.append(f"stderr {stderr_len} chars")
            extra_str = f" ({', '.join(extras)})" if extras else ""
            return f"{status}{extra_str}"

        return None

    def _summarize_untyped_result(self, data: Dict[str, Any]) -> Optional[str]:
        """Fallback summary for results without a tool_name or failed parsing."""
        # Todo summary (from get_summary) - generate nice summary
        if all(k in data for k in ("total", "pending", "in_progress", "completed")):
            total = data.get("total", 0)
            pending = data.get("pending", 0)
            in_progress = data.get("in_progress", 0)
            completed = data.get("completed", 0)

            parts = []
            if pending > 0:
                parts.append(f"{pending} pending")
            if in_progress > 0:
                parts.append(f"{in_progress} in progress")
            if completed > 0:
                parts.append(f"{completed} completed")

            if parts:
                return f"{total} todo{'s' if total != 1 else ''} ({', '.join(parts)})"
            return f"{total} todo{'s' if total != 1 else ''}"

        # Single todo item (from add_todo/update_todo)
        if all(k in data for k in ("id", "content", "status", "priority")):
            status = data.get("status", "pending")
            if status == "completed":
                return "todo completed"
            elif status == "in_progress":
                return "todo in progress"
            else:
                return "todo added"

        # Table results (rows + columns)
        if "rows" in data and isinstance(data["rows"], list):
            row_count = len(data["rows"])
            return f"{row_count} row{'s' if row_count != 1 else ''}"

        # Graph nodes
        if "nodes" in data and isinstance(data["nodes"], list):
            node_count = len(data["nodes"])
            return f"{node_count} result{'s' if node_count != 1 else ''}"

        # Search results
        if "results" in data and isinstance(data["results"], list):
            result_count = len(data["results"])
            return f"{result_count} match{'es' if result_count != 1 else ''}"

        # Lineage with hops
        if "hops" in data and isinstance(data["hops"], list):
            hop_count = len(data["hops"])
            return f"{hop_count} hop{'s' if hop_count != 1 else ''}"

        # Generic success
        if data.get("success") is True:
            return "success"

        # Message-based results
        if "message" in data and isinstance(data["message"], str):
            msg = data["message"]
            if len(msg) > 30:
                return msg[:60] + "..."
            return msg

        return None