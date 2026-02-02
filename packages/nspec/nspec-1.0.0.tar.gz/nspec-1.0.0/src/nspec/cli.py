"""Command-line interface for nspec management.

This module provides the CLI entry point. Business logic is delegated to:
- validator.py: NspecValidator for validation and generation
- table_formatter.py: NspecTableFormatter for table display
- session.py: Session handoff and management
- crud.py: CRUD operations for specs

Note: Directory paths are configurable via .novabuilt.dev/nspec/config.toml.
See nspec.paths module for configuration details.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from nspec.crud import (
    add_dependency,
    check_acceptance_criteria,
    check_impl_task,
    clean_dangling_deps,
    complete_spec,
    create_adr,
    create_new_spec,
    delete_spec,
    finalize_spec,
    list_adrs,
    move_dependency,
    next_status,
    reject_spec,
    remove_dependency,
    set_loe,
    set_priority,
    set_status,
    supersede_spec,
    validate_spec_criteria,
)
from nspec.datasets import DatasetLoader
from nspec.paths import get_paths
from nspec.session import (
    append_session_log,
    generate_handoff,
    get_modified_files,
    initialize_session,
    sync_spec_state,
)
from nspec.spinner import spinner
from nspec.statuses import print_status_codes
from nspec.table_formatter import NspecTableFormatter
from nspec.validator import NspecValidator

logger = logging.getLogger("nspec")

# Exceptions expected during nspec CLI operations
_NspecCliErrors = (RuntimeError, ValueError, KeyError, TypeError, OSError, IOError)


def run_validation_check(
    docs_root: Path, operation_name: str, project_root: Path | None = None
) -> bool:
    """Run validation after a mutation operation and report results."""
    print(f"\nRunning validation after {operation_name}...")
    validator = NspecValidator(docs_root=docs_root, project_root=project_root)
    success, errors = validator.validate()

    if success:
        print("Validation passed - nspec is consistent")
        return True
    else:
        print(f"Validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        print("\nFix these errors before proceeding with other nspec operations.")
        return False


# =============================================================================
# Command Handlers
# =============================================================================


def handle_statusline(args) -> int:
    """Output compact status line for Claude Code integration.

    Format: E{epic} · S{spec} · [{completed}/{total}]

    Uses the same TaskParser as the TUI for consistent counts.
    """
    from nspec.session import StateDAO
    from nspec.tasks import TaskParser

    project_root = getattr(args, "project_root", None) or Path.cwd()

    # Read spec_id and epic from consolidated state.json
    dao = StateDAO(project_root)
    spec_id = dao.get_spec_id() or "---"
    epic_id = dao.get_active_epic() or "---"

    # Get task counts using the same parser as TUI
    completed = 0
    total = 0

    if spec_id and spec_id != "---":
        paths = get_paths(args.docs_root, project_root=getattr(args, "project_root", None))
        impl_files = list(paths.active_impls_dir.glob(f"IMPL-{spec_id}-*.md"))

        if impl_files:
            impl_path = impl_files[0]
            content = impl_path.read_text()
            parser = TaskParser()
            tasks = parser.parse(content, impl_path)

            def count_all(task_list):
                t, c = 0, 0
                for task in task_list:
                    t += 1
                    if task.completed:
                        c += 1
                    if task.children:
                        ct, cc = count_all(task.children)
                        t += ct
                        c += cc
                return t, c

            total, completed = count_all(tasks)

    import time

    # ANSI colors for terminal statusline
    cyan = "\033[36m"
    yellow = "\033[33m"
    green = "\033[32m"
    dim = "\033[2m"
    reset = "\033[0m"

    if completed == total and total > 0:
        progress_color = green
    elif completed > 0:
        progress_color = yellow
    else:
        progress_color = dim

    # Spinner: only show when there are pending tasks to work on
    spinner = ""
    if total > 0 and completed < total:
        frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        spinner = " " + frames[int(time.time() * 4) % len(frames)]

    print(
        f"{cyan}E{epic_id}{reset}"
        f" {dim}·{reset} "
        f"{yellow}S{spec_id}{reset}"
        f" {dim}·{reset} "
        f"{progress_color}[{completed}/{total}]{reset}"
        f"{spinner}",
        end="",
    )
    return 0


def handle_validate(args) -> int:
    """Run all validation layers."""
    validator = NspecValidator(
        docs_root=args.docs_root,
        strict_mode=getattr(args, "strict_epic_grouping", False),
        strict_completion_parity=not getattr(args, "no_strict_completion_parity", False),
        project_root=getattr(args, "project_root", None),
    )
    success, errors = validator.validate()

    if success:
        print("✅ Nspec validation passed - no errors found")
        return 0
    else:
        print(f"\nFound {len(errors)} errors:")
        for error in errors:
            print(error)
            print()
        return 1


def handle_generate(args) -> int:
    """Generate NSPEC.md from validated fRIMPLs."""
    # Pass 0: Auto-clean dangling dependencies
    cleaned = clean_dangling_deps(args.docs_root)
    if cleaned:
        for spec_id, path, removed in cleaned:
            print(f"Spec {spec_id}: removed dangling deps {removed}")

    # Pass 1: Validate
    validator = NspecValidator(
        docs_root=args.docs_root, project_root=getattr(args, "project_root", None)
    )
    with spinner("Loading"):
        success, errors = validator.validate()

    if not success:
        print(f"\nValidation failed with {len(errors)} errors. Cannot generate.")
        for error in errors:
            print(error)
            print()
        print("Fix errors first, then run --generate again.")
        return 1

    # Pass 2: Generate files
    validator.generate_nspec(Path("NSPEC.md"))
    validator.generate_nspec_completed(Path("NSPEC_COMPLETED.md"))
    return 0


def handle_dashboard(args) -> int:
    """Generate + stats in one call."""
    # Clean dangling deps
    cleaned = clean_dangling_deps(args.docs_root)
    if cleaned:
        for spec_id, path, removed in cleaned:
            print(f"Spec {spec_id}: removed dangling deps {removed}")

    # Auto-assign ungrouped specs to default epic (if specified)
    default_epic = getattr(args, "default_epic", None)
    if default_epic:
        from nspec.crud import auto_assign_ungrouped_to_epic

        try:
            assigned = auto_assign_ungrouped_to_epic(default_epic, args.docs_root)
            if assigned:
                for spec_id, epic_id in assigned:
                    print(f"Spec {spec_id}: auto-assigned to Epic {epic_id}")
        except (FileNotFoundError, ValueError) as e:
            print(f"Auto-assign failed: {e}")

    # Validate and generate
    validator = NspecValidator(
        docs_root=args.docs_root,
        strict_mode=getattr(args, "strict_epic_grouping", False),
        strict_completion_parity=not getattr(args, "no_strict_completion_parity", False),
        project_root=getattr(args, "project_root", None),
    )
    validator.verbose_status = getattr(args, "verbose_status", False)
    validator.epic_filter = getattr(args, "epic", None)

    with spinner("Loading"):
        success, errors = validator.validate()

    if not success:
        print(f"\nValidation failed with {len(errors)} errors.")
        for error in errors:
            print(error)
            print()
        return 1

    # Generate files
    validator.generate_nspec(Path("NSPEC.md"))
    validator.generate_nspec_completed(Path("NSPEC_COMPLETED.md"))

    # Show stats (without calendar)
    formatter = NspecTableFormatter(
        datasets=validator.datasets,
        ordered_active_specs=validator.ordered_active_specs,
        verbose_status=validator.verbose_status,
        epic_filter=validator.epic_filter,
    )
    formatter.show_stats(show_calendar=False)
    return 0


def handle_stats(args) -> int:
    """Show engineering metrics dashboard."""
    from nspec.dev_metrics import print_dev_metrics

    print_dev_metrics(Path("."))
    return 0


def handle_progress(args) -> int:
    """Show task/AC progress."""
    validator = NspecValidator(
        docs_root=args.docs_root, project_root=getattr(args, "project_root", None)
    )

    try:
        loader = DatasetLoader(
            docs_root=args.docs_root, project_root=getattr(args, "project_root", None)
        )
        validator.datasets = loader.load()
    except ValueError as e:
        print(f"Failed to load datasets: {e}")
        return 1

    if args.progress == "__summary__":
        validator.show_progress(show_all=args.all)
    else:
        validator.show_progress(spec_id=args.progress)
    return 0


def handle_deps(args) -> int:
    """List direct dependencies of a spec/epic."""
    loader = DatasetLoader(args.docs_root, project_root=getattr(args, "project_root", None))
    datasets = loader.load()

    fr = datasets.active_frs.get(args.deps)
    if not fr:
        print(f"Spec {args.deps} not found in active nspec")
        return 1

    if not fr.deps:
        print(f"Spec {args.deps} has no dependencies")
        return 0

    title = fr.path.stem.replace(f"FR-{args.deps}-", "").replace("-", " ").title()
    print(f"\nDependencies of {args.deps}: {title}")
    print(f"   Priority: {fr.priority} | Status: {fr.status}")
    print(f"   Count: {len(fr.deps)} dependencies\n")

    for dep_id in sorted(fr.deps, key=lambda x: int(x) if x.isdigit() else 0):
        dep_fr = datasets.active_frs.get(dep_id)
        if dep_fr:
            dep_title = dep_fr.path.stem.replace(f"FR-{dep_id}-", "").replace("-", " ").title()
            dep_impl = datasets.active_impls.get(dep_id)
            impl_status = dep_impl.status if dep_impl else "N/A"
            print(f"   {dep_id}: {dep_title}")
            print(f"        FR: {dep_fr.status} | IMPL: {impl_status} | Pri: {dep_fr.priority}")
        else:
            dep_fr = datasets.completed_frs.get(dep_id)
            if dep_fr:
                print(f"   {dep_id}: (completed)")
            else:
                print(f"   {dep_id}: (not found)")

    print()
    return 0


def handle_context(args) -> int:
    """Output LLM-friendly context for epic's dependencies."""
    from collections import defaultdict

    loader = DatasetLoader(args.docs_root, project_root=getattr(args, "project_root", None))
    datasets = loader.load()

    epic_fr = datasets.active_frs.get(args.context)
    if not epic_fr:
        print(f"Epic {args.context} not found in active nspec")
        return 1

    if not epic_fr.deps:
        print(f"Epic {args.context} has no dependencies")
        return 0

    epic_title = epic_fr.path.stem.replace(f"FR-{args.context}-", "").replace("-", " ").title()

    # Collect all incomplete deps
    incomplete: dict[str, dict] = {}
    completed: list[str] = []

    for dep_id in epic_fr.deps:
        dep_fr = datasets.active_frs.get(dep_id)
        if dep_fr:
            dep_impl = datasets.active_impls.get(dep_id)
            dep_title = dep_fr.path.stem.replace(f"FR-{dep_id}-", "").replace("-", " ")
            incomplete[dep_id] = {
                "title": dep_title,
                "fr_status": dep_fr.status,
                "impl_status": dep_impl.status if dep_impl else "N/A",
                "priority": dep_fr.priority,
                "upstream": list(dep_fr.deps) if dep_fr.deps else [],
            }
        else:
            if datasets.completed_frs.get(dep_id):
                completed.append(dep_id)

    # Build reverse dependency map
    downstream: dict[str, list[str]] = defaultdict(list)
    for spec_id, info in incomplete.items():
        for up_id in info["upstream"]:
            if up_id in incomplete:
                downstream[up_id].append(spec_id)

    # Categorize specs
    ready_to_start: list[tuple[str, str]] = []
    blocked_by_active: list[tuple[str, str, list[str]]] = []
    active_work: list[tuple[str, str]] = []

    for spec_id, info in incomplete.items():
        blockers = [u for u in info["upstream"] if u in incomplete]
        is_active = "Active" in info["impl_status"] or "Active" in info["fr_status"]
        is_hold = "Hold" in info["impl_status"] or "hold" in info["impl_status"].lower()

        if is_active and not is_hold:
            active_work.append((spec_id, info["title"]))
        elif not blockers:
            ready_to_start.append((spec_id, info["title"]))
        else:
            active_blockers = [
                b
                for b in blockers
                if incomplete.get(b, {}).get("impl_status", "").find("Active") >= 0
            ]
            if active_blockers:
                blocked_by_active.append((spec_id, info["title"], active_blockers))
            else:
                ready_to_start.append((spec_id, info["title"]))

    # Output YAML-like format
    print(f"""# LLM Context: Epic {args.context}
epic:
  id: {args.context}
  title: "{epic_title}"
  total_deps: {len(epic_fr.deps)}
  completed: {len(completed)}
  remaining: {len(incomplete)}

active_work:""")
    if active_work:
        for sid, title in sorted(active_work):
            print(f"  - {sid}: {title}")
    else:
        print("  []")

    print("\nready_to_start:")
    if ready_to_start:
        for sid, title in sorted(ready_to_start):
            print(f"  - {sid}: {title}")
    else:
        print("  []")

    print("\nblocked_by_active:")
    if blocked_by_active:
        for sid, title, blockers in sorted(blocked_by_active):
            print(f"  - {sid}: {title}")
            print(f"    blocked_by: [{', '.join(blockers)}]")
    else:
        print("  []")

    return 0


