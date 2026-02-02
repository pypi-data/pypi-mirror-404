"""Task and Acceptance Criteria parsing for fRIMPL progress tracking.

This module provides classes and functions for parsing, validating, and tracking:
- Acceptance Criteria (AC) from FR documents (Success Criteria sections)
- Implementation Tasks from IMPL documents (Day/Phase sections)

Both use checkbox format: `- [ ]` (pending) or `- [x]` (completed)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Regex patterns for parsing
# Matches: - [ ] task, - [x] task, - [~] task (obsolete), - [→S123] task (delegated)
CHECKBOX_RE = re.compile(r"^- \[([ x~]|→[ES]\d{3}[a-z]?)\] (.+)$", re.MULTILINE)
SECTION_RE = re.compile(r"^##+ (.+)$", re.MULTILINE)
# Pattern to extract delegated spec ID
DELEGATED_RE = re.compile(r"^→([ES]\d{3}[a-z]?)$", re.IGNORECASE)
# Pattern to match BLOCKED marker line following a task
BLOCKED_RE = re.compile(r"^\s+- \*\*BLOCKED:\*\*\s+(.+)$")
# Pattern to extract task tag (e.g., #code, #tui, #docs, #infra)
TAG_RE = re.compile(r"\s+#(code|tui|docs|infra)\s*$")

# Verification routes: tag → (run_tests, description)
VERIFICATION_ROUTES: dict[str, tuple[bool, str]] = {
    "code": (True, "Run `make test-quick`"),
    "tui": (True, "Run `make test-quick` + Playwright MCP visual check"),
    "docs": (False, "Markdown lint / link check (no test gate)"),
    "infra": (False, "Manual verification (no test gate)"),
}


@dataclass
class AcceptanceCriteria:
    """Single acceptance criterion from FR checkbox.

    Acceptance criteria define WHAT needs to be delivered for a spec
    to be considered complete. They come from FR Success Criteria sections.

    Example from FR:
        ### Functional Requirements
        - [ ] ScheduledTask entity schema defined
        - [x] Temporal execution engine works
    """

    id: str  # Slugified: "functional-req-1"
    description: str  # "ScheduledTask entity schema defined"
    completed: bool  # False for [ ], True for [x] or [~] (obsolete)
    section: str  # "Functional Requirements"
    category: str  # "functional" | "performance" | "quality" | "documentation"
    line_number: int  # For error reporting

    @property
    def emoji(self) -> str:
        """Status emoji for display."""
        return "✅" if self.completed else "🟡"


@dataclass
class Task:
    """Hierarchical implementation task from IMPL checkbox.

    Tasks define HOW the spec will be implemented. They come from
    IMPL Day/Phase sections and should be actionable work items.
    Tasks can have children (nested list items) forming a tree.

    Example from IMPL:
        ## Day 1: Setup
        - [x] Create directory structure
        - [ ] Write conftest.py
          - Define fixtures
          - Add mock helpers
        - [→220] PostgreSQL adapter (delegated to spec 220)

    The nested items become children of "Write conftest.py".
    """

    id: str  # Slugified: "day1-setup-task1" or explicit "1.1"
    description: str  # "Create directory structure"
    completed: bool  # False for [ ], True for [x], [~] (obsolete), or [→XXX]
    section: str  # "Day 1: Setup"
    line_number: int  # For error reporting
    delegated_to: str | None = None  # Spec ID if delegated (e.g., "220")
    depth: int = 0  # Indentation level (0 = top-level)
    children: list[Task] = field(default_factory=list)
    parent: Task | None = field(default=None, repr=False)  # Back-reference
    spec_id: str | None = None  # Spec this task belongs to (for URI)
    tag: str | None = None  # Verification tag: code, tui, docs, infra (None = code)
    blocked: bool = False  # True if task has a BLOCKED marker
    blocked_reason: str | None = None  # Reason from BLOCKED marker

    @property
    def effective_tag(self) -> str:
        """Return the verification tag, defaulting to 'code'."""
        return self.tag or "code"

    @property
    def verification_route(self) -> tuple[bool, str]:
        """Return (run_tests, description) for this task's verification."""
        return VERIFICATION_ROUTES.get(self.effective_tag, VERIFICATION_ROUTES["code"])

    @property
    def emoji(self) -> str:
        """Status emoji for display."""
        if self.delegated_to:
            return f"→{self.delegated_to}"
        return "✅" if self.completed else "🟡"

    @property
    def path(self) -> str:
        """XPath-style path within spec (no spec prefix).

        Format: /section/task-id/child-id/...
        Example: /day1-setup/1.1/0

        Used for navigation within a spec's task tree.
        """
        parts = []
        node: Task | None = self
        while node is not None:
            if node.id:
                parts.append(node.id)
            node = node.parent

        # Add section as root
        if self.section:
            parts.append(slugify(self.section))

        parts.reverse()
        return "/" + "/".join(parts)

    @property
    def uri(self) -> str:
        """Full praxis:// URI for this task.

        Format: praxis://impl/{spec_id}{path}
        Example: praxis://impl/444/day-1-create-kernel-types/1.1

        Can be pasted into TUI to navigate directly to this task.
        """
        spec = self.spec_id or "unknown"
        return f"praxis://impl/{spec}{self.path}"

    @property
    def short_path(self) -> str:
        """Shortened path showing just immediate context.

        Example: day1-setup/1.1 instead of full path
        """
        if self.parent:
            return f"{slugify(self.section)}/{self.parent.id}/{self.id}"
        return f"{slugify(self.section)}/{self.id}"

    @property
    def is_leaf(self) -> bool:
        """True if this task has no children."""
        return len(self.children) == 0

    @property
    def child_count(self) -> int:
        """Total number of descendants (recursive)."""
        count = len(self.children)
        for child in self.children:
            count += child.child_count
        return count

    @property
    def completion_status(self) -> tuple[int, int]:
        """Return (completed, total) for this task and all descendants."""
        completed = 1 if self.completed else 0
        total = 1
        for child in self.children:
            c, t = child.completion_status
            completed += c
            total += t
        return completed, total


