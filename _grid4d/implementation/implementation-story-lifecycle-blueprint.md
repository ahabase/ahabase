# ahabase Story Lifecycle Blueprint

> The basics of Priorities row 8: the local story lifecycle in the consumer's own git repository - mint by scan-numbering, worktree + branch, status read from the documents, complete with tag + merge + archive. No state beside the tree.

**Implements:** [ontology-grid4d-blueprint](ontology-grid4d-blueprint) - within [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint)
**Story:** [AHA-0030](AHA-0030)
**Code:** story, cli_story

## Overview

Three commands over the consumer's own repository: `ahabase story create <description>` mints the next story (its number derived by scan, never stored), `ahabase story status` reads what is, `ahabase story complete <STORY>` marks, tags `v<STORY>` at the head, merges to the main branch, archives to `story/history/` keeping the declared window, and removes the worktree and the branch. The mint fills the R1 pattern templates; the local lifecycle only - no collab, no team log, no phases, no counters branch (the AHA-0030 row-8 cut). The shared-tree phases (the whole mint, the completion) run under one inter-process lock, so parallel sessions work parallel stories (AHA-0032).

## Rules

1. **No state beside the tree** - The next number is the max the tree already names: `story/`, `story/history/`, and the story folders of every live worktree under `_worktrees/`, plus one. Reason: a stored counter is a second registration that drifts from the tree (checkpoint 0, seat c020eeb4; the method copy's counters CAS is cross-instance machinery this row leaves behind).
2. **The story's state is its document** - `**Status:**` in the story doc is the one state; status reads it, complete rewrites it (`in_progress` → `completed`). Reason: a state file beside the documents is parallel configuration by another name (the Human's 2026-11-20 ruling).
3. **The def file declares the two knobs** - `**Branch:**` (else git's `init.defaultBranch`, else `main`, and it must exist) and `**StoryHistoryKeep:**` (else 2). Reason: configuration that the tree already carries must not be duplicated (no parallel configuration).
4. **Create refuses a dirty tree and mints from the patterns** - A clean main tree is required; the worktree `_worktrees/<STORY>` gets branch `feature/<STORY>-<slug>`; the story set (story, tests, knowledge map) is the R1 templates filled with the provided keys (`STORY`, `TITLE`, `EPIC`, `TYPE`, `STATUS`, `DATE`), every other placeholder left verbatim as the visible TODO; the set is committed in the worktree. Reason: the minted set must validate by the format core that minted it (measured in the suite).
5. **`_worktrees/` is ignored in git, by the engine** - create appends the ignore line when absent and commits it as `chore:`. Reason: the consumer's `git status` must stay clean without a manual step.
6. **Complete verifies, then never guesses** - Every refusal precedes every write: a dirty worktree, a missing companion (`<STORY>-tests.md`, `<STORY>-knowledge-map.md`), no worktree for the story, a root not on the declared main branch (the refusal names both branches, detached head included), or a dirty root - each refuses naming the reason. The tag `v<STORY>` lands at the worktree head; the merge into the declared main branch is `--no-ff` (the story stays a story in history); a failed merge is ABORTED when a merge is in progress (no `MERGE_HEAD` left behind), the error carries git's own words (git reports a merge conflict on stdout, so the engine surfaces stdout too), and the worktree, the branch and the story stay intact - complete is idempotent (an already-completed `**Status:**` skips the mark commit, an existing `v<STORY>` tag is not re-created), so a re-run after the conflict is resolved on the main branch completes the story; then the window: completed sets beyond `**StoryHistoryKeep:**` MOVE to `story/history/` - archived, never deleted (the Epic's whole story history is kept, measured on the ahabase Epic itself: its newest two completed sets stay in `story/`, every older one lives in `history/`); the archive move is committed (`chore:`) only when it moved something; the worktree and the branch are removed. Reason: fail-closed is the package's standing shape - a complete that merges into whatever branch happens to be checked out, or a conflicted merge that leaves the story marked, tagged and unrecoverable, reports success while guessing (both measured by review, AHA-0030); the tag version IS the story identity (no separate version store to drift); deleting history to honor a window would be a data-loss shape the tree never asked for.
7. **Status reads, never writes** - `active:` the live-worktree story in progress; `open:` the worktree stories and the on-main story documents whose `**Status:**` is not completed (companions, the Priorities file and the identity are not stories); `completed:` the distinct story numbers completed in `story/` (within the window) or archived in `history/`. Reason: a report that writes is a measurement that changes its subject.
8. **One lock over the shared-tree phases** - The whole mint and complete's main-tree phase run under ONE exclusive inter-process lock: a file inside the repository's COMMON git directory (resolved through `rev-parse --path-format=absolute --git-common-dir`, so never in status and never in history, and ONE mutex per repository whichever tree - main or linked worktree - the command runs from; keying on the per-invocation git dir instead let a session inside its own worktree take a different mutex over the same shared refs, measured by review in AHA-0032 round 1), taken through the platform arm's `lock` (filelock: flock on POSIX, msvcrt on Windows - released on process death, so a crashed holder strands nothing), with a bounded wait that refuses by name on expiry. Work inside distinct worktrees never takes the lock. The mint leaves nothing behind whichever way it dies: a failure of ANY class after the worktree add (BaseException - OSError, StoryError, click's Abort, KeyboardInterrupt) rolls the mint back, the worktree and the branch removed, the refusal naming the failure and the cleanup, an interrupt re-raised after the cleanup so it keeps its class; a create killed outright (SIGKILL runs no rollback) leaves a half-minted corpse - a story-named worktree whose branch holds no commit beyond the main branch - and the next create, inside the lock, heals every corpse (worktree and branch removed) so the number returns to the scan instead of wedging or orphaning; the heal is STRICT (round-2 review, AHA-0032): a corpse is exactly a killed mint's shape - the branch reflog holds only its creation entry and the worktree's dirt is limited to the mint's own template files - so a hand-merged story's worktree (the consumer landed it by plain git; no commit sits beyond main either) with uncommitted files survives a following create untouched, a worktree hand-made on a creation-only branch whose only dirt IS the mint's own template files is indistinguishable from a killed mint by design and heals the same way, and a classification failure fails closed the same way (nothing deleted). Reason: the scan reserves nothing until the story set lands, so two concurrent creates mint the same number and collide at three layers - the shared index lock, the per-worktree admin lock, the filesystem - and the aftermath is a prunable worktree plus orphan branches that only manual surgery recovers (measured 2026-11-21, the issue filed with AHA-0032); concurrent completes lose the update at the merge (git's own refusal, healed by the re-run). The lock is a mutex, not state: nothing derived is stored, the tree stays the only record.

