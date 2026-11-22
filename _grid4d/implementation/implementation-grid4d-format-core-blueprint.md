# ahabase Grid4d Format Core Blueprint

> The basics of Priorities row 3: an Epic's `_grid4d/` tree validated namingly, and the pattern templates the story engine mints from - identity self-registered by the def file, no parallel configuration.

**Implements:** [ontology-grid4d-blueprint](ontology-grid4d-blueprint) - within [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint)
**Story:** [AHA-0030](AHA-0030)
**Code:** grid4d, cli_grid4d

## Overview

One door over one reading of the Epic's tree, standard library only (click for the door): `ahabase validate [--root DIR]` validates folders, identity, naming, structure and links, and every violation prints as `rule: path - detail` - the class, not a boolean. The surface was frozen by the AHA-0030 checkpoint-0 design review (the story's Notes carry every fold).

## Rules

1. **The def file is the registration** - Read identity only from `_grid4d/story/<NAME>.md` (`**Type:** Epic` + `**StoryPrefix:**`); strip one optional trailing dash from the prefix (`prefix_from`, the one home of the prefix law). Reason: identity that registers itself needs no registry beside the tree (the Human's 2026-11-20 ruling).
2. **Split identity from the package** - `**CodeArtifacts:**` is optional; absent means a knowledge-only Epic whose code-consuming surfaces (lineage modules, capabilities scan) see no package. Reason: the loader's raise-without-`CodeArtifacts` was the measured R4 blocker - the core never needs a code package to validate knowledge.
3. **Derive the story grammar from the prefix** - `<PREFIX>-<number>[-tests|-knowledge-map|-artifact-map].md`, nothing hardcoded. Reason: the evolucean copy's literal `^(DSDENG-|EVOLUCEAN-|...)$` is a containment and a self-registration violation in a public package.
4. **Report the unknown** - An unknown folder, a misnamed artifact, a broken subepic index, a duplicate name, a missing section, an unresolved link: each is a `Finding(rule, path, detail)`. Reason: the evolucean copy silently ignores a document no type matches; silence is not validity (new surface, not a port).
5. **Resolve patterns whole-file, first match wins** - The subepic's `subepic/<s>/pattern/<s>-<type>.md`, then the Epic's `_grid4d/pattern/<epic>-<type>.md`, then the package's name-neutral default, looked up last. Reason: no per-key merge exists in the minting path, and "key" is undefined for markdown (checkpoint 0, seat c020eeb4).
6. **Fill only the provided keys** - `fill` replaces the provided placeholder keys; every other name stays verbatim. Reason: an unknown placeholder must surface in review, not vanish.
7. **Take structure from the pattern** - A document's required sections are the `##` headings of its resolved template; `story/history/` is structure-exempt, `_archive/` and `_generated/` skipped. Reason: archived documents predate sections (measured: the kept history stories lack `## References`), and the archive holds historical names.
8. **Call the one link checker** - Fold `containment.compute`'s unresolved links into findings; the generator exceptions it carries are the evolucean practice's names, harmless on a consumer tree. Reason: one implementation, two entry points; a second checker would drift.
9. **Fail closed at the door** - A tree that is not an Epic reports as an `identity` finding with exit 1; exit 0 holds, 1 findings, 2 a usage problem. Reason: the consumer leg's expected-failure rows must be able to match a broken tree (checkpoint 0, seat b39ec132).
10. **Init writes what only a fresh tree needs** - `ahabase init NAME [--prefix NS]` creates the folder skeleton and the identity file from the package's epic pattern (no tree exists yet, so nothing can override it), declares NO `**CodeArtifacts:**` line (the loader reads one as a real declaration - measured; the line is the consumer's to add when the Epic carries code), and refuses an existing `_grid4d/`. Reason: the self-registration starts at the pattern; init never touches a tree that already is one.

## Template

The modules and their purposes:

| Path | Purpose |
|------|---------|
| `src/ahabase/grid4d.py` | the format core: `Finding`, `validate(epic)`, `init(root, name, prefix)`, `pattern_template(epic, type, subepic)`, `fill(template, values)` |
| `src/ahabase/cli_grid4d.py` | the doors: `ahabase validate [--root DIR]`, `ahabase init NAME [--prefix NS]` |
| `src/ahabase/patterns/*.md` | the name-neutral default templates: epic, story, tests, knowledge-map (package data, pinned in the containment allowlist, AHA-0030 R3) |
| `src/ahabase/epic.py` | the identity split: `prefix_from`, optional `CodeArtifacts` |
| `tests/test_grid4d.py` | the suite: knowledge-only scratch Epic, valid tree green, seeded violations with locations, grammar derivation, duplicates, pattern order, placeholders, links fold, the init skeleton |

## Structure

| Section | Required |
|---------|:--------:|
| Overview | ✅ |
| Rules | ✅ |
| Template | ✅ |
| Structure | ✅ |
| Example | ✅ |
| Related | optional |

## Example

The ahabase Epic's own tree is the canonical run: `ahabase validate` holds on it - [AHABASE](AHABASE) registers itself with `StoryPrefix: AHA-`, [AHA-0030](AHA-0030) is a story set named by the derived grammar, and the suite's scratch fixture proves the knowledge-only split (no `CodeArtifacts` anywhere, `validate` green).

## Related

- [ontology-grid4d-blueprint](ontology-grid4d-blueprint) - the concept this implements
- [implementation-ahabase-release-containment-blueprint](implementation-ahabase-release-containment-blueprint) - the gate whose one named allowance ships the templates
