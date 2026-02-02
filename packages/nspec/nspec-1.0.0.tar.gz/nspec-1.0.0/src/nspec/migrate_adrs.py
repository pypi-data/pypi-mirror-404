#!/usr/bin/env python3
"""Migrate legacy ADR files to fRIMPL format (FR-9XX/IMPL-9XX).

This script:
1. Parses existing ADR-XXX.md files from docs/02-architecture/adrs/
2. Generates FR-9XX and IMPL-9XX pairs in fRIMPL format
3. Archives old ADR files to docs/02-architecture/adrs/archive/
4. Maps ADR-001 → FR-901, ADR-002 → FR-902, etc.

Note: Directory paths are configurable via .novabuilt.dev/nspec/config.toml.
See nspec.paths module for configuration details.

Usage:
    python src/tools/nspec/migrate_adrs.py [--dry-run] [--adr-number N]

Options:
    --dry-run: Preview changes without writing files
    --adr-number N: Migrate only ADR-N (default: migrate all)
"""

import argparse
import re
from datetime import date
from pathlib import Path

from nspec.paths import NspecPaths, get_paths

# Exceptions expected during ADR migration operations
_AdrMigrationErrors = (RuntimeError, ValueError, KeyError, TypeError, OSError, IOError)


def extract_title(content: str) -> str:
    """Extract title from first heading."""
    for line in content.split("\n")[:10]:
        if line.startswith("# "):
            title = line[2:].strip()
            # Remove ADR-XXX: prefix if present
            title = re.sub(r"^ADR-\d+:\s*", "", title)
            return title
    return "Unknown ADR"


def extract_sections(content: str) -> dict[str, str]:
    """Extract major sections from ADR content."""
    sections = {}
    current_section = None
    current_content = []

    for line in content.split("\n"):
        # Skip the title line
        if line.startswith("# "):
            continue

        # Check for level 2 headings
        if line.startswith("## "):
            # Save previous section
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()

            # Start new section
            current_section = line[3:].strip()
            current_content = []
        else:
            # Accumulate content
            if current_section:
                current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def generate_fr_content(adr_number: int, title: str, sections: dict[str, str]) -> str:
    """Generate FR-9XX content from ADR sections."""
    fr_number = 900 + adr_number

    # Extract key sections
    context = sections.get("Context", sections.get("Problem", ""))
    decision = sections.get("Decision", sections.get("Solution", ""))
    alternatives = sections.get("Alternatives Considered", sections.get("Alternatives", ""))
    consequences = sections.get("Consequences", sections.get("Impact", ""))

    # Build FR content
    fr_content = f"""# FR-{fr_number}: {title}

**Request ID:** FR-{fr_number}
**Type:** ADR
**Date:** {date.today().isoformat()}
**Status:** ✅ Completed
**Priority:** 🏗️ A2
**Implementation:** [IMPL-{fr_number}](../impls/active/IMPL-{fr_number}-{_slugify(title)}.md)

## Executive Summary

Architecture decision for {title.lower()}.

## Problem Statement

{context if context else "See original ADR for full context."}

## Decision

{decision if decision else "See original ADR for decision rationale."}

## Alternatives Considered

{alternatives if alternatives else "See original ADR for alternatives analysis."}

## Consequences

{consequences if consequences else "See original ADR for consequences."}

## Implementation Status

**Status:** ✅ Implemented

This architecture decision was implemented in praxis-v1/v2 and is now documented
in fRIMPL format for consistency with the unified nspec system.

Original ADR archived at:
`docs/02-architecture/adrs/archive/ADR-{adr_number:03d}-{_slugify(title)}.md`

---

**Note:** This FR was migrated from legacy ADR-{adr_number:03d} format
on {date.today().isoformat()}.
For historical context, see the original ADR file in the archive directory.
"""

    return fr_content


def generate_impl_content(adr_number: int, title: str) -> str:
    """Generate IMPL-9XX content (retrospective since ADR already implemented)."""
    fr_number = 900 + adr_number

    impl_content = f"""# Implementation Plan: {title}

**Implementation ID:** IMPL-{fr_number}
**Type:** ADR
**Feature Request:** [FR-{fr_number}](../frs/active/FR-{fr_number}-{_slugify(title)}.md)
**Status:** ✅ Completed
**LOE:** N/A (retrospective)
**Created:** {date.today().isoformat()}

## Implementation Summary

**Status:** ✅ Completed (Retrospective)

This architecture decision was implemented in praxis-v1/v2. This IMPL document
serves as a retrospective record for the unified fRIMPL nspec system.

## Historical Context

This ADR was originally documented as ADR-{adr_number:03d} in the legacy format at
`docs/02-architecture/adrs/` and has been migrated to fRIMPL format
(FR-{fr_number}/IMPL-{fr_number}) for consistency with the unified nspec system.

**Migration Date:** {date.today().isoformat()}

**Original Location:** `docs/02-architecture/adrs/ADR-{adr_number:03d}-{_slugify(title)}.md`

**Archive Location:** `docs/02-architecture/adrs/archive/ADR-{adr_number:03d}-{_slugify(title)}.md`

## Implementation Notes

For implementation details, architectural rationale, and design decisions, see:
- FR-{fr_number} for the architecture decision documentation
- Original ADR in archive directory for historical context
- Git hispec for code changes implementing this decision

---

**Note:** This is a retrospective IMPL document created during ADR migration.
The actual implementation work was completed prior to this documentation.
"""

    return impl_content


