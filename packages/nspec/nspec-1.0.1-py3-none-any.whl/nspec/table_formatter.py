"""Table Formatter - Nspec table rendering for CLI display.

Extracted from cli.py to reduce module size and improve maintainability.
"""

import re
import unicodedata
from typing import Any

from nspec.datasets import NspecDatasets
from nspec.statuses import (
    ALL_PRIORITIES,
    DepDisplayEmoji,
    EpicDisplayEmoji,
    get_all_status_emojis,
    get_dep_display_emoji,
    get_status_emoji_fallback,
    get_status_emoji_pattern,
    get_status_legend,
    parse_status_text,
)


class NspecTableFormatter:
    """Formats nspec data as a terminal table."""

    def __init__(
        self,
        datasets: NspecDatasets,
        ordered_active_specs: list[str],
        verbose_status: bool = False,
        epic_filter: str | None = None,
    ):
        """Initialize formatter.

        Args:
            datasets: Loaded nspec datasets
            ordered_active_specs: Pre-computed ordered list of spec IDs
            verbose_status: If True, show full status text instead of emoji only
            epic_filter: If set, only show this epic and its dependencies
        """
        self.datasets = datasets
        self.ordered_active_specs = ordered_active_specs
        self.verbose_status = verbose_status
        self.epic_filter = epic_filter
        self._status_emoji_fallback = get_status_emoji_fallback()

    def show_stats(self, show_calendar: bool = True) -> None:
        """Show nspec statistics and table.

        Args:
            show_calendar: If True, show the activity heatmap and velocity stats.
                          If False, just show the table (cleaner for daily use).
        """
        # Show velocity calendar only when requested
        if show_calendar:
            import os
            from pathlib import Path

            from nspec.velocity import render_compact_chart

            # Determine which repos to include
            include_all = os.environ.get("NSPEC_ALL_REPOS", "false").lower() == "true"

            if include_all:
                # Load repos from projects.txt
                repos = [Path(".")]
                projects_file = Path("projects.txt")
                if projects_file.exists():
                    parent = Path("..").resolve()
                    for line in projects_file.read_text().splitlines():
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        repo_path = Path(line) if line.startswith("/") else parent / line
                        if repo_path.exists() and (repo_path / ".git").exists():
                            repos.append(repo_path)
            else:
                repos = [Path(".")]

            calendar_lines = render_compact_chart(repos, use_color=True, show_best_run=True)

            if calendar_lines:
                for line in calendar_lines:
                    print(line)
                print()

        # Show status legend
        print(get_status_legend())
        print()

        # Show epic filter indicator if active
        if self.epic_filter:
            fr = self.datasets.get_fr(self.epic_filter)
            title = fr.title.split(": ", 1)[-1] if fr else f"Spec {self.epic_filter}"
            filter_emoji = ALL_PRIORITIES.get("P1", ALL_PRIORITIES.get("P2")).emoji
            print(f"{filter_emoji} Filtered: Epic {self.epic_filter} - {title}")
            print()

        # Show table of active specs
        table_output = self._format_table()
        table_lines = table_output.split("\n")
        if table_lines:
            table_width = (
                max(len(line) for line in table_lines[:2]) if len(table_lines) >= 2 else 80
            )
            print("-" * (table_width - 2))
            print(table_output)

    def _format_table(self) -> str:
        """Format active specs as clean table with compact spacing."""

        def extract_emoji_and_text(status: str) -> tuple[str, str]:
            """Extract emoji and text from status string."""
            match = re.match(get_status_emoji_pattern(), status)
            if match:
                emoji = match.group(1)
                text = status[len(match.group(0)) :].strip()
                return emoji, text
            return "", status.strip()

        def clean_status(status: str) -> str:
            """Extract status text without emoji."""
            _, text = extract_emoji_and_text(status)
            text = text.replace("in progress", "active").replace("in-progress", "active")
            return text.strip().lower()

        def format_status(status: str, priority: str = "") -> str:
            """Format status with emoji prefix."""
            emoji, text = extract_emoji_and_text(status)

            if not emoji:
                status_clean = clean_status(status)
                emoji = self._status_emoji_fallback.get(status_clean, "")
                text = status_clean

            # Compact mode: emoji only (default)
            if not self.verbose_status:
                return emoji if emoji else text

            return f"{emoji} {text}" if emoji else text

        def clean_title(title: str) -> str:
            """Remove redundant prefixes and clean title."""
            title = re.sub(r"^Spec\s+\d+[a-z]?:\s+", "", title)
            title = re.sub(r"^FR-\d+[a-z]?:\s+", "", title, flags=re.IGNORECASE)
            title = re.sub(r"^Feature Request:\s+", "", title, flags=re.IGNORECASE)
            title = re.sub(rf"[{get_all_status_emojis()}]", "", title)
            return title.strip()

        def get_display_width(text: str) -> int:
            """Calculate actual terminal display width."""
            ansi_pattern = re.compile(r"\033\[[0-9;]*m")
            clean_text = ansi_pattern.sub("", text)

            width = 0
            for char in clean_text:
                if unicodedata.east_asian_width(char) in ("F", "W"):
                    width += 2
                else:
                    width += 1
            return width

        def clean_estimate(raw: str | None) -> str:
            """Normalize estimate values and drop leading '~'."""
            if raw is None:
                return "TBD"
            value = str(raw).strip()
            if value.startswith("~"):
                value = value[1:].strip()
            return value or "TBD"

        def wrap_estimate(estimate: str) -> list[str]:
            """Split comma-separated estimates into separate lines."""
            if not estimate or estimate == "TBD":
                return [estimate]

            parts = [part.strip() for part in estimate.split(",") if part.strip()]
            seen = set()
            unique_parts = []
            for part in parts:
                if part not in seen:
                    seen.add(part)
                    unique_parts.append(part)
            return unique_parts if unique_parts else [estimate]

        def pad_text(text: str, width: int, align: str = "left") -> str:
            """Pad text to a specific display width."""
            text = text or ""
            display_width = get_display_width(text)
            if display_width >= width:
                return text

            pad_len = width - display_width
            if align == "right":
                return " " * pad_len + text
            if align == "center":
                left = pad_len // 2
                right = pad_len - left
                return (" " * left) + text + (" " * right)
            return text + (" " * pad_len)

        def get_epic_status_emoji(epic_id: str) -> str:
            """Calculate epic status from its dependencies."""
            epic_fr = self.datasets.active_frs.get(epic_id)
            if not epic_fr or not epic_fr.deps:
                return EpicDisplayEmoji.PROPOSED

            has_active = False
            all_completed = True

            for dep_id in epic_fr.deps:
                if dep_id in self.datasets.completed_frs:
                    continue
                all_completed = False
                dep_fr = self.datasets.active_frs.get(dep_id)
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

        def format_deps(deps: list[str]) -> str:
            """Format dependencies with status emoji prefix."""
            if not deps:
                return ""

            def is_superseded(dep_id: str) -> bool:
                dep_fr = self.datasets.active_frs.get(dep_id)
                return dep_fr and "superseded" in dep_fr.status.lower()

            filtered_deps = [d for d in deps if not is_superseded(d)]
            if not filtered_deps:
                return ""

            nspec_order = {sid: idx for idx, sid in enumerate(self.ordered_active_specs)}

            def dep_sort_key(dep_id: str) -> tuple[int, int, str]:
                if dep_id in self.datasets.completed_frs:
                    return (0, 0, dep_id)
                elif dep_id in nspec_order:
                    return (1, nspec_order[dep_id], dep_id)
                else:
                    return (2, 9999, dep_id)

            sorted_deps = sorted(filtered_deps, key=dep_sort_key)

            def format_single_dep(dep_id: str) -> str:
                if dep_id in self.datasets.completed_frs:
                    return f"{DepDisplayEmoji.COMPLETED}{dep_id}"
                elif dep_id in self.datasets.active_frs:
                    dep_fr = self.datasets.active_frs[dep_id]
                    if dep_fr.type == "Epic":
                        emoji = get_epic_status_emoji(dep_id)
                        return f"{emoji}{dep_id}"
                    emoji = get_dep_display_emoji(dep_fr.status)
                    return f"{emoji}{dep_id}"
                else:
                    return dep_id

            formatted = [format_single_dep(dep_id) for dep_id in sorted_deps]
            return ",".join(formatted)

        # Build reverse dependency map
        reverse_deps: dict[str, list[str]] = {}
        for spec_id, fr in self.datasets.active_frs.items():
            for dep_id in fr.deps:
                if dep_id not in reverse_deps:
                    reverse_deps[dep_id] = []
                reverse_deps[dep_id].append(spec_id)

        def format_dependents(spec_id: str) -> str:
            """Format specs that depend on this spec."""
            dependents = reverse_deps.get(spec_id, [])
            if not dependents:
                return ""

            nspec_order = {sid: idx for idx, sid in enumerate(self.ordered_active_specs)}

            def dep_sort_key(dep_id: str) -> tuple[int, int, str]:
                if dep_id in nspec_order:
                    return (0, nspec_order[dep_id], dep_id)
                else:
                    return (1, 9999, dep_id)

            sorted_dependents = sorted(dependents, key=dep_sort_key)

            def format_single_dependent(dep_id: str) -> str:
                dep_fr = self.datasets.active_frs.get(dep_id)
                if dep_fr:
                    if dep_fr.type == "Epic":
                        emoji = get_epic_status_emoji(dep_id)
                        return f"{emoji}{dep_id}"
                    emoji = get_dep_display_emoji(dep_fr.status)
                    return f"{emoji}{dep_id}"
                else:
                    return dep_id

            formatted = [format_single_dependent(dep_id) for dep_id in sorted_dependents]
            return ",".join(formatted)

        def wrap_deps(deps_str: str, width: int, max_tokens: int) -> list[str]:
            """Wrap dependencies at comma boundaries."""
            if not deps_str:
                return [""]

            parts = deps_str.split(",")
            lines: list[str] = []
            current_parts: list[str] = []

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                candidate_parts = current_parts + [part]
                candidate = ",".join(candidate_parts)
                if current_parts and (
                    len(current_parts) >= max_tokens or get_display_width(candidate) > width
                ):
                    lines.append(",".join(current_parts))
                    current_parts = [part]
                else:
                    current_parts = candidate_parts

            if current_parts:
                lines.append(",".join(current_parts))

            return lines or [""]

        # Build normalized rows
        rows: list[dict[str, Any]] = []

        # Filter by epic if specified
        epic_scope: set[str] | None = None
        if self.epic_filter:
            epic_scope = self._get_epic_scope(self.epic_filter)

        for spec_id in self.ordered_active_specs:
            if epic_scope is not None and spec_id not in epic_scope:
                continue

            fr = self.datasets.get_fr(spec_id)
            impl = self.datasets.get_impl(spec_id)
            if not fr:
                continue
            estimate = clean_estimate(impl.effective_loe if impl else None)
            display_status = impl.status if impl else fr.status
            rows.append(
                {
                    "id": spec_id,
                    "priority": fr.priority or "",
                    "deps": format_deps(fr.deps),
                    "dependents": format_dependents(spec_id),
                    "status": format_status(display_status, fr.priority or ""),
                    "estimate": estimate,
                    "title": clean_title(fr.title),
                    "is_epic": fr.type == "Epic",
                }
            )

        if not rows:
            return "No active specs"

        # Determine column widths
        max_deps_width = 17
        max_deps_per_line = 3
        priority_header = "Pr"
        width_id = max(len("ID"), max(get_display_width(row["id"]) for row in rows))
        width_pri = max(
            2, len(priority_header), max(get_display_width(row["priority"]) for row in rows)
        )
        width_status = max(len("Status"), max(get_display_width(row["status"]) for row in rows))
        width_est = max(len("Est"), max(get_display_width(row["estimate"]) for row in rows))

        for row in rows:
            row["deps_lines"] = wrap_deps(row["deps"], max_deps_width, max_deps_per_line)
            row["dependents_lines"] = wrap_deps(
                row["dependents"], max_deps_width, max_deps_per_line
            )
            row["estimate_lines"] = wrap_estimate(row["estimate"])

        deps_line_lengths = [
            get_display_width(line) for row in rows for line in row.get("deps_lines", [""])
        ]
        width_deps = max(len("Upstream"), min(max_deps_width, max(deps_line_lengths or [0])))

        dependents_line_lengths = [
            get_display_width(line) for row in rows for line in row.get("dependents_lines", [""])
        ]
        width_dependents = max(
            len("Downstream"), min(max_deps_width, max(dependents_line_lengths or [0]))
        )

        estimate_line_lengths = [
            get_display_width(line) for row in rows for line in row.get("estimate_lines", [""])
        ]
        width_est = max(len("Est"), max(estimate_line_lengths or [0]))

        # ANSI codes for formatting
        ROW_EVEN = ""
        ROW_ODD = "\033[48;5;236m"
        ROW_EPIC = "\033[48;5;22m"
        RESET = "\033[0m"
        HEADER_STYLE = "\033[1;37m"

        separator = " | "
        header_parts = [
            pad_text("ID", width_id, "right"),
            pad_text(priority_header, width_pri, "right"),
            pad_text("St", width_status, "left"),
            pad_text("Upstream", width_deps, "left"),
            pad_text("Downstream", width_dependents, "left"),
            pad_text("Est", width_est, "right"),
            "Title",
        ]
        header = separator.join(header_parts)
        header_line = f"{HEADER_STYLE}{header}{RESET}"

        col_widths = [
            width_id,
            width_pri,
            width_status,
            width_deps,
            width_dependents,
            width_est,
            30,
        ]
        separator_line = "-+-".join("-" * w for w in col_widths)

        lines = [header_line, separator_line]

        def render_rows(row_list: list[dict], start_idx: int = 0) -> int:
            """Render a list of rows, return next row index."""
            row_idx = start_idx
            for row in row_list:
                deps_lines = row["deps_lines"]
                dependents_lines = row["dependents_lines"]
                estimate_lines = row["estimate_lines"]
                max_lines = max(len(deps_lines), len(dependents_lines), len(estimate_lines))

                if row.get("is_epic"):
                    row_bg = ROW_EPIC
                else:
                    row_bg = ROW_ODD if row_idx % 2 == 1 else ROW_EVEN

                for idx in range(max_lines):
                    deps_line = deps_lines[idx] if idx < len(deps_lines) else ""
                    dependents_line = dependents_lines[idx] if idx < len(dependents_lines) else ""
                    estimate_line = estimate_lines[idx] if idx < len(estimate_lines) else ""

                    if idx == 0:
                        line_parts = [
                            pad_text(row["id"], width_id, "right"),
                            pad_text(row["priority"], width_pri, "right"),
                            pad_text(row["status"], width_status, "left"),
                            pad_text(deps_line, width_deps, "left"),
                            pad_text(dependents_line, width_dependents, "left"),
                            pad_text(estimate_line, width_est, "right"),
                            row["title"],
                        ]
                        line_content = separator.join(line_parts)
                        lines.append(f"{row_bg}{line_content}{RESET}" if row_bg else line_content)
                    else:
                        if estimate_line or deps_line or dependents_line:
                            line_parts = [
                                pad_text("", width_id, "right"),
                                pad_text("", width_pri, "right"),
                                pad_text("", width_status, "left"),
                                pad_text(deps_line, width_deps, "left"),
                                pad_text(dependents_line, width_dependents, "left"),
                                pad_text(estimate_line, width_est, "right"),
                                "",
                            ]
                            line_content = separator.join(line_parts)
                            lines.append(
                                f"{row_bg}{line_content}{RESET}" if row_bg else line_content
                            )

                row_idx += 1
            return row_idx

        render_rows(rows, 0)

        return "\n".join(lines)

    def _get_epic_scope(self, epic_id: str) -> set[str]:
        """Get the epic and all its transitive dependencies."""
        result = {epic_id}
        to_process = [epic_id]

        while to_process:
            current = to_process.pop()
            fr = self.datasets.get_fr(current)
            if fr and fr.deps:
                for dep_id in fr.deps:
                    if dep_id not in result:
                        result.add(dep_id)
                        to_process.append(dep_id)

        return result
