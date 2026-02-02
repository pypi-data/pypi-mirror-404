"""nspec MCP Server — Expose backlog tools via Model Context Protocol.

Provides both stdio and SSE transports for AI coding assistant integration.
Each tool is a thin wrapper calling existing crud/reports/session functions.

Usage:
    nspec-mcp          # stdio transport (default, for Claude Code)
    nspec-mcp --sse    # SSE transport (for web clients)
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("nspec.mcp")

mcp = FastMCP(
    "nspec",
    instructions="Specification-driven backlog management tools for AI-native development",
)


def _resolve_docs_root(docs_root: str | None = None) -> Path:
    """Resolve docs root path, defaulting to ./docs.

    When no config.toml exists and no NSPEC_* env vars are set,
    silently creates a default config (MCP is non-interactive).
    Also applies configurable emojis from config.toml.
    """
    root = Path(docs_root) if docs_root else Path("docs")
    resolved = root.resolve()
    logger.debug("docs_root: %s (resolved: %s, exists: %s)", root, resolved, resolved.exists())

    project_root = root.parent
    try:
        from nspec.init import needs_init

        if needs_init(project_root):
            from nspec.config import NspecConfig

            NspecConfig.scaffold(project_root)
    except OSError:
        pass  # Read-only filesystem or other I/O issue

    # Apply configurable emojis from config.toml
    try:
        from nspec.config import NspecConfig
        from nspec.statuses import configure as configure_statuses

        config = NspecConfig.load(project_root)
        configure_statuses(config.emojis)
    except Exception:
        pass  # Don't break MCP on config issues

    return root


def _run_test_gate() -> tuple[bool, str]:
    """Run make test-quick as a quality gate.

    Returns:
        (passed, output) tuple
    """
    try:
        result = subprocess.run(
            ["make", "test-quick"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        return passed, output.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, f"Test gate failed: {e}"


def _get_task_tag(spec_id: str, task_id: str, docs_root: Path) -> str:
    """Get the verification tag for a task, defaulting to 'code'.

    Loads the IMPL file, parses tasks, and finds the matching task
    to read its tag. Returns 'code' if task not found or no tag set.
    """
    from nspec.datasets import DatasetLoader
    from nspec.tasks import TaskParser

    try:
        loader = DatasetLoader(docs_root)
        datasets = loader.load()
        impl = datasets.get_impl(spec_id)
        if impl and impl.tasks:
            parser = TaskParser()
            flat = parser.flatten(impl.tasks)
            for task in flat:
                if task.id == task_id:
                    return task.effective_tag
    except Exception:
        pass
    return "code"


def _compute_task_progress(impl_path: Path) -> dict[str, Any]:
    """Read an IMPL file and return task progress counts.

    Returns dict with 'done', 'total', 'remaining' keys.
    """
    import re

    try:
        content = impl_path.read_text()
    except OSError:
        return {}

    done = len(re.findall(r"^\s*- \[x\]", content, re.MULTILINE))
    obsolete = len(re.findall(r"^\s*- \[~\]", content, re.MULTILINE))
    pending = len(re.findall(r"^\s*- \[ \]", content, re.MULTILINE))
    total = done + obsolete + pending

    remaining: list[str] = []
    for line in content.split("\n"):
        if re.match(r"^\s*- \[ \]", line):
            remaining.append(line.strip().removeprefix("- [ ] "))

    return {
        "done": done + obsolete,
        "total": total,
        "remaining_tasks": remaining[:10],  # Cap at 10 to avoid huge responses
    }


def _find_epic_for_spec(spec_id: str, docs_root: Path) -> str | None:
    """Find which epic a spec belongs to by scanning epic FR deps lines."""
    import re

    from nspec.paths import get_paths

    paths = get_paths(docs_root)
    for fr_file in paths.active_frs_dir.glob("FR-*.md"):
        try:
            content = fr_file.read_text()
        except OSError:
            continue

        # Check if this is an epic (priority starts with E)
        priority_match = re.search(r"\*\*Priority:\*\*\s*\S+\s*(E\d)", content)
        if not priority_match:
            continue

        # Check if spec_id is in this epic's deps
        deps_match = re.search(r"^deps:\s*\[([^\]]*)\]", content, re.MULTILINE)
        if not deps_match:
            continue

        dep_ids = [d.strip() for d in deps_match.group(1).split(",") if d.strip()]
        if spec_id in dep_ids:
            # Extract epic's spec_id from filename
            name_match = re.match(r"FR-([ES]\d{3}[a-z]?)-", fr_file.name, re.IGNORECASE)
            if name_match:
                return name_match.group(1)

    return None


# ---------------------------------------------------------------------------
# Query Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def epics(docs_root: str | None = None) -> dict[str, Any]:
    """List all epics with progress tracking.

    Shows epic ID, priority, title, and completion percentages
    for specs grouped under each epic.

    Args:
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.reports import ReportContext, epic_summary_report

    root = _resolve_docs_root(docs_root)
    ctx = ReportContext.load(root)
    return epic_summary_report(ctx)