def slugify(text: str) -> str:
    """Convert text to slug format.

    Examples:
        "Functional Requirements" -> "functional-requirements"
        "Day 1: Setup" -> "day1-setup"
    """
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)  # Remove special chars
    text = re.sub(r"[-\s]+", "-", text)  # Convert spaces/dashes to single dash
    return text.strip("-")


def categorize_ac_section(section: str) -> str:
    """Determine category of acceptance criteria section.

    Categories:
        - functional: Feature functionality, behavior, API
        - performance: Speed, throughput, latency, scalability
        - quality: Tests, coverage, documentation, code quality
        - documentation: Docs, guides, examples

    Args:
        section: Section name like "Functional Requirements"

    Returns:
        Category string
    """
    section_lower = section.lower()

    if any(
        kw in section_lower for kw in ["functional", "feature", "behavior", "api", "capability"]
    ):
        return "functional"

    if any(
        kw in section_lower
        for kw in ["performance", "speed", "latency", "throughput", "scalability"]
    ):
        return "performance"

    if any(
        kw in section_lower
        for kw in [
            "quality",
            "test",
            "coverage",
            "code quality",
            "reliability",
            "security",
        ]
    ):
        return "quality"

    if any(kw in section_lower for kw in ["documentation", "docs", "guide", "example"]):
        return "documentation"

    # Default to functional if unclear
    return "functional"


