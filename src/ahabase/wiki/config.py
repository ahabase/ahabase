"""Wiki configuration loading and path resolution.

The config file is ``<workspace>/_config/<epic>.wiki.yaml`` - the
workspace-level convention, not the method side's in-repository file.
Absent or empty means the defaults, never a refusal: the door's contract
makes an unconfigured Epic a valid state (the standard mirror path and
the ``_grid4d/`` source, no document mapping).

Implements: implementation-ahabase-wiki-door-blueprint
Blueprint: implementation-ahabase-wiki-door-blueprint

Capability: wiki-projection
"""

from __future__ import annotations

from pathlib import Path

from .._yaml_unique import load as _load_unique
from ..config import get_workspace_dir


def load_wiki_config(epic: str) -> dict:
    """The Epic's wiki config; ``{}`` when the file is absent or empty.

    A duplicated key warns once and keeps YAML's last-wins value - the
    house loader's tolerant contract (a strict load would stop every
    door on a hand-edited file).
    """
    path = get_workspace_dir() / "_config" / f"{epic}.wiki.yaml"
    if not path.exists():
        return {}
    loaded = _load_unique(path.read_text(encoding="utf-8", errors="replace"),
                          str(path), strict=False)
    return loaded if isinstance(loaded, dict) else {}


def resolve_wiki_paths(epic: str, config: dict) -> tuple[Path, Path]:
    """The mirror and source paths: the config's ``wiki.target`` /
    ``wiki.source`` overrides, else the defaults ``_wikis/<epic>.wiki``
    and ``_grid4d/`` - both anchored at the workspace root.
    """
    wiki_config = config.get("wiki", {})
    target = wiki_config.get("target", f"_wikis/{epic}.wiki")
    source = wiki_config.get("source", "_grid4d")
    workspace = get_workspace_dir()
    return workspace / target, workspace / epic / source
