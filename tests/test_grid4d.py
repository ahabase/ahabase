"""The grid4d format core's suite (AHA-0030, R1).

Proves the slice's promises on a scratch consumer Epic: the
identity split (a knowledge-only Epic validates - no
``**CodeArtifacts:**`` anywhere), a valid tree green, each seeded
violation reported with its location, the story grammar derived from
the def file's prefix, the pattern resolution order, placeholders
verbatim, and the links fold.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ahabase import grid4d
from ahabase.cli_grid4d import validate
from ahabase.epic import EpicError, load

IDENTITY = """# DEMO

> A scratch Epic for the format core's suite.

**Type:** Epic
**StoryPrefix:** DEMO-

## Overview

A knowledge-only Epic: no **CodeArtifacts:** line anywhere.

## Related

- [DEMO-Priorities](DEMO-Priorities)
"""

PRIORITIES = """# DEMO Priorities

## Period

now

## Priorities

none

## Related
"""

STORY = """# DEMO-0001: the story

> The story set the grammar names.

**Type:** default
**Epic:** [DEMO](DEMO)
**Status:** completed

## Goal

Land the suite's fixture.

## Requirements

### R1: the fixture

**Acceptance Criterion:** it exists.

## Acceptance Criteria

- [x] R1: the fixture

## Notes

none

## References

- [DEMO](DEMO)
"""

TESTS = """# DEMO-0001-tests

## Design

One test per requirement.

## Definition

