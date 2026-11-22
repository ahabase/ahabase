# Safe as the first public capability of ahabase

> Find where your secrets are, move them out without breaking anything, keep them out of an AI agent's reach - built from the best existing tools, not a new vault.

**Status:** open
**Source:** shaping with the Human in [AHA-0003](AHA-0003), 2026-10-25, after the instance inventory missed consumers templated from configuration files
**Ontology mapping:** [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - the mechanism it extends; secret values are the most protected data class of the trust zone model

## Human direction (2026-10-25)

- **Mandatory precondition.** Safe handling of every credential is the first capability of ahabase and a precondition of every further step: a product that handles credentials unsafely is flawed, contestable and dangerous from its start.
- **Integrate, do not reinvent.** Take the best of existing solutions and join them in a robust, consistent and sustainable form.
- **Minimalism at maximal function.** As little own code as possible; every own line must earn its place against an existing tool.
- **Open, in the first open zone, not for profit** (Human, 2026-10-25). The safe is offered as open source in the 0 Public zone to fill a gap, not to earn; the community improves and shares it. The added value of ahabase comes in the further zones, never by holding this capability back.

## Why it comes first: boundaries make sharing possible

A key thought of ahabase (Human, 2026-10-25): a collaborating community must be more successful than individuals, and successful collaboration needs each individual's boundary defined - what is on their personal side and what is to be shared. The safe is the critical precondition of the ability to share:

- **Sharing needs a boundary one can trust.** A person shares freely only what is known to be separated from what is personal; without that certainty every share is a risk, and people either share nothing or leak.
- **The safe makes the innermost boundary explicit and enforceable.** Secret values are the tightest part of the personal side - the Vault, the innermost zone (see Personal and shared in the Epic identity; zones renamed 2026-10-31): they stay in the individual's own store and never travel. What travels is the shareable part - a reference (`safe://NAME`), a manifest entry without a value, a configuration, a procedure, a tool.
- **Share capabilities, never credentials.** Two people or two instances that use the same service each hold their own credential in their own store; they share how the work is done, not the key to it.
- **An agent crosses boundaries for its user** - it reads, runs and writes on the user's behalf, and its output may reach a shared screen, a transcript or another person. The agent guard and the output watch keep it on the right side of the boundary.
- **From the innermost boundary outwards.** The same question - personal or shared - is asked of knowledge, configuration and work at every further zone; the safe answers it first for the data where a mistake cannot be undone.

## Grounding

The direction rests on established public knowledge:

- **Clearly defined boundaries come first.** Elinor Ostrom, *Governing the Commons* (1990; Nobel Memorial Prize in Economic Sciences 2009): the first of her eight design principles of communities that sustain a shared resource is clearly defined boundaries - of who belongs and of the resource itself. In our paraphrase of her argument, communities without them tend to lose what they share.
- **Privacy is boundary regulation, not closedness.** Irwin Altman, *The Environment and Social Behavior* (1975): privacy is the ability to open and to close a boundary as the situation needs. Our reading: who cannot regulate the boundary does not open it.
- **Shared information becomes co-owned, under rules.** Sandra Petronio, *Boundaries of Privacy: Dialectics of Disclosure* (2002), Communication Privacy Management: people own their private information; sharing makes the recipients co-owners bound by rules; breaches ("boundary turbulence") damage trust.
- **Teams share and learn when it is safe.** Amy Edmondson, psychological safety in work teams (*Administrative Science Quarterly*, 1999).
- **Human trust is layered.** The layers of personal relationships (about 5, 15, 50 and 150 people; Zhou, Sornette, Hill and Dunbar, 2005) are concentric, as the trust zones are.
- **Sharing by trust level is practice in security.** The Traffic Light Protocol 2.0 (FIRST, 2022) labels information by how far it may travel; the trust zones map onto it (the Vault = TLP:RED).
- **Least privilege.** Saltzer and Schroeder, *The Protection of Information in Computer Systems* (1975): every program and user operates with the least set of privileges necessary - the agent guard applies it to an AI agent.

**A precision, confirmed by the Human (2026-10-25).** A community is not more successful than individuals by itself. Research on collective intelligence (Woolley, Chabris, Pentland, Hashmi and Malone, *Science*, 2010) finds that groups outperform their members under conditions - among them evenly distributed participation and social sensitivity - while groups also fail through groupthink (Janis, 1972) and social loafing (Latané, Williams and Harkins, 1979). The ambition of ahabase is the kind of community sharing that gives its members a competitive advantage, built on all knowledge available today: not sharing at any cost, but sharing where it makes sense and adds value - altruism that brings a differential advantage. Trusted boundaries are one condition of it, and the safe provides the first of them.

**Both individuals and teams** (Human, 2026-10-25). ahabase offers the conditions for work alone and for work in teams, taking the best of both: the individual's own space for focused work, own decisions and own secrets, and the team's breadth, review and shared capability. The ground for it: people working alone and pooling their results generate more ideas than the same people brainstorming together, which loses ideas to production blocking (Michael Diehl and Wolfgang Stroebe, *Journal of Personality and Social Psychology*, 1987), while many independent reviewers find errors one author misses - Linus's law in Eric Raymond's *The Cathedral and the Bazaar* (1999). The pattern is the one of open source: each contributor works in their own space, the community integrates and reviews. The safe serves both sides: each person keeps their own store, the team shares references, procedures and tools.

**Altruism that pays is well grounded.** Reciprocal altruism (Robert Trivers, 1971) and the evolution of cooperation in repeated interaction (Robert Axelrod, *The Evolution of Cooperation*, 1984) show that helping others pays when interactions repeat; indirect reciprocity (Martin Nowak and Karl Sigmund, *Nature*, 1998 and 2005) shows that it pays through reputation, even towards those who never return the help directly. Open source research finds the same in software: in the private-collective model of innovation (Eric von Hippel and Georg von Krogh, *Organization Science*, 2003) contributors reveal their work freely and still gain private benefits - learning, reputation, a say in the direction - that those who only take do not; firms that reveal freely gain through adoption and improvement by others (Harhoff, Henkel and von Hippel, *Research Policy*, 2003). The trust zones are where this is decided: what to share, with whom and how far, so that sharing adds value instead of giving it away.

## Motivating scenario

A presenter shows an AI agent at work to a live audience; during ordinary work the agent prints a password (a configuration file read, an environment listing, an error message with a connection string) and the shared screen shows it to everyone. The value did not leak from a vault - it was readable where the agent looked, nothing stopped the command that showed it, and nothing watched the output.

## The gap

Vaults with a `run` command exist (1Password CLI, Bitwarden, Doppler, Infisical, HashiCorp Vault and OpenBao), as do OS-store bridges (envchain, aws-vault, the `keyring` library), git credential helpers (Git Credential Manager, the OS-store helpers, `gh auth git-credential`), encrypted files (sops, dotenvx) and secret scanners (gitleaks, trufflehog, detect-secrets). Each assumes a clean start or a single concern. Three things stay unsolved for an individual user:

1. **Nobody knows where their secrets are** - shell profiles (often duplicated), credentials in git remote URLs and URL rewrites, configuration files and their backups, values templated into configs, transcripts of agent sessions. A careful manual pass still misses consumers.
2. **Moving out without breaking** - tools describe where a secret should live, not how a working system gets there: consumers, impact, equality proof, one consumer at a time, rollback, rotation last.
3. **An AI agent in the shell** - an agent reads configuration and environment, values land in its context, transcripts and logs; an agent that may run the same interpreter can read the OS store. Protection needs code, permission rules and a sandbox together.

## The capability

| Part | Existing tools it builds on | Own part (the glue only) |
|---|---|---|
| `safe scan` - names and places of secrets, never values | gitleaks / trufflehog / detect-secrets for value shapes (redacted), git config, shell profiles, configuration templates (`env_var(...)`, `${VAR}`), agent transcripts | the places to look and a report of names, places and consumers - no value, no fingerprint |
| store | OS store through `keyring`; 1Password (`op`), Bitwarden (`bw`), Vault/OpenBao as store plugins | the store protocol and the manifest (exists) |
| use | `safe run` (exists); git credential helpers as they are | references `safe://NAME`, resolution for tools with own config (exists) |
| `safe compare` | sha256, constant-time compare | exists (AHA-0003) |
| `safe migrate` | - | the gated procedure of the inventory method: impact map, shadow run, switch, control run, rollback, Human rotation |
| `safe agent-guard` | Claude Code permission rules, sandbox and hooks (and their equivalents of other agents) | the rule set for the stores' locations and the profile files, installed and checked by `doctor` |
| output watch | agent hooks after a tool call; the known values of the safe and the scanners' value shapes | a value that slips into output is masked in what the model sees and named, never repeated; in Claude Code this protects the model's context, not the screen (established in AHA-0005) |
| `safe scan --before-share` | `safe scan` | a quick check before screen sharing or recording: where readable values still lie that an agent could show |
| health | `doctor` (exists) | expiry at session start |

**Three layers, strongest first:** (1) the value is not where an agent looks - references instead of values (store, scan, migrate); (2) the agent cannot run what shows a value (agent-guard); (3) what slips through is masked before the model reads it (output watch) - which protects the model's context, not the screen; a shared screen is protected only by layers 1 and 2. No single layer is enough: a value can end on the screen, in the model's context and so at its provider, in a transcript, in a log.

## Conditions before it is offered

- **Proven on our own instances first** - the migration of this instance and the home instance completes (dogfooding); every step tests the product.
- **No own cryptography** - only established stores and libraries.
- **An honest threat model** - published with what the safe protects and what it does not: [implementation-ahabase-safe-threat-model-blueprint](implementation-ahabase-safe-threat-model-blueprint) (AHA-0006); its designed controls for the agent path come before `safe scan`.
- **The release gate of a security tool** - SECURITY.md and a vulnerability reporting route, secret scans over the whole history, CI, tests on every supported platform.
- **Ready for a community** - CONTRIBUTING.md, a plugin route for stores, scanners and agent guards so others extend it without forking, clear review rules for security changes.
- **Each existing tool is evaluated before own code** - a short comparison (maturity, licence, maintenance, platform reach, what it prints) decides integrate or write; the decision is recorded in the safe blueprint.

## Open questions

Answered by the research of [AHA-0005](AHA-0005) (decisions in [implementation-ahabase-safe-integration-blueprint](implementation-ahabase-safe-integration-blueprint)):

- Scanner engine: gitleaks (MIT, offline, redacting), detect-secrets as the pure-Python fallback; not trufflehog by default (it sends found keys to providers).
- Git credential helper: Git Credential Manager (MIT, several accounts on one host), no own helper; the manifest names its items.
- Claude Code hooks and output: a PostToolUse hook can replace a tool's result for all tools, but only what the model sees - not, as far as documented, the user's screen. The screen is protected only before a command runs.
- Vendor offerings for agents: each is cloud-bound, bound to one vault, or fails open; none combines a local scanner with masking of known values - own glue on the agent's mechanisms.

Still open:

- Which agents beside Claude Code get a guard in the first release, and what their hooks can do.
- Whether Claude Code's sandbox stops a store reached through a system service rather than a file (to be measured in the guard's story).

## Promotion path

1. A research story: evaluate the existing tools per part of the table; the integrate-or-write decision per part - done in [AHA-0005](AHA-0005).
2. The threat model - done in [AHA-0006](AHA-0006); it puts the agent path first.
3. Consumer binding, reveal by a person only and `safe agent-guard` (closing prompt injection through agents).
4. `safe scan` as a package story - the read-only discovery step for a user, built after the agent path.
5. The migration of this instance completes through the impact map, with the Human's consent per consumer; then `safe migrate` as a command over the proven procedure.
6. Public release only through roadmap step 11, with the supply-chain controls of the threat model (T1).

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - the mechanism
- [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint) - where the safe sits
- [AHABASE](AHABASE) - the Epic
