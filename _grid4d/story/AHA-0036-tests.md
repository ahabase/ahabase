# AHA-0036-tests

> Test definition for AHA-0036 with one test per requirement.

## Design

One row per requirement leg, every leg standalone, both polarities inside each row's population. The in-tree suites run with the development venv against `PYTHONPATH=$PWD/src`. The parity row is the port's anchor: the golden mirror under `tests/fixtures/wiki-golden/` was captured 2026-11-22 (landing day) from a live method-side run of sync + generate over the fixture epic - the capture config and tree are embedded verbatim in `tests/test_wiki.py` (`FIXTURE_YAML`, `_fixture_epic`), so the row re-measures the same input the golden was produced from; the suite carries the golden, not a dependency on the method package (the cold leg and any consumer install have no method CLI to call). The capture also measured the preserved-directory quirk the port documents: an unquoted `dir/::` YAML key parses as `dir/:` and silently degrades to a skipped manual mapping - the row's config uses the quoted form and the blueprint documents the quoting. The publish rows run entirely against throwaway local bare `*.wiki.git` remotes with git isolated from the host (`GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_SYSTEM=/dev/null`, the commit identity from the environment) and the identity probe pinned at its seam (`account_of_safe_login` monkeypatched) - the fail-closed gate runs measured while the credential chain stays offline; no live GitHub anywhere in the suite. The R4 cold row is the standing public-push gate, the same command shape as AHA-0035's: HEAD exported (never the dirty tree), wheel built in a fresh venv, installed, `import ahabase` witnessed resolving into that venv, full pytest from the exported tree - the passed count recorded in the story document.

## Definition

