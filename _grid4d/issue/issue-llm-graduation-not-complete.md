# issue: the llm graduation is not complete - the proxy is not in the package, and the method's remaining layer is unmeasured

**Status:** open
**Type:** rule progress (One place per capability)
**First seen:** 2026-11-09, architecture review of the package at v0.0028.0.0000.00
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) row 2 (llm)

## Problem

Row 2's "done looks like" names paths, **proxy** and provider selection in ahabase. The package has `ahabase.llm` (paths, discovery, verify, switch, session) and the `ahabase llm` door. It has no proxy: the local proxy service (start, stop, its service definition) is still the method's.

The method's llm layer still holds about 1,160 lines in the four modules that now delegate to the package (paths, path resolution, path verification, discovery), measured 2026-11-09. Whether this is thin delegation plus method tuning, or logic that the Rule "One place per capability" says must not remain, has not been measured. The flip story's census guard counts call sites, not the size or content of what remains.

## Why it matters

The Rule says no copies. Without a measure, the row cannot be closed with evidence, and the same question returns at every later graduation.

## Candidate fixes

- Measure the remaining method layer per function: delegation, method-specific tuning, or duplicated logic; record the table in the llm subepic.
- Graduate the proxy as the next llm story.
- A graduation check that reports the size of the method's remaining layer beside the call-site census ([idea-graduation-checks-include-every-epic-rule](idea-graduation-checks-include-every-epic-rule) is the place for it).
