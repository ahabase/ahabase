"""``ahabase story``: the local story lifecycle's door.

Three commands over the consumer's own git repository: ``create``
(mint: number by scan, worktree + branch, the story set from the
pattern templates), ``status`` (what is: open stories, completed
count) and ``complete`` (mark, tag ``v<STORY>``, merge to the main
branch, archive, remove the worktree). No collab, no team log, no
phases - the local lifecycle only. Every refusal names its reason;
exit codes: 0 done, 1 refused, 2 a usage problem.

Implements: implementation-story-lifecycle-blueprint
Blueprint: implementation-story-lifecycle-blueprint

Capability: story-lifecycle
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import story
from .epic import EpicError, load


@click.group()
def story_group():
    """The local story lifecycle: mint, show, complete.

    Capability: story-lifecycle
    """


ROOT = click.option("--root", type=click.Path(file_okay=False, path_type=Path), default=".",
                    show_default=True, help="The Epic's directory (the one holding _grid4d/).")


def _load(root: Path):
    try:
        return load(root)
    except EpicError as error:
        click.echo(f"identity: {error}")
        sys.exit(1)


@story_group.command()
@click.argument("description")
@ROOT
def create(root: Path, description: str):
    """Mint a story: the next number by scan, its worktree + branch, the story set.

    DESCRIPTION names the work (it titles the story and slugs the branch).
    """
    epic = _load(root)
    try:
        worktree = story.create(epic, description)
    except story.StoryError as error:
        click.echo(f"story: {error}")
        sys.exit(1)
    click.echo(f"story: {worktree.name} minted at {worktree}")
    click.echo("story: work the set in the worktree, then 'ahabase story complete'")


@story_group.command()
@ROOT
def status(root: Path):
    """Show what is: the open stories and the completed count."""
    epic = _load(root)
    for line in story.status(epic):
        click.echo(line)


@story_group.command()
@click.argument("story_id")
@ROOT
def complete(root: Path, story_id: str):
    """Complete a story: tag, merge to main, archive, remove the worktree.

    STORY_ID is the story's name (e.g. DEMO-0002); run from the Epic's main tree.
    """
    epic = _load(root)
    try:
        story.complete(epic, story_id)
    except story.StoryError as error:
        click.echo(f"story: {error}")
        sys.exit(1)
    click.echo(f"story: {story_id} completed - tagged, merged, archived")
