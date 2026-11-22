# Boundary Blueprint

> The line every person draws between their personal side and what they share - the condition of collaboration.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Trust and boundaries → Boundary
**Placement:** base - a declared line between personal and shared that software can keep
**State:** implemented in part - the safe keeps it for safe values; for knowledge and work it is planned

## Overview

**Boundary** = the line between a person's personal side and what they give to others. Collaboration needs every individual's boundary defined: a person shares freely only what is known to be separated from what is personal (Human, 2026-10-25). The personal side is the Personal [Trust Zone](ontology-trust-zone-blueprint) (zone 4) - the person and their own instances, with their private work; the secrets themselves sit deeper, in the Vault (zone 5), as values behind references; everything given to others is shared, and its zone says how far it travels. The same holds for an instance of a person and for a team: each has its own side and a shared side.

## Attributes

- **Owner** - the person (or instance, or team) whose boundary it is
- **Personal side** - what stays with the owner: secrets, private work, unpublished knowledge
- **Shared side** - what the owner gives, each piece with its zone
- **Crossing** - a move of something from the personal side to the shared side; always the owner's decision

## Relations

- **is_drawn_by** → the owner
- **places** → [Safe Value](ontology-safe-value-blueprint): safe values stay on the personal side
- **uses** → [Trust Zone](ontology-trust-zone-blueprint): the shared side is graded by zone
- **is_kept_by** → [Agent Guard](ontology-agent-guard-blueprint) and [Output Watch](ontology-output-watch-blueprint): an agent acting for the owner stays on the right side

## Constraints

- **Explicit** - a boundary that software must keep is declared, not inferred.
- **Crossing is the owner's** - no tool moves anything across the boundary on its own.
- **Share capabilities, not credentials** - two people or instances using the same service each keep their own credential; they share how the work is done, never the key to it.
- **Innermost first** - the safe draws the boundary first for secrets, where a mistake cannot be undone; the same question is then asked of knowledge, configuration and work.

## Example

- personal: a token in the user's OS store, a draft not yet shared
- shared: a `safe://NAME` reference in a team's configuration, a published procedure

## Related

- [ontology-trust-zone-blueprint](ontology-trust-zone-blueprint) - how far shared knowledge travels
- [safe-first-public-capability](safe-first-public-capability) - boundaries make sharing possible
