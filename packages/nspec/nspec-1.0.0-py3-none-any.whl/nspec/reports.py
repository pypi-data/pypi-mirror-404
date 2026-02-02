"""
Nspec report data providers.

Each report function returns a JSON-serializable dict that can be:
1. Rendered by the TUI using Rich markup
2. Exported as JSON for external tools
3. Consumed by MCP tools

Report Structure:
{
    "title": "Report Title",
    "generated_at": "2026-01-20T12:00:00",
    "sections": [
        {
            "name": "Section Name",
            "type": "table|list|metric|chart",
            "data": { ... section-specific data ... }
        }
    ]
}
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .datasets import DatasetLoader, NspecDatasets


def _is_epic(fr) -> bool:
    """Check if FR is an epic based on priority."""
    return fr.priority.startswith("E")


def _is_done(status: str) -> bool:
    """Check if status indicates completion."""
    return "Ready" in status or "Completed" in status or "✅" in status or "🟠" in status


def _is_active(status: str) -> bool:
    """Check if status indicates active work."""
    return "Active" in status or "🔵" in status


@dataclass
class ReportContext:
    """Context for generating reports."""

    datasets: NspecDatasets
    docs_root: Path

    @classmethod
    def load(cls, docs_root: Path | None = None) -> ReportContext:
        """Load datasets and create context."""
        root = docs_root or Path("docs")
        loader = DatasetLoader(root)
        datasets = loader.load()
        return cls(datasets=datasets, docs_root=root)


def epic_summary_report(ctx: ReportContext) -> dict[str, Any]:
    """Generate epic summary report with spec counts and progress."""
    epics = []

    for spec_id, fr in ctx.datasets.active_frs.items():
        if _is_epic(fr):
            # Count specs in this epic (specs that have this epic in deps)
            children = [
                sid
                for sid, s in ctx.datasets.active_frs.items()
                if spec_id in s.deps and not _is_epic(s)
            ]

            # Calculate progress from IMPL status
            completed = 0
            active = 0
            for sid in children:
                impl = ctx.datasets.active_impls.get(sid)
                if impl:
                    if _is_done(impl.status):
                        completed += 1
                    elif _is_active(impl.status):
                        active += 1

            total = len(children)
            pct = (completed / total * 100) if total > 0 else 0

            epics.append(
                {
                    "id": spec_id,
                    "title": fr.title,
                    "priority": fr.priority,
                    "total": total,
                    "completed": completed,
                    "active": active,
                    "pending": total - completed - active,
                    "progress_pct": round(pct, 1),
                }
            )

    # Sort by priority rank
    priority_rank = {"E0": 0, "E1": 1, "E2": 2, "E3": 3}
    epics.sort(key=lambda x: priority_rank.get(x["priority"], 9))

    return {
        "title": "Epic Summary",
        "generated_at": datetime.now().isoformat(),
        "sections": [
            {
                "name": "Epics by Priority",
                "type": "table",
                "columns": ["ID", "Priority", "Title", "Progress", "Done", "Active", "Pending"],
                "data": [
                    {
                        "id": e["id"],
                        "priority": e["priority"],
                        "title": e["title"][:40] + "..." if len(e["title"]) > 40 else e["title"],
                        "progress": f"{e['progress_pct']}%",
                        "done": e["completed"],
                        "active": e["active"],
                        "pending": e["pending"],
                    }
                    for e in epics
                ],
            },
            {
                "name": "Summary Metrics",
                "type": "metrics",
                "data": {
                    "total_epics": len(epics),
                    "total_specs": sum(e["total"] for e in epics),
                    "completed_specs": sum(e["completed"] for e in epics),
                    "active_specs": sum(e["active"] for e in epics),
                },
            },
        ],
    }


def velocity_report(ctx: ReportContext) -> dict[str, Any]:
    """Generate velocity report based on completed specs."""
    # Group completed specs by priority
    by_priority: dict[str, list[dict]] = defaultdict(list)

    for spec_id, impl in ctx.datasets.active_impls.items():
        if _is_done(impl.status):
            fr = ctx.datasets.active_frs.get(spec_id)
            if fr and not _is_epic(fr):
                loe = fr.loe if hasattr(fr, "loe") else impl.loe or "N/A"
                by_priority[fr.priority].append(
                    {
                        "id": spec_id,
                        "title": fr.title[:50],
                        "loe": loe,
                    }
                )

    # Also include completed specs from completed_impls
    for spec_id, impl in ctx.datasets.completed_impls.items():
        fr = ctx.datasets.completed_frs.get(spec_id)
        if fr and not _is_epic(fr):
            loe = fr.loe if hasattr(fr, "loe") else impl.loe or "N/A"
            by_priority[fr.priority].append(
                {
                    "id": spec_id,
                    "title": fr.title[:50],
                    "loe": loe,
                }
            )

    # Calculate LOE totals
    def parse_loe(loe: str) -> float:
        """Parse LOE to days."""
        if not loe or loe == "N/A":
            return 0
        try:
            num = float(loe[:-1])
            unit = loe[-1].lower()
            if unit == "h":
                return num / 8
            elif unit == "w":
                return num * 5
            return num  # days
        except (ValueError, IndexError):
            return 0

    priority_totals = {}
    for priority, specs in by_priority.items():
        total_days = sum(parse_loe(s["loe"]) for s in specs)
        priority_totals[priority] = {
            "count": len(specs),
            "total_days": round(total_days, 1),
        }

    return {
        "title": "Velocity Report",
        "generated_at": datetime.now().isoformat(),
        "sections": [
            {
                "name": "Completed by Priority",
                "type": "table",
                "columns": ["Priority", "Specs", "Total LOE (days)"],
                "data": [
                    {"priority": p, "specs": v["count"], "loe": v["total_days"]}
                    for p, v in sorted(priority_totals.items())
                ],
            },
            {
                "name": "Recent Completions",
                "type": "list",
                "data": [
                    {"id": s["id"], "title": s["title"], "loe": s["loe"]}
                    for specs in by_priority.values()
                    for s in specs[:5]
                ][:15],
            },
        ],
    }


def blockers_report(ctx: ReportContext) -> dict[str, Any]:
    """Generate blockers report showing dependency chains."""
    blockers = []

    for spec_id, fr in ctx.datasets.active_frs.items():
        if _is_epic(fr):
            continue

        impl = ctx.datasets.active_impls.get(spec_id)
        if impl and _is_done(impl.status):  # Already done
            continue

        # Check dependencies
        blocking_deps = []
        for dep_id in fr.deps:
            dep_fr = ctx.datasets.active_frs.get(dep_id)
            if dep_fr and _is_epic(dep_fr):
                continue  # Skip epic deps
            dep_impl = ctx.datasets.active_impls.get(dep_id)
            if dep_impl and not _is_done(dep_impl.status):  # Not done
                blocking_deps.append(
                    {
                        "id": dep_id,
                        "title": dep_fr.title[:30] if dep_fr else "Unknown",
                        "status": dep_impl.status if dep_impl else "Unknown",
                    }
                )

        if blocking_deps:
            blockers.append(
                {
                    "id": spec_id,
                    "title": fr.title[:40],
                    "priority": fr.priority,
                    "blocked_by": blocking_deps,
                }
            )

    # Sort by priority
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    blockers.sort(key=lambda x: priority_rank.get(x["priority"], 9))

    return {
        "title": "Blockers Report",
        "generated_at": datetime.now().isoformat(),
        "sections": [
            {
                "name": "Blocked Specs",
                "type": "blockers",
                "data": blockers[:20],  # Top 20
            },
            {
                "name": "Summary",
                "type": "metrics",
                "data": {
                    "total_blocked": len(blockers),
                    "p0_blocked": sum(1 for b in blockers if b["priority"] == "P0"),
                    "p1_blocked": sum(1 for b in blockers if b["priority"] == "P1"),
                },
            },
        ],
    }


def status_matrix_report(ctx: ReportContext) -> dict[str, Any]:
    """Generate status matrix showing FR/IMPL status combinations."""
    matrix: dict[tuple[str, str], list[str]] = defaultdict(list)

    for spec_id, fr in ctx.datasets.active_frs.items():
        if _is_epic(fr):
            continue
        impl = ctx.datasets.active_impls.get(spec_id)
        fr_status = fr.status or "Unknown"
        impl_status = impl.status if impl else "Unknown"
        matrix[(fr_status, impl_status)].append(spec_id)

    # Convert to table format
    rows = []
    for (fr_status, impl_status), specs in sorted(matrix.items()):
        rows.append(
            {
                "fr_status": fr_status,
                "impl_status": impl_status,
                "count": len(specs),
                "specs": specs[:5],  # Sample
            }
        )

    return {
        "title": "Status Matrix",
        "generated_at": datetime.now().isoformat(),
        "sections": [
            {
                "name": "FR × IMPL Status Combinations",
                "type": "matrix",
                "data": rows,
            },
        ],
    }


# Registry of available reports
REPORTS = {
    "epic_summary": {
        "name": "Epic Summary",
        "description": "Overview of epics with progress tracking",
        "fn": epic_summary_report,
    },
    "velocity": {
        "name": "Velocity",
        "description": "Completed specs and LOE analysis",
        "fn": velocity_report,
    },
    "blockers": {
        "name": "Blockers",
        "description": "Specs blocked by dependencies",
        "fn": blockers_report,
    },
    "status_matrix": {
        "name": "Status Matrix",
        "description": "FR/IMPL status combinations",
        "fn": status_matrix_report,
    },
}


def generate_report(report_id: str, docs_root: Path | None = None) -> dict[str, Any]:
    """Generate a report by ID."""
    if report_id not in REPORTS:
        raise ValueError(f"Unknown report: {report_id}. Available: {list(REPORTS.keys())}")

    ctx = ReportContext.load(docs_root)
    return REPORTS[report_id]["fn"](ctx)


def list_reports() -> list[dict[str, str]]:
    """List available reports."""
    return [
        {"id": rid, "name": r["name"], "description": r["description"]}
        for rid, r in REPORTS.items()
    ]
