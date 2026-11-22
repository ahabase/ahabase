"""The parallel-lifecycle suite (AHA-0032).

The races only exist between real processes, so every requirement drives
the door through subprocesses fired at the same instant inside a scratch
Epic - measuring the worktree's own source (PYTHONPATH to src, never an
installed copy). The red arms prove the guards bite: a holder killed
mid-flight releases the lock with the process, and a failure injected
into the mint leaves no worktree, no branch, and a refusal by name.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest
from filelock import FileLock

from ahabase import story
from ahabase.epic import load

from test_story import _branches, _tags, repo  # noqa: F401 - the scratch-Epic fixture

SRC = Path(__file__).resolve().parent.parent / "src"
MINTED = re.compile(r"story: (DEMO-\d+) minted at")


def _spawn(root: Path, *args: str) -> subprocess.Popen:
    """One door invocation as a real process (the door's contract, exit
    codes and named refusals included), measuring this worktree's source."""
    env = dict(os.environ, PYTHONPATH=str(SRC))
    return subprocess.Popen([sys.executable, "-m", "ahabase", *args],
                            cwd=root, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)


def _finish(proc: subprocess.Popen) -> str:
    output = proc.stdout.read()
    assert proc.wait() == 0, output
    return output


def _git_out(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, check=True).stdout


def test_r1_concurrent_create_mints_distinct_numbers_without_a_wedge(repo: Path) -> None:
    """Five rounds, two create processes fired simultaneously per round:
    both mint each round, the numbers stay distinct and monotone, no
    orphan branch, no prunable admin entry, no injected ignore entry
    (AHA-0035: the worktree home is outside the repository), no
    traceback anywhere."""
    for round_ in range(5):
        procs = [_spawn(repo, "story", "create", f"round {round_} {tag}")
                 for tag in ("alpha", "beta")]
        outputs = [_finish(proc) for proc in procs]
        for output in outputs:
            assert "Traceback" not in output
        numbers = sorted(MINTED.search(output).group(1) for output in outputs)
        assert numbers[0] != numbers[1], outputs
    worktrees = sorted(path.name for path in
                       (repo.parent / "_worktrees" / repo.name).iterdir())
    assert worktrees == sorted(f"DEMO-{number:04d}" for number in range(2, 12))
    assert len(_branches(repo)) == 1 + 10  # main plus the ten story branches, no orphans
    assert "prunable" not in _git_out(repo, "worktree", "list", "--porcelain")
    assert not (repo / ".gitignore").exists()


def test_r1cwd_one_lock_whichever_cwd(repo: Path) -> None:
    """The lock is keyed on the repository's common git directory: a
    lifecycle command invoked from inside a linked story worktree (the
    normal seat of a parallel session) takes the same mutex as one from
    the main root - an external holder of the common lock blocks it, and
    the repository holds exactly one lock file."""
    first = story.create(load(repo), "first story")
    assert story._lock_path(first) == story._lock_path(repo)
    holder = FileLock(str(story._lock_path(repo)))
    holder.acquire()
    try:
        waiter = _spawn(first, "story", "create", "from the worktree cwd")
        time.sleep(1.0)  # blocked only if the worktree-cwd door keys on the common dir
        assert waiter.poll() is None
    finally:
        holder.release()
    output = _finish(waiter)
    assert MINTED.search(output)
    locks = list(repo.rglob("ahabase-story.lock"))
    assert locks == [story._lock_path(repo)]


def test_r2_concurrent_complete_both_land(repo: Path) -> None:
    """Two completes fired simultaneously: both land, each story exactly
    one merge commit, both tags, no worktree or branch left, status
    counts both completed."""
    names = [story.create(load(repo), f"story {word}").name for word in ("one", "two")]
    procs = [_spawn(repo, "story", "complete", name) for name in names]
    for proc in procs:
        _finish(proc)
    subjects = _git_out(repo, "log", "--format=%s")
    for name in names:
        assert subjects.count(f"merge {name} (story complete)") == 1
    assert sorted(_tags(repo)) == sorted(f"v{name}" for name in names)
    assert not any((repo.parent / "_worktrees" / repo.name).iterdir())
    assert _branches(repo) == ["main"]
    assert story.status(load(repo))[-1] == "completed: 3"  # the history floor plus both


