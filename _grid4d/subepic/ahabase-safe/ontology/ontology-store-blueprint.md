# Store Blueprint

> Where a secret's value lives - the user's own, preferably an established one, never a new vault of ours.

**Ontology:** [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) → Values → Store
**Placement:** base - a protocol with a shared contract test
**State:** implemented (keyring, env, memory); further stores planned

## Overview

**Store** = the place that holds secret values for their owner and hands them out on request: the operating system's credential store (macOS Keychain, Secret Service, Windows Credential Manager), read-only environment variables in CI, and later password managers and vaults. ahabase integrates existing stores behind one protocol; it does not build its own cryptography.

## Attributes

- **Kind** - `keyring` (the OS store, default), `env` (read-only, CI), `memory` (tests only); later stores as plugins
- **Operations** - get, set, delete, exists
- **Availability** - whether it can serve in the current context (a login session, a service, CI)

## Relations

- **holds** → [Safe Values](ontology-safe-value-blueprint)
- **named_in** → [Manifest](ontology-manifest-blueprint) entries (each entry names its store)

## Constraints

- **The user's own** - the value stays in a store the owner controls.
- **No own cryptography** - only established stores and libraries.
- **Context matters** - a store may be locked outside a login session; a consumer running as a service is tested in its own context.
- **Loss means rotation** - values are not backed up elsewhere; when a store is lost, every manifest entry is issued anew at its provider.

## Example

- the OS store through the `keyring` library on a workstation; environment variables of the CI provider in a pipeline

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rule 3 and the known limits
