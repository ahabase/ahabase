"""The story lifecycle's suite (AHA-0030, R2).

Proves the local lifecycle end to end on a scratch consumer git
repository: the mint (number by scan across story/, history/ and the
live worktrees; worktree + branch; the story set filled from the R1
package templates - and the minted set passes the R1 validator), the
status report, the completion (tag ``v<STORY>`` at the head, merge
to the main branch, archive to history/ keeping the declared window,
worktree and branch removed), the fail-closed refusals, and the
re-run of create minting the next number.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ahabase import grid4d, story
from ahabase.epic import load

from test_grid4d import IDENTITY, PRIORITIES, _write

ARCHIVED_STORY = """# DEMO-0001: archived

> One completed story in history - the numbering's floor.

**Type:** default
**Epic:** [DEMO](DEMO)
**Status:** completed

## Goal

none

## Requirements

### R1: the floor

**Acceptance Criterion:** it exists.

## Acceptance Criteria

- [x] R1: the floor

## Notes

none

## References

- [DEMO](DEMO)
"""


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch consumer Epic in its own git repository on main; the
    workspace is pinned to tmp_path so the workspace-level worktree home
    (AHA-0035: ``<workspace>/_worktrees/<repo>/<STORY>``) stays inside the
    test's throwaway tree."""
    monkeypatch.setenv("AHABASE_WORKSPACE", str(tmp_path))
    root = tmp_path / "demo"
    _write(root / "_grid4d/story/DEMO.md", IDENTITY)
    _write(root / "_grid4d/story/DEMO-Priorities.md", PRIORITIES)
    _write(root / "_grid4d/story/history/DEMO-0001.md", ARCHIVED_STORY)
    _write(root / "_grid4d/story/history/DEMO-0001-tests.md",
           "# DEMO-0001-tests\n\n## Design\n\n## Definition\n\n## Execution\n\n## Related\n")
    _write(root / "_grid4d/ontology/00-demo-ontology-index.md",
           "# demo Ontology\n\n## Vocabulary\n\n- [Alpha](ontology-alpha-blueprint)\n")
    _write(root / "_grid4d/ontology/ontology-alpha-blueprint.md",
           "# Alpha Blueprint\n\n**State:** planned\n\n## Overview\n\nA concept.\n\n## Related\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.test")
    # deterministic default-branch resolution, independent of the host's global config
    _git(root, "config", "init.defaultBranch", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "chore: the scratch Epic")
    return root


def _tags(root: Path) -> list[str]:
    result = subprocess.run(["git", "tag"], cwd=root, capture_output=True, text=True)
    return result.stdout.split()


def _branches(root: Path) -> list[str]:
    result = subprocess.run(["git", "branch", "--format", "%(refname:short)"],
                            cwd=root, capture_output=True, text=True)
    return result.stdout.split()


def test_create_mints_the_next_number_and_a_valid_set(repo: Path) -> None:
    """One more than history's max; the worktree, the branch, and a story
    set that passes the R1 validator."""
    worktree = story.create(load(repo), "first story")
    assert worktree == repo.parent / "_worktrees" / repo.name / "DEMO-0002"
    # the workspace-level home (AHA-0035): nothing worktree-shaped lands
    # inside the repository, and no ignore entry is injected
    assert not (repo / "_worktrees").exists()
    assert not (repo / ".gitignore").exists()
    assert f"feature/DEMO-0002-first-story" in _branches(repo)
    docs = {path.name for path in (worktree / "_grid4d" / "story").glob("DEMO-0002*")}
    assert docs == {"DEMO-0002.md", "DEMO-0002-tests.md", "DEMO-0002-knowledge-map.md"}
    text = (worktree / "_grid4d/story/DEMO-0002.md").read_text(encoding="utf-8")
    assert "# DEMO-0002: first story" in text
    assert "**Status:** in_progress" in text
    # unprovided placeholders stay verbatim - the visible TODO
    assert "{GOAL}" in text
    # the minted set validates by the format core that minted it
    assert grid4d.validate(load(worktree)) == []


def test_status_reports_active_open_and_completed(repo: Path) -> None:
    worktree = story.create(load(repo), "first story")
    lines = story.status(load(repo))
    assert lines[0] == "active: DEMO-0002 (worktree _worktrees/demo/DEMO-0002)"
    assert lines[1] == "open: DEMO-0002 (worktree, in_progress)"
    assert lines[2] == "completed: 1"
    story.complete(load(repo), "DEMO-0002")
    lines = story.status(load(repo))
    assert lines[0] == "active: none"
    assert lines[1] == "open: none"
    assert lines[2] == "completed: 2"


