# ahabase Architecture Blueprint

> The architecture of ahabase: the open base - doors over one registry, the package's own services - and the methods, evolucean first among them, that build on it as plugins. Amended 2026-11-22: the base is the complete engine, not a minimal core.

**Implements:** [ontology-door-blueprint](ontology-door-blueprint), [ontology-registry-blueprint](ontology-registry-blueprint), [ontology-plugin-blueprint](ontology-plugin-blueprint), [ontology-health-check-blueprint](ontology-health-check-blueprint)
**Story:** [AHA-0001](AHA-0001), [AHA-0004](AHA-0004) (base and method), [AHA-0017](AHA-0017) (ontology shape), [AHA-0033](AHA-0033) (the full-engine amendment)
**Code:** __init__, __main__, cli, plugins
**Status:** accepted by the Human (2026-10-24; base and method 2026-10-25); the full-engine amendment accepted by the Human (2026-11-22)

## Overview

The Human (2026-10-24) asked how the open package and the closed part work together, and accepted: the open package never calls the closed part; the closed part builds on the package and plugs into it. The Human then (2026-10-25) named the consequence: architecturally ahabase is the core - the **base** - and evolucean is a **method** that inherits from it. This blueprint fixes that shape so every later story (the safe, the grid4d format, the MCP server, the Claude Code plugin, the method as a plugin) lands in its place.

The Human (2026-11-22) then ruled the base's completeness: **the public package must be fully functional like today's evolucean CLI** - the minimal-consumer cut had gone below the usability boundary (measured that day: 61 top-level commands in the evolucean CLI against 8 doors in the package, with the `trust` door missing entirely, below even the rows-3-4-8 basics ruling of 2026-11-20). Entropy reduction over evolucean means cleaner seams at the same completeness, never feature amputation: a consumer without status, sync and projections idles blind; without trust and collab there is no game, only solo story writing. The design question inverts accordingly - not "what can we cut for a consumer" but "what of evolucean is the engine, and what is this one machine". The sections added by AHA-0033 (The complete engine, and the rules 10-13) carry that ruling.

## Base and method

**Why the base is open** (Human, 2026-10-25). The value of knowledge grows and must be protectable; the cost of work, the creation of software included, falls. Protecting code therefore protects little - a closed tool can be rebuilt from its behaviour and documentation - while open code builds trust, adoption and contributions. What is protected is knowledge: a method's know-how and every user's own knowledge, by the trust zones. This is the known move of commoditizing one's complements (Joel Spolsky, 2002): the tool is made open so that the knowledge built with it gains value. A consequence: the closed evolucean shrinks over time to what is valuable - the method as knowledge and a thin plugin - while its mechanism moves into the base.

**Why it is sustainable.** An open base with protected extensions is a proven shape: Chromium and Chrome, Code - OSS and Visual Studio Code with proprietary extensions, the Eclipse platform with its plugins, PostgreSQL with extensions. Our reading of Android is the failure mode to avoid: function moving over the years from the open project into closed services, so that the open part alone carries less and less - hence the rule never back ([00-ahabase-ontology-index](00-ahabase-ontology-index), Constraints). The conditions are a stable, versioned extension contract (rule 3), extensions that register instead of patching the base (rule 4), tests of the base independent of any extension, and a minimal base.

**How the closed part adapts.** By the strangler fig pattern (Martin Fowler, 2004): the new grows beside the old and takes over one capability at a time while the old keeps working; behind a shared interface where needed (branch by abstraction) and with both paths working for a while before the old is removed (parallel change, expand and contract). The safe was built this way - in the package, nothing switched - and rule 2 removes a capability from the evolucean CLI once it lives here.

**Turning the inheritance.** Today the Epic header says ahabase inherits evolucean, because the story workflow lives in evolucean's tooling - a known exception. The direction turns when the knowledge format and the story workflow live in the package (step 2 of the order below), in these steps:

1. The base concepts of the knowledge format are written in this ontology; evolucean's blueprints of the same concepts become extensions that keep their names and link to the base (old links keep resolving, history stays as it is).
2. Dual reading (expand): the tooling resolves a concept in the base first, then in the method; both work.
3. A rehearsal on a scratch instance: verify, projections and gradients before and after the turn, outputs compared; only expected differences.
4. The turn itself is small - the `Inherits` header and the registry - and reversible by reverting it while the method's files exist; the rollback is tested first.
5. Contract: duplicates removed once the turned instance runs green.