def test_r3_create_waits_for_a_completing_session(repo: Path, monkeypatch) -> None:
    """A create fired at the same instant as a complete waits out the
    completion, then mints exactly the next number - no refusal names
    uncommitted changes; and the bound's edge: a lock held past the bound
    refuses by name."""
    first = story.create(load(repo), "first story")
    completer = _spawn(repo, "story", "complete", first.name)
    creator = _spawn(repo, "story", "create", "second story")
    completer_out, creator_out = _finish(completer), _finish(creator)
    assert "uncommitted changes" not in completer_out + creator_out
    assert MINTED.search(creator_out).group(1) == "DEMO-0003"

    holder = FileLock(str(story._lock_path(repo)))
    holder.acquire()
    try:
        monkeypatch.setattr(story, "_LOCK_TIMEOUT", 0.3)
        with pytest.raises(story.StoryError, match="holds the lifecycle lock"):
            story.create(load(repo), "blocked story")
    finally:
        holder.release()


def test_r4a_a_killed_holder_releases_the_lock_and_the_next_create_heals_corpses(
        repo: Path) -> None:
    """The lock rides the process: a holder killed mid-flight (kill -9)
    strands nothing - the waiting create proceeds and mints with no
    manual prune. A create killed outright (SIGKILL runs no rollback)
    leaves a half-minted corpse - a worktree whose branch holds nothing
    beyond main; the next create heals it whichever side of the template
    writes the kill landed on: the corpse goes, its branch goes, the
    number returns to the scan (never skipped, never a manual prune).
    And the heal stays strict: a HAND-MERGED story's worktree (main
    fast-forwarded to its head, nothing beyond main either) with an
    uncommitted note survives a following create untouched. Each strict
    leg carries its own witness (round-3 review): a CLEAN hand-merged
    worktree survives only through the reflog leg, and a hand-made
    worktree on a creation-only branch carrying one foreign file
    survives only through the dirt leg."""
    holder = subprocess.Popen(
        [sys.executable, "-c",
         "import sys, time\n"
         "from filelock import FileLock\n"
         "lock = FileLock(sys.argv[1])\n"
         "lock.acquire()\n"
         "print('held', flush=True)\n"
         "time.sleep(300)\n", str(story._lock_path(repo))],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"
        waiter = _spawn(repo, "story", "create", "after the kill")
        time.sleep(1.0)  # the waiter is now blocked on the held lock
    finally:
        holder.kill()
        holder.wait()
    output = _finish(waiter)
    assert MINTED.search(output).group(1) == "DEMO-0002"

    # a corpse from a kill BEFORE the template writes: the branch sits at
    # main, no story set anywhere - the state the next create must heal,
    # not refuse
    _git_out(repo, "worktree", "add", "-b", "feature/DEMO-0003-corpse",
             str(repo.parent / "_worktrees" / repo.name / "DEMO-0003"))
    output = _finish(_spawn(repo, "story", "create", "heals the bare corpse"))
    assert MINTED.search(output).group(1) == "DEMO-0003"
    assert "feature/DEMO-0003-corpse" not in _branches(repo)
    assert "prunable" not in _git_out(repo, "worktree", "list", "--porcelain")

    # a corpse from a kill AFTER the writes, before the set commit: the
    # story doc sits UNCOMMITTED in the corpse - the disk scan would see
    # it and skip the number; the heal removes the corpse first, so the
    # number returns instead of orphaning the corpse forever
    _git_out(repo, "worktree", "add", "-b", "feature/DEMO-0004-corpse",
             str(repo.parent / "_worktrees" / repo.name / "DEMO-0004"))
    doc = (repo.parent / "_worktrees" / repo.name / "DEMO-0004"
           / "_grid4d/story/DEMO-0004.md")
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("# DEMO-0004: a corpse with its writes done\n", encoding="utf-8")
    output = _finish(_spawn(repo, "story", "create", "heals the written corpse"))
    assert MINTED.search(output).group(1) == "DEMO-0004"
    assert "feature/DEMO-0004-corpse" not in _branches(repo)
    live = sorted(path.name for path in
                  (repo.parent / "_worktrees" / repo.name).iterdir())
    assert live == ["DEMO-0002", "DEMO-0003", "DEMO-0004"]  # the heals left no corpse behind

    # a HAND-MERGED story (the consumer landed it by plain git, main fast
    # -forwarded to the story head, so no commit sits beyond main either)
    # with an uncommitted note in its worktree is NOT a corpse: the
    # branch reflog carries its commits - the next create mints past it
    # and the worktree, the note and the branch all SURVIVE (round-2
    # review: the loose predicate force-deleted exactly this)
    merged = story.create(load(repo), "hand merged story")
    (merged / "work.txt").write_text("real work\n", encoding="utf-8")
    _git_out(merged, "add", "-A")
    _git_out(merged, "commit", "-m", "DEMO-0005(feat): work landed by hand")
    hand_branch = _git_out(merged, "branch", "--show-current").strip()
    _git_out(repo, "merge", "--ff-only", hand_branch)
    note = merged / "notes-uncommitted.txt"
    note.write_text("not mine to delete\n", encoding="utf-8")
    output = _finish(_spawn(repo, "story", "create", "past the hand merge"))
    assert MINTED.search(output).group(1) == "DEMO-0006"
    assert note.is_file() and merged.is_dir()
    assert hand_branch in _branches(repo)

    # the reflog leg ALONE (round-3 review, mutant A - the reflog guard
    # deleted): a hand-merged story with a CLEAN worktree - no dirt at
    # all, so the dirt clause would classify it a corpse - survives only
    # because its branch reflog carries its commits
    clean = story.create(load(repo), "clean hand merged story")
    (clean / "work.txt").write_text("landed clean\n", encoding="utf-8")
    _git_out(clean, "add", "-A")
    _git_out(clean, "commit", "-m", "DEMO-0007(feat): clean hand landing")
    clean_branch = _git_out(clean, "branch", "--show-current").strip()
    _git_out(repo, "merge", "--ff-only", clean_branch)
    output = _finish(_spawn(repo, "story", "create", "past the clean merge"))
    assert MINTED.search(output).group(1) == "DEMO-0008"
    assert (clean / "work.txt").is_file() and clean.is_dir()
    assert clean_branch in _branches(repo)

    # the dirt leg ALONE (round-3 review, mutant B - the dirt check
    # forced True): a hand-made worktree on a CREATION-ONLY branch (the
    # reflog is exactly a killed mint's shape, no commit beyond main)
    # carrying one foreign user file survives only because that file is
    # not the mint's own dirt; its story doc sits uncommitted on disk,
    # so the scan counts it and the create mints PAST it
    _git_out(repo, "worktree", "add", "-b", "feature/DEMO-0009-handmade",
             str(repo.parent / "_worktrees" / repo.name / "DEMO-0009"))
    handmade = repo.parent / "_worktrees" / repo.name / "DEMO-0009"
    doc = handmade / "_grid4d/story/DEMO-0009.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("# DEMO-0009: hand-made, one foreign file\n", encoding="utf-8")
    (handmade / "user-note.txt").write_text("not the mint's\n", encoding="utf-8")
    output = _finish(_spawn(repo, "story", "create", "past the hand-made tree"))
    assert MINTED.search(output).group(1) == "DEMO-0010"
    assert (handmade / "user-note.txt").is_file() and handmade.is_dir()
    assert "feature/DEMO-0009-handmade" in _branches(repo)

    # nothing above was healed away: every story-named worktree is alive
    live = sorted(path.name for path in
                  (repo.parent / "_worktrees" / repo.name).iterdir())
    assert live == sorted(f"DEMO-{number:04d}" for number in range(2, 11))


def test_r4b_a_failure_inside_the_mint_cleans_up_and_refuses_by_name(
        repo: Path, monkeypatch) -> None:
    """A failure between worktree add and the story-set commit rolls the
    mint back: no worktree directory, no branch, exit 1, the refusal
    names the failure and the removal - for every failure class: an
    injected OSError, click's Abort (SIGINT through the door, the same
    refusal), a raw KeyboardInterrupt (the cleanup runs, then the
    interrupt keeps its class, never swallowed) - and each time the next
    create recovers."""
    from click.testing import CliRunner

    from ahabase.cli_story import story_group

    original = story.fill
    calls = {"count": 0}

    def injected(template, values):
        calls["count"] += 1
        if calls["count"] == 2:  # the tests document - after the worktree add
            raise OSError("the pretend-full disk")
        return original(template, values)

    monkeypatch.setattr(story, "fill", injected)
    result = CliRunner().invoke(story_group, ["create", "doomed story", "--root", str(repo)])
    assert result.exit_code == 1
    assert "the pretend-full disk" in result.output
    assert "the worktree and the branch were removed" in result.output
    assert not (repo.parent / "_worktrees" / repo.name / "DEMO-0002").exists()
    assert _branches(repo) == ["main"]
    assert story.status(load(repo))[0] == "active: none"

    # targeted restore - a bare undo would also drop the fixture's
    # AHABASE_WORKSPACE pin (same monkeypatch instance), and the next
    # mint would land in the real ~/ahabase workspace
    # (issue-monkeypatch-undo-drops-fixture-env-pins)
    monkeypatch.setattr(story, "fill", original)
    assert story.create(load(repo), "recovered story").name == "DEMO-0002"

    # the interrupt class: click's Abort (SIGINT through the door) cleans
    # up and refuses by name like any failure
    from click.exceptions import Abort

    calls["count"] = 0

    def abortive(template, values):
        calls["count"] += 1
        if calls["count"] == 2:
            raise Abort()
        return original(template, values)

    monkeypatch.setattr(story, "fill", abortive)
    result = CliRunner().invoke(story_group, ["create", "aborted story", "--root", str(repo)])
    assert result.exit_code == 1
    assert "failed (Abort)" in result.output
    assert "the worktree and the branch were removed" in result.output
    assert not (repo.parent / "_worktrees" / repo.name / "DEMO-0003").exists()

    # a raw KeyboardInterrupt (not an Exception subclass): the cleanup
    # runs, then the interrupt keeps its class AT THE ENGINE - never
    # swallowed into a fake success (the door's click layer renders the
    # propagated interrupt as Aborted, exit 1 - the Abort arm above)
    calls["count"] = 0

    def interrupting(template, values):
        calls["count"] += 1
        if calls["count"] == 2:
            raise KeyboardInterrupt()
        return original(template, values)

    monkeypatch.setattr(story, "fill", interrupting)
    with pytest.raises(KeyboardInterrupt):
        story.create(load(repo), "interrupted story")
    assert not (repo.parent / "_worktrees" / repo.name / "DEMO-0003").exists()
    assert sorted(_branches(repo)) == ["feature/DEMO-0002-recovered-story", "main"]

    monkeypatch.setattr(story, "fill", original)  # targeted, never a bare undo (issue-monkeypatch-undo-drops-fixture-env-pins)
    assert story.create(load(repo), "second recovery").name == "DEMO-0003"


def test_r5_work_never_blocks_on_the_lifecycle_lock(repo: Path) -> None:
    """A plain git commit inside a story worktree proceeds while an
    external process holds the lifecycle lock; the lock file stays inside
    the git directory - invisible to status and to history - and the
    completion works once the lock is free."""
    worktree = story.create(load(repo), "first story")
    doc = worktree / "_grid4d/story/DEMO-0002.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("{GOAL}", "edited under the lock"),
                   encoding="utf-8")
    holder = FileLock(str(story._lock_path(repo)))
    holder.acquire()
    try:
        subprocess.run(["git", "add", "-A"], cwd=worktree, check=True, timeout=30)
        subprocess.run(["git", "commit", "-q", "-m", "DEMO-0002(docs): work under the lock"],
                       cwd=worktree, check=True, timeout=30)
    finally:
        holder.release()
    assert story._lock_path(repo).parent.name == ".git"
    assert _git_out(repo, "status", "--porcelain").strip() == ""
    assert "ahabase-story.lock" not in _git_out(repo, "log", "--all", "--name-only",
                                                "--pretty=format:")
    story.complete(load(repo), "DEMO-0002")
    assert _tags(repo) == ["vDEMO-0002"]
