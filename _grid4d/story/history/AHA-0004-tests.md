# AHA-0004-tests

> Test definition for AHA-0004 with one test per requirement.

## Design

The rows check the ontology's structure and verification, the presence of the rulings in the index and the identity, the naming, and the links of the current documents. Every guard stands alone with an explicit exit, so a failing check cannot pass under `set -e`. Nothing of the instance is read or changed.

## Definition

```yaml
tests:
  - name: R1_big_picture
    description: the index exists with its sections, names all layers with their state and verifies
    command: |
      f=_grid4d/ontology/00-ahabase-ontology-index.md
      for s in "## Purpose" "## Taxonomy" "## Vocabulary" "## Relations" "## Constraints"; do
        if ! grep -q "^$s" "$f"; then echo "missing $s"; exit 1; fi
      done
      for l in "0 Primitives" "1 Knowledge structure" "2 Trust and boundaries" "3 Platform" "Collaboration (basis)"; do
        if ! grep -q "$l" "$f"; then echo "missing layer $l"; exit 1; fi
      done
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$f"
    expect:
      exit_code: 0
  - name: R2_competence
    description: the rulings are in the index and the identity; no current document calls evolucean the core
    command: |
      for r in "The boundary criterion" "Never back" "Collaboration in three layers"; do
        if ! grep -q "$r" _grid4d/ontology/00-ahabase-ontology-index.md; then echo "index lacks $r"; exit 1; fi
      done
      if ! grep -q "Base and method" _grid4d/story/AHABASE.md; then echo "identity lacks the rule"; exit 1; fi
      hits=$(grep -rniE "evolucean core|closed core|the core's|of the core\b" _grid4d/story/AHABASE.md _grid4d/ontology _grid4d/implementation _grid4d/idea _grid4d/issue README.md || true)
      if [ -n "$hits" ]; then echo "$hits"; exit 1; fi
    expect:
      exit_code: 0
  - name: R3_move_and_turn
    description: the architecture blueprint carries the argument, the steps and the gate; the identity names the exception
    command: |
      f=_grid4d/implementation/implementation-ahabase-architecture-blueprint.md
      for s in "## Base and method" "strangler fig" "Gate of the turn" "Dual reading" "rollback"; do
        if ! grep -qi "$s" "$f"; then echo "blueprint lacks $s"; exit 1; fi
      done
      if ! grep -q "known exception until the format and the workflow move here" _grid4d/story/AHABASE.md; then echo "identity lacks the exception"; exit 1; fi
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$f"
    expect:
      exit_code: 0
  - name: R4_concepts
    description: sixteen concept blueprints exist, verify and are in the vocabulary; implementation blueprints implement concepts; no Concepts in brief left
    command: |
      idx=_grid4d/ontology/00-ahabase-ontology-index.md
      n=0
      for c in trust-zone boundary safe-value reference store manifest consumer shadow-run rotation agent-guard output-watch scan-finding door registry plugin health-check; do
        f=_grid4d/ontology/ontology-$c-blueprint.md
        if [ ! -f "$f" ]; then echo "missing $f"; exit 1; fi
        if ! grep -q "(ontology-$c-blueprint)" "$idx"; then echo "not in vocabulary: $c"; exit 1; fi
        if ! grep -qE "^\*\*Placement:\*\* (base|method) - .+" "$f"; then echo "no placement with reason: $c"; exit 1; fi
        if ! grep -qE "^\*\*State:\*\* (defined|implemented|planned)" "$f"; then echo "no state: $c"; exit 1; fi
        ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$f" >/dev/null || { echo "verify failed: $f"; exit 1; }
        n=$((n+1))
      done
      if [ "$n" -ne 16 ]; then echo "expected 16, got $n"; exit 1; fi
      for b in architecture safe; do
        if ! grep -E "^\*\*Implements:\*\*" "_grid4d/implementation/implementation-ahabase-$b-blueprint.md" | grep -q "(ontology-"; then echo "$b blueprint implements no concept"; exit 1; fi
      done
      if grep -q "^## Concepts in brief" _grid4d/story/AHABASE.md; then echo "extract still in the identity"; exit 1; fi
    expect:
      exit_code: 0
      timeout: 300
  - name: R5_links_point_inward
    description: current documents link only within the repository and name no closed-zone document, except the listed generated lines tied to their issues
    command: |
      python3 - <<'PY'
      import pathlib, re, sys
      root = pathlib.Path("_grid4d")
      names = {p.stem for p in root.rglob("*.md")}
      released = re.compile(r"^AHA-000[1-3][.-]")  # released stories keep their text
      known = {
          ("AHA-0004.md", "implementation-story-blueprint"): "open-zone-documents-link-into-the-closed-zone",  # exception entry
      }
      pattern_line = "closed = re.compile("  # the one line of this test that carries the pattern
      closed = re.compile(r"\bEVOLUCEAN-[A-Z]|ahabase-package-architecture|foundation-roadmap")
      bad, seen = [], set()
      for p in sorted(root.rglob("*.md")):
          if released.search(p.name) or "history" in p.parts:
              continue
          for n, line in enumerate(p.read_text().splitlines(), 1):
              if p.name == "AHA-0004-tests.md" and (pattern_line in line or "# exception entry" in line):
                  continue
              hits = [t for t in re.findall(r"\]\(([^)#]+)\)", line)
                      if not t.startswith("http") and pathlib.Path(t).stem not in names]
              # a blueprint named in plain text must be one of this repository
              hits += [f"(text) {t}" for t in re.findall(r"(?<![\w$-])[a-z0-9]+(?:-[a-z0-9]+)*-blueprint\b", re.sub(r"\]\([^)]*\)", "", line))
                       if t not in names]
              if closed.search(line) and not hits:
                  hits = ["(name in text)"]
              for t in hits:
                  key = next((k for k in known if k[0] == p.name and k[1] in line), None)
                  if key:
                      seen.add(key)
                  else:
                      bad.append(f"{p}:{n}: {t}")
      for k in known:
          print(f"known exception {k[0]} -> {k[1]} ({known[k]})" + ("" if k in seen else " - no longer present, remove it"))
      print("\n".join(bad) or "links point inward")
      sys.exit(1 if bad else 0)
      PY
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_big_picture | ✅ | 2026-10-25 |
| R2_competence | ✅ | 2026-10-25 |
| R3_move_and_turn | ✅ | 2026-10-25 |
| R4_concepts | ✅ | 2026-10-25 |
| R5_links_point_inward | ✅ | 2026-10-25 |

## Related

- [AHA-0004](AHA-0004) - Parent story
