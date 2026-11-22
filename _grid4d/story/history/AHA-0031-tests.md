# AHA-0031-tests

> Test definition for AHA-0031 with one test per requirement.

## Design

Test requirements for AHA-0031. One test per requirement, each a self-contained scenario script under `playground/tests/` (the leg's shape: mktemp sandbox, fail-closed assertions, exit 0 = green). R4's held-seam arm runs against the live playground (`~/ahabase-playground`, bootstrapped when absent) and snapshots the real workspace's `_data/` and `_config/` around a full story cycle.

## Definition

```yaml
tests:
  - name: R1_the_workspace_bootstrap_net
    description: the bootstrap produces the witnessed net - CLAUDE.md declaring ahabase the primary tool, the wheel-served venv (pip show), the entrypoint pin with the get_workspace_dir() probe, the settings.json allowlist, no seeded memory, the scenarios document, both fixtures, and the fail-closed refusal on an existing workspace
    command: sh playground/tests/r1-net.sh
    expect:
      exit_code: 0
  - name: R2_the_plug_and_play_seam
    description: the empty scratch repo and the non-empty messy repo both register through init and validate green; the messy story lands on the declared branch measured three ways with the tag edge; the Branch-less control lands on main (the red arm)
    command: sh playground/tests/r2-seam.sh
    expect:
      exit_code: 0
  - name: R3_the_request_archetypes
    description: five archetypes through story create/status/complete alone - docs-only, code+tests, the archive window (oldest archived, newest stays), the real conflicted merge (abort named, recovery named, one merge commit and the one pre-merge tag after the re-run), and the three refusals (each names its reason and writes nothing)
    command: sh playground/tests/r3-archetypes.sh
    expect:
      exit_code: 0
  - name: R4_isolation_both_arms
    description: the load-bearing arm (sandboxed HOME, unset env - the writing probe lands under $HOME/ahabase, the forgotten-pin target witnessed) and the held-seam arm (the live playground, real HOME, a full story cycle - the real workspace's _data/ and _config/ unchanged)
    command: sh playground/tests/r4-arms.sh
    expect:
      exit_code: 0
  - name: R5_the_comparison_lens
    description: the reference shelf builds sanitized into the playground's reference/ (both help trees, the development CLAUDE.md, the knowledge inventory, memory titles only), is idempotent with a stable census, the scenarios chapter carries the three-way classification, and the sample walk names every census door - a census row with no report row is a stale walk, a red
    command: sh playground/tests/r5-comparison.sh
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_the_workspace_bootstrap_net | ✅ | 2026-11-21 |
| R2_the_plug_and_play_seam | ✅ | 2026-11-21 |
| R3_the_request_archetypes | ✅ | 2026-11-21 |
| R4_isolation_both_arms | ✅ | 2026-11-21 |
| R5_the_comparison_lens | ✅ | 2026-11-21 |

Run at c20172d1d3a7eb18283e804dfc7422916eec8290
## Related

- [AHA-0031](AHA-0031) - Parent story

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
