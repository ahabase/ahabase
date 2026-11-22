# Plugin Blueprint

> A distribution that builds on ahabase and registers its capabilities into the registry - a method such as evolucean is one.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Platform → Plugin
**Placement:** base - a contract and its loading rules, tested
**State:** implemented

## Overview

**Plugin** = an installed distribution that declares an entry point in `ahabase.plugins` and registers commands and [Health Checks](ontology-health-check-blueprint) into the [Registry](ontology-registry-blueprint). A method is a plugin: it imports the package's format and services and adds its know-how; the package never imports a plugin. Installing a plugin means trusting its code; `doctor` lists each plugin with the distribution and version it came from.

## Attributes

- **Entry point** - `ahabase.plugins`, naming an object with `API_VERSION` and `register(registry)`
- **Distribution and version** - where it came from
- **State** - loaded, or failed with its reason

## Relations

- **registers_into** → [Registry](ontology-registry-blueprint)
- **imports** → the package (never the reverse)
- **extends** → base concepts, when the plugin is a method

## Constraints

- **Dependency direction** - a plugin imports the package; the package imports no plugin.
- **Robust loading** - an import error, a failure in `register` or an incompatible version is that plugin's problem; its partial registrations are rolled back; the next plugin still loads.
- **Trust is explicit** - a plugin runs with the user's rights; the user installs it by choice.
- **Safe access is declared** (designed) - a plugin states whether it uses the safe and which entries; undeclared access is refused and reported. It limits accidents and honest plugins, not a determined malicious one ([implementation-ahabase-safe-threat-model-blueprint](implementation-ahabase-safe-threat-model-blueprint), T3).

## Example

- a method distribution registers its story commands and its own health checks

## Related

- [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint) - the plugin contract
