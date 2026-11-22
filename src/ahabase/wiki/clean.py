"""Wiki duplicate cleaning - root copy wins, newest is promoted.

The clean operation of the validation pair: when a filename exists at
the root and in subfolders, the subfolder copies go; when only
subfolder copies exist, the newest is promoted to the root and the rest
go. The mirror is created when absent (an empty mirror is a valid wiki
state).

Implements: implementation-ahabase-wiki-door-blueprint
Blueprint: implementation-ahabase-wiki-door-blueprint

Capability: wiki-validation
"""

from __future__ import annotations

import shutil
from pathlib import Path

import click

from .validate import find_duplicates


def clean_wiki(wiki_path: Path, dry_run: bool) -> None:
    """Remove duplicate files from subfolders, keeping the root copy."""
    click.echo(f"Cleaning wiki: {wiki_path}")

    duplicates = find_duplicates(wiki_path)
    stats = {"removed": 0, "promoted": 0}

    if not duplicates:
        click.echo("  No duplicates to clean.")
        return

    click.echo("\n=== Cleaning duplicates ===")

    for name, paths in sorted(duplicates.items()):
        root_copies = [p for p in paths if p.parent == wiki_path]
        subfolder_copies = [p for p in paths if p.parent != wiki_path]

        if root_copies:
            # Root copy exists - remove subfolder copies
            for subfolder_path in subfolder_copies:
                rel_path = subfolder_path.relative_to(wiki_path)
                if dry_run:
                    click.echo(f"  Would remove: {rel_path}")
                else:
                    subfolder_path.unlink()
                    click.echo(f"  Removed: {rel_path}")
                stats["removed"] += 1
        elif subfolder_copies:
            # No root copy - promote newest to root
            newest = max(subfolder_copies, key=lambda p: p.stat().st_mtime)
            target = wiki_path / name

            if dry_run:
                click.echo(f"  Would promote: {newest.relative_to(wiki_path)} -> {name}")
            else:
                shutil.copy2(newest, target)
                click.echo(f"  Promoted: {newest.relative_to(wiki_path)} -> {name}")
            stats["promoted"] += 1

            # Remove all subfolder copies (including the one we promoted from)
            for other in subfolder_copies:
                rel_path = other.relative_to(wiki_path)
                if dry_run:
                    click.echo(f"  Would remove: {rel_path}")
                else:
                    other.unlink()
                    click.echo(f"  Removed: {rel_path}")
                stats["removed"] += 1

    click.echo(f"\n=== Summary ===")
    click.echo(f"Files removed: {stats['removed']}")
    click.echo(f"Files promoted to root: {stats['promoted']}")

    if dry_run:
        click.echo("\n(Dry run - no changes made)")
