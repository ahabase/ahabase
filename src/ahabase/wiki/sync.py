"""Wiki sync - the document passes and the orphan purge.

``sync_documents`` orchestrates five passes; each pass is a small
function here so the orchestration stays readable and testable:
preserved directories (wiki-only content the config marks), the mapped
documents, the auto-sync glob patterns, the story worktrees, and the
purge of everything the config no longer accounts for. The mirror is
created when absent - an empty mirror is a valid wiki state, not a
refusal.

Implements: implementation-ahabase-wiki-door-blueprint
Blueprint: implementation-ahabase-wiki-door-blueprint

Capability: wiki-projection
"""

from __future__ import annotations

import glob
import shutil
from pathlib import Path

import click

from .context import SyncPlan


def sync_document(source: Path, target: Path, dry_run: bool) -> bool:
    """Copy a single document from source to target; False when the
    source does not exist (the caller reports the missing mapping)."""
    if not source.exists():
        return False

    if dry_run:
        click.echo(f"  Would copy: {source.name}")
    else:
        shutil.copy2(source, target)
        click.echo(f"  Copied: {source.name}")

    return True


def register_preserved_directories(documents: dict, plan: SyncPlan):
    """First sync pass: register wiki-only directory mappings.

    Directory-level null mappings (keys ending with ``::`` - YAML needs
    the key quoted to survive parsing) mark whole wiki directories as
    wiki-only: their existing files are added to the expected set
    instead of being synced or purged.
    """
    for wiki_name, source_rel in documents.items():
        if wiki_name.endswith("::") and source_rel is None:
            dir_path = wiki_name.rstrip(":").rstrip("/")

            # Special case: root directory pattern
            if dir_path in (".", ""):
                plan.preserved_directories.append("(root)")
                for item in plan.wiki_path.iterdir():
                    if item.is_file() and ".git" not in item.parts:
                        plan.expected_paths.add(item)
                plan.stats["preserved_dirs"] += 1
                continue

            # Directory pattern - preserve all existing files under this wiki directory
            wiki_dir = plan.wiki_path / dir_path
            if wiki_dir.exists() and wiki_dir.is_dir():
                plan.preserved_directories.append(dir_path)
                for item in wiki_dir.rglob("*"):
                    if item.is_file() and ".git" not in item.parts:
                        plan.expected_paths.add(item)
                    elif item.is_dir() and ".git" not in item.parts:
                        plan.expected_folders.add(item.name)
                plan.stats["preserved_dirs"] += 1


def sync_mapped_documents(documents: dict, source_path: Path, plan: SyncPlan):
    """Second sync pass: copy file-level document mappings (the wiki
    filename flattens to the mirror root)."""
    click.echo("\n=== Syncing mapped documents ===")
    for wiki_name, source_rel in documents.items():
        # Skip directory patterns (already processed above)
        if wiki_name.endswith("::"):
            continue
        if source_rel is None:
            plan.stats["skipped"] += 1
            continue

        source_file = source_path / source_rel
        # Use wiki_name as target filename (flatten to root)
        target_file = plan.wiki_path / f"{wiki_name}.md"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        plan.expected_paths.add(target_file)
        plan.expected_folders.add(target_file.parent.name)

        if sync_document(source_file, target_file, plan.dry_run):
            plan.stats["synced"] += 1
        else:
            click.echo(f"  Warning: Source not found: {source_file}")
            plan.stats["missing"] += 1


def sync_auto_patterns(auto_sync: list, source_path: Path, plan: SyncPlan):
    """Third sync pass: copy files matched by auto_sync glob patterns.

    A ``wiki_pattern`` of ``{basename}`` flattens to the mirror root;
    otherwise the folder structure relative to the source is preserved.
    """
    if not auto_sync:
        return
    click.echo("\n=== Syncing auto-pattern files ===")
    for pattern_config in auto_sync:
        source_pattern = pattern_config.get("source_pattern", "")
        full_pattern = str(source_path / source_pattern)

        for source_file in glob.glob(full_pattern, recursive=True):
            source_path_obj = Path(source_file)
            # Check wiki_pattern for flattening behavior
            wiki_pattern = pattern_config.get("wiki_pattern")
            if wiki_pattern == "{basename}":
                # Flatten to wiki root using just the filename
                target_file = plan.wiki_path / source_path_obj.name
            else:
                # Preserve folder structure relative to source
                rel_path = source_path_obj.relative_to(source_path)
                target_file = plan.wiki_path / rel_path
                # Track all parent folders (only when preserving structure)
                for parent in rel_path.parents:
                    if parent != Path("."):
                        plan.expected_folders.add(
                            str(parent.parts[0]) if parent.parts else "")
            target_file.parent.mkdir(parents=True, exist_ok=True)
            plan.expected_paths.add(target_file)

            if sync_document(source_path_obj, target_file, plan.dry_run):
                plan.stats["synced"] += 1


