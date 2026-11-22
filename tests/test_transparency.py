"""The transparency core on fictional Epic trees: the ontology map and the lineage."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ahabase import lineage, ontology_map
from ahabase.cli import build_cli
from ahabase.epic import EpicError, load
from ahabase.plugins import Registry


def main_cli():
    """The CLI with the package's commands only (no installed plugin)."""
    return build_cli(Registry())

INDEX = """# demo Ontology

## Vocabulary

### Things

- [Alpha](ontology-alpha-blueprint) - the first
- [Beta](ontology-beta-blueprint) - the second

### Later

- [Gamma](ontology-gamma-blueprint) - planned

## Relations

- prose only

## Related

- [DEMO](DEMO)
"""

CONCEPT = """# {name} Blueprint

**State:** {state}

## Relations

{relations}

## Related
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def epic_tree(tmp_path: Path) -> Path:
    """A small Epic whose lineage holds: two implemented concepts, one planned."""
    root = tmp_path / "demo"
    _write(root / "_grid4d/story/DEMO.md",
           "# DEMO\n\n**Type:** Epic\n**StoryPrefix:** DEMO-\n**CodeArtifacts:** src/demo\n")
    _write(root / "_grid4d/ontology/00-demo-ontology-index.md", INDEX)
    _write(root / "_grid4d/ontology/ontology-alpha-blueprint.md", CONCEPT.format(
        name="Alpha", state="implemented",
        relations="- **uses** → [Beta](ontology-beta-blueprint)\n- **mentions** → a plain word"))
    _write(root / "_grid4d/ontology/ontology-beta-blueprint.md", CONCEPT.format(
        name="Beta", state="implemented", relations="- **feeds** → [Gamma](ontology-gamma-blueprint)"))
    _write(root / "_grid4d/ontology/ontology-gamma-blueprint.md", CONCEPT.format(
        name="Gamma", state="planned", relations=""))
    _write(root / "_grid4d/implementation/implementation-demo-core-blueprint.md",
           "# Core\n\n**Implements:** [ontology-alpha-blueprint](ontology-alpha-blueprint), "
           "[ontology-beta-blueprint](ontology-beta-blueprint)\n"
           "**Code:** __init__, core, sub.__init__, sub.deep\n")
    _write(root / "_grid4d/implementation/implementation-demo-notes-blueprint.md",
           "# Notes\n\n**Implements:** [ontology-beta-blueprint](ontology-beta-blueprint)\n"
           "**Code:** none (document blueprint)\n")
    back = '"""{doc}\n\nImplements: implementation-demo-core-blueprint\n"""\n'
    _write(root / "src/demo/__init__.py", back.format(doc="The package."))
    _write(root / "src/demo/core.py", '"""The core.\n\nImplements: implementation-demo-core-blueprint\n'
           'Capability: demo-core\n"""\n')
    _write(root / "src/demo/sub/deep.py", back.format(doc="A nested module."))
    _write(root / "src/demo/sub/__init__.py", back.format(doc="Sub."))
    _write(root / "_grid4d/ontology/ontology-capabilities-index.md",
           "# demo Capabilities\n\n## Taxonomy\n\n"
           "- **demo-core** → [Alpha](ontology-alpha-blueprint) - the core's capability\n")
    return root


def _classes(root: Path) -> list[str]:
    return [kind for kind, _ in lineage.compute(load(root)).divergences]


# ---- reading the tree ------------------------------------------------------

def test_load_reads_identity_and_package(epic_tree):
    epic = load(epic_tree)
    assert epic.identity.name == "DEMO.md"
    assert epic.package == (epic_tree / "src/demo").resolve()


def test_load_accepts_a_knowledge_only_epic(epic_tree):
    """Identity is split from the package (AHA-0030): no CodeArtifacts
    line means a knowledge-only Epic, not a refusal."""
    ident = epic_tree / "_grid4d/story/DEMO.md"
    ident.write_text(ident.read_text(encoding="utf-8").replace("**CodeArtifacts:** src/demo\n", ""), encoding="utf-8")
    epic = load(epic_tree)
    assert epic.package is None


