"""``ahabase wiki``: the wiki projection's door.

The five operations of the graduated wiki capability over the mirror at
``<workspace>/_wikis/<epic>.wiki``: ``sync`` (the ``_grid4d/`` documents
in, orphans purged), ``generate`` (``_Sidebar.md`` and ``Home.md`` from
the config), ``check`` (duplicates; exit 3 when found), ``clean``
(dedupe, root copy wins), ``publish`` (the mirror becomes the
repository's wiki, pushed under the declared account), and ``status``
(the mirror's git state). Exit codes distinguish the outcomes: 0 done,
1 refused (the remedy printed), 2 usage, 3 check found duplicates.

The door is epic-explicit: ``--epic NAME`` names the Epic (the seam's
optional flag); an omitted name refuses with the remedy rather than
resolving an ambient Epic.

Implements: implementation-ahabase-wiki-door-blueprint
Blueprint: implementation-ahabase-wiki-door-blueprint

Capability: wiki-projection
"""

from __future__ import annotations

import sys

import click

from .config import get_workspace_dir
from .wiki.config import load_wiki_config, resolve_wiki_paths
from .wiki.context import WikiRefusal
from .wiki.publish import mirror_status, publish


@click.group("wiki")
def wiki_group() -> None:
    """The Epic's knowledge as a GitHub-wiki mirror."""


_EPIC = click.option("--epic", metavar="NAME",
                     help="The Epic's name under the workspace root.")
_DRY = click.option("--dry-run", is_flag=True,
                    help="Show what would be done without making changes.")


def _resolve(epic: str | None):
    """The epic root, config, mirror and source paths; the door's one
    resolution (a missing Epic directory or an omitted name refuses)."""
    if not epic:
        raise WikiRefusal("name the Epic: --epic NAME (the door resolves "
                          "no ambient Epic)")
    epic_root = get_workspace_dir() / epic
    if not epic_root.is_dir():
        raise WikiRefusal(f"no Epic directory at {epic_root} under the "
                          "workspace - check the name")
    config = load_wiki_config(epic)
    wiki_path, source_path = resolve_wiki_paths(epic, config)
    return epic_root, config, wiki_path, source_path


def _refused(call):
    """Run a door body; a refusal prints its remedy and exits 1."""
    try:
        return call()
    except WikiRefusal as error:
        click.echo(f"wiki: {error}")
        sys.exit(1)


@wiki_group.command()
@_EPIC
@_DRY
def sync(epic: str | None, dry_run: bool) -> None:
    """Sync the Epic's _grid4d/ documents into the wiki mirror."""
    from .wiki.sync import sync_documents

    def run():
        epic_root, config, wiki_path, source_path = _resolve(epic)
        if not source_path.exists():
            raise WikiRefusal(f"source path not found: {source_path} - the "
                              "Epic's wiki source (wiki.source in the yaml)")
        sync_documents(epic, wiki_path, source_path, config,
                       get_workspace_dir(), dry_run)
    _refused(run)


@wiki_group.command()
@_EPIC
def check(epic: str | None) -> None:
    """Check the wiki mirror for duplicate page names; exit 3 when found."""
    from .wiki.validate import check_wiki

    def run() -> int:
        _, _, wiki_path, _ = _resolve(epic)
        wiki_path.mkdir(parents=True, exist_ok=True)
        duplicates = check_wiki(wiki_path)
        return 3 if duplicates else 0
    sys.exit(_refused(run) or 0)


@wiki_group.command()
@_EPIC
@_DRY
def clean(epic: str | None, dry_run: bool) -> None:
    """Remove duplicate pages from subfolders (the root copy wins)."""
    from .wiki.clean import clean_wiki

    def run():
        _, _, wiki_path, _ = _resolve(epic)
        wiki_path.mkdir(parents=True, exist_ok=True)
        clean_wiki(wiki_path, dry_run)
    _refused(run)


@wiki_group.command()
@_EPIC
@_DRY
def generate(epic: str | None, dry_run: bool) -> None:
    """Generate _Sidebar.md and Home.md from the wiki config."""
    from .wiki.generate import generate_navigation

    def run():
        _, config, wiki_path, _ = _resolve(epic)
        wiki_path.mkdir(parents=True, exist_ok=True)
        generate_navigation(wiki_path, config, dry_run)
    _refused(run)


@wiki_group.command("publish")
@_EPIC
@_DRY
def publish_command(epic: str | None, dry_run: bool) -> None:
    """Publish the mirror to the repository's wiki under the declared account."""
    def run():
        epic_root, config, wiki_path, _ = _resolve(epic)
        publish(epic, epic_root, wiki_path, config, dry_run)
    _refused(run)


@wiki_group.command()
@_EPIC
def status(epic: str | None) -> None:
    """Show the wiki mirror's git status (uncommitted pages, clone state)."""
    def run():
        _, _, wiki_path, _ = _resolve(epic)
        click.echo(f"wiki mirror: {wiki_path}")
        if not (wiki_path / ".git").exists():
            click.echo("not a git clone - publish initializes it")
            return
        state = mirror_status(wiki_path)
        click.echo(f"clean: {state['clean']}")
        click.echo(f"uncommitted: {state['uncommitted_count']}")
        for line in state["files"]:
            click.echo(f"  {line}")
    _refused(run)
