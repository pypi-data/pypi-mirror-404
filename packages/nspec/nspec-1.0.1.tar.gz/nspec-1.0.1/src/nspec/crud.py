"""CRUD operations for fRIMPL spec management.

This module provides LLM-friendly commands for creating and deleting specs:
- create_new_spec: Generate FR+IMPL from templates with auto-numbering
- delete_spec: Remove FR+IMPL files (with safety guards)
- get_next_spec_id: Auto-assign spec IDs based on priority ranges

Spec ID Ranges:
    - P0/P1: 001-099 (high priority, current sprint work)
    - P2: 100-499 (medium priority, next sprint candidates)
    - P3: 900-999 (low priority, nspec, nice-to-have)

Note: Directory paths are now configurable via .novabuilt.dev/nspec/config.toml.
See nspec.paths module for configuration details.
"""

import fcntl
import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from nspec.ids import normalize_spec_ref, spec_ref_number
from nspec.paths import NspecPaths, get_paths
from nspec.statuses import (
    FR_STATUSES,
    IMPL_STATUSES,
    FRStatusCode,
    IMPLStatusCode,
    is_completed_status,
)

# Lock directory for file-level locks (avoids polluting source dirs)
_LOCK_DIR = Path("/tmp/nspec-locks")


@contextmanager
def _file_lock(path: Path) -> Iterator[None]:
    """Acquire an exclusive file lock to prevent concurrent read-modify-write races.

    Uses a separate lock file in /tmp to avoid modifying the target directory.
    """
    _LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = _LOCK_DIR / f"{path.name}.lock"
    fd = lock_path.open("w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()


def _line_matches_task_id(line: str, task_id: str) -> bool:
    """Check if a checkbox line contains the given task ID.

    Matches both ``**1**: Desc`` and ``1. Desc`` formats.
    """
    bold_pattern = f"**{task_id}**:"
    plain_pattern_dot = f"] {task_id}. "
    plain_pattern_colon = f"] {task_id}: "
    return bold_pattern in line or plain_pattern_dot in line or plain_pattern_colon in line


# Exceptions expected during CRUD file operations
_NspecCrudErrors = (RuntimeError, ValueError, KeyError, TypeError, OSError, IOError)

# Priority ranges for auto-numbering (specs)
PRIORITY_RANGES = {
    "P0": (1, 499),  # Critical: Full spec range
    "P1": (1, 499),  # High: Full spec range
    "P2": (100, 499),  # Medium: Upper spec range
    "P3": (500, 899),  # Low: Middle-upper range
}

# Epic IDs are kept in a low range for visibility
EPIC_ID_RANGE = (1, 99)


def get_all_spec_ids(
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> set[str]:
    """Get all spec IDs from active + completed directories.

    Args:
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Set of all spec IDs (both active and completed)
    """
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)
    all_ids = set()

    def _extract_ref_from_stem(stem: str) -> str | None:
        match = re.match(r"FR-([ES]\d{3}[a-z]?)", stem, re.IGNORECASE)
        if not match:
            return None
        try:
            return normalize_spec_ref(match.group(1))
        except ValueError:
            return None

    # Active FRs
    if paths.active_frs_dir.exists():
        for path in paths.active_frs_dir.glob("FR-*.md"):
            if path.stem.upper() != "TEMPLATE":
                ref = _extract_ref_from_stem(path.stem)
                if ref:
                    all_ids.add(ref)

    # Completed FRs
    if paths.completed_frs_dir.exists():
        for path in paths.completed_frs_dir.glob("FR-*.md"):
            ref = _extract_ref_from_stem(path.stem)
            if ref:
                all_ids.add(ref)

    return all_ids


def clean_dangling_deps(
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
    *,
    dry_run: bool = False,
) -> list[tuple[str, str, list[str]]]:
    """Remove dependencies pointing to non-existent specs.

    Auto-cleans FR files that reference deleted specs in their deps list.

    Args:
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)
        dry_run: If True, report changes without writing files

    Returns:
        List of (spec_id, fr_path, removed_deps) for each cleaned file
    """
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)
    all_spec_ids = get_all_spec_ids(docs_root, paths_config, project_root)
    cleaned: list[tuple[str, str, list[str]]] = []

    # Check active FRs
    if not paths.active_frs_dir.exists():
        return cleaned

    deps_pattern = re.compile(r"^deps:\s*\[([^\]]*)\]", re.MULTILINE)

    for path in paths.active_frs_dir.glob("FR-*.md"):
        if path.stem.upper() == "TEMPLATE":
            continue

        match = re.match(r"FR-([ES]\d{3}[a-z]?)", path.stem, re.IGNORECASE)
        if not match:
            continue

        try:
            spec_id = normalize_spec_ref(match.group(1))
        except ValueError:
            continue
        content = path.read_text(encoding="utf-8")
        deps_match = deps_pattern.search(content)

        if not deps_match:
            continue

        deps_str = deps_match.group(1)
        if not deps_str.strip():
            continue

        # Parse current deps
        current_deps = [d.strip() for d in deps_str.split(",") if d.strip()]

        # Find dangling deps
        dangling: list[str] = []
        valid: list[str] = []
        for dep in current_deps:
            try:
                normalized = normalize_spec_ref(dep)
            except ValueError:
                # Leave unparseable deps alone (validator will catch)
                valid.append(dep)
                continue

            if normalized in all_spec_ids:
                valid.append(normalized)
            else:
                dangling.append(dep)

        if dangling:
            # Rewrite deps line without dangling refs
            new_deps_str = ", ".join(valid)
            new_deps_line = f"deps: [{new_deps_str}]"
            new_content = deps_pattern.sub(new_deps_line, content)
            if not dry_run:
                path.write_text(new_content, encoding="utf-8")
            cleaned.append((spec_id, str(path), dangling))

    return cleaned


def get_next_spec_id(
    priority: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
    *,
    id_prefix: Literal["S", "E"] = "S",
) -> str:
    """Determine next ID based on type and existing specs.

    First looks for gaps (unused IDs) in the range, then falls back to
    incrementing from the highest used ID.

    Args:
        priority: P0, P1, P2, or P3
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Next available ID (e.g., "S044", "S105", "E007")

    Raises:
        ValueError: If priority range is exhausted
    """
    all_spec_ids = get_all_spec_ids(docs_root, paths_config, project_root)
    if id_prefix == "E":
        range_start, range_end = EPIC_ID_RANGE
    else:
        range_start, range_end = PRIORITY_RANGES[priority]

    # Find all used IDs in range
    used_in_range = set()
    for sid in all_spec_ids:
        numeric = spec_ref_number(sid)
        if range_start <= numeric <= range_end:
            used_in_range.add(numeric)

    if not used_in_range:
        # Range is empty, start at beginning
        return f"{id_prefix}{range_start:03d}"

    # First, look for gaps (reusable IDs)
    highest = max(used_in_range)
    for candidate in range(range_start, highest):
        if candidate not in used_in_range:
            return f"{id_prefix}{candidate:03d}"

    # No gaps found, use next after highest
    next_id = highest + 1
    if next_id > range_end:
        raise ValueError(
            f"Priority range exhausted for {priority} "
            f"(range: {range_start}-{range_end}, highest: {highest})"
        )

    return f"{id_prefix}{next_id:03d}"


def create_new_spec(
    title: str,
    priority: str,
    docs_root: Path,
    fr_template: str | Path | None = None,
    impl_template: str | Path | None = None,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[Path, Path, str]:
    """Create new FR + IMPL from templates.

    Args:
        title: Spec title (e.g., "Feature Name")
        priority: P0, P1, P2, or P3
        docs_root: Path to docs/ directory
        fr_template: Optional path to FR template (relative to docs_root or absolute).
                     Defaults to "frs/active/TEMPLATE.md"
        impl_template: Optional path to IMPL template (relative to docs_root or absolute).
                       Defaults to "impls/active/TEMPLATE.md"
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        (fr_path, impl_path, spec_id) - Paths to created files and assigned ID

    Raises:
        ValueError: If priority is invalid or range exhausted
        FileNotFoundError: If templates don't exist
    """
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    # Validate priority
    if priority not in PRIORITY_RANGES:
        raise ValueError(f"Invalid priority: {priority}. Must be P0-P3.")

    # Get next spec ID
    spec_id = get_next_spec_id(priority, docs_root, paths_config, project_root, id_prefix="S")

    # Check for existing files with this ID (collision detection)
    # This catches cases where an ID is reused with a different slug
    fr_dir = paths.active_frs_dir
    impl_dir = paths.active_impls_dir
    existing_frs = list(fr_dir.glob(f"FR-{spec_id}-*.md"))
    existing_impls = list(impl_dir.glob(f"IMPL-{spec_id}-*.md"))

    if existing_frs:
        raise ValueError(
            f"Spec ID {spec_id} collision: FR file already exists with different slug: "
            f"{existing_frs[0].name}"
        )
    if existing_impls:
        raise ValueError(
            f"Spec ID {spec_id} collision: IMPL file already exists with different slug: "
            f"{existing_impls[0].name}"
        )

    # Generate filenames
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)  # Remove special chars
    slug = re.sub(r"[-\s]+", "-", slug)  # Convert spaces to dashes
    slug = slug.strip("-")

    fr_filename = f"FR-{spec_id}-{slug}.md"
    impl_filename = f"IMPL-{spec_id}-{slug}.md"

    # Resolve template paths
    if fr_template is None:
        fr_template_path = paths.active_frs_dir / "TEMPLATE.md"
    else:
        fr_template_path = Path(fr_template)
        if not fr_template_path.is_absolute():
            fr_template_path = docs_root / fr_template_path

    if impl_template is None:
        impl_template_path = paths.active_impls_dir / "TEMPLATE.md"
    else:
        impl_template_path = Path(impl_template)
        if not impl_template_path.is_absolute():
            impl_template_path = docs_root / impl_template_path

    if not fr_template_path.exists():
        raise FileNotFoundError(f"FR template not found: {fr_template_path}")
    if not impl_template_path.exists():
        raise FileNotFoundError(f"IMPL template not found: {impl_template_path}")

    fr_template = fr_template_path.read_text()
    impl_template = impl_template_path.read_text()

    # Get current date
    from datetime import datetime

    current_date = datetime.now().strftime("%Y-%m-%d")

    # Replace placeholders
    # FR replacements: XXX → spec_id, title in heading, [FEATURE NAME]/[SPEC TITLE] → title
    # P2 → priority, YYYY-MM-DD → current_date
    fr_content = fr_template.replace("XXX", spec_id)
    fr_content = re.sub(
        r"^(# FR-\d{3}: )Title$", rf"\g<1>{title}", fr_content, count=1, flags=re.MULTILINE
    )
    fr_content = fr_content.replace("[FEATURE NAME]", title)
    fr_content = fr_content.replace("[SPEC TITLE]", title)  # For code review templates
    fr_content = fr_content.replace("slug", slug)
    fr_content = fr_content.replace("YYYY-MM-DD", current_date)
    from nspec.statuses import SPEC_PRIORITIES

    _priority_emojis = "".join(p.emoji for p in SPEC_PRIORITIES.values())
    fr_content = re.sub(
        rf"\*\*Priority:\*\*\s+[{_priority_emojis}]\s+P[0-3]",
        f"**Priority:** {_get_priority_emoji(priority)} {priority}",
        fr_content,
    )

    # IMPL replacements: XXX → spec_id, title in heading, [FEATURE NAME]/[SPEC TITLE] → title
    impl_content = impl_template.replace("XXX", spec_id)
    impl_content = re.sub(
        r"^(# IMPL-\d{3}: )Title$", rf"\g<1>{title}", impl_content, count=1, flags=re.MULTILINE
    )
    impl_content = impl_content.replace("[FEATURE NAME]", title)
    impl_content = impl_content.replace("[SPEC TITLE]", title)  # For code review templates
    impl_content = impl_content.replace("slug", slug)
    impl_content = impl_content.replace("YYYY-MM-DD", current_date)

    # Write files
    fr_path = paths.active_frs_dir / fr_filename
    impl_path = paths.active_impls_dir / impl_filename

    fr_path.write_text(fr_content)
    impl_path.write_text(impl_content)

    return fr_path, impl_path, spec_id


