# AHA-0006-tests

> Test definition for AHA-0006 with one test per requirement.

## Design

The rows check the structure of the threat model, the designed rules in the concepts and the agreement of every document that states the order of the next steps. Every guard stands alone with an explicit exit. Nothing of the instance is read or changed.

## Definition

```yaml
tests:
  - name: R1_threat_model
    description: assets, attackers, eight threats with four parts each, rules; verifies
    command: |
      f=_grid4d/implementation/implementation-ahabase-safe-threat-model-blueprint.md
      for s in "## Assets" "## Attackers" "## Threats" "## Rules" "### Repudiation" "Kerckhoffs"; do
        if ! grep -qF "$s" "$f"; then echo "missing: $s"; exit 1; fi
      done
      for t in 1 2 3 4 5 6 7 8 9 10 11; do
        if ! grep -q "^### T$t " "$f"; then echo "missing T$t"; exit 1; fi
      done
      for p in "- **Vector:**" "- **Today (implemented):**" "- **Designed:**" "- **Residual (accepted):**"; do
        n=$(grep -cF -- "$p" "$f")
        if [ "$n" -ne 11 ]; then echo "expected 11 of '$p', got $n"; exit 1; fi
      done
      for c in spoofing tampering elevation disclosure "denial of service"; do
        if ! grep -E "^### T[0-9]+ .*\(.*$c" "$f" >/dev/null; then echo "STRIDE class without a row: $c"; exit 1; fi
      done
      for b in "**By absolute path**" "**No shells, interpreters or wrappers**" "**No general-purpose network tools**" "**Minimal environment**" "**Shell-free, pinned**"; do
        if ! grep -qF "$b" "$f"; then echo "binding rule missing: $b"; exit 1; fi
      done
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$f"
    expect:
      exit_code: 0
  - name: R2_design_rules
    description: the designed rules are in their concepts with a link to the threat model
    command: |
      o=_grid4d/ontology
      if ! grep -q "Allowed consumers\*\* (designed)" $o/ontology-manifest-blueprint.md; then echo "manifest lacks consumer binding"; exit 1; fi
      if ! grep -q "inside a git working tree" $o/ontology-manifest-blueprint.md; then echo "manifest lacks the working-tree rule"; exit 1; fi
      if ! grep -q "Revealed by a person only\*\* (designed)" $o/ontology-safe-value-blueprint.md; then echo "safe value lacks reveal rule"; exit 1; fi
      if ! grep -q "ahabase safe get" $o/ontology-agent-guard-blueprint.md; then echo "agent guard lacks defaults"; exit 1; fi
      if ! grep -q "Network allow-list" $o/ontology-agent-guard-blueprint.md; then echo "agent guard lacks network list"; exit 1; fi
      if ! grep -q "Protected places\*\* (designed)" $o/ontology-agent-guard-blueprint.md; then echo "agent guard lacks protected places"; exit 1; fi
      if grep -q "an agent's shell cannot reveal" $o/ontology-safe-value-blueprint.md; then echo "safe value overclaims the reveal check"; exit 1; fi
      if ! grep -q "Safe access is declared\*\* (designed)" $o/ontology-plugin-blueprint.md; then echo "plugin lacks declaration"; exit 1; fi
      for c in manifest agent-guard plugin; do
        if ! grep -q "(implementation-ahabase-safe-threat-model-blueprint)" $o/ontology-$c-blueprint.md; then echo "$c lacks the link"; exit 1; fi
      done
    expect:
      exit_code: 0
  - name: R3_order
    description: every document that states the order puts the agent path before the scanner; the idea links the model
    command: |
      if ! grep -q "Close the agent path first" _grid4d/implementation/implementation-ahabase-safe-threat-model-blueprint.md; then echo "model lacks the rule"; exit 1; fi
      if ! grep -q "the agent path first - consumer binding" _grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md; then echo "integration order disagrees"; exit 1; fi
      if ! grep -q "the threat model (AHA-0006), the agent path" _grid4d/implementation/implementation-ahabase-architecture-blueprint.md; then echo "architecture order disagrees"; exit 1; fi
      i=_grid4d/idea/safe-first-public-capability.md
      a=$(grep -n "safe agent-guard" "$i" | grep -E "^[0-9]+:3\. " | cut -d: -f1)
      s=$(grep -n "^4\. \`safe scan\`" "$i" | cut -d: -f1)
      if [ -z "$a" ] || [ -z "$s" ] || [ "$a" -ge "$s" ]; then echo "idea's promotion path does not put the agent path first"; exit 1; fi
      if ! grep -q "(implementation-ahabase-safe-threat-model-blueprint)" "$i"; then echo "idea lacks the link"; exit 1; fi
      left=$(grep -rln "safest first step\|first step for any user" _grid4d/ontology _grid4d/implementation _grid4d/idea || true)
      if [ -n "$left" ]; then echo "scan still called the first step in: $left"; exit 1; fi
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_threat_model | ✅ | 2026-10-25 |
| R2_design_rules | ✅ | 2026-10-25 |
| R3_order | ✅ | 2026-10-25 |

## Related

- [AHA-0006](AHA-0006) - Parent story
