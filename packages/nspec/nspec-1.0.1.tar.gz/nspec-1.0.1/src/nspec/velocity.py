"""Velocity chart rendering toolkit.

Provides GitHub-style activity visualization for nspec tools.
Adapted from arc/nspec_velocity.py for use as a reusable toolkit.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# Global default for activity window (overridable via NSPEC_ACTIVITY_DAYS env var)
DEFAULT_ACTIVITY_DAYS = int(os.environ.get("NSPEC_ACTIVITY_DAYS", "60"))


# =============================================================================
# 🚀 EMERGENT FUNCTION: Timeline metrics for reuse as Praxis handler
# Handler: praxis.handlers.metrics.timeline
# Inputs:  repo_path (Path)
# Outputs: TimelineMetrics dataclass
# =============================================================================


@dataclass(frozen=True, slots=True)
class TimelineMetrics:
    """Project timeline metrics - immutable value object.

    Designed for use as a Praxis handler output type.
    """

    start_date: str  # ISO format YYYY-MM-DD
    end_date: str  # ISO format YYYY-MM-DD
    total_days: int  # Calendar days since project start
    active_days: int  # Days with at least one commit
    total_commits: int
    total_loc: int
    loc_per_active_day: float
    loc_per_calendar_day: float
    commits_per_active_day: float

    def as_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_days": self.total_days,
            "active_days": self.active_days,
            "total_commits": self.total_commits,
            "total_loc": self.total_loc,
            "loc_per_active_day": round(self.loc_per_active_day, 2),
            "loc_per_calendar_day": round(self.loc_per_calendar_day, 2),
            "commits_per_active_day": round(self.commits_per_active_day, 2),
        }


def get_timeline_metrics(repo_path: Path) -> TimelineMetrics | None:
    """Gather project timeline metrics since first commit.

    🚀 EMERGENT: Candidate for praxis.handlers.metrics.timeline

    Fast, single-pass implementation:
    - One git log call for commit history
    - One find|wc call for LOC
    - Returns immutable dataclass

    Args:
        repo_path: Path to git repository

    Returns:
        TimelineMetrics or None if repo invalid
    """
    # Get first and last commit dates + daily counts in single git call
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "log", "--pretty=format:%ct", "--all"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None

    if not result.stdout.strip():
        return None

    # Parse all timestamps
    timestamps = []
    for line in result.stdout.strip().split("\n"):
        if line:
            try:
                timestamps.append(int(line))
            except ValueError:
                continue

    if not timestamps:
        return None

    # Calculate date range
    first_ts, last_ts = min(timestamps), max(timestamps)
    start_date = datetime.fromtimestamp(first_ts, tz=UTC).date()
    end_date = datetime.fromtimestamp(last_ts, tz=UTC).date()
    total_days = (end_date - start_date).days + 1

    # Count unique active days
    active_dates = {datetime.fromtimestamp(ts, tz=UTC).date() for ts in timestamps}
    active_days = len(active_dates)
    total_commits = len(timestamps)

    # Get LOC (reuse optimized function)
    total_loc = _count_source_lines(repo_path)

    # Calculate rates
    loc_per_active = total_loc / active_days if active_days > 0 else 0.0
    loc_per_calendar = total_loc / total_days if total_days > 0 else 0.0
    commits_per_active = total_commits / active_days if active_days > 0 else 0.0

    return TimelineMetrics(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        total_days=total_days,
        active_days=active_days,
        total_commits=total_commits,
        total_loc=total_loc,
        loc_per_active_day=loc_per_active,
        loc_per_calendar_day=loc_per_calendar,
        commits_per_active_day=commits_per_active,
    )


def iter_daily_loc_timeline(
    repo_path: Path, *, since_days: int | None = None
) -> Iterator[tuple[str, int, int]]:
    """Yield (date, commits, cumulative_loc_estimate) per active day.

    🚀 EMERGENT: Candidate for praxis.handlers.metrics.timeline_series

    Memory-efficient generator for large histories.
    LOC is estimated proportionally based on commit distribution.

    Args:
        repo_path: Path to git repository
        since_days: Limit to last N days (None = full history)

    Yields:
        (iso_date, commit_count, cumulative_loc_estimate) tuples
    """
    # Build git command
    cmd = ["git", "-C", str(repo_path), "log", "--pretty=format:%ct", "--all"]
    if since_days:
        since = datetime.now(UTC) - timedelta(days=since_days)
        cmd.extend(["--since", since.isoformat()])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return

    if not result.stdout.strip():
        return

    # Count commits per day
    daily_counts: Counter[str] = Counter()
    for line in result.stdout.strip().split("\n"):
        if line:
            try:
                ts = int(line)
                day = datetime.fromtimestamp(ts, tz=UTC).date().isoformat()
                daily_counts[day] += 1
            except ValueError:
                continue

    if not daily_counts:
        return

    # Get total LOC for proportional estimation
    total_loc = _count_source_lines(repo_path)
    total_commits = sum(daily_counts.values())

    # Yield sorted by date with cumulative LOC estimate
    cumulative_commits = 0
    for day in sorted(daily_counts.keys()):
        count = daily_counts[day]
        cumulative_commits += count
        # Estimate LOC proportional to commit progress
        loc_estimate = int(total_loc * cumulative_commits / total_commits)
        yield (day, count, loc_estimate)


@dataclass(frozen=True, slots=True)
class VelocityRun:
    """A period of accelerating development velocity.

    Represents a "hot streak" where LOC growth rate is increasing
    (positive second derivative of cumulative LOC).
    """

    start_date: str  # ISO format
    end_date: str  # ISO format
    days: int  # Duration in calendar days
    total_loc_delta: int  # LOC added during run
    peak_daily_loc: int  # Highest single-day LOC
    avg_daily_loc: float  # Average LOC/day during run
    acceleration: float  # Avg daily increase in velocity (LOC/day²)

    def as_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "days": self.days,
            "total_loc_delta": self.total_loc_delta,
            "peak_daily_loc": self.peak_daily_loc,
            "avg_daily_loc": round(self.avg_daily_loc, 1),
            "acceleration": round(self.acceleration, 2),
        }


def find_velocity_runs(
    repo_path: Path, *, min_run_days: int = 3, since_days: int | None = None
) -> list[VelocityRun]:
    """Find periods of accelerating development velocity.

    🚀 EMERGENT: Candidate for praxis.handlers.metrics.velocity_runs

    Identifies "hot streaks" where the derivative of LOC is increasing
    (velocity accelerating). A run ends when velocity decreases for
    consecutive days.

    Args:
        repo_path: Path to git repository
        min_run_days: Minimum days for a run to be counted (default: 3)
        since_days: Limit analysis to last N days (None = full history)

    Returns:
        List of VelocityRun sorted by total_loc_delta descending
    """
    # Collect daily data
    daily_data = list(iter_daily_loc_timeline(repo_path, since_days=since_days))
    if len(daily_data) < 3:
        return []

    # Calculate daily LOC deltas (first derivative)
    deltas: list[tuple[str, int]] = []  # (date, loc_delta)
    for i in range(1, len(daily_data)):
        date = daily_data[i][0]
        loc_delta = daily_data[i][2] - daily_data[i - 1][2]
        deltas.append((date, loc_delta))

    if len(deltas) < 2:
        return []

    # Find runs where velocity is increasing (positive second derivative)
    runs: list[VelocityRun] = []
    run_start_idx: int | None = None
    prev_delta = deltas[0][1]

    for i in range(1, len(deltas)):
        curr_delta = deltas[i][1]
        accelerating = curr_delta >= prev_delta and curr_delta > 0

        if accelerating:
            if run_start_idx is None:
                run_start_idx = i - 1  # Start from previous day
        else:
            # Run ended - capture if long enough
            if run_start_idx is not None:
                run_end_idx = i - 1
                run_days = run_end_idx - run_start_idx + 1

                if run_days >= min_run_days:
                    run_deltas = [deltas[j][1] for j in range(run_start_idx, run_end_idx + 1)]
                    total_loc = sum(run_deltas)
                    peak_loc = max(run_deltas)
                    avg_loc = total_loc / run_days

                    # Calculate acceleration (change in velocity per day)
                    if run_days > 1:
                        accel = (run_deltas[-1] - run_deltas[0]) / (run_days - 1)
                    else:
                        accel = 0.0

                    runs.append(
                        VelocityRun(
                            start_date=deltas[run_start_idx][0],
                            end_date=deltas[run_end_idx][0],
                            days=run_days,
                            total_loc_delta=total_loc,
                            peak_daily_loc=peak_loc,
                            avg_daily_loc=avg_loc,
                            acceleration=accel,
                        )
                    )

                run_start_idx = None

        prev_delta = curr_delta

    # Handle run that extends to end of data
    if run_start_idx is not None:
        run_end_idx = len(deltas) - 1
        run_days = run_end_idx - run_start_idx + 1

        if run_days >= min_run_days:
            run_deltas = [deltas[j][1] for j in range(run_start_idx, run_end_idx + 1)]
            total_loc = sum(run_deltas)
            peak_loc = max(run_deltas)
            avg_loc = total_loc / run_days
            accel = (run_deltas[-1] - run_deltas[0]) / (run_days - 1) if run_days > 1 else 0.0

            runs.append(
                VelocityRun(
                    start_date=deltas[run_start_idx][0],
                    end_date=deltas[run_end_idx][0],
                    days=run_days,
                    total_loc_delta=total_loc,
                    peak_daily_loc=peak_loc,
                    avg_daily_loc=avg_loc,
                    acceleration=accel,
                )
            )

    # Sort by total LOC delta descending
    return sorted(runs, key=lambda r: r.total_loc_delta, reverse=True)


def get_best_velocity_run(repo_path: Path, *, since_days: int | None = None) -> VelocityRun | None:
    """Get the single best velocity run (highest LOC output).

    🚀 EMERGENT: Candidate for praxis.handlers.metrics.best_run

    Args:
        repo_path: Path to git repository
        since_days: Limit analysis to last N days (None = full history)

    Returns:
        Best VelocityRun or None if no qualifying runs found
    """
    runs = find_velocity_runs(repo_path, min_run_days=2, since_days=since_days)
    return runs[0] if runs else None


# Cache settings
CACHE_DIR = Path("work")
CACHE_FILE = CACHE_DIR / ".velocity_cache.json"
CACHE_MAX_AGE_HOURS = 24


def _get_cache() -> dict | None:
    """Load cache if valid (less than CACHE_MAX_AGE_HOURS old)."""
    if not CACHE_FILE.exists():
        return None

    try:
        data = json.loads(CACHE_FILE.read_text())
        cached_time = datetime.fromisoformat(data.get("timestamp", ""))
        age = datetime.now(UTC) - cached_time
        if age.total_seconds() < CACHE_MAX_AGE_HOURS * 3600:
            return data
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    return None


def _save_cache(
    daily_counts: dict[str, int],
    total_loc: int,
    days: int,
    best_run: VelocityRun | None = None,
) -> None:
    """Save results to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "days": days,
        "daily_counts": daily_counts,
        "total_loc": total_loc,
        "best_run": best_run.as_dict() if best_run else None,
    }
    CACHE_FILE.write_text(json.dumps(data, indent=2))


