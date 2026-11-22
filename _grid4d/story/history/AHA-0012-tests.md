# AHA-0012-tests

> Test definition for AHA-0012 with one test per requirement.

## Design

Test requirements for AHA-0012. One test per requirement. The code requirements (R2-R5) run the package suite against the worktree code; R1 and R_docs check the blueprints' text, where the ruled architecture is stated and drawn.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_architecture_drawn_and_stated
    description: "the safe blueprint carries the ruling and the Architecture section: the mermaid diagram (owner/set, entry, store, targets, the three transports, the nowhere-else invariant), every element naming its rule; rule 7 amended; the git row names the helper item a target; the integration blueprint names the glue (git credential approve)"
    command: |
      b=_grid4d/implementation/implementation-ahabase-safe-blueprint.md
      i=_grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md
      for k in "## Architecture" "Human ruling 2026-10-30, rule 7" "flowchart TB" "safe set NAME - the only rotation" "the same command refreshes" "targets - copies in a tool's own store, maintained by the safe (rule 7)" "entry NAME - names and metadata, never a value (rule 2)" "store - the one value (rule 3)" "safe run - the value in one child's environment (rule 4)" "safe://NAME read in the tool's own process (rule 1)" "a value nowhere else" "Environment variables are transport, never storage" "safe refresh NAME" "its item a target of the secret's entry - written and refreshed by the safe on rotation (rule 7)" ; do grep -qF "$k" $b || { echo MISSING "$k"; exit 1; }; done
      for k in "no own credential helper is written" "git credential approve" "git credential fill"; do grep -qF "$k" $i || { echo MISSING "$k" in integration; exit 1; }; done
      echo R1_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_OK"
      timeout: 60
  - name: R2_targets_in_the_manifest
    description: "an entry names targets (kind and destination); adding twice is one target; a malformed target is refused the way a malformed binding is; the kinds parse their arguments"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -m pytest -q tests/test_safe.py -k "malformed_target or target_add_twice or target_kinds_parse_and_label"
    expect:
      exit_code: 0
      stdout_contains: "passed"
      timeout: 120
  - name: R3_rotation_refreshes_targets
    description: "set refreshes the entry's targets and returns what it did; a failing target is named, not swallowed, and the value is stored regardless; a write the destination did not take is a failure, never a refreshed copy (git accepts a value with no helper configured); git and gh receive the value on stdin, never in an argument list; the CLI names an unreachable target and exits nonzero, and refresh rewrites it"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -m pytest -q tests/test_safe.py -k "set_refreshes_targets or failing_target or did_not_take or feeds_stdin or cli_target_add_list_refresh or wrong_spec"
    expect:
      exit_code: 0
      stdout_contains: "passed"
      timeout: 120
  - name: R4_health_knows_targets
    description: "health reports a target that is not present and names an unknown kind; a missing tool (no gh) makes its target absent, and the message carries no value; the presence check prompts nothing (no GUI, no terminal)"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -m pytest -q tests/test_safe.py -k "unknown_target_kind or missing_tools or failing_target or prompts_nothing"
    expect:
      exit_code: 0
      stdout_contains: "passed"
      timeout: 120
  - name: R5_suite_green
    description: "the whole suite, existing contract included, is green under the isolation (no real store, no real git or gh)"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -m pytest -q
    expect:
      exit_code: 0
      stdout_contains: "passed"
      timeout: 300
  - name: R_docs_blueprints_state_what_was_built
    description: "the blueprint's Template offers target add/remove and refresh; Structure names the target kinds; the story records the ruling, the fixture and the AHA-0011 overlap decision"
    command: |
      b=_grid4d/implementation/implementation-ahabase-safe-blueprint.md
      s=_grid4d/story/AHA-0012.md
      for k in "ahabase safe target add NAME KIND" "ahabase safe target remove NAME KIND" "ahabase safe refresh NAME" "GitCredentialTarget" "GhLoginTarget"; do grep -qF "$k" $b || { echo MISSING "$k"; exit 1; }; done
      for k in "The ruling (Human, 2026-10-30)" "AHA-0011 overlap - resolved" "Naming:" "agent boundary stands owed"; do grep -qF "$k" $s || { echo MISSING "$k" in story; exit 1; }; done
      echo R_DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "R_DOCS_OK"
      timeout: 60
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_architecture_drawn_and_stated | ✅ | 2026-10-30 |
| R2_targets_in_the_manifest | ✅ | 2026-10-30 |
| R3_rotation_refreshes_targets | ✅ | 2026-10-30 |
| R4_health_knows_targets | ✅ | 2026-10-30 |
| R5_suite_green | ✅ | 2026-10-30 |
| R_docs_blueprints_state_what_was_built | ✅ | 2026-10-30 |

Earlier runs (counts kept in prose - the freshness mechanism reads the bare Run at line only): at 53d9c55, R2-R5 with 3, 6, 3 and 139 tests passed (R1, R_docs by their greps); re-measured at 754fe81 after the review fix, R2-R5 with 3, 7, 4 and 141 tests passed (R1, R_docs by their greps).

Run at 9842f7241e009b3d9b5af1bfd4a94a314e4bd2a2

## Related

- [AHA-0012](AHA-0012) - Parent story

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
