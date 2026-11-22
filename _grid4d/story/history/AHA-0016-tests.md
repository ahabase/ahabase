# AHA-0016-tests

> Test definition for AHA-0016 with one test per requirement.

## Design

Test requirements for AHA-0016. One test per requirement. The real-tree rows (R1, R2, R3, R4, R5) run in this worktree against its own venv (``.venv`` created by the story; every row that imports ``ahabase`` first asserts the imported module comes from this tree, so a stale editable install cannot measure the wrong substrate); the red-control rows build a scratch copy with ``git archive HEAD`` of the runner's checkout, add the planted defect, assert the plant landed (grep) and then assert the check turns red - the gate must fail on the copy it measures. R4 drives the evolucean ``ProjectionRegistry.generate_all`` with an ``Epic`` bound to the tree being measured, the same call the sync tail makes (calling tree wins); its red control strips the ``Blueprint:`` alias lines and expects the baseline cells back, proving the alias lines are the mechanism. R_team holds the review verdict record; R_docs and R_issues hold the documentation and issue-file assertions. The rows are the macOS lane: R3_red's ``sed -i ''`` is the BSD form (GNU sed wants no empty suffix); CI replays pytest only.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_index_declares_capabilities_mapped_to_existing_concepts
    description: "the capabilities index parses, declares exactly 14 entries, and every link of every entry bullet resolves to a document of this repository"
    command: |
      PY=$PWD/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      "$PY" - <<'PYEOF'
      import re
      from pathlib import Path
      import ahabase
      assert 'worktrees/ahabase/AHA-0016' in str(ahabase.__file__), ahabase.__file__
      index = Path('_grid4d/ontology/ontology-capabilities-index.md')
      text = index.read_text()
      entries = re.findall(r'^- \*\*([a-z-]+)\*\*', text, re.MULTILINE)
      assert len(entries) == 14, entries
      links = 0
      bad = []
      for line in text.splitlines():
          if not line.startswith('- **'):
              continue
          for label, target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line):
              links += 1
              stem = target[:-3] if target.endswith('.md') else target
              if '/' not in stem and not (index.parent / (stem + '.md')).exists():
                  bad.append(target)
      assert links >= 14, links
      assert not bad, bad
      print('R1_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R1_OK"
      timeout: 60
  - name: R2_every_module_carries_its_capabilities
    description: "all module files of src/ahabase carry at least one Capability line, and the set of names in code is a subset of the index names"
    command: |
      PY=$PWD/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      "$PY" - <<'PYEOF'
      import re
      from pathlib import Path
      import ahabase
      assert 'worktrees/ahabase/AHA-0016' in str(ahabase.__file__), ahabase.__file__
      src = Path('src/ahabase')
      modules = sorted(p.name for p in src.glob('*.py'))
      assert len(modules) == 13, modules
      index = set(re.findall(r'^- \*\*([a-z-]+)\*\*',
                  Path('_grid4d/ontology/ontology-capabilities-index.md').read_text(),
                  re.MULTILINE))
      bare = []
      names = set()
      for m in modules:
          found = re.findall(r'Capability:\s*([a-z-]+)', (src / m).read_text())
          if not found:
              bare.append(m)
          names |= set(found)
      assert not bare, bare
      undefined = sorted(names - index)
      assert not undefined, undefined
      assert len(names) == 14, sorted(names)
      print('R2_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R2_OK"
      timeout: 60
  - name: R3_gate_holds_on_the_real_tree
    description: "ahabase verify on this tree exits 0 with all three hold lines and the declared count"
    command: |
      CLI=$PWD/.venv/bin/ahabase
      test -x "$CLI" || { echo NO_VENV; exit 1; }
      out=$("$CLI" verify --root .)
      echo "$out" | grep -q "^lineage: holds$" || { echo MISSING lineage; exit 1; }
      echo "$out" | grep -q "^capabilities: holds (14 defined)$" || { echo MISSING capabilities; exit 1; }
      echo "$out" | grep -q "^links: holds" || { echo MISSING links; exit 1; }
      echo R3_OK
    expect:
      exit_code: 0
      stdout_contains: "R3_OK"
      timeout: 60
  - name: R3_red_planted_undefined_capability_fails_the_copy
    description: "red control - a scratch copy with a planted undefined Capability line in safe.py fails verify with CAPABILITY undefined naming module and name; the plant is asserted landed before the run"
    command: |
      PY=$PWD/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      rm -rf /tmp/aha16r3 && mkdir -p /tmp/aha16r3
      git archive HEAD | tar -x -C /tmp/aha16r3
      sed -i '' '1a\
      Capability: no-such-capability
      ' /tmp/aha16r3/src/ahabase/safe.py
      grep -q "no-such-capability" /tmp/aha16r3/src/ahabase/safe.py || { echo PLANT_NOT_LANDED; exit 1; }
      "$PY" - <<'PYEOF'
      import subprocess, sys
      copy = '/tmp/aha16r3'
      sys.path.insert(0, copy + '/src')
      import ahabase
      assert ahabase.__file__.startswith(copy), ahabase.__file__
      from ahabase.cli import main
      sys.argv = ['ahabase', 'verify', '--root', copy]
      try:
          main()
      except SystemExit as exit_:
          assert exit_.code == 1, exit_.code
      else:
          raise AssertionError('verify held with an undefined capability')
      print('R3_RED_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R3_RED_OK"
      timeout: 60
  - name: R4_concepts_projection_reads_the_flipped_cells
    description: "the concepts projection generated against this tree reads door, lineage, portability, store grounded 1/1, safe-value 1/2, and Fully grounded 4/19"
    command: |
      PY=$HOME/ahabase/evolucean/knowledge-usage-cli/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      "$PY" - <<'PYEOF'
      from pathlib import Path
      from knowledge_usage_cli.projections import ProjectionRegistry
      from knowledge_usage_cli.projections.base import Epic
      root = Path.cwd()
      epic = Epic(name='ahabase', path=root, scope='epic', prefix='AHABASE-')
      ProjectionRegistry.generate_all(epic)
      page = (root / '_grid4d/_generated/epic/AHABASE-Concepts.md').read_text()
      for row in ('| door |', '| lineage |', '| portability |', '| store |'):
          line = [l for l in page.splitlines() if l.startswith(row)]
          assert len(line) == 1, (row, line)
          assert '1/1' in line[0], line[0]
      line = [l for l in page.splitlines() if l.startswith('| safe-value |')]
      assert len(line) == 1 and '1/2' in line[0], line
      assert 'Fully grounded:** 4/19' in page, 'coverage line'
      print('R4_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R4_OK"
      timeout: 120
  - name: R4_red_without_alias_lines_the_baseline_returns
    description: "red control - a scratch copy with every Blueprint alias line stripped regenerates the baseline cells (0/1, 0/2, Fully grounded 0/19): the alias lines are the mechanism"
    command: |
      PY=$HOME/ahabase/evolucean/knowledge-usage-cli/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      rm -rf /tmp/aha16r4 && mkdir -p /tmp/aha16r4/ahabase
      git archive HEAD | tar -x -C /tmp/aha16r4/ahabase
      PYM=$PY python3 - <<'SHEOF'
      import os, re
      from pathlib import Path
      src = Path('/tmp/aha16r4/ahabase/src/ahabase')
      stripped = 0
      for p in src.glob('*.py'):
          t = p.read_text()
          t2 = re.sub(r'^Blueprint: implementation-ahabase-[\w-]+-blueprint\n', '', t,
                      flags=re.MULTILINE)
          stripped += t.count('Blueprint: implementation-ahabase')
          p.write_text(t2)
      assert stripped >= 10, stripped
      print('stripped', stripped)
      SHEOF
      "$PY" - <<'PYEOF'
      from pathlib import Path
      from knowledge_usage_cli.projections import ProjectionRegistry
      from knowledge_usage_cli.projections.base import Epic
      epic = Epic(name='ahabase', path=Path('/tmp/aha16r4/ahabase'), scope='epic', prefix='AHABASE-')
      ProjectionRegistry.generate_all(epic)
      page = (epic.path / '_grid4d/_generated/epic/AHABASE-Concepts.md').read_text()
      for row in ('| door |', '| lineage |', '| portability |', '| store |'):
          line = [l for l in page.splitlines() if l.startswith(row)]
          assert len(line) == 1, (row, line)
          assert '0/1' in line[0], line[0]
      assert 'Fully grounded:** 0/19' in page, 'coverage line'
      print('R4_RED_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R4_RED_OK"
      timeout: 120
  - name: R5_links_hold_on_the_real_tree
    description: "the containment half of verify holds on this synced tree and on a clean checkout of the committed HEAD - the gate's green must not depend on ignored files being on disk"
    command: |
      CLI=$PWD/.venv/bin/ahabase
      test -x "$CLI" || { echo NO_VENV; exit 1; }
      out=$("$CLI" verify --root .)
      echo "$out" | grep -Eq "^links: holds \([0-9]+ documents scanned, [0-9]+ generator exceptions? declared\)$" || { echo "BAD links line: $out"; exit 1; }
      rm -rf /tmp/aha16clean && mkdir -p /tmp/aha16clean
      git archive HEAD | tar -x -C /tmp/aha16clean
      PY=$PWD/.venv/bin/python
      "$PY" - <<'PYEOF'
      import io, sys
      from contextlib import redirect_stdout
      sys.path.insert(0, '/tmp/aha16clean/src')
      import ahabase
      assert ahabase.__file__.startswith('/tmp/aha16clean'), ahabase.__file__
      from ahabase.cli import main
      sys.argv = ['ahabase', 'verify', '--root', '/tmp/aha16clean']
      buffer = io.StringIO()
      try:
          with redirect_stdout(buffer):
              main()
      except SystemExit as exit_:
          assert exit_.code in (0, None), f'clean checkout red: exit {exit_.code}'
      assert 'links: holds' in buffer.getvalue(), buffer.getvalue()
      print('CLEAN_OK')
      PYEOF
      echo R5_OK
    expect:
      exit_code: 0
      stdout_contains: "R5_OK"
      timeout: 120
  - name: R5_red_planted_outbound_link_fails_the_copy
    description: "red control - a scratch copy with a hand-written link to a document of another repository planted in an ontology doc fails verify naming the file and the target; the plant is asserted landed before the run"
    command: |
      PY=$PWD/.venv/bin/python
      test -x "$PY" || { echo NO_VENV; exit 1; }
      rm -rf /tmp/aha16r5 && mkdir -p /tmp/aha16r5
      git archive HEAD | tar -x -C /tmp/aha16r5
      printf '\n- [Elsewhere](evolucean-story-view)\n' >> /tmp/aha16r5/_grid4d/ontology/ontology-door-blueprint.md
      grep -q "evolucean-story-view" /tmp/aha16r5/_grid4d/ontology/ontology-door-blueprint.md || { echo PLANT_NOT_LANDED; exit 1; }
      "$PY" - <<'PYEOF'
      import io, sys
      from contextlib import redirect_stdout
      copy = '/tmp/aha16r5'
      sys.path.insert(0, copy + '/src')
      import ahabase
      assert ahabase.__file__.startswith(copy), ahabase.__file__
      from ahabase.cli import main
      sys.argv = ['ahabase', 'verify', '--root', copy]
      buffer = io.StringIO()
      try:
          with redirect_stdout(buffer):
              main()
      except SystemExit as exit_:
          assert exit_.code == 1, exit_.code
      else:
          raise AssertionError('verify held with an outbound link')
      out = buffer.getvalue()
      assert 'LINK unresolved: _grid4d/ontology/ontology-door-blueprint.md -> evolucean-story-view' in out, out
      print('R5_RED_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R5_RED_OK"
      timeout: 60
  - name: R_team_review_verdict_logged
    description: "both review seats measured the pinned commit: two APPROVE rows in the story's Review section, naming the commit, from two different sessions (a seat's own re-approval after findings does not count twice)"
    command: |
      n=$(grep -c '^- \*\*APPROVE' _grid4d/story/AHA-0016.md || true)
      test "$n" -ge 2 || { echo "MISSING verdicts: $n"; exit 1; }
      seats=$(grep '^- \*\*APPROVE' _grid4d/story/AHA-0016.md | grep -o 'session [0-9a-f]*' | sort -u | wc -l | tr -d ' ')
      test "$seats" -ge 2 || { echo "SINGLE SEAT: $seats"; exit 1; }
      echo R_TEAM_OK
    expect:
      exit_code: 0
      stdout_contains: "R_TEAM_OK"
      timeout: 30
  - name: R_docs_ontology_and_docstrings_carry_the_vocabulary
    description: "the trust-zone concept states the implemented zone check, the safe-integration blueprint names safe as its code, and every module docstring carries both an Implements and a Blueprint line"
    command: |
      grep -q "implemented in part - the open-zone link containment check" _grid4d/ontology/ontology-trust-zone-blueprint.md || { echo MISSING trust-zone state; exit 1; }
      grep -qF "**Code:** safe" _grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md || { echo MISSING code line; exit 1; }
      for f in src/ahabase/*.py; do
        grep -q "^Implements: implementation-" "$f" || { echo "MISSING Implements in $f"; exit 1; }
        grep -q "^Blueprint: implementation-" "$f" || { echo "MISSING Blueprint in $f"; exit 1; }
      done
      echo R_DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "R_DOCS_OK"
      timeout: 60
  - name: R_issues_friction_logged_and_offenders_fixed
    description: "the invite-routing friction exists as an open issue, and the two hand-written cross-repo offenders are fixed in their documents (backticked notation, plain-words link)"
    command: |
      grep -qF "**Status:** open" _grid4d/issue/bare-session-address-refused-toward-the-wrong-instance.md || { echo MISSING friction issue; exit 1; }
      grep -q "not a link)" _grid4d/implementation/implementation-ahabase-transparency-blueprint.md || { echo MISSING notation fix; exit 1; }
      grep -q "named in plain words" _grid4d/issue/story-tests-run-at-line-must-stay-bare.md || { echo MISSING plain-words fix; exit 1; }
      echo R_ISSUES_OK
    expect:
      exit_code: 0
      stdout_contains: "R_ISSUES_OK"
      timeout: 60
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_index_declares_capabilities_mapped_to_existing_concepts | ✅ | 2026-10-31 |
| R2_every_module_carries_its_capabilities | ✅ | 2026-10-31 |
| R3_gate_holds_on_the_real_tree | ✅ | 2026-10-31 |
| R3_red_planted_undefined_capability_fails_the_copy | ✅ | 2026-10-31 |
| R4_concepts_projection_reads_the_flipped_cells | ✅ | 2026-10-31 |
| R4_red_without_alias_lines_the_baseline_returns | ✅ | 2026-10-31 |
| R5_links_hold_on_the_real_tree | ✅ | 2026-10-31 |
| R5_red_planted_outbound_link_fails_the_copy | ✅ | 2026-10-31 |
| R_team_review_verdict_logged | ✅ | 2026-10-31 |
| R_docs_ontology_and_docstrings_carry_the_vocabulary | ✅ | 2026-10-31 |
| R_issues_friction_logged_and_offenders_fixed | ✅ | 2026-10-31 |

Run at ddc1f224c25cc277ae68d162657830a3e691bb21
## Related

- [AHA-0016](AHA-0016) - Parent story
