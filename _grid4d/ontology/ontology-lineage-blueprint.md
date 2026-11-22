# Lineage Blueprint

> The declared path from a concept to the code that implements it and back - and the check that the knowledge and the code still say the same.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Knowledge structure → Lineage
**Placement:** base - a deterministic join over declared fields; structure that software verifies, no know-how
**State:** implemented - `ahabase verify` at Epic scope (AHA-0009)
**Story:** [AHA-0009](AHA-0009)

## Overview

**Lineage** = the chain concept → implementation blueprint → code module, read only from declared fields, and the reverse chain module → blueprint through the module's docstring. It answers "which code implements this concept" and "which knowledge explains this module", and it finds where the two have drifted apart. It is a reflexion model: what the knowledge declares is compared with what the code is, and every difference is named by its class.

## Attributes

- **Concept** - an `ontology-*-blueprint` with its `**State:**` line (the State is read from the concept's own blueprint)
- **Implementation blueprint** - names its concepts in `**Implements:**` and its code in `**Code:**`
- **Code line** - module names relative to the package declared by the Epic's `**CodeArtifacts:**` (`safe, cli_safe`; a nested module as `sub.module`), or `none (document blueprint)`
- **Back-link** - an `Implements: implementation-...-blueprint` line in a module's docstring
- **Class of a finding** - an absence (concept without implementation), a document blueprint, or one of six divergences: a State claiming "implemented" with no blueprint, an Implements link to a missing concept, no Code line, a Code line naming a missing module, a module no Code line names, a missing or wrong back-link

## Relations

- **run_by** → [Door](ontology-door-blueprint) - `ahabase verify` on the CLI
- **complements** → [Projection](ontology-projection-blueprint) - the projection shows the structure, the lineage checks it

## Constraints

- **Declared only** - no name guessing: a join exists only where a field states it.
- **Absences are not divergences** - a concept without implementation is reported with its State and never fails the check when the State admits it (planned, defined, implemented in part); a document blueprint is its own class and never fails.
- **A State is a declaration too** - a State that says "implemented" (not "in part") while no blueprint implements the concept contradicts the lineage and fails (local review of AHA-0009).
- **Divergences fail** - any of the six makes `ahabase verify` exit 1.
- **First verified instance** - the package's own Epic; the core appears in its own lineage.

## Example

- `ABSENCE concept-without-implementation: ontology-trust-zone-blueprint (State: defined; the zone check is planned)`
- `DIVERGENCE back-link: plugins - no 'Implements:' line in its docstring`

## Related

- [implementation-ahabase-transparency-blueprint](implementation-ahabase-transparency-blueprint) - how it is computed
- [AHA-0008-lane-transparency](AHA-0008-lane-transparency) - the design and the measured prototype