@mcp.tool()
def show(spec_id: str, docs_root: str | None = None) -> dict[str, Any]:
    """Show full details for a spec (FR + IMPL).

    Returns title, priority, status, acceptance criteria,
    tasks, dependencies, and completion progress.

    Args:
        spec_id: ID (e.g., "S004", "E001")
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.datasets import DatasetLoader

    root = _resolve_docs_root(docs_root)
    loader = DatasetLoader(root)
    datasets = loader.load()

    fr = datasets.get_fr(spec_id)
    impl = datasets.get_impl(spec_id)

    if not fr and not impl:
        return {"error": f"Spec {spec_id} not found"}

    result: dict[str, Any] = {"spec_id": spec_id}

    if fr:
        result["fr"] = {
            "title": fr.title,
            "priority": fr.priority,
            "status": fr.status,
            "deps": fr.deps,
            "ac_completion": fr.ac_completion_percent,
        }

    if impl:
        result["impl"] = {
            "status": impl.status,
            "loe": impl.loe,
            "completion": impl.completion_percent,
        }

    result["is_active"] = datasets.is_active(spec_id)
    return result


@mcp.tool()
def next_spec(epic_id: str | None = None, docs_root: str | None = None) -> dict[str, Any]:
    """Find the next spec to work on based on priority and blockers.

    Returns the highest-priority unblocked spec, optionally
    filtered to a specific epic.

    Args:
        epic_id: Optional epic ID to filter by
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.datasets import DatasetLoader
    from nspec.reports import ReportContext, blockers_report
    from nspec.validator import NspecValidator

    root = _resolve_docs_root(docs_root)
    loader = DatasetLoader(root)
    datasets = loader.load()

    # Get blocked spec IDs
    ctx = ReportContext(datasets=datasets, docs_root=root)
    blockers = blockers_report(ctx)
    blocked_ids = set()
    for section in blockers.get("sections", []):
        if section.get("type") == "blockers":
            for b in section.get("data", []):
                blocked_ids.add(b["id"])

    # Use TUI's epic-aware ordering for consistent pick order
    validator = NspecValidator(docs_root=root)
    validator.datasets = datasets
    tui_order = validator._generate_ordered_nspec()

    # Priority ranking (for response metadata only)
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

    # Build candidate set with eligibility filtering
    eligible: dict[str, dict[str, Any]] = {}
    epic_scope: set[str] | None = None
    if epic_id:
        epic_fr = datasets.get_fr(epic_id)
        epic_scope = set(epic_fr.deps) if epic_fr and epic_fr.deps else set()

    for spec_id, fr in datasets.active_frs.items():
        if fr.type == "Epic":
            continue  # Skip epics
        if spec_id in blocked_ids:
            continue

        # Filter by epic if specified
        if epic_scope is not None and spec_id not in epic_scope:
            continue

        impl = datasets.active_impls.get(spec_id)
        if impl and ("Ready" in impl.status or "Completed" in impl.status):
            continue  # Already done
        if impl and ("Paused" in impl.status):
            continue  # Parked
        if impl and impl.has_blocked_tasks:
            continue  # Has blocked tasks

        rank = priority_rank.get(fr.priority, 9)
        eligible[spec_id] = {
            "spec_id": spec_id,
            "title": fr.title,
            "priority": fr.priority,
            "priority_rank": rank,
            "status": impl.status if impl else "Unknown",
            "completion": impl.completion_percent if impl else 0,
        }

    # Order candidates by TUI display order
    candidates = [eligible[sid] for sid in tui_order if sid in eligible]

    if not candidates:
        return {"message": "No unblocked specs found", "candidates": []}

    return {"next": candidates[0], "alternatives": candidates[1:5]}


