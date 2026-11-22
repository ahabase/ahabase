# issue: the identity describes doors and a plugin model that are not in use

**Status:** open
**Type:** consistency between the Epic identity and the code
**First seen:** 2026-11-09, architecture review of the package at v0.0028.0.0000.00
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) rows 3 and 5 to 8 (each graduation must know how it is consumed)

## Problem

The [AHABASE](AHABASE) Overview describes:

- the doors "the `ahabase` CLI, the MCP server (`ahabase serve`) and the Claude Code plugin" and the services "`doctor`, `init`, `verify`";
- evolucean as "a closed, optional plugin that ... registers its commands and MCP tools through Python entry points".

At v0.0028.0.0000.00 the CLI has `doctor`, `llm`, `ontology`, `safe`, `verify`. There is no `serve`, no `init`, no MCP server and no Claude Code plugin. No distribution registers the `ahabase.plugins` entry point group; the registry (`plugins.py`) loads nothing. The method consumes the package the other way: it imports `ahabase` as a library and pins a release tag, through declared seams; the 2026-11-08 Direct use ruling adds that a graduated capability is also called from the ahabase door itself.

The roadmap ([idea-ahabase-foundation-roadmap](idea-ahabase-foundation-roadmap), step 10) places the MCP server, the Claude Code plugin and the method registered as a plugin after the format graduates, so the Overview mixes today's state with that plan.

## Why it matters

Rows 5 to 8 move large layers (collaboration, decision, projection, story). Each graduation must know whether the method consumes it as a library through a seam, or extends it as a plugin through the registry. Two models described as one lets each graduation choose its own.

## Candidate fixes

[idea-integration-model-decision](idea-integration-model-decision).
