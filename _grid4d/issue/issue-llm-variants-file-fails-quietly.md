# issue: a malformed variants file reads as "no paths"

**Status:** open
**Type:** robustness, inconsistent failure policy
**First seen:** 2026-11-09, architecture review of the package at v0.0028.0.0000.00
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) row 2 (llm)

## Problem

`ahabase.llm.paths.load_variants` returns an empty dict when the variants file is missing **or unreadable**: `except (OSError, yaml.YAMLError): return {}`. A YAML syntax error or a file the user cannot read therefore looks exactly like an instance with no variants. Since the provider ladder became instance data (the method no longer carries built-in paths), that file is the whole ladder: a typo silently removes every instance path, and the user sees the native routes only, with no message.

The safe, in the same package, fails closed and names the cause (a malformed manifest entry raises `SafeError` with the entry name).

## Why it matters

The two halves of the package follow two failure policies. The llm door is the next capability the priorities finish, and the instance file is now its only source of paths.

## Candidate fixes

[idea-llm-graduation-hardening](idea-llm-graduation-hardening), point 1.