```yaml
tests: []
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1 | ok | |

## Related

- [DEMO-0001](DEMO-0001)
"""

KNOWLEDGE_MAP = """# DEMO-0001 Knowledge Map

**Story:** [DEMO-0001](DEMO-0001)

## Consumed

- the fixture

## Updated

- none

## Created

- this map
"""

SUBEPIC_INDEX = """# DEMO-SUB

> A subepic that grew its own folders.

**Type:** SubEpic
**Inherits:** demo
**StoryPrefix:** DEMO-SUB-

## Overview

One concept of its own.

## Related
"""

SUB_CONCEPT = """# Sub Alpha Blueprint

**State:** planned

## Overview

A subepic concept.

## Related
"""


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A valid knowledge-only Epic: root folders, a subepic, history."""
    root = tmp_path / "demo"
    _write(root / "_grid4d/story/DEMO.md", IDENTITY)
    _write(root / "_grid4d/story/DEMO-Priorities.md", PRIORITIES)
    _write(root / "_grid4d/story/DEMO-0001.md", STORY)
    _write(root / "_grid4d/story/DEMO-0001-tests.md", TESTS)
    _write(root / "_grid4d/story/DEMO-0001-knowledge-map.md", KNOWLEDGE_MAP)
    _write(root / "_grid4d/story/history/DEMO-0002.md", "# DEMO-0002\n\nno sections - history is structure-exempt\n")
    _write(root / "_grid4d/story/history/DEMO-0002-tests.md", "# DEMO-0002-tests\n\n## Design\n\n## Definition\n\n## Execution\n\n## Related\n")
    _write(root / "_grid4d/ontology/00-demo-ontology-index.md", "# demo Ontology\n\n## Vocabulary\n\n- [Alpha](ontology-alpha-blueprint)\n")
    _write(root / "_grid4d/ontology/ontology-alpha-blueprint.md", "# Alpha Blueprint\n\n**State:** planned\n\n## Overview\n\nA concept.\n\n## Related\n")
    _write(root / "_grid4d/implementation/implementation-demo-core-blueprint.md", "# Core\n\n**Implements:** [ontology-alpha-blueprint](ontology-alpha-blueprint)\n**Code:** none (document blueprint)\n\n## Overview\n\n## Related\n")
    _write(root / "_grid4d/pattern/demo-notes.md", "# demo notes pattern\n\n## Overview\n\n## Related\n")
    _write(root / "_grid4d/playbook/demo-walkthrough-playbook.md", "# walkthrough\n\n## Overview\n")
    _write(root / "_grid4d/issue/a-known-issue.md", "# a known issue\n\n## Overview\n")
    _write(root / "_grid4d/subepic/demo-sub/story/DEMO-SUB.md", SUBEPIC_INDEX)
    _write(root / "_grid4d/subepic/demo-sub/ontology/ontology-sub-alpha-blueprint.md", SUB_CONCEPT)
    return root


def _validate(root: Path) -> list[str]:
    return [str(finding) for finding in grid4d.validate(load(root))]


def test_a_valid_tree_holds(tree: Path) -> None:
    """The whole valid tree - identity split, subepic, history - is green."""
    assert _validate(tree) == []


def test_identity_is_split_from_the_package(tree: Path) -> None:
    """A knowledge-only Epic loads: no CodeArtifacts, package None."""
    epic = load(tree)
    assert epic.package is None
    assert epic.story_prefix == "DEMO"


def test_prefix_trailing_dash_is_stripped(tree: Path) -> None:
    """The historical ``DEMO-`` declaration yields the namespace ``DEMO``."""
    identity = tree / "_grid4d/story/DEMO.md"
    identity.write_text(IDENTITY.replace("**StoryPrefix:** DEMO-\n",
                                         "**StoryPrefix:** DEMO\n"), encoding="utf-8")
    assert load(tree).story_prefix == "DEMO"


def test_unknown_folder_reported_with_location(tree: Path) -> None:
    folder = (tree / "_grid4d/experiments").mkdir()
    findings = _validate(tree)
    assert any(f.startswith("unknown-folder: _grid4d/experiments")
               for f in findings), findings


def test_misnamed_artifact_reported_with_location(tree: Path) -> None:
    _write(tree / "_grid4d/ontology/notes.md", "# notes\n")
    findings = _validate(tree)
    assert any(f.startswith("misnamed-artifact: _grid4d/ontology/notes.md")
               for f in findings), findings


def test_missing_identity_reported_by_the_door(tree: Path) -> None:
    (tree / "_grid4d/story/DEMO.md").unlink()
    result = CliRunner().invoke(validate, ["--root", str(tree)])
    assert result.exit_code == 1
    assert result.output.startswith("identity:")


def test_story_grammar_derives_from_the_prefix(tree: Path) -> None:
    """A foreign-prefix story doc is a finding - the grammar is not hardcoded."""
    _write(tree / "_grid4d/story/OTHER-0007.md", STORY)
    findings = _validate(tree)
    assert any(f.startswith("misnamed-artifact: _grid4d/story/OTHER-0007.md")
               for f in findings), findings


def test_history_naming_checked_structure_exempt(tree: Path) -> None:
    misnamed = _write(tree / "_grid4d/story/history/notes.md", "# notes\n")
    findings = _validate(tree)
    assert any(f.startswith("misnamed-artifact: _grid4d/story/history/notes.md")
               for f in findings), findings
    # DEMO-0002.md carries no required section and is NOT a finding


def test_duplicate_name_across_folders(tree: Path) -> None:
    _write(tree / "_grid4d/subepic/demo-sub/ontology/ontology-alpha-blueprint.md", SUB_CONCEPT)
    findings = _validate(tree)
    assert any(f.startswith("duplicate-name: _grid4d/subepic/demo-sub/ontology/ontology-alpha-blueprint.md")
               for f in findings), findings


def test_missing_section_reported(tree: Path) -> None:
    story = tree / "_grid4d/story/DEMO-0001.md"
    story.write_text(STORY.replace("## References\n\n- [DEMO](DEMO)\n", ""), encoding="utf-8")
    findings = _validate(tree)
    assert any(f.startswith("missing-section: _grid4d/story/DEMO-0001.md")
               and "## References" in f for f in findings), findings


def test_unregistered_subepic_story_folder(tree: Path) -> None:
    (tree / "_grid4d/subepic/demo-sub/story/DEMO-SUB.md").unlink()
    findings = _validate(tree)
    assert any(f.startswith("identity: _grid4d/subepic/demo-sub/story")
               for f in findings), findings


def test_unresolved_link_folds_into_findings(tree: Path) -> None:
    concept = tree / "_grid4d/ontology/ontology-alpha-blueprint.md"
    concept.write_text("# Alpha\n\n**State:** planned\n\n## Overview\n\nSee "
                       "[Missing](ontology-nope-blueprint).\n\n## Related\n",
                       encoding="utf-8")
    findings = _validate(tree)
    assert any(f.startswith("unresolved-link: _grid4d/ontology/ontology-alpha-blueprint.md")
               and "ontology-nope-blueprint" in f for f in findings), findings


def test_special_folder_coverage_stated_as_it_is(tree: Path) -> None:
    """_archive/ is skipped entirely; _generated/ is skipped by the folder
    and naming checks but its rendered links are still resolved - the link
    arm IS containment.compute, whose skip list is its own scope (review
    5948: the stated coverage must state what is)."""
    for folder in ("_archive", "_generated"):
        _write(tree / f"_grid4d/{folder}/projection.md",
               "# projection\n\nSee [Nope](ontology-nope-blueprint).\n")
    findings = _validate(tree)
    assert any(f.startswith("unresolved-link: _grid4d/_generated/projection.md")
               for f in findings), findings
    assert not any("_archive" in f for f in findings), findings


def test_pattern_resolution_epic_overrides_default(tree: Path) -> None:
    """The Epic's own <epic>-story.md wins over the package default: its
    extra required section turns a story doc that satisfies the default
    into a finding."""
    _write(tree / "_grid4d/pattern/demo-story.md",
           "# {STORY}\n\n## Overview\n\n## Extra Section\n")
    findings = _validate(tree)
    assert any(f.startswith("missing-section: _grid4d/story/DEMO-0001.md")
               and "## Extra Section" in f for f in findings), findings


def test_pattern_resolution_subepic_overrides_epic(tree: Path) -> None:
    """The subepic's own template wins over both higher levels."""
    _write(tree / "_grid4d/pattern/demo-story.md",
           "# {STORY}\n\n## Overview\n\n## From Epic\n")
    _write(tree / "_grid4d/subepic/demo-sub/pattern/demo-sub-story.md",
           "# {STORY}\n\n## Overview\n\n## From Subepic\n")
    epic = load(tree)
    template = grid4d.pattern_template(epic, "story", subepic="demo-sub")
    assert template is not None and "From Subepic" in template


def test_fill_replaces_only_provided_keys() -> None:
    out = grid4d.fill("# {STORY}: {TITLE}\n\n{UNKNOWN}\n",
                      {"STORY": "DEMO-0003", "TITLE": "a title"})
    assert out == "# DEMO-0003: a title\n\n{UNKNOWN}\n"


def test_the_door_holds_and_exits_zero(tree: Path) -> None:
    result = CliRunner().invoke(validate, ["--root", str(tree)])
    assert result.exit_code == 0
    assert "grid4d: holds" in result.output


def test_the_door_reports_findings_and_exits_one(tree: Path) -> None:
    (tree / "_grid4d/experiments").mkdir()
    result = CliRunner().invoke(validate, ["--root", str(tree)])
    assert result.exit_code == 1
    assert "unknown-folder: _grid4d/experiments" in result.output


def test_init_mints_a_skeleton_that_validates(tmp_path: Path) -> None:
    """A fresh tree's skeleton: every knowledge folder, the identity file
    written from the package's epic pattern - and the skeleton passes
    validate immediately (the placeholders are TODOs, not violations)."""
    root = tmp_path / "fresh"
    root.mkdir()
    identity = grid4d.init(root, "DEMO")
    assert identity == root / "_grid4d/story/DEMO.md"
    assert all((root / "_grid4d" / folder).is_dir()
               for folder in grid4d.KNOWLEDGE_FOLDERS)
    text = identity.read_text(encoding="utf-8")
    assert "**StoryPrefix:** DEMO-" in text
    # the skeleton is knowledge-only: no **CodeArtifacts:** line to fake
    assert "CodeArtifacts" not in text
    assert "{OVERVIEW}" in text  # the visible TODO: only the consumer can declare it
    epic = load(root)
    assert epic.story_prefix == "DEMO"
    assert grid4d.validate(epic) == []


def test_init_adopts_a_non_empty_directory_without_git(tmp_path: Path) -> None:
    """A plug-and-play Epic is usually an existing repository: files
    present, history present. The init door is git-blind (no subprocess in
    grid4d.py), so the non-empty edge needs no git to prove: files in the
    root survive the mint and the adopted tree validates immediately."""
    root = tmp_path / "adopted"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src" / "lib.py").write_text("def tool():\n    return 42\n",
                                         encoding="utf-8")
    (root / "README.md").write_text("an existing consumer repository\n",
                                    encoding="utf-8")
    grid4d.init(root, "ADOPT")
    assert (root / "src" / "lib.py").read_text(encoding="utf-8").startswith("def tool")
    assert (root / "README.md").exists()  # the consumer's own files survive
    assert grid4d.validate(load(root)) == []


def test_init_prefix_defaults_to_the_name_uppercased(tmp_path: Path) -> None:
    root = tmp_path / "fresh"
    root.mkdir()
    grid4d.init(root, "demo")
    assert load(root).story_prefix == "DEMO"


def test_init_refuses_an_existing_tree(tree: Path) -> None:
    with pytest.raises(grid4d.FormatError, match="already exists"):
        grid4d.init(tree, "OTHER")


def test_init_refuses_a_missing_root(tmp_path: Path) -> None:
    with pytest.raises(grid4d.FormatError, match="is not a directory"):
        grid4d.init(tmp_path / "nowhere", "DEMO")


def test_init_refuses_a_shapeless_namespace(tmp_path: Path) -> None:
    root = tmp_path / "fresh"
    root.mkdir()
    with pytest.raises(grid4d.FormatError, match="uppercase"):
        grid4d.init(root, "DEMO", prefix="no")


def test_the_init_door(tmp_path: Path) -> None:
    from ahabase.cli_grid4d import init

    root = tmp_path / "fresh"
    root.mkdir()
    result = CliRunner().invoke(init, ["DEMO", "--root", str(root)])
    assert result.exit_code == 0
    assert "initialized DEMO" in result.output
    # the second run refuses: never touches an existing tree
    result = CliRunner().invoke(init, ["DEMO", "--root", str(root)])
    assert result.exit_code == 1
    assert "already exists" in result.output
