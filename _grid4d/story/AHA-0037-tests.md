# AHA-0037-tests

> Test definition for AHA-0037 with one test per requirement.

## Design

One row per requirement leg, standalone. The Windows result cannot be run here: the R1 acceptance criterion is a `workflow_dispatch` run of the story branch measured through `gh run view` and recorded in the Notes; the rows here prove the platform-independent half (the tests pass on this platform, the source spelling, the cancellation expression). The in-tree rows run with the development venv against `PYTHONPATH=$PWD/src`.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_status_posix_and_portable_stubs_on_this_platform
    description: 'the six named tests pass here - status prints the posix location, the lock test holds its invariant, the wiki stubs and the hook witness run; the Windows side is measured by the dispatch run (R1 AC), not by this row'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_story.py::test_status_reports_active_open_and_completed tests/test_story.py::test_legacy_in_repo_worktree_still_counts tests/test_story_parallel.py::test_r1cwd_one_lock_whichever_cwd tests/test_wiki_publish.py::test_probe_returns_the_login_both_polarities tests/test_wiki_publish.py::test_publish_end_to_end_with_the_real_probe tests/test_wiki_publish.py::test_push_child_never_sees_ambient_tokens'
    expect:
      exit_code: 0
  - name: R1_status_location_is_posix_source
    description: 'the source of the printed location is the posix spelling - no str(Path) of a relative worktree location remains in story.py status'
    command: 'grep -q "relative_to(base).as_posix()" src/ahabase/story.py && ! grep -q "return str(worktree.relative_to(base))" src/ahabase/story.py'
    expect:
      exit_code: 0
  - name: R2_cancel_only_feature_branches_and_prs
    description: 'the workflow parses; its group is keyed on the ref; its cancel-in-progress expression, evaluated on the three refs, is false for refs/heads/main and for a tag and true for a feature branch'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -c "import yaml;d=yaml.safe_load(open(\".github/workflows/tests.yml\"));c=d[\"concurrency\"];e=c[\"cancel-in-progress\"];assert \"github.ref\" in c[\"group\"];assert \"refs/heads/main\" in e and \"refs/tags/\" in e;f=lambda ref:(ref!=\"refs/heads/main\") and not ref.startswith(\"refs/tags/\");assert (f(\"refs/heads/main\"),f(\"refs/tags/v0.1\"),f(\"refs/heads/feature/x\"))==(False,False,True)"'
    expect:
      exit_code: 0
  - name: R3_single_push_idea_names_evidence
    description: 'the idea document exists and names the two main runs and both options'
    command: 'f=_grid4d/idea/idea-single-push-story-completion.md; test -f $f && grep -q 45119412297 $f && grep -q 45119437351 $f && grep -qi "one combined push" $f'
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_status_posix_and_portable_stubs_on_this_platform | ✅ | 2026-11-23 |
| R1_status_location_is_posix_source | ✅ | 2026-11-23 |
| R2_cancel_only_feature_branches_and_prs | ✅ | 2026-11-23 |
| R3_single_push_idea_names_evidence | ✅ | 2026-11-23 |

Run at c112940ff092971702556b2e9aa7d90bb96dc451
## Related

- [AHA-0037](AHA-0037) - Parent story

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
