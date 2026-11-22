# Wiki Projection Blueprint

> A projection of the Epic's knowledge into a GitHub wiki: the local mirror generated from ``_grid4d/``, published as the repository's wiki under the declared account.

**Ontology:** [00-ahabase-ontology-index](00-ahabase-ontology-index) → Knowledge structure → Wiki Projection
**Placement:** base - generated structure with deterministic checks (page set, navigation bytes, exit codes); what the pages say is each Epic's own knowledge
**State:** implemented - the door lands with AHA-0036 (generate, sync, check, clean, publish, status)

## Overview

**Wiki Projection** = a [Projection](ontology-projection-blueprint) whose target is a git mirror of a GitHub wiki: ``<workspace>/_wikis/<epic>.wiki``. The mirror is generated (``sync`` copies the documents the config maps and purges what it no longer accounts for; ``generate`` renders ``_Sidebar.md`` and ``Home.md`` from the config - the same bytes every time), checked (``check`` finds duplicate page names; ``clean`` dedupes, root copy wins) and published (``publish`` makes the mirror a clone of the repository's wiki remote, commits the delta and pushes under the Epic's declared GitHub account - the same fail-closed identity gate as the release path). The config lives at ``<workspace>/_config/<epic>.wiki.yaml``; absent or empty means the defaults (the standard mirror path, the ``_grid4d/`` source, no mapping) - an unconfigured Epic is a valid state, never a refusal.

## Attributes

- **Mirror** - ``<workspace>/_wikis/<epic>.wiki``, one of the seven standard folders; a plain tree until publish makes it a clone
- **Config** - ``_config/<epic>.wiki.yaml``: target/source overrides, the documents mapping (``name: path``; ``null`` = wiki-only, ``"dir/::"`` = a preserved wiki-only directory), auto_sync patterns, worktree sources, navigation content
- **Navigation** - ``_Sidebar.md`` and ``Home.md``, pure functions of the config (sections, collapsible blocks, external links, tables, stats)
- **Identity** - the push runs under the Epic identity's ``**GitHubAccount:**`` declaration through the safe's credential chain; a mismatch refuses with the remedy

## Relations

- **extends** → [Projection](ontology-projection-blueprint) - generated from the documents, never written by hand
- **reads** → [Grid4d](ontology-grid4d-blueprint) - the ``_grid4d/`` tree is the source of the mapping
- **exposed by** → [Door](ontology-door-blueprint) - ``ahabase wiki sync|generate|check|clean|publish|status``

## Constraints

- **Same bytes** - the same config and source tree render the same mirror; the navigation builders are pure functions of the config
- **The mirror is generated** - hand edits ride the next sync's purge unless the config accounts for them (a preserved directory is the declared exception)
- **Fail-closed publish** - no reachable remote, an account mismatch or an ambiguous mirror (a push pending plus new changes) refuses with the remedy; nothing publishes silently wrong
- **Epic-explicit** - the door takes ``--epic NAME``; it resolves no ambient Epic

## Example

- ``ahabase wiki sync --epic demolib && ahabase wiki generate --epic demolib && ahabase wiki publish --epic demolib`` fills ``_wikis/demolib.wiki`` from ``demolib/_grid4d/``, renders the navigation and pushes the delta to ``demolib.wiki.git`` under the declared account

## Related

- [implementation-ahabase-wiki-door-blueprint](implementation-ahabase-wiki-door-blueprint) - the door and its modules
- [Projection](ontology-projection-blueprint) - the parent concept
