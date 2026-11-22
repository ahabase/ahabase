# issue: the package version is 0.0.1 in every release

**Status:** open
**Type:** consistency, diagnosability
**First seen:** 2026-11-09, architecture review of the package at v0.0028.0.0000.00
**Serves:** every row of [AHABASE-Priorities](AHABASE-Priorities): a method consumes each graduation by pinning a release tag

## Problem

`src/ahabase/__init__.py` holds `__version__ = "0.0.1"`, and `pyproject.toml` reads the version from it (`[tool.hatch.version] path`). The releases v0.0017.0.0000.00 to v0.0028.0.0000.00 all install as `ahabase 0.0.1`. `ahabase --version`, `ahabase doctor` and the installed distribution's metadata report the same number for every release.

A consumer that pins a tag cannot see which release it has installed except through the installer's VCS record (`direct_url.json`, `requested_revision`). Observed 2026-11-09: a consumer's tree pinned a newer release than its environment held, its commands failed on a missing module, and the version shown was the same in both.

## Why it matters

The priorities graduate eight capabilities, each consumed back by pinning a release. Each graduation changes the pin, so drift between the pin and the installed package will be frequent. With one version for all releases, the drift is invisible to `doctor`. The Vision's `pip install ahabase` also needs a real version: PyPI does not accept the same version twice.

## Candidate fixes

[idea-version-from-the-release-tag](idea-version-from-the-release-tag).
