"""Textual TUI for Nspec Management.

A terminal user interface for viewing and managing the nspec with:
- Auto-refresh via file watching (2-second polling)
- Scrollable table with search
- Detail panel for selected spec
- Keyboard navigation (vim-style)
- Claude Follow Mode for live task tracking

Usage:
    python -m tools.nspec --tui
    # Or via make: make nspec.tui

Keybindings (Main View):
    q       Quit
    /       Focus search bar
    Escape  Clear search, return to table
    n       Jump to next search match
    N       Jump to previous match
    Enter   Open detail view
    r       Manual refresh
    e       Set epic filter
    f       Toggle Follow Mode (tracks current spec)
    m       Move spec to epic
    s       Show reports

Keybindings (Detail View):
    Escape  Close detail view
    Tab     Next section
    Shift+Tab Previous section
    Enter   Toggle section expand/collapse
    <-/h    Navigate to upstream dependency
    ->/l    Navigate to downstream dependent
    1/2/3   Jump to dependency 1/2/3
    y       Copy spec URI to clipboard
    g       Go to URI from clipboard
    x       Mark first pending task complete
    ~       Mark first pending task obsolete

Follow Mode:
    Press 'f' to enable Follow Mode. The TUI will:
    - Auto-navigate to the current spec (from .novabuilt.dev/nspec/state.json)
    - Show a spinner on the first pending task
    - Auto-refresh when IMPL file changes
    - Auto-scroll to keep active task visible
"""

from .app import NspecTUI, main
from .detail_screen import DetailViewScreen
from .report_screen import ReportScreen, SectionWidgetFactory
from .state import FollowModeState, NspecData
from .table import NspecTable
from .utils import clean_title, extract_emoji_and_text, format_status, get_display_width
from .widgets import (
    EpicBanner,
    EpicSelector,
    HelpModal,
    MoveSpecModal,
    SearchBar,
    SectionContent,
    SectionHeader,
    StatusIndicator,
    SpecDetailPanel,
    TaskRow,
)

__all__ = [
    # Main app
    "NspecTUI",
    "main",
    # Screens
    "DetailViewScreen",
    "ReportScreen",
    "SectionWidgetFactory",
    # State
    "NspecData",
    "FollowModeState",
    # Table
    "NspecTable",
    # Utilities
    "clean_title",
    "extract_emoji_and_text",
    "format_status",
    "get_display_width",
    # Widgets
    "EpicBanner",
    "EpicSelector",
    "HelpModal",
    "MoveSpecModal",
    "SearchBar",
    "SectionContent",
    "SectionHeader",
    "StatusIndicator",
    "SpecDetailPanel",
    "TaskRow",
]
