# idea: workspace guard story (the D1 refusal)

> The named follow-up for the AHA-0035 round-1 finding 2: `story create` refuses an unpinned workspace and a repository outside the pinned workspace - AHA-0033 decision D1, measured unimplemented by two review seats.

**Source:** AHA-0035 round-1 review (home-6098/6099, home-6100); the open record is [issue-story-create-falls-through-unpinned-workspace](issue-story-create-falls-through-unpinned-workspace).

## The story it wants to be

One default story, small surface: a refusal branch in `story.py`'s mint path (the guard lives beside `_worktrees_dir`), a refusal row per arm in the story suite, and the two standing fall-through witnesses flipped to refusal assertions (`tests/consumer-leg.sh` mint sections, `playground/tests/r4-arms.sh` arm 1). The design decision it opens with: what counts as an explicit pin - the env var alone, or also a workspace marker minted by `ahabase workspace ensure` so a fresh consumer's first run works without an env var. The consumer docs (playground CLAUDE.md "source the entrypoint first") already push the pin; the guard turns the push into a hard edge.

## Why it is its own story

The refusal changes behavior for every unpinned consumer - the consumer leg, the playground isolation arm, the bootstrap docs all carry the fall-through today as a load-bearing witness. Riding it on AHA-0035 would have made the topology story a behavior break for consumers at the same time; the review's own alternative was to name the deferral, which this idea is.

## Second leg from the round-2 review (home-6106, seat c020eeb4)

A legacy in-repo story is VISIBLE after AHA-0035 (the porcelain scan) but not COMPLETABLE: `story complete` still builds its worktree path from `_worktrees_dir` (the workspace shelf) while `status` resolves the real location through `_worktree_paths`. Measured on a live old-layout worktree: complete refuses with "no worktree for <STORY> under <workspace>/_worktrees/<epic>" - the message points at the shelf and never suggests `git worktree move`. Not a regression (the round-1 engine hid the story altogether) and the population is the pre-release playground, but the story should resolve the worktree through `_worktree_paths` in complete too (the same helper), or name the move in the refusal.
