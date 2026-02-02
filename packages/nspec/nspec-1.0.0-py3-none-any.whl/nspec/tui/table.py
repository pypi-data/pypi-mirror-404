"""NspecTable widget for the Nspec TUI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from textual.message import Message
from textual.widgets import DataTable

from nspec.statuses import (
    DepDisplayEmoji,
    EpicDisplayEmoji,
    get_dep_display_emoji,
    parse_status_text,
)

from .utils import clean_title, format_status

if TYPE_CHECKING:
    from .state import NspecData

# Fixed column widths - all columns except Title have explicit widths
FIXED_COL_WIDTHS = {
    "id": 5,
    "priority": 3,
    "status": 3,
    "upstream": 16,  # emoji(2)+id(3)+comma(1)+emoji(2)+id(3)+badge(5) = 16
    "downstream": 16,
    "estimate": 5,
}
FIXED_COLS_TOTAL = sum(FIXED_COL_WIDTHS.values())  # 48
TABLE_OVERHEAD = 20  # borders(4) + column padding (7 cols × 2 = 14) + scrollbar(2)
MIN_TITLE_WIDTH = 25  # Title won't shrink below this


class NspecTable(DataTable):
    """Custom DataTable for nspec display."""

    class SpecSelected(Message):
        """Message sent when a spec is selected."""

        def __init__(self, spec_id: str) -> None:
            """Initialize with spec ID."""
            super().__init__()
            self.spec_id = spec_id

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize nspec table."""
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True

    def populate(
        self,
        data: NspecData,
        search_query: str = "",
        epic_filter: str | None = None,
        viewport_width: int = 120,
    ) -> int:
        """Populate table with nspec data. Returns row count."""
        self.clear(columns=True)

        if not data.datasets:
            return 0

        epic_scope: set[str] | None = None
        completed_in_epic: list[str] = []
        if epic_filter and not search_query:
            epic_scope, completed_in_epic = self._get_epic_scope_with_completed(data, epic_filter)

        search_lower = search_query.lower()

        # Collect spec data - title auto-expands so no truncation needed
        spec_data: list[tuple[str, str, str, str, str, str, str]] = []
        seen_ids: set[str] = set()  # Track IDs to avoid duplicates

        for spec_id in data.ordered_specs:
            if epic_scope is not None and spec_id not in epic_scope:
                continue

            fr = data.datasets.get_fr(spec_id)
            impl = data.datasets.get_impl(spec_id)

            if not fr:
                continue

            title = clean_title(fr.title)
            if search_query:
                searchable = f"{spec_id} {title} {fr.priority}".lower()
                if search_lower not in searchable:
                    continue

            deps_str = self._format_deps(data, fr.deps)
            dependents_str = self._format_dependents(data, spec_id)
            status_str = format_status(impl.status if impl else fr.status)
            estimate = impl.effective_loe if impl else "TBD"

            spec_data.append(
                (spec_id, fr.priority, status_str, title, deps_str, dependents_str, estimate)
            )
            seen_ids.add(spec_id)

        # Add completed specs when filtering by epic (no search)
        if epic_filter and completed_in_epic and not search_query:
            for spec_id in completed_in_epic:
                fr = data.datasets.completed_frs.get(spec_id)
                impl = data.datasets.completed_impls.get(spec_id)

                if not fr:
                    continue

                title = clean_title(fr.title)
                status_str = "✅"
                estimate = impl.effective_loe if impl else "—"
                spec_data.append(
                    (spec_id, fr.priority, status_str, title, "", "", estimate)
                )  # No deps for completed

        # Search completed specs when there's a search query
        if search_query:
            for spec_id, fr in data.datasets.completed_frs.items():
                if spec_id in seen_ids:  # Skip duplicates
                    continue

                title = clean_title(fr.title)
                searchable = f"{spec_id} {title} {fr.priority}".lower()
                if search_lower not in searchable:
                    continue

                impl = data.datasets.completed_impls.get(spec_id)
                status_str = "✅"
                estimate = impl.effective_loe if impl else "—"
                spec_data.append((spec_id, fr.priority, status_str, title, "", "", estimate))

        # Show all completed specs when no epic filter and no search query.
        # This keeps "All Specs" consistent with epic views, which include completed specs.
        if not epic_filter and not search_query:
            for spec_id in sorted(data.datasets.completed_frs.keys()):
                if spec_id in seen_ids:
                    continue
                fr = data.datasets.completed_frs.get(spec_id)
                if not fr:
                    continue
                title = clean_title(fr.title)
                impl = data.datasets.completed_impls.get(spec_id)
                status_str = "✅"
                estimate = impl.effective_loe if impl else "—"
                spec_data.append((spec_id, fr.priority, status_str, title, "", "", estimate))

        # Calculate title width from available space (viewport - fixed cols - overhead)
        title_width = max(MIN_TITLE_WIDTH, viewport_width - FIXED_COLS_TOTAL - TABLE_OVERHEAD)

        # Build final rows - apply dim styling for completed specs and truncate titles
        def truncate_title(t: str, max_len: int) -> str:
            """Truncate title to max length with ellipsis."""
            if len(t) <= max_len:
                return t
            return t[: max_len - 1] + "…"

        rows: list[tuple[str, str, str, str, str, str, str]] = []
        for spec_id, priority, status_str, title, deps_str, dependents_str, estimate in spec_data:
            truncated = truncate_title(title, title_width)
            display_title = f"[dim]{truncated}[/]" if status_str == "✅" else truncated
            rows.append(
                (spec_id, priority, status_str, display_title, deps_str, dependents_str, estimate)
            )

        # Add columns - Title width calculated from available space
        self.add_column("ID", key="id", width=FIXED_COL_WIDTHS["id"])
        self.add_column("Pr", key="priority", width=FIXED_COL_WIDTHS["priority"])
        self.add_column("St", key="status", width=FIXED_COL_WIDTHS["status"])
        self.add_column("Title", key="title", width=title_width)
        self.add_column("Upstream", key="deps", width=FIXED_COL_WIDTHS["upstream"])
        self.add_column("Downstream", key="dependents", width=FIXED_COL_WIDTHS["downstream"])
        self.add_column("Est", key="estimate", width=FIXED_COL_WIDTHS["estimate"])

        # Add rows
        for spec_id, priority, status_str, title, deps_str, dependents_str, estimate in rows:
            self.add_row(
                spec_id,
                priority,
                status_str,
                title,
                deps_str,
                dependents_str,
                estimate,
                key=spec_id,
            )

        return len(rows)

    def _get_epic_scope(self, data: NspecData, epic_id: str) -> set[str]:
        """Get the epic and its direct dependencies (no transitive traversal).

        Specs should only appear under their direct parent epic,
        not under grandparent epics.
        """
        result = {epic_id}
        fr = data.datasets.get_fr(epic_id) if data.datasets else None
        if fr and fr.deps:
            result.update(fr.deps)
        return result

    def _get_epic_scope_with_completed(
        self, data: NspecData, epic_id: str
    ) -> tuple[set[str], list[str]]:
        """Get epic scope split into active and completed specs.

        Returns:
            Tuple of (active_scope set, completed_specs list)
        """
        active_scope = {epic_id}
        completed_specs: list[str] = []

        fr = data.datasets.get_fr(epic_id) if data.datasets else None
        if fr and fr.deps:
            for dep_id in fr.deps:
                if data.datasets and dep_id in data.datasets.completed_frs:
                    completed_specs.append(dep_id)
                else:
                    active_scope.add(dep_id)

        return active_scope, completed_specs

    def _format_deps(self, data: NspecData, deps: list[str]) -> str:
        """Format dependencies with status emoji prefix."""
        if not deps or not data.datasets:
            return ""

        def is_superseded(dep_id: str) -> bool:
            dep_fr = data.datasets.active_frs.get(dep_id) if data.datasets else None
            return dep_fr is not None and "superseded" in dep_fr.status.lower()

        filtered_deps = [d for d in deps if not is_superseded(d)]
        if not filtered_deps:
            return ""

        nspec_order = {sid: idx for idx, sid in enumerate(data.ordered_specs)}

        def dep_sort_key(dep_id: str) -> tuple[int, int, str]:
            if data.datasets and dep_id in data.datasets.completed_frs:
                return (0, 0, dep_id)
            elif dep_id in nspec_order:
                return (1, nspec_order[dep_id], dep_id)
            else:
                return (2, 9999, dep_id)

        sorted_deps = sorted(filtered_deps, key=dep_sort_key)[:2]

        def format_single_dep(dep_id: str) -> str:
            if data.datasets and dep_id in data.datasets.completed_frs:
                return f"{DepDisplayEmoji.COMPLETED}{dep_id}"
            elif data.datasets and dep_id in data.datasets.active_frs:
                dep_fr = data.datasets.active_frs[dep_id]
                if dep_fr.priority.startswith("E"):
                    emoji = self._get_epic_status_emoji(data, dep_id)
                    return f"{emoji}{dep_id}"
                emoji = get_dep_display_emoji(dep_fr.status)
                return f"{emoji}{dep_id}"
            else:
                return dep_id

        formatted = [format_single_dep(dep_id) for dep_id in sorted_deps]
        result = ",".join(formatted)
        if len(filtered_deps) > 2:
            result += f" [bold]+{len(filtered_deps) - 2}[/]"
        return result

    def _format_dependents(self, data: NspecData, spec_id: str) -> str:
        """Format specs that depend on this spec."""
        dependents = data.reverse_deps.get(spec_id, [])
        if not dependents:
            return ""

        nspec_order = {sid: idx for idx, sid in enumerate(data.ordered_specs)}

        def dep_sort_key(dep_id: str) -> tuple[int, int, str]:
            if dep_id in nspec_order:
                return (0, nspec_order[dep_id], dep_id)
            else:
                return (1, 9999, dep_id)

        sorted_dependents = sorted(dependents, key=dep_sort_key)[:2]

        def format_single_dependent(dep_id: str) -> str:
            if data.datasets:
                dep_fr = data.datasets.active_frs.get(dep_id)
                if dep_fr:
                    if dep_fr.priority.startswith("E"):
                        emoji = self._get_epic_status_emoji(data, dep_id)
                        return f"{emoji}{dep_id}"
                    emoji = get_dep_display_emoji(dep_fr.status)
                    return f"{emoji}{dep_id}"
            return dep_id

        formatted = [format_single_dependent(dep_id) for dep_id in sorted_dependents]
        result = ",".join(formatted)
        if len(dependents) > 2:
            result += f" [bold]+{len(dependents) - 2}[/]"
        return result

    def _get_epic_status_emoji(self, data: NspecData, epic_id: str) -> str:
        """Calculate epic status from its dependencies."""
        if not data.datasets:
            return EpicDisplayEmoji.PROPOSED

        epic_fr = data.datasets.active_frs.get(epic_id)
        if not epic_fr or not epic_fr.deps:
            return EpicDisplayEmoji.PROPOSED

        has_active = False
        all_completed = True

        for dep_id in epic_fr.deps:
            if dep_id in data.datasets.completed_frs:
                continue
            all_completed = False
            dep_fr = data.datasets.active_frs.get(dep_id)
            if dep_fr:
                status_text = parse_status_text(dep_fr.status)
                if status_text in ("active", "testing"):
                    has_active = True

        if all_completed and epic_fr.deps:
            return EpicDisplayEmoji.COMPLETED
        elif has_active:
            return EpicDisplayEmoji.ACTIVE
        else:
            return EpicDisplayEmoji.PROPOSED

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        if event.row_key:
            self.post_message(self.SpecSelected(str(event.row_key.value)))