def delete_spec(
    spec_id: str,
    docs_root: Path,
    force: bool = False,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[Path, Path]:
    """Delete FR + IMPL files for a spec.

    Safety: Requires force=True or REALLY_DELETE_NSPEC_ITEM=Y environment variable.

    Args:
        spec_id: Spec ID to delete (e.g., "S044" or "044")
        docs_root: Path to docs/ directory
        force: Skip safety check if True
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        (fr_path, impl_path) - Paths of deleted files

    Raises:
        RuntimeError: If safety check fails
        FileNotFoundError: If FR or IMPL not found
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    # Safety check - skip if force=True
    if not force and os.environ.get("REALLY_DELETE_NSPEC_ITEM") != "Y":
        raise RuntimeError(
            "Safety check failed: use --force or set REALLY_DELETE_NSPEC_ITEM=Y\n"
            "Usage: make nspec.delete <spec_id> FORCE=1"
        )

    # Find FR and IMPL files
    fr_pattern = f"FR-{spec_id}-*.md"
    impl_pattern = f"IMPL-{spec_id}-*.md"

    fr_dir = paths.active_frs_dir
    impl_dir = paths.active_impls_dir

    fr_files = list(fr_dir.glob(fr_pattern))
    impl_files = list(impl_dir.glob(impl_pattern))

    if not fr_files:
        raise FileNotFoundError(f"FR-{spec_id}-*.md not found in {fr_dir}")
    if not impl_files:
        raise FileNotFoundError(f"IMPL-{spec_id}-*.md not found in {impl_dir}")

    # Take first match (should only be one)
    fr_path = fr_files[0]
    impl_path = impl_files[0]

    # Delete files
    fr_path.unlink()
    impl_path.unlink()

    return fr_path, impl_path


def _check_completion_readiness(
    fr_path: Path, impl_path: Path, spec_id: str
) -> tuple[bool, list[str]]:
    """Check if a spec is ready for completion by validating acceptance criteria and tasks.

    Supports both completed and rejected specs:
    - Completed: FR must be ✅ Completed, IMPL must be 🟠 Ready, AC checked, tasks done
    - Rejected: FR must be ❌ Rejected, skips AC/task validation

    Checkbox markers recognized as "complete":
    - [x] - Explicitly completed
    - [~] - Obsolete/not applicable (intentionally skipped)
    - [→XXX] - Delegated to another spec

    Args:
        fr_path: Path to FR file
        impl_path: Path to IMPL file
        spec_id: Spec ID being checked

    Returns:
        (is_ready, warnings) - is_ready=True if validation passes, warnings list always returned
    """
    from nspec.tasks import AcceptanceCriteriaParser, TaskParser

    warnings = []
    fr_content = fr_path.read_text()
    impl_content = impl_path.read_text()

    # Check FR status first - rejected specs skip AC/task validation
    fr_status = re.search(r"^\*\*Status:\*\*\s+(.+)$", fr_content, re.MULTILINE)
    is_rejected = fr_status and ("❌" in fr_status.group(1) or "Rejected" in fr_status.group(1))

    if is_rejected:
        # Rejected specs are ready for archival without AC/task validation
        warnings.append("ℹ️  Spec rejected - skipping AC/task validation")
        return True, warnings

    # For completed specs, check FR acceptance criteria using the parser
    # This ensures consistent counting with nspec_task display
    try:
        ac_parser = AcceptanceCriteriaParser()
        acceptance_criteria = ac_parser.parse(fr_content, fr_path)
        if acceptance_criteria:
            # Parser only returns [x] and [ ] items, but we also need to count [~] as complete
            # Re-scan for all AC items including obsolete markers
            ac_pattern = r"^- \[(.)\].*AC-[FQPD]"
            fr_criteria = re.findall(ac_pattern, fr_content, re.MULTILINE)
            if fr_criteria:
                # Count [x], [~], and [→...] as complete
                checked = sum(1 for c in fr_criteria if c.lower() == "x" or c == "~" or c == "→")
                total = len(fr_criteria)
                if checked < total:
                    remaining = total - checked
                    warnings.append(  # pyright: ignore[reportUnknownMemberType]
                        f"❌ FR acceptance criteria incomplete: "
                        f"{checked}/{total} checked ({remaining} remaining)"
                    )
    except ValueError:
        # Parser failed - fall back to simple regex (may have format issues)
        ac_pattern = r"^- \[(.)\].*AC-[FQPD]"
        fr_criteria = re.findall(ac_pattern, fr_content, re.MULTILINE)
        if fr_criteria:
            checked = sum(1 for c in fr_criteria if c.lower() == "x" or c == "~" or c == "→")
            total = len(fr_criteria)
            if checked < total:
                remaining = total - checked
                warnings.append(
                    f"❌ FR acceptance criteria incomplete: "
                    f"{checked}/{total} checked ({remaining} remaining)"
                )

    # Check IMPL tasks using the TaskParser for consistency with nspec_task display
    try:
        task_parser = TaskParser()
        task_tree = task_parser.parse(impl_content, impl_path)
        flat_tasks = task_parser.flatten(task_tree)
        if flat_tasks:
            # TaskParser already handles [x], [~], and [→XXX] as complete.
            # IMPORTANT: Count nested tasks too; parse() returns a tree.
            checked = sum(1 for t in flat_tasks if t.completed)
            total = len(flat_tasks)
            completion_pct = (checked / total * 100) if total > 0 else 100
            if checked < total:
                remaining = [t for t in flat_tasks if not t.completed]
                sample = "; ".join(t.description for t in remaining[:5])
                suffix = f" Remaining: {sample}" if sample else ""
                warnings.append(
                    f"❌ IMPL tasks incomplete: "
                    f"{checked}/{total} checked ({completion_pct:.0f}% complete).{suffix}"
                )
    except ValueError:
        # Parser failed - fall back to simple regex counting [x] and [~]
        impl_tasks = re.findall(r"^- \[(.)\]", impl_content, re.MULTILINE)
        if impl_tasks:
            checked = sum(1 for c in impl_tasks if c.lower() == "x" or c == "~" or c == "→")
            total = len(impl_tasks)
            completion_pct = (checked / total * 100) if total > 0 else 100
            if checked < total:
                warnings.append(
                    f"❌ IMPL tasks incomplete: "
                    f"{checked}/{total} checked ({completion_pct:.0f}% complete)"
                )

    # Check if status is already marked complete
    impl_status = re.search(r"^\*\*Status:\*\*\s+(.+)$", impl_content, re.MULTILINE)

    if fr_status and "✅" not in fr_status.group(1) and "Completed" not in fr_status.group(1):
        warnings.append(f"❌ FR status not marked complete: {fr_status.group(1)}")

    # IMPL terminal state is "🟠 Ready" (not "✅ Completed" like FR)
    if impl_status and "🟠" not in impl_status.group(1) and "Ready" not in impl_status.group(1):
        warnings.append(f"❌ IMPL status not ready: {impl_status.group(1)} (expected 🟠 Ready)")

    # Check review verdict and reviewer
    verdict = _get_review_verdict(impl_content)
    implementer = _get_impl_field(impl_content, "Implementer")
    reviewer = _get_impl_field(impl_content, "Reviewer")

    if verdict != "APPROVED":
        if verdict == "NEEDS_WORK":
            warnings.append("❌ Review verdict is NEEDS_WORK - address feedback before completing")
        elif verdict == "PENDING" or not verdict:
            warnings.append("❌ Review not completed - run nspec_request_review then get approval")
        else:
            warnings.append(f"❌ Review verdict invalid: {verdict} (expected APPROVED)")

    if implementer and reviewer:
        if implementer.lower() == reviewer.lower():
            warnings.append(
                f"❌ Reviewer ({reviewer}) cannot be same as implementer ({implementer})"
            )
    elif not reviewer and verdict == "APPROVED":
        warnings.append("❌ No reviewer recorded but verdict is APPROVED - invalid state")

    # Determine if ready
    blockers = [w for w in warnings if w.startswith("❌")]
    is_ready = len(blockers) == 0

    return is_ready, warnings


def complete_spec(
    spec_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[Path, Path, Path, Path]:
    """Move FR + IMPL files to completed directory using git mv.

    Validates completion readiness by checking:
    - FR acceptance criteria are checked
    - IMPL tasks are complete
    - Status fields are marked complete

    If files already exist in completed directory:
    - Diff active vs completed versions
    - If identical: git rm active files (no move needed)
    - If different: raise error (manual resolution required)

    Args:
        spec_id: Spec ID to complete (e.g., "044")
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        (fr_old_path, fr_new_path, impl_old_path, impl_new_path)

    Raises:
        FileNotFoundError: If FR or IMPL not found in active directories
        RuntimeError: If git mv fails, files differ, or validation fails
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)
    import subprocess

    # Find FR and IMPL files in active directories
    fr_pattern = f"FR-{spec_id}-*.md"
    impl_pattern = f"IMPL-{spec_id}-*.md"

    fr_dir = paths.active_frs_dir
    impl_dir = paths.active_impls_dir
    completed_dir = paths.completed_done

    fr_files = list(fr_dir.glob(fr_pattern))
    impl_files = list(impl_dir.glob(impl_pattern))

    # Check if files are already in completed directory
    if not fr_files or not impl_files:
        completed_fr_files = list(completed_dir.glob(fr_pattern))
        completed_impl_files = list(completed_dir.glob(impl_pattern))

        if completed_fr_files and completed_impl_files:
            print(f"✅ Spec {spec_id} is already completed")
            print(f"   FR: {completed_fr_files[0].relative_to(docs_root)}")
            print(f"   IMPL: {completed_impl_files[0].relative_to(docs_root)}")
            return (
                fr_dir / completed_fr_files[0].name,  # Dummy old path
                completed_fr_files[0],
                impl_dir / completed_impl_files[0].name,  # Dummy old path
                completed_impl_files[0],
            )

    if not fr_files:
        raise FileNotFoundError(f"FR-{spec_id}-*.md not found in {fr_dir}")
    if not impl_files:
        raise FileNotFoundError(f"IMPL-{spec_id}-*.md not found in {impl_dir}")

    # Take first match (should only be one)
    fr_old_path = fr_files[0]
    impl_old_path = impl_files[0]

    fr_new_path = completed_dir / fr_old_path.name
    impl_new_path = completed_dir / impl_old_path.name

    # Validate completion readiness
    is_ready, warnings = _check_completion_readiness(fr_old_path, impl_old_path, spec_id)

    if warnings:
        print(f"\n🔍 Completion validation for Spec {spec_id}:")
        for warning in warnings:
            print(f"   {warning}")
        print()

    if not is_ready:
        error_msg = f"❌ Spec {spec_id} is not ready for completion.\n\n"
        error_msg += "Issues found:\n"
        for warning in [w for w in warnings if w.startswith("❌")]:
            error_msg += f"  {warning}\n"
        error_msg += "\nFix the validation or fix your spec:\n"
        error_msg += "  1. Mark all acceptance criteria as complete in FR file\n"
        error_msg += "  2. Ensure FR status is '✅ Completed' and IMPL status is '🟠 Ready'\n"
        error_msg += "  3. Update IMPL task checkboxes as work is completed\n"
        raise RuntimeError(error_msg)

    # Check if files already exist in completed directory
    if fr_new_path.exists() or impl_new_path.exists():
        # Diff active vs completed
        fr_same = False
        impl_same = False

        if fr_new_path.exists():
            fr_same = fr_old_path.read_text() == fr_new_path.read_text()

        if impl_new_path.exists():
            impl_same = impl_old_path.read_text() == impl_new_path.read_text()

        # If both exist and are identical, just delete active files
        if fr_new_path.exists() and impl_new_path.exists() and fr_same and impl_same:
            print("ℹ️  Files already exist in completed directory and are identical")
            print(f"   Removing active files: {fr_old_path.name}, {impl_old_path.name}")
            subprocess.run(["git", "rm", str(fr_old_path)], check=True, capture_output=True)
            subprocess.run(["git", "rm", str(impl_old_path)], check=True, capture_output=True)
            return fr_old_path, fr_new_path, impl_old_path, impl_new_path

        # If files differ, raise error
        error_msg = "Files already exist in completed directory but differ:\n"
        if fr_new_path.exists() and not fr_same:
            error_msg += f"  - {fr_new_path} differs from {fr_old_path}\n"
        if impl_new_path.exists() and not impl_same:
            error_msg += f"  - {impl_new_path} differs from {impl_old_path}\n"
        error_msg += "Manual resolution required."
        raise RuntimeError(error_msg)

    # Update status to completed before moving files
    fr_content = fr_old_path.read_text()
    impl_content = impl_old_path.read_text()

    # Replace status with completed status (using centralized status definition)
    completed_status = FR_STATUSES[FRStatusCode.COMPLETED].full
    fr_content = re.sub(
        r"^\*\*Status:\*\*.*$", f"**Status:** {completed_status}", fr_content, flags=re.MULTILINE
    )
    impl_content = re.sub(
        r"^\*\*Status:\*\*.*$", f"**Status:** {completed_status}", impl_content, flags=re.MULTILINE
    )

    # Write updated content
    fr_old_path.write_text(fr_content)
    impl_old_path.write_text(impl_content)

    print(f"✅ Updated status to completed for {spec_id}")

    # Ensure completed directory exists
    completed_dir.mkdir(parents=True, exist_ok=True)

    # Use git mv to move files
    try:
        subprocess.run(
            ["git", "mv", str(fr_old_path), str(fr_new_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "mv", str(impl_old_path), str(impl_new_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git mv failed: {e.stderr}") from e

    # Show post-completion checklist
    print(f"\n✅ Spec {spec_id} completed successfully!")
    print(f"   • Moved: {fr_old_path.name} → docs/completed/done/")
    print(f"   • Moved: {impl_old_path.name} → docs/completed/done/")
    print("\n📋 Post-Completion Checklist:")
    print("   1. Run: make nspec")
    print("      → Regenerates NSPEC.md (removes from active)")
    print("      → Auto-updates NSPEC_COMPLETED.md (adds to completed)")
    print("   2. Run: make nspec.validate-consistency")
    print("      → Final consistency check")
    print("   3. Optional: Document this work session")
    print(f"      → Create: docs/08-sessions/session-YYYY-MM-DD-spec-{spec_id}-summary.md")
    print("   4. Run: make all")
    print("      → Full validation (tests, lint, security)")
    print("   5. Commit:")
    print("      → git add .")
    print(f'      → git commit -m "feat: Complete Spec {spec_id}"')
    print()

    return fr_old_path, fr_new_path, impl_old_path, impl_new_path


def supersede_spec(
    spec_id: str,
    docs_root: Path,
    force: bool = False,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[Path, Path, Path, Path]:
    """Move a spec to the superseded directory.

    This is used when a spec has been superseded by another spec or epic.
    The spec is moved from active directories (10/11) to docs/completed/superseded/
    and its status is updated to Superseded.

    Args:
        spec_id: Spec ID to supersede (e.g., "053")
        docs_root: Path to docs/ directory
        force: If True, skip validation checks
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Tuple of (fr_old_path, fr_new_path, impl_old_path, impl_new_path)

    Raises:
        FileNotFoundError: If FR or IMPL not found in active directories
        RuntimeError: If git mv fails or files already exist in superseded directory
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)
    import subprocess

    # Find FR and IMPL files in active directories
    fr_pattern = f"FR-{spec_id}-*.md"
    impl_pattern = f"IMPL-{spec_id}-*.md"

    fr_dir = paths.active_frs_dir
    impl_dir = paths.active_impls_dir
    superseded_dir = paths.superseded_dir

    fr_files = list(fr_dir.glob(fr_pattern))
    impl_files = list(impl_dir.glob(impl_pattern))

    # Check if files are already in superseded directory
    if not fr_files or not impl_files:
        superseded_fr_files = list(superseded_dir.glob(fr_pattern))
        superseded_impl_files = list(superseded_dir.glob(impl_pattern))

        if superseded_fr_files and superseded_impl_files:
            print(f"✅ Spec {spec_id} is already superseded")
            print(f"   FR: {superseded_fr_files[0].relative_to(docs_root)}")
            print(f"   IMPL: {superseded_impl_files[0].relative_to(docs_root)}")
            return (
                fr_dir / superseded_fr_files[0].name,  # Dummy old path
                superseded_fr_files[0],
                impl_dir / superseded_impl_files[0].name,  # Dummy old path
                superseded_impl_files[0],
            )

    if not fr_files:
        raise FileNotFoundError(f"FR-{spec_id}-*.md not found in {fr_dir}")
    if not impl_files:
        raise FileNotFoundError(f"IMPL-{spec_id}-*.md not found in {impl_dir}")

    # Take first match (should only be one)
    fr_old_path = fr_files[0]
    impl_old_path = impl_files[0]

    fr_new_path = superseded_dir / fr_old_path.name
    impl_new_path = superseded_dir / impl_old_path.name

    # Check if files already exist in superseded directory
    if fr_new_path.exists() or impl_new_path.exists():
        raise RuntimeError(
            f"Files already exist in superseded directory:\n"
            f"  - {fr_new_path.relative_to(docs_root)}\n"
            f"  - {impl_new_path.relative_to(docs_root)}\n"
            "Manual resolution required."
        )

    # Update status to superseded before moving files
    fr_content = fr_old_path.read_text()
    impl_content = impl_old_path.read_text()

    # Replace status with superseded status (using centralized status definitions)
    superseded_status = FR_STATUSES[FRStatusCode.SUPERSEDED].full
    hold_status = IMPL_STATUSES[IMPLStatusCode.HOLD].full
    fr_content = re.sub(
        r"^\*\*Status:\*\*.*$", f"**Status:** {superseded_status}", fr_content, flags=re.MULTILINE
    )
    impl_content = re.sub(
        r"^\*\*Status:\*\*.*$", f"**Status:** {hold_status}", impl_content, flags=re.MULTILINE
    )

    # Write updated content
    fr_old_path.write_text(fr_content)
    impl_old_path.write_text(impl_content)

    print(f"✅ Updated status to superseded for Spec {spec_id}")

    # Ensure superseded directory exists
    superseded_dir.mkdir(parents=True, exist_ok=True)

    # Use git mv to move files
    try:
        subprocess.run(
            ["git", "mv", str(fr_old_path), str(fr_new_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "mv", str(impl_old_path), str(impl_new_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git mv failed: {e.stderr}") from e

    # Show post-supersede message
    print(f"\n🔄 Spec {spec_id} superseded successfully!")
    print(f"   • Moved: {fr_old_path.name} → docs/completed/superseded/")
    print(f"   • Moved: {impl_old_path.name} → docs/completed/superseded/")
    print("\n📋 Next Steps:")
    print("   1. Run: make nspec")
    print("      → Regenerates NSPEC.md")
    print("   2. Update the superseding spec/epic to reference this spec")
    print("   3. Commit:")
    print("      → git add .")
    print(f'      → git commit -m "chore: Supersede Spec {spec_id}"')
    print()

    return fr_old_path, fr_new_path, impl_old_path, impl_new_path


def reject_spec(
    spec_id: str,
    docs_root: Path,
    force: bool = False,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[Path, Path, Path, Path]:
    """Move a spec to the rejected directory.

    This is used when a spec has been rejected (won't implement, duplicate, etc).
    The spec is moved from active directories (10/11) to docs/completed/rejected/
    and its status is updated to Rejected.

    Args:
        spec_id: Spec ID to reject (e.g., "281")
        docs_root: Path to docs/ directory
        force: If True, skip validation checks
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Tuple of (fr_old_path, fr_new_path, impl_old_path, impl_new_path)

    Raises:
        FileNotFoundError: If FR or IMPL not found in active directories
        RuntimeError: If git mv fails or files already exist in rejected directory
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)
    import subprocess

    # Find FR and IMPL files in active directories
    fr_pattern = f"FR-{spec_id}-*.md"
    impl_pattern = f"IMPL-{spec_id}-*.md"

    fr_dir = paths.active_frs_dir
    impl_dir = paths.active_impls_dir
    rejected_dir = paths.rejected_dir

    fr_files = list(fr_dir.glob(fr_pattern))
    impl_files = list(impl_dir.glob(impl_pattern))

    # Check if files are already in rejected directory
    if not fr_files or not impl_files:
        rejected_fr_files = list(rejected_dir.glob(fr_pattern))
        rejected_impl_files = list(rejected_dir.glob(impl_pattern))

        if rejected_fr_files and rejected_impl_files:
            print(f"✅ Spec {spec_id} is already rejected")
            print(f"   FR: {rejected_fr_files[0].relative_to(docs_root)}")
            print(f"   IMPL: {rejected_impl_files[0].relative_to(docs_root)}")
            return (
                fr_dir / rejected_fr_files[0].name,  # Dummy old path
                rejected_fr_files[0],
                impl_dir / rejected_impl_files[0].name,  # Dummy old path
                rejected_impl_files[0],
            )

    if not fr_files:
        raise FileNotFoundError(f"FR-{spec_id}-*.md not found in {fr_dir}")
    if not impl_files:
        raise FileNotFoundError(f"IMPL-{spec_id}-*.md not found in {impl_dir}")

    # Take first match (should only be one)
    fr_old_path = fr_files[0]
    impl_old_path = impl_files[0]

    fr_new_path = rejected_dir / fr_old_path.name
    impl_new_path = rejected_dir / impl_old_path.name

    # Check if files already exist in rejected directory
    if fr_new_path.exists() or impl_new_path.exists():
        raise RuntimeError(
            f"Files already exist in rejected directory:\n"
            f"  - {fr_new_path.relative_to(docs_root)}\n"
            f"  - {impl_new_path.relative_to(docs_root)}\n"
            "Manual resolution required."
        )

    # Update status to rejected before moving files
    fr_content = fr_old_path.read_text()
    impl_content = impl_old_path.read_text()

    # Replace status with rejected status (using centralized status definitions)
    rejected_status = FR_STATUSES[FRStatusCode.REJECTED].full
    hold_status = IMPL_STATUSES[IMPLStatusCode.HOLD].full
    fr_content = re.sub(
        r"^\*\*Status:\*\*.*$", f"**Status:** {rejected_status}", fr_content, flags=re.MULTILINE
    )
    impl_content = re.sub(
        r"^\*\*Status:\*\*.*$", f"**Status:** {hold_status}", impl_content, flags=re.MULTILINE
    )

    # Write updated content
    fr_old_path.write_text(fr_content)
    impl_old_path.write_text(impl_content)

    print(f"✅ Updated status to rejected for Spec {spec_id}")

    # Ensure rejected directory exists
    rejected_dir.mkdir(parents=True, exist_ok=True)

    # Use git mv to move files
    try:
        subprocess.run(
            ["git", "mv", str(fr_old_path), str(fr_new_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "mv", str(impl_old_path), str(impl_new_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git mv failed: {e.stderr}") from e

    # Show post-reject message
    print(f"\n❌ Spec {spec_id} rejected successfully!")
    print(f"   • Moved: {fr_old_path.name} → docs/completed/rejected/")
    print(f"   • Moved: {impl_old_path.name} → docs/completed/rejected/")
    print("\n📋 Next Steps:")
    print("   1. Run: make nspec")
    print("      → Regenerates NSPEC.md")
    print("   2. Commit:")
    print("      → git add .")
    print(f'      → git commit -m "chore: Reject Spec {spec_id}"')
    print()

    return fr_old_path, fr_new_path, impl_old_path, impl_new_path


def finalize_spec(
    spec_id: str,
    docs_root: Path,
    execute: bool = False,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> None:
    """Show completion status and provide command to finalize a spec.

    Lists all unchecked acceptance criteria and tasks, then provides
    a single make command that will mark everything complete and archive.

    Args:
        spec_id: Spec ID to finalize (e.g., "183")
        docs_root: Path to docs/ directory
        execute: If True, actually mark everything complete and run complete
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        None (prints to stdout)

    Raises:
        FileNotFoundError: If FR or IMPL not found
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    # Find FR and IMPL files
    fr_pattern = f"FR-{spec_id}-*.md"
    impl_pattern = f"IMPL-{spec_id}-*.md"

    fr_dir = paths.active_frs_dir
    impl_dir = paths.active_impls_dir

    fr_files = list(fr_dir.glob(fr_pattern))
    impl_files = list(impl_dir.glob(impl_pattern))

    if not fr_files:
        raise FileNotFoundError(f"FR-{spec_id}-*.md not found in {fr_dir}")
    if not impl_files:
        raise FileNotFoundError(f"IMPL-{spec_id}-*.md not found in {impl_dir}")

    fr_path = fr_files[0]
    impl_path = impl_files[0]
    fr_content = fr_path.read_text()
    impl_content = impl_path.read_text()

    # Extract unchecked acceptance criteria
    unchecked_criteria = []
    for match in re.finditer(r"^- \[ \]\s*(AC-[FQPD]\d+:?.*)$", fr_content, re.MULTILINE):
        unchecked_criteria.append(match.group(1).strip())

    # Extract unchecked IMPL tasks
    unchecked_tasks = []
    for match in re.finditer(
        r"^- \[ \]\s*\*\*(\d+\.\d+)\*\*:?\s*(.*)$", impl_content, re.MULTILINE
    ):
        task_id = match.group(1)
        task_desc = match.group(2).strip()[:50]  # Truncate for display
        unchecked_tasks.append(f"{task_id}: {task_desc}")

    # Check status
    fr_status = re.search(r"^\*\*Status:\*\*\s+(.+)$", fr_content, re.MULTILINE)
    impl_status = re.search(r"^\*\*Status:\*\*\s+(.+)$", impl_content, re.MULTILINE)

    fr_complete = fr_status and is_completed_status(fr_status.group(1))
    impl_complete = impl_status and is_completed_status(impl_status.group(1))

    if execute:
        # Mark all unchecked criteria as complete
        updated_fr = fr_content
        for _ in unchecked_criteria:
            updated_fr = re.sub(
                r"^(- )\[ \](\s*AC-[FQPD])", r"\1[x]\2", updated_fr, count=1, flags=re.MULTILINE
            )

        # Mark all unchecked tasks as complete
        updated_impl = impl_content
        updated_impl = re.sub(
            r"^(- )\[ \](\s*\*\*\d+\.\d+\*\*)", r"\1[x]\2", updated_impl, flags=re.MULTILINE
        )

        # Update status to Completed (using centralized status definition)
        completed_status = FR_STATUSES[FRStatusCode.COMPLETED].full
        updated_fr = re.sub(
            r"^\*\*Status:\*\*.*$",
            f"**Status:** {completed_status}",
            updated_fr,
            flags=re.MULTILINE,
        )
        updated_impl = re.sub(
            r"^\*\*Status:\*\*.*$",
            f"**Status:** {completed_status}",
            updated_impl,
            flags=re.MULTILINE,
        )

        # Write files
        fr_path.write_text(updated_fr)
        impl_path.write_text(updated_impl)

        print(f"✅ Marked {len(unchecked_criteria)} acceptance criteria complete")
        print(f"✅ Marked {len(unchecked_tasks)} IMPL tasks complete")
        print("✅ Updated FR to Completed and IMPL to Ready")
        print()
        print(f"Now run: make nspec.complete {spec_id}")
        return

    # Display mode - show what needs to be done
    print(f"\n📋 Spec {spec_id} Completion Status")
    print("=" * 50)

    # Status
    print("\n📊 Status:")
    print(
        f"   FR:   {fr_status.group(1) if fr_status else 'Unknown'} {'✅' if fr_complete else '❌'}"
    )
    impl_status_text = impl_status.group(1) if impl_status else "Unknown"
    impl_check = "✅" if impl_complete else "❌"
    print(f"   IMPL: {impl_status_text} {impl_check}")

    # Unchecked criteria
    if unchecked_criteria:
        print(f"\n📝 Unchecked Acceptance Criteria ({len(unchecked_criteria)}):")
        for ac in unchecked_criteria:
            print(f"   - [ ] {ac}")
    else:
        print("\n✅ All acceptance criteria complete")

    # Unchecked tasks
    if unchecked_tasks:
        print(f"\n📝 Unchecked IMPL Tasks ({len(unchecked_tasks)}):")
        for task in unchecked_tasks[:10]:  # Limit display
            print(f"   - [ ] {task}")
        if len(unchecked_tasks) > 10:
            print(f"   ... and {len(unchecked_tasks) - 10} more")
    else:
        print("\n✅ All IMPL tasks complete")

    # Provide finalize command
    needs_work = unchecked_criteria or unchecked_tasks or not fr_complete or not impl_complete
    if needs_work:
        print("\n🚀 To mark everything complete and archive:")
        print(f"   make nspec.finalize {spec_id} EXECUTE=1")
        print()
        print("   This will:")
        if unchecked_criteria:
            print(f"   • Mark {len(unchecked_criteria)} acceptance criteria as [x]")
        if unchecked_tasks:
            print(f"   • Mark {len(unchecked_tasks)} IMPL tasks as [x]")
        if not fr_complete or not impl_complete:
            print("   • Set FR to ✅ Completed and IMPL to 🟠 Ready")
        print(f"   • Then run: make nspec.complete {spec_id}")
    else:
        print(f"\n✅ Spec {spec_id} is ready for completion!")
        print(f"   Run: make nspec.complete {spec_id}")

    print()


def add_dependency(
    spec_id: str,
    dependency_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> dict[str, Path | str | None]:
    """Add a dependency to a spec's FR file.

    Updates the deps: [...] line in the FR file to include the new dependency.
    Creates the deps line if it doesn't exist.

    If the target spec is an epic and the dependency already belongs to another
    epic, the dependency is automatically moved (removed from the old epic first).

    Args:
        spec_id: Spec ID to update (e.g., "093")
        dependency_id: Dependency to add (e.g., "090")
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Dict with keys:
            - path: Path to updated FR file
            - moved_from: Epic ID if dependency was moved from another epic, None otherwise

    Raises:
        FileNotFoundError: If FR not found
        ValueError: If dependency already exists or is self-referential
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)
    import re

    from nspec.datasets import DatasetLoader

    spec_id = normalize_spec_ref(spec_id)
    dependency_id = normalize_spec_ref(dependency_id)

    # Find FR file
    fr_pattern = f"FR-{spec_id}-*.md"
    fr_dir = paths.active_frs_dir
    fr_files = list(fr_dir.glob(fr_pattern))

    if not fr_files:
        raise FileNotFoundError(f"FR-{spec_id}-*.md not found in {fr_dir}")

    fr_path = fr_files[0]

    # Check for self-referential dependency
    if spec_id == dependency_id:
        raise ValueError(f"Cannot add self-referential dependency: {spec_id}")

    # Track if we moved the dependency from another epic
    moved_from: str | None = None

    # Check if target is an epic and dependency is already in another epic
    loader = DatasetLoader(docs_root=docs_root)
    datasets = loader.load()

    target_fr = datasets.active_frs.get(spec_id)
    if target_fr and target_fr.type == "Epic":
        # Target is an epic - check if dependency is in another epic
        for epic_id, fr in datasets.active_frs.items():
            if fr.type == "Epic" and epic_id != spec_id and dependency_id in fr.deps:
                # Dependency is in another epic - remove it first
                remove_dependency(epic_id, dependency_id, docs_root, paths_config, project_root)
                moved_from = epic_id
                break

    # Read current content
    content = fr_path.read_text()

    # Check if deps line exists
    deps_match = re.search(r"^deps:\s*\[(.*?)\]$", content, re.MULTILINE)

    if deps_match:
        # Parse existing dependencies
        deps_str = deps_match.group(1).strip()
        existing_deps = [d.strip() for d in deps_str.split(",") if d.strip()]

        # Check if dependency already exists
        if dependency_id in existing_deps:
            raise ValueError(f"Dependency {dependency_id} already exists in FR-{spec_id}")

        # Add new dependency
        existing_deps.append(dependency_id)
        new_deps_str = ", ".join(existing_deps)
        new_deps_line = f"deps: [{new_deps_str}]"

        # Replace old deps line
        content = re.sub(r"^deps:\s*\[.*?\]$", new_deps_line, content, flags=re.MULTILINE)
    else:
        # Find where to insert deps line (after **Dependencies:** header or before ## section)
        # Look for **Dependencies:** section first
        deps_header_match = re.search(r"(\*\*Dependencies:\*\*\s*\n)", content, re.MULTILINE)

        if deps_header_match:
            # Insert after **Dependencies:** header
            insert_pos = deps_header_match.end()
            content = content[:insert_pos] + f"deps: [{dependency_id}]\n" + content[insert_pos:]
        else:
            # Insert before first ## section
            section_match = re.search(r"^## ", content, re.MULTILINE)
            if section_match:
                insert_pos = section_match.start()
                content = (
                    content[:insert_pos]
                    + f"\n**Dependencies:**\ndeps: [{dependency_id}]\n\n"
                    + content[insert_pos:]
                )
            else:
                # Append at end
                content += f"\n\n**Dependencies:**\ndeps: [{dependency_id}]\n"

    # Write updated content
    fr_path.write_text(content)

    return {"path": fr_path, "moved_from": moved_from}


def remove_dependency(
    spec_id: str,
    dependency_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Remove a dependency from a spec's FR file.

    Updates the deps: [...] line in the FR file to remove the dependency.

    Args:
        spec_id: Spec ID to update (e.g., "093")
        dependency_id: Dependency to remove (e.g., "104")
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Path to updated FR file

    Raises:
        FileNotFoundError: If FR not found
        ValueError: If dependency doesn't exist
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    # Find FR file
    fr_pattern = f"FR-{spec_id}-*.md"
    fr_dir = paths.active_frs_dir
    fr_files = list(fr_dir.glob(fr_pattern))

    if not fr_files:
        raise FileNotFoundError(f"FR-{spec_id}-*.md not found in {fr_dir}")

    fr_path = fr_files[0]

    # Read current content
    content = fr_path.read_text()

    # Check if deps line exists
    deps_match = re.search(r"^deps:\s*\[(.*?)\]$", content, re.MULTILINE)

    if not deps_match:
        raise ValueError(f"No dependencies found in FR-{spec_id}")

    # Parse existing dependencies
    deps_str = deps_match.group(1).strip()
    existing_deps = [d.strip() for d in deps_str.split(",") if d.strip()]

    # Check if dependency exists
    if dependency_id not in existing_deps:
        raise ValueError(f"Dependency {dependency_id} not found in FR-{spec_id}")

    # Remove dependency
    existing_deps.remove(dependency_id)

    if existing_deps:
        # Update deps line with remaining dependencies
        new_deps_str = ", ".join(existing_deps)
        new_deps_line = f"deps: [{new_deps_str}]"
        content = re.sub(r"^deps:\s*\[.*?\]$", new_deps_line, content, flags=re.MULTILINE)
    else:
        # Remove entire deps line if no dependencies left
        content = re.sub(r"^deps:\s*\[.*?\]\n?", "", content, flags=re.MULTILINE)

    # Write updated content
    fr_path.write_text(content)

    return fr_path


def move_dependency(
    spec_id: str,
    target_epic_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> dict[str, list[str] | str | None]:
    """Move a spec to a target epic, removing from any other epics.

    This is a convenience method that:
    1. Finds all epics that currently have this spec as a dependency
    2. Removes the spec from all epics except the target
    3. Adds the spec to the target epic (if not already there)
    4. Auto-bumps the spec's priority if needed for parity

    Args:
        spec_id: Spec ID to move (e.g., "306")
        target_epic_id: Target epic ID (e.g., "297")
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Dict with keys:
            - removed_from: List of epic IDs spec was removed from
            - added_to: Epic ID if added (None if already there)
            - priority_bumped: New priority if bumped (None if not)

    Raises:
        FileNotFoundError: If spec or epic FR not found
        ValueError: If target is not an epic
    """
    from nspec.datasets import DatasetLoader

    spec_id = normalize_spec_ref(spec_id)
    target_epic_id = normalize_spec_ref(target_epic_id)

    # Load datasets to find current state
    loader = DatasetLoader(docs_root=docs_root)
    datasets = loader.load()

    # Verify target is an epic
    target_fr = datasets.active_frs.get(target_epic_id)
    if not target_fr:
        raise FileNotFoundError(f"Epic FR-{target_epic_id} not found")
    if target_fr.type != "Epic":
        raise ValueError(f"Spec {target_epic_id} is not an epic (type: {target_fr.type})")

    # Verify spec exists
    spec_fr = datasets.active_frs.get(spec_id)
    if not spec_fr:
        raise FileNotFoundError(f"Spec FR-{spec_id} not found")

    # Find all epics that have this spec
    epics_with_spec = []
    for epic_id, fr in datasets.active_frs.items():
        if fr.type == "Epic" and spec_id in fr.deps:
            epics_with_spec.append(epic_id)

    result: dict[str, list[str] | str | None] = {
        "removed_from": [],
        "added_to": None,
        "priority_bumped": None,
    }

    # Remove from other epics
    for epic_id in epics_with_spec:
        if epic_id != target_epic_id:
            remove_dependency(epic_id, spec_id, docs_root, paths_config, project_root)
            result["removed_from"].append(epic_id)  # type: ignore[union-attr]

    # Add to target epic if not already there
    if target_epic_id not in epics_with_spec:
        add_dependency(target_epic_id, spec_id, docs_root, paths_config, project_root)
        result["added_to"] = target_epic_id

    # Check if priority bump needed
    target_level = _get_priority_level(target_fr.priority)
    spec_level = _get_priority_level(spec_fr.priority)

    if spec_level > target_level:
        # Spec priority is lower (higher number) than epic - need to bump
        new_priority = f"P{target_level}"
        set_priority(
            spec_id,
            new_priority,
            docs_root,
            auto_update_deps=True,
            paths_config=paths_config,
            project_root=project_root,
        )
        result["priority_bumped"] = new_priority

    return result


def _get_priority_level(priority: str) -> int:
    """Extract numeric level from priority.

    Args:
        priority: Priority code (P0-P3)

    Returns:
        Numeric level (0-3, or 999 for invalid)
    """
    priority_map = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return priority_map.get(priority, 999)


def _find_dependent_specs(
    spec_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> list[tuple[str, str]]:
    """Find all specs that depend on the given spec.

    Args:
        spec_id: Spec ID to check
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        List of (dependent_spec_id, dependent_priority) tuples
    """
    from nspec.datasets import DatasetLoader

    spec_id = normalize_spec_ref(spec_id)
    loader = DatasetLoader(docs_root=docs_root)
    datasets = loader.load()

    dependents: list[tuple[str, str]] = []
    for dependent_id, fr in datasets.active_frs.items():
        if dependent_id == spec_id:
            continue
        if spec_id in (fr.deps or []):
            dependents.append((dependent_id, fr.priority))

    return dependents


def set_priority(
    spec_id: str,
    priority: str,
    docs_root: Path,
    auto_update_deps: bool = True,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Change priority for a spec's FR file with optional dependency auto-update.

    Updates the **Priority:** line in both active and completed FR files.
    Optionally updates dependencies using bidirectional inheritance.

    When DOWNGRADING priority (e.g., P1 → P2), checks if any higher-priority specs
    depend on this spec. If so, raises ValueError with list of blocking dependencies.

    Args:
        spec_id: Spec ID to update (e.g., "093")
        priority: New priority (P0-P3)
        docs_root: Path to docs/ directory
        auto_update_deps: If True, auto-update dependencies to match priority level
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Path to updated FR file

    Raises:
        FileNotFoundError: If FR not found
        ValueError: If priority is invalid or downgrade blocked by dependents
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    spec_id = normalize_spec_ref(spec_id)

    # Validate priority
    if priority.upper() not in PRIORITY_RANGES:
        raise ValueError(f"Invalid priority: {priority}. Must be P0-P3.")

    priority = priority.upper()

    # Find FR file in active or completed directories
    fr_pattern = f"FR-{spec_id}-*.md"
    active_fr_dir = paths.active_frs_dir
    completed_fr_dir = paths.completed_frs_dir

    fr_files = list(active_fr_dir.glob(fr_pattern))
    if not fr_files:
        fr_files = list(completed_fr_dir.glob(fr_pattern))

    if not fr_files:
        raise FileNotFoundError(
            f"FR-{spec_id}-*.md not found in {active_fr_dir} or {completed_fr_dir}"
        )

    fr_path = fr_files[0]

    # Read current content
    content = fr_path.read_text()

    # Extract current priority to check if this is a downgrade
    current_priority_match = re.search(
        r"^\*\*Priority:\*\*\s+[🔥🟠🟡🔵]\s+(P[0-3])",
        content,
        re.MULTILINE,
    )

    if current_priority_match:
        current_priority = current_priority_match.group(1)
        current_level = _get_priority_level(current_priority)
        new_level = _get_priority_level(priority)

        # Check if this is a downgrade (increasing level number = lower priority)
        if new_level > current_level:
            # Find specs that depend on this one
            dependents = _find_dependent_specs(spec_id, docs_root, paths_config, project_root)

            # Filter for dependents with higher priority (lower level number)
            blocking_dependents = [
                (dep_id, dep_priority)
                for dep_id, dep_priority in dependents
                if _get_priority_level(dep_priority) < new_level
            ]

            if blocking_dependents:
                # Build error message
                dep_list = ", ".join(
                    f"Spec {dep_id} ({dep_priority})"
                    for dep_id, dep_priority in blocking_dependents
                )
                raise ValueError(
                    f"Cannot downgrade Spec {spec_id} from {current_priority} to {priority}.\n"
                    f"The following higher-priority specs depend on it: {dep_list}\n"
                    f"Either:\n"
                    f"  1. Remove these dependencies first using 'make nspec.remove-dep'\n"
                    f"  2. Upgrade dependent specs to match or lower priority"
                )

    # Update priority line (handle both Spec and Epic priorities)
    emoji = _get_priority_emoji(priority)
    content = re.sub(
        r"^\*\*Priority:\*\*\s+[🔥🟠🟡🔵]\s+(P[0-3])",
        f"**Priority:** {emoji} {priority}",
        content,
        flags=re.MULTILINE,
    )

    # Write updated content
    fr_path.write_text(content)

    # Auto-update dependencies to match priority level
    if auto_update_deps:
        _auto_update_dependency_priorities(
            spec_id, priority, docs_root, content, paths_config, project_root
        )

    return fr_path


def _build_reverse_dependency_map(
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> dict[str, list[tuple[str, str]]]:
    """Build a map of spec_id -> list of (dependent_id, dependent_priority).

    For each spec, find all specs that depend on it.

    Args:
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Dict mapping spec_id to list of (dependent_id, dependent_priority) tuples
    """
    from nspec.datasets import DatasetLoader

    loader = DatasetLoader(docs_root=docs_root)
    datasets = loader.load()

    reverse_deps: dict[str, list[tuple[str, str]]] = {}
    for dependent_id, fr in datasets.active_frs.items():
        for dep_id in fr.deps or []:
            reverse_deps.setdefault(dep_id, []).append((dependent_id, fr.priority))

    return reverse_deps


def _calculate_effective_priority(
    dep_id: str,
    reverse_deps: dict[str, list[tuple[str, str]]],
    updated_priorities: dict[str, int],
) -> int:
    """Calculate the effective priority level for a dependency.

    The effective priority is the HIGHEST priority (LOWEST level number)
    among all specs that depend on this one.

    Args:
        dep_id: Dependency spec ID
        reverse_deps: Reverse dependency map from _build_reverse_dependency_map
        updated_priorities: Dict of spec_id -> new priority level for specs being updated

    Returns:
        Effective priority level (0-3), or 3 if no dependents
    """
    dependents = reverse_deps.get(dep_id, [])

    if not dependents:
        return 3  # No dependents, lowest priority

    min_level = 3  # Start with lowest priority (highest number)

    for dependent_id, dependent_priority in dependents:
        # Check if this dependent has an updated priority
        if dependent_id in updated_priorities:
            level = updated_priorities[dependent_id]
        else:
            level = _get_priority_level(dependent_priority)

        min_level = min(min_level, level)

    return min_level


def _auto_update_dependency_priorities(
    spec_id: str,
    new_priority: str,
    docs_root: Path,
    fr_content: str,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> None:
    """Auto-update dependency priorities using bidirectional inheritance.

    Implements smart priority inheritance:
    - When upgrading (P2 → P1): Dependencies are upgraded to match
    - When downgrading (P1 → P2): Dependencies are downgraded ONLY if no other
      higher-priority spec depends on them

    Formula: dep_priority = MAX(priorities of all dependents) where MAX means
    the highest priority (lowest level number).

    Uses two-pass traversal for transitive dependencies (e.g., 210→211).

    Args:
        spec_id: Spec ID that was updated
        new_priority: New priority for the spec (P0-P3)
        docs_root: Path to docs/ directory
        fr_content: (legacy) FR content; ignored (deps are resolved via datasets)
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)
    """
    from nspec.datasets import DatasetLoader

    spec_id = normalize_spec_ref(spec_id)
    loader = DatasetLoader(docs_root=docs_root)
    datasets = loader.load()

    fr = datasets.get_fr(spec_id)
    if not fr or not fr.deps:
        return

    dep_ids = [d for d in fr.deps if d in datasets.active_frs]
    if not dep_ids:
        return

    reverse_deps = _build_reverse_dependency_map(docs_root, paths_config, project_root)
    updated_priorities: dict[str, int] = {spec_id: _get_priority_level(new_priority)}

    print(f"📝 Auto-updating {len(dep_ids)} dependencies with bidirectional inheritance...")

    level_to_priority = {0: "P0", 1: "P1", 2: "P2", 3: "P3"}

    for pass_num in range(2):
        if pass_num == 1:
            print("   🔄 Pass 2: Checking transitive dependencies...")

        for dep_id in dep_ids:
            try:
                dep_fr = datasets.get_fr(dep_id)
                if not dep_fr:
                    if pass_num == 0:
                        print(f"   ⚠️  Dependency {dep_id} not found, skipping")
                    continue

                current_priority = dep_fr.priority
                current_level = _get_priority_level(current_priority)
                effective_level = _calculate_effective_priority(
                    dep_id, reverse_deps, updated_priorities
                )

                if current_level != effective_level:
                    new_dep_priority = level_to_priority.get(effective_level)
                    if not new_dep_priority:
                        if pass_num == 0:
                            msg = (
                                f"   ⚠️  Invalid effective level {effective_level}, "
                                f"skipping {dep_id}"
                            )
                            print(msg)
                        continue

                    direction = "⬆️" if effective_level < current_level else "⬇️"
                    set_priority(
                        dep_id,
                        new_dep_priority,
                        docs_root,
                        auto_update_deps=False,
                        paths_config=paths_config,
                        project_root=project_root,
                    )
                    update_msg = (
                        f"   {direction} Updated Spec {dep_id}: "
                        f"{current_priority} → {new_dep_priority}"
                    )
                    print(update_msg)
                    updated_priorities[dep_id] = effective_level
                else:
                    if pass_num == 0:
                        print(
                            f"   ⏭️  Spec {dep_id} at {current_priority} "
                            f"(effective level {effective_level}), no update needed"
                        )

            except _NspecCrudErrors as e:
                print(f"   ❌ Error updating dependency {dep_id}: {e}")


def check_acceptance_criteria(
    spec_id: str,
    criteria_id: str,
    docs_root: Path,
    marker: str = "x",
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Mark an acceptance criterion as complete or obsolete in FR file.

    Updates a checkbox from [ ] to [x] (complete) or [~] (obsolete).

    Args:
        spec_id: Spec ID (e.g., "127")
        criteria_id: Acceptance criteria ID (e.g., "AC-F1", "AC-Q2", "AC-D1")
        docs_root: Path to docs/ directory
        marker: Checkbox marker - "x" for complete, "~" for obsolete
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Path to updated FR file

    Raises:
        FileNotFoundError: If FR not found
        ValueError: If criteria ID not found or invalid marker
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    if marker not in ("x", "~"):
        raise ValueError(f"Invalid marker '{marker}'. Use 'x' (complete) or '~' (obsolete).")
    # Find FR file in active or completed directories
    fr_pattern = f"FR-{spec_id}-*.md"
    active_fr_dir = paths.active_frs_dir
    completed_fr_dir = paths.completed_frs_dir

    fr_files = list(active_fr_dir.glob(fr_pattern))
    if not fr_files:
        fr_files = list(completed_fr_dir.glob(fr_pattern))

    if not fr_files:
        raise FileNotFoundError(
            f"FR-{spec_id}-*.md not found in {active_fr_dir} or {completed_fr_dir}"
        )

    fr_path = fr_files[0]

    with _file_lock(fr_path):
        content = fr_path.read_text()

        # Find and update the specific AC line
        pattern = rf"^- \[ \](.*{re.escape(criteria_id)}:.*)"
        match = re.search(pattern, content, re.MULTILINE)

        if not match:
            raise ValueError(
                f"Acceptance criterion '{criteria_id}' not found in FR-{spec_id}. "
                f"Make sure it matches pattern: '- [ ] {criteria_id}: ...'"
            )

        # Replace [ ] with [x] or [~] for this specific line
        old_line = f"- [ ]{match.group(1)}"
        new_line = f"- [{marker}]{match.group(1)}"
        content = content.replace(old_line, new_line, 1)

        fr_path.write_text(content)
    return fr_path


def check_impl_task(
    spec_id: str,
    task_id: str,
    docs_root: Path,
    marker: str = "x",
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Mark an IMPL task as complete or obsolete.

    Updates a checkbox from [ ] to [x] (complete) or [~] (obsolete).

    Args:
        spec_id: Spec ID (e.g., "127")
        task_id: Task number to match (e.g., "1.1", "2.3")
        docs_root: Path to docs/ directory
        marker: Checkbox marker - "x" for complete, "~" for obsolete
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Path to updated IMPL file

    Raises:
        FileNotFoundError: If IMPL not found
        ValueError: If task ID not found or matches multiple tasks
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    if marker not in ("x", "~"):
        raise ValueError(f"Invalid marker '{marker}'. Use 'x' (complete) or '~' (obsolete).")

    # Find IMPL file in active or completed directories
    impl_pattern = f"IMPL-{spec_id}-*.md"
    active_impl_dir = paths.active_impls_dir
    completed_impl_dir = paths.completed_impls_dir

    impl_files = list(active_impl_dir.glob(impl_pattern))
    if not impl_files:
        impl_files = list(completed_impl_dir.glob(impl_pattern))

    if not impl_files:
        raise FileNotFoundError(
            f"IMPL-{spec_id}-*.md not found in {active_impl_dir} or {completed_impl_dir}"
        )

    impl_path = impl_files[0]

    with _file_lock(impl_path):
        content = impl_path.read_text()
        lines = content.split("\n")
        matching_lines = []

        # Handle Definition of Done items (format: "dod-1", "dod-2", etc.)
        if task_id.lower().startswith("dod-"):
            dod_num_str = task_id[4:]  # Extract number after "dod-"
            if not dod_num_str.isdigit():
                raise ValueError(
                    f"Invalid DoD task ID '{task_id}'. Use format 'dod-1', 'dod-2', etc."
                )
            dod_num = int(dod_num_str)

            # Find Definition of Done section - count ALL checkboxes by position
            in_dod_section = False
            dod_checkboxes = []  # (line_idx, line, is_unchecked)
            for i, line in enumerate(lines):
                if line.strip().startswith("## Definition of Done"):
                    in_dod_section = True
                    continue
                if in_dod_section and line.strip().startswith("## "):
                    break  # Next section
                if in_dod_section and line.startswith("- ["):
                    is_unchecked = line.startswith("- [ ]")
                    dod_checkboxes.append((i, line, is_unchecked))

            if not dod_checkboxes:
                raise ValueError(f"No Definition of Done items found in IMPL-{spec_id}.")
            if dod_num < 1 or dod_num > len(dod_checkboxes):
                raise ValueError(
                    f"DoD item {dod_num} not found. IMPL-{spec_id} has "
                    f"{len(dod_checkboxes)} DoD items (use dod-1 to dod-{len(dod_checkboxes)})."
                )

            line_idx, line, is_unchecked = dod_checkboxes[dod_num - 1]
            if not is_unchecked:
                raise ValueError(f"DoD item dod-{dod_num} is already checked in IMPL-{spec_id}.")
            matching_lines = [(line_idx, line)]
        else:
            # Find unchecked task matching task ID
            # Supports both "**1**: desc" and "1. desc" formats
            for i, line in enumerate(lines):
                if line.startswith("- [ ]") and _line_matches_task_id(line, task_id):
                    matching_lines.append((i, line))

            if not matching_lines:
                raise ValueError(
                    f"Task '{task_id}' not found in IMPL-{spec_id}. "
                    f"Make sure it exists and is not already checked."
                )

            if len(matching_lines) > 1:
                match_count = len(matching_lines)
                raise ValueError(
                    f"Task ID '{task_id}' matches {match_count} tasks "
                    f"in IMPL-{spec_id}. This shouldn't happen - check for duplicates:\n"
                    + "\n".join(f"  {i + 1}. {line}" for i, line in matching_lines)
                )

        # Replace [ ] with [x] or [~] for the matching line
        line_idx, old_line = matching_lines[0]
        new_line = old_line.replace("- [ ]", f"- [{marker}]", 1)
        lines[line_idx] = new_line
        content = "\n".join(lines)

        impl_path.write_text(content)
    return impl_path


def _get_priority_emoji(priority: str) -> str:
    """Get emoji for priority level.

    Args:
        priority: Priority code (P0-P3)

    Returns:
        Emoji for the priority

    Raises:
        ValueError: If priority is not recognized (invalid priority code)
    """
    from nspec.statuses import ALL_PRIORITIES

    if priority not in ALL_PRIORITIES:
        raise ValueError(
            f"Invalid priority '{priority}'. Must be one of: {', '.join(ALL_PRIORITIES.keys())}"
        )

    return ALL_PRIORITIES[priority].emoji


def calculate_epic_loe(
    spec_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[int, int]:
    """Calculate Epic LOE from active dependencies.

    Args:
        spec_id: Epic spec ID (e.g., "093")
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        (parallel_hours, sequential_hours)
        parallel = max of all dep parallel LOEs
        sequential = sum of all dep sequential LOEs

    Note:
        Completed dependencies are skipped (don't add to remaining work).
    """
    from nspec.datasets import DatasetLoader

    spec_id = normalize_spec_ref(spec_id)
    loader = DatasetLoader(docs_root=docs_root)
    datasets = loader.load()

    epic_fr = datasets.get_fr(spec_id)
    if not epic_fr or epic_fr.type != "Epic" or not epic_fr.deps:
        return (0, 0)

    dep_hours: list[int] = []
    for dep_id in epic_fr.deps:
        # Skip completed dependencies (they don't add to remaining work)
        if dep_id in datasets.completed_impls:
            continue
        dep_impl = datasets.active_impls.get(dep_id)
        if not dep_impl:
            continue
        dep_hours.append(dep_impl.effective_loe_hours)

    if not dep_hours:
        return (0, 0)

    return (max(dep_hours), sum(dep_hours))


def _parse_loe_to_hours(loe_str: str) -> tuple[int, int]:
    """Parse LOE string to hours (parallel, sequential).

    Formats:
        - "~5d" → (0, 40h)  # Sequential only
        - "~3w,~10d" → (120h, 80h)  # Parallel, sequential

    Args:
        loe_str: LOE string (e.g., "~5d", "~3w,~10d")

    Returns:
        (parallel_hours, sequential_hours)
    """
    # Check if format is "~XXh,~YYd" (parallel, sequential)
    if "," in loe_str:
        parts = loe_str.split(",")
        parallel_str = parts[0].strip()
        sequential_str = parts[1].strip()

        parallel_hours = _loe_component_to_hours(parallel_str)
        sequential_hours = _loe_component_to_hours(sequential_str)

        return (parallel_hours, sequential_hours)
    else:
        # Single value = sequential only
        sequential_hours = _loe_component_to_hours(loe_str)
        return (0, sequential_hours)


def _loe_component_to_hours(component: str) -> int:
    """Convert LOE component to hours.

    Args:
        component: LOE component (e.g., "~5d", "~3w", "~40h", "~1.5d")

    Returns:
        Hours as integer (rounded from float if needed)
    """
    component = component.strip().replace("~", "")

    if component.endswith("h"):
        return int(float(component[:-1]))
    elif component.endswith("d"):
        return int(float(component[:-1]) * 8)  # 1 day = 8 hours
    elif component.endswith("w"):
        return int(float(component[:-1]) * 40)  # 1 week = 40 hours
    else:
        return 0


def _format_hours_to_loe(hours: int) -> str:
    """Format hours to LOE string with smart unit selection.

    Rules:
    - < 24h (3 days): use hours (e.g., "20h")
    - >= 24h and < 56h (7 days): use days with decimal (e.g., "3.5d")
    - >= 56h: use weeks with decimal (e.g., "1.4w")

    Args:
        hours: Hours as integer

    Returns:
        LOE string (e.g., "20h", "3.5d", "1.4w")
    """
    if hours == 0:
        return "0h"
    elif hours < 24:
        # Under 3 days: use hours
        return f"{hours}h"
    elif hours < 56:
        # 3 days to 7 days: use days with decimal
        days = hours / 8
        if days == int(days):
            return f"{int(days)}d"
        else:
            return f"{days:.1f}d"
    else:
        # 7 days and over: use weeks with decimal
        weeks = hours / 40
        if weeks == int(weeks):
            return f"{int(weeks)}w"
        else:
            return f"{weeks:.1f}w"


def update_epic_loe(
    spec_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path | None:
    """Update Epic FR and IMPL LOE based on dependencies.

    Only updates if spec is an Epic (Type: Epic).
    Updates both:
    - FR: **LOE Remaining:** field (uses parallel estimate)
    - IMPL: **LOE:** field (uses parallel,sequential format)

    Args:
        spec_id: Spec ID to update (e.g., "093")
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Path to updated IMPL file, or None if not an Epic

    Raises:
        FileNotFoundError: If FR or IMPL not found
    """
    from nspec.datasets import DatasetLoader

    spec_id = normalize_spec_ref(spec_id)
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    loader = DatasetLoader(docs_root=docs_root)
    datasets = loader.load()
    fr_meta = datasets.get_fr(spec_id)
    if not fr_meta or fr_meta.type != "Epic":
        return None

    fr_pattern = f"FR-{spec_id}-*.md"
    fr_files = list(paths.active_frs_dir.glob(fr_pattern))
    if not fr_files:
        raise FileNotFoundError(f"FR-{spec_id}-*.md not found in {paths.active_frs_dir}")

    fr_path = fr_files[0]
    fr_content = fr_path.read_text()

    # Calculate LOE from dependencies
    parallel_hours, sequential_hours = calculate_epic_loe(
        spec_id, docs_root, paths_config, project_root
    )

    # Load IMPL file
    impl_pattern = f"IMPL-{spec_id}-*.md"
    impl_dir = paths.active_impls_dir
    impl_files = list(impl_dir.glob(impl_pattern))

    if not impl_files:
        raise FileNotFoundError(f"IMPL-{spec_id}-*.md not found in {impl_dir}")

    impl_path = impl_files[0]
    impl_content = impl_path.read_text()

    # Format LOE string for Epics (always show parallel, sequential)
    if parallel_hours == 0 and sequential_hours == 0:
        loe_str = "TBD"
        fr_loe_str = "TBD"
    else:
        # Epics always show both parallel and sequential
        # Parallel = longest dependency (if all done in parallel)
        # Sequential = sum of all dependencies (if all done sequentially)
        parallel_str = _format_hours_to_loe(parallel_hours)
        sequential_str = _format_hours_to_loe(sequential_hours)
        loe_str = f"{parallel_str},{sequential_str}"
        # FR shows just the parallel estimate (best case with parallelization)
        fr_loe_str = f"~{parallel_str}"

    # Update IMPL **LOE:** line
    impl_content = re.sub(
        r"^\*\*LOE:\*\*\s+.+$", f"**LOE:** {loe_str}", impl_content, flags=re.MULTILINE
    )

    # Update FR **LOE Remaining:** line (if it exists)
    if re.search(r"^\*\*LOE Remaining:\*\*", fr_content, re.MULTILINE):
        fr_content = re.sub(
            r"^\*\*LOE Remaining:\*\*\s+.+$",
            f"**LOE Remaining:** {fr_loe_str}",
            fr_content,
            flags=re.MULTILINE,
        )
        # Write updated FR
        fr_path.write_text(fr_content)

    # Write updated IMPL
    impl_path.write_text(impl_content)

    return impl_path


# LOE format validation regex (matches validators.py but simpler for single values)
_LOE_FORMAT_RE = re.compile(r"^(\d+(?:\.\d+)?)(h|d|w)$|^N/A$", re.IGNORECASE)


def set_loe(
    spec_id: str,
    loe: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Set LOE for a spec's IMPL file with format validation.

    Validates LOE format before writing to prevent invalid values.

    Args:
        spec_id: Spec ID to update (e.g., "280")
        loe: New LOE value (e.g., "14d", "3w", "20h", "N/A")
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Path to updated IMPL file

    Raises:
        FileNotFoundError: If IMPL not found
        ValueError: If LOE format is invalid

    Examples:
        Valid: "5d", "3w", "20h", "2.5d", "N/A"
        Invalid: "~5d", "14d (aggregate)", "TBD", "5 days"
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    # Validate LOE format
    loe = loe.strip()
    if not _LOE_FORMAT_RE.match(loe):
        raise ValueError(
            f"❌ Invalid LOE format: '{loe}'\n"
            f"   Required format: <number><unit> or N/A\n"
            f"   Valid units: h (hours), d (days), w (weeks)\n"
            f"   Examples: 5d, 3w, 20h, 2.5d, N/A\n"
            f"   Invalid: ~5d, 14d (notes), TBD, 5 days"
        )

    # Normalize case for N/A
    if loe.upper() == "N/A":
        loe = "N/A"

    # Find IMPL file in active or completed directories
    impl_pattern = f"IMPL-{spec_id}-*.md"
    active_impl_dir = paths.active_impls_dir
    completed_impl_dir = paths.completed_impls_dir

    impl_files = list(active_impl_dir.glob(impl_pattern))
    if not impl_files:
        impl_files = list(completed_impl_dir.glob(impl_pattern))

    if not impl_files:
        raise FileNotFoundError(
            f"IMPL-{spec_id}-*.md not found in {active_impl_dir} or {completed_impl_dir}"
        )

    impl_path = impl_files[0]

    # Read current content
    content = impl_path.read_text()

    # Update LOE line
    new_content = re.sub(
        r"^\*\*LOE:\*\*\s+.+$",
        f"**LOE:** {loe}",
        content,
        flags=re.MULTILINE,
    )

    if new_content == content:
        # LOE line not found - this shouldn't happen for valid IMPL files
        raise ValueError(f"❌ No **LOE:** line found in {impl_path.name}")

    # Write updated content
    impl_path.write_text(new_content)

    return impl_path


def _get_current_status(
    content: str, *, kind: Literal["FR", "IMPL", "ANY"] = "ANY"
) -> tuple[int, str, str] | None:
    """Extract current status from file content.

    Args:
        content: File content to parse

    Returns:
        Tuple of (status_code, emoji, text) or None if not found
    """
    # Build reverse lookup from centralized statuses (support both current + legacy emoji)
    fr_map: dict[str, tuple[int, str, str]] = {
        s.full: (s.code, s.emoji, s.text) for s in FR_STATUSES.values()
    }
    # Legacy emoji variants
    fr_map["🟢 Active"] = (2, "🟢", "Active")

    impl_map: dict[str, tuple[int, str, str]] = {
        s.full: (s.code, s.emoji, s.text) for s in IMPL_STATUSES.values()
    }
    # Legacy emoji variants
    impl_map["📋 Planning"] = (0, "📋", "Planning")
    impl_map["🚧 Active"] = (1, "🚧", "Active")
    impl_map["✅ Completed"] = (3, "✅", "Completed")  # legacy alias for Ready
    impl_map["⏸️ Paused"] = (4, "⏸️", "Paused")  # legacy pause button emoji
    if kind == "FR":
        status_map = fr_map
    elif kind == "IMPL":
        status_map = impl_map
    else:
        status_map = {**fr_map, **impl_map}

    match = re.search(r"^\*\*Status:\*\*\s+(.+)$", content, re.MULTILINE)
    if match:
        status_str = match.group(1).strip()
        return status_map.get(status_str)
    return None


def _validate_transition(
    current_fr: int,
    current_impl: int,
    new_fr: int,
    new_impl: int,
    fr_statuses: dict,
    impl_statuses: dict,
) -> tuple[bool, str]:
    """Validate state transition is logically valid.

    Args:
        current_fr: Current FR status code
        current_impl: Current IMPL status code
        new_fr: New FR status code
        new_impl: New IMPL status code
        fr_statuses: FR status mapping
        impl_statuses: IMPL status mapping

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Terminal FR states (can't transition from these)
    terminal_fr = {3, 4, 5}  # Completed, Rejected, Superseded
    # Terminal IMPL states
    terminal_impl = {3}  # Ready (for archival)

    # Rule 1: Can't revert from terminal FR states
    if current_fr in terminal_fr and new_fr != current_fr:
        curr_emoji, curr_text = fr_statuses[current_fr]
        return (
            False,
            f"Cannot change FR from terminal state {curr_emoji} {curr_text} ({current_fr})",
        )

    # Rule 2: Can't revert from terminal IMPL states
    if current_impl in terminal_impl and new_impl != current_impl:
        curr_emoji, curr_text = impl_statuses[current_impl]
        return (
            False,
            f"Cannot change IMPL from terminal state {curr_emoji} {curr_text} ({current_impl})",
        )

    # Rule 3: IMPL can't start until FR spec is finalized (Active)
    # FR must be Active (2) before IMPL can be Active (1) or beyond
    # Rationale: The FR defines WHAT to build - it must be complete before implementation
    if new_impl >= 1 and new_fr < 2:
        return (
            False,
            "Cannot start IMPL until FR is Active (2) - finalize the spec first",
        )

    # Rule 4: Can't mark IMPL Ready without completing FR
    if new_impl == 3 and new_fr != 3:
        return (
            False,
            "Cannot mark IMPL as Ready (3) unless FR is also Completed (3)",
        )

    # Rule 5: If completing FR, IMPL should also be ready
    if new_fr == 3 and new_impl != 3:
        return (
            False,
            "Cannot mark FR as Completed (3) unless IMPL is also Ready (3)",
        )

    return (True, "")


def set_status(
    spec_id: str,
    fr_status: int,
    impl_status: int,
    docs_root: Path,
    *,
    force: bool = False,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[Path, Path]:
    """Set status for both FR and IMPL files atomically.

    Status codes:
      FR: 0=Proposed, 1=In Design, 2=Active, 3=Completed, 4=Rejected, 5=Superseded, 6=Deferred
      IMPL: 0=Planning, 1=Active, 2=Testing, 3=Ready, 4=Paused, 5=Hold

    Args:
        spec_id: Spec ID to update (e.g., "128")
        fr_status: FR status code (0-6)
        impl_status: IMPL status code (0-5)
        docs_root: Path to docs/ directory
        force: If True, skip transition validation (for recovery from bad states)
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Tuple of (FR path, IMPL path)

    Raises:
        FileNotFoundError: If FR or IMPL not found
        ValueError: If status codes are invalid or transition is illogical (unless force=True)
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    # Build status mappings from centralized statuses module
    fr_statuses = {code: (s.emoji, s.text) for code, s in FR_STATUSES.items()}
    impl_statuses = {code: (s.emoji, s.text) for code, s in IMPL_STATUSES.items()}

    # Validate status codes
    if fr_status not in fr_statuses:
        raise ValueError(f"Invalid FR status code: {fr_status}. Must be 0-6.")
    if impl_status not in impl_statuses:
        raise ValueError(f"Invalid IMPL status code: {impl_status}. Must be 0-5.")

    # Find FR file
    fr_pattern = f"FR-{spec_id}-*.md"
    active_fr_dir = paths.active_frs_dir
    completed_fr_dir = paths.completed_frs_dir

    fr_files = list(active_fr_dir.glob(fr_pattern))
    if not fr_files:
        fr_files = list(completed_fr_dir.glob(fr_pattern))

    if not fr_files:
        raise FileNotFoundError(
            f"FR-{spec_id}-*.md not found in {active_fr_dir} or {completed_fr_dir}"
        )

    fr_path = fr_files[0]

    # Find IMPL file
    impl_pattern = f"IMPL-{spec_id}-*.md"
    active_impl_dir = paths.active_impls_dir
    completed_impl_dir = paths.completed_impls_dir

    impl_files = list(active_impl_dir.glob(impl_pattern))
    if not impl_files:
        impl_files = list(completed_impl_dir.glob(impl_pattern))

    if not impl_files:
        raise FileNotFoundError(
            f"IMPL-{spec_id}-*.md not found in {active_impl_dir} or {completed_impl_dir}"
        )

    impl_path = impl_files[0]

    # Lock both files to prevent concurrent read-modify-write races
    # (e.g., task_complete and activate called in parallel)
    with _file_lock(fr_path), _file_lock(impl_path):
        # Read current content to extract current statuses
        fr_content = fr_path.read_text()
        impl_content = impl_path.read_text()

        # Extract current statuses
        current_fr_tuple = _get_current_status(fr_content, kind="FR")
        current_impl_tuple = _get_current_status(impl_content, kind="IMPL")

        if current_fr_tuple is None:
            raise ValueError(f"Could not parse current FR status from {fr_path.name}")
        if current_impl_tuple is None:
            raise ValueError(f"Could not parse current IMPL status from {impl_path.name}")

        current_fr, current_fr_emoji, current_fr_text = current_fr_tuple
        current_impl, current_impl_emoji, current_impl_text = current_impl_tuple

        # Validate transition is logically valid (unless force is set)
        if not force:
            is_valid, error_msg = _validate_transition(
                current_fr, current_impl, fr_status, impl_status, fr_statuses, impl_statuses
            )
            if not is_valid:
                # Show current state for context
                print("\n❌ Invalid state transition:")
                print(
                    f"   Current: FR = {current_fr_emoji} {current_fr_text} ({current_fr})  |  "
                    f"IMPL = {current_impl_emoji} {current_impl_text} ({current_impl})"
                )
                new_fr_emoji, new_fr_text = fr_statuses[fr_status]
                new_impl_emoji, new_impl_text = impl_statuses[impl_status]
                print(
                    f"   Requested: FR = {new_fr_emoji} {new_fr_text} ({fr_status})  |  "
                    f"IMPL = {new_impl_emoji} {new_impl_text} ({impl_status})"
                )
                print(f"\n   Reason: {error_msg}\n")
                raise ValueError(error_msg)
        else:
            print("\n⚠️  Force mode: Skipping transition validation")

        # Show BEFORE state
        print(f"\n📊 Setting Spec {spec_id} statuses...")
        print(
            f"   BEFORE: FR = {current_fr_emoji} {current_fr_text} ({current_fr})  |  "
            f"IMPL = {current_impl_emoji} {current_impl_text} ({current_impl})"
        )

        # Update FR status
        fr_emoji, fr_text = fr_statuses[fr_status]
        fr_content = re.sub(
            r"^\*\*Status:\*\*.*$",
            f"**Status:** {fr_emoji} {fr_text}",
            fr_content,
            flags=re.MULTILINE,
        )
        fr_path.write_text(fr_content)

        # Update IMPL status
        impl_emoji, impl_text = impl_statuses[impl_status]
        # Match any emoji + text until end of line (handles template files with FR statuses)
        impl_content = re.sub(
            r"^\*\*Status:\*\*.*$",
            f"**Status:** {impl_emoji} {impl_text}",
            impl_content,
            flags=re.MULTILINE,
        )
        impl_path.write_text(impl_content)

    # Show AFTER state
    print(
        f"   AFTER:  FR = {fr_emoji} {fr_text} ({fr_status})  |  "
        f"IMPL = {impl_emoji} {impl_text} ({impl_status})"
    )
    print("\n   ✅ Files updated:")
    print(f"      • {fr_path.name}")
    print(f"      • {impl_path.name}\n")

    # Update state.json when activating (FR=2 Active, IMPL=1 Active)
    if fr_status == 2 and impl_status == 1:
        from nspec.session import StateDAO

        root = project_root if project_root else docs_root.parent
        dao = StateDAO(root)
        dao.set_spec_id(spec_id)
        print(f"   📝 Updated session tracker: {dao.state_path.name}\n")

    return fr_path, impl_path


def next_status(
    spec_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[Path, Path]:
    """Auto-advance IMPL status to next logical state.

    Automatically progresses IMPL through: Planning → Active → Testing → Ready
    Also auto-upgrades FR when needed (e.g., FR becomes Active when IMPL becomes Active)

    Args:
        spec_id: Spec ID to advance (e.g., "128")
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Tuple of (FR path, IMPL path)

    Raises:
        FileNotFoundError: If FR or IMPL not found
        ValueError: If already at terminal state or transition invalid
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)

    # Find files
    fr_pattern = f"FR-{spec_id}-*.md"
    impl_pattern = f"IMPL-{spec_id}-*.md"

    active_fr_dir = paths.active_frs_dir
    completed_fr_dir = paths.completed_frs_dir
    fr_files = list(active_fr_dir.glob(fr_pattern))
    if not fr_files:
        fr_files = list(completed_fr_dir.glob(fr_pattern))
    if not fr_files:
        raise FileNotFoundError(
            f"FR-{spec_id}-*.md not found in {active_fr_dir} or {completed_fr_dir}"
        )
    fr_path = fr_files[0]

    active_impl_dir = paths.active_impls_dir
    completed_impl_dir = paths.completed_impls_dir
    impl_files = list(active_impl_dir.glob(impl_pattern))
    if not impl_files:
        impl_files = list(completed_impl_dir.glob(impl_pattern))
    if not impl_files:
        raise FileNotFoundError(
            f"IMPL-{spec_id}-*.md not found in {active_impl_dir} or {completed_impl_dir}"
        )
    impl_path = impl_files[0]

    # Read current statuses
    fr_content = fr_path.read_text()
    impl_content = impl_path.read_text()

    current_fr_tuple = _get_current_status(fr_content, kind="FR")
    current_impl_tuple = _get_current_status(impl_content, kind="IMPL")

    if current_fr_tuple is None:
        raise ValueError(f"Could not parse current FR status from {fr_path.name}")
    if current_impl_tuple is None:
        raise ValueError(f"Could not parse current IMPL status from {impl_path.name}")

    current_fr, current_fr_emoji, current_fr_text = current_fr_tuple
    current_impl, current_impl_emoji, current_impl_text = current_impl_tuple

    # Define IMPL progression path
    impl_progression = {
        0: 1,  # Planning → Active
        1: 2,  # Active → Testing
        2: 3,  # Testing → Ready
        # 3: terminal (Ready for archival)
        # 4: Paused (no auto-progression)
    }

    if current_impl not in impl_progression:
        if current_impl == 3:
            print(
                f"\n✅ Spec {spec_id} IMPL already at terminal state: "
                f"{current_impl_emoji} {current_impl_text}\n"
            )
            raise ValueError(f"IMPL already Ready ({current_impl}) - use nspec_complete to archive")
        elif current_impl == 4:
            print(
                f"\n⏸️  Spec {spec_id} IMPL is Paused - cannot auto-advance\n"
                f"   Use: make nspec.reset {spec_id} to reset, then activate\n"
            )
            raise ValueError(f"IMPL is Paused ({current_impl}) - cannot auto-advance")

    next_impl = impl_progression[current_impl]

    # Auto-upgrade FR if needed
    # When IMPL goes Active (1+), FR must be Active (2) - spec must be finalized first
    # When IMPL goes Ready (3), FR must also be Completed (3)
    next_fr = current_fr
    if next_impl >= 1 and current_fr < 2:  # IMPL starting but FR spec not finalized
        next_fr = 2  # Upgrade FR to "Active" (spec finalized)
        msg = (
            f"\n🔄 Auto-upgrading FR: {current_fr_emoji} {current_fr_text} "
            f"→ 🟢 Active (spec finalized)"
        )
        print(msg)
    if next_impl == 3:  # IMPL ready, FR must also be completed
        next_fr = 3
        msg = f"\n🔄 Auto-upgrading FR: {current_fr_emoji} {current_fr_text} → ✅ Completed"
        print(msg)

    # Use set_status to apply the change (includes validation and feedback)
    return set_status(
        spec_id,
        next_fr,
        next_impl,
        docs_root,
        paths_config=paths_config,
        project_root=project_root,
    )


def validate_spec_criteria(
    spec_id: str,
    docs_root: Path,
    strict: bool = False,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[bool, list[str]]:
    """Validate acceptance criteria for a spec (policy-as-code).

    Checks:
    1. FR file has acceptance criteria defined
    2. Criteria follow AC-[FQP]N naming convention
    3. Optionally checks if criteria are marked complete (strict mode)

    Args:
        spec_id: Spec ID to validate (e.g., "127")
        docs_root: Path to docs/ directory
        strict: If True, require all criteria to be checked
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Tuple of (is_valid, list[violation_messages])

    Example output:
        (False, [
            "❌ No acceptance criteria defined in FR-127",
            "⚠️  AC-F1 not checked",
            "⚠️  AC-Q2 not checked"
        ])
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)
    violations = []

    # Find FR file
    fr_pattern = f"FR-{spec_id}-*.md"
    active_fr_dir = paths.active_frs_dir
    completed_fr_dir = paths.completed_frs_dir

    fr_files = list(active_fr_dir.glob(fr_pattern))
    if not fr_files:
        fr_files = list(completed_fr_dir.glob(fr_pattern))

    if not fr_files:
        violations.append(f"❌ FR-{spec_id}-*.md not found")
        return False, violations

    fr_path = fr_files[0]
    fr_content = fr_path.read_text()

    # Check for acceptance criteria section
    if "## Success Criteria" not in fr_content and "## Acceptance Criteria" not in fr_content:
        violations.append(
            f"⚠️  No 'Success Criteria' or 'Acceptance Criteria' section in FR-{spec_id}"
        )

    # Find all acceptance criteria
    ac_pattern = r"^- \[(.)\]\s+(AC-[FQPD]\d+):"
    matches = list(re.finditer(ac_pattern, fr_content, re.MULTILINE))

    if not matches:
        violations.append(
            f"❌ No acceptance criteria found in FR-{spec_id} "
            f"(expected AC-F*, AC-Q*, AC-P*, AC-D* format)"
        )
        return False, violations

    # Check criteria naming convention
    for match in matches:
        checkbox_state = match.group(1)
        criteria_id = match.group(2)

        # Validate naming convention (AC-[FQPD]N where F=functional, Q=quality,
        # P=performance, D=documentation)
        if not re.match(r"AC-[FQPD]\d+$", criteria_id):
            violations.append(f"⚠️  Invalid criteria ID format: {criteria_id}")

        # In strict mode, check if criteria are marked complete
        if strict and checkbox_state.lower() != "x":
            violations.append(f"⚠️  {criteria_id} not checked")

    # Summary stats
    total_criteria = len(matches)
    checked_criteria = sum(1 for m in matches if m.group(1).lower() == "x")
    completion_pct = (checked_criteria / total_criteria * 100) if total_criteria > 0 else 0

    if strict and checked_criteria < total_criteria:
        violations.insert(
            0,
            f"❌ Only {checked_criteria}/{total_criteria} criteria checked "
            f"({completion_pct:.0f}% complete)",
        )

    is_valid = len(violations) == 0
    return is_valid, violations


def auto_assign_ungrouped_to_epic(
    default_epic: str,
    docs_root: Path,
) -> list[tuple[str, str]]:
    """Find ungrouped specs and add them to the default epic.

    A spec is "ungrouped" if it's not a dependency of any epic.
    This function adds all ungrouped non-epic specs to the specified
    default epic's deps list.

    Args:
        default_epic: Epic ID to assign ungrouped specs to (e.g., "215")
        docs_root: Path to docs/ directory

    Returns:
        List of (spec_id, epic_id) tuples that were added

    Raises:
        FileNotFoundError: If default epic FR not found
    """
    from nspec.datasets import DatasetLoader

    loader = DatasetLoader(docs_root)
    datasets = loader.load()

    default_epic = normalize_spec_ref(default_epic)
    epic_fr = datasets.active_frs.get(default_epic)
    if not epic_fr:
        raise FileNotFoundError(f"Epic FR-{default_epic} not found in active nspec")

    if epic_fr.type != "Epic":
        raise ValueError(f"Spec {default_epic} is not an epic (type: {epic_fr.type})")

    epics = {sid for sid, fr in datasets.active_frs.items() if fr.type == "Epic"}

    specs_under_epics: set[str] = set()
    for epic_id in epics:
        epic = datasets.active_frs[epic_id]
        for dep_id in epic.deps:
            specs_under_epics.add(dep_id)

    ungrouped_specs = []
    for spec_id, fr in datasets.active_frs.items():
        if fr.type == "Epic":
            continue
        if "superseded" in fr.status.lower():
            continue
        if spec_id not in specs_under_epics:
            ungrouped_specs.append(spec_id)

    if not ungrouped_specs:
        return []

    assigned = []
    for spec_id in ungrouped_specs:
        try:
            add_dependency(default_epic, spec_id, docs_root)
            assigned.append((spec_id, default_epic))
        except ValueError:
            continue  # Spec already assigned to an epic

    return assigned


# ============================================================================
# ADR (Architecture Decision Record) Management
# ============================================================================


def get_next_adr_id(docs_root: Path) -> str:
    """Get the next available ADR ID in the 900-999 range.

    Args:
        docs_root: Path to docs/ directory

    Returns:
        Next available ADR ID (e.g., "901", "902")

    Raises:
        ValueError: If ADR range is exhausted (900-999)
    """
    adr_dir = docs_root / "03-architecture"
    if not adr_dir.exists():
        return "901"

    # Find all existing ADR files
    used_ids = set()
    for f in adr_dir.glob("ADR-*.md"):
        # Extract ID from filename like ADR-245-title.md or ADR-901-title.md
        match = re.match(r"ADR-(\d+)", f.stem)
        if match:
            used_ids.add(int(match.group(1)))

    # Find next available in 900-999 range
    for next_id in range(901, 1000):
        if next_id not in used_ids:
            return f"{next_id}"

    raise ValueError("ADR range exhausted (900-999)")


def create_adr(title: str, docs_root: Path) -> tuple[str, Path]:
    """Create a new ADR in the docs/03-architecture directory.

    ADRs are stored as ADR-XXX-title.md files (not as FR/IMPL pairs).

    Args:
        title: Title for the ADR
        docs_root: Path to docs/ directory

    Returns:
        (adr_id, adr_path) - The assigned ID and path to created file

    Raises:
        ValueError: If ADR range is exhausted
        FileNotFoundError: If ADR template doesn't exist
    """
    from datetime import datetime

    adr_dir = docs_root / "03-architecture"
    template_path = adr_dir / "ADR-TEMPLATE.md"

    if not template_path.exists():
        raise FileNotFoundError(f"ADR template not found: {template_path}")

    # Get next ADR ID
    adr_id = get_next_adr_id(docs_root)

    # Generate filename
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)  # Remove special chars
    slug = re.sub(r"[-\s]+", "-", slug)  # Convert spaces to dashes
    slug = slug.strip("-")

    filename = f"ADR-{adr_id}-{slug}.md"
    adr_path = adr_dir / filename

    # Load and populate template
    template = template_path.read_text()
    current_date = datetime.now().strftime("%Y-%m-%d")

    content = template.replace("ADR-XXX:", f"ADR-{adr_id}:")
    content = content.replace("[Decision Title]", title)
    content = content.replace("YYYY-MM-DD", current_date)

    # Write the file
    adr_path.write_text(content)

    return adr_id, adr_path


def list_adrs(docs_root: Path) -> list[tuple[str, str, str, Path]]:
    """List all ADRs with their status.

    Args:
        docs_root: Path to docs/ directory

    Returns:
        List of (adr_id, status, title, path) tuples, sorted by ID
    """
    adr_dir = docs_root / "03-architecture"
    if not adr_dir.exists():
        return []

    adrs = []
    for f in adr_dir.glob("ADR-*.md"):
        # Skip template
        if f.stem.upper() == "TEMPLATE":
            continue

        # Extract ID from filename
        match = re.match(r"ADR-(\d+)", f.stem)
        if not match:
            continue

        adr_id = match.group(1)

        # Read file to get status and title
        content = f.read_text()

        # Extract status - look for **Status:** DRAFT/PROPOSED/ACCEPTED/etc
        status_match = re.search(r"\*\*Status:\*\*\s+(\w+)", content)
        status = status_match.group(1) if status_match else "UNKNOWN"

        # Extract title from first heading after ADR-XXX:
        title_match = re.search(r"^#\s+ADR-\d+:\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f.stem

        adrs.append((adr_id, status, title, f))

    # Sort by ID
    adrs.sort(key=lambda x: int(x[0]))

    return adrs


# =============================================================================
# Review Workflow Functions
# =============================================================================


def _get_impl_field(impl_content: str, field_name: str) -> str | None:
    """Extract a field value from IMPL content.

    Args:
        impl_content: IMPL file content
        field_name: Field name without ** markers (e.g., "Implementer")

    Returns:
        Field value or None if not found/empty
    """
    pattern = rf"^\*\*{field_name}:\*\*\s*(.+)$"
    match = re.search(pattern, impl_content, re.MULTILINE)
    if match:
        value = match.group(1).strip()
        if value and value != "—":
            return value
    return None


def _set_impl_field(impl_content: str, field_name: str, value: str) -> str:
    """Set a field value in IMPL content.

    If field doesn't exist, adds it after the header block.

    Args:
        impl_content: IMPL file content
        field_name: Field name without ** markers (e.g., "Implementer")
        value: New value to set

    Returns:
        Updated content
    """
    pattern = rf"^\*\*{field_name}:\*\*.*$"
    replacement = f"**{field_name}:** {value}"

    # Check if field exists
    if re.search(pattern, impl_content, re.MULTILINE):
        return re.sub(pattern, replacement, impl_content, flags=re.MULTILINE)

    # Field doesn't exist - add it after the last ** field in the header
    # Find the last **Field:** line before the first ---
    lines = impl_content.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            break
        if line.startswith("**") and ":**" in line:
            insert_idx = i

    if insert_idx is not None:
        lines.insert(insert_idx + 1, replacement)
        return "\n".join(lines)

    # Fallback: just prepend warning (shouldn't happen with valid IMPL)
    print(f"⚠️  Could not find header block to add **{field_name}:** field")
    return impl_content


def _get_review_verdict(impl_content: str) -> str | None:
    """Extract review verdict from IMPL content.

    Returns:
        "PENDING", "APPROVED", "NEEDS_WORK", or None
    """
    pattern = r"^\*\*Verdict:\*\*\s*(\w+)"
    match = re.search(pattern, impl_content, re.MULTILINE)
    if match:
        return match.group(1).upper()
    return None


def _set_review_verdict(impl_content: str, verdict: str) -> str:
    """Set review verdict in IMPL content.

    If **Verdict:** line doesn't exist, inserts the Review section.
    """
    pattern = r"^\*\*Verdict:\*\*.*$"
    replacement = f"**Verdict:** {verdict}"

    # Check if Verdict line exists
    if re.search(pattern, impl_content, re.MULTILINE):
        return re.sub(pattern, replacement, impl_content, flags=re.MULTILINE)

    # Verdict line doesn't exist - need to add Review section
    # Try to insert before ## Session Notes or at end
    review_section = f"""## Review

**Verdict:** {verdict}
**Reviewed:** —

### Checklist (for reviewer)
- [ ] Code quality acceptable
- [ ] Tests are meaningful
- [ ] No security concerns
- [ ] Matches spec intent

### Notes
[Reviewer findings go here]

"""

    # Insert before ## Session Notes if it exists
    session_marker = "## Session Notes"
    if session_marker in impl_content:
        idx = impl_content.index(session_marker)
        return impl_content[:idx] + review_section + impl_content[idx:]

    # Otherwise append before final --- or at end
    if impl_content.rstrip().endswith("---"):
        return impl_content.rstrip()[:-3] + review_section + "---\n"

    return impl_content.rstrip() + "\n\n" + review_section


def _add_review_note(impl_content: str, note: str) -> str:
    """Safely add a note to the Review Notes section.

    Uses string manipulation instead of regex replacement to avoid
    issues with special characters in the note text.

    Args:
        impl_content: IMPL file content
        note: Note text to add (can contain any characters)

    Returns:
        Updated content with note added after ### Notes header
    """
    marker = "### Notes\n"
    if marker in impl_content:
        # Insert note right after the ### Notes line
        idx = impl_content.index(marker) + len(marker)
        return impl_content[:idx] + note + "\n\n" + impl_content[idx:]

    # Fallback: ### Notes not found, try adding after ## Review
    review_marker = "## Review\n"
    if review_marker in impl_content:
        idx = impl_content.index(review_marker) + len(review_marker)
        return impl_content[:idx] + f"\n### Notes\n{note}\n\n" + impl_content[idx:]

    # Last resort: append to end
    return impl_content + f"\n\n### Notes\n{note}\n"


def request_review(
    spec_id: str,
    implementer: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Mark spec as ready for review.

    Sets the Implementer field and moves to Testing status.

    Args:
        spec_id: Spec ID
        implementer: Name/handle of implementer (e.g., "Claude", "Codex")
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Path to updated IMPL file

    Raises:
        FileNotFoundError: If IMPL not found
        ValueError: If spec is not in Active status
    """
    impl_path = _find_impl_file(spec_id, docs_root, paths_config, project_root)
    content = impl_path.read_text()

    # Validate IMPL is in Active status (can't request review before work starts)
    current_status = _get_current_status(content, kind="IMPL")
    if current_status:
        status_code, _, status_text = current_status
        if status_code == 0:  # Planning
            raise ValueError(
                f"❌ Cannot request review: Spec {spec_id} is still in Planning. "
                f"Run nspec_activate first."
            )
        if status_code >= 2:  # Testing or beyond
            raise ValueError(
                f"❌ Cannot request review: Spec {spec_id} is already in {status_text}."
            )

    # Update implementer field
    content = _set_impl_field(content, "Implementer", implementer)

    # Ensure verdict is PENDING
    content = _set_review_verdict(content, "PENDING")

    impl_path.write_text(content)

    # Move to Testing status (FR stays Active, IMPL goes to Testing)
    set_status(
        spec_id, 2, 2, docs_root, paths_config=paths_config, project_root=project_root
    )  # FR=Active, IMPL=Testing

    print(f"✅ Spec {spec_id} ready for review")
    print(f"   Implementer: {implementer}")
    print("   Status: 🧪 Testing (awaiting review)")
    print(
        f"\n   Next: A different reviewer should run: nspec_start_review {spec_id} <reviewer_name>"
    )

    return impl_path


def start_review(
    spec_id: str,
    reviewer: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Claim a spec for review.

    Sets the Reviewer field. Validates reviewer != implementer.

    Args:
        spec_id: Spec ID
        reviewer: Name/handle of reviewer
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Path to updated IMPL file

    Raises:
        FileNotFoundError: If IMPL not found
        ValueError: If reviewer == implementer or spec not in Testing status
    """
    impl_path = _find_impl_file(spec_id, docs_root, paths_config, project_root)
    content = impl_path.read_text()

    # Check implementer
    implementer = _get_impl_field(content, "Implementer")
    if implementer and implementer.lower() == reviewer.lower():
        raise ValueError(f"❌ Reviewer cannot be the same as implementer ({implementer})")

    # Set reviewer
    content = _set_impl_field(content, "Reviewer", reviewer)
    impl_path.write_text(content)

    print(f"✅ Review started for Spec {spec_id}")
    print(f"   Implementer: {implementer or '(not set)'}")
    print(f"   Reviewer: {reviewer}")
    print("\n   After review, run either:")
    print(f"   - nspec_approve {spec_id}           # If approved")
    print(f"   - nspec_request_changes {spec_id}   # If changes needed")

    return impl_path


def approve_review(
    spec_id: str,
    notes: str | None,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Approve a spec's review.

    Sets verdict to APPROVED and moves to Ready status.

    Args:
        spec_id: Spec ID
        notes: Optional review notes
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Path to updated IMPL file
    """
    impl_path = _find_impl_file(spec_id, docs_root, paths_config, project_root)
    content = impl_path.read_text()

    # Validate reviewer is set
    reviewer = _get_impl_field(content, "Reviewer")
    if not reviewer:
        raise ValueError("❌ Cannot approve: No reviewer set. Run nspec_start_review first.")

    # Set verdict
    content = _set_review_verdict(content, "APPROVED")

    # Add review date
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    content = _set_impl_field(content, "Reviewed", today)

    # Add notes to Review section if provided
    if notes:
        content = _add_review_note(content, notes)

    impl_path.write_text(content)

    # Move to Ready status (FR=Completed when IMPL=Ready per set_status auto-upgrade)
    set_status(
        spec_id, 3, 3, docs_root, paths_config=paths_config, project_root=project_root
    )  # FR=Completed, IMPL=Ready

    print(f"✅ Spec {spec_id} APPROVED")
    print(f"   Reviewer: {reviewer}")
    print(f"   Reviewed: {today}")
    print(f"\n   Ready to complete: nspec_complete {spec_id}")

    return impl_path


def request_changes(
    spec_id: str,
    notes: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Request changes on a spec's review.

    Sets verdict to NEEDS_WORK. Spec stays in Testing status.

    Args:
        spec_id: Spec ID
        notes: Review notes explaining what needs to change
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Path to updated IMPL file
    """
    impl_path = _find_impl_file(spec_id, docs_root, paths_config, project_root)
    content = impl_path.read_text()

    # Validate reviewer is set
    reviewer = _get_impl_field(content, "Reviewer")
    if not reviewer:
        raise ValueError(
            "❌ Cannot request changes: No reviewer set. Run nspec_start_review first."
        )

    # Set verdict
    content = _set_review_verdict(content, "NEEDS_WORK")

    # Add notes to Review section
    content = _add_review_note(content, f"**Changes requested ({reviewer}):** {notes}")

    impl_path.write_text(content)

    implementer = _get_impl_field(content, "Implementer")

    print(f"⚠️  Spec {spec_id} NEEDS WORK")
    print(f"   Reviewer: {reviewer}")
    print(f"   Notes: {notes}")
    print(f"\n   Implementer ({implementer}) should address feedback, then:")
    print(f"   - nspec_request_review {spec_id} {implementer}  # Re-submit for review")

    return impl_path


def _find_impl_file(
    spec_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Find IMPL file for a spec.

    Searches both active and completed directories.
    """
    spec_id = normalize_spec_ref(spec_id)
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)
    impl_pattern = f"IMPL-{spec_id}-*.md"

    # Check active directory first
    impl_dir = paths.active_impls_dir
    impl_files = list(impl_dir.glob(impl_pattern))
    if impl_files:
        return impl_files[0]

    # Check completed directory
    completed_dir = paths.completed_impls_dir
    impl_files = list(completed_dir.glob(impl_pattern))
    if impl_files:
        return impl_files[0]

    raise FileNotFoundError(f"IMPL-{spec_id}-*.md not found")


def get_review_status(
    spec_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> dict:
    """Get review status for a spec.

    Returns:
        Dict with implementer, reviewer, verdict, reviewed date
    """
    impl_path = _find_impl_file(spec_id, docs_root, paths_config, project_root)
    content = impl_path.read_text()

    return {
        "implementer": _get_impl_field(content, "Implementer"),
        "reviewer": _get_impl_field(content, "Reviewer"),
        "verdict": _get_review_verdict(content),
        "reviewed": _get_impl_field(content, "Reviewed"),
    }


def set_task_blocked(
    spec_id: str,
    task_id: str,
    reason: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Mark an IMPL task as blocked by inserting a BLOCKED marker.

    Inserts a `  - **BLOCKED:** <reason>` line immediately after the task line.

    Args:
        spec_id: Spec ID (e.g., "004")
        task_id: Task number to match (e.g., "1", "2.1", "dod-1")
        reason: Reason for blocking
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for config lookup

    Returns:
        Path to updated IMPL file

    Raises:
        FileNotFoundError: If IMPL not found
        ValueError: If task ID not found
    """
    impl_path = _find_impl_file(spec_id, docs_root, paths_config, project_root)
    content = impl_path.read_text()
    lines = content.split("\n")

    target_line_idx = None

    for i, line in enumerate(lines):
        if line.startswith("- [") and _line_matches_task_id(line, task_id):
            target_line_idx = i
            break

    if target_line_idx is None:
        raise ValueError(
            f"Task '{task_id}' not found in IMPL-{spec_id}. Make sure the task exists."
        )

    # Check if already blocked
    if target_line_idx + 1 < len(lines):
        next_line = lines[target_line_idx + 1]
        if "**BLOCKED:**" in next_line:
            raise ValueError(f"Task '{task_id}' in IMPL-{spec_id} is already blocked.")

    # Insert BLOCKED marker after the task line
    blocked_line = f"  - **BLOCKED:** {reason}"
    lines.insert(target_line_idx + 1, blocked_line)

    impl_path.write_text("\n".join(lines))
    return impl_path


def set_task_unblocked(
    spec_id: str,
    task_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> Path:
    """Remove the BLOCKED marker from an IMPL task.

    Args:
        spec_id: Spec ID (e.g., "004")
        task_id: Task number to match (e.g., "1", "2.1")
        docs_root: Path to docs/ directory
        paths_config: Optional custom paths configuration
        project_root: Project root for config lookup

    Returns:
        Path to updated IMPL file

    Raises:
        FileNotFoundError: If IMPL not found
        ValueError: If task or BLOCKED marker not found
    """
    impl_path = _find_impl_file(spec_id, docs_root, paths_config, project_root)
    content = impl_path.read_text()
    lines = content.split("\n")

    target_line_idx = None

    for i, line in enumerate(lines):
        if line.startswith("- [") and _line_matches_task_id(line, task_id):
            target_line_idx = i
            break

    if target_line_idx is None:
        raise ValueError(f"Task '{task_id}' not found in IMPL-{spec_id}.")

    # Check for BLOCKED marker on next line
    if target_line_idx + 1 >= len(lines) or "**BLOCKED:**" not in lines[target_line_idx + 1]:
        raise ValueError(f"Task '{task_id}' in IMPL-{spec_id} is not blocked.")

    # Remove the BLOCKED line
    lines.pop(target_line_idx + 1)

    impl_path.write_text("\n".join(lines))
    return impl_path


def park_spec(
    spec_id: str,
    docs_root: Path,
    reason: str | None = None,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[Path, Path]:
    """Park a spec by setting IMPL to Paused and FR to Deferred.

    Sets both statuses and optionally records a blocker summary
    in the IMPL execution notes.

    Args:
        spec_id: Spec ID (e.g., "004")
        docs_root: Path to docs/ directory
        reason: Optional blocker reason to record in IMPL
        paths_config: Optional custom paths configuration
        project_root: Project root for config lookup

    Returns:
        Tuple of (FR path, IMPL path)

    Raises:
        FileNotFoundError: If FR or IMPL not found
    """
    impl_path = _find_impl_file(spec_id, docs_root, paths_config, project_root)
    impl_content = impl_path.read_text()
    current_impl_status = _get_current_status(impl_content, kind="IMPL")

    if current_impl_status and current_impl_status[2] == "Paused":
        raise ValueError(f"Spec {spec_id} is already paused.")

    # Set FR to Deferred, IMPL to Paused
    fr_path, impl_path = set_status(
        spec_id,
        FRStatusCode.DEFERRED,
        IMPLStatusCode.PAUSED,
        docs_root,
        force=True,
        paths_config=paths_config,
        project_root=project_root,
    )

    # Record blocker summary in IMPL execution notes
    if reason:
        impl_content = impl_path.read_text()
        timestamp = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
        note = f"\n- **{timestamp}:** PARKED — {reason}"

        if "## Execution Notes" in impl_content:
            parts = impl_content.split("## Execution Notes", 1)
            rest = parts[1]
            next_section = re.search(r"\n##\s", rest)
            if next_section:
                insert_pos = next_section.start()
                new_content = (
                    parts[0] + "## Execution Notes" + rest[:insert_pos] + note + rest[insert_pos:]
                )
            else:
                new_content = impl_content + note
        else:
            new_content = impl_content.rstrip() + "\n\n## Execution Notes\n" + note

        impl_path.write_text(new_content)

    return fr_path, impl_path
