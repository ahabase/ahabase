# AHA-0008 lane: the state of the evolucean root Epic

> What the root of the method Epic carries today - open issues and ideas, its own measures, the plan it holds for ahabase - and what ahabase depends on in it. Written as public: counts and kinds, no closed know-how, no plugged-in Epic content.

**Lane:** evolucean root state (work seat)
**Read:** the evolucean repository, main at df08cd4 (2026-10-24 22:53 local time), and its generated projections of 2026-10-26 07:35; read 2026-10-26 06:50Z
**Story:** [AHA-0008](AHA-0008)

## Read

### Size and activity

637 completed stories (counted over the full commit messages of the method's main - 630 for the Epic and its SubEpics plus 7 for the instance identity; a subject-only count reads 633, the release tags 617, an older projection 467 - the scope of the count decides the number); 14 SubEpics (analysed in their own lane). The method's figures below come from its projections generated on this instance at 2026-10-26 07:35Z; another instance with an older projection reads earlier values. The root's main has not moved since 2026-10-24 22:53 - every story since then was an ahabase story.

### Root issues (the root's `issue/` folder, counted by their Status and Priority lines)

Counting rules, so the table can be reproduced: the first word of a file's `**Status:**` line decides; a status word outside open, resolved and partially (one file says `cosmetic`) is counted as open; files without a Status line are counted under "no status line" - among them two index files, which are not issues. The local review counted strictly and found 207 resolved and 11 without a status line: one file states its resolution only in prose ("Resolved by ...") without a Status line; the table below counts it as resolved. The open count (185) is the same under both rules.

| Status | Priority | Count |
|---|---|---|
| open | none given | 117 |
| open | medium | 42 |
| open | low | 21 |
| open | high | 4 |
| open | critical | 1 |
| resolved | any | 208 |
| partially resolved | any | 7 |
| no status line | - | 10 |

185 open issues; 117 of them (63%) carry no priority. The open critical and high ones: plugged-in Epic content leaving its boundary (critical; parts done), the containment allow list per instance, the bootstrap gaps of the tooling for a non-dbt Epic (raised from ahabase), an LLM proxy's plain-text tool call poisoning a session, SubEpic identities lacking their contribution.

### Root ideas

116 open ideas (the namespace's projection counts 32 of 177 converted across all Epics).

### The method's own measures (its gradients projection, 2026-10-26)

Code traceability 523 of 931 functions; blueprint coverage 91%; test coverage 224 of 369 modules; ontology coverage 30 of 61 (49%); blueprint traceability 197 of 224 (87%); 35 code modules without a blueprint (orphans: missing blueprints); dependency validity 195 link issues; four recurring issues; knowledge usage freshness 1,465 of 4,065.

### The plan it holds for ahabase

The foundation roadmap (an idea document of the root) was last changed 2026-10-24 22:26 - before AHA-0004 to AHA-0007. It does not carry: the ontology as the base and the method extending it, the research decisions, the threat model and the order it set (agent path before the scanner), the hardening, the equal requirement of security and usability. Its step 1b (release code reads the account from the registry) and step 6 (the tooling's bootstrap gaps) are still open; step 8 is partly done (AHA-0003). The order of the next ahabase stories now lives in the ahabase architecture blueprint.

## What ahabase depends on in the root

1. **The tooling it runs on** - story workflow, knowledge map, containment, projections, sync - is the method's CLI. Its gaps for a non-ahabase-shaped Epic (bootstrap gaps, hard-coded paths in projections, the orphans glob, the lineage fishbone's own source) are the root's to fix until the format moves into the package.
2. **Step 1b and the distribution fixes** - needed before any wide-reach token moves.
3. **The generators' links into the closed zone** (story header, knowledge map) - logged in ahabase, fixed in the root.
4. **The roadmap itself** - its owner is the root's trust layer; it is stale.

## Inferred

- **Two documents state the plan** (the root's roadmap and the ahabase architecture blueprint's order), and only one is current. Under the rule that the open side holds the extract and the closed side refers to it, the ahabase order should be the source and the roadmap should point to it for the package steps, keeping only the instance's secret migration (instance specific) and the method's own steps.
- **The root carries much unprioritized debt** (117 of 185 open issues without a priority). None of it blocks the next ahabase story directly; the tooling gaps above do block transparency for ahabase (generated projections, lineage).
- **The method measures itself well** (traceability, coverage, freshness) - exactly the transparency the Human asks for ahabase; the gap is that these measures do not yet work for any Epic shaped differently from the method's own CLI.

## Related

- [AHA-0008](AHA-0008) - the story
- [AHA-0008-lane-ahabase-state](AHA-0008-lane-ahabase-state) - the other work lane
