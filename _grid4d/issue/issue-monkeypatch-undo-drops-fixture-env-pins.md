# monkeypatch undo drops fixture env pins

> A bare `monkeypatch.undo()` in a test also reverts env pins set by the SAME instance's fixtures - and once the engine resolves its topology from the environment, the reverted pin silently redirects the code under test into the real workspace.

**Status:** open
**Priority:** medium

## Problem

Found in AHA-0035 (2026-11-22), the r4b recovery rehearsal of `tests/test_story_parallel.py`: the test called `monkeypatch.undo()` to restore a patched `story.fill`, but pytest serves one monkeypatch instance per test - fixtures included - so the undo also dropped the fixture's `monkeypatch.setenv("AHABASE_WORKSPACE", str(tmp_path))`. The engine then resolved the default workspace (`~/ahabase`), the recovery mint read REAL-workspace debris for its story number (DEMO-0005 instead of the expected 0004), and the mint itself landed in the real workspace - directories under `~/ahabase/_worktrees/demo/` pointing into pytest tmp repositories, verified and removed by hand. Under the pre-AHA-0035 layout the bug was invisible (the worktree path did not depend on the workspace); the new topology made the shared-instance hazard load-bearing.

## Expected

Never a bare `monkeypatch.undo()` in a test whose fixtures pin the environment on the same instance: restore targeted - `monkeypatch.setattr(story, "fill", original)` for the one attribute the test patched, leaving the fixture pins intact. A fixture pin that a test genuinely must drop should be re-applied explicitly, so the reader sees the window in which the code runs unpinned. The two call sites in `test_story_parallel.py` carry the targeted restore with a comment naming this issue.

## Fix

The class rule, not new code: this document is the reference the review cites when a suite grows an env-dependent seam (every workspace-resolved path in `config.py` widens the blast radius of a dropped pin). A lint-shaped guard would need static analysis of pytest fixture graphs - not worth it while the call sites are countable by grep.

## Related

- [AHA-0035](AHA-0035) - where the hazard became load-bearing and was measured
- [implementation-ahabase-config-door-blueprint](implementation-ahabase-config-door-blueprint) - the env-pinned workspace seam (`AHABASE_WORKSPACE`)
