"""Base wizard framework for typedef TUI.

This module provides base classes for building multi-step wizards with
consistent styling matching the Data Concierge TUI.
"""
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Optional

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import Button, Label, Static

# Color palette from existing TUI (kept for Python code that needs colors)
USER_BLUE = "#2f4aa6"
ASSISTANT_DARK = "#172031"
ASSISTANT_LIGHT = "#acbefa"
ACTIVE_YELLOW = "#ffbf30"
BORDER_SECONDARY = "#374881"
SURFACE_DARK = "#111111"
ACCENT_PURPLE = "#6a3cd9"
ERROR_RED = "#ff4d4f"
BACKGROUND_BLUE = "#29394e"

# Path to shared CSS file
STYLES_PATH = Path(__file__).parent / "styles.tcss"


class StepState(Enum):
    """State machine for wizard steps with async validation."""

    IDLE = auto()  # Ready for user input
    VALIDATING = auto()  # Running async validation
    VALID = auto()  # Validation passed
    INVALID = auto()  # Validation failed
    WORKING = auto()  # Background work in progress
    COMPLETED = auto()  # Work finished successfully
    FAILED = auto()  # Work failed


class AsyncStepMixin:
    """Mixin for steps that perform async validation or background work.

    This mixin provides a state machine to properly handle async operations
    in wizard steps, ensuring thread-safe UI updates and preventing
    double-submission during validation.

    Usage:
        class MyStep(WizardStep, AsyncStepMixin):
            def __init__(self, ...):
                super().__init__(...)
                self.init_async_state()  # Initialize mixin state

            @work(thread=True)
            def _do_validation(self):
                self.set_state(StepState.VALIDATING)
                try:
                    # ... validation logic ...
                    self.set_state(StepState.VALID)
                except Exception as e:
                    self.set_state(StepState.INVALID, str(e))

            async def validate(self):
                if self.state == StepState.IDLE:
                    self._do_validation()
                    return False, ""  # Signal "in progress"
                return self.check_async_state()
    """

    state: StepState
    _error_message: str

    def init_async_state(self) -> None:
        """Initialize async state. Call this in __init__ of subclasses."""
        self.state = StepState.IDLE
        self._error_message = ""

    def set_state(self, new_state: StepState, error: str = "") -> None:
        """Thread-safe state transition with optional error message."""
        self.state = new_state
        self._error_message = error
        # Update UI from worker thread if app is available
        if hasattr(self, "app") and self.app:
            self.app.call_from_thread(self._on_state_changed)

    def _on_state_changed(self) -> None:
        """Called on main thread when state changes. Override for custom UI updates."""
        pass

    def reset_state(self) -> None:
        """Reset to IDLE state. Useful when going back in wizard."""
        self.state = StepState.IDLE
        self._error_message = ""

    def check_async_state(self) -> tuple[bool, str]:
        """Check current state and return validation result.

        Returns:
            tuple: (is_valid, error_message)
                - (False, "") means validation is still in progress
                - (False, "error") means validation failed
                - (True, "") means validation passed
        """
        if self.state == StepState.VALIDATING:
            return False, ""  # Still working
        if self.state == StepState.WORKING:
            return False, ""  # Still working
        if self.state == StepState.INVALID:
            return False, self._error_message
        if self.state == StepState.FAILED:
            return False, self._error_message
        if self.state in (StepState.VALID, StepState.COMPLETED):
            return True, ""
        # IDLE state - shouldn't reach here if used correctly
        return True, ""


