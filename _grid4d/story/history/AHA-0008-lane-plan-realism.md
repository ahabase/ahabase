# AHA-0008 lane: plan realism

> Is the ahabase plan realistic and does it go the right way? The direction holds. The plan is two documents that disagree, most of its steps wait on a person rather than on code, and one step - moving the knowledge format and the story workflow into the package - is far larger than it reads.

**Lane:** plan realism (home coordinator). **Read on:** 2026-10-26. **Trees read:** the ahabase repository at head `d4436a7` (this story's branch); the foundation roadmap in evolucean's repository, file `ahabase-foundation-roadmap` at its main head `df08cd4b`; and, for the closed side, only aggregate measurements of the evolucean command line at the home instance's checked-out head `e35a8970` (an ancestor of `df08cd4b`, two days behind; the measurements do not depend on the difference). Everything below is marked **read** (a file or a measurement says it) or **inferred** (my reasoning from what was read).

Per the surface rule this document describes the closed method only by aggregates (counts, sizes, rates) and by the roadmap's step numbers; no module names, nothing about how it works. Module-level detail goes to evolucean's owners through the team.

## 1. Where ahabase stands

**Read.**
- 78 commits in three days (15 on 2026-10-24, 56 on 2026-10-25, 7 on 2026-10-26 until the read); seven stories released (AHA-0001 to AHA-0007), this one is the eighth.
- The package: 1,236 lines of code in `src/ahabase` (safe 595 and its command 384, plugin registry 168, CLI 80, version 9) and 1,059 lines of tests; the story rows report 98 tests green at the last review. Four of the seven stories shipped code (AHA-0001, 0002, 0003, 0007); three are documents (research, threat model, ontology).
- The ontology has 16 concept blueprints. By their own **State** line: 7 implemented (health check, manifest, plugin, reference, registry, safe value, store), 5 implemented in part (boundary, consumer, door, rotation, shadow run), 3 planned (agent guard, output watch, scan finding), 1 defined only (trust zone). The two layers that describe the base's own centre - primitives (layer 0) and the knowledge structure with Epic, Story, Requirement, Test, Issue and Idea (layer 1) - are **named but not defined**; they are "defined when the format moves".
- The release gate in the Epic identity lists licence, README, SECURITY.md, CONTRIBUTING.md, clean containment, secret scans over the whole history, tests and CI. At `d4436a7` the licence and README exist; SECURITY.md, CONTRIBUTING.md and any CI configuration do not.
- The home instance (read, by existence): it has no clone of the ahabase repository, no entry for it in its registry, and no safe data or impact map yet.

**Inferred.** The first capability is about half built: the part that handles values is real and well reviewed; the agent guard and `scan` are designs only; nothing of the secret migration has run on the home instance.

## 2. The plan as written - two documents

1. The **architecture blueprint** (this repository) orders five steps: the safe including the agent path and `scan`; the knowledge format and story workflow move into the package and the inheritance turns; the MCP server; the Claude Code plugin; the method as a plugin. It is current: it records base and method, the threat model's order (agent path first) and the equal requirement of security and usability.
2. The **foundation roadmap** (evolucean's repository, written 2026-10-24) has 15 rows: 1 inventory and impact map, 1a compare, 1b release code reads the account from the registry, 2 shadow run per consumer, 3 rotation tested, 4 switch one consumer at a time, 4a shared tokens switch on both instances in one window, 4b transcripts, 5 agent boundary, 6 core tooling gaps of a non-package Epic, 7 quotes replaced by meaning plus a language check, 8 package housekeeping, 9 format into the package then MCP, plugin, core as plugin, 10 Trust Zones with a zone check, 11 public release. By the writer's own note it is stale since before AHA-0004: it does not contain the base and method ontology, the research, the threat model and its order, the hardening or the equal requirement.

The documents agree on direction and disagree on emphasis: the roadmap is a secret-migration plan with gates; the blueprint is a package-architecture plan.

## 3. Findings on realism

**F1. The plan is gated by a person, not by code (read).** Of the roadmap's 15 rows, 9 carry a Human gate (consent per consumer at 2, the Human performs the rotation at 3, consent per switch at 4, the home instance's own Human or seat at 4a, a Human decision at 4b, consent for the settings change at 5, review of each architecture step at 9, each outward move at 10, the release at 11). Of the other 6, rows 1 and 1a are done; 1b, 6, 7 and 8 are open and ungated (8 partly done). **Inferred:** the calendar time of steps 2 to 5 is the time of the Human's decisions per consumer, which no seat can shorten; the number of consumers (instance data, not read from here) multiplies it. The plan should be scheduled around the Human's availability, with the ungated rows used to keep seats productive meanwhile.

**F2. The home instance is at the start of the secret migration (read).** The roadmap lists three home-owned preconditions for steps 2 to 5 there: its own impact map, an allow list for the containment check, and a registry flag for the ahabase entry. By existence checks the home instance has none of them and no clone of the repository. Step 4a (shared tokens switch on both instances in one window) cannot happen before the home side catches up. **Inferred:** the home inventory is a small, ungated analysis story and the cheapest way to move the critical path.

**F3. Step 9 (format into the package) is the dominant code effort (read + inferred).** Measured on the evolucean command line at the home head (the population is every module under its package, 378 modules, 98,091 lines; the 237 modules at the top level are 66,282 lines):
- The modules that hold the knowledge format and the story workflow - chosen by me by name, 31 seeds - together with everything they import at module level are **44 modules, 13,271 lines (14% of the code)**, and that set imports nothing from the collaboration, model-access, sensing, hook or external-adapter parts at module level.
- With imports inside functions counted, the same seeds reach **363 of 378 modules (97%)**: **35 function-level imports leave the 44-module set**, towards projections (6), the collaboration layer (5), sensors (4), knowledge-map logging (3), snapshots (3) and a few others.
- The tests bound to the seeds are **43 of 157 test files, 18,036 of 71,340 test lines**.
- The package today is 1,236 lines. Step 9 moves roughly ten times as much code as the base has, under the rule that the base stays minimal; and the roadmap's precondition for it, row 8 (package housekeeping including the version scheme), is only partly done.

**F4. The code to move is the busiest code (read).** Of 146 commits to the evolucean command line since 2026-10-19, **25 touch the 31 seed modules** - about 3.6 a day, including the story-completion, test-runner and closing-check work of the last week. A move done while those stories continue drifts under the mover; the expand-and-contract pattern in the architecture blueprint helps only if one side is the source of truth during the move. **Inferred:** a freeze window or a "package first" rule for new work in the moved parts is a precondition, not a detail.

**F5. The plugin contract cannot yet carry the method (read + inferred).** The registry offers `add_command` and `add_check` only, API version 1 (read). **Inferred** from F3: the method also needs to register hooks, sensors, projection generators and document-pattern resolution, and the MCP tools the blueprint plans. Registering the method as a plugin (the last part of step 9) needs a contract of version 2, designed from the method's real needs list; the MCP server and the Claude Code plugin need the same extension points.

**F6. Velocity does not extrapolate (inferred).** Observed: four code-bearing stories added 1,236 lines in about two days with two to five review rounds each (about 310 lines per code story). The move at the same per-line cost would be about 40 story-equivalents; a behaviour-preserving move needs characterization tests but no design, so I assume one half to one quarter of the per-line cost, giving **10 to 20 story-equivalents**. At the observed two to four code stories a day that is **three to ten working days**, with wide error bars (assumptions: the pace holds, reviewers stay available, no conflicts with a freeze). The sign matters more than the number: the move is weeks of calendar, not a story.

**F7. The turn is coupled to the team's own channel (inferred).** Both instances coordinate through the method's collaboration layer, and the turn requires every instance to switch in the same window. A failed turn can cut the team off from the channel it needs to recover. The module-level closure in F3 shows the collaboration layer is not in the moving set, which is the right shape; the rehearsal and the tested rollback in the blueprint must run with the channel in place and a second route (a plain message to the Human) agreed beforehand.

**F8. Installing the agent guard is a known fragile act (read, from this project's own incident).** On 2026-10-23 the home instance's machine hooks were bound to a development environment by an install step; when that environment's worktree was removed the gate failed silently open for a time and was repaired by reinstalling from the main environment. The agent guard (roadmap row 5) is the same kind of act: hooks and settings written into a user's environment, and it carries the Human's consent gate. Its story should pin the guard to a stable installed path, verify it at session start (the health check is already planned for that) and fail loudly, not open.

**F9. The plan is not self-contained (read).** Three ahabase documents cite roadmap steps by number from a document in the closed repository, which this Epic's own rule forbids linking; the roadmap itself was not visible from the home instance until the writer named its path and head. Per the rule "the extract is the one source of truth", the step list belongs in this repository's architecture blueprint (title, state, gate and dependency per step), and the closed side should refer to it. The two plan documents (section 2) should become one.

**F10. Parts of the release gate are cheap and independent (read + inferred).** SECURITY.md, CONTRIBUTING.md, CI and the history scans (row 11's preconditions) do not depend on step 9 or on the guard; row 10's zone check is a precondition of the scans and also unblocks the generated-link issue. They are small documentation and configuration stories that can run beside the code work. **Inferred:** leaving them to the end makes the first public release wait on items that need no waiting.

## 4. Does it go the right way?

**Direction: yes, with caveats.** Safe first, an open base with a protected method, and the rule that nothing returns to the closed side are coherent, and each rests on a recorded reasoning. The review found no contradiction between the identity, the architecture blueprint and the ontology on direction. The caveats are order, size and the people the plan waits on.

**Recommended order (inferred; the Human decides):**
1. **Agent boundary / agent guard** (roadmap row 5, already the next story): includes F8 - a stable install path, a start-of-session check, loud failure. Independent of the format move.
2. **Ungated rows beside it**, so seats stay productive while the Human's gates are pending: the home instance's inventory and the three home preconditions (F2), 1b, 6, 7, 8 (the version scheme unblocks 9), and the release-gate hygiene stories (F10).
3. **Shadow run, rotation and switching per consumer** (rows 2 to 4b) on the Human's schedule, starting with the least critical consumer, as the roadmap already says; the guard from step 1 should be in place first so a switched consumer is not exposed to the agent path.
4. **Plugin contract version 2** designed from the method's needs list (F5), with the MCP server over the registry; the MCP tools that read the format follow the first format slice.
5. **Step 9 in slices (F3, F4, F6):** first the read, validate and template part of the format (the smaller seed group, about 2.9 thousand lines, plus its tests), then the story workflow, each slice behind characterization tests and a freeze or "package first" rule.
6. **The turn** at the gate the blueprint defines, plus F7's second route; then the method as a plugin and the Claude Code plugin door.
7. **`safe scan`** after the guard, as the idea says; it does not depend on step 9 and can move earlier if the Human prefers discovery before the migration.
8. **Row 10 and the release (row 11)** last, with row 10's zone check before the scans.

## 5. Decisions for the Human

1. **Merge the two plan documents** into one current plan in this repository (F9) and keep the Human gates visible per row (F1).
2. **Split step 9 into slices with a freeze or "package first" rule** for new work in the moved parts of the method (F3, F4, F6).
3. **Run the ungated rows and the home inventory now** while the gated rows wait (F1, F2, F10), and schedule the Human's share of the migration (rows 2 to 4b) as time on the Human's calendar.
4. **Put the plugin contract version 2 and the MCP server before the move** (F5), with the format-reading MCP tools following the first slice.

## Limits

- The roadmap was read in full at `df08cd4b`; the home instance's checked-out evolucean head is two days behind, so the roadmap was read from the fetched ref, not from the working tree. Rows are quoted by number and short title only.
- Sizes and rates come from a static parse of module imports and from the closed repository's commit log on the home instance; the module set is my choice by name, so a different seed list changes the numbers (14% and 97% bracket the answer: tied at the top of each file, tied to everything at run time). Dynamic imports (entry points, import by name) are not seen by a static parse.
- The number of consumers in the migration is instance data and was not available; F1's calendar estimate is therefore qualitative.
- No code was run for this lane. Effort figures are inferred from observed pace and carry wide error bars. The home-instance preconditions in F2 were checked by existence only, not by content.
