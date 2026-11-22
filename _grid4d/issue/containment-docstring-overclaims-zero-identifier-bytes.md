# The containment docstring overclaims zero identifier bytes

> `artifact_containment.py`'s module docstring says "over the whole wheel and the whole sdist, zero member bytes carry a corporate identifier" - stronger than the bytes support: the composed pattern fragments DO ship in the module, each one concatenation away from readable.

**Status:** open
**Priority:** low (wording; no behavior defect)

## Problem

Measured 2026-11-20 (AHA-0029 review checkpoint 2, seat d2014bf4, journal
seq 5901, non-blocking): the F1 fix composes the pattern vocabulary at
runtime (``"kamen" + "skl"``, ``r"github\.tim" + "br" + r"\.ai"``) so no
tree byte carries a FULL identifier - true, and the artifact-level test
asserts exactly that. But the docstring's closing claim, "zero member
bytes carry a corporate identifier", reads as "no fragment ships", which
is false: every fragment ships, and any reader of the published module
can reassemble each identifier with one concatenation. The composition
removes the literal, not the identifier - the honest limit already
stated for the tombstone digest in the blueprint's Known limits ("the
tombstone digest is not secrecy") belongs to the composed vocabulary
too.

## Expected

The docstring's redaction sentence claims what the bytes support: no
member carries a corporate identifier as a contiguous byte sequence
(the artifact-level test's exact assertion), and the composed fragments
do ship in this module - reassembly is possible for a reader, the scan
guards the artifact against the assembled form, and the pattern table
is readable to a maintainer. Same honest-limit wording in the blueprint
wherever the zero-claim appears.

## Fix

Reword the docstring sentence (`src/ahabase/artifact_containment.py`,
the "zero member bytes" clause) at the next story touching the module;
the blueprint already carries the tombstone-not-secrecy limit, so fold
the same clause for the composed vocabulary there. No behavior change;
no test change (the test asserts the literal, not the docstring).

## Related

- [AHA-0029](AHA-0029) - where the composed vocabulary landed and the note was raised
- [implementation-ahabase-release-containment-blueprint](implementation-ahabase-release-containment-blueprint) - the authority doc for the arm's claims