def _slugify(title: str) -> str:
    """Convert title to slug for filename."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug


def migrate_adr(
    adr_path: Path,
    docs_root: Path,
    dry_run: bool = False,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[Path, Path]:
    """Migrate a single ADR file to FR-9XX/IMPL-9XX format.

    Args:
        adr_path: Path to ADR-XXX.md file
        docs_root: Path to docs/ directory
        dry_run: If True, print actions without writing files
        paths_config: Optional custom paths configuration
        project_root: Project root for finding .novabuilt.dev/nspec/config.toml (default: cwd)

    Returns:
        Tuple of (fr_path, impl_path) that would be created
    """
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)
    # Extract ADR number from filename
    match = re.search(r"(\d+)", adr_path.stem)
    if not match:
        raise ValueError(f"Could not extract ADR number from {adr_path.name}")

    adr_number = int(match.group(1))
    fr_number = 900 + adr_number

    prefix = "[DRY RUN] " if dry_run else ""
    print(f"\n{prefix}Migrating ADR-{adr_number:03d} → FR-{fr_number}/IMPL-{fr_number}")

    # Read original ADR
    content = adr_path.read_text()

    # Extract title and sections
    title = extract_title(content)
    sections = extract_sections(content)

    print(f"  Title: {title}")
    print(f"  Sections found: {', '.join(sections.keys())}")

    # Generate FR and IMPL content
    fr_content = generate_fr_content(adr_number, title, sections)
    impl_content = generate_impl_content(adr_number, title)

    # Prepare paths
    slug = _slugify(title)
    fr_path = paths.active_frs_dir / f"FR-{fr_number}-{slug}.md"
    impl_path = paths.active_impls_dir / f"IMPL-{fr_number}-{slug}.md"
    archive_dir = docs_root / "02-architecture" / "adrs" / "archive"
    archive_path = archive_dir / f"ADR-{adr_number:03d}-{slug}.md"

    if not dry_run:
        # Write FR file
        fr_path.write_text(fr_content)
        print(f"  ✅ Created: {fr_path.relative_to(docs_root.parent)}")

        # Write IMPL file
        impl_path.write_text(impl_content)
        print(f"  ✅ Created: {impl_path.relative_to(docs_root.parent)}")

        # Archive old ADR
        archive_dir.mkdir(parents=True, exist_ok=True)
        adr_path.rename(archive_path)
        print(f"  📦 Archived: {archive_path.relative_to(docs_root.parent)}")
    else:
        print(f"  [DRY RUN] Would create: {fr_path.relative_to(docs_root.parent)}")
        print(f"  [DRY RUN] Would create: {impl_path.relative_to(docs_root.parent)}")
        print(f"  [DRY RUN] Would archive: {archive_path.relative_to(docs_root.parent)}")

    return fr_path, impl_path


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description="Migrate ADRs to fRIMPL format")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--adr-number", type=int, help="Migrate only this ADR number")
    args = parser.parse_args()

    # Find docs root
    docs_root = Path(__file__).parent.parent.parent.parent / "docs"
    adr_dir = docs_root / "02-architecture" / "adrs"

    if not adr_dir.exists():
        print(f"❌ ADR directory not found: {adr_dir}")
        return 1

    # Find ADR files
    if args.adr_number:
        # Migrate specific ADR
        pattern = f"*{args.adr_number:03d}*.md"
        adr_files = list(adr_dir.glob(pattern))
        if not adr_files:
            pattern = f"{args.adr_number:03d}-*.md"
            adr_files = list(adr_dir.glob(pattern))
        if not adr_files:
            print(f"❌ ADR-{args.adr_number:03d} not found")
            return 1
    else:
        # Migrate all ADRs (but skip README)
        adr_files = sorted(
            [
                f
                for f in adr_dir.glob("*.md")
                if re.search(r"\d{3}", f.stem) and f.name != "README.md"
            ]
        )

    if not adr_files:
        print("❌ No ADR files found to migrate")
        return 1

    print(f"{'=' * 80}")
    print(f"ADR → fRIMPL Migration {'(DRY RUN)' if args.dry_run else ''}")
    print(f"{'=' * 80}")
    print(f"Found {len(adr_files)} ADR(s) to migrate")

    # Migrate each ADR
    migrated = []
    errors = []

    for adr_path in adr_files:
        try:
            fr_path, impl_path = migrate_adr(adr_path, docs_root, dry_run=args.dry_run)
            migrated.append((adr_path, fr_path, impl_path))
        except _AdrMigrationErrors as e:
            errors.append((adr_path, e))
            print(f"  ❌ Error: {e}")

    # Summary
    print(f"\n{'=' * 80}")
    print("Migration Summary")
    print(f"{'=' * 80}")
    print(f"✅ Successfully migrated: {len(migrated)}")
    print(f"❌ Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for adr_path, error in errors:
            print(f"  - {adr_path.name}: {error}")

    if not args.dry_run and migrated:
        print("\n📋 Next Steps:")
        print("  1. Run: make nspec")
        print("  2. Run: make nspec.validate-consistency")
        print("  3. Review generated FR-9XX/IMPL-9XX files")
        print("  4. Commit:")
        print("     git add docs/frs/active/FR-9*.md")
        print("     git add docs/impls/active/IMPL-9*.md")
        print("     git add docs/02-architecture/adrs/archive/")
        print('     git commit -m "feat: Migrate 17 ADRs to fRIMPL format (FR-901 to FR-917)"')

    return 0 if not errors else 1


if __name__ == "__main__":
    exit(main())
