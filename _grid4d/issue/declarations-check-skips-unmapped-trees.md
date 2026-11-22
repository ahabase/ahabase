# Declarations check skips unmapped trees and exits green

> `declarations check --epic-root` maps a tree to its Epic through git and falls back to the directory name; a tree that maps to nothing silently skips the whole Epic scope and exits 0 - a check that can pass on a tree it never looked at.

**Status:** open
**Priority:** medium

## Problem

Measured 2026-10-30 (AHA-0015): on a copy of this Epic's tree extracted without `.git` into a directory named `tree`, with one declared page deliberately missing, `declarations check --epic-root <copy>` printed only `declarations check: no subepics` and exited 0 - the Epic-scope block never ran, because `map_tree_to_epic_name` fell back to the directory name (`tree`), no `tree-projections-pattern.md` exists, and the epic branch of the check treats a missing declaration as "nothing to check" (`cli_history.py`: `if epic_decl is not None:`). The same copy in a directory named `ahabase` reports `DRIFT - gaps: AHABASE-Issues.md` and exits 1, as it should. The SubEpic half has the same shape: a SubEpic without a declaration is reported `no declaration (default set applies)` - stated - but an Epic-scope tree the mapper cannot name is not reported at all.

## Expected

A tree passed with `--epic-root` that maps to no known Epic is refused loudly (`unknown epic <name>` and a non-zero exit), not silently skipped; the directory-name fallback never turns a check into a no-op.

## Fix

In evolucean's repository. Until then this Epic's red controls name their scratch copies `ahabase` (noted in AHA-0015's tests Design and story Notes).

## Related

- [AHA-0015](AHA-0015) - where it was measured and worked around
- [story-prefix-derived-from-repo-name](story-prefix-derived-from-repo-name) - the same naming-not-reading class
