# Shadow Run Blueprint

> The proof, before a consumer switches, that the safe holds the same value as the source it reads today and that the consumer works through the safe.

**Ontology:** [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) → Access → Shadow Run
**Placement:** base - an equality proof and a control run, both deterministic
**State:** implemented in part - `safe compare` and `safe run` exist; the guided procedure is planned

## Overview

**Shadow Run** = running a [Consumer](ontology-consumer-blueprint)'s path through the safe next to its normal path, without depending on it. First the stored value is compared with the current source without showing either (`ahabase safe compare`); then the consumer runs once through `ahabase safe run` beside its normal run and both results are compared. Only a green shadow run lets the switch be proposed.

## Attributes

- **Comparison** - same or different, by constant-time digest comparison, printing neither value nor fingerprint
- **Context** - the consumer's own context (a service as a service, not from a terminal)
- **Control run** - one normal run and one run through the safe, results compared
- **Outcome** - green, red, or not possible in this context

## Relations

- **proves** → [Consumer](ontology-consumer-blueprint) ready to switch
- **compares** → the stored value with the current source
- **precedes** → the switch and, after it, a [Rotation](ontology-rotation-blueprint)

## Constraints

- **Nothing switches without it** - and nothing switches without the owner's consent after it.
- **The owner's step** - the comparison answers equality for any candidate, so it is run by the owner, interactively, with a limit of five comparisons of one name a minute (implemented, AHA-0007), and denied to an agent by the agent guard (planned) (threat model, T11).
- **No disclosure** - neither the value nor a fingerprint is printed; a false "same" is the worst outcome, so only line endings are stripped from a file and a URL is read raw.
- **In its own context** - a consumer without a login session is proven without one.

## Example

- `ahabase safe compare <enterprise-tool>-api --env <enterprise-tool>_API_KEY` answers `same`; one read-only tool command runs normally and through `safe run` with equal results

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rule 8
