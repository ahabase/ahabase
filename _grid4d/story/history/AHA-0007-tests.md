# AHA-0007-tests

> Test definition for AHA-0007 with one test per requirement.

## Design

The package's pytest suite carries the contract on fictional values: the existing tests adapted, a new file for the hardening. The rows run the relevant tests by name in the story's virtual environment, and check the documents. Every guard stands alone with an explicit exit. Nothing of the instance is read or changed.

## Definition

```yaml
tests:
  - name: R1_threat_model
    description: T12 with seven controls, rule 5, the extended binding rules, development versus operation; the identity names the equal requirement
    command: |
      f=_grid4d/implementation/implementation-ahabase-safe-threat-model-blueprint.md
      if ! grep -q "^### T12 Lockout by the safe's own controls" "$f"; then echo "no T12"; exit 1; fi
      n=$(sed -n '/^### T12/,/^### Repudiation/p' "$f" | grep -cE "^  [1-7]\. \*\*")
      if [ "$n" -ne 7 ]; then echo "T12 has $n controls, expected 7"; exit 1; fi
      for s in "Security, simplicity and reliability are equal requirements" "Development versus operation" "Arguments that redirect a consumer are refused" "Installed commands only" "stable across upgrades" "certificate bundles"; do
        if ! grep -qF "$s" "$f"; then echo "missing: $s"; exit 1; fi
      done
      if ! grep -q "security, simplicity and reliability of use are equal requirements" _grid4d/story/AHABASE.md; then echo "identity lacks the ruling"; exit 1; fi
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$f"
    expect:
      exit_code: 0
  - name: R2_consumer_binding
    description: binding rules enforced before any value is read; refusals name the way through
    command: |
      .venv/bin/python -m pytest -q tests/test_safe_hardening.py -k "bound or bind or path or upgrade or prefix or unbind"
    expect:
      exit_code: 0
      timeout: 300
  - name: R3_environment_shell_free
    description: no other exported value in the child, base and kept variables present; executed as a list
    command: |
      .venv/bin/python -m pytest -q tests/test_safe_hardening.py -k "base_and_no_other or shell_free"
    expect:
      exit_code: 0
      timeout: 300
  - name: R4_owner_commands
    description: reveal and compare need the owner; bursts of comparisons refused
    command: |
      .venv/bin/python -m pytest -q tests/test_safe_hardening.py -k "reveal or compare"
    expect:
      exit_code: 0
      timeout: 300
  - name: R5_manifest_and_overrides
    description: no manifest in a git tree, overrides need the owner, doctor reports; the whole suite passes isolated through HOME
    command: |
      .venv/bin/python -m pytest -q tests/test_safe_hardening.py -k "override or git_working_tree or disappeared"
      if grep -qE "setenv\(\"AHABASE_(HOME|SAFE_MANIFEST)\"" tests/conftest.py; then echo "the suite still isolates through the override variables"; exit 1; fi
      .venv/bin/python -m pytest -q
    expect:
      exit_code: 0
      timeout: 300
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_threat_model | ✅ | 2026-10-25 |
| R2_consumer_binding | ✅ | 2026-10-25 |
| R3_environment_shell_free | ✅ | 2026-10-25 |
| R4_owner_commands | ✅ | 2026-10-25 |
| R5_manifest_and_overrides | ✅ | 2026-10-25 |

## Related

- [AHA-0007](AHA-0007) - Parent story
