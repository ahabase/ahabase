# AHA-0009-tests

> Test definition for AHA-0009 with one test per requirement.

## Design

R1 checks the declarations by reading the documents and modules. R2 and R3 run the new commands on the tree and on a temporary copy with a planted change, so each green row is backed by a red control in the same row; the package's own test suite carries the unit tests and runs in R3. R4 checks that the new capability appears in its own lineage. Every guard stands alone with an explicit exit; the rows stay red until the work lands.

The commands' contract the rows rely on: `ahabase verify` exits 0 when the lineage holds, 1 on a divergence and prints one `DIVERGENCE <class>: ...` line per divergence (classes `state-contradiction`, `missing-concept`, `no-code-line`, `missing-module`, `unclaimed-module`, `back-link`; the first two from the local review on f619ada, covered by the package tests); `ahabase ontology graph --check` exits 1 and says `stale` when the block differs from what would be generated; a usage error is click's exit 2, and a crash also exits 1 but prints no class line, so a red control that requires exit 1 and its class line passes neither on a crash nor on a wrong argument. Every red control first confirms that its planted change landed (local review, fail-open findings 1-5 on 939c0c8).

## Definition

```yaml
tests:
  - name: R1_lineage_declarations
    description: CodeArtifacts in the identity; a Code line naming existing modules (or the document marker) in every implementation blueprint; an Implements line naming an existing blueprint in every module; a projections declaration
    command: |
      grep -qE '^\*\*CodeArtifacts:\*\* src/ahabase$' _grid4d/story/AHABASE.md || { echo "no CodeArtifacts"; exit 1; }
      for f in _grid4d/implementation/implementation-ahabase-*-blueprint.md; do
        line=$(grep -E '^\*\*Code:\*\* ' "$f" | head -1 | sed 's/^\*\*Code:\*\* //')
        [ -n "$line" ] || { echo "no Code line: $f"; exit 1; }
        [ "$line" = "none (document blueprint)" ] && continue
        for m in $(echo "$line" | tr ',' ' '); do
          [ -f "src/ahabase/$m.py" ] || { echo "Code names a missing module: $f -> $m"; exit 1; }
        done
      done
      for m in src/ahabase/*.py; do
        b=$(grep -oE '^Implements: implementation-ahabase-[a-z-]+-blueprint$' "$m" | head -1 | sed 's/^Implements: //')
        [ -n "$b" ] || { echo "no Implements: $m"; exit 1; }
        [ -f "_grid4d/implementation/$b.md" ] || { echo "Implements names a missing blueprint: $m -> $b"; exit 1; }
      done
      [ -f _grid4d/pattern/ahabase-projections-pattern.md ] || { echo "no projections declaration"; exit 1; }
      echo ok
    expect:
      exit_code: 0
  - name: R2_ontology_map_generated
    description: the map is generated, idempotent, the committed map is current, and --check catches a hand edit
    command: |
      d=$(mktemp -d); cp -R _grid4d src "$d/"
      ix="$d/_grid4d/ontology/00-ahabase-ontology-index.md"
      perl -0pi -e 's/<!-- ontology-map:begin -->.*?<!-- ontology-map:end -->\n?//s' "$ix"
      if grep -q 'ontology-map:begin' "$ix"; then echo "control: block not removed"; exit 1; fi
      .venv/bin/ahabase ontology graph --root "$d" >/dev/null || { echo "generate failed"; exit 1; }
      grep -q '<!-- ontology-map:begin -->' "$ix" || { echo "no map block written"; exit 1; }
      sed -n '/<!-- ontology-map:begin -->/,/<!-- ontology-map:end -->/p' "$ix" | grep -q 'flowchart' || { echo "no mermaid in the block"; exit 1; }
      a=$(shasum "$ix")
      .venv/bin/ahabase ontology graph --root "$d" >/dev/null || { echo "second generate failed"; exit 1; }
      [ "$a" = "$(shasum "$ix")" ] || { echo "not idempotent"; exit 1; }
      .venv/bin/ahabase ontology graph --root "$d" --check >/dev/null || { echo "regenerated copy not current"; exit 1; }
      .venv/bin/ahabase ontology graph --root . --check || { echo "committed map is stale"; exit 1; }
      perl -0pi -e 's/(<!-- ontology-map:begin -->\n)/$1%% hand edit\n/' "$ix"
      grep -q '%% hand edit' "$ix" || { echo "control not planted"; exit 1; }
      rc=0; out=$(.venv/bin/ahabase ontology graph --root "$d" --check 2>&1) || rc=$?
      [ "$rc" = 1 ] || { echo "hand edit: expected exit 1, got $rc: $out"; exit 1; }
      echo "$out" | grep -q 'stale' || { echo "hand edit: no stale message: $out"; exit 1; }
      echo ok
    expect:
      exit_code: 0
  - name: R3_lineage_check
    description: verify is green on the tree and red with the right class on each planted gap (a control asks only for its own class; other classes a plant also causes are allowed); the package suite passes
    command: |
      .venv/bin/ahabase verify --root . >/dev/null || { echo "verify red on the tree"; exit 1; }
      plant() { d=$(mktemp -d); cp -R _grid4d src "$d/"; echo "$d"; }
      expect_gap() {
        rc=0; out=$(.venv/bin/ahabase verify --root "$1" 2>&1) || rc=$?
        [ "$rc" = 1 ] || { echo "$2: expected exit 1, got $rc: $out"; exit 1; }
        echo "$out" | grep -q "^DIVERGENCE $2:" || { echo "$2: class not reported: $out"; exit 1; }
      }
      d=$(plant); f="$d/_grid4d/implementation/implementation-ahabase-safe-blueprint.md"
      grep -q '^\*\*Code:\*\* ' "$f" || { echo "control A: no Code line to remove"; exit 1; }
      perl -ni -e 'print unless /^\*\*Code:\*\* /' "$f"
      if grep -q '^\*\*Code:\*\* ' "$f"; then echo "control A not planted"; exit 1; fi
      expect_gap "$d" no-code-line
      d=$(plant); f="$d/src/ahabase/plugins.py"
      perl -ni -e 'print unless /^Implements: /' "$f"
      if grep -q '^Implements: ' "$f"; then echo "control B not planted"; exit 1; fi
      expect_gap "$d" back-link
      d=$(plant); printf '"""A stray module."""\n' > "$d/src/ahabase/stray.py"
      [ -f "$d/src/ahabase/stray.py" ] || { echo "control C not planted"; exit 1; }
      expect_gap "$d" unclaimed-module
      d=$(plant); f="$d/_grid4d/implementation/implementation-ahabase-safe-blueprint.md"
      perl -pi -e 's/^(\*\*Code:\*\* .*)$/$1, ghost/' "$f"
      grep -q '^\*\*Code:\*\* .*, ghost$' "$f" || { echo "control D not planted"; exit 1; }
      expect_gap "$d" missing-module
      d=$(plant); f="$d/src/ahabase/plugins.py"
      perl -pi -e 's/^Implements: implementation-ahabase-architecture-blueprint$/Implements: implementation-ahabase-safe-blueprint/' "$f"
      grep -q '^Implements: implementation-ahabase-safe-blueprint$' "$f" || { echo "control E not planted"; exit 1; }
      expect_gap "$d" back-link
      d=$(plant)
      printf '# Orphan Blueprint\n\n**State:** planned\n' > "$d/_grid4d/ontology/ontology-orphan-blueprint.md"
      rc=0; out=$(.venv/bin/ahabase verify --root "$d" 2>&1) || rc=$?
      [ "$rc" = 0 ] || { echo "planned absence made verify red ($rc): $out"; exit 1; }
      echo "$out" | grep -q '^ABSENCE concept-without-implementation: ontology-orphan-blueprint (State: planned)$' || { echo "absence not reported: $out"; exit 1; }
      echo "$out" | grep -q '^DOCUMENT implementation-ahabase-safe-threat-model-blueprint$' || { echo "document class not reported: $out"; exit 1; }
      perl -pi -e 's/^\*\*State:\*\* planned$/**State:** implemented/' "$d/_grid4d/ontology/ontology-orphan-blueprint.md"
      grep -q '^\*\*State:\*\* implemented$' "$d/_grid4d/ontology/ontology-orphan-blueprint.md" || { echo "control F not planted"; exit 1; }
      expect_gap "$d" state-contradiction
      .venv/bin/python -m pytest -q tests >/dev/null || { echo "package suite red"; exit 1; }
      echo ok
    expect:
      exit_code: 0
      timeout: 180
  - name: R4_capability_in_its_own_lineage
    description: an implementation blueprint names the core module in its Code line and implements a concept of this story; the architecture order marks the step done
    command: |
      f=$(grep -lE '^\*\*Code:\*\* (.*, )?lineage(,|$)' _grid4d/implementation/implementation-ahabase-*-blueprint.md | head -1)
      [ -n "$f" ] || { echo "no blueprint names the lineage module"; exit 1; }
      [ -f src/ahabase/lineage.py ] || { echo "no lineage module"; exit 1; }
      c=$(grep -E '^\*\*Implements:\*\* ' "$f" | grep -oE 'ontology-(lineage|projection)-blueprint' | head -1)
      [ -n "$c" ] || { echo "core blueprint implements no concept of this story"; exit 1; }
      grep -qE '^\*\*Story:\*\* .*AHA-0009' "_grid4d/ontology/$c.md" || { echo "$c is not a concept of this story"; exit 1; }
      sed -n '/^## Order of the next stories/,/^## /p' _grid4d/implementation/implementation-ahabase-architecture-blueprint.md | grep -qE '^[0-9]+\. \*\*Transparency\*\* .* - done \(AHA-0009\)\.$' || { echo "order item not marked done"; exit 1; }
      echo ok
    expect:
      exit_code: 0
  - name: R_team_logged
    description: the team record exists and at least one verdict line names a full commit
    command: |
      grep -qE '^- \*\*Team record' _grid4d/story/AHA-0009.md || { echo "no team record"; exit 1; }
      grep -qE '^- \*\*Verdict [^*]+:\*\* (APPROVED|CHANGES) at [0-9a-f]{40}' _grid4d/story/AHA-0009.md || { echo "no verdict line with its commit"; exit 1; }
      echo ok
    expect:
      exit_code: 0
  - name: R_docs_complete
    description: the concepts the core implements (its blueprint's Implements line) carry Placement and State and appear in the index vocabulary
    command: |
      n=0
      core=_grid4d/implementation/implementation-ahabase-transparency-blueprint.md
      [ -f "$core" ] || { echo "no core blueprint"; exit 1; }
      for c in $(grep -E '^\*\*Implements:\*\* ' "$core" | grep -oE '\(ontology-[a-z-]+-blueprint\)' | tr -d '()'); do
        f="_grid4d/ontology/$c.md"
        [ -f "$f" ] || { echo "implemented concept missing: $c"; exit 1; }
        grep -qE '^\*\*Placement:\*\* .+' "$f" && grep -qE '^\*\*State:\*\* .+' "$f" || { echo "missing Placement/State: $f"; exit 1; }
        grep -q "($(basename "$f" .md))" _grid4d/ontology/00-ahabase-ontology-index.md || { echo "not in the index: $f"; exit 1; }
        n=$((n+1))
      done
      [ "$n" -ge 1 ] || { echo "no concept of this story"; exit 1; }
      echo ok
    expect:
      exit_code: 0
  - name: R_issues_logged
    description: the issues record names at least one entry - a logged issue or an explicit none-met statement
    command: |
      line=$(grep -E '^- \*\*Issues:\*\* ' _grid4d/story/AHA-0009.md | head -1)
      [ -n "$line" ] || { echo "no issues record"; exit 1; }
      [ "$line" = "- **Issues:** none met" ] && { echo ok; exit 0; }
      n=0
      for i in $(echo "$line" | grep -oE '\]\([a-z0-9-]+\)' | tr -d '])('); do
        [ -f "_grid4d/issue/$i.md" ] || { echo "issue link does not resolve: $i"; exit 1; }
        n=$((n+1))
      done
      [ "$n" -ge 1 ] || { echo "no issue linked"; exit 1; }
      echo ok
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_lineage_declarations | ✅ | 2026-10-26 |
| R2_ontology_map_generated | ✅ | 2026-10-26 |
| R3_lineage_check | ✅ | 2026-10-26 |
| R4_capability_in_its_own_lineage | ✅ | 2026-10-26 |
| R_team_logged | ✅ | 2026-10-26 |
| R_docs_complete | ✅ | 2026-10-26 |
| R_issues_logged | ✅ | 2026-10-26 |

## Related

- [AHA-0009](AHA-0009) - Parent story
