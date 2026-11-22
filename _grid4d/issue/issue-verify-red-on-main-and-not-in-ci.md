# issue: `ahabase verify` is red on main and the CI does not run it

**Status:** open
**Type:** rule enforcement gap (Links point inward, 0 Public content only), silent failure
**First seen:** 2026-11-09, architecture review of the package at v0.0028.0.0000.00; corrected the same day after a fresh-clone run (the 65 generated failures are not in git)
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) row 4 (trust: every graduation passes the open-zone checks), and so every row

## Problem

`ahabase verify` exits 1 on `main`. On a fresh clone (what a CI run sees) it reports **one** unresolved link: `issue/verify-write-rules-enforces-an-undeclared-rule.md` links `../story/AHA-0023`, a relative path into the story folder that does not resolve. This is exactly the kind of link the Rule "Links point inward" says must fail.

On a tree where the method's projections have been generated, the same command reports 66: the other 65 are in `_grid4d/subepic/*/_generated/`, which `.gitignore` excludes (`_generated/`). They exist only on that tree, and they link to the method's concepts. So the result of `verify` depends on whether generators ran on the tree, while git never holds those files.

The CI workflow (`.github/workflows/tests.yml`) runs only `pytest`. Nothing runs `ahabase verify`, so the Epic's own transparency gates (lineage, capabilities, containment, the link census) are not enforced on any commit. It is the same pattern as [issue-windows-ci-red-on-main-unseen](issue-windows-ci-red-on-main-unseen): a check that is red and that nobody reads.

## Why it matters

Every row of the priorities is a graduation, and a graduation must pass the open-zone checks. A check that only runs when someone remembers it is not a gate. On a working tree the one real failure is hidden among 65 failures of files that are not in the repository at all, so a reader cannot tell a new failure from the old noise.

## Candidate fixes

[idea-verify-as-a-ci-gate-with-named-exceptions](idea-verify-as-a-ci-gate-with-named-exceptions).
