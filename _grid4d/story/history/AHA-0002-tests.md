# AHA-0002-tests

> Test definition for AHA-0002 with one test per requirement.

## Design

The package's pytest suite carries the contract on fictional secrets: the stores' shared contract, the manifest and references, the CLI commands, and the isolation (temporary workspace, manifest and HOME; a guard keyring backend that fails any test reaching the real OS store). The rows run it in the story's virtual environment and check the blueprint. Nothing of the instance is read or changed.

## Definition

```yaml
tests:
  - name: R1_safe_blueprint
    description: the safe blueprint exists with its sections and validates
    command: |
      f=_grid4d/implementation/implementation-ahabase-safe-blueprint.md
      for s in "## Rules" "## Known limits" "## Later steps" "## Template" "## Example"; do grep -q "^$s" "$f" || { echo "missing $s"; exit 1; }; done
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$f"
    expect:
      exit_code: 0
  - name: R2_stores
    description: memory and keyring stores pass the same contract (keyring against a fake backend); env store is read-only
    command: |
      .venv/bin/python -m pytest -q tests/test_safe.py -k "store_contract or keyring_store or env_store"
    expect:
      exit_code: 0
      timeout: 300
  - name: R3_references_manifest
    description: the manifest holds no value; references resolve; plain values pass through; unknown names error without a value; rotation recorded
    command: |
      .venv/bin/python -m pytest -q tests/test_safe.py -k "manifest or rotation or health"
    expect:
      exit_code: 0
      timeout: 300
  - name: R4_cli_commands
    description: set from stdin, list without values, get refuses without --reveal, run gives only the child the value, doctor reports a missing secret; no value argument
    command: |
      .venv/bin/python -m pytest -q tests/test_safe.py -k "cli or argument or reserved"
    expect:
      exit_code: 0
      timeout: 300
  - name: R5_instance_untouched
    description: the whole suite passes with the guard keyring installed (any real OS store call fails a test); the instance has no safe manifest created by this story
    command: |
      .venv/bin/python -m pytest -q
      grep -q "GuardKeyring" tests/conftest.py
      test ! -e ~/ahabase/_config/safe.json
    expect:
      exit_code: 0
      timeout: 300
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_safe_blueprint | ✅ | 2026-10-24 |
| R2_stores | ✅ | 2026-10-24 |
| R3_references_manifest | ✅ | 2026-10-24 |
| R4_cli_commands | ✅ | 2026-10-24 |
| R5_instance_untouched | ✅ | 2026-10-24 |

## Related

- [AHA-0002](AHA-0002) - Parent story