# =============================================================================
# Session Commands
# =============================================================================


def handle_handoff(args) -> int:
    """Generate session handoff summary."""
    if not args.id:
        print("Error: --id required for --handoff")
        return 1

    output = generate_handoff(args.id, args.docs_root)
    print(output)
    return 0


def handle_session_start(args) -> int:
    """Initialize session context."""
    if not args.id:
        print("Error: --id required for --session-start")
        return 1

    output = initialize_session(args.id, args.docs_root)
    print(output)
    return 0


def handle_session_log(args) -> int:
    """Append note to execution notes."""
    if not args.id or not args.note:
        print("Error: --id and --note required for --session-log")
        return 1

    output = append_session_log(args.id, args.note, args.docs_root)
    print(output)
    return 0


def handle_modified_files(args) -> int:
    """List modified files."""
    files = get_modified_files(Path.cwd(), args.since_commit)
    for f in files:
        print(f)
    return 0


def handle_sync(args) -> int:
    """Sync spec state."""
    if not args.id:
        print("Error: --id required for --sync")
        return 1

    output = sync_spec_state(args.id, args.docs_root, force=args.force)
    print(output)
    return 0


# =============================================================================
# CRUD Commands
# =============================================================================


def resolve_epic(explicit_epic: str | None, docs_root: Path) -> str | None:
    """Resolve epic ID: explicit flag > config default > None.

    Args:
        explicit_epic: Explicitly provided epic ID (--epic flag)
        docs_root: Path to docs/ directory

    Returns:
        Resolved epic ID, or None if no epic specified or configured
    """
    if explicit_epic:
        return explicit_epic

    # Check config for defaults.epic
    from nspec.config import NspecConfig

    config = NspecConfig.load(docs_root.parent)
    if config.defaults.epic:
        return config.defaults.epic

    return None


