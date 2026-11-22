# verify write-rules enforces a rule the owning tree never declared

> Running `knowledge-usage verify` from the ahabase tree prints `✗ Write rules: 1 problems - rules file present but the owning tree declares no writes - the guard enforces an undeclared rule`. The ahabase identity declares no `writes:`, yet a generated rules file exists and the guard enforces it - a rule with no declarer.

**Status:** open
**Priority:** medium

## Problem

The write-rules guard reads a generated rules file (the evolucean-style `*_story.md` write rules); when the owning Epic's identity declares no `writes:` block, the file is still present and the guard still enforces it. Verify therefore fails on the ahabase tree with a rule nobody in this Epic declared. The failure is tree-dependent: the same command from the evolucean tree instead flags `llm-pin-model-tests.py` (that Epic's own pre-existing finding, logged in evolucean as verify-flags-llm-pin-model-tests-while-suite-runs-green).

First seen during AHA-0023's R2 measurement (reviewer checkpoint 2, 2026-11-08): identical on the ahabase main tree at 8e994c5 with no story content - pre-existing, not caused by AHA-0023, and never naming AHABASE-Priorities.md.

## Occurrences

| Date | Where | Signature |
|------|-------|-----------|
| 2026-11-08 | reviewer (seat 565b7f0e), AHA-0023 worktree at 0742620 | `✗ Write rules: 1 problems` + the undeclared-rule line |
| 2026-11-08 | reviewer, ahabase main tree at 8e994c5 (no story) | identical - pre-exists the story |
| 2026-11-08 | author (44af88c3), AHA-0023 worktree at 0742620 | identical, confirmed first-hand |

## Solution Direction

Pick one owner of the truth: either the ahabase identity declares its `writes:` (the write rules this Epic actually wants guarded), or the write-rules check skips an Epic whose identity declares no writes instead of enforcing the generated file. The guard must not enforce a rule without a declarer.

## Related

- [AHA-0023](AHA-0023) - the story whose review surfaced it (logged per R_issues, no silent findings)

---
