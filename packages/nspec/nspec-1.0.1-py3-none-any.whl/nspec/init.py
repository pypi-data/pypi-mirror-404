"""Project initialization for nspec.

Detects the project stack (language, package manager, test framework, CI platform)
and scaffolds nspec configuration files, directory structure, and CI config.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nspec.config import NspecConfig

# FR template (matches docs/frs/active/TEMPLATE.md)
FR_TEMPLATE = """\
# FR-XXX: Title

**Priority:** 🟡 P2
**Status:** 🟡 Proposed
deps: []

## Overview
Description of the feature request.

## Acceptance Criteria
- [ ] AC-F1: First acceptance criterion
"""

# IMPL template (matches docs/impls/active/TEMPLATE.md)
IMPL_TEMPLATE = """\
# IMPL-XXX: Title

**Status:** 🟡 Planning
**LOE:** N/A

## Tasks
- [ ] 1. First task
"""

# Runner prefix mapping per detected stack
RUNNER_PREFIXES: dict[tuple[str, str], str] = {
    ("python", "poetry"): "poetry run nspec",
    ("python", "pip"): "python -m nspec",
    ("python", "hatch"): "hatch run nspec",
    ("python", "uv"): "uv run nspec",
    ("node", "npm"): "npx nspec",
    ("node", "yarn"): "npx nspec",
    ("node", "pnpm"): "npx nspec",
    ("rust", "cargo"): "cargo run --bin nspec --",
    ("go", "go"): "go run . --",
}

DEFAULT_RUNNER_PREFIX = "nspec"


@dataclass
class DetectedStack:
    """Result of project stack detection."""

    language: str = "unknown"
    package_manager: str = "unknown"
    test_framework: str = "unknown"
    ci_platform: str = "none"

    @property
    def runner_prefix(self) -> str:
        """Return the nspec runner prefix for this stack."""
        return RUNNER_PREFIXES.get((self.language, self.package_manager), DEFAULT_RUNNER_PREFIX)


def detect_stack(project_root: Path) -> DetectedStack:
    """Detect the project's language, package manager, test framework, and CI platform.

    Args:
        project_root: Root directory of the project to analyze.

    Returns:
        DetectedStack with detected values, or defaults for undetectable fields.
    """
    stack = DetectedStack()

    # Detect language and package manager
    _detect_language(project_root, stack)

    # Detect test framework
    _detect_test_framework(project_root, stack)

    # Detect CI platform
    _detect_ci_platform(project_root, stack)

    return stack


def _detect_language(project_root: Path, stack: DetectedStack) -> None:
    """Detect language and package manager from project files."""
    # Python — check pyproject.toml for build system
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        stack.language = "python"
        content = pyproject.read_text()

        if "poetry" in content.lower():
            stack.package_manager = "poetry"
        elif "hatchling" in content.lower() or "hatch" in content.lower():
            stack.package_manager = "hatch"
        elif (project_root / "uv.lock").exists():
            stack.package_manager = "uv"
        else:
            stack.package_manager = "pip"
        return

    # Python — setup.py / requirements.txt fallback
    if (project_root / "setup.py").exists() or (project_root / "requirements.txt").exists():
        stack.language = "python"
        if (project_root / "uv.lock").exists():
            stack.package_manager = "uv"
        else:
            stack.package_manager = "pip"
        return

    # Node.js
    package_json = project_root / "package.json"
    if package_json.exists():
        stack.language = "node"
        if (project_root / "pnpm-lock.yaml").exists():
            stack.package_manager = "pnpm"
        elif (project_root / "yarn.lock").exists():
            stack.package_manager = "yarn"
        else:
            stack.package_manager = "npm"
        return

    # Rust
    if (project_root / "Cargo.toml").exists():
        stack.language = "rust"
        stack.package_manager = "cargo"
        return

    # Go
    if (project_root / "go.mod").exists():
        stack.language = "go"
        stack.package_manager = "go"
        return


def _detect_test_framework(project_root: Path, stack: DetectedStack) -> None:
    """Detect test framework from project files."""
    if stack.language == "python":
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text().lower()
            if "pytest" in content:
                stack.test_framework = "pytest"
                return
            if "unittest" in content:
                stack.test_framework = "unittest"
                return
        # Check for test directories
        if (project_root / "tests").exists() or (project_root / "test").exists():
            stack.test_framework = "pytest"
            return
        stack.test_framework = "pytest"
        return

    if stack.language == "node":
        package_json = project_root / "package.json"
        if package_json.exists():
            content = package_json.read_text().lower()
            if "vitest" in content:
                stack.test_framework = "vitest"
                return
            if "jest" in content:
                stack.test_framework = "jest"
                return
            if "mocha" in content:
                stack.test_framework = "mocha"
                return
        stack.test_framework = "jest"
        return

    if stack.language == "rust":
        stack.test_framework = "cargo-test"
        return

    if stack.language == "go":
        stack.test_framework = "go-test"
        return


def _detect_ci_platform(project_root: Path, stack: DetectedStack) -> None:
    """Detect CI platform from project files."""
    if (project_root / ".github" / "workflows").exists():
        stack.ci_platform = "github"
        return

    if (project_root / "cloudbuild.yaml").exists() or (project_root / "cloudbuild.yml").exists():
        stack.ci_platform = "cloudbuild"
        return

    if (project_root / ".gitlab-ci.yml").exists():
        stack.ci_platform = "gitlab"
        return


def needs_init(project_root: Path) -> bool:
    """Check whether a project needs nspec initialization.

    Returns True when no config.toml is found AND no NSPEC_* env vars are set.

    Args:
        project_root: Root directory of the project.

    Returns:
        True if the project has no nspec configuration.
    """
    from nspec.config import CONFIG_REL_PATH

    config_file = project_root / CONFIG_REL_PATH
    if config_file.exists():
        return False

    # Check for any NSPEC_* environment variables
    nspec_env_vars = [k for k in os.environ if k.startswith("NSPEC_")]
    return not nspec_env_vars


def interactive_init(
    project_root: Path,
    interactive: bool = True,
) -> NspecConfig:
    """Run interactive (or non-interactive) initialization to choose config paths.

    Args:
        project_root: Root directory of the project.
        interactive: If True, prompt the user for path choices.
                    If False, return defaults immediately (for MCP/scripting).

    Returns:
        NspecConfig with the chosen paths.
    """
    from nspec.config import CONFIG_REL_PATH, DefaultsConfig, NspecConfig, PathsConfig

    config_file = project_root / CONFIG_REL_PATH

    if not interactive:
        return NspecConfig(
            paths=PathsConfig(),
            defaults=DefaultsConfig(),
            config_file=config_file,
        )

    # Show defaults and ask user
    defaults = PathsConfig()
    print("\nDefault directory layout:")
    print(f"  Feature requests: {defaults.feature_requests}")
    print(f"  Implementation:   {defaults.implementation}")
    print(f"  Completed:        {defaults.completed}")
    print(f"    Done subdir:       {defaults.completed_done}")
    print(f"    Superseded subdir: {defaults.completed_superseded}")
    print(f"    Rejected subdir:   {defaults.completed_rejected}")

    try:
        answer = input("\nAccept these defaults? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "y"

    if answer in ("", "y", "yes"):
        return NspecConfig(
            paths=defaults,
            defaults=DefaultsConfig(),
            config_file=config_file,
        )

    # Prompt for each path
    def _prompt(label: str, default: str) -> str:
        try:
            value = input(f"  {label} [{default}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            value = ""
        return value if value else default

    print("\nEnter custom directory names (press Enter for default):")
    paths = PathsConfig(
        feature_requests=_prompt("Feature requests dir", defaults.feature_requests),
        implementation=_prompt("Implementation dir", defaults.implementation),
        completed=_prompt("Completed dir", defaults.completed),
        completed_done=_prompt("Completed/done subdir", defaults.completed_done),
        completed_superseded=_prompt("Completed/superseded subdir", defaults.completed_superseded),
        completed_rejected=_prompt("Completed/rejected subdir", defaults.completed_rejected),
    )

    return NspecConfig(
        paths=paths,
        defaults=DefaultsConfig(),
        config_file=config_file,
    )


def scaffold_project(
    project_root: Path,
    docs_root: Path | None = None,
    stack: DetectedStack | None = None,
    ci_platform_override: str | None = None,
    force: bool = False,
    config: NspecConfig | None = None,
) -> list[Path]:
    """Scaffold a new nspec project structure.

    Creates config.toml, nspec.mk, docs directories with templates, and CI config.

    Args:
        project_root: Root directory of the project.
        docs_root: Docs directory path. Defaults to project_root / "docs".
        stack: Detected stack. If None, auto-detects.
        ci_platform_override: Override CI platform (github/cloudbuild/gitlab/none).
        force: If True, overwrite existing files.

    Returns:
        List of paths that were created.

    Raises:
        FileExistsError: If files already exist and force is False.
    """
    if stack is None:
        stack = detect_stack(project_root)

    if docs_root is None:
        docs_root = project_root / "docs"

    ci_platform = ci_platform_override if ci_platform_override else stack.ci_platform
    created: list[Path] = []

    # 1. .novabuilt.dev/nspec/config.toml
    from nspec.config import NspecConfig

    config_file = project_root / ".novabuilt.dev" / "nspec" / "config.toml"
    if config is not None:
        # Use caller-provided config (from interactive_init)
        config.config_file = config_file
        if config_file.exists() and not force:
            raise FileExistsError(f"File already exists: {config_file} (use --force to overwrite)")
        config.save()
    else:
        config = NspecConfig.scaffold(project_root, force=force)
    created.append(config_file)

    # 2. nspec.mk
    created.extend(
        _write_file(
            project_root / "nspec.mk",
            _generate_nspec_mk(stack),
            force=force,
        )
    )

    # 3. Docs directories — use paths from config
    fr_dir = docs_root / config.paths.feature_requests
    impl_dir = docs_root / config.paths.implementation
    completed_base = docs_root / config.paths.completed

    dirs_to_create = [
        fr_dir,
        impl_dir,
        completed_base / config.paths.completed_done,
        completed_base / config.paths.completed_superseded,
        completed_base / config.paths.completed_rejected,
    ]

    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        created.append(d)

    # 4. FR template
    created.extend(
        _write_file(
            fr_dir / "TEMPLATE.md",
            FR_TEMPLATE,
            force=force,
        )
    )

    # 5. IMPL template
    created.extend(
        _write_file(
            impl_dir / "TEMPLATE.md",
            IMPL_TEMPLATE,
            force=force,
        )
    )

    # 6. CI config
    if ci_platform and ci_platform != "none":
        ci_files = _generate_ci_config(ci_platform)
        for rel_path, content in ci_files:
            created.extend(
                _write_file(
                    project_root / rel_path,
                    content,
                    force=force,
                )
            )

    # 7. Install built-in skills to .claude/commands/
    from nspec.skills import install_skills, resolve_skills

    skills_sources = config.skills.sources if hasattr(config, "skills") else ["builtin"]
    resolved = resolve_skills(skills_sources, project_root=project_root)
    installed = install_skills(project_root, resolved)
    created.extend(installed)

    return created


def _write_file(path: Path, content: str, *, force: bool = False) -> list[Path]:
    """Write content to a file, creating parent directories as needed.

    Returns:
        List containing the path if written, empty list if skipped.

    Raises:
        FileExistsError: If file exists and force is False.
    """
    if path.exists() and not force:
        raise FileExistsError(f"File already exists: {path} (use --force to overwrite)")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return [path]


def _generate_nspec_mk(stack: DetectedStack) -> str:
    """Generate nspec.mk content for the given stack."""
    from nspec.templates.init.nspec_mk import render

    return render(runner_prefix=stack.runner_prefix)


def _generate_ci_config(platform: str) -> list[tuple[str, str]]:
    """Generate CI config file(s) for the given platform.

    Returns:
        List of (relative_path, content) tuples.
    """
    if platform == "github":
        from nspec.templates.init.ci_github import render

        return [(".github/workflows/nspec.yml", render())]

    if platform == "cloudbuild":
        from nspec.templates.init.ci_cloudbuild import render

        return [("cloudbuild.yaml", render())]

    if platform == "gitlab":
        from nspec.templates.init.ci_gitlab import render

        return [(".gitlab-ci.yml", render())]

    return []
