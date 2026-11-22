# Progressive capability configuration

> What ahabase can do is decided by patterns - a pattern can change a capability's behavior: start with the basics, add per need, close what a deployment must not do.

**Status:** open
**Source:** the Human, 2026-10-31 (consolidation session, [AHA-0017](AHA-0017))

## Idea

It must be easy to change what ahabase does - for example to exclude cross-instance collaboration entirely. The selection reaches subepics and individual capabilities of a subepic. A deployment starts with ahabase's basic capabilities only and adds the rest when they become useful - the same ladder as "many doors, one core", applied to configuration.

- **Configuration is done by patterns.** A pattern can change a capability's behavior - that is the mechanism this idea is about, not a parallel configuration system. Selecting a subepic or one of its capabilities means declaring the patterns that govern it; what a capability does is always readable from the patterns in force, and a capability without a governing pattern behaves in its default way.
- **Off means off.** A capability closed by its pattern is off everywhere - no half-configured surface, no command that runs while its door is closed.
- **The unit of choice is the subepic capability.** Coarse (a subepic) and fine (one capability of it) selections both work.
- **Basic by default.** The first install does the minimum well; every further capability is an explicit, easy add.

**Where it stands.** Configuring capabilities through patterns is a direction the Human has long worked toward in the method, and it has not fully succeeded there yet. What exists today selects some behavior per instance through the method's CLI settings (hooks, epics, document types); a pattern that measurably changes a capability's behavior is the unfinished core of this idea.

## Related

- [AHABASE](AHABASE) - Vision (many doors, one core)
- [ontology-capabilities-index](ontology-capabilities-index) - the vocabulary patterns select from
- [idea-pattern-verification](idea-pattern-verification) - whether a pattern is followed, measured
- [idea-decision-panels](idea-decision-panels) - a scorecard of what is on is itself a panel
