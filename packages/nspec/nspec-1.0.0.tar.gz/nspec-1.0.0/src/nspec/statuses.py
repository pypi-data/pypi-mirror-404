"""Centralized status definitions for nspec tooling.

This is the SINGLE SOURCE OF TRUTH for all status emojis, codes, and text.
All other modules should import from here - DO NOT duplicate these definitions.
"""

from dataclasses import dataclass
from enum import IntEnum

# =============================================================================
# FR (Feature Request) Statuses
# =============================================================================


class FRStatusCode(IntEnum):
    """FR status codes for programmatic use."""

    PROPOSED = 0
    IN_DESIGN = 1
    ACTIVE = 2
    COMPLETED = 3
    REJECTED = 4
    SUPERSEDED = 5
    DEFERRED = 6


@dataclass(frozen=True)
class FRStatus:
    """FR status definition."""

    code: int
    emoji: str
    text: str

    @property
    def full(self) -> str:
        """Full status string (emoji + text)."""
        return f"{self.emoji} {self.text}"


# FR status definitions - keyed by code
FR_STATUSES: dict[int, FRStatus] = {
    0: FRStatus(0, "🟡", "Proposed"),
    1: FRStatus(1, "🔵", "In Design"),
    2: FRStatus(2, "🔵", "Active"),
    3: FRStatus(3, "✅", "Completed"),
    4: FRStatus(4, "❌", "Rejected"),
    5: FRStatus(5, "🔄", "Superseded"),
    6: FRStatus(6, "⏳", "Deferred"),
}

# Reverse lookup: full status string -> FRStatus
FR_STATUS_BY_TEXT: dict[str, FRStatus] = {s.full: s for s in FR_STATUSES.values()}

# Terminal FR statuses (cannot transition out of these)
FR_TERMINAL_CODES = {FRStatusCode.COMPLETED, FRStatusCode.REJECTED, FRStatusCode.SUPERSEDED}


# =============================================================================
# IMPL (Implementation) Statuses
# =============================================================================


class IMPLStatusCode(IntEnum):
    """IMPL status codes for programmatic use."""

    PLANNING = 0
    ACTIVE = 1
    TESTING = 2
    READY = 3  # Ready for archival (distinct from FR Completed)
    PAUSED = 4
    HOLD = 5


@dataclass(frozen=True)
class IMPLStatus:
    """IMPL status definition."""

    code: int
    emoji: str
    text: str

    @property
    def full(self) -> str:
        """Full status string (emoji + text)."""
        return f"{self.emoji} {self.text}"


# IMPL status definitions - keyed by code
# Flow: Planning → Active → Testing → Ready → [archived via nspec_complete]
IMPL_STATUSES: dict[int, IMPLStatus] = {
    0: IMPLStatus(0, "🟡", "Planning"),
    1: IMPLStatus(1, "🔵", "Active"),
    2: IMPLStatus(2, "🧪", "Testing"),
    3: IMPLStatus(3, "🟠", "Ready"),  # Ready for archival
    4: IMPLStatus(4, "⏳", "Paused"),
    5: IMPLStatus(5, "⚪", "Hold"),
}

# Reverse lookup: full status string -> IMPLStatus
IMPL_STATUS_BY_TEXT: dict[str, IMPLStatus] = {s.full: s for s in IMPL_STATUSES.values()}

# Terminal IMPL statuses
IMPL_TERMINAL_CODES = {IMPLStatusCode.READY}


# =============================================================================
# Priority Definitions
# =============================================================================


@dataclass(frozen=True)
class Priority:
    """Priority definition."""

    code: str  # P0, P1, P2, P3, E0, E1, E2, E3
    emoji: str
    rank: int  # Lower = higher priority

    @property
    def full(self) -> str:
        """Full priority string (emoji + code)."""
        return f"{self.emoji} {self.code}"

    @property
    def is_epic(self) -> bool:
        """True if this is an epic priority."""
        return self.code.startswith("E")


# Spec priorities
SPEC_PRIORITIES: dict[str, Priority] = {
    "P0": Priority("P0", "🔥", 0),  # Critical
    "P1": Priority("P1", "🟠", 1),  # High
    "P2": Priority("P2", "🟡", 2),  # Medium
    "P3": Priority("P3", "🔵", 3),  # Low
}

# Epic priorities
EPIC_PRIORITIES: dict[str, Priority] = {
    "E0": Priority("E0", "🚀", 0),  # Spotlight
    "E1": Priority("E1", "🎯", 1),  # High
    "E2": Priority("E2", "🎪", 2),  # Medium
    "E3": Priority("E3", "🎨", 3),  # Low
}

