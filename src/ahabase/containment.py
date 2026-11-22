"""The open-zone link containment: a document of this repository links only within it.

The rule (ruled by the Human in AHA-0003, carried by the issue
``open-zone-documents-link-into-the-closed-zone``): a document of an open
Epic links only to documents of its own repository and names no document
of the closed zone. This check enforces the rule on every ``_grid4d``
document outside ``story/history/`` and ``_archive/`` (released and
archived documents are not scanned; they still resolve as link targets,
because an archived document exists even after its story closes).

A markdown link ``[text](target)`` that is not a URL must resolve within
the repository, in one of the three forms the real tree uses: a
name-only target matching a document's stem, a ``.md``-suffixed name, or
a relative path resolving from the linking file. What is scanned is
rendered text: fenced blocks and inline code spans are stripped first -
what does not render as a link is not read as one (the same reading as
the method CLI's ``strip_code_fences`` precedent).

The exceptions name links that generators still write into this open
Epic, never a hand-written one; each is tied to its issue and disappears
when the generator learns the open Epic's own documents (the fix lives
in the method's repository, per the issue's Fix section):

- the story-header blueprint name and the issues page's Related-block
  names (``open-zone-documents-link-into-the-closed-zone``, gaps 1/3);
- the knowledge-map hook's rows that declare themselves: a
  path-prefixed target (another repository's document,
  ``knowledge-map-links-a-document-of-another-repository``) or the
  ``(Generated)`` kind marker (this Epic's own ignored generated page,
  present on a synced tree, absent from a fresh clone).

Implements: implementation-ahabase-transparency-blueprint
Blueprint: implementation-ahabase-transparency-blueprint

Capability: link-containment
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .epic import Epic

#: Markdown links whose target is not a URL, an anchor or an address-less
#: reference fragment.
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)#\s]+)(?:#[^)\s]*)?\)")

#: Fenced code blocks (``` or ~~~): not rendered links.
FENCE_RE = re.compile(r"^[ \t]*(```|~~~).*$")

#: Inline code spans (one backtick or more): what they hold renders
#: literally, not as a link.
INLINE_RE = re.compile(r"(`+)[^`\n]*\1")

#: A knowledge-map row as the logger writes it: ``- [Name](target) (Kind)``.
#: Two target classes ride, both declared by the row itself: the
#: cross-repository rows (a path-prefixed target, the km issue) and the
#: rows the logger marks ``(Generated)``, whose name-only targets name
#: this Epic's own generated pages - pages written under the ignored
#: ``_generated/``, present on a synced tree and absent from a fresh
#: clone. Any other target that does not resolve is a dead link whatever
#: wrote it (review of the pin, finding 4; review of 002c8a0, finding 1).
HOOK_ROW_RE = re.compile(r"^- \[[^\]]+\]\(([^)]+)\) \(([A-Z][a-z]+)\)$")

#: Directories that are not scanned (their documents still resolve as
#: targets). Released stories keep their history; archives are inactive.
UNSCANNED_PARTS = ("story/history", "_archive")

#: Links the method's generators still write into this open Epic, tied to
#: ``open-zone-documents-link-into-the-closed-zone`` (gaps 1 and 3): the
#: blueprint name of every minted story header, and the three names of
#: the Related block the issues generator appends to its page.
GENERATOR_EXCEPTIONS = frozenset({
    "implementation-story-blueprint",
    "implementation-cli-projections_epic_issues-blueprint",
    "implementation-cli-issue_matcher-blueprint",
    "implementation-cli-sensors-blueprint",
})


@dataclass(frozen=True)
class Report:
    """What the link check found: links that leave the repository, per file."""

    unresolved: dict[str, list[str]] = field(default_factory=dict)
    exempted: int = 0
    scanned: int = 0

    @property
    def holds(self) -> bool:
        return not self.unresolved


def _rendered_text(text: str) -> str:
    """Fenced blocks and inline spans out: what is left renders as written."""
    kept: list[str] = []
    fenced = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            kept.append(line)
    return INLINE_RE.sub("", "\n".join(kept))


def _resolves(target: str, path: Path, targets: set[str], root: Path) -> bool:
    """Does the target name a document of this repository?

    Three forms, all in the real tree: a name-only stem, a ``.md``-suffixed
    stem, and a relative path from the linking file (``..`` included,
    suffix or not). Whatever resolves must land inside the Epic's root.
    """
    name = target[:-3] if target.endswith(".md") else target
    if "/" not in target and name in targets:
        return True
    resolved = (path.parent / target).resolve()
    candidates = (resolved, resolved.parent / (resolved.name + ".md"))
    for candidate in candidates:
        if candidate.is_file() and root in candidate.parents:
            return True
    return False


def _hook_row(line: str, path: Path) -> str | None:
    """The target of an excepted knowledge-map row, else None.

    The logger appends ``- [Name](target) (Kind)`` rows to a knowledge
    map's Consumed section. Two classes never resolve within a fresh
    clone and ride, each declared by the row itself: the rows naming
    another repository's documents (a path-prefixed target,
    ``<repo>/<name>``, the km issue) and the rows marked
    ``(Generated)``, whose name-only targets name this Epic's own
    ignored generated pages. Any other target of the same shape must
    resolve like any other link - the row shape alone exempts nothing.
    The row shape is the logger's, not prose: a hand-written link in
    running text never matches it.
    """
    if not path.name.endswith("-knowledge-map.md"):
        return None
    match = HOOK_ROW_RE.match(line)
    if not match:
        return None
    target, kind = match.group(1), match.group(2)
    if "/" in target or kind == "Generated":
        return target
    return None


def compute(epic: Epic) -> Report:
    """Check every scanned document's links resolve within the repository."""
    grid = epic.grid
    documents = [p for p in sorted(grid.rglob("*.md"))]

    # Every document of the tree is a resolvable target - history and
    # archives included: an archived document still exists to be linked.
    targets = {p.stem for p in documents}

    unresolved: dict[str, list[str]] = {}
    exempted = 0
    scanned = 0
    for path in documents:
        if any(part in path.relative_to(grid).as_posix() for part in UNSCANNED_PARTS):
            continue
        scanned += 1
        text = _rendered_text(path.read_text(encoding="utf-8", errors="replace"))
        for line in text.splitlines():
            hook_target = _hook_row(line, path)
            targets_in_line = [hook_target] if hook_target else LINK_RE.findall(line)
            for target in targets_in_line:
                if "://" in target or target.startswith("mailto:"):
                    continue
                if _resolves(target, path, targets, epic.root):
                    continue
                if target in GENERATOR_EXCEPTIONS or hook_target:
                    exempted += 1
                    continue
                # Posix key on every OS: str() would report backslashes on
                # Windows, whose CI lane asserts the same form as the rest.
                unresolved.setdefault(
                    path.relative_to(epic.root).as_posix(), []).append(target)

    return Report(unresolved=unresolved, exempted=exempted, scanned=scanned)


def report(check: Report) -> list[str]:
    """Lines to print for the link check; the last line is the verdict."""
    lines: list[str] = []
    for where, targets in sorted(check.unresolved.items()):
        for target in targets:
            lines.append(f"LINK unresolved: {where} -> {target} "
                         "- does not resolve within this repository")
    if check.holds:
        lines.append(f"links: holds ({check.scanned} documents scanned, "
                     f"{check.exempted} generator exception"
                     f"{'s' if check.exempted != 1 else ''} declared)")
    return lines