**Gate of the turn:** the base passes its own suite; dual reading runs; the rehearsal is green; the rollback is proven; every instance the user runs (each a workspace of this user with its own registry) turns in the same window, so no instance inherits the old way while another inherits the new; the Human consents. Afterwards a domain Epic may inherit the base directly, without any method - the free first step of adoption.

## Layers

```
  Doors (open)          CLI `ahabase`     MCP `ahabase serve`     Claude Code plugin
                              \                 |                    /
  Open package          ┌───────────────────────────────────────────────┐
  `ahabase`             │  registry: commands, health checks, tools     │
  (Apache-2.0)          │  grid4d format, secrets, config, doctor       │
                        └───────────────────────────────────────────────┘
                                       ▲ imports services, registers
  Plugins               ┌───────────────────────────────────────────────┐
  (installed by choice) │  the evolucean method (closed), other plugins │
                        └───────────────────────────────────────────────┘
```

- **Doors** - the ways in. The CLI and the MCP server are two views of the same registry: what a plugin registers is available in both. The Claude Code plugin is thin (skills, hooks, settings) and calls the CLI or the MCP server; it holds no logic of its own.
- **Open package** - the registry and the services every door and plugin needs: the grid4d format (read, validate, templates), secrets (an interface whose values stay in the user's own store), configuration, `doctor`, `init`, `verify`.
- **Plugins** - distributions that declare an entry point in `ahabase.plugins`. The evolucean method becomes one of them.

## The complete engine (2026-11-22, AHA-0033)

The full-engine ruling extends the layers above with two more beneath and a residue: the base package is the **engine** (the full game), heavy stores are **optional substrate** (add-on doors with their own install extras, never prerequisites, never dual-mode doors - rule 12), and the local installation is the **workspace**. The private residue names what never ships.

| Layer | What lives there | Who writes | Worked example (from the census) |
|---|---|---|---|
| Doors | Entry surfaces: CLI subcommands, MCP tools, the Claude Code plugin | Door code, in stories | `ahabase story` - the CLI door over the lifecycle engine |
| Engine (the open package) | The full game: story lifecycle (mint, pool, complete; lock, heal), grid4d documents machinery (validate, skeleton, pattern, km, find, fork, registry), trust, collab (MQTT transport, git membership - D3), status/sync, projections, snapshot, release, llm, safe | Engine stories, in worktrees | The AHA-0032 lock: keyed on the common git dir, released on process death |
| Substrate (optional) | Heavy stores, each an add-on door with its own install extra: usage measurement DB, Kuzu graph, MQTT broker, LiteLLM proxy | The installing consumer, by choice | The collab MQTT broker - the multiplayer transport (D3): absent it, the engine runs solo and the multiplayer door waits (a door-level requirement, never an engine prerequisite) |
| Workspace | The local installation: repos (anywhere under it), engine-owned state folders | The engine (state folders), the human (repos, `_inbox`) | `~/ahabase-playground` - the prototype consumer workspace |
| Private residue | This namespace's machine layer: enterprise bridges (<enterprise-tool>, confluence, jira, dbt, db-query), the sensor and wake fleet, the LLM proxy specifics | evolucean-only stories | `db-query` - enterprise network and packages no consumer has |

Ownership rule: a layer never writes another layer's domain. Doors do not implement; the engine does not know which door called it; substrate never appears in a tree; workspace folders never carry meaning a tree must read to function. Growth stays what the plugin contract already makes it - a new door, never engine surgery.

### The state invariant

Trees + git are the only source of truth. Everything outside a tree - every file in `_data/` and `_generated/` - is either a cache, rebuildable by a named command, or an append-only journal, which is the record itself and is never rebuilt (its retention is explicit, never silent). Engine-owned, gitignored. This replaces the over-cut "no state beside the tree" of the minimal-consumer draft.

| State kind | Where | Class | Rebuild |
|---|---|---|---|
| Lifecycle locks | inside the git dir | cache (vanishes on release; process death releases) | nothing to rebuild - the next command proceeds |
| Collab local journals | `_data/` | journal (the chat record today - chat rows, review requests, verdicts) | none today - it is the record; retention is explicit |
| Projections | `_generated/` | cache | `ahabase sync` / `ahabase projection` recompute from trees |
| Usage measurement | substrate DB (add-on) | cache (raw events are the journals) | re-ingest from the journals; the store is an add-on door, not a mode of the doors |
| Snapshots | the snapshot store under `_temp/` | journal (durable anchors: baselines, completion diffs) | not rebuilt - created and diffed by the snapshot door; retention is explicit |
| Worktrees | `_worktrees/<epic>/<STORY>` | cache of the branch tip + journal of uncommitted work | the cache half re-materializes from the branch; the uncommitted half is not protected - retention is explicit: commit-before-complete is its only safety |

The invariant holds everywhere: delete any `_data/` or `_generated/` content and the game loses no truth - a cache rebuilds by its named command, and a journal is the record, kept by its explicit retention (the chat journal today is the only record of review requests and verdicts; deleting it deletes the record). AHA-0032's crash model - nothing strands, the next command heals - is the pattern for every state kind.

### The workspace skeleton

`ahabase init` (workspace mode) lays out the whole board; every placeholder folder carries `_README.md` (what belongs, who writes, rebuild policy). No placeholder without a writer. Every installation - the dev namespace, the frozen Work copy, a consumer's machine - shows the same anatomy: `ls` is the map.

```
<workspace>/
├── ahabase.env            # the workspace pin (AHABASE_WORKSPACE); written by init
├── _config/               # llm-paths-variants.yaml (optional); wiki configurations when configured
├── _data/                 # engine state: collab journals, caches
├── _generated/            # projections, recomputed from trees
├── _inbox/                # external inputs landing zone (human, external captures)
├── _temp/                 # scratch, snapshot store
├── _wikis/                # wiki mirrors (the wiki door, decision D2)
└── _worktrees/            # <epic>/<STORY> - engine-owned, outside every repo (decision D1)
```

| Folder | Writer | Content | Policy |
|---|---|---|---|
| `_config/` | human + the llm/wiki doors | path variants, wiki configs | llm variants are read by the llm door; wiki configs are read by no code today (D2 reconciliation); never truth |
| `_data/` | engine doors | journals, caches | gitignored; caches rebuildable, journals kept by explicit retention |
| `_generated/` | projection/sync doors | projections | gitignored, recomputed |
| `_inbox/` | human, external systems | inputs awaiting processing | surfaced, never auto-deleted |
| `_temp/` | snapshot door, anything | scratch, snapshots | disposable except the snapshot store's retention |
| `_wikis/` | wiki door | local wiki mirrors | mirrors only; the remote wiki is truth |
| `_worktrees/` | story lifecycle | `<epic>/<STORY>` worktrees | branches are truth |

The repos stay pure (rule 11): tracked content only. Epic repositories sit directly under the workspace root, siblings of the state folders - the layout the dev namespace has always run; no `repos/` folder is invented (round-4 review, D4: the ancestor test measured all seven placeholders present and `repos/` absent). Discovery scans the workspace for def files.

### The capability fate map

The census (evolucean `--help`, measured 2026-11-22): 61 commands. Fates: **engine** (the public package runs it), **engine/substrate** (an engine door, fuller behavior when a substrate store is present), **private** (this namespace only, reason stated), **dies** (migration-internal or superseded by an engine design).

| Family | Commands (census) | Fate |
|---|---|---|
| Story lifecycle | story, pause, resume, active-story, test, snapshot, release | engine (story ships; pool, test runner, snapshot, release land as sequenced doors) |
| Grid4d documents | verify, skeleton, pattern, km, ontology, find, fork, link, registry, declarations, verify-file, verify-stdin, verify-capabilities | engine (verify and ontology ship; validate is a package door with no evolucean ancestor command; the rest land with the documents-machinery door group) |
| Trust and collab | trust, collab, sessions | engine (trust is a missing rows-3-4-8 basic; collab's transport is MQTT with membership rows on the collab branch - D3) |
| Game loop | status, sync, projection, export-gradient, export-karma, karma, query, pipeline | engine (tree+git doors; measurement views land as substrate add-on doors, never dual modes - rule 12) |
| Agent layer | claude, hook-handler, pre-tool-handler, inbox-handler, session-end-handler, stop-handler, recovery | engine (the Claude Code plugin door) |
| LLM | llm, llm-init, llm-update | engine (llm ships; llm-init folds into it; llm-update is substrate-optional - provider model lists) |
| Wiki | wiki | engine (D2: essential) |
| Init, identity and health | init, epic, doctor | engine (absorbed: workspace init lays the skeleton, Epic init bootstraps `_grid4d/`, doctor checks the installation - init and doctor ship today; def-file identity - rule 5) |
| Machine layer | distribution, sensor, mqtt, external, ingest, ha, history, store-service | private (this namespace's fleet ops; candidates for far-future optional doors, never the public flip) |
| Work-specific | export-dbt, ml | private (enterprise sandboxes; personal notebook mining) |
| Migration internals | containment, extract-functions, extract-rules, test-role, test-scope, config | dies (a one-release stub, dev tooling, and the namespace registry superseded by def-file identity) |

None omitted: all 61 census names appear in the fate rows above (round-1 review measured the first draft at 59 of 61 - `doctor` and `link` were missing while the cell held `validate`, a package door, not a census command; fixed). The 8 shipped doors (doctor, init, llm, ontology, safe, story, validate, verify) mark the starting point; `safe` and `validate` have no evolucean ancestor command - they are the engine's own doors.

### The numbered decisions of 2026-11-22

**D1 - worktrees live outside the repo.** `<workspace>/_worktrees/<epic>/<STORY>`, not `<repo>/_worktrees/`. Reason: a worktree is local temporary structure and does not belong in the git repo structure; the engine must never write `.gitignore` lines or chore commits to hide its own local state - and it must not fall through to a default silently either: `story create` refuses by name when the workspace is not pinned explicitly (`AHABASE_WORKSPACE`) or when the Epic's repo is not under the resolved workspace (both sides resolved before the comparison - the same directory has two spellings on macOS) (round-2 review: a forgotten pin would otherwise mint into the dev machine's real `~/ahabase` - `get_workspace_dir()`'s never-None default stays for reads, the minter treats the unpinned default as a refusal). Reverses the AHA-0031 in-repo choice - [implementation-story-lifecycle-blueprint](implementation-story-lifecycle-blueprint) rules 1, 4, 5 and 8 are the amendment targets: the scan directory moves to the workspace epic subfolder (rule 1), rule 4's minted path moves with it, and every site that builds or walks the in-repo path moves - the number scan (`story.py:125`), the half-minted heal (`story.py:239` - it iterates the directory and returns empty when absent, so unless it moves with the scan the AHA-0032 corpse-heal quietly switches off; rule 8 states the heal), the mint (`story.py:277`), the status scan (`story.py:333`), and complete's worktree handling and refusal text (`story.py:369-372`); the ignore write with its chore commit is deleted (rule 5), and the forgotten-pin refusal lands next to that deletion. Eight dependent artifacts assert the in-repo path today (playground/CLAUDE.md, playground/scenarios.md, playground/tests/r2-seam.sh, playground/tests/r3-archetypes.sh, playground/tests/r4-arms.sh, tests/consumer-leg.sh, tests/test_story.py, tests/test_story_parallel.py); the migration story re-enumerates them by its own `grep -rl _worktrees` rather than trusting this list. The AHA-0032 lock is untouched: it keys on the common git dir, not the worktree location. Boundary: one workspace assumes one clone per Epic; a second clone of the same Epic on one machine takes a second workspace.

**D2 - wiki publishing is an essential engine door.** Not private practice: a knowledge system whose output no human outside the agent loop can read is half finished. The `wiki` door migrates with the other groups. The wiki configuration surface is engine format - today three conventions exist (round-2 review re-measured the readers over both source trees): the functioning one is `<epic>.wiki.yml` at the repository root (keys `wiki.target`, `wiki.source`) - the only one any code reads; the evolucean `epic init` also writes `_grid4d/wiki.yml` (`name`, `extends`) whose `extends` no code reads; and the dev namespace documents `_config/<epic>-wiki.yaml` as the publishing config (ahabase.md) while the actual file on disk is `_config/evolucean.wiki.yaml` - empty, dot-named against the documented dash form, and read by no code either; the wiki-door migration story reconciles the three into one file with one reader. `_wikis/` ships from init. The consumer's alternative stays plain `git push` - the door adds the rendered mirror, not a monopoly.

**D3 - the public collab transport is MQTT; membership stays on git.** Two records, two homes. What rides git is membership, and only that: `trust join` appends seat rows to `stories/<STORY>.log` on the collab branch - the record seats already trust, proven by practice. (The method CLI also keeps an orphan `counters` branch of story-ID counters on both repositories; that is not transport - the package already refuses stored counters, ids derive by scan, `story.py`'s "never stored, no counters branch" - so the counters branch dies with the migration, in the engine's own rule.) What carries the game - chat rows, review requests, verdicts - is the MQTT fabric, the transport evolucean practice has proven; the instance-local chat journal stays the record of those rows (a journal, never rebuilt - the state invariant). Same-instance and cross-instance seats differ only in which delivery route wakes them. This reverses the same-day first draft of this decision ("the public collab transport is the git journal, MQTT is substrate"): that draft extended git to carry chat rows - a mechanism with no evolucean ancestor that has run in practice, out of place by D4. The broker is substrate and conditional: optional for the engine (solo play and every tree+git door), required for the multiplayer door - absent it the engine runs solo and the fan-out reports the journal-only delivery outcome, the running roster's own reporting (`DELIVERY_OUTCOMES` in `collab_team_roster.py`); no git replacement is invented.

**D4 - carry the proven, simplify, never invent.** The standing strategy for every door migration: ahabase is the minimalist but fully functional version of evolucean - what has proven itself within evolucean, running in practice, is what migrates; simplification of a proven mechanism is welcome; a mechanism with no proven ancestor is not invented in the public package. Experimenting is evolucean's role, not ahabase's - ahabase carries only what survived that experimenting (D3's first-draft git transport had no ancestor - hence the reversal; membership on the collab branch has one - hence it stays). The criteria for evaluating every proposed architecture in this plan: robustness, consistency, minimalism (Human, same day). Reviewers ask for the ancestor.

### Sequencing toward the public flip

Order of door groups, each landing release-visible (extends the rows-3-4-8 basics ruling - no doors-only 0.x):

1. **Basics complete** - the trust door (the missing basic), the test runner, the story pool (pause, resume, active-story): the story game is fully playable solo.
2. **Documents machinery** - skeleton, pattern, km, find, fork, registry, declarations: the knowledge format is fully self-describing. The folded idea `pattern-override-discovery` decides here (the pattern door lists effective-versus-fallback per document type); `shared-taxonomy-space` decides here too (what of ontology, pattern and implementation ships with the package - the package patterns are the seed).
3. **Game loop** - status, sync (tree-based), projections from trees: an idle instance steers itself.
4. **Agent layer** - the Claude Code plugin door (hooks, stop-handler, recovery): the game plays itself with the Human.
5. **Collab over MQTT** - trust teams, seats, review rounds: the game is multiplayer; the broker joins the critical path here (D3 - the proven fabric, membership rows stay on the collab branch).
6. **Wiki door** - D2: knowledge reaches humans outside the loop. The folded idea `example-epic-in-distribution` decides here (a runnable example Epic in the distribution; it doubles as the playground's replacement).
7. **Public flip** - the fresh-start repo (the current repository is not publishable as-is: account names, the internal mirror, all history) and the PyPI release carrying steps 1-6.

Substrate add-on doors (measurement DB, Kuzu, proxy management) attach after the flip, in demand order, each with its own install extra (rule 12); the MQTT broker is the one substrate on the critical path - step 5, the multiplayer transport (D3).

### Open questions (deliberately undecided)

- **Substrate optionality mechanics** - install extras (`ahabase[duckdb]`), lazy detection, or explicit declaration in `_config/`: rule 12 states the behavior, not the packaging.
- **Collab transport details** - broker packaging for consumers (which broker, embedded or external, auth), delivery-versus-record semantics of journal rows; the git extension of chat rows is dead by the D3 reversal - no design work there.
- **Fresh-start repo mechanics** - history severance, the internal-mirror exile, CI replay: the flip story's own scope, fed by this blueprint.
- **The dev namespace convergence plan** - which evolucean doors migrate onto the package engine first (the standing migration's door order), separate from the public sequencing above. Convergence includes pinning the dev workspace explicitly - `AHABASE_WORKSPACE` is unset on the dev machine today, and under D1's rule an unpinned create refuses (round-3 review note).
- **The `_inbox` processing model** - who moves items out, and into what (issue docs, idea docs, or stories).

## Rules

1. **Dependency direction** - plugins import the package; the package imports no plugin (a test parses every module of `src/ahabase` and fails on an import of the evolucean method or a string literal naming it - `import_module`, `__import__`, a subprocess call; an import assembled from pieces at run time is beyond a parse).
2. **One place per capability** - a capability lives in exactly one distribution. What moves into this package is removed from the evolucean CLI, which imports it; `ahabase doctor` checks only the package and runs the checks plugins register, so no check exists twice.
3. **Plugin contract** - an entry point names an object with `API_VERSION` (the major registry API it needs) and `register(registry)`. The registry offers `add_command(command, name=None)` and `add_check(name, check)`; MCP tools join the same registry in their story. Registry API version: 1.
4. **Robust loading** - an import error, any failure in `register` (an exception or `SystemExit`; only Ctrl-C passes), an incompatible `API_VERSION` or a name already taken is recorded as that plugin's problem; a failed plugin's partial registrations are rolled back; the package's own command names are reserved before any plugin loads and the registry is read through read-only views, so nothing is overwritten; a failing health check never skips the next. `doctor` reports it and exits non-zero (review c6e031a3).
5. **Trust** - installing a plugin means trusting its code; `doctor` lists each plugin with the distribution and version it came from.
6. **Zones** - this package is 0 Public content, open and verifiable: the code that touches user data, safe values and the network lives here. A method's know-how is 3 Core. Safe values are Vault-held (5 Vault): the package offers the interface, the values stay in the user's store and are resolved only into the process that needs them ([ontology-trust-zone-blueprint](ontology-trust-zone-blueprint)).
7. **Surface rule** - in this repository a method is described only by its surface (command names, the plugin contract), never by how it works.
8. **Base and method** - the boundary criterion, never back and collaboration in three layers decide what belongs here ([00-ahabase-ontology-index](00-ahabase-ontology-index), Constraints).
9. **Private until the first release** - see the Epic identity.
10. **Trees + git are the only source of truth** (2026-11-22) - every state kind outside a tree is a cache or an append-only journal with a named rebuild command (the state invariant table). No state kind exists without a rebuild path or an explicit retention rule.
11. **The repo is pure** (2026-11-22) - a repository holds tracked content only: the Epic's code, tests and `_grid4d/`. The engine never writes into a repo to manage its own local concerns - no ignore lines, no chore commits hiding local state (decision D1).
12. **Substrate is additive, never dual-mode** (2026-11-22; restated round 4 under D4) - the engine runs trees + git and needs no store; the heavy stores (usage DB, Kuzu, MQTT broker, proxy) arrive as add-on doors with their own install extras, never as prerequisites of the engine. No door ships two modes: a tree-mode-and-store-mode pair has no evolucean ancestor (evolucean holds duckdb and kuzu as hard dependencies; no door of ours runs both ways). A door that needs a store names its store and refuses without it - the multiplayer door names the broker (D3).
13. **Uniform anatomy everywhere** (2026-11-22) - every installation shows the same workspace skeleton; placeholder folders carry their own `_README.md` contract; no placeholder without a writer.

## Order of the next stories

Superseded by the sequencing of the full-engine amendment (above) for everything after its step 3; the original order survives below as the record of the base build.

The Human set transparency before the agent guard (AHA-0008, decision 1): it makes every later step visible in the lineage.

1. **Transparency** - the lineage declarations and the package core: `ahabase ontology graph` and the Epic-scope lineage in `ahabase verify` ([implementation-ahabase-transparency-blueprint](implementation-ahabase-transparency-blueprint)) - done (AHA-0009).
2. The safe - `ahabase safe` with the OS store as default ([implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint), AHA-0002/0003; mechanism only, nothing switched on the instance), then the research of existing tools (AHA-0005), the threat model (AHA-0006), the agent path - consumer binding (AHA-0007), reveal by a person only (AHA-0007), the agent guard - and `safe scan`.
3. The grid4d format and the story workflow moved out of the evolucean CLI into this package, in slices with the "package first" rule (AHA-0008, decision 3); the inheritance turns (above).
4. The MCP server (`ahabase serve`) over the registry.
5. The Claude Code plugin.
6. The evolucean method registered as a plugin; `knowledge-usage` keeps working until then.

## Ontology shape

Decided by the Human (2026-10-31, [AHA-0017](AHA-0017)): the Epic ontology carries the architecture of ahabase only; a concrete capability's concepts live in that capability's subepic ontology. The criterion is the base-and-method boundary applied one level down: a concept belongs to the Epic ontology when it describes structure that spans capabilities (Trust Zone, Boundary, Door, Plugin, Registry, Health Check, Portability, Lineage, Consumer-facing indexes such as the capabilities index); it belongs to a subepic ontology when it describes how one capability works.

- **Moves to the first subepic, `ahabase-safe`** - the safe's concepts: safe-value, reference, consumer, store, manifest, rotation, scan-finding, shadow-run, output-watch, agent-guard.
- **Classified (Human, 2026-10-31, [AHA-0018](AHA-0018))** - the remaining capability-flavoured concepts, by the same criterion: **Projection stays Epic-level** - generated views that span capabilities (the ontology map today, the projections to come) are architecture; **Lineage stays Epic-level** - the concept-to-code path is the Epic-wide verification spine; the capabilities index stays Epic-level (consumer-facing, named in the criterion); Trust Zone, Boundary and the platform concepts (Door, Registry, Plugin, Health Check, Portability) stay - structure that spans capabilities. Nothing else moves in AHA-0018; a future capability's concepts land directly in that capability's subepic, never in the Epic's ontology first.
- **Executor** - AHA-0018: creates the subepics (`ahabase-safe` first), moves the blueprints, registers the subepic through its identity document (the registry entry stays empty plumbing), and teaches the verify gates where each index lives (wiki links are name-only, so the moves themselves are cheap for links; the cost sits in the registration and the gates).
- **Index maps render at their own level** (Human, 2026-10-31) - the Epic index's map shows the Epic-level concepts and each subepic as one unit; a subepic's own index carries its detailed map. The Epic map today renders one module's wiring: its trust-and-boundaries cluster holds 12 of the map's 18 nodes - ten of them the safe's concepts and two (Trust Zone, Boundary) Epic-level - because the safe's structure sat at the Epic level; maps are generated projections, never hand-edited, so the move fixes the map - the generator learns the level rule in AHA-0018, which also fixes the map's missing portability node.

A concept enters an ontology only when it is robust, minimal and needed by already-agreed implementation (Human, 2026-10-31); the shape is weighed again when the knowledge format graduates here.

## Template

```toml
[project.entry-points."ahabase.plugins"]
<name> = "<module>"
```

```python
API_VERSION = 1

def register(registry):
    registry.add_command(<click command>)
    registry.add_check("<name>", lambda: (True, "<detail>"))
```

## Structure

`src/ahabase/__init__.py` (version), `src/ahabase/plugins.py` (registry, contract, loading), `src/ahabase/cli.py` (the CLI door, `doctor`), `src/ahabase/__main__.py` (the module door, `python -m ahabase`), the safe's modules ([implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint)), the transparency modules ([implementation-ahabase-transparency-blueprint](implementation-ahabase-transparency-blueprint)), the story lifecycle modules ([implementation-story-lifecycle-blueprint](implementation-story-lifecycle-blueprint)), the llm paths modules ([implementation-ahabase-llm-blueprint](implementation-ahabase-llm-blueprint)), `tests/` (pytest). Every module names its blueprint in an `Implements:` line of its docstring, and every implementation blueprint names its modules in its `**Code:**` line; `ahabase verify` checks both directions. Build: hatchling >= 1.27 (PEP 639 license expression); the sdist carries the package, tests, README, LICENSE and pyproject only - the Epic's knowledge (`_grid4d`) is not part of the package. Worktrees live outside every repo (decision D1): `<workspace>/_worktrees/<epic>/<STORY>`.

## Example

```
$ ahabase doctor
ahabase 0.0.1 (registry API 1)
python 3.14.6 (.venv/bin/python3.14)
plugin example: loaded - from example-plugin 1.0
  commands: hello
check example: ok - ok
```

## Related

- [AHABASE](AHABASE) - the Epic
- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - the first service of the package
- [implementation-story-lifecycle-blueprint](implementation-story-lifecycle-blueprint) - the lifecycle whose in-repo worktree choice decision D1 reverses, and whose lock survives the reversal
- [00-ahabase-ontology-index](00-ahabase-ontology-index) - the base's concepts and the boundary criterion

This blueprint decides the package architecture that evolucean's distribution layer proposed; the full-engine amendment (AHA-0033, 2026-11-22) decides its completeness, its state invariant and its workspace anatomy.