def validate_epic_exists(epic_id: str, docs_root: Path, project_root: Path | None = None) -> bool:
    """Validate that epic ID exists in active nspec.

    Args:
        epic_id: Epic ID to validate
        docs_root: Path to docs/ directory

    Returns:
        True if epic exists

    Raises:
        ValueError: If epic doesn't exist
    """
    paths = get_paths(docs_root, project_root=project_root)
    pattern = f"FR-{epic_id.zfill(3)}-*.md"
    matches = list(paths.active_frs_dir.glob(pattern))

    if not matches:
        raise ValueError(f"Epic {epic_id} not found in {paths.active_frs_dir}")

    return True


def handle_create_new(args) -> int:
    """Create new FR+IMPL from templates."""
    if not args.title:
        print("Error: --title required for --create-new")
        return 1

    try:
        # Resolve epic FIRST (before creating anything)
        epic_id = resolve_epic(getattr(args, "epic", None), args.docs_root)

        # Validate epic exists BEFORE creating files (only if epic specified)
        if epic_id:
            validate_epic_exists(
                epic_id, args.docs_root, project_root=getattr(args, "project_root", None)
            )

        # Create spec files
        fr_path, impl_path, spec_id = create_new_spec(
            title=args.title,
            priority=args.priority,
            docs_root=args.docs_root,
            fr_template=getattr(args, "fr_template", None),
            impl_template=getattr(args, "impl_template", None),
        )

        # Add spec to epic (only if epic specified)
        if epic_id:
            move_dependency(
                spec_id=spec_id,
                target_epic_id=epic_id,
                docs_root=args.docs_root,
            )

        # Git add if requested
        if args.git_add:
            import subprocess

            subprocess.run(["git", "add", str(fr_path), str(impl_path)], check=True)

        if epic_id:
            print(f"Created Spec {spec_id} in Epic {epic_id}")
        else:
            print(f"Created Spec {spec_id}")
        print(str(fr_path))
        print(str(impl_path))
        return 0
    except (ValueError, FileNotFoundError) as e:
        print(f"Failed to create spec: {e}")
        return 1


def handle_delete(args) -> int:
    """Delete FR+IMPL for a spec."""
    if not args.id:
        print("Error: --id required for --delete")
        return 1

    try:
        fr_path, impl_path = delete_spec(
            spec_id=args.id,
            docs_root=args.docs_root,
            force=args.force,
        )
        print(f"Deleted Spec {args.id}")
        print(f"   Removed: {fr_path.name}")
        print(f"   Removed: {impl_path.name}")
        return 0
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Failed to delete spec: {e}")
        return 1


def handle_complete(args) -> int:
    """Move FR+IMPL to completed directory."""
    if not args.id:
        print("Error: --id required for --complete")
        return 1

    try:
        fr_old, fr_new, impl_old, impl_new = complete_spec(
            spec_id=args.id,
            docs_root=args.docs_root,
        )
        print(str(fr_old))
        print(str(fr_new))
        print(str(impl_old))
        print(str(impl_new))
        return 0
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Failed to complete spec: {e}")
        return 1


def handle_supersede(args) -> int:
    """Move FR+IMPL to superseded directory."""
    if not args.id:
        print("Error: --id required for --supersede")
        return 1

    try:
        fr_old, fr_new, impl_old, impl_new = supersede_spec(
            spec_id=args.id,
            docs_root=args.docs_root,
            force=args.force,
        )
        print(str(fr_old))
        print(str(fr_new))
        print(str(impl_old))
        print(str(impl_new))
        return 0
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Failed to supersede spec: {e}")
        return 1


def handle_reject(args) -> int:
    """Archive spec as rejected."""
    if not args.id:
        print("Error: --id required for --reject")
        return 1

    try:
        fr_old, fr_new, impl_old, impl_new = reject_spec(
            spec_id=args.id,
            docs_root=args.docs_root,
            force=args.force,
        )
        print(str(fr_old))
        print(str(fr_new))
        print(str(impl_old))
        print(str(impl_new))
        return 0
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Failed to reject spec: {e}")
        return 1


def handle_finalize(args) -> int:
    """Show completion status."""
    if not args.id:
        print("Error: --id required for --finalize")
        return 1

    try:
        finalize_spec(
            spec_id=args.id,
            docs_root=args.docs_root,
            execute=args.execute,
        )
        return 0
    except FileNotFoundError as e:
        print(f"Failed to finalize spec: {e}")
        return 1


def handle_add_dep(args) -> int:
    """Add dependency to a spec."""
    if not args.to or not args.dep:
        print("Error: --to and --dep required for --add-dep")
        return 1

    try:
        result = add_dependency(
            spec_id=args.to,
            dependency_id=args.dep,
            docs_root=args.docs_root,
        )
        print(f"Added dependency {args.dep} to Spec {args.to}")
        print(f"   Updated: {result['path']}")
        if result.get("moved_from"):
            print(f"   Moved from Epic {result['moved_from']}")

        run_validation_check(args.docs_root, "dependency addition")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to add dependency: {e}")
        return 1


