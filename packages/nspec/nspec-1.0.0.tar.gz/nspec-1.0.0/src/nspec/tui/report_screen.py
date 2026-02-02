"""Report screen for the Nspec TUI."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static, TabbedContent, TabPane

from nspec.reports import REPORTS, generate_report


class SectionWidgetFactory:
    """MVC-style factory: Model (JSON) -> View (native TUI widgets)."""

    @classmethod
    def create(cls, section: dict, section_id: str) -> DataTable | Static:
        """Create appropriate widget for section type."""
        section_type = section.get("type", "text")
        factories = {
            "table": cls._create_table,
            "matrix": cls._create_table,
            "metrics": cls._create_metrics,
            "list": cls._create_list,
            "blockers": cls._create_blockers,
        }
        factory = factories.get(section_type, cls._create_static)
        return factory(section, section_id)

    @classmethod
    def _create_table(cls, section: dict, section_id: str) -> DataTable:
        """Create DataTable widget from table section."""
        table = DataTable(id=section_id, zebra_stripes=True)
        table.cursor_type = "row"

        columns = section.get("columns", [])
        data = section.get("data", [])

        for col in columns:
            table.add_column(col, key=col.lower().replace(" ", "_"))

        for row in data:
            cells = []
            for col in columns:
                key = col.lower().replace(" ", "_").replace("(", "").replace(")", "")
                val = row.get(key, row.get(col.lower(), ""))
                cells.append(str(val))
            table.add_row(*cells)

        return table

    @classmethod
    def _create_metrics(cls, section: dict, section_id: str) -> Static:
        """Create Static widget for metrics section."""
        data = section.get("data", {})
        lines = []
        for key, value in data.items():
            label = key.replace("_", " ").title()
            lines.append(f"[bold]{label}:[/] {value}")
        return Static("\n".join(lines), id=section_id)

    @classmethod
    def _create_list(cls, section: dict, section_id: str) -> Static:
        """Create Static widget for list section."""
        data = section.get("data", [])
        if not data:
            return Static("[dim]No items[/]", id=section_id)

        lines = []
        for item in data:
            if isinstance(item, dict):
                spec_id = item.get("id", "")
                title = item.get("title", "")
                loe = item.get("loe", "N/A")
                lines.append(f"  * [bold]{spec_id}[/] {title} [dim]({loe})[/]")
            else:
                lines.append(f"  * {item}")
        return Static("\n".join(lines), id=section_id)

    @classmethod
    def _create_blockers(cls, section: dict, section_id: str) -> Static:
        """Create Static widget for blockers section."""
        data = section.get("data", [])
        if not data:
            return Static("[bold]No blocked specs![/]", id=section_id)

        lines = []
        priority_colors = {"P0": "bold", "P1": "bold", "P2": "", "P3": "dim"}

        for blocker in data:
            priority = blocker.get("priority", "")
            color = priority_colors.get(priority, "white")
            lines.append(
                f"[{color}]{priority}[/] [bold]{blocker.get('id', '')}[/] "
                f"{blocker.get('title', '')}"
            )
            for dep in blocker.get("blocked_by", []):
                lines.append(
                    f"    <- blocked by [bold]{dep.get('id', '')}[/] "
                    f"{dep.get('title', '')} [dim][{dep.get('status', '')}][/]"
                )
            lines.append("")

        return Static("\n".join(lines), id=section_id)

    @classmethod
    def _create_static(cls, section: dict, section_id: str) -> Static:
        """Fallback: create Static widget with raw data."""
        data = section.get("data", "")
        if isinstance(data, (list, dict)):
            import json

            content = json.dumps(data, indent=2)
        else:
            content = str(data)
        return Static(content, id=section_id)


class ReportScreen(Screen):
    """Full-screen report view with tabbed reports using native widgets."""

    BINDINGS = [
        Binding("escape", "close", "Close", priority=True),
        Binding("q", "close", "Close"),
        Binding("r", "refresh", "Refresh"),
        Binding("1", "tab_1", "Tab 1"),
        Binding("2", "tab_2", "Tab 2"),
        Binding("3", "tab_3", "Tab 3"),
        Binding("4", "tab_4", "Tab 4"),
    ]

    CSS_PATH = "templates/reports/report_screen.tcss"

    def __init__(self, docs_root: Path | None = None) -> None:
        """Initialize report screen."""
        super().__init__()
        self.docs_root = docs_root or Path("docs")
        self.reports_data: dict[str, dict] = {}

    def compose(self) -> ComposeResult:
        """Create layout - data populated on mount."""
        yield Header()
        with TabbedContent(id="report-tabs"):
            for report_id, report_info in REPORTS.items():
                with TabPane(report_info["name"], id=f"tab-{report_id}"):
                    with VerticalScroll(id=f"scroll-{report_id}"):
                        yield Static(
                            report_info["name"], classes="report-header", id=f"header-{report_id}"
                        )
                        yield Static("Loading...", classes="report-meta", id=f"meta-{report_id}")
                        yield Container(id=f"content-{report_id}")
        yield Footer()

    def on_mount(self) -> None:
        """Populate reports after mount when app context is available."""
        for report_id in REPORTS:
            try:
                report_data = generate_report(report_id, self.docs_root)
                self.reports_data[report_id] = report_data
                self._populate_report(report_id, report_data)
            except Exception as e:
                container = self.query_one(f"#content-{report_id}", Container)
                container.mount(Static(f"[bold]Error:[/] {e}"))

    def _populate_report(self, report_id: str, report_data: dict) -> None:
        """Populate a report tab with data."""
        header = self.query_one(f"#header-{report_id}", Static)
        header.update(report_data.get("title", "Report"))

        meta = self.query_one(f"#meta-{report_id}", Static)
        meta.update(f"Generated: {report_data.get('generated_at', 'Unknown')}")

        container = self.query_one(f"#content-{report_id}", Container)

        for idx, section in enumerate(report_data.get("sections", [])):
            section_id = f"{report_id}-section-{idx}"

            container.mount(
                Static(
                    f"[bold]=== {section.get('name', 'Section')} ===[/]",
                    classes="section-header",
                )
            )

            widget = SectionWidgetFactory.create(section, section_id)
            container.mount(widget)

    def action_close(self) -> None:
        """Close the report screen."""
        self.app.pop_screen()

    def key_escape(self) -> None:
        """Handle escape key directly."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Refresh reports - reloads the screen."""
        self.app.pop_screen()
        self.app.push_screen(ReportScreen(self.docs_root))

    def action_tab_1(self) -> None:
        """Switch to first tab."""
        self._switch_tab(0)

    def action_tab_2(self) -> None:
        """Switch to second tab."""
        self._switch_tab(1)

    def action_tab_3(self) -> None:
        """Switch to third tab."""
        self._switch_tab(2)

    def action_tab_4(self) -> None:
        """Switch to fourth tab."""
        self._switch_tab(3)

    def _switch_tab(self, index: int) -> None:
        """Switch to tab by index."""
        try:
            tabbed = self.query_one(TabbedContent)
            tabs = list(REPORTS.keys())
            if index < len(tabs):
                tabbed.active = f"tab-{tabs[index]}"
        except Exception:
            pass