@mcp.tool()
def get_epic(docs_root: str | None = None) -> dict[str, str | None]:
    """Get the currently active epic from .novabuilt.dev/nspec/state.json.

    Args:
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.session import StateDAO

    dao = StateDAO(Path.cwd())
    epic = dao.get_active_epic()
    if epic:
        return {"active_epic": epic}
    return {"active_epic": None, "message": "No active epic set"}


@mcp.tool()
def validate(docs_root: str | None = None) -> dict[str, Any]:
    """Run the 6-layer validation engine on all specs.

    Checks format, existence, dependencies, business logic,
    and ordering across all FR and IMPL documents.

    Args:
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.validator import NspecValidator

    root = _resolve_docs_root(docs_root)
    validator = NspecValidator(root)
    success, errors = validator.validate()
    return {
        "valid": success,
        "error_count": len(errors),
        "errors": errors[:50],  # Cap at 50 to avoid huge responses
    }


@mcp.tool()
def session_start(spec_id: str, docs_root: str | None = None) -> str:
    """Initialize a work session for a spec.

    Shows where work left off, pending tasks, blockers,
    and suggested first action.

    Args:
        spec_id: Spec ID to start working on
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.session import initialize_session

    root = _resolve_docs_root(docs_root)
    return initialize_session(spec_id, root)


# ---------------------------------------------------------------------------
# Mutation Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def task_complete(
    spec_id: str,
    task_id: str,
    marker: str = "x",
    run_tests: bool = True,
    docs_root: str | None = None,
) -> dict[str, Any]:
    """Mark an IMPL task as complete.

    By default runs `make test-quick` before marking the task.
    Set run_tests=False to skip the test gate.

    Args:
        spec_id: ID (e.g., "S004")
        task_id: Task number (e.g., "1", "2.1", "dod-1")
        marker: "x" for complete, "~" for obsolete
        run_tests: Run test gate before marking (default: True)
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import check_impl_task
    from nspec.tasks import VERIFICATION_ROUTES

    root = _resolve_docs_root(docs_root)

    # Check task tag to determine verification route
    task_tag = _get_task_tag(spec_id, task_id, root)
    should_run_tests, verification_hint = VERIFICATION_ROUTES.get(
        task_tag, VERIFICATION_ROUTES["code"]
    )

    if run_tests and should_run_tests:
        passed, output = _run_test_gate()
        if not passed:
            return {
                "success": False,
                "reason": "Test gate failed — task not marked",
                "test_output": output[-2000:],  # Last 2000 chars
            }

    path = check_impl_task(spec_id, task_id, root, marker=marker)

    # Compute progress from the updated file
    progress = _compute_task_progress(path)

    result: dict[str, Any] = {
        "success": True,
        "path": str(path),
        "task_id": task_id,
        "marker": marker,
        "tag": task_tag,
        "verification": verification_hint,
        **progress,
    }

    if progress.get("done") == progress.get("total") and progress.get("total", 0) > 0:
        result["next_action"] = (
            f"All {progress['total']} tasks complete. "
            "Call criteria_complete for any remaining ACs, then advance to move to Testing."
        )

    return result


