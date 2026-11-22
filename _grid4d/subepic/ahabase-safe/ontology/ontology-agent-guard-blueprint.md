# Agent Guard Blueprint

> Keeps an AI agent acting for a person from the commands and places that would show a secret value.

**Ontology:** [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) → Guards → Agent Guard
**Placement:** base - a rule set whose installation `doctor` can check
**State:** planned

## Overview

**Agent Guard** = the rule set that keeps an AI agent on the right side of its owner's [Boundary](ontology-boundary-blueprint): it may not read the stores' locations or the files that still hold values, and it may not run what prints a value (an environment listing, a profile read, a remote URL with a credential, a reveal). It is built from what each agent already offers - permission rules, a sandbox, hooks before a tool call - and checked by `doctor`. It applies least privilege (Saltzer and Schroeder, 1975) to an agent.

## Attributes

- **Agent** - the agent it guards (Claude Code first)
- **Denied places** - store locations, files still holding values
- **Denied commands** - commands that print values; by default also `ahabase safe get`, `ahabase safe set` and `ahabase safe compare` (an equality oracle, T11), and `ahabase safe run` except through the consumer binding (the agent path of prompt injection, [implementation-ahabase-safe-threat-model-blueprint](implementation-ahabase-safe-threat-model-blueprint), T2)
- **Network allow-list** - outbound hosts the bound consumers need, nothing else
- **Protected places** (designed) - no writes to the manifest or to bound consumers' configuration, no setting of the safe's override variables, no pseudo-terminal wrappers; `ahabase` and consumers matched by absolute path (threat model, T9 and T10)
- **Mechanism** - permission rules, sandbox, a pre-call hook, as the agent supports

## Relations

- **keeps** → [Boundary](ontology-boundary-blueprint)
- **complements** → [Output Watch](ontology-output-watch-blueprint): the guard prevents, the watch catches what slips through
- **checked_by** → [Health Check](ontology-health-check-blueprint)

## Constraints

- **Before the first wide-reach secret moves** - a store is no safer than files while an agent can read it through its own interpreter.
- **Existing mechanisms only** - no own sandbox; the agent's own permission rules, sandbox and hooks.
- **A change of the agent's settings is the owner's consent** - the guard is proposed, never installed silently.

## Example

- a pre-call hook refuses `printenv` and a read of a shell profile that still exports a token

## Related

- [safe-first-public-capability](safe-first-public-capability) - the three layers
