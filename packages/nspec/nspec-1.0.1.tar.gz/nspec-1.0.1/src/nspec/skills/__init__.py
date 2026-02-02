"""Built-in Claude Code skills bundled with nspec.

Skills are markdown files that define Claude Code slash commands.
They are installed to `.claude/commands/` during `nspec init` or
via the `skills_install` MCP tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

# Header comment added to installed skill files to track nspec management
MANAGED_HEADER = "<!-- managed-by: nspec -->\n"


def get_builtin_skills() -> dict[str, str]:
    """Return all built-in skills as a dict of {name: content}.

    Names are the skill filenames without extension (e.g., "go", "loop").
    Content is the raw markdown text of the skill file.

    Returns:
        Dict mapping skill name to markdown content.
    """
    skills: dict[str, str] = {}
    skills_dir = resources.files("nspec.skills")

    for item in skills_dir.iterdir():
        if hasattr(item, "name") and item.name.endswith(".md"):
            name = item.name.removesuffix(".md")
            skills[name] = item.read_text(encoding="utf-8")

    return skills


def resolve_skills(
    sources: list[str],
    project_root: Path | None = None,
) -> dict[str, SkillInfo]:
    """Resolve skills from an ordered list of sources.

    Later sources override earlier ones by filename (merge semantics).

    Args:
        sources: Ordered list of source identifiers.
            - "builtin": skills bundled with the nspec package
            - Any other string: path to a directory of .md skill files
        project_root: Root directory for resolving relative paths.

    Returns:
        Dict mapping skill name to SkillInfo, in merge order.
    """
    resolved: dict[str, SkillInfo] = {}

    if not sources:
        sources = ["builtin"]
    elif "builtin" not in sources:
        sources = ["builtin", *sources]

    for source in sources:
        if source == "builtin":
            for name, content in get_builtin_skills().items():
                resolved[name] = SkillInfo(
                    name=name,
                    content=content,
                    source="builtin",
                    path=None,
                )
        else:
            # Filesystem source — resolve relative to project root
            source_path = Path(source).expanduser()
            if not source_path.is_absolute() and project_root:
                source_path = project_root / source_path
            if source_path.is_dir():
                for md_file in sorted(source_path.glob("*.md")):
                    name = md_file.stem
                    content = md_file.read_text(encoding="utf-8")
                    resolved[name] = SkillInfo(
                        name=name,
                        content=content,
                        source=str(source),
                        path=md_file,
                    )

    return resolved


def install_skills(
    project_root: Path,
    skills: dict[str, SkillInfo],
) -> list[Path]:
    """Write resolved skills to `.claude/commands/` in the project.

    Only writes files that are new or already managed by nspec (have the
    managed-by header). User-created files are left untouched.

    Args:
        project_root: Project root directory.
        skills: Resolved skills from resolve_skills().

    Returns:
        List of paths that were written.
    """
    commands_dir = project_root / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for name, info in skills.items():
        target = commands_dir / f"{name}.md"

        # Skip files not managed by nspec (user-created)
        if target.exists():
            existing = target.read_text(encoding="utf-8")
            if not existing.startswith(MANAGED_HEADER):
                continue

        # Write with managed-by header
        target.write_text(MANAGED_HEADER + info.content, encoding="utf-8")
        written.append(target)

    return written


@dataclass
class SkillInfo:
    """Metadata about a resolved skill."""

    name: str
    content: str
    source: str  # "builtin" or a path string
    path: Path | None  # None for builtin skills
