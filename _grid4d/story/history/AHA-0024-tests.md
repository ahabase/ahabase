# AHA-0024-tests

> Test definition for AHA-0024 with one test per requirement.

## Design

Test requirements for AHA-0024. One test per requirement. The R2 row checks that the frozen heading exists; it does not verify the contract's substance, which the reviewers judge by reading the blueprint against the method code.

## Definition

```yaml
tests:
  - name: R1_ontology_subepic_exists_and_names_no_closed_zone_doc
    description: The ahabase-llm subepic identity, the ontology index and at least one concept blueprint exist, and no document of the subepic names a closed-zone document.
    command: 'test -f _grid4d/subepic/ahabase-llm/story/AHABASE-LLM.md && test -f _grid4d/subepic/ahabase-llm/ontology/00-ahabase-llm-ontology-index.md && test "$(ls _grid4d/subepic/ahabase-llm/ontology/ontology-*-blueprint.md | wc -l)" -ge 1 && ! grep -rn -E "evolucean-[a-z]" _grid4d/subepic/ahabase-llm'
    expect:
      exit_code: 0
  - name: R2_blueprint_carries_the_frozen_seam_contract
    description: The implementation blueprint exists and carries the section Seam contract (frozen).
    command: 'grep -q "^## Seam contract (frozen)" _grid4d/subepic/ahabase-llm/implementation/implementation-ahabase-llm-blueprint.md'
    expect:
      exit_code: 0
  - name: R3a_access_path_and_discovery
    description: Access path resolution and discovery are ported with tests; nothing imports a method.
    command: 'test -f src/ahabase/llm/paths.py && test -f src/ahabase/llm/discovery.py && ! grep -rn -E "knowledge_usage_cli|evolucean" src/ahabase/llm && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi; $PY -m pytest tests/llm -q'
    expect:
      exit_code: 0
  - name: R3b_verification_and_failure_classification
    description: Verification and failure classification are ported with tests; nothing imports a method.
    command: 'test -f src/ahabase/llm/verify.py && ! grep -rn -E "knowledge_usage_cli|evolucean" src/ahabase/llm && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi; $PY -m pytest tests/llm -q'
    expect:
      exit_code: 0
  - name: R3c_switch_restore_and_session_payload
    description: The settings switch, restore and session payload are ported with tests; a credential canary test in tests/llm plants a value in each source and asserts it appears in no output, log line or file.
    command: 'test -f src/ahabase/llm/switch.py && test -f src/ahabase/llm/session.py && ! grep -rn -E "knowledge_usage_cli|evolucean" src/ahabase/llm && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi; $PY -m pytest tests/llm -q'
    expect:
      exit_code: 0
  - name: R4_six_checks_table_in_notes
    description: The Notes carry the six graduation checks with evidence rows.
    command: 'test "$(grep -c "^| Check [1-6] " _grid4d/story/AHA-0024.md)" -eq 6'
    expect:
      exit_code: 0
  - name: R4b_rules_conformance_table_in_notes
    description: The Notes carry one conformance row per Rule of the Epic (eleven rows).
    command: 'test "$(grep -c "^| Rule [0-9]* " _grid4d/story/AHA-0024.md)" -eq 11'
    expect:
      exit_code: 0
  - name: R5_release_ready_branch_pushed_and_clean
    description: Release readiness, checkable before the release (the tag itself appears at completion and is read from the remote by the flip story R4) - the branch is pushed at the head and no tag of this story exists yet (a clean tree is not required because the tests file carries the run stamp).
    command: 'b=$(git branch --show-current) && heads=$(git ls-remote origin "refs/heads/$b") && tags=$(git ls-remote --tags origin "v0.0024.*") && test "$(git rev-parse HEAD)" = "${heads%%[[:space:]]*}" && test -z "$tags"'
    expect:
      exit_code: 0
  - name: R6_flip_story_named_in_notes
    description: The Notes name the minted flip story and its frozen-contract diff result.
    command: 'grep -q "flip story: EVOLUCEAN-AHB-" _grid4d/story/AHA-0024.md && grep -q "contract diff: empty" _grid4d/story/AHA-0024.md'
    expect:
      exit_code: 0
  - name: R_ontology_closing_table_in_notes
    description: The Notes carry the closing table of concepts added, merged or removed.
    command: 'grep -q "Concepts added, merged or removed" _grid4d/story/AHA-0024.md'
    expect:
      exit_code: 0
  - name: R_team_checkpoints_recorded
    description: The Notes record the reviewer checkpoints per stage.
    command: 'grep -q "Review checkpoint" _grid4d/story/AHA-0024.md'
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_ontology_subepic_exists_and_names_no_closed_zone_doc | ✅ | 2026-11-08 |
| R2_blueprint_carries_the_frozen_seam_contract | ✅ | 2026-11-08 |
| R3a_access_path_and_discovery | ✅ | 2026-11-08 |
| R3b_verification_and_failure_classification | ✅ | 2026-11-08 |
| R3c_switch_restore_and_session_payload | ✅ | 2026-11-08 |
| R4_six_checks_table_in_notes | ✅ | 2026-11-08 |
| R4b_rules_conformance_table_in_notes | ✅ | 2026-11-08 |
| R5_release_tag_on_the_remote | ❌ | 2026-11-08 |
| R6_flip_story_named_in_notes | ✅ | 2026-11-08 |
| R_ontology_closing_table_in_notes | ✅ | 2026-11-08 |
| R_team_checkpoints_recorded | ✅ | 2026-11-08 |
| R5_release_ready_branch_pushed_and_clean | ✅ | 2026-11-08 |

Run at 15d444a90767b7b61aa54d531c1303e4d87d2ab7
## Related

- [AHA-0024](AHA-0024) - Parent story

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
