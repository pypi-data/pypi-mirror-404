"""Small widget classes for the Nspec TUI."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from textual import events, on
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Input, Label, OptionList, Static
from textual.widgets.option_list import Option

from nspec.statuses import EPIC_PRIORITIES
from nspec.validators import FRMetadata, IMPLMetadata

from .utils import clean_title


class SearchBar(Input):
    """Search input with vim-like keybindings.

    Prevents single-character app bindings (q, n, r, e, s, m) from triggering
    while typing in the search bar.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize search bar."""
        super().__init__(*args, placeholder="Search specs...", **kwargs)

    def _on_key(self, event: events.Key) -> None:
        """Handle key events - stop propagation for characters that have app bindings."""
        # Handle escape to blur search bar and let app handle it
        if event.key == "escape":
            self.value = ""
            self.blur()
            # Don't stop - let the app's action_clear_search handle hiding the container
            return
        # Let the Input handle the key first
        super()._on_key(event)
        # Stop propagation for single printable characters to prevent app bindings
        if len(event.key) == 1 and event.key.isprintable():
            event.stop()
        # Also stop for characters that might trigger app shortcuts
        if event.key in ("q", "n", "r", "e", "s", "m", "/"):
            event.stop()


class StatusIndicator(Static):
    """Shows refresh status and legend."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize status indicator."""
        super().__init__(*args, **kwargs)
        self.last_refresh = datetime.now()
        self.auto_refresh = True
        self.follow_mode_enabled = False
        self.follow_spec_id: str | None = None

    def update_status(
        self,
        count: int,
        epic_filter: str | None = None,
        follow_mode: bool = False,
        follow_spec: str | None = None,
    ) -> None:
        """Update the status display."""
        now = datetime.now().strftime("%H:%M:%S")

        status = f"[bold]Specs:[/] {count} | [bold]Last refresh:[/] {now}"
        if epic_filter:
            status += f" | [bold]Epic:[/] {epic_filter}"

        refresh_icon = "+" if self.auto_refresh else "-"
        status += f" | {refresh_icon} Auto-refresh"

        # Follow mode indicator
        if follow_mode:
            follow_text = (
                f"[bold]* FOLLOW: {follow_spec}[/]" if follow_spec else "[bold]* FOLLOW[/]"
            )
            status += f" | {follow_text}"

        self.update(status)


class EpicBanner(Static):
    """Banner showing the current epic filter."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize epic banner."""
        super().__init__(*args, **kwargs)

    def show_epic(self, epic_id: str, title: str, spec_count: int) -> None:
        """Display epic banner."""
        self.update(f"[bold]EPIC {epic_id}:[/] {title} [dim]({spec_count} specs)[/]")

    def hide(self) -> None:
        """Hide the banner."""
        self.update("")


class EpicSelector(Static):
    """Modal selector for choosing an epic."""

    class EpicSelected(Message):
        """Message sent when an epic is selected."""

        def __init__(self, epic_id: str | None) -> None:
            """Initialize with epic ID (None to clear filter)."""
            super().__init__()
            self.epic_id = epic_id

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize epic selector."""
        super().__init__(*args, **kwargs)
        self.epics: list[tuple[str, str]] = []  # (id, title) pairs

    def compose(self) -> ComposeResult:
        """Create the option list."""
        yield Label("[bold]Select an Epic[/] (Enter to select, Esc to cancel)")
        yield OptionList(id="epic-list")

    def on_mount(self) -> None:
        """Focus the option list when mounted."""
        option_list = self.query_one("#epic-list", OptionList)
        option_list.focus()

    def set_epics(self, epics: list[tuple[str, str, int, str]]) -> None:
        """Set the list of epics (id, title, spec_count, priority)."""
        option_list = self.query_one("#epic-list", OptionList)

        # Clear all options
        option_list.clear_options()

        # Add "All Specs" option first
        option_list.add_option(Option("[dim]All Specs (clear filter)[/]", id="__all__"))

        # Add each epic with priority emoji
        for epic_id, title, count, priority in epics:
            emoji = EPIC_PRIORITIES.get(priority, EPIC_PRIORITIES.get("E3")).emoji
            display = f"{emoji} {epic_id}: {title[:40]}{'...' if len(title) > 40 else ''} ({count})"
            option_list.add_option(Option(display, id=epic_id))

    @on(OptionList.OptionSelected)
    def handle_selection(self, event: OptionList.OptionSelected) -> None:
        """Handle epic selection."""
        option_id = str(event.option_id) if event.option_id is not None else ""
        if option_id == "__all__":
            self.post_message(self.EpicSelected(None))
        else:
            self.post_message(self.EpicSelected(option_id))


class MoveSpecModal(Static):
    """Modal selector for moving a spec to a different epic."""

    class SpecMoved(Message):
        """Message sent when a spec is moved."""

        def __init__(self, spec_id: str, target_epic: str) -> None:
            """Initialize with spec ID and target epic."""
            super().__init__()
            self.spec_id = spec_id
            self.target_epic = target_epic

    class MoveCancelled(Message):
        """Message sent when move is cancelled."""

        pass

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize move spec modal."""
        super().__init__(*args, **kwargs)
        self.spec_id: str | None = None
        self.spec_title: str = ""

    def compose(self) -> ComposeResult:
        """Create the option list."""
        yield Label(id="move-label")
        yield OptionList(id="move-epic-list")

    def on_mount(self) -> None:
        """Focus the option list when mounted."""
        option_list = self.query_one("#move-epic-list", OptionList)
        option_list.focus()

    def set_spec(self, spec_id: str, spec_title: str) -> None:
        """Set the spec to be moved."""
        self.spec_id = spec_id
        self.spec_title = spec_title
        label = self.query_one("#move-label", Label)
        truncated = spec_title[:30] + "..." if len(spec_title) > 30 else spec_title
        label.update(
            f"[bold]Move Spec {spec_id}:[/] {truncated}\n[dim](Enter to select, Esc to cancel)[/]"
        )

    def set_epics(
        self, epics: list[tuple[str, str, int, str]], current_epic: str | None = None
    ) -> None:
        """Set the list of epics (id, title, spec_count, priority).

        Args:
            epics: List of (epic_id, title, spec_count, priority) tuples
            current_epic: Current epic ID to mark (optional)
        """
        option_list = self.query_one("#move-epic-list", OptionList)

        # Clear all options
        option_list.clear_options()

        # Add each epic with priority emoji
        for epic_id, title, count, priority in epics:
            emoji = EPIC_PRIORITIES.get(priority, EPIC_PRIORITIES.get("E3")).emoji
            marker = " [dim](current)[/]" if epic_id == current_epic else ""
            display = f"{emoji} {epic_id}: {title[:35]}{'...' if len(title) > 35 else ''} ({count}){marker}"
            option_list.add_option(Option(display, id=epic_id))

    @on(OptionList.OptionSelected)
    def handle_selection(self, event: OptionList.OptionSelected) -> None:
        """Handle epic selection for move."""
        if self.spec_id and event.option_id:
            self.post_message(self.SpecMoved(self.spec_id, str(event.option_id)))


