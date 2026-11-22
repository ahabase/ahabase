# The README name-unreserved note is stale for TestPyPI after the dry-run upload

> README.md says "The `ahabase` name is not reserved on either index yet" - written before the dry run, true at upload time, stale now: TestPyPI serves ahabase 0.0.1 while production PyPI still answers 404.

**Status:** open
**Priority:** low (docs; the sentence ships in the sdist already on TestPyPI, where it was true at upload time)

## Problem

Measured 2026-11-20 (AHA-0029 review, seat c020eeb4, journal seq 5907,
non-blocking, F4): the R3 note landed before the R4 upload, when neither
index carried the name. The dry run then uploaded 0.0.1 to TestPyPI
(https://test.pypi.org/project/ahabase/0.0.1/), so "either index" is now
half false: reserved on TestPyPI, still unreserved on production PyPI
(404). The install-line caveat itself stays right - it is trusted only
after the PRODUCTION reservation - but the sentence names both indexes
equally.

## Expected

The note distinguishes the two indexes: the name is reserved on TestPyPI
(the dry-run channel) and not yet on production PyPI; the install line
becomes trusted only when the production reservation happens. Written
so the production publish again changes only what it must (the
reservation sentence), keeping R3's one-line-swap shape.

## Fix

Reword at the next README touch (rides a story; the README ships in the
sdist, so its bytes ride the redaction arm - keep the wording free of
any identifier value). The already-uploaded TestPyPI sdist keeps the
stale sentence - harmless there, it was true at its upload time.

## Related

- [AHA-0029](AHA-0029) - R3 wrote the note, R4's upload made it half stale
- [implementation-ahabase-release-containment-blueprint](implementation-ahabase-release-containment-blueprint) - the release path the note guards
