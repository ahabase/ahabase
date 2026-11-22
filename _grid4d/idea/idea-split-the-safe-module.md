# idea: split the safe module along its concerns

**Status:** open
**Origin:** architecture review of the package, 2026-11-09 (robustness, maintainability, consistency, minimalism), weighed against [AHABASE](AHABASE) and [AHABASE-Priorities](AHABASE-Priorities)
**Addresses:** [issue-safe-module-carries-every-safe-concern](issue-safe-module-carries-every-safe-concern)
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) row 1

Turn `safe.py` into a package with the public names unchanged (`from ahabase.safe import Safe, SafeError, ...` keeps working through `safe/__init__.py`):

| Module | Content |
|--------|---------|
| `safe/stores.py` | `Store`, `MemoryStore`, `EnvStore`, `KeyringStore` |
| `safe/manifest.py` | `Entry`, load and validation, the lock, the atomic save |
| `safe/targets.py` | `TargetKind`, the git credential and gh login targets, `gh_config_dir`, rotation |
| `safe/consumers.py` | binding, `check_consumer`, the child environment, the not-bindable rules |
| `safe/__init__.py` | `Safe` (the façade) and the re-exports |

A pure move with no behaviour change: the existing 414 tests are the red control (they must pass unchanged), plus an import test of every public name. Do it before the next target kind arrives, so that change lands in one small module.
