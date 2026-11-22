"""``ahabase ontology graph`` and ``ahabase verify``: the transparency door of the CLI.

Both read an Epic's tree (``--root``, default the current directory) and
print; only ``ontology graph`` without ``--check`` writes, and only the
ontology map between its markers - in the Epic's ontology index and each
subepic's (maps render at their own level). Exit codes:
0 holds, 1 a finding (a divergence, a stale map), 2 a usage problem or a
tree that is not an Epic.

``verify`` checks three things, one exit code: the lineage (concept ->
implementation blueprint -> code, both directions), the capability
vocabulary (every ``Capability:`` name the code declares is defined in
the Epic's capabilities index) and the open-zone link containment (every
link of the Epic's documents resolves within the repository or rides a
declared generator exception).

Implements: implementation-ahabase-transparency-blueprint
Blueprint: implementation-ahabase-transparency-blueprint

Capability: lineage-validation
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

import click

from . import capabilities, containment, lineage, ontology_map
from .epic import EpicError, load

ROOT = click.option("--root", type=click.Path(file_okay=False, path_type=Path), default=".",
                    show_default=True, help="The Epic's directory (the one holding _grid4d/).")


def _epic(root: Path):
    try:
        return load(root)
    except EpicError as error:
        click.echo(f"ahabase: {error}", err=True)
        sys.exit(2)


@click.group()
def ontology():
    """The Epic's ontology."""


@ontology.command()
@ROOT
@click.option("--check", is_flag=True, help="Write nothing; exit 1 when the map is stale.")
def graph(root: Path, check: bool):
    """Generate the ontology map into each ontology index (between its markers).

    The Epic's index first, then every subepic's - maps render at their
    own level.

    Capability: ontology-projection
    """
    epic = _epic(root)
    try:
        scopes = ontology_map.expected_scopes(epic)
    except EpicError as error:
        click.echo(f"ahabase: {error}", err=True)
        sys.exit(2)
    except ontology_map.MarkerError as error:
        click.echo(f"ontology map: {error}")
        sys.exit(1)

    def summary(built: ontology_map.Map) -> str:
        return f"{built.concepts} concepts, {built.facets} facets, {built.edges} relations"

    stale = [scope for scope in scopes if scope[1] != scope[2]]
    if check:
        for path, current, wanted, built in scopes:
            if current == wanted:
                click.echo(f"ontology map: current in {path.name} ({summary(built)})")
        for path, current, wanted, _ in stale:
            click.echo(f"ontology map: stale in {path.name} - run `ahabase ontology graph`")
            diff = difflib.unified_diff(current.splitlines(), wanted.splitlines(),
                                        "committed", "generated", lineterm="", n=1)
            for line in list(diff)[:40]:
                click.echo(f"  {line}")
        sys.exit(1 if stale else 0)
    for path, current, wanted, built in scopes:
        if current != wanted:
            path.write_text(wanted, encoding="utf-8")
            click.echo(f"ontology map: written to {path.name} ({summary(built)})")
        else:
            click.echo(f"ontology map: unchanged in {path.name} ({summary(built)})")


@click.command()
@ROOT
def verify(root: Path):
    """Check the Epic: lineage both directions, the capability vocabulary, the open-zone links.

    Capability: lineage-validation
    """
    epic = _epic(root)
    findings = 0

    result = lineage.compute(epic)
    for line in lineage.report(result):
        click.echo(line)
    findings += 0 if result.holds else 1

    caps = capabilities.compute(epic)
    for line in capabilities.report(caps):
        click.echo(line)
    findings += 0 if caps.holds else 1

    links = containment.compute(epic)
    for line in containment.report(links):
        click.echo(line)
    findings += 0 if links.holds else 1

    sys.exit(0 if findings == 0 else 1)
