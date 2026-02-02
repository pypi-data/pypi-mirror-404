"""TUI operations wrapper for nspec CRUD functions.

Provides a high-level interface for TUI modals to perform nspec operations
with consistent error handling and result formatting.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class MoveResult:
    """Result of a move_spec operation."""

    success: bool
    spec_id: str
    target_epic: str
    removed_from: list[str]
    added_to: str | None
    priority_bumped: str | None
    error: str | None = None


def move_spec(
    spec_id: str,
    target_epic_id: str,
    docs_root: Path | None = None,
) -> MoveResult:
    """Move a spec to a target epic.

    Wraps crud.move_dependency with TUI-friendly error handling.

    Args:
        spec_id: Spec ID to move (e.g., "306")
        target_epic_id: Target epic ID (e.g., "297")
        docs_root: Path to docs/ directory (defaults to "docs")

    Returns:
        MoveResult with success status and details
    """
    from nspec.crud import move_dependency

    if docs_root is None:
        docs_root = Path("docs")

    try:
        result = move_dependency(spec_id, target_epic_id, docs_root)
        return MoveResult(
            success=True,
            spec_id=spec_id,
            target_epic=target_epic_id,
            removed_from=result.get("removed_from", []) or [],
            added_to=result.get("added_to"),
            priority_bumped=result.get("priority_bumped"),
        )
    except FileNotFoundError as e:
        return MoveResult(
            success=False,
            spec_id=spec_id,
            target_epic=target_epic_id,
            removed_from=[],
            added_to=None,
            priority_bumped=None,
            error=str(e),
        )
    except ValueError as e:
        return MoveResult(
            success=False,
            spec_id=spec_id,
            target_epic=target_epic_id,
            removed_from=[],
            added_to=None,
            priority_bumped=None,
            error=str(e),
        )