def _get_cached_loc() -> int | None:
    """Get cached LOC if cache is valid (LOC doesn't depend on days parameter)."""
    cache = _get_cache()
    if cache and "total_loc" in cache:
        return cache["total_loc"]
    return None


def _get_cached_best_run(days: int) -> VelocityRun | None:
    """Get cached best run if cache is valid and days match."""
    cache = _get_cache()
    if cache and cache.get("days") == days and cache.get("best_run"):
        run_data = cache["best_run"]
        return VelocityRun(
            start_date=run_data["start_date"],
            end_date=run_data["end_date"],
            days=run_data["days"],
            total_loc_delta=run_data["total_loc_delta"],
            peak_daily_loc=run_data["peak_daily_loc"],
            avg_daily_loc=run_data["avg_daily_loc"],
            acceleration=run_data["acceleration"],
        )
    return None


def render_compact_chart(
    repo_path: Path | list[Path],
    days: int | None = None,
    use_color: bool = False,
    show_streak: bool = False,
    show_best_run: bool = False,
) -> list[str]:
    """Render a compact GitHub-style velocity chart.

    Args:
        repo_path: Path to git repository or list of repo paths (aggregated)
        days: Number of days to display (default: from DEFAULT_ACTIVITY_DAYS global)
        use_color: Use ANSI color codes (default: False)
        show_streak: Show streak stats and highlight streak days (default: False)
        show_best_run: Show best velocity run in stats (default: False)

    Returns:
        List of lines to display (caller joins with \\n)
    """
    # Use global default if not specified
    if days is None:
        days = DEFAULT_ACTIVITY_DAYS

    # Try to use cache first
    cache = _get_cache()
    best_run: VelocityRun | None = None
    cache_needs_update = False

    if cache and cache.get("days") == days:
        # Full cache hit - same days parameter
        daily_counts = cache["daily_counts"]
        total_loc = cache["total_loc"]
        # Get cached best run if available
        if show_best_run:
            best_run = _get_cached_best_run(days)
    else:
        cache_needs_update = True
        # Collect commit data from git (aggregate if multiple repos)
        if isinstance(repo_path, list):
            daily_counts = {}
            for path in repo_path:
                repo_counts = _collect_daily_commits(path, days)
                for day, count in repo_counts.items():
                    daily_counts[day] = daily_counts.get(day, 0) + count
        else:
            daily_counts = _collect_daily_commits(repo_path, days)

        # LOC doesn't depend on days - reuse cached value if available
        cached_loc = _get_cached_loc()
        if cached_loc is not None:
            total_loc = cached_loc
        elif isinstance(repo_path, list):
            total_loc = sum(_count_source_lines(path) for path in repo_path)
        else:
            total_loc = _count_source_lines(repo_path)

    # Compute best run if needed and not cached
    if show_best_run and best_run is None:
        cache_needs_update = True
        primary_path = repo_path[0] if isinstance(repo_path, list) else repo_path
        best_run = get_best_velocity_run(primary_path, since_days=days)

    # Save to cache if anything was computed
    if cache_needs_update:
        _save_cache(daily_counts, total_loc, days, best_run)

    if not daily_counts:
        return []

    lines: list[str] = []
    lines.append(f"📈 Activity (last {days} days):")
    lines.append("")

    # Calculate max streak for highlighting (only if showing streak)
    if show_streak:
        max_streak, streak_dates = _compute_max_streak(daily_counts)
    else:
        max_streak, streak_dates = 0, set()

    # Render calendar with streak highlighting
    _render_calendar(
        lines, daily_counts, window_days=days, use_color=use_color, streak_dates=streak_dates
    )

    # Summary stats
    total_commits = sum(daily_counts.values())
    active_days = len(daily_counts)

    lines.append("")
    loc_str = f"{total_loc:,}" if total_loc > 0 else "N/A"

    # Calculate LOC per day with industry ranking
    if active_days > 0 and total_loc > 0:
        loc_per_day_num = total_loc // active_days
        loc_per_day = f"{loc_per_day_num:,}"

        # Calculate team size equivalent (based on industry avg: 26.4 LOC/dev/day)
        # Reference: Mean across 29 US projects = 26.4 LOC/day per developer
        avg_loc_per_dev = 26.4
        team_size = loc_per_day_num / avg_loc_per_dev

        if team_size < 1.5:
            rank = "Solo Dev 👤"
        elif team_size < 2.5:
            rank = "Pair 👥"
        elif team_size < 5:
            rank = "Pizza Team 🍕"
        elif team_size < 10:
            rank = "Squad 🚀"
        elif team_size < 20:
            rank = "Team ⚡"
        elif team_size < 50:
            rank = "Department 🏢"
        elif team_size < 100:
            rank = "Division 🏭"
        else:
            rank = f"~{int(team_size)} devs 🌐"

        loc_metric = f"{loc_per_day} ({rank})"
    else:
        loc_metric = "N/A"

    # Build stats box
    stats_parts = [f"{total_commits} commits", f"{active_days} active days"]

    if show_streak:
        stats_parts.append(f"{max_streak}d max streak🔥")

    stats_parts.extend([f"{loc_str} LOC", f"LOC/Day: {loc_metric}"])

    stats_line = " • ".join(stats_parts)

    # Best velocity run line (if enabled)
    run_line = ""
    if show_best_run and best_run:
        run_line = (
            f"🚀 Best run: {best_run.start_date} → {best_run.end_date} "
            f"({best_run.days}d, +{best_run.total_loc_delta:,} LOC, "
            f"peak {best_run.peak_daily_loc:,}/day)"
        )

    # Calculate display width (emojis are 2 chars wide in terminal)
    def display_width(s: str) -> int:
        """Calculate terminal display width accounting for wide chars."""
        import unicodedata

        width = 0
        for ch in s:
            # Use East Asian Width property
            ea = unicodedata.east_asian_width(ch)
            if ea in ("F", "W") or ord(ch) >= 0x1F300:  # Fullwidth or Wide
                width += 2
            else:
                width += 1
        return width

    def pad_to_width(s: str, target: int) -> str:
        """Pad string to target display width."""
        current = display_width(s)
        return s + " " * (target - current)

    # Calculate box width based on display width
    stats_width = display_width(stats_line)
    run_width = display_width(run_line) if run_line else 0
    content_width = max(stats_width, run_width)
    box_width = content_width + 4  # 2 chars padding each side

    # Draw box
    lines.append(f"  ╭{'─' * box_width}╮")
    lines.append(f"  │  {pad_to_width(stats_line, content_width)}  │")
    if run_line:
        lines.append(f"  │  {pad_to_width(run_line, content_width)}  │")
    lines.append(f"  ╰{'─' * box_width}╯")

    return lines


