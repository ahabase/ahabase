"""The wiki projection suite (AHA-0036, R1/R3).

The parity row: the door's output on the fixture epic equals the golden
mirror captured from a live method-side run (2026-11-22, the landing
day; the capture script's config is embedded verbatim below) - same
file set, same bytes, both operations (sync, generate). The defaults
polarity: no yaml, the standard mirror path, nothing mapped, the
default navigation. The seam surface: six subcommands, distinguishable
exits (0 done, 1 refused, 2 usage, 3 duplicates). The consumer rows:
the playground names the door and the publish flow, the indexes carry
the capability and the concept.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ahabase.cli_wiki import wiki_group

# The fixture config, verbatim as the golden capture ran it (the
# method-side door read the same bytes from its in-repository file).
FIXTURE_YAML = """\
wiki:
  name: fixepic
  target: _wikis/fixepic.wiki
  source: _grid4d

sidebar:
  - section: null
    items:
      - label: Home
        target: Home
  - section: Concepts
    items:
      - label: Concept A
        target: concept-a
      - label: Nested
        target: ontology/deep/nested
  - separator: true
  - section: Links
    header_link: https://example.org/docs
    items:
      - label: External docs
        target: https://example.org/docs
        external: true
  - section: Foldout
    collapsible: true
    items:
      - label: Kept
        target: keepdir/kept

home:
  title: Fixture Wiki
  subtitle: A fixture epic for the parity row.
  sections:
    - title: About
      content: |
        Raw markdown content line one.
        Raw markdown content line two.
      blockquote: |
        A quoted line.
        Another quoted line.
    - title: Table
      table:
        - label: Concept A
          target: concept-a
          description: The first concept
    - title: Numbers
      stats:
        concepts: 3
        relationships: 5
        tests: 12
        data_stories: 2
    - image:
        src: https://example.org/diagram.png
        alt: The fixture diagram

documents:
  concept-a: ontology/concept-a.md
  manual-only: null
  "keepdir/::": null

auto_sync:
  - source_pattern: "implementation/**/*.md"
  - source_pattern: "story/*.md"
    wiki_pattern: "{basename}"

exclude:
  - "**/*-knowledge-map.md"

worktree_sources:
  enabled: true
  pattern: "story/{STORY}*.md"

validation:
  link_format: path_based
  require_targets: true
  warn_orphans: true