def test_load_refuses_a_package_outside_the_epic(epic_tree, tmp_path):
    (tmp_path / "elsewhere").mkdir()
    ident = epic_tree / "_grid4d/story/DEMO.md"
    ident.write_text(ident.read_text(encoding="utf-8").replace("src/demo", "../elsewhere"), encoding="utf-8")
    with pytest.raises(EpicError, match="not a directory inside"):
        load(epic_tree)


# ---- the lineage -------------------------------------------------------------

def test_lineage_holds_with_absence_and_document(epic_tree):
    result = lineage.compute(load(epic_tree))
    assert result.holds, result.divergences
    assert [kind for kind, _ in result.absences] == ["concept-without-implementation"]
    assert "ontology-gamma-blueprint (State: planned)" in result.absences[0][1]
    assert [bp.stem for bp in result.blueprints if bp.document] == ["implementation-demo-notes-blueprint"]
    report = lineage.report(result)
    assert report[-1] == "lineage: holds"
    assert "DOCUMENT implementation-demo-notes-blueprint" in report


def test_nested_module_joins_through_its_dotted_name(epic_tree):
    result = lineage.compute(load(epic_tree))
    assert "sub.deep" in result.modules
    assert ("ontology-alpha-blueprint", "implementation-demo-core-blueprint",
            "__init__, core, sub.__init__, sub.deep") in result.rows()


def test_blueprint_without_code_line_diverges(epic_tree):
    notes = epic_tree / "_grid4d/implementation/implementation-demo-notes-blueprint.md"
    notes.write_text(notes.read_text(encoding="utf-8").replace("**Code:** none (document blueprint)\n", ""), encoding="utf-8")
    assert _classes(epic_tree) == ["no-code-line"]


def test_code_naming_a_missing_module_diverges(epic_tree):
    core = epic_tree / "_grid4d/implementation/implementation-demo-core-blueprint.md"
    core.write_text(core.read_text(encoding="utf-8").replace("**Code:** __init__,", "**Code:** __init__, ghost,"), encoding="utf-8")
    assert _classes(epic_tree) == ["missing-module"]


def test_path_form_in_code_line_is_not_a_module(epic_tree):
    core = epic_tree / "_grid4d/implementation/implementation-demo-core-blueprint.md"
    core.write_text(core.read_text(encoding="utf-8").replace("core,", "src/demo/core.py,"), encoding="utf-8")
    assert sorted(_classes(epic_tree)) == ["back-link", "missing-module", "unclaimed-module"]


def test_module_no_blueprint_names_diverges(epic_tree):
    _write(epic_tree / "src/demo/stray.py",
           '"""Stray.\n\nImplements: implementation-demo-core-blueprint\n"""\n')
    assert sorted(_classes(epic_tree)) == ["back-link", "unclaimed-module"]


def test_missing_back_link_diverges(epic_tree):
    (epic_tree / "src/demo/core.py").write_text('"""The core, no back-link."""\n', encoding="utf-8")
    assert _classes(epic_tree) == ["back-link"]


def test_back_link_in_a_comment_does_not_count(epic_tree):
    (epic_tree / "src/demo/core.py").write_text(
        '"""The core."""\n# Implements: implementation-demo-core-blueprint\n', encoding="utf-8")
    assert _classes(epic_tree) == ["back-link"]


def test_back_link_to_an_unknown_blueprint_diverges(epic_tree):
    (epic_tree / "src/demo/core.py").write_text(
        '"""The core.\n\nImplements: implementation-demo-gone-blueprint\n"""\n', encoding="utf-8")
    assert _classes(epic_tree) == ["back-link"]


def test_back_link_to_a_blueprint_that_does_not_name_the_module(epic_tree):
    (epic_tree / "src/demo/core.py").write_text(
        '"""The core.\n\nImplements: implementation-demo-notes-blueprint\n"""\n', encoding="utf-8")
    assert _classes(epic_tree) == ["back-link"]


