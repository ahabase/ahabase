# AHA-0001-tests

> Test definition for AHA-0001 with one test per requirement.

## Design

The package's own pytest suite carries the contract (fictional plugins through a seam for the entry points; a parse of every module for the dependency rule); the rows below run it in the story's virtual environment and check the documents and the guards. Written by hand: `story create` minted no tests document here (the root tests pattern is not inherited yet - the parallel EVOLUCEAN-DISTRIBUTION story).

## Definition

```yaml
tests:
  - name: R1_architecture_blueprint
    description: the architecture blueprint exists with its sections and validates
    command: |
      f=_grid4d/implementation/implementation-ahabase-architecture-blueprint.md
      for s in "## Layers" "## Rules" "## Order of the next stories" "## Template" "## Example"; do grep -q "^$s" "$f" || { echo "missing $s"; exit 1; }; done
      grep -q "Surface rule" "$f" && grep -q "Dependency direction" "$f"
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$f"
    expect:
      exit_code: 0
  - name: R2_package_skeleton
    description: a fresh venv installs the package; ahabase --version and doctor exit 0
    command: |
      base=$(mktemp -d) && [ -d "${base:?}" ] || exit 1
      python3 -m venv "$base/venv" && "$base/venv/bin/pip" install -q -e . || { rm -rf "$base"; exit 1; }
      "$base/venv/bin/ahabase" --version && "$base/venv/bin/ahabase" doctor; rc=$?
      rm -rf "$base"
      exit $rc
    expect:
      exit_code: 0
      timeout: 600
  - name: R3_plugin_contract
    description: fictional plugins - command and check added; failing, incompatible, colliding and unimportable plugins reported while the CLI works; no import of the core
    command: |
      .venv/bin/python -m pytest -q tests
    expect:
      exit_code: 0
      timeout: 300
  - name: R4_repository_guards
    description: the dbt pre-push hook is gone; this tests document exists; the story's commits pass the containment check
    command: |
      hooks="$(cd "$(git rev-parse --git-common-dir)" && pwd)/hooks"
      ! grep -q "dbt" "$hooks/pre-push" 2>/dev/null
      test -f _grid4d/story/AHA-0001-tests.md
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage containment check --range origin/main..HEAD --repo .
    expect:
      exit_code: 0
      timeout: 120
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_architecture_blueprint | ✅ | 2026-10-24 |
| R2_package_skeleton | ✅ | 2026-10-24 |
| R3_plugin_contract | ✅ | 2026-10-24 |
| R4_repository_guards | ✅ | 2026-10-24 |

## Related

- [AHA-0001](AHA-0001) - Parent story
