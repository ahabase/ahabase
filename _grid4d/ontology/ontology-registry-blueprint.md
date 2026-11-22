# Registry Blueprint

> The one list of commands, health checks and tools behind every door.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Platform → Registry
**Placement:** base - a versioned API with tested invariants
**State:** implemented (commands and checks); MCP tools planned

## Overview

**Registry** = the place where the package's own capabilities and every [Plugin](ontology-plugin-blueprint)'s capabilities are registered: commands, [Health Checks](ontology-health-check-blueprint) and, later, MCP tools. Every [Door](ontology-door-blueprint) reads it. Its API carries a version, so a plugin states which version it needs.

## Attributes

- **Commands** - by name
- **Checks** - by name
- **API version** - the major version a plugin must match
- **Reserved names** - the package's own, taken before any plugin loads

## Relations

- **read_by** → [Door](ontology-door-blueprint)
- **filled_by** → the package and [Plugins](ontology-plugin-blueprint)

## Constraints

- **Nothing overwritten** - a taken name is a plugin's problem, recorded and reported, never a replacement.
- **Read-only views** - a plugin registers through the API, never by editing the registry.
- **Versioned** - an incompatible API version is refused with a reason.

## Example

- the package reserves `safe` and `doctor`; a plugin adds `hello` and a check `example`

## Related

- [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint) - rules 3 and 4
