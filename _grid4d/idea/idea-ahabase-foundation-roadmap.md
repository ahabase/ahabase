# ahabase foundation roadmap

> The ordered steps that build the foundation of ahabase - the open package, its safe, its guards and its zones - reconciled against the state after seventeen stories; this extract is the one source of truth for this Epic.

**Status:** open
**Source:** consolidation session with the Human, 2026-10-31 ([AHA-0017](AHA-0017)); this extract consolidates the plan the method incubated and supersedes it for this Epic (the closed-side original is the method's to retire - its pointing here is the method's task, per the link rule)

## Decisions this roadmap carries

- **Architecture** (Human, 2026-10-24): the open `ahabase` package never imports a method; a method builds on the package and plugs in through entry points; one registry behind every door (CLI, MCP server, Claude Code plugin). Private until the first release.
- **Base and method** (Human, 2026-10-25): a concept belongs here when it describes structure software can verify; what enters the open zone never goes back.
- **Secrets** (Human, 2026-10-24): changing how secrets are stored or used happens only with proven end-to-end function, a known impact on every consumer, a tested rotation, one consumer at a time, each step with the Human's consent; rotation is performed by the Human.
- **Incubator and proven selection** (Human, 2026-10-30, [AHA-0011](AHA-0011)): evolucean stays the private incubator; a proven capability graduates here ([graduation-criteria](graduation-criteria)); the incubator deletes its copy - one place per capability.
- **Ontology shape** (Human, 2026-10-31, [AHA-0017](AHA-0017)): the Epic ontology carries architecture only; a capability's concepts live in its subepic ontology ([implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint), Ontology shape).
- **History stays as it is** (Human, 2026-10-23): no rewrite of historical stories or git history. Human rulings are recorded by their meaning, never quoted; every document is English.

## Done

| Step | Where |
|---|---|
| The Epic, package architecture, registry and plugin contract | [AHA-0001](AHA-0001) |
| The safe: secrets mechanism, pluggable backends, references not values - nothing switched | [AHA-0002](AHA-0002) |
| `safe compare`: fingerprint comparison, never printing a value | [AHA-0003](AHA-0003) |
| The open ontology: package, safe, trust zones, boundaries | [AHA-0004](AHA-0004) |
| Safe research: existing tools per concept, integrate-or-write | [AHA-0005](AHA-0005) |
| Safe threat model: assets, attackers, vectors, controls, design rules | [AHA-0006](AHA-0006) |
| Safe hardening: consumer binding, minimal child environment, reveal by a person only, manifest protection | [AHA-0007](AHA-0007) |
| Foundation review: both Epics, plan realism, ontology quality (team, two instances) | [AHA-0008](AHA-0008) |
| Transparency: lineage declarations, ontology graph, Epic-scope lineage in `ahabase verify` | [AHA-0009](AHA-0009) |
| Identity states Infrastructure true | [AHA-0010](AHA-0010) |
| Direction recorded: safe for all sensitive information, open tools and closed knowledge, reciprocity, incubator | [AHA-0011](AHA-0011) |
| Safe targets and rotation in one place | [AHA-0012](AHA-0012) |
| Refresh proven by the stored value; git credential read-back glue in safe.py | [AHA-0013](AHA-0013) |
| Safe on Windows: lock, platform dispatch, exec, prompts, permissions, CI parity (three lanes) | [AHA-0014](AHA-0014) |
| Projections declared (concepts, issues), generation proved, open-zone link check | [AHA-0015](AHA-0015) |
| Capabilities: taxonomy, code tags, verify gates, vocabulary bridge | [AHA-0016](AHA-0016) |
| Consolidation: ideas captured, ontology shape decided, naming prefixes, this roadmap | [AHA-0017](AHA-0017) |

## Next, in order