def test_complete_tags_merges_and_keeps_the_set_in_window(repo: Path) -> None:
    """The R2 end-to-end: create, one document edit, complete. The default
    window holds the completed set in story/ (nothing archived yet) - the
    Epic's whole history is kept, never pruned."""
    worktree = story.create(load(repo), "first story")
    doc = worktree / "_grid4d/story/DEMO-0002.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("{GOAL}", "the edited goal"),
                   encoding="utf-8")
    _git(worktree, "add", "-A")
    _git(worktree, "commit", "-q", "-m", "DEMO-0002(docs): the one edit")

    story.complete(load(repo), "DEMO-0002")

    assert _tags(repo) == ["vDEMO-0002"]
    assert "feature/DEMO-0002-first-story" not in _branches(repo)
    assert not (repo.parent / "_worktrees" / repo.name / "DEMO-0002").exists()
    # within the window (default 2): the completed set stays reachable in story/
    kept = {p.name for p in (repo / "_grid4d/story").glob("DEMO-0002*")}
    assert kept == {"DEMO-0002.md", "DEMO-0002-tests.md", "DEMO-0002-knowledge-map.md"}
    assert not (repo / "_grid4d/story/history/DEMO-0002.md").exists()
    text = (repo / "_grid4d/story/DEMO-0002.md").read_text(encoding="utf-8")
    assert "**Status:** completed" in text
    assert "the edited goal" in text
    # the merged main tree still validates
    assert grid4d.validate(load(repo)) == []


def test_a_re_run_of_create_mints_the_next_number(repo: Path) -> None:
    """The scan reads history after the archive - no stored counter."""
    story.create(load(repo), "first story")
    story.complete(load(repo), "DEMO-0002")
    second = story.create(load(repo), "second story")
    assert second == repo.parent / "_worktrees" / repo.name / "DEMO-0003"


def test_create_refuses_a_dirty_main_tree(repo: Path) -> None:
    (repo / "_grid4d/story/DEMO.md").write_text(IDENTITY + "\n", encoding="utf-8")
    with pytest.raises(story.StoryError, match="uncommitted changes"):
        story.create(load(repo), "first story")


def test_complete_refuses_a_dirty_worktree(repo: Path) -> None:
    worktree = story.create(load(repo), "first story")
    (worktree / "_grid4d/story/DEMO-0002.md").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(story.StoryError, match="uncommitted changes"):
        story.complete(load(repo), "DEMO-0002")


def test_complete_refuses_an_incomplete_set(repo: Path) -> None:
    worktree = story.create(load(repo), "first story")
    (worktree / "_grid4d/story/DEMO-0002-knowledge-map.md").unlink()
    _git(worktree, "add", "-A")
    _git(worktree, "commit", "-q", "-m", "DEMO-0002(chore): drop the map")
    with pytest.raises(story.StoryError, match="DEMO-0002-knowledge-map.md is missing"):
        story.complete(load(repo), "DEMO-0002")


def test_complete_refuses_a_story_without_a_worktree(repo: Path) -> None:
    with pytest.raises(story.StoryError, match="no worktree for DEMO-0009"):
        story.complete(load(repo), "DEMO-0009")


def test_beyond_the_window_the_set_archives_never_deletes(repo: Path) -> None:
    """StoryHistoryKeep: 1 - the newest completed set stays in story/, the
    older one MOVES to history/ (archived, never deleted)."""
    _write(repo / "_grid4d/story/DEMO.md",
           IDENTITY.replace("**StoryPrefix:** DEMO-\n",
                            "**StoryPrefix:** DEMO-\n**StoryHistoryKeep:** 1\n"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore: declare the window")
    story.complete(load(repo), story.create(load(repo), "first story").name)   # DEMO-0002
    story.complete(load(repo), story.create(load(repo), "second story").name)  # DEMO-0003
    # the newest completed set stays in story/
    assert {p.name for p in (repo / "_grid4d/story").glob("DEMO-0003*")} == {
        "DEMO-0003.md", "DEMO-0003-tests.md", "DEMO-0003-knowledge-map.md"}
    # the older one moved to history/ (beside the fixture's DEMO-0001)
    history = repo / "_grid4d/story/history"
    assert {p.name for p in history.glob("DEMO-0002*")} == {
        "DEMO-0002.md", "DEMO-0002-tests.md", "DEMO-0002-knowledge-map.md"}
    assert {p.name for p in history.glob("DEMO-0001*")}
    # the count reads both places: in-window and archived
    assert story.status(load(repo))[-1] == "completed: 3"


def test_complete_refuses_a_root_not_on_the_main_branch(repo: Path) -> None:
    """complete merges into the DECLARED main branch, never whatever the
    root has checked out (review 5940 F1): the refusal names both branches
    and precedes every write - no mark, no tag, nothing removed."""
    worktree = story.create(load(repo), "first story")
    _git(repo, "checkout", "-q", "-b", "scratch-work")
    with pytest.raises(story.StoryError) as excinfo:
        story.complete(load(repo), "DEMO-0002")
    message = str(excinfo.value)
    assert "scratch-work" in message and "'main'" in message
    assert _tags(repo) == []
    assert "feature/DEMO-0002-first-story" in _branches(repo)
    assert worktree.is_dir()
    text = (worktree / "_grid4d/story/DEMO-0002.md").read_text(encoding="utf-8")
    assert "**Status:** in_progress" in text


def test_complete_refuses_a_dirty_root(repo: Path) -> None:
    """The merge writes into the root, so the root must be clean first -
    and the refusal precedes every write (review 5940 F2's rule)."""
    story.create(load(repo), "first story")
    (repo / "uncommitted.txt").write_text("dirty", encoding="utf-8")
    with pytest.raises(story.StoryError, match="uncommitted changes"):
        story.complete(load(repo), "DEMO-0002")
    assert _tags(repo) == []
    text = (repo.parent / "_worktrees" / repo.name
            / "DEMO-0002/_grid4d/story/DEMO-0002.md").read_text(encoding="utf-8")
    assert "**Status:** in_progress" in text


def test_a_conflicted_merge_aborts_and_leaves_the_story_recoverable(repo: Path) -> None:
    """A conflict is refused with git's own words (stdout included), the
    merge is ABORTED (no MERGE_HEAD), and the worktree, the branch and the
    story survive intact (review 5940 F2)."""
    worktree = story.create(load(repo), "first story")
    doc = worktree / "_grid4d/story/DEMO-0002.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("{GOAL}", "the story goal"),
                   encoding="utf-8")
    # the same file edited on both sides -> a content conflict
    (worktree / "_grid4d/story/DEMO.md").write_text(
        IDENTITY + "\nthe story side\n", encoding="utf-8")
    _git(worktree, "add", "-A")
    _git(worktree, "commit", "-q", "-m", "DEMO-0002(docs): the story side")
    (repo / "_grid4d/story/DEMO.md").write_text(
        IDENTITY + "\nthe main side\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore: the main side")

    with pytest.raises(story.StoryError, match="CONFLICT"):
        story.complete(load(repo), "DEMO-0002")

    assert not (repo / ".git" / "MERGE_HEAD").exists()
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                            capture_output=True, text=True).stdout
    assert status.strip() == ""
    assert "feature/DEMO-0002-first-story" in _branches(repo)
    assert worktree.is_dir()