@mcp.tool()
def criteria_complete(
    spec_id: str,
    criteria_id: str,
    marker: str = "x",
    run_tests: bool = True,
    docs_root: str | None = None,
) -> dict[str, Any]:
    """Mark an acceptance criterion as complete in the FR file.

    By default runs `make test-quick` before marking.
    Set run_tests=False to skip the test gate.

    Args:
        spec_id: ID (e.g., "S004")
        criteria_id: Criterion ID (e.g., "AC-F1", "AC-Q2")
        marker: "x" for complete, "~" for obsolete
        run_tests: Run test gate before marking (default: True)
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import check_acceptance_criteria

    root = _resolve_docs_root(docs_root)

    if run_tests:
        passed, output = _run_test_gate()
        if not passed:
            return {
                "success": False,
                "reason": "Test gate failed — criterion not marked",
                "test_output": output[-2000:],
            }

    path = check_acceptance_criteria(spec_id, criteria_id, root, marker=marker)
    return {
        "success": True,
        "path": str(path),
        "criteria_id": criteria_id,
        "marker": marker,
    }


@mcp.tool()
def activate(spec_id: str, docs_root: str | None = None) -> dict[str, Any]:
    """Activate a spec by advancing its status and writing state.json.

    Sets IMPL to Active and FR to Active, and persists the spec ID
    to .novabuilt.dev/nspec/state.json for tool integration.

    Args:
        spec_id: Spec ID to activate
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import set_status
    from nspec.session import StateDAO

    root = _resolve_docs_root(docs_root)

    # Set FR=Active(2), IMPL=Active(1)
    fr_path, impl_path = set_status(spec_id, 2, 1, root)

    # Persist spec_id to state.json
    dao = StateDAO(Path.cwd())
    dao.set_spec_id(spec_id)

    # Auto-detect epic: find which epic FR lists this spec as a dependency
    epic_id = _find_epic_for_spec(spec_id, root)
    if epic_id:
        dao.set_active_epic(epic_id)

    return {
        "success": True,
        "spec_id": spec_id,
        "epic_id": epic_id,
        "fr_path": str(fr_path),
        "impl_path": str(impl_path),
    }


@mcp.tool()
def advance(spec_id: str, docs_root: str | None = None) -> dict[str, Any]:
    """Advance a spec to the next logical status.

    Progresses IMPL through: Planning -> Active -> Testing -> Ready.
    Also auto-upgrades FR status when appropriate.

    Args:
        spec_id: Spec ID to advance
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import next_status

    root = _resolve_docs_root(docs_root)
    fr_path, impl_path = next_status(spec_id, root)
    return {
        "success": True,
        "spec_id": spec_id,
        "fr_path": str(fr_path),
        "impl_path": str(impl_path),
    }


@mcp.tool()
def complete(spec_id: str, docs_root: str | None = None) -> dict[str, Any]:
    """Complete a spec and archive it to completed/done.

    Validates that all acceptance criteria and tasks are checked
    before archiving.

    Args:
        spec_id: Spec ID to complete
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import complete_spec
    from nspec.session import clear_session

    root = _resolve_docs_root(docs_root)
    fr_old, fr_new, impl_old, impl_new = complete_spec(spec_id, root)

    # Auto-clear session state on spec completion
    clear_session(Path.cwd())

    return {
        "success": True,
        "spec_id": spec_id,
        "fr_moved": f"{fr_old} -> {fr_new}",
        "impl_moved": f"{impl_old} -> {impl_new}",
    }


