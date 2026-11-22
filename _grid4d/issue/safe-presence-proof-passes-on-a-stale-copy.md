# safe presence proof passes on a stale copy

> `_refresh_targets` proves a write by `present()`, which only asks whether the destination holds SOME value - a stale copy from the previous rotation satisfies it, so a silent write failure over an existing item is still reported "refreshed".

**Status:** open
**Priority:** high

## Problem

Found in the delta review of [AHA-0012](AHA-0012) at b3b0df7, 2026-10-30, by the reviewer-deepseek seat (static-only, seat 656cf2f6). The presence-proof added in 754fe81 closes the empty-destination case (no helper configured); it does not close the steady-state case of a rotation: `set` on an existing name rewrites targets whose store already holds the PREVIOUS value. A helper that accepts the write, exits 0 and persists nothing leaves the old value in place - `present()` reads a non-empty password / `gh auth status` answers 0 - and the target is reported "refreshed". No code path in the delta compares what was written with what is stored, so the rule 7 sentence "a write is proven by presence" holds only under the unstated precondition that the destination held nothing before.

## Expected

`present()` already reads the value into the checking process and drops it; the refresh proof should compare that value (its digest, in constant time as `compare` does) with the value just written - in-process, never printed, so the no-disclosure rule is untouched. The kinds own the comparison (the protocol grows a verify), the test fake grows a lying-with-stale-copy mode, and the blueprint sentence is scoped to what the mechanism then proves.

Along the way (same review, non-blocking): `impl.absence` is read in the `else:` branch outside the try, so a kind raising on the attribute takes the whole loop down instead of being reported; and nothing enforces the protocol member (`runtime_checkable` is off) - one assertion over `TARGET_KINDS` closes it.

## Fix

A small safe story before the first real targets are registered (the owner's `safe target add` steps are still pending) - the wording and the proof are cheapest to fix while no live rotation depends on them.

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rule 7, "a write is proven by presence"
- [AHA-0012](AHA-0012) - where the presence-proof landed (754fe81)
