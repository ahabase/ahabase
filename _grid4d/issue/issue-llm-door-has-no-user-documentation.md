# issue: the llm door has no user documentation

**Status:** open
**Type:** documentation gap
**First seen:** 2026-11-09, architecture review of the package at v0.0028.0.0000.00
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) row 2 (llm), and the Vision (`pip install ahabase` gives a working tool at step 0)

## Problem

`docs/` holds `safe.md` only, and the README describes the safe. The `ahabase llm` door (path list, discovery, verify, switch, `session-launch`) and the variants file it reads are described only in the implementation blueprint ([implementation-ahabase-llm-blueprint](implementation-ahabase-llm-blueprint)), which is written for developers of the package.

## Why it matters

A user who installs the package finds the second capability through `--help` only, and nothing tells them how to write a variants file, which auth forms are accepted (`safe://`, `env:`, a key helper) or why a literal credential is refused.

## Candidate fixes

A `docs/llm.md` in the form of `docs/safe.md`: the variants file with one example per auth form, the commands, the refusals and their remedies; the README names both capabilities.
