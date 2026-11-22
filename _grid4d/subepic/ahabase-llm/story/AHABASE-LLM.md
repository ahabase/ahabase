# AHABASE-LLM

> The model door: how a tool finds, checks and uses the way to a language model - an access path resolved, verified before it is trusted, switched with a backup, and discovered on the machine - without a credential ever sitting in a document or in the clear.

**Type:** SubEpic
**Inherits:** ahabase
**StoryPrefix:** AHA-LLM-
**CodeEvidence:** parent

## Overview

The llm connection core is the second capability subepic of ahabase, after the safe. By the Epic's shape rule a concrete capability's concepts live in its own subepic, so the Epic ontology keeps only the architecture and this subepic carries the vocabulary of the model door.

What the model door is: a tool that works with a language model reaches it through an **access path** (a gateway, a direct endpoint, a subscription login, a cloud provider's native route). The door resolves which path is in force, **verifies** a path with a real minimal request and says why it fails, **switches** the tool's settings to a verified path with a backup that can be restored, and **discovers** which paths a machine can use with cheap local checks only. A path's credential is always a reference to a value in the safe or a variable the safe injects into the consumer process; no value is written into a document, a definition or a log.

What stays with the method (tuned to how work is done well, not structure software can verify): the choice of a model for a task, the model catalogue, the hook guidance texts, the proxy and service management, local model runtimes and telemetry. The stories of this subepic are minted under the prefix `AHA-LLM-`.

## Related

- [AHABASE](AHABASE) - the parent Epic
- [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index) - the model door's concepts and their map
- [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) - the safe, whose references the model door's paths hold

---
