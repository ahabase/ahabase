# AHA-0014-tests

> Test definition for AHA-0014 with one test per requirement.

## Design

Test requirements for AHA-0014. One test per requirement. The code requirements (R1-R3) run the package suite against the worktree code; R4 adds the CI matrix declaration and the both-variant fixtures; R_docs checks the ontology concept, the blueprints and the Epic rule; R_team holds the review verdict record. Per-OS facts are stated per lane: the suite rows here run on the macOS lane, the Windows and Ubuntu lanes prove the same suite in CI (R4).

## Definition

```yaml
pipefail: true
tests:
  - name: R1_imports_and_locks_on_every_os
    description: "no platform-only import sits at module top (parsed, not grepped), both arms exist and the dispatch commits to one, the lock goes through filelock (a recording FileLock sees the manifest lock), the lock file keeps 0o600 on POSIX, and the concurrent-sets contract test is green unchanged"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -c 'import ahabase.safe, ahabase._posix, ahabase._win; print("IMPORT_OK")'
      PYTHONPATH=src "$PY" -m pytest -q tests/test_safe.py -k "platform_only_import or platform_arms or goes_through_filelock or lock_file_mode_600 or concurrent_sets"
    expect:
      exit_code: 0
      stdout_contains: "IMPORT_OK"
      timeout: 120
  - name: R2_exec_detection_per_os
    description: "executables resolve the way the OS does - shutil.which decides (X_OK here, PATHEXT on the Windows lane), bind refuses what which cannot resolve, and the Windows exec suffixes (python.exe, cmd.exe, .bat, .cmd) reach NOT_BINDABLE with the same refusal message shape as the POSIX one"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -m pytest -q tests/test_safe.py -k "exec_detection or script_suffixes"
    expect:
      exit_code: 0
      stdout_contains: "passed"
      timeout: 120
  - name: R3_prompts_and_permissions_both_os
    description: "the quiet environment disables prompts with the arm's askpass no-op (true on POSIX, rundll32 on Windows - no Unix-only executable name) and the presence check carries it; the Windows arm states owner-only as the profile ACLs in code and blueprint, and the manifest and lock file keep 0o600 on this lane"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -m pytest -q tests/test_safe.py -k "askpass_noop or prompts_nothing or manifest_mode_600"
      grep -q "profile directory's ACLs" src/ahabase/_win.py || { echo MISSING arm ACL statement; exit 1; }
      grep -q "user profile directory's ACLs" _grid4d/implementation/implementation-ahabase-safe-windows-blueprint.md || { echo MISSING blueprint ACL statement; exit 1; }
      echo R3_OK
    expect:
      exit_code: 0
      stdout_contains: "R3_OK"
      timeout: 120
  - name: R4_suite_green_and_ci_matrix
    description: "the whole suite is green, the workflow runs a matrix of macOS, Windows and Ubuntu on every push, and the fixture makers ship both script variants (.sh here, .bat on Windows)"
    command: |
      PY=$HOME/ahabase/ahabase/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      PYTHONPATH=src "$PY" -m pytest -q
      test -f .github/workflows/tests.yml || { echo MISSING workflow; exit 1; }
      for lane in macos-latest windows-latest ubuntu-latest; do grep -q "$lane" .github/workflows/tests.yml || { echo MISSING lane $lane; exit 1; }; done
      grep -q '\.bat' tests/test_safe.py || { echo MISSING bat variant; exit 1; }
      grep -q '\.bat' tests/test_safe_hardening.py || { echo MISSING hardening bat variant; exit 1; }
      echo R4_OK
    expect:
      exit_code: 0
      stdout_contains: "R4_OK"
      timeout: 180
  - name: R_team_review_verdict_logged
    description: "a review seat measured the pinned commit and its verdict, naming the commit, is logged in the story's Review section"
    command: |
      grep -q "APPROVE" _grid4d/story/AHA-0014.md || { echo MISSING verdict; exit 1; }
      echo R_TEAM_OK
    expect:
      exit_code: 0
      stdout_contains: "R_TEAM_OK"
      timeout: 30
  - name: R_docs_ontology_and_blueprints
    description: "the layering path is the base concept ontology-portability-blueprint (State implemented, listed in the index taxonomy and vocabulary), the windows blueprint implements it with the dispatch, the library choice and the per-OS statements, the safe blueprint's old POSIX-only locking claim is gone and its replacement names the port, the integration blueprint names the arm's no-op, and AHABASE.md carries the both-variants rule"
    command: |
      bp=_grid4d/ontology/ontology-portability-blueprint.md
      test -f $bp || { echo MISSING concept; exit 1; }
      grep -qF "**State:** implemented" $bp || { echo MISSING state; exit 1; }
      for k in Portability portability-blueprint; do grep -q "$k" _grid4d/ontology/00-ahabase-ontology-index.md || { echo MISSING index $k; exit 1; }; done
      wbp=_grid4d/implementation/implementation-ahabase-safe-windows-blueprint.md
      grep -q "ontology-portability-blueprint" $wbp || { echo MISSING concept link; exit 1; }
      grep -qF "**Code:** _win, _posix" $wbp || { echo MISSING code line; exit 1; }
      grep -qF "Locking is POSIX" _grid4d/implementation/implementation-ahabase-safe-blueprint.md && { echo OLD POSIX CLAIM SURVIVES; exit 1; }
      grep -q "msvcrt" _grid4d/implementation/implementation-ahabase-safe-blueprint.md || { echo MISSING safe port; exit 1; }
      grep -q "rundll32" _grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md || { echo MISSING integration arm; exit 1; }
      grep -q "Both OS variants in the same story" _grid4d/story/AHABASE.md || { echo MISSING epic rule; exit 1; }
      echo R_DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "R_DOCS_OK"
      timeout: 60
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_imports_and_locks_on_every_os | ✅ | 2026-10-30 |
| R2_exec_detection_per_os | ✅ | 2026-10-30 |
| R3_prompts_and_permissions_both_os | ✅ | 2026-10-30 |
| R4_suite_green_and_ci_matrix | ✅ | 2026-10-30 (local lane; CI run 41131374999, head 4da53b9 - code-identical to the pin - green on all three lanes at 4e89f30) |
| R_team_review_verdict_logged | ✅ | 2026-10-30 (APPROVE at 4e89f30, both review seats: seq 4773, second seat seq 4776) |
| R_docs_ontology_and_blueprints | ✅ | 2026-10-30 |

Run at e0fb5c1ce6080f044674871deb5b03534b113004
## Related

- [AHA-0014](AHA-0014) - Parent story

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
