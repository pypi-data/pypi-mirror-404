"""Validation checkers for Layers 3-6 - cross-document validation.

After Layer 1 (format) and Layer 2 (loading) succeed, these checkers
validate relationships between documents:

    Layer 3: Existence - FR/IMPL pairing, orphan detection
    Layer 4: Dependencies - graph validation, circular deps
    Layer 5: Business Logic - priority inheritance, LOE totals
    Layer 6: Ordering - nspec structure, deps-first ordering

All checkers return lists of error messages. Empty list = validation passed.
"""

from dataclasses import dataclass

from nspec.datasets import NspecDatasets


@dataclass
class ValidationError:
    """Single validation error with context."""

    layer: str  # "Layer 3: Existence", etc.
    message: str  # Error description
    spec_id: str | None = None  # Related spec ID if applicable
    severity: str = "error"  # "error" | "warning"

    def __str__(self) -> str:
        """Format error for display."""
        prefix = "❌" if self.severity == "error" else "⚠️ "
        return f"{prefix} {self.message}"


class ExistenceChecker:
    """Layer 3: Validate FR/IMPL pairing and detect orphans.

    Checks:
        1. Every FR has matching IMPL (same location)
        2. Every IMPL has matching FR (same location)
        3. No mixed locations (FR active but IMPL completed)
        4. No orphaned documents
    """

    def __init__(self, datasets: NspecDatasets):
        """Initialize with datasets."""
        self.datasets = datasets

    def check(self) -> list[ValidationError]:
        """Run all existence validations.

        Returns:
            List of ValidationError objects (empty if valid)
        """
        errors = []

        # Check active FRs have active IMPLs
        errors.extend(self._check_active_fr_impl_pairing())

        # Check active IMPLs have active FRs
        errors.extend(self._check_active_impl_fr_pairing())

        # Check completed FRs have completed IMPLs
        errors.extend(self._check_completed_fr_impl_pairing())

        # Check completed IMPLs have completed FRs
        errors.extend(self._check_completed_impl_fr_pairing())

        return errors

    def _check_active_fr_impl_pairing(self) -> list[ValidationError]:
        """Check every active FR has matching active IMPL."""
        errors = []

        for spec_id, fr in self.datasets.active_frs.items():
            if spec_id not in self.datasets.active_impls:
                # Check if IMPL exists in completed (mixed location)
                if spec_id in self.datasets.completed_impls:
                    errors.append(
                        ValidationError(
                            layer="Layer 3: Existence",
                            message=(
                                f"Mixed location for Spec {spec_id}\n"
                                f"   FR in docs/frs/active/ but IMPL in docs/completed/IMPL/\n"  # noqa: E501
                                f"   Spec appears complete (IMPL done) but FR still active\n"
                                f"   ➜ If spec is complete, move {fr.path.name} to docs/completed/FR/"  # noqa: E501
                            ),
                            spec_id=spec_id,
                        )
                    )
                else:
                    # True orphan - no IMPL at all
                    errors.append(
                        ValidationError(
                            layer="Layer 3: Existence",
                            message=(
                                f"Orphaned FR: {fr.path.name} (docs/frs/active/)\n"
                                f"   Expected matching IMPL-{spec_id}-*.md in docs/impls/active/\n"  # noqa: E501
                                f"   ➜ Create IMPL or delete FR if obsolete"
                            ),
                            spec_id=spec_id,
                        )
                    )

        return errors

    def _check_active_impl_fr_pairing(self) -> list[ValidationError]:
        """Check every active IMPL has matching active FR."""
        errors = []

        for spec_id, impl in self.datasets.active_impls.items():
            if spec_id not in self.datasets.active_frs:
                # Check if FR exists in completed (mixed location)
                if spec_id in self.datasets.completed_frs:
                    self.datasets.completed_frs[spec_id]
                    errors.append(
                        ValidationError(
                            layer="Layer 3: Existence",
                            message=(
                                f"Mixed location for Spec {spec_id}\n"
                                f"   FR in docs/completed/FR/ but IMPL in docs/impls/active/\n"  # noqa: E501
                                f"   FR appears complete but IMPL still active\n"
                                f"   ➜ Review IMPL-{spec_id}-*.md - if complete, move to docs/completed/IMPL/\n"  # noqa: E501
                                f"   ➜ If IMPL has incomplete tasks, move FR back to docs/frs/active/"  # noqa: E501
                            ),
                            spec_id=spec_id,
                        )
                    )
                else:
                    # True orphan - no FR at all
                    errors.append(
                        ValidationError(
                            layer="Layer 3: Existence",
                            message=(
                                f"Orphaned IMPL: {impl.path.name} (docs/impls/active/)\n"
                                f"   Expected matching FR-{spec_id}-*.md in docs/frs/active/\n"  # noqa: E501
                                f"   ➜ Create FR or delete IMPL if obsolete"
                            ),
                            spec_id=spec_id,
                        )
                    )

        return errors

    def _check_completed_fr_impl_pairing(self) -> list[ValidationError]:
        """Check every completed FR has matching completed IMPL."""
        errors = []

        for spec_id, fr in self.datasets.completed_frs.items():
            if spec_id not in self.datasets.completed_impls:
                # This is a warning, not error - completed FR without IMPL might be valid
                errors.append(
                    ValidationError(
                        layer="Layer 3: Existence",
                        message=(
                            f"Completed FR without matching IMPL: {fr.path.name}\n"
                            f"   Expected IMPL-{spec_id}-*.md in docs/completed/IMPL/\n"
                            f"   ➜ Verify spec was actually completed or create missing IMPL"  # noqa: E501
                        ),
                        spec_id=spec_id,  # noqa: E501
                        severity="warning",
                    )
                )

        return errors

    def _check_completed_impl_fr_pairing(self) -> list[ValidationError]:
        """Check every completed IMPL has matching completed FR."""
        errors = []

        for spec_id, impl in self.datasets.completed_impls.items():
            if spec_id not in self.datasets.completed_frs:
                # This is a warning
                errors.append(  # noqa: E501
                    ValidationError(
                        layer="Layer 3: Existence",
                        message=(
                            f"Completed IMPL without matching FR: {impl.path.name}\n"
                            f"   Expected FR-{spec_id}-*.md in docs/completed/FR/\n"
                            f"   ➜ Verify spec was actually completed or create missing FR"
                        ),
                        spec_id=spec_id,
                        severity="warning",
                    )
                )

        return errors


