# Config Blueprint

> Where everything lives: the workspace, each epic's settings and data, the machine's id - the layer every other capability stands on.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Platform → Config
**Placement:** base - a service with no dependency on any other concept
**State:** implemented - the graduated config/instance-state layer (AHA-0021, the pilot graduation)

## Overview

**Config** = the resolution of the instance's places and of each tenant epic's settings: the workspace root, the per-epic settings file, the per-epic data directory, the machine id, and the collaboration scope holdings of the sessions dir. It is the first graduated capability: a method's config layer moved into the base so that every method and every future capability reads the same places through one seam.

The door is **workspace-level and epic-explicit**. Which epic a call is for is a required keyword, never ambient state - a function whose result depends on which epic the caller "currently is" would push that ambientness into every consumer, and a root that may be absent (a None contract) would let the absence propagate past path operations and be silently tolerated - a fail-open shape for the foundation layer. Both were ruled out at the landing's first review checkpoint (AHA-0021, 2026-11-02).

## Attributes

- **Workspace root** - `AHABASE_WORKSPACE` env, default `~/ahabase`; always a path, never None; `get_instance_root` is the ported second name of the same resolution
- **Settings convention** - `_config/<epic>-cli-settings.yml` under the workspace (this door's own convention); a missing file is normal and reads as `{}`; a duplicated key warns once and keeps YAML's last-wins; `AHABASE_CONFIG` overrides with a direct file path; the four path keys get `~` expanded
- **Data layout** - `<workspace>/_data/<epic>` by default; the settings `data_dir` overrides; a relative value anchors at the workspace root (a wheel has no project root)
- **Epic name** - a name, not a path segment: validated, `[A-Za-z0-9][A-Za-z0-9_-]*`
- **Machine id** - the hostname
- **Holdings allowlist** - the sessions reader returns named fields only, never the raw scope entry: a scope file is raw runtime state, and a blanket passthrough would let anything that ever lands there reach what renders it

## Relations

- underlies → every other capability (each reads its places through this seam)
- feeds → the collaboration basis (Instance, Sharing - named in the index, defined with the collaboration story): the sessions dir this reads is where a running instance's scope bindings live; the collab store stays where the serving epic's data dir puts it until the collab concepts land and decide their own root

## Constraints

- No ambient epic - the settings readers take the epic as a required keyword
- Never None for the roots - absence is resolved, not propagated
- The collaboration store does not move with this concept: a running instance's journal, board, inbox and sessions stay where the serving epic's data dir puts them; per-epic versus workspace-wide collab rooting is the collab landing's decision, recorded here so it is made consciously
- Ported behavior is kept unless it contradicts the above; every departure is recorded in the landing story

## Example

- `ahabase.config.load_settings(epic="amethod")` reads `<workspace>/_config/amethod-cli-settings.yml`, `{}` when the file does not exist
- `ahabase.config.get_data_dir(epic="amethod")` returns `<workspace>/_data/amethod`, created on demand

## Related

- [implementation-ahabase-config-door-blueprint](implementation-ahabase-config-door-blueprint) - the landed door
- [Door](ontology-door-blueprint) - a future `ahabase config` view of the same layer through the CLI
- [00-ahabase-ontology-index](00-ahabase-ontology-index) - the layer this belongs to
