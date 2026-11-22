# Manifest Blueprint

> The description of every secret of a safe - name, store, purpose, owner, scope, expiry, rotation - without any value.

**Ontology:** [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) → Values → Manifest
**Placement:** base - a data structure with checkable invariants (no value, atomic writes)
**State:** implemented (the safe)

## Overview

**Manifest** = the list of a safe's [Safe Values](ontology-safe-value-blueprint) with their metadata. It lets software check health (every entry present, nothing expiring unseen) and lets a person rotate or recover, because it says what exists and where it came from - without holding any value.

## Attributes

- **Entry** - name, store, store key, purpose, owner, scope, created, expires, last rotated
- **Allowed consumers** (implemented, AHA-0007) - the executables, by absolute path with the package root they must stay inside, an optional argument prefix and the redirecting options they may use, allowed to receive the value through `safe run`; never a shell, an interpreter, a wrapper or a general-purpose network tool; an entry without them is usable by the owner only, interactively. Its protection against editing is part of the design ([implementation-ahabase-safe-threat-model-blueprint](implementation-ahabase-safe-threat-model-blueprint), T2 and T9)
- **Location** - the instance's configuration (`_config/safe.json`) or a path set for it

## Relations

- **describes** → [Safe Value](ontology-safe-value-blueprint) (one entry each)
- **names** → [Store](ontology-store-blueprint) per entry
- **read_by** → [Health Check](ontology-health-check-blueprint)

## Constraints

- **No value** - by design readable; it tells which secrets exist, never what they are.
- **Atomic and locked writes** - concurrent writers lose no entry.
- **Instance data** - a manifest belongs to its instance and is not committed to a shared repository; it is part of the target map an attacker would want (implemented: the safe refuses to write it inside a git working tree).

## Example

- `jira-api: store=keyring, purpose=issue tracker, expires=2027-01-31`

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rule 2
