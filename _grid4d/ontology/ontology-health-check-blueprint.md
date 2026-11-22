# Health Check Blueprint

> A named check that `doctor` runs - of the package, the safe or a plugin - reporting ok or a problem.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Platform → Health Check
**Placement:** base - a named check with a fixed result shape
**State:** implemented; the run at session start is planned

## Overview

**Health Check** = a function registered under a name that answers whether a part works, with a short detail. `ahabase doctor` runs every check of the [Registry](ontology-registry-blueprint) and exits non-zero when one fails. The safe's check reports missing entries and secrets expiring within 14 days; a plugin adds its own.

## Attributes

- **Name** - unique in the registry (`safe` is the package's)
- **Result** - ok or a problem, with a detail that never carries a secret value

## Relations

- **registered_in** → [Registry](ontology-registry-blueprint)
- **reads** → [Manifest](ontology-manifest-blueprint) (the safe's check)

## Constraints

- **Independent** - a failing check never skips the next.
- **No values** - details name, never reveal.
- **Early** (planned) - the safe's check is to run at session start too, so expiry is announced, not discovered by a failing workflow.

## Example

- `check safe: ok - 4 secrets, all present`

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rule 6
