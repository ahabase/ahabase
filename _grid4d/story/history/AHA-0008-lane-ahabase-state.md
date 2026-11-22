# AHA-0008 lane: the state of the ahabase Epic

> What the ahabase Epic is today - ontology, blueprints, code, tests, issues, releases - and where its parts do not yet meet.

**Lane:** ahabase state (work seat)
**Read:** repository ahabase/ahabase, main at the release of AHA-0007 (v0.0007.0.0000.00), story branch head d4436a7, 2026-10-26 06:45Z
**Story:** [AHA-0008](AHA-0008)

## Read

### Stories and releases

Seven stories released in two days (2026-10-24 to 2026-10-26), each with a tag: the Epic and plugin contract (AHA-0001), the safe (0002), compare (0003), the ontology (0004), the tool research (0005), the threat model (0006), the hardening (0007). 77 commits on main. Every story was reviewed on both instances; AHA-0007 took four rounds plus two deltas (the vanished-consumer guard and the one-letter abbreviations), with every home seat engaged.

### Ontology

The index and 16 concept blueprints (layers 2 and 3; layers 0, 1 and the basis of collaboration are named, not defined). Every concept states its Placement (all: base) and its State:

| State | Concepts | Count |
|---|---|---|
| implemented | Safe Value, Reference, Manifest, Store, Registry, Plugin, Health Check | 7 |
| implemented in part | Shadow Run, Consumer, Rotation, Door, Boundary | 5 |
| defined, check planned | Trust Zone | 1 |
| planned | Agent Guard, Output Watch, Scan Finding | 3 |

### Implementation blueprints and their lineage lines

| Blueprint | Implements (concepts) | Code line |
|---|---|---|
| architecture | Door, Registry, Plugin, Health Check | none |
| safe | Safe Value, Reference, Store, Manifest, Shadow Run, Rotation | `src/ahabase/safe.py`, `src/ahabase/cli_safe.py` |
| safe integration | Store, Scan Finding, Agent Guard, Output Watch, Consumer | none (decisions, no code yet) |
| safe threat model | Safe Value, Manifest, Agent Guard, Plugin | none (a model) |

### Code and tests

Five modules, 1,236 lines: `__init__`, `cli` (the door, `doctor`), `plugins` (registry, contract, loading), `safe` (stores, manifest, binding), `cli_safe` (the safe's commands). Two runtime dependencies (`click`, `keyring`). 61 test functions in four files, 98 collected cases with their parameters; the suite isolates through a temporary home and a guard keyring; mutation controls were run in every safe story.

### Issues and ideas

Four open issues on main - `epic-bootstrap-gaps-for-non-dbt-epics` (the evolucean tooling's gaps for a non-dbt Epic), `knowledge-map-links-a-document-of-another-repository` (a path-prefixed link the map hook writes), `open-zone-documents-link-into-the-closed-zone` (the two generators and the missing check, one file), `safe-set-keeps-a-carriage-return-from-stdin` - and a fifth on this story's branch, `safe-run-guard-member-without-a-test` (found after AHA-0007's release); one open idea (the safe as the first public capability).

## Gaps between the parts (read, counted by hand)

1. **Concepts without an implementation blueprint:** Trust Zone, Boundary (2 of 16). Both are implemented only through other concepts (the safe keeps the boundary for safe values; no zone check exists).
2. **Implementation blueprints without a Code line:** architecture (its code exists: `plugins.py`, `cli.py`), integration and threat model (no code of their own yet - they need `**Code:** none` to say so).
3. **Code without a Code line:** `plugins.py`, `cli.py` are named in the architecture blueprint's prose (its Structure section) but by no `**Code:**` line, so no software can trace them; no module carries an `Implements:` back-link in its docstring.
4. **No test-to-requirement trace beyond the story rows:** the stories' test documents select pytest tests by name (`-k`), which is a trace in one direction only; a renamed test silently drops out of a row's selection while the row still passes (pytest exits non-zero when nothing is selected, so a row fails - inferred from pytest's behaviour, not measured here).
5. **No generated projection of the Epic exists:** the identity has no `**CodeArtifacts:**` line, so the workspace's projections skip orphans, gradients and artifacts for this Epic (see the story's starting evidence).

## Inferred

- The Epic's knowledge is consistent and well reviewed, but its consistency is checked by people and by per-story test rows, not yet by software across the Epic: the five gaps above are exactly what a lineage check and the orphans projection would report.
- The safe is the most mature part (implemented, hardened, threat-modelled); the platform (doors other than the CLI, the MCP server, the plugin) and the knowledge format (layer 1) are not started - the plan's step 9.
- The pace (seven stories in two days, each with wide review) is sustainable only while each story stays small; AHA-0007's four rounds show the cost of a story that mixes much code with much documentation.

## Related

- [AHA-0008](AHA-0008) - the story
- [00-ahabase-ontology-index](00-ahabase-ontology-index) - the ontology read
