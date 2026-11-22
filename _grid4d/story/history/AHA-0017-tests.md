# AHA-0017-tests

> Test definition for AHA-0017 with one test per requirement.

## Design

Test requirements for AHA-0017. One test per requirement. This is a documentation-only story, so every row measures the tree and the story's own git delta with plain shell, git and python3 - no venv, no package import. The scope claims (R2: no ontology file touched, no subepic created; R4: adds only, every added knowledge file prefixed, no renames) are measured against the merge-base with main, which the rows compute themselves - the enforcement is the named git diff. R1's population claim has a red control: the same file-loop that holds on this tree must fail on a scratch copy missing one idea file, so a broken loop cannot read green. R_team counts verdicts and distinct sessions and stays red until the review seats have spoken (the total is seat-dependent by design). The rows are the macOS lane (system python3, BSD-tolerant shell).

## Definition

```yaml
pipefail: true
tests:
  - name: R1_idea_population_exists_as_declared
    description: "the ten idea files exist as named, each open, each carrying its source date, and the landscape question is in the business-models idea"
    command: |
      files="idea-decision-driven-stories idea-decision-panels idea-progressive-capability-configuration idea-context-composition idea-cross-instance-context-view idea-pattern-verification idea-team-roles-and-progress idea-stop-status-unification idea-knowledge-browsing-obsidian idea-ahabase-foundation-roadmap"
      for f in $files; do
        p="_grid4d/idea/$f.md"
        test -f "$p" || { echo "MISSING $f"; exit 1; }
        grep -q '^\*\*Status:\*\* open' "$p" || { echo "NOT OPEN $f"; exit 1; }
        grep -q '2026-10-31' "$p" || { echo "NO SOURCE DATE $f"; exit 1; }
      done
      grep -q 'Open question: core or landscape' _grid4d/idea/open-source-business-models.md || { echo MISSING_LANDSCAPE; exit 1; }
      echo R1_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_OK"
      timeout: 60
  - name: R1_red_population_loop_fails_on_a_missing_file
    description: "red control - the same population loop on a scratch copy with one idea file removed fails; the green row cannot come from a broken loop"
    command: |
      rm -rf /tmp/aha17r1 && mkdir -p /tmp/aha17r1/_grid4d
      cp -R _grid4d/idea /tmp/aha17r1/_grid4d/
      rm /tmp/aha17r1/_grid4d/idea/idea-pattern-verification.md
      files="idea-decision-driven-stories idea-decision-panels idea-progressive-capability-configuration idea-context-composition idea-cross-instance-context-view idea-pattern-verification idea-team-roles-and-progress idea-stop-status-unification idea-knowledge-browsing-obsidian idea-ahabase-foundation-roadmap"
      rc=0
      root=/tmp/aha17r1
      for f in $files; do test -f "$root/_grid4d/idea/$f.md" || rc=1; done
      test "$rc" -eq 1 || { echo RED_DID_NOT_FIRE; exit 1; }
      echo R1_RED_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_RED_OK"
      timeout: 60
  - name: R2_rules_recorded_and_scope_held
    description: "the ontology-shape rule with its admission clause is in the Epic identity, the target structure with its executor is in the architecture blueprint, and the story's delta touches no ontology file and creates no subepic"
    command: |
      grep -q '^- \*\*Ontology shape\*\* (Human, 2026-10-31)' _grid4d/story/AHABASE.md || { echo MISSING_RULE; exit 1; }
      grep -q 'robust, minimal and needed by already-agreed implementation' _grid4d/story/AHABASE.md || { echo MISSING_ADMISSION; exit 1; }
      grep -q '^## Ontology shape$' _grid4d/implementation/implementation-ahabase-architecture-blueprint.md || { echo MISSING_SECTION; exit 1; }
      grep -q 'one follow-up story' _grid4d/implementation/implementation-ahabase-architecture-blueprint.md || { echo MISSING_EXECUTOR; exit 1; }
      base=$(git merge-base HEAD main)
      touched=$(git diff --name-only "$base" HEAD -- _grid4d/ontology/)
      test -z "$touched" || { echo "ONTOLOGY_TOUCHED: $touched"; exit 1; }
      created=$(git diff --name-only "$base" HEAD | grep '^_grid4d/subepic/' || true)
      test -z "$created" || { echo "SUBEPIC_CREATED: $created"; exit 1; }
      echo R2_OK
    expect:
      exit_code: 0
      stdout_contains: "R2_OK"
      timeout: 60
  - name: R3_roadmap_extract_reconciled
    description: "the roadmap extract links all seventeen stories in its Done table, carries the re-derived Next table, exactly thirteen capability rows in its inventory, and the absorbed release mechanics"
    command: |
      python3 - <<'PYEOF'
      from pathlib import Path
      import re
      t = Path('_grid4d/idea/idea-ahabase-foundation-roadmap.md').read_text()
      done = re.search(r'## Done\n\n(.*?)\n## Next', t, re.S).group(1)
      for i in range(1, 18):
          assert f'AHA-{i:04d}' in done, f'AHA-{i:04d} missing from Done'
      assert '## Next, in order' in t
      inv = re.search(r'## Capability inventory\n\n(.*?)\n## Related', t, re.S).group(1)
      rows = [l for l in inv.splitlines()
              if l.startswith('| ') and not l.startswith('| Capab') and '---' not in l]
      assert len(rows) == 13, rows
      assert 'Trusted Publishing' in t and 'TestPyPI first' in t, 'release mechanics'
      print('R3_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R3_OK"
      timeout: 60
  - name: R4_prefix_convention_recorded_and_held
    description: "the naming rule is in the Epic identity; every knowledge file this story added under idea/ or issue/ carries its prefix; nothing under idea/ or issue/ was deleted (no renames)"
    command: |
      grep -q '^- \*\*Knowledge file naming\*\* (Human, 2026-10-31)' _grid4d/story/AHABASE.md || { echo MISSING_CONVENTION; exit 1; }
      base=$(git merge-base HEAD main)
      added=$(git diff --diff-filter=A --name-only "$base" HEAD -- _grid4d/idea/ _grid4d/issue/ || true)
      test -n "$added" || { echo NOTHING_ADDED; exit 1; }
      bad=$(printf '%s' "$added" | grep -Ev '/(idea|issue)-' || true)
      test -z "$bad" || { echo "UNPREFIXED: $bad"; exit 1; }
      deleted=$(git diff --diff-filter=D --name-only "$base" HEAD -- _grid4d/idea/ _grid4d/issue/ || true)
      test -z "$deleted" || { echo "RENAMED_OR_DELETED: $deleted"; exit 1; }
      echo R4_OK
    expect:
      exit_code: 0
      stdout_contains: "R4_OK"
      timeout: 60
  - name: R_team_review_verdict_logged
    description: "review seats measured the pinned commit: two APPROVE rows in the story's Review section, naming the commit, from two different sessions"
    command: |
      n=$(grep -c '^- \*\*APPROVE' _grid4d/story/AHA-0017.md || true)
      test "$n" -ge 2 || { echo "MISSING verdicts: $n"; exit 1; }
      named=$(grep '^- \*\*APPROVE' _grid4d/story/AHA-0017.md | grep -c 'at [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]' || true)
      test "$named" -eq "$n" || { echo "VERDICT_WITHOUT_COMMIT: $named/$n"; exit 1; }
      seats=$(grep '^- \*\*APPROVE' _grid4d/story/AHA-0017.md | grep -o 'session [0-9a-f]*' | sort -u | wc -l | tr -d ' ')
      test "$seats" -ge 2 || { echo "SINGLE SEAT: $seats"; exit 1; }
      echo R_TEAM_OK
    expect:
      exit_code: 0
      stdout_contains: "R_TEAM_OK"
      timeout: 30
  - name: R_docs_every_decision_written_where_it_is_read
    description: "each rule this story decided lives at its named home: the two identity rules, the blueprint's Ontology shape section with the safe set, and the roadmap's decisions block"
    command: |
      grep -q '^- \*\*Ontology shape\*\* (Human, 2026-10-31)' _grid4d/story/AHABASE.md || { echo IDENTITY_SHAPE; exit 1; }
      grep -q '^- \*\*Knowledge file naming\*\* (Human, 2026-10-31)' _grid4d/story/AHABASE.md || { echo IDENTITY_NAMING; exit 1; }
      grep -q 'Moves to the first subepic' _grid4d/implementation/implementation-ahabase-architecture-blueprint.md || { echo BLUEPRINT_SAFE_SET; exit 1; }
      grep -q '## Decisions this roadmap carries' _grid4d/idea/idea-ahabase-foundation-roadmap.md || { echo ROADMAP_DECISIONS; exit 1; }
      echo R_DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "R_DOCS_OK"
      timeout: 60
  - name: R_issues_added_issue_files_carry_the_prefix
    description: "every issue file this story adds under issue/ carries the issue- prefix (vacuously green while the story met no unlogged problem)"
    command: |
      base=$(git merge-base HEAD main)
      added=$(git diff --diff-filter=A --name-only "$base" HEAD -- _grid4d/issue/ || true)
      bad=$(printf '%s' "$added" | grep -Ev '/issue-' || true)
      test -z "$bad" || { echo "UNPREFIXED_ISSUE: $bad"; exit 1; }
      echo R_ISSUES_OK
    expect:
      exit_code: 0
      stdout_contains: "R_ISSUES_OK"
      timeout: 60
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_idea_population_exists_as_declared | ✅ | 2026-10-31 |
| R1_red_population_loop_fails_on_a_missing_file | ✅ | 2026-10-31 |
| R2_rules_recorded_and_scope_held | ✅ | 2026-10-31 |
| R3_roadmap_extract_reconciled | ✅ | 2026-10-31 |
| R4_prefix_convention_recorded_and_held | ✅ | 2026-10-31 |
| R_team_review_verdict_logged | ✅ | 2026-10-31 |
| R_docs_every_decision_written_where_it_is_read | ✅ | 2026-10-31 |
| R_issues_added_issue_files_carry_the_prefix | ✅ | 2026-10-31 |

Run at 7267ed44b69b98b714517b55c822293915cb1c74
## Related

- [AHA-0017](AHA-0017) - Parent story

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