# ADR priorities
ADR_PRIORITIES: dict[str, Priority] = {
    "A1": Priority("A1", "🏛️", 1),  # Critical
    "A2": Priority("A2", "🏗️", 2),  # Important
    "A3": Priority("A3", "🔧", 3),  # Nice-to-have
}

# All priorities combined
ALL_PRIORITIES: dict[str, Priority] = {
    **SPEC_PRIORITIES,
    **EPIC_PRIORITIES,
    **ADR_PRIORITIES,
}

# Priority rank for sorting (lower = higher priority)
PRIORITY_RANK: dict[str, int] = {p.code: p.rank for p in ALL_PRIORITIES.values()}

# Priority display names
PRIORITY_NAMES: dict[str, str] = {
    "P0": "CRITICAL",
    "P1": "HIGH",
    "P2": "MEDIUM",
    "P3": "LOW",
    "E0": "SPOTLIGHT EPIC",
    "E1": "HIGH EPIC",
    "E2": "MEDIUM EPIC",
    "E3": "LOW EPIC",
    "A1": "CRITICAL ADR",
    "A2": "IMPORTANT ADR",
    "A3": "NICE-TO-HAVE ADR",
}


# =============================================================================
# Display Emojis for Dependencies/References
# =============================================================================


class DepDisplayEmoji:
    """Emojis used for displaying dependency status in nspec table."""

    COMPLETED = "✅"
    ACTIVE = "🔵"
    PROPOSED = "🟡"
    REJECTED = "❌"
    SUPERSEDED = "🔄"
    TESTING = "🧪"
    PAUSED = "⏳"
    UNKNOWN = "❓"


class EpicDisplayEmoji:
    """Emojis used for displaying epic status (derived from dependencies).

    Epic status is calculated, not stored:
    - PROPOSED: No deps have started (all proposed/planning)
    - ACTIVE: At least one dep is active/testing
    - COMPLETED: All deps are completed
    """

    PROPOSED = "📋"  # Clipboard - planning phase
    ACTIVE = "🚀"  # Rocket - work in progress
    COMPLETED = "🏆"  # Trophy - delivered


# =============================================================================
# Helper Functions
# =============================================================================


def get_fr_status(code: int) -> FRStatus | None:
    """Get FR status by code."""
    return FR_STATUSES.get(code)


def get_impl_status(code: int) -> IMPLStatus | None:
    """Get IMPL status by code."""
    return IMPL_STATUSES.get(code)


def get_priority(code: str) -> Priority | None:
    """Get priority by code (P0-P3, E0-E3)."""
    return ALL_PRIORITIES.get(code.upper())


def parse_status_text(status_str: str) -> str:
    """Extract status text from full status string (e.g., '🔵 Active' -> 'active')."""
    if not status_str:
        return ""
    parts = status_str.split(maxsplit=1)
    return parts[-1].lower().strip() if parts else ""


def is_active_status(status_str: str) -> bool:
    """Check if status represents active work."""
    text = parse_status_text(status_str)
    return text in ("active", "testing", "in design")


def is_completed_status(status_str: str) -> bool:
    """Check if status represents completed work."""
    text = parse_status_text(status_str)
    return text == "completed"


def is_superseded_status(status_str: str) -> bool:
    """Check if status is superseded."""
    text = parse_status_text(status_str)
    return text == "superseded"


def get_dep_display_emoji(status_str: str) -> str:
    """Get the emoji to display for a dependency based on its status.

    Args:
        status_str: Full status string like '🔵 Active' or 'active'

    Returns:
        Display emoji for dependency list
    """
    text = parse_status_text(status_str)

    if text == "completed":
        return DepDisplayEmoji.COMPLETED
    elif text == "active":
        return DepDisplayEmoji.ACTIVE
    elif text == "testing":
        return DepDisplayEmoji.TESTING
    elif text == "rejected":
        return DepDisplayEmoji.REJECTED
    elif text == "superseded":
        return DepDisplayEmoji.SUPERSEDED
    elif text == "paused":
        return DepDisplayEmoji.PAUSED
    else:  # proposed, planning, in design, hold, etc.
        return DepDisplayEmoji.PROPOSED


# =============================================================================
# Legend and Display Helpers
# =============================================================================


def get_status_legend() -> str:
    """Generate the status legend string for display.

    Shows key statuses for the nspec table legend.
    """
    return (
        f"Specs: {FR_STATUSES[0].emoji} Proposed  "
        f"{FR_STATUSES[2].emoji} Active  "
        f"{IMPL_STATUSES[2].emoji} Testing  "
        f"{FR_STATUSES[3].emoji} Completed  "
        f"{IMPL_STATUSES[4].emoji} Paused\n"
        f"Epics:   {EpicDisplayEmoji.PROPOSED} Planning  "
        f"{EpicDisplayEmoji.ACTIVE} In Progress  "
        f"{EpicDisplayEmoji.COMPLETED} Done"
    )