class AcceptanceCriteriaParser:
    """Parse acceptance criteria from FR documents.

    Scans for "Success Criteria" section and extracts checkbox items.
    Each checkbox becomes an AcceptanceCriteria object.
    """

    def parse(self, content: str, path: Path) -> list[AcceptanceCriteria]:
        """Parse all acceptance criteria from FR content.

        Args:
            content: Full FR document text
            path: Path to FR file (for error reporting)

        Returns:
            List of AcceptanceCriteria objects

        Raises:
            ValueError: If checkbox format is invalid
        """
        criteria = []
        lines = content.split("\n")
        current_section = ""
        in_success_criteria = False

        for line_num, line in enumerate(lines, start=1):
            # Track when we enter Success/Acceptance Criteria section
            stripped = line.strip()
            if stripped.startswith("## Success Criteria") or stripped.startswith(
                "## Acceptance Criteria"
            ):
                in_success_criteria = True
                continue

            # Exit Success Criteria section if we hit another top-level section
            if (
                in_success_criteria
                and line.strip().startswith("##")
                and not line.strip().startswith("###")
            ):
                break

            # Track subsections within Success Criteria
            if in_success_criteria and line.strip().startswith("###"):
                current_section = line.strip().lstrip("#").strip()
                continue

            # Parse checkbox items
            if in_success_criteria:
                match = CHECKBOX_RE.match(line)
                if match:
                    checkbox_content = match.group(1)
                    completed = checkbox_content == "x" or checkbox_content == "~"
                    description = match.group(2).strip()

                    # Validate checkbox format strictly
                    if not self._is_valid_checkbox_format(line):
                        raise ValueError(
                            f"❌ Invalid checkbox format in {path.name} line {line_num}:\n"
                            f"   Found: {line.strip()}\n"
                            f"   Required: - [ ] or - [x] (dash, space, bracket, space, bracket)\n"
                            f"   ➜ Fix: Use exactly '- [ ]' or '- [x]'"
                        )

                    # Generate unique ID
                    section_slug = slugify(current_section)
                    ac_id = f"{section_slug}-{len(criteria)}"

                    # Categorize
                    category = categorize_ac_section(current_section)

                    criteria.append(
                        AcceptanceCriteria(
                            id=ac_id,
                            description=description,
                            completed=completed,
                            section=current_section,
                            category=category,
                            line_number=line_num,
                        )
                    )

        return criteria

    def _is_valid_checkbox_format(self, line: str) -> bool:
        """Validate strict checkbox format.

        Valid:
            - [ ] Description (pending)
            - [x] Description (completed)
            - [~] Description (obsolete/N/A)

        Invalid:
            * [ ] Description  (asterisk instead of dash)
            -[ ] Description   (no space after dash)
            - [] Description   (no space in brackets)
            - [X] Description  (uppercase X)
        """
        stripped = line.strip()
        return (
            stripped.startswith("- [ ] ")
            or stripped.startswith("- [x] ")
            or stripped.startswith("- [~] ")
        )


