# issue: one module carries every concern of the safe

**Status:** open
**Type:** maintainability
**First seen:** 2026-11-09, architecture review of the package at v0.0028.0.0000.00
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) row 1 (evolucean consumes the ahabase safe)

## Problem

`safe.py` is 1,128 lines: the stores (memory, environment, keyring), the manifest (load, lock, atomic save), the binding of consumers, three target kinds (git credential, gh login, gh login per account), refresh and rotation, the consumer check, the git credential helper protocol and health. `cli_safe.py` adds 620 lines. Together they are a third of the package.

## Why it matters

Row 1 finishes when every secret read and write of the method goes through the safe's targets. Each new consumer is likely to add a target kind or a store; in one module each addition widens the review surface of the code the Epic ranks first ("Safe first").

## Candidate fixes

[idea-split-the-safe-module](idea-split-the-safe-module).
