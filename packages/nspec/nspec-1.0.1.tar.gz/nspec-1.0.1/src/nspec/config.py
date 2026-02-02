"""Configuration DAO for .novabuilt.dev/nspec/config.toml.

Single data access object that owns all reads and writes to the nspec
configuration file. Replaces scattered TOML parsing in paths.py, cli.py,
and init.py with a unified, typed interface.

Config file location: .novabuilt.dev/nspec/config.toml

Schema:
    [paths]
    feature_requests = "frs/active"
    implementation = "impls/active"
    completed = "completed"
    completed_done = "done"
    completed_superseded = "superseded"
    completed_rejected = "rejected"

    [defaults]
    epic = "001"

    [session]
    state_file = "state.json"

    [skills]
    sources = ["builtin"]

    [emojis]
    # fr_proposed = "🟡"
    # impl_paused = "⏳"
    # priority_p0 = "🔥"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Canonical config file location relative to project root
CONFIG_REL_PATH = ".novabuilt.dev/nspec/config.toml"


@dataclass
class PathsConfig:
    """Typed representation of [paths] section."""

    feature_requests: str = "frs/active"
    implementation: str = "impls/active"
    completed: str = "completed"
    completed_done: str = "done"
    completed_superseded: str = "superseded"
    completed_rejected: str = "rejected"


@dataclass
class SessionConfig:
    """Typed representation of [session] section."""

    state_file: str = "state.json"


@dataclass
class SkillsConfig:
    """Typed representation of [skills] section."""

    sources: list[str] = field(default_factory=lambda: ["builtin"])


@dataclass
class EmojisConfig:
    """Typed representation of [emojis] section.

    All fields are optional. When set, they override the default emoji
    for the corresponding status/priority/display element.
    """

    # FR statuses
    fr_proposed: str | None = None
    fr_in_design: str | None = None
    fr_active: str | None = None
    fr_completed: str | None = None
    fr_rejected: str | None = None
    fr_superseded: str | None = None
    fr_deferred: str | None = None

    # IMPL statuses
    impl_planning: str | None = None
    impl_active: str | None = None
    impl_testing: str | None = None
    impl_ready: str | None = None
    impl_paused: str | None = None
    impl_hold: str | None = None

    # Priorities
    priority_p0: str | None = None
    priority_p1: str | None = None
    priority_p2: str | None = None
    priority_p3: str | None = None

    # Dependency display
    dep_completed: str | None = None
    dep_active: str | None = None
    dep_proposed: str | None = None
    dep_rejected: str | None = None
    dep_superseded: str | None = None
    dep_testing: str | None = None
    dep_paused: str | None = None
    dep_unknown: str | None = None

    # Epic display
    epic_proposed: str | None = None
    epic_active: str | None = None
    epic_completed: str | None = None


@dataclass
class DefaultsConfig:
    """Typed representation of [defaults] section."""

    epic: str | None = None


@dataclass
class NspecConfig:
    """Single data access object for .novabuilt.dev/nspec/config.toml.

    Usage:
        # Load existing config
        config = NspecConfig.load(project_root)
        print(config.paths.feature_requests)
        print(config.defaults.epic)

        # Modify and persist
        config.defaults.epic = "002"
        config.save()

        # Scaffold new project
        config = NspecConfig.scaffold(project_root)
    """

    paths: PathsConfig = field(default_factory=PathsConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    skills: SkillsConfig = field(default_factory=SkillsConfig)
    emojis: EmojisConfig = field(default_factory=EmojisConfig)
    config_file: Path | None = field(default=None, repr=False)

    @classmethod
    def load(cls, project_root: Path | None = None) -> NspecConfig:
        """Load config from .novabuilt.dev/nspec/config.toml.

        Searches upward from project_root (or cwd) for the config file.
        Returns default config if no file is found.

        Args:
            project_root: Directory to start searching from.
                         If None, uses current working directory.

        Returns:
            NspecConfig with values from file, or defaults if not found.
        """
        if project_root is None:
            project_root = Path.cwd()

        config_file = _find_config_file(project_root)
        raw = _parse_toml(config_file) if config_file else {}

        paths_raw = raw.get("paths", {})
        defaults_raw = raw.get("defaults", {})
        session_raw = raw.get("session", {})
        skills_raw = raw.get("skills", {})
        emojis_raw = raw.get("emojis", {})

        paths = PathsConfig(
            feature_requests=paths_raw.get("feature_requests", PathsConfig.feature_requests),
            implementation=paths_raw.get("implementation", PathsConfig.implementation),
            completed=paths_raw.get("completed", PathsConfig.completed),
            completed_done=paths_raw.get("completed_done", PathsConfig.completed_done),
            completed_superseded=paths_raw.get(
                "completed_superseded", PathsConfig.completed_superseded
            ),
            completed_rejected=paths_raw.get("completed_rejected", PathsConfig.completed_rejected),
        )

        defaults = DefaultsConfig(
            epic=str(defaults_raw["epic"]) if "epic" in defaults_raw else None,
        )

        session = SessionConfig(
            state_file=session_raw.get("state_file", SessionConfig.state_file),
        )

        skills_sources = skills_raw.get("sources")
        skills = SkillsConfig(
            sources=skills_sources if isinstance(skills_sources, list) else ["builtin"],
        )

        # Build EmojisConfig — only set fields that are present in TOML
        emojis_kwargs = {}
        for field_name in EmojisConfig.__dataclass_fields__:
            if field_name in emojis_raw:
                emojis_kwargs[field_name] = str(emojis_raw[field_name])
        emojis = EmojisConfig(**emojis_kwargs)

        return cls(
            paths=paths,
            defaults=defaults,
            session=session,
            skills=skills,
            emojis=emojis,
            config_file=config_file,
        )

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Read an arbitrary value by section and key.

        Convenience method for callers that need ad-hoc access without
        knowing the typed fields. Prefer direct attribute access when possible.

        Returns the default if the section/key doesn't exist or if the
        value is None.

        Args:
            section: TOML section name (e.g., "defaults", "paths")
            key: Key within the section
            default: Fallback if not found or None

        Returns:
            The value, or default if not found or None.
        """
        section_obj = getattr(self, section, None)
        if section_obj is None:
            return default
        value = getattr(section_obj, key, None)
        if value is None:
            return default
        return value

    def save(self) -> None:
        """Persist current config state to disk.

        Writes to self.config_file. Raises ValueError if no config_file is set.
        """
        if self.config_file is None:
            raise ValueError("Cannot save: no config_file path set")

        content = self._to_toml()
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(content)

    @classmethod
    def scaffold(cls, project_root: Path, *, force: bool = False) -> NspecConfig:
        """Create default config.toml for a new project.

        Args:
            project_root: Project root directory.
            force: If True, overwrite existing file.

        Returns:
            NspecConfig with default values, saved to disk.

        Raises:
            FileExistsError: If config file exists and force is False.
        """
        config_file = project_root / CONFIG_REL_PATH
        if config_file.exists() and not force:
            raise FileExistsError(f"File already exists: {config_file} (use --force to overwrite)")

        config = cls(
            paths=PathsConfig(),
            defaults=DefaultsConfig(),
            config_file=config_file,
        )
        config.save()
        return config

    def _to_toml(self) -> str:
        """Serialize config to TOML string."""
        lines = [
            "# nspec configuration",
            f"# Location: {CONFIG_REL_PATH}",
            "# See: https://github.com/Novabuiltdevv/nspec",
            "",
            "[paths]",
        ]

        # Only write non-default values as active; write defaults as comments
        default_paths = PathsConfig()
        for field_name in (
            "feature_requests",
            "implementation",
            "completed",
            "completed_done",
            "completed_superseded",
            "completed_rejected",
        ):
            value = getattr(self.paths, field_name)
            default_value = getattr(default_paths, field_name)
            if value != default_value:
                lines.append(f'{field_name} = "{value}"')
            else:
                lines.append(f'# {field_name} = "{default_value}"')

        lines.extend(["", "[defaults]"])

        if self.defaults.epic is not None:
            lines.append(f'epic = "{self.defaults.epic}"')
        else:
            lines.append('# epic = "001"')

        lines.extend(["", "[session]"])
        default_session = SessionConfig()
        if self.session.state_file != default_session.state_file:
            lines.append(f'state_file = "{self.session.state_file}"')
        else:
            lines.append(f'# state_file = "{default_session.state_file}"')

        lines.extend(["", "[skills]"])
        default_skills = SkillsConfig()
        if self.skills.sources != default_skills.sources:
            sources_str = ", ".join(f'"{s}"' for s in self.skills.sources)
            lines.append(f"sources = [{sources_str}]")
        else:
            lines.append('# sources = ["builtin"]')

        lines.extend(["", "[emojis]"])
        lines.append("# Override any status/priority/display emoji below.")
        lines.append("# Missing keys use built-in defaults.")

        # Import defaults for commented-out reference
        from nspec.statuses import (
            _DEFAULT_DEP_EMOJIS,
            _DEFAULT_EPIC_EMOJIS,
            _DEFAULT_FR_EMOJIS,
            _DEFAULT_FR_TEXTS,
            _DEFAULT_IMPL_EMOJIS,
            _DEFAULT_IMPL_TEXTS,
            _DEFAULT_PRIORITY_EMOJIS,
        )

        # FR statuses
        _FR_KEY_MAP = {
            0: "fr_proposed",
            1: "fr_in_design",
            2: "fr_active",
            3: "fr_completed",
            4: "fr_rejected",
            5: "fr_superseded",
            6: "fr_deferred",
        }
        for code, key in _FR_KEY_MAP.items():
            value = getattr(self.emojis, key, None)
            default = _DEFAULT_FR_EMOJIS[code]
            label = _DEFAULT_FR_TEXTS[code]
            if value is not None:
                lines.append(f'{key} = "{value}"  # {label}')
            else:
                lines.append(f'# {key} = "{default}"  # {label}')

        # IMPL statuses
        _IMPL_KEY_MAP = {
            0: "impl_planning",
            1: "impl_active",
            2: "impl_testing",
            3: "impl_ready",
            4: "impl_paused",
            5: "impl_hold",
        }
        for code, key in _IMPL_KEY_MAP.items():
            value = getattr(self.emojis, key, None)
            default = _DEFAULT_IMPL_EMOJIS[code]
            label = _DEFAULT_IMPL_TEXTS[code]
            if value is not None:
                lines.append(f'{key} = "{value}"  # {label}')
            else:
                lines.append(f'# {key} = "{default}"  # {label}')

        # Priorities
        for pcode in ("P0", "P1", "P2", "P3"):
            key = f"priority_{pcode.lower()}"
            value = getattr(self.emojis, key, None)
            default = _DEFAULT_PRIORITY_EMOJIS[pcode]
            if value is not None:
                lines.append(f'{key} = "{value}"  # {pcode}')
            else:
                lines.append(f'# {key} = "{default}"  # {pcode}')

        # Dependency display
        _DEP_KEY_MAP = {
            "COMPLETED": "dep_completed",
            "ACTIVE": "dep_active",
            "PROPOSED": "dep_proposed",
            "REJECTED": "dep_rejected",
            "SUPERSEDED": "dep_superseded",
            "TESTING": "dep_testing",
            "PAUSED": "dep_paused",
            "UNKNOWN": "dep_unknown",
        }
        for attr, key in _DEP_KEY_MAP.items():
            value = getattr(self.emojis, key, None)
            default = _DEFAULT_DEP_EMOJIS[attr]
            if value is not None:
                lines.append(f'{key} = "{value}"  # dep {attr.lower()}')
            else:
                lines.append(f'# {key} = "{default}"  # dep {attr.lower()}')

        # Epic display
        _EPIC_KEY_MAP = {
            "PROPOSED": "epic_proposed",
            "ACTIVE": "epic_active",
            "COMPLETED": "epic_completed",
        }
        for attr, key in _EPIC_KEY_MAP.items():
            value = getattr(self.emojis, key, None)
            default = _DEFAULT_EPIC_EMOJIS[attr]
            if value is not None:
                lines.append(f'{key} = "{value}"  # epic {attr.lower()}')
            else:
                lines.append(f'# {key} = "{default}"  # epic {attr.lower()}')

        lines.append("")  # trailing newline
        return "\n".join(lines)


def _find_config_file(start_dir: Path) -> Path | None:
    """Search upward from start_dir for .novabuilt.dev/nspec/config.toml.

    Stops at git root or after 10 levels.

    Args:
        start_dir: Directory to start searching from.

    Returns:
        Path to config file if found, None otherwise.
    """
    search_dir = start_dir
    for _ in range(10):
        config_file = search_dir / CONFIG_REL_PATH
        if config_file.exists():
            return config_file

        if (search_dir / ".git").exists():
            break

        parent = search_dir.parent
        if parent == search_dir:
            break
        search_dir = parent

    return None


def _parse_toml(config_file: Path) -> dict[str, Any]:
    """Parse a TOML file into a dict.

    Args:
        config_file: Path to the TOML file.

    Returns:
        Parsed dict, or empty dict on error.
    """
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redefine]
        except ImportError:
            return {}

    try:
        with open(config_file, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}
