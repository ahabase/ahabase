"""The workspace door: the seven standard folders at the workspace root.

The Human ruling of 2026-11-22 (AHA-0035): every ahabase workspace
carries the seven standard folders - ``_config``, ``_data``,
``_generated``, ``_inbox``, ``_temp``, ``_wikis``, ``_worktrees`` - at
its root, outside every repository (the proven workspace topology).
``ensure`` is the consumer's idempotent act: a fresh workspace gains the
set, a folder a consumer deleted reappears, existing contents are never
touched.

Implements: implementation-ahabase-config-door-blueprint
Blueprint: implementation-ahabase-config-door-blueprint

Capability: config-management
"""

from __future__ import annotations

import click

from .config import ensure_standard_folders, get_workspace_dir


@click.group("workspace")
def workspace_group() -> None:
    """The workspace's standard folders."""


@workspace_group.command()
def ensure() -> None:
    """Create the seven standard folders at the workspace root (idempotent)."""
    click.echo(f"workspace: {get_workspace_dir()}")
    for folder in ensure_standard_folders():
        click.echo(folder.name)
