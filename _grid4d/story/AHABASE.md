# AHABASE

> The open base of ahabase: a tool to build a knowledge base in which one's knowledge is shared under control or protected - the grid4d format, the safe and the doors (CLI, MCP, Claude Code plugin) that methods such as evolucean extend

**Type:** Epic
**Inherits:** evolucean
**StoryPrefix:** AHA-
**Infrastructure:** true
**Remote:** https://github.com/ahabase/ahabase.git
**Branch:** main
**Merge:** true
**Release:** true
**GitOperations:** true
**SnapshotOnComplete:** true
**StoryHistoryKeep:** 2
**GitHubAccount:** lubomirkamensky
**CodeArtifacts:** src/ahabase

## Overview

The open `ahabase` package (Apache-2.0) is architecturally the core of the system - the **base** (Human, 2026-10-25). It owns the grid4d **format** (read and validate `_grid4d/` structure, templates), the shared services every door needs (the **safe**, configuration, `doctor`, `init`, `verify`) and the **doors** themselves - the `ahabase` CLI, the MCP server (`ahabase serve`) and the Claude Code plugin - over one registry of commands and tools. Its concepts are defined in [00-ahabase-ontology-index](00-ahabase-ontology-index).

evolucean is a **method** built on the base (shaping, gradients, measurement, karma, the Game Master, tuned patterns and playbooks): a closed, optional plugin that imports the package's format and services, registers its commands and MCP tools through Python entry points and extends the base's concepts. The base never imports a method (Human, 2026-10-24: the package architecture proposed by evolucean's distribution layer, accepted as the first proposal; 2026-10-25: base and method).

**Incubator and proven selection** (Human, 2026-10-30, option C of [AHA-0011](AHA-0011)): evolucean stays the private incubator. It prototypes new capabilities, tunes the method, and keeps its own knowledge and instance context. Software becomes open by **graduating** into this package: a proven capability moves here, passes the open-zone checks, and evolucean deletes its copy and imports it (Rule "One place per capability"). The two have different reach: **ahabase is fully public**, while **evolucean is open only to the community of its developers**. It is shared inside their trust zone and is never public. What evolucean shares with that community carries only what the zone may see, and the content of closed plug-and-play Epics and instance context stay out (the trust-zone check). Every proven capability ends up public, here.

## Vision

`pip install ahabase` gives a working, private, free tool at step 0; every further capability is discovered when it becomes useful ("many doors, one core"). The premise (Human, 2026-10-25): the value of knowledge grows and must be protectable, while the cost of work, the creation of software included, falls - so the mechanism is open and what is protected is knowledge. The code that touches user data, safe values and the network lives here, open and verifiable, so users can trust the tool while each user's knowledge and a method's know-how stay protected (Trust Zones).

Collaboration is the reason (Human, 2026-10-25): a collaborating community must be more successful than individuals, and collaboration needs every individual's boundary defined - what is personal and what is shared. The safe draws the innermost boundary first, for the data where a mistake cannot be undone; sharing capabilities, never credentials, grows from there. The ambition is community sharing that gives a competitive advantage, built on all knowledge available today: not sharing at any cost, but where it makes sense and adds value - altruism that brings a differential advantage. Sharing multiplies (Human, 2026-10-30): the tool is a gift to everyone and a non-sharer keeps all of it, but the one who shares and collaborates gains what others share and earns wider trust zones, so the altruist gains an edge over the selfish. What counts is the value delivered to others (Karma of usage by others), not the volume shared, and the rules against gaming belong to the communities. It offers the conditions both for the individual's work and for teamwork, taking the best of both ([safe-first-public-capability](safe-first-public-capability)).

## Rules

- **Never imports a method** - dependencies point from evolucean to ahabase only; a method plugs in through entry points.
- **Base and method** (Human, 2026-10-25) - a concept belongs here when it describes structure that software can verify, and to a method when it describes how to work well; what enters the open zone never goes back; collaboration has an open basis, a paid organizational layer and a method's tuned playbooks; a method extends the base's concepts ([00-ahabase-ontology-index](00-ahabase-ontology-index), Constraints). The **Inherits** line below still names evolucean, because the story workflow lives in evolucean's tooling - a known exception until the format and the workflow move here and the direction turns ([implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint), Base and method).
- **One place per capability** - what moves here is removed from the evolucean CLI, which imports it; no copies.
- **Ontology shape** (Human, 2026-10-31) - the Epic ontology carries the architecture of ahabase only - the structural concepts (Trust Zone, Boundary, Door, Plugin, Registry, Health Check, Portability, Lineage, the capabilities index); a concrete capability's concepts live in that capability's subepic ontology, the safe as the first subepic. This dissolves the exception that the Epic's first capability grew at the Epic level. A concept enters an ontology only when it is robust, minimal and needed by already-agreed implementation; the shape is weighed again when the knowledge format graduates here. The moves, the registration and the gates are AHA-0018 ([implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint), Ontology shape).
- **Both OS variants in the same story** (Human, 2026-10-30) - ahabase is built for macOS and Windows immediately (the colleagues run both, the owner tests on both), so every code-impacting story easily delivers both OS variants in the same story: an established library first (`filelock`, `shutil.which`), the platform dispatch (`_win.py`/`_posix.py`) for what genuinely differs, and the CI matrix (macOS, Windows, Ubuntu) that turns the rule red in the story that breaks the other OS ([implementation-ahabase-safe-windows-blueprint](implementation-ahabase-safe-windows-blueprint)).
- **0 Public content only** - no 3 Core know-how, no plugged-in Epic content, no safe values (content containment and the Trust Zone check guard every commit).
- **Safe first** (Human, 2026-10-25; direction 2026-10-30) - the absolute safety of every user's sensitive information is the condition of success. The scope of the safe stays, for now, on credentials including tokens (Human, 2026-10-30: critical, and already implemented in theory). Widening it to personal data, private notes, organization-confidential data and the content of closed Epics, above all at the LLM prompt, is a later step. Safe handling of every credential is the first capability and a mandatory precondition of every further step; security, simplicity and reliability of use are equal requirements - a leaked value and a service lost to impractical credential handling are both failures to minimize; it integrates the best existing tools instead of reinventing them, minimal own code at maximal function; it is open source in the first open zone, not for profit - the community improves and shares it, and the added value of ahabase comes in the further zones ([safe-first-public-capability](safe-first-public-capability)).
- **Knowledge written as public** (Human, 2026-10-24) - everything in this Epic's `_grid4d` may become public together with the code, so it is written as if public now: no plugged-in Epic content, no secrets, no instance specifics (hosts, accounts, local paths, inventories - those stay in the instance's `_data/`), Human rulings recorded by their meaning with a date, in English.
- **Knowledge file naming** (Human, 2026-10-31) - a new issue file is named `issue-<name>.md`, a new idea file `idea-<name>.md`; existing files keep their names, because wiki links are name-only and a rename breaks every link that names the file.
- **Links point inward** (Human, 2026-10-25) - a document of this open Epic links only to documents of this repository and names no document of the closed zone; the closed method may link here, never the reverse - the same direction as the code. What this Epic needs from the closed zone is extracted into its own documents in the extent it needs, and that extract is the one source of truth for it: the closed side refers to it instead of keeping a second copy. Generated links (the story header, the knowledge map) still break the rule until evolucean's generators are fixed; they are never edited by hand, and each is a known exception listed by file and target in the story's link check and tied to its issue - any other link fails ([open-zone-documents-link-into-the-closed-zone](open-zone-documents-link-into-the-closed-zone)). That the closed side refers to the extract instead of keeping a copy is evolucean's task; nothing in this repository can enforce it. The name evolucean is not a document and may appear anywhere, in plain text (Human, 2026-10-25: it is wanted, as marketing). Released stories keep their text.
- **Private until the first release** (Human, 2026-10-24) - the repository turns public only by the Human's decision, together with the first real PyPI release, after: license, README, SECURITY.md, CONTRIBUTING.md, clean containment, zone and secret scans over the whole history, tests and CI.

## Concepts

The concepts of this Epic are defined in its own ontology, the source of truth for them: [00-ahabase-ontology-index](00-ahabase-ontology-index) - among them [Trust Zone](ontology-trust-zone-blueprint), [Boundary](ontology-boundary-blueprint) (personal and shared) and [Safe Value](ontology-safe-value-blueprint). An **Epic** is one repository that owns its artefacts (here: the package code) and its knowledge (`_grid4d/`); its stories carry its prefix (`AHA-`); the Epic concept itself is defined when the knowledge format moves here.

## Related

- [00-ahabase-ontology-index](00-ahabase-ontology-index) - the base's concepts
- [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint) - how the package and its plugins fit
- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - the safe
- [safe-first-public-capability](safe-first-public-capability) - where the safe goes next

---
