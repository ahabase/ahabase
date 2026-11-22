"""The grid4d format core: an Epic's knowledge tree, validated (AHA-0030, row 3 basics).

What the format is - this module is the one home of each rule:

- **Folders:** ``_grid4d/`` holds the knowledge folders (``story``,
  ``ontology``, ``implementation``, ``pattern``, ``playbook``,
  ``issue``, ``idea``, ``metric``), the special folders (``_archive``,
  ``_generated``) and ``subepic/``; any other directory under it is a
  finding. A subepic directory holds the same folders at its level.
- **Identity:** the def file ``_grid4d/story/<NAME>.md`` IS the
  registration - ``**Type:** Epic`` plus its ``**StoryPrefix:**``
  declaration (the Human's 2026-11-20 ruling: no parallel
  configuration); a subepic with its own ``story/`` declares itself
  the same way with ``**Type:** SubEpic``. ``**CodeArtifacts:**`` is
  optional - a knowledge-only Epic is a valid Epic.
- **Naming:** checked statelessly in-tree, derived from what the tree
  declares. The story naming grammar derives from the def file's
  ``StoryPrefix`` - never a hardcoded prefix literal; the knowledge
  folders carry their conventions; a name is unique across the Epic's
  knowledge folders. An unknown or misnamed document is REPORTED
  (new surface: the method copy silently ignores a document no
  type matches).
- **Structure:** a document's required sections are the ``##``
  headings of the pattern template resolved for its type - the
  document-type map's one home is the resolution chain (a subepic's
  own ``subepic/<s>/pattern/<s>-<type>.md``, then the Epic's
  ``_grid4d/pattern/<epic>-<type>.md``, then the package's
  name-neutral default, looked up last and overriding nothing). A
  template is a WHOLE FILE, first match wins; there is no per-key
  merge.
- **Links:** resolved by the package's own open-zone link check
  (``containment.compute``) - one implementation, two entry points.
- **Init:** ``init`` writes a fresh tree's skeleton from the package's
  own epic pattern - the self-registration starts at the pattern, and
  an existing ``_grid4d/`` is refused, never touched.

Stated coverage - what this core does not check: ``_archive/`` is
skipped entirely (inactive knowledge); ``_generated/`` is skipped by
the folder and naming checks but its rendered links are still
resolved (the link arm IS ``containment.compute``, whose skip list
is its own scope - one home per fact); ``story/history/`` is
naming-checked but structure-exempt (archived documents predate
sections); the link check covers rendered links only - fenced code
blocks and code spans are stripped before resolution, so a name
mentioned without linking is not covered; files directly under
``_grid4d/`` sit outside every knowledge folder and are not
name-checked.

Fail-closed: validation only reads, and a tree the core cannot
interpret is reported, never silently ignored.

Implements: implementation-grid4d-format-core-blueprint
Blueprint: implementation-grid4d-format-core-blueprint

Capability: grid4d-format
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from . import containment
from .epic import Epic, header, prefix_from, subepics

#: The knowledge folders of ``_grid4d/`` and of every subepic directory.
KNOWLEDGE_FOLDERS = frozenset({
    "story", "ontology", "implementation", "pattern", "playbook",
    "issue", "idea", "metric",
})

#: The special folders: skipped by validation (inactive and generated knowledge).
SPECIAL_FOLDERS = frozenset({"_archive", "_generated"})

#: The document types the structure check reads and the story engine
#: (R2) mints from: the pattern file's name after its scope prefix.
TYPES = ("epic", "story", "tests", "knowledge-map")

#: The measured naming conventions of the knowledge folders: the flat
#: folders carry lowercase kebab names, ontology and implementation
#: carry their folder prefix (the ontology index file is its own shape),
#: a playbook file ends -playbook, a pattern file is scoped to the
#: Epic or one of its subepics.
_FLAT_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*\.md$")
_ONTOLOGY_NAME = re.compile(r"^(ontology-[\w-]+|00-[\w-]+-ontology-index)\.md$")
_IMPLEMENTATION_NAME = re.compile(r"^implementation-[\w-]+\.md$")
_PLAYBOOK_NAME = re.compile(r"^[\w-]+-playbook\.md$")


@dataclass(frozen=True)
class Finding:
    """One format violation: the rule, the path, the detail - not a boolean."""

    rule: str    # unknown-folder | misnamed-artifact | identity | duplicate-name |
                 # missing-section | unresolved-link
    path: str    # posix path relative to the Epic's root
    detail: str

    def __str__(self) -> str:
        return f"{self.rule}: {self.path} - {self.detail}"


class FormatError(Exception):
    """The format core refuses a write: the message says why."""


def init(root: Path, name: str, prefix: str | None = None) -> Path:
    """Initialize an Epic's tree in ``root``: the folder skeleton and the
    self-registering identity file, written from the package's epic
    pattern (no tree exists yet, so nothing can override it). The
    knowledge-only skeleton carries its placeholders verbatim - the
    visible TODOs for what only the consumer can declare (the package
    location, the overview, the related documents). Returns the identity
    file; refuses a tree that already carries ``_grid4d/``."""
    grid = root / "_grid4d"
    if not root.is_dir():
        raise FormatError(f"{root} is not a directory - create it first")
    if grid.exists():
        raise FormatError(f"{grid} already exists - init never touches an existing tree")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", name):
        raise FormatError(f"the Epic name {name!r} must be letters, digits and dashes")
    namespace = prefix if prefix is not None else name.upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9-]*", namespace):
        raise FormatError(f"the story namespace {namespace!r} must be uppercase "
                          "letters, digits and dashes")
    for folder in sorted(KNOWLEDGE_FOLDERS):
        (grid / folder).mkdir(parents=True, exist_ok=True)
    template = (files("ahabase") / "patterns" / "epic.md").read_text(encoding="utf-8")
    skeleton = fill(template, {"EPIC": name, "PREFIX": namespace})
    # the knowledge-only skeleton declares no package: the loader reads a
    # **CodeArtifacts:** line as a real declaration (measured), and only the
    # consumer knows the path - the line is theirs to add, not ours to fake
    skeleton = re.sub(r"^\*\*CodeArtifacts:\*\*.*\n", "", skeleton,
                      count=1, flags=re.MULTILINE)
    identity = grid / "story" / f"{name}.md"
    identity.write_text(skeleton, encoding="utf-8")
    return identity


@dataclass(frozen=True)
class _Scope:
    """One story-numbering scope: the Epic, or a subepic with its own story/."""

    name: str            # the def file's stem (the identity's name)
    prefix: str          # the namespace its **StoryPrefix:** declares
    grid: Path           # the folder holding this scope's knowledge folders
    subepic: str | None  # the subepic directory name (pattern resolution); None at root


def pattern_template(epic: Epic, doc_type: str, subepic: str | None = None) -> str | None:
    """The WHOLE-FILE template for a document type; first match wins.

    The chain: the subepic's own pattern folder, then the Epic's, then
    the package's name-neutral default - looked up last, so an Epic's
    own template overrides the default and nothing else. None when
    even the package carries no default for the type (no template, no
    structure check).
    """
    if doc_type not in TYPES:
        raise ValueError(f"unknown document type {doc_type!r}")
    candidates = []
    if subepic is not None:
        candidates.append(epic.grid / "subepic" / subepic / "pattern" / f"{subepic}-{doc_type}.md")
    candidates.append(epic.grid / "pattern" / f"{epic.name.lower()}-{doc_type}.md")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8", errors="replace")
    resource = files("ahabase") / "patterns" / f"{doc_type}.md"
    if resource.is_file():
        return resource.read_text(encoding="utf-8")
    return None


def fill(template: str, values: dict[str, str]) -> str:
    """Fill a template: only the provided keys; every other name stays verbatim."""
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template


def _sections(text: str) -> list[str]:
    """The ``## `` headings of a template - the sections it requires."""
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _rel(epic: Epic, path: Path) -> str:
    return path.relative_to(epic.root).as_posix()