def _collect_daily_commits(repo_path: Path, days: int) -> dict[str, int]:
    """Collect commit counts by day using git log.

    Args:
        repo_path: Path to git repository
        days: Number of days to look back

    Returns:
        Dict mapping ISO date string to commit count
    """
    now = datetime.now(UTC)
    since = now - timedelta(days=days)

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_path),
                "log",
                "--since",
                since.isoformat(),
                "--pretty=format:%ct",
                "--all",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return {}

    # Parse timestamps
    daily_counts: Counter[str] = Counter()
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            timestamp = int(line)
            dt = datetime.fromtimestamp(timestamp, tz=UTC)
            day_key = dt.date().isoformat()
            daily_counts[day_key] += 1
        except ValueError:
            continue

    return dict(daily_counts)


def _compute_day_streak(daily_counts: dict[str, int], now: datetime) -> int:
    """Compute current consecutive day streak.

    Args:
        daily_counts: Dict mapping ISO date string to commit count
        now: Current datetime

    Returns:
        Number of consecutive days with commits
    """
    streak = 0
    current = now.date()

    while daily_counts.get(current.isoformat(), 0) > 0:
        streak += 1
        current -= timedelta(days=1)

    return streak


def _compute_max_streak(daily_counts: dict[str, int]) -> tuple[int, set[str]]:
    """Compute maximum consecutive day streak in the dataset.

    Args:
        daily_counts: Dict mapping ISO date string to commit count

    Returns:
        Tuple of (longest consecutive days, set of ISO date strings in max streak)
    """
    if not daily_counts:
        return 0, set()

    # Get all dates with commits, sorted
    dates_with_commits = sorted(
        [datetime.fromisoformat(d).date() for d in daily_counts if daily_counts[d] > 0]
    )

    if not dates_with_commits:
        return 0, set()

    max_streak = 1
    current_streak = 1
    max_streak_start_idx = 0
    current_streak_start_idx = 0

    for i in range(1, len(dates_with_commits)):
        # Check if consecutive day
        if (dates_with_commits[i] - dates_with_commits[i - 1]).days == 1:
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
                max_streak_start_idx = current_streak_start_idx
        else:
            current_streak = 1
            current_streak_start_idx = i

    # Extract the dates in the max streak
    streak_dates = set(
        dates_with_commits[max_streak_start_idx + i].isoformat() for i in range(max_streak)
    )

    return max_streak, streak_dates