def handle_remove_dep(args) -> int:
    """Remove dependency from a spec."""
    if not args.to or not args.dep:
        print("Error: --to and --dep required for --remove-dep")
        return 1

    try:
        fr_path = remove_dependency(
            spec_id=args.to,
            dependency_id=args.dep,
            docs_root=args.docs_root,
        )
        print(f"Removed dependency {args.dep} from Spec {args.to}")
        print(f"   Updated: {fr_path}")

        run_validation_check(args.docs_root, "dependency removal")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to remove dependency: {e}")
        return 1


def handle_move_dep(args) -> int:
    """Move spec to target epic."""
    if not args.to or not args.dep:
        print("Error: --to and --dep required for --move-dep")
        return 1

    try:
        result = move_dependency(
            spec_id=args.dep,
            target_epic_id=args.to,
            docs_root=args.docs_root,
        )

        print(f"Moved Spec {args.dep} to Epic {args.to}")
        if result["removed_from"]:
            for epic_id in result["removed_from"]:
                print(f"   Removed from Epic {epic_id}")
        if result["added_to"]:
            print(f"   Added to Epic {result['added_to']}")
        if result["priority_bumped"]:
            print(f"   Priority bumped to {result['priority_bumped']}")

        run_validation_check(args.docs_root, "dependency move")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to move dependency: {e}")
        return 1


def handle_dep_clean(args) -> int:
    """Remove dependencies pointing to non-existent specs."""
    cleaned = clean_dangling_deps(
        args.docs_root,
        project_root=getattr(args, "project_root", None),
        dry_run=getattr(args, "dry_run", False),
    )
    if not cleaned:
        print("No dangling deps found")
        return 0

    for spec_id, path, removed in cleaned:
        prefix = "[dry-run] " if getattr(args, "dry_run", False) else ""
        print(f"{prefix}Spec {spec_id}: removed dangling deps {removed}")
        print(f"   Updated: {path}")

    if not getattr(args, "dry_run", False):
        run_validation_check(args.docs_root, "dangling dependency cleanup")
    return 0


def handle_set_priority(args) -> int:
    """Change priority for a spec."""
    if not args.id or not args.priority:
        print("Error: --id and --priority required for --set-priority")
        return 1

    try:
        fr_path = set_priority(
            spec_id=args.id,
            priority=args.priority,
            docs_root=args.docs_root,
        )
        print(f"Updated Spec {args.id} to {args.priority}")
        print(f"   Updated: {fr_path}")

        run_validation_check(args.docs_root, "priority change")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to set priority: {e}")
        return 1


def handle_set_loe(args) -> int:
    """Set LOE for a spec."""
    if not args.id or not args.loe:
        print("Error: --id and --loe required for --set-loe")
        return 1

    try:
        impl_path = set_loe(
            spec_id=args.id,
            loe=args.loe,
            docs_root=args.docs_root,
        )
        print(f"Updated Spec {args.id} LOE to {args.loe}")
        print(f"   Updated: {impl_path}")

        run_validation_check(args.docs_root, "LOE change")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to set LOE: {e}")
        return 1


def handle_set_status(args) -> int:
    """Set status for FR and IMPL files atomically."""
    if not args.id or args.fr_status is None or args.impl_status is None:
        print("Error: --id, --fr-status, and --impl-status required")
        return 1

    try:
        set_status(
            spec_id=args.id,
            fr_status=args.fr_status,
            impl_status=args.impl_status,
            docs_root=args.docs_root,
            force=args.force,
        )
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to set status: {e}")
        return 1


def handle_next_status(args) -> int:
    """Auto-advance IMPL to next logical state."""
    if not args.id:
        print("Error: --id required for --next-status")
        return 1

    try:
        next_status(
            spec_id=args.id,
            docs_root=args.docs_root,
        )
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to advance status: {e}")
        return 1


def handle_check_criteria(args) -> int:
    """Mark acceptance criterion as complete or obsolete."""
    if not args.id or not args.criteria_id:
        print("Error: --id and --criteria-id required for --check-criteria")
        return 1

    marker = getattr(args, "marker", "x")
    marker_desc = "complete" if marker == "x" else "obsolete"

    try:
        fr_path = check_acceptance_criteria(
            spec_id=args.id,
            criteria_id=args.criteria_id,
            docs_root=args.docs_root,
            marker=marker,
        )
        print(f"Marked {args.criteria_id} as {marker_desc} for Spec {args.id}")
        print(f"   Updated: {fr_path}")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to check criteria: {e}")
        return 1


def handle_check_task(args) -> int:
    """Mark IMPL task as complete or obsolete."""
    if not args.id or not args.task_id:
        print("Error: --id and --task-id required for --check-task")
        return 1

    marker = getattr(args, "marker", "x")
    marker_desc = "complete" if marker == "x" else "obsolete"

    try:
        impl_path = check_impl_task(
            spec_id=args.id,
            task_id=args.task_id,
            docs_root=args.docs_root,
            marker=marker,
        )
        print(f"Marked task '{args.task_id}' as {marker_desc} for Spec {args.id}")
        print(f"   Updated: {impl_path}")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to check task: {e}")
        return 1


def handle_validate_criteria(args) -> int:
    """Validate acceptance criteria for a spec."""
    if not args.id:
        print("Error: --id required for --validate-criteria")
        return 1

    try:
        is_valid, violations = validate_spec_criteria(
            spec_id=args.id,
            docs_root=args.docs_root,
            strict=args.strict,
        )

        if is_valid:
            print(f"Spec {args.id} acceptance criteria validation passed")
            return 0
        else:
            print(f"Spec {args.id} acceptance criteria validation failed:\n")
            for violation in violations:
                print(f"   {violation}")
            return 1
    except _NspecCliErrors as e:
        print(f"Validation error: {e}")
        return 1


def handle_create_adr(args) -> int:
    """Create a new ADR."""
    if not args.title:
        print("Error: --title required for --create-adr")
        return 1

    try:
        adr_id, fr_path = create_adr(args.title, args.docs_root)
        print(f"Created ADR-{adr_id}: {args.title}")
        print(f"   {fr_path}")
        return 0
    except _NspecCliErrors as e:
        print(f"Error creating ADR: {e}")
        return 1


def handle_list_adrs(args) -> int:
    """List all ADRs."""
    try:
        adrs = list_adrs(args.docs_root)
        if not adrs:
            print("No ADRs found (FR-900-999 range)")
            return 0

        print(f"\nArchitecture Decision Records ({len(adrs)} total)")
        print("=" * 60)
        for adr_id, status, title, path in adrs:
            status_emoji = {
                "DRAFT": "D",
                "PROPOSED": "P",
                "ACCEPTED": "A",
                "DEPRECATED": "!",
                "SUPERSEDED": ">",
            }.get(status.upper(), "?")
            print(f"  ADR-{adr_id}: [{status_emoji}] {status}")
            print(f"           {title}")
            print()
        return 0
    except _NspecCliErrors as e:
        print(f"Error listing ADRs: {e}")
        return 1


