"""Wiki structure validation - duplicate detection and the check walk.

A duplicate is the same filename in more than one location under the
mirror; GitHub's wiki serves one page per name per folder, and flat
syncing makes subfolder copies shadow-ambiguities the reader cannot
resolve. ``.git`` parts are never walked.

Implements: implementation-ahabase-wiki-door-blueprint
Blueprint: implementation-ahabase-wiki-door-blueprint

Capability: wiki-validation
"""

from __future__ import annotations

from pathlib import Path

import click


def find_duplicates(wiki_path: Path) -> dict[str, list[Path]]:
    """Find duplicate files in the wiki (same filename in multiple
    locations): name -> the paths carrying it, only names with more
    than one."""
    files_by_name: dict[str, list[Path]] = {}

    for md_file in wiki_path.rglob("*.md"):
        if ".git" in md_file.parts:
            continue
        name = md_file.name
        if name not in files_by_name:
            files_by_name[name] = []
        files_by_name[name].append(md_file)

    return {name: paths for name, paths in files_by_name.items() if len(paths) > 1}


def check_wiki(wiki_path: Path) -> dict[str, list[Path]]:
    """Report the mirror's duplicates (the summary lines the door prints);
    returns the duplicates so the door can exit distinguishably."""
    click.echo(f"Checking wiki: {wiki_path}")

    click.echo("\n=== Checking for duplicates ===")
    duplicates = find_duplicates(wiki_path)

    if not duplicates:
        click.echo("  No duplicates found.")
    else:
        for name, paths in sorted(duplicates.items()):
            click.echo(f"\n  {name} ({len(paths)} copies):")
            for path in paths:
                rel_path = path.relative_to(wiki_path)
                is_root = path.parent == wiki_path
                marker = " [ROOT]" if is_root else " [SUBFOLDER]"
                click.echo(f"    - {rel_path}{marker}")

    # Summary
    total_duplicates = sum(len(p) - 1 for p in duplicates.values())
    click.echo(f"\n=== Summary ===")
    click.echo(f"Files with duplicates: {len(duplicates)}")
    click.echo(f"Extra copies: {total_duplicates}")
    return duplicates
