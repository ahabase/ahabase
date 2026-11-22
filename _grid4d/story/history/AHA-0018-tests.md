# AHA-0018-tests

> Test definition for AHA-0018 with one test per requirement.

## Design

Test requirements for AHA-0018. One test per requirement, each measuring the tree and the story's git delta after execution, in plain shell, git and python3 (macOS lane, BSD-tolerant). The decided values are the Human's answers of 2026-10-31: the subepic's `StoryPrefix` is `AHA-SAFE` (the identity file keeps the subepic-name stem `AHABASE-SAFE.md`); the safe implementation blueprint moves with the concepts; projection stays Epic-level. R2 runs the package's own gates through the main tree's venv interpreter with the worktree's package on `PYTHONPATH` (`python -m ahabase`, the module door this story adds): the venv's `ahabase` binary is an editable install of the main tree and would run the pre-story code during the story, so the row pins the interpreter for its dependencies and carries the code under test itself; the same invocation then measures a clean clone of the worktree (the clone carries no venv of its own). The registry divergence check (`knowledge-usage doctor`) is run by the seat at execution and recorded in the Execution notes, not as a hard row. Scope claims (R5: exactly the safe set moves) are measured against the merge-base with main, which the rows compute themselves. R_team stays red until two APPROVE rows from two different sessions name their commits (the total is seat-dependent by design); its guard has the naming leg, the two-session leg, and the green path when both verdicts are in. The R3 row builds its mermaid fence at runtime (printf '\140\140\140' passed through an environment variable): a literal fence inside the Definition block would close the yaml fence for every shipped reader, which stops at the first fence pair and truncates the definition (the review seat's blocking finding, seq 4862).

## Definition

