# Consumer Blueprint

> A program or process that reads a secret - the unit in which credentials move to the safe, one at a time.

**Ontology:** [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) → Access → Consumer
**Placement:** base - kinds and states of a consumer are structure; the order of a migration follows a published procedure
**State:** implemented in part - bound with `safe bind` (AHA-0007); inventoried by hand today, found by `safe scan` when it exists (planned)

## Overview

**Consumer** = anything that reads a [Safe Value](ontology-safe-value-blueprint) to do its work: a tool with its own configuration, a program reading an environment variable (a database client, a build tool), git over https, a service started without a terminal, a CI job. Before a consumer switches to a [Reference](ontology-reference-blueprint), its current source is known, its impact is known and a [Shadow Run](ontology-shadow-run-blueprint) has proven equality.

## Attributes

- **Kind** - own configuration, environment variable, git credential, service (no login session), CI
- **Current source** - where it reads the value today (a profile export, a configuration file, a remote URL, a templated variable)
- **Blast radius** - what stops working if it fails
- **State** - inventoried, shadow-run, switched, old source removed

## Relations

- **reads** → [Safe Value](ontology-safe-value-blueprint)
- **proven_by** → [Shadow Run](ontology-shadow-run-blueprint) before the switch
- **found_by** → [Scan Finding](ontology-scan-finding-blueprint)

## Constraints

- **One at a time** - consumers switch one by one, least critical first, each with a control run and a rollback.
- **The old source stays until proven** - it is removed only after the new path is green and the owner agrees.
- **Templated sources count** - a variable referenced from a configuration template is a consumer of that variable.
- **Bound, released code only** - a consumer is bound as an installed, released command; a copy under development in a story's worktree is never bound and runs on fictional values (threat model, T9).

## Example

- a database client reading a password from an environment variable that a shell profile exports

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - consumers by kind
