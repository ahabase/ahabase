# Decision-driven stories

> The human makes the significant decisions and nothing else; every decision is a numbered story document with a diagram at the right abstraction level, and everything downstream - review, tests, a PR - keys on those decisions.

**Status:** open
**Source:** the Human, 2026-10-31 (consolidation session, [AHA-0017](AHA-0017))

## Idea

The main value a human adds is the significant decision; implementation detail belongs to the agents. For each decision the human needs one clear picture - a diagram that finds the right abstraction level, showing the problem minimally, without implementation detail.

- **One decision, one numbered story document.** Every significant decision gets its own story document carrying that diagram and the decision itself, documented. Decisions are traceable the way stories are.
- **The diagram is built with the agent, live.** Its creation happens before the human's eyes; the human reacts and polishes it interactively with the agent until it shows the problem at the level that lets the decision be made.
- **A PR is a list of decisions.** When pull requests are introduced, a PR carries the list of decisions it implements. The division of labor: the human reviews only the decisions; an LLM reviews that the code and documentation changes reflect them; software tests the scenarios relevant to implementing each decision.
- **Decision transparency.** The state of every open decision is visible while the story runs - what is decided, what waits, what changed (the open questions of the consolidation session name this directly).

**Where it stands.** The method incubates most of this: its decision subepic (founded on the Human's yes of 2026-10-30) builds robust, minimal diagrams for decisions - its decision ontology carries situation, question, option, criterion, consequence, method, decision, diagram-type and supersession blueprints behind their own index - with a decision-record template, a projections pattern of its own, and open ideas on a situation picture taken from a projection, a scorecard counted by a sensor, and diagram experience findable by kind; scorecard rounds run over the collaboration channel. This idea carries what is not there yet: the numbered story document as a decision's home (one decision, one story document), the PR as a list of decisions with the division of review (the human decides, an LLM checks the reflection, software tests the scenarios), and the choice of what graduates from the subepic into the base.

## Related

- [idea-decision-panels](idea-decision-panels) - the panels the decisions are made on
- [idea-team-roles-and-progress](idea-team-roles-and-progress) - who decides and who reviews what
- [AHABASE](AHABASE) - Vision