def _story_grammar(prefix: str) -> re.Pattern[str]:
    """``<PREFIX>-<number>`` and its -tests, -knowledge-map, -artifact-map
    companions - derived from the def file's declaration, nothing else."""
    suffixes = "|".join(re.escape(s) for s in ("-tests", "-knowledge-map", "-artifact-map"))
    return re.compile(rf"^{re.escape(prefix)}-\d+(?:{suffixes})?\.md$")


def _doc_type(stem: str) -> str | None:
    """The document type a story-set stem names, or None (naming only)."""
    if stem.endswith("-tests"):
        return "tests"
    if stem.endswith("-knowledge-map"):
        return "knowledge-map"
    if stem.endswith("-artifact-map"):
        return None  # part of the story set, no template in this slice
    return "story"


def _check_folders(epic: Epic, grid: Path, findings: list[Finding]) -> None:
    """The directories of one grid level are knowledge folders, special
    folders or (at the root) subepic/ - anything else is a finding.
    Root-level files sit outside every knowledge folder: not name-checked."""
    allowed = KNOWLEDGE_FOLDERS | SPECIAL_FOLDERS | ({"subepic"} if grid == epic.grid else set())
    for child in sorted(grid.iterdir()):
        if child.is_dir() and child.name not in allowed:
            findings.append(Finding(
                "unknown-folder", _rel(epic, child),
                "not a knowledge folder, a special folder or subepic/"))


