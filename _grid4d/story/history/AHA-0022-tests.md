# AHA-0022-tests

> Test definition for AHA-0022 with one test per requirement.

## Design

Test requirements for AHA-0022. One test per requirement.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_per_account_target
    description: "the distinct kind gh-login-account HOSTNAME ACCOUNT parses, labels and runs gh with its own GH_CONFIG_DIR; gh-login (the default login) is unchanged; an old reader refuses the unknown kind; gh-config-dir is the one path"
    command: |
      test -x .venv/bin/python || { echo NO_VENV; exit 1; }
      .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_safe.py -k "target_kinds_parse_and_label or per_account_dir or gh_login_refreshes or gh_login_verifies or account_login_is_a_distinct_kind or gh_config_dir_is_the_one_path"
    expect:
      exit_code: 0
  - name: R2_no_plaintext_token
    description: "a gh that writes the token into its config files - as oauth_token or under a renamed field - makes refresh fail, names gh exit code, leaves no token file; a keyring write passes"
    command: |
      .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_safe.py -k "refuses_a_plaintext_token or refuses_the_value_under_any_field"
    expect:
      exit_code: 0
  - name: R3_location_and_mode
    description: "the directory is under the workspace _config/ (AHABASE_HOME), owner-only 0700; whole safe suite green"
    command: |
      .venv/bin/python -m pytest -q -p no:cacheprovider tests/
    expect:
      exit_code: 0
  - name: R4_measured_on_work
    description: "both accounts registered and refreshed; GH_CONFIG_DIR=<dir> gh api user names the right login for each (the owner's measurement, recorded in the story)"
    command: |
      # cross-order (home-5235 F5): each login re-checked after the other was written
      for a in <user> <corporate-account> <user>; do
        d=$(.venv/bin/ahabase safe gh-config-dir "$a") || exit 1
        test -d "$d" || { echo "NO DIR $a"; exit 1; }
        got=$(env -u GH_TOKEN -u GITHUB_TOKEN GH_CONFIG_DIR="$d" gh api user --jq .login) || exit 1
        test "$got" = "$a" || { echo "WRONG LOGIN $a: $got"; exit 1; }
        grep -q "oauth_token" "$d"/*.yml 2>/dev/null && { echo "PLAINTEXT $a"; exit 1; }
      done
      echo R4_OK
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_per_account_target | ✅ | 2026-11-06 |
| R2_no_plaintext_token | ✅ | 2026-11-06 |
| R3_location_and_mode | ✅ | 2026-11-06 |
| R4_measured_on_work | ✅ | 2026-11-06 |

Run at 132681157e076ac1dba2e8eb5ce61d64ae59d107
## Related

- [AHA-0022](AHA-0022) - Parent story

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
