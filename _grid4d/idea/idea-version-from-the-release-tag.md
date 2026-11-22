# idea: the package version comes from the release tag

**Status:** deferred to the preparation of the first PyPI release (2026-11-09: no priority row needs it now; the drift it would show is prevented on the consumer side, by a drift check in the method's update)
**Origin:** architecture review of the package, 2026-11-09 (robustness, maintainability, consistency, minimalism), weighed against [AHABASE](AHABASE) and [AHABASE-Priorities](AHABASE-Priorities)
**Addresses:** [issue-package-version-never-changes](issue-package-version-never-changes)
**Serves:** every row of [AHABASE-Priorities](AHABASE-Priorities), and the first PyPI release

Derive the version from git instead of a literal:

- **Build side:** `hatch-vcs` (the hatchling plugin over `setuptools-scm`): `[tool.hatch.version] source = "vcs"` and a tag pattern that maps `v0.0028.0.0000.00` to a PEP 440 version (for example `0.28.0`, or `0.0028.0.0000.0` if the five segments must stay). Builds between tags get a `.devN+g<sha>` suffix automatically.
- **Runtime side:** `__version__ = importlib.metadata.version("ahabase")`, so `--version` and `doctor` show what is installed.
- **Doctor:** print the version beside the install source (the VCS commit for a git install), so pin drift is one command away.

Risks measured or known before choosing it: CI checkouts are shallow and carry no tags by default (`actions/checkout` needs `fetch-depth: 0`), a build outside git (an sdist) needs `fallback_version`, and the tag `v0.0028.0.0000.00` normalizes to `0.28.0.0.0` under PEP 440 (checked with `packaging`). The alternative without a build plugin is a release step that writes the version into `__init__.py` before tagging; to be weighed then.

Why this form: it is the established tool for the hatchling build the package already uses; no release step has to remember to edit a file. To decide: the mapping of the five-segment tag to PEP 440 (PyPI needs it before the first release).

## Related

- [idea-ahabase-foundation-roadmap](idea-ahabase-foundation-roadmap) - release mechanics (Trusted Publishing, TestPyPI)