@mcp.tool()
def task_block(
    spec_id: str,
    task_id: str,
    reason: str,
    docs_root: str | None = None,
) -> dict[str, Any]:
    """Mark an IMPL task as blocked with a reason.

    Inserts a BLOCKED marker line after the task in the IMPL file.

    Args:
        spec_id: ID (e.g., "S004")
        task_id: Task number (e.g., "1", "2.1")
        reason: Why the task is blocked
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import set_task_blocked

    root = _resolve_docs_root(docs_root)
    path = set_task_blocked(spec_id, task_id, reason, root)
    return {
        "success": True,
        "path": str(path),
        "task_id": task_id,
        "reason": reason,
    }


@mcp.tool()
def task_unblock(
    spec_id: str,
    task_id: str,
    docs_root: str | None = None,
) -> dict[str, Any]:
    """Remove the BLOCKED marker from an IMPL task.

    Args:
        spec_id: ID (e.g., "S004")
        task_id: Task number (e.g., "1", "2.1")
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import set_task_unblocked

    root = _resolve_docs_root(docs_root)
    path = set_task_unblocked(spec_id, task_id, root)
    return {
        "success": True,
        "path": str(path),
        "task_id": task_id,
    }


@mcp.tool()
def park(
    spec_id: str,
    reason: str | None = None,
    docs_root: str | None = None,
) -> dict[str, Any]:
    """Park a spec by setting IMPL status to Paused.

    Use this when a spec is blocked and cannot proceed.

    Args:
        spec_id: Spec ID to park
        reason: Optional reason for parking
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import park_spec

    root = _resolve_docs_root(docs_root)
    fr_path, impl_path = park_spec(spec_id, root, reason=reason)
    result: dict[str, Any] = {
        "success": True,
        "spec_id": spec_id,
        "fr_path": str(fr_path),
        "impl_path": str(impl_path),
    }
    if reason:
        result["reason"] = reason
    return result


@mcp.tool()
def blocked_specs(
    docs_root: str | None = None,
) -> dict[str, Any]:
    """List specs that have blocked tasks or are paused.

    Scans active IMPLs for BLOCKED task markers and Paused status.

    Args:
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.datasets import DatasetLoader

    root = _resolve_docs_root(docs_root)
    loader = DatasetLoader(root)
    datasets = loader.load()

    def _collect_blocked(tasks: list, out: list[str]) -> None:
        for task in tasks:
            if task.blocked and task.blocked_reason:
                out.append(f"Task {task.id}: {task.blocked_reason}")
            if task.children:
                _collect_blocked(task.children, out)

    blocked: list[dict[str, Any]] = []
    for spec_id, impl in datasets.active_impls.items():
        reasons: list[str] = []
        is_paused = "Paused" in impl.status

        _collect_blocked(impl.tasks, reasons)

        if reasons or is_paused:
            fr = datasets.get_fr(spec_id)
            blocked.append(
                {
                    "spec_id": spec_id,
                    "title": fr.title if fr else f"Spec {spec_id}",
                    "status": impl.status,
                    "is_paused": is_paused,
                    "blocked_tasks": reasons,
                }
            )

    return {
        "count": len(blocked),
        "specs": blocked,
    }