def test_implements_naming_a_missing_concept_diverges(epic_tree):
    """Local review on f619ada, finding 1a."""
    core = epic_tree / "_grid4d/implementation/implementation-demo-core-blueprint.md"
    core.write_text(core.read_text(encoding="utf-8").replace(
        "**Implements:** ", "**Implements:** [Ghost](ontology-ghost-blueprint), "))
    assert _classes(epic_tree) == ["missing-concept"]


@pytest.mark.parametrize("state, red", [
    ("implemented", True),
    ("implemented (the safe)", True),
    ("implemented in part - one half", False),
    ("defined; the check is planned", False),
    ("planned", False),
])
def test_state_against_implementation(epic_tree, state, red):
    """Local review on f619ada, finding 1b: a State claiming 'implemented' needs a blueprint."""
    gamma = epic_tree / "_grid4d/ontology/ontology-gamma-blueprint.md"
    gamma.write_text(gamma.read_text(encoding="utf-8").replace("**State:** planned", f"**State:** {state}"), encoding="utf-8")
    result = lineage.compute(load(epic_tree))
    assert ([k for k, _ in result.divergences] == ["state-contradiction"]) is red
    assert (not result.absences) is red


# ---- the ontology map ----------------------------------------------------------

def test_map_has_facets_nodes_and_only_concept_edges(epic_tree):
    built = ontology_map.build(load(epic_tree))
    assert (built.concepts, built.facets, built.edges) == (3, 2, 2)
    assert "subgraph F0[Things]" in built.block
    assert "alpha -->|uses| beta" in built.block
    assert "plain word" not in built.block


def test_map_is_written_before_related_and_idempotent(epic_tree):
    epic = load(epic_tree)
    path, current, wanted, _ = ontology_map.expected(epic)
    assert current != wanted
    assert wanted.index(ontology_map.BEGIN) < wanted.index("## Related")
    path.write_text(wanted, encoding="utf-8")
    _, again, wanted_again, _ = ontology_map.expected(epic)
    assert again == wanted_again


def test_map_replaces_only_between_the_markers(epic_tree):
    epic = load(epic_tree)
    path, _, wanted, _ = ontology_map.expected(epic)
    path.write_text(wanted.replace("## Related", "## Related\n\n- a hand line kept"), encoding="utf-8")
    _, current, regenerated, _ = ontology_map.expected(epic)
    assert regenerated == current
    assert "- a hand line kept" in regenerated


@pytest.mark.parametrize("damage", ["drop-end", "drop-begin", "second-begin", "end-first"])
def test_unbalanced_markers_stop_without_writing(epic_tree, damage):
    """Local review on f619ada, finding 2: a stray marker must not cost hand text."""
    epic = load(epic_tree)
    path, _, wanted, _ = ontology_map.expected(epic)
    B, E = ontology_map.BEGIN, ontology_map.END
    text = wanted.replace(B, f"{B}\n- a hand line")
    text = {"drop-end": text.replace(E, ""),
            "drop-begin": text.replace(B, ""),
            "second-begin": text.replace("## Related", f"{B}\n## Related"),
            "end-first": text.replace(B, "@@").replace(E, B).replace("@@", E)}[damage]
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ontology_map.MarkerError, match="unbalanced"):
        ontology_map.expected(epic)
    result = CliRunner().invoke(main_cli(), ["ontology", "graph", "--root", str(epic_tree)])
    assert result.exit_code == 1 and "unbalanced" in result.output
    assert path.read_text(encoding="utf-8") == text


# ---- the doors -------------------------------------------------------------------