def _render_calendar(
    lines: list[str],
    daily_counts: dict[str, int],
    *,
    window_days: int = 30,
    use_color: bool = False,
    streak_dates: set[str] | None = None,
) -> None:
    """Render ASCII calendar with block shading for activity.

    Adapted from arc/nspec_velocity.py:_render_calendar().

    Args:
        lines: Output list to append calendar lines to
        daily_counts: Dict mapping ISO date to commit count
        window_days: Number of days to display
        use_color: Use ANSI color codes for month-based coloring
    """
    # Month color mapping (ANSI codes)
    month_colors = {
        1: "\033[94m",  # January - Blue
        2: "\033[96m",  # February - Cyan
        3: "\033[92m",  # March - Green
        4: "\033[93m",  # April - Yellow
        5: "\033[95m",  # May - Magenta
        6: "\033[91m",  # June - Red
        7: "\033[33m",  # July - Orange (dark yellow)
        8: "\033[32m",  # August - Dark green
        9: "\033[36m",  # September - Dark cyan
        10: "\033[35m",  # October - Dark magenta
        11: "\033[94m",  # November - Blue
        12: "\033[37m",  # December - White
    }
    month_names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }
    reset = "\033[0m"

    # Get date range
    if not daily_counts:
        return

    now = datetime.now(UTC).date()
    calendar_start = now - timedelta(days=window_days - 1)

    # Week header
    lines.append("      Mon Tue Wed Thu Fri Sat Sun")

    # Find the Monday before start
    days_since_monday = calendar_start.weekday()
    week_start = calendar_start - timedelta(days=days_since_monday)

    # Track months present in the calendar and their activity
    months_in_calendar = set()
    month_totals: dict[int, list[int]] = {}

    # Calculate relative thresholds from actual activity (5 levels)
    active_counts = [c for c in daily_counts.values() if c > 0]
    if active_counts:
        active_counts_sorted = sorted(active_counts)
        n = len(active_counts_sorted)
        # Percentile-based thresholds for 5 levels (20%, 40%, 60%, 80%)
        p20_idx = int(n * 0.20)
        p40_idx = int(n * 0.40)
        p60_idx = int(n * 0.60)
        p80_idx = int(n * 0.80)
        threshold_light = active_counts_sorted[p20_idx] if p20_idx < n else 1
        threshold_mild = active_counts_sorted[p40_idx] if p40_idx < n else 2
        threshold_medium = active_counts_sorted[p60_idx] if p60_idx < n else 3
        threshold_high = active_counts_sorted[p80_idx] if p80_idx < n else 4
    else:
        # Fallback to hardcoded if no data
        threshold_light = 1
        threshold_mild = 2
        threshold_medium = 4
        threshold_high = 7

    # Render weeks
    current = week_start
    week_num = 0
    while current <= now:
        week_line = f"  W{week_num + 1:02d} "
        for day_idx in range(7):
            day = current + timedelta(days=day_idx)
            day_str = day.isoformat()

            if day < calendar_start or day > now:
                week_line += "    "
            else:
                months_in_calendar.add(day.month)
                count = daily_counts.get(day_str, 0)

                # Track month totals
                if day.month not in month_totals:
                    month_totals[day.month] = []
                month_totals[day.month].append(count)

                color = month_colors[day.month] if use_color else ""
                is_streak_day = streak_dates and day_str in streak_dates

                if count == 0:
                    cell = "    "  # Blank space for no activity
                elif is_streak_day:
                    # Fire emoji for max streak days with month color background
                    cell = f" {color}🔥{reset} "
                elif count <= threshold_light:
                    cell = f" {color}░{reset}  "  # Light (25% fill)
                elif count <= threshold_mild:
                    cell = f" {color}▒{reset}  "  # Mild (50% fill)
                elif count <= threshold_medium:
                    cell = f" {color}▓{reset}  "  # Medium (75% fill)
                elif count <= threshold_high:
                    cell = f" {color}█{reset}  "  # High (100% fill)
                else:
                    cell = f" {color}█{reset}  "  # Very high (100% fill - brightest)
                week_line += cell

        lines.append(week_line)
        current += timedelta(days=7)
        week_num += 1

    lines.append("")
    lines.append("      Legend: (blank) none  ░ light  ▒ mild  ▓ medium  █ high/very high activity")

    # Add month color legend with average activity icon
    if use_color and months_in_calendar:
        month_legend = "      Months: "
        sorted_months = sorted(months_in_calendar)

        # Find most productive month
        month_averages = {}
        for month in sorted_months:
            month_counts = month_totals.get(month, [])
            month_averages[month] = sum(month_counts) / len(month_counts) if month_counts else 0
        most_productive_month = (
            max(month_averages, key=month_averages.get) if month_averages else None
        )

        month_parts = []
        bold = "\033[1m"
        for month in sorted_months:
            color = month_colors[month]
            # Calculate average for this month
            month_counts = month_totals.get(month, [])
            avg = sum(month_counts) / len(month_counts) if month_counts else 0

            # Pick icon based on average (5 levels)
            if avg == 0:
                icon = " "  # Blank for no activity
            elif avg <= threshold_light:
                icon = "░"
            elif avg <= threshold_mild:
                icon = "▒"
            elif avg <= threshold_medium:
                icon = "▓"
            else:
                icon = "█"

            # Bold the most productive month
            if month == most_productive_month:
                month_parts.append(f"{bold}{color}{icon} {month_names[month]}{reset}")
            else:
                month_parts.append(f"{color}{icon} {month_names[month]}{reset}")
        lines.append(month_legend + "  ".join(month_parts))


