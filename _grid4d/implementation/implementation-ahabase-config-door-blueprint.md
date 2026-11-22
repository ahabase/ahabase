# ahabase Config Door Implementation Blueprint

> The landed config/instance-state layer: the six-function library seam graduated from evolucean's CLI as the pilot graduation - the layer every other capability stands on.

**Implements:** [ontology-config-blueprint](ontology-config-blueprint)
**Stories:** [AHA-0021](AHA-0021), [AHA-0035](AHA-0035)
**Code:** config, cli_workspace, _yaml_unique
**Status:** landed 2026-11-02 (AHA-0021); the flip story in the method's repository repoints its consumers to this seam; AHA-0035 added the workspace folder set (additive, the frozen six-function seam unchanged)

## Overview

The graduation's Phase 1: the method's config/instance-state layer moved into the base as `ahabase.config`, so every method and future capability reads the same places through one seam. The door is workspace-level and epic-explicit - the six functions, three taking the epic as a required keyword, three needing no argument. This blueprint fixes the seam contract the method's flip story quotes, and records every departure from ported behavior.

## Rules

1. **Epic-explicit, required keyword** - `load_settings`, `get_data_dir`, `list_scope_holdings` take `epic` as a required keyword; no env-derived epic inside the door. Ambient epic ("which epic am I") pushed into consumers is the fail-open shape the landing rejected (checkpoint 1, 2026-11-02).
2. **Never-None roots** - `get_workspace_dir` and `get_instance_root` always return a path (`AHABASE_WORKSPACE` env, default `~/ahabase`); the ported `None` contract is removed at the door, the method's callers adapt at the flip.
3. **Settings convention (the door's own)** - `_config/<epic>-cli-settings.yml` under the workspace; precedence: `AHABASE_CONFIG` env (a settings file path, any epic, wins when the file exists) → the convention path → missing file is normal and reads `{}`; duplicated keys warn once and last-wins; `wikis_dir`, `workspace_dir`, `config_dir`, `data_dir` get `~` expanded. Nothing parameterized existed to port - the convention is new and says so.
4. **Data layout** - settings `data_dir` when set, else `<workspace>/_data/<epic>` (the ported default was the method product's own home directory and could not ride); a relative value anchors at the workspace root (correcting a ported latent bug: the settings expansion collapses a `./` prefix, so the ported relative-path test never fired and such a value silently landed in the process cwd); the dir is created on demand.
5. **Collab store does not move** - the collaboration store (journal, board, inbox, sessions) stays where the serving epic's data dir puts it; per-epic versus workspace-wide collab rooting is the collab capability's own landing to decide, recorded in [ontology-config-blueprint](ontology-config-blueprint).
6. **Epic is a name, not a path segment** - validated as `[A-Za-z0-9][A-Za-z0-9_-]*`; a path-shaped value is refused.
7. **Holdings are an allowlist** - `list_scope_holdings` returns named fields only, never the raw scope entry: a scope file is raw runtime state, and a blanket passthrough would let anything that ever lands there reach what renders it (the ported lesson: a field shipped by the write path but dropped here made liveness checks permanently wrong while a hand-built test entry masked it).
8. **The flip absorbs the blast radius at one wrapper** - the method's flip keeps one thin method-side wrapper defaulting `epic="evolucean"` for its 51 parameterless call sites, and its guard censuses call sites, not import lines: an import that resolves is not a call that reads the right file.
9. **The wrapper ports the settings `workspace_dir` preference** - the ported `get_workspace_dir` read the settings key first (live steering: a relocating instance sets it), while this door's frozen contract is env + default; the wrapper carries locate-then-override (the ported order) so post-flip behavior is identical. Checkpoint 2's gap finding (both resolutions agree today, so the divergence is invisible until an instance relocates); neither reopens the API shape.
10. **The project-fallback tail is settled consciously at the flip** - the ported precedence had a third step (a project config file, which exists in the source tree); the door reads `{}` when the workspace file is absent. Recorded recommendation: no project fallback in the wrapper - the door's contract is workspace file or `AHABASE_CONFIG` - with the flip measuring first whether that file's live content is read by any workspace-less layout (fresh checkout, CI, temp trees) before dropping it.
11. **The seven standard folders (AHA-0035)** - every workspace carries `_config`, `_data`, `_generated`, `_inbox`, `_temp`, `_wikis`, `_worktrees` at its root (the Human ruling 2026-11-22, the proven workspace topology): `ensure_standard_folders()` creates the set on demand, idempotently - a deleted folder reappears, existing contents are never touched - and no Epic repository ever receives any of the seven (the story worktree home is `<workspace>/_worktrees/<repo>`, never in-repo). The CLI door is `ahabase workspace ensure` (`cli_workspace`). Additive to the frozen six: the flip's quoted contract text is unchanged.

## Template

The seam contract, the text the method's flip story quotes verbatim (frozen at this door's first release):

```markdown
- **Type:** Python import (library seam), future CLI door `ahabase config` behind the one registry.
- **Surface:** `get_workspace_dir()`, `get_instance_root()`, `get_machine_id()` (workspace-level, no argument, never None) and `load_settings(*, epic)`, `get_data_dir(*, epic)`, `list_scope_holdings(*, epic)` (epic-explicit, required keyword) - re-exported from the `ahabase` package.
- **Settings convention:** `_config/<epic>-cli-settings.yml` under the workspace; precedence `AHABASE_CONFIG` env (a settings file path, any epic, wins when the file exists) -> the convention path -> missing file is normal and reads `{}`; duplicated keys warn once, last-wins; `wikis_dir`, `workspace_dir`, `config_dir`, `data_dir` get `~` expanded.
- **Data layout:** settings `data_dir` when set, else `<workspace>/_data/<epic>`; a relative value anchors at the workspace root; created on demand.
- **Collab store boundary:** the collaboration store stays where the serving epic's data dir puts it; per-epic versus workspace-wide rooting is the collab capability's landing to decide.
- **Floor:** the first ahabase release carrying the door (released tag; the flip pins `ahabase>=X`).
- **Custody boundary:** implementations move; story-scoped config and all per-instance data stay with the instance.
```

## Structure

| Module | Role |
|---|---|
| `src/ahabase/config.py` | the door: the six surface functions + the private helpers (`_settings_path`, `_stale_seconds`, `_scopes_dir`, `_expand_path`, `_check_epic`) and the AHA-0035 folder set (`STANDARD_FOLDERS`, `ensure_standard_folders`) |
| `src/ahabase/cli_workspace.py` | the `ahabase workspace ensure` door - the folder census as the consumer's idempotent act (AHA-0035) |
| `src/ahabase/_yaml_unique.py` | the duplicated-key-warns loader the settings load rides on (ported) |
| `src/ahabase/__init__.py` | re-exports the surface - the package seam |

| Function | Shape | Ported from |
|---|---|---|
| `get_workspace_dir()` | workspace root, never None | the method config facade (None contract removed) |
| `get_instance_root()` | the same resolution, ported second name | the method's snapshot config |
| `get_machine_id()` | the hostname | the method's agent config |
| `load_settings(*, epic)` | the epic's settings dict | the method config facade |
| `get_data_dir(*, epic)` | the epic's data dir, created on demand | the method config facade |
| `list_scope_holdings(*, epic)` | the sessions allowlist read with staleness | the method's scopes config |
| `ensure_standard_folders()` | the seven standard folders at the workspace root, created on demand, idempotent | new (AHA-0035, the Human ruling 2026-11-22) |

## Example

The suites that hold the rules measured: `tests/test_config_door.py` - composition (name-for-name), required keyword, precedence, data layout, epic-name validation, holdings allowlist - and `tests/test_workspace.py` - the folder census, both polarities (AHA-0035). Canonical call:

```python
from ahabase import load_settings, get_data_dir

load_settings(epic="amethod")      # <workspace>/_config/amethod-cli-settings.yml, {} when absent
get_data_dir(epic="amethod")       # <workspace>/_data/amethod, created on demand
```

The consumer's act at the CLI (AHA-0035):

```sh
ahabase workspace ensure   # the seven standard folders at the workspace root, idempotent
```

## Related

- [ontology-config-blueprint](ontology-config-blueprint) - the concept this implements
- [AHA-0021](AHA-0021) - the landing story (evidence rows, red controls, review log)
- [AHA-0035](AHA-0035) - the workspace folder set (the Human ruling 2026-11-22)