class SpecDetailPanel(Static):
    """Panel showing details of the selected spec."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize detail panel."""
        super().__init__(*args, **kwargs)
        self.visible = True

    def show_spec(
        self,
        spec_id: str,
        fr: FRMetadata | None,
        impl: IMPLMetadata | None,
    ) -> None:
        """Display spec details."""
        if not fr:
            self.update(f"[dim]Spec {spec_id} not found[/]")
            return

        lines = []
        lines.append(f"[bold]Spec {spec_id}[/]")
        lines.append("-" * 30)

        # Title (truncated if long)
        title = clean_title(fr.title)
        if len(title) > 35:
            title = title[:32] + "..."
        lines.append(f"[bold]{title}[/]")
        lines.append("")

        # FR metadata
        lines.append("[underline]Feature Request[/]")
        lines.append(f"  Status: {fr.status}")
        lines.append(f"  Priority: {fr.priority}")
        lines.append(f"  Type: {fr.type}")

        # Dependencies
        if fr.deps:
            deps_str = ", ".join(fr.deps[:5])
            if len(fr.deps) > 5:
                deps_str += f" (+{len(fr.deps) - 5} more)"
            lines.append(f"  Deps: {deps_str}")

        # Acceptance Criteria progress
        if fr.ac_total > 0:
            lines.append(f"  AC: {fr.ac_completed}/{fr.ac_total} ({fr.ac_completion_percent}%)")

        lines.append("")

        # IMPL metadata
        if impl:
            lines.append("[underline]Implementation[/]")
            lines.append(f"  Status: {impl.status}")
            lines.append(f"  LOE: {impl.effective_loe}")

            # Task progress
            if impl.tasks_total > 0:
                lines.append(
                    f"  Tasks: {impl.tasks_completed}/{impl.tasks_total} ({impl.completion_percent}%)"
                )

                # Show first few tasks
                lines.append("")
                lines.append("[underline]Tasks[/]")
                for task in impl.tasks[:8]:
                    check = "[x]" if task.completed else "[ ]"
                    desc = (
                        task.description[:25] + "..."
                        if len(task.description) > 25
                        else task.description
                    )
                    lines.append(f"  {check} {desc}")
                if len(impl.tasks) > 8:
                    lines.append(f"  ... +{len(impl.tasks) - 8} more")
        else:
            lines.append("[dim]No IMPL found[/]")

        self.update("\n".join(lines))

    def clear_spec(self) -> None:
        """Clear the panel."""
        self.update("[dim]Select a spec to see details[/]")


class SectionHeader(Static):
    """Clickable section header for detail view."""

    def __init__(self, title: str, section_id: str, *args: Any, **kwargs: Any) -> None:
        """Initialize section header."""
        super().__init__(*args, **kwargs)
        self.title = title
        self.section_id = section_id
        self.expanded = True

    def render(self) -> str:
        """Render the section header."""
        icon = "▼" if self.expanded else "▶"
        return f"[bold]{icon} {self.title}[/]"

    def toggle(self) -> bool:
        """Toggle expanded state, return new state."""
        self.expanded = not self.expanded
        self.refresh()
        return self.expanded


