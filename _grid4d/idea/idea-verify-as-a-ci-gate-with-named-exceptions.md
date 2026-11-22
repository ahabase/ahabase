# idea: `ahabase verify` as a CI gate

**Status:** open
**Origin:** architecture review of the package, 2026-11-09 (robustness, maintainability, consistency, minimalism), weighed against [AHABASE](AHABASE) and [AHABASE-Priorities](AHABASE-Priorities)
**Addresses:** [issue-verify-red-on-main-and-not-in-ci](issue-verify-red-on-main-and-not-in-ci)
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) row 4, and the open-zone check of every graduation

One step: `ahabase verify` after `pytest` in the CI workflow, on the fresh checkout, which sees only what git holds (the gitignored `_generated/` pages never reach it). Proved once by a branch with a broken link that turns the run red.

It is too small for a story of its own: it rides with the next story that changes code in this repository. The one real failure found by the review (the relative story link in `verify-write-rules-enforces-an-undeclared-rule.md`) was fixed directly as a free record on 2026-11-09, so `verify` on a fresh clone is green and the gate starts green.

Considered and dropped (minimalism): skipping `_generated/` inside `verify` so a synced working tree gives the CI's answer. It only removes local noise, not a gap of the gate.

Why this form: it reuses the existing check and the existing CI; nothing new is built. Rejected: running `verify` only in the method's story completion, because the open package must be checkable without the method.

## Related

- [issue-windows-ci-red-on-main-unseen](issue-windows-ci-red-on-main-unseen) - the same "red and unread" pattern
- [open-zone-documents-link-into-the-closed-zone](open-zone-documents-link-into-the-closed-zone) - the generated-link exception
