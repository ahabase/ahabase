# AHABASE Priorities

> The current priorities of the Epic - one open period, a ranked numbered list.

**Type:** priorities
**Epic:** [AHABASE](AHABASE)
**Concept:** ontology-priority-blueprint (evolucean)

## Period

**P1** — 2026-11-08 · open · set by the Human 2026-11-08

The ranked list below is the Human's current intent for this Epic. Position is importance: rank 1 first. Rows have no lifecycle - stories serve rows, rows are not stories. This document is a current snapshot only, never a history log; closed periods are in git history (`git log --follow -- this file`), as everywhere in grid4d. A period ends when the Human replaces the list, not by date.

Every row serves one ruling - the incubation decision in the [AHABASE](AHABASE) Overview ("Incubator and proven selection", Human, 2026-10-30) with its Rule "one place per capability": a proven capability graduates into this package, passes the open-zone checks, and evolucean deletes its copy and consumes it back through declared seams. The named gap of each row is the evolucean copy of that capability - the copy the ruling says must not exist.

## Priorities

1. Close the safe area of the migration: make evolucean consume the ahabase safe — serves the incubation ruling; done looks like: every evolucean secret read and write goes through the ahabase safe's targets and evolucean's own secret handling is retired (the safe was born here, subepic ahabase-safe, so nothing migrates in - what ends is the evolucean copy; the per-account logins of AHA-0022 are the working seam)
2. Migrate the llm capability from evolucean into ahabase — serves the incubation ruling; done looks like: the llm connection core graduates - the graduation the config door already named as next (AHA-0021) - paths, proxy and provider selection live in ahabase and evolucean's llm layer consumes them
3. Migrate the grid4d infrastructure from evolucean into ahabase — serves the incubation ruling; done looks like: the format core - `_grid4d/` validation and patterns - lives in ahabase behind the one registry; the config door landed as pilot graduation 1 (AHA-0021); the story-lifecycle engine is row 8's, not this row's
4. Migrate the trust capability from evolucean into ahabase — serves the incubation ruling; done looks like: the trust-zone and containment checks run from ahabase and every graduation passes them there (the open-zone check of the graduation criteria)
5. Migrate the collaboration capability from evolucean into ahabase — serves the incubation ruling; done looks like: the collab fabric (chat, team log, receipts, presence) lives in ahabase and evolucean consumes it through declared seams, keeping only its method-specific tuning
6. Migrate the decision capability from evolucean into ahabase — serves the incubation ruling; done looks like: the decision capability (decision diagrams, option scorecards) lives in ahabase and evolucean's decision practice consumes it
7. Migrate the projection capability from evolucean into ahabase — serves the incubation ruling; done looks like: projection generation lives in ahabase (the declared ahabase-projections-pattern) and every Epic's projections run through it
8. Migrate the story capability from evolucean into ahabase — serves the incubation ruling; done looks like: the story layer (create, worktree, release, complete) lives in ahabase and evolucean's story practice consumes it, keeping its tuning

Structural gradients not named above stay under their automatic ordering; no row rules one out.

## Related

- [AHABASE](AHABASE) - the Vision every row serves
- ontology-priority-blueprint (evolucean) - the concept
- evolucean-priorities (evolucean pattern, via EVOLUCEAN-0552) - the form this document follows
- evolucean-shaping-idle-session-pattern (evolucean) - the idle procedure that reads the priorities first

---