class DependencyChecker:
    """Layer 4: Validate dependency graph.

    Checks:
        1. All deps exist (active OR completed)
        2. No circular dependencies
        3. Deps only in FR files (not in IMPL)
    """

    def __init__(self, datasets: NspecDatasets):
        """Initialize with datasets."""
        self.datasets = datasets

    def check(self) -> list[ValidationError]:
        """Run all dependency validations.

        Returns:
            List of ValidationError objects (empty if valid)
        """
        errors = []

        # Check all deps exist
        errors.extend(self._check_deps_exist())

        # Check for circular deps
        errors.extend(self._check_circular_deps())

        return errors

    def _check_deps_exist(self) -> list[ValidationError]:
        """Validate all dependencies exist (active or completed)."""
        errors = []
        all_spec_ids = self.datasets.all_spec_ids()

        # Check active FRs
        for spec_id, fr in self.datasets.active_frs.items():
            for dep_id in fr.deps:
                if dep_id not in all_spec_ids:
                    errors.append(
                        ValidationError(
                            layer="Layer 4: Dependencies",
                            message=(
                                f"Invalid dependency in {fr.path.name}\n"
                                f"   Spec {spec_id} depends on Spec {dep_id} which doesn't exist\n"  # noqa: E501
                                f"   Available specs: {sorted(list(all_spec_ids))[:10]}...\n"
                                f"   ➜ Fix deps: [...] in {fr.path.name}"
                            ),
                            spec_id=spec_id,
                        )
                    )

        # Check completed FRs (they can still have deps for historical tracking)
        for spec_id, fr in self.datasets.completed_frs.items():
            for dep_id in fr.deps:
                if dep_id not in all_spec_ids:
                    errors.append(
                        ValidationError(
                            layer="Layer 4: Dependencies",
                            message=(
                                f"Invalid dependency in completed {fr.path.name}\n"
                                f"   Spec {spec_id} depends on Spec {dep_id} which doesn't exist\n"  # noqa: E501
                                f"   ➜ Historical data may be incomplete"
                            ),
                            spec_id=spec_id,
                            severity="warning",
                        )
                    )

        return errors

    def _check_circular_deps(self) -> list[ValidationError]:
        """Detect circular dependencies using DFS."""
        errors = []

        # Build graph (only active specs - completed can't have circular deps)
        graph = {spec_id: fr.deps for spec_id, fr in self.datasets.active_frs.items()}

        # DFS to detect cycles
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: list[str]) -> list[str] | None:
            """DFS helper - returns cycle path if found."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path.copy())
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            rec_stack.remove(node)
            return None

        # Check each node
        for spec_id in graph:
            if spec_id not in visited:
                cycle = dfs(spec_id, [])
                if cycle:
                    cycle_str = " → ".join(cycle)
                    errors.append(
                        ValidationError(
                            layer="Layer 4: Dependencies",
                            message=(
                                f"Circular dependency detected: {cycle_str}\n"
                                f"   Specs form a dependency loop\n"
                                f"   ➜ Remove one dependency to break the cycle"
                            ),
                            spec_id=cycle[0],
                        )
                    )
                    break  # Only report first cycle found

        return errors


class BusinessLogicChecker:
    """Layer 5: Validate business rules.

    Checks:
        1. Priority inheritance (spec priority <= max(dep priorities))
        2. LOE totals (spec LOE >= sum(active dep LOEs))
        3. Completion state consistency
        4. (Strict mode) Every spec must be grouped under an epic
    """

    def __init__(
        self,
        datasets: NspecDatasets,
        strict_mode: bool = False,
        strict_completion_parity: bool = True,
    ):
        """Initialize with datasets.

        Args:
            datasets: Loaded nspec datasets
            strict_mode: If True, enforce that every spec must be a dependency
                        of at least one epic (for grouping/organization)
            strict_completion_parity: If True, IMPL=Completed requires FR=Completed
        """
        self.datasets = datasets
        self.strict_mode = strict_mode
        self.strict_completion_parity = strict_completion_parity
        # Unified priority order: P0 > P1 > P2 > P3
        self.priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

    def check(self) -> list[ValidationError]:
        """Run all business logic validations.

        Returns:
            List of ValidationError objects (empty if valid)
        """
        errors = []

        # Check priority inheritance
        errors.extend(self._check_priority_inheritance())

        # Check epic dependency rules (epics only depend on epics)
        errors.extend(self._check_epic_dependency_rules())

        # Strict mode: Check every spec is grouped under an epic
        if self.strict_mode:
            errors.extend(self._check_spec_epic_grouping())

        # Check specs belong to only one epic (always enforced)
        errors.extend(self._check_single_epic_membership())

        # Check FR/IMPL status parity (IMPL Active requires FR Active)
        errors.extend(self._check_fr_impl_status_parity())

        # Check epic consistency (spec deps must be in same epic or cross-epic link)
        errors.extend(self._check_epic_consistency())

        # NOTE: LOE totals check disabled - LOE is now auto-calculated from deps
        # in NspecDatasets.calculate_loe_rollups(). The effective_loe field
        # contains the rolled-up value, so manual LOE mismatches are no longer relevant.
        # errors.extend(self._check_loe_totals())

        return errors

    def _check_priority_inheritance(self) -> list[ValidationError]:
        """Check priority inheritance (DEPRECATED - replaced by dependency-aware sorting).

        NOTE: This check is disabled as of Spec 123. We now allow high-priority
        specs to depend on lower-priority specs, and the dependency-aware
        sorting algorithm (cli.py:_calculate_effective_priority) handles promoting
        dependencies to appear in the correct order.

        Example: Spec 093 (P1) can depend on Spec 044 (P2), and the sorter will
        promote 044 to appear before other P2 specs.

        This validation rule was removed to enable more flexible priority management
        while maintaining correct execution order through topological sorting.
        """
        # Disabled - dependency-aware sorting handles this
        return []

    def _check_priority_parity(self) -> list[ValidationError]:
        """Legacy parity check (E/P priority levels).

        Priority is unified to P0-P3 (FR-100), and dependency-aware ordering handles
        promotion in views. Keep this method as a no-op for backwards compatibility.
        """
        return []

    def _check_epic_dependency_rules(self) -> list[ValidationError]:
        """Check epic dependency rules.

        Rules:
            1. Specs cannot depend on epics (only epics can depend on epics/specs)
            2. Epics cannot be superseded if another active epic depends on them

        These rules ensure clean epic hierarchies and prevent orphaned dependencies.
        """
        errors = []

        # Identify all epics
        epics_set = {sid for sid, fr in self.datasets.active_frs.items() if fr.type == "Epic"}

        for spec_id, fr in self.datasets.active_frs.items():
            # Rule 1: Specs cannot depend on epics
            if fr.type != "Epic":
                # This is a spec - check it doesn't depend on any epic
                for dep_id in fr.deps:
                    if dep_id in self.datasets.completed_frs:
                        continue
                    if dep_id in epics_set:
                        self.datasets.active_frs[dep_id]
                        errors.append(
                            ValidationError(
                                layer="Layer 5: Business Logic",
                                message=(
                                    f"Spec-to-epic dependency violation in {fr.path.name}\n"
                                    f"   Spec {spec_id} depends on Epic {dep_id}\n"
                                    f"   ❌ Specs cannot depend on epics\n"
                                    f"   ➜ Remove {dep_id} from {spec_id}'s deps, "
                                    f"or make {spec_id} a dep of Epic {dep_id} instead"
                                ),
                                spec_id=spec_id,
                            )
                        )

        # Rule 2: Check for superseded epics that are still depended on
        for spec_id, fr in self.datasets.active_frs.items():
            if "superseded" in fr.status.lower() and fr.type == "Epic":
                # This is a superseded epic - check if any active epic depends on it
                for other_id, other_fr in self.datasets.active_frs.items():
                    if other_id == spec_id:
                        continue
                    if "superseded" in other_fr.status.lower():
                        continue  # Skip other superseded items
                    if spec_id in other_fr.deps:
                        errors.append(
                            ValidationError(
                                layer="Layer 5: Business Logic",
                                message=(
                                    f"Superseded epic still has dependents: "
                                    f"{fr.path.name}\n"
                                    f"   Epic {spec_id} is superseded but {other_id} "
                                    f"depends on it\n"
                                    f"   ❌ Cannot supersede an epic that others "
                                    f"depend on\n"
                                    f"   ➜ Remove {spec_id} from {other_id}'s deps, "
                                    f"or un-supersede Epic {spec_id}"
                                ),
                                spec_id=spec_id,
                            )
                        )

        # Rule 3: Superseded epics must have empty deps (deps should migrate to superseding epic)
        for spec_id, fr in self.datasets.active_frs.items():
            if "superseded" in fr.status.lower() and fr.type == "Epic" and fr.deps:
                errors.append(
                    ValidationError(
                        layer="Layer 5: Business Logic",
                        message=(
                            f"Superseded epic still has dependencies: {fr.path.name}\n"
                            f"   Epic {spec_id} is superseded but still has deps: {fr.deps}\n"
                            f"   ❌ Superseded epics must have empty deps\n"
                            f"   ➜ Move deps to the superseding epic, then clear deps:\n"
                            f"      Edit {fr.path.name} and set deps: []"
                        ),
                        spec_id=spec_id,
                    )
                )

        return errors

    def _check_spec_epic_grouping(self) -> list[ValidationError]:
        """Check that every spec is grouped under at least one epic.

        In strict mode, every non-epic spec (P0-P3) must be a dependency of
        at least one epic. This ensures all work is organized under
        epic containers for better project management.

        Specs that are not dependencies of any epic are considered "ungrouped"
        and will be flagged as errors.

        Example:
            Epic 093 depends on [138, 152, 194]  -> Specs 138, 152, 194 are grouped
            Spec 999 has no epic depending on it -> Spec 999 is ungrouped (ERROR)
        """
        errors = []

        # Build set of all epics
        epics = {sid for sid, fr in self.datasets.active_frs.items() if fr.type == "Epic"}

        # Build set of all specs that are dependencies of an epic
        # (i.e., some epic depends on them)
        specs_under_epics: set[str] = set()
        for epic_id in epics:
            epic_fr = self.datasets.active_frs[epic_id]
            for dep_id in epic_fr.deps:
                specs_under_epics.add(dep_id)

        # Find ungrouped specs (non-epic specs not under any epic)
        ungrouped_specs = []
        for spec_id, fr in self.datasets.active_frs.items():
            # Skip epics - they don't need to be under another epic
            if fr.type == "Epic":
                continue

            # Skip superseded specs - they're not active work
            if "superseded" in fr.status.lower():
                continue

            # Check if this spec is a dependency of any epic
            if spec_id not in specs_under_epics:
                ungrouped_specs.append((spec_id, fr))

        # Report ungrouped specs as a single consolidated error
        if ungrouped_specs:
            # Group by priority for cleaner reporting
            by_priority: dict[str, list[tuple[str, object]]] = {}
            for spec_id, fr in ungrouped_specs:
                if fr.priority not in by_priority:
                    by_priority[fr.priority] = []
                by_priority[fr.priority].append((spec_id, fr))

            # Build consolidated message
            lines = [
                f"Found {len(ungrouped_specs)} ungrouped specs (strict mode "
                f"requires epic grouping):",
                "",
            ]

            for priority in sorted(by_priority.keys()):
                specs = by_priority[priority]
                level = priority[1]  # P1 -> "1", P2 -> "2", etc.
                matching_epics = [
                    eid for eid in epics if self.datasets.active_frs[eid].priority == f"E{level}"
                ]
                epic_hint = (
                    f"(available E{level} epics: {', '.join(sorted(matching_epics))})"
                    if matching_epics
                    else f"(no E{level} epics exist)"
                )

                lines.append(f"   {priority} specs {epic_hint}:")
                for spec_id, fr in sorted(specs, key=lambda x: x[0]):
                    # Extract short title from filename
                    title = fr.path.stem.replace(f"FR-{spec_id}-", "").replace("-", " ").title()
                    lines.append(f"      {spec_id}: {title}")
                lines.append("")

            lines.append("   ➜ To fix, add specs to epics:")
            lines.append("      make nspec.add-dep <epic_id> <spec_id>")

            errors.append(
                ValidationError(
                    layer="Layer 5: Business Logic (Strict)",
                    message="\n".join(lines),
                    spec_id=None,
                )
            )

        return errors

    def _check_single_epic_membership(self) -> list[ValidationError]:
        """Check that specs belong to at most one epic.

        A spec should only be a dependency of ONE epic to maintain clear ownership
        and avoid confusion about which epic tracks the spec's progress.

        Example:
            Spec 194 in deps of Epic 093 AND Epic 215 -> ERROR (multi-epic)
            Spec 194 in deps of Epic 093 only -> OK

        Returns:
            List of ValidationError objects for specs in multiple epics
        """
        errors = []

        # Build set of all epics
        epics = {sid for sid, fr in self.datasets.active_frs.items() if fr.type == "Epic"}

        # Track which epics each spec belongs to
        spec_to_epics: dict[str, list[str]] = {}
        for epic_id in epics:
            epic_fr = self.datasets.active_frs[epic_id]
            for dep_id in epic_fr.deps:
                # Skip if dependency is itself an epic (epics can depend on epics)
                if dep_id in epics:
                    continue
                # Skip completed specs - they may have historical multi-epic refs
                if dep_id in self.datasets.completed_frs:
                    continue
                # Track the spec -> epic mapping
                if dep_id not in spec_to_epics:
                    spec_to_epics[dep_id] = []
                spec_to_epics[dep_id].append(epic_id)

        # Find specs in multiple epics
        multi_epic_specs = [
            (spec_id, epic_list)
            for spec_id, epic_list in spec_to_epics.items()
            if len(epic_list) > 1
        ]

        if multi_epic_specs:
            lines = [
                f"Found {len(multi_epic_specs)} specs belonging to multiple epics:",
                "",
            ]

            for spec_id, epic_list in sorted(multi_epic_specs, key=lambda x: x[0]):
                fr = self.datasets.active_frs.get(spec_id)
                if fr:
                    title = fr.path.stem.replace(f"FR-{spec_id}-", "").replace("-", " ").title()
                    epic_str = ", ".join(sorted(epic_list))
                    lines.append(f"   {spec_id}: {title}")
                    lines.append(f"      └─ In epics: {epic_str}")

            lines.append("")
            lines.append("   ➜ Each spec should belong to exactly one epic.")
            lines.append("   ➜ To fix, remove from extra epics:")
            lines.append("      make nspec.remove-dep <epic_id> <spec_id>")

            errors.append(
                ValidationError(
                    layer="Layer 5: Business Logic",
                    message="\n".join(lines),
                    spec_id=None,
                )
            )

        return errors

    def _check_fr_impl_status_parity(self) -> list[ValidationError]:
        """Check FR/IMPL status parity rules.

        Rule: IMPL cannot be Active (1+) unless FR is Active (2+).
        Rationale: FR defines WHAT to build - spec must be finalized before implementation.

        Returns consolidated error listing all violations.
        """
        errors = []
        violations = []

        # Status codes: FR 0=Proposed, 1=In Design, 2=Active, 3=Completed
        #               IMPL 0=Planning, 1=Active, 2=Testing, 3=Completed
        fr_status_names = {
            "proposed": 0,
            "in design": 1,
            "active": 2,
            "completed": 3,
            "rejected": 4,
            "superseded": 5,
            "deferred": 6,
        }
        impl_status_names = {
            "planning": 0,
            "active": 1,
            "testing": 2,
            "completed": 3,
            "paused": 4,
            "hold": 5,
        }

        for spec_id, impl in self.datasets.active_impls.items():
            fr = self.datasets.active_frs.get(spec_id)
            if not fr:
                continue  # Orphan check handles this

            # Parse status text to codes using centralized parser
            from nspec.statuses import parse_status_text

            fr_status_text = parse_status_text(fr.status)
            impl_status_text = parse_status_text(impl.status)

            fr_code = fr_status_names.get(fr_status_text, -1)
            impl_code = impl_status_names.get(impl_status_text, -1)

            # Rule 1: IMPL Active/Testing requires FR Active (2+)
            # Skip Paused (4) and Hold (5) - work isn't active
            if impl_code >= 1 and impl_code <= 2 and fr_code < 2 and fr_code >= 0:
                violations.append((spec_id, fr, impl, fr_status_text, impl_status_text, "active"))

            # Rule 2: IMPL Completed requires FR Completed (strict, configurable)
            # Cannot mark implementation done until spec is finalized as complete
            if self.strict_completion_parity and impl_code == 3 and fr_code != 3:
                violations.append(
                    (spec_id, fr, impl, fr_status_text, impl_status_text, "completed")
                )

        # Consolidate into single error message
        if violations:
            active_violations = [
                (s, f, i, fs, ist) for s, f, i, fs, ist, vt in violations if vt == "active"
            ]
            completed_violations = [
                (s, f, i, fs, ist) for s, f, i, fs, ist, vt in violations if vt == "completed"
            ]

            lines = [
                f"Found {len(violations)} FR/IMPL status parity violations:",
                "",
            ]

            if active_violations:
                lines.append("   Rule 1: IMPL cannot be Active/Testing until FR is Active")
                lines.append("")
                for spec_id, fr, _impl, fr_status, impl_status in sorted(
                    active_violations, key=lambda x: x[0]
                ):
                    title = fr.path.stem.replace(f"FR-{spec_id}-", "").replace("-", " ").title()
                    lines.append(f"      {spec_id}: {title}")
                    lines.append(f"           FR={fr_status.title()}, IMPL={impl_status.title()}")
                lines.append("")
                lines.append("   ➜ Fix: make nspec.activate <id>")
                lines.append("")

            if completed_violations:
                lines.append("   Rule 2: IMPL cannot be Completed until FR is Completed")
                lines.append("")
                for spec_id, fr, _impl, fr_status, impl_status in sorted(
                    completed_violations, key=lambda x: x[0]
                ):
                    title = fr.path.stem.replace(f"FR-{spec_id}-", "").replace("-", " ").title()
                    lines.append(f"      {spec_id}: {title}")
                    lines.append(f"           FR={fr_status.title()}, IMPL={impl_status.title()}")
                lines.append("")
                lines.append("   ➜ Fix: make nspec.next-status <id>  # Advance until completed")

            errors.append(
                ValidationError(
                    layer="Layer 5: Business Logic",
                    message="\n".join(lines),
                    spec_id=None,
                )
            )

        return errors

    def _check_epic_consistency(self) -> list[ValidationError]:
        """Check that specs and their dependencies are in the same epic.

        Rules:
            1. If spec A depends on spec B, both should be in the same epic
            2. Exception: If spec A's epic depends on spec B's epic (epic-to-epic
               dependency), this creates a cross-epic bridge that allows the dependency

        Epic ordering uses the unified P0-P3 priority values.
        each other. Spec priorities (P0-P3) are for within-epic ordering.

        Example violations:
            - Spec in Epic 226 depends on Spec in Epic 344, and Epic 226 has no
              dependency on Epic 344

        Example allowed:
            - Spec in Epic 226 depends on Spec in Epic 344, and Epic 226 depends
              on Epic 344 (explicit cross-epic bridge)
        """
        errors = []

        # Build set of all epics and spec-to-epic mapping
        epics_set = {sid for sid, fr in self.datasets.active_frs.items() if fr.type == "Epic"}

        # Map specs to their owning epic (the epic that depends on them)
        spec_to_epic: dict[str, str] = {}
        for epic_id in epics_set:
            epic_fr = self.datasets.active_frs[epic_id]
            for dep_id in epic_fr.deps:
                # Only map non-epic dependencies
                if (
                    dep_id not in epics_set
                    and dep_id in self.datasets.active_frs
                    and dep_id not in spec_to_epic
                ):
                    # Note: _check_single_epic_membership already ensures single epic
                    # Here we just need the first/only epic for comparison
                    spec_to_epic[dep_id] = epic_id

        # Build cross-epic links from epic-to-epic dependencies
        # cross_epic_links[epic_a] = set of epic_ids that epic_a depends on
        cross_epic_links: dict[str, set[str]] = {eid: set() for eid in epics_set}
        for epic_id in epics_set:
            epic_fr = self.datasets.active_frs[epic_id]
            for dep_id in epic_fr.deps:
                # Epic-to-epic dependency creates a cross-epic bridge
                if dep_id in epics_set:
                    cross_epic_links[epic_id].add(dep_id)

        # Check each spec's dependencies for epic consistency
        violations = []
        for spec_id, fr in self.datasets.active_frs.items():
            # Skip epics - they can depend on anything
            if fr.type == "Epic":
                continue

            # Skip specs not in any epic
            if spec_id not in spec_to_epic:
                continue

            spec_epic = spec_to_epic[spec_id]

            for dep_id in fr.deps:
                # Skip completed dependencies
                if dep_id in self.datasets.completed_frs:
                    continue

                # Skip if dep isn't in any epic (orphan)
                if dep_id not in spec_to_epic:
                    continue

                dep_epic = spec_to_epic[dep_id]

                # Same epic = OK
                if dep_epic == spec_epic:
                    continue

                # Different epic - check for cross-epic bridge
                # Cross-epic link exists if spec_epic depends on dep_epic
                if dep_epic in cross_epic_links.get(spec_epic, set()):
                    continue  # Cross-epic bridge exists

                # Violation: dependency in different epic with no bridge
                violations.append((spec_id, spec_epic, dep_id, dep_epic))

        if violations:
            lines = [
                f"Found {len(violations)} epic consistency violations:",
                "",
                "   Specs with dependencies in different epics (no cross-epic link):",
                "",
            ]

            for spec_id, spec_epic, dep_id, dep_epic in sorted(violations):
                fr = self.datasets.active_frs.get(spec_id)
                title = (
                    fr.path.stem.replace(f"FR-{spec_id}-", "").replace("-", " ").title()
                    if fr
                    else ""
                )
                lines.append(
                    f"   Spec {spec_id} (Epic {spec_epic}) depends on "
                    f"Spec {dep_id} (Epic {dep_epic})"
                )
                lines.append(f"      └─ {title}")

            lines.append("")
            lines.append("   ➜ To fix, either:")
            lines.append("      1. Move the spec to the same epic as its dependency:")
            lines.append("         make nspec.remove-dep <current_epic> <spec>")
            lines.append("         make nspec.add-dep <dep_epic> <spec>")
            lines.append("      2. Add a cross-epic bridge (epic depends on the dependency):")
            lines.append("         make nspec.add-dep <spec_epic> <dep_id>")

            errors.append(
                ValidationError(
                    layer="Layer 5: Business Logic",
                    message="\n".join(lines),
                    spec_id=None,
                )
            )

        return errors

    def _check_loe_totals(self) -> list[ValidationError]:
        """Validate LOE totals against dependency estimates.

        Rule: Spec LOE should be >= sum of active dependency LOEs.
        This is a warning, not an error (estimates can be off).
        """
        errors = []

        for spec_id, fr in self.datasets.active_frs.items():
            impl = self.datasets.active_impls.get(spec_id)
            if not impl or not fr.deps:
                continue

            # Parse spec LOE (returns tuple: parallel, sequential)
            spec_parallel, spec_sequential = self._parse_loe_to_hours(impl.loe)

            # Determine if this is an epic
            is_epic = fr.type == "Epic" or spec_id.startswith("E")

            # Sum dependency LOEs (only active deps, skip completed)
            dep_parallel_total = 0
            dep_sequential_total = 0
            for dep_id in fr.deps:
                # Skip completed dependencies - they don't add to remaining work
                if dep_id in self.datasets.completed_impls:
                    continue
                if dep_id in self.datasets.active_impls:
                    dep_impl = self.datasets.active_impls[dep_id]
                    dep_par, dep_seq = self._parse_loe_to_hours(dep_impl.loe)
                    dep_parallel_total = max(dep_parallel_total, dep_par)  # Max for parallel
                    dep_sequential_total += dep_seq  # Sum for sequential

            # For epics: Check parallel >= max(deps), sequential >= sum(deps)
            # For specs: Check LOE >= sum(deps) (sequential only)
            if is_epic:
                # Epic validation: parallel should be >= max dep, sequential >= sum deps
                if dep_parallel_total > 0 and spec_parallel < dep_parallel_total:
                    dep_par_str = self._format_hours_to_loe(dep_parallel_total)
                    errors.append(
                        ValidationError(
                            layer="Layer 5: Business Logic",
                            message=(
                                f"Epic parallel LOE mismatch in {impl.path.name}\n"
                                f"   Spec {spec_id} parallel LOE: {spec_parallel}h\n"
                                f"   Longest dependency: {dep_par_str} ({dep_parallel_total}h)\n"
                                f"   Epic parallel LOE should be ≥ longest dependency\n"
                                f"   ➜ Consider increasing parallel LOE to ~{dep_par_str} or higher"
                            ),
                            spec_id=spec_id,
                            severity="warning",
                        )
                    )
                if dep_sequential_total > 0 and spec_sequential < dep_sequential_total:
                    dep_seq_str = self._format_hours_to_loe(dep_sequential_total)
                    errors.append(
                        ValidationError(
                            layer="Layer 5: Business Logic",
                            message=(
                                f"Epic sequential LOE mismatch in {impl.path.name}\n"
                                f"   Spec {spec_id} sequential LOE: {spec_sequential}h\n"
                                f"   Sum of active dep LOEs: {dep_seq_str} "
                                f"({dep_sequential_total}h)\n"
                                f"   Epic sequential LOE should be ≥ sum of "
                                f"dependency LOEs\n"
                                f"   ➜ Consider increasing sequential LOE to "
                                f"~{dep_seq_str} or higher"
                            ),
                            spec_id=spec_id,
                            severity="warning",
                        )
                    )
            else:
                # Spec validation: LOE >= sum of deps (sequential)
                if dep_sequential_total > 0 and spec_sequential < dep_sequential_total:
                    dep_loe_str = self._format_hours_to_loe(dep_sequential_total)
                    errors.append(
                        ValidationError(
                            layer="Layer 5: Business Logic",
                            message=(
                                f"LOE total mismatch in {impl.path.name}\n"
                                f"   Spec {spec_id} LOE: {impl.loe} "
                                f"({spec_sequential}h)\n"
                                f"   Sum of active dep LOEs: {dep_loe_str} "
                                f"({dep_sequential_total}h)\n"
                                f"   Spec LOE should be ≥ sum of dependency LOEs\n"
                                f"   ➜ Consider increasing LOE to ~{dep_loe_str} "
                                f"or higher"
                            ),
                            spec_id=spec_id,
                            severity="warning",
                        )
                    )

        return errors

    def _parse_loe_to_hours(self, loe: str) -> tuple[int, int]:
        """Convert LOE string to hours.

        Examples:
            Specs: ~5h -> (5, 5), ~3d -> (24, 24), ~2w -> (80, 80)
            Epics: ~18d,~79d -> (144, 632) (parallel, sequential)

        Returns:
            Tuple of (parallel_hours, sequential_hours)
            For specs, both values are the same
        """
        loe = loe.strip()

        # Check if this is epic format (parallel,sequential)
        if "," in loe:
            parts = loe.split(",")
            parallel = self._parse_single_loe(parts[0].strip())
            sequential = self._parse_single_loe(parts[1].strip())
            return (parallel, sequential)
        else:
            hours = self._parse_single_loe(loe)
            return (hours, hours)

    def _parse_single_loe(self, loe: str) -> int:
        """Parse a single LOE value to hours (supports decimals)."""
        loe = loe.lstrip("~")
        if loe.endswith("h"):
            return int(float(loe[:-1]))
        elif loe.endswith("d"):
            return int(float(loe[:-1]) * 8)  # 8 hour work day
        elif loe.endswith("w"):
            return int(float(loe[:-1]) * 40)  # 40 hour work week
        return 0

    def _format_hours_to_loe(self, hours: int) -> str:
        """Convert hours back to LOE format.

        Examples:
            5 -> ~5h
            24 -> ~3d
            80 -> ~2w
        """
        if hours >= 40 and hours % 40 == 0:
            return f"~{hours // 40}w"
        elif hours >= 8 and hours % 8 == 0:
            return f"~{hours // 8}d"
        else:
            return f"~{hours}h"


class OrderingChecker:
    """Layer 6: Validate nspec ordering.

    Checks:
        1. Dependencies appear before dependents
        2. Priority groups ordered (P0 > P1 > P2 > P3)
        3. Within priority: deps-first ordering
    """

    def __init__(self, datasets: NspecDatasets):
        """Initialize with datasets."""
        self.datasets = datasets

    def check(self, ordered_spec_ids: list[str]) -> list[ValidationError]:
        """Validate spec order follows rules.

        Args:
            ordered_spec_ids: List of spec IDs in nspec order

        Returns:
            List of ValidationError objects (empty if valid)
        """
        # DISABLED: Cross-epic dependency ordering conflicts with epic grouping.
        # Epic grouping is more important for visual organization.
        # Future enhancement: smart priority inheritance where prioritizing
        # an epic auto-upgrades its dependencies (dep_priority = MAX of dependents).
        return []
