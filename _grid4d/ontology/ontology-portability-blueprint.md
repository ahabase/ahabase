# Portability Blueprint

> One codebase on the operating systems its users run - by construction from the first line, never a port after the fact.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Platform → Portability
**Placement:** base - the layering is structure software can verify (a library dependency, one dispatch point, CI lanes)
**State:** implemented (the safe, [AHA-0014](AHA-0014)); every code-impacting story carries it

## Overview

**Portability** = the property that the code runs on the operating systems its users run (macOS and Windows immediately - Human direction, 2026-10-30; Ubuntu in CI) without a per-OS fork of the code. The mistake it exists to prevent was measured in the safe's first year: five POSIX bindings (`fcntl` at module top, the `flock` manifest lock, a Unix-only askpass executable, `X_OK` exec detection, `0o600` as the permissions story) that each passed on the author's OS and broke the module's import or its rules on another. Portability is therefore designed in when a capability is written, not discovered later.

The path is the established one, minimal and proven before us - three layers, used in order:

1. **An established library first** - when the platform reach of a problem is already solved, the library is the mechanism: `filelock` for inter-process locking (flock on POSIX, msvcrt on Windows), `shutil.which` for executable resolution (X_OK on POSIX, PATHEXT on Windows), `keyring` for the OS stores, `pathlib` for paths. Hand-rolling a platform mechanism a library already ships is the wheel this base never reinvents.
2. **A platform dispatch for what genuinely differs** - one sibling module per OS (`_win.py`, `_posix.py`), chosen once at import time; each difference has exactly one home, and the arm that owns it states its OS's meaning (the lock file's `0o600` on POSIX, the user profile directory's ACLs on Windows). No `if platform.system()` scattered through the code.
3. **Own code last** - only behavior that is truly new; where it must state an OS fact, it states it through the arm.

## Attributes

- **OS variants** - macOS and Windows (the users), Ubuntu (the CI lane); a story that changes code ships both variants in the same story
- **Dispatch point** - import time, one choice; the arms expose the same members
- **Statement home** - a per-OS fact lives in the arm that owns it, in code comment and blueprint

## Relations

- **applies_to** → every [Door](ontology-door-blueprint), [Registry](ontology-registry-blueprint), [Plugin](ontology-plugin-blueprint) and [Health Check](ontology-health-check-blueprint) of the base - and every test of it

## Constraints

- **Both variants in the same story** (Human, 2026-10-30) - a code-impacting story easily delivers both OS variants; "we port it later" is the mistake this concept exists to prevent.
- **The rule is measured, not remembered** - the CI matrix (macOS, Windows, Ubuntu) runs the suite on every push; portability without a lane that can turn red is a claim.
- **Library, then dispatch, then own code** - in that order; the dispatch exists only for a difference the library does not already absorb, and own platform code only for behavior no one has solved.
- **Honest per-OS statements** - a fact of one OS (a mode bit) is tested on its lane and skipped with its reason on the other; the other lane's meaning (ACLs) is stated in the arm and the blueprint - never silently.
- **Text is UTF-8, by name** - the OS's default codec differs (cp1252 on Windows); every text read and write names `encoding="utf-8"`, so no document or manifest depends on the locale.

## Example

- the safe's manifest lock: `filelock` (layer 1), the lock file's `0o600` pre-create in `_posix.py` and the ACL statement in `_win.py` (layer 2), the read-modify-write unchanged on every OS (layer 3)

## Related

- [implementation-ahabase-safe-windows-blueprint](implementation-ahabase-safe-windows-blueprint) - this concept implemented in the safe
- [AHABASE.md](AHABASE) - the both-variants rule of the Epic
