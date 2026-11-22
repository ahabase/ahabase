# ahabase Capabilities Index

> Taxonomy of the ahabase package's capabilities - every capability the code declares must be defined here, and every entry points at the concept that grounds it.

**Type:** Ontology Index
**Blueprint:** [00-ahabase-ontology-index](00-ahabase-ontology-index)
**Scope:** ahabase

## Overview

Capabilities are functional categories that classify what the package's code does. Every `Capability:` line the code carries (whole file text, the method CLI's gate surface - not the docstring alone) must name a capability defined in this index, and each entry maps to the concept blueprint that defines it. `ahabase verify` enforces the first half: a `Capability:` name missing here is a finding. The open-zone link check enforces the second half at the document level: every `→ [x](x)` target must resolve within this repository.

## Taxonomy

### Grid4d

- **grid4d-format** → [Grid4d](ontology-grid4d-blueprint) - the knowledge-tree format core: an Epic's _grid4d/ folders, identity, naming, structure and links validated (grid4d.py, cli_grid4d.py, AHA-0030)
- **story-lifecycle** → [Grid4d](ontology-grid4d-blueprint) - the local story lifecycle: mint by scan-numbering, worktree + branch, status from the documents, complete with tag + merge + archive (story.py, cli_story.py, AHA-0030)

### Config

- **config-management** → [Config](ontology-config-blueprint) - the graduated config door: the epic's settings load (the `_config/<epic>-cli-settings.yml` convention, precedence, duplicate-key warn) and the data-dir resolution (config.py, _yaml_unique.py)
- **instance-state** → [Config](ontology-config-blueprint) - the workspace/instance resolution and the machine id: where the instance is, which machine it runs on (config.py)
- **scope-holdings** → [Config](ontology-config-blueprint) - the sessions-dir allowlist read with staleness: which collaboration scopes hold bindings (config.py)

### Doors

- **cli-command** → [Door](ontology-door-blueprint) - the `ahabase` command line: the group, its shared options, the version line, the entry point (cli.py)
- **health-report** → [Health Check](ontology-health-check-blueprint) - `ahabase doctor`: the named checks of an installation (cli.py)
- **plugin-registry** → [Plugin](ontology-plugin-blueprint) / [Registry](ontology-registry-blueprint) - the entry-point group `ahabase.plugins` filling the one registry behind every door (plugins.py)

### Model door

- **llm-paths** → [Access Path](ontology-access-path-blueprint) / [Verification](ontology-verification-blueprint) / [Settings Switch](ontology-settings-switch-blueprint) - the model door: access path resolution and identity, verification with failure classification, the verified settings switch with backup and restore, the session payload (the ahabase-llm subepic, [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index))
- **llm-discovery** → [Discovery Registry](ontology-discovery-registry-blueprint) - which access paths a machine can use, from cheap local checks only (the ahabase-llm subepic)

### Secrets

- **secrets-door** → [Safe Value](ontology-safe-value-blueprint) - `ahabase safe set / get --reveal / list / delete`: the secrets door; values arrive from a hidden prompt or stdin, never from an argument (cli_safe.py)
- **secrets-manifest** → [Manifest](ontology-manifest-blueprint) - describing every secret without its value: purpose, owner, scope, expiry, targets (safe.py `Entry`, cli_safe.py)
- **secrets-store** → [Store](ontology-store-blueprint) - the pluggable stores behind one protocol (memory, env, keyring) and the trusted location rule for where a store may live (safe.py, cli_safe.py)
- **secrets-bind** → [Consumer](ontology-consumer-blueprint) - binding a secret to the one command that may read it; `safe run` resolves the reference into the environment of a single child process (cli_safe.py, safe.py)
- **secrets-rotate** → [Rotation](ontology-rotation-blueprint) - `safe compare / refresh`: replace a value, prove the new one through the store's own verify, retire the old one (cli_safe.py, safe.py)
- **agent-guard** → [Agent Guard](ontology-agent-guard-blueprint) - a value is revealed only to a person at an interactive terminal, destructive steps only after the owner confirms (cli_safe.py)
- **platform-dispatch** → [Portability](ontology-portability-blueprint) - one codebase, per-OS arms chosen once at import (`_posix.py` / `_win.py`)

### Wiki projection

- **wiki-projection** → [Wiki Projection](ontology-wiki-blueprint) - the graduated wiki generation: `_grid4d/` documents into the `_wikis/<epic>.wiki` mirror (the five sync passes) and the `_Sidebar.md`/`Home.md` navigation rendered from the config (wiki/, cli_wiki.py, AHA-0036)
- **wiki-validation** → [Wiki Projection](ontology-wiki-blueprint) - the mirror's duplicate check (exit 3 when found) and the dedupe clean, root copy wins (wiki/validate, wiki/clean)
- **wiki-publishing** → [Wiki Projection](ontology-wiki-blueprint) - the publish tail: the mirror as a clone of the repository's wiki remote, the delta commit, the push under the declared account through the safe's credential chain, fail-closed (wiki/publish)

### Transparency

- **lineage-validation** → [Lineage](ontology-lineage-blueprint) - the declared path from concept to implementation blueprint to code, checked in both directions; `ahabase verify` (lineage.py, epic.py, cli_transparency.py)
- **ontology-projection** → [Projection](ontology-projection-blueprint) - the ontology map generated into the index between its markers, the same bytes every time (ontology_map.py, cli_transparency.py)
- **capability-vocabulary** → [Lineage](ontology-lineage-blueprint) - the capability gate: every `Capability:` name the Epic's code declares is defined in the Epic's capabilities index (verify, AHA-0016 R3)
- **link-containment** → [Trust Zone](ontology-trust-zone-blueprint) - the open-zone rule as a check: every wiki link of the Epic's documents resolves within the repository or rides the declared exception (verify, AHA-0016 R5)

### Trust

- **artifact-containment** → [Trust Zone](ontology-trust-zone-blueprint) - the Users-zone channel guard as a check: the built wheel and sdist carry only allowlisted, canonical, pattern-clean bytes (artifact_containment.py, AHA-0029)

## Related

- [AHABASE](AHABASE) - the Epic
- [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint) - the doors this vocabulary names
- [implementation-ahabase-transparency-blueprint](implementation-ahabase-transparency-blueprint) - the door that enforces it
