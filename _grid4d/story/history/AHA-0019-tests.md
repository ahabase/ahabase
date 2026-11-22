# AHA-0019-tests

> Test definition for AHA-0019 with one test per requirement.

## Design

Test requirements for AHA-0019. One test per requirement. The rows run in this worktree against its own venv (``.venv`` created by the story) and the ``ahabase`` console script it installs. The R1 rows build a fixture manifest (env store, the fictional host ``fixture.github.example``) and drive the helper cross-process, the way git drives it; the R2 row performs the live authenticated ``push --dry-run`` against the private origin with the helper isolated by the command-line reset (``-c "credential.helper="``) and asserts on the GIT_TRACE record that no other credential helper ran; the R3 rows hold the tutorial to its rehearsal contract (the ``--add`` wiring pair, the refusal literals, the public-perimeter grep over every identifier the workspace's registry carries). R_team holds the review verdict record; R_docs and R_issues hold the documentation and story-notes assertions.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_helper_protocol_answers_from_the_fixture_store
    description: "credential get answers username/password for the target's host, nothing for another host, and store/erase fail soft with the owner's-path notice while the manifest stays unchanged"
    command: |
      CLI=$PWD/.venv/bin/ahabase
      test -x "$CLI" || { echo NO_VENV; exit 1; }
      R=$(mktemp -d)
      printf '{"secrets": {"fixture-gh": {"store": "env", "key": "FIXTURE_GH", "purpose": "helper row", "targets": [{"kind": "git-credential", "host": "fixture.github.example", "account": "1148"}]}}}' > "$R/safe.json"
      export AHABASE_SAFE_MANIFEST="$R/safe.json" FIXTURE_GH=fixture-value-0123456789
      out=$(printf 'protocol=https\nhost=fixture.github.example\n\n' | "$CLI" safe credential get)
      echo "$out" | grep -qx 'username=1148' || { echo "NO USERNAME: $out"; exit 1; }
      echo "$out" | grep -qxF 'password=fixture-value-0123456789' || { echo "NO PASSWORD"; exit 1; }
      out=$(printf 'protocol=https\nhost=other.example\n\n' | "$CLI" safe credential get)
      test -z "$out" || { echo "UNKNOWN HOST ANSWERED: $out"; exit 1; }
      before=$(md5 -q "$R/safe.json")
      for verb in store erase; do
        err=$(printf 'protocol=https\nhost=fixture.github.example\nusername=1148\npassword=x\n\n' | "$CLI" safe credential "$verb" 2>&1 >/dev/null)
        echo "$err" | grep -q "the safe stores nothing from git" || { echo "NO NOTICE ($verb): $err"; exit 1; }
      done
      test "$(md5 -q "$R/safe.json")" = "$before" || { echo "MANIFEST CHANGED"; exit 1; }
      echo R1_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_OK"
      timeout: 60
  - name: R1_missing_value_fails_soft_with_the_remedy
    description: "a manifest entry whose store value is gone answers nothing on stdout and names ahabase safe set on stderr, never the value"
    command: |
      CLI=$PWD/.venv/bin/ahabase
      test -x "$CLI" || { echo NO_VENV; exit 1; }
      R=$(mktemp -d)
      printf '{"secrets": {"fixture-gh": {"store": "env", "key": "FIXTURE_GH", "targets": [{"kind": "git-credential", "host": "fixture.github.example", "account": "1148"}]}}}' > "$R/safe.json"
      out=$(printf 'protocol=https\nhost=fixture.github.example\n\n' | env -u FIXTURE_GH AHABASE_SAFE_MANIFEST="$R/safe.json" "$CLI" safe credential get 2>"$R/err"); rc=$?
      test $rc -eq 0 || { echo "EXIT $rc"; exit 1; }
      test -z "$out" || { echo "STDOUT NOT EMPTY: $out"; exit 1; }
      grep -q "not in its store 'env'" "$R/err" || { echo "BAD NOTICE"; cat "$R/err"; exit 1; }
      grep -q "ahabase safe set fixture-gh" "$R/err" || { echo "NO REMEDY"; exit 1; }
      echo R1_SOFT_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_SOFT_OK"
      timeout: 60
  - name: R1_git_credential_fill_interop
    command: |
      CLI=$PWD/.venv/bin/ahabase
      test -x "$CLI" || { echo NO_VENV; exit 1; }
      R=$(mktemp -d)
      printf '{"secrets": {"fixture-gh": {"store": "env", "key": "FIXTURE_GH", "targets": [{"kind": "git-credential", "host": "fixture.github.example", "account": "1148"}]}}}' > "$R/safe.json"
      out=$(printf 'protocol=https\nhost=fixture.github.example\n\n' | env AHABASE_SAFE_MANIFEST="$R/safe.json" FIXTURE_GH=fixture-value-0123456789 git -c "credential.helper=" -c "credential.helper=!$CLI safe credential" credential fill 2>/dev/null)
      echo "$out" | grep -qx 'username=1148' || { echo "NO USERNAME: $out"; exit 1; }
      echo "$out" | grep -qxF 'password=fixture-value-0123456789' || { echo "NO PASSWORD: $out"; exit 1; }
      echo R1_FILL_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_FILL_OK"
      timeout: 60
  - name: R1_pytest_suite_green
    description: "the full suite passes, including the 12 helper tests on fictional secrets"
    command: |
      PY=$PWD/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      "$PY" -m pytest -q 2>&1 | tail -3
      echo "$?" | grep -qx 0 || true
      "$PY" -m pytest -q >/dev/null 2>&1 || { echo SUITE_RED; exit 1; }
      "$PY" -m pytest -q tests/test_safe_git_helper.py 2>&1 | grep -E "12 passed" || { echo HELPER_TESTS_CHANGED; exit 1; }
      echo R1_PYTEST_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_PYTEST_OK"
      timeout: 300
  - name: R2_live_push_dry_run_with_the_safe_as_only_helper
    description: "a real authenticated push --dry-run against the private origin succeeds with the safe's helper as the only github.com credential source - the GIT_TRACE record names no other helper and carries the fail-soft store notice"
    command: |
      CLI=$PWD/.venv/bin/ahabase
      test -x "$CLI" || { echo NO_VENV; exit 1; }
      out=$(GIT_TRACE=1 git -c "credential.helper=" -c "credential.https://github.com.helper=!$CLI safe credential" push --dry-run origin HEAD 2>&1); rc=$?
      test $rc -eq 0 || { echo "PUSH FAILED: $out"; exit 1; }
      echo "$out" | grep -q "safe credential get" || { echo "SAFE NOT CONSULTED"; exit 1; }
      if echo "$out" | grep -q osxkeychain; then echo "OSXKEYCHAIN RAN"; exit 1; fi
      if echo "$out" | grep -q "gh auth git-credential"; then echo "GH HELPER RAN"; exit 1; fi
      echo "$out" | grep -q "the safe stores nothing from git" || { echo "NO STORE NOTICE"; exit 1; }
      echo "$out" | grep -qE "up-to-date|->" || { echo "NO PUSH RESULT"; exit 1; }
      echo R2_OK
    expect:
      exit_code: 0
      stdout_contains: "R2_OK"
      timeout: 180
  - name: R3_tutorial_carries_the_measured_wiring_and_texts
    description: "docs/safe.md holds the --add wiring pair, the reset explanation, and the refusal/output literals the rehearsal measured"
    command: |
      f=docs/safe.md
      test -f "$f" || { echo NO_TUTORIAL; exit 1; }
      grep -qF 'git config --global credential.https://git.example.com.helper ""' "$f" || { echo NO_EMPTY_LINE; exit 1; }
      grep -qF 'git config --global --add credential.https://git.example.com.helper "!ahabase safe credential"' "$f" || { echo NO_ADD_LINE; exit 1; }
      grep -q "a plain set would" "$f" || { echo NO_REPLACE_WARNING; exit 1; }
      grep -qF "the safe stores nothing from git" "$f" || { echo NO_STORE_NOTICE; exit 1; }
      grep -qF "is not a bound consumer of" "$f" || { echo NO_UNBOUND_TEXT; exit 1; }
      grep -qF "changed since it was bound" "$f" || { echo NO_CHANGED_TEXT; exit 1; }
      grep -qF "valid while the file is unchanged" "$f" || { echo NO_BIND_OUTPUT; exit 1; }
      grep -q "The owner's walkthrough" "$f" || { echo NO_OWNER_SECTION; exit 1; }
      grep -q "The user's walkthrough" "$f" || { echo NO_USER_SECTION; exit 1; }
      grep -q -- "--reveal" "$f" || { echo NO_REVEAL; exit 1; }
      echo R3_DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "R3_DOCS_OK"
      timeout: 30
  - name: R3_tutorial_public_perimeter_clean
    description: "the tutorial names no real identifier - grep over the workspace's personal, epic and registry names comes back empty"
    command: |
      f=docs/safe.md
      if grep -riEq '<work-user>|lubomir|<enterprise-project>|mang|<enterprise-tool>|evolucean|ahabase/|<account-id>' "$f"; then
        grep -riEn '<work-user>|lubomir|<enterprise-project>|mang|<enterprise-tool>|evolucean|ahabase/|<account-id>' "$f"
        echo PERIMETER_LEAK; exit 1
      fi
      echo R3_PERIMETER_OK
    expect:
      exit_code: 0
      stdout_contains: "R3_PERIMETER_OK"
      timeout: 30
  - name: R3_rehearsal_and_wiring_recorded_in_the_story
    description: "the story Notes carry the live R2 run record, the --add wiring instructions with the replacement warning, and the private-repo probe lesson"
    command: |
      f=_grid4d/story/AHA-0019.md
      grep -q "push --dry-run origin" "$f" || { echo NO_LIVE_RUN; exit 1; }
      grep -qF 'git config --global --add credential.https://github.com.helper' "$f" || { echo NO_WIRING; exit 1; }
      grep -q "replace the empty entry" "$f" || { echo NO_WARNING; exit 1; }
      grep -q "info/refs" "$f" || { echo NO_PROBE_LESSON; exit 1; }
      grep -q "came back clean" "$f" || { echo NO_PERIMETER_RECORD; exit 1; }
      echo R3_NOTES_OK
    expect:
      exit_code: 0
      stdout_contains: "R3_NOTES_OK"
      timeout: 30
  - name: R_team_review_verdict_logged
    description: "review practiced: two APPROVE rows in the story's review record naming the pinned commit, from two different sessions"
    command: |
      n=$(grep -c '^- \*\*APPROVE' _grid4d/story/AHA-0019.md || true)
      test "$n" -ge 2 || { echo "MISSING verdicts: $n"; exit 1; }
      seats=$(grep '^- \*\*APPROVE' _grid4d/story/AHA-0019.md | grep -o 'session [0-9a-f]*' | sort -u | wc -l | tr -d ' ')
      test "$seats" -ge 2 || { echo "SINGLE SEAT: $seats"; exit 1; }
      echo R_TEAM_OK
    expect:
      exit_code: 0
      stdout_contains: "R_TEAM_OK"
      timeout: 30
  - name: R_docs_surfaces_reflected
    description: "the new surface is in the safe blueprint (structure, template, example, consumer row), the integration blueprint's amendment, the CLI template and the README"
    command: |
      grep -q "parse_credential_request" _grid4d/subepic/ahabase-safe/implementation/implementation-ahabase-safe-blueprint.md || { echo NO_STRUCTURE; exit 1; }
      grep -q "safe credential VERB" _grid4d/subepic/ahabase-safe/implementation/implementation-ahabase-safe-blueprint.md || { echo NO_TEMPLATE; exit 1; }
      grep -q "credential get" _grid4d/subepic/ahabase-safe/implementation/implementation-ahabase-safe-blueprint.md || { echo NO_EXAMPLE; exit 1; }
      grep -q "Amended (AHA-0019" _grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md || { echo NO_AMENDMENT; exit 1; }
      grep -q "docs/safe.md" README.md || { echo NO_README; exit 1; }
      grep -q "Capability: secrets-door\|credential" src/ahabase/cli_safe.py || { echo NO_DOCSTRING; exit 1; }
      echo R_DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "R_DOCS_OK"
      timeout: 30
  - name: R_issues_nothing_silent
    description: "the two findings of the story - the wiring replacement trap and the contaminated visibility probe - are recorded as fixed, not silent"
    command: |
      grep -q "a plain set would" docs/safe.md || { echo WIRING_SILENT; exit 1; }
      grep -q "authenticates silently through the keychain item" _grid4d/story/AHA-0019.md || { echo PROBE_SILENT; exit 1; }
      echo R_ISSUES_OK
    expect:
      exit_code: 0
      stdout_contains: "R_ISSUES_OK"
      timeout: 30
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_helper_protocol_answers_from_the_fixture_store | ✅ | 2026-10-31 |
| R1_missing_value_fails_soft_with_the_remedy | ✅ | 2026-10-31 |
| R1_git_credential_fill_interop | ✅ | 2026-10-31 |
| R1_pytest_suite_green | ✅ | 2026-10-31 |
| R2_live_push_dry_run_with_the_safe_as_only_helper | ✅ | 2026-10-31 |
| R3_tutorial_carries_the_measured_wiring_and_texts | ✅ | 2026-10-31 |
| R3_tutorial_public_perimeter_clean | ✅ | 2026-10-31 |
| R3_rehearsal_and_wiring_recorded_in_the_story | ✅ | 2026-10-31 |
| R_team_review_verdict_logged | ✅ | 2026-10-31 |
| R_docs_surfaces_reflected | ✅ | 2026-10-31 |
| R_issues_nothing_silent | ✅ | 2026-10-31 |

Run at 958028145ffeed5c0078dea1f356adf093fe6974
## Related

- [AHA-0019](AHA-0019) - Parent story
