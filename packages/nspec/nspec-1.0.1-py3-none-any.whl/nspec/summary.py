"""Nspec summary generation toolkit.

Provides reusable methods for generating project status summaries:
- Newly added specs (last N hours)
- Recently completed specs
- Completion statistics by priority
- Combined project status display

Other tools can import and use these methods for reporting.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from nspec.datasets import NspecDatasets

# Exceptions expected during summary generation operations
_SummaryGenerationErrors = (RuntimeError, ValueError, KeyError, TypeError, OSError, IOError)


@dataclass
class CompletionStats:
    """Completion statistics for a priority level."""

    priority: str
    completed: int
    total: int
    completion_percent: int

    @property
    def emoji(self) -> str:
        """Get emoji for priority level."""
        from nspec.statuses import SPEC_PRIORITIES

        p = SPEC_PRIORITIES.get(self.priority)
        return p.emoji if p else "⚪"


@dataclass
class RecentSpec:
    """Recently added or completed spec."""

    spec_id: str
    title: str
    priority: str
    timestamp: datetime | None = None

    @property
    def display_time(self) -> str:
        """Human-readable time since timestamp."""
        if not self.timestamp:
            return "unknown"

        now = datetime.now(UTC)
        delta = now - self.timestamp
        hours = delta.total_seconds() / 3600

        if hours < 1:
            return "< 1h ago"
        elif hours < 24:
            return f"{int(hours)}h ago"
        else:
            days = int(hours / 24)
            return f"{days}d ago"


def get_recently_added(
    datasets: NspecDatasets,
    docs_root: Path,
    hours: int = 24,
) -> list[RecentSpec]:
    """Get specs added in the last N hours.

    Args:
        datasets: Loaded nspec datasets
        docs_root: Root docs directory
        hours: Time window in hours (default: 24)

    Returns:
        List of recently added specs, sorted by recency
    """
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    recent: list[RecentSpec] = []

    for spec_id, fr in datasets.active_frs.items():
        # Use file modification time as proxy for creation time
        try:
            mtime = fr.path.stat().st_mtime
            file_time = datetime.fromtimestamp(mtime, tz=UTC)

            if file_time >= cutoff:
                recent.append(
                    RecentSpec(
                        spec_id=spec_id,
                        title=fr.title.split(": ", 1)[-1],
                        priority=fr.priority,
                        timestamp=file_time,
                    )
                )
        except OSError:
            # Skip if file doesn't exist or can't be accessed
            continue

    # Sort by timestamp (most recent first)
    recent.sort(key=lambda s: s.timestamp or datetime.min, reverse=True)
    return recent


def get_recently_completed(
    datasets: NspecDatasets,
    docs_root: Path,
    hours: int = 168,  # 1 week default
) -> list[RecentSpec]:
    """Get specs completed in the last N hours.

    Args:
        datasets: Loaded nspec datasets
        docs_root: Root docs directory
        hours: Time window in hours (default: 168 = 1 week)

    Returns:
        List of recently completed specs, sorted by recency
    """
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    recent: list[RecentSpec] = []

    for spec_id, fr in datasets.completed_frs.items():
        # Use file modification time in completed directory
        try:
            mtime = fr.path.stat().st_mtime
            file_time = datetime.fromtimestamp(mtime, tz=UTC)

            if file_time >= cutoff:
                recent.append(
                    RecentSpec(
                        spec_id=spec_id,
                        title=fr.title.split(": ", 1)[-1],
                        priority=fr.priority,
                        timestamp=file_time,
                    )
                )
        except OSError:
            continue

    # Sort by timestamp (most recent first)
    recent.sort(key=lambda s: s.timestamp or datetime.min, reverse=True)
    return recent


def get_completion_stats_by_priority(
    datasets: NspecDatasets,
) -> list[CompletionStats]:
    """Calculate completion statistics grouped by priority.

    Args:
        datasets: Loaded nspec datasets

    Returns:
        List of CompletionStats for each priority (P0, P1, P2, P3)
    """
    # Count by priority
    priority_counts: dict[str, tuple[int, int]] = {
        "P0": (0, 0),
        "P1": (0, 0),
        "P2": (0, 0),
        "P3": (0, 0),
    }

    # Count completed
    for _spec_id, fr in datasets.completed_frs.items():
        priority = fr.priority
        if priority in priority_counts:
            completed, total = priority_counts[priority]
            priority_counts[priority] = (completed + 1, total + 1)

    # Count active (not completed)
    for _spec_id, fr in datasets.active_frs.items():
        priority = fr.priority
        if priority in priority_counts:
            completed, total = priority_counts[priority]
            priority_counts[priority] = (completed, total + 1)

    # Build stats
    stats: list[CompletionStats] = []
    for priority in ["P0", "P1", "P2", "P3"]:
        completed, total = priority_counts[priority]
        pct = int((completed / total) * 100) if total > 0 else 0
        stats.append(
            CompletionStats(
                priority=priority,
                completed=completed,
                total=total,
                completion_percent=pct,
            )
        )

    return stats


def render_project_status(
    datasets: NspecDatasets,
    docs_root: Path,
    *,
    show_velocity: bool = True,
    show_recent_added: bool = True,
    show_recent_completed: bool = True,
    show_completion_stats: bool = True,
    velocity_days: int = 30,
    recent_hours: int = 24,
    completed_hours: int = 168,
) -> list[str]:
    """Render complete project status summary.

    This is the main high-level method that other tools should use.

    Args:
        datasets: Loaded nspec datasets
        docs_root: Root docs directory
        show_velocity: Include velocity chart
        show_recent_added: Include newly added specs
        show_recent_completed: Include recently completed specs
        show_completion_stats: Include completion ratios by priority
        velocity_days: Days for velocity chart (default: 30)
        recent_hours: Hours for "newly added" (default: 24)
        completed_hours: Hours for "recently completed" (default: 168 = 1 week)

    Returns:
        List of lines to display (caller joins with \\n)
    """
    lines: list[str] = []

    # 1. Velocity Chart
    if show_velocity:
        from nspec.velocity import render_compact_chart

        try:
            velocity_lines = render_compact_chart(
                repo_path=docs_root.parent,  # Project root
                days=velocity_days,
            )
            lines.extend(velocity_lines)
            lines.append("")
        except _SummaryGenerationErrors:
            # If velocity fails, skip it silently
            pass

    # 2. Newly Added (last 24 hours)
    if show_recent_added:
        recent_added = get_recently_added(datasets, docs_root, hours=recent_hours)
        if recent_added:
            lines.append(f"📝 Newly Added (last {recent_hours}h):")
            for spec in recent_added[:5]:  # Limit to 5
                lines.append(f"  • Spec {spec.spec_id}: {spec.title} ({spec.display_time})")
            lines.append("")

    # 3. Newly Completed (last week)
    if show_recent_completed:
        recent_completed = get_recently_completed(datasets, docs_root, hours=completed_hours)
        if recent_completed:
            days = completed_hours // 24
            lines.append(f"✅ Recently Completed (last {days}d):")
            for spec in recent_completed[:5]:  # Limit to 5
                lines.append(f"  • Spec {spec.spec_id}: {spec.title} ({spec.display_time})")
            lines.append("")

    # 4. Current Totals by Priority
    if show_completion_stats:
        stats = get_completion_stats_by_priority(datasets)
        lines.append("📊 Current Totals:")
        for stat in stats:
            if stat.total > 0:  # Only show priorities with specs
                lines.append(
                    f"  {stat.emoji} {stat.priority}: {stat.completed} / {stat.total} "
                    f"specs completed ({stat.completion_percent}%)"
                )
        lines.append("")

    return lines