# =============================================================================
# Main Entry Point
# =============================================================================


def handle_init(args: argparse.Namespace) -> int:
    """Initialize a new nspec project."""
    from nspec.init import detect_stack, interactive_init, scaffold_project

    project_root = Path.cwd()
    docs_root = getattr(args, "docs_root", None) or project_root / "docs"

    stack = detect_stack(project_root)
    ci_override = getattr(args, "ci", None)
    force = getattr(args, "force", False)

    print(f"Detected stack: {stack.language}/{stack.package_manager}")
    if stack.ci_platform != "none":
        print(f"Detected CI: {stack.ci_platform}")

    # Interactive path selection
    config = interactive_init(project_root, interactive=True)

    try:
        created = scaffold_project(
            project_root=project_root,
            docs_root=docs_root,
            stack=stack,
            ci_platform_override=ci_override,
            force=force,
            config=config,
        )
    except FileExistsError as e:
        print(f"Error: {e}")
        return 1

    print(f"\nCreated {len(created)} files/directories:")
    for p in created:
        if p.is_file():
            try:
                rel = p.relative_to(project_root)
            except ValueError:
                rel = p
            print(f"  {rel}")

    print("\nNext steps:")
    print("  1. Review .novabuilt.dev/nspec/config.toml and adjust paths if needed")
    print("  2. Add 'include nspec.mk' to your Makefile")
    print("  3. Create your first spec: nspec --create-new --title 'My Feature'")
    return 0


def _add_common_args(sub: argparse.ArgumentParser) -> None:
    """Add common arguments shared across subcommand parsers."""
    sub.add_argument("--docs-root", type=Path, default=Path("docs"), help="Docs root")
    sub.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root for config (default: parent of --docs-root)",
    )


def _add_id_arg(sub: argparse.ArgumentParser) -> None:
    """Add --id argument to a subparser."""
    sub.add_argument("--id", type=str, required=True, help="Spec ID")