def sync_worktree_documents(config: dict, epic: str, workspace: Path,
                            plan: SyncPlan):
    """Fourth sync pass: copy documents from active story worktrees.

    Scans ``<workspace>/_worktrees/<epic>/`` for stories and syncs their
    documents based on the ``worktree_sources`` config. The main tree
    takes precedence - only worktree documents the main tree has not
    already produced are synced.
    """
    import fnmatch

    worktree_config = config.get("worktree_sources", {})
    if not worktree_config.get("enabled", False):
        return

    worktrees_path = workspace / "_worktrees" / epic
    if not worktrees_path.exists():
        return

    # Default pattern: story/{STORY}*.md (all story-related docs)
    source_pattern = worktree_config.get("pattern", "story/{STORY}*.md")
    exclude_patterns = config.get("exclude", [])

    click.echo("\n=== Syncing worktree documents ===")
    synced_count = 0

    for story_dir in sorted(worktrees_path.iterdir()):
        if not story_dir.is_dir() or story_dir.name.startswith("."):
            continue

        story_id = story_dir.name
        grid4d_path = story_dir / "_grid4d"
        if not grid4d_path.exists():
            continue

        # Expand pattern with story ID and glob
        pattern_expanded = source_pattern.replace("{STORY}", story_id)
        full_pattern = str(grid4d_path / pattern_expanded)

        for source_file in glob.glob(full_pattern):
            source_path_obj = Path(source_file)
            target_name = source_path_obj.stem  # filename without extension
            target_file = plan.wiki_path / f"{target_name}.md"

            # Check exclude patterns
            skip = False
            for excl in exclude_patterns:
                # Remove leading **/ if present
                excl_pattern = excl.removeprefix("**/") if excl.startswith("**/") else excl
                if fnmatch.fnmatch(source_path_obj.name, excl_pattern):
                    skip = True
                    break
            if skip:
                continue

            # Main tree takes precedence - skip if already synced
            if target_file in plan.expected_paths:
                continue

            plan.expected_paths.add(target_file)

            if sync_document(source_path_obj, target_file, plan.dry_run):
                synced_count += 1

    if synced_count > 0:
        plan.stats["synced"] += synced_count
        click.echo(f"  Synced {synced_count} worktree documents")
    else:
        click.echo("  No worktree documents to sync")


def purge_orphans(plan: SyncPlan):
    """Fifth sync pass: remove wiki files and folders outside the plan."""
    click.echo("\n=== Purging orphaned content ===")
    for item in sorted(plan.wiki_path.rglob("*")):
        if ".git" in item.parts:
            continue
        if item.is_file() and item not in plan.expected_paths:
            rel_path = item.relative_to(plan.wiki_path)
            if plan.dry_run:
                click.echo(f"  Would remove: {rel_path}")
            else:
                item.unlink()
                click.echo(f"  Removed: {rel_path}")
            plan.stats["purged"] += 1

    # Remove empty folders
    for item in sorted(plan.wiki_path.rglob("*"), reverse=True):
        if ".git" in item.parts:
            continue
        if item.is_dir() and not any(item.iterdir()):
            rel_path = item.relative_to(plan.wiki_path)
            if plan.dry_run:
                click.echo(f"  Would remove empty folder: {rel_path}/")
            else:
                item.rmdir()
                click.echo(f"  Removed empty folder: {rel_path}/")
            plan.stats["purged"] += 1

    if plan.stats["purged"] == 0:
        click.echo("  Nothing to purge.")


def render_sync_summary(plan: SyncPlan):
    """Final sync pass: print the run summary."""
    click.echo("\n=== Summary ===")
    click.echo(f"Documents synced: {plan.stats['synced']}")
    click.echo(f"Documents skipped (manual): {plan.stats['skipped']}")
    click.echo(f"Documents missing: {plan.stats['missing']}")
    if plan.preserved_directories:
        click.echo(f"Preserved directories: {', '.join(plan.preserved_directories)}")
    click.echo(f"Items purged: {plan.stats['purged']}")

    if plan.dry_run:
        click.echo("\n(Dry run - no changes made)")


def sync_documents(epic: str, wiki_path: Path, source_path: Path,
                   config: dict, workspace: Path, dry_run: bool) -> None:
    """Run the five passes: ``_grid4d/`` documents into the mirror.

    The mirror is created when absent (the door is its writer); a
    missing source tree refuses - nothing accounts for the documents.
    """
    if not source_path.exists():
        raise FileNotFoundError(str(source_path))
    wiki_path.mkdir(parents=True, exist_ok=True)

    click.echo(f"Epic: {epic}")
    click.echo(f"Source: {source_path}")
    click.echo(f"Target: {wiki_path}")

    plan = SyncPlan(wiki_path=wiki_path, dry_run=dry_run)
    plan.expected_paths.update(
        {wiki_path / "_Sidebar.md", wiki_path / "Home.md"})
    plan.expected_folders.add(".git")

    # Process documents config - separate directory patterns from file patterns
    documents = config.get("documents", {})

    register_preserved_directories(documents, plan)
    sync_mapped_documents(documents, source_path, plan)
    sync_auto_patterns(config.get("auto_sync", []), source_path, plan)
    sync_worktree_documents(config, epic, workspace, plan)
    purge_orphans(plan)
    render_sync_summary(plan)