class TaskParser:
    """Parse hierarchical implementation tasks from IMPL documents.

    Scans for Day/Phase sections and extracts checkbox items and nested
    list items. Builds a tree structure based on indentation.

    Example IMPL structure:
        ## Day 1: Setup
        - [x] Create directory structure
        - [ ] Write conftest.py
          - Define fixtures
          - Add mock helpers
        - [→220] PostgreSQL adapter

    The nested items become children of "Write conftest.py".
    """

    # Pattern for any list item (checkbox or plain)
    LIST_ITEM_RE = re.compile(r"^(\s*)- (.+)$")
    # Pattern specifically for checkboxes
    CHECKBOX_ITEM_RE = re.compile(r"^(\s*)- \[([ x~]|→\d{3})\] (.+)$")

    def parse(self, content: str, path: Path) -> list[Task]:
        """Parse all tasks from IMPL content into a tree structure.

        Args:
            content: Full IMPL document text
            path: Path to IMPL file (for error reporting)

        Returns:
            List of top-level Task objects (children nested within)

        Raises:
            ValueError: If task format is invalid
        """
        root_tasks: list[Task] = []  # Top-level tasks per section
        lines = content.split("\n")
        current_section = ""
        task_counter = 0

        # Stack to track parent tasks at each depth level
        # parent_stack[depth] = task at that depth (or None for root)
        parent_stack: list[Task | None] = [None] * 20  # Support up to 20 levels

        for line_num, line in enumerate(lines, start=1):
            # Track current task section (## or ### headers)
            stripped = line.strip()
            if stripped.startswith("##"):
                header_text = stripped.lstrip("#").strip()
                if self._is_task_section(header_text):
                    current_section = header_text
                    # Reset parent stack and task counter for new section
                    parent_stack = [None] * 20
                    task_counter = 0
                else:
                    # Any other header exits the current task section
                    # (e.g., "Execution Notes", "Session Notes", etc.)
                    current_section = ""
                    parent_stack = [None] * 20
                continue

            # Skip if not in a Day/Phase section
            if not current_section:
                continue

            # Try to match checkbox item first
            checkbox_match = self.CHECKBOX_ITEM_RE.match(line)
            if checkbox_match:
                indent = checkbox_match.group(1)
                checkbox_content = checkbox_match.group(2)
                description = checkbox_match.group(3).strip()
                depth = len(indent) // 2  # Assume 2-space indentation

                # Determine completion state and delegation
                delegated_to: str | None = None
                if checkbox_content == "x" or checkbox_content == "~":
                    completed = True
                elif checkbox_content == " ":
                    completed = False
                else:
                    delegated_match = DELEGATED_RE.match(checkbox_content)
                    if delegated_match:
                        delegated_to = delegated_match.group(1)
                        completed = True
                    else:
                        completed = False

                # Peek at next line for BLOCKED marker
                blocked = False
                blocked_reason: str | None = None
                if line_num < len(lines):  # line_num is 1-indexed, check next
                    next_line = lines[line_num]  # lines[line_num] is the next line
                    blocked_match = BLOCKED_RE.match(next_line)
                    if blocked_match:
                        blocked = True
                        blocked_reason = blocked_match.group(1).strip()

                parent = parent_stack[depth - 1] if depth > 0 else None
                task = self._create_task(
                    description=description,
                    completed=completed,
                    section=current_section,
                    line_number=line_num,
                    delegated_to=delegated_to,
                    depth=depth,
                    task_counter=task_counter,
                    parent=parent,
                )
                task.blocked = blocked
                task.blocked_reason = blocked_reason
                task_counter += 1

                self._attach_to_parent(task, depth, parent_stack, root_tasks)
                continue

            # NOTE: Plain list items (non-checkbox bullets) are NOT captured as tasks.
            # Only checkbox items (- [ ], - [x], - [~], - [→XXX]) are tracked.
            # Plain bullets are documentation/notes, not actionable tasks.

        return root_tasks

    def _create_task(
        self,
        description: str,
        completed: bool,
        section: str,
        line_number: int,
        delegated_to: str | None,
        depth: int,
        task_counter: int,
        parent: Task | None = None,
    ) -> Task:
        """Create a Task with generated ID."""
        # Extract tag from end of description (e.g., "Add auth middleware #code")
        tag: str | None = None
        tag_match = TAG_RE.search(description)
        if tag_match:
            tag = tag_match.group(1)
            description = description[: tag_match.start()].rstrip()

        # Extract task ID if present (e.g., "**1.1**: Description")
        task_id = ""
        clean_desc = description
        if description.startswith("**") and "**:" in description:
            id_end = description.index("**:")
            task_id = description[2:id_end]
            clean_desc = description[id_end + 4 :].strip()

        # Generate ID
        if task_id:
            generated_id = task_id
        elif parent:
            # Children get parent ID + index
            child_idx = len(parent.children)
            generated_id = f"{parent.id}.{child_idx}"
        else:
            # Special case: Definition of Done uses "dod-N" format
            if section.lower() == "definition of done":
                generated_id = f"dod-{task_counter + 1}"  # 1-indexed for user-friendliness
            else:
                section_slug = slugify(section)
                generated_id = f"{section_slug}-{task_counter}"

        return Task(
            id=generated_id,
            description=clean_desc if task_id else description,
            completed=completed,
            section=section,
            line_number=line_number,
            delegated_to=delegated_to,
            depth=depth,
            tag=tag,
        )

    def _attach_to_parent(
        self,
        task: Task,
        depth: int,
        parent_stack: list[Task | None],
        root_tasks: list[Task],
    ) -> None:
        """Attach task to its parent based on depth, or to root list."""
        if depth == 0:
            # Top-level task
            root_tasks.append(task)
            task.parent = None
        else:
            # Find parent at previous depth
            parent = parent_stack[depth - 1]
            if parent:
                task.parent = parent
                parent.children.append(task)
            else:
                # No parent found, treat as root
                root_tasks.append(task)

        # Update stack: this task becomes the parent for deeper items
        parent_stack[depth] = task
        # Clear deeper levels (they're no longer valid parents)
        for i in range(depth + 1, len(parent_stack)):
            parent_stack[i] = None

    def flatten(self, tasks: list[Task]) -> list[Task]:
        """Flatten hierarchical tasks into a flat list (for backward compatibility).

        Performs depth-first traversal to return all tasks.
        """
        result: list[Task] = []
        for task in tasks:
            result.append(task)
            if task.children:
                result.extend(self.flatten(task.children))
        return result

    # Section prefixes that contain trackable tasks
    TASK_SECTION_PREFIXES = (
        # Minimal template sections
        "Tasks",  # Main tasks section (new minimal template)
        "Definition of Done",  # DoD checklist (new minimal template)
        # Legacy template sections (for existing specs)
        "Day ",  # Daily roadmap sections
        "Phase ",  # Phase tracking sections
        "Gate ",  # Validation gate sections (Gate 1:, Gate 4:)
        "Testing Checklist",  # Testing checklist section
        "Completion Checklist",  # Final completion checklist
        "Implementation Verification",  # Implementation verification checklist
        "Validation Gates",  # Validation gates section
        "Code Quality",  # Completion sub-section
        "Testing",  # Completion sub-section (standalone)
        "Documentation",  # Completion sub-section
        "Quality Gates",  # Completion sub-section
        "Nspec Hygiene",  # Completion sub-section
        "Before Starting",  # Testing checklist sub-section
        "During Implementation",  # Testing checklist sub-section
        "Before Ending",  # Testing checklist sub-section
        "Before Marking",  # Testing checklist sub-section
        "Manual Verification",  # Gate 4 sub-section
    )

    def _is_task_section(self, header_text: str) -> bool:
        """Check if a header indicates a section that contains trackable tasks.

        Args:
            header_text: The header text without leading # symbols

        Returns:
            True if this section should have its checkboxes parsed as tasks
        """
        return any(header_text.startswith(prefix) for prefix in self.TASK_SECTION_PREFIXES)

    def _is_valid_checkbox_format(self, line: str) -> bool:
        """Validate strict checkbox format.

        Valid formats:
            - [ ] Description (pending)
            - [x] Description (completed)
            - [~] Description (obsolete/N/A)
            - [→XXX] Description (delegated to spec XXX)
        """
        stripped = line.strip()
        if (
            stripped.startswith("- [ ] ")
            or stripped.startswith("- [x] ")
            or stripped.startswith("- [~] ")
        ):
            return True
        # Check for delegation format: - [→XXX]
        if stripped.startswith("- [→") and "] " in stripped:
            # Extract content between brackets
            bracket_content = stripped[4 : stripped.index("] ")]
            return bool(re.match(r"^\d{3}$", bracket_content))
        return False

    def _is_valid_section_format(self, line: str) -> bool:
        """Validate section format: ## Day X: or ## Phase X:"""
        stripped = line.strip().lstrip("#").strip()
        return (stripped.startswith("Day ") and ":" in stripped) or (
            stripped.startswith("Phase ") and ":" in stripped
        )

    def _starts_with_action_verb(self, description: str) -> bool:
        """Check if task description starts with action verb.

        Common action verbs:
            Create, Implement, Write, Add, Update, Fix, Test, Run,
            Configure, Setup, Install, Deploy, Build, Remove, Delete
        """
        action_verbs = {
            "create",
            "implement",
            "write",
            "add",
            "update",
            "fix",
            "test",
            "run",
            "configure",
            "setup",
            "install",
            "deploy",
            "build",
            "remove",
            "delete",
            "refactor",
            "migrate",
            "validate",
            "verify",
            "ensure",
            "check",
            "review",
            "document",
            "archive",
            "move",
            "rename",
            "generate",
            "parse",
            "extract",
            "analyze",
            "publish",
            "design",
            "plan",
            "define",
            "prepare",
            "initialize",
            "load",
            "save",
            "fetch",
            "send",
            "receive",
            "process",
            "transform",
            "convert",
            "execute",
            "invoke",
            "call",
            "launch",
            "start",
            "stop",
            "resume",
            "pause",
            "integrate",
            "connect",
            "link",
            "merge",
            "combine",
            "join",
            "split",
            "separate",
            "isolate",
            "enable",
            "disable",
            "toggle",
            "switch",
            "activate",
            "deactivate",
            "keep",
            "maintain",
            "extend",
            "expand",
            "capture",
            "externalize",
            "draft",
            "seed",
            "swap",
            "honor",
            "respect",
            "notify",
            "announce",
            "close",
            "ship",
            "monitor",
            "compose",
            "render",
            "emit",
            "surface",
            "gather",
            "collect",
            "aggregate",
            "record",
            "log",
            "trace",
            "snapshot",
            "wire",
            "handle",
            "identify",
            "expose",
            "enhance",
            "establish",
            "detect",
            "optimize",
            "populate",
            "provide",
            "apply",
            "calculate",
            "display",
            "filter",
            "track",
            "support",
            "confirm",
            "introduce",
            "deduplicate",
            "highlight",
            "refresh",
            "restore",
            "rebuild",
            "map",
            "persist",
            "replace",
            "raise",
            "trigger",
            "subscribe",
            "show",
            "cover",
            "align",
            "begin",
        }

        first_word = description.split()[0].lower() if description.split() else ""
        return first_word in action_verbs

    def _validate_no_empty_sections(self, content: str, path: Path) -> None:
        """Validate all Day/Phase sections have at least one task."""
        lines = content.split("\n")
        current_section = ""
        current_section_line = 0
        current_section_tasks = 0

        for line_num, line in enumerate(lines, start=1):
            # New section
            if line.strip().startswith("## Day ") or line.strip().startswith("## Phase "):
                # Check previous section if it exists
                if current_section and current_section_tasks == 0:
                    raise ValueError(
                        f"❌ Empty section in {path.name} line {current_section_line}:\n"
                        f"   Section: {current_section}\n"
                        f"   Problem: No tasks found under this section\n"
                        f"   ➜ Fix: Add tasks or remove empty section"
                    )

                current_section = line.strip().lstrip("#").strip()
                current_section_line = line_num
                current_section_tasks = 0
                continue

            # Count tasks in current section
            if CHECKBOX_RE.match(line):
                current_section_tasks += 1

        # Check last section
        if current_section and current_section_tasks == 0:
            raise ValueError(
                f"❌ Empty section in {path.name} line {current_section_line}:\n"
                f"   Section: {current_section}\n"
                f"   Problem: No tasks found under this section\n"
                f"   ➜ Fix: Add tasks or remove empty section"
            )