# =============================================================================
# Emoji Constants for Pattern Matching
# =============================================================================

# All possible status emojis (for regex pattern matching)
ALL_STATUS_EMOJIS = "🟡🔵✅❌🔄⏳🧪🟢🔴📋🚧🚀🏆"

# Regex pattern to match status emoji at start of string
STATUS_EMOJI_PATTERN = rf"^([{ALL_STATUS_EMOJIS}])\s+"


def get_status_emoji_fallback() -> dict[str, str]:
    """Generate fallback mapping from status text to emoji.

    This consolidates all status->emoji mappings in one place.
    Used when parsing status strings that don't have emoji prefix.
    """
    return {
        # FR statuses
        "proposed": FR_STATUSES[0].emoji,
        "in-design": FR_STATUSES[1].emoji,
        "in design": FR_STATUSES[1].emoji,
        "active": FR_STATUSES[2].emoji,
        "completed": FR_STATUSES[3].emoji,
        "complete": FR_STATUSES[3].emoji,
        "rejected": FR_STATUSES[4].emoji,
        "superseded": FR_STATUSES[5].emoji,
        "deferred": FR_STATUSES[6].emoji,
        # IMPL statuses
        "planning": IMPL_STATUSES[0].emoji,
        "testing": IMPL_STATUSES[2].emoji,
        "paused": IMPL_STATUSES[4].emoji,
        "hold": IMPL_STATUSES[5].emoji,
        # Legacy aliases
        "in-progress": FR_STATUSES[2].emoji,  # maps to active
        "blocked": "🔴",  # legacy, not in standard statuses
    }


def print_status_codes() -> None:
    """Print all status codes reference.

    Usage: Run `make nspec.status-codes` to see this output.
    """
    print("\n" + "=" * 60)
    print("NSPEC STATUS CODES REFERENCE")
    print("=" * 60)

    print("\n📋 FR (Feature Request) Status Codes:")
    print("-" * 40)
    print("  Code  Emoji  Status")
    print("-" * 40)
    for code, status in FR_STATUSES.items():
        print(f"    {code}     {status.emoji}    {status.text}")

    print("\n📋 IMPL (Implementation) Status Codes:")
    print("-" * 40)
    print("  Code  Emoji  Status")
    print("-" * 40)
    for code, status in IMPL_STATUSES.items():
        print(f"    {code}     {status.emoji}    {status.text}")

    print("\n📋 Priority Codes:")
    print("-" * 40)
    print("  Spec Priorities:")
    for code, priority in SPEC_PRIORITIES.items():
        name = PRIORITY_NAMES.get(code, "")
        print(f"    {code}  {priority.emoji}  {name}")
    print("\n  Epic Priorities:")
    for code, priority in EPIC_PRIORITIES.items():
        name = PRIORITY_NAMES.get(code, "")
        print(f"    {code}  {priority.emoji}  {name}")

    print("\n" + "=" * 60)
    print("USAGE:")
    print("=" * 60)
    print("\n  Start work:  make nspec.activate <SPEC_ID>")
    print("  Advance:     make nspec.next-status <SPEC_ID>")
    print("  Reset:       make nspec.reset <SPEC_ID>")
    print("\n  Workflow:    activate → next-status (repeat) → complete")
    print()


def get_status_codes_help() -> str:
    """Return a concise string of status codes for --help epilog."""
    fr_codes = ", ".join(f"{s.code}={s.text}" for s in FR_STATUSES.values())
    impl_codes = ", ".join(f"{s.code}={s.text}" for s in IMPL_STATUSES.values())
    return f"FR codes: {fr_codes}\nIMPL codes: {impl_codes}"


# =============================================================================
# Valid State Pairs Matrix (FR-286)
# =============================================================================
# Defines which (FR_status, IMPL_status) combinations are valid.
# Reference: DEV-PROCESS.md lines 956-960 (Linear Flow diagram)
#
# FR:   Proposed → In Design → Active → Completed
#                                 ↓
# IMPL:                      Planning → Active → Testing → Ready → [archived]
#
# Key rule: IMPL cannot advance past Planning(0) until FR reaches Active(2)


@dataclass(frozen=True)
class StateValidation:
    """Validation result for a state pair."""

    valid: bool
    reason: str


