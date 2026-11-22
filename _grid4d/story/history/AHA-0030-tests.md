# AHA-0030-tests

> Test definition for AHA-0030: one test per requirement.

## Design

Test requirements for AHA-0030. One test per requirement: R1 the grid4d format core's suite, R2 the story lifecycle's suite, R3 the containment gate over the grown package, R4 the consumer leg (one script, exit 0, expected failures included), R5 the full suite.

## Definition

```yaml
tests:
  - name: R1_grid4d_format_core
    description: The format core's suite passes - identity split, seeded violations with locations, grammar derivation, pattern order, placeholders, links fold, the init skeleton.
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_grid4d.py'
    expect:
      exit_code: 0
  - name: R2_story_lifecycle
    description: The story lifecycle's suite passes - mint by scan, worktree + branch, status, the fail-closed refusals, the window archiving beyond it, the door.
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_story.py'
    expect:
      exit_code: 0
  - name: R3_containment_gate
    description: The containment gate passes over the grown package - the patterns ship as pinned package data, a mutant identifier in a new module is RED, a .md outside patterns/ is RED.
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_artifact_containment.py'
    expect:
      exit_code: 0
  - name: R4_consumer_leg
    description: The consumer leg holds - the built wheel in a clean venv under a throwaway HOME, init + validate green, three seeded violations failing nonzero with their naming report, two lifecycle cycles with the archive move, per-step inventory diffs, the HOME snapshot unchanged. One script, exit 0.
    command: 'AHABASE_LEG_PYTHON=python3.13 ./tests/consumer-leg.sh'
    expect:
      exit_code: 0
  - name: R5_full_suite
    description: The full suite passes on the story branch (the three-platform matrix rides CI; its run ids are in the story's Notes).
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q'
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_grid4d_format_core | ✅ | 2026-11-20 |
| R2_story_lifecycle | ✅ | 2026-11-20 |
| R3_containment_gate | ✅ | 2026-11-20 |
| R4_consumer_leg | ✅ | 2026-11-20 |
| R5_full_suite | ✅ | 2026-11-20 |

Run at 83cef940f4988b8bdb80ae254ce732c3698bc368
## Related

- [AHA-0030](AHA-0030) - the parent story
