# Open-zone documents link into the closed zone

> The rule "links point inward" holds for what is written by hand; three generators of evolucean still write links from this open Epic into the closed zone, and no check enforces the rule.

**Status:** open
**Priority:** high

## Problem

Ruled by the Human on 2026-10-25 in [AHA-0003](AHA-0003): a document of the open zone links only within its own repository and names no closed-zone document; what it needs is extracted into it. The hand-written links of the current documents were replaced by extracts in that story. Four gaps remain, all in evolucean's repository (the surface rule):

1. **Story header** - creating a story writes a `**Blueprint:**` line linking evolucean's story blueprint into the new story document.
2. **Knowledge map** - the map hook records documents read from evolucean's repository as links with a path prefix ([knowledge-map-links-a-document-of-another-repository](knowledge-map-links-a-document-of-another-repository)).
3. **Projection Related block** - measured 2026-10-30 (AHA-0015): the `issues` page the generator writes for this Epic ends with a Related section naming three implementation blueprints of the method's own CLI (`implementation-cli-projections_epic_issues-blueprint`, `implementation-cli-issue_matcher-blueprint`, `implementation-cli-sensors-blueprint`). Listed by file and target in AHA-0015's link check and tied here, the rule's exception path for generated links.
4. **No check** - nothing reports a link of this Epic's `_grid4d` that does not resolve within the repository; the story tests check that links exist, not where they lead. Since AHA-0015 the generated pages are checked per story (R3 of that story); the hand-written documents remain unchecked between stories.

## Expected

- For an Epic whose registry entry marks it as infrastructure or open, both generators write no link into another repository: the story header names its blueprint in plain words (or a blueprint of the open Epic once it has its own), the knowledge map lists a document of another repository as plain text or leaves it out.
- A check run with the containment check on every commit of an open Epic reports each added link that does not resolve within the repository; released stories are not scanned (history stays as it is).

## Fix

In evolucean's repository - with the containment and story-guard work of roadmap step 6. Until then, the generated lines stay as written (never edited by hand) and the check is a story test of each story of this Epic.

## Related

- [AHABASE](AHABASE) - rule Links point inward
- [knowledge-map-links-a-document-of-another-repository](knowledge-map-links-a-document-of-another-repository) - the map half
- [AHA-0003](AHA-0003) - where it was ruled
