"""Centralized path configuration for nspec directories.

This module provides configurable paths for the nspec directory structure.
Instead of hardcoding paths like "frs/active", "impls/active",
and "completed" throughout the codebase, all code should use these
centralized path definitions.

Configuration priority (highest to lowest):
1. CLI arguments (--fr-dir, --impl-dir, etc.)
2. Environment variables (NSPEC_FR_DIR, NSPEC_IMPL_DIR, etc.)
3. .novabuilt.dev/nspec/config.toml (project config)
4. Built-in defaults

Default structure:
    docs/
    ├── {feature_requests_dir}/     # Active FR documents (default: frs/active)
    ├── {implementation_dir}/        # Active IMPL documents (default: impls/active)
    └── {completed_dir}/             # Completed work (default: completed)
        ├── done/                    # Completed FRs and IMPLs
        ├── superseded/              # Superseded specs
        └── rejected/                # Rejected specs

Example .novabuilt.dev/nspec/config.toml:
    [paths]
    feature_requests = "frs/active"
    implementation = "impls/active"
    completed = "completed"

    [defaults]
    epic = "001"  # Default epic for new specs
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nspec.config import NspecConfig

# =============================================================================
# Default Directory Names (can be overridden via environment or config)
# =============================================================================

# Environment variable names for configuration
ENV_FR_DIR = "NSPEC_FR_DIR"
ENV_IMPL_DIR = "NSPEC_IMPL_DIR"
ENV_COMPLETED_DIR = "NSPEC_COMPLETED_DIR"
ENV_COMPLETED_DONE_SUBDIR = "NSPEC_COMPLETED_DONE_SUBDIR"
ENV_COMPLETED_SUPERSEDED_SUBDIR = "NSPEC_COMPLETED_SUPERSEDED_SUBDIR"
ENV_COMPLETED_REJECTED_SUBDIR = "NSPEC_COMPLETED_REJECTED_SUBDIR"

# Default directory names
DEFAULT_FR_DIR = "frs/active"
DEFAULT_IMPL_DIR = "impls/active"
DEFAULT_COMPLETED_DIR = "completed"
DEFAULT_COMPLETED_DONE_SUBDIR = "done"
DEFAULT_COMPLETED_SUPERSEDED_SUBDIR = "superseded"
DEFAULT_COMPLETED_REJECTED_SUBDIR = "rejected"


def _get_config_value(
    env_var: str,
    default: str,
) -> str:
    """Get configuration value with priority: env var > default.

    Args:
        env_var: Environment variable name
        default: Default value (typically from NspecConfig)

    Returns:
        Configuration value from highest priority source
    """
    env_value = os.environ.get(env_var)
    if env_value is not None:
        return env_value
    return default


def get_toml_value(
    section: str, key: str, default: Any = None, project_root: Path | None = None
) -> Any:
    """Read an arbitrary value from .novabuilt.dev/nspec/config.toml.

    Delegates to NspecConfig.load().get().

    Args:
        section: TOML section name (e.g., "defaults", "paths")
        key: Key within the section
        default: Fallback if not found
        project_root: Project root to search from

    Returns:
        The value, or default if not found.
    """
    config = NspecConfig.load(project_root)
    return config.get(section, key, default)


@dataclass
class NspecPaths:
    """Configuration for nspec directory paths.

    This dataclass holds all the directory names used by the nspec system.
    It can be initialized with custom values or will use defaults from:
    1. Environment variables (highest priority after explicit values)
    2. config.toml file
    3. Built-in defaults

    Usage:
        # Use defaults (loads from config.toml if exists, then env vars, then defaults)
        paths = NspecPaths.from_config()

        # Use custom paths (CLI override)
        paths = NspecPaths(
            feature_requests_dir="feature-specs",
            implementation_dir="impl-plans",
        )

        # Get absolute paths relative to docs_root
        resolved = paths.resolve(docs_root=Path("docs"))
    """

    # Directory names (not full paths)
    feature_requests_dir: str
    implementation_dir: str
    completed_dir: str
    completed_done_subdir: str
    completed_superseded_subdir: str
    completed_rejected_subdir: str

    @classmethod
    def from_config(cls, project_root: Path | None = None) -> "NspecPaths":
        """Create NspecPaths from configuration sources.

        Loads configuration with priority:
        1. Environment variables
        2. config.toml file (via NspecConfig)
        3. Built-in defaults

        Args:
            project_root: Project root to search for config.toml.
                         If None, searches from current directory.

        Returns:
            NspecPaths with configuration loaded from available sources
        """
        config = NspecConfig.load(project_root)

        return cls(
            feature_requests_dir=_get_config_value(ENV_FR_DIR, config.paths.feature_requests),
            implementation_dir=_get_config_value(ENV_IMPL_DIR, config.paths.implementation),
            completed_dir=_get_config_value(ENV_COMPLETED_DIR, config.paths.completed),
            completed_done_subdir=_get_config_value(
                ENV_COMPLETED_DONE_SUBDIR, config.paths.completed_done
            ),
            completed_superseded_subdir=_get_config_value(
                ENV_COMPLETED_SUPERSEDED_SUBDIR, config.paths.completed_superseded
            ),
            completed_rejected_subdir=_get_config_value(
                ENV_COMPLETED_REJECTED_SUBDIR, config.paths.completed_rejected
            ),
        )

    def resolve(self, docs_root: Path) -> "ResolvedPaths":
        """Resolve directory names to absolute paths relative to docs_root.

        Args:
            docs_root: The root docs directory (e.g., Path("docs"))

        Returns:
            ResolvedPaths with all paths resolved relative to docs_root
        """
        completed_base = docs_root / self.completed_dir
        return ResolvedPaths(
            docs_root=docs_root,
            feature_requests=docs_root / self.feature_requests_dir,
            implementation=docs_root / self.implementation_dir,
            completed=completed_base,
            completed_done=completed_base / self.completed_done_subdir,
            completed_superseded=completed_base / self.completed_superseded_subdir,
            completed_rejected=completed_base / self.completed_rejected_subdir,
            config=self,
        )


@dataclass
class ResolvedPaths:
    """Resolved absolute paths for nspec directories.

    This is the primary interface for accessing nspec paths throughout
    the codebase. Get an instance via NspecPaths.resolve(docs_root).

    Attributes:
        docs_root: The root docs directory
        feature_requests: Directory for active FR documents
        implementation: Directory for active IMPL documents
        completed: Base directory for completed work
        completed_done: Subdirectory for completed specs
        completed_superseded: Subdirectory for superseded specs
        completed_rejected: Subdirectory for rejected specs
        config: The NspecPaths configuration used to create this
    """

    docs_root: Path
    feature_requests: Path
    implementation: Path
    completed: Path
    completed_done: Path
    completed_superseded: Path
    completed_rejected: Path
    config: NspecPaths

    # Aliases for backward compatibility and clarity
    @property
    def active_frs_dir(self) -> Path:
        """Alias for feature_requests (active FR directory)."""
        return self.feature_requests

    @property
    def active_impls_dir(self) -> Path:
        """Alias for implementation (active IMPL directory)."""
        return self.implementation

    @property
    def completed_frs_dir(self) -> Path:
        """Alias for completed_done (completed FR/IMPL directory)."""
        return self.completed_done

    @property
    def completed_impls_dir(self) -> Path:
        """Alias for completed_done (completed FR/IMPL are co-located)."""
        return self.completed_done

    @property
    def superseded_dir(self) -> Path:
        """Alias for completed_superseded."""
        return self.completed_superseded

    @property
    def rejected_dir(self) -> Path:
        """Alias for completed_rejected."""
        return self.completed_rejected


# =============================================================================
# Convenience Functions
# =============================================================================

# Module-level default configuration (can be replaced for testing)
_default_config: NspecPaths | None = None


def get_default_config(project_root: Path | None = None) -> NspecPaths:
    """Get the default NspecPaths configuration.

    This returns a singleton configuration that reads from:
    1. config.toml file (if exists)
    2. Environment variables
    3. Built-in defaults

    The configuration can be replaced via set_default_config() for testing.

    Args:
        project_root: Project root to search for config.toml.
                     If None, searches from current directory.

    Returns:
        NspecPaths with configuration loaded from available sources
    """
    global _default_config
    if _default_config is None:
        _default_config = NspecPaths.from_config(project_root)
    return _default_config


def set_default_config(config: NspecPaths | None) -> None:
    """Set the default NspecPaths configuration.

    Primarily used for testing to override the default paths.

    Args:
        config: New default configuration, or None to reset to defaults
    """
    global _default_config
    _default_config = config


def get_paths(
    docs_root: Path,
    config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> ResolvedPaths:
    """Get resolved paths for a docs root directory.

    This is the primary entry point for getting nspec paths throughout
    the codebase. It handles configuration loading and path resolution.

    Configuration priority:
    1. Explicit config parameter (if provided)
    2. Environment variables
    3. config.toml file
    4. Built-in defaults

    Args:
        docs_root: The root docs directory (e.g., Path("docs"))
        config: Optional custom configuration. If None, loads from sources.
        project_root: Project root for finding config.toml. If None, uses cwd.

    Returns:
        ResolvedPaths with all paths resolved relative to docs_root

    Example:
        # Load from config.toml (if exists) + env vars + defaults
        paths = get_paths(Path("docs"))
        fr_dir = paths.feature_requests  # Path("docs/frs/active")
        impl_dir = paths.implementation  # Path("docs/impls/active")

        # Override with custom config
        custom_config = NspecPaths(feature_requests_dir="specs")
        paths = get_paths(Path("docs"), config=custom_config)
    """
    if project_root is None:
        # Prefer the docs_root's parent (project root) over CWD to avoid
        # accidentally reading config.toml from whatever directory the process
        # happens to be launched in.
        project_root = docs_root.parent

    if config is None:
        config = get_default_config(project_root)
    return config.resolve(docs_root)


def reset_default_config() -> None:
    """Reset the default configuration to None (will be recreated on next access).

    Useful in tests to ensure environment variable changes are picked up.
    """
    global _default_config
    _default_config = None
