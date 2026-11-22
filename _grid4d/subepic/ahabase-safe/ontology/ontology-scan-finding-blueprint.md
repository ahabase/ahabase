# Scan Finding Blueprint

> A place where a readable secret still lies - reported by name and place, never by value.

**Ontology:** [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) → Guards → Scan Finding
**Placement:** base - a read-only scan with a fixed report shape
**State:** planned (`safe scan`)

## Overview

**Scan Finding** = one result of `ahabase safe scan`: a shell profile that exports a token, a remote URL or URL rewrite carrying a credential, a configuration file or its backup with a value, a variable templated into a configuration, an agent transcript that once printed a value. Scanning is read-only and changes nothing - the discovery step a user takes before moving anything; it is built after the agent path is closed (threat model, rule 2). The value shapes come from established scanners.

## Attributes

- **Place** - file and line, or configuration key
- **Kind** - profile export, URL credential, configuration value, template reference, transcript
- **Name** - the variable or key name, if any
- **Consumers** - who reads it, where known

## Relations

- **points_to** → a [Consumer](ontology-consumer-blueprint)'s current source
- **feeds** → the inventory and the impact map before a [Shadow Run](ontology-shadow-run-blueprint)
- **produced_by** → a scan or an [Output Watch](ontology-output-watch-blueprint)

## Constraints

- **Names and places only** - no value and no fingerprint.
- **Read-only** - a scan never changes what it finds.
- **Before sharing** - a quick scan before a screen is shared or recorded shows what an agent could still display.

## Example

- `~/.zshenv: line 12: export DB_PASSWORD (profile export; consumers: database client, build tool)`

## Related

- [safe-first-public-capability](safe-first-public-capability) - the scan as the first part
