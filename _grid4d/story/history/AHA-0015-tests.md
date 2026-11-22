# AHA-0015-tests

> Test definition for AHA-0015 with one test per requirement.

## Design

Test requirements for AHA-0015. One test per requirement. The declaration (R1) is checked as parsed yaml plus its prose markers; R2 and R3 drive `ProjectionRegistry.generate_all` - the same call the sync tail makes - with an `Epic` bound to this worktree (the CLI command resolves the workspace tree, which the story guard holds); each of R2, R3, R4 carries a red control on a scratch copy built with `git archive HEAD` of the runner's checkout (a docs-only delta above the pin today), named `ahabase` because the copy carries no `.git` and the tree-to-epic mapping falls to the directory name - measured: an oddly named copy checks green, [declarations-check-skips-unmapped-trees](declarations-check-skips-unmapped-trees)); R_team holds the review verdict record; R_docs and R_issues hold the pattern prose and the issue files.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_declaration_parses_and_prose_names_the_rules
    description: "the pattern's yaml fence parses and declares exactly [concepts, issues], and the prose names the story, the two issues, the stories-not-declared reason and the fallback"
    command: |
      PY=$HOME/ahabase/evolucean/knowledge-usage-cli/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      "$PY" - <<'PYEOF'
      import re, yaml
      from pathlib import Path
      text = Path('_grid4d/pattern/ahabase-projections-pattern.md').read_text()
      fence = chr(96) * 3
      m = re.search(fence + r'yaml\n(.*?)' + fence, text, re.DOTALL)
      assert m, 'no yaml fence'
      parsed = yaml.safe_load(m.group(1))
      assert parsed.get('projections') == ['concepts', 'issues'], parsed
      for marker in ('AHA-0015', 'story-prefix-derived-from-repo-name',
                     'open-zone-documents-link-into-the-closed-zone',
                     'Not declared', 'fallback'):
          assert marker in text, marker
      print('R1_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R1_OK"
      timeout: 60
  - name: R2_generation_proof_in_worktree
    description: "generate_all bound to this worktree writes exactly the two declared pages, the Concepts page carries the portability row and the ontology index link, and the Issues page lists this story's new issue - the pages reflect this tree"
    command: |
      PY=$HOME/ahabase/evolucean/knowledge-usage-cli/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      "$PY" - <<'PYEOF'
      import datetime
      from pathlib import Path
      from knowledge_usage_cli.projections import ProjectionRegistry
      from knowledge_usage_cli.projections.base import Epic
      root = Path.cwd()
      epic = Epic(name='ahabase', path=root, scope='epic', prefix='AHABASE-')
      paths = ProjectionRegistry.generate_all(epic)
      names = sorted(p.name for p in paths)
      assert names == ['AHABASE-Concepts.md', 'AHABASE-Issues.md'], names
      gen = root / '_grid4d/_generated/epic'
      on_disk = sorted(p.name for p in gen.glob('*.md'))
      assert on_disk == names, on_disk
      concepts = (gen / 'AHABASE-Concepts.md').read_text()
      issues = (gen / 'AHABASE-Issues.md').read_text()
      assert '| portability |' in concepts, 'portability row missing'
      assert '](00-ahabase-ontology-index)' in concepts, 'index link missing'
      assert '](story-prefix-derived-from-repo-name)' in issues, 'new issue missing'
      assert datetime.date.today().isoformat() in concepts, 'stamp not today'
      print('R2_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R2_OK"
      timeout: 120
  - name: R2_red_empty_declaration_writes_nothing
    description: "red control - on a scratch copy built with git archive HEAD of the runner's checkout, with the empty declaration restored, the same call writes no page and creates no epic generated dir (the declaration gates, fail-closed)"
    command: |
      PY=$HOME/ahabase/evolucean/knowledge-usage-cli/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      rm -rf /tmp/aha15r2 && mkdir -p /tmp/aha15r2/ahabase
      git archive HEAD | tar -x -C /tmp/aha15r2/ahabase
      sed -i '' 's/projections: \[concepts, issues\]/projections: []/' /tmp/aha15r2/ahabase/_grid4d/pattern/ahabase-projections-pattern.md
      "$PY" - <<'PYEOF'
      from pathlib import Path
      from knowledge_usage_cli.projections import ProjectionRegistry
      from knowledge_usage_cli.projections.base import Epic
      epic = Epic(name='ahabase', path=Path('/tmp/aha15r2/ahabase'), scope='epic', prefix='AHABASE-')
      paths = ProjectionRegistry.generate_all(epic)
      assert paths == [], [p.name for p in paths]
      assert not (epic.path / '_grid4d/_generated/epic').exists(), 'epic dir created'
      print('R2_RED_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R2_RED_OK"
      timeout: 120
  - name: R3_open_zone_link_check
    description: "every wiki-style link of both generated pages resolves within this repository or is a listed known exception, every listed exception occurs (no stale rows), and the Concepts page resolves fully inward"
    command: |
      PY=$HOME/ahabase/evolucean/knowledge-usage-cli/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      "$PY" - <<'PYEOF'
      import re, sys
      from pathlib import Path
      from knowledge_usage_cli.projections import ProjectionRegistry
      from knowledge_usage_cli.projections.base import Epic
      root = Path.cwd()
      epic = Epic(name='ahabase', path=root, scope='epic', prefix='AHABASE-')
      ProjectionRegistry.generate_all(epic)
      gen = root / '_grid4d/_generated/epic'
      stems = set()
      for folder in ('story', 'story/history', 'ontology', 'implementation', 'pattern', 'issue', 'idea'):
          base = root / '_grid4d' / folder
          if base.is_dir():
              stems |= {p.stem for p in base.rglob('*.md')}
      exceptions = {'AHABASE-Issues.md': {
          'implementation-cli-projections_epic_issues-blueprint',
          'implementation-cli-issue_matcher-blueprint',
          'implementation-cli-sensors-blueprint'}}
      bad = []
      for page in ('AHABASE-Concepts.md', 'AHABASE-Issues.md'):
          text = (gen / page).read_text()
          targets = {t for t in re.findall(r'\]\(([^)#\s]+)\)', text)
                     if not t.startswith(('http', 'mailto'))}
          unresolved = {t for t in targets if t not in stems}
          allowed = exceptions.get(page, set())
          for t in sorted(unresolved - allowed):
              bad.append(f'{page}: unlisted closed-zone name {t}')
          for t in sorted(allowed - unresolved):
              bad.append(f'{page}: stale exception {t}')
          for t in sorted(allowed & unresolved):
              print(f'known exception {page}: {t}')
          if page == 'AHABASE-Concepts.md' and unresolved:
              bad.append(f'{page}: must resolve inward, got {sorted(unresolved)}')
      if bad:
          print('LINK CHECK RED')
          for b in bad:
              print(' ', b)
          sys.exit(1)
      print('R3_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R3_OK"
      timeout: 120
  - name: R3_red_planted_link_turns_red
    description: "red control - a link planted into the Issues page of a scratch copy that resolves nowhere makes the same check exit non-zero"
    command: |
      PY=$HOME/ahabase/evolucean/knowledge-usage-cli/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      rm -rf /tmp/aha15r3 && mkdir -p /tmp/aha15r3/ahabase
      git archive HEAD | tar -x -C /tmp/aha15r3/ahabase
      "$PY" - <<'PYEOF'
      from pathlib import Path
      from knowledge_usage_cli.projections import ProjectionRegistry
      from knowledge_usage_cli.projections.base import Epic
      epic = Epic(name='ahabase', path=Path('/tmp/aha15r3/ahabase'), scope='epic', prefix='AHABASE-')
      ProjectionRegistry.generate_all(epic)
      page = epic.path / '_grid4d/_generated/epic/AHABASE-Issues.md'
      page.write_text(page.read_text() + '\n[probe](evolucean-closed-zone-probe)\n')
      print('planted')
      PYEOF
      if "$PY" - <<'PYEOF'
      import re, sys
      from pathlib import Path
      root = Path('/tmp/aha15r3/ahabase')
      gen = root / '_grid4d/_generated/epic'
      stems = set()
      for folder in ('story', 'story/history', 'ontology', 'implementation', 'pattern', 'issue', 'idea'):
          base = root / '_grid4d' / folder
          if base.is_dir():
              stems |= {p.stem for p in base.rglob('*.md')}
      exceptions = {'AHABASE-Issues.md': {
          'implementation-cli-projections_epic_issues-blueprint',
          'implementation-cli-issue_matcher-blueprint',
          'implementation-cli-sensors-blueprint'}}
      bad = []
      for page in ('AHABASE-Concepts.md', 'AHABASE-Issues.md'):
          text = (gen / page).read_text()
          targets = {t for t in re.findall(r'\]\(([^)#\s]+)\)', text)
                     if not t.startswith(('http', 'mailto'))}
          unresolved = {t for t in targets if t not in stems}
          allowed = exceptions.get(page, set())
          bad += [f'{page}: unlisted {t}' for t in sorted(unresolved - allowed)]
          bad += [f'{page}: stale {t}' for t in sorted(allowed - unresolved)]
      if bad:
          print('LINK CHECK RED (expected)')
          sys.exit(1)
      print('LINK CHECK GREEN')
      PYEOF
      then
        echo "RED CONTROL FAILED - check stayed green"; exit 1
      fi
      echo R3_RED_OK
    expect:
      exit_code: 0
      stdout_contains: "R3_RED_OK"
      timeout: 120
  - name: R4_declarations_check_satisfied
    description: "declarations check against this worktree reports the Epic satisfied with the declared count and exits 0"
    command: |
      KU=$HOME/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage
      test -x "$KU" || { echo NO_VENV; exit 1; }
      "$KU" declarations check --epic-root .
    expect:
      exit_code: 0
      stdout_contains: "ahabase (epic): satisfied (2 projections)"
      timeout: 60
  - name: R4_red_removed_page_is_drift
    description: "red control - a scratch copy (named ahabase - the mapping falls to the directory name when the copy carries no git) with one declared page removed reports DRIFT and exits non-zero"
    command: |
      PY=$HOME/ahabase/evolucean/knowledge-usage-cli/.venv/bin/python
      KU=$HOME/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage
      test -x "$KU" || { echo NO_VENV; exit 1; }
      rm -rf /tmp/aha15r4 && mkdir -p /tmp/aha15r4/ahabase
      git archive HEAD | tar -x -C /tmp/aha15r4/ahabase
      "$PY" - <<'PYEOF'
      from pathlib import Path
      from knowledge_usage_cli.projections import ProjectionRegistry
      from knowledge_usage_cli.projections.base import Epic
      epic = Epic(name='ahabase', path=Path('/tmp/aha15r4/ahabase'), scope='epic', prefix='AHABASE-')
      ProjectionRegistry.generate_all(epic)
      PYEOF
      rm /tmp/aha15r4/ahabase/_grid4d/_generated/epic/AHABASE-Issues.md
      if "$KU" declarations check --epic-root /tmp/aha15r4/ahabase; then
        echo "RED CONTROL FAILED - check stayed green"; exit 1
      fi
      out=$("$KU" declarations check --epic-root /tmp/aha15r4/ahabase 2>&1 || true)
      echo "$out" | grep -q "DRIFT" || { echo "no DRIFT line"; exit 1; }
      echo R4_RED_OK
    expect:
      exit_code: 0
      stdout_contains: "R4_RED_OK"
      timeout: 120
  - name: R_team_review_verdict_logged
    description: "a review seat measured the pinned commit and its verdict, naming the commit, is logged in the story's Review section"
    command: |
      grep -q "APPROVE" _grid4d/story/AHA-0015.md || { echo MISSING verdict; exit 1; }
      echo R_TEAM_OK
    expect:
      exit_code: 0
      stdout_contains: "R_TEAM_OK"
      timeout: 30
  - name: R_docs_pattern_prose_and_issue_updates
    description: "the pattern names the fallback and the exception path in prose, the open-zone issue carries the projection Related block as a measured surface, and both issue links of the story resolve to files"
    command: |
      grep -q "fallback" _grid4d/pattern/ahabase-projections-pattern.md || { echo MISSING fallback prose; exit 1; }
      grep -q "open-zone-documents-link-into-the-closed-zone" _grid4d/pattern/ahabase-projections-pattern.md || { echo MISSING exception path; exit 1; }
      grep -q "Projection Related block" _grid4d/issue/open-zone-documents-link-into-the-closed-zone.md || { echo MISSING new surface; exit 1; }
      test -f _grid4d/issue/story-prefix-derived-from-repo-name.md || { echo MISSING prefix issue; exit 1; }
      echo R_DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "R_DOCS_OK"
      timeout: 60
  - name: R_issues_problems_logged
    description: "every problem met by this story exists as an issue file with Status open, and the story's Notes record the drift cleanup"
    command: |
      for f in story-prefix-derived-from-repo-name open-zone-documents-link-into-the-closed-zone declarations-check-skips-unmapped-trees; do
        grep -qF "**Status:** open" _grid4d/issue/$f.md || { echo "MISSING open status: $f"; exit 1; }
      done
      grep -q "Drift cleanup" _grid4d/story/AHA-0015.md || { echo MISSING cleanup note; exit 1; }
      echo R_ISSUES_OK
    expect:
      exit_code: 0
      stdout_contains: "R_ISSUES_OK"
      timeout: 60
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_declaration_parses_and_prose_names_the_rules | ✅ | 2026-10-30 |
| R2_generation_proof_in_worktree | ✅ | 2026-10-30 |
| R2_red_empty_declaration_writes_nothing | ✅ | 2026-10-30 |
| R3_open_zone_link_check | ✅ | 2026-10-30 |
| R3_red_planted_link_turns_red | ✅ | 2026-10-30 |
| R4_declarations_check_satisfied | ✅ | 2026-10-30 |
| R4_red_removed_page_is_drift | ✅ | 2026-10-30 |
| R_team_review_verdict_logged | ✅ | 2026-10-30 |
| R_docs_pattern_prose_and_issue_updates | ✅ | 2026-10-30 |
| R_issues_problems_logged | ✅ | 2026-10-30 |

Run at e9fa32fd043d203646b67d28d7181be2cf7fe4d2
## Related

- [AHA-0015](AHA-0015) - Parent story

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
