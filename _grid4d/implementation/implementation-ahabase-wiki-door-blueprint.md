# ahabase Wiki Door Implementation Blueprint

> The landed wiki projection: the four proven operations graduated from the method CLI's wiki layer, plus publish - the tail no side had - under the declared account.

**Implements:** [ontology-wiki-blueprint](ontology-wiki-blueprint)
**Stories:** [AHA-0036](AHA-0036)
**Code:** cli_wiki, wiki.__init__, wiki.config, wiki.context, wiki.generate, wiki.sync, wiki.validate, wiki.clean, wiki.publish
**Status:** landed 2026-11-22 (AHA-0036); the flip story in the method's repository repoints its consumers to this seam

## Overview

The graduation's Phase 1 (the dossier: `evolucean/_grid4d/subepic/evolucean-ahabase/implementation/evolucean-ahabase-wiki-dossier.md`): the method CLI's wiki layer - page generation into a local mirror, measured dormant there (stale mirror, no publish loop) - moved into the base as `ahabase.wiki` behind the one registry, and the missing publish tail built here so the capability completes its loop: the mirror becomes a clone of the repository's wiki remote, the synced delta commits, and the push rides the safe's credential chain under the Epic's declared GitHub account. This blueprint fixes the seam contract the method's flip story quotes, and records every departure from ported behavior.

## Rules

1. **Epic-explicit door** - every subcommand takes `--epic NAME`; an omitted name refuses with the remedy (exit 1), never an ambient resolution. The ported auto-detect (the primary epic) is ambient state the door rejects, per the config door's landing decision.
2. **Config convention (the door's own)** - `_config/<epic>.wiki.yaml` under the workspace, the house convention - not the ported in-repository `<epic>.wiki.yml` (a departure, recorded: the workspace `_config/` is where every per-epic file lives); absent or empty reads `{}` - the defaults apply (target `_wikis/<epic>.wiki`, source `_grid4d/`, no mapping) and **nothing refuses** on a missing config, a departure from the ported refusal (an unconfigured Epic is a valid state; the method side's own live config file was empty, so the ported refusal fired on the real instance).
3. **Rendered bytes are the contract** - the navigation builders are pure functions of the config and produce byte-identical output to the method side's on the same config (the parity row compares against the golden captured from a live method-side run); quirks ride along deliberately (e.g. a trailing `> ` line after a blockquote).
4. **The mirror is created, not demanded** - a missing mirror directory is created by every operation (an empty mirror is a valid wiki state); the ported "wiki path not found" refusal is gone. The door is the mirror's writer.
5. **Preserved directories need quoted YAML keys** - the `"dir/::"` mapping: unquoted, YAML parses the key as `dir/:` and the pattern silently degrades to a skipped manual mapping (measured live at the golden capture); the port keeps the key convention and documents the quoting.
6. **Exit codes distinguish the outcomes** - 0 done (check with no duplicates; publish pushed or nothing to publish), 1 refused (the remedy printed; the one refusal class of the migrated four), 2 usage, 3 check found duplicates. The flip parses these; publish refusals name their class in the message (no remote reachable, account mismatch, ambiguous mirror).
7. **Fail-closed publish identity** - the Epic identity's `**GitHubAccount:**` must be declared and must equal the account the safe's gh login opens (`gh api user`, ambient token env scrubbed); a mismatch refuses with both names and the remedy - the release gate's design, never a silent other account. The ambient token variables (`GH_TOKEN`, `GITHUB_TOKEN`, both enterprise variants) are scrubbed from **every** child this module runs - the probe's and the git children's alike - so the account the gate verified is the only token source the push can ride; a credential helper preferring an ambient token (gh's prefers `GH_TOKEN`) would otherwise push as another account while the gate had proven the safe's (round-1 review, 2026-11-22: the intent-vs-action class of the AHA-0034 record).
8. **The remote is derived, never guessed** - `publish.remote` in the yaml overrides; else derived from the epic repository's origin (`<repo>.wiki.git`, an ssh github origin normalized to https so the push rides the credential chain); `publish.branch` overrides the default `master` (the GitHub wiki's). A derivation that cannot happen refuses with the remedy.
9. **The delta, not the tree** - publish fetches, resets the index to the remote head (`--mixed`, the working tree is the synced truth), commits `wiki: publish <epic> mirror`, pushes `-u`. A pending commit from a failed push plus new uncommitted changes refuses (ambiguous mirror, remedy named); a pending commit alone is pushed (recovery). A failed push leaves the commit in the mirror - the next run pushes it.
10. **`.git` is structure, not content** - every walk (duplicates, purge, preserved dirs) skips `.git` parts; the mirror is a clone exactly when publish made it one.
11. **No method literals in the package** - the port speaks the engine's vocabulary; the plugin guard (`tests/test_plugins.py`) holds the line mechanically.

