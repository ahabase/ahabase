# AHA-0008 synthesis: where we stand, whether the plan holds, and what to build first

> The direction holds. The plan needs one home, a smaller next step and an honest size for the format move; transparency can start now, cheaply, in the package - and it should come first, because it makes every later step measurable.

**Lanes synthesized:** [AHA-0008-lane-ahabase-state](AHA-0008-lane-ahabase-state) (work), [AHA-0008-lane-evolucean-root](AHA-0008-lane-evolucean-root) (work), [AHA-0008-lane-evolucean-subepics](AHA-0008-lane-evolucean-subepics) (home, deepseek seat), [AHA-0008-lane-transparency](AHA-0008-lane-transparency) (home, Z.AI seat - special role), [AHA-0008-lane-plan-realism](AHA-0008-lane-plan-realism) (home coordinator)
**Written:** 2026-10-26 by the work seat. **Review:** pending - the home primary seat and the work instance's local reviewer, verdicts recorded in the story notes; the SubEpics lane's figures checked against their source by that lane's seat (all match).
**Story:** [AHA-0008](AHA-0008)

## Where both Epics stand

**ahabase** - young, consistent and well reviewed (seven stories, every one reviewed on both instances; 1,236 lines of code, 98 test cases; an ontology of 16 concepts with their states). The safe is the mature part: implemented, threat-modelled and hardened through four review rounds. The platform beyond the CLI, the knowledge format and the release-gate hygiene (security policy, contribution guide, CI) are not started. Its consistency is checked by people and by per-story test rows, **not yet by software across the Epic**: the work lane counted five lineage gaps by hand (two concepts without an implementation blueprint, three blueprints without a Code line, two modules no Code line names, no test-to-requirement trace beyond the rows, no generated projections), and the transparency lane reproduced them by running a lineage computation on the tree.