def test_complete_re_runs_after_the_conflict_is_resolved(repo: Path) -> None:
    """complete is idempotent: the re-run after the conflict was resolved on
    the main branch skips the already-made mark and tag and completes the
    story (review 5940 F2's recovery path)."""
    worktree = story.create(load(repo), "first story")
    doc = worktree / "_grid4d/story/DEMO-0002.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("{GOAL}", "the story goal"),
                   encoding="utf-8")
    (worktree / "_grid4d/story/DEMO.md").write_text(
        IDENTITY + "\nthe story side\n", encoding="utf-8")
    _git(worktree, "add", "-A")
    _git(worktree, "commit", "-q", "-m", "DEMO-0002(docs): the story side")
    (repo / "_grid4d/story/DEMO.md").write_text(
        IDENTITY + "\nthe story side\n", encoding="utf-8")  # resolved: the story's version
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore: the resolved side")

    story.complete(load(repo), "DEMO-0002")  # first run merges clean (no conflict)
    # now the conflict shape: a SECOND story conflicting, refused, resolved, re-run
    worktree = story.create(load(repo), "second story")
    doc = worktree / "_grid4d/story/DEMO-0003.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("{GOAL}", "the second goal"),
                   encoding="utf-8")
    (worktree / "_grid4d/story/DEMO.md").write_text(
        IDENTITY + "\nthe second story side\n", encoding="utf-8")
    _git(worktree, "add", "-A")
    _git(worktree, "commit", "-q", "-m", "DEMO-0003(docs): the second story side")
    (repo / "_grid4d/story/DEMO.md").write_text(
        IDENTITY + "\nthe main side again\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore: the main side again")

    with pytest.raises(story.StoryError, match="CONFLICT"):
        story.complete(load(repo), "DEMO-0003")
    # the human resolves on main, the re-run completes the story
    (repo / "_grid4d/story/DEMO.md").write_text(
        IDENTITY + "\nthe second story side\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore: resolve toward the story")
    story.complete(load(repo), "DEMO-0003")

    assert _tags(repo) == ["vDEMO-0002", "vDEMO-0003"]
    assert not (repo.parent / "_worktrees" / repo.name / "DEMO-0003").exists()
    assert "feature/DEMO-0003-second-story" not in _branches(repo)
    text = (repo / "_grid4d/story/DEMO-0003.md").read_text(encoding="utf-8")
    assert "**Status:** completed" in text
    assert grid4d.validate(load(repo)) == []


def test_the_door_refuses_namingly(repo: Path) -> None:
    """The CLI surface: a refusal exits 1 with its reason; status prints."""
    from click.testing import CliRunner

    from ahabase.cli_story import story_group

    result = CliRunner().invoke(story_group, ["complete", "DEMO-0009", "--root", str(repo)])
    assert result.exit_code == 1
    assert "no worktree for DEMO-0009" in result.output

    result = CliRunner().invoke(story_group, ["create", "first story", "--root", str(repo)])
    assert result.exit_code == 0
    assert "DEMO-0002 minted" in result.output
    result = CliRunner().invoke(story_group, ["status", "--root", str(repo)])
    assert result.exit_code == 0
    assert "active: DEMO-0002" in result.output
    # the mint commit already exists - nothing left to stage
    result = CliRunner().invoke(story_group, ["complete", "DEMO-0002", "--root", str(repo)])
    assert result.exit_code == 0
    assert _tags(repo) == ["vDEMO-0002"]
