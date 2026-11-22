# issue: the llm module computes the tool's settings paths at import time, outside the config door

**Status:** open
**Type:** consistency (the config door as the seam), testability
**First seen:** 2026-11-09, architecture review of the package at v0.0028.0.0000.00
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) rows 2 (llm) and 3 (grid4d infrastructure)

## Problem

`ahabase.llm.paths` defines `SETTINGS_PATH = Path.home() / ".claude" / "settings.json"` and `CREDENTIALS_PATH` as module constants, evaluated once at import. Everything else the llm module needs from the instance (the variants file) comes through the config door (`get_workspace_dir()`). The architecture names the config door as the seam every capability stands on.

Consequences: a test or a second host tool must patch module constants; a different home or tool location set after import is not seen; the module hard-wires one host tool's file layout.

## Why it matters

Rows 5 to 8 of the priorities will bring more host-tool integration (collaboration, story). If each capability reads host-tool files through its own constants, the config door stops being the one seam.

## Candidate fixes

[idea-llm-graduation-hardening](idea-llm-graduation-hardening), point 3.
