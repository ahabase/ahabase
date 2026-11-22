# ahabase Safe Integration Blueprint

> Which existing tool each part of the safe integrates, and what little ahabase writes itself - decided per concept of the ontology, from a comparison of the tools available in October 2026.

**Implements:** [ontology-store-blueprint](ontology-store-blueprint), [ontology-scan-finding-blueprint](ontology-scan-finding-blueprint), [ontology-agent-guard-blueprint](ontology-agent-guard-blueprint), [ontology-output-watch-blueprint](ontology-output-watch-blueprint), [ontology-consumer-blueprint](ontology-consumer-blueprint) (git over https) - within [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint)
**Story:** [AHA-0005](AHA-0005)
**Code:** safe
**Status:** the git credential helper's part is built in safe (AHA-0013); the scanner, further stores and the agent hooks remain proposed - decisions per part below, each in its own story

## Overview

The Human ruled (2026-10-25) that the safe integrates the best existing tools instead of reinventing them, with minimal own code at maximal function. This blueprint records, per part, the tools compared, the decision (integrate or write), how the integration is invoked and what remains as own glue.

**Evidence.** Licences, invocation and options were read on the projects' own repositories and documentation on 2026-10-25; a fact not found there is marked unverified. **Versions, release dates and maintenance states** (latest release, "feature complete", "very active", "v2 in progress") were taken from the projects' release pages by a research pass on that day and not re-checked by hand - they are a snapshot, and each part's story re-checks them before building (rule 5). The agent's mechanisms were read in its official documentation (permissions and hooks references), the decisive statements twice. Sources: github.com/gitleaks/gitleaks, github.com/betterleaks/betterleaks, github.com/trufflesecurity/trufflehog, github.com/Yelp/detect-secrets, github.com/GitGuardian/ggshield, github.com/jaraco/keyring, 1password.dev (CLI), bitwarden.com (Secrets Manager CLI), github.com/openbao/openbao, github.com/git-ecosystem/git-credential-manager, code.claude.com/docs (permissions, hooks, sandboxing).

## Rules

1. **Integrate before writing** - own code is limited to glue: invoking a tool, reducing its output to names and places, and mapping it onto the ontology's concepts.
2. **Offline by default** - an integrated tool must work without sending anything off the machine; a tool that sends content or values to a service (a cloud scanner, provider-side verification of a found key) is not used, or only with that behaviour switched off.
3. **Our own reduction of output** - even when a tool redacts, ahabase removes value fields from its output itself before anything is shown or stored; a tool's redaction is a second layer, not the only one.
4. **Licence fit** - an integrated tool is invoked as a separate program or used as a library under a licence compatible with Apache-2.0; a tool with a source-available or proprietary licence is optional, never required.
5. **Re-check before building** - the comparison below is a snapshot; a part's story confirms maintenance and options of the chosen tool first.

## Decisions per part

### Scanner (Scan Finding)

| Tool | Licence | State (2026-10) | Offline | Values in output |
|---|---|---|---|---|
| gitleaks | MIT | v8.30.1 (2026-03); its maintainer declares it feature complete, security fixes only | yes | `--redact` (full or partial); `dir`, `git` and `stdin` modes; JSON report |
| Betterleaks | MIT | v1.9.0 (2026-09); the same author's successor, v2 in progress | yes; live checks only with `--validate` | no redaction flag found |
| trufflehog | AGPL-3.0 | very active | only with `--no-verification` (by default it verifies candidates against the providers) | the JSON carries the raw value |
| detect-secrets | Apache-2.0 | 1.5.0 (2024-05), slow | yes, with `--no-verify` | baseline holds hashes (unverified) |
| ggshield | MIT client | active | no - content goes to a cloud API | not documented |

**Decision: integrate gitleaks** as a subprocess (`gitleaks dir <path> --redact -f json`), with own glue that drops every value field from the report and maps each result to a Scan Finding (place, kind, name). Own code adds the places a code scanner does not look at: shell profiles, git remote URLs and URL rewrites, configuration templates that reference variables, agent transcripts. **Fallback:** detect-secrets with `--no-verify` when no gitleaks binary is available. **Watch:** Betterleaks, once its v2 is stable and has redaction. Not used: trufflehog by default (it sends found keys to providers), ggshield (cloud).

### Stores (Store)

| Tool | Licence | How it is called | Notes |
|---|---|---|---|
| Python `keyring` | MIT (unverified) | library, pluggable backends by entry point | OS stores built in; the safe's default (exists) |
| 1Password CLI `op` | proprietary (unverified) | `op read op://vault/item/field`, `op run` | `op run` masks values in output by default - the model for our `safe run` |
| Bitwarden `bw`, Secrets Manager `bws` | `bw` GPL-3.0 (unverified); `bws` not a standard open licence | `bw get`, `bws secret get`, `bws run` | personal vault and team secrets |
| OpenBao | MPL-2.0 | HTTP API, `bao` CLI | open fork of Vault; preferred over Vault, whose releases since 2023-08 are under BSL |
| gopass / pass | MIT (unverified) / GPL | `gopass show -o` | GPG or age, git-synced |
| envchain, aws-vault | MIT | wrappers | stagnant; not used |

**Decision: keep `keyring` as the one interface; add stores as small own backends that call each manager's CLI** (`op read`, `bw get` / `bws secret get`), each optional and installed by choice; OpenBao over its HTTP API later. Not depended on: the existing third-party keyring backends for 1Password and Bitwarden (alpha or thin, and they register at a priority that can take over the default backend). **Adopt from `op run`:** masking of known values in the child's output by `safe run`.

