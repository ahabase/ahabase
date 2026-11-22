"""The capability vocabulary: what the Epic's code declares, the ontology must define.

One check, generic over any Epic: the code artifacts the identity document
declares are scanned for ``Capability: <name>`` lines - the whole file
text, the same surface the method CLI's capability gate reads, not the
parsed docstring alone - and every name must be defined in the Epic's
``_grid4d/ontology/ontology-capabilities-index.md`` (a ``- **name** →
[concept]…`` bullet). A name in code that the index does not define is a
finding - the taxonomy is the single vocabulary, and drift fails the
check instead of silently growing.

The reverse direction is not checked: an index may define a capability
ahead of the code that will carry it (the Minimal rule - a concept is
defined when the next steps build on it).

Implements: implementation-ahabase-transparency-blueprint
Blueprint: implementation-ahabase-transparency-blueprint

Capability: capability-vocabulary
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .epic import Epic

#: ``Capability: <name>`` lines in the file text of the code artifacts
#: (whole text, the method CLI's gate surface - not the docstring alone).
CAPABILITY_RE = re.compile(r"Capability:\s*([a-z0-9-]+)")

#: ``- **name** →`` bullets of the capabilities index.
INDEX_RE = re.compile(r"^- \*\*([a-z0-9-]+)\*\*", re.MULTILINE)

INDEX_NAME = "ontology-capabilities-index.md"


@dataclass(frozen=True)
class Report:
    """What the capability check found: undefined names, per module.

    ``declared`` is how many capability names the index defines (0 when
    it is absent).
    """

    undefined: dict[str, list[str]] = field(default_factory=dict)
    index_missing: bool = False
    declared: int = 0

    @property
    def holds(self) -> bool:
        return not self.undefined and not self.index_missing


def compute(epic: Epic) -> Report:
    """Compare the Epic's code capabilities against its capabilities index."""
    index_path = epic.ontology / INDEX_NAME
    index_names: set[str] = set()
    index_missing = not index_path.exists()
    if not index_missing:
        index_names = set(INDEX_RE.findall(index_path.read_text(encoding="utf-8",
                                                                errors="replace")))

    undefined: dict[str, list[str]] = {}
    if epic.package is not None and epic.package.is_dir():
        for py_file in sorted(epic.package.rglob("*.py")):
            names = set(CAPABILITY_RE.findall(
                py_file.read_text(encoding="utf-8", errors="replace")))
            missing = sorted(names - index_names)
            if missing:
                # Posix key on every OS: str() would report backslashes on
                # Windows, whose CI lane asserts the same form as the rest.
                undefined[py_file.relative_to(epic.root).as_posix()] = missing

    report = Report(undefined=undefined, index_missing=index_missing,
                    declared=len(index_names))
    return report


def report(check: Report) -> list[str]:
    """Lines to print for the capability check; the last line is the verdict."""
    lines: list[str] = []
    for where, names in sorted(check.undefined.items()):
        for name in names:
            lines.append(f"CAPABILITY undefined: {name} ({where}) - "
                         f"define it in ontology/{INDEX_NAME}")
    if check.index_missing:
        lines.append(f"CAPABILITY index missing: ontology/{INDEX_NAME} "
                     "does not exist - the Epic declares no capability vocabulary")
    if check.holds:
        lines.append(f"capabilities: holds ({check.declared} defined)")
    return lines