@mcp.tool()
def create_spec(
    title: str,
    priority: str = "P2",
    epic_id: str | None = None,
    docs_root: str | None = None,
) -> dict[str, Any]:
    """Create a new FR+IMPL spec pair.

    Auto-assigns the next available spec ID in the priority range.
    Optionally adds the spec to an epic.

    Args:
        title: Spec title (e.g., "Add search feature")
        priority: Priority level (P0-P3). Default: P2
        epic_id: Optional epic ID to group under
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import create_new_spec, move_dependency

    root = _resolve_docs_root(docs_root)
    fr_path, impl_path, spec_id = create_new_spec(title, priority, root)

    # Verify files exist on disk after creation
    if not fr_path.exists():
        logger.error("create_spec: FR file missing after creation: %s", fr_path)
        return {"success": False, "error": f"FR file not found after creation: {fr_path}"}
    if not impl_path.exists():
        logger.error("create_spec: IMPL file missing after creation: %s", impl_path)
        return {"success": False, "error": f"IMPL file not found after creation: {impl_path}"}

    logger.debug("create_spec: created %s → FR=%s, IMPL=%s", spec_id, fr_path, impl_path)

    result: dict[str, Any] = {
        "success": True,
        "spec_id": spec_id,
        "fr_path": str(fr_path),
        "impl_path": str(impl_path),
    }

    if epic_id:
        # Verify spec is loadable before adding to epic
        from nspec.datasets import DatasetLoader

        try:
            loader = DatasetLoader(root)
            datasets = loader.load()
            if spec_id not in datasets.active_frs:
                logger.warning(
                    "create_spec: spec %s created but not loadable — skipping add_dep to epic %s",
                    spec_id,
                    epic_id,
                )
                result["epic_warning"] = (
                    f"Spec {spec_id} created but failed validation — not added to epic {epic_id}"
                )
                return result
        except ValueError as e:
            logger.warning("create_spec: dataset load failed after create: %s", e)

        move_dependency(spec_id, epic_id, root)
        result["epic_id"] = epic_id

    return result


@mcp.tool()
def set_priority(spec_id: str, priority: str, docs_root: str | None = None) -> dict[str, Any]:
    """Change a spec's priority level.

    Automatically updates dependent spec priorities to maintain
    the priority inheritance rule (child <= parent).

    Args:
        spec_id: Spec ID to update
        priority: New priority (P0-P3)
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import set_priority

    root = _resolve_docs_root(docs_root)
    path = set_priority(spec_id, priority, root)
    return {"success": True, "spec_id": spec_id, "priority": priority, "path": str(path)}


@mcp.tool()
def add_dep(spec_id: str, dep_id: str, docs_root: str | None = None) -> dict[str, Any]:
    """Add a dependency to a spec.

    If the target is an epic and the dependency belongs to another
    epic, it will be automatically moved.

    Args:
        spec_id: Spec ID to add dependency to
        dep_id: Dependency spec ID
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import add_dependency

    root = _resolve_docs_root(docs_root)
    result = add_dependency(spec_id, dep_id, root)
    return {
        "success": True,
        "spec_id": spec_id,
        "dep_id": dep_id,
        "path": str(result["path"]),
        "moved_from": result.get("moved_from"),
    }


@mcp.tool()
def remove_dep(spec_id: str, dep_id: str, docs_root: str | None = None) -> dict[str, Any]:
    """Remove a dependency from a spec.

    Args:
        spec_id: Spec ID to remove dependency from
        dep_id: Dependency spec ID to remove
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.crud import remove_dependency

    root = _resolve_docs_root(docs_root)
    path = remove_dependency(spec_id, dep_id, root)
    return {"success": True, "spec_id": spec_id, "dep_id": dep_id, "path": str(path)}


@mcp.tool()
def session_save(
    spec_id: str,
    task_id: str | None = None,
    notes: str | None = None,
    docs_root: str | None = None,
) -> dict[str, Any]:
    """Persist session state for cross-session handoff.

    Saves spec progress to .novabuilt.dev/nspec/state.json.
    Increments attempt counter for the given task_id.

    Args:
        spec_id: Spec ID being worked on
        task_id: Current task ID (optional)
        notes: Session notes (optional)
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.session import SessionState, load_session, save_session

    project_root = Path.cwd()

    # Load existing session or create new
    existing = load_session(project_root)
    if existing and existing.spec_id == spec_id:
        state = existing
        state.last_task = task_id or state.last_task
        state.notes = notes or state.notes
    else:
        state = SessionState(
            spec_id=spec_id,
            last_task=task_id,
            notes=notes,
        )

    # Increment attempt counter for task
    if task_id:
        state.attempts[task_id] = state.attempts.get(task_id, 0) + 1

    path = save_session(state, project_root)

    result: dict[str, Any] = {
        "success": True,
        "path": str(path),
        "spec_id": spec_id,
        "task_id": task_id,
        "attempts": state.attempts,
    }

    # Auto-park if a task hits 3 consecutive failures
    if task_id and state.attempts.get(task_id, 0) >= 3:
        from nspec.crud import park_spec

        root = _resolve_docs_root(docs_root)
        reason = (
            f"Auto-parked: task {task_id} failed {state.attempts[task_id]} consecutive attempts"
        )
        try:
            park_spec(spec_id, root, reason=reason)
            result["auto_parked"] = True
            result["park_reason"] = reason
        except (FileNotFoundError, ValueError):
            # Already paused or file not found — don't fail the save
            pass

    return result


@mcp.tool()
def session_resume(
    spec_id: str,
    docs_root: str | None = None,
) -> dict[str, Any]:
    """Load persisted session state for a spec.

    Returns saved session context if state.json has a matching spec_id.

    Args:
        spec_id: Spec ID to resume
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.session import load_session

    project_root = Path.cwd()
    state = load_session(project_root)

    if not state or state.spec_id != spec_id:
        return {
            "found": False,
            "spec_id": spec_id,
            "message": f"No saved session for spec {spec_id}",
        }

    return {
        "found": True,
        "spec_id": state.spec_id,
        "last_task": state.last_task,
        "attempts": state.attempts,
        "notes": state.notes,
        "started_at": state.started_at,
        "updated_at": state.updated_at,
    }


