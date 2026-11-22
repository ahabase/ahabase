# issue: the atomic file write is implemented more than once

**Status:** open
**Type:** minimalism (One place per capability, applied to primitives)
**First seen:** 2026-11-09, architecture review of the package at v0.0028.0.0000.00
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) row 3 (grid4d infrastructure)

## Problem

Two functions in the package write a file atomically (temporary file in the same directory, flush, `fsync`, `os.replace`): `Safe._save` in `safe.py` (mode 0600 from the first byte, refuses an unignored git tree) and `_atomic_write` in `llm/switch.py` (keeps the existing mode). The method holds a third for its own rules files. The lock primitive is shared already (`_platform.lock` over `filelock`); the write is not.

## Why it matters

Each graduation in rows 3 to 8 brings code that writes instance files (state, logs, projections). Without one primitive, each will bring its own variant, with its own choice of mode, fsync and cleanup on failure.

## Candidate fixes

[idea-shared-file-primitives](idea-shared-file-primitives).
