# Access Path Blueprint

> A named route to a language model: where it is, which model it serves and how it authenticates - never the credential itself.

**Ontology:** [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index) → Route → Access Path
**Placement:** base - the shape of a route and the resolution of its identity are structure software can verify
**State:** defined; the implementation lands in AHA-0024

## Overview

**Access Path** = one way a tool reaches a language model: through a local gateway, a direct provider endpoint, a subscription login, a cloud provider's native route, or any other compatible endpoint. A path has an identity (its id), an endpoint, the model it serves (and optionally a model per tier), and an authentication.

The door answers three questions about paths: which paths are defined, which one the tool currently points at (its **identity in force**, read from the tool's settings and environment), and in which order paths are tried when one fails (the **ladder** with its rescue order). The ladder's shape belongs to the base; which paths an instance lists, and in which order, is that instance's own data.

A path can be **pinned** for one session: the session starts through that path without touching the machine's settings, carrying the path's environment and a key helper reference. The pin is the path in force for the session, not a separate concept.

## Attributes

- **Id** - the stable name of the path
- **Endpoint** - the base address, or none where the route is native to the tool
- **Model** - the single model, with an optional model per tier
- **Authentication** - how the path proves itself: a [Reference](ontology-reference-blueprint) to a [Safe Value](ontology-safe-value-blueprint), a variable the safe injects into the consumer process, the subscription login, or the cloud provider's own credential chain (presence is checked, the value is never read)
- **Kind** - gateway, direct endpoint, subscription, cloud-native, custom
- **Paid** - whether using the path costs money; a paid path is used only with explicit confirmation and never as a fallback

## Relations

- **authenticates_with** → [Reference](ontology-reference-blueprint) - never a literal value
- **checked_by** → [Verification](ontology-verification-blueprint)
- **targeted_by** → [Settings Switch](ontology-settings-switch-blueprint)
- **listed_in** → [Discovery Registry](ontology-discovery-registry-blueprint)

## Constraints

- A definition with a literal credential is refused; the credential is a reference or an injected variable.
- The ladder lists a path at most once; a paid path is never in the rescue order.
- The identity in force is derived from the tool's settings and environment, never stored separately.

## Related

- [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index) - the vocabulary

---