def test_cli_verify_exit_codes(epic_tree):
    runner = CliRunner()
    ok = runner.invoke(main_cli(), ["verify", "--root", str(epic_tree)])
    assert ok.exit_code == 0, ok.output
    assert "lineage: holds" in ok.output
    assert "capabilities: holds" in ok.output
    assert "links: holds" in ok.output
    (epic_tree / "src/demo/core.py").write_text('"""No back-link."""\n', encoding="utf-8")
    red = runner.invoke(main_cli(), ["verify", "--root", str(epic_tree)])
    assert red.exit_code == 1
    assert "DIVERGENCE back-link: core" in red.output


def test_cli_verify_on_a_tree_that_is_not_an_epic(tmp_path):
    result = CliRunner().invoke(main_cli(), ["verify", "--root", str(tmp_path)])
    assert result.exit_code == 2
    assert "not an Epic" in result.output


def test_cli_graph_write_then_check(epic_tree):
    runner = CliRunner()
    stale = runner.invoke(main_cli(), ["ontology", "graph", "--root", str(epic_tree), "--check"])
    assert stale.exit_code == 1 and "stale" in stale.output
    wrote = runner.invoke(main_cli(), ["ontology", "graph", "--root", str(epic_tree)])
    assert wrote.exit_code == 0 and "written" in wrote.output
    current = runner.invoke(main_cli(), ["ontology", "graph", "--root", str(epic_tree), "--check"])
    assert current.exit_code == 0 and "current" in current.output
    index = epic_tree / "_grid4d/ontology/00-demo-ontology-index.md"
    index.write_text(index.read_text(encoding="utf-8").replace("flowchart LR", "flowchart LR\n    %% hand edit"), encoding="utf-8")
    edited = runner.invoke(main_cli(), ["ontology", "graph", "--root", str(epic_tree), "--check"])
    assert edited.exit_code == 1 and "stale" in edited.output


def test_the_package_lineage_holds():
    """The package's own Epic is the first verified instance."""
    root = Path(__file__).resolve().parent.parent
    if not (root / "_grid4d").is_dir():
        pytest.skip("the Epic's knowledge is not part of the sdist")
    result = lineage.compute(load(root))
    assert result.holds, result.divergences


# ---- the subepic level (AHA-0018) ------------------------------------------

INDEX_MOVED = """# demo Ontology

## Vocabulary

### Things

- [Beta](ontology-beta-blueprint) - the second

### Later

- [Gamma](ontology-gamma-blueprint) - planned

## Relations

- prose only

## Related

- [DEMO](DEMO)
"""

SUB_INDEX = """# demo-safe Ontology

## Taxonomy

- **extends:** [00-demo-ontology-index](00-demo-ontology-index)

## Vocabulary

### Values

- [Alpha](ontology-alpha-blueprint) - the first

## Relations

- prose only

## Constraints

- prose only

## Related

- [DEMO-SAFE](DEMO-SAFE)
"""


@pytest.fixture
def subepic_tree(epic_tree: Path) -> Path:
    """The same Epic with alpha and its implementation moved into a subepic."""
    sub = epic_tree / "_grid4d/subepic/demo-safe"
    _write(sub / "story/DEMO-SAFE.md",
           "# DEMO-SAFE\n\n**Type:** SubEpic\n**Inherits:** demo\n**StoryPrefix:** DEMO-SAFE-\n")
    _write(sub / "ontology/00-demo-safe-ontology-index.md", SUB_INDEX)
    alpha = epic_tree / "_grid4d/ontology/ontology-alpha-blueprint.md"
    _write(sub / "ontology/ontology-alpha-blueprint.md", alpha.read_text(encoding="utf-8"))
    alpha.unlink()
    core = epic_tree / "_grid4d/implementation/implementation-demo-core-blueprint.md"
    _write(sub / "implementation/implementation-demo-core-blueprint.md",
           core.read_text(encoding="utf-8"))
    core.unlink()
    index = epic_tree / "_grid4d/ontology/00-demo-ontology-index.md"
    index.write_text(INDEX_MOVED, encoding="utf-8")
    return epic_tree