def _count_source_lines(repo_path: Path) -> int:
    """Count lines of source code using find + wc -l (fast).

    Counts files with extensions: .py, .java, .c, .cpp, .h, .go, .rs, .js, .ts, .tsx
    Only counts files in src/, tests/, and gateway/ directories
    Excludes: node_modules, venv, .git, __pycache__, build, dist, work directories

    Args:
        repo_path: Path to git repository

    Returns:
        Total lines of source code
    """
    # Only count code in these directories
    source_dirs = ["src", "tests", "gateway"]

    # Build a single find command with all extensions and exclusions
    # Using -regex for efficiency instead of multiple -name calls
    ext_pattern = r".*\.\(py\|java\|c\|cpp\|h\|hpp\|go\|rs\|js\|ts\|tsx\|jsx\)$"

    total_lines = 0
    for source_dir in source_dirs:
        source_path = repo_path / source_dir
        if not source_path.exists():
            continue

        # Single find | xargs wc -l command - much faster than Python file iteration
        # Excludes are handled via -path patterns
        cmd = (
            f"find {source_path} -type f -regex '{ext_pattern}' "
            f"-not -path '*/node_modules/*' "
            f"-not -path '*/.venv/*' "
            f"-not -path '*/venv/*' "
            f"-not -path '*/__pycache__/*' "
            f"-not -path '*/build/*' "
            f"-not -path '*/dist/*' "
            f"-not -path '*/work/*' "
            f"-not -path '*/.pytest_cache/*' "
            f"-not -path '*/htmlcov/*' "
            f"-print0 | xargs -0 wc -l 2>/dev/null | tail -1"
        )

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.stdout.strip():
                # Output is like "  12345 total" or just "  12345" for single file
                parts = result.stdout.strip().split()
                if parts:
                    total_lines += int(parts[0])
        except (subprocess.TimeoutExpired, ValueError):
            continue

    return total_lines
