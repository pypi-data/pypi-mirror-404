"""State management classes for the Nspec TUI.

Note: Directory paths are configurable via .novabuilt.dev/nspec/config.toml.
See nspec.paths module for configuration details.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from nspec.datasets import NspecDatasets
from nspec.paths import NspecPaths, get_paths
from nspec.validator import NspecValidator


class FollowModeState:
    """State for Claude Follow Mode - auto-tracks current spec."""

    def __init__(self, project_root: Path | None = None):
        """Initialize follow mode state."""
        self.project_root = project_root or Path(".")
        self.enabled = False
        self.current_spec_id: str | None = None
        self._last_state_mtime: float = 0.0

    @property
    def state_file(self) -> Path:
        """Path to consolidated state.json."""
        from nspec.session import StateDAO

        return StateDAO(self.project_root).state_path

    def read_current_spec(self) -> str | None:
        """Read current spec ID from state.json."""
        try:
            from nspec.session import StateDAO

            return StateDAO(self.project_root).get_spec_id()
        except Exception:
            return None

    def check_for_changes(self) -> bool:
        """Check if state.json changed. Returns True if spec changed."""
        try:
            sf = self.state_file
            if sf.exists():
                mtime = sf.stat().st_mtime
                if mtime > self._last_state_mtime:
                    self._last_state_mtime = mtime
                    new_spec = self.read_current_spec()
                    if new_spec != self.current_spec_id:
                        self.current_spec_id = new_spec
                        return True
        except Exception:
            pass
        return False


class NspecData:
    """Container for loaded nspec data."""

    def __init__(
        self,
        docs_root: Path | None = None,
        paths_config: NspecPaths | None = None,
        project_root: Path | None = None,
    ):
        """Initialize with docs root directory.

        Args:
            docs_root: Root docs directory (default: Path("docs"))
            paths_config: Optional custom paths configuration
            project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)
        """
        self.docs_root = docs_root or Path("docs")
        self.paths_config = paths_config
        self.project_root = project_root
        self.paths = get_paths(self.docs_root, config=paths_config, project_root=project_root)
        self.datasets: NspecDatasets | None = None
        self.ordered_specs: list[str] = []
        self.reverse_deps: dict[str, list[str]] = {}
        self.last_load_time: datetime | None = None
        self.error: str | None = None

    def load(self) -> bool:
        """Load nspec data. Returns True on success."""
        try:
            validator = NspecValidator(
                docs_root=self.docs_root,
                paths_config=self.paths_config,
                project_root=self.project_root,
            )
            success, errors = validator.validate()

            if not success:
                self.error = f"Validation failed: {len(errors)} errors"
                return False

            self.datasets = validator.datasets
            self.ordered_specs = validator.ordered_active_specs

            # Build reverse dependency map
            self.reverse_deps = {}
            if self.datasets:
                for spec_id, fr in self.datasets.active_frs.items():
                    for dep_id in fr.deps:
                        if dep_id not in self.reverse_deps:
                            self.reverse_deps[dep_id] = []
                        self.reverse_deps[dep_id].append(spec_id)

            self.last_load_time = datetime.now()
            self.error = None
            return True

        except ValueError as e:
            self.error = str(e)
            return False

    def get_mtime(self) -> float:
        """Get the latest modification time of FR/IMPL/completed directories."""
        latest = 0.0
        for directory in [
            self.paths.active_frs_dir,
            self.paths.active_impls_dir,
            self.paths.completed,
        ]:
            if directory.exists():
                # Check directory mtime (catches file additions/removals)
                dir_mtime = directory.stat().st_mtime
                if dir_mtime > latest:
                    latest = dir_mtime
                # Check individual file mtimes
                for path in directory.glob("**/*.md"):
                    mtime = path.stat().st_mtime
                    if mtime > latest:
                        latest = mtime
        return latest