**evolucean** - large and active (637 completed stories; 1,242 of its 3,724 commits on its main at the read tip df08cd4 fall within the 14 days before the tip's own committer time, i.e. after 2026-10-10T20:53:07Z - an absolute instant, so the number does not move with the clock the count runs at), and it measures itself well (traceability, coverage, freshness) - exactly the transparency asked for ahabase. Its open work is large and mostly unordered: 185 open root issues, 63% without a priority; 171 open items in the SubEpics, **none** with a priority (the field is not in use there), 72% of them in collaboration. The SubEpic folders are quiet since a cross-cutting sweep on 2026-10-23; every SubEpic story is completed. The SubEpics' own open work is largely about lineage and projections - the method struggles with the same mechanisms ahabase needs.

**The team** - the home instance's checked-out copy of the method's repository is behind its main - by date, two days (its head is of 2026-10-23, main of 2026-10-24, root lane and plan-realism lane); by count, 57 commits (SubEpics lane) - an ancestor of main, so nothing diverged; it has no clone of the ahabase repository, no registry entry for it and no secret inventory yet. Wide review works: every lane delivered within its window, two of them with measured prototypes.

## Is the plan realistic

**Direction: yes** - every lane agrees: safe first, an open base with a protected method, never back, the agent path before the scanner. No lane found a contradiction between the identity, the architecture blueprint and the ontology on direction.

**But five things must change for the plan to hold:**

1. **One plan, in this repository.** The plan lives in two documents that disagree - the method's roadmap (stale since before the ontology story) and this Epic's architecture order. By this Epic's own rule (the extract is the one source of truth, links point inward) the step list belongs here, with each step's state, gate and dependency; the method's roadmap keeps only the instance's secret migration and refers here for the package steps (plan-realism F9; root lane).
2. **The plan waits on the Human, by design.** Nine of the roadmap's fifteen rows carry a Human gate; the calendar of the secret migration is the Human's calendar. Seats stay productive on the ungated rows meanwhile (F1).
3. **The format move (step 9) is weeks, not a story.** The modules that hold the knowledge format and the story workflow, with what they import at module level, are 44 modules and 13,271 lines - ten times the whole base today; counting imports inside functions as well, they reach 363 of the method's 378 modules (plan-realism F3, a static parse; the scope of the count decides the number) - and they are the method's busiest code (about 3.6 commits a day). It needs slices behind characterization tests and a "package first" rule for new work in the moved parts while it runs (F3, F4, F6).
4. **The plugin contract must grow before the move.** Version 1 registers commands and checks; the method also needs hooks, sensors, projection generators and document-pattern resolution - a version 2 designed from that list, with the MCP server on the same extension points (F5).
5. **Two fragile acts need their safeguards written first:** installing the agent guard (a stable installed path, a check at session start, loud failure - an earlier silent-open incident is the reason, F8) and turning the inheritance (it is coupled to the channel the team uses to recover - a second route agreed beforehand, F7).

## Order of the next stories

Proposed; the Human decides:

1. **Transparency, first and small** (this Epic): the declarations (`**CodeArtifacts:**`, the architecture blueprint's Code line, the document-blueprint marker, the modules' `Implements:` back-links, a projections declaration) and the package core - `ahabase ontology graph` (a generated concept map in the index) and the lineage half of `ahabase verify` (the Epic-scope table, gaps, reverse check). Both measured as prototypes on clones: 16 concepts, 33 typed edges, byte-identical on regeneration; 19 lineage rows with exactly the hand-counted gaps. Why first: it is base territory by the ruled criterion, small (about 120 lines in the prototype), needs no Human gate, and makes every later story - the guard included - visible in the lineage.
2. **The agent guard** (this Epic), with F8's safeguards; it needs the Human's consent for the settings change.
3. **Beside them, ungated:** the one-plan document here (decision 2); the method's owners take the transparency lane's evolucean findings and the distribution fixes (release reads the account from the registry; the tooling's bootstrap gaps); the home instance's own preconditions (fetch, a clone of this repository, the registry flag, the containment allow list, its secret inventory) by the home side; the release-gate hygiene (security policy, contribution guide, CI) as small stories.
4. **The secret migration per consumer** on the Human's schedule, starting with the least critical consumer, after the guard.
5. **Plugin contract version 2 and the MCP server.**
6. **The format move in slices** (read/validate/templates first, then the story workflow), with the "package first" rule.
7. **The turn of the inheritance** behind its gate and a second route; then the method as a plugin and the Claude Code plugin.
8. **`safe scan`** after the guard (it can move earlier if the Human wants discovery before the migration).
9. **Trust zones' check, then the public release.**

## Transparency to build first

From the transparency lane (Z.AI, special role), checked against the other lanes:

- **The computation exists; its wiring does not.** The method's lineage model (concept to implementation blueprint to code, gaps as absences and divergences) is format-generic; run on the ahabase tree with the source pointed at the package it gives the right answer, with today's wiring it gives none. The method's projections run for every Epic, but their inputs are wired to the method's own layout.
- **Build the core in the package now; fix the method only as far as its pages mislead about other Epics; generalize fully with the format move.** Reasons: base territory; one place per capability (generalizing in the method first would edit the same code twice); the computation is small to write anew; the strangler fig keeps the method working.
- **What ahabase adds:** declarations only, then one small generator story. The generated map lands behind markers, never hand-written.
- **Not in the minimal core:** per-concept hub diagrams (a follow-up); a test-to-requirement trace (the work lane's fifth gap - a later step of the same lineage).

## Findings for the method's owners

Routed through the team as issues of the method, not written into its zone from here: the orphans scan's fixed layout; lineage only at SubEpic scope and reading the method's own source; the counted hard-coded paths in projections; a fixed output name written into every Epic; a `Code:` join that cannot name a nested module; the artifact map's parallel-window line carrying a foreign story id into other Epics' documents; one SubEpic keeping its stories without an archive; no priorities in the SubEpics' items.

**A finding about this story itself:** the transparency lane and this story's starting-evidence section named the method's modules and line numbers - closed internals in documents written as public, against the surface rule (the plan-realism lane deliberately kept to aggregates); the SubEpics lane as first delivered named the method's documents themselves - the stems of its 171 open items and six of its story ids - against this Epic's rule that the open zone names no closed document. Before completion, that detail moves to the method's side with the issues above, and the documents here keep the surface and the counts (what is wrong and how much, not where in the closed code or which closed document). The starting-evidence section is cut (91b620a); the SubEpics lane's revision 2 (421b462) cut the document stems, and the transparency lane's cut is its seat's next commit - both lanes are cut by their seats, and the story completes only when both cuts are in.

## Decisions for the Human

1. **Order:** transparency (declarations and package core) before the agent guard - recommended - or the guard first.
2. **One plan here:** the step list moves into this Epic (state, gate, dependency per step), the method's roadmap refers to it.
3. **The format move:** in slices with a "package first" rule for new work in the moved parts of the method.
4. **Document blueprints:** blueprints that are documents by design (the threat model, the integration decisions) carry `**Code:** none (document blueprint)`, and the lineage reports them as their own class instead of absences.
5. **The home side:** ask the home Human to bring the home instance up to date (fetch the method's repository, clone this one, the registry flag, the allow list) and to start the home secret inventory.
6. **Priorities in the method:** a triage of the method's unprioritized open work (117 root issues, all 171 SubEpic items), or leave it - the method's own decision.
7. **Release hygiene now:** the security policy, contribution guide and CI as small stories beside the code work.

## Related

- [AHA-0008](AHA-0008) - the story
- [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint) - the order this proposes to replace
