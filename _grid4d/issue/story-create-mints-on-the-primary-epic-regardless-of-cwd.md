# story create mints on the primary epic regardless of cwd

> `knowledge-usage story create` run from another epic's tree still mints on the primary epic (evolucean) - silently, with a worktree, branch, binding, join row and pool entry - and no command exists to undo a just-minted story.

**Status:** open
**Priority:** high

## Problem

Measured 2026-10-30, AHA-0014's creation: `story create "safe on Windows..."` run with cwd `~/ahabase/ahabase` minted EVOLUCEAN-0523 in the evolucean repository (branch, worktree, bootstrapped venv, baseline record, author join row, pool entry at front, legacy global pointer moved). The help's "--epic TEXT (default: primary epic)" is accurate - the command does not resolve the epic from cwd, and nothing before the mint echoes which epic is about to receive the story. The undo was manual surgery with no sanctioned path: `story worktree-prune` refuses anything but `stale-released`, there is no `story delete`, and the pool entry plus legacy pointer had to be cleared through the CLI's internal APIs (`config_state.update_state`, `config_scopes.unbind_active_story`).

## Expected

`story create` resolves the epic from the calling tree when it is a registered epic (cwd first, `--epic` explicit, primary epic only as a last-resort fallback with a printed warning), echoes `Epic: <name>` before minting, and offers an undo window for a just-minted, never-started story (no commits beyond the baseline, no messages) - one command that removes worktree, branch, pool entry, pointer and join row in the reverse order of create.

## Fix

Lands with story tracking becoming an ahabase capability - [story-tracking-as-an-ahabase-capability](../idea/story-tracking-as-an-ahabase-capability). Until then: always pass `--epic` for non-primary epics.

## Related

- AHA-0014 (the story whose creation hit this)
