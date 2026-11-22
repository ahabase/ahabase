# AHA-0025-tests

> Test definition for AHA-0025 with one test per requirement.

## Design

Test requirements for AHA-0025. One test per requirement.

## Definition

```yaml
tests:
  - name: R1_four_tests_pass_and_ci_recorded
    description: The four tests pass locally and the Notes record the green matrix run.
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_config_door.py tests/test_safe.py tests/test_safe_git_helper.py && grep -q "CI measured (R1)" _grid4d/story/AHA-0025.md'
    expect:
      exit_code: 0
  - name: R2_only_tests_changed
    description: No file outside tests and the story documents differs from the baseline.
    command: 'base=$(git merge-base origin/main HEAD) && test -n "$base" && git diff --name-only $base HEAD > /tmp/aha25-changed.txt && test -s /tmp/aha25-changed.txt && ! grep -v -e ^tests/ -e ^_grid4d/story/AHA-0025 /tmp/aha25-changed.txt'
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_four_tests_pass_and_ci_recorded | ✅ | 2026-11-08 |
| R2_only_tests_changed | ✅ | 2026-11-08 |

Run at 3d33f0e10ad9dbb720bc304033d9d6ea650a5026
## Related

- [AHA-0025](AHA-0025) - Parent story

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
