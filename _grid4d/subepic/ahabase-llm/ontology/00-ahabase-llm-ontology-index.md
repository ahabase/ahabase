# ahabase-llm Ontology

> The model door's concepts: an access path to a language model is resolved, verified with a classified failure, switched with a backup, and discovered locally; its credential is a reference, never a value.

**Type:** Ontology Index
**Status:** defined - founded by [AHA-0024](AHA-0024); the implementation lands in the same story
**Scope:** ahabase-llm

## Purpose

This index carries the vocabulary of one capability: the model door. The Epic's ontology keeps the structure that spans capabilities ([00-ahabase-ontology-index](00-ahabase-ontology-index)); the safe's concepts live in [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index). A concept is here only when the code that lands needs it and it is robust and minimal.

## Taxonomy

### Position

- **extends:** [00-ahabase-ontology-index](00-ahabase-ontology-index) - the Epic's architecture (Door, Config) that the model door serves
- **scope:** how a tool reaches a language model - the one capability this subepic owns

### Facets

| Facet | Values | Purpose |
|-------|--------|---------|
| Route | Access Path | what is reached and how it authenticates |
| Trust | Verification | whether a route answers, and why not |
| Change | Settings Switch | moving the tool to a verified route, reversibly |
| Knowledge | Discovery Registry | which routes a machine can use |

### Hierarchy

```
ahabase-llm
├── ontology/          → this index and the four concept blueprints
├── implementation/    → implementation-ahabase-llm-blueprint
└── story/             → AHABASE-LLM (the subepic identity)
```

### Entry Points

| Use case | Start here |
|----------|------------|
| What a route is and how it authenticates | [Access Path](ontology-access-path-blueprint) |
| Why a route does not answer | [Verification](ontology-verification-blueprint) |
| Moving the tool to another route | [Settings Switch](ontology-settings-switch-blueprint) |
| Which routes this machine can use | [Discovery Registry](ontology-discovery-registry-blueprint) |

## Vocabulary

- [Access Path](ontology-access-path-blueprint) - a named route to a model (endpoint, model, authentication); the ladder it belongs to and its pin for one session
- [Verification](ontology-verification-blueprint) - a real minimal request through a path, and the class of its failure (auth, transient, cli, unavailable)
- [Settings Switch](ontology-settings-switch-blueprint) - changing the tool's settings to a verified path, with a backup and a restore
- [Discovery Registry](ontology-discovery-registry-blueprint) - the per-machine record of which paths exist and are usable, built from cheap local checks

## Concept map

Every concept names the code family that needs it; a concept with no family is removed.

| Concept | Code family it grounds |
|---------|------------------------|
| Access Path | path definitions, authentication resolution, current-path identity, the ladder and rescue order, the session payload |
| Verification | the preflight request, the failure classification and its hints, the cheap reachability sensors |
| Settings Switch | the verified switch, the atomic settings write, the backups and the restore |
| Discovery Registry | introspection of what runs, local availability, the registry |

## Relations

- An [Access Path](ontology-access-path-blueprint) authenticates with a [Reference](ontology-reference-blueprint) to a [Safe Value](ontology-safe-value-blueprint), or reads a variable the safe injects into the consumer process ([Consumer](ontology-consumer-blueprint)); it never holds a value.
- [Verification](ontology-verification-blueprint) checks an Access Path; a [Settings Switch](ontology-settings-switch-blueprint) happens only after a successful Verification of its target.
- A [Discovery Registry](ontology-discovery-registry-blueprint) lists Access Paths by machine and is stored in the instance's data directory, resolved by the [Config](ontology-config-blueprint) door.
- The model door is entered through the [Door](ontology-door-blueprint) `ahabase llm`, behind the one [Registry](ontology-registry-blueprint).

## Constraints

- A credential value MUST NOT appear in a path definition, a document, a log line or a backup; a path holds a reference or an injected variable.
- A path is switched to only after a successful Verification of that path.
- Discovery uses cheap local checks only: no network, no token spent.
- Per-machine data (the registry, the instance's own path variants, backups) stays with the instance and never travels with the code.
- What the method tunes (model choice for a task, the model catalogue, guidance texts, proxy and service management, local model runtimes, telemetry) is not in this subepic.

## Related

- [AHABASE-LLM](AHABASE-LLM) - the subepic identity
- [implementation-ahabase-llm-blueprint](implementation-ahabase-llm-blueprint) - how the concepts are built
- [00-ahabase-ontology-index](00-ahabase-ontology-index) - the Epic ontology this extends

---
