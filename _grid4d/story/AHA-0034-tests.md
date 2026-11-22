# AHA-0034-tests

> Test definition for AHA-0034 with one test per requirement.

## Design

One row per requirement. Repository-state rows call gh against the live ahabase org (network rows; red until the flip lands); tree rows are self-contained greps runnable from a copy of the worktree. Account-name literals never appear in any row: the R2 row measures the committed scrub report (counts per class), not the literals themselves.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_canonical_public_linux_ci
    description: the canonical repository is public and its CI workflow is Linux-only for the push path
    command: test "$(gh repo view ahabase/ahabase --json visibility --jq .visibility)" = "public" && grep -q "ubuntu-latest" .github/workflows/tests.yml && ! grep -q "macos-latest" .github/workflows/tests.yml
    expect:
      exit_code: 0
  - name: R2_scrub_report_zero_matches
    description: every scrub class in the committed report shows zero matches against the seeded tree
    command: 'for c in personal-account corporate-account enterprise-host internal-mirror secret-material; do grep -q "^- $c: 0 match" _grid4d/story/AHA-0034-scrub-report.md || exit 1; done'
    expect:
      exit_code: 0
  - name: R3_flip_and_renames
    description: the private archive keeps the releases and the canonical repository has fresh-root history
    command: test "$(gh repo view ahabase/ahabase-private --json visibility --jq .visibility)" = "private" && gh release list -R ahabase/ahabase-private --limit 200 | grep -q v0.0033 && test "$(gh api 'repos/ahabase/ahabase/commits?per_page=100' --jq '.[-1].commit.committer.date' | cut -c1-10)" \> 2026-11-21
    expect:
      exit_code: 0
  - name: R4_workspace_on_public_history
    description: the workspace epic tree sits on the public fresh history and the public ledger holds this story
    command: test "$(git -C /Users/<user>/ahabase/ahabase log --oneline | wc -l | tr -d ' ')" -lt 100 && gh api repos/ahabase/ahabase/contents/_grid4d/story --jq '.[].name' | grep -q AHA-0034.md
    expect:
      exit_code: 0
  - name: R5_continuity_guarantees
    description: the story states the continuity non-goals and the public repository carries no collab branch at handover
    command: grep -q "append-only" _grid4d/story/AHA-0034.md && grep -q "frozen consumer" _grid4d/story/AHA-0034.md && ! gh api repos/ahabase/ahabase/branches --jq '.[].name' | grep -qx collab
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_canonical_public_linux_ci | ⚪ | |
| R2_scrub_report_zero_matches | ⚪ | |
| R3_flip_and_renames | ⚪ | |
| R4_workspace_on_public_history | ⚪ | |
| R5_continuity_guarantees | ⚪ | |

## Related

- [AHA-0034](AHA-0034) - Parent story

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
