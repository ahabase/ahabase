# AHA-0032-tests

> Test definition for AHA-0032 with one test per requirement.

## Design

The races only exist between real processes, so every row drives the installed CLI through subprocesses fired at the same instant, inside a scratch epic each row builds for itself. The harness lives in the package test suite (tests/test_story_parallel.py); the rows below enter it through tests/parallel/run.sh, which resolves the worktree's own venv and fails closed with a named reason when the substrate is missing. The kill and injected-failure arms (R4) are mutant-style: they prove the guard bites, not that the happy path exists - the kill arm kills an external lock holder, the corpse arms pre-plant the exact state a SIGKILLed mint leaves (before and after the template writes) and witness the heal, the survival arm pre-plants a hand-merged story with an uncommitted note and witnesses the heal REFUSING it, and each strict leg carries its own witness - a clean hand-merged worktree survives only through the reflog leg, a hand-made creation-only worktree with one foreign file survives only through the dirt leg (a worktree whose only dirt IS the mint's templates is indistinguishable from a killed mint by design and heals the same way), the failure arms inject OSError, click's Abort and a raw KeyboardInterrupt.

## Definition

```yaml
tests:
  - name: R1-concurrent-create
    description: two create processes fired simultaneously per round, five rounds in a scratch epic - both stories minted each round, distinct numbers, no orphan branches, no prunable admin entry, one ignore line, no traceback in any output
    command: sh tests/parallel/run.sh r1_concurrent
    expect:
      exit_code: 0
  - name: R1-common-dir-lock
    description: a create invoked from inside a linked story worktree (default root) keys on the repository's common git directory like one from the main root - an external holder of the common lock blocks it, then it completes, and the repository holds exactly one lock file
    command: sh tests/parallel/run.sh r1cwd
    expect:
      exit_code: 0
  - name: R2-concurrent-complete
    description: two complete processes fired simultaneously on two stories with committed sets - both completed, exactly one merge commit per story, both tags, no story worktree or branch left, status counts both completed
    command: sh tests/parallel/run.sh r2
    expect:
      exit_code: 0
  - name: R3-create-waits-for-complete
    description: complete and create fired at the same instant - both succeed, the minted number is exactly one past the completing story's, no refusal names uncommitted changes
    command: sh tests/parallel/run.sh r3
    expect:
      exit_code: 0
  - name: R4-killed-holder-heals-corpses
    description: an external lock holder killed with kill -9 - the waiting create proceeds with no manual prune; both kinds of half-minted corpse a killed mint leaves (bare - branch at the main head, no writes; written - the story document uncommitted, which the scan would otherwise skip past) are healed by the next create - no corpse directory, no corpse branch, the number reused, no prunable entry; and a HAND-MERGED story's worktree (main fast-forwarded to its head, an uncommitted note inside) SURVIVES the next create untouched - the heal is strict (creation-only branch reflog, dirt limited to the mint's own files), each leg witnessed ALONE - a hand-merged story with a CLEAN worktree survives only through the reflog leg, and a hand-made worktree on a creation-only branch carrying one foreign user file survives only through the dirt leg
    command: sh tests/parallel/run.sh r4a
    expect:
      exit_code: 0
  - name: R4-injected-failure-cleans-up
    description: a failure injected between worktree add and the story-set commit - an OSError, click's Abort, and a raw KeyboardInterrupt - each rolls the mint back (no worktree directory, no branch), the refusal names the failure and the removal (an interrupt keeps its class at the engine; the door renders it exit 1), and the next create recovers
    command: sh tests/parallel/run.sh r4b
    expect:
      exit_code: 0
  - name: R5-work-never-blocks
    description: an external process holds the lifecycle lock while a plain git commit lands in a story worktree - the commit succeeds immediately; the lock file stays inside the git directory, absent from status and history
    command: sh tests/parallel/run.sh r5
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1-concurrent-create | ✅ | 2026-11-21 |
| R1-common-dir-lock | ✅ | 2026-11-21 |
| R2-concurrent-complete | ✅ | 2026-11-21 |
| R3-create-waits-for-complete | ✅ | 2026-11-21 |
| R4-killed-holder-heals-corpses | ✅ | 2026-11-21 |
| R4-injected-failure-cleans-up | ✅ | 2026-11-21 |
| R5-work-never-blocks | ✅ | 2026-11-21 |

Run-at: 501ec2b1b95f8e7268ca6c2819b2b317d2b8020b

Run at d928924c7f20c473987b80947cbb3783ef5f79df

## Related

- [AHA-0032](AHA-0032) - Parent story

---
## _behavior

enforced_by:
  - pattern: gof-behavioral-template-method
    how: tests skeleton minted per story (R-per-requirement rows)
  - pattern: gof-behavioral-interpreter
    how: _behavior validation plus the stop-hook coverage matcher reading Execution rows

validation:
  required_sections: [Design, Definition, Execution]
  definition_format: yaml_code_block
