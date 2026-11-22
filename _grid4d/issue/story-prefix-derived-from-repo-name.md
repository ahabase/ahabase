# Story projection prefix derived from the repository name

> The sync tail builds an Epic's ticket prefix as `<repository-name>-` in upper case; an Epic whose ticket prefix differs gets an empty Stories page that asserts a falsehood.

**Status:** open
**Priority:** medium

## Problem

Measured 2026-10-30 (AHA-0015, generator API on a scratch copy of this Epic's tree): the export tail of `sync` constructs each Epic as `prefix=f"{repo_name.upper()}-"`; for this repository that is `AHABASE-`, while this Epic's stories are minted `AHA-####`. The `stories` projection filters `story/` and `story/history/` by that prefix, so the page it would write here carries `Scope: AHABASE-* stories only` and `Total: 0 completed, 0 open` - false of an Epic with fourteen completed stories. With the true prefix (`AHA-`) the same call fills the page with all of them. The measurable carrier of the true value is the Epic identity document's own line (`_grid4d/story/AHABASE.md`: `**StoryPrefix:** AHA-`); the registry's per-Epic prefix entry (`_config/ahabase.yaml`, machine-local, outside the repository) may hold it too - the tail reads neither.

## Expected

The tail (and any epic-scope call site) derives an Epic's ticket prefix from the Epic's own declaration - the registry's story-prefix entry or the identity document's `StoryPrefix:` field - not from the repository name.

## Fix

In evolucean's repository. Until then this Epic declares no `stories` page ([ahabase-projections-pattern](ahabase-projections-pattern) names this issue); the measured evidence lives in AHA-0015.

## Related

- [ahabase-projections-pattern](ahabase-projections-pattern) - the declaration that waits on this
- [AHA-0015](AHA-0015) - where it was measured
