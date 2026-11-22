"""The capability vocabulary gate and the open-zone link containment (AHA-0016)."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ahabase import capabilities, containment
from ahabase.cli import build_cli
from ahabase.epic import load
from ahabase.plugins import Registry

from test_transparency import epic_tree  # noqa: F401 - the shared demo-Epic fixture


def main_cli():
    """The CLI with the package's commands only (no installed plugin)."""
    return build_cli(Registry())


# ---- the capability gate ---------------------------------------------------------

def test_gate_holds_when_code_names_are_defined(epic_tree):
    check = capabilities.compute(load(epic_tree))
    assert check.holds and check.declared == 1
    assert capabilities.report(check) == ["capabilities: holds (1 defined)"]


def test_gate_fails_an_undefined_name(epic_tree):
    core = epic_tree / "src/demo/core.py"
    core.write_text(core.read_text(encoding="utf-8").replace(
        "Capability: demo-core", "Capability: no-such-capability"), encoding="utf-8")
    check = capabilities.compute(load(epic_tree))
    assert not check.holds
    assert check.undefined == {"src/demo/core.py": ["no-such-capability"]}
    assert any("CAPABILITY undefined: no-such-capability (src/demo/core.py)" in line
               for line in capabilities.report(check))


def test_gate_fails_a_missing_index(epic_tree):
    (epic_tree / "_grid4d/ontology/ontology-capabilities-index.md").unlink()
    check = capabilities.compute(load(epic_tree))
    assert not check.holds and check.index_missing
    assert any("CAPABILITY index missing" in line
               for line in capabilities.report(check))


def test_the_cli_gates_capabilities(epic_tree):
    core = epic_tree / "src/demo/core.py"
    core.write_text('"""The core.\n\n    Capability: planted\n\n'
                    'Implements: implementation-demo-core-blueprint\n"""\n', encoding="utf-8")
    result = CliRunner().invoke(main_cli(), ["verify", "--root", str(epic_tree)])
    assert result.exit_code == 1
    assert "CAPABILITY undefined: planted" in result.output


# ---- the link containment --------------------------------------------------------

def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_links_hold_on_the_demo_tree(epic_tree):
    check = containment.compute(load(epic_tree))
    assert check.holds and check.scanned >= 6


def test_a_hand_written_link_out_of_the_repository_fails(epic_tree):
    doc = epic_tree / "_grid4d/ontology/ontology-alpha-blueprint.md"
    doc.write_text(doc.read_text(encoding="utf-8")
                   + "\n- [Elsewhere](implementation-story-blueprint-x)\n", encoding="utf-8")
    check = containment.compute(load(epic_tree))
    assert not check.holds
    assert check.unresolved == {"_grid4d/ontology/ontology-alpha-blueprint.md":
                                ["implementation-story-blueprint-x"]}
    assert any(line.startswith("LINK unresolved: _grid4d/ontology/ontology-alpha-blueprint.md"
                               " -> implementation-story-blueprint-x")
               for line in containment.report(check))


def test_the_declared_generator_exceptions_ride(epic_tree):
    doc = epic_tree / "_grid4d/story/note.md"
    _write(doc, "- [Story pattern](implementation-story-blueprint) - minted header\n")
    check = containment.compute(load(epic_tree))
    assert check.holds and check.exempted == 1


def test_only_declared_hook_rows_ride(epic_tree):
    """Review of the pin, finding 4: the row shape exempts nothing by itself."""
    km = epic_tree / "_grid4d/story/DEMO-knowledge-map.md"
    _write(km, "## Consumed\n\n"
               "- [Concepts](DEMO-Concepts) (Generated)\n"
               "- [a rule](evolucean/evolucean-story) (Rule)\n")
    check = containment.compute(load(epic_tree))
    assert check.holds and check.exempted == 2


def test_a_name_only_dead_row_in_a_map_fails(epic_tree):
    """A logger row without the declarations is a dead link when unresolved."""
    km = epic_tree / "_grid4d/story/DEMO-knowledge-map.md"
    _write(km, "## Consumed\n\n"
               "- [Gone](a-page-that-does-not-exist) (Rule)\n")
    check = containment.compute(load(epic_tree))
    assert not check.holds
    assert check.unresolved == {"_grid4d/story/DEMO-knowledge-map.md":
                                ["a-page-that-does-not-exist"]}


def test_hand_written_prose_in_a_knowledge_map_does_not_ride(epic_tree):
    km = epic_tree / "_grid4d/story/DEMO-knowledge-map.md"
    _write(km, "See [the method's pattern](evolucean/evolucean-story) in prose.\n")
    check = containment.compute(load(epic_tree))
    assert not check.holds
    assert "evolucean/evolucean-story" in check.unresolved[
        km.relative_to(epic_tree).as_posix()]


def test_relative_paths_and_md_suffixes_resolve(epic_tree):
    _write(epic_tree / "_grid4d/issue/one.md",
           "- [the idea](../idea/two) and [the identity](DEMO.md)\n")
    _write(epic_tree / "_grid4d/idea/two.md", "# Two\n")
    check = containment.compute(load(epic_tree))
    assert check.holds, check.unresolved


def test_fenced_and_inline_code_is_not_read_as_links(epic_tree):
    doc = epic_tree / "_grid4d/issue/notation.md"
    _write(doc, "```\n[not a link](nowhere-at-all)\n```\n\n"
                "The form ``[x](nowhere-either)`` is notation.\n")
    check = containment.compute(load(epic_tree))
    assert check.holds, check.unresolved


def test_history_and_archive_are_not_scanned_but_resolve(epic_tree):
    _write(epic_tree / "_grid4d/story/history/OLD.md",
           "- [leaves](outside-the-repository)\n")
    _write(epic_tree / "_grid4d/issue/fresh.md", "- [the old story](OLD)\n")
    check = containment.compute(load(epic_tree))
    assert check.holds


def test_the_cli_gates_links(epic_tree):
    doc = epic_tree / "_grid4d/ontology/ontology-beta-blueprint.md"
    doc.write_text(doc.read_text(encoding="utf-8")
                   + "\n- [Out](a-document-of-another-repository)\n", encoding="utf-8")
    result = CliRunner().invoke(main_cli(), ["verify", "--root", str(epic_tree)])
    assert result.exit_code == 1
    assert "LINK unresolved" in result.output
