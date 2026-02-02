"""Dataset architecture for fRIMPL validation - Layer 2.

This module provides the four-dataset architecture that separates:
    - Active FRs (configurable, default: docs/frs/active/)
    - Active IMPLs (configurable, default: docs/impls/active/)
    - Completed FRs (configurable, default: docs/completed/done/)
    - Completed IMPLs (configurable, default: docs/completed/done/)

Directory paths are configurable via .novabuilt.dev/nspec/config.toml, environment variables,
or programmatically. See nspec.paths module for configuration details.

Each dataset is loaded with strict validation (Layer 1) before being
made available for cross-document validation (Layers 3-6).

Architecture:
    NspecDatasets - Container for all four datasets
    DatasetLoader - Loads and validates all documents
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from nspec.paths import NspecPaths, get_paths

logger = logging.getLogger("nspec")
from nspec.validators import (
    FRMetadata,
    FRValidator,
    IMPLMetadata,
    IMPLValidator,
)


@dataclass
class NspecDatasets:
    """Four datasets representing complete fRIMPL state.

    This separates active work (in progress) from completed work,
    and separates feature specs (FR) from implementation plans (IMPL).

    Design rationale:
        - Active vs Completed: Different validation rules apply
        - FR vs IMPL: Different document types, different purposes
        - Clean separation enables efficient querying and validation
    """

    active_frs: dict[str, FRMetadata]  # Spec ID → FR metadata
    active_impls: dict[str, IMPLMetadata]  # Spec ID → IMPL metadata
    completed_frs: dict[str, FRMetadata]  # Spec ID → FR metadata
    completed_impls: dict[str, IMPLMetadata]  # Spec ID → IMPL metadata

    def all_spec_ids(self) -> set[str]:
        """Get all spec IDs across all datasets.

        Returns:
            Set of spec IDs (both active and completed)
        """
        return set(self.active_frs.keys()) | set(self.completed_frs.keys())

    def get_fr(self, spec_id: str) -> FRMetadata | None:
        """Get FR from active or completed datasets.

        Args:
            spec_id: Spec ID like "001" or "060a"

        Returns:
            FRMetadata if found, None otherwise
        """
        return self.active_frs.get(spec_id) or self.completed_frs.get(spec_id)

    def get_impl(self, spec_id: str) -> IMPLMetadata | None:
        """Get IMPL from active or completed datasets.

        Args:
            spec_id: Spec ID like "001" or "060a"

        Returns:
            IMPLMetadata if found, None otherwise
        """
        return self.active_impls.get(spec_id) or self.completed_impls.get(spec_id)

    def is_active(self, spec_id: str) -> bool:
        """Check if spec is in active datasets.

        Args:
            spec_id: Spec ID to check

        Returns:
            True if FR is in active_frs
        """
        return spec_id in self.active_frs

    def is_completed(self, spec_id: str) -> bool:
        """Check if spec is in completed datasets.

        Args:
            spec_id: Spec ID to check

        Returns:
            True if FR is in completed_frs
        """
        return spec_id in self.completed_frs

    def active_spec_count(self) -> int:
        """Count of active specs."""
        return len(self.active_frs)

    def completed_spec_count(self) -> int:
        """Count of completed specs."""
        return len(self.completed_frs)

    def total_spec_count(self) -> int:
        """Total count of all specs."""
        return len(self.all_spec_ids())

    def get_active_specs(self) -> list[tuple[FRMetadata, IMPLMetadata | None]]:
        """Get all active specs with their FR and IMPL.

        Returns:
            List of (FR, IMPL) tuples, sorted by spec ID
        """
        specs = []
        for spec_id, fr in sorted(self.active_frs.items()):
            impl = self.active_impls.get(spec_id)
            specs.append((fr, impl))
        return specs

    def get_completed_specs(self) -> list[tuple[FRMetadata, IMPLMetadata | None]]:
        """Get all completed specs with their FR and IMPL.

        Returns:
            List of (FR, IMPL) tuples, sorted by spec ID
        """
        specs = []
        for spec_id, fr in sorted(self.completed_frs.items()):
            impl = self.completed_impls.get(spec_id)
            specs.append((fr, impl))
        return specs

    def calculate_loe_rollups(self) -> None:
        """Calculate LOE rollups from dependencies for all active specs.

        For each spec with dependencies:
        - calculated_loe_parallel = max of all dep sequential LOEs (longest dep)
        - calculated_loe_sequential = sum of all active dep sequential LOEs
        - effective_loe = calculated value if has deps, else manual value

        This modifies IMPLMetadata objects in place.
        """
        from .validators import _format_hours_to_loe

        for spec_id, fr in self.active_frs.items():
            impl = self.active_impls.get(spec_id)
            if not impl or not fr.deps:
                continue

            # Calculate from active (non-completed) dependencies only
            dep_parallel_total = 0  # Max of deps (parallel execution)
            dep_sequential_total = 0  # Sum of deps (sequential execution)

            for dep_id in fr.deps:
                # Skip completed dependencies - they don't add to remaining work
                if dep_id in self.completed_impls:
                    continue
                if dep_id in self.active_impls:
                    dep_impl = self.active_impls[dep_id]
                    # Use effective_loe_hours which may itself be calculated
                    dep_hours = dep_impl.effective_loe_hours
                    dep_parallel_total = max(dep_parallel_total, dep_hours)
                    dep_sequential_total += dep_hours

            # Store calculated values
            impl.calculated_loe_parallel = dep_parallel_total if dep_parallel_total > 0 else None
            impl.calculated_loe_sequential = (
                dep_sequential_total if dep_sequential_total > 0 else None
            )

            # Set effective LOE: use calculated if deps exist and have LOE, else manual
            if dep_sequential_total > 0:
                is_epic = fr.priority.startswith("E")
                if is_epic:
                    # Epics show parallel,sequential format
                    par_str = _format_hours_to_loe(dep_parallel_total)
                    seq_str = _format_hours_to_loe(dep_sequential_total)
                    impl.effective_loe = f"{par_str},{seq_str}"
                    impl.effective_loe_hours = dep_sequential_total
                else:
                    # Regular specs use sequential (sum of deps)
                    impl.effective_loe = _format_hours_to_loe(dep_sequential_total)
                    impl.effective_loe_hours = dep_sequential_total


class DatasetLoader:
    """Load and validate all four fRIMPL datasets.

    This class orchestrates Layer 1 validation (format checking) while
    loading documents into the four datasets. Any format violations
    cause immediate failure - no silent fixes.

    Usage:
        loader = DatasetLoader(docs_root=Path("docs"))
        datasets = loader.load()  # Raises ValueError on any invalid document
    """

    def __init__(
        self,
        docs_root: Path | None = None,
        active_frs_dir: Path | None = None,
        active_impls_dir: Path | None = None,
        completed_frs_dir: Path | None = None,
        completed_impls_dir: Path | None = None,
        paths_config: NspecPaths | None = None,
        project_root: Path | None = None,
    ):
        """Initialize dataset loader.

        Can be initialized in three ways:

        1. Standard mode (production with configuration):
            DatasetLoader(docs_root=Path("docs"))
            Loads paths from .novabuilt.dev/nspec/config.toml (if exists), environment variables,
            or built-in defaults. Directory structure is configurable.

        2. Custom mode (testing with explicit paths):
            DatasetLoader(
                active_frs_dir=Path("tests/nspec/test_case/active-fr"),
                active_impls_dir=Path("tests/nspec/test_case/active-impl"),
                ...
            )
            Allows arbitrary directory paths for black-box testing.

        3. Custom configuration mode:
            DatasetLoader(
                docs_root=Path("docs"),
                paths_config=NspecPaths(feature_requests_dir="specs", ...)
            )
            Uses custom path configuration instead of loading from file/env.

        Args:
            docs_root: Root docs directory (standard mode)
            active_frs_dir: Custom active FR directory (testing mode)
            active_impls_dir: Custom active IMPL directory (testing mode)
            completed_frs_dir: Custom completed FR directory (testing mode)
            completed_impls_dir: Custom completed IMPL directory (testing mode)
            paths_config: Custom paths configuration (overrides file/env config)
            project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)
        """
        if docs_root:
            # Standard mode - use configuration system
            paths = get_paths(docs_root, config=paths_config, project_root=project_root)
            self.active_frs_dir = paths.active_frs_dir
            self.active_impls_dir = paths.active_impls_dir
            self.completed_frs_dir = paths.completed_frs_dir
            self.completed_impls_dir = paths.completed_impls_dir
            self.superseded_dir = paths.superseded_dir
        else:
            # Custom mode (testing) - use explicitly provided paths
            self.active_frs_dir = active_frs_dir
            self.active_impls_dir = active_impls_dir
            self.completed_frs_dir = completed_frs_dir
            self.completed_impls_dir = completed_impls_dir
            self.superseded_dir = None

        self.fr_validator = FRValidator()
        self.impl_validator = IMPLValidator()

    def load(self) -> NspecDatasets:
        """Load all datasets with strict validation.

        This is Layer 2 validation - each document goes through
        Layer 1 (format validation) before being added to datasets.

        Returns:
            NspecDatasets with all four datasets populated

        Raises:
            ValueError: If any document fails validation
        """
        active_frs = (
            self._load_frs(self.active_frs_dir, require_completed=False)
            if self.active_frs_dir
            else {}
        )
        active_impls = (
            self._load_impls(self.active_impls_dir, require_completed=False)
            if self.active_impls_dir
            else {}
        )
        completed_frs = (
            self._load_frs(self.completed_frs_dir, require_completed=True)
            if self.completed_frs_dir
            else {}
        )
        completed_impls = (
            self._load_impls(self.completed_impls_dir, require_completed=True)
            if self.completed_impls_dir
            else {}
        )

        # Also load superseded specs - they count as "completed" for dependency purposes
        if self.superseded_dir and self.superseded_dir.exists():
            superseded_frs = self._load_frs(
                self.superseded_dir, require_completed=False, allow_superseded=True
            )
            superseded_impls = self._load_impls(
                self.superseded_dir, require_completed=False, allow_superseded=True
            )
            completed_frs.update(superseded_frs)
            completed_impls.update(superseded_impls)

        datasets = NspecDatasets(
            active_frs=active_frs,
            active_impls=active_impls,
            completed_frs=completed_frs,
            completed_impls=completed_impls,
        )

        # Calculate LOE rollups from dependencies (must be done after all loading)
        datasets.calculate_loe_rollups()

        return datasets

    def _load_frs(
        self,
        directory: Path,
        require_completed: bool = False,
        allow_superseded: bool = False,
    ) -> dict[str, FRMetadata]:
        """Load and validate all FRs in directory.

        Args:
            directory: Directory containing FR-*.md files
            require_completed: If True, enforce all FRs have ✅ Completed status
            allow_superseded: If True, allow 🔄 Superseded status as valid

        Returns:
            Dict mapping spec ID to FRMetadata

        Raises:
            ValueError: If any FR fails validation
        """
        if not directory or not directory.exists():
            logger.debug("_load_frs: directory missing or None: %s", directory)
            return {}

        fr_files = list(directory.glob("FR-*.md"))
        logger.debug("_load_frs: %s → %d files found", directory, len(fr_files))

        frs = {}
        for path in fr_files:
            # Skip template files
            if path.stem.upper() == "TEMPLATE":
                continue

            try:
                content = path.read_text()
                metadata = self.fr_validator.validate(
                    path,
                    content,
                    require_completed=require_completed,
                    allow_superseded=allow_superseded,
                )
                # Check for duplicate spec IDs (same ID, different slug)
                if metadata.spec_id in frs:
                    existing = frs[metadata.spec_id]
                    raise ValueError(
                        f"Duplicate spec ID {metadata.spec_id} detected:\n"
                        f"  - {existing.path.name}\n"
                        f"  - {path.name}\n"
                        f"Each spec ID must be unique. Delete one or renumber."
                    )
                frs[metadata.spec_id] = metadata
            except ValueError as e:
                logger.warning("_load_frs: validation failed for %s: %s", path.name, e)
                raise ValueError(
                    f"Failed to load FR from {path.relative_to(directory.parent)}:\n{e}"
                ) from None

        logger.debug("_load_frs: loaded %d FRs: %s", len(frs), sorted(frs.keys()))
        return frs

    def _load_impls(
        self,
        directory: Path,
        require_completed: bool = False,
        allow_superseded: bool = False,
    ) -> dict[str, IMPLMetadata]:
        """Load and validate all IMPLs in directory.

        Args:
            directory: Directory containing IMPL-*.md files
            require_completed: If True, enforce all IMPLs have ✅ Complete status
            allow_superseded: If True, allow ⚪ Hold status as valid (used for superseded)

        Returns:
            Dict mapping spec ID to IMPLMetadata

        Raises:
            ValueError: If any IMPL fails validation
        """
        if not directory or not directory.exists():
            logger.debug("_load_impls: directory missing or None: %s", directory)
            return {}

        impl_files = list(directory.glob("IMPL-*.md"))
        logger.debug("_load_impls: %s → %d files found", directory, len(impl_files))

        impls = {}
        for path in impl_files:
            # Skip template files
            if path.stem.upper() == "TEMPLATE":
                continue

            try:
                content = path.read_text()
                metadata = self.impl_validator.validate(
                    path,
                    content,
                    require_completed=require_completed,
                    allow_superseded=allow_superseded,
                )
                # Check for duplicate spec IDs (same ID, different slug)
                if metadata.spec_id in impls:
                    existing = impls[metadata.spec_id]
                    raise ValueError(
                        f"Duplicate spec ID {metadata.spec_id} detected:\n"
                        f"  - {existing.path.name}\n"
                        f"  - {path.name}\n"
                        f"Each spec ID must be unique. Delete one or renumber."
                    )
                impls[metadata.spec_id] = metadata
            except ValueError as e:
                logger.warning("_load_impls: validation failed for %s: %s", path.name, e)
                raise ValueError(
                    f"Failed to load IMPL from {path.relative_to(directory.parent)}:\n{e}"
                ) from None

        logger.debug("_load_impls: loaded %d IMPLs: %s", len(impls), sorted(impls.keys()))
        return impls


class DatasetStats:
    """Compute statistics across datasets.

    Useful for reporting and dashboard generation.
    """

    def __init__(self, datasets: NspecDatasets):
        """Initialize with datasets."""
        self.datasets = datasets

    def priority_breakdown(self) -> dict[str, int]:
        """Count active specs by priority.

        Returns:
            Dict like {"P0": 3, "P1": 15, "P2": 25, "P3": 5}
        """
        breakdown = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for fr in self.datasets.active_frs.values():
            breakdown[fr.priority] += 1
        return breakdown

    def status_breakdown(self) -> dict[str, int]:
        """Count active specs by status.

        Returns:
            Dict like {"🟡 Proposed": 20, "🟢 In Progress": 15, ...}
        """
        breakdown: dict[str, int] = {}
        for fr in self.datasets.active_frs.values():
            breakdown[fr.status] = breakdown.get(fr.status, 0) + 1
        return breakdown

    def overall_progress(self) -> dict[str, float]:
        """Calculate overall progress across all active specs.

        Returns:
            Dict with:
                - ac_completion: Average AC completion %
                - task_completion: Average task completion %
                - overall_completion: Combined average
        """
        if not self.datasets.active_frs:
            return {
                "ac_completion": 0.0,
                "task_completion": 0.0,
                "overall_completion": 0.0,
            }

        total_ac_completion = 0
        total_task_completion = 0
        spec_count = 0

        for spec_id, fr in self.datasets.active_frs.items():
            impl = self.datasets.active_impls.get(spec_id)

            total_ac_completion += fr.ac_completion_percent
            total_task_completion += impl.completion_percent if impl else 0
            spec_count += 1

        ac_avg = total_ac_completion / spec_count if spec_count > 0 else 0
        task_avg = total_task_completion / spec_count if spec_count > 0 else 0
        overall_avg = (ac_avg + task_avg) / 2

        return {
            "ac_completion": round(ac_avg, 1),
            "task_completion": round(task_avg, 1),
            "overall_completion": round(overall_avg, 1),
        }

    def dependency_graph(self) -> dict[str, list[str]]:
        """Build dependency graph for active specs.

        Returns:
            Dict mapping spec ID to list of dependency IDs
        """
        graph = {}
        for spec_id, fr in self.datasets.active_frs.items():
            graph[spec_id] = fr.deps
        return graph

    def specs_without_progress(self) -> list[str]:
        """Find active specs with 0% completion (no AC or tasks done).

        Returns:
            List of spec IDs
        """
        zero_progress = []
        for spec_id, fr in self.datasets.active_frs.items():
            impl = self.datasets.active_impls.get(spec_id)

            ac_done = fr.ac_completion_percent == 0
            tasks_done = (impl.completion_percent == 0) if impl else True

            if ac_done and tasks_done:
                zero_progress.append(spec_id)

        return sorted(zero_progress)

    def specs_near_completion(self, threshold: int = 80) -> list[str]:
        """Find active specs near completion.

        Args:
            threshold: Completion percentage threshold (default 80%)

        Returns:
            List of spec IDs with completion >= threshold
        """
        near_complete = []
        for spec_id, fr in self.datasets.active_frs.items():
            impl = self.datasets.active_impls.get(spec_id)

            if not impl:
                continue

            # Average of AC and task completion
            overall = (fr.ac_completion_percent + impl.completion_percent) / 2

            if overall >= threshold:
                near_complete.append(spec_id)

        return sorted(near_complete)
