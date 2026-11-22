# AHA-0021-tests

> Test definition for AHA-0021 with one test per requirement.

## Design

Test requirements for AHA-0021. One test per requirement. Rows R1 and R3 are red until the door lands (the honest starting state); R2 and R4 green when their documents/tables exist.

## Definition

```yaml
tests:
  - name: R1_door_lands_importable
    description: The six contract surface functions import from the ahabase package as a library seam.
    command: PYTHONPATH=src python3 -c "from ahabase import get_workspace_dir, get_instance_root, load_settings, list_scope_holdings, get_data_dir, get_machine_id"
    expect:
      exit_code: 0
  - name: R2_six_checks_evidence_rows
    description: The story carries the six graduation-checks evidence table (one numbered row per check).
    command: test "$(grep -c '^| [1-6] |' _grid4d/story/AHA-0021.md)" = "6"
    expect:
      exit_code: 0
  - name: R3_surface_composition_guard
    description: Name-for-name surface composition guard (the census lesson - composition, not presence); every named function exists and is callable, none extra promised.
    command: PYTHONPATH=src python3 -c "import ahabase; surface = ['get_workspace_dir', 'get_instance_root', 'load_settings', 'list_scope_holdings', 'get_data_dir', 'get_machine_id']; missing = [s for s in surface if not callable(getattr(ahabase, s, None))]; assert not missing, missing"
    expect:
      exit_code: 0
  - name: R4_rollout_checklist_in_story
    description: The dossier Rollout section rides the story - the work channel stays explicitly UNMEASURED until measured, the lagging-instance invariant named.
    command: grep -q "UNMEASURED" _grid4d/story/AHA-0021.md && grep -q "lagging-instance" _grid4d/story/AHA-0021.md
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_door_lands_importable | ✅ | 2026-11-02 |
| R2_six_checks_evidence_rows | ✅ | 2026-11-02 |
| R3_surface_composition_guard | ✅ | 2026-11-02 |
| R4_rollout_checklist_in_story | ✅ | 2026-11-02 |

Run at 31ead8d173395ba763962e11659c12c51dfb5a95
Re-run provenance: checkpoint-2 close-out commit (one test row added - malformed settings - plus story/tests docs; source unchanged since 23465e2); full package suite 207 passed at this tree.

### Red controls (R3)

The repo suite `tests/test_config_door.py` (13 tests) carries the guard; each control was applied to the source, asserted landed by grep, demonstrated red, reverted (asserted by grep + clean diff), and the suite rerun green:

| Control | Mutation | Red result |
|---|---|---|
| Surface rename | `get_machine_id` -> `machine_id_mutant` in `src/ahabase/config.py` (aliased in `__init__.py` so the package import survives) | `test_surface_composition_name_for_name` red (module public set != the six) and `test_workspace_trio` red (AttributeError) - the composition, not just the import, is what guards |
| Wrong default | data-dir default segment `_data` -> `_datax_mutant` in `get_data_dir` | `test_data_dir_default_is_the_ahabase_layout` red |
| Swallowed parse | `load_settings` body wrapped in `try/except Exception: return {}` | `test_malformed_settings_is_a_loud_failure` red (Failed: DID NOT RAISE - the row added at checkpoint 2, deepseek seat: malformed was implemented but unguarded) |

After all three reverts: full package suite 207 passed (2026-11-02), `ahabase verify` holds (lineage, capabilities 17 defined, links 77 documents).

## Related

- [AHA-0021](AHA-0021) - Parent story

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