# Matrix of valid (FR, IMPL) state pairs
# Key: (fr_status_code, impl_status_code)
# Value: StateValidation(valid, reason)
VALID_STATE_PAIRS: dict[tuple[int, int], StateValidation] = {
    # FR=Proposed(0): Only IMPL=Planning allowed
    (0, 0): StateValidation(True, "Both not started"),
    (0, 1): StateValidation(False, "Cannot start IMPL until FR is Active"),
    (0, 2): StateValidation(False, "Cannot start IMPL until FR is Active"),
    (0, 3): StateValidation(False, "Cannot complete IMPL without finalized spec"),
    (0, 4): StateValidation(True, "FR proposed, IMPL paused"),
    (0, 5): StateValidation(True, "FR proposed, IMPL on hold"),
    # FR=In Design(1): Only IMPL=Planning allowed
    (1, 0): StateValidation(True, "Spec being designed, impl planning"),
    (1, 1): StateValidation(False, "Cannot start IMPL while spec in design"),
    (1, 2): StateValidation(False, "Cannot test IMPL while spec in design"),
    (1, 3): StateValidation(False, "Cannot complete IMPL without finalized spec"),
    (1, 4): StateValidation(True, "FR in design, IMPL paused"),
    (1, 5): StateValidation(True, "FR in design, IMPL on hold"),
    # FR=Active(2): IMPL can proceed through all states except Completed
    (2, 0): StateValidation(True, "Spec done, impl not started"),
    (2, 1): StateValidation(True, "Spec locked, actively implementing"),
    (2, 2): StateValidation(True, "Spec locked, testing implementation"),
    (2, 3): StateValidation(False, "Cannot complete IMPL until FR is Completed"),
    (2, 4): StateValidation(True, "FR active, IMPL paused"),
    (2, 5): StateValidation(True, "FR active, IMPL on hold"),
    # FR=Completed(3): Only IMPL=Completed valid (atomic completion)
    (3, 0): StateValidation(False, "FR completed but IMPL not started - inconsistent"),
    (3, 1): StateValidation(False, "FR completed but IMPL still active - inconsistent"),
    (3, 2): StateValidation(False, "FR completed but IMPL still testing - inconsistent"),
    (3, 3): StateValidation(True, "Both completed"),
    (3, 4): StateValidation(False, "FR completed but IMPL paused - inconsistent"),
    (3, 5): StateValidation(False, "FR completed but IMPL on hold - inconsistent"),
    # FR=Rejected(4): Any IMPL state valid (spec cancelled)
    (4, 0): StateValidation(True, "FR rejected, IMPL not started"),
    (4, 1): StateValidation(True, "FR rejected mid-implementation"),
    (4, 2): StateValidation(True, "FR rejected during testing"),
    (4, 3): StateValidation(True, "FR rejected after IMPL complete"),
    (4, 4): StateValidation(True, "FR rejected, IMPL paused"),
    (4, 5): StateValidation(True, "FR rejected, IMPL on hold"),
    # FR=Superseded(5): Any IMPL state valid (spec replaced)
    (5, 0): StateValidation(True, "FR superseded, IMPL not started"),
    (5, 1): StateValidation(True, "FR superseded mid-implementation"),
    (5, 2): StateValidation(True, "FR superseded during testing"),
    (5, 3): StateValidation(True, "FR superseded after IMPL complete"),
    (5, 4): StateValidation(True, "FR superseded, IMPL paused"),
    (5, 5): StateValidation(True, "FR superseded, IMPL on hold"),
    # FR=Deferred(6): IMPL should be Paused or Hold
    (6, 0): StateValidation(True, "FR deferred, IMPL planning"),
    (6, 1): StateValidation(False, "Cannot have active IMPL with deferred FR"),
    (6, 2): StateValidation(False, "Cannot have testing IMPL with deferred FR"),
    (6, 3): StateValidation(False, "Cannot complete IMPL with deferred FR"),
    (6, 4): StateValidation(True, "Both deferred/paused"),
    (6, 5): StateValidation(True, "FR deferred, IMPL on hold"),
}


def is_valid_state_pair(fr_status: int, impl_status: int) -> tuple[bool, str]:
    """Check if a (FR, IMPL) state combination is valid.

    Args:
        fr_status: FR status code (0-6)
        impl_status: IMPL status code (0-5)

    Returns:
        Tuple of (is_valid, reason_message)
    """
    key = (fr_status, impl_status)
    if key not in VALID_STATE_PAIRS:
        return (False, f"Unknown state combination: FR={fr_status}, IMPL={impl_status}")

    validation = VALID_STATE_PAIRS[key]
    return (validation.valid, validation.reason)