def _check_story_folder(epic: Epic, scope: _Scope, findings: list[Finding],
                        structure: list[tuple[Path, str, str | None]]) -> None:
    """The story folder: the def file, the Priorities doc, the story set,
    and history/ (naming-checked, structure-exempt)."""
    story = scope.grid / "story"
    grammar = _story_grammar(scope.prefix)
    for path in sorted(story.iterdir()):
        if path.is_dir():
            if path.name == "history":
                # history carries the story set and its companions (lane
                # docs, synthesis - measured: AHA-0008's lanes): prefix-
                # anchored, looser than the active grammar
                archived_grammar = re.compile(
                    rf"^{re.escape(scope.prefix)}-\d+(?:-[\w-]+)?\.md$")
                for archived in sorted(path.iterdir()):
                    if archived.is_dir():
                        findings.append(Finding(
                            "unknown-folder", _rel(epic, archived),
                            "no directory under story/history/"))
                    elif not archived_grammar.match(archived.name):
                        findings.append(Finding(
                            "misnamed-artifact", _rel(epic, archived),
                            f"story/history/ carries the story set and its "
                            f"companions ({scope.prefix}-<number>...)"))
                continue
            findings.append(Finding(
                "unknown-folder", _rel(epic, path),
                "the story folder carries documents and history/ only"))
            continue
        if path.stem == scope.name:
            structure.append((path, "epic", scope.subepic))  # the def file itself
            continue
        if path.name == f"{scope.name}-Priorities.md":
            continue  # the Priorities doc: named by the format, no template
        if grammar.match(path.name):
            doc_type = _doc_type(path.stem)
            if doc_type is not None:
                structure.append((path, doc_type, scope.subepic))
            continue
        findings.append(Finding(
            "misnamed-artifact", _rel(epic, path),
            f"story/ carries the def file, {scope.name}-Priorities.md and the "
            f"story set ({scope.prefix}-<number>...)"))


def _check_knowledge_folder(epic: Epic, folder: Path, name_re: re.Pattern[str],
                            convention: str, findings: list[Finding],
                            names: dict[str, str]) -> None:
    """One non-story knowledge folder: markdown documents, named by the
    folder's convention, no subdirectories, names unique across the Epic."""
    for path in sorted(folder.iterdir()):
        if path.is_dir():
            findings.append(Finding(
                "unknown-folder", _rel(epic, path),
                "a knowledge folder carries documents, not directories"))
            continue
        if path.suffix != ".md":
            findings.append(Finding(
                "misnamed-artifact", _rel(epic, path),
                "a knowledge folder carries markdown documents"))
            continue
        if not name_re.match(path.name):
            findings.append(Finding(
                "misnamed-artifact", _rel(epic, path), convention))
            continue
        first = names.setdefault(path.stem, _rel(epic, path))
        if first != _rel(epic, path):
            findings.append(Finding(
                "duplicate-name", _rel(epic, path),
                f"the name is already used by {first}"))


