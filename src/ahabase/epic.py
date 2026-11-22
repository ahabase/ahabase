"""The Epic's tree: where its knowledge and its code live.

An Epic is a directory with ``_grid4d/``; its identity is the story-folder
document whose header says ``**Type:** Epic``. The identity IS the
registration (AHA-0030, the Human's 2026-11-20 ruling): its
``**StoryPrefix:**`` line declares the story numbering namespace, and no
second place carries that fact. Its ``**CodeArtifacts:**`` line names the
package the Epic's code lives in - optional, because a knowledge-only Epic
is a valid Epic (identity and package are separate declarations: the
format core never needs a code package to validate knowledge).
Only reads; standard library only.

Implements: implementation-ahabase-transparency-blueprint
Blueprint: implementation-ahabase-transparency-blueprint

Capability: lineage-validation
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class EpicError(Exception):
    """The tree is not an Epic this package can read; the message says why."""


@dataclass(frozen=True)
class Epic:
    root: Path
    identity: Path
    story_prefix: str  # the namespace the def file declares, without its trailing dash
    package: Path | None

    @property
    def grid(self) -> Path:
        return self.root / "_grid4d"

    @property
    def ontology(self) -> Path:
        return self.grid / "ontology"

    @property
    def implementation(self) -> Path:
        return self.grid / "implementation"

    @property
    def name(self) -> str:
        """The Epic's name: its identity file's stem (``AHABASE.md`` -> ``AHABASE``)."""
        return self.identity.stem


def header(text: str, field: str) -> str | None:
    """The value of a ``**Field:** value`` header line, or None."""
    match = re.search(rf"^\*\*{re.escape(field)}:\*\* ?(.*)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def prefix_from(text: str) -> str | None:
    """The story-numbering namespace a ``**StoryPrefix:**`` line declares.

    The declaration is uppercase letters, digits and dashes, and may end
    with one dash (the historical form ``AHA-``); the namespace is the
    prefix without it (``AHA``). None when the line is absent or invalid.
    """
    value = header(text, "StoryPrefix")
    if not value or not re.fullmatch(r"[A-Z][A-Z0-9-]*-?", value):
        return None
    return value.rstrip("-")


def load(root: Path) -> Epic:
    """Read the Epic at ``root``: its identity, story prefix and package.

    Identity requires ``**Type:** Epic`` and a ``**StoryPrefix:**``
    declaration (the registration); ``**CodeArtifacts:**`` is optional -
    absent means a knowledge-only Epic whose code-consuming surfaces see
    no package.
    """
    root = Path(root).resolve()
    story = root / "_grid4d" / "story"
    if not story.is_dir():
        raise EpicError(f"no _grid4d/story/ under {root} - not an Epic")
    identities = [p for p in sorted(story.glob("*.md"))
                  if header(p.read_text(encoding="utf-8", errors="replace"), "Type") == "Epic"]
    if len(identities) != 1:
        raise EpicError(f"expected one Epic identity (**Type:** Epic) in {story}, "
                        f"found {len(identities)}")
    identity = identities[0]
    text = identity.read_text(encoding="utf-8", errors="replace")
    prefix = prefix_from(text)
    if prefix is None:
        raise EpicError(f"{identity.name} declares no **StoryPrefix:** line "
                        f"(the registration, AHA-0030)")
    package = None
    artifacts = header(text, "CodeArtifacts")
    if artifacts:
        package = (root / artifacts).resolve()
        if root not in package.parents or not package.is_dir():
            raise EpicError(f"**CodeArtifacts:** {artifacts} is not a directory inside {root}")
    return Epic(root=root, identity=identity, story_prefix=prefix, package=package)


def subepics(epic: Epic) -> list[Path]:
    """The subepic roots under the Epic's ``_grid4d/subepic/``, sorted by name.

    A subepic inherits the Epic's folders until it grows its own; when it
    does, its ``ontology/`` and ``implementation/`` are read together with
    the Epic's own, so a concept may live at either level (the ontology
    shape, AHA-0017/AHA-0018).
    """
    root = epic.grid / "subepic"
    if not root.is_dir():
        return []
    return sorted(path for path in root.iterdir() if path.is_dir())
