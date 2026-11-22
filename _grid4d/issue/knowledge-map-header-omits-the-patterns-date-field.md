# Knowledge-map header omits the pattern's Date field

> `ensure_km_structure` writes the knowledge-map header with only `**Story:**`, while the live pattern requires `**Date:**` - every map the logger mints fails its own pattern validation on the next read.

**Status:** open
**Priority:** low

## Problem

Measured 2026-10-30 (AHA-0015, at the story's finish): the PostToolUse hook's pattern validation blocks every read of a story knowledge-map with `Missing required field: Date`. The logger's creation path writes the header without the line (`km_structure.py:187` renders `> **Story:** [{story}]({story})` and nothing else), while the pattern template carries `**Date:** {date}` (`evolucean/_grid4d/pattern/evolucean-knowledge-map.md:6`, added with the km git-reconcile of EVOLUCEAN-0488) and the validator derives required fields from the template (`pattern_inference.py:119-121` searches the document for `**{field}:**`). Not specific to this story: the archived `AHA-0012-knowledge-map.md` in the main tree raises the same error on read.

## Expected

The creation path writes every field the live pattern requires (the `Date` line with the mint date), so a freshly logged map passes its own read-gate; maps minted before the fix pass too once their header carries the line.

## Fix

In evolucean's repository (`km_structure.ensure_km_structure`). Until then this Epic's maps get the `**Date:**` line added by hand at the story's finish (AHA-0015's map) - the hook's own printed remedy, touching only the header, never the auto-logged Consumed section.

## Related

- [AHA-0015](AHA-0015) - where it was measured
- [declarations-check-skips-unmapped-trees](declarations-check-skips-unmapped-trees) - another logger/validator pair that drifted apart
