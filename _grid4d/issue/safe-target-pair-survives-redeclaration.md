# safe target pair survives redeclaration

> A manifest that already holds both custody modes of one target (plain + `"copy": false`, hand-written or written by the pre-remedy commit) is not healed by re-declaring it: the early return fires on the first match and nothing is saved, and adding the other spec can leave a duplicated identical entry.

**Status:** open
**Priority:** low

## Problem

Found in the round-2 review of [AHA-0020](AHA-0020) at 38787df, 2026-10-31, by the reviewer seat home-4937 (session 641903b1, journal seq 4940) - a non-blocking note on the conversion remedy (90946fa). The shipped code can no longer CREATE the pair (`target_add` keys its identity on `_same_target`, same as `target_remove`), but a manifest that already holds `[plain, scope-only]` for one host/account - hand-written, or written by the pre-remedy branch commit 9432c27 which was never released - is not healed by re-declaring:

- re-adding the plain spec: `next()` finds the plain entry first, `replaced == spec`, the early return fires - nothing is saved, BOTH entries survive;
- re-adding the scope-only spec: the replacement comprehension maps EVERY `_same_target` match to the new spec, leaving `[scope-only, scope-only]` - a duplicated identical entry that `safe list` prints twice and rotation names twice in `scope`.

## Expected

The heal is two lines: collapse all `_same_target` matches to the single new spec, and take the early return only when exactly one match exists and equals the spec. Pinned by a test whose fixture is a hand-written pair manifest, asserting one entry after re-declaring in either direction (the arming fixture - without it the row measures nothing).

## Fix

A small follow-up riding the next safe story; not blocking AHA-0020 (the reviewer's explicit call: the shipped code cannot create the state, so the defect is reachable only from a manifest written outside it).

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rule 7, the one-custody-mode rule this heal completes
- [AHA-0020](AHA-0020) - the conversion remedy (90946fa) whose review surfaced this