def _add_force_arg(sub: argparse.ArgumentParser) -> None:
    """Add --force argument to a subparser."""
    sub.add_argument("--force", action="store_true", help="Skip safety checks")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Nspec management - validation, generation, and CRUD operations"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command")
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new nspec project",
        description="Scaffold a new nspec project with docs structure, config, and optional CI.",
        epilog="Examples:\n  nspec init\n  nspec init --ci github\n  nspec init --force --docs-root my-docs/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    init_parser.add_argument(
        "--ci",
        type=str,
        choices=["github", "cloudbuild", "gitlab", "none"],
        default=None,
        help="CI platform (auto-detected if not specified)",
    )
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    init_parser.add_argument(
        "--docs-root", type=Path, default=None, help="Docs root directory (default: docs/)"
    )

    # -------------------------------------------------------------------------
    # Top-level subcommands
    # -------------------------------------------------------------------------

    # nspec tui
    tui_sub = subparsers.add_parser(
        "tui",
        help="Launch interactive TUI",
        description="Launch the interactive terminal UI for browsing and managing specs.",
        epilog="Examples:\n  nspec tui\n  nspec tui --docs-root my-docs/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_common_args(tui_sub)
    tui_sub.set_defaults(handler=lambda args: _handle_tui_subcommand(args))

    # nspec statusline
    statusline_sub = subparsers.add_parser(
        "statusline",
        help="Output compact status line for Claude Code",
        description="Output a compact one-line status summary for Claude Code integration.",
        epilog="Examples:\n  nspec statusline\n  nspec statusline --docs-root my-docs/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_common_args(statusline_sub)
    statusline_sub.set_defaults(handler=handle_statusline)

    # nspec generate
    generate_sub = subparsers.add_parser(
        "generate",
        help="Generate NSPEC.md",
        description="Generate NSPEC.md from validated FR and IMPL documents.",
        epilog="Examples:\n  nspec generate\n  nspec generate --docs-root my-docs/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_common_args(generate_sub)
    generate_sub.set_defaults(handler=handle_generate)

    # nspec dashboard
    dashboard_sub = subparsers.add_parser(
        "dashboard",
        help="Generate + stats combined",
        description="Generate NSPEC.md and display engineering metrics in one command.",
        epilog="Examples:\n  nspec dashboard\n  nspec dashboard --epic 100\n  nspec dashboard --verbose-status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_common_args(dashboard_sub)
    dashboard_sub.add_argument("--verbose-status", action="store_true", help="Full status text")
    dashboard_sub.add_argument("--epic", type=str, help="Filter by epic ID")
    dashboard_sub.add_argument(
        "--strict-epic-grouping", action="store_true", help="Require epic grouping"
    )
    dashboard_sub.add_argument("--no-strict-completion-parity", action="store_true")
    dashboard_sub.add_argument("--default-epic", type=str, help="Default epic for ungrouped specs")
    dashboard_sub.set_defaults(handler=handle_dashboard)

    # nspec stats
    stats_sub = subparsers.add_parser(
        "stats",
        help="Show engineering metrics",
        description="Display engineering metrics: completion rates, velocity, and burndown.",
        epilog="Examples:\n  nspec stats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_common_args(stats_sub)
    stats_sub.set_defaults(handler=handle_stats)

    # -------------------------------------------------------------------------
    # nspec validate [criteria]
    # -------------------------------------------------------------------------
    validate_sub = subparsers.add_parser(
        "validate",
        help="Run validation",
        description="Run the 6-layer validation engine on all FR and IMPL documents.",
        epilog="Examples:\n  nspec validate\n  nspec validate --strict-epic-grouping\n  nspec validate criteria --id 002 --strict",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_common_args(validate_sub)
    validate_sub.add_argument(
        "--strict-epic-grouping", action="store_true", help="Require epic grouping"
    )
    validate_sub.add_argument("--no-strict-completion-parity", action="store_true")
    validate_sub.set_defaults(handler=handle_validate)

    validate_subs = validate_sub.add_subparsers(dest="validate_command")
    validate_criteria_sub = validate_subs.add_parser(
        "criteria", help="Validate acceptance criteria"
    )
    _add_common_args(validate_criteria_sub)
    _add_id_arg(validate_criteria_sub)
    validate_criteria_sub.add_argument("--strict", action="store_true", help="Strict validation")
    validate_criteria_sub.set_defaults(handler=handle_validate_criteria)

    # -------------------------------------------------------------------------
    # nspec spec <cmd>
    # -------------------------------------------------------------------------
    spec_sub = subparsers.add_parser(
        "spec",
        help="Spec CRUD operations",
        description="Create, delete, complete, and manage spec lifecycle.",
        epilog="Examples:\n  nspec spec create --title 'Add search' --priority P1\n  nspec spec complete --id 003\n  nspec spec progress --id 002",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    spec_subs = spec_sub.add_subparsers(dest="spec_command")

    # nspec spec create
    spec_create = spec_subs.add_parser("create", help="Create new FR+IMPL spec")
    _add_common_args(spec_create)
    spec_create.add_argument("--title", type=str, required=True, help="Spec title")
    spec_create.add_argument("--priority", type=str, default="P2", help="Priority (P0-P3)")
    spec_create.add_argument("--epic", type=str, help="Target epic ID")
    spec_create.add_argument("--git-add", action="store_true", help="Git add created files")
    spec_create.add_argument("--fr-template", type=str, help="Path to FR template")
    spec_create.add_argument("--impl-template", type=str, help="Path to IMPL template")
    spec_create.set_defaults(handler=handle_create_new)

    # nspec spec delete
    spec_delete = spec_subs.add_parser("delete", help="Delete FR+IMPL spec")
    _add_common_args(spec_delete)
    _add_id_arg(spec_delete)
    _add_force_arg(spec_delete)
    spec_delete.set_defaults(handler=handle_delete)

    # nspec spec complete
    spec_complete = spec_subs.add_parser("complete", help="Archive spec as completed")
    _add_common_args(spec_complete)
    _add_id_arg(spec_complete)
    spec_complete.set_defaults(handler=handle_complete)

    # nspec spec supersede
    spec_supersede = spec_subs.add_parser("supersede", help="Archive spec as superseded")
    _add_common_args(spec_supersede)
    _add_id_arg(spec_supersede)
    _add_force_arg(spec_supersede)
    spec_supersede.set_defaults(handler=handle_supersede)

    # nspec spec reject
    spec_reject = spec_subs.add_parser("reject", help="Archive spec as rejected")
    _add_common_args(spec_reject)
    _add_id_arg(spec_reject)
    _add_force_arg(spec_reject)
    spec_reject.set_defaults(handler=handle_reject)

    # nspec spec finalize
    spec_finalize = spec_subs.add_parser("finalize", help="Show spec completion status")
    _add_common_args(spec_finalize)
    _add_id_arg(spec_finalize)
    spec_finalize.add_argument("--execute", action="store_true", help="Execute finalization")
    spec_finalize.set_defaults(handler=handle_finalize)

    # nspec spec progress
    spec_progress = spec_subs.add_parser("progress", help="Show task/AC progress")
    _add_common_args(spec_progress)
    spec_progress.add_argument("--id", type=str, help="Spec ID (omit for summary)")
    spec_progress.add_argument("--all", action="store_true", help="Show all specs")
    spec_progress.set_defaults(handler=_handle_spec_progress)

    # nspec spec deps
    spec_deps = spec_subs.add_parser("deps", help="List dependencies")
    _add_common_args(spec_deps)
    _add_id_arg(spec_deps)
    spec_deps.set_defaults(handler=_handle_spec_deps)

    # nspec spec context
    spec_context = spec_subs.add_parser("context", help="LLM context for epic")
    _add_common_args(spec_context)
    _add_id_arg(spec_context)
    spec_context.set_defaults(handler=_handle_spec_context)

    # -------------------------------------------------------------------------
    # nspec dep <cmd>
    # -------------------------------------------------------------------------
    dep_sub = subparsers.add_parser(
        "dep",
        help="Dependency operations",
        description="Add, remove, and move dependencies between specs and epics.",
        epilog=(
            "Examples:\n"
            "  nspec dep add --to 003 --dep 001\n"
            "  nspec dep remove --to 003 --dep 001\n"
            "  nspec dep move --to 100 --dep 005\n"
            "  nspec dep clean\n"
            "  nspec dep clean --dry-run"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    dep_subs = dep_sub.add_subparsers(dest="dep_command")

    # nspec dep add
    dep_add = dep_subs.add_parser("add", help="Add dependency")
    _add_common_args(dep_add)
    dep_add.add_argument("--to", type=str, required=True, help="Target spec/epic ID")
    dep_add.add_argument("--dep", type=str, required=True, help="Dependency ID")
    dep_add.set_defaults(handler=handle_add_dep)

    # nspec dep remove
    dep_remove = dep_subs.add_parser("remove", help="Remove dependency")
    _add_common_args(dep_remove)
    dep_remove.add_argument("--to", type=str, required=True, help="Target spec/epic ID")
    dep_remove.add_argument("--dep", type=str, required=True, help="Dependency ID")
    dep_remove.set_defaults(handler=handle_remove_dep)

    # nspec dep move
    dep_move = dep_subs.add_parser("move", help="Move spec to epic")
    _add_common_args(dep_move)
    dep_move.add_argument("--to", type=str, required=True, help="Target epic ID")
    dep_move.add_argument("--dep", type=str, required=True, help="Spec ID to move")
    dep_move.set_defaults(handler=handle_move_dep)

    # nspec dep clean
    dep_clean = dep_subs.add_parser("clean", help="Remove dangling dependency references")
    _add_common_args(dep_clean)
    dep_clean.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    dep_clean.set_defaults(handler=handle_dep_clean)

    # -------------------------------------------------------------------------
    # nspec task <cmd>
    # -------------------------------------------------------------------------
    task_sub = subparsers.add_parser(
        "task",
        help="Task and property operations",
        description="Check off tasks/criteria, set priority, LOE, and advance status.",
        epilog="Examples:\n  nspec task check --id 002 --task-id 1.1\n  nspec task criteria --id 002 --criteria-id AC-F1\n  nspec task set-priority --id 002 --priority P0\n  nspec task next-status --id 002",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    task_subs = task_sub.add_subparsers(dest="task_command")

    # nspec task check
    task_check = task_subs.add_parser("check", help="Mark task complete/obsolete")
    _add_common_args(task_check)
    _add_id_arg(task_check)
    task_check.add_argument("--task-id", type=str, required=True, help="Task ID (e.g., 1.1)")
    task_check.add_argument(
        "--marker", type=str, default="x", choices=["x", "~"],
        help="Marker: x=complete, ~=obsolete",
    )
    task_check.set_defaults(handler=handle_check_task)

    # nspec task criteria
    task_criteria = task_subs.add_parser("criteria", help="Mark criterion complete/obsolete")
    _add_common_args(task_criteria)
    _add_id_arg(task_criteria)
    task_criteria.add_argument(
        "--criteria-id", type=str, required=True, help="Criteria ID (e.g., AC-F1)"
    )
    task_criteria.add_argument(
        "--marker", type=str, default="x", choices=["x", "~"],
        help="Marker: x=complete, ~=obsolete",
    )
    task_criteria.set_defaults(handler=handle_check_criteria)

    # nspec task set-priority
    task_priority = task_subs.add_parser("set-priority", help="Change priority")
    _add_common_args(task_priority)
    _add_id_arg(task_priority)
    task_priority.add_argument("--priority", type=str, required=True, help="Priority (P0-P3)")
    task_priority.set_defaults(handler=handle_set_priority)

    # nspec task set-loe
    task_loe = task_subs.add_parser("set-loe", help="Set LOE estimate")
    _add_common_args(task_loe)
    _add_id_arg(task_loe)
    task_loe.add_argument("--loe", type=str, required=True, help="LOE value (5d, 3w, etc)")
    task_loe.set_defaults(handler=handle_set_loe)

    # nspec task next-status
    task_next = task_subs.add_parser("next-status", help="Advance to next status")
    _add_common_args(task_next)
    _add_id_arg(task_next)
    task_next.set_defaults(handler=handle_next_status)

    # nspec task set-status
    task_status = task_subs.add_parser("set-status", help="Set FR and IMPL status")
    _add_common_args(task_status)
    _add_id_arg(task_status)
    task_status.add_argument("--fr-status", type=int, required=True, help="FR status code")
    task_status.add_argument("--impl-status", type=int, required=True, help="IMPL status code")
    _add_force_arg(task_status)
    task_status.set_defaults(handler=handle_set_status)

    # -------------------------------------------------------------------------
    # nspec session <cmd>
    # -------------------------------------------------------------------------
    session_sub = subparsers.add_parser(
        "session",
        help="Session management",
        description="Manage work sessions: start, log notes, handoff, and sync state.",
        epilog="Examples:\n  nspec session start --id 002\n  nspec session log --id 002 --note 'Fixed parsing bug'\n  nspec session handoff --id 002\n  nspec session files --since-commit HEAD~3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    session_subs = session_sub.add_subparsers(dest="session_command")

    # nspec session start
    session_start = session_subs.add_parser("start", help="Initialize session context")
    _add_common_args(session_start)
    _add_id_arg(session_start)
    session_start.set_defaults(handler=handle_session_start)

    # nspec session log
    session_log = session_subs.add_parser("log", help="Append session note")
    _add_common_args(session_log)
    _add_id_arg(session_log)
    session_log.add_argument("--note", type=str, required=True, help="Note text")
    session_log.set_defaults(handler=handle_session_log)

    # nspec session handoff
    session_handoff = session_subs.add_parser("handoff", help="Generate session handoff")
    _add_common_args(session_handoff)
    _add_id_arg(session_handoff)
    session_handoff.set_defaults(handler=handle_handoff)

    # nspec session sync
    session_sync = session_subs.add_parser("sync", help="Sync spec state")
    _add_common_args(session_sync)
    _add_id_arg(session_sync)
    _add_force_arg(session_sync)
    session_sync.set_defaults(handler=handle_sync)

    # nspec session files
    session_files = session_subs.add_parser("files", help="List modified files")
    _add_common_args(session_files)
    session_files.add_argument("--since-commit", type=str, help="Git ref for comparison")
    session_files.set_defaults(handler=handle_modified_files)

    # -------------------------------------------------------------------------
    # nspec adr <cmd>
    # -------------------------------------------------------------------------
    adr_sub = subparsers.add_parser(
        "adr",
        help="Architecture Decision Records",
        description="Create and list Architecture Decision Records (ADRs).",
        epilog="Examples:\n  nspec adr create --title 'Use argparse over click'\n  nspec adr list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    adr_subs = adr_sub.add_subparsers(dest="adr_command")

    # nspec adr create
    adr_create = adr_subs.add_parser("create", help="Create new ADR")
    _add_common_args(adr_create)
    adr_create.add_argument("--title", type=str, required=True, help="ADR title")
    adr_create.set_defaults(handler=handle_create_adr)

    # nspec adr list
    adr_list = adr_subs.add_parser("list", help="List all ADRs")
    _add_common_args(adr_list)
    adr_list.set_defaults(handler=handle_list_adrs)

    # TUI mode
    parser.add_argument("--tui", action="store_true", help="Launch interactive TUI")
    parser.add_argument(
        "--statusline", action="store_true", help="Output compact status line for Claude Code"
    )

    # Core commands
    parser.add_argument("--validate", action="store_true", help="Run all validation layers")
    parser.add_argument("--generate", action="store_true", help="Generate NSPEC.md")
    parser.add_argument("--dashboard", action="store_true", help="Generate + stats combined")
    parser.add_argument("--stats", action="store_true", help="Show engineering metrics")
    parser.add_argument("--progress", nargs="?", const="__summary__", help="Show progress")
    parser.add_argument("--all", action="store_true", help="Show all specs (with --progress)")
    parser.add_argument("--deps", type=str, metavar="SPEC_ID", help="List dependencies")
    parser.add_argument("--context", type=str, metavar="EPIC_ID", help="LLM context for epic")
    parser.add_argument("--status-codes", action="store_true", help="Print status codes")

    # Session commands
    parser.add_argument("--handoff", action="store_true", help="Generate session handoff")
    parser.add_argument("--session-start", action="store_true", help="Initialize session")
    parser.add_argument("--session-log", action="store_true", help="Append session note")
    parser.add_argument("--note", type=str, help="Note text (for --session-log)")
    parser.add_argument("--modified-files", action="store_true", help="List modified files")
    parser.add_argument("--since-commit", type=str, help="Git ref for --modified-files")
    parser.add_argument("--sync", action="store_true", help="Sync spec state")

    # CRUD commands
    parser.add_argument("--create-new", action="store_true", help="Create new FR+IMPL spec")
    parser.add_argument("--delete", action="store_true", help="Delete FR+IMPL spec")
    parser.add_argument("--complete", action="store_true", help="Archive spec as completed")
    parser.add_argument("--supersede", action="store_true", help="Archive spec as superseded")
    parser.add_argument("--reject", action="store_true", help="Archive spec as rejected")
    parser.add_argument("--finalize", action="store_true", help="Show spec completion status")
    parser.add_argument("--execute", action="store_true", help="Execute finalization")

    # Dependency commands
    parser.add_argument("--add-dep", action="store_true", help="Add dependency")
    parser.add_argument("--remove-dep", action="store_true", help="Remove dependency")
    parser.add_argument("--move-dep", action="store_true", help="Move spec to epic")
    parser.add_argument("--to", type=str, help="Target spec/epic ID")
    parser.add_argument("--dep", type=str, help="Dependency ID")

    # Property commands
    parser.add_argument("--set-priority", action="store_true", help="Change priority")
    parser.add_argument("--set-loe", action="store_true", help="Set LOE estimate")
    parser.add_argument("--loe", type=str, help="LOE value (5d, 3w, etc)")
    parser.add_argument("--_set_frimpl_status", action="store_true", help="[Internal] Set status")
    parser.add_argument("--next-status", action="store_true", help="Advance to next status")
    parser.add_argument("--fr-status", type=int, help="FR status code")
    parser.add_argument("--impl-status", type=int, help="IMPL status code")

    # Task/criteria commands
    parser.add_argument(
        "--check-criteria", action="store_true", help="Mark criterion complete/obsolete"
    )
    parser.add_argument("--check-task", action="store_true", help="Mark task complete/obsolete")
    parser.add_argument("--validate-criteria", action="store_true", help="Validate criteria")
    parser.add_argument("--criteria-id", type=str, help="Criteria ID (e.g., AC-F1)")
    parser.add_argument("--task-id", type=str, help="Task ID to mark (e.g., 1.1)")
    parser.add_argument(
        "--marker",
        type=str,
        default="x",
        choices=["x", "~"],
        help="Marker: x=complete, ~=obsolete (default: x)",
    )
    parser.add_argument("--strict", action="store_true", help="Strict validation")

    # ADR commands
    parser.add_argument("--create-adr", action="store_true", help="Create new ADR")
    parser.add_argument("--list-adrs", action="store_true", help="List all ADRs")

    # Common options
    parser.add_argument("--id", type=str, help="Spec ID")
    parser.add_argument("--title", type=str, help="Spec/ADR title")
    parser.add_argument("--priority", type=str, default="P2", help="Priority (P0-P3)")
    parser.add_argument("--force", action="store_true", help="Skip safety checks")
    parser.add_argument("--git-add", action="store_true", help="Git add created files")
    parser.add_argument("--docs-root", type=Path, default=Path("docs"), help="Docs root")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root for .novabuilt.dev/nspec/config.toml (default: parent of --docs-root)",
    )
    parser.add_argument("--verbose-status", action="store_true", help="Full status text")
    parser.add_argument(
        "--epic",
        type=str,
        help="Epic ID (for --create-new: target epic; for views: filter by epic)",
    )
    parser.add_argument(
        "--fr-template", type=str, help="Path to FR template (relative to docs root or absolute)"
    )
    parser.add_argument(
        "--impl-template",
        type=str,
        help="Path to IMPL template (relative to docs root or absolute)",
    )
    parser.add_argument("--strict-epic-grouping", action="store_true", help="Require epic grouping")
    parser.add_argument("--no-strict-completion-parity", action="store_true")
    parser.add_argument("--default-epic", type=str, help="Default epic for ungrouped specs")

    return parser


def _handle_tui_subcommand(args) -> int:
    """Adapter for 'nspec tui' subcommand."""
    from nspec.tui import main as tui_main

    tui_main(docs_root=args.docs_root, project_root=args.project_root)
    return 0


def _handle_spec_progress(args) -> int:
    """Adapter for 'nspec spec progress' — maps --id to args.progress."""
    args.progress = args.id if args.id else "__summary__"
    return handle_progress(args)


def _handle_spec_deps(args) -> int:
    """Adapter for 'nspec spec deps' — maps --id to args.deps."""
    args.deps = args.id
    return handle_deps(args)


def _handle_spec_context(args) -> int:
    """Adapter for 'nspec spec context' — maps --id to args.context."""
    args.context = args.id
    return handle_context(args)


def main() -> int:
    """Main CLI entry point."""
    # Configure logging
    log_level = logging.DEBUG if os.environ.get("NSPEC_DEBUG") == "Y" else logging.WARNING
    logging.basicConfig(level=log_level, format="%(message)s", stream=sys.stdout)

    parser = build_parser()

    # Enable tab completion if argcomplete is installed
    try:
        import argcomplete

        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    args = parser.parse_args()

    # Subcommand dispatch (before flag-based dispatch)
    if args.command == "init":
        return handle_init(args)

    # Handler-based dispatch for new subcommands
    if hasattr(args, "handler"):
        if getattr(args, "project_root", None) is None:
            args.project_root = args.docs_root.parent
        return args.handler(args)

    if getattr(args, "project_root", None) is None:
        args.project_root = args.docs_root.parent

    # Warn if no config found (but don't block)
    from nspec.init import needs_init

    if needs_init(args.project_root):
        print("No nspec configuration found. Run 'nspec init' to set up your project.")

    # TUI mode - launch interactive interface
    if args.tui:
        from nspec.tui import main as tui_main

        tui_main(docs_root=args.docs_root, project_root=args.project_root)
        return 0

    # Status line for Claude Code integration
    if args.statusline:
        return handle_statusline(args)

    # Dispatch to handlers
    if args.status_codes:
        print_status_codes()
        return 0

    if args.validate:
        return handle_validate(args)
    if args.generate:
        return handle_generate(args)
    if args.dashboard:
        return handle_dashboard(args)
    if args.stats:
        return handle_stats(args)
    if args.progress:
        return handle_progress(args)
    if args.deps:
        return handle_deps(args)
    if args.context:
        return handle_context(args)

    # Session commands
    if args.handoff:
        return handle_handoff(args)
    if args.session_start:
        return handle_session_start(args)
    if args.session_log:
        return handle_session_log(args)
    if args.modified_files:
        return handle_modified_files(args)
    if args.sync:
        return handle_sync(args)

    # CRUD commands
    if args.create_new:
        return handle_create_new(args)
    if args.delete:
        return handle_delete(args)
    if args.complete:
        return handle_complete(args)
    if args.supersede:
        return handle_supersede(args)
    if args.reject:
        return handle_reject(args)
    if args.finalize:
        return handle_finalize(args)

    # Dependency commands
    if args.add_dep:
        return handle_add_dep(args)
    if args.remove_dep:
        return handle_remove_dep(args)
    if args.move_dep:
        return handle_move_dep(args)

    # Property commands
    if args.set_priority:
        return handle_set_priority(args)
    if args.set_loe:
        return handle_set_loe(args)
    if args._set_frimpl_status:
        return handle_set_status(args)
    if args.next_status:
        return handle_next_status(args)

    # Task/criteria commands
    if args.check_criteria:
        return handle_check_criteria(args)
    if args.check_task:
        return handle_check_task(args)
    if args.validate_criteria:
        return handle_validate_criteria(args)

    # ADR commands
    if args.create_adr:
        return handle_create_adr(args)
    if args.list_adrs:
        return handle_list_adrs(args)

    # No command specified
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