```yaml
pipefail: true
tests:
  - name: R1_parity_with_method_side_golden
    description: 'the same fixture epic and config produce the same mirror the method side produced - file set and bytes (sync output + generated _Sidebar.md/Home.md), compared against the golden captured from a live method-side run (2026-11-22); the config exercises the full schema (mapped and null documents, a quoted preserved-directory pattern, auto_sync with flatten and structure, worktree sources, collapsible/separator/header_link/external sidebar sections, home content/blockquote/table/stats/image)'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_wiki.py::test_parity_with_the_method_side_golden'
    expect:
      exit_code: 0
  - name: R1_defaults_when_config_absent
    description: 'the other polarity - no yaml anywhere: the standard mirror path created (not demanded), nothing mapped and nothing copied, the default navigation rendered (# Wiki, no sections), no refusal anywhere in the run'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_wiki.py::test_defaults_when_the_config_is_absent'
    expect:
      exit_code: 0
  - name: R1_check_clean_both_polarities
    description: 'duplicates found (exit 3, ROOT/SUBFOLDER markers) and cleaned - the root copy wins over subfolder copies; with no root copy the newest subfolder copy is promoted (mtime decides, set by hand); after clean the check holds (exit 0)'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_wiki.py::test_check_and_clean_both_polarities'
    expect:
      exit_code: 0
  - name: R2_publish_end_to_end_delta_idempotent
    description: 'publishing a fixture mirror to a throwaway local bare remote succeeds end to end - the mirror becomes a clone, the delta commits, the push lands and the pushed tree equals the mirror (commit equality); a second run after a source change pushes only the delta (one new commit, the pushed bytes are the synced bytes); a third run with no change reports nothing to publish and commits nothing'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_wiki_publish.py::test_publish_end_to_end_and_delta_only'
    expect:
      exit_code: 0
  - name: R2_refuse_wrong_account
    description: 'the identity gate - the probe naming another account refuses (exit 1) with both names and the remedy naming the declaration, BEFORE anything is committed or pushed (no commit on the remote, not even a clone made)'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_wiki_publish.py::test_publish_refuses_the_wrong_account'
    expect:
      exit_code: 0
  - name: R2_refuse_unreachable_remote
    description: 'no wiki remote reachable - the fetch failure refuses (exit 1) with the remedy naming publish.remote, never a silent skip; nothing lands on the reachable remote'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_wiki_publish.py::test_publish_refuses_an_unreachable_remote'
    expect:
      exit_code: 0
  - name: R2_refuse_pending_plus_dirty
    description: 'the ambiguous mirror - a push-pending commit plus new uncommitted changes refuses (exit 1) with the remedy naming the manual push; nothing new lands on the remote'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_wiki_publish.py::test_publish_refuses_pending_plus_dirty'
    expect:
      exit_code: 0
  - name: R2_probe_fails_closed
    description: 'the probe itself - no gh on PATH refuses with the remedy (the real function, not the pinned seam), never a fallback that would skip the identity gate'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_wiki_publish.py::test_account_probe_fails_closed_without_gh'
    expect:
      exit_code: 0
  - name: R3_seam_surface_distinguishable_exits
    description: 'the seam the flip relies on - six subcommands present; the exits distinguish the outcomes (0 done, 1 refused with the remedy printed for an omitted name and an unknown epic, 2 usage, 3 duplicates found)'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_wiki.py::test_seam_surface_six_subcommands_distinguishable_exits'
    expect:
      exit_code: 0
  - name: R3_consumer_surface_grep_rows
    description: 'the consumer sees the capability - the playground names the door (sync) and the publish flow and the mirror path; the capabilities index carries wiki-projection, wiki-validation, wiki-publishing; the ontology index carries Wiki Projection'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_wiki.py::test_consumer_surface_names_the_door_and_the_flow'
    expect:
      exit_code: 0
  - name: R4_full_suite_including_the_plugin_guard
    description: 'the whole artifact suite green from the worktree source, the plugin guard included (no method literals anywhere in src/ahabase/*.py) - the passed count recorded in the story document'
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q'
    expect:
      exit_code: 0
  - name: R4_cold_ci_built_export
    description: 'the standing public-push gate - HEAD exported to a clean tree (never the dirty worktree), wheel built in a fresh venv and installed into it, import ahabase witnessed to resolve inside that venv, and the full pytest suite run from the exported tree; the passed count is recorded in the story document'
    command: 'd=$(mktemp -d) && mkdir "$d/tree" && git archive HEAD | tar -x -C "$d/tree" && python3.13 -m venv "$d/venv" && "$d/venv/bin/python" -m pip -q install --upgrade pip build hatchling pytest && "$d/venv/bin/python" -m build --wheel --no-isolation --outdir "$d/dist" "$d/tree" >/dev/null && "$d/venv/bin/python" -m pip -q install "$d"/dist/ahabase-*.whl && cd "$d/tree" && "$d/venv/bin/python" -c "import ahabase, sys; sys.exit(0 if ''/venv/'' in ahabase.__file__ else 1)" && PYTHONDONTWRITEBYTECODE=1 "$d/venv/bin/python" -m pytest -q -p no:cacheprovider; rc=$?; cd /; rm -rf "$d"; exit $rc'
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_parity_with_method_side_golden | ✅ | 2026-11-22 |
| R1_defaults_when_config_absent | ✅ | 2026-11-22 |
| R1_check_clean_both_polarities | ✅ | 2026-11-22 |
| R2_publish_end_to_end_delta_idempotent | ✅ | 2026-11-22 |
| R2_refuse_wrong_account | ✅ | 2026-11-22 |
| R2_refuse_unreachable_remote | ✅ | 2026-11-22 |
| R2_refuse_pending_plus_dirty | ✅ | 2026-11-22 |
| R2_probe_fails_closed | ✅ | 2026-11-22 |
| R3_seam_surface_distinguishable_exits | ✅ | 2026-11-22 |
| R3_consumer_surface_grep_rows | ✅ | 2026-11-22 |
| R4_full_suite_including_the_plugin_guard | ✅ | 2026-11-22 |
| R4_cold_ci_built_export | ✅ | 2026-11-22 |

Run at b969d490b3b3baa6a91ca5036715437c6eea829e

## Related

- [AHA-0036](AHA-0036) - Parent story

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
