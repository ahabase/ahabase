"""Shared state of one wiki run: the sync plan and the refusal type.

The plan carries the mutable state of one sync so the pass functions
keep small signatures instead of threading five arguments through each.
The refusal is the door's one failure shape: a precondition that did not
hold, with the remedy in the message - the door prints it and exits 1.

Implements: implementation-ahabase-wiki-door-blueprint
Blueprint: implementation-ahabase-wiki-door-blueprint

Capability: wiki-projection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class WikiRefusal(Exception):
    """A precondition failed; the message names the remedy."""


@dataclass
class SyncPlan:
    """Mutable state of one wiki sync run.

    expected_paths - every wiki file the config accounts for; anything
        else under the wiki tree is purgeable.
    expected_folders - folder names the config accounts for (kept even
        when empty after purge).
    stats - counters rendered in the command summary.
    preserved_directories - names of wiki-only directories kept verbatim.
    dry_run - when True, pass functions only report intended changes.
    """

    wiki_path: Path
    expected_paths: set = field(default_factory=set)
    expected_folders: set = field(default_factory=set)
    stats: dict = field(default_factory=lambda: {
        "synced": 0, "skipped": 0, "missing": 0, "purged": 0,
        "preserved_dirs": 0,
    })
    preserved_directories: list = field(default_factory=list)
    dry_run: bool = False