```yaml
pipefail: true
tests:
  - name: R1_ahabase_safe_subepic_exists_as_declared
    description: "the subepic identity declares StoryPrefix AHA-SAFE, the ten safe concept blueprints and the safe implementation blueprint live under the subepic and not at the Epic level, and the moves are git renames"
    command: |
      grep -q '^\*\*StoryPrefix:\*\* AHA-SAFE' _grid4d/subepic/ahabase-safe/story/AHABASE-SAFE.md || { echo MISSING_IDENTITY; exit 1; }
      for c in agent-guard consumer manifest output-watch reference rotation safe-value scan-finding shadow-run store; do
        test -f "_grid4d/subepic/ahabase-safe/ontology/ontology-$c-blueprint.md" || { echo "MISSING $c"; exit 1; }
        test ! -f "_grid4d/ontology/ontology-$c-blueprint.md" || { echo "STILL_EPIC $c"; exit 1; }
      done
      test -f _grid4d/subepic/ahabase-safe/implementation/implementation-ahabase-safe-blueprint.md || { echo MISSING_IMPL; exit 1; }
      test ! -f _grid4d/implementation/implementation-ahabase-safe-blueprint.md || { echo IMPL_STILL_EPIC; exit 1; }
      base=$(git merge-base HEAD main)
      moved=$(git diff --find-renames --diff-filter=R --name-only "$base" HEAD | wc -l | tr -d ' ')
      test "$moved" -ge 11 || { echo "NOT_RENAMES: $moved"; exit 1; }
      echo R1_OK
    expect:
      exit_code: 0
      stdout_contains: "R1_OK"
      timeout: 60
  - name: R2_gates_resolve_subepic_indexes
    description: "the package's verify passes in the worktree and in a clean clone of it, so the gates resolve concepts through the subepic index without the original tree"
    command: |
      VP=/Users/<user>/ahabase/ahabase/.venv/bin/python
      W=$PWD
      PYTHONPATH="$W/src" "$VP" -m ahabase verify --root . || { echo WORKTREE_VERIFY_FAILED; exit 1; }
      rm -rf /tmp/aha18r2 && git clone -q . /tmp/aha18r2 || { echo CLONE_FAILED; exit 1; }
      cd /tmp/aha18r2 && PYTHONPATH="$W/src" "$VP" -m ahabase verify --root . || { echo CLONE_VERIFY_FAILED; exit 1; }
      echo R2_OK
    expect:
      exit_code: 0
      stdout_contains: "R2_OK"
      timeout: 300
  - name: R3_maps_render_at_their_own_level
    description: "the Epic map carries every Epic-level concept including portability plus the subepic as one node and no safe concept detail; the subepic index carries its own detailed map"
    command: |
      f=$(printf '\140\140\140')
      FENCE="$f" python3 - <<'PYEOF'
      import os, re, pathlib
      fence = os.environ['FENCE']
      t = pathlib.Path('_grid4d/ontology/00-ahabase-ontology-index.md').read_text()
      blocks = re.findall(fence + r'mermaid\n(.*?)' + fence, t, re.S)
      assert blocks, 'no epic map'
      m = blocks[0].lower()
      assert 'portability' in m, 'no portability node'
      assert 'ahabase-safe' in m, 'no subepic node'
      assert 'safe-value' not in m and 'safe value' not in m, 'safe detail leaked into the epic map'
      s = pathlib.Path('_grid4d/subepic/ahabase-safe/ontology/00-ahabase-safe-ontology-index.md').read_text()
      sb = re.findall(fence + r'mermaid\n(.*?)' + fence, s, re.S)
      assert sb, 'no subepic map'
      assert 'store' in sb[0].lower(), 'no safe concept in the subepic map'
      print('R3_OK')
      PYEOF
    expect:
      exit_code: 0
      stdout_contains: "R3_OK"
      timeout: 60
  - name: R4_trust_zone_blueprint_six_zones
    description: "the amended blueprint names all six zones, the machine-receiver chain, the many-to-one TLP mapping, the documents-0-4 rule, and an Example section"
    command: |
      p=_grid4d/ontology/ontology-trust-zone-blueprint.md
      for z in '0 Public' '1 Users' '2 Shared' '3 Core' '4 Personal' '5 Vault'; do
        grep -q "$z" "$p" || { echo "MISSING_ZONE $z"; exit 1; }
      done
      grep -q 'machine receivers' "$p" || { echo MISSING_RECEIVER_CHAIN; exit 1; }
      grep -q 'many-to-one' "$p" || { echo MISSING_TLP_MAPPING; exit 1; }
      grep -q 'Documents occupy zones 0-4' "$p" || { echo MISSING_DOCUMENT_RULE; exit 1; }
      grep -q '^## Example' "$p" || { echo MISSING_EXAMPLES; exit 1; }
      echo R4_OK
    expect:
      exit_code: 0
      stdout_contains: "R4_OK"
      timeout: 60
  - name: R5_remaining_concepts_classified_nothing_else_moves
    description: "projection is classified stays Epic-level in the architecture blueprint, and exactly the eleven safe files (ten concepts plus the implementation blueprint) leave the Epic folders - no other deletion"
    command: |
      grep -q 'stays Epic-level' _grid4d/implementation/implementation-ahabase-architecture-blueprint.md || { echo MISSING_CLASSIFICATION; exit 1; }
      base=$(git merge-base HEAD main)
      git diff --no-renames --diff-filter=D --name-only "$base" HEAD | sort > /tmp/aha18deleted
      printf '%s\n' \
        _grid4d/implementation/implementation-ahabase-safe-blueprint.md \
        _grid4d/ontology/ontology-agent-guard-blueprint.md \
        _grid4d/ontology/ontology-consumer-blueprint.md \
        _grid4d/ontology/ontology-manifest-blueprint.md \
        _grid4d/ontology/ontology-output-watch-blueprint.md \
        _grid4d/ontology/ontology-reference-blueprint.md \
        _grid4d/ontology/ontology-rotation-blueprint.md \
        _grid4d/ontology/ontology-safe-value-blueprint.md \
        _grid4d/ontology/ontology-scan-finding-blueprint.md \
        _grid4d/ontology/ontology-shadow-run-blueprint.md \
        _grid4d/ontology/ontology-store-blueprint.md | sort > /tmp/aha18expected
      diff -u /tmp/aha18expected /tmp/aha18deleted || { echo UNEXPECTED_DELETIONS; exit 1; }
      echo R5_OK
    expect:
      exit_code: 0
      stdout_contains: "R5_OK"
      timeout: 60
  - name: R_team_review_verdict_logged
    description: "review seats measured the pinned commit: two APPROVE rows in the story's Review section, each naming its commit, from two different sessions"
    command: |
      n=$(grep -c '^- \*\*APPROVE' _grid4d/story/AHA-0018.md || true)
      test "$n" -ge 2 || { echo "APPROVE rows found: $n (need 2)"; exit 1; }
      named=$(grep '^- \*\*APPROVE' _grid4d/story/AHA-0018.md | grep -c 'at [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]' || true)
      test "$named" -eq "$n" || { echo "VERDICT_WITHOUT_COMMIT: $named/$n"; exit 1; }
      seats=$(grep '^- \*\*APPROVE' _grid4d/story/AHA-0018.md | grep -o 'session [0-9a-f]*' | sort -u | wc -l | tr -d ' ')
      test "$seats" -ge 2 || { echo "SINGLE SEAT: $seats"; exit 1; }
      echo R_TEAM_OK
    expect:
      exit_code: 0
      stdout_contains: "R_TEAM_OK"
      timeout: 30
  - name: R_docs_every_decision_at_its_home
    description: "each rule this story lands sits where it is read: the subepic named in the architecture blueprint, the classification list there too, and the amended zones in the trust-zone blueprint"
    command: |
      grep -q 'ahabase-safe' _grid4d/implementation/implementation-ahabase-architecture-blueprint.md || { echo BLUEPRINT_SUBEPIC; exit 1; }
      grep -q 'stays Epic-level' _grid4d/implementation/implementation-ahabase-architecture-blueprint.md || { echo BLUEPRINT_CLASSIFICATION; exit 1; }
      grep -q '5 Vault' _grid4d/ontology/ontology-trust-zone-blueprint.md || { echo TRUST_SIX_ZONES; exit 1; }
      echo R_DOCS_OK
    expect:
      exit_code: 0
      stdout_contains: "R_DOCS_OK"
      timeout: 60
  - name: R_issues_added_issue_files_carry_the_prefix
    description: "every issue file this story adds under issue/ carries the issue- prefix (vacuously green while the story meets no unlogged problem)"
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
| R1_ahabase_safe_subepic_exists_as_declared | ✅ | 2026-10-31 |
| R2_gates_resolve_subepic_indexes | ✅ | 2026-10-31 |
| R3_maps_render_at_their_own_level | ✅ | 2026-10-31 |
| R4_trust_zone_blueprint_six_zones | ✅ | 2026-10-31 |
| R5_remaining_concepts_classified_nothing_else_moves | ✅ | 2026-10-31 |
| R_team_review_verdict_logged | ✅ | 2026-10-31 |
| R_docs_every_decision_at_its_home | ✅ | 2026-10-31 |
| R_issues_added_issue_files_carry_the_prefix | ✅ | 2026-10-31 |

Run at 20ea49e1d74d9a7769e42cd998ce0c22a4472b7e
R1: 11 renames from the merge-base. R2: lineage holds, capabilities hold (14 defined), links hold (72 documents scanned, 7 generator exceptions declared - 71 until the issue file added at 6cc6c15) - in the worktree and in the clean clone both. R5: exactly 11 deletions, no other. R_issues: one issue file added at 6cc6c15 (the review seat's non-blocking observation), carrying the prefix. R_team: green - three APPROVE rows from three different sessions, each naming its commit (641903b1 at 6eae94d8, seq 4865; bd00df25 at 61d9be7, seq 4872; 85a6bfd8 at 61d9be7, seq 4873 - the quota filled at 4872, the third verdict answered the still-open request 4870 minutes later); the guard needs two, the record carries three. Table recorded by the shipped runner (`knowledge-usage test`) at this commit.

## Related

- [AHA-0018](AHA-0018) - Parent story

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
