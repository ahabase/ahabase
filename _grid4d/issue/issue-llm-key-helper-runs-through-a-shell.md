# issue: a path's key helper runs through the shell

**Status:** open
**Type:** robustness, portability (Both OS variants)
**First seen:** 2026-11-09, architecture review of the package at v0.0028.0.0000.00
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) rows 1 (safe) and 2 (llm)

## Problem

`ahabase.llm.paths.resolve_key` runs a path's `key_helper` with `subprocess.run(helper, shell=True, ...)`. The command string comes from the instance's variants file. The shell differs by platform (`/bin/sh` on macOS and Linux, `cmd.exe` on Windows), so quoting, paths with spaces and the meaning of characters such as `%`, `^` and `&` differ, and a helper written on one OS may not run on the other. A failing helper returns `None` (`OSError` or a timeout), indistinguishable from an empty key.

The rest of the package calls programs with an argument list (`git`, `gh`, `security`).

## Why it matters

The key helper is the place where a credential is obtained. The Epic rules ask for both OS variants in the same story and for safe handling of every credential; a shell-parsed command line is the least portable and least predictable form for it.

## Candidate fixes

[idea-llm-graduation-hardening](idea-llm-graduation-hardening), point 2.
