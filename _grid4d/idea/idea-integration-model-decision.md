# idea: decide the integration model before the large graduations

**Status:** open - needs the Human's decision
**Origin:** architecture review of the package, 2026-11-09 (robustness, maintainability, consistency, minimalism), weighed against [AHABASE](AHABASE) and [AHABASE-Priorities](AHABASE-Priorities)
**Addresses:** [issue-identity-describes-doors-and-a-plugin-model-not-in-use](issue-identity-describes-doors-and-a-plugin-model-not-in-use)
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) rows 3 and 5 to 8

The package has two ways for a method to meet it, and the identity describes the second while the code lives the first:

| Option | How a method meets the package | Today |
|--------|--------------------------------|-------|
| A. Library and seams | the method imports `ahabase.<capability>` and pins a release; the package's door also calls the capability directly (Direct use) | how safe, config and llm graduated |
| B. Plugin through the registry | the method registers commands and tools through the `ahabase.plugins` entry points; the doors list them | built (`plugins.py`), used by no distribution |
| C. Both, with a rule | A for graduated capabilities, B only for what stays method-specific (its tuned commands), so the `ahabase` door can list the method's commands without the method importing back | not stated anywhere |

Recommendation: **C**, stated as a Rule in [AHABASE](AHABASE), because it matches what the graduations already do (A) and keeps the registry for the purpose the roadmap gives it. Then the Overview separates today's doors (CLI: `doctor`, `llm`, `ontology`, `safe`, `verify`) from the planned ones (`serve`, the Claude Code plugin, `init`), and the registry gets its first real consumer or waits without growing.

If the decision is A only, the registry is code without a consumer and is a candidate to remove until a plugin needs it.
