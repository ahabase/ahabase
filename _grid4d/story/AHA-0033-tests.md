# AHA-0033-tests

> Test definition for AHA-0033 with one test per requirement - document properties of the amended architecture blueprint (shaping story; the census recount runs with the reviewers, not the suite).

## Design

One row per requirement, each measuring a decidable property of the deliverable file `_grid4d/implementation/implementation-ahabase-architecture-blueprint.md`: the layer table and its ownership columns (R1), fate-map completeness over the full 61-name census (R2), the state invariant and its rebuild column (R3), the workspace skeleton and every placeholder folder (R4), the numbered decisions (R5), and the sequencing with the folded ideas and the open questions (R6). All rows are self-contained greps and loops runnable from a copy of the worktree; no row asserts anything a settings file can override.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_layer_model_ownership
    description: the blueprint carries the engine layer table with all five layers named and the ownership rule sentence
    command: grep -q "Private residue" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md && grep -q "Ownership rule" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md && grep -q "Substrate (optional)" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md
    expect:
      exit_code: 0
  - name: R2_fate_map_every_census_name
    description: the Commands cells of the fate table, parsed as name tokens, equal the 61-name census exactly - sorted-set equality catches a missing name, a foreign name in a cell, and a duplicate (round-1 strengthened file-grep to the table; round-2 strengthened row-spanning grep to Commands-cell membership)
    command: bp=_grid4d/implementation/implementation-ahabase-architecture-blueprint.md; rows=$(sed -n "/### The capability fate map/,/### The numbered decisions/p" "$bp" | grep "^|"); cells=$(printf '%s\n' "$rows" | awk -F'|' '{c=$3; gsub(/^[ \t]+|[ \t]+$/, "", c); if (c=="" || c ~ /^-+$/ || c ~ /\(/) next; print c}' | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$' | sort); want=$(printf '%s\n' "active-story claude collab config containment declarations distribution doctor epic export-dbt export-gradient export-karma external extract-functions extract-rules find fork ha history hook-handler inbox-handler ingest init karma km link llm llm-init llm-update ml mqtt ontology pause pattern pipeline pre-tool-handler projection query recovery registry release resume sensor session-end-handler sessions skeleton snapshot status stop-handler store-service story sync test test-role test-scope trust verify verify-capabilities verify-file verify-stdin wiki" | tr ' ' '\n' | sort); [ "$cells" = "$want" ]
    expect:
      exit_code: 0
  - name: R3_state_invariant_and_rebuild_column
    description: the invariant sentence and the rebuild column of the state table are present
    command: grep -q "only source of truth" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md && grep -q "| Rebuild |" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md
    expect:
      exit_code: 0
  - name: R4_workspace_skeleton_all_folders
    description: the skeleton block names every placeholder folder with its contract table
    command: for f in _config _data _generated _inbox _temp _wikis _worktrees; do grep -q "$f/" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md || exit 1; done && grep -q "No placeholder without a writer" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md
    expect:
      exit_code: 0
  - name: R5_numbered_decisions
    description: decisions D1 through D4 are present with their headings (round 4 reversed D3 to MQTT per the Human ruling and added the D4 strategy)
    command: grep -q "D1 - worktrees live outside the repo" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md && grep -q "D2 - wiki publishing is an essential engine door" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md && grep -q "D3 - the public collab transport is MQTT; membership stays on git" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md && grep -q "D4 - carry the proven, simplify, never invent" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md
    expect:
      exit_code: 0
  - name: R6_sequencing_ideas_open_questions
    description: the sequencing section the three folded ideas and the open questions section exist
    command: grep -q "Sequencing toward the public flip" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md && for i in shared-taxonomy-space example-epic-in-distribution pattern-override-discovery; do grep -q "$i" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md || exit 1; done && grep -q "Open questions" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_layer_model_ownership | ✅ | 2026-11-22 |
| R2_fate_map_every_census_name | ✅ | 2026-11-22 |
| R3_state_invariant_and_rebuild_column | ✅ | 2026-11-22 |
| R4_workspace_skeleton_all_folders | ✅ | 2026-11-22 |
| R5_numbered_decisions | ✅ | 2026-11-22 |
| R6_sequencing_ideas_open_questions | ✅ | 2026-11-22 |

Run at 0aca9d6549347dad46999ef1a9ee399686ea0e5a
## Related

- [AHA-0033](AHA-0033) - Parent story

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