# --- URI Parsing and Resolution ---


@dataclass
class URIResolution:
    """Result of resolving a praxis:// URI."""

    success: bool
    spec_id: str | None = None
    task: Task | None = None
    path: str = ""
    error: str | None = None
    suggestions: list[str] = field(default_factory=list)  # "Did you mean?" hints


def parse_uri(uri: str) -> tuple[str | None, str]:
    """Parse a praxis:// URI into (spec_id, path).

    Format: praxis://impl/{spec_id}/{section}/{task_id}/...
    Example: praxis://impl/444/day-1-create-kernel-types/1.1

    Returns:
        (spec_id, path) tuple, or (None, "") if invalid
    """
    if not uri.startswith("praxis://impl/"):
        return None, ""

    # Strip scheme
    rest = uri[len("praxis://impl/") :]
    parts = rest.split("/", 1)

    if len(parts) == 1:
        return parts[0], ""
    return parts[0], "/" + parts[1]


def resolve_path(tasks: list[Task], path: str) -> Task | None:
    """Resolve a path to a Task within a task tree.

    Args:
        tasks: List of root tasks
        path: Path like /day-1-create-kernel-types/1.1/0

    Returns:
        Matching Task or None
    """
    if not path or path == "/":
        return None

    # Split path into segments
    segments = [s for s in path.strip("/").split("/") if s]
    if not segments:
        return None

    # First segment is section, find tasks in that section
    section_slug = segments[0]
    current_tasks = [t for t in tasks if slugify(t.section) == section_slug]

    if not current_tasks:
        return None

    # If only section specified, return None (it's a section, not a task)
    if len(segments) == 1:
        return None

    # Navigate through remaining segments
    for segment in segments[1:]:
        found = None
        for task in current_tasks:
            if task.id == segment:
                found = task
                break
        if found:
            current_tasks = found.children
        else:
            return None

    return found


