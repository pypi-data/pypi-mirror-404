"""Engineering metrics dashboard for VP/CEO visibility.

Displays velocity, quality, and codebase health metrics without nspec details.
Focused on demonstrating LLM-assisted development velocity.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Exceptions expected during metrics collection operations
_MetricsCollectionErrors = (
    RuntimeError,
    ValueError,
    KeyError,
    TypeError,
    OSError,
    IOError,
    json.JSONDecodeError,
)

# Activity window for metrics (overridable via env)
DEFAULT_METRICS_DAYS = int(os.environ.get("DEV_METRICS_DAYS", "60"))


@dataclass(frozen=True)
class VelocityMetrics:
    """Velocity metrics for the time period."""

    total_commits: int
    active_days: int
    calendar_days: int
    total_loc: int
    loc_per_day: int
    specs_completed: int
    specs_per_week: float
    best_run_start: str | None
    best_run_end: str | None
    best_run_days: int
    best_run_loc: int
    best_run_peak: int
    team_rank: str


@dataclass(frozen=True)
class ComplexityMetrics:
    """Code complexity metrics from radon."""

    cc_a_pct: float  # Low complexity %
    cc_b_pct: float  # Moderate complexity %
    cc_c_pct: float  # High complexity %
    cc_f_pct: float  # Very high complexity %
    avg_mi: float  # Average Maintainability Index
    mi_grade: str  # A/B/C/F grade
    hotspots: list[tuple[str, int, float]]  # (file, cc, mi)


@dataclass(frozen=True)
class QualityMetrics:
    """Test and quality metrics."""

    test_coverage: float
    coverage_tier: str
    pyright_errors: int
    lint_issues: int
    security_issues: int
    source_files: int
    test_files: int
    test_ratio: float
    doc_files: int


@dataclass(frozen=True)
class DoraMetrics:
    """DORA-style delivery metrics."""

    spec_velocity: float  # specs/week
    velocity_tier: str
    quality_gate_pass: float  # % of commits passing
    pass_tier: str
    change_failure_rate: float  # % of commits that are fixes
    cfr_tier: str


def _run_cmd(cmd: str | list[str], timeout: int = 30) -> str:
    """Run command and return output."""
    try:
        if isinstance(cmd, str):
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return ""


def _get_team_rank(loc_per_day: int) -> str:
    """Get team size equivalent rank based on LOC/day.

    Reference: Industry avg ~26.4 LOC/dev/day
    """
    avg_loc_per_dev = 26.4
    team_size = loc_per_day / avg_loc_per_dev

    if team_size < 1.5:
        return "Solo Dev 👤"
    elif team_size < 2.5:
        return "Pair 👥"
    elif team_size < 5:
        return "Pizza Team 🍕"
    elif team_size < 10:
        return "Squad 🚀"
    elif team_size < 20:
        return "Team ⚡"
    elif team_size < 50:
        return "Department 🏢"
    elif team_size < 100:
        return "Division 🏭"
    else:
        return f"~{int(team_size)} devs 🌐"


def collect_velocity_metrics(repo_path: Path, days: int = DEFAULT_METRICS_DAYS) -> VelocityMetrics:
    """Collect velocity metrics from git history."""
    since = datetime.now(UTC) - timedelta(days=days)

    # Get commits
    log_output = _run_cmd(
        f"git -C {repo_path} log --since='{since.isoformat()}' --pretty=format:'%ct' --all"
    )

    timestamps = []
    for line in log_output.split("\n"):
        if line.strip():
            try:
                timestamps.append(int(line.strip().strip("'")))
            except ValueError:
                continue

    total_commits = len(timestamps)
    active_dates = {datetime.fromtimestamp(ts, tz=UTC).date() for ts in timestamps}
    active_days = len(active_dates)

    # Count LOC
    total_loc = _count_source_lines(repo_path)
    loc_per_day = total_loc // active_days if active_days > 0 else 0

    # Specs completed (count commits with completion patterns)
    # Relies on conventional commits: "feat(FR-XXX): Complete" or "chore: Archive"
    completed_output = _run_cmd(
        f"git -C {repo_path} log --oneline --since='{since.isoformat()}' "
        f"| grep -iE 'complete.*FR-|FR-.*complete|archive.*(spec|spec)|chore:.*archive'"
    )
    specs_completed = len([line for line in completed_output.split("\n") if line.strip()])
    specs_per_week = (specs_completed / days) * 7 if days > 0 else 0

    # Best velocity run (from velocity module cache if available)
    best_run = _get_best_run(repo_path, days)

    return VelocityMetrics(
        total_commits=total_commits,
        active_days=active_days,
        calendar_days=days,
        total_loc=total_loc,
        loc_per_day=loc_per_day,
        specs_completed=specs_completed,
        specs_per_week=round(specs_per_week, 1),
        best_run_start=best_run.get("start"),
        best_run_end=best_run.get("end"),
        best_run_days=best_run.get("days", 0),
        best_run_loc=best_run.get("loc", 0),
        best_run_peak=best_run.get("peak", 0),
        team_rank=_get_team_rank(loc_per_day),
    )


def _get_best_run(repo_path: Path, days: int) -> dict[str, Any]:
    """Get best velocity run from cache or compute."""
    cache_file = repo_path / "work" / ".velocity_cache.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            if data.get("best_run"):
                run = data["best_run"]
                return {
                    "start": run.get("start_date"),
                    "end": run.get("end_date"),
                    "days": run.get("days", 0),
                    "loc": run.get("total_loc_delta", 0),
                    "peak": run.get("peak_daily_loc", 0),
                }
        except (json.JSONDecodeError, KeyError):
            pass
    return {}


def collect_complexity_metrics(repo_path: Path) -> ComplexityMetrics:
    """Collect complexity metrics using radon."""
    # Run radon cc for cyclomatic complexity
    cc_output = _run_cmd(
        f"docker run --rm -v {repo_path}:/app -w /app praxis-uber-base:latest "
        "radon cc src/ -a -nb --total-average -j 2>/dev/null || "
        f"radon cc {repo_path}/src -a -nb --total-average -j 2>/dev/null",
        timeout=60,
    )

    # Parse CC grades
    cc_grades = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    hotspots: list[tuple[str, int, float]] = []

    try:
        if cc_output:
            cc_data = json.loads(cc_output)
            for file_path, functions in cc_data.items():
                if isinstance(functions, list):
                    for func in functions:
                        grade = func.get("rank", "A")
                        cc_grades[grade] = cc_grades.get(grade, 0) + 1
                        # Track hotspots (C or worse)
                        if grade in ("C", "D", "E", "F"):
                            cc = func.get("complexity", 0)
                            name = func.get("name", "unknown")
                            hotspots.append((f"{file_path}:{name}", cc, 0.0))
    except (json.JSONDecodeError, TypeError):
        pass

    total_funcs = sum(cc_grades.values()) or 1
    cc_a_pct = round(cc_grades["A"] / total_funcs * 100, 1)
    cc_b_pct = round(cc_grades["B"] / total_funcs * 100, 1)
    cc_c_pct = round((cc_grades["C"] + cc_grades["D"]) / total_funcs * 100, 1)
    cc_f_pct = round((cc_grades["E"] + cc_grades["F"]) / total_funcs * 100, 1)

    # Run radon mi for maintainability
    mi_output = _run_cmd(
        f"docker run --rm -v {repo_path}:/app -w /app praxis-uber-base:latest "
        "radon mi src/ -nb -s -j 2>/dev/null || "
        f"radon mi {repo_path}/src -nb -s -j 2>/dev/null",
        timeout=60,
    )

    avg_mi = 0.0
    mi_count = 0
    try:
        if mi_output:
            mi_data = json.loads(mi_output)
            for file_path, file_mi in mi_data.items():
                if isinstance(file_mi, dict):
                    mi_val = file_mi.get("mi", 0)
                    avg_mi += mi_val
                    mi_count += 1
                    # Update hotspots with MI
                    for i, (hp_file, hp_cc, _) in enumerate(hotspots):
                        if hp_file.startswith(file_path):
                            hotspots[i] = (hp_file, hp_cc, mi_val)
    except (json.JSONDecodeError, TypeError):
        pass

    avg_mi = round(avg_mi / mi_count, 1) if mi_count > 0 else 0.0

    # MI grade
    if avg_mi >= 80:
        mi_grade = "A"
    elif avg_mi >= 60:
        mi_grade = "B"
    elif avg_mi >= 40:
        mi_grade = "C"
    else:
        mi_grade = "F"

    # Sort hotspots by CC descending
    hotspots.sort(key=lambda x: x[1], reverse=True)

    return ComplexityMetrics(
        cc_a_pct=cc_a_pct,
        cc_b_pct=cc_b_pct,
        cc_c_pct=cc_c_pct,
        cc_f_pct=cc_f_pct,
        avg_mi=avg_mi,
        mi_grade=mi_grade,
        hotspots=hotspots[:5],  # Top 5 hotspots
    )


def collect_quality_metrics(repo_path: Path) -> QualityMetrics:
    """Collect test coverage and quality metrics."""
    coverage = 0.0

    # Try to read from .coverage file using coverage report
    cov_file = repo_path / "work" / ".coverage"
    if cov_file.exists():
        try:
            # Run coverage report to get percentage
            result = _run_cmd(
                f"cd {repo_path} && coverage report "
                f"--data-file=work/.coverage 2>/dev/null | tail -1",
                timeout=30,
            )
            if result and "TOTAL" in result:
                # Parse "TOTAL ... XX%" format
                match = re.search(r"(\d+)%", result)
                if match:
                    coverage = float(match.group(1))
        except _MetricsCollectionErrors:
            pass

    # Fallback: try htmlcov
    if coverage == 0.0:
        htmlcov = repo_path / "work" / "htmlcov" / "index.html"
        if htmlcov.exists():
            try:
                content = htmlcov.read_text()
                match = re.search(r'class="pc_cov">(\d+)%</span>', content)
                if match:
                    coverage = float(match.group(1))
            except _MetricsCollectionErrors:
                pass

    # Fallback: try coverage.json
    if coverage == 0.0:
        cov_json = repo_path / "work" / "coverage.json"
        if cov_json.exists():
            try:
                data = json.loads(cov_json.read_text())
                coverage = data.get("totals", {}).get("percent_covered", 0.0)
            except _MetricsCollectionErrors:
                pass

    # Coverage tier
    if coverage >= 90:
        coverage_tier = "ELITE"
    elif coverage >= 80:
        coverage_tier = "HIGH"
    elif coverage >= 67:
        coverage_tier = "MEDIUM"
    else:
        coverage_tier = "LOW"

    # Count pyright errors (from cache or run)
    pyright_errors = 0
    pyright_output = _run_cmd("pyright --outputjson 2>/dev/null | head -1", timeout=120)
    if pyright_output:
        try:
            data = json.loads(pyright_output)
            pyright_errors = data.get("summary", {}).get("errorCount", 0)
        except json.JSONDecodeError:
            pass

    # Count files
    source_files = (
        len(list((repo_path / "src").rglob("*.py"))) if (repo_path / "src").exists() else 0
    )
    test_files = (
        len(list((repo_path / "tests").rglob("*.py"))) if (repo_path / "tests").exists() else 0
    )
    doc_files = (
        len(list((repo_path / "docs").rglob("*.md"))) if (repo_path / "docs").exists() else 0
    )

    test_ratio = round(test_files / source_files, 2) if source_files > 0 else 0.0

    return QualityMetrics(
        test_coverage=coverage,
        coverage_tier=coverage_tier,
        pyright_errors=pyright_errors,
        lint_issues=0,  # Assume clean from CI
        security_issues=0,  # Assume clean from CI
        source_files=source_files,
        test_files=test_files,
        test_ratio=test_ratio,
        doc_files=doc_files,
    )


def collect_nspec_health(repo_path: Path) -> dict[str, int]:
    """Collect nspec health metrics from NSPEC.md and completed directory."""
    nspec_path = repo_path / "NSPEC.md"
    completed_dir = repo_path / "docs" / "completed" / "done"

    active = 0
    p0 = 0
    in_design = 0

    if nspec_path.exists():
        content = nspec_path.read_text()
        # Extract "Total Active: XX specs" from header
        match = re.search(r"\*\*Total Active:\*\*\s*(\d+)", content)
        if match:
            active = int(match.group(1))

        # Count P0 specs from "<emoji> P0: X / Y specs"
        from nspec.statuses import FR_STATUSES, SPEC_PRIORITIES

        p0_emoji = re.escape(SPEC_PRIORITIES["P0"].emoji)
        p0_match = re.search(rf"{p0_emoji} P0:\s*(\d+)\s*/\s*(\d+)", content)
        if p0_match:
            completed_p0, total_p0 = int(p0_match.group(1)), int(p0_match.group(2))
            p0 = total_p0 - completed_p0  # Active P0s = total - completed

        # Count Proposed status
        proposed_full = FR_STATUSES[0].full
        in_design = content.count(proposed_full)

    # Count completed
    completed = 0
    if completed_dir.exists():
        completed = len(list(completed_dir.glob("FR-*.md")))

    return {
        "active": active,
        "p0": p0,
        "in_design": in_design,
        "completed": completed,
    }


def collect_tech_debt(repo_path: Path) -> dict[str, any]:
    """Collect technical debt indicators."""
    # Count complexity hotspots (C grade or worse from radon)
    hotspot_count = 0
    top_hotspots: list[str] = []

    cc_output = _run_cmd(
        f"radon cc {repo_path}/src -a -nb --total-average 2>/dev/null | "
        f"grep -E '^\\s+[CDEF]' | head -10",
        timeout=60,
    )
    if cc_output:
        hotspot_lines = [line.strip() for line in cc_output.split("\n") if line.strip()]
        hotspot_count = len(hotspot_lines)
        top_hotspots = hotspot_lines[:3]

    # Count skipped tests
    skipped_tests = 0
    skip_output = _run_cmd(
        f"grep -r '@pytest.mark.skip\\|@skip\\|pytest.skip' "
        f"{repo_path}/tests --include='*.py' 2>/dev/null | wc -l",
        timeout=30,
    )
    if skip_output:
        with contextlib.suppress(ValueError):
            skipped_tests = int(skip_output.strip())

    # Count TODO/FIXME comments
    todo_output = _run_cmd(
        f"grep -r 'TODO\\|FIXME\\|XXX\\|HACK' {repo_path}/src --include='*.py' 2>/dev/null | wc -l",
        timeout=30,
    )
    todo_count = 0
    if todo_output:
        with contextlib.suppress(ValueError):
            todo_count = int(todo_output.strip())

    return {
        "hotspot_count": hotspot_count,
        "top_hotspots": top_hotspots,
        "skipped_tests": skipped_tests,
        "todo_count": todo_count,
    }


def collect_dora_metrics(repo_path: Path, days: int = DEFAULT_METRICS_DAYS) -> DoraMetrics:
    """Collect DORA-style delivery metrics."""
    since = datetime.now(UTC) - timedelta(days=days)

    # Spec velocity (count commits with completion patterns)
    completed_output = _run_cmd(
        f"git -C {repo_path} log --oneline --since='{since.isoformat()}' "
        f"| grep -iE 'complete.*FR-|FR-.*complete|archive.*(spec|spec)|chore:.*archive'"
    )
    specs = len([line for line in completed_output.split("\n") if line.strip()])
    spec_velocity = round((specs / days) * 7, 1) if days > 0 else 0

    if spec_velocity >= 10:
        velocity_tier = "ELITE"
    elif spec_velocity >= 5:
        velocity_tier = "HIGH"
    elif spec_velocity >= 2:
        velocity_tier = "MEDIUM"
    else:
        velocity_tier = "LOW"

    # Quality gate pass rate (commits without "fix" in message)
    all_commits = _run_cmd(f"git -C {repo_path} log --since='{since.isoformat()}' --oneline")
    total = len([line for line in all_commits.split("\n") if line.strip()])
    fix_commits = len([line for line in all_commits.split("\n") if "fix" in line.lower()])
    passed = total - fix_commits

    quality_gate_pass = round((passed / total) * 100, 1) if total > 0 else 100.0
    if quality_gate_pass >= 95:
        pass_tier = "ELITE"
    elif quality_gate_pass >= 90:
        pass_tier = "HIGH"
    elif quality_gate_pass >= 80:
        pass_tier = "MEDIUM"
    else:
        pass_tier = "LOW"

    # Change failure rate (fix commits / total)
    cfr = round((fix_commits / total) * 100, 1) if total > 0 else 0.0
    if cfr <= 5:
        cfr_tier = "ELITE"
    elif cfr <= 10:
        cfr_tier = "HIGH"
    elif cfr <= 15:
        cfr_tier = "MEDIUM"
    else:
        cfr_tier = "LOW"

    return DoraMetrics(
        spec_velocity=spec_velocity,
        velocity_tier=velocity_tier,
        quality_gate_pass=quality_gate_pass,
        pass_tier=pass_tier,
        change_failure_rate=cfr,
        cfr_tier=cfr_tier,
    )


def _count_source_lines(repo_path: Path) -> int:
    """Count lines of source code."""
    source_dirs = ["src", "tests", "gateway"]
    ext_pattern = r".*\.\(py\|java\|c\|cpp\|h\|hpp\|go\|rs\|js\|ts\|tsx\|jsx\)$"

    total_lines = 0
    for source_dir in source_dirs:
        source_path = repo_path / source_dir
        if not source_path.exists():
            continue

        cmd = (
            f"find {source_path} -type f -regex '{ext_pattern}' "
            f"-not -path '*/node_modules/*' "
            f"-not -path '*/.venv/*' "
            f"-not -path '*/venv/*' "
            f"-not -path '*/__pycache__/*' "
            f"-not -path '*/build/*' "
            f"-not -path '*/dist/*' "
            f"-not -path '*/work/*' "
            f"-print0 | xargs -0 wc -l 2>/dev/null | tail -1"
        )

        result = _run_cmd(cmd, timeout=30)
        if result:
            parts = result.strip().split()
            if parts:
                with contextlib.suppress(ValueError):
                    total_lines += int(parts[0])

    return total_lines


def _tier_symbol(tier: str) -> str:
    """Get symbol for tier."""
    symbols = {
        "ELITE": "✓ ELITE ",
        "HIGH": "✓ HIGH  ",
        "MEDIUM": "○ MEDIUM",
        "LOW": "✗ LOW   ",
    }
    return symbols.get(tier, tier)


def render_dev_metrics(repo_path: Path = Path("."), days: int = DEFAULT_METRICS_DAYS) -> list[str]:
    """Render the full engineering metrics dashboard.

    Returns list of lines to print.
    """
    lines: list[str] = []

    # Collect all metrics
    velocity = collect_velocity_metrics(repo_path, days)
    quality = collect_quality_metrics(repo_path)
    dora = collect_dora_metrics(repo_path, days)

    # Header
    lines.append("")
    lines.append("╭" + "─" * 72 + "╮")
    lines.append("│" + "Engineering Metrics Dashboard".center(72) + "│")
    lines.append("│" + f"(LLM-Assisted Development • Last {days} days)".center(72) + "│")
    lines.append("╰" + "─" * 72 + "╯")
    lines.append("")

    # Velocity section
    lines.append("📈 VELOCITY METRICS")
    lines.append("─" * 74)

    col1 = f"  Total Commits:     {velocity.total_commits:,}"
    pct = velocity.active_days * 100 // velocity.calendar_days
    col2 = f"Active Days:      {velocity.active_days} of {velocity.calendar_days} ({pct}%)"
    lines.append(f"{col1:<37}│  {col2}")

    col1 = f"  Total LOC:         {velocity.total_loc:,}"
    col2 = f"LOC/Day:          {velocity.loc_per_day:,} ({velocity.team_rank})"
    lines.append(f"{col1:<37}│  {col2}")

    col1 = f"  Specs Completed:  {velocity.specs_completed}"
    col2 = f"Specs/Week:       {velocity.specs_per_week}"
    lines.append(f"{col1:<37}│  {col2}")

    if velocity.best_run_start:
        lines.append("")
        best_run_info = (
            f"  🚀 Best Run: {velocity.best_run_start} → {velocity.best_run_end} "
            f"({velocity.best_run_days}d, +{velocity.best_run_loc:,} LOC, "
            f"peak {velocity.best_run_peak:,}/day)"
        )
        lines.append(best_run_info)
    lines.append("")

    # Quality section
    lines.append("🔬 CODE QUALITY METRICS")
    lines.append("─" * 74)

    cov_status = _tier_symbol(quality.coverage_tier)
    cov_line = (
        f"  Test Coverage:     {quality.test_coverage:.1f}%  "
        f"(Target: 90%, Floor: 67%)  {cov_status}"
    )
    lines.append(cov_line)
    lines.append("")

    lines.append("  Source Files:      " + str(quality.source_files))
    lines.append("  Test Files:        " + str(quality.test_files))
    ratio_status = "✓" if quality.test_ratio >= 0.5 else "✗"
    lines.append(f"  Test/Source Ratio: {quality.test_ratio:.2f}  (Target: ≥0.5) {ratio_status}")
    lines.append(f"  Documentation:     {quality.doc_files} files")

    if quality.pyright_errors > 0:
        lines.append(f"  Type Errors:       {quality.pyright_errors} (pyright)")
    lines.append("")

    # Delivery section (simplified - removed misleading DORA heuristics)
    lines.append("📊 DELIVERY METRICS")
    lines.append("─" * 74)

    lines.append(
        f"  Spec Velocity:       {dora.spec_velocity}/week".ljust(35)
        + f"{_tier_symbol(dora.velocity_tier):<12} (Target: 10)"
    )
    lines.append(
        f"  Commits/Active Day:  {velocity.total_commits / velocity.active_days:.1f}".ljust(35)
        + "─"
    )
    lines.append(
        f"  Active Day Rate:     {velocity.active_days * 100 // velocity.calendar_days}%".ljust(35)
        + f"({velocity.active_days}/{velocity.calendar_days} days)"
    )
    lines.append("")

    # Nspec Health section
    nspec = collect_nspec_health(repo_path)
    lines.append("📋 NSPEC HEALTH")
    lines.append("─" * 74)
    lines.append(f"  Active Specs:      {nspec['active']:<8} P0 Critical: {nspec['p0']}")
    lines.append(f"  Completed (all):   {nspec['completed']:<8} In Design:   {nspec['in_design']}")
    lines.append("")

    # Technical Debt section
    debt = collect_tech_debt(repo_path)
    lines.append("🔧 TECHNICAL DEBT")
    lines.append("─" * 74)
    debt_line = (
        f"  Complexity Hotspots: {debt['hotspot_count']:<6} "
        f"Skipped Tests: {debt['skipped_tests']:<6} TODOs: {debt['todo_count']}"
    )
    lines.append(debt_line)
    if debt["top_hotspots"]:
        lines.append(f"  Worst: {debt['top_hotspots'][0][:60]}")
    lines.append("")

    # Summary footer - fixed width, no centering (emoji width varies)
    overall_tier = _compute_overall_tier(velocity, quality, dora)

    lines.append("╭" + "─" * 72 + "╮")
    # Build fixed-width columns
    col1 = f"Overall: {overall_tier}"
    col2 = f"Velocity: {velocity.team_rank}"
    col3 = f"Coverage: {quality.test_coverage:.1f}%"
    lines.append(f"│  {col1:<22} │  {col2:<22} │  {col3:<18}│")
    lines.append("╰" + "─" * 72 + "╯")
    lines.append("")

    return lines


def _compute_overall_tier(
    velocity: VelocityMetrics,
    quality: QualityMetrics,
    dora: DoraMetrics,
) -> str:
    """Compute overall health tier based on coverage and velocity."""
    tier_scores = {"ELITE": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

    # Only use meaningful metrics: coverage and spec velocity
    scores = [
        tier_scores.get(quality.coverage_tier, 2),
        tier_scores.get(dora.velocity_tier, 2),
    ]

    avg = sum(scores) / len(scores)

    if avg >= 3.5:
        return "ELITE 🏆"
    elif avg >= 2.5:
        return "HIGH ⭐"
    elif avg >= 1.5:
        return "MEDIUM"
    else:
        return "NEEDS ATTENTION ⚠️"


def print_dev_metrics(repo_path: Path = Path("."), days: int = DEFAULT_METRICS_DAYS) -> None:
    """Print the engineering metrics dashboard."""
    lines = render_dev_metrics(repo_path, days)
    for line in lines:
        print(line)
