# Settings Switch Blueprint

> Moving the tool to a verified route, with a backup that can always be restored.

**Ontology:** [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index) → Change → Settings Switch
**Placement:** base - an atomic write, a backup and a restore are structure software can verify
**State:** defined; the implementation lands in AHA-0024

## Overview

**Settings Switch** = changing the tool's settings so that it points at a different [Access Path](ontology-access-path-blueprint). The switch happens only after a successful [Verification](ontology-verification-blueprint) of the target. The settings file is written atomically after a backup of its previous content; any backup can be listed and restored. Output of a switch is redacted: it shows what changed, never a credential value.

A session that needs another route without changing the machine uses the path's pin instead of a switch.

## Attributes

- **Target** - the path switched to
- **Backup** - the previous settings, kept before every write, named by time
- **Outcome** - switched, refused (the verification failed, with its class), or restored

## Relations

- **requires** → [Verification](ontology-verification-blueprint)
- **targets** → [Access Path](ontology-access-path-blueprint)

## Constraints

- No write without a prior successful Verification of the target.
- No write without a backup of the previous content.
- The written settings hold a reference or a key helper for the credential, never a literal value; no backup holds one that the previous settings did not already hold.
- A restore verifies the backup parses before it replaces the settings.

## Related

- [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index) - the vocabulary

---
