# AHA-0023-tests

> Test definition for AHA-0023 with one test per requirement.

## Design

Test requirements for AHA-0023. One test per requirement. R_team is red until the reviewer seat's checkpoints are recorded in the story (the honest starting state); R1 and R2 are green once the document and the scanner measurements hold. R2 is scoped: the workspace scanners must be consistent about this story's document and must not name it - a pre-existing unrelated scanner finding (llm-pin-model-tests.py, observed before this story's document landed) is out of scope and logged separately, never silently.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_document_form
    description: "the priorities document instantiates the ruled form - P1 open set by the Human 2026-11-08, snapshot rulings, structural default line, exactly eight numbered rows in the Human's order (safe, llm, grid4d infrastructure, trust, collaboration, decision, projection, story), each row with serves and done-looks-like, no date-range period name, AHABASE the only wiki link"
    command: |
      python3 - <<'EOF'
      import re, pathlib
      doc = pathlib.Path('_grid4d/story/AHABASE-Priorities.md').read_text()
      assert '**P1** — 2026-11-08 · open · set by the Human 2026-11-08' in doc
      assert 'current snapshot only, never a history log' in doc
      assert 'replaces the list, not by date' in doc
      assert 'git log --follow -- this file' in doc
      assert 'Structural gradients not named above stay under their automatic ordering; no row rules one out.' in doc
      assert '2026-W45' not in doc
      rows = re.findall(r'^(\d+)\. (.+)$', doc, re.M)
      assert [n for n, _ in rows] == [str(i) for i in range(1, 9)], [n for n, _ in rows]
      order = ['safe', 'llm', 'grid4d infrastructure', 'trust', 'collaboration', 'decision', 'projection', 'story']
      for (n, txt), area in zip(rows, order):
          assert area in txt.lower(), (n, area)
          assert 'serves' in txt and 'done looks like' in txt, n
      links = re.findall(r'\]\(([^)]+)\)', doc)
      assert set(links) == {'AHABASE'}, links
      print('R1_OK')
      EOF
    expect:
      exit_code: 0
  - name: R2_scanner_ignorance
    description: "with the document in place, status is green; verify's source counts are consistent (the document ingested by sync) and no scanner line names AHABASE-Priorities as a problem - the document is declaration, not a validated type; pre-existing unrelated findings are out of scope and logged"
    command: |
      CLI=/Users/<user>/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage
      s=$("$CLI" status 2>&1) || { echo "STATUS RED"; echo "$s"; exit 1; }
      v=$("$CLI" verify 2>&1) || true
      printf '%s\n%s\n' "$s" "$v" | grep -q "AHABASE-Priorities" && { echo "SCANNER NAMES THE DOC"; exit 1; }
      printf '%s\n' "$v" | grep -q "Sources inconsistent" && { echo "SOURCES INCONSISTENT"; exit 1; }
      echo R2_OK
    expect:
      exit_code: 0
  - name: R_team_review_recorded
    description: "the reviewer seat's checkpoints are recorded in the story Notes (mutual review every story); friction observed during the work is logged as issue or idea docs, none silent"
    command: |
      grep -q "Review (home:c020eeb4" _grid4d/story/AHA-0023.md || { echo "NO REVIEW RECORD"; exit 1; }
      echo R_TEAM_OK
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_document_form | ✅ | 2026-11-08 |
| R2_scanner_ignorance | ✅ | 2026-11-08 |
| R_team_review_recorded | ✅ | 2026-11-08 |

Run at a967c3247081cd4ab1d8742e4a4c86ca6cd7c876
## Related

- [AHA-0023](AHA-0023) - Parent story

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
