# AHA-0034-tests

> Test definition for AHA-0034 with one test per requirement.

## Design

One row per requirement. Repository-state rows call gh against the live ahabase org (network rows; red until the flip lands); tree rows are self-contained greps runnable from a copy of the worktree. Account-name literals never appear in any row: the R2 row measures the committed scrub report (counts per class) and, when the uncommitted scrub config is present, re-runs the export gate over the story tree itself (the gate fails closed on any remaining class member - a config-pattern zero cannot green it; a public clone without the config measures the report legs only). Read points: the R5 branch list is read at the handover, before seats re-join - the fresh collab branch born on the public repository afterwards is the expected continuity, not a violation; a gh failure fails the row.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_canonical_public_linux_ci
    description: the canonical repository is public and macOS runners appear only inside the conditional tags/dispatch matrix arm (the push path is ubuntu-only)
    command: test "$(gh repo view ahabase/ahabase --json visibility --jq .visibility)" = "public" && grep -q "ubuntu-latest" .github/workflows/tests.yml && n=$(grep -c "macos-latest" .github/workflows/tests.yml || true) && g=$(grep "macos-latest" .github/workflows/tests.yml | grep "workflow_dispatch" | grep -c "refs/tags/" || true) && test "$n" -ge 1 && test "$n" -eq "$g"
    expect:
      exit_code: 0
  - name: R2_scrub_report_zero_matches
    description: every scrub class in the committed report shows zero matches under the one declared case-insensitive method, and the export gate re-runs clean over the story tree when the uncommitted config is present
    command: 'for c in personal-account corporate-account enterprise-host internal-mirror secret-material; do grep -q "^- $c: 0 match" _grid4d/story/AHA-0034-scrub-report.md || exit 1; done; cfg="${AHA_WORKSPACE:-$HOME/ahabase}/_config/ahabase-scrub-patterns.txt"; if [ -f "$cfg" ]; then d=$(mktemp -d) && scripts/export-public-seed.sh "$PWD" "$d/seed" >/dev/null && rm -rf "$d"; fi'
    expect:
      exit_code: 0
  - name: R3_flip_and_renames
    description: the private archive keeps the releases and the canonical repository has fresh-root history
    command: test "$(gh repo view ahabase/ahabase-private --json visibility --jq .visibility)" = "private" && gh release list -R ahabase/ahabase-private --limit 200 | grep -q v0.0033 && test "$(gh api 'repos/ahabase/ahabase/commits?per_page=100' --jq '.[-1].commit.committer.date' | cut -c1-10)" \> 2026-11-21
    expect:
      exit_code: 0
  - name: R4_workspace_on_public_history
    description: the canonical repository holds the fresh-root history (fewer than 100 commits) and its public ledger holds this story; the local rewiring of the workspace epic tree is recorded measured in the story Notes at handover
    command: test "$(gh api 'repos/ahabase/ahabase/commits?per_page=100' --jq 'length')" -lt 100 && gh api repos/ahabase/ahabase/contents/_grid4d/story --jq '.[].name' | grep -q AHA-0034.md
    expect:
      exit_code: 0
  - name: R5_continuity_guarantees
    description: the story states the continuity non-goals and the public repository carries no collab branch - read at the handover, before seats re-join (the fresh collab branch born on the public repository afterwards is the expected continuity, not a violation); a gh failure fails the row
    command: grep -q "append-only" _grid4d/story/AHA-0034.md && grep -q "frozen consumer" _grid4d/story/AHA-0034.md && branches=$(gh api repos/ahabase/ahabase/branches --jq '.[].name') && ! printf '%s\n' "$branches" | grep -qx collab
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