## Template

The modules and their purposes:

| Path | Purpose |
|------|---------|
| `src/ahabase/story.py` | the engine: `next_number(epic)` (the scan), `create(epic, description)`, `status(epic)`, `complete(epic, story)`, `main_branch(epic)`, `history_keep(epic)` |
| `src/ahabase/cli_story.py` | the door: `ahabase story create/status/complete [--root DIR]` |
| `tests/test_story.py` | the suite: scratch consumer git repository, e2e create → edit → complete, the scan re-run, refusals, the window, the door |
| `tests/test_story_parallel.py` | the parallel suite (AHA-0032): concurrent creates and completes through real processes, the killed-holder and injected-failure red arms, the lock-free work proof |
| `tests/parallel/run.sh` | the story rows' entry: resolves the worktree's own venv, fails closed when absent |

## Structure

| Section | Required |
|---------|:--------:|
| Overview | ✅ |
| Rules | ✅ |
| Template | ✅ |
| Structure | ✅ |
| Example | ✅ |
| Related | optional |

## Example

The suite's scratch repository is the canonical run: one archived story in `history/` (the numbering's floor), `create` mints `DEMO-0002` with a set that passes `grid4d.validate`, one document edit, `complete` leaves `vDEMO-0002` tagged, the set merged and held in `story/` by the default window, the worktree and branch gone - and the next `create` mints `DEMO-0003`, because the scan reads the tree, not a counter. The consumer leg's two cycles with the window at 1 prove the archive move: the first completed set stays in `story/`, the second completion carries it to `history/` - kept, never deleted. The parallel suite fires two doors at the same instant: five paired creates mint `DEMO-0002` through `DEMO-0011` with no orphan branch and no prunable entry, a create invoked from inside a linked worktree takes the same common lock as one from the main root, two paired completes each land exactly one merge, a create fired against a completing session waits and mints the next number, a holder killed mid-flight strands nothing (the waiting create proceeds on its own), a mint killed outright leaves a corpse the next create heals with the number returned - and an injected failure of any class leaves no worktree and no branch behind.

## Related

- [ontology-grid4d-blueprint](ontology-grid4d-blueprint) - the concept this implements (the story set and its naming)
- [implementation-grid4d-format-core-blueprint](implementation-grid4d-format-core-blueprint) - the core whose patterns the mint fills