class WizardStep(Container):
    """Base class for wizard steps with consistent styling."""

    def __init__(self, title: str, description: str, step_id: str):
        """Initialize a wizard step with identifiers and labels."""
        super().__init__(id=f"step-{step_id}", classes="wizard-step")
        self.title = title
        self.description = description
        self.step_id = step_id
        self.error_message = ""

    def compose(self) -> ComposeResult:
        """Compose the wizard step with title, description, and content."""
        yield Label(self.title, classes="wizard-title")
        yield Label(self.description, classes="wizard-description")

        # Error message (hidden by default)
        yield Static("", id=f"error-{self.step_id}", classes="wizard-error")

        # Step-specific content (scrollable for long forms)
        with VerticalScroll(classes="wizard-content"):
            yield from self.get_content()

        # Status area outside scroll - always visible at bottom of step
        # Steps can update this via query_one("#step-status", Static)
        yield Static("", id="step-status", classes="step-status")

    def get_content(self) -> ComposeResult:
        """Override to provide step-specific content."""
        raise NotImplementedError("Subclasses must implement get_content()")

    async def validate(self) -> tuple[bool, str]:
        """Validate step data.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        return True, ""

    def get_data(self) -> dict[str, Any]:
        """Extract data from the step.
        
        Returns:
            dict: Step data to be included in final wizard result
        """
        return {}

    def show_error(self, message: str):
        """Display an error message on the step."""
        error_widget = self.query_one(f"#error-{self.step_id}", Static)
        error_widget.update(f"❌ {message}")
        error_widget.display = True

    def clear_error(self):
        """Clear any error message."""
        try:
            error_widget = self.query_one(f"#error-{self.step_id}", Static)
            error_widget.update("")
            error_widget.display = False
        except NoMatches:
            # Error widget might not exist in all steps
            pass


class WizardScreen(Screen):
    """Base wizard screen with multi-step navigation."""

    CSS_PATH = STYLES_PATH

    def __init__(
        self,
        steps: list[WizardStep],
        title: str = "Setup Wizard",
        on_complete: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        """Initialize the wizard screen with steps and optional callback."""
        super().__init__()
        self.steps = steps
        self.wizard_title = title
        self.current_step_idx = 0
        self.on_complete = on_complete
        self.wizard_data: dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        """Compose the wizard screen."""
        with Vertical(classes="wizard-container") as container:
            container.border_title = self.wizard_title

            # Progress indicator
            yield Static(
                self._get_progress_text(),
                id="wizard-progress",
                classes="wizard-progress",
            )

            # Current step (will be swapped as user navigates)
            yield self.steps[self.current_step_idx]

        # Navigation buttons
        with Horizontal(classes="wizard-nav"):
            yield Button("← Back", id="back-btn", classes="wizard-button")
            yield Button(
                "Next →" if self.current_step_idx < len(self.steps) - 1 else "Finish",
                id="next-btn",
                classes="wizard-button",
                variant="primary",
            )
            yield Button("Cancel", id="cancel-btn", classes="wizard-button", variant="error")

    def _get_progress_text(self) -> str:
        """Get progress indicator text."""
        return f"Step {self.current_step_idx + 1} of {len(self.steps)}"

    def on_mount(self) -> None:
        """Handle screen mount."""
        self._update_navigation_state()
        self._focus_first_step_widget()

    async def on_key(self, event: events.Key) -> None:
        """Handle Enter to advance the wizard."""
        if event.key != "enter":
            return

        focused = self.app.focused
        if isinstance(focused, Button):
            if focused.id == "back-btn":
                await self._go_back()
                event.stop()
            elif focused.id == "cancel-btn":
                self.dismiss(None)
                event.stop()
            elif focused.id == "next-btn":
                await self._go_next()
                event.stop()
            return

        # Don't auto-advance; allow focused widgets (inputs) to handle Enter.
        return

    def _update_navigation_state(self):
        """Update button states based on current step."""
        back_btn = self.query_one("#back-btn", Button)
        next_btn = self.query_one("#next-btn", Button)
        
        # Disable back button on first step
        back_btn.disabled = self.current_step_idx == 0
        
        # Update next button label
        if self.current_step_idx == len(self.steps) - 1:
            next_btn.label = "Finish"
        else:
            next_btn.label = "Next →"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "back-btn":
            await self._go_back()
        elif event.button.id == "next-btn":
            await self._go_next()

    async def _go_next(self):
        """Move to next step or finish wizard."""
        current_step = self.steps[self.current_step_idx]

        # Validate current step
        is_valid, error_msg = await current_step.validate()
        if not is_valid:
            # Only show error if there's a message (empty means "in progress")
            if error_msg:
                current_step.show_error(error_msg)
            return

        # Clear any previous errors
        current_step.clear_error()
        
        # Collect data from current step
        step_data = current_step.get_data()
        self.wizard_data.update(step_data)
        
        # Check if this is the last step
        if self.current_step_idx == len(self.steps) - 1:
            # Wizard complete
            if self.on_complete:
                self.on_complete(self.wizard_data)
            self.dismiss(self.wizard_data)
            return
        
        # Move to next step
        self.current_step_idx += 1
        await self._switch_step()

    async def _go_back(self):
        """Move to previous step."""
        if self.current_step_idx > 0:
            self.current_step_idx -= 1
            await self._switch_step()

    async def _switch_step(self):
        """Switch to the current step."""
        # Update progress text
        progress = self.query_one("#wizard-progress", Static)
        progress.update(self._get_progress_text())
        
        # Remove old step and mount new one
        container = self.query_one(".wizard-container", Vertical)
        
        # Remove all steps except progress
        for step in self.steps:
            if step.is_attached:
                await step.remove()
        
        # Mount current step
        await container.mount(self.steps[self.current_step_idx])
        
        # Update navigation
        self._update_navigation_state()
        self._focus_first_step_widget()

    def _focus_first_step_widget(self) -> None:
        """Focus the top-most interactive widget within the current step."""
        step = self.steps[self.current_step_idx]
        candidates = list(step.query(".wizard-content *")) or list(step.query("*"))
        for widget in candidates:
            if not getattr(widget, "can_focus", False):
                continue
            if not getattr(widget, "display", True):
                continue
            if hasattr(widget, "disabled") and widget.disabled:
                continue
            widget.focus()
            return
        # Fallback to primary navigation (avoid cancel by default).
        try:
            next_btn = self.query_one("#next-btn", Button)
            if not next_btn.disabled:
                next_btn.focus()
                return
            back_btn = self.query_one("#back-btn", Button)
            if not back_btn.disabled:
                back_btn.focus()
                return
        except NoMatches:
            # Navigation buttons may not exist; leave focus unchanged.
            pass


class BaseWizardApp(App):
    """Base application for running wizards."""

    def __init__(self, wizard_screen: WizardScreen):
        """Wrap a wizard screen to run as a Textual App."""
        super().__init__()
        self.wizard_screen = wizard_screen
        self.result: Optional[dict[str, Any]] = None

    def on_mount(self) -> None:
        """Mount the wizard screen."""
        def handle_result(data: Optional[dict[str, Any]]):
            self.result = data
            # Pass data through exit so App.run() returns the wizard result
            self.exit(data)

        self.wizard_screen.on_complete = handle_result
        self.push_screen(self.wizard_screen, callback=handle_result)

