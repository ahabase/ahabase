# Output Watch Blueprint

> Catches a safe value that slips into a tool's output despite the guard and masks it in what the model sees - named, never repeated; the last layer, not a protection of the screen.

**Ontology:** [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) → Guards → Output Watch
**Placement:** base - matching known values and value shapes is deterministic
**State:** planned (reach established for Claude Code; other agents to be established)

## Overview

**Output Watch** = the third layer of protection. When a value reaches output anyway - an error message with a connection string, a log line, a configuration read - the watch recognizes it by the known values of the safe and by the value shapes of established scanners, and masks it before it reaches the model's context - and with it the model's provider and the agent's later steps. It does not keep the value off the user's screen: the tool has already run and printed. It reports the safe value's name and the place, never the value.

## Attributes

- **Signals** - known values of the safe (compared without storing them elsewhere), value shapes of scanners
- **Action** - mask in what the model sees, or warn where an agent's hooks cannot rewrite
- **Report** - name and place only

## Relations

- **complements** → [Agent Guard](ontology-agent-guard-blueprint)
- **produces** → [Scan Finding](ontology-scan-finding-blueprint) for what it caught
- **keeps** → [Boundary](ontology-boundary-blueprint)

## Constraints

- **Never repeats the value** - a report that showed it would be the leak.
- **Honest reach** - what an agent's hooks cannot rewrite is reported as a warning, not claimed as blocked. In Claude Code a hook after a tool call replaces only what the model sees; the tool has already run and the user's screen is not documented to change - so a value on a shared screen is stopped only by the guard before the command, or by the value not being there ([implementation-ahabase-safe-integration-blueprint](implementation-ahabase-safe-integration-blueprint)).
- **Last layer, not the first** - values that are not where an agent looks need no watch.

## Example

- a database error containing a password is masked before the model reads it, so the agent neither repeats it nor sends it on; the report says which safe value and which command. The same error was already visible in the terminal - on a shared screen only the guard before the command, or the value not being there, would have prevented it

## Related

- [safe-first-public-capability](safe-first-public-capability) - the motivating scenario