"""

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "wiki-golden"


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "ws"
    monkeypatch.setenv("AHABASE_WORKSPACE", str(root))
    return root


def _fixture_epic(workspace: Path, *, config: bool) -> Path:
    """The capture script's epic tree: the same files, the same config
    bytes; ``config`` also writes the engine-side yaml location."""
    epic = workspace / "fixepic"
    grid = epic / "_grid4d"
    (grid / "ontology/deep").mkdir(parents=True)
    (grid / "implementation").mkdir(parents=True)
    (grid / "story").mkdir(parents=True)
    (workspace / "_wikis" / "fixepic.wiki" / "keepdir").mkdir(parents=True)
    (workspace / "_worktrees" / "fixepic" / "FIXEPIC-0002" / "_grid4d" / "story")\
        .mkdir(parents=True)
    (grid / "ontology/concept-a.md").write_text("# Concept A\n\nThe first concept.\n")
    (grid / "ontology/concept-b.md").write_text("# Concept B\n\nThe second concept.\n")
    (grid / "ontology/deep/nested.md").write_text("# Nested\n\nA nested concept.\n")
    (grid / "implementation/impl-a.md").write_text(
        "# Impl A\n\nThe first implementation blueprint.\n")
    (grid / "implementation/impl-b.md").write_text(
        "# Impl B\n\nThe second implementation blueprint.\n")
    (grid / "story/FIXEPIC-0001.md").write_text("# FIXEPIC-0001\n\nA story.\n")
    (workspace / "_worktrees/fixepic/FIXEPIC-0002/_grid4d/story/FIXEPIC-0002.md")\
        .write_text("# FIXEPIC-0002\n\nA worktree story.\n")
    (workspace / "_wikis/fixepic.wiki/keepdir/kept.md").write_text(
        "# Kept\n\nA wiki-only page kept by the dir pattern.\n")
    if config:
        target = workspace / "_config"
        target.mkdir(parents=True, exist_ok=True)
        (target / "fixepic.wiki.yaml").write_text(FIXTURE_YAML)
    return epic


def _mirror_tree(root: Path) -> dict[str, str]:
    """Every file under the mirror (relative posix path -> bytes), the
    shape the parity row compares."""
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            out[path.relative_to(root).as_posix()] = path.read_text()
    return out


def test_parity_with_the_method_side_golden(workspace: Path) -> None:
    """R1: the same fixture epic and config produce the same mirror the
    method side produced - file set and bytes (the golden, captured
    2026-11-22 from a live method-side run of sync + generate)."""
    _fixture_epic(workspace, config=True)
    runner = CliRunner()
    assert runner.invoke(wiki_group, ["sync", "--epic", "fixepic"]).exit_code == 0
    assert runner.invoke(wiki_group, ["generate", "--epic", "fixepic"]).exit_code == 0
    assert _mirror_tree(workspace / "_wikis/fixepic.wiki") == _mirror_tree(GOLDEN)


def test_defaults_when_the_config_is_absent(workspace: Path) -> None:
    """R1, the other polarity: no yaml - the standard mirror path, the
    ``_grid4d/`` source, nothing mapped (nothing copied), and the
    default navigation. No refusal: an unconfigured Epic is valid."""
    _fixture_epic(workspace, config=False)
    runner = CliRunner()
    result = runner.invoke(wiki_group, ["sync", "--epic", "fixepic"])
    assert result.exit_code == 0, result.output
    mirror = workspace / "_wikis/fixepic.wiki"
    assert mirror.is_dir()  # created, not demanded
    assert not any(mirror.iterdir())  # nothing mapped, nothing copied
    assert runner.invoke(wiki_group, ["generate", "--epic", "fixepic"]).exit_code == 0
    assert (mirror / "_Sidebar.md").read_text() == "\n"  # no sections
    home = (mirror / "Home.md").read_text()
    assert home.startswith("# Wiki\n")  # the default title
    assert "**Concepts**" not in home  # no fixture content leaked in


def test_seam_surface_six_subcommands_distinguishable_exits(
        workspace: Path) -> None:
    """R3: the seam the flip relies on - six subcommands, and the exits
    distinguish the outcomes: 0 done, 1 refused (name omitted, no such
    epic), 2 usage, 3 duplicates found."""
    epic = _fixture_epic(workspace, config=False)
    mirror = workspace / "_wikis/fixepic.wiki"
    (mirror / "sub").mkdir(parents=True)
    (mirror / "dup.md").write_text("root copy\n")
    (mirror / "sub/dup.md").write_text("sub copy\n")
    runner = CliRunner()

    help_text = runner.invoke(wiki_group, ["--help"]).output
    for name in ("check", "clean", "generate", "sync", "publish", "status"):
        assert name in help_text, f"subcommand {name} missing from the door"

    assert runner.invoke(wiki_group, ["status", "--epic", "fixepic"]).exit_code == 0
    assert runner.invoke(wiki_group, ["check", "--epic", "fixepic"]).exit_code == 3
    assert runner.invoke(wiki_group, ["check", "--epic", "nosuchepic"]).exit_code == 1
    assert runner.invoke(wiki_group, ["check"]).exit_code == 1  # no ambient epic
    assert runner.invoke(wiki_group, ["check", "--epic", "fixepic", "--bogus"])\
        .exit_code == 2

    # the refused legs print the remedy, not a stack trace
    refused = runner.invoke(wiki_group, ["check", "--epic", "nosuchepic"])
    assert "no Epic directory" in refused.output
    unnamed = runner.invoke(wiki_group, ["check"])
    assert "--epic" in unnamed.output


def test_check_and_clean_both_polarities(workspace: Path) -> None:
    """Duplicates found and cleaned: the root copy wins; with no root
    copy the newest subfolder copy is promoted. The mtime decides - set
    by hand, the ported rule."""
    import os

    epic = _fixture_epic(workspace, config=False)
    mirror = workspace / "_wikis/fixepic.wiki"
    (mirror / "sub_a").mkdir(parents=True)
    (mirror / "sub_b").mkdir(parents=True)
    (mirror / "dup.md").write_text("root copy\n")
    (mirror / "sub_a/dup.md").write_text("sub copy a\n")
    (mirror / "sub_a/solo.md").write_text("old\n")
    os.utime(mirror / "sub_a/dup.md", (1, 1))
    (mirror / "sub_b/solo.md").write_text("new\n")
    os.utime(mirror / "sub_b/solo.md", (2, 2))
    os.utime(mirror / "sub_a/solo.md", (1, 1))
    runner = CliRunner()

    found = runner.invoke(wiki_group, ["check", "--epic", "fixepic"])
    assert found.exit_code == 3
    assert "dup.md (2 copies)" in found.output
    assert "[ROOT]" in found.output and "[SUBFOLDER]" in found.output

    cleaned = runner.invoke(wiki_group, ["clean", "--epic", "fixepic"])
    assert cleaned.exit_code == 0, cleaned.output
    assert (mirror / "dup.md").read_text() == "root copy\n"  # root wins
    assert not (mirror / "sub_a/dup.md").exists()
    # no root copy of solo.md - the newest subfolder copy is promoted
    assert (mirror / "solo.md").read_text() == "new\n"
    assert not (mirror / "sub_a/solo.md").exists()
    assert not (mirror / "sub_b/solo.md").exists()

    assert runner.invoke(wiki_group, ["check", "--epic", "fixepic"]).exit_code == 0


def test_consumer_surface_names_the_door_and_the_flow(
        workspace: Path) -> None:
    """R3: the consumer sees the capability - the playground names the
    door and the publish flow; the capabilities index carries the three
    capabilities; the ontology index carries the concept."""
    root = Path(__file__).resolve().parents[1]
    playground = (root / "playground" / "CLAUDE.md").read_text()
    assert "ahabase wiki sync" in playground
    assert "ahabase wiki publish" in playground
    assert "_wikis/<epic>.wiki" in playground or "_wikis/scratch.wiki" in playground

    capabilities = (root / "_grid4d" / "ontology"
                    / "ontology-capabilities-index.md").read_text()
    for name in ("wiki-projection", "wiki-validation", "wiki-publishing"):
        assert f"**{name}**" in capabilities

    index = (root / "_grid4d" / "ontology"
             / "00-ahabase-ontology-index.md").read_text()
    assert "Wiki Projection" in index
