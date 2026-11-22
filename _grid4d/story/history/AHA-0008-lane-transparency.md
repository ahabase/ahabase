# AHA-0008 lane: transparency architecture - the lineage check and the generated projections

> The special-role lane: design the ontology-to-code lineage check and the generated projections for ahabase, measured against how evolucean does it today, with prototypes measured on clones.

**Seat:** e962e97f (Z.AI, glm-5.3), routed by the home coordinator (home-3333), claim home-3343
**Trees read:** ahabase @ d4436a799b14f9379f73b7307e2dd2bd09a4bf00 (branch head as named in work-1236; detached clone, clean before and after) · evolucean CLI @ e35a8970 (the home main tree) · the evolucean foundation roadmap @ df08cd4b (git object read)
**Date read:** 2026-10-26, 06:50Z-07:40Z. Prototypes and their outputs: `/tmp/aha0008-proto/` (ephemeral; read-only over the clones, no instance writes).

## Read (measured)

### How evolucean does it today

READ: the projection framework is already mostly Epic-agnostic. A registry registers projections and reads what a scope DECLARES from its `<scope>-projections-pattern.md`; projection output names carry an `EPIC` placeholder the framework substitutes per scope - the file-writing substitution sits in the projection base and its fragment renderers (re-attributed per the primary verdict; the declared-pages query substitutes the placeholder only to assemble its set of known page names - it writes no files). Mermaid is already the rendering tool (the fishbone family). `knowledge-usage sync` generates for every Epic discovered in the workspace, ahabase included.

READ: the lineage model joins only declared fields: an implementation blueprint's `**Implements:**`/`**Concepts:**` links to concepts; its `**Code:**` module list (bare module names only); the 1:1 naming rule `implementation-cli-<module>-blueprint`; and a module docstring `Implements:` back-link. Gaps: concept without root anchor, concept without implementation, implementation without code, scope implementation without concept. The lineage fishbone page only places this on a page.

READ, the five Epic-specific blockers, each verified in the method's code (locations delivered chat-side to the method's owners, not printed here - the surface rule):

