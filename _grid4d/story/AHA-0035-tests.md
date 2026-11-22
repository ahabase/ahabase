# AHA-0035-tests

> Test definition for AHA-0035 with one test per requirement.

## Design

One row per requirement leg, every leg standalone. The in-tree suites run with the development venv against `PYTHONPATH=$PWD/src`; the wheel-level legs (the consumer leg, the playground suite, the cold leg) pin `python3.13` - the system python is older than the package floor (`requires-python >= 3.11`). Both polarities live inside each row's population: the R1 suites carry the negative arms (no `_worktrees` and no injected ignore entry inside the Epic repository) beside the mint-path assertions; the R2 census row measures all seven folders present at the workspace root AND none inside a repository; the R3 grep row whitelists exactly the one negation pair that names the in-repo path (r2-seam) and asserts the workspace anchors positively. The R4 row is the standing public-push gate rehearsed on this story: it exports HEAD (never the dirty tree), builds the wheel in a fresh venv, installs it, witnesses that `import ahabase` resolves into that venv, and runs the full pytest suite from the exported tree - the passed count is recorded in the story document. The cold venv and every cache live OUTSIDE the exported tree: the containment suite builds an sdist from the tree during the run, and a git-archive extract carries no `.git` for hatchling to consult, so a stray directory inside the tree rides into that sdist - the containment guard caught exactly this in the first rehearsal shape (the venv at `$d/venv` inside `$d`), which is the guard doing its job.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_engine_suites_workspace_worktrees
    description: the rebased story suites pass - the mint path, the status message, corpse healing, and the parallel-mint family all resolve worktrees under <workspace>/_worktrees/<epic>/<STORY>, with the negative arms (no _worktrees directory, no injected .gitignore line inside the repository) rehearsed beside them
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_story.py tests/test_story_parallel.py'
    expect:
      exit_code: 0
  - name: R1_consumer_leg_wheel_mint
    description: the consumer leg through the built wheel - a story minted in a sandboxed HOME lands its worktree at <default-workspace>/_worktrees/demo/<STORY>, the repository inventories hold no .gitignore and no _worktrees entry, the completed worktree is removed, and the HOME snapshot outside the worktree home is unchanged
    command: AHABASE_LEG_PYTHON=python3.13 sh tests/consumer-leg.sh
    expect:
      exit_code: 0
  - name: R2_standard_folders_census
    description: the workspace suite and the config-door surface suite pass - all seven standard folders created at the workspace root (census in both polarities - every folder present, none inside an Epic repository), a deleted folder reappears with existing contents untouched, and the workspace door echoes the set in order
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_workspace.py tests/test_config_door.py'
    expect:
      exit_code: 0
  - name: R3_playground_no_inrepo_paths
    description: no playground document or test directs anyone to an in-repo _worktrees path - the only occurrences naming repos/<name>/_worktrees are the r2-seam negation pair, no cd walks into a repo-relative _worktrees, and the workspace anchors (the messy worktree, the scratch worktree home) are asserted positively
    command: 'inrepo=$(grep -rn "repos/[a-z]*/_worktrees" playground/ | grep -Ev ''an in-repo _worktrees|! -e .\$WS/repos/messy/_worktrees. \]'' || true) && [ -z "$inrepo" ] && ! grep -rnEq ''cd (\./|\.\./)?_worktrees'' playground/ && grep -q ''WORKTREE="\$WS/_worktrees/messy/MESSY-0001"'' playground/tests/r2-seam.sh && grep -q ''WTS="\$WS/_worktrees/scratch"'' playground/tests/r3-archetypes.sh'
    expect:
      exit_code: 0
  - name: R3_playground_suite_fresh_workspace
    description: the five playground rows run green end to end - r1/r2/r3 each bootstrap a throwaway workspace (the census with both polarities and the deleted-folder reappearing, the messy-repo seam, the five request archetypes), r4 runs its isolation arms against the live playground, r5 walks the gap sample over every census door both trees
    command: AHABASE_PYTHON=python3.13 sh playground/tests/r1-net.sh && AHABASE_PYTHON=python3.13 sh playground/tests/r2-seam.sh && AHABASE_PYTHON=python3.13 sh playground/tests/r3-archetypes.sh && AHABASE_PYTHON=python3.13 sh playground/tests/r4-arms.sh && AHABASE_PYTHON=python3.13 sh playground/tests/r5-comparison.sh
    expect:
      exit_code: 0
  - name: R4_cold_ci_built_export
    description: the standing public-push gate - HEAD exported to a clean tree (never the dirty worktree), wheel built in a fresh venv and installed into it, import ahabase witnessed to resolve inside that venv, and the full pytest suite run from the exported tree; the passed count is recorded in the story document
    command: 'd=$(mktemp -d) && mkdir "$d/tree" && git archive HEAD | tar -x -C "$d/tree" && python3.13 -m venv "$d/venv" && "$d/venv/bin/python" -m pip -q install --upgrade pip build hatchling pytest && "$d/venv/bin/python" -m build --wheel --no-isolation --outdir "$d/dist" "$d/tree" >/dev/null && "$d/venv/bin/python" -m pip -q install "$d"/dist/ahabase-*.whl && cd "$d/tree" && "$d/venv/bin/python" -c "import ahabase, sys; sys.exit(0 if ''/venv/'' in ahabase.__file__ else 1)" && PYTHONDONTWRITEBYTECODE=1 "$d/venv/bin/python" -m pytest -q -p no:cacheprovider; rc=$?; cd /; rm -rf "$d"; exit $rc'
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_engine_suites_workspace_worktrees | ✅ | 2026-11-22 |
| R1_consumer_leg_wheel_mint | ✅ | 2026-11-22 |
| R2_standard_folders_census | ✅ | 2026-11-22 |
| R3_playground_no_inrepo_paths | ✅ | 2026-11-22 |
| R3_playground_suite_fresh_workspace | ✅ | 2026-11-22 |
| R4_cold_ci_built_export | ✅ | 2026-11-22 |

Run at f93ed4bed325000482ded35658759af7385a3e06

## Related

- [AHA-0035](AHA-0035) - Parent story

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
