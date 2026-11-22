# story create falls through an unpinned workspace

> AHA-0033 blueprint decision D1 says `story create` refuses when the workspace is not pinned explicitly or the repo sits outside it - "no silent fall-through to the default workspace". The engine accepts both cases silently today.

**Status:** open
**Priority:** high

## Problem

Measured twice independently in the AHA-0035 round-1 review (seats c020eeb4 home-6098/6099 and 9327c5e0 home-6100, sandboxed HOME, private workspaces):

- **Unpinned arm:** with `AHABASE_WORKSPACE` unset, a repository anywhere on disk mints its worktree at `<HOME>/ahabase/_worktrees/<repo>/<STORY>` - creating `~/ahabase` on the way. A consumer who forgot the pin scatters worktrees of unrelated epics into the default workspace, the exact class D1 was written against.
- **Outside arm:** with the workspace pinned to W, a repository outside W is accepted - its worktree lands at `W/_worktrees/<repo>` on a shelf whose workspace never owned the repo.

A grep over `src/` finds no forgotten-pin guard anywhere, while the approved blueprint carries the clause verbatim. Until this story's workspace topology (AHA-0035) the fall-through was invisible in the layout; the new topology makes it load-bearing, and two review seats reproduced both arms.

## Expected

The D1 refusal, as its own story: `story create` refuses unless the workspace is explicitly chosen AND the repository sits under it, each refusal naming its reason and its remedy. The design question that story must answer first: what counts as an explicit pin - the env var alone, or also a workspace marker minted by `ahabase workspace ensure` (a marker keeps the fresh-consumer first run working without an env var; env-only is stricter). Two standing traces currently WITNESS the fall-through as load-bearing and flip to refusal assertions with the fix: `tests/consumer-leg.sh` (the mint sections) and `playground/tests/r4-arms.sh` arm 1.

## Fix

Deliberately deferred out of AHA-0035 (recorded in its story Notes): the refusal changes every unpinned consumer flow - the consumer leg, the playground isolation arm, the bootstrap docs - and deserves its own story with a row per refusal arm, not a rider on the topology story. The follow-up candidate is registered as [idea-workspace-guard-story](idea-workspace-guard-story).

## Related

- [AHA-0033](AHA-0033) - the blueprint carrying decision D1
- [AHA-0035](AHA-0035) - the topology that made the fall-through load-bearing; the round that measured it
- [implementation-ahabase-config-door-blueprint](implementation-ahabase-config-door-blueprint) - the workspace seam (`AHABASE_WORKSPACE`, `get_workspace_dir`)
