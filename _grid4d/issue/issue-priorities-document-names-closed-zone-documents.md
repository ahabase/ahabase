# issue: AHABASE-Priorities names documents of the closed zone

**Status:** open
**Type:** rule conflict (Links point inward)
**First seen:** 2026-11-08, review of work stream B against the Epic's Rules

## Problem

The Epic rule "Links point inward" says a document of this open Epic links only to documents of this repository and names no document of the closed zone. `_grid4d/story/AHABASE-Priorities.md` (AHA-0023) names three documents of the closed method as plain text: the concept document of the priorities, the document pattern it instantiates and the idle-session procedure that reads it (in its header and its Related list). The plain-text form avoids a link but not the naming the rule forbids. Older story documents show the same habit, and so does the pairing of two stories: a landing story names its flip story's id and the reverse (the pipeline's practice since the first graduation), so the rule's reading for a story id is open and is the Human's to settle.

## Candidate resolutions

1. Describe the form without naming the closed documents ("the ranked-priorities form the method defines") and keep the pointers on the closed side, which may link here; for the pairing, keep the id of the other story out of the open document and let the closed side record the pair.
2. Rule exception: record in the Rules that plain-text pointers to closed-zone documents are allowed in story documents; change the rule, not the practice. This is the Human's decision.
3. Extract the needed part of the priorities form into an ahabase document (the rule's own remedy: "extracted into its own documents in the extent it needs") when a second method needs the pattern.

## Related

- [AHABASE](AHABASE) - Rules, "Links point inward"
- [AHABASE-Priorities](AHABASE-Priorities) - the document concerned

---