| # | Step | Precondition | Gate |
|---|---|---|---|
| 1 | Inventory of every secret and its consumers; impact map (analysis only, no value read) | the safe exists | none |
| 2 | Verify the release path reads the GitHub account from the registry (the identity carries it; the reading is unverified) | - | none, before any token switch |
| 3 | Shadow run per consumer (resolve through the safe next to the current path, compare, do not use) | 1 | Human consent per consumer |
| 4 | Rotation performed by the Human, non-critical token first, rollback per step; GitHub tokens shared with the home instance rotate in one joint window | 3 | Human performs it |
| 5 | Switch one consumer at a time, control run before and after; afterwards the transcripts scan - values printed in past sessions listed, the Human decides per secret | 4 | Human consent per switch |
| 6 | Agent boundary: permission rules, sandbox and hooks for the stores' locations | 1 | Human consent (settings change) |
| 7 | Bootstrap gaps for non-dbt Epics | - | [epic-bootstrap-gaps-for-non-dbt-epics](epic-bootstrap-gaps-for-non-dbt-epics) |
| 8 | Quotes by meaning in current documents; automatic language check of added lines | - | none |
| 9 | Subepic adoption: create `ahabase-safe`, move the capability blueprints, register the subepics, teach the gates where each index lives | the shape decision (done) | [AHA-0017](AHA-0017) R2 |
| 10 | The grid4d format graduates here ([graduation-criteria](graduation-criteria)); then the MCP server (`ahabase serve`), the Claude Code plugin, the method registered as a plugin - one capability at a time | 9 | Human review of each architecture step |
| 11 | Decision panels: visualize and document the scorecards and diagrams decisions are made on - the Human's declared current main task; incubated in the method's decision subepic (founded 2026-10-30), the base's part is what graduates | - | [idea-decision-panels](idea-decision-panels) |
| 12 | Progressive capability configuration | - | [idea-progressive-capability-configuration](idea-progressive-capability-configuration) |
| 13 | Trust zones: declaration of a zone per document, the protective default, the zone check guarding a distribution | - | Human decides each outward move |
| 14 | Public release | license (Apache-2.0), README, CI matrix, tests done; ahead: SECURITY.md, CONTRIBUTING.md, containment/zone/secret scans over the whole history | Human decision |

Release mechanics (absorbed from the consumed architecture idea): PEP 541 forbids name squatting, so the first release is real; Trusted Publishing from GitHub Actions with attestations; TestPyPI first; the upload is an outward publication on the Human's instruction only. MCP timing is decided - CLI now, MCP server and plugin next (step 10).

## Capability inventory

The thirteen key capabilities the Human named (2026-10-31), each with where it lives today:

| Capability | Lives today |
|---|---|
| Credential safe | this package (`ahabase safe`, AHA-0002..0014) |
| Knowledge taxonomy space (the grid4d format) | declared and read here; the full format and workflow still in the method (step 10) |
| Generated projections | the method's generators; this Epic declares its minimal set (AHA-0015) |
| Epic isolation and plug-and-play Epics | the contract here (AHA-0001); the runtime tooling in the method |
| Any change driven by story increment in git | the method (story workflow) |
| Pattern driven improvements | the method |
| Story test suites | the method |
| Parallel work in worktree | the method |
| CLI verification and testing | this package (`ahabase verify` and its gates, AHA-0009/0016) beside the method's own |
| Team collaboration of LLM sessions and tools (scorecard) | the method (collaboration subepic); the scorecard and diagram direction is its decision subepic, tracked as [idea-decision-panels](idea-decision-panels) |
| Subepic layers to focus a direction | format concept proven in the method; adopted here 2026-10-31 (step 9 executes) |
| Cost optimization/monitoring | not yet (partial pieces in the method's LLM layer) |
| Sensors and metrics | the method (distribution layer) |

## Related

- [AHABASE](AHABASE) - the Epic, its Rules and Vision
- [graduation-criteria](graduation-criteria) - how capabilities arrive here
- [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint) - the architecture and the ontology shape
- [safe-first-public-capability](safe-first-public-capability) - where the safe goes next
