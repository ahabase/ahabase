# AHA-0010-tests

> Test definition for AHA-0010 with one test per requirement.

## Design

R1 reads the identity document and compares its fields with the main branch: the only new field is `Infrastructure`. R2 runs the package's own lineage check. The process rows read the story document. Every guard stands alone with an explicit exit.

## Definition

```yaml
tests:
  - name: R1_identity_states_infrastructure
    description: AHABASE.md states Infrastructure true and nothing else changed among its fields
    command: |
      grep -qx '\*\*Infrastructure:\*\* true' _grid4d/story/AHABASE.md || { echo "no Infrastructure line"; exit 1; }
      T=$(mktemp -d)
      git show origin/main:_grid4d/story/AHABASE.md | grep -E '^\*\*[A-Za-z]+:\*\*' > "$T/before"
      grep -E '^\*\*[A-Za-z]+:\*\*' _grid4d/story/AHABASE.md > "$T/after"
      added=$(diff "$T/before" "$T/after" | grep -cE '^[<>]'); rm -rf "$T"
      [ "$added" = 1 ] || { echo "fields changed beyond Infrastructure: $added"; exit 1; }
      echo INFRA_OK
    expect:
      exit_code: 0
      stdout_contains: "INFRA_OK"

  - name: R2_package_verifies
    description: ahabase verify passes on the tree
    command: |
      PYTHONPATH=src ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/python -c "import sys; from ahabase.cli import main; sys.argv = ['ahabase', 'verify', '--root', '.']; main()" > /dev/null && echo VERIFY_OK
    expect:
      exit_code: 0
      stdout_contains: "VERIFY_OK"

  - name: R_team_verdict
    description: reviewer-haiku verdict with a full commit
    command: |
      sed -n '/^## Review/,/^## /p' _grid4d/story/AHA-0010.md | grep -E 'reviewer-haiku.*[0-9a-f]{40}' | grep -qv awaiting && echo TEAM_OK
    expect:
      exit_code: 0
      stdout_contains: "TEAM_OK"

  - name: R_docs_order
    description: the order of landing is recorded
    command: |
      grep -q 'Order of landing' _grid4d/story/AHA-0010.md && echo DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "DOCS_OK"

  - name: R_issues_section
    description: Issues section filled
    command: |
      sed -n '/^## Issues/,/^## /p' _grid4d/story/AHA-0010.md | grep -q '^- ' && echo ISSUES_OK
    expect:
      exit_code: 0
      stdout_contains: "ISSUES_OK"
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_identity_states_infrastructure | ✅ | 2026-10-26 |
| R2_package_verifies | ✅ | 2026-10-26 |
| R_team_verdict | ✅ | 2026-10-26 |
| R_docs_order | ✅ | 2026-10-26 |
| R_issues_section | ✅ | 2026-10-26 |
