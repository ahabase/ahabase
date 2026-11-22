# AHA-0026-tests

> Test definition for AHA-0026 with one test per requirement.

## Design

Test requirements for AHA-0026. One test per requirement.

## Definition

```yaml
tests:
  - name: R1_blueprint_names_both_roles
    description: The implementation blueprint carries the two-executables paragraph naming runner and bound helper.
    command: 'B=_grid4d/subepic/ahabase-llm/implementation/implementation-ahabase-llm-blueprint.md; grep -q "Two executables" $B && grep -q "safe_executable" $B && grep -q "safe bind NAME /absolute/path/to/HELPER" $B && ! grep -q "bind NAME /absolute/path/to/ahabase" $B'
    expect:
      exit_code: 0
  - name: R2_key_value_separates_runner_and_helper
    description: The key_value tests with a fake runner pass.
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/llm/test_session.py'
    expect:
      exit_code: 0
  - name: R3_verify_and_switch_use_the_bound_run
    description: The verify and switch tests for the bound run pass.
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/llm/test_verify.py'
    expect:
      exit_code: 0
  - name: R4_release_ci_recorded
    description: The Notes record the green matrix run.
    command: 'grep -q "CI measured (R4): green" _grid4d/story/AHA-0026.md'
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_blueprint_names_both_roles | ✅ | 2026-11-08 |
| R2_key_value_separates_runner_and_helper | ✅ | 2026-11-08 |
| R3_verify_and_switch_use_the_bound_run | ✅ | 2026-11-08 |
| R4_release_ci_recorded | ✅ | 2026-11-08 |

Run at 424b65042e3e3305d40d2115e2145b925829f993
## Related

- [AHA-0026](AHA-0026) - Parent story

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