def test_lineage_joins_through_both_levels(subepic_tree):
    """A subepic's blueprint implementing an Epic-level concept still joins."""
    result = lineage.compute(load(subepic_tree))
    assert result.holds, result.divergences
    assert ("ontology-alpha-blueprint", "implementation-demo-core-blueprint",
            "__init__, core, sub.__init__, sub.deep") in result.rows()
    assert ("ontology-beta-blueprint", "implementation-demo-core-blueprint",
            "__init__, core, sub.__init__, sub.deep") in result.rows()


def test_a_subepic_concept_marked_implemented_without_its_blueprint_diverges(subepic_tree):
    """The state-contradiction check reads the subepic's concepts too."""
    gone = subepic_tree / "_grid4d/subepic/demo-safe/implementation/implementation-demo-core-blueprint.md"
    gone.unlink()
    result = lineage.compute(load(subepic_tree))
    assert {kind for kind, _ in result.divergences} == {
        "state-contradiction", "unclaimed-module", "back-link"}
    assert any("ontology-alpha-blueprint" in what for kind, what in result.divergences
               if kind == "state-contradiction")


def test_epic_map_shows_the_subepic_as_one_unit(subepic_tree):
    built = ontology_map.build(load(subepic_tree))
    assert "demo_safe[demo-safe]" in built.block
    assert "alpha[alpha]" not in built.block
    assert "beta[beta]" in built.block


def test_subepic_map_renders_its_own_concepts_only(subepic_tree):
    scopes = ontology_map.expected_scopes(load(subepic_tree))
    assert [path.name for path, _, _, _ in scopes] == [
        "00-demo-ontology-index.md", "00-demo-safe-ontology-index.md"]
    sub_block = scopes[1][3].block
    assert "alpha[alpha]" in sub_block
    assert "beta[beta]" not in sub_block
    assert "Capability subepics" not in sub_block


def test_a_subepic_without_an_ontology_is_no_scope(epic_tree):
    _write(epic_tree / "_grid4d/subepic/demo-bare/story/DEMO-BARE.md",
           "# DEMO-BARE\n\n**Type:** SubEpic\n**Inherits:** demo\n**StoryPrefix:** DEMO-BARE-\n")
    scopes = ontology_map.expected_scopes(load(epic_tree))
    assert len(scopes) == 1


def test_a_subepic_with_two_indexes_refuses(subepic_tree):
    _write(subepic_tree / "_grid4d/subepic/demo-safe/ontology/00-extra-ontology-index.md",
           SUB_INDEX)
    with pytest.raises(EpicError, match="00-\\*-ontology-index.md"):
        ontology_map.expected_scopes(load(subepic_tree))


def test_graph_writes_and_checks_both_levels(subepic_tree):
    runner = CliRunner()
    wrote = runner.invoke(main_cli(), ["ontology", "graph", "--root", str(subepic_tree)])
    assert wrote.exit_code == 0, wrote.output
    assert wrote.output.count("written to") == 2
    current = runner.invoke(main_cli(), ["ontology", "graph", "--root", str(subepic_tree), "--check"])
    assert current.exit_code == 0 and current.output.count("current in") == 2
    sub_index = subepic_tree / "_grid4d/subepic/demo-safe/ontology/00-demo-safe-ontology-index.md"
    sub_index.write_text(sub_index.read_text(encoding="utf-8").replace(
        "flowchart LR", "flowchart LR\n    %% hand edit"), encoding="utf-8")
    stale = runner.invoke(main_cli(), ["ontology", "graph", "--root", str(subepic_tree), "--check"])
    assert stale.exit_code == 1
    assert "stale in 00-demo-safe-ontology-index.md" in stale.output
    assert "current in 00-demo-ontology-index.md" in stale.output


def test_verify_holds_on_a_tree_with_a_subepic(subepic_tree):
    ok = CliRunner().invoke(main_cli(), ["verify", "--root", str(subepic_tree)])
    assert ok.exit_code == 0, ok.output
    assert "lineage: holds" in ok.output