@mcp.tool()
def session_clear(
    docs_root: str | None = None,
) -> dict[str, Any]:
    """Delete the session state file.

    Args:
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.session import clear_session

    project_root = Path.cwd()
    deleted = clear_session(project_root)
    return {
        "success": True,
        "deleted": deleted,
    }


@mcp.tool()
def skills_install(docs_root: str | None = None) -> dict[str, Any]:
    """Write resolved skills to `.claude/commands/`.

    Installs built-in nspec skills (and any custom sources from config)
    to the project's `.claude/commands/` directory. Only overwrites files
    that are managed by nspec (have the managed-by header).

    Args:
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.config import NspecConfig
    from nspec.skills import install_skills, resolve_skills

    project_root = Path.cwd()
    config = NspecConfig.load(project_root)
    resolved = resolve_skills(config.skills.sources, project_root=project_root)
    installed = install_skills(project_root, resolved)

    return {
        "success": True,
        "installed": [str(p.relative_to(project_root)) for p in installed],
        "count": len(installed),
    }


@mcp.tool()
def skills_list(docs_root: str | None = None) -> dict[str, Any]:
    """List available skills with source info.

    Returns all resolved skills showing which source each comes from.

    Args:
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.config import NspecConfig
    from nspec.skills import resolve_skills

    project_root = Path.cwd()
    config = NspecConfig.load(project_root)
    resolved = resolve_skills(config.skills.sources, project_root=project_root)

    skills_info = []
    for name, info in sorted(resolved.items()):
        skills_info.append(
            {
                "name": name,
                "source": info.source,
                "size": len(info.content),
            }
        )

    return {
        "sources": config.skills.sources,
        "skills": skills_info,
        "count": len(skills_info),
    }


@mcp.tool()
def skills_sync(docs_root: str | None = None) -> dict[str, Any]:
    """Re-sync skills from sources (update after nspec upgrade).

    Re-resolves skills from configured sources and updates managed
    files in `.claude/commands/`. Useful after `pip install --upgrade nspec`.

    Args:
        docs_root: Path to docs directory (default: ./docs)
    """
    from nspec.config import NspecConfig
    from nspec.skills import install_skills, resolve_skills

    project_root = Path.cwd()
    config = NspecConfig.load(project_root)
    resolved = resolve_skills(config.skills.sources, project_root=project_root)
    installed = install_skills(project_root, resolved)

    return {
        "success": True,
        "synced": [str(p.relative_to(project_root)) for p in installed],
        "count": len(installed),
    }


def main() -> None:
    """Entry point for nspec-mcp command."""
    logger.debug("MCP server starting: cwd=%s, argv=%s", Path.cwd(), sys.argv)
    transport = "sse" if "--sse" in sys.argv else "stdio"
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