### Git credential helper (Consumer: git over https)

| Helper | Licence | Several accounts on one host |
|---|---|---|
| Git Credential Manager (GCM) | MIT | yes - a user in the remote URL or `credential.<url>.username`; stores: OS keychain, Secret Service, GPG/pass, Windows stores; OAuth for the big hosts |
| git-credential-osxkeychain / libsecret | GPL-2.0, ship with git | only through a user in the URL |
| `gh auth git-credential` | MIT (unverified) | several accounts can log in, but git gets only the active one |

**Decision: integrate GCM** as the recommended helper; the minimal OS helpers stay a valid choice; `gh` is not used for several accounts. Own glue: no own credential helper is written - the safe's manifest names the helper's item as a **target** of the secret's entry (kind `git-credential`, host and account; [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint), rule 7), and the safe talks to whatever helper the user has configured, through git itself: `git credential approve` writes the value to every configured helper on rotation (the value on stdin, never in an argument list), `git credential fill` answers presence for health, and every write is proven by reading the destination back - the value `fill` returns, compared with the value written by digest, in constant time, in-process, never printed; a destination holding the previous value fails the proof as surely as one that took nothing (git accepts a value with no credential helper configured and writes nothing, exit 0); its every prompt is disabled on every OS (git's terminal prompt, askpass through the platform arm's no-op - `true` on POSIX, `rundll32` on Windows, [implementation-ahabase-safe-windows-blueprint](implementation-ahabase-safe-windows-blueprint) - and GCM's GUI). `gh` is proven the same way: `gh auth token` prints the login's token - captured, compared, dropped. The helper resolution follows git's own config chain, including a repo-local `credential.helper` of the directory the command runs in - the store written is whichever helper that resolution feeds, exactly as a plain git invocation would use. GCM and the minimal OS helpers need no code of their own to be targets.

**Amended (AHA-0019, 2026-10-31):** the call-model - every use answered live by the safe, no value resting in a third party's store - made the safe itself the helper: `ahabase safe credential` speaks git's credential-helper protocol read-only over the safe's store (`get` answers the entry whose `git-credential` target names the host; `store`/`erase` never write), so git's credential never exists outside the safe. This is the first-party route and needs no third-party helper at all; GCM and the OS helpers remain the integrated **targets** for the custody model (the safe writes and refreshes their item on rotation). The two routes are per model, not in competition - a machine picks one and wires it once.

### Agent guard and output watch (Agent Guard, Output Watch)

What Claude Code offers, from its documentation (checked 2026-10-25):

- **Permission rules** - deny rules with wildcards for Bash (`Bash(printenv *)`); Read and Edit deny rules also apply to file commands Claude Code recognizes in Bash (`cat`, `head`, `tail`, `sed`, `tee`) and to redirection targets - but not to a command that reads files without naming them, nor to a Python or Node script that opens files itself.
- **Sandbox** - OS-level (Seatbelt on macOS, bubblewrap on Linux) restrictions of Bash and its child processes, including denied read paths; it does not apply to the Read tool (permission rules cover that), and hooks, MCP servers and excluded commands run outside it. Whether it stops a store reached through a system service rather than a file is not documented.
- **PreToolUse hook** - can deny a call or replace its input (`updatedInput`) before it runs.
- **PostToolUse hook** - `updatedToolOutput` replaces a tool's result for all tools, but **only what the model sees**: the tool has already run, and the documentation does not say that the user's screen or the transcript show the replaced output; telemetry captures the original. The hooks reference, section PostToolUse decision control (read 2026-10-25), describes `updatedToolOutput` as replacing the tool's output before it is sent to Claude, prefers it over the MCP-only field because it works for all tools, and warns that it only changes what Claude sees.

Vendor offerings found: 1Password's agent hooks (validate mounted environment files; fail open), GitGuardian's MCP server and assistant hooks (content goes to its cloud API), Infisical's and Doppler's MCP servers (read values from their services, masking optional). None combines a local scanner with masking of known values for any store.

**Decision: write own glue on the agent's mechanisms** - (1) a permission rule set and sandbox configuration for the stores' locations and the files still holding values, proposed to the owner and checked by `doctor`; (2) a PreToolUse hook that denies commands which print values and checks a command's text with the local scanner; (3) a PostToolUse hook that masks known values of the safe and scanner-shaped values in what the model sees.

**Consequence for the motivating scenario.** A value shown on a shared screen is stopped only before the command runs: by the value not being where the agent looks (references instead of values) and by the guard denying the command. The output watch protects the model's context, not the screen - it is the last layer and is described honestly as such.

## Structure

The parts are built in this order, each in its own story: the agent path first - consumer binding, reveal by a person only and the agent guard (the threat model closes prompt injection before anything else, [implementation-ahabase-safe-threat-model-blueprint](implementation-ahabase-safe-threat-model-blueprint), rule 2); then the scanner (read-only, the discovery step for a user); the output watch; further stores; the git credential helper's manifest entries.

## Template

```
ahabase safe scan [PATH ...]             # names and places, never values (gitleaks + own places)
ahabase safe guard install --agent claude-code   # propose rules, sandbox and hooks; owner consents
```

## Example

```
$ ahabase safe scan ~
~/.profile:12  profile export   DB_PASSWORD   consumers: database client
<repo>/.git/config  remote URL credential  origin
2 findings - names and places only
```

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - the mechanism
- [safe-first-public-capability](safe-first-public-capability) - the direction this decides
- [00-ahabase-ontology-index](00-ahabase-ontology-index) - the concepts
