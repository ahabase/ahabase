# AHA-0020-tests

> Test definition for AHA-0020 with one test per requirement.

## Design

Test requirements for AHA-0020. One test per requirement. The rows run in this worktree against its own venv (``.venv`` created by the story) and the ``ahabase`` console script it installs. The R1 rows build a fixture manifest (env store, the fictional host ``fixture.github.example``) and measure the variant end to end: the owner-gated steps run under a pseudo-terminal (``script -q /dev/null``, the owner-confirm seam AHA-0002 built), the helper answer and the default's byte-identity are measured cross-process the way git and an owner drive them, and the pytest row holds the whole suite green with the variant's unit rows present. The R2 rows hold the tutorial and the blueprint to their rehearsal contract (the one-flag form, the measured output literals, the public-perimeter grep over every identifier the workspace's registry carries). R_team holds the review verdict record; R_docs and R_issues hold the documentation and story-notes assertions.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_scope_only_variant_cli_lifecycle
    description: "the owner-gated surface under a pty - add with --no-copy says scope only and writes copy false, list distinguishes, refresh writes nothing and says so, remove matches a spec typed without the flag, and --no-copy on gh-login is refused"
    command: |
      CLI=$PWD/.venv/bin/ahabase
      test -x "$CLI" || { echo NO_VENV; exit 1; }
      R=$(mktemp -d)
      printf '{"secrets": {"fixture-gh": {"store": "env", "key": "FIXTURE_GH", "purpose": "variant row", "targets": []}}}' > "$R/safe.json"
      export AHABASE_SAFE_MANIFEST="$R/safe.json" FIXTURE_GH=fixture-value-0123456789
      out=$({ printf 'fixture-gh\n'; sleep 2; } | script -q /dev/null "$CLI" safe target add fixture-gh git-credential fixture.github.example 1148 --no-copy 2>&1 | tr -d '\r')
      echo "$out" | grep -q "(scope only)" || { echo "NO SCOONLY MARK: $out"; exit 1; }
      echo "$out" | grep -q "maintains no copy" || { echo "NO NOCOPY TEXT: $out"; exit 1; }
      grep -q '"copy": false' "$R/safe.json" || { echo "NO COPY FIELD"; cat "$R/safe.json"; exit 1; }
      listed=$("$CLI" safe list 2>&1)
      echo "$listed" | grep -q "git-credential fixture.github.example/1148 (no copy)" || { echo "LIST BLIND: $listed"; exit 1; }
      out=$({ printf 'fixture-gh\n'; sleep 2; } | script -q /dev/null "$CLI" safe refresh fixture-gh 2>&1 | tr -d '\r')
      echo "$out" | grep -q "scope target git-credential fixture.github.example/1148 - no copy is maintained" || { echo "NO SCOPE LINE: $out"; exit 1; }
      if echo "$out" | grep -q "refreshed target"; then echo "FAKE REFRESHED: $out"; exit 1; fi
      out=$({ printf 'fixture-gh\n'; sleep 2; } | script -q /dev/null "$CLI" safe target remove fixture-gh git-credential fixture.github.example 1148 2>&1 | tr -d '\r')
      echo "$out" | grep -q "removed target" || { echo "REMOVE BLIND TO COPY FIELD: $out"; exit 1; }
      grep -q '"targets": \[\]' "$R/safe.json" || { echo "TARGET SURVIVED"; cat "$R/safe.json"; exit 1; }
      rc=0
      out=$({ printf 'fixture-gh\n'; sleep 2; } | script -q /dev/null "$CLI" safe target add fixture-gh gh-login --no-copy 2>&1 | tr -d '\r') || rc=$?
      test "$rc" -ne 0 || { echo "GH REFUSAL EXITED 0: $out"; exit 1; }
      echo "$out" | grep -q "gh login is a copy by definition" || { echo "GH REUSAL MISSING: $out"; exit 1; }
      if grep -q 'gh-login' "$R/safe.json"; then echo "GH TARGET ADDED ANYWAY"; exit 1; fi
      echo R1_LIFECYCLE_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_LIFECYCLE_OK"
      timeout: 120
  - name: R1_helper_answers_for_a_scope_only_host
    description: "the load-bearing property the caller waits on - credential get answers for a host whose only declaration is scope-only, reading the store value, and stays silent for another host"
    command: |
      CLI=$PWD/.venv/bin/ahabase
      test -x "$CLI" || { echo NO_VENV; exit 1; }
      R=$(mktemp -d)
      printf '{"secrets": {"fixture-gh": {"store": "env", "key": "FIXTURE_GH", "purpose": "scope row", "targets": [{"kind": "git-credential", "host": "fixture.github.example", "account": "1148", "copy": false}]}}}' > "$R/safe.json"
      out=$(printf 'protocol=https\nhost=fixture.github.example\n\n' | env AHABASE_SAFE_MANIFEST="$R/safe.json" FIXTURE_GH=fixture-value-0123456789 "$CLI" safe credential get)
      echo "$out" | grep -qx 'username=1148' || { echo "NO USERNAME: $out"; exit 1; }
      echo "$out" | grep -qxF 'password=fixture-value-0123456789' || { echo "NO PASSWORD"; exit 1; }
      out=$(printf 'protocol=https\nhost=other.example\n\n' | env AHABASE_SAFE_MANIFEST="$R/safe.json" FIXTURE_GH=fixture-value-0123456789 "$CLI" safe credential get)
      test -z "$out" || { echo "UNKNOWN HOST ANSWERED: $out"; exit 1; }
      echo R1_HELPER_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_HELPER_OK"
      timeout: 60
  - name: R1_default_target_is_byte_identical
    description: "the same add without the flag prints today's output and writes no copy field - the variant is opt-in per target"
    command: |
      CLI=$PWD/.venv/bin/ahabase
      test -x "$CLI" || { echo NO_VENV; exit 1; }
      R=$(mktemp -d)
      printf '{"secrets": {"fixture-gh": {"store": "env", "key": "FIXTURE_GH", "purpose": "default row", "targets": []}}}' > "$R/safe.json"
      export AHABASE_SAFE_MANIFEST="$R/safe.json"
      out=$({ printf 'fixture-gh\n'; sleep 2; } | script -q /dev/null "$CLI" safe target add fixture-gh git-credential fixture.github.example 1148 2>&1 | tr -d '\r')
      echo "$out" | grep -q "added to fixture-gh - .safe set fixture-gh. writes it" || { echo "DEFAULT OUTPUT CHANGED: $out"; exit 1; }
      if echo "$out" | grep -q "scope only"; then echo "FLAG LEAKED INTO DEFAULT: $out"; exit 1; fi
      if grep -q '"copy"' "$R/safe.json"; then echo "COPY FIELD IN DEFAULT"; cat "$R/safe.json"; exit 1; fi
      echo R1_DEFAULT_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_DEFAULT_OK"
      timeout: 60
  - name: R1_adding_the_other_mode_converts
    description: "one target has one custody mode - adding the spec of an already-declared target with --no-copy converts it under a pty (the review finding's remedy), the manifest holds exactly one git-credential target with copy false, and rotation names it in scope only, never as refreshed"
    command: |
      CLI=$PWD/.venv/bin/ahabase
      test -x "$CLI" || { echo NO_VENV; exit 1; }
      R=$(mktemp -d)
      printf '{"secrets": {"fixture-gh": {"store": "env", "key": "FIXTURE_GH", "purpose": "conversion row", "targets": []}}}' > "$R/safe.json"
      export AHABASE_SAFE_MANIFEST="$R/safe.json" FIXTURE_GH=fixture-value-0123456789
      { printf 'fixture-gh\n'; sleep 2; } | script -q /dev/null "$CLI" safe target add fixture-gh git-credential fixture.github.example 1148 >/dev/null 2>&1
      out=$({ printf 'fixture-gh\n'; sleep 2; } | script -q /dev/null "$CLI" safe target add fixture-gh git-credential fixture.github.example 1148 --no-copy 2>&1 | tr -d '\r')
      echo "$out" | grep -q "converted to scope only" || { echo "NO CONVERSION MARK: $out"; exit 1; }
      echo "$out" | grep -q "stays until removed by hand" || { echo "LEFTOVER COPY SILENT: $out"; exit 1; }
      n=$(grep -c '"kind": "git-credential"' "$R/safe.json" || true)
      test "$n" -eq 1 || { echo "MODES COEXIST: $n"; cat "$R/safe.json"; exit 1; }
      grep -q '"copy": false' "$R/safe.json" || { echo "NO COPY FALSE"; cat "$R/safe.json"; exit 1; }
      out=$({ printf 'fixture-gh\n'; sleep 2; } | script -q /dev/null "$CLI" safe refresh fixture-gh 2>&1 | tr -d '\r')
      echo "$out" | grep -q "scope target git-credential fixture.github.example/1148 - no copy is maintained" || { echo "NO SCOPE LINE: $out"; exit 1; }
      if echo "$out" | grep -q "refreshed target"; then echo "DOUBLE REPORT: $out"; exit 1; fi
      echo R1_CONVERT_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_CONVERT_OK"
      timeout: 120
  - name: R1_pytest_suite_green
    description: "the full suite passes with the variant rows on fictional secrets - the count is a floor, not an exact self-count (later stories only add rows)"
    command: |
      PY=$PWD/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      "$PY" -m pytest -q >/dev/null 2>&1 || { echo SUITE_RED; exit 1; }
      n=$("$PY" -m pytest -q 2>&1 | tail -1)
      c=$(echo "$n" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1)
      test "$c" -ge 192 || { echo "COUNT DROPPED: $c"; exit 1; }
      m=$("$PY" -m pytest -q tests/test_safe.py -k scope_only 2>&1 | tail -1 | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1)
      test "$m" -ge 4 || { echo "VARIANT_ROWS_MISSING: $m"; exit 1; }
      echo R1_PYTEST_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_PYTEST_OK"
      timeout: 300
  - name: R2_tutorial_teaches_the_variant
    description: "docs/safe.md teaches the variant where targets are taught - the flag, the measured add and rotation outputs, the list and remove behavior, and the gh-login refusal"
    command: |
      f=docs/safe.md
      test -f "$f" || { echo NO_TUTORIAL; exit 1; }
      grep -q -- "--no-copy" "$f" || { echo NO_FLAG; exit 1; }
      grep -qF "(scope only) - the credential helper answers for the host; the safe maintains no copy" "$f" || { echo NO_ADD_OUTPUT; exit 1; }
      grep -qF "scope target git-credential git.example.com/42 - no copy is maintained" "$f" || { echo NO_ROTATION_OUTPUT; exit 1; }
      grep -qF "(no copy)" "$f" || { echo NO_LIST_FORM; exit 1; }
      grep -q "it with or without the flag" "$f" || { echo NO_REMOVE_BEHAVIOR; exit 1; }
      grep -q "a .gh-login. target is a copy by definition" "$f" || { echo NO_GH_REFUSAL; exit 1; }
      echo R2_TUTORIAL_OK
    expect:
      exit_code: 0
      stdout_contains: "R2_TUTORIAL_OK"
      timeout: 30
  - name: R2_blueprint_records_the_variant
    description: "the implementation blueprint carries the field, the rotation and health semantics, the removal match, the helper property and the integration row"
    command: |
      f=_grid4d/subepic/ahabase-safe/implementation/implementation-ahabase-safe-blueprint.md
      grep -q '"copy": false' "$f" || { echo NO_FIELD; exit 1; }
      grep -q "no copy is maintained" "$f" || { echo NO_ROTATION_SEMANTICS; exit 1; }
      grep -q "the health check is silent for it" "$f" || { echo NO_HEALTH_SEMANTICS; exit 1; }
      grep -q "matches it with or without the flag" "$f" || { echo NO_REMOVAL_MATCH; exit 1; }
      grep -q "it reads the safe's store value, not a copy" "$f" || { echo NO_HELPER_PROPERTY; exit 1; }
      grep -q "A scope-only .git-credential. target" "$f" || { echo NO_INTEGRATION_ROW; exit 1; }
      grep -q "refused on a .gh-login. target" "$f" || { echo NO_GH_REFUSAL; exit 1; }
      echo R2_BLUEPRINT_OK
    expect:
      exit_code: 0
      stdout_contains: "R2_BLUEPRINT_OK"
      timeout: 30
  - name: R2_tutorial_public_perimeter_clean
    description: "the tutorial names no real identifier - grep over the workspace's personal, epic and registry names comes back empty"
    command: |
      f=docs/safe.md
      if grep -riEq '<work-user>|lubomir|<enterprise-project>|mang|<enterprise-tool>|evolucean|ahabase/|<account-id>' "$f"; then
        grep -riEn '<work-user>|lubomir|<enterprise-project>|mang|<enterprise-tool>|evolucean|ahabase/|<account-id>' "$f"
        echo PERIMETER_LEAK; exit 1
      fi
      echo R2_PERIMETER_OK
    expect:
      exit_code: 0
      stdout_contains: "R2_PERIMETER_OK"
      timeout: 30
  - name: R_team_review_verdict_logged
    description: "review practiced: two APPROVE rows in the story's review record naming the pinned commit, from two different sessions"
    command: |
      n=$(grep -c '^- \*\*APPROVE' _grid4d/story/AHA-0020.md || true)
      test "$n" -ge 2 || { echo "MISSING verdicts: $n"; exit 1; }
      seats=$(grep '^- \*\*APPROVE' _grid4d/story/AHA-0020.md | grep -o 'session [0-9a-f]*' | sort -u | wc -l | tr -d ' ')
      test "$seats" -ge 2 || { echo "SINGLE SEAT: $seats"; exit 1; }
      echo R_TEAM_OK
    expect:
      exit_code: 0
      stdout_contains: "R_TEAM_OK"
      timeout: 30
  - name: R_docs_surfaces_reflected
    description: "the variant is in the blueprint's structure and command surface, and the code docstrings carry the semantics"
    command: |
      grep -q "scope-only variant is the spec field" _grid4d/subepic/ahabase-safe/implementation/implementation-ahabase-safe-blueprint.md || { echo NO_STRUCTURE; exit 1; }
      grep -q -- "--no-copy: helper scope only, no copy" _grid4d/subepic/ahabase-safe/implementation/implementation-ahabase-safe-blueprint.md || { echo NO_COMMAND_SURFACE; exit 1; }
      grep -q "no copy to write" src/ahabase/safe.py || { echo NO_SKIP_COMMENT; exit 1; }
      grep -q "the custody mode never blocks removal" src/ahabase/safe.py || { echo NO_SAME_TARGET_DOC; exit 1; }
      grep -q "scope-only: no copy exists to be missing" src/ahabase/safe.py || { echo NO_HEALTH_COMMENT; exit 1; }
      grep -q -- "--no-copy is a git-credential option" src/ahabase/cli_safe.py || { echo NO_REFUSAL_TEXT; exit 1; }
      echo R_DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "R_DOCS_OK"
      timeout: 30
  - name: R_issues_nothing_silent
    description: "the coupling this story decouples is named in the story Notes in plain text (its issue file lives in the evolucean epic), so nothing about it is silent here either"
    command: |
      grep -q "safe-git-helper-target-couples-scope-and-custody" _grid4d/story/AHA-0020.md || { echo COUPLING_SILENT; exit 1; }
      grep -q "Scope fences" _grid4d/story/AHA-0020.md || { echo NO_SCOPE_FENCES; exit 1; }
      echo R_ISSUES_OK
    expect:
      exit_code: 0
      stdout_contains: "R_ISSUES_OK"
      timeout: 30
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_scope_only_variant_cli_lifecycle | ✅ | 2026-10-31 |
| R1_helper_answers_for_a_scope_only_host | ✅ | 2026-10-31 |
| R1_default_target_is_byte_identical | ✅ | 2026-10-31 |
| R1_pytest_suite_green | ✅ | 2026-10-31 |
| R2_tutorial_teaches_the_variant | ✅ | 2026-10-31 |
| R2_blueprint_records_the_variant | ✅ | 2026-10-31 |
| R2_tutorial_public_perimeter_clean | ✅ | 2026-10-31 |
| R_team_review_verdict_logged | ✅ | 2026-10-31 |
| R_docs_surfaces_reflected | ✅ | 2026-10-31 |
| R_issues_nothing_silent | ✅ | 2026-10-31 |
| R1_adding_the_other_mode_converts | ✅ | 2026-10-31 |

Run at 8e3f0e0188cafdf38351f1428126e8af6345fba9
## Related

- [AHA-0020](AHA-0020) - Parent story

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