class SectionContent(Static):
    """Content container for a section."""

    pass


class TaskRow(Static):
    """Individual task row widget for scroll targeting.

    Accepts a `state` string that maps to a CSS class for theme-driven styling:
        "complete"  → .task-complete   ($success)
        "pending"   → .task-pending    ($text-muted)
        "delegated" → .task-delegated  ($accent)
        "active"    → .task-active     ($success + bold, spinner row)
        "chrome"    → .task-chrome     ($text-muted, tree borders)
        None        → no extra class   (default $text)
    """

    def __init__(
        self,
        content: str,
        task_id: str | None = None,
        is_active: bool = False,
        state: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(content, **kwargs)
        self.task_id = task_id
        self.is_active = is_active
        if is_active:
            self.add_class("task-active")
        if state:
            self.add_class(f"task-{state}")


class DynamicFooter(Static):
    """Footer that can toggle between normal and extended bindings display."""

    # Primary bindings for main app view
    APP_PRIMARY_BINDINGS = [
        ("q", "Quit"),
        ("/", "Search"),
        ("n/N", "Next/Prev"),
        ("Enter", "Details"),
        ("e", "Epic"),
        ("f", "Follow"),
        ("?", "More"),
    ]

    # Extended bindings for main app view
    APP_EXTENDED_BINDINGS = [
        ("r", "Refresh"),
        ("m", "Move"),
        ("s", "Reports"),
        ("Esc", "Clear"),
        ("?", "Less"),
    ]

    # Primary bindings for detail screen
    DETAIL_PRIMARY_BINDINGS = [
        ("Esc", "Close"),
        ("Tab", "Next"),
        ("Enter", "Toggle"),
        ("←/→", "Nav"),
        ("y", "URI"),
        ("x", "Complete"),
        ("?", "More"),
    ]

    # Extended bindings for detail screen
    DETAIL_EXTENDED_BINDINGS = [
        ("d", "Expand Deps"),
        ("Y", "Copy Spec"),
        ("Alt+y", "Copy Epic"),
        ("~", "Obsolete"),
        ("g", "Goto URI"),
        ("1-3", "Jump Dep"),
        ("?", "Less"),
    ]

    def __init__(self, context: str = "app", *args: Any, **kwargs: Any) -> None:
        """Initialize dynamic footer.

        Args:
            context: Either "app" for main app or "detail" for detail screen
        """
        super().__init__(*args, **kwargs)
        self._extended_mode = False
        self._context = context

    def on_mount(self) -> None:
        """Render initial footer content."""
        # Safely auto-detect context from parent screen type
        try:
            # If we're in a DetailViewScreen, use detail bindings
            from .detail_screen import DetailViewScreen

            # Ensure screen property is accessible
            if hasattr(self, "screen") and self.screen is not None:
                if isinstance(self.screen, DetailViewScreen):
                    self._context = "detail"
        except Exception:
            # If context detection fails, keep default
            pass

        try:
            self._render_footer()
        except Exception:
            # If initial render fails, set a safe fallback
            self.renderable = "[dim]Loading...[/]"

    def set_extended_mode(self, extended: bool) -> None:
        """Set whether to show extended bindings."""
        self._extended_mode = extended
        self._render_footer()

    def _render_footer(self) -> None:
        """Render the footer content based on current mode and context."""
        if self._context == "detail":
            bindings = (
                self.DETAIL_EXTENDED_BINDINGS
                if self._extended_mode
                else self.DETAIL_PRIMARY_BINDINGS
            )
        else:
            bindings = (
                self.APP_EXTENDED_BINDINGS if self._extended_mode else self.APP_PRIMARY_BINDINGS
            )

        parts = []
        for key, desc in bindings:
            parts.append(f"[bold]{key}[/] {desc}")
        self.update(" | ".join(parts))


class HelpModal(Static):
    """Modal showing help information and legend."""

    HELP_TEXT = """[bold]novaspec HELP[/]

[bold underline]Status Legend[/]
[bold]Specs:[/]   🟡 Proposed  🔵 Active  🧪 Testing  ✅ Completed  ⏳ Paused
[bold]Epics:[/]   📋 Planning  🚀 In Progress  🏆 Done

[bold underline]Keybindings[/]
[bold]q[/]       Quit
[bold]/[/]       Search specs
[bold]Esc[/]     Clear search / Close modal
[bold]n/N[/]     Next/Previous search match
[bold]Enter[/]   Open spec details
[bold]e[/]       Epic filter selector
[bold]f[/]       Toggle follow mode
[bold]r[/]       Refresh data
[bold]b[/]       Toggle compact mode (borderless)
[bold]m[/]       Move spec to epic
[bold]s[/]       Show reports
[bold]h[/]       Show this help
[bold]?[/]       Toggle extended footer

[dim]Press Esc or h to close[/]"""

    def compose(self) -> ComposeResult:
        """Compose the help modal."""
        yield Label(self.HELP_TEXT)
