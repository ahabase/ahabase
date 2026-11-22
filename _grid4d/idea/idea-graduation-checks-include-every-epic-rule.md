# idea: the graduation checks name every Rule of the Epic

**Status:** open
**Origin:** work stream B, 2026-11-08 (the Human: every migration of a capability must satisfy the Rules of ahabase)

The graduation criteria list seven checks (ontology and blueprint, tests with red controls, proven use, open-zone clean, named seams, direct use, added 2026-11-08 by the ruling that a capability is called from this package's own door, and the Human's confirmation, last). The Rules of the Epic are broader: never imports a method, base and method, one place per capability, ontology shape, both OS variants, public content only, Safe first, knowledge written as public, file naming, links point inward, private until the first release. A capability can pass all seven checks and still break a Rule (a literal credential in a definition passes "open-zone clean" if it is not an instance detail).

Make the Rules an eighth check: one evidence row per Rule, software-checkable where the Rule allows (an import scan for "never imports a method", a link census for "links point inward", a canary for "Safe first"). Serves the Epic Rule "what software can check, software checks" and the incubation ruling.

## Related

- [graduation-criteria](graduation-criteria) - the seven checks
- [AHABASE](AHABASE) - the Rules

---
