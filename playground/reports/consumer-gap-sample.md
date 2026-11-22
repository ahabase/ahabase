# The consumer gap walk - the sample report

> The first walk, performed 2026-11-21 by the AHA-0031 seat against the
> shelf built the same day. This is the versioned example of the gap-walk
> chapter (scenarios.md, "the comparison lens"): the suite row
> `r5-comparison.sh` enforces that this report names every door group the
> census records - when the development CLI grows a door, the row goes red
> and this file gets re-walked. A recorded walk is a claim to re-measure.

Measured against the shelf: the development CLI (knowledge-usage, the
development workspace's primary) exposes **61 top-level doors**; the ahabase
CLI (this playground's primary, from the wheel) exposes **9** - `doctor`,
`init`, `llm`, `ontology`, `safe`, `story`, `validate`, `verify`,
`workspace` (re-walked 2026-11-22: AHA-0035 added the workspace door).

## The walk

| door (the development CLI) | the ahabase side | classification | evidence |
|---|---|---|---|
| active-story | story show | covered | `ahabase story show` names the active story |
| claude | absent | package gap (deferred) | the Claude-hooks layer (game master, km auto-log) is agent machinery beyond the first-public basics |
| collab | absent | package gap (deferred) | multi-instance collaboration; beyond the first-public basics by ruling (basics = grid4d, trust, story) |
| config | absent | dev-only by design | the `_config/` registry is development plumbing; ahabase identity self-registers through the def file - no parallel configuration |
| containment | absent | dev-only by design | the removed-word gate is repo-internal guard machinery; the package's own AST guard lives in its test suite |
| declarations | absent | package gap (deferred) | SubEpic projection declarations - beyond basics |
| distribution | absent | package gap (deferred) | the machine layer (installer, sensors, sense/heal) |
| doctor | doctor | covered | the same door in both CLIs |
| epic | init | covered | `ahabase init` is the same seam with the smaller net: the Epic skeleton, not the whole game board |
| export-dbt | absent | dev-only by design | dbt exports target the work-machine enterprise stack |
| export-gradient | absent | package gap (deferred) | the blueprint-vs-implementation gradient report |
| export-karma | absent | package gap (deferred) | the karma export |
| external | absent | package gap (deferred) | external platform sensing |
| extract-functions | absent | dev-only by design | CLI-internal audit tooling |
| extract-rules | absent | dev-only by design | CLI-internal audit tooling |
| find | absent | package gap (deferred) | cross-Epic document find; useful to a consumer, beyond basics |
| fork | absent | package gap (deferred) | document forking |
| ha | absent | dev-only by design | the Home Assistant bridge is personal infrastructure |
| history | absent | package gap (deferred) | the VictoriaMetrics history store |
| hook-handler | absent | dev-only by design | evolucean hook plumbing |
| inbox-handler | absent | dev-only by design | evolucean hook plumbing |
| ingest | absent | dev-only by design | MQTT ingest targets the personal broker layer |
| init | init | covered | the Epic skeleton door |
| karma | absent | package gap (deferred) | karma metrics |
| km | absent | package gap (deferred) | knowledge-map reconciliation; the hook auto-log is agent machinery |
| link | absent | package gap (deferred) | link management |
| llm | llm | covered | the model-access door |
| llm-init | llm | covered | folded into the llm door (discover, verify) |
| llm-update | absent | dev-only by design | the OpenRouter free-list refresh serves the personal proxy |
| ml | absent | package gap (deferred) | the ML SubEpic |
| mqtt | absent | dev-only by design | the personal broker layer |
| ontology | ontology | covered | the Epic's ontology door |
| pattern | absent | package gap (deferred) | pattern management |
| pause | absent | package gap (deferred) | the story pool is beyond the basics lifecycle |
| pipeline | absent | dev-only by design | readings-pipeline internals |
| pre-tool-handler | absent | dev-only by design | evolucean hook plumbing |
| projection | absent | package gap (deferred) | Epic-level projections |
| query | absent | package gap (deferred) | ad-hoc queries over derived stores (DuckDB/Kuzu); ahabase holds no derived stores yet |
| recovery | absent | dev-only by design | the recovery pack rides the hook layer |
| registry | absent | dev-only by design | the unique-name registry is derived-store machinery; naming checks ride `validate` |
| release | absent | dev-only by design | the release flow is repository-internal; a consumer's release rides the story tag complete mints |
| resume | absent | package gap (deferred) | the story pool |
| sensor | absent | dev-only by design | internal sensing |
| session-end-handler | absent | dev-only by design | evolucean hook plumbing |
| sessions | absent | package gap (deferred) | collaboration sessions |
| skeleton | absent | dev-only by design | CLI-internal structure tooling |
| snapshot | absent | package gap (deferred) | instance-state snapshots |
| status | story show | covered | `ahabase story show` carries the game status; discoverable through `story --help` |
| stop-handler | absent | dev-only by design | the game master is the evolucean game |
| store-service | absent | dev-only by design | the live store service |
| story | story | covered | the lifecycle door (mint/show/complete versus create/status/complete - a naming divergence, both help texts self-describe) |
| sync | absent | package gap (deferred) | the derived-store pipeline; ahabase `verify` stands alone without derived stores |
| test | absent | **package gap (near-term)** | the finding below: the story set requires a `-tests.md` file and `complete` refuses without it, but the wheel-served CLI carries no runner - a consumer cannot execute the tests file their story must ship |
| test-role | absent | dev-only by design | testing internals |
| test-scope | absent | dev-only by design | testing internals |
| trust | absent (safe covers the secrets dimension) | package gap (deferred) | sharing agreements and the sharing gate are multi-instance machinery; `ahabase safe` carries the secrets store, not the sharing zones |
| verify | verify | covered | the consistency door |
| verify-capabilities | absent | dev-only by design | CLI-internal capability audit |
| verify-file | absent | dev-only by design | the validator's internals; `validate` carries the file checks |
| verify-stdin | absent | dev-only by design | the validator's internals |
| wiki | absent | package gap (deferred) | wiki sync |

## The tally

| classification | doors |
|---|---|
| covered (an ahabase door carries it) | 10 |
| package gap, near-term (first-public basics need it) | 1 |
| package gap, deferred (beyond the first-public basics) | 24 |
| dev-only by design (not package material by ruling) | 26 |
| **total** | **61** |

## The near-term finding: the test runner

The walk's first product. The ahabase story set includes `-tests.md` by
construction (`story create` mints it; `complete` refuses without it), yet
the wheel-served CLI exposes no `test` door - the consumer's tests file is
required but cannot be executed. This ranks with the first-public basics
(grid4d, trust, story): a story lifecycle that demands a file the package
cannot run is a self-description gap in the package's own contract. The
fix is a package door, and this report is its evidence.

## The reverse direction: the ahabase side census (not gaps - but walked)

The young package moves first, so its doors get walked too: a tenth door
here re-walks this report exactly like a new development door (the suite
row enforces both sides).

| door (the ahabase CLI) | in the development tree | classification | evidence |
|---|---|---|---|
| doctor | yes | covered | the same door in both trees |
| init | yes (epic) | covered | the skeleton seam, the smaller net |
| llm | yes | covered | the model-access door |
| ontology | yes | covered | the Epic's ontology door |
| safe | no | ahabase-born | the secrets store was born in ahabase (safe://, the owner's terminal step) |
| story | yes | covered | the lifecycle door (mint/show/complete) |
| validate | in pieces (verify-file, verify-stdin) | folded | a top-level door in ahabase; the development tree carries the pieces as internals |
| verify | yes | covered | the consistency door |
| workspace | no (the folders exist, created by hand) | ahabase-born | the seven standard folders at the workspace root, created idempotently (AHA-0035); the development tree carries the folders but no door mints them |

That is the intended direction - the young package is the entropy
reduction over the development CLI, not a copy of it.
