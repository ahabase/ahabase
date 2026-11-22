# AHA-0013-tests

> Test definition for AHA-0013 with one test per requirement.

## Design

Test requirements for AHA-0013. One test per requirement. The code requirements (R1, R2, R4) run the package suite against the worktree code; R3 and R_docs check the records and the blueprints' text, where the convention and the amended rule are stated.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_refresh_proven_by_the_stored_value
    description: "a stale copy (the rotation's steady state - the destination answers with the old value) fails the proof while presence passes; the proof reads the destination back (git credential fill, gh auth token) and compares the value by digest; every registered kind carries the proof members"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -m pytest -q tests/test_safe.py -k "stale_copy or proof_members or verifies"
    expect:
      exit_code: 0
      stdout_contains: "passed"
      timeout: 120
  - name: R2_absence_messages_name_their_conditions
    description: "the git absence message names both causes (no helper configured, resolution from the directory the safe ran in; or a helper whose store holds no item - a locked keychain, an item never written); the gh message names a login existing with a different or stale token - asserted on the rendered messages, not the source literals; the prompt test is armed against ambient GCM and GIT values"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -c 'from ahabase import safe; git = safe.TARGET_KINDS["git-credential"].absence; gh = safe.TARGET_KINDS["gh-login"].absence; assert "either no credential helper is configured" in git and "resolved from the directory the safe ran in" in git and "a locked keychain, an item never written" in git and "a login can exist with a different or stale token" in gh; print("MESSAGES_OK")'
      PYTHONPATH=src "$PY" -m pytest -q tests/test_safe.py -k "prompts_nothing"
    expect:
      exit_code: 0
      stdout_contains: "MESSAGES_OK"
      timeout: 120
  - name: R3_records_and_conventions
    description: "the AHA-0012 record carries both late verdicts, exactly one bare Run at line with the counts in prose, the three issue files land, and both blueprints state the read-back proof"
    command: |
      old=_grid4d/story/AHA-0012.md
      oldt=_grid4d/story/AHA-0012-tests.md
      for k in "deepseek-reviewer seat" "reviewer-deepseek seat" "safe presence proof passes on a stale copy" ; do grep -qF "$k" $old || { echo MISSING "$k" in story; exit 1; }; done
      test "$(grep -c '^Run at ' $oldt)" = "1" || { echo RUN_AT_LINES $(grep -c '^Run at ' $oldt); exit 1; }
      grep -q "re-run at" $oldt && { echo STALE_ANNOTATED_LINE; exit 1; }
      grep -qF "re-measured at 754fe81" $oldt || { echo MISSING counts prose; exit 1; }
      for f in safe-presence-proof-passes-on-a-stale-copy safe-git-target-absence-remedy-explains-nothing story-tests-run-at-line-must-stay-bare ; do test -f _grid4d/issue/$f.md || { echo MISSING issue $f; exit 1; }; done
      grep -qF "reading the destination back" _grid4d/implementation/implementation-ahabase-safe-blueprint.md || { echo MISSING blueprint rule; exit 1; }
      grep -qF "gh auth token" _grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md || { echo MISSING integration gh; exit 1; }
      echo R3_OK
    expect:
      exit_code: 0
      stdout_contains: "R3_OK"
      timeout: 60
  - name: R4_suite_green
    description: "the whole suite, existing contract included, is green under the isolation (no real store, no real git or gh)"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -m pytest -q
    expect:
      exit_code: 0
      stdout_contains: "passed"
      timeout: 300
  - name: R_docs_state_what_was_built
    description: "the story records its decisions (verify, not presence; the gh read-back); the integration blueprint names the read-back glue; the issue files close against R1-R3"
    command: |
      st=_grid4d/story/AHA-0013.md
      for k in "Verify, not presence" "gh auth token" ; do grep -qF "$k" $st || { echo MISSING "$k" in story; exit 1; }; done
      grep -qF "compared, dropped" _grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md || { echo MISSING integration capture wording; exit 1; }
      grep -qF "closed by R1" $st && grep -qF "closed by R2" $st && grep -qF "closed by R3" $st || { echo MISSING issue closure links; exit 1; }
      echo R_DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "R_DOCS_OK"
      timeout: 60
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_refresh_proven_by_the_stored_value | ✅ | 2026-10-30 |
| R2_absence_messages_name_their_conditions | ✅ | 2026-10-30 |
| R3_records_and_conventions | ✅ | 2026-10-30 |
| R4_suite_green | ✅ | 2026-10-30 |
| R_docs_state_what_was_built | ✅ | 2026-10-30 |

All five rows green in the story worktree, 2026-10-30: R1 with 4 tests passed, R2 with the rendered messages asserted (MESSAGES_OK) and 1 test passed, R4 with 145 tests passed; R3 and R_docs by their greps (R3_OK, R_DOCS_OK).

Run at 3431ef6da76ccf26396787ab682d79981db39449

## Related

- [AHA-0013](AHA-0013) - Parent story

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
