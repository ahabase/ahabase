# Rotation Blueprint

> Replacing a secret's value at its provider, setting it in the safe and revoking the old one - done by the owner, after the switch.

**Ontology:** [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) → Access → Rotation
**Placement:** base - an ordered procedure whose record software keeps
**State:** implemented in part - setting an existing name records the rotation; the tested procedure per consumer is planned

## Overview

**Rotation** = the change of a secret's value: a new value is issued at the provider, set in the [Store](ontology-store-blueprint) through the safe (the [Manifest](ontology-manifest-blueprint) records the day), every [Consumer](ontology-consumer-blueprint) runs again, and the old value is revoked at the provider. Because a value lives in one place, a rotation is one change instead of a search for copies.

## Attributes

- **Trigger** - expiry, suspected disclosure, a switch completed, a lost store
- **Order** - issue new, set in the safe, run consumers, revoke old
- **Performer** - the owner

## Relations

- **replaces** → the value of a secret
- **follows** → a [Shadow Run](ontology-shadow-run-blueprint) and the switch of every consumer that reads it
- **recorded_in** → [Manifest](ontology-manifest-blueprint) (last rotated)

## Constraints

- **After the switch, never before** - a rotation before all consumers read through the safe would break the ones still reading copies.
- **The owner rotates** - software prepares and checks; the owner issues and revokes.
- **Shared values rotate in one window** - a value two instances use is rotated on both together.
- **Tested first on a non-critical secret** - with a rollback for every step.

## Example

- a token expires in 14 days: the health check warns; the owner issues a new one, sets it, runs the consumers, revokes the old one

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rule 7 and the later steps
