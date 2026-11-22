# Safe Value Blueprint

> A value that grants access - a token, a password, a key - kept in the safe, and therefore never in a document, a repository or an output.

**Ontology:** [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) → Values → Safe Value
**Placement:** base - what it is and that it never leaves its store is structure software verifies
**State:** implemented (the safe)

## Overview

**Safe Value** = a value whose knowledge grants access to something: an API token, a password, a private key, a connection string with credentials - what is commonly called a secret. It belongs to the Vault of the [Trust Zone](ontology-trust-zone-blueprint) (zone 5): it lives only in the owner's [Store](ontology-store-blueprint); everything else refers to it by name. The concept is named after the mechanism that keeps it (Human, 2026-10-25).

## Attributes

- **Name** - unique within the owner's safe, used in a [Reference](ontology-reference-blueprint)
- **Value** - never printed, never written outside the store
- **Purpose, owner, scope** - what it is for, who answers for it, what it grants
- **Expiry and last rotation** - recorded in the [Manifest](ontology-manifest-blueprint)

## Relations

- **lives_in** → [Store](ontology-store-blueprint) (exactly one)
- **described_by** → [Manifest](ontology-manifest-blueprint) entry, without the value
- **referenced_by** → [Reference](ontology-reference-blueprint)
- **read_by** → [Consumer](ontology-consumer-blueprint) (0:N) - only the consumers its manifest entry allows (implemented)
- **replaced_by** → [Rotation](ontology-rotation-blueprint)

## Constraints

- **Nothing outside the store** - not in configuration, documents, repositories, logs, transcripts or output.
- **A name is not the value** - names and metadata may be shared; values never.
- **No fingerprint either** - a hash of a short value can be guessed offline, so it is not shown.
- **Revealed by a person only** (implemented, AHA-0007) - showing a value needs an interactive terminal and the name typed as confirmation. A pseudo-terminal wrapper passes the terminal check, so against an agent the reveal is guarded by the agent guard and the sandbox, not by the check alone (threat model, T2).

## Example

- `jira-api` - the value lives in the OS store; the configuration says `safe://jira-api`

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - the mechanism