def _check_structure(epic: Epic, structure: list[tuple[Path, str, str | None]],
                     findings: list[Finding]) -> None:
    """Every pattern-resolved document carries its pattern's ``##`` sections."""
    for path, doc_type, subepic in structure:
        template = pattern_template(epic, doc_type, subepic)
        if template is None:
            continue  # no template resolved: naming already passed, nothing to check
        present = set(_sections(_read(path)))
        for section in _sections(template):
            if section not in present:
                findings.append(Finding(
                    "missing-section", _rel(epic, path),
                    f"no '## {section}' - the {doc_type} pattern requires it"))


def _subepic_scopes(epic: Epic, findings: list[Finding]) -> list[_Scope]:
    """A scope for every subepic that grew its own story/ folder; a subepic
    whose story folder has no readable index is reported, not guessed."""
    scopes = []
    for sub in subepics(epic):
        story = sub / "story"
        if not story.is_dir():
            continue
        indexes = [p for p in sorted(story.glob("*.md"))
                   if header(_read(p), "Type") == "SubEpic"]
        if len(indexes) != 1:
            findings.append(Finding(
                "identity", _rel(epic, story),
                f"expected one SubEpic index (**Type:** SubEpic), found {len(indexes)}"))
            continue
        prefix = prefix_from(_read(indexes[0]))
        if prefix is None:
            findings.append(Finding(
                "identity", _rel(epic, indexes[0]),
                "declares no valid **StoryPrefix:** line (the registration)"))
            continue
        scopes.append(_Scope(name=indexes[0].stem, prefix=prefix, grid=sub, subepic=sub.name))
    return scopes


def validate(epic: Epic) -> list[Finding]:
    """Validate an Epic's ``_grid4d/`` tree: folders, identity, naming,
    structure, links. Reads only; every violation reported namingly."""
    findings: list[Finding] = []
    structure: list[tuple[Path, str, str | None]] = []
    names: dict[str, str] = {}

    # every grid level gets the folder and naming checks: the root and
    # every subepic directory, whether or not the subepic grew a story/
    grids = [epic.grid] + subepics(epic)
    scopes = [_Scope(name=epic.name, prefix=epic.story_prefix,
                     grid=epic.grid, subepic=None)]
    scopes += _subepic_scopes(epic, findings)

    pattern_scopes = {epic.name.lower()} | {sub.name for sub in subepics(epic)}
    pattern_name = re.compile(
        r"^(?:" + "|".join(sorted(re.escape(s) for s in pattern_scopes)) + r")-[\w-]+\.md$")

    for grid in grids:
        _check_folders(epic, grid, findings)
        for folder, name_re, convention in (
            ("ontology", _ONTOLOGY_NAME, "ontology/ carries ontology-*.md (and its 00-*-ontology-index)"),
            ("implementation", _IMPLEMENTATION_NAME, "implementation/ carries implementation-*.md"),
            ("pattern", pattern_name, "pattern/ carries <scope>-*.md (the Epic's or a subepic's scope)"),
            ("playbook", _PLAYBOOK_NAME, "playbook/ carries *-playbook.md"),
            ("issue", _FLAT_NAME, "issue/ carries lowercase kebab names"),
            ("idea", _FLAT_NAME, "idea/ carries lowercase kebab names"),
            ("metric", _FLAT_NAME, "metric/ carries lowercase kebab names"),
        ):
            path = grid / folder
            if path.is_dir():
                _check_knowledge_folder(epic, path, name_re, convention, findings, names)

    for scope in scopes:
        if (scope.grid / "story").is_dir():
            _check_story_folder(epic, scope, findings, structure)

    _check_structure(epic, structure, findings)

    links = containment.compute(epic)
    for where, targets in links.unresolved.items():
        for target in targets:
            findings.append(Finding(
                "unresolved-link", where, f"does not resolve: {target}"))

    return sorted(findings, key=lambda f: (f.path, f.rule))