def find_similar_paths(tasks: list[Task], path: str, max_results: int = 5) -> list[str]:
    """Find paths similar to the given path (for 'did you mean?' suggestions).

    Uses simple substring/prefix matching and Levenshtein-like heuristics.
    """
    target_segments = [s for s in path.strip("/").split("/") if s]
    if not target_segments:
        return []

    suggestions: list[tuple[int, str]] = []  # (score, path)

    def score_task(task: Task) -> int:
        """Score how similar task path is to target."""
        task_segments = [s for s in task.path.strip("/").split("/") if s]
        score = 0

        # Exact segment matches
        for i, seg in enumerate(target_segments):
            if i < len(task_segments):
                if task_segments[i] == seg:
                    score += 10
                elif seg in task_segments[i] or task_segments[i] in seg:
                    score += 5

        # Penalize length difference
        score -= abs(len(task_segments) - len(target_segments)) * 2

        return score

    def collect_paths(task_list: list[Task]) -> None:
        for task in task_list:
            score = score_task(task)
            if score > 0:
                suggestions.append((score, task.path))
            if task.children:
                collect_paths(task.children)

    collect_paths(tasks)

    # Sort by score descending and return top results
    suggestions.sort(key=lambda x: x[0], reverse=True)
    return [path for _, path in suggestions[:max_results]]
