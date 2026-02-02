"""Detail view screen for the Nspec TUI."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Header, Static

from nspec.crud import check_impl_task
from nspec.tasks import Task
from nspec.validators import FRMetadata, IMPLMetadata

from .utils import clean_title, format_status
from .widgets import SectionContent, SectionHeader, TaskRow

if TYPE_CHECKING:
    from .state import NspecData


class DetailViewScreen(Screen):
    """Full-screen detail view for a spec with navigable sections."""

    BINDINGS = [
        Binding("escape", "close", "Close", priority=True),
        Binding("q", "close", "Close"),
        Binding("tab", "next_section", "Next"),
        Binding("shift+tab", "prev_section", "Prev"),
        Binding("down", "next_section", "Next Section", show=False),
        Binding("up", "prev_section", "Prev Section", show=False),
        Binding("j", "next_section", "Next Section", show=False),
        Binding("k", "prev_section", "Prev Section", show=False),
        Binding("enter", "toggle_section", "Toggle"),
        Binding("space", "toggle_section", "Toggle Section", show=False),
        Binding("left", "go_upstream", "Upstream"),
        Binding("h", "go_upstream", "Upstream", show=False),
        Binding("right", "go_downstream", "Downstream"),
        Binding("l", "go_downstream", "Downstream", show=False),
        Binding("1", "jump_dep_1", "Dep 1", show=False),
        Binding("2", "jump_dep_2", "Dep 2", show=False),
        Binding("3", "jump_dep_3", "Dep 3", show=False),
        Binding("y", "copy_uri", "Copy URI"),
        Binding("g", "goto_uri", "Goto URI"),
        Binding("x", "mark_task_complete", "Complete"),
        Binding("tilde", "mark_task_obsolete", "Obsolete", key_display="~"),
        Binding("d", "toggle_deps", "Expand Deps", show=False),
        Binding("shift+y", "copy_spec", "Copy Spec", key_display="Y", show=False),
        Binding("alt+y", "copy_epic", "Copy Epic", show=False),
        Binding("question_mark", "toggle_footer", "More", key_display="?"),
    ]

    # Spinner animation frames for in-progress tasks
    SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(
        self,
        spec_id: str,
        fr: FRMetadata | None,
        impl: IMPLMetadata | None,
        data: NspecData | None = None,
        is_follow_target: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize detail view screen."""
        super().__init__(*args, **kwargs)
        self.spec_id = spec_id
        self.fr = fr
        self.impl = impl
        self.data = data
        self.is_follow_target = is_follow_target
        self.sections: list[str] = []
        self.current_section_idx = 0
        self.upstream_specs: list[str] = []
        self.downstream_specs: list[str] = []
        self.spinner_frame_idx = 0
        self.first_pending_task_id: str | None = None
        self.active_task_line: int = 0
        self.show_all_deps: bool = False
        self.show_extended_footer: bool = False
        self._build_navigation_lists()

    def _is_pending_task(self, task: Task) -> bool:
        """Return True for tasks that represent actionable pending work."""
        return (not task.completed) and (task.delegated_to is None)

    def _select_active_task_id(self) -> str | None:
        """Select the active task for follow mode.

        We select the first pending *leaf* task (depth-first). A task is a "leaf"
        if no other task IDs begin with `{id}.` - this handles hierarchy via
        dotted IDs (e.g., 2.1 is parent of 2.1.1) even without markdown indentation.

        Parent/grouping tasks are skipped UNLESS all their descendants are complete,
        in which case the parent task is promoted to active.
        """
        if not self.impl or not self.impl.tasks:
            return None

        def flatten(tasks: list[Task]) -> list[Task]:
            result: list[Task] = []
            for t in tasks:
                result.append(t)
                if t.children:
                    result.extend(flatten(t.children))
            return result

        flat_tasks = flatten(self.impl.tasks)
        task_by_id = {t.id: t for t in flat_tasks}
        all_ids = [t.id for t in flat_tasks]

        def get_descendant_ids(task_id: str) -> list[str]:
            """Return all task IDs that start with this ID + dot."""
            prefix = f"{task_id}."
            return [tid for tid in all_ids if tid.startswith(prefix)]

        def has_pending_descendants(task_id: str) -> bool:
            """Return True if any descendant is pending (incomplete)."""
            for desc_id in get_descendant_ids(task_id):
                desc_task = task_by_id.get(desc_id)
                if desc_task and self._is_pending_task(desc_task):
                    return True
            return False

        for task in flat_tasks:
            if not self._is_pending_task(task):
                continue
            # Skip parent tasks only if they have pending descendants
            # (promotes parent when all descendants are complete)
            if has_pending_descendants(task.id):
                continue
            return task.id

        return None

    def _virtual_y_within(self, widget: Widget, ancestor: Widget) -> int | None:
        """Return widget virtual y relative to ancestor (virtual coordinate space)."""
        y = widget.virtual_region.y
        parent = widget.parent
        while parent is not None and parent is not ancestor:
            if not isinstance(parent, Widget):
                return None
            y += parent.virtual_region.y
            parent = parent.parent
        return y if parent is ancestor else None

    def _build_navigation_lists(self) -> None:
        """Build lists of upstream and downstream specs for navigation."""
        if not self.data or not self.data.datasets:
            return

        if self.fr and self.fr.deps:
            self.upstream_specs = list(self.fr.deps)

        if self.spec_id in self.data.reverse_deps:
            self.downstream_specs = list(self.data.reverse_deps[self.spec_id])

    def _navigate_to_spec(self, target_id: str) -> None:
        """Navigate to a different spec, replacing current screen."""
        if not self.data or not self.data.datasets:
            return

        fr = self.data.datasets.get_fr(target_id)
        impl = self.data.datasets.get_impl(target_id)

        if not fr and target_id in self.data.datasets.completed_frs:
            fr = self.data.datasets.completed_frs[target_id]
        if not impl and target_id in self.data.datasets.completed_impls:
            impl = self.data.datasets.completed_impls[target_id]

        if not fr:
            self.notify(f"Spec {target_id} not found", severity="warning", timeout=2)
            return

        self.app.pop_screen()
        new_screen = DetailViewScreen(
            spec_id=target_id,
            fr=fr,
            impl=impl,
            data=self.data,
        )
        self.app.push_screen(new_screen)

    def on_mount(self) -> None:
        """Start spinner animation and file watching."""
        # Always watch for file changes so MCP tool mutations are reflected
        self.set_interval(1.0, self._check_file_changes)
        self._last_impl_mtime = self._get_impl_mtime()
        self._last_fr_mtime = self._get_fr_mtime()

        if self.is_follow_target:
            self.set_interval(0.1, self._animate_spinner)
            self.call_after_refresh(self._scroll_to_tasks)

    def _get_impl_mtime(self) -> float:
        """Get modification time of the IMPL file for this spec."""
        impl_dir = self.data.paths.active_impls_dir if self.data else Path("docs") / "impls/active"
        pattern = f"IMPL-{self.spec_id}-*.md"
        for path in impl_dir.glob(pattern):
            return path.stat().st_mtime
        return 0.0

    def _get_fr_mtime(self) -> float:
        """Get modification time of the FR file for this spec."""
        fr_dir = self.data.paths.active_frs_dir if self.data else Path("docs") / "frs/active"
        pattern = f"FR-{self.spec_id}-*.md"
        for path in fr_dir.glob(pattern):
            return path.stat().st_mtime
        return 0.0

    @work(exclusive=True, thread=True)
    def _check_file_changes(self) -> None:
        """Check if FR or IMPL files changed and refresh view."""
        impl_mtime = self._get_impl_mtime()
        fr_mtime = self._get_fr_mtime()

        impl_changed = hasattr(self, "_last_impl_mtime") and impl_mtime > self._last_impl_mtime
        fr_changed = hasattr(self, "_last_fr_mtime") and fr_mtime > self._last_fr_mtime

        if impl_changed:
            self._last_impl_mtime = impl_mtime
        if fr_changed:
            self._last_fr_mtime = fr_mtime

        if impl_changed or fr_changed:
            self.app.call_from_thread(self._refresh_spec_data)

    def _refresh_spec_data(self) -> None:
        """Reload FR+IMPL data and refresh the view."""
        if not self.data or not self.data.datasets:
            return

        self.data.load()
        self.fr = self.data.datasets.get_fr(self.spec_id)
        self.impl = self.data.datasets.get_impl(self.spec_id)

        try:
            # Refresh tasks
            tasks_container = self.query_one("#tasks-content", Vertical)
            tasks_container.remove_children()
            self.first_pending_task_id = None
            for task_row in self._compose_task_rows():
                tasks_container.mount(task_row)

            # Refresh overview (has FR + IMPL status info)
            overview_content = self.query_one("#overview-content", SectionContent)
            overview_content.update(self._render_overview())

            # Refresh acceptance criteria
            try:
                criteria_content = self.query_one("#criteria-content", SectionContent)
                criteria_content.update(self._render_criteria())
            except Exception:
                pass  # Section may not exist if no ACs

            # Refresh frozen header (task progress)
            try:
                header = self.query_one("#spec-header", Static)
                header.update(self._render_header())
            except Exception:
                pass

            self.notify("Spec updated", timeout=1)

            if self.is_follow_target:
                self.call_after_refresh(self._scroll_to_active_task)
        except Exception:
            pass

    def _scroll_to_tasks(self) -> None:
        """Scroll to the tasks section in follow mode."""
        if "tasks" in self.sections:
            self._scroll_to_active_task()

    def _scroll_to_active_task(self) -> None:
        """Scroll to position the active task 1/3 down the viewport."""
        try:
            scroll_container = self.query_one("#detail-scroll", VerticalScroll)
            active_task = self.query_one("#active-task", TaskRow)
            widget_y = self._virtual_y_within(active_task, scroll_container)
            if widget_y is None:
                raise ValueError("active task not in detail scroll container")

            viewport_height = (
                scroll_container.scrollable_content_region.height or scroll_container.size.height
            )
            context_lines = viewport_height // 3

            target_scroll_y = max(0, widget_y - context_lines)
            scroll_container.scroll_to(y=target_scroll_y, animate=True)
        except Exception:
            self._scroll_to_section("tasks")

    def _find_task_by_id(self, task_id: str):
        """Find a task by its ID in the IMPL task tree."""
        if not self.impl or not self.impl.tasks:
            return None

        def search_tree(tasks):
            for task in tasks:
                if task.id == task_id:
                    return task
                if task.children:
                    found = search_tree(task.children)
                    if found:
                        return found
            return None

        return search_tree(self.impl.tasks)

    def _animate_spinner(self) -> None:
        """Animate the spinner for the active task."""
        self.spinner_frame_idx = (self.spinner_frame_idx + 1) % len(self.SPINNER_FRAMES)
        try:
            active_task = self.query_one("#active-task", TaskRow)
            if active_task and self.first_pending_task_id:
                spinner_char = self.SPINNER_FRAMES[
                    self.spinner_frame_idx % len(self.SPINNER_FRAMES)
                ]
                task = self._find_task_by_id(self.first_pending_task_id)
                if task:
                    prefix = "│ "
                    child_hint = f" ({len(task.children)})" if task.children else ""
                    task_id_str = (
                        f"{task.id:>5}  " if task.id and not task.id.startswith("day") else ""
                    )
                    content = f"{prefix}{spinner_char} {task_id_str}{task.description}{child_hint}"
                    active_task.update(content)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        """Create the detail view layout."""
        yield Header()
        # Frozen header - stays in place while content scrolls
        yield Static(self._render_header(), id="spec-header")
        with VerticalScroll(id="detail-scroll"):
            self.sections.append("overview")
            yield SectionHeader("Overview", "overview", classes="section-header focused")
            yield SectionContent(
                self._render_overview(), id="overview-content", classes="section-content"
            )

            if self.fr and self.fr.ac_total > 0:
                self.sections.append("criteria")
                yield SectionHeader("Acceptance Criteria", "criteria", classes="section-header")
                yield SectionContent(
                    self._render_criteria(), id="criteria-content", classes="section-content"
                )

            if self.impl and self.impl.tasks:
                self.sections.append("tasks")
                yield SectionHeader("Implementation Tasks", "tasks", classes="section-header")
                with Vertical(id="tasks-content", classes="section-content"):
                    for task_row in self._compose_task_rows():
                        yield task_row

            if self.upstream_specs or self.downstream_specs:
                self.sections.append("deps")
                yield SectionHeader("Dependencies & Navigation", "deps", classes="section-header")
                yield SectionContent(
                    self._render_deps(), id="deps-content", classes="section-content"
                )

            if self.impl:
                self.sections.append("adr")
                yield SectionHeader("ADR / Execution Notes", "adr", classes="section-header")
                yield SectionContent(
                    self._render_adr(), id="adr-content", classes="section-content"
                )

        yield Footer()

    def _render_header(self) -> str:
        """Render the frozen spec header."""
        lines = []

        # Row 1: Spec ID + Title combined
        title = clean_title(self.fr.title) if self.fr else "Unknown Spec"
        lines.append(f"[bold]Spec {self.spec_id}:[/bold] {title}")

        # Row 2: Epic info
        epic_info = self._get_epic_info()
        if epic_info:
            epic_id, epic_title = epic_info
            lines.append(f"Epic {epic_id}: {epic_title}")
        elif self.fr:
            # Fallback: show FR/IMPL status if no epic found
            status = f"FR: {self.fr.status}"
            if self.impl:
                status += f" | IMPL: {self.impl.status}"
            lines.append(status)

        # Row 3: Task Progress
        if self.impl and self.impl.tasks_total > 0:
            lines.append(
                f"Tasks: {self.impl.tasks_completed}/{self.impl.tasks_total} ({self.impl.completion_percent}%)"
            )

        return "\n".join(lines)

    def _get_epic_info(self) -> tuple[str, str] | None:
        """Find the epic that contains this spec, return (epic_id, epic_title) or None."""
        if not self.data or not self.data.datasets:
            return None

        # Check all epics to see if this spec is one of their dependencies
        for epic_id, epic_fr in self.data.datasets.active_frs.items():
            # Epics have priority E0-E3
            if epic_fr.priority.startswith("E") and self.spec_id in epic_fr.deps:
                return (epic_id, clean_title(epic_fr.title))

        # Also check completed epics
        for epic_id, epic_fr in self.data.datasets.completed_frs.items():
            if epic_fr.priority.startswith("E") and self.spec_id in epic_fr.deps:
                return (epic_id, clean_title(epic_fr.title))

        return None

    def _render_overview(self) -> str:
        """Render the overview section."""
        lines = []

        if self.fr:
            lines.append(f"[bold]Priority:[/] {self.fr.priority}")
            lines.append(f"[bold]Type:[/] {self.fr.type}")
            lines.append(f"[bold]FR Status:[/] {self.fr.status}")

            if self.fr.ac_total > 0:
                lines.append(
                    f"[bold]AC Progress:[/] {self.fr.ac_completed}/{self.fr.ac_total} ({self.fr.ac_completion_percent}%)"
                )

        if self.impl:
            lines.append("")
            lines.append(f"[bold]IMPL Status:[/] {format_status(self.impl.status, verbose=True)}")
            lines.append(f"[bold]LOE:[/] {self.impl.effective_loe}")

            if self.impl.tasks_total > 0:
                lines.append(
                    f"[bold]Task Progress:[/] {self.impl.tasks_completed}/{self.impl.tasks_total} ({self.impl.completion_percent}%)"
                )

        return "\n".join(lines) if lines else "[dim]No overview data[/]"

    def _render_criteria(self) -> str:
        """Render acceptance criteria section."""
        if not self.fr:
            return "[dim]No acceptance criteria[/]"

        lines = []
        if hasattr(self.fr, "acceptance_criteria") and self.fr.acceptance_criteria:
            for ac in self.fr.acceptance_criteria:
                check = "[bold]✓[/]" if getattr(ac, "completed", False) else "[dim]○[/]"
                ac_id = getattr(ac, "id", "")
                ac_desc = getattr(ac, "description", str(ac))
                lines.append(f"{check} {ac_id}: {ac_desc}")
        else:
            lines.append(
                f"[bold]{self.fr.ac_completed}[/] of [bold]{self.fr.ac_total}[/] criteria completed"
            )
            lines.append(f"[dim]({self.fr.ac_completion_percent}% complete)[/]")

        return "\n".join(lines) if lines else "[dim]No acceptance criteria defined[/]"

    def _compose_task_rows(self) -> Generator[TaskRow]:
        """Yield TaskRow widgets for each task line."""
        if not self.impl or not self.impl.tasks:
            yield TaskRow("[dim]No tasks defined[/]")
            return

        active_task_id = self._select_active_task_id() if self.is_follow_target else None
        self.first_pending_task_id = active_task_id

        sections: dict[str, list] = {}
        for task in self.impl.tasks:
            section = task.section or "Tasks"
            if section not in sections:
                sections[section] = []
            sections[section].append(task)

        for section_name, tasks in sections.items():
            done = 0
            total = 0
            for t in tasks:
                c, tot = t.completion_status
                done += c
                total += tot
            progress = f"{done}/{total}"

            header = f"├─ {section_name} ({progress}) "
            header += "─" * max(1, 50 - len(section_name) - len(progress) - 8)
            yield TaskRow(header, state="chrome")

            yield from self._compose_task_tree(tasks, depth=0, active_task_id=active_task_id)

            yield TaskRow(f"└{'─' * 55}", state="chrome")
            yield TaskRow("")

    def _compose_task_tree(
        self,
        tasks: list,
        depth: int,
        active_task_id: str | None,
    ) -> Generator[TaskRow]:
        """Recursively yield TaskRow widgets for task tree."""
        for i, task in enumerate(tasks):
            is_last = i == len(tasks) - 1
            indent = "  " * depth

            if depth == 0:
                prefix = "│ "
            else:
                branch = "└─" if is_last else "├─"
                prefix = f"│ {indent}{branch} "

            is_active_task = (
                self.is_follow_target and active_task_id is not None and task.id == active_task_id
            )

            if task.delegated_to:
                check = f"->{task.delegated_to}"
                state = "delegated"
            elif task.completed:
                check = "✓"
                state = "complete"
            elif is_active_task:
                spinner_char = self.SPINNER_FRAMES[
                    self.spinner_frame_idx % len(self.SPINNER_FRAMES)
                ]
                check = spinner_char
                state = "active"
            else:
                check = "○"
                state = "pending"

            child_hint = f" ({len(task.children)})" if task.children else ""

            task_id_str = f"{task.id:>5}  " if task.id and not task.id.startswith("day") else ""

            content = f"{prefix}{check} {task_id_str}{task.description}{child_hint}"

            row_id = "active-task" if is_active_task else None
            yield TaskRow(
                content,
                task_id=task.id,
                is_active=is_active_task,
                state=state,
                id=row_id,
            )

            if task.children:
                yield from self._compose_task_tree(
                    task.children, depth + 1, active_task_id=active_task_id
                )

    def _render_deps(self) -> str:
        """Render dependencies section."""
        lines = []
        display_limit = None if self.show_all_deps else 5

        if self.upstream_specs:
            expand_hint = (
                " [dim](d=expand)[/]"
                if not self.show_all_deps and len(self.upstream_specs) > 5
                else ""
            )
            lines.append(f"[bold]Upstream[/] [dim](<- left arrow)[/]{expand_hint}")
            deps_to_show = (
                self.upstream_specs
                if display_limit is None
                else self.upstream_specs[:display_limit]
            )
            for i, dep_id in enumerate(deps_to_show, 1):
                key_hint = f"[dim][{i}][/] " if i <= 3 else "    "
                title = ""
                if self.data and self.data.datasets:
                    fr = self.data.datasets.get_fr(dep_id)
                    if not fr and dep_id in self.data.datasets.completed_frs:
                        fr = self.data.datasets.completed_frs[dep_id]
                    if fr:
                        title = f" - {clean_title(fr.title)[:40]}"
                lines.append(f"  {key_hint}[bold]{dep_id}[/]{title}")
            if display_limit and len(self.upstream_specs) > display_limit:
                lines.append(
                    f"  [dim]... +{len(self.upstream_specs) - display_limit} more (press 'd' to expand)[/]"
                )
        else:
            lines.append("[dim]No upstream dependencies[/]")

        lines.append("")

        if self.downstream_specs:
            lines.append("[bold]Downstream[/] [dim](-> right arrow)[/]")
            deps_to_show = (
                self.downstream_specs
                if display_limit is None
                else self.downstream_specs[:display_limit]
            )
            for dep_id in deps_to_show:
                title = ""
                if self.data and self.data.datasets:
                    fr = self.data.datasets.get_fr(dep_id)
                    if fr:
                        title = f" - {clean_title(fr.title)[:40]}"
                lines.append(f"  [bold]{dep_id}[/]{title}")
            if display_limit and len(self.downstream_specs) > display_limit:
                lines.append(
                    f"  [dim]... +{len(self.downstream_specs) - display_limit} more (press 'd' to expand)[/]"
                )
        else:
            lines.append("[dim]No downstream dependents[/]")

        return "\n".join(lines)

    def _render_adr(self) -> str:
        """Render ADR/execution notes section."""
        if not self.impl:
            return "[dim]No ADR or execution notes[/]"

        lines = []
        lines.append(
            "[dim]Architecture decisions and execution notes are stored in the IMPL file.[/]"
        )
        lines.append("")
        impl_dir_display = (
            str(self.data.paths.active_impls_dir) if self.data else "docs/impls/active"
        )
        lines.append(f"[bold]File:[/] {impl_dir_display}/IMPL-{self.spec_id}-*.md")

        return "\n".join(lines)

    def action_close(self) -> None:
        """Close the detail view."""
        self.app.pop_screen()

    def key_escape(self) -> None:
        """Handle escape key directly."""
        self.app.pop_screen()

    def action_next_section(self) -> None:
        """Move to next section."""
        if not self.sections:
            return
        self._update_section_focus(self.current_section_idx, focused=False)
        self.current_section_idx = (self.current_section_idx + 1) % len(self.sections)
        self._update_section_focus(self.current_section_idx, focused=True)
        self._scroll_to_section(self.sections[self.current_section_idx])

    def action_prev_section(self) -> None:
        """Move to previous section."""
        if not self.sections:
            return
        self._update_section_focus(self.current_section_idx, focused=False)
        self.current_section_idx = (self.current_section_idx - 1) % len(self.sections)
        self._update_section_focus(self.current_section_idx, focused=True)
        self._scroll_to_section(self.sections[self.current_section_idx])

    def action_toggle_section(self) -> None:
        """Toggle current section expanded/collapsed."""
        if not self.sections:
            return

        section_id = self.sections[self.current_section_idx]
        content_id = f"{section_id}-content"

        try:
            content = self.query_one(f"#{content_id}", SectionContent)
            headers = list(self.query(".section-header").results(SectionHeader))

            for header in headers:
                if header.section_id == section_id:
                    expanded = header.toggle()
                    if expanded:
                        content.remove_class("collapsed")
                    else:
                        content.add_class("collapsed")
                    break
        except Exception:
            pass

    def _update_section_focus(self, idx: int, focused: bool) -> None:
        """Update visual focus state for a section header."""
        if idx >= len(self.sections):
            return

        section_id = self.sections[idx]
        try:
            headers = list(self.query(".section-header").results(SectionHeader))
            for header in headers:
                if header.section_id == section_id:
                    if focused:
                        header.add_class("focused")
                    else:
                        header.remove_class("focused")
                    break
        except Exception:
            pass

    def _scroll_to_section(self, section_id: str) -> None:
        """Scroll to position section 1/3 down the viewport."""
        try:
            scroll_container = self.query_one("#detail-scroll", VerticalScroll)
            headers = list(self.query(".section-header").results(SectionHeader))
            for header in headers:
                if header.section_id == section_id:
                    viewport_height = (
                        scroll_container.scrollable_content_region.height
                        or scroll_container.size.height
                    )
                    widget_y = header.virtual_region.y
                    target_scroll_y = max(0, widget_y - (viewport_height // 3))
                    scroll_container.scroll_to(y=target_scroll_y, animate=True)
                    break
        except Exception:
            pass

    def action_go_upstream(self) -> None:
        """Navigate to first upstream dependency."""
        if not self.upstream_specs:
            self.notify("No upstream dependencies", timeout=1)
            return
        self._navigate_to_spec(self.upstream_specs[0])

    def action_go_downstream(self) -> None:
        """Navigate to first downstream dependent."""
        if not self.downstream_specs:
            self.notify("No downstream dependents", timeout=1)
            return
        self._navigate_to_spec(self.downstream_specs[0])

    def action_jump_dep_1(self) -> None:
        """Jump to first dependency."""
        if self.upstream_specs:
            self._navigate_to_spec(self.upstream_specs[0])

    def action_jump_dep_2(self) -> None:
        """Jump to second dependency."""
        if len(self.upstream_specs) > 1:
            self._navigate_to_spec(self.upstream_specs[1])

    def action_jump_dep_3(self) -> None:
        """Jump to third dependency."""
        if len(self.upstream_specs) > 2:
            self._navigate_to_spec(self.upstream_specs[2])

    def action_copy_uri(self) -> None:
        """Copy spec URI to clipboard."""
        uri = f"praxis://impl/{self.spec_id}"
        self._copy_to_clipboard(uri)
        self.notify(f"Copied: {uri}", timeout=2)

    def action_goto_uri(self) -> None:
        """Navigate to URI from clipboard."""
        from nspec.tasks import find_similar_paths, parse_uri, resolve_path

        uri = self._read_from_clipboard()
        if not uri:
            self.notify("Clipboard empty or not accessible", severity="warning", timeout=2)
            return

        uri = uri.strip()
        if not uri.startswith("praxis://"):
            self.notify(f"Not a praxis:// URI: {uri[:30]}...", severity="warning", timeout=2)
            return

        spec_id, path = parse_uri(uri)
        if not spec_id:
            self.notify("Invalid URI format", severity="error", timeout=2)
            return

        if spec_id != self.spec_id:
            self._navigate_to_spec(spec_id)
            self.notify(f"Navigated to spec {spec_id}", timeout=2)
            return

        if path and self.impl and self.impl.tasks:
            task = resolve_path(self.impl.tasks, path)
            if task:
                self.notify(f"Found: {task.description[:40]}...", timeout=2)
            else:
                suggestions = find_similar_paths(self.impl.tasks, path, max_results=3)
                if suggestions:
                    self.notify(
                        f"Not found. Did you mean: {suggestions[0]}?", severity="warning", timeout=3
                    )
                else:
                    self.notify(f"Path not found: {path}", severity="warning", timeout=2)
        else:
            self.notify(f"Already viewing spec {spec_id}", timeout=2)

    def _read_from_clipboard(self) -> str | None:
        """Read text from system clipboard."""
        try:
            proc = subprocess.run(["pbpaste"], capture_output=True, timeout=2)
            if proc.returncode == 0:
                return proc.stdout.decode("utf-8")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        try:
            proc = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"], capture_output=True, timeout=2
            )
            if proc.returncode == 0:
                return proc.stdout.decode("utf-8")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return None

    def _copy_to_clipboard(self, text: str) -> bool:
        """Copy text to system clipboard."""
        try:
            proc = subprocess.run(["pbcopy"], input=text.encode(), capture_output=True, timeout=2)
            if proc.returncode == 0:
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        try:
            proc = subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text.encode(),
                capture_output=True,
                timeout=2,
            )
            if proc.returncode == 0:
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return False

    def action_mark_task_complete(self) -> None:
        """Mark the first pending task as complete."""
        self._mark_task_with_marker("x", "complete")

    def action_mark_task_obsolete(self) -> None:
        """Mark the first pending task as obsolete."""
        self._mark_task_with_marker("~", "obsolete")

    def _mark_task_with_marker(self, marker: str, marker_desc: str) -> None:
        """Mark the first pending task with given marker."""
        if not self.first_pending_task_id:
            self.notify("No pending tasks to mark", severity="warning", timeout=2)
            return

        task_id = self.first_pending_task_id

        # Accept numeric IDs (1.1, 2.3) or dod-N format
        is_numeric = re.match(r"^\d+(\.\d+)+$", task_id)
        is_dod = re.match(r"^dod-\d+$", task_id, re.IGNORECASE)
        if task_id.startswith("day") or (not is_numeric and not is_dod):
            self.notify(
                f"Task {task_id} not in supported format (e.g., 1.1 or dod-1). Use MCP tool directly.",
                severity="warning",
                timeout=3,
            )
            return

        docs_root = Path("docs")

        try:
            check_impl_task(self.spec_id, task_id, docs_root, marker)
            self.notify(f"v Task {task_id} marked {marker_desc}", timeout=2)
            self._refresh_spec_data()

        except FileNotFoundError as e:
            self.notify(f"IMPL not found: {e}", severity="error", timeout=3)
        except ValueError as e:
            self.notify(f"Error: {e}", severity="error", timeout=3)
        except Exception as e:
            self.notify(f"Failed: {e}", severity="error", timeout=3)

    def action_toggle_deps(self) -> None:
        """Toggle between collapsed (5) and expanded (all) dependencies view."""
        self.show_all_deps = not self.show_all_deps
        try:
            deps_content = self.query_one("#deps-content", SectionContent)
            deps_content.update(self._render_deps())
            state = "expanded" if self.show_all_deps else "collapsed"
            self.notify(f"Dependencies {state}", timeout=1)
        except Exception:
            pass

    def action_copy_spec(self) -> None:
        """Copy formatted spec details to clipboard."""
        lines = []

        # Header
        title = clean_title(self.fr.title) if self.fr else "Unknown Spec"
        lines.append(f"Spec {self.spec_id}: {title}")

        # Epic info
        epic_info = self._get_epic_info()
        if epic_info:
            epic_id, epic_title = epic_info
            lines.append(f"Epic: {epic_id} - {epic_title}")

        # Status
        if self.fr:
            status = f"Status: FR {self.fr.status}"
            if self.impl:
                status += f" | IMPL {self.impl.status}"
            lines.append(status)

        # Task progress
        if self.impl and self.impl.tasks_total > 0:
            lines.append(
                f"Tasks: {self.impl.tasks_completed}/{self.impl.tasks_total} ({self.impl.completion_percent}%)"
            )

        # Dependencies
        if self.upstream_specs:
            lines.append("")
            lines.append("Dependencies:")
            for dep_id in self.upstream_specs:
                dep_title = ""
                if self.data and self.data.datasets:
                    fr = self.data.datasets.get_fr(dep_id)
                    if not fr and dep_id in self.data.datasets.completed_frs:
                        fr = self.data.datasets.completed_frs[dep_id]
                    if fr:
                        dep_title = f": {clean_title(fr.title)[:50]}"
                lines.append(f"- {dep_id}{dep_title}")

        text = "\n".join(lines)
        if self._copy_to_clipboard(text):
            self.notify("Spec details copied to clipboard", timeout=2)
        else:
            self.notify("Failed to copy to clipboard", severity="warning", timeout=2)

    def action_copy_epic(self) -> None:
        """Copy formatted epic summary with all specs to clipboard."""
        epic_info = self._get_epic_info()
        if not epic_info:
            self.notify("Spec is not part of an epic", severity="warning", timeout=2)
            return

        epic_id, epic_title = epic_info
        if not self.data or not self.data.datasets:
            self.notify("No nspec data available", severity="warning", timeout=2)
            return

        # Get epic FR
        epic_fr = self.data.datasets.get_fr(epic_id)
        if not epic_fr:
            self.notify(f"Epic {epic_id} not found", severity="warning", timeout=2)
            return

        lines = []
        lines.append(f"Epic {epic_id}: {epic_title}")
        lines.append(
            f"Priority: {epic_fr.priority} | Specs: {len(epic_fr.deps) if epic_fr.deps else 0}"
        )

        # Calculate progress
        total_tasks = 0
        completed_tasks = 0
        if epic_fr.deps:
            for spec_id in epic_fr.deps:
                impl = self.data.datasets.get_impl(spec_id)
                if not impl and spec_id in self.data.datasets.completed_impls:
                    impl = self.data.datasets.completed_impls[spec_id]
                if impl:
                    total_tasks += impl.tasks_total
                    completed_tasks += impl.tasks_completed

        if total_tasks > 0:
            progress = int(completed_tasks / total_tasks * 100)
            lines[1] += f" | Progress: {progress}%"

        # Specs list
        if epic_fr.deps:
            lines.append("")
            lines.append("Specs:")
            for spec_id in epic_fr.deps:
                spec_fr = self.data.datasets.get_fr(spec_id)
                is_completed = False
                if not spec_fr:
                    if spec_id in self.data.datasets.completed_frs:
                        spec_fr = self.data.datasets.completed_frs[spec_id]
                        is_completed = True

                if spec_fr:
                    spec_title = clean_title(spec_fr.title)[:50]
                    check = "[x]" if is_completed else "[ ]"
                    status = "Completed" if is_completed else spec_fr.status
                    lines.append(f"- {check} {spec_id}: {spec_title} ({status})")
                else:
                    lines.append(f"- [ ] {spec_id}: (not found)")

        text = "\n".join(lines)
        if self._copy_to_clipboard(text):
            self.notify("Epic summary copied to clipboard", timeout=2)
        else:
            self.notify("Failed to copy to clipboard", severity="warning", timeout=2)

    def action_toggle_footer(self) -> None:
        """Toggle between normal and extended footer bindings."""
        # Footer toggle not implemented with built-in Footer
        pass
