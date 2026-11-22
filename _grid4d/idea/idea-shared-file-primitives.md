# idea: one module for the file primitives

**Status:** open
**Origin:** architecture review of the package, 2026-11-09 (robustness, maintainability, consistency, minimalism), weighed against [AHABASE](AHABASE) and [AHABASE-Priorities](AHABASE-Priorities)
**Addresses:** [issue-atomic-write-implemented-more-than-once](issue-atomic-write-implemented-more-than-once)
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) row 3, ahead of rows 5 to 8

A small `ahabase.files` (or `ahabase._fs`) with:

- `atomic_write(path, text, *, mode=None, keep_mode=True)`: temporary file in the same directory, flush, `fsync`, `os.replace`, cleanup on any failure; `mode=0o600` creates the file owner-only from the first byte;
- `exclusive(path)`: the existing `_platform.lock` under a public name;
- the git-tree guard of the safe (`inside_git_tree`, `git_tracks_possible`) as an opt-in check (`refuse_in_unignored_tree=True`).

`Safe._save` and `llm.switch._atomic_write` call it; the method's own copy is replaced when its rules writer next changes. Each later graduation uses it instead of bringing its own.

Why now: it is cheapest while there are two callers; after rows 5 to 8 there would be many.