## Template

The seam contract, the text the method's flip story quotes verbatim (frozen at the dossier, quoted unchanged in the landing story; `status` is additive beyond the frozen five - the flip may use it, never depend on it being absent):

```markdown
- **Type:** subprocess - the publish surface touches the credential chain; the one-way dependency stays clean: the method shells out to the `ahabase` entry point, ahabase imports nothing of the method.
- **Surface:** `ahabase wiki check|clean|generate|sync|publish [--epic NAME]` - the four migrated doors plus publish, exit codes distinguishable per outcome (0 done, 1 refused, 2 usage, 3 check found duplicates). Additive: `ahabase wiki status [--epic NAME]` (the mirror's git state).
- **Floor:** the landing's released tag (`v0.0036.0.0000.00`). Strict floor on the released tag, never a branch or tree.
- **Custody boundary:** implementation and tests move; data (yaml, mirror, settings) stays; `get_story_behavior` stays in the method's repository.
```

## Structure

| Module | Role |
|---|---|
| `src/ahabase/cli_wiki.py` | the door: the `wiki` group, the epic-explicit resolution, the exit-code contract |
| `src/ahabase/wiki/__init__.py` | the package: the capability's contract line |
| `src/ahabase/wiki/config.py` | the config load (workspace convention, defaults) and path resolution |
| `src/ahabase/wiki/context.py` | the sync plan (one run's mutable state) and the refusal type |
| `src/ahabase/wiki/generate.py` | the navigation builders (pure) and the generate operation |
| `src/ahabase/wiki/sync.py` | the five passes: preserved dirs, mapped documents, auto patterns, worktrees, purge |
| `src/ahabase/wiki/validate.py` | duplicate detection and the check walk |
| `src/ahabase/wiki/clean.py` | the dedupe (root copy wins, newest promoted) |
| `src/ahabase/wiki/publish.py` | the identity gate, remote derivation, delta commit, push, mirror status |

| Function | Shape | Ported from |
|---|---|---|
| `load_wiki_config(epic)` | the yaml at `_config/<epic>.wiki.yaml`, `{}` when absent/empty | the method wiki config (location changed, refusal removed) |
| `resolve_wiki_paths(epic, config)` | (mirror, source) anchored at the workspace | the method wiki config |
| `build_sidebar_lines` / `build_home_lines` | pure renderers, byte-parity | the method wiki generate |
| `sync_documents(...)` | the five passes into the mirror | the method wiki sync |
| `find_duplicates` / `check_wiki` / `clean_wiki` | the validation pair | the method wiki validate/clean |
| `account_of_safe_login()` | `gh api user --jq .login`, env scrubbed, fail-closed | the method's safe route (the probe pattern) |
| `declared_account(epic_root)` | the identity's GitHubAccount, placeholder-aware | the method's release gate (the declaration read) |
| `publish(...)` | identity gate, clone/fetch, delta commit, push | new (the missing tail) |
| `mirror_status(wiki_path)` | porcelain status dict | the method's wiki hook status read |

## Example

The suites that hold the rules measured: `tests/test_wiki.py` - the parity row against the golden (config present with overrides), the defaults polarity (config absent), the seam surface (six subcommands, distinguishable exits), the consumer-surface grep rows - and `tests/test_wiki_publish.py` - the end-to-end local bare remote (clone/init, commit, push, the pushed tree equals the mirror), the delta-only second run, the wrong-account refusal, the round-1 rows (the real probe both polarities, the end-to-end run with the probe real, the push-child token-scrub witness). Canonical calls:

```sh
ahabase wiki sync --epic amethod   # _grid4d/ into _wikis/amethod.wiki (orphans purged)
ahabase wiki generate --epic amethod   # _Sidebar.md + Home.md from the yaml
ahabase wiki publish --epic amethod   # delta commit + push under the declared account
```

## Related

- [ontology-wiki-blueprint](ontology-wiki-blueprint) - the concept this implements
- [AHA-0036](AHA-0036) - the landing story (the dossier link, the flip named)
