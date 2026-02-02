"""Nspec Validator - Core validation and generation logic.

Extracted from cli.py to reduce module size and improve maintainability.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from nspec.checkers import (
    BusinessLogicChecker,
    DependencyChecker,
    ExistenceChecker,
    OrderingChecker,
)
from nspec.datasets import DatasetLoader, DatasetStats, NspecDatasets
from nspec.paths import NspecPaths
from nspec.spinner import spinner
from nspec.statuses import (
    ALL_PRIORITIES,
    FR_STATUSES,
    PRIORITY_NAMES,
    FRStatusCode,
    is_completed_status,
)
from nspec.summary import render_project_status
from nspec.validators import _parse_loe_to_hours

logger = logging.getLogger("nspec")


class NspecValidator:
    """Main orchestrator for nspec validation and generation.

    This class runs all 6 validation layers and provides reporting.

    Architecture (2-pass):
        Pass 1: Load datasets, validate, and calculate final sorted order
        Pass 2: Format final sorted datasets to NSPEC.md and NSPEC_COMPLETED.md
    """

    def __init__(
        self,
        docs_root: Path,
        strict_mode: bool = False,
        strict_completion_parity: bool = True,
        paths_config: NspecPaths | None = None,
        project_root: Path | None = None,
    ):
        """Initialize validator.

        Args:
            docs_root: Root docs directory (usually Path("docs"))
            strict_mode: If True, enforce that every spec must be grouped
                        under at least one epic
            strict_completion_parity: If True, IMPL=Completed requires FR=Completed
        """
        self.docs_root = docs_root
        self.strict_mode = strict_mode
        self.strict_completion_parity = strict_completion_parity
        self.paths_config = paths_config
        self.project_root = project_root
        self.datasets: NspecDatasets | None = None
        self.ordered_active_specs: list[str] = []
        self.ordered_completed_specs: list[str] = []
        self.verbose_status: bool = False  # Compact status by default (emoji only)
        self.epic_filter: str | None = None  # Filter to show only epic + dependencies

    def validate(self) -> tuple[bool, list[str]]:
        """Run all validation layers.

        Returns:
            (success, errors) - success=True if no errors
        """
        errors = []

        # Layer 1-2: Format validation + dataset loading
        logger.debug("Layer 1-2: Loading and validating document formats...")
        try:
            with spinner("Loading nspec"):
                loader = DatasetLoader(
                    docs_root=self.docs_root,
                    paths_config=self.paths_config,
                    project_root=self.project_root,
                )
                self.datasets = loader.load()
            logger.debug(
                f"Loaded {self.datasets.total_spec_count()} specs "
                f"({self.datasets.active_spec_count()} active, "
                f"{self.datasets.completed_spec_count()} completed)"
            )
        except ValueError as e:
            errors.append(str(e))
            return False, errors

        # Layer 3: Existence validation
        logger.debug("Layer 3: Checking FR/IMPL pairing...")
        checker = ExistenceChecker(self.datasets)
        layer3_errors = checker.check()
        if layer3_errors:
            errors.extend([str(e) for e in layer3_errors])
        else:
            logger.debug("All FR/IMPL pairs valid")

        # Layer 4: Dependency validation
        logger.debug("Layer 4: Validating dependency graph...")
        checker = DependencyChecker(self.datasets)
        layer4_errors = checker.check()
        if layer4_errors:
            errors.extend([str(e) for e in layer4_errors])
        else:
            logger.debug("Dependency graph valid")

        # Layer 5: Business logic validation
        logger.debug("Layer 5: Checking business rules...")
        checker = BusinessLogicChecker(
            self.datasets,
            strict_mode=self.strict_mode,
            strict_completion_parity=self.strict_completion_parity,
        )
        layer5_errors = checker.check()
        if layer5_errors:
            # Separate errors and warnings
            warnings = [e for e in layer5_errors if e.severity == "warning"]
            real_errors = [e for e in layer5_errors if e.severity == "error"]

            if real_errors:
                errors.extend([str(e) for e in real_errors])
            if warnings:
                logger.warning(f"{len(warnings)} warnings (non-blocking):")
                for w in warnings:
                    logger.warning(f"   {w}")

        if not layer5_errors or all(e.severity == "warning" for e in layer5_errors):
            logger.debug("Business rules valid")

        # Layer 6: Ordering validation (generate ordered list first)
        logger.debug("Layer 6: Validating nspec ordering...")
        self.ordered_active_specs = self._generate_ordered_nspec()
        checker = OrderingChecker(self.datasets)
        layer6_errors = checker.check(self.ordered_active_specs)
        if layer6_errors:
            errors.extend([str(e) for e in layer6_errors])
        else:
            logger.debug("Nspec ordering valid")

        # Generate ordered list for completed specs (simple: by spec ID)
        self.ordered_completed_specs = sorted(self.datasets.completed_frs.keys())

        # Layer 7: Completed-in-active validation
        # Fail if any active spec has "Completed" status (should be archived)
        completed_status = FR_STATUSES[FRStatusCode.COMPLETED]
        completed_in_active = []
        for spec_id, fr in self.datasets.active_frs.items():
            if is_completed_status(fr.status):
                completed_in_active.append((spec_id, fr.title))

        if completed_in_active:
            error_lines = [
                "VALIDATION ERROR: Completed specs in active directory",
                "",
                f'The following specs have "{completed_status.full}" status '
                "but are still in docs/frs/active/:",
                "",
            ]
            for spec_id, title in completed_in_active:
                # Clean up title (remove prefix if present)
                clean_title = title.split(": ", 1)[-1] if ": " in title else title
                error_lines.append(f"  - Spec {spec_id}: {clean_title}")

            error_lines.extend(
                [
                    "",
                    "To fix, archive each completed spec:",
                ]
            )
            for spec_id, _ in completed_in_active:
                error_lines.append(f"  make nspec.complete {spec_id}")

            error_lines.extend(
                [
                    "",
                    "Or if they shouldn't be completed, update their status:",
                ]
            )
            for spec_id, _ in completed_in_active:
                error_lines.append(f"  make nspec.activate {spec_id}  # Set to Active")

            errors.append("\n".join(error_lines))

        success = len(errors) == 0
        return success, errors

    def _calculate_effective_priority(
        self, sid: str, active_frs: dict[str, Any], memo: dict[str, int]
    ) -> int:
        """Calculate effective priority with dependency promotion.

        If a high-priority spec depends on this spec, promote this spec's
        effective priority to match.

        Args:
            sid: Spec ID to calculate priority for
            active_frs: Dictionary of active FR documents
            memo: Memoization cache for recursive calls

        Returns:
            Effective priority rank (0=P0, 1=P1, 2=P2, 3=P3)
        """
        if sid in memo:
            return memo[sid]

        # Priority ranking: P0 critical, then E1/P1 high, E2/P2 medium, E3/P3 low
        priority_rank = {"P0": 0, "E0": 0, "E1": 1, "P1": 1, "E2": 2, "P2": 2, "E3": 3, "P3": 3}
        fr = active_frs.get(sid)
        own_priority = priority_rank.get(fr.priority if fr else "P3", 6)

        # Find all specs that depend on this spec
        dependent_priorities = []
        for other_sid, other_fr in active_frs.items():
            if sid in other_fr.deps:
                # Recursively calculate dependent's effective priority
                dep_priority = self._calculate_effective_priority(other_sid, active_frs, memo)
                dependent_priorities.append(dep_priority)

        # Effective priority is the highest (lowest number) among:
        # - Own priority
        # - All dependent spec priorities (transitive)
        if dependent_priorities:
            effective = min(own_priority, min(dependent_priorities))
        else:
            effective = own_priority

        memo[sid] = effective
        return effective

    def _generate_ordered_nspec(self) -> list[str]:
        """Generate ordered list of active spec IDs grouped by parent epic.

        Multi-pass algorithm:
            Pass 1: Load all specs, identify epics
            Pass 2: Build "epic sets" (epic + its direct spec dependencies)
            Pass 3: Topological sort of epics based on epic-to-epic dependencies
            Pass 4: Order specs within each epic set by status
            Pass 5: Assemble final list: orphans first, then epic sets in topo order

        Validation:
            - Specs cannot appear as dependencies of multiple epics (fail fast)

        Returns:
            List of spec IDs in nspec order
        """
        if not self.datasets:
            return []

        active_frs = self.datasets.active_frs
        spec_ids = list(active_frs.keys())

        # Priority ranking: P0 critical, then E0/E1/P1 high, E2/P2 medium, E3/P3 low
        priority_rank = {"P0": 0, "E0": 0, "E1": 1, "P1": 1, "E2": 2, "P2": 2, "E3": 3, "P3": 3}
        # Status ranking: Active/Testing first, then Planning/In-Design, then Proposed/Paused
        status_rank = {
            "active": 0,
            "testing": 0,
            "in-progress": 0,
            "in design": 1,
            "planning": 1,
            "proposed": 2,
            "paused": 3,
            "deferred": 4,
            "superseded": 99,
        }

        # === PASS 1: Filter and identify epics ===
        spec_ids = [
            sid
            for sid in spec_ids
            if not (active_frs.get(sid) and "superseded" in active_frs[sid].status.lower())
        ]
        spec_ids_set = set(spec_ids)

        def get_status_rank(status: str) -> int:
            status_text = status.split(maxsplit=1)[-1].lower().strip() if status else ""
            return status_rank.get(status_text, 2)

        def is_epic(sid: str) -> bool:
            fr = active_frs.get(sid)
            return fr is not None and fr.priority.startswith("E")

        epics = [sid for sid in spec_ids if is_epic(sid)]
        epics_set = set(epics)

        # === PASS 2: Build epic-to-epic dependency graph first ===
        epic_deps_on_epics: dict[str, list[str]] = {eid: [] for eid in epics}
        spec_deps_by_epic: dict[str, list[str]] = {eid: [] for eid in epics}

        for epic_id in epics:
            fr = active_frs.get(epic_id)
            if not fr:
                continue
            for dep_id in fr.deps:
                if dep_id not in spec_ids_set:
                    continue  # Completed/external dep
                if dep_id in epics_set:
                    epic_deps_on_epics[epic_id].append(dep_id)
                else:
                    spec_deps_by_epic[epic_id].append(dep_id)

        # === PASS 3: Topological sort of epics ===
        epic_in_degree: dict[str, int] = {eid: 0 for eid in epics}
        epic_graph: dict[str, list[str]] = {eid: [] for eid in epics}

        for epic_id, dep_epics in epic_deps_on_epics.items():
            for dep_epic in dep_epics:
                if dep_epic in epics_set:
                    epic_graph[dep_epic].append(epic_id)
                    epic_in_degree[epic_id] += 1

        # Sort epics by priority, then status for tie-breaking
        def epic_sort_key(eid: str) -> tuple[int, int, str]:
            fr = active_frs.get(eid)
            pri = priority_rank.get(fr.priority if fr else "E3", 3)
            stat = get_status_rank(fr.status if fr else "")
            return (pri, stat, eid)

        # Topological sort of epics
        epic_queue = [eid for eid in epics if epic_in_degree[eid] == 0]
        ordered_epics: list[str] = []

        while epic_queue:
            epic_queue.sort(key=epic_sort_key)
            node = epic_queue.pop(0)
            ordered_epics.append(node)

            for neighbor in epic_graph[node]:
                epic_in_degree[neighbor] -= 1
                if epic_in_degree[neighbor] == 0:
                    epic_queue.append(neighbor)

        # Add any remaining epics (cycles)
        for eid in epics:
            if eid not in ordered_epics:
                ordered_epics.append(eid)

        # === PASS 3.5: Assign specs to earliest epic in topo order ===
        epic_sets: dict[str, list[str]] = {eid: [] for eid in epics}
        spec_to_epic: dict[str, str] = {}

        for epic_id in ordered_epics:  # Process in topological order!
            for spec_id in spec_deps_by_epic[epic_id]:
                if spec_id not in spec_to_epic:
                    spec_to_epic[spec_id] = epic_id
                    epic_sets[epic_id].append(spec_id)

        # Orphan specs (not part of any epic)
        orphan_specs = [
            sid for sid in spec_ids if sid not in epics_set and sid not in spec_to_epic
        ]

        # === PASS 4: Cluster-aware sorting within each epic set ===
        # Sort by: Priority → Total LOE (desc) → Clusters first → Topo within cluster
        def is_blocked(sid: str) -> bool:
            """Check if spec has incomplete (active) dependencies."""
            fr = active_frs.get(sid)
            if not fr or not fr.deps:
                return False
            return any(dep_id in spec_ids_set for dep_id in fr.deps)

        def get_spec_loe_hours(sid: str) -> int:
            """Get LOE in hours for a spec."""
            impl = self.datasets.get_impl(sid) if self.datasets else None
            if impl and impl.loe:
                hours, _ = _parse_loe_to_hours(impl.loe)
                return hours
            return 0

        def cluster_sort_specs(spec_list: list[str]) -> list[str]:
            """Sort specs using cluster-aware algorithm."""
            if not spec_list:
                return []

            spec_set = set(spec_list)

            # Build sibling dependency graph (deps within this epic set)
            sibling_deps: dict[str, set[str]] = {sid: set() for sid in spec_list}
            sibling_rdeps: dict[str, set[str]] = {sid: set() for sid in spec_list}
            for sid in spec_list:
                fr = active_frs.get(sid)
                if fr and fr.deps:
                    for dep_id in fr.deps:
                        if dep_id in spec_set:
                            sibling_deps[sid].add(dep_id)
                            sibling_rdeps[dep_id].add(sid)

            # Find connected components (clusters) via BFS
            visited: set[str] = set()
            clusters: list[list[str]] = []
            for sid in spec_list:
                if sid in visited:
                    continue
                cluster: list[str] = []
                queue = [sid]
                while queue:
                    current = queue.pop(0)
                    if current in visited:
                        continue
                    visited.add(current)
                    cluster.append(current)
                    for dep in sibling_deps.get(current, set()):
                        if dep not in visited:
                            queue.append(dep)
                    for rdep in sibling_rdeps.get(current, set()):
                        if rdep not in visited:
                            queue.append(rdep)
                clusters.append(cluster)

            # Separate orphans (single-node, no edges) from real clusters
            orphan_ids: set[str] = set()
            real_clusters: list[list[str]] = []
            for cluster in clusters:
                if len(cluster) == 1:
                    sid = cluster[0]
                    has_edges = bool(sibling_deps.get(sid)) or bool(sibling_rdeps.get(sid))
                    if not has_edges:
                        orphan_ids.add(sid)
                        continue
                real_clusters.append(cluster)

            # Calculate cluster properties for sorting
            def _has_active_spec(sids: list[str]) -> bool:
                """Check if any spec in the list has Active/Testing IMPL status."""
                for sid in sids:
                    impl = self.datasets.get_impl(sid) if self.datasets else None
                    if impl and ("Active" in impl.status or "Testing" in impl.status):
                        return True
                    fr = active_frs.get(sid)
                    if fr and "active" in fr.status.lower():
                        return True
                return False

            def cluster_sort_key(cluster: list[str]) -> tuple[int, int, int, int]:
                """(has_active, priority, -total_loe, is_orphan=0)

                Active clusters sort before non-active clusters.
                """
                total_loe = sum(get_spec_loe_hours(sid) for sid in cluster)
                # Best (lowest) priority in cluster
                best_pri = min(
                    priority_rank.get(active_frs[sid].priority if active_frs.get(sid) else "P3", 3)
                    for sid in cluster
                )
                # 0 = has active (sorts first), 1 = no active
                active = 0 if _has_active_spec(cluster) else 1
                return (active, best_pri, -total_loe, 0)

            def orphan_sort_key(sid: str) -> tuple[int, int, int, int, str]:
                """(has_active, priority, -loe, is_orphan=1, id)"""
                fr = active_frs.get(sid)
                pri = priority_rank.get(fr.priority if fr else "P3", 3)
                loe = get_spec_loe_hours(sid)
                impl = self.datasets.get_impl(sid) if self.datasets else None
                active = 0 if (impl and ("Active" in impl.status or "Testing" in impl.status)) else 1
                return (active, pri, -loe, 1, sid)

            # Sort clusters by priority, then total LOE descending
            real_clusters.sort(key=cluster_sort_key)

            # Topo-sort within each cluster (roots first)
            # Tie-breaker: status (Active first) → priority → ID
            def topo_sort_key(sid: str) -> tuple[int, int, str]:
                fr = active_frs.get(sid)
                # Active status = 0 (first), others = 1
                stat = 0 if (fr and "active" in fr.status.lower()) else 1
                pri = priority_rank.get(fr.priority if fr else "P3", 3)
                return (stat, pri, sid)

            def topo_sort(cluster: list[str]) -> list[str]:
                cluster_set = set(cluster)
                in_degree = {sid: 0 for sid in cluster}
                for sid in cluster:
                    for dep in sibling_deps.get(sid, set()):
                        if dep in cluster_set:
                            in_degree[sid] += 1
                queue = sorted([sid for sid in cluster if in_degree[sid] == 0], key=topo_sort_key)
                result: list[str] = []
                while queue:
                    current = queue.pop(0)
                    result.append(current)
                    for dependent in sibling_rdeps.get(current, set()):
                        if dependent in cluster_set:
                            in_degree[dependent] -= 1
                            if in_degree[dependent] == 0:
                                queue.append(dependent)
                                queue.sort(key=topo_sort_key)
                return result

            # Assemble: sorted clusters first, then orphans
            sorted_specs: list[str] = []
            for cluster in real_clusters:
                sorted_specs.extend(topo_sort(cluster))
            orphan_list = sorted(
                [sid for sid in spec_list if sid in orphan_ids], key=orphan_sort_key
            )
            sorted_specs.extend(orphan_list)

            return sorted_specs

        # Apply cluster-aware sorting to each epic's specs
        for epic_id in epic_sets:
            epic_sets[epic_id] = cluster_sort_specs(epic_sets[epic_id])

        # Sort orphan specs (not in any epic) the same way
        orphan_specs = cluster_sort_specs(orphan_specs)

        # === PASS 5: Assemble final ordered list ===
        ordered: list[str] = []

        for epic_id in ordered_epics:
            # Add this epic's spec dependencies first
            for spec_id in epic_sets[epic_id]:
                if spec_id not in ordered:
                    ordered.append(spec_id)
            # Then add the epic itself
            ordered.append(epic_id)

        # Add orphan specs (already sorted by cluster_sort_specs)
        for sid in orphan_specs:
            if sid not in ordered:
                ordered.append(sid)

        # Safety: add any remaining specs
        for sid in spec_ids:
            if sid not in ordered:
                ordered.append(sid)

        return ordered

    def _get_epic_scope(self, epic_id: str) -> set[str]:
        """Get the epic and all its transitive dependencies.

        Args:
            epic_id: The epic spec ID to start from

        Returns:
            Set of spec IDs including the epic and all dependencies
        """
        if not self.datasets:
            return {epic_id}

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

    def generate_nspec(self, output_path: Path) -> None:
        """Generate NSPEC.md file (Pass 2: Format pre-sorted datasets).

        Uses the ordered spec lists computed during validate() (Pass 1).

        Args:
            output_path: Where to write NSPEC.md
        """
        if not self.datasets:
            print("No datasets loaded. Run validate() first.")
            return

        if not self.ordered_active_specs:
            print("No ordered specs available. Run validate() first.")
            return

        # Use pre-computed ordered list from Pass 1
        ordered_specs = self.ordered_active_specs

        # Build markdown content with project status summary
        lines = [
            "# Praxis Core V2 - Active Nspec",
            "",
            "<!-- WARNING: GENERATED FILE - DO NOT EDIT MANUALLY -->",
            "<!-- Source: FR/IMPL docs in docs/frs/active/ and docs/impls/active/ -->",
            "<!-- To update: Edit FR/IMPL docs, then run `make nspec` -->",
            "",
            f"**Last Updated:** {self._get_date()}",
            f"**Total Active:** {len(ordered_specs)} specs",
            "",
        ]

        # Add project status summary
        summary_lines = render_project_status(
            datasets=self.datasets,
            docs_root=self.docs_root,
            show_velocity=True,
            show_recent_added=True,
            show_recent_completed=True,
            show_completion_stats=True,
            velocity_days=30,
            recent_hours=24,
            completed_hours=168,
        )
        lines.extend(summary_lines)

        lines.extend(
            [
                "---",
                "",
            ]
        )

        # Group by priority
        current_priority = None
        for spec_id in ordered_specs:
            fr = self.datasets.get_fr(spec_id)
            impl = self.datasets.get_impl(spec_id)

            if not fr:
                continue

            # Priority header
            if fr.priority != current_priority:
                current_priority = fr.priority
                priority = ALL_PRIORITIES.get(fr.priority)
                priority_emoji = priority.emoji if priority else "?"
                priority_name = PRIORITY_NAMES.get(fr.priority, "UNKNOWN")
                lines.append(f"## {priority_emoji} {fr.priority} - {priority_name}")
                lines.append("")

            # Spec entry
            status_emoji = fr.status.split()[0]  # Extract emoji
            loe = impl.effective_loe if impl else "~TBD"

            # Calculate overall progress if we have both AC and tasks
            progress_str = ""
            if impl and (fr.ac_total > 0 or impl.tasks_total > 0):
                overall = (fr.ac_completion_percent + impl.completion_percent) / 2
                progress_str = f" [{int(overall)}%]"

            lines.append(f"### Spec {spec_id}: {fr.title.split(': ', 1)[-1]}{progress_str}")
            lines.append(f"* **Status:** {status_emoji} {fr.status.split(maxsplit=1)[-1]}")
            lines.append(f"* **Priority:** {fr.priority}")
            lines.append(f"* **LOE:** {loe}")

            if fr.deps:
                deps_str = ", ".join(fr.deps)
                lines.append(f"* **Dependencies:** {deps_str}")

            # Progress breakdown if available
            if impl and (fr.ac_total > 0 or impl.tasks_total > 0):
                lines.append("* **Progress:**")
                if fr.ac_total > 0:
                    lines.append(
                        f"  - Acceptance Criteria: {fr.ac_completed}/{fr.ac_total} "
                        f"({fr.ac_completion_percent}%)"
                    )
                if impl.tasks_total > 0:
                    lines.append(
                        f"  - Implementation Tasks: {impl.tasks_completed}/{impl.tasks_total} "
                        f"({impl.completion_percent}%)"
                    )

            lines.append(f"* **FR:** [FR-{spec_id}]({fr.path.relative_to(self.docs_root)})")
            if impl:
                lines.append(
                    f"* **IMPL:** [IMPL-{spec_id}]({impl.path.relative_to(self.docs_root)})"
                )

            lines.append("")

        # Write file
        output_path.write_text("\n".join(lines))

    def generate_nspec_completed(self, output_path: Path) -> None:
        """Generate NSPEC_COMPLETED.md file (Pass 2: Format completed specs).

        Uses the ordered completed spec list computed during validate() (Pass 1).

        Args:
            output_path: Where to write NSPEC_COMPLETED.md
        """
        if not self.datasets:
            print("No datasets loaded. Run validate() first.")
            return

        if not self.ordered_completed_specs:
            # No completed specs - create empty file
            output_path.write_text(
                "# Praxis Core V2 - Completed Specs\n\n"
                "<!-- WARNING: GENERATED FILE - DO NOT EDIT MANUALLY -->\n"
                "<!-- Source: Completed FR/IMPL docs in docs/completed/ -->\n\n"
                "**No completed specs yet.**\n"
            )
            return

        lines = [
            "# Praxis Core V2 - Completed Specs",
            "",
            "<!-- WARNING: GENERATED FILE - DO NOT EDIT MANUALLY -->",
            "<!-- Source: Completed FR/IMPL docs in docs/completed/ -->",
            "",
            f"**Last Updated:** {self._get_date()}",
            f"**Total Completed:** {len(self.ordered_completed_specs)} specs",
            "",
            "---",
            "",
        ]

        # Add completed specs (simple list format)
        for spec_id in self.ordered_completed_specs:
            fr = self.datasets.get_fr(spec_id)
            impl = self.datasets.get_impl(spec_id)

            if not fr:
                continue

            lines.append(f"### Spec {spec_id}: {fr.title.split(': ', 1)[-1]}")
            lines.append(f"* **Status:** {FR_STATUSES[FRStatusCode.COMPLETED].full}")
            lines.append(f"* **Priority:** {fr.priority}")

            if impl and impl.effective_loe:
                lines.append(f"* **LOE:** {impl.effective_loe}")

            lines.append(f"* **FR:** [FR-{spec_id}]({fr.path.relative_to(self.docs_root)})")
            if impl:
                lines.append(
                    f"* **IMPL:** [IMPL-{spec_id}]({impl.path.relative_to(self.docs_root)})"
                )

            lines.append("")

        # Write file
        output_path.write_text("\n".join(lines))

    def show_progress(self, spec_id: str | None = None, show_all: bool = False) -> None:
        """Show task/AC progress for specs.

        Args:
            spec_id: Specific spec ID to show (or None for all)
            show_all: Show all specs with progress
        """
        if not self.datasets:
            print("No datasets loaded. Run validate() first.")
            return

        if spec_id:
            # Show specific spec
            self._show_spec_progress(spec_id)
        elif show_all:
            # Show all active specs
            for sid in sorted(self.datasets.active_frs.keys()):
                self._show_spec_progress(sid)
                print()
        else:
            # Show summary
            self._show_progress_summary()

    def _show_spec_progress(self, spec_id: str) -> None:
        """Show detailed progress for one spec."""
        fr = self.datasets.get_fr(spec_id)
        impl = self.datasets.get_impl(spec_id)

        if not fr:
            print(f"Spec {spec_id} not found")
            return

        print(f"Spec {spec_id}: {fr.title.split(': ', 1)[-1]}")

        # FR Acceptance Criteria
        if fr.ac_total > 0:
            print(
                f"|- FR-{spec_id} Acceptance Criteria: "
                f"{fr.ac_completion_percent}% ({fr.ac_completed}/{fr.ac_total})"
            )

            # Group by section
            sections = {}
            for ac in fr.acceptance_criteria:
                if ac.section not in sections:
                    sections[ac.section] = []
                sections[ac.section].append(ac)

            for section, acs in sections.items():
                completed = sum(1 for ac in acs if ac.completed)
                pct = int((completed / len(acs)) * 100) if acs else 0
                print(f"|  |- {section}: {pct}% ({completed}/{len(acs)})")
                for ac in acs:
                    print(f"|  |  {ac.emoji} {ac.description}")

        # IMPL Tasks
        if impl and impl.tasks_total > 0:
            print("|")
            print(
                f"\\- IMPL-{spec_id} Implementation Tasks: "
                f"{impl.completion_percent}% ({impl.tasks_completed}/{impl.tasks_total})"
            )

            # Group by section
            sections = {}
            for task in impl.tasks:
                if task.section not in sections:
                    sections[task.section] = []
                sections[task.section].append(task)

            for section, tasks in sections.items():
                completed = sum(1 for t in tasks if t.completed)
                pct = int((completed / len(tasks)) * 100) if tasks else 0
                print(f"   |- {section}: {pct}% ({completed}/{len(tasks)})")
                for task in tasks:
                    print(f"   |  {task.emoji} {task.description}")

        # Overall
        if impl and (fr.ac_total > 0 or impl.tasks_total > 0):
            overall = (fr.ac_completion_percent + impl.completion_percent) / 2
            print(f"\nOverall Spec Progress: {int(overall)}%")

    def _show_progress_summary(self) -> None:
        """Show summary progress across all specs."""
        stats = DatasetStats(self.datasets)
        progress = stats.overall_progress()

        print("Nspec Progress Summary")
        print("\nOverall Completion:")
        print(f"  Acceptance Criteria: {progress['ac_completion']}%")
        print(f"  Implementation Tasks: {progress['task_completion']}%")
        print(f"  Combined Average: {progress['overall_completion']}%")

        # Priority breakdown
        print("\nSpecs by Priority:")
        priority_breakdown = stats.priority_breakdown()
        for priority in ["P0", "P1", "P2", "P3"]:
            count = priority_breakdown[priority]
            print(f"  {priority}: {count} specs")

        # Near completion
        near_complete = stats.specs_near_completion(threshold=80)
        if near_complete:
            print("\nNear Completion (>=80%):")
            for sid in near_complete:
                fr = self.datasets.get_fr(sid)
                impl = self.datasets.get_impl(sid)
                if fr and impl:
                    overall = (fr.ac_completion_percent + impl.completion_percent) / 2
                    print(f"  Spec {sid}: {int(overall)}% - {fr.title.split(': ', 1)[-1]}")

        # Zero progress
        zero_progress = stats.specs_without_progress()
        if zero_progress:
            print(f"\nNot Started (0% progress): {len(zero_progress)} specs")

    def _get_date(self) -> str:
        """Get current date in YYYY-MM-DD format."""
        return datetime.now().strftime("%Y-%m-%d")
