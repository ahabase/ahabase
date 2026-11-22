"""The workspace folders suite (AHA-0035, R2).

The seven standard folders at the workspace root - the Human ruling of
2026-11-22 (the proven evolucean topology, outside every repository):
``ensure`` creates the set in a fresh workspace, is idempotent, recreates
what a consumer deletes, never touches existing contents, and no Epic
repository ever receives any of the seven. The census holds both
polarities: all seven named at the root, none inside a repo - the repo
leg runs a real story mint beside the ensure, the state that would carry
worktree-shaped dirt into a repository under the retired layout.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ahabase import config, story
from ahabase.epic import load

from test_story import repo  # noqa: F401 - the scratch-Epic fixture


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fresh workspace root pinned through the env (the door's own
    resolution); nothing exists under it before the first ensure."""
    root = tmp_path / "ws"
    monkeypatch.setenv("AHABASE_WORKSPACE", str(root))
    return root


def test_ensure_creates_the_seven_in_a_fresh_workspace(workspace: Path) -> None:
    folders = config.ensure_standard_folders()
    assert [folder.name for folder in folders] == list(config.STANDARD_FOLDERS)
    for name in config.STANDARD_FOLDERS:
        assert (workspace / name).is_dir()


def test_ensure_is_idempotent_and_recreates_the_deleted(workspace: Path) -> None:
    config.ensure_standard_folders()
    kept = workspace / "_config" / "consumer-cli-settings.yml"
    kept.write_text("a: 1\n", encoding="utf-8")
    (workspace / "_temp").rmdir()  # a consumer deletes one of the seven
    config.ensure_standard_folders()
    assert (workspace / "_temp").is_dir()  # the deleted folder reappears
    assert kept.read_text(encoding="utf-8") == "a: 1\n"  # contents untouched


def test_no_standard_folder_lands_inside_an_epic_repository(repo: Path) -> None:
    """The census against the living state: the workspace is the fixture's
    pinned root (tmp_path), the repo sits inside it, and a story mint plus
    an ensure leave the repository free of all seven - the worktree lands
    at ``<workspace>/_worktrees/<repo>/<STORY>`` (R1), the folders at the
    root (this requirement), nothing inside the repository."""
    story.create(load(repo), "beside the census")
    config.ensure_standard_folders()
    for name in config.STANDARD_FOLDERS:
        assert (repo.parent / name).is_dir()  # the workspace holds all seven
        assert not (repo / name).exists()  # the repository holds none


def test_the_door_prints_the_census(workspace: Path) -> None:
    from click.testing import CliRunner

    from ahabase.cli_workspace import workspace_group

    result = CliRunner().invoke(workspace_group, ["ensure"])
    assert result.exit_code == 0
    lines = result.output.splitlines()
    assert lines[0] == f"workspace: {workspace}"
    assert lines[1:] == list(config.STANDARD_FOLDERS)
