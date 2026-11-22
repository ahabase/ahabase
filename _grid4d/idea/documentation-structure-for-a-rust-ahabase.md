# Documentation Structure for a Rust ahabase

> The knowledge structure the ahabase CLI needs before its first Rust line: capabilities defined in the ontology, lineage through implementation blueprints down to the code, and generated projections keeping the whole chain honest from day one.

## Why now

The ahabase CLI is planned in Rust: one binary composing modules and their capabilities, built for macOS and Windows immediately. Documentation structure that arrives after the code does not arrive - evolucean measured this: 243 per-module implementation blueprints for 381 modules, 51% coverage, families rescued by facade claims. The structure must be standing before the first module, so every module meets it as ontology, not as a discovered gap.

## Facts to design against (measured in evolucean)

- **Ontology**: one flat folder, one file per concept (`ontology-<concept>-blueprint.md`), one hand-written index per scope (`00-<name>-ontology-index.md`: Taxonomy, Vocabulary, Relations, Constraints); placement is a breadcrumb line; links are bare stems resolved by basename across the whole tree; a sub-scope inherits the parent wholesale until it needs its own folder.
- **Implementation**: a blueprint per capability at the top level; per-module files under `cli/` started 1:1 and lost the race to module count - the sustainable shape ended up "a family shares one blueprint whose `**Code:**` names the family".
- **Lineage**: `**Implements:**` lines up, `**Story:**` origin, `**Code:**` down, and a docstring line in each module. Evolucean parses none of the code side; ahabase's lineage check is hard in both directions (every module claimed, every claim backed by a docstring line). Hard is the base's own rule: what software can validate, software validates.
- **The one gate that held**: capability grounding - every capability named by code must be defined in the ontology. Everything else drifted; that did not.

## The structure

```
_grid4d/
├── ontology/
│   ├── 00-ahabase-ontology-index.md        # the only hand-written map per scope
│   └── ontology-<concept>-blueprint.md     # one concept per file, flat
├── implementation/
│   ├── implementation-<capability>-blueprint.md   # one per capability (safe, doors, ...)
│   └── cli/
│       └── implementation-cli-<module>-blueprint.md  # Rust modules; a family shares one
├── pattern/          # only templates the CLI machine-reads (_behavior)
├── story/            # story workflow, unchanged
├── idea/  issue/     # unchanged
└── _generated/       # projections only - never hand-edited
```

## Contracts

1. **Concept → blueprint → code, one direction, both ends checked.** The ontology blueprint says WHAT a thing is, its attributes, relations, constraints and State; the implementation blueprint says HOW (Rules, Structure, Template, Example) and links up (`**Implements:**`) and down (`**Code:**`); each code module names its blueprint in its module docs (`//! Implements: <blueprint>` in Rust, `Implements:` in the Python docstring). The check validates both directions - an unclaimed module is red, a claim without a module is red. This is [Lineage](ontology-lineage-blueprint) made mechanical; in Rust the check becomes a subcommand of the CLI itself, so the tool validates its own documentation.
2. **A capability is defined in the ontology first.** A capability enters as a base concept: what it promises, its attributes, the [Health Check](ontology-health-check-blueprint) that measures it. The implementation blueprint's command/function table names it; the [Registry](ontology-registry-blueprint) registers it for every [Door](ontology-door-blueprint); `doctor` runs its check. A generated capabilities index is the projection that keeps code, registry and ontology saying the same thing - the one evolucean gate that held, hard from day one.
3. **Families share a blueprint.** One implementation blueprint per capability; a module family (one command group, one crate, one concern) is claimed by a single blueprint's `**Code:**` list; a module gets its own file only when it carries its own Rules. Coverage is measured by projection; an unclaimed module is a red finding, never a silent 51%.
4. **Projections from the first day, not only lineage.** The [Projection](ontology-projection-blueprint) concept already says generated views replace hand-written ones; the Rust era starts with: ontology map (already generated), lineage coverage, capabilities/artifacts index, story projections. Anything a projection can compute, no document says by hand.
5. **The index is the only hand-written map.** Taxonomy, Vocabulary, Relations, Constraints - one file per scope, extended when a concept is admitted (Placement criterion, Minimal constraint: a concept is defined when the next step builds on it, State says implemented / in part / planned).
6. **Portability rides along.** Every capability, test and doc statement follows [Portability](ontology-portability-blueprint): both OS variants in the same story, CI lanes as the measure, text I/O UTF-8 by name.

## Rust specifics

- `//! Implements:` module doc comments are the code-side lineage line; `**Code:**` names Rust module paths (crate::module), same as it names Python modules today.
- `implementation/cli/` mirrors the source tree 1:1 (module families sharing), so the structure a reader walks in code is the structure they walk in knowledge.
- The lineage and capability-grounding checks live in the CLI (a `verify`/`doctor` lane), so documentation consistency is measured by the product itself on every CI lane - the competence boundary (software validates, the LLM executes) applied to ahabase's own docs.

## Distribution (both OS, from the matrix)

Prebuilt binaries are the product's shape: one CI matrix (macOS aarch64/x86_64, Windows x64) builds and ships release artifacts; brew tap (macOS), winget/scoop (Windows), `cargo install` for Rust users. pip remains a transitional [Door](ontology-door-blueprint) while the Python package lives; the knowledge structure above does not depend on the packaging channel.

## First story shape (proposal)

A Shaping story that: admits the Capability concept (base placement), states the Rust lineage contract (concept → blueprint → `//! Implements:`), and delivers the first two projections (lineage coverage, capabilities index) - small, measured, and standing before the first Rust module.

## Open questions

- One workspace with capability crates, or one crate with modules - and does the `cli/` knowledge folder mirror crates (subfolders) or modules (flat families)?
- Where does a plugin (a method) document its capabilities - its own `_grid4d/` under the [Plugin](ontology-plugin-blueprint) contract; what exactly the base index names of a plugin and what it must not.
- The Python→Rust transition order: which capability ports first (the safe is the candidate - smallest surface, hardest portability constraints, already measured on three lanes).

## Related

- [ontology-lineage-blueprint](ontology-lineage-blueprint) - the declared path this structure makes mechanical
- [ontology-projection-blueprint](ontology-projection-blueprint) - generated views, never hand-written
- [ontology-registry-blueprint](ontology-registry-blueprint) - the one list capabilities register into
- [ontology-capability references in the architecture](implementation-ahabase-architecture-blueprint) - base and method in code
- [safe-first-public-capability](safe-first-public-capability) - why the safe ports first
