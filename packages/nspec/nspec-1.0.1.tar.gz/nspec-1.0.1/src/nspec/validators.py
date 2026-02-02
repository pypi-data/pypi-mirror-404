"""Format validators for FR and IMPL documents - Layer 1 validation.

This module provides strict fail-fast validation for fRIMPL document formats.
All validation happens at parse time - invalid documents raise ValueError immediately.

Validation Rules:
    FR Documents:
        - Priority: MUST be P0, P1, P2, or P3 (not "High", "Medium", "Low")
        - Status: MUST be emoji + text format (🟡 Proposed, 🟢 In Progress, etc.)
        - Dependencies: MUST use deps: [XXX, YYY] format
        - ID: MUST be prefixed (S### for specs, E### for epics), optional letter suffix
        - Filename: MUST be FR-S###-description.md or FR-E###-description.md
        - Acceptance Criteria: Optional but validated if present

    IMPL Documents:
        - Status: MUST match FR status values (🟡 Proposed, 🟢 Active, ✅ Complete, etc.)
        - LOE: MUST be ~Xh, ~Xd, or ~Xw format (not ~TBD)
        - ID: MUST match FR ID (S###/E###)
        - Filename: MUST be IMPL-S###-description.md or IMPL-E###-description.md
        - Tasks: MUST follow strict checkbox format with action verbs
        - No Dependencies: deps: [...] is FORBIDDEN in IMPL (belongs in FR only)
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from nspec.ids import normalize_spec_ref
from nspec.tasks import (
    AcceptanceCriteria,
    AcceptanceCriteriaParser,
    Task,
    TaskParser,
)

# Spec/Epic ID format: E### / S### (+ optional letter suffix)
SPEC_REF_PATTERN = re.compile(r"^[ES]\d{3}[a-z]?$", re.IGNORECASE)

# FR header patterns
# Allow 🔥 (P0), 🟠 (P1), 🟡 (P2), 🔵 (P3)
# Note: ️? makes the variation selector (U+FE0F) optional for emoji compatibility
FR_PRIORITY_RE = re.compile(r"^\*\*Priority:\*\*\s+[🔥🟠🟡🔵]️?\s+(P[0-3])$", re.MULTILINE)
# Type field (optional, defaults to Feature if omitted)
FR_TYPE_RE = re.compile(
    r"^\*\*Type:\*\*\s+(Feature|Enhancement|Bug|ADR|Refactor|Epic)$", re.MULTILINE
)
# FR_STATUS_RE and IMPL_STATUS_RE are built after enum definitions
DEPS_RE = re.compile(r"^deps:\s*\[(.*?)\]$", re.MULTILINE | re.DOTALL)
# LOE formats:
#   Specs: 5d, 3w, 10h
#   Epics: 18d,79d (parallel,sequential)
#   Retrospective: N/A (optional note in parentheses)
LOE_RE = re.compile(
    r"^\*\*LOE:\*\*\s+(?:(\d+(?:\.\d+)?)(h|d|w)(?:,(\d+(?:\.\d+)?)(h|d|w))?|N/A(?:\s+\([^)]+\))?)$",
    re.MULTILINE,
)


class SpecType(str, Enum):
    """Valid FR/IMPL Type values."""

    FEATURE = "Feature"  # New capability (default)
    ENHANCEMENT = "Enhancement"  # Improvement to existing feature
    BUG = "Bug"  # Fix for defect
    ADR = "ADR"  # Architecture Decision Record
    REFACTOR = "Refactor"  # Code quality improvement
    EPIC = "Epic"  # Container for multiple specs


class Priority(str, Enum):
    """Valid FR Priority values - P0-P3."""

    P0 = "P0"  # Critical spec
    P1 = "P1"  # High priority spec
    P2 = "P2"  # Medium priority spec
    P3 = "P3"  # Low priority spec


def _build_valid_fr_statuses() -> list[str]:
    """Get valid FR status strings from centralized statuses module."""
    from nspec.statuses import FR_STATUSES

    return [s.full for s in FR_STATUSES.values()]


def _build_valid_impl_statuses() -> list[str]:
    """Get valid IMPL status strings from centralized statuses module."""
    from nspec.statuses import IMPL_STATUSES

    return [s.full for s in IMPL_STATUSES.values()]


# These are kept as str Enums for backwards compat with code that does `FRStatus.PROPOSED`
# but values are derived from the centralized statuses module at import time.
class FRStatus(str, Enum):
    """Valid FR Status values — derived from statuses module."""

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list) -> str:  # type: ignore[override]
        from nspec.statuses import FR_STATUSES

        _name_to_code = {
            "PROPOSED": 0,
            "IN_DESIGN": 1,
            "ACTIVE": 2,
            "COMPLETED": 3,
            "REJECTED": 4,
            "SUPERSEDED": 5,
            "DEFERRED": 6,
        }
        return FR_STATUSES[_name_to_code[name]].full

    PROPOSED = auto()
    IN_DESIGN = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    REJECTED = auto()
    SUPERSEDED = auto()
    DEFERRED = auto()


def _make_impl_status() -> type:
    """Build IMPLStatus enum from statuses module.

    COMPLETED is kept as a distinct value (✅ Completed) separate from
    READY (🟠 Ready) because completed-directory files use a different
    status string than ready-to-archive active files.
    """
    from nspec.statuses import FR_STATUSES, IMPL_STATUSES

    # Use unique_value trick: create with explicit values to avoid alias dedup
    return Enum(  # type: ignore[return-value]
        "IMPLStatus",
        {
            "PLANNING": IMPL_STATUSES[0].full,
            "ACTIVE": IMPL_STATUSES[1].full,
            "TESTING": IMPL_STATUSES[2].full,
            "READY": IMPL_STATUSES[3].full,
            "COMPLETED": FR_STATUSES[3].full,  # ✅ Completed (for archived files)
            "PAUSED": IMPL_STATUSES[4].full,
            "HOLD": IMPL_STATUSES[5].full,
        },
        type=str,
    )


IMPLStatus = _make_impl_status()  # type: ignore[assignment,misc]


class LOEUnit(str, Enum):
    """Valid LOE time units."""

    HOURS = "h"
    DAYS = "d"
    WEEKS = "w"


# Build strict status regex patterns from statuses module
_fr_statuses = "|".join(re.escape(s.value) for s in FRStatus)
# Add legacy FR emoji variants
_fr_statuses += "|" + re.escape("🟢 Active")
FR_STATUS_RE = re.compile(rf"^\*\*Status:\*\*\s+({_fr_statuses})$", re.MULTILINE)

_impl_statuses = "|".join(re.escape(s.value) for s in IMPLStatus)
# Add legacy IMPL emoji variants
_impl_legacy = ["📋 Planning", "🚧 Active", "✅ Completed", "⏸️ Paused"]
_impl_statuses += "|" + "|".join(re.escape(s) for s in _impl_legacy)
IMPL_STATUS_RE = re.compile(rf"^\*\*Status:\*\*\s+({_impl_statuses})$", re.MULTILINE)


@dataclass
class FRMetadata:
    """Parsed and validated FR metadata with acceptance criteria tracking."""

    spec_id: str  # Normalized: "S001", "E007", "S100a"
    title: str  # From first heading
    type: str  # Feature, Enhancement, Bug, ADR, Refactor, Epic
    priority: str  # P0, P1, P2, P3
    status: str  # Emoji + text
    deps: list[str]  # Normalized spec IDs
    path: Path  # Source file path

    # NEW: Acceptance criteria tracking
    acceptance_criteria: list[AcceptanceCriteria]  # All AC from Success Criteria
    ac_total: int  # Total AC count
    ac_completed: int  # Completed AC count
    ac_completion_percent: int  # Completion percentage

    def __post_init__(self) -> None:
        """Calculate AC statistics."""
        self.ac_total = len(self.acceptance_criteria)
        self.ac_completed = sum(1 for ac in self.acceptance_criteria if ac.completed)
        self.ac_completion_percent = (
            int((self.ac_completed / self.ac_total) * 100) if self.ac_total > 0 else 0
        )


@dataclass
class IMPLMetadata:
    """Parsed and validated IMPL metadata with task tracking."""

    spec_id: str  # Normalized: "S001", "E007", "S100a"
    type: str  # Feature, Enhancement, Bug, ADR, Refactor, Epic
    status: str  # Emoji + text
    loe: str  # Manual LOE: Xh, Xd, Xw (or parallel,sequential for epics)
    path: Path  # Source file path

    # NEW: Task tracking
    tasks: list[Task]  # All tasks from Day/Phase sections
    tasks_total: int  # Total task count
    tasks_completed: int  # Completed task count
    completion_percent: int  # Completion percentage

    # LOE rollup from dependencies (set by calculate_loe_rollups)
    loe_parallel_hours: int = 0  # Parsed parallel hours from manual LOE
    loe_sequential_hours: int = 0  # Parsed sequential hours from manual LOE
    calculated_loe_parallel: int | None = None  # Calculated from deps (max)
    calculated_loe_sequential: int | None = None  # Calculated from deps (sum)
    effective_loe: str = ""  # LOE to use (calculated if deps, else manual)
    effective_loe_hours: int = 0  # Hours version of effective_loe

    def __post_init__(self) -> None:
        """Calculate task statistics and parse LOE."""
        # Count all tasks recursively (tasks may have children)
        self.tasks_total, self.tasks_completed = self._count_tasks_recursive(self.tasks)
        self.completion_percent = (
            int((self.tasks_completed / self.tasks_total) * 100) if self.tasks_total > 0 else 0
        )
        # Parse manual LOE to hours
        self.loe_parallel_hours, self.loe_sequential_hours = _parse_loe_to_hours(self.loe)
        # Default effective LOE to manual (will be overwritten if deps exist)
        self.effective_loe = self.loe
        self.effective_loe_hours = self.loe_sequential_hours

    @property
    def has_blocked_tasks(self) -> bool:
        """True if any task (recursively) has a BLOCKED marker."""
        return self._check_blocked_recursive(self.tasks)

    def _check_blocked_recursive(self, tasks: list[Task]) -> bool:
        """Check if any task in the tree is blocked."""
        for task in tasks:
            if task.blocked:
                return True
            if task.children and self._check_blocked_recursive(task.children):
                return True
        return False

    def _count_tasks_recursive(self, tasks: list[Task]) -> tuple[int, int]:
        """Count total and completed tasks recursively through children."""
        total = 0
        completed = 0
        for task in tasks:
            total += 1
            if task.completed:
                completed += 1
            if task.children:
                child_total, child_completed = self._count_tasks_recursive(task.children)
                total += child_total
                completed += child_completed
        return total, completed


def _parse_loe_to_hours(loe: str) -> tuple[int, int]:
    """Convert LOE string to hours.

    Examples:
        Specs: 5h -> (5, 5), 3d -> (24, 24), 2w -> (80, 80)
        Epics: 18d,79d -> (144, 632) (parallel, sequential)

    Returns:
        Tuple of (parallel_hours, sequential_hours)
        For specs, both values are the same
    """
    loe = loe.strip()
    if not loe or loe.upper() == "N/A":
        return (0, 0)

    # Check if this is epic format (parallel,sequential)
    if "," in loe:
        parts = loe.split(",")
        parallel = _parse_single_loe(parts[0].strip())
        sequential = _parse_single_loe(parts[1].strip())
        return (parallel, sequential)
    else:
        hours = _parse_single_loe(loe)
        return (hours, hours)


def _parse_single_loe(loe: str) -> int:
    """Parse a single LOE value to hours (supports decimals)."""
    loe = loe.lstrip("~")
    if loe.endswith("h"):
        return int(float(loe[:-1]))
    elif loe.endswith("d"):
        return int(float(loe[:-1]) * 8)  # 8 hour work day
    elif loe.endswith("w"):
        return int(float(loe[:-1]) * 40)  # 40 hour work week
    return 0


def _format_hours_to_loe(hours: int) -> str:
    """Convert hours back to LOE format.

    Examples:
        5 -> 5h
        24 -> 3d
        80 -> 2w
    """
    if hours <= 0:
        return "N/A"
    if hours >= 40 and hours % 40 == 0:
        return f"{hours // 40}w"
    elif hours >= 8 and hours % 8 == 0:
        return f"{hours // 8}d"
    else:
        return f"{hours}h"


class FRValidator:
    """Validates FR document format - FAIL FAST on any violation.

    Validation layers:
        1. Filename format (FR-S###-name.md / FR-E###-name.md)
        2. ID format (S### / E###, optional suffix)
        3. Required header fields (Priority, Status)
        4. Priority format (P0-P3 only)
        5. Status format (emoji + text)
        6. Dependency format (deps: [...])
        7. Acceptance criteria format (if present)
        8. Completed files MUST have ✅ Completed status (if require_completed=True)
    """

    def __init__(self) -> None:
        """Initialize FR validator with AC parser."""
        self.ac_parser = AcceptanceCriteriaParser()

    def validate(
        self,
        path: Path,
        content: str,
        require_completed: bool = False,
        allow_superseded: bool = False,
    ) -> FRMetadata:
        """Parse and validate FR - raise ValueError on any issue.

        Args:
            path: Path to FR file
            content: Full file content
            require_completed: If True, enforce status must be ✅ Completed
            allow_superseded: If True, allow 🔄 Superseded status as valid

        Returns:
            FRMetadata with all parsed fields

        Raises:
            ValueError: On any validation failure
        """
        # Extract spec ID from filename
        spec_id = self._extract_spec_id(path)

        # Extract header (first 30 lines for metadata)
        header_content = "\n".join(content.split("\n")[:30])

        # Extract and validate title
        title = self._extract_title(content, path)

        # Validate and extract type (defaults to Feature if omitted)
        spec_type = self._validate_type(header_content, path)

        # Validate and extract priority
        priority = self._validate_priority(header_content, path)

        # Cross-validate type and priority
        self._validate_type_priority_consistency(spec_type, priority, path)

        # Validate and extract status
        status = self._validate_status(header_content, path)

        # Status validation based on mode
        if require_completed and status != FRStatus.COMPLETED.value:
            raise ValueError(
                f"❌ Completed file {path.name} has wrong status: {status}\n"
                f"   Completed files MUST have status: {FRStatus.COMPLETED.value}\n"
                f"   ➜ Fix the status or move the file out of completed directory."
            )
        elif allow_superseded and status not in [
            FRStatus.SUPERSEDED.value,
            FRStatus.COMPLETED.value,
        ]:
            raise ValueError(
                f"❌ Superseded file {path.name} has wrong status: {status}\n"
                f"   Superseded files MUST have status: {FRStatus.SUPERSEDED.value}\n"
                f"   ➜ Fix the status or move the file out of superseded directory."
            )

        # Parse dependencies
        deps = self._parse_dependencies(content, path)

        # Parse acceptance criteria (optional but validated if present)
        try:
            acceptance_criteria = self.ac_parser.parse(content, path)
        except ValueError as e:
            # Re-raise with context
            raise ValueError(f"Acceptance criteria validation failed:\n{e}") from None

        return FRMetadata(
            spec_id=spec_id,
            title=title,
            type=spec_type,
            priority=priority,
            status=status,
            deps=deps,
            path=path,
            acceptance_criteria=acceptance_criteria,
            ac_total=0,  # Calculated in __post_init__
            ac_completed=0,
            ac_completion_percent=0,
        )

    def _extract_spec_id(self, path: Path) -> str:
        """Extract and validate spec ID from filename.

        Examples:
            FR-S001-feature.md -> "S001"
            FR-E007-loop.md -> "E007"
            FR-S060a-part1.md -> "S060a"
            FR-1234-invalid.md -> ValueError

        Raises:
            ValueError: If filename or spec ID format is invalid
        """
        match = re.match(r"FR-([ES]\d{3}[a-z]?)", path.stem, re.IGNORECASE)
        if not match:
            raise ValueError(
                f"❌ Invalid FR filename format: {path.name}\n"
                f"   Required format: FR-S###-description.md or FR-E###-description.md\n"
                f"   Examples: FR-S005-feature.md, FR-E007-loop.md"
            )

        raw_id = match.group(1)
        try:
            return normalize_spec_ref(raw_id)
        except ValueError:
            raise ValueError(
                f"❌ Invalid ID format in filename: '{raw_id}'\n"
                f"   Valid format: E### or S### (optional suffix)\n"
                f"   Examples: E001, S004, S100a"
            ) from None

    def _extract_title(self, content: str, path: Path) -> str:
        """Extract title from first heading.

        Expected format:
            # FR-XXX: Title Text

        Raises:
            ValueError: If no title found in first 10 lines
        """
        for line in content.split("\n")[:10]:
            if line.startswith("# "):
                return line[2:].strip()

        raise ValueError(
            f"❌ No title found in {path.name}\n"
            f"   Expected: # FR-XXX: Title on first line\n"
            f"   ➜ The fRIMPL is broken - fix it manually."
        )

    def _validate_priority(self, header_content: str, path: Path) -> str:
        """Validate priority is exactly P0, P1, P2, or P3.

        Raises:
            ValueError: If priority missing, wrong format, or invalid value
        """
        match = FR_PRIORITY_RE.search(header_content)
        if not match:
            # Check if Priority line exists but with wrong format
            priority_line = re.search(r"^\*\*Priority:\*\*\s+(.+?)$", header_content, re.MULTILINE)
            if priority_line:
                invalid_value = priority_line.group(1).strip()
                raise ValueError(
                    f"❌ Invalid priority format in {path.name}: '{invalid_value}'\n"
                    f"   Valid values: P0-P3\n"
                    f"   Required format: **Priority:** 🟠 P1\n"
                    f"   ➜ The fRIMPL is broken - fix it manually."
                )
            else:
                raise ValueError(
                    f"❌ Missing required field in {path.name}: priority\n"
                    f"   Required format: **Priority:** 🟠 P1\n"
                    f"   ➜ The fRIMPL is broken - fix it manually."
                )

        # Extract the priority value (P0-P3)
        priority_value = match.group(1)

        # Validate against enum
        try:
            Priority(priority_value)
        except ValueError:
            valid_values = ", ".join([p.value for p in Priority])
            raise ValueError(
                f"❌ Invalid priority value in {path.name}: {priority_value}\n"
                f"   Valid values: {valid_values}\n"
                f"   ➜ The fRIMPL is broken - fix it manually."
            ) from None

        return priority_value

    def _validate_type(self, header_content: str, path: Path) -> str:
        """Validate type field (defaults to Feature if omitted).

        Returns:
            Type value (Feature, Enhancement, Bug, ADR, Refactor, Epic)

        Raises:
            ValueError: If type present but invalid format
        """
        match = FR_TYPE_RE.search(header_content)
        if not match:
            # Type field is optional - default to Feature
            return SpecType.FEATURE.value

        type_value = match.group(1)

        # Validate against enum
        try:
            SpecType(type_value)
        except ValueError:
            valid_values = ", ".join([t.value for t in SpecType])
            raise ValueError(
                f"❌ Invalid type value in {path.name}: {type_value}\n"
                f"   Valid values: {valid_values}\n"
                f"   ➜ The fRIMPL is broken - fix it manually."
            ) from None

        return type_value

    def _validate_type_priority_consistency(
        self, spec_type: str, priority: str, path: Path
    ) -> None:
        """Cross-validate type and priority consistency.

        As of the prefixed ID reform (FR-100), priority is unified to P0-P3 for all types.
        """
        _ = (spec_type, priority, path)

    def _validate_status(self, header_content: str, path: Path) -> str:
        """Validate status format (emoji + text).

        Raises:
            ValueError: If status missing or invalid format
        """
        match = FR_STATUS_RE.search(header_content)
        if not match:
            # Try to extract what was actually found
            status_line_match = re.search(
                r"^\*\*Status:\*\*\s+(.+?)$", header_content, re.MULTILINE
            )
            found_value = status_line_match.group(1) if status_line_match else "NOT FOUND"

            valid_values = "\n   ".join([s.value for s in FRStatus])
            raise ValueError(
                f"❌ Invalid status in {path.name}\n"
                f"   Found: **Status:** {found_value}\n"
                f"   Valid choices:\n   {valid_values}\n"
                f"   ➜ Check for typos like '✅ Complete' (should be '✅ Completed')"
            )

        status_value = match.group(1)

        # Validate against enum
        try:
            FRStatus(status_value)
        except ValueError:
            valid_values = "\n   ".join([s.value for s in FRStatus])
            raise ValueError(
                f"❌ Invalid status value in {path.name}: {status_value}\n"
                f"   Valid values:\n   {valid_values}\n"
                f"   ➜ The fRIMPL is broken - fix it manually."
            ) from None

        return status_value

    def _parse_dependencies(self, content: str, path: Path) -> list[str]:
        """Parse deps: [...] format.

        Valid formats:
            deps: []
            deps: [S001]
            deps: [S001, E002, S060a]

        Returns:
            List of normalized spec IDs

        Raises:
            ValueError: If dependency format is invalid
        """
        match = DEPS_RE.search(content)
        if not match:
            return []

        deps_content = match.group(1).strip()
        if not deps_content:
            return []

        # Parse comma-separated spec IDs
        deps = []
        for dep in deps_content.split(","):
            dep = dep.strip()
            if dep:
                try:
                    deps.append(normalize_spec_ref(dep))
                except ValueError:
                    raise ValueError(
                        f"❌ Invalid dependency ID in {path.name}: '{dep}'\n"
                        f"   Valid format: E### or S### (optional suffix)\n"
                        f"   ➜ The fRIMPL is broken - fix it manually."
                    ) from None

        return deps


class IMPLValidator:
    """Validates IMPL document format - FAIL FAST on any violation.

    Validation layers:
        1. Filename format (IMPL-S###-name.md / IMPL-E###-name.md)
        2. ID format (S### / E###, optional suffix)
        3. Required header fields (Status, LOE)
        4. Status format (emoji + text)
        5. LOE format (~Xh, ~Xd, ~Xw)
        6. No dependencies (deps forbidden in IMPL)
        7. Task format and validation
        8. Completed files MUST have ✅ Completed status (if require_completed=True)
    """

    def __init__(self) -> None:
        """Initialize IMPL validator with task parser."""
        self.task_parser = TaskParser()

    def validate(
        self,
        path: Path,
        content: str,
        require_completed: bool = False,
        allow_superseded: bool = False,
    ) -> IMPLMetadata:
        """Parse and validate IMPL - raise ValueError on any issue.

        Args:
            path: Path to IMPL file
            content: Full file content
            require_completed: If True, enforce status must be ✅ Completed
            allow_superseded: If True, allow ⚪ Hold or ⏸️ Paused status (used for superseded)

        Returns:
            IMPLMetadata with all parsed fields

        Raises:
            ValueError: On any validation failure
        """
        # Extract spec ID from filename
        spec_id = self._extract_spec_id(path)

        # Extract header
        header_content = "\n".join(content.split("\n")[:30])

        # Validate and extract type (defaults to Feature if omitted)
        spec_type = self._validate_type(header_content, path)

        # Validate and extract status
        status = self._validate_status(header_content, path)

        # Status validation based on mode
        if require_completed and status != IMPLStatus.COMPLETED.value:
            raise ValueError(
                f"❌ Completed file {path.name} has wrong status: {status}\n"
                f"   Completed files MUST have status: {IMPLStatus.COMPLETED.value}\n"
                f"   ➜ Fix the status or move the file out of completed directory."
            )
        if not require_completed and not allow_superseded and status == IMPLStatus.COMPLETED.value:
            raise ValueError(
                f"❌ Active file {path.name} has completed status: {status}\n"
                f"   Active IMPLs MUST NOT have status: "
                f"{IMPLStatus.COMPLETED.value}\n"
                f"   ➜ Use {IMPLStatus.READY.value} (ready to archive) or "
                f"move the file into the completed directory."
            )

        # Validate and extract LOE
        loe = self._validate_loe(header_content, path)

        # CRITICAL: Fail if deps: declaration found in IMPL header
        # (Section headers like "## Dependencies" are OK in content)
        if re.search(r"^deps:\s*\[", header_content, re.MULTILINE):
            raise ValueError(
                f"❌ IMPL contains dependencies in {path.name}\n"
                f"   Dependencies belong ONLY in FR files\n"
                f"   ➜ Remove deps from IMPL, add to FR-{spec_id}-*.md"
            )

        # Parse tasks
        try:
            tasks = self.task_parser.parse(content, path)
        except ValueError as e:
            # Re-raise with context
            raise ValueError(f"Task validation failed:\n{e}") from None

        return IMPLMetadata(
            spec_id=spec_id,
            type=spec_type,
            status=status,
            loe=loe,
            path=path,
            tasks=tasks,
            tasks_total=0,  # Calculated in __post_init__
            tasks_completed=0,
            completion_percent=0,
        )

    def _extract_spec_id(self, path: Path) -> str:
        """Extract and validate spec ID from filename (same as FR)."""
        match = re.match(r"IMPL-([ES]\d{3}[a-z]?)", path.stem, re.IGNORECASE)
        if not match:
            raise ValueError(
                f"❌ Invalid IMPL filename format: {path.name}\n"
                f"   Required format: IMPL-S###-description.md or IMPL-E###-description.md\n"
                f"   Examples: IMPL-S005-feature.md, IMPL-E007-loop.md"
            )

        raw_id = match.group(1)
        try:
            return normalize_spec_ref(raw_id)
        except ValueError:
            raise ValueError(
                f"❌ Invalid ID format in filename: '{raw_id}'\n"
                f"   Valid format: E### or S### (optional suffix)\n"
                f"   Examples: E001, S004, S100a"
            ) from None

    def _validate_type(self, header_content: str, path: Path) -> str:
        """Validate type field (defaults to Feature if omitted).

        Returns:
            Type value (Feature, Enhancement, Bug, ADR, Refactor, Epic)

        Raises:
            ValueError: If type present but invalid format
        """
        match = FR_TYPE_RE.search(header_content)
        if not match:
            # Type field is optional - default to Feature
            return SpecType.FEATURE.value

        type_value = match.group(1)

        # Validate against enum
        try:
            SpecType(type_value)
        except ValueError:
            valid_values = ", ".join([t.value for t in SpecType])
            raise ValueError(
                f"❌ Invalid type value in {path.name}: {type_value}\n"
                f"   Valid values: {valid_values}\n"
                f"   ➜ The fRIMPL is broken - fix it manually."
            ) from None

        return type_value

    def _validate_status(self, header_content: str, path: Path) -> str:
        """Validate status format (emoji + text)."""
        match = IMPL_STATUS_RE.search(header_content)
        if not match:
            # Try to extract what was actually found
            status_line_match = re.search(
                r"^\*\*Status:\*\*\s+(.+?)$", header_content, re.MULTILINE
            )
            found_value = status_line_match.group(1) if status_line_match else "NOT FOUND"

            valid_values = "\n   ".join([s.value for s in IMPLStatus])
            raise ValueError(
                f"❌ Invalid status in {path.name}\n"
                f"   Found: **Status:** {found_value}\n"
                f"   Valid choices:\n   {valid_values}\n"
                f"   ➜ Check for typos like '✅ Complete' (should be '✅ Completed')"
            )

        status_value = match.group(1)

        # Validate against enum
        try:
            IMPLStatus(status_value)
        except ValueError:
            valid_values = "\n   ".join([s.value for s in IMPLStatus])
            raise ValueError(
                f"❌ Invalid status value in {path.name}: {status_value}\n"
                f"   Valid values:\n   {valid_values}\n"
                f"   ➜ The fRIMPL is broken - fix it manually."
            ) from None

        return status_value

    def _validate_loe(self, header_content: str, path: Path) -> str:
        """Validate LOE format: ~Xh, ~Xd, ~Xw.

        Raises:
            ValueError: If LOE missing, wrong format, or invalid unit
        """
        match = LOE_RE.search(header_content)
        if not match:
            # Check if LOE line exists but with wrong format
            loe_line = re.search(
                r"^\*\*(?:LOE|Estimated Effort).*?:\*\*\s*(.+?)$",
                header_content,
                re.MULTILINE,
            )
            if loe_line:
                invalid_value = loe_line.group(1).strip()
                valid_units = ", ".join([u.value for u in LOEUnit])
                raise ValueError(
                    f"❌ Invalid LOE format in {path.name}: '{invalid_value}'\n"
                    f"   Required format: **LOE:** 5d (number + unit, NO TILDE) or **LOE:** N/A\n"
                    f"   Valid units: {valid_units}\n"
                    f"   ➜ Use format like 5d, 3w, 20h, or N/A (retrospective)."
                )
            else:
                raise ValueError(
                    f"❌ Missing required field in {path.name}: LOE\n"
                    f"   Required format: **LOE:** 5d or **LOE:** N/A\n"
                    f"   ➜ The fRIMPL is broken - fix it manually."
                )

        # Handle N/A case (retrospective ADRs with no LOE data)
        if match.group(1) is None:
            # This is an N/A match - return the full matched text
            return match.group(0).split("**LOE:**")[1].strip()

        number = match.group(1)
        unit = match.group(2).lower()

        # Check if this is epic format (has second LOE value)
        if match.group(3) and match.group(4):
            number2 = match.group(3)
            unit2 = match.group(4).lower()

            # Validate both units
            try:
                LOEUnit(unit)
                LOEUnit(unit2)
            except ValueError:
                valid_units = ", ".join([u.value for u in LOEUnit])
                raise ValueError(
                    f"❌ Invalid LOE unit in {path.name}\n"
                    f"   Valid units: {valid_units}\n"
                    f"   ➜ The fRIMPL is broken - use h (hours), d (days), or w (weeks)."
                ) from None

            return f"{number}{unit},{number2}{unit2}"
        else:
            # Validate unit against enum
            try:
                LOEUnit(unit)
            except ValueError:
                valid_units = ", ".join([u.value for u in LOEUnit])
                raise ValueError(
                    f"❌ Invalid LOE unit in {path.name}: '{unit}'\n"
                    f"   Valid units: {valid_units}\n"
                    f"   ➜ The fRIMPL is broken - use h (hours), d (days), or w (weeks)."
                ) from None

            return f"{number}{unit}"
