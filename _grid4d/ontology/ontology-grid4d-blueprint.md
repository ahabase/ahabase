# Grid4d Blueprint

> The knowledge-tree format: what an Epic's `_grid4d/` is - its folders, its self-registering identity, its naming, its document structure and its links - one home per rule.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Knowledge structure → Grid4d
**Placement:** base - layer 1 (the knowledge structure): the format every Epic's tree follows, the umbrella of the layer's named concepts
**State:** implemented in part - the format core validates folders, identity, naming, structure and links (AHA-0030); the layer's named concepts (Epic, Story, Document Pattern and the rest) get their own blueprints with the full row-3 migration

## Overview

**Grid4d** = the format of an Epic's knowledge tree. It is the base the methods build on: a tree that follows it can be validated by software, which is the premise of the whole architecture - what can be validated by software MUST be validated by software. The design principle is the Human's (2026-11-20, AHA-0030): each rule lands simpler than the method copy it precedes - more robustness, more minimalism, less entropy.

## Rules

1. **One home per rule** - Each format rule lives in exactly one place: the naming law in the format core, the structure law in the resolved pattern, the registration in the def file. Reason: the second place a fact lives is entropy to cut (the Human's 2026-11-20 ruling).
2. **The def file is the registration** - An Epic registers itself through `_grid4d/story/<NAME>.md`: `**Type:** Epic` plus its `**StoryPrefix:**` declaration; a subepic with its own `story/` does the same with `**Type:** SubEpic`. No parallel configuration. Reason: identity that registers itself needs no registry beside the tree.
3. **Identity is split from the package** - `**CodeArtifacts:**` is optional; a knowledge-only Epic is a valid Epic. Reason: the format core never needs a code package to validate knowledge.
4. **Naming derives from the tree** - The story grammar derives from the declared prefix, each knowledge folder carries its measured convention, and a name is unique across the Epic's knowledge folders. Reason: a hardcoded prefix literal in a public package is a containment and a self-registration violation.
5. **Unknown means reported** - An unknown or misnamed document is a finding with its location, never silently ignored. Reason: silence is not validity (the method copy's blind spot, closed here).
6. **Structure comes from the resolved pattern** - A document's required sections are the `##` headings of the pattern template resolved for its type; the template is a whole file, first match wins. Reason: markdown has no keys to merge, and one resolution chain keeps the document-type map in one home.
7. **Links resolve in-tree** - Link resolution calls the package's own open-zone link check, one implementation with two entry points. Reason: a second link checker would drift from the first.
8. **Fail-closed, read-only** - A tree the validator cannot interpret is reported with its class, and validation never writes. Reason: a validator that guesses or repairs is a writer wearing a checker's name.
9. **State the coverage** - The skipped zones are stated, not implied: `_archive/` and `_generated/` entirely, `story/history/` structure (naming still checked), rendered links only (fenced blocks and code spans stripped), no name-check for files directly under `_grid4d/`. Reason: stated coverage is measurable; implied coverage over-claims.

## Template

The folder set and its naming conventions (the grammar a tree follows):

| Folder | Convention |
|--------|------------|
| `story/` | the def file `<NAME>.md`, `<NAME>-Priorities.md`, the story set `<PREFIX>-<number>[-tests\|-knowledge-map\|-artifact-map].md`, and `history/` |
| `ontology/` | `ontology-*.md` and the `00-*-ontology-index.md` |
| `implementation/` | `implementation-*.md` |
| `pattern/` | `<scope>-*.md` - the Epic's scope or a subepic's |
| `playbook/` | `*-playbook.md` |
| `issue/`, `idea/`, `metric/` | lowercase kebab names |
| `_archive/`, `_generated/` | skipped by validation |
| `subepic/<name>/` | the same folders at the subepic's level |

The def file (the registration itself):

```markdown
# <NAME>

> One-line purpose.

**Type:** Epic
**StoryPrefix:** <PREFIX>-
**CodeArtifacts:** <package directory, optional>

## Overview

What this Epic is.

## Related

- [related-doc](related-doc)
```

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

The ahabase Epic's own tree is the canonical example - it follows the format and the format core holds on it (`ahabase validate` exits 0): [AHABASE](AHABASE) registers itself, [AHA-0030](AHA-0030) is a story set named by the grammar.

## Related

- [implementation-grid4d-format-core-blueprint](implementation-grid4d-format-core-blueprint) - the code that validates the format
- [AHA-0030](AHA-0030) - the basics slice that lands the core
