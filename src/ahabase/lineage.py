"""The lineage of an Epic: concept -> implementation blueprint -> code, and back.

Joined only through declared fields:

- a concept is an ``ontology/ontology-*-blueprint.md`` with a ``**State:**``
  line, at the Epic's level or a subepic's (``subepic/<name>/ontology/``);
- an implementation blueprint (``implementation/implementation-*-blueprint.md``,
  at either level the same way) names its concepts in ``**Implements:**`` and
  its code in ``**Code:**``:
  module names relative to the package (``safe``, ``cli_safe``; a nested
  module as ``sub.module``), or ``none (document blueprint)``;
- a module of the package names its blueprint in its docstring with an
  ``Implements: implementation-...-blueprint`` line.

What the lineage reports, by class (a reflexion model: absences and
divergences between what the knowledge says and what the code is):

- ``ABSENCE concept-without-implementation`` - no blueprint implements the
  concept; reported with the concept's State, never red (a planned or
  defined concept is expected to have none, a concept implemented in part
  may lack one);
- ``DOCUMENT`` - a blueprint that is a document by design; its own class,
  never red;
- ``DIVERGENCE state-contradiction`` - a concept whose State says it is
  implemented (fully: the State begins with ``implemented`` and is not
  ``implemented in part``) while no blueprint implements it;
- ``DIVERGENCE missing-concept`` - ``**Implements:**`` links a concept that
  does not exist;
- ``DIVERGENCE no-code-line`` - a blueprint without a ``**Code:**`` line;
- ``DIVERGENCE missing-module`` - ``**Code:**`` names a module that does not
  exist;
- ``DIVERGENCE unclaimed-module`` - a module no ``**Code:**`` line names;
- ``DIVERGENCE back-link`` - a module without an ``Implements:`` line, or
  one naming a blueprint whose ``**Code:**`` does not name the module.

Any divergence makes the lineage red.

Design and measurement: the AHA-0008 transparency lane, prototype B.

Implements: implementation-ahabase-transparency-blueprint
Blueprint: implementation-ahabase-transparency-blueprint

Capability: lineage-validation
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from .epic import Epic, header, subepics

DOCUMENT_MARKER = "none (document blueprint)"
LINK = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")
BACK_LINK = re.compile(r"^Implements: (implementation-[\w-]+-blueprint)\s*$", re.MULTILINE)
MODULE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")


@dataclass
class Blueprint:
    stem: str
    concepts: list[str]
    code: list[str] | None  # None: no Code line; []: a document blueprint

    @property
    def document(self) -> bool:
        return self.code == []


@dataclass
class Lineage:
    concepts: dict[str, str]  # stem -> State
    blueprints: list[Blueprint]
    modules: dict[str, str | None]  # dotted name -> the blueprint its docstring names
    absences: list[tuple[str, str]] = field(default_factory=list)
    divergences: list[tuple[str, str]] = field(default_factory=list)

    @property
    def holds(self) -> bool:
        return not self.divergences

    def rows(self) -> list[tuple[str, str, str]]:
        """(concept, blueprint, code) - one row per declared join."""
        out = []
        for bp in self.blueprints:
            code = "document" if bp.document else ", ".join(bp.code or []) or "-"
            out += [(c, bp.stem, code) for c in bp.concepts]
        return sorted(out)


def _docstring(path: Path) -> str:
    """The module docstring, empty when absent or unreadable."""
    try:
        return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8", errors="replace"))) or ""
    except SyntaxError:
        return ""


def _claims_implemented(state: str) -> bool:
    """Whether a State says the concept is implemented in full."""
    return state.startswith("implemented") and not state.startswith("implemented in part")


def modules(package: Path | None) -> dict[str, str | None]:
    """Every module of the package by dotted name, with the blueprint it claims.

    A knowledge-only Epic declares no package (AHA-0030): no modules.
    """
    out = {}
    if package is None:
        return out
    for path in sorted(package.rglob("*.py")):
        name = ".".join(path.relative_to(package).with_suffix("").parts)
        claim = BACK_LINK.search(_docstring(path))
        out[name] = claim.group(1) if claim else None
    return out


def blueprint(path: Path) -> Blueprint:
    text = path.read_text(encoding="utf-8", errors="replace")
    implements = header(text, "Implements") or ""
    concepts = [t for t in LINK.findall(implements) if t.startswith("ontology-")]
    line = header(text, "Code")
    if line is None:
        code = None
    elif line == DOCUMENT_MARKER:
        code = []
    else:
        code = [part.strip() for part in line.split(",") if part.strip()]
    return Blueprint(stem=path.stem, concepts=sorted(set(concepts)), code=code)


def concept_docs(epic: Epic) -> list[Path]:
    """Every concept blueprint: the Epic's ontology folder and each subepic's."""
    docs = sorted(epic.ontology.glob("ontology-*-blueprint.md"))
    for sub in subepics(epic):
        ontology = sub / "ontology"
        if ontology.is_dir():
            docs += sorted(ontology.glob("ontology-*-blueprint.md"))
    return docs


def implementation_docs(epic: Epic) -> list[Path]:
    """Every implementation blueprint: the Epic's folder and each subepic's."""
    docs = sorted(epic.implementation.glob("implementation-*-blueprint.md"))
    for sub in subepics(epic):
        implementation = sub / "implementation"
        if implementation.is_dir():
            docs += sorted(implementation.glob("implementation-*-blueprint.md"))
    return docs


def compute(epic: Epic) -> Lineage:
    """The Epic's lineage with its absences and divergences."""
    concepts = {p.stem: header(p.read_text(encoding="utf-8", errors="replace"), "State") or "no State line"
                for p in concept_docs(epic)}
    blueprints = [blueprint(p) for p in implementation_docs(epic)]
    mods = modules(epic.package)
    result = Lineage(concepts=concepts, blueprints=blueprints, modules=mods)

    implemented = {c for bp in blueprints for c in bp.concepts}
    for stem, state in concepts.items():
        if stem in implemented:
            continue
        if _claims_implemented(state):
            result.divergences.append(("state-contradiction", f"{stem} - State says "
                                       f"{state!r} but no blueprint implements it"))
        else:
            result.absences.append(("concept-without-implementation", f"{stem} (State: {state})"))
    for bp in blueprints:
        for concept in bp.concepts:
            if concept not in concepts:
                result.divergences.append(("missing-concept", f"{bp.stem} implements {concept}, "
                                           f"which does not exist"))

    named: dict[str, set[str]] = {}
    for bp in blueprints:
        if bp.code is None:
            result.divergences.append(("no-code-line", bp.stem))
            continue
        for name in bp.code:
            if not MODULE_NAME.match(name) or name not in mods:
                result.divergences.append(("missing-module", f"{bp.stem} names {name!r}, "
                                           f"not a module of {epic.package.name}"))
                continue
            named.setdefault(name, set()).add(bp.stem)

    by_stem = {bp.stem: bp for bp in blueprints}
    for name, claim in mods.items():
        if name not in named:
            result.divergences.append(("unclaimed-module", f"{name} - no **Code:** line names it"))
        if claim is None:
            result.divergences.append(("back-link", f"{name} - no 'Implements:' line in its docstring"))
        elif claim not in by_stem:
            result.divergences.append(("back-link", f"{name} - names {claim}, which does not exist"))
        elif name not in (by_stem[claim].code or []):
            result.divergences.append(("back-link", f"{name} - names {claim}, whose **Code:** "
                                       f"does not name it"))
    return result


def report(lineage: Lineage) -> list[str]:
    """The lines ``ahabase verify`` prints."""
    documents = [bp.stem for bp in lineage.blueprints if bp.document]
    lines = [f"lineage: {len(lineage.concepts)} concepts, {len(lineage.blueprints)} implementation "
             f"blueprints ({len(documents)} documents), {len(lineage.modules)} modules",
             "", "| Concept | Implementation | Code |", "|---|---|---|"]
    lines += [f"| {c} | {b} | {code} |" for c, b, code in lineage.rows()]
    lines.append("")
    lines += [f"ABSENCE {kind}: {what}" for kind, what in lineage.absences]
    lines += [f"DOCUMENT {stem}" for stem in documents]
    lines += [f"DIVERGENCE {kind}: {what}" for kind, what in lineage.divergences]
    verdict = "holds" if lineage.holds else f"{len(lineage.divergences)} divergence(s)"
    lines.append(f"lineage: {verdict}")
    return lines
