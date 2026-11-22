# Pattern verification

> Are patterns verified? Today patterns are declarations the CLI reads and prose players follow - nothing measures that a pattern is followed, or that following it helps.

**Status:** open
**Source:** the Human, 2026-10-31 (consolidation session, [AHA-0017](AHA-0017)) - raised as an open question

## Idea

The open question, with the directions to weigh:

- **Verification of use** - a gate: does the tree actually follow the pattern (the way `ahabase verify` gates capabilities and links)?
- **Verification of effect** - a measurement: does following the pattern improve what the pattern claims to improve?
- **Explicit non-verification** - patterns as advice, their use visible but not enforced.

Each pattern could sit in a different lane; the decision belongs to the pattern's own declaration, not to a global rule.

**Where it stands.** The method verifies pattern use through PostToolUse hooks: pattern-shaped documents (a story's tests skeleton against its required sections) are validated at the edit, and guards enforce story rules. The Human suspects this lane no longer holds everywhere (2026-10-31, unverified, worth measuring): agents increasingly change documents by running scripts instead of the editor tools, a script-driven write fires no post-edit hook, and that class of change may escape the check unnoticed. The open question therefore has two parts - which patterns declare which lane (gate, measurement, advice), and at which layer a check must sit to see every write: the tool layer sees only tool-mediated edits, while a verification pass and the git level see all writes.

## Related

- [AHABASE](AHABASE) - Rules
- [idea-decision-driven-stories](idea-decision-driven-stories) - decisions about verification are themselves decisions