1. **CodeArtifacts gate** - the registry configuration reads `**CodeArtifacts:**` from the identity and the capability projections walk only declared packages. AHABASE.md has no such line (measured: grep over the identity returns nothing), so the capability/orphans/gradients/artifacts family skips ahabase.
2. **Orphans scan naming** - the orphans scan globs `implementation-cli-*-blueprint.md` and `-tests.md`, evolucean's `implementation/cli/` layout; ahabase's implementation folder is flat `implementation-ahabase-*`.
3. **Lineage scope and source** - the lineage fishbone declares SubEpic scope only (no Epic-scope variant exists) and reads the evolucean CLI's own source tree as its code side; the output-discovery path is hard-coded the same way.
4. **Hard-coded CLI paths in projections** - the string `knowledge-usage-cli` appears in the projection modules on 27 non-comment lines. Occurrence rule (printed with the number, per the primary verdict): 29 candidate lines, 2 of them inside trailing comments; 15 modules carry a non-comment occurrence (12 epic-scope + 3 namespace-scope), 17 counting comment-only ones (14+3). The path-BUILDING form `epic.path / "knowledge-usage-cli" / ...` or a CLI-root derivation sits in 7 modules: 5 carry the string in code under the rule above (the direct path builds), and 2 derive the CLI root in code while their string occurrence sits in a trailing comment the rule excludes - so the 7 does not re-derive from the 15 alone. (Corrected from the first delivery's 18 files / 8 builders; one member of that list was only a generated-page header.)
5. **Fixed output name** - the concept fishbone writes a fixed `EVOLUCEAN-Concept-Fishbone.md` output name literally instead of using the `EPIC` placeholder the framework provides.

READ, a sixth finding not in the brief: the `Code:` join cannot name a nested module. Module matching is bare names only, so an entry naming a nested path resolves to the bare name, which is absent from the flat module map; nested modules join only through the docstring back-link or the 1:1 rule. Measured on evolucean's own ontology-quality blueprint (`**Code:**` line names both a top-level and a nested module; the top-level one joins, the nested one does not).

READ: Prototype A - evolucean's actual lineage computation, run on the ahabase clone with three wirings of its code-side source. With today's wiring (the CLI's own source): 16 concepts, 14 with implementation, 19 implementation rows, **rows with code = 0** - the one `**Code:**` declaration ahabase has is silently erased by the source hard-code. With the source pointed at the ahabase package root (`src/ahabase`): the same computation yields **6 rows with code** (safe-value, reference, store, manifest, shadow-run, rotation -> ahabase-safe -> `safe`, `cli_safe`), gaps exactly: boundary and trust-zone without implementation; architecture, safe-integration and safe-threat-model without code. The computation is format-generic; the WIRING is Epic-specific.

READ: Prototype B - the base-side transparency core, measured on the clone (`/tmp/aha0008-proto/protoB_core.py`, ~120 lines, stdlib only):
- **Concept map**: parses the index Vocabulary facets (16 concepts, 2 facets) and every blueprint's machine-regular Relations bullets; renders a mermaid `flowchart LR` with facets as subgraphs and **33 typed edges** across 27 relation labels; writes it into the index copy behind `<!-- ontology-map:begin/end -->` markers; **idempotent** - regenerating over its own output produces a byte-identical file (measured).
- **Lineage at Epic scope**: the same declared joins with the Epic's own index as the anchor level; 19 rows; gaps exactly as above.
- **Reverse check**: all 5 modules (`__init__`, `cli`, `cli_safe`, `plugins`, `safe`) lack a docstring `Implements:` back-link.

READ, the ahabase tree itself: all 4 implementation blueprints carry `**Implements:**` (architecture: door, registry, plugin, health-check; safe: 6 concepts; safe-integration: 5; safe-threat-model: 4); only the safe blueprint carries `**Code:**` (as `src/ahabase/safe.py, src/ahabase/cli_safe.py` - path form; the join convention wants bare modules relative to the package root); no `**CodeArtifacts:**`; no `<scope>-projections-pattern.md`.

## Inferred

INFERRED: the boundary and trust-zone concepts are without implementation because their guard work (containment, zone checks) is planned in roadmap steps 6 and 10, not yet written - the index's State column supports this but no blueprint names them.

INFERRED: safe-integration and safe-threat-model are document blueprints by intent (how the safe is used with git; the threat catalogue); their "without code" gap is a classification gap, not a missing implementation - but today's lineage vocabulary has no way to say "document by design", so they render as absences.

## The design (decision)

**Build the transparency core in the ahabase package now; change evolucean only as far as needed to stop its pages lying about ahabase; the full generalization rides roadmap step 9.** Reasons, each resting on a measurement or a ruled constraint:

1. **Base-and-method criterion** (AHABASE.md Rules; the ontology's boundary criterion): a lineage check and generated projections are "structure that software can verify" - base territory by the ruled definition. Keeping them only in the evolucean CLI inverts the direction the architecture blueprint fixes.
2. **One place per capability** (AHABASE.md Rules): the capability ends in the package. Generalizing evolucean's copy first means editing the same code twice (once to generalize in the method, once to move it at step 9) and basing the base's transparency on a method plugin's release cycle.
3. **The computation is already generic; the wiring is not** (Prototype A): what must be written anew is small - the measured core is ~120 lines of stdlib parsing plus mermaid rendering; the joins already exist and work on ahabase the moment the inputs are wired.
4. **Strangler fig** (the architecture blueprint's own pattern): the new grows beside the old; evolucean's sync keeps working for evolucean; nothing switches off.

**Order:**

1. **ahabase declarations first (no generator change, unlocks today's evolucean sync in part):**
   - `**CodeArtifacts:** src/ahabase` in AHABASE.md (blocker 1 is a declaration gap on ahabase's side, not a code gap on evolucean's);
   - `**Code:**` for the architecture blueprint in bare-module form (`cli.py, plugins.py, __init__.py`);
   - a document-blueprint convention so doc-only blueprints stop rendering as absences - proposed: `**Code:** none (document blueprint)`; the lineage reports them as a class of their own. Decision for the synthesis;
   - module docstring `Implements:` back-links in all 5 modules;
   - a `ahabase-projections-pattern.md` declaring the two pages below (costs nothing today, states intent).
2. **The package core (its own story, small):** `ahabase ontology graph` (the concept map into the index behind the markers, idempotent - Prototype B measured) and the lineage half of `ahabase verify` (the Epic-scope table + gaps + reverse check - Prototype B measured). Hub ego-graphs per concept (my consultation home-3296) are a follow-up, not part of the minimal core: the canonical map already answers "where does X live".
3. **evolucean-side stop-the-lying fixes (its owners' story, not a precondition for 1-2):** the `EPIC` placeholder in the concept fishbone's output file; Epic-scope lineage reading the code side from the Epic's CodeArtifacts instead of the CLI's own source; the orphans glob from the Epic's declared layout; the path-building hard-codes behind one resolution helper. These close blockers 2-5 for every Epic, ahabase included, and shrink to almost nothing at step 9 when the generalized subset moves into the package and evolucean imports it (the architecture blueprint's dual-reading expand phase).

## What ahabase must add (the full list)

Headers and declarations only - no new code beyond the generator story: the CodeArtifacts line; the architecture `Code:` line; the document-blueprint marker convention (decision); 5 docstring back-links; the projections-pattern declaration; the marker block in the index lands generated, never hand-written (the same rule as the knowledge map).

## Findings that belong to evolucean's owners

Routed per R_docs through the team, not written into the open zone from here: blockers 2-5 above (orphans naming, lineage scope/src, the counted hard-coded-path population, the fixed output name) and the sixth finding (the nested-module `Code:` join). This lane names no closed-module locations: the file-and-line detail - corrected per the primary verdict (the blocker-4 count with its occurrence rule, the seven path-builders with the header occurrence reclassified, the substitution sites re-attributed) - is delivered chat-side to the method's owners with this revision round, for filing as their issues.

## Open decisions for the synthesis

1. The document-blueprint `Code:` convention (proposed above).
2. The order confirmation: declarations now, package core next, evolucean fixes parallel-not-blocking.
3. Hub ego-graphs: defer (recommended) or fold into the core story.

## Notes

- The lane's claim rows: claim home-3343; this file pushed by the seat itself per work-1236 (one commit, this file only).
- The concept-map marker block is appended after `## Related` in the prototype because no markers exist yet; the design places `## Ontology map` before `## Related` when the generator lands.
- Revision 2 (2026-10-26, after the primary verdict at 32bafd0): the closed-name cut landed - this document keeps the surface only (what is wrong, not where in the closed code). The verdict's three findings are fixed where they live now: the blocker-4 count (15/17 files with the occurrence rule, 27 non-comment lines, 7 path-builders) is corrected above; the header-only occurrence and the substitution re-attribution are corrected in the chat-side delivery to the method's owners.
- Revision 3 (2026-10-26, after the second check on 6361c5f): two wording fixes, both re-measured here. The 7-builders clause now states its own derivation (5 in-code under the rule + 2 comment-only derivations, so the 7 does not re-derive from the 15 alone), and the declared-pages sentence no longer denies the placeholder substitution - that query substitutes to assemble its known page names; it writes no files.
