# Door Blueprint

> A way into ahabase - the CLI, the MCP server, the Claude Code plugin - each a view of the same registry.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Platform → Door
**Placement:** base - an interface without logic of its own
**State:** implemented in part - the CLI exists; the MCP server and the Claude Code plugin are planned

## Overview

**Door** = an interface through which a person or an agent uses ahabase. Every door shows the same [Registry](ontology-registry-blueprint): what a [Plugin](ontology-plugin-blueprint) registers is available through each of them. Many doors keep the barrier to start low for users with different starting points; one registry keeps them consistent.

## Attributes

- **Kind** - CLI (`ahabase`), MCP server (`ahabase serve`), Claude Code plugin (skills, hooks, settings)
- **Audience** - a person in a terminal, an agent through MCP, an agent inside Claude Code
- **Logic** - none of its own; a door translates, the registry acts

## Relations

- **exposes** → [Registry](ontology-registry-blueprint)
- **calls** → another door (the Claude Code plugin calls the CLI or the MCP server)

## Constraints

- **No logic in a door** - a capability lives once, behind the registry.
- **Same contract** - a command and its result mean the same through every door.
- **Open** - every door is part of the open package.

## Example

- `ahabase doctor` in a terminal and the `doctor` tool of the MCP server run the same checks

## Related

- [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint) - the layers
