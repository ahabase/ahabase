# Reference Blueprint

> `safe://NAME` - what configuration holds instead of a secret's value.

**Ontology:** [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) → Values → Reference
**Placement:** base - a syntax and its resolution rules, deterministic
**State:** implemented (the safe)

## Overview

**Reference** = a pointer to a [Safe Value](ontology-safe-value-blueprint) by name, written `safe://NAME`. Configuration, scripts and shared procedures hold references; the value is resolved only into the process that needs it. A reference is shareable: it says which secret is needed, not what it is.

## Attributes

- **Prefix** - `safe://`
- **Name** - the secret's name in the [Manifest](ontology-manifest-blueprint)

## Relations

- **points_to** → [Safe Value](ontology-safe-value-blueprint)
- **resolved_for** → [Consumer](ontology-consumer-blueprint): into its process only

## Constraints

- **Pass-through** - resolving a value without the prefix returns it unchanged, so a consumer switches one setting at a time.
- **Unknown name fails by name** - the error names the secret, never a value.
- **Process-scoped** - a resolved value goes into the child process's environment, never into the parent's output.

## Example

- `ahabase safe run --env JIRA_TOKEN=safe://jira-api -- jira-tool search ...`

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rules 1 and 4
