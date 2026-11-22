# ahabase Safe on Windows Blueprint

> One safe codebase on macOS and Windows: an established lock library, a platform dispatch with one home per difference, and CI lanes that prove both variants on every story.

**Implements:** [ontology-portability-blueprint](ontology-portability-blueprint) - the portable delta of [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) and [implementation-ahabase-safe-integration-blueprint](implementation-ahabase-safe-integration-blueprint)
**Story:** [AHA-0014](AHA-0014)
**Code:** _win, _posix

## Overview

ahabase is built for macOS and Windows immediately (Human direction, 2026-10-30: the colleagues run both, the owner tests on both), so the safe - the first code capability - is one codebase on both from its first year, not a later port. The module carried five POSIX bindings (the `fcntl` import at module top, the `flock` manifest lock, `GIT_ASKPASS="true"` naming a Unix executable, `os.access(..., X_OK)` exec detection, and `0o600` as the permissions story); this blueprint is the delta that removed them and the shape that keeps them removed ([ontology-portability-blueprint](ontology-portability-blueprint), the concept this implements).

## Rules

1. **An established library before a hand-rolled wheel** - the manifest lock goes through `filelock` (POSIX `flock`, Windows `msvcrt` behind one API); the platform reach of locking is a solved problem, and solving it again is the wheel this Epic does not reinvent.
2. **Platform dispatch chosen once, at import** - `safe.py` imports `_win` on `win32` and `_posix` elsewhere; platform specifics live in exactly one sibling per platform, and no `if platform.system()` is scattered through the module. `safe.py` imports on every OS (no platform-only import at module top).
3. **The lock's contract is unchanged by the port** - exclusive, released on process death, one writer at a time, on `<manifest>.lock`; the concurrent-writers test that proved the contract on POSIX runs unchanged on every lane. On POSIX the lock file is created `0o600` (owner-only from its first byte); on Windows owner-only rests on the user profile directory's ACLs, which the manifest and its lock file inherit - there is no mode bit to honor on NTFS.
4. **Exec detection is the OS's answer, through the stdlib** - `shutil.which` resolves executables the way its OS does (`X_OK` on POSIX, `PATHEXT` suffixes on Windows) at every check site (`bind`, `run`, `doctor`); no rule of ours per platform, no `os.access` that lies on Windows.
5. **Not-bindable matching strips the OS's exec suffix** - the arm's `exec_base_name` (PATHEXT suffix stripped on Windows, unchanged on POSIX) feeds the name matching, so `python.exe`, `cmd.exe`, `powershell.exe` and `.bat`/`.cmd` relays under a listed name hit the same refusal with the same message shape; `cmd` is in the set.
6. **Prompts disabled without a Unix-only name** - the quiet environment's askpass no-op comes from the arm (`true` on POSIX, `rundll32` on Windows); git's terminal prompt is off and GCM is non-interactive and GUI-off everywhere.
7. **CI proves both variants on every story** - the matrix (macOS, Windows, Ubuntu) runs the suite on every push; fixtures that need an OS-side script ship both variants (`.sh` and `.bat`, the maker takes the pair); tests that state one OS's fact (mode `0o600`) skip on the other lane with the reason named; what the lane itself decides (symlinks) is marked by the lane's measured capability, not skipped wholesale.
8. **Text I/O names UTF-8** - the locale codec differs per OS (cp1252 on a Western Windows, where the documents' `→` cannot encode); every read and write of documents, manifests and generated maps passes `encoding="utf-8"` - the first Windows lane run measured the crash this prevents (28 `UnicodeEncodeError` in the transparency suite), and a bare `read_text` on cp1252 mangles the same arrows before the map check sees them.

## Structure

`src/ahabase/_posix.py` - the POSIX arm: `lock(path)` (pre-creates the lock file `0o600`, then `filelock`), `exec_base_name` (the name as-is), `ASKPASS_NOOP` (`true`). `src/ahabase/_win.py` - the Windows arm: `lock(path)` (`filelock`, owner-only by the inherited profile ACLs), `exec_base_name` (the PATHEXT suffix stripped), `ASKPASS_NOOP` (`rundll32`). `src/ahabase/safe.py` - the import-time choice, `_locked`, the `shutil.which` check sites and `not_bindable_reason`. `.github/workflows/tests.yml` - the three-lane matrix. `tests/` - the pair-shipping fixture makers (`_consumer`, `_exe`), the lane-conditional statements.

## Known limits

- **Real Windows verification is the owner's step** - CI's `windows-latest` lane proves the suite on a clean runner; a `doctor` + `safe` round trip on the owner's Windows machine (as the target registration was for AHA-0012/0013) is the Human's post-merge step.
- **`rundll32` as the askpass no-op** - the established Windows trick (exits immediately without arguments); if a hardened image ever removes it, the arm is the one place to change.

## Template

```python
# safe.py - the dispatch is one import-time choice, not a scattered check
if sys.platform == "win32":
    from . import _win as _platform
else:
    from . import _posix as _platform

# every platform difference lives in the arm, as a member both arms expose
with _platform.lock(path):
    ...  # the read-modify-write, on any OS
```

## Example

```
$ python -c "import ahabase.safe"          # on Windows: ImportError before AHA-0014, imports after
$ python -c "from ahabase import _posix, _win; print(_posix.lock, _win.lock)"
<function lock ...> <function lock ...>    # both arms exist on every OS; only the choice differs
```

## Related

- [ontology-portability-blueprint](ontology-portability-blueprint) - the concept these rules implement
- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - the capability this delta makes portable (rules 2, 4-7)
- [implementation-ahabase-safe-integration-blueprint](implementation-ahabase-safe-integration-blueprint) - git/gh glue whose quiet environment became portable
- [AHA-0014](AHA-0014) - the story
