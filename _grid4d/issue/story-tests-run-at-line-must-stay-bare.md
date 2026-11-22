# story tests run at line must stay bare

> A tests file's "Run at <sha> (...); re-run at <sha> (...)" line does not match the CLI's `RUN_AT_RE` (`^Run at ([0-9a-f]{7,40})\s*$`), so the freshness mechanism reads the file as ('unknown', 'no Run at line') - the certification is invisible to the thing that certifies it.

**Status:** open
**Priority:** medium

## Problem

Found in the delta review of [AHA-0012](AHA-0012) at b3b0df7, 2026-10-30, by the reviewer-deepseek seat, which ran the CLI's own freshness predicate on the delta's tests file and measured ('unknown', 'no Run at line'); the same file with a bare `Run at 754fe81...` line reads ('fresh', '754fe81'). `stamp_run_at` writes the bare line and, when the regex misses, inserts a NEW line under `## Execution` - so a line carrying counts and history is the one shape that cannot carry the claim, and a later stamp would silently add a second line.

## Expected

Exactly one bare `Run at <full-sha>` line naming the newest run; counts and the history of runs go into the Execution table or the prose under it, never into the Run at line. The AHA-0012 record was corrected to the bare shape on 2026-10-30.

## Fix

Convention from here on; guard option: the pattern validator or `verify` could reject an annotated Run at line.

## Related

- [AHA-0012-tests](AHA-0012-tests) - the file that carried the annotated line
- `implementation-story-blueprint` (a document of evolucean's repository, named in plain words - the open zone links only within its own) - the Execution section
