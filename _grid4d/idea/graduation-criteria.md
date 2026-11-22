# Graduation Criteria

> A capability moves from the incubator into this package only when software can show it is proven. Each graduation then deletes the incubator's copy, so the capability lives in one place.

**Status:** open
**Source:** the Human, 2026-10-30 ([AHA-0011](AHA-0011), notes 4 and 5)

## Idea

A graduation passes all of these checks, and software checks every one that can be checked:

1. **Ontology and blueprint** - the capability's concept and its implementation blueprint exist and are linked.
2. **Tests with red controls** - its tests pass, and planted mutants turn them red.
3. **Proven use** - it has been used in practice and measured (usage and karma readings over a stated period).
4. **Open-zone clean** - no instance, company or person detail in its code, tests or documents; the containment and trust-zone checks pass over everything that moves.
5. **Named seams** - it enters through a few named interfaces, checked by a test, and imports no method.
6. **Direct use** (Human ruling 2026-11-08) - the capability is called from this package's own door, like `safe`: its command, run with nothing of the incubator present, serves a real call on the instance's data. Measured, with the command and its answer recorded, before the Human's confirmation is asked; a capability that answers only through the incubator's wrappers has moved its code, not its purpose.
7. **The Human's confirmation** - the graduation is a decision, and the Human makes it, last, on the evidence of checks 1 to 6.

After the move, the incubator deletes its copy and imports the package (Rule "One place per capability"). No capability exists twice.

## Prior art

One-way incubation into a stable product: Fedora into RHEL, Chrome Canary into Stable, the Apache Incubator into top-level projects. The alternatives weighed were one codebase with an experimental flag, which would leak instance detail and unfinished code into the open, and a rewrite from scratch, which would lose proven behaviour.

## Related

- [AHABASE](AHABASE) - Overview, "Incubator and proven selection"
- [implementation-ahabase-architecture-blueprint](implementation-ahabase-architecture-blueprint)
