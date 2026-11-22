# AHA-0005-tests

> Test definition for AHA-0005 with one test per requirement.

## Design

The rows check the structure of the integration blueprint and that the safe blueprint, the idea and the Output Watch concept carry the same decisions. Every guard stands alone with an explicit exit. Nothing of the instance is read or changed.

## Definition

```yaml
tests:
  - name: R1_comparison
    description: the integration blueprint compares tools for all four parts and verifies
    command: |
      f=_grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md
      for s in "### Scanner (Scan Finding)" "### Stores (Store)" "### Git credential helper" "### Agent guard and output watch"; do
        if ! grep -qF "$s" "$f"; then echo "missing part: $s"; exit 1; fi
      done
      for t in gitleaks trufflehog detect-secrets keyring OpenBao "Git Credential Manager" "PostToolUse"; do
        if ! grep -qF "$t" "$f"; then echo "not compared: $t"; exit 1; fi
      done
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$f"
    expect:
      exit_code: 0
  - name: R2_decisions
    description: a decision per part, the five rules, the git helper decision in the safe blueprint
    command: |
      f=_grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md
      n=$(grep -c "^\*\*Decision:" "$f")
      if [ "$n" -ne 4 ]; then echo "expected 4 decisions, got $n"; exit 1; fi
      for r in "Integrate before writing" "Offline by default" "Our own reduction of output" "Licence fit" "Re-check before building"; do
        if ! grep -qF "$r" "$f"; then echo "missing rule: $r"; exit 1; fi
      done
      if ! grep -q "Git Credential Manager, integrated as it is" _grid4d/implementation/implementation-ahabase-safe-blueprint.md; then echo "safe blueprint lacks the git decision"; exit 1; fi
    expect:
      exit_code: 0
  - name: R3_hook_reach
    description: the reach of each agent mechanism and the consequence are stated, and the concept and the idea agree
    command: |
      f=_grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md
      for s in "Permission rules" "Sandbox" "PreToolUse hook" "PostToolUse hook" "only what the model sees" "Consequence for the motivating scenario"; do
        if ! grep -qF "$s" "$f"; then echo "missing: $s"; exit 1; fi
      done
      if ! grep -q "replaces only what the model sees" _grid4d/ontology/ontology-output-watch-blueprint.md; then echo "concept disagrees"; exit 1; fi
      if grep -qiE "reaching the screen|before it reaches the shared screen" _grid4d/ontology/ontology-output-watch-blueprint.md; then echo "concept still claims the screen"; exit 1; fi
      if ! grep -q "not the screen" _grid4d/idea/safe-first-public-capability.md; then echo "idea disagrees"; exit 1; fi
    expect:
      exit_code: 0
  - name: R4_open_questions
    description: the idea says which questions were answered and which remain; the research step is done
    command: |
      i=_grid4d/idea/safe-first-public-capability.md
      if ! grep -q "Answered by the research of \[AHA-0005\]" "$i"; then echo "no answered list"; exit 1; fi
      if ! grep -q "^Still open:" "$i"; then echo "no still-open list"; exit 1; fi
      if ! grep -q "done in \[AHA-0005\]" "$i"; then echo "promotion path not updated"; exit 1; fi
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$i"
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_comparison | ✅ | 2026-10-25 |
| R2_decisions | ✅ | 2026-10-25 |
| R3_hook_reach | ✅ | 2026-10-25 |
| R4_open_questions | ✅ | 2026-10-25 |

## Related

- [AHA-0005](AHA-0005) - Parent story
