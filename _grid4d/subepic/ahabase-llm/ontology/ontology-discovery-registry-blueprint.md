# Discovery Registry Blueprint

> What this machine can actually use: the routes that exist here, found without the network.

**Ontology:** [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index) → Knowledge → Discovery Registry
**Placement:** base - a record per machine and the rule "cheap local checks only" are structure software can verify
**State:** defined; the implementation lands in AHA-0024

## Overview

**Discovery Registry** = the per-machine record of which [Access Paths](ontology-access-path-blueprint) are usable on this machine. Discovery introspects what the tool actually runs and assesses each known path with cheap local checks only: whether a variable is set, a credential file or login is present, a native provider flag is on. It uses no network and spends no token; a network check is [Verification](ontology-verification-blueprint)'s job, taken with consent.

The registry is stored in the instance's data directory (resolved by the [Config](ontology-config-blueprint) door) and never travels with the code: a machine records only its own paths.

## Attributes

- **Machine** - the identity of the machine the record belongs to
- **Path id** - the path assessed
- **Available** - whether the local checks found what the path needs
- **Evidence** - the name of the check that decided (never a value)
- **Checked at** - when the assessment ran

## Relations

- **lists** → [Access Path](ontology-access-path-blueprint)
- **stored_by** → [Config](ontology-config-blueprint) - the instance's data directory

## Constraints

- Discovery performs local checks only; presence is checked, a credential value is never read.
- A record describes one machine; another machine's record is never read as this machine's.

## Related

- [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index) - the vocabulary

---
