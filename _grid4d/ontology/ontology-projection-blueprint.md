# Projection Blueprint

> A view of an Epic's knowledge generated from its documents - never written by hand, and the same bytes every time it is generated from the same sources.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Knowledge structure → Projection
**Placement:** base - a deterministic rendering of declared structure; checkable by regeneration
**State:** implemented in part - the ontology map (`ahabase ontology graph`, AHA-0009); further projections planned
**Story:** [AHA-0009](AHA-0009)

## Overview

**Projection** = content derived from an Epic's documents by a generator: a map, a table, a report. It is declared by the Epic (its projections pattern), written by the generator only - into its own file or between markers inside a document - and idempotent: generating it again over its own output changes no byte. That property makes "never hand-written" checkable: a stale or hand-edited projection differs from what the generator writes.

## Attributes

- **Source** - the documents it is generated from (for the ontology map: the index's Vocabulary and every concept's Relations)
- **Place** - a file of its own, or a block between `<!-- name:begin -->` and `<!-- name:end -->` markers in a document
- **Generator** - the command that writes it (`ahabase ontology graph`)
- **Check** - the same command with `--check`: exit 1 when the projection differs from what would be generated

## Relations

- **run_by** → [Door](ontology-door-blueprint) - `ahabase ontology graph` on the CLI
- **declared_by** → the Epic's projections pattern (`ahabase-projections-pattern`)

## Constraints

- **Generated only** - nobody edits a projection by hand; a fix goes into its sources.
- **Idempotent** - same sources, same bytes.
- **Declared** - a generator writes only what the Epic declares; an Epic that declares no page of a method's generator gets none.

## Example

- The ontology map in [00-ahabase-ontology-index](00-ahabase-ontology-index): a mermaid flowchart, one subgraph per facet, one typed edge per relation.

## Related

- [implementation-ahabase-transparency-blueprint](implementation-ahabase-transparency-blueprint) - how the ontology map is generated
- [ahabase-projections-pattern](ahabase-projections-pattern) - what this Epic declares
