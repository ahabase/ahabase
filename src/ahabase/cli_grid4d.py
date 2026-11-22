"""``ahabase validate`` and ``ahabase init``: the grid4d format core's doors.

``validate`` reads an Epic's tree (``--root``, default the current
directory) and reports every format finding namingly - the rule, the
path, the detail. A tree that is not an Epic this package can read
(no ``_grid4d/story/``, no identity file, no valid registration)
reports as an ``identity`` finding, not a crash: the door is
fail-closed with the class named. ``init`` writes a fresh tree's
skeleton from the package's epic pattern and refuses an existing
``_grid4d/``. Exit codes: 0 done, 1 refused, 2 a usage problem.

Implements: implementation-grid4d-format-core-blueprint
Blueprint: implementation-grid4d-format-core-blueprint

Capability: grid4d-format
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import grid4d
from .epic import EpicError, load


@click.command()
@click.option("--root", type=click.Path(file_okay=False, path_type=Path), default=".",
              show_default=True, help="The Epic's directory (the one holding _grid4d/).")
def validate(root: Path):
    """Validate an Epic's _grid4d/ tree: folders, identity, naming, structure, links.

    Capability: grid4d-format
    """
    try:
        epic = load(root)
    except EpicError as error:
        click.echo(f"identity: {error}")
        sys.exit(1)
    findings = grid4d.validate(epic)
    for finding in findings:
        click.echo(str(finding))
    if findings:
        click.echo(f"grid4d: {len(findings)} finding(s)")
        sys.exit(1)
    click.echo("grid4d: holds")


@click.command()
@click.argument("name")
@click.option("--prefix", metavar="NS",
              help="The story-numbering namespace (default: the name, uppercased).")
@click.option("--root", type=click.Path(file_okay=False, path_type=Path), default=".",
              show_default=True, help="The directory the Epic initializes in.")
def init(root: Path, name: str, prefix: str | None):
    """Initialize an Epic: the _grid4d/ skeleton and the self-registering identity file.

    NAME names the Epic (its identity file's stem). The skeleton is
    knowledge-only; declare a **CodeArtifacts:** line when the Epic
    carries code.

    Capability: grid4d-format
    """
    try:
        identity = grid4d.init(root, name, prefix)
    except grid4d.FormatError as error:
        click.echo(f"grid4d: {error}")
        sys.exit(1)
    click.echo(f"grid4d: initialized {name} - the registration is {identity}")
    click.echo("grid4d: fill the placeholders (the overview, the related documents), "
               "commit, and 'ahabase validate'")
