"""The ontology map: a projection of the Epic's ontology, generated into its index.

The map is a mermaid flowchart: one subgraph per facet of the index's
``## Vocabulary`` (its ``###`` headings), one node per concept linked
there, and one typed edge per Relations bullet of a concept blueprint
(``- **relation** → [Target](ontology-target-blueprint)``) whose target is
also a concept of the index. Maps render at their own level (AHA-0018):
the Epic's index shows the Epic-level concepts plus one node per subepic
that carries its own ontology index; a subepic's index carries the
detailed map of its own concepts. It is written between the ontology-map
markers, never by hand; generating it again over its own output changes no
byte, so a hand edit or a stale map is found by comparison (``--check``).

Design and measurement: the AHA-0008 transparency lane, prototype B.

Implements: implementation-ahabase-transparency-blueprint
Blueprint: implementation-ahabase-transparency-blueprint

Capability: ontology-projection
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .epic import Epic, EpicError, subepics

BEGIN, END = "<!-- ontology-map:begin -->", "<!-- ontology-map:end -->"
SECTION = "## Ontology map"
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
RELATION = re.compile(r"^- \*\*([\w ]+)\*\* → \[[^\]]+\]\((ontology-[\w-]+-blueprint)\)",
                      re.MULTILINE)


@dataclass(frozen=True)
class Map:
    block: str
    concepts: int
    facets: int
    edges: int


def index_path(epic: Epic) -> Path:
    """The Epic's ontology index: the one ``00-*-ontology-index.md``."""
    found = sorted(epic.ontology.glob("00-*-ontology-index.md"))
    if len(found) != 1:
        raise EpicError(f"expected one 00-*-ontology-index.md in {epic.ontology}, "
                        f"found {len(found)}")
    return found[0]


def subepic_scopes(epic: Epic) -> list[tuple[str, Path, Path]]:
    """(name, index, ontology folder) per subepic carrying an ontology index.

    A subepic is a directory of ``_grid4d/subepic/``; when it grows its
    own ``ontology/`` holding one ``00-*-ontology-index.md``, that index
    is a projection scope of its own - and one unit node of the Epic's
    map (the level rule, AHA-0018).
    """
    out = []
    for sub in subepics(epic):
        ontology = sub / "ontology"
        if not ontology.is_dir():
            continue
        found = sorted(ontology.glob("00-*-ontology-index.md"))
        if len(found) != 1:
            raise EpicError(f"expected one 00-*-ontology-index.md in {ontology}, "
                            f"found {len(found)}")
        out.append((sub.name, found[0], ontology))
    return out


def _section(text: str, heading: str) -> str:
    """The body of a ``## heading`` section, empty when absent."""
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text,
                      re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def facets(index_text: str) -> list[tuple[str, list[str]]]:
    """(facet, [concept blueprint stems]) in the order of the Vocabulary."""
    out = []
    for match in re.finditer(r"^### (.+?)\n(.*?)(?=^### |\Z)", _section(index_text, "Vocabulary"),
                             re.MULTILINE | re.DOTALL):
        stems = []
        for _, target in LINK.findall(match.group(2)):
            if target.startswith("ontology-") and target not in stems:
                stems.append(target)
        out.append((match.group(1).strip(), stems))
    return out


def relations(ontology: Path) -> list[tuple[str, str, str]]:
    """(source stem, relation, target stem) from every concept blueprint's Relations."""
    edges = []
    for path in sorted(ontology.glob("ontology-*-blueprint.md")):
        body = _section(path.read_text(encoding="utf-8", errors="replace"), "Relations")
        for label, target in RELATION.findall(body):
            edges.append((path.stem, label.strip(), target))
    return edges


def _node(stem: str) -> str:
    return stem.removeprefix("ontology-").removesuffix("-blueprint").replace("-", "_")


def _label(stem: str) -> str:
    return stem.removeprefix("ontology-").removesuffix("-blueprint").replace("-", " ")


def _unit(name: str) -> str:
    """The node id of a subepic unit: the subepic's own name."""
    return name.replace("-", "_")


def build_at(index: Path, ontology: Path, units: list[str]) -> Map:
    """The map of one scope: the concepts its index's Vocabulary links.

    ``units`` names the subepics that appear as one node each - only the
    Epic's own map carries them; a subepic's map stays at its own level.
    """
    groups = facets(index.read_text(encoding="utf-8", errors="replace"))
    known = {stem for _, stems in groups for stem in stems}
    edges = [e for e in relations(ontology) if e[0] in known and e[2] in known]
    lines = ["```mermaid", "flowchart LR"]
    for number, (name, stems) in enumerate(groups):
        lines.append(f"    subgraph F{number}[{name}]")
        lines += [f"        {_node(s)}[{_label(s)}]" for s in stems]
        lines.append("    end")
    if units:
        lines.append(f"    subgraph F{len(groups)}[Capability subepics]")
        lines += [f"        {_unit(n)}[{n}]" for n in units]
        lines.append("    end")
    lines += [f"    {_node(s)} -->|{label}| {_node(t)}" for s, label, t in edges]
    lines.append("```")
    return Map(block="\n".join(lines), concepts=len(known), facets=len(groups),
               edges=len(edges))


def build(epic: Epic) -> Map:
    """The Epic's own map: its concepts plus one unit per capability subepic."""
    return build_at(index_path(epic), epic.ontology,
                    [name for name, _, _ in subepic_scopes(epic)])


class MarkerError(Exception):
    """The markers are not one balanced pair; nothing is written."""


def _markers_balanced(index_text: str) -> bool:
    """None of the markers, or exactly one BEGIN before exactly one END."""
    begins, ends = index_text.count(BEGIN), index_text.count(END)
    if begins == ends == 0:
        return False
    if begins == ends == 1 and index_text.index(BEGIN) < index_text.index(END):
        return True
    raise MarkerError(f"the ontology-map markers are unbalanced ({begins} begin, {ends} end) - "
                      f"repair them by hand; nothing was written")


def render(index_text: str, block: str) -> str:
    """The index with the map between the markers (a new section before Related).

    Text outside the markers is never touched; markers that are not one
    balanced pair stop it (MarkerError), because a guess could replace hand
    text between a stray marker and the real one.
    """
    framed = f"{BEGIN}\n{block}\n{END}"
    if _markers_balanced(index_text):
        return re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: framed,
                      index_text, count=1, flags=re.DOTALL)
    section = f"{SECTION}\n\nGenerated by `ahabase ontology graph` - never edit by hand.\n\n{framed}\n\n"
    if "\n## Related" in index_text:
        head, _, tail = index_text.partition("\n## Related")
        return f"{head.rstrip()}\n\n{section}## Related{tail}"
    return f"{index_text.rstrip()}\n\n{section}"


def expected(epic: Epic) -> tuple[Path, str, str, Map]:
    """(index path, current text, text with the current map, the map)."""
    return expected_scopes(epic)[0]


def expected_scopes(epic: Epic) -> list[tuple[Path, str, str, Map]]:
    """Every scope's (index path, current text, wanted text, map).

    The Epic's own scope first, then each subepic's, by name - the order
    ``ahabase ontology graph`` writes and checks them in.
    """
    scopes = [(index_path(epic), epic.ontology, [n for n, _, _ in subepic_scopes(epic)])]
    scopes += [(index, ontology, []) for _, index, ontology in subepic_scopes(epic)]
    out = []
    for index, ontology, units in scopes:
        current = index.read_text(encoding="utf-8", errors="replace")
        built = build_at(index, ontology, units)
        out.append((index, current, render(current, built.block), built))
    return out
