# story lifecycle races under concurrent sessions

> Two concurrent `ahabase story create` calls wedge the repository until manual git surgery; two concurrent `complete` calls leave one story half-done (healed by a serial re-run). No phase of the lifecycle holds a critical section.

**Status:** open
**Priority:** high

## Problem

Measured 2026-11-21 in a scratch epic (5 rounds, two `ahabase story create` processes fired simultaneously per round; wheel-package CLI, default settings):

- The number scan (`next_number`) reserves nothing: a minted number becomes visible to another session's scan only when the story set lands in the worktree, so two concurrent creates mint the same number. The collision then surfaces at three layers - the shared `.git/index.lock` (the ignore commit), git's internal `.git/worktrees/<STORY>/index.lock` (both `worktree add` calls share the admin directory name), and the filesystem: a failed `worktree add` removes the directory the winner just created, and the winner then dies with an unhandled `FileNotFoundError` traceback (breaking the named-refusal contract of the door).
- The aftermath is a wedge, not a failure: the story shows as `prunable` (its branch flagged checked-out in a worktree that no longer exists), orphan `feature/<STORY>-<slug>` branches accumulate (8 in the measurement), and because the story set never landed, every later create offers the same number and fails again (rounds 3-5: both processes fail every time). Only manual `git worktree prune` plus branch deletion recovers; the prune alone leaves the orphans.
- Minor: both processes append `_worktrees/` to `.gitignore` (a duplicate line).

Concurrent `complete` (measured the same day, two completes fired simultaneously): one lands fully; the other fails at the merge with git's own lost-update refusal (`update_ref failed for ref 'HEAD': ... is at <sha> but expected <sha>`), leaving a half-done state - the tag exists, the story is marked completed in its worktree, but nothing merged. A serial re-run heals it completely (idempotency holds); the refusal text does not tell the user that a re-run heals.

Concurrent `create` racing `complete` (measured the same day, three rounds): passed 3/3 - when the ignore line already exists, create writes nothing to the shared tree, and its worktree/branch names are fresh. The residual exposure is the narrow window where create's clean-check lands inside complete's transiently dirty archive phase - a benign refusal, not corruption.

Parallel work inside distinct worktrees is not affected: once minted, the worktrees and branches are independent.

## Expected

Parallel work is a designed capability: N sessions create, work, and complete N stories concurrently. Every mutation of the shared tree - the whole create critical section (scan, ignore write, worktree add, story-set commit) and complete's main-tree phase (mark, tag, merge, archive, worktree/branch removal) - runs under one exclusive inter-process lock; work inside distinct worktrees stays lock-free. A failure inside create cleans up the worktree and branch it minted and refuses by name (never a traceback). The lock releases on process death, so a crashed holder wedges nothing - the primitive already ships in the package (`_posix.lock` / `_win.lock`, filelock-based, no new dependency).

## Fix

[AHA-0032](../story/AHA-0032.md) - parallel story lifecycle under one lock. Until it lands: never run two lifecycle commands at the same moment in one Epic.

## Related

- the lock primitive: `src/ahabase/_posix.py`, `src/ahabase/_win.py`
- AHA-0031 (the consumer playground, where parallel consumer sessions are the expected use)
